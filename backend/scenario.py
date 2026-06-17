import asyncio
import json
import logging
import datetime
from typing import Set, Dict, Any, List
from fastapi import WebSocket
from agents import SCENARIOS, ALL_AGENTS, get_resolution_step

# Band SDK integration imports
from band_agents import CISOBandAdapter, CFOBandAdapter, CEOBandAdapter
from band.core.types import PlatformMessage

logger = logging.getLogger("scenario")


class MockAgentTools:
    def __init__(self, sender_name: str, debate_list: list):
        self.sender_name = sender_name
        self.debate_list = debate_list
        self._participants = []

    async def send_message(self, content: str, mentions=None) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Determine role and sentiment
        role = "CEO" if "CEO" in self.sender_name else ("CISO" if "CISO" in self.sender_name else "CFO")
        sentiment = "critical" if role == "CISO" else ("alert" if role == "CFO" else "neutral")
        
        self.debate_list.append({
            "sender": self.sender_name,
            "role": role,
            "timestamp": timestamp,
            "content": content,
            "sentiment": sentiment
        })

    async def send_event(self, content: str, message_type: str, metadata=None) -> None:
        pass

    async def add_participant(self, identifier: str, role: str = "member") -> None:
        pass

    async def remove_participant(self, identifier: str) -> None:
        pass

    @property
    def participants(self) -> list:
        return self._participants

    async def get_participants(self) -> list:
        return self._participants

    async def lookup_peers(self, page: int = 1, page_size: int = 50) -> list:
        return []

    async def create_chatroom(self, task_id: str | None = None) -> str:
        return "room"


