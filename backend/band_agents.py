import os
import random
import logging
import json
import re
from typing import Any, List, ClassVar
try:
    from band import Emit, Capability
    from band.core.simple_adapter import SimpleAdapter
    from band.core.types import PlatformMessage
    from band.core.protocols import AgentToolsProtocol
    _has_band_sdk = True
except ImportError:
    _has_band_sdk = False
    # Stub types for when band-sdk is not installed
    from enum import Enum
    class Emit(Enum):
        EXECUTION = "execution"
    class Capability(Enum):
        MEMORY = "memory"
    class SimpleAdapter:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
        def __init__(self, *args, **kwargs): pass
        def __class_getitem__(cls, item):
            return cls
    class PlatformMessage:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class AgentToolsProtocol:
        pass

logger = logging.getLogger("band_agents")

# Try importing langchain components for live LLM functionality
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    has_gemini = True
except ImportError:
    has_gemini = False

try:
    from langchain_openai import ChatOpenAI
    has_openai = True
except ImportError:
    has_openai = False

# SIMULATE_LLM=1 enables context-aware template responses that vary per scenario
_simulate_llm = os.getenv("SIMULATE_LLM", "1").lower() in ("1", "true", "yes")


# Tool definitions — each agent declares what tools it can invoke
AGENT_TOOLS = {
    "CISO": [
        {"name": "quarantine_server", "description": "Isolate a compromised server from the network immediately", "params": {"server_id": "string", "reason": "string"}},
        {"name": "revoke_credentials", "description": "Revoke access tokens and rotate keys for specified accounts", "params": {"account_ids": "list[string]", "reason": "string"}},
        {"name": "lockdown_segment", "description": "Apply full network lockdown to a subnet segment", "params": {"segment": "string"}},
    ],
    "CFO": [
        {"name": "freeze_transactions", "description": "Temporarily freeze all outbound transactions on a gateway", "params": {"gateway_id": "string", "duration_minutes": "int"}},
        {"name": "escalate_to_risk", "description": "Flag suspicious activity to risk committee for review", "params": {"case_id": "string", "estimated_loss": "string"}},
    ],
    "CEO": [
        {"name": "escalate_to_operator", "description": "Prompt the human operator to make a final decision", "params": {"question": "string", "options": "list[string]"}},
        {"name": "call_board_vote", "description": "Initiate an executive board voting round", "params": {"motion": "string", "quorum": "int"}},
    ],
    "Detection": [
        {"name": "create_alert", "description": "Create a structured security alert with IoC details", "params": {"title": "string", "severity": "string", "indicators": "list[string]"}},
    ],
    "Legal": [
        {"name": "generate_compliance_report", "description": "Generate a regulatory compliance filing", "params": {"regulation": "string", "deadline_hours": "int"}},
    ],
    "default": [
        {"name": "send_notification", "description": "Send a notification to the specified channel", "params": {"channel": "string", "message": "string"}},
    ],
}

