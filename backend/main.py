import asyncio
import datetime
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from scenario import ScenarioManager
from persistence import RedisPersistence
from agents import SCENARIOS, ScenarioDefinition, CrisisScenarioStep


# Setup logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="Enterprise Crisis Command Center AI Backend")

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiter ───────────────────────────────────────────────────────────
# Rate limit string (e.g. "5/minute", "10/minute"). Set RATE_LIMIT env var to override.
_rate_limit_str = os.getenv("RATE_LIMIT", "5/minute")
limiter = Limiter(key_func=get_remote_address)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Persistence & Manager ───────────────────────────────────────────────────
persistence = RedisPersistence()
manager = ScenarioManager(persistence=persistence)

# Server start time (set during startup event)
_server_started_at = None


@app.on_event("startup")
async def startup():
    """Initialize persistence and restore state from Redis on server start."""
    global _server_started_at
    _server_started_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    available = await persistence.initialize()
    if not available:
        return

    # Restore dynamic scenario definitions created via webhook
    restored = await persistence.restore_dynamic_scenarios()
    for sid, defn_data in restored.items():
        try:
            scenario_def = ScenarioDefinition(**defn_data)
            SCENARIOS[sid] = scenario_def
            logger.info(f"Restored dynamic scenario {sid} from Redis")
        except Exception as e:
            logger.warning(f"Failed to restore scenario {sid}: {e}")

    # Restore manager state (alerts, active scenario state payload)
    await manager.restore_from_persistence()


@app.on_event("shutdown")
async def shutdown():
    """Clean up Redis connection on server stop."""
    await persistence.close()