class ScenarioManager:
    def __init__(self, persistence=None):
        self.active_connections: Set[WebSocket] = set()
        self.is_running = False
        self.current_step_index = -1
        self.scenario_state = "INITIAL"
        self.active_scenario_id = "INC-001"
        self.current_state_payload = self._get_initial_state()
        self.loop_task = None
        self.decision_made = None
        self.step_delay = 3.5
        self.alerts_history: List[Dict[str, Any]] = []
        self.persistence = persistence

    async def restore_from_persistence(self):
        """Restore manager state from Redis after a server restart."""
        if not self.persistence or not self.persistence.is_available:
            return

        # Restore alert history
        saved_alerts = await self.persistence.load_alerts()
        if saved_alerts:
            self.alerts_history = saved_alerts
            logger.info(f"Restored {len(saved_alerts)} alerts from Redis")

        # Restore active scenario state
        scenario_id, state_payload, sim_data = await self.persistence.restore_state()
        if scenario_id and state_payload:
            self.active_scenario_id = scenario_id
            self.current_state_payload = state_payload
            self.scenario_state = state_payload.get("scenarioState", "INITIAL")
            logger.info(f"Restored scenario {scenario_id} state from Redis (state={self.scenario_state})")

        if sim_data:
            self.current_step_index = sim_data.get("current_step_index", -1)
            self.decision_made = sim_data.get("decision_made")
            # Don't auto-resume the simulation loop — user must restart
            self.is_running = False
            self.current_state_payload["simulationRunning"] = False


    def _get_initial_state(self) -> Dict[str, Any]:
        scenario = SCENARIOS[self.active_scenario_id]
        
        # Build initial agents list from the scenario specification
        active_agents = []
        for name in scenario.agents_involved:
            agent_info = ALL_AGENTS.get(name)
            if agent_info:
                active_agents.append({
                    "id": agent_info["id"],
                    "name": agent_info["name"],
                    "role": agent_info["role"],
                    "status": "IDLE",
                    "lastMessage": agent_info["lastMessage"],
                    "tags": agent_info["tags"]
                })
        
        return {
            "scenarioState": "INITIAL",
            "scenarioId": self.active_scenario_id,
            "scenarioTitle": scenario.title,
            "severity": scenario.severity.upper() if scenario.severity.upper() in ["OPTIMAL", "ALPHA", "OMEGA", "P1"] else "ALPHA",
            "riskScore": 0,
            "revenueAtRisk": "$0",
            "affectedUsers": 0,
            "nodesCompromised": 0,
            "activeIncidentsCount": 0,
            "regionalStatus": [
                { "name": "US-EAST-1", "status": "OPTIMAL" },
                { "name": "EU-WEST-2", "status": "OPTIMAL" },
                { "name": "AP-SOUTH-1", "status": "OPTIMAL" },
                { "name": "SA-EAST-1", "status": "OPTIMAL" }
            ],
            "timeline": [],
            "agents": active_agents,
            "debate": [],
            "auditLogs": [],
            "postMortem": None,
            "shutdownLabel": scenario.shutdown_label,
            "isolationLabel": scenario.isolation_label,
            "simulationRunning": False
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Immediately send current state to newly connected client
        await websocket.send_json({
            "type": "state_update",
            "payload": self.current_state_payload
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        dead: list[WebSocket] = []
        for conn in list(self.active_connections):
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.active_connections.discard(conn)

    def start_simulation(self, scenario_id: str = "INC-001"):
        if self.loop_task:
            self.loop_task.cancel()
            self.loop_task = None
            
        self.is_running = True
        self.decision_made = None
        self.current_step_index = 0
        self.active_scenario_id = scenario_id
        
        # Reset current payload for the selected scenario
        self.current_state_payload = self._get_initial_state()
        self.current_state_payload["simulationRunning"] = True
        
        # Persist the initial state immediately
        asyncio.create_task(self._persist_state())
        
        self.loop_task = asyncio.create_task(self._run_loop())

    async def _persist_state(self):
        """Persist current state & simulation progress to Redis."""
        if not self.persistence or not self.persistence.is_available:
            return
        try:
            sim_data = {
                "current_step_index": self.current_step_index,
                "scenario_state": self.scenario_state,
                "is_running": self.is_running,
                "decision_made": self.decision_made,
                "active_scenario_id": self.active_scenario_id,
            }
            await self.persistence.save_full_state(
                self.active_scenario_id,
                self.current_state_payload,
                sim_data,
            )
        except Exception as e:
            logger.warning(f"Failed to persist state: {e}")

    async def _run_loop(self):
        try:
            scenario = SCENARIOS.get(self.active_scenario_id, SCENARIOS["INC-001"])
            steps = scenario.steps
            
            while self.is_running and self.current_step_index < len(steps):
                step = steps[self.current_step_index]
                self.scenario_state = step.step_name
                
                # Apply step updates
                self.current_state_payload["scenarioState"] = step.step_name
                self.current_state_payload["riskScore"] = step.risk_score
                self.current_state_payload["revenueAtRisk"] = step.revenue_at_risk
                self.current_state_payload["affectedUsers"] = step.affected_users
                self.current_state_payload["nodesCompromised"] = step.nodes_compromised
                self.current_state_payload["activeIncidentsCount"] = step.active_incidents

                if step.timeline_event:
                    self.current_state_payload["timeline"].append(step.timeline_event)
                
                if step.audit_log:
                    self.current_state_payload["auditLogs"].append({
                        "id": str(len(self.current_state_payload["auditLogs"]) + 1),
                        **step.audit_log
                    })

                if step.agent_update:
                    # Support both list of updates and single update dict
                    updates = step.agent_update if isinstance(step.agent_update, list) else [step.agent_update]
                    agents = self.current_state_payload["agents"]
                    for update in updates:
                        for a in agents:
                            if a["id"] == update["id"]:
                                a.update(update)

                if step.step_name == "DEBATE_ACTIVE":
                    # Instantiate real Band SDK adapters
                    ciso = CISOBandAdapter(scenario_context=scenario.description)
                    cfo = CFOBandAdapter(scenario_context=scenario.description)
                    ceo = CEOBandAdapter(scenario_context=scenario.description)
                    
                    ciso.agent_name = "CISO_SHIELD"
                    cfo.agent_name = "CFO_QUANT"
                    ceo.agent_name = "CEO_ALPHA"
                    
                    debate_list = []
                    
                    # 1. System prompts the debate
                    msg1 = PlatformMessage(
                        id="sys_init", room_id="room",
                        content=f"Incident {self.active_scenario_id} ({scenario.title}) debate active. What is your recommendation?",
                        sender_id="sys", sender_type="system", sender_name="System",
                        message_type="chat", metadata=None, created_at=datetime.datetime.now()
                    )
                    
                    # 2. CISO speaks
                    tools_ciso = MockAgentTools("CISO_SHIELD", debate_list)
                    await ciso.on_message(msg1, tools_ciso, [], None, None, is_session_bootstrap=True, room_id="room")
                    
                    # 3. CFO responds
                    tools_cfo = MockAgentTools("CFO_QUANT", debate_list)
                    history_cfo = [f"[{d['sender']}]: {d['content']}" for d in debate_list]
                    msg2 = PlatformMessage(
                        id="msg_ciso", room_id="room", content=debate_list[-1]["content"],
                        sender_id="ciso", sender_type="agent", sender_name="CISO_SHIELD",
                        message_type="chat", metadata=None, created_at=datetime.datetime.now()
                    )
                    await cfo.on_message(msg2, tools_cfo, history_cfo, None, None, is_session_bootstrap=False, room_id="room")
                    
                    # 4. CEO makes the decision prompt
                    tools_ceo = MockAgentTools("CEO_ALPHA", debate_list)
                    history_ceo = [f"[{d['sender']}]: {d['content']}" for d in debate_list]
                    msg3 = PlatformMessage(
                        id="msg_cfo", room_id="room", content=debate_list[-1]["content"],
                        sender_id="cfo", sender_type="agent", sender_name="CFO_QUANT",
                        message_type="chat", metadata=None, created_at=datetime.datetime.now()
                    )
                    await ceo.on_message(msg3, tools_ceo, history_ceo, None, None, is_session_bootstrap=False, room_id="room")
                    
                    self.current_state_payload["debate"] = debate_list
                else:
                    if step.debate_messages:
                        self.current_state_payload["debate"].extend(step.debate_messages)

                # Set regional status degradation for specific milestones
                if step.step_name == "RISK_LEGAL":
                    self.current_state_payload["regionalStatus"] = [
                        { "name": "US-EAST-1", "status": "CRITICAL" },
                        { "name": "EU-WEST-2", "status": "DEGRADED" },
                        { "name": "AP-SOUTH-1", "status": "OPTIMAL" },
                        { "name": "SA-EAST-1", "status": "OPTIMAL" }
                    ]
                
                # Broadcast updated payload
                await self.broadcast({
                    "type": "state_update",
                    "payload": self.current_state_payload
                })

                # Persist state after each step
                asyncio.create_task(self._persist_state())

                # If we hit the debate phase, we pause and wait for the operator decision
                if step.step_name == "DEBATE_ACTIVE":
                    logger.info(f"Simulation reached DEBATE_ACTIVE for {self.active_scenario_id}. Pausing.")
                    break

                self.current_step_index += 1
                await asyncio.sleep(self.step_delay)

        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled.")
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")

    async def submit_decision(self, decision: str):
        if self.scenario_state != "DEBATE_ACTIVE":
            return
        
        self.decision_made = decision
        res_step = get_resolution_step(decision, self.active_scenario_id)

        # Apply final step updates
        self.current_state_payload["scenarioState"] = res_step.step_name
        self.current_state_payload["riskScore"] = res_step.risk_score
        self.current_state_payload["revenueAtRisk"] = res_step.revenue_at_risk
        self.current_state_payload["affectedUsers"] = res_step.affected_users
        self.current_state_payload["nodesCompromised"] = res_step.nodes_compromised
        self.current_state_payload["activeIncidentsCount"] = res_step.active_incidents

        if res_step.timeline_event:
            self.current_state_payload["timeline"].append(res_step.timeline_event)

        if res_step.audit_log:
            self.current_state_payload["auditLogs"].append({
                "id": str(len(self.current_state_payload["auditLogs"]) + 1),
                **res_step.audit_log
            })

        if res_step.debate_messages:
            self.current_state_payload["debate"].extend(res_step.debate_messages)

        # Change all agents to SLEEPING or IDLE after resolution
        for a in self.current_state_payload["agents"]:
            a["status"] = "SLEEPING"
            a["lastMessage"] = "Crisis resolved. Monitoring post-recovery checks."

        # Generate post mortem report data based on scenario
        scenario = SCENARIOS.get(self.active_scenario_id, SCENARIOS["INC-001"])
        
        label_used = scenario.shutdown_label if decision == "SHUTDOWN" else scenario.isolation_label
        
        post_mortem_report = {
            "rootCause": f"Incident triggered by {scenario.description}",
            "timelineAnalysis": f"00:01 Alarm detection -> 00:15 Multi-agent war room setup via Band -> 00:30 Board room debate -> " + (
                f"01:00 Countermeasure executed: {label_used} -> System health restored."
            ),
            "businessImpact": (
                f"Secured all primary assets. Revenue at risk returned to base levels."
            ),
            "complianceReport": f"Regulatory reporting signed off for {scenario.initial_data.get('regulation', 'Internal Security Operations')}.",
            "lessonsLearned": "Ensure MFA is enforced globally. Implement automated micro-segmentation and containment policies.",
            "preventionPlan": "Deploy real-time AI security sentinel across all subnet sectors to monitor and auto-quarantine."
        }

        self.current_state_payload["postMortem"] = post_mortem_report
        self.current_state_payload["simulationRunning"] = False
        self.scenario_state = "RESOLVED"
        
        # Broadcast final state
        await self.broadcast({
            "type": "state_update",
            "payload": self.current_state_payload
        })
        
        # Persist the resolved state
        await self._persist_state()

    def reset_sync(self):
        if self.loop_task:
            self.loop_task.cancel()
            self.loop_task = None
        self.is_running = False
        self.scenario_state = "INITIAL"
        self.current_state_payload = self._get_initial_state()

    async def reset(self):
        self.reset_sync()
        # Clear persisted state
        if self.persistence and self.persistence.is_available:
            await self.persistence.clear_simulation(self.active_scenario_id)
        await self.broadcast({
            "type": "state_update",
            "payload": self.current_state_payload
        })