# Multiple fallback variants per role — ensures every demo is visibly unique
FALLBACK_VARIANTS: dict = {
    "ciso_decision": [
        "The exfiltration of Customer PostgreSQL is ongoing. I recommend an immediate database shutdown. The risks of further exfiltration exceed any operational costs.",
        "I've traced the active connection pool — 45GB/s is being siphoned to an external IP in Eastern Europe. Shutdown now or we lose the entire customer dataset.",
        "PostgreSQL replication logs show unauthorized COPY TO commands. Every second we delay costs us 45GB of PII. There is no alternative to a full shutdown.",
    ],
    "ciso_general": [
        "Containment is my top priority. Tracing active database connection logs and queries. Recommend revoking compromised credentials.",
        "Scanning network egress points. The breach appears confined to the database subnet but I need verification before signing off on any decision.",
        "I've isolated the compromised database process. Threat signature indicates a known SQL injection variant — CVE-2024-XXXX pattern confirmed.",
    ],
    "cfo_decision": [
        "Shutting down the database halts all customer checkout processes. That represents -$12M/hr in liquidity. I recommend partial network isolation of Segment G-9.",
        "A full shutdown freezes our payment pipeline entirely. Our daily revenue exposure is $50M. Isolation lets us keep 75% of transaction flow alive.",
        "I've run the numbers: $12M per hour of downtime vs $500K additional exfiltration risk under isolation. The financial math favors isolation.",
    ],
    "cfo_general": [
        "We must protect the Q3 balance sheet. A full shutdown represents an unacceptable loss; let's attempt subnet isolation instead.",
        "Our cash reserves can absorb a limited breach but not a 72-hour operational halt. If we can keep 60% of transaction throughput, we survive this quarter.",
        "Revenue at risk verified at $4.2M. Transaction conversion dropped 35% since the breach began. Every minute of full outage widens the gap.",
    ],
    "ceo_decision": [
        "We need to act. Operator, please select whether to execute a full database shutdown or attempt network isolation.",
        "The board is divided. I need you to break the tie, Operator — shutdown severs all risk but halts operations; isolation keeps us running but carries residual breach exposure.",
        "Time is our scarcest resource. Operator, I need your command: do we pull the emergency brake or steer through the storm?",
    ],
    "detection": [
        "ALERT: SQL Injection pattern detected on Customer PostgreSQL. Unauthorized queries originating from external VPN IP 185.220.101.4.",
        "WARNING: Anomalous data transfer volume detected on database port 5432. Traffic pattern matches known exfiltration toolkit signature.",
        "CRITICAL: PostgreSQL audit log shows 47 unauthorized SELECT statements against the customer PII table in the last 90 seconds.",
    ],
    "infra": [
        "Isolating database subnet G-9. Diverting operational API traffic through backup routes.",
        "Network segmentation active on Segment G-9. East-west traffic blocked. DNS routing diverted to secondary nameservers.",
        "Cloud infrastructure team engaged. Spinning up forensic mirror of compromised database volume for analysis.",
    ],
    "legal": [
        "EU region sensitive data involved. GDPR Article 33 triggers a mandatory 72-hour notification limit to the supervisory authority.",
        "This breach involves PII of EU residents. Under GDPR, we must notify the lead authority within 72 hours. The clock started at first detection.",
        "Legal exposure assessment underway. If this is a zero-day vector, our liability caps at 4% of global turnover under Article 83 of GDPR.",
    ],
    "finance": [
        "Revenue risk verified: $4.2M. Transaction conversion down 35% across all active payment gateways.",
        "Financial impact projection: $4.2M direct loss with additional $1.8M in regulatory fine exposure if GDPR timelines are missed.",
        "Auditing transaction logs for signs of payment API abuse. Conversion funnel shows 35% drop in the last 15 minutes alone.",
    ],
    "cx": [
        "150,000 active EU customer accounts identified in scope of exposure. Churn risk projected at 8% if breach is publicly disclosed.",
        "Customer trust metrics dropping sharply. Support ticket volume up 500% in the last 10 minutes. Preparing escalation scripts for call center.",
        "Session abandonment rate spiking. 150K accounts potentially exposed — that's 12% of our total EU customer base.",
    ],
}


