# Crisis Command Center Backend (Band SDK Powered)

This is the backend service for the Enterprise Crisis Command Center, an interactive multi-agent crisis simulation workspace. The backend implements actual agent adapters using the **Band SDK** (`band-sdk`) for agentic collaboration.

---

## Architecture Overview

The backend is structured to support both local interactive runs and live cloud deployments:

1. **Band SDK Agent Adapters (`band_agents.py`)**
   - Implements custom adapters by subclassing `SimpleAdapter` for key roles: `CISOBandAdapter` (CISO), `CFOBandAdapter` (CFO), and `CEOBandAdapter` (CEO).
   - Dynamically calls LLM APIs (Gemini/OpenAI) using LangChain if API keys are configured, falling back to deterministic role Heuristics if offline.
2. **FastAPI Simulator WebSocket (`main.py` & `scenario.py`)**
   - Drives the visual simulation steps (`DETECTION` → `INVESTIGATION` → `RISK_LEGAL` → `DEBATE_ACTIVE` → `RESOLVED`).
   - At the `DEBATE_ACTIVE` step, the backend instantiates the real `SimpleAdapter` classes and executes a live message exchange loop (simulated local room), streaming the generated dialogue live to the Next.js frontend.
3. **Cloud Agent Launcher (`run_real_band_agents.py`)**
   - A direct script that instantiates real `Agent.create(...)` runtimes from the `band` library and registers them live on the [band.ai](https://app.band.ai) platform for production room collaboration.

---

## Quick Start (Local Development)

### 1. Install Dependencies
This project uses `uv` for lightning-fast virtual environment and package management.
```bash
uv sync
```

### 2. Run the Server
Start the FastAPI WebSocket server on port 8000:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Hackathon Deployment (Cloud Mode)

To run the same agent classes live in a chat room on the real [band.ai](https://app.band.ai) platform:

### 1. Set Up Environment Variables
Export your Band Agent IDs and API Keys (and optionally LLM provider keys like `GEMINI_API_KEY` or `OPENAI_API_KEY`):
```powershell
# Windows PowerShell
$env:CISO_AGENT_ID="your-ciso-agent-uuid"
$env:CISO_API_KEY="your-ciso-api-key"
$env:CFO_AGENT_ID="your-cfo-agent-uuid"
$env:CFO_API_KEY="your-cfo-api-key"
$env:CEO_AGENT_ID="your-ceo-agent-uuid"
$env:CEO_API_KEY="your-ceo-api-key"
$env:GEMINI_API_KEY="your-google-gemini-key"
```

### 2. Launch the Cloud Agents
Run the runner script:
```bash
uv run python run_real_band_agents.py
```
This registers the adapters live on the platform. Any messages sent in the active Band room will trigger the adapters to process inputs and coordinate.

---

## Testing

Backend test execution is optimized using configurable step delays, running the entire 147-test suite in **under 2 seconds**:
```bash
uv run pytest
```
