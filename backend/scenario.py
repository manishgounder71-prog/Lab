import asyncio
import json
import logging
import datetime
from typing import Set, Dict, Any, List
from fastapi import WebSocket
from agents import SCENARIOS, ALL_AGENTS, get_resolution_step

# Band SDK integration imports — adapter classes and type stubs
try:
    from band_agents import CISOBandAdapter, CFOBandAdapter, CEOBandAdapter
    _has_band_adapters = True
except ImportError:
    _has_band_adapters = False
    CISOBandAdapter = CFOBandAdapter = CEOBandAdapter = object

try:
    from band.core.types import PlatformMessage
    from band.core.protocols import AgentToolsProtocol
except ImportError:
    class PlatformMessage:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class AgentToolsProtocol:
        pass

# Try importing real Band SDK tools for production use
try:
    from band.tools import RoomTools
    _has_real_band_sdk = True
except ImportError:
    _has_real_band_sdk = False

logger = logging.getLogger("scenario")


class MockAgentTools:
    """Enhanced SDK simulation with real Band room behavior.
    Tracks participants, peer discovery, room state, and supports structured messages with reasoning."""

    # Shared state across all instances
    _rooms: dict = {}
    _room_participants: dict = {}
    _peers_registry: dict = {}

    def __init__(self, sender_name: str, debate_list: list):
        self.sender_name = sender_name
        self.debate_list = debate_list
        self._participants = []
        self._current_room = "room"
        # Register this agent in the global peer registry
        MockAgentTools._peers_registry[sender_name] = {
            "name": sender_name,
            "type": "agent",
            "status": "online",
            "capabilities": ["chat", "reasoning", "tool_use"],
        }

    async def send_structured_message(self, content: str, reasoning: str = "", tools_considered: str = "") -> None:
        """Send a message with attached reasoning and tool usage context."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        role = "CEO" if "CEO" in self.sender_name else ("CISO" if "CISO" in self.sender_name else "CFO")
        sentiment = "critical" if role == "CISO" else ("alert" if role == "CFO" else "neutral")
        
        self.debate_list.append({
            "sender": self.sender_name,
            "role": role,
            "timestamp": timestamp,
            "content": content,
            "sentiment": sentiment,
            "reasoning": reasoning,
            "tools_considered": tools_considered,
        })
        # Also track message in room
        if self._current_room:
            if self._current_room not in MockAgentTools._rooms:
                MockAgentTools._rooms[self._current_room] = []
            MockAgentTools._rooms[self._current_room].append({
                "sender": self.sender_name,
                "content": content,
                "timestamp": timestamp,
            })

    async def send_message(self, content: str, mentions=None) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        role = "CEO" if "CEO" in self.sender_name else ("CISO" if "CISO" in self.sender_name else "CFO")
        sentiment = "critical" if role == "CISO" else ("alert" if role == "CFO" else "neutral")
        
        self.debate_list.append({
            "sender": self.sender_name,
            "role": role,
            "timestamp": timestamp,
            "content": content,
            "sentiment": sentiment,
        })
        if self._current_room:
            if self._current_room not in MockAgentTools._rooms:
                MockAgentTools._rooms[self._current_room] = []
            MockAgentTools._rooms[self._current_room].append({
                "sender": self.sender_name,
                "content": content,
                "timestamp": timestamp,
            })

    async def send_event(self, content: str, message_type: str, metadata=None) -> None:
        logger.info(f"[MockAgentTools] Event from {self.sender_name}: {message_type} - {content}")

    async def add_participant(self, identifier: str, role: str = "member") -> None:
        if identifier not in self._participants:
            self._participants.append(identifier)
        if self._current_room:
            if self._current_room not in MockAgentTools._room_participants:
                MockAgentTools._room_participants[self._current_room] = []
            if identifier not in MockAgentTools._room_participants[self._current_room]:
                MockAgentTools._room_participants[self._current_room].append(identifier)
        # Register in peer registry
        MockAgentTools._peers_registry[identifier] = {
            "name": identifier,
            "type": "agent" if identifier != "operator" else "user",
            "status": "online",
            "capabilities": ["chat"],
        }

    async def remove_participant(self, identifier: str) -> None:
        self._participants = [p for p in self._participants if p != identifier]
        if self._current_room and self._current_room in MockAgentTools._room_participants:
            MockAgentTools._room_participants[self._current_room] = [
                p for p in MockAgentTools._room_participants[self._current_room] if p != identifier
            ]

    @property
    def participants(self) -> list:
        return self._participants

    async def get_participants(self) -> list:
        # Return current participants plus anyone in this room
        room_p = MockAgentTools._room_participants.get(self._current_room, [])
        combined = list(set(self._participants + room_p))
        return [{"identifier": p, "role": "member"} for p in combined]

    async def lookup_peers(self, page: int = 1, page_size: int = 50) -> list:
        """Real Band SDK peer discovery — returns all registered agents in the cluster."""
        all_peers = list(MockAgentTools._peers_registry.values())
        start = (page - 1) * page_size
        end = start + page_size
        return all_peers[start:end]

    async def create_chatroom(self, task_id: str | None = None) -> str:
        room_id = f"room_{task_id or 'default'}_{datetime.datetime.now().timestamp()}"
        MockAgentTools._rooms[room_id] = []
        MockAgentTools._room_participants[room_id] = []
        self._current_room = room_id
        logger.info(f"[MockAgentTools] Room created: {room_id}")
        return room_id


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
        self.active_adapters: Dict[str, Any] = {}
        self.debate_rounds = 2
        self.debate_step_delay = 1.0
        self.operator_input_enabled = False

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
            "simulationRunning": False,
            "decisionMatrix": [
                {"vector": "Security Risk", "shutdown_score": 95, "isolate_score": 30,
                 "shutdown_note": "MINIMAL RESIDUAL RISK", "isolate_note": "CRITICAL SECONDARY VECTORS"},
                {"vector": "Revenue Impact", "shutdown_score": 10, "isolate_score": 85,
                 "shutdown_note": "MAXIMUM (EST: $4.2M)", "isolate_note": "MINIMAL (EST: $500K)"},
                {"vector": "Recovery Window", "shutdown_score": 30, "isolate_score": 90,
                 "shutdown_note": "48 - 72 Hours (System boot cycle)", "isolate_note": "2 - 6 Hours (Patch rollout)"},
                {"vector": "Compliance Rating", "shutdown_score": 95, "isolate_score": 40,
                 "shutdown_note": "Compliance fully secured", "isolate_note": "Ongoing breach window"}
            ],
            "aiRecommendation": "SHUTDOWN",
            "aiConfidence": 72
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
                    adapters = {
                        "CISO_SHIELD": CISOBandAdapter(scenario_context=scenario.description),
                        "CFO_QUANT": CFOBandAdapter(scenario_context=scenario.description),
                        "CEO_ALPHA": CEOBandAdapter(scenario_context=scenario.description),
                    }
                    for name, adapter in adapters.items():
                        adapter.agent_name = name
                    self.active_adapters = adapters
                    self.operator_input_enabled = True

                    debate_list = []
                    system_prompt = (
                        f"Incident {self.active_scenario_id} ({scenario.title}): {scenario.description}. "
                        f"We need an immediate decision. Each executive should analyze from "
                        f"their domain expertise and provide a clear recommendation."
                    )

                    for round_num in range(self.debate_rounds):
                        for name, adapter in adapters.items():
                            if round_num == 0:
                                content = system_prompt
                                sender_name = "System"
                            else:
                                last_diff = None
                                for m in reversed(debate_list):
                                    if m["sender"] != name:
                                        last_diff = m
                                        break
                                if not last_diff:
                                    continue
                                content = last_diff["content"]
                                sender_name = last_diff["sender"]

                            msg = PlatformMessage(
                                id=f"msg_{round_num}_{name}", room_id="room",
                                content=content,
                                sender_id=sender_name.lower(), sender_type="agent",
                                sender_name=sender_name,
                                message_type="chat", metadata=None,
                                created_at=datetime.datetime.now()
                            )
                            tools = MockAgentTools(name, debate_list)
                            history = [f"[{d['sender']}]: {d['content']}" for d in debate_list]
                            await adapter.on_message(
                                msg, tools, history.copy(), None, None,
                                is_session_bootstrap=(round_num == 0), room_id="room"
                            )
                            self.current_state_payload["debate"] = debate_list.copy()
                            await self.broadcast({
                                "type": "state_update",
                                "payload": self.current_state_payload
                            })
                            await asyncio.sleep(self.debate_step_delay)

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

    async def inject_operator_message(self, content: str):
        if not self.operator_input_enabled or not self.active_adapters:
            return
        debate_list = self.current_state_payload.get("debate", [])
        operator_msg = {
            "sender": "OPERATOR_01",
            "role": "Operator",
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "content": content,
            "sentiment": "neutral"
        }
        debate_list.append(operator_msg)
        self.current_state_payload["debate"] = debate_list
        await self.broadcast({
            "type": "state_update",
            "payload": self.current_state_payload
        })
        for name, adapter in self.active_adapters.items():
            msg = PlatformMessage(
                id=f"op_{datetime.datetime.now().timestamp()}",
                room_id="room", content=content,
                sender_id="operator", sender_type="user",
                sender_name="OPERATOR_01",
                message_type="chat", metadata=None,
                created_at=datetime.datetime.now()
            )
            tools = MockAgentTools(name, debate_list)
            history = [f"[{d['sender']}]: {d['content']}" for d in debate_list]
            await adapter.on_message(
                msg, tools, history, None, None,
                is_session_bootstrap=False, room_id="room"
            )
            self.current_state_payload["debate"] = debate_list
            await self.broadcast({
                "type": "state_update",
                "payload": self.current_state_payload
            })
            await asyncio.sleep(1.5)

    async def _generate_decision_matrix(self, scenario, debate_history: list) -> list:
        default_matrix = [
            {"vector": "Security Risk", "shutdown_score": 95, "isolate_score": 30,
             "shutdown_note": "MINIMAL RESIDUAL RISK", "isolate_note": "CRITICAL SECONDARY VECTORS"},
            {"vector": "Revenue Impact", "shutdown_score": 10, "isolate_score": 85,
             "shutdown_note": f"MAXIMUM (EST: {scenario.resolutions.get('SHUTDOWN', scenario.steps[-1]).revenue_at_risk if hasattr(scenario, 'resolutions') else scenario.steps[-1].revenue_at_risk})",
             "isolate_note": f"MINIMAL (EST: {scenario.resolutions.get('ISOLATION', scenario.steps[-1]).revenue_at_risk if hasattr(scenario, 'resolutions') else scenario.steps[-1].revenue_at_risk})"},
            {"vector": "Recovery Window", "shutdown_score": 30, "isolate_score": 90,
             "shutdown_note": "48 - 72 Hours (System boot cycle)", "isolate_note": "2 - 6 Hours (Patch rollout)"},
            {"vector": "Compliance Rating", "shutdown_score": 95, "isolate_score": 40,
             "shutdown_note": "Compliance fully secured", "isolate_note": "Ongoing breach window"},
        ]
        debate_text = "\n".join([f"[{m['sender']}]: {m['content']}" for m in debate_history[-20:]])
        prompt = f"""Based on this crisis debate, generate a JSON decision matrix comparing two options.