def get_fallback_response(role_key: str, message: str, seed: int, scenario_context: str = "", history: list | None = None) -> str:
    """Generate context-aware fallback response using scenario context and debate history.
    When SIMULATE_LLM=1, produces unique responses per session by weaving scenario
    details into template responses instead of using random.choice from static strings."""
    # Mix context hash into seed so different scenarios diverge
    ctx_hash = sum(ord(c) * (i + 1) for i, c in enumerate(scenario_context[:100]))
    seed = seed ^ (ctx_hash & 0x7FFFFFFF)
    role_lower = role_key.lower()
    msg_lower = message.lower()
    rng = random.Random(seed)

    # Extract key terms from scenario context for dynamic response generation
    ctx_words = re.findall(r'\b(\w{5,})\b', scenario_context) if scenario_context else []
    stopwords = {"about", "after", "also", "been", "being", "breach", "data", "detected",
                 "detection", "during", "identified", "impact", "multiple", "other",
                 "potential", "progress", "required", "system", "systems", "their",
                 "ther", "within", "from", "that", "this", "with", "they", "have",
                 "been", "into", "over", "than", "very", "across", "after", "backup",
                 "critical", "customer", "external", "infrastructure", "network"}
    ctx_terms = sorted(set(w for w in ctx_words if w.lower() not in stopwords))[:5]
    ctx_preview = ", ".join(ctx_terms) if ctx_terms else "the active incident"

    # Check if this is a decision call (shutdown/vote related)
    is_decision = any(kw in msg_lower for kw in ("shutdown", "decision", "call", "vote", "act", "resolve", "operator"))

    # Build awareness of what other agents said
    prev_agent_stance = ""
    if history:
        for h in reversed(history[-3:]):
            if "recommend" in h.lower() or "suggest" in h.lower() or "should" in h.lower():
                prev_agent_stance = h
                break

    # ── CISO: Security-first, shutdown advocate ──
    if "ciso" in role_lower:
        if is_decision:
            templates = [
                f"The exfiltration of {ctx_preview} is ongoing. I recommend an immediate shutdown — the risk of further data loss exceeds any operational cost.",
                f"I've traced the active connection. {ctx_preview} is being siphoned to an external IP. Shutdown now or we lose everything.",
                f"Forensic analysis shows unauthorized data transfer. Every second costs us more data. There is no alternative to a full shutdown.",
            ]
        else:
            templates = [
                f"Containment is my priority. Tracing active connections related to {ctx_preview}. Recommend revoking compromised credentials immediately.",
                f"Scanning network egress points. The breach appears focused on {ctx_preview} but I need full verification before signing off.",
                f"I've isolated the compromised process. Threat signature indicates active exploitation of {ctx_preview} infrastructure.",
            ]
        if prev_agent_stance and "financ" in prev_agent_stance.lower():
            templates.append("I hear the financial concerns, but a dollar value cannot replace customer trust. Security must come first — shutdown is the only path.")
        return rng.choice(templates)

    # ── CFO: Business-continuity, isolation advocate ──
    elif "cfo" in role_lower:
        if is_decision:
            templates = [
                f"Shutting down {ctx_preview} halts all customer operations. That represents severe liquidity impact. I recommend partial network isolation instead.",
                f"A full shutdown freezes our payment pipeline entirely. Our daily revenue exposure is massive. Isolation lets us keep critical flows alive.",
                f"I've run the numbers: the cost of downtime vs residual exfiltration risk under isolation. The financial math overwhelmingly favors isolation.",
            ]
        else:
            templates = [
                f"We must protect the balance sheet. A full shutdown of {ctx_preview} represents unacceptable loss. Let's attempt subnet isolation.",
                f"Our cash reserves can absorb a limited breach but not a prolonged operational halt. Keeping 60%+ throughput is essential for Q3.",
                f"Revenue at risk verified. Transaction conversion dropped significantly since the breach on {ctx_preview} began.",
            ]
        if prev_agent_stance and "secur" in prev_agent_stance.lower():
            templates.append("Security concerns are valid, but a full shutdown is the most expensive option. Isolation achieves both containment and continuity.")
        return rng.choice(templates)

    # ── CEO: Decision coordinator ──
    elif "ceo" in role_lower:
        templates = [
            f"We need to act on {ctx_preview}. Operator, please decide: full shutdown or network isolation? The board has laid out both cases.",
            "The board is divided. I need you to break the tie — shutdown severs all risk but halts operations; isolation keeps us running but carries residual exposure.",
            f"Time is our scarcest resource on {ctx_preview}. Operator, I need your command: do we pull the emergency brake or steer through the storm?",
        ]
        if prev_agent_stance:
            templates.append(f"Considering the arguments presented, we need a decisive choice. {prev_agent_stance[:80]}... What is your command, Operator?")
        return rng.choice(templates)

    # ── Detection/Threat ──
    elif "threat" in role_lower or "detection" in role_lower or "sentinel" in role_lower:
        templates = [
            f"ALERT: Unauthorized query pattern detected on {ctx_preview}. Traffic originating from external VPN infrastructure. Immediate investigation required.",
            f"WARNING: Anomalous data transfer volume on {ctx_preview}. Traffic pattern matches known exfiltration toolkit signature.",
            f"CRITICAL: Audit log shows unauthorized SELECT statements against customer PII in {ctx_preview} during the last detection window.",
        ]
        return rng.choice(templates)

    # ── Infra/Operations ──
    elif "infra" in role_lower or "ops" in role_lower or "operation" in role_lower:
        templates = [
            f"Network response for {ctx_preview} is degraded. Preparing to isolate subnet and divert traffic through backup routes.",
            f"Network segmentation ready. East-west traffic on {ctx_preview} can be blocked on your command. DNS routing ready to switch.",
            f"Cloud infrastructure team standing by. Forensic mirror of {ctx_preview} can be spun up for analysis.",
        ]
        return rng.choice(templates)

    # ── Legal/Compliance ──
    elif "legal" in role_lower or "compliance" in role_lower:
        templates = [
            f"EU region sensitive data involved in {ctx_preview}. GDPR Article 33 triggers mandatory 72-hour notification window.",
            f"This breach involves PII. Under GDPR, we must notify the lead authority within 72 hours. The clock started at first detection.",
            f"Legal exposure assessment underway. If this involves {ctx_preview}, our liability could be significant under Article 83 of GDPR.",
        ]
        return rng.choice(templates)

    # ── Finance/Revenue ──
    elif "finance" in role_lower or "revenue" in role_lower:
        templates = [
            f"Revenue risk verified for {ctx_preview}. Transaction conversion dropping across all active payment gateways.",
            f"Financial impact projection escalating. Additional regulatory fine exposure if GDPR timelines on {ctx_preview} are missed.",
            f"Auditing transaction logs for {ctx_preview}. Conversion funnel showing significant drop in the last monitoring window.",
        ]
        return rng.choice(templates)

    # ── CX/Churn/Telemetry ──
    elif "telemetry" in role_lower or "churn" in role_lower or "cx" in role_lower or "customer" in role_lower:
        templates = [
            f"Active customer accounts identified in scope of {ctx_preview}. Churn risk projected if breach is publicly disclosed.",
            f"Customer trust metrics dropping sharply. Support ticket volume spiking. Preparing escalation scripts related to {ctx_preview}.",
            f"Session abandonment rate increasing. Significant customer base potentially exposed through {ctx_preview}.",
        ]
        return rng.choice(templates)

    # ── PR/Communications ──
    elif "pr" in role_lower or "comm" in role_lower or "public" in role_lower:
        templates = [
            f"Preparing crisis statements regarding {ctx_preview}. Recommend immediate proactive disclosure before details leak externally.",
            f"Media monitoring shows chatter about {ctx_preview}. We need a unified message before this reaches mainstream coverage.",
            f"Press hold templates being updated for {ctx_preview}. Recommend board approval before any external communication.",
        ]
        return rng.choice(templates)

    return f"Standing by to assist from the {role_key} department. Analyzing {ctx_preview} telemetry."


