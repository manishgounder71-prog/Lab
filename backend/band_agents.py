import os
import logging
from typing import Any, List, ClassVar
from band import Emit, Capability
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage
from band.core.protocols import AgentToolsProtocol

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


async def call_llm_or_fallback(
    role: str,
    objective: str,
    message: str,
    history: List[str],
    scenario_context: str
) -> str:
    """Call LLM (Gemini or OpenAI) if keys are present, else use fallback logic."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    prompt = f"""You are the {role} in an Enterprise Crisis Command Center war room.
Your core objective/personality is: {objective}.

Scenario context:
{scenario_context}

Recent conversation history:
{history}

Incoming message:
{message}

Respond in character as {role}. Be concise, authoritative, and direct (max 2-3 sentences). Focus on your specific domain concerns."""

    if has_gemini and gemini_key:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_key)
            res = await llm.ainvoke(prompt)
            return res.content.strip()
        except Exception as e:
            logger.error(f"Gemini call failed for {role}: {e}")

    if has_openai and openai_key:
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
            res = await llm.ainvoke(prompt)
            return res.content.strip()
        except Exception as e:
            logger.error(f"OpenAI call failed for {role}: {e}")

    # Heuristic template fallback
    role_lower = role.lower()
    msg_lower = message.lower()
    
    if "ciso" in role_lower:
        if "shutdown" in msg_lower or "decision" in msg_lower or "call" in msg_lower or "vote" in msg_lower:
            return "The exfiltration of Customer PostgreSQL is ongoing. I recommend an immediate database shutdown. The risks of further exfiltration exceed any operational costs."
        return "Containment is my top priority. Tracing active database connection logs and queries. Recommend revoking compromised credentials."
        
    elif "cfo" in role_lower:
        if "shutdown" in msg_lower or "decision" in msg_lower or "call" in msg_lower or "vote" in msg_lower:
            return "Shutting down the database halts all customer checkout processes. That represents -$12M/hr in liquidity. I recommend partial network isolation of Segment G-9."
        return "We must protect the Q3 balance sheet. A full shutdown represents an unacceptable loss; let's attempt subnet isolation instead."
        
    elif "ceo" in role_lower:
        return "We need to act. Operator, please select whether to execute a full database shutdown or attempt network isolation."
        
    elif "threat" in role_lower or "detection" in role_lower:
        return "ALERT: SQL Injection pattern detected on Customer PostgreSQL. Unauthorized queries are originating from external VPN IP."
        
    elif "cyber" in role_lower or "containment" in role_lower:
        return "SQL injection vulnerability leveraged on DB Gateway. Exfiltration rate: 45GB/s."
        
    elif "infra" in role_lower:
        return "Isolating database subnet G-9. Diverting operational API traffic."
        
    elif "legal" in role_lower:
        return "EU region sensitive data involved. GDPR Article 33 triggers a mandatory 72-hour notification limit."
        
    elif "finance" in role_lower:
        return "Revenue risk verified: $4.2M. Transaction conversion down 35%."
        
    elif "telemetry" in role_lower or "churn" in role_lower or "cx" in role_lower:
        return "150,000 active EU customer accounts identified in scope of exposure."

    return f"Standing by to assist from the {role} department. Telemetry monitored."


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

        response = await call_llm_or_fallback(
            role="Chief Information Security Officer Agent",
            objective="Prioritize data security, containment, and immediate shutdown of compromised assets to prevent further leaks.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        await tools.send_message(response)


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

        response = await call_llm_or_fallback(
            role="Chief Financial Risk Strategist",
            objective="Protect revenue flow and business operations. Prioritize partial subnet isolation over complete shutdowns to avoid $12M/hr downtime losses.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        await tools.send_message(response)


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

        response = await call_llm_or_fallback(
            role="Chief Executive Decision Agent",
            objective="Coordinate crisis command votes, align board members, and prompt the operator to make a final SHUTDOWN vs ISOLATION choice.",
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        await tools.send_message(response)


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

        response = await call_llm_or_fallback(
            role=self.role_name,
            objective=self.objective,
            message=msg.content,
            history=history,
            scenario_context=self.scenario_context
        )
        await tools.send_message(response)