# ── API Key Authentication ──────────────────────────────────────────────────

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Dependency that validates the X-API-Key header.
    If API_KEY env var is not set, all requests are allowed (dev mode).
    """
    expected = os.getenv("API_KEY")
    if not expected:
        logger.warning("API_KEY not configured — webhook endpoint accepts all requests")
        return True
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return True

class ExternalAlert(BaseModel):
    source: str
    event_type: str
    severity: str
    title: str
    description: str

    @field_validator("source", "title", "description")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty")
        if len(v) > 500:
            raise ValueError("Field must not exceed 500 characters")
        return v.strip()

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"Severity must be one of {allowed}")
        return upper

def create_dynamic_scenario(alert: ExternalAlert) -> ScenarioDefinition:
    # Generates a dynamic scenario based on the incoming alert parameters
    scenario_id = f"INC-EXT-{datetime.datetime.now().strftime('%M%S')}"
    severity_str = alert.severity.title() if alert.severity else "Critical"
    
    # Define steps
    steps = [
        CrisisScenarioStep(
            step_name="DETECTION",
            risk_score=75,
            revenue_at_risk="$1.5M",
            affected_users=50000,
            nodes_compromised=4,
            active_incidents=1,
            timeline_event={
                "time": "00:01",
                "title": f"ALERT DETECTED via {alert.source}",
                "description": alert.title,
                "module": "ALERTS",
                "severity": alert.severity.lower()
            },
            audit_log={
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                "agent": "Detection_Agent",
                "action": "INGEST_ALERT",
                "details": f"Alert ingested from {alert.source}: {alert.description}"
            },
            agent_update=[
                {"id": "detection", "status": "ACTIVE", "lastMessage": f"Ingested alert from {alert.source}: {alert.title}"},
                {"id": "sec", "status": "THINKING", "lastMessage": "Scanning network layers for indicators of compromise."},
                {"id": "infra", "status": "THINKING", "lastMessage": "Verifying subnet performance metrics."}
            ]
        ),
        CrisisScenarioStep(
            step_name="INVESTIGATION",
            risk_score=88,
            revenue_at_risk="$4.5M",
            affected_users=120000,
            nodes_compromised=18,
            active_incidents=4,
            timeline_event={
                "time": "00:15",
                "title": "THREAT VECTOR CORRELATION",
                "description": f"Security traces indicators across subnets. Payload from {alert.source} matches active attack pattern.",
                "module": "BAND_SDK",
                "severity": "high"
            },
            audit_log={
                "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime("%H:%M:%S"),
                "agent": "Security_Agent",
                "action": "CORRELATION",
                "details": f"Confirmed exfiltration footprint matching alert: {alert.description}"
            },
            agent_update=[
                {"id": "detection", "status": "SLEEPING", "lastMessage": "Alert logged. Sentinel active and monitoring endpoints."},
                {"id": "sec", "status": "ACTIVE", "lastMessage": f"Tracing {alert.event_type} vector. Isolating endpoints."},
                {"id": "infra", "status": "ACTIVE", "lastMessage": "Cloud firewall configs retrieved. Traffic failover queued."}
            ]
        ),
        CrisisScenarioStep(
            step_name="RISK_LEGAL",
            risk_score=95,
            revenue_at_risk="$8.5M",
            affected_users=320000,
            nodes_compromised=48,
            active_incidents=11,
            timeline_event={
                "time": "00:30",
                "title": "REGULATORY TRIGGER",
                "description": f"Compliance officer warns of data privacy trigger under GDPR Art. 33 due to {alert.event_type}.",
                "module": "LEGAL",
                "severity": "critical"
            },
            audit_log={
                "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%H:%M:%S"),
                "agent": "Risk_Agent",
                "action": "LEGAL_AUDIT",
                "details": f"Evaluated impact on EU/US users. Incident requires prompt report."
            },
            agent_update=[
                {"id": "sec", "status": "SLEEPING", "lastMessage": "Exfiltration logs isolated. Traces completed."},
                {"id": "legal", "status": "ACTIVE", "lastMessage": "Regulatory disclosure checklists generated."},
                {"id": "finance", "status": "ACTIVE", "lastMessage": f"Estimating total business impact for {alert.event_type} event."}
            ]
        ),
        CrisisScenarioStep(
            step_name="DEBATE_ACTIVE",
            risk_score=100,
            revenue_at_risk="$12.0M",
            affected_users=500000,
            nodes_compromised=82,
            active_incidents=22,
            timeline_event={
                "time": "00:40",
                "title": "C-SUITE EMERGENCY ALIGNMENT",
                "description": f"CISO, CFO, and CEO debating response plan for {alert.title}.",
                "module": "BOARD",
                "severity": "critical"
            },
            audit_log={
                "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=40)).strftime("%H:%M:%S"),
                "agent": "CEO_ALPHA",
                "action": "INITIATE_VOTE",
                "details": "CEO requests final decision between enterprise lockdown and segment containment."
            },
            agent_update=[
                {"id": "ciso", "status": "THINKING", "lastMessage": f"CISO recommends immediate shutdown to safeguard customer credentials."},
                {"id": "cfo", "status": "THINKING", "lastMessage": "CFO advises segmented defense to keep transaction gateways online."},
                {"id": "ceo", "status": "THINKING", "lastMessage": f"Addressing {alert.title}. Awaiting operator decision."}
            ]
        )
    ]
    
    resolutions = {
        "SHUTDOWN": CrisisScenarioStep(
            step_name="RESOLVED",
            risk_score=15,
            revenue_at_risk="$0",
            affected_users=500000,
            nodes_compromised=0,
            active_incidents=0,
            timeline_event={
                "time": "01:00",
                "title": "EMERGENCY SHUTDOWN EXECUTED",
                "description": f"All services powered down to contain {alert.event_type}.",
                "module": "MITIGATION",
                "severity": "medium"
            },
            audit_log={
                "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=60)).strftime("%H:%M:%S"),
                "agent": "infra",
                "action": "CONTAINMENT",
                "details": f"Successfully mitigated {alert.event_type} using full shutdown."
            }
        ),
        "ISOLATION": CrisisScenarioStep(
            step_name="RESOLVED",
            risk_score=48,
            revenue_at_risk="$2.5M",
            affected_users=500000,
            nodes_compromised=8,
            active_incidents=2,
            timeline_event={
                "time": "01:00",
                "title": "NETWORK SEGMENTATION ACTIVE",
                "description": f"Threat contained to isolated subnet. Core transactions online.",
                "module": "MITIGATION",
                "severity": "high"
            },
            audit_log={
                "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=60)).strftime("%H:%M:%S"),
                "agent": "sec",
                "action": "CONTAINMENT",
                "details": f"Subnet quarantined. Shielding other infrastructure from {alert.event_type} vector."
            }
        )
    }
    
    return ScenarioDefinition(
        id=scenario_id,
        title=alert.title,
        severity=severity_str,
        description=alert.description,
        estimated_impact=f"Simultaneous breach simulated from {alert.source}.",
        agents_involved=[
            "Incident Detection Agent", "Cybersecurity Agent", "Infrastructure Agent",
            "Legal Compliance Agent", "Finance Agent", "Customer Impact Agent",
            "Public Relations Agent", "CEO Agent", "CFO Agent", "CISO Agent"
        ],
        initial_data={
            "incident_id": scenario_id,
            "incident_type": alert.event_type,
            "severity": alert.severity
        },
        shutdown_label="EMERGENCY LOCKDOWN",
        isolation_label="SEGMENT CONTAINMENT",
        steps=steps,
        resolutions=resolutions
    )

@app.post("/api/incident/trigger")
@limiter.limit(_rate_limit_str)
async def trigger_incident(request: Request, alert: ExternalAlert, _auth=Depends(verify_api_key)):
    new_scenario = create_dynamic_scenario(alert)
    SCENARIOS[new_scenario.id] = new_scenario
    
    alert_record = {
        "id": new_scenario.id,
        "timestamp": datetime.datetime.now().isoformat(),
        "source": alert.source,
        "event_type": alert.event_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "status": "Active War Room Spawned"
    }
    manager.alerts_history.insert(0, alert_record)
    
    # Persist to Redis (fire-and-forget — non-blocking)
    asyncio.create_task(persistence.push_alert(alert_record))
    asyncio.create_task(persistence.save_scenario_definition(
        new_scenario.id, new_scenario.model_dump()
    ))
    
    manager.start_simulation(new_scenario.id)
    
    await manager.broadcast({
        "type": "external_alert_received",
        "payload": alert_record
    })
    
    return {"status": "success", "scenario_id": new_scenario.id, "alert": alert_record}

@app.get("/api/incident/alerts")
def get_alerts():
    return manager.alerts_history

@app.head("/")
@app.get("/")
def read_root():
    return {"status": "online", "service": "Crisis Command Center Backend"}


@app.head("/health")
@app.get("/health")
async def health_check():
    """
    Health check endpoint returning system status, Redis connectivity,
    rate limit configuration, and active simulation state.
    """
    # Redis status
    redis_available = persistence.is_available
    redis_info = {
        "available": redis_available,
        "url_configured": bool(persistence._redis_url),
    }

    # Rate limiter info
    rate_limit_info = {
        "configured_limit": _rate_limit_str,
    }

    # Manager / simulation state
    active_scenario = {
        "id": manager.active_scenario_id,
        "state": manager.scenario_state,
        "running": manager.is_running,
        "step_index": manager.current_step_index,
        "decision_made": manager.decision_made,
        "connected_clients": len(manager.active_connections),
        "alerts_history_count": len(manager.alerts_history),
    }

    # Auth info (key existence only — never expose the key itself)
    api_key_configured = bool(os.getenv("API_KEY"))

    return {
        "status": "healthy",
        "service": "Crisis Command Center Backend",
        "version": "1.0.0",
        "redis": redis_info,
        "rate_limit": rate_limit_info,
        "auth": {"api_key_configured": api_key_configured},
        "active_scenario": active_scenario,
        "uptime": {"started_at": _server_started_at},
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time crisis updates.
    Requires ?api_key=<key> query param if API_KEY env var is set (dev mode allows unauthenticated).
    """
    # Authenticate via query parameter
    expected_api_key = os.getenv("API_KEY")
    if expected_api_key:
        provided_key = websocket.query_params.get("api_key", "")
        if not provided_key:
            await websocket.close(code=4001, reason="Missing api_key query parameter")
            logger.warning("WebSocket rejected: missing api_key query param")
            return
        if provided_key != expected_api_key:
            await websocket.close(code=4001, reason="Invalid API key")
            logger.warning(f"WebSocket rejected: invalid API key from {websocket.client}")
            return

    await manager.connect(websocket)
    try:
        while True:
            # Wait for incoming messages from the client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                payload = message.get("payload", {})
                
                logger.info(f"Received WS action: {action}")
                
                if action in ("start_demo", "start_scenario"):
                    scenario_id = payload.get("scenario_id", "INC-001")
                    manager.start_simulation(scenario_id)
                elif action == "submit_decision":
                    decision = payload.get("decision")
                    await manager.submit_decision(decision)
                elif action == "reset":
                    await manager.reset()
            except Exception as e:
                logger.error(f"Error parsing websocket payload: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