def get_reasoning(role_key: str, message: str, seed: int, scenario_context: str = "") -> str:
    ctx_hash = sum(ord(c) * (i + 1) for i, c in enumerate(scenario_context[:100]))
    rng = random.Random(seed + 1 + ctx_hash)
    ctx_words = re.findall(r'\b(\w{5,})\b', scenario_context) if scenario_context else []
    stopwords = {"about", "after", "also", "been", "being", "breach", "data", "detected",
                 "detection", "during", "identified", "impact", "multiple", "other",
                 "potential", "progress", "required", "system", "systems", "their",
                 "ther", "within", "from", "that", "this", "with", "they", "have",
                 "been", "into", "over", "than", "very", "across", "after", "backup",
                 "critical", "customer", "external", "infrastructure", "network"}
    ctx_terms = sorted(set(w for w in ctx_words if w.lower() not in stopwords))
    ctx = ctx_terms[0] if ctx_terms else "current threat vector"
    templates = [
        f"Analyzing incoming telemetry against known threat patterns for {ctx}... correlated with signature database. Decision framework loaded.",
        f"Cross-referencing domain KPIs with scenario impact matrix for {ctx}... risk/reward calculation in progress. Escalation threshold met.",
        f"Evaluating three mitigation paths for {ctx}: (a) full containment, (b) partial isolation, (c) monitored deferral. Weighing operational continuity vs residual risk.",
        f"Ingesting real-time metrics from sub-agents on {ctx}... threat intelligence feed reports active C2 beaconing. Recomputed conviction score.",
        f"Querying historical incident database for similar patterns to {ctx}... 3 matches found. Applying lessons-learned filters to current vector.",
    ]
    return rng.choice(templates)