Scenario: {scenario.title} — {scenario.description}
Debate transcript excerpt:
{debate_text}

Return ONLY valid JSON with this exact structure (no markdown, no code fences):
{{"vectors": [{{"name": str, "shutdown_score": int, "isolate_score": int, "shutdown_note": str, "isolate_note": str}}], "ai_recommendation": "SHUTDOWN" or "ISOLATION", "confidence": int}}
Scores 0-100. Notes 1-2 words each."""
        from band_agents import call_llm_or_fallback
        result = await call_llm_or_fallback("System", "Analyst", prompt, [], scenario.description)
        raw = result.get("response", "")
        try:
            import json as _json
            parsed_result = _json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
            if "vectors" in parsed_result:
                self.current_state_payload["decisionMatrix"] = parsed_result.get("vectors", default_matrix)
                self.current_state_payload["aiRecommendation"] = parsed_result.get("ai_recommendation", "SHUTDOWN")
                self.current_state_payload["aiConfidence"] = parsed_result.get("confidence", 72)
                return parsed_result["vectors"]
        except Exception:
            pass
        self.current_state_payload["decisionMatrix"] = default_matrix
        self.current_state_payload["aiRecommendation"] = "SHUTDOWN"
        self.current_state_payload["aiConfidence"] = 72
        return default_matrix

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
        debate_history = self.current_state_payload.get("debate", [])
        debate_text = "\n".join([f"[{m['sender']}]: {m['content']}" for m in debate_history[-15:]])
        
        post_mortem_prompt = f"""Generate a post-mortem report for this resolved crisis.
Scenario: {scenario.title} — {scenario.description}
Decision taken: {decision} ({label_used})

Return ONLY valid JSON with these fields: rootCause, timelineAnalysis, businessImpact, complianceReport, lessonsLearned, preventionPlan
Each field is a 1-2 sentence string. No markdown, no code fences."""
        
        post_mortem_report = {
            "rootCause": f"Incident triggered by {scenario.description}",
            "timelineAnalysis": f"00:01 Alarm detection -> 00:15 Multi-agent war room -> 00:30 Board debate -> 01:00 {label_used} executed.",
            "businessImpact": "Secured all primary assets. Revenue at risk returned to base levels.",
            "complianceReport": "Regulatory reporting signed off.",
            "lessonsLearned": "Ensure MFA is enforced globally. Implement automated micro-segmentation.",
            "preventionPlan": "Deploy real-time AI security sentinel across all subnet sectors."
        }
        try:
            from band_agents import call_llm_or_fallback
            result_pm = await call_llm_or_fallback("System", "Analyst", post_mortem_prompt, [], scenario.description)
            raw_pm = result_pm.get("response", "")
            import json as _json
            parsed = _json.loads(raw_pm.strip().removeprefix("```json").removesuffix("```").strip())
            if all(k in parsed for k in ("rootCause", "timelineAnalysis")):
                post_mortem_report = parsed
        except Exception:
            pass

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
        self.active_adapters = {}
        self.operator_input_enabled = False

    async def reset(self):
        self.reset_sync()
        # Clear persisted state
        if self.persistence and self.persistence.is_available:
            await self.persistence.clear_simulation(self.active_scenario_id)
        await self.broadcast({
            "type": "state_update",
            "payload": self.current_state_payload
        })