def get_tool_considered(role_key: str, seed: int, scenario_context: str = "") -> str:
    ctx_hash = sum(ord(c) * (i + 1) for i, c in enumerate(scenario_context[:100]))
    rng = random.Random(seed + 2 + (ctx_hash & 0x7FFFFFFF))
    role_key_lower = role_key.lower()

    if "ciso" in role_key_lower:
        tools = AGENT_TOOLS.get("CISO", AGENT_TOOLS["default"])
    elif "cfo" in role_key_lower:
        tools = AGENT_TOOLS.get("CFO", AGENT_TOOLS["default"])
    elif "ceo" in role_key_lower:
        tools = AGENT_TOOLS.get("CEO", AGENT_TOOLS["default"])
    elif "detection" in role_key_lower or "threat" in role_key_lower:
        tools = AGENT_TOOLS.get("Detection", AGENT_TOOLS["default"])
    elif "legal" in role_key_lower:
        tools = AGENT_TOOLS.get("Legal", AGENT_TOOLS["default"])
    else:
        tools = AGENT_TOOLS["default"]

    chosen = rng.choice(tools)
    return f"TOOL: {chosen['name']} — {chosen['description']}"


async def call_llm_or_fallback(
    role: str,
    objective: str,
    message: str,
    history: List[str],
    scenario_context: str
) -> dict:
    """Call LLM (Gemini or OpenAI) if keys are present, else use fallback logic.
    Returns dict with 'reasoning', 'tools_considered', 'response' keys."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    seed = random.randint(0, 2**31)

    structured_prompt = f"""You are the {role} in an Enterprise Crisis Command Center war room.
Your core objective/personality is: {objective}.

Scenario context:
{scenario_context}

Recent conversation history:
{history}

Incoming message:
{message}

You have access to these tools:
{AGENT_TOOLS}

Respond in character as {role}. You MUST output your response in the following format:
REASONING: <1-2 sentences of your internal analysis and thought process>
TOOLS_CONSIDERED: <the tool you considered using, or "none">
RESPONSE: <your actual response to the war room, max 2-3 sentences>

Be concise, authoritative, and direct. Focus on your specific domain concerns."""

    if has_gemini and gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key, timeout=10.0)
            res = await llm.ainvoke(structured_prompt)
            return _parse_structured_response(res.content.strip(), role, message, seed, scenario_context, history)
        except Exception as e:
            logger.error(f"Gemini call failed for {role}: {e}")

    if has_openai and openai_key:
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key, timeout=10.0, max_retries=1)
            res = await llm.ainvoke(structured_prompt)
            return _parse_structured_response(res.content.strip(), role, message, seed, scenario_context, history)
        except Exception as e:
            logger.error(f"OpenAI call failed for {role}: {e}")

    # Fallback with randomized variants (or SIMULATE_LLM context-aware templates)
    logger.info(f"Using fallback response for {role} (simulate_llm={_simulate_llm})")
    return {
        "reasoning": get_reasoning(role, message, seed, scenario_context),
        "tools_considered": get_tool_considered(role, seed, scenario_context),
        "response": get_fallback_response(role, message, seed, scenario_context, history),
    }


def _parse_structured_response(text: str, role: str, message: str, seed: int, scenario_context: str = "", history: list | None = None) -> dict:
    """Try to parse LLM response into structured format, fallback to basic."""
    reasoning = ""
    tools_considered = ""
    response = text

    for line in text.split("\n"):
        if line.startswith("REASONING:"):
            reasoning = line.replace("REASONING:", "").strip()
        elif line.startswith("TOOLS_CONSIDERED:"):
            tools_considered = line.replace("TOOLS_CONSIDERED:", "").strip()
        elif line.startswith("RESPONSE:"):
            response = line.replace("RESPONSE:", "").strip()

    if not reasoning:
        reasoning = get_reasoning(role, message, seed, scenario_context)
    if not tools_considered:
        tools_considered = get_tool_considered(role, seed, scenario_context)
    if not response:
        response = get_fallback_response(role, message, seed, scenario_context, history)

    return {
        "reasoning": reasoning,
        "tools_considered": tools_considered,
        "response": response,
    }


# Define Band adapters subclassing SimpleAdapter

class CISOBandAdapter(SimpleAdapter[list]):
    SUPPORTED_EMIT: ClassVar[frozenset[Emit]] = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES: ClassVar[frozenset[Capability]] = frozenset({Capability.MEMORY})

    def __init__(self, scenario_context: str = "Active Database Breach"):
        super().__init__()
        self.scenario_context = scenario_context

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history: list,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        if msg.sender_name == self.agent_name:
            return

        result = await call_llm_or_fallback(
            role="Chief Information Security Officer Agent",
            objective="Prioritize data security, containment, and immediate shutdown of compromised assets to prevent further leaks.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        # Send the response with reasoning attached via the tools protocol
        if hasattr(tools, 'send_structured_message'):
            await tools.send_structured_message(result["response"], reasoning=result["reasoning"], tools_considered=result["tools_considered"])
        else:
            await tools.send_message(f"[{result['tools_considered']}] {result['response']}")


class CFOBandAdapter(SimpleAdapter[list]):
    SUPPORTED_EMIT: ClassVar[frozenset[Emit]] = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES: ClassVar[frozenset[Capability]] = frozenset({Capability.MEMORY})

    def __init__(self, scenario_context: str = "Active Database Breach"):
        super().__init__()
        self.scenario_context = scenario_context

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history: list,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        if msg.sender_name == self.agent_name:
            return

        result = await call_llm_or_fallback(
            role="Chief Financial Risk Strategist",
            objective="Protect revenue flow and business operations. Prioritize partial subnet isolation over complete shutdowns to avoid $12M/hr downtime losses.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        if hasattr(tools, 'send_structured_message'):
            await tools.send_structured_message(result["response"], reasoning=result["reasoning"], tools_considered=result["tools_considered"])
        else:
            await tools.send_message(f"[{result['tools_considered']}] {result['response']}")


class CEOBandAdapter(SimpleAdapter[list]):
    SUPPORTED_EMIT: ClassVar[frozenset[Emit]] = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES: ClassVar[frozenset[Capability]] = frozenset({Capability.MEMORY})

    def __init__(self, scenario_context: str = "Active Database Breach"):
        super().__init__()
        self.scenario_context = scenario_context

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history: list,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        if msg.sender_name == self.agent_name:
            return

        result = await call_llm_or_fallback(
            role="Chief Executive Decision Agent",
            objective="Coordinate crisis command votes, align board members, and prompt the operator to make a final SHUTDOWN vs ISOLATION choice.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        if hasattr(tools, 'send_structured_message'):
            await tools.send_structured_message(result["response"], reasoning=result["reasoning"], tools_considered=result["tools_considered"])
        else:
            await tools.send_message(f"[{result['tools_considered']}] {result['response']}")


class OperationalAgentAdapter(SimpleAdapter[list]):
    SUPPORTED_EMIT: ClassVar[frozenset[Emit]] = frozenset({Emit.EXECUTION})
    SUPPORTED_CAPABILITIES: ClassVar[frozenset[Capability]] = frozenset({Capability.MEMORY})

    def __init__(self, role_name: str, objective: str, scenario_context: str = "Active Database Breach"):
        super().__init__()
        self.role_name = role_name
        self.objective = objective
        self.scenario_context = scenario_context

    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history: list,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        if msg.sender_name == self.agent_name:
            return

        result = await call_llm_or_fallback(
            role=self.role_name,
            objective=self.objective,
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        if hasattr(tools, 'send_structured_message'):
            await tools.send_structured_message(result["response"], reasoning=result["reasoning"], tools_considered=result["tools_considered"])
        else:
            await tools.send_message(f"[{result['tools_considered']}] {result['response']}")
