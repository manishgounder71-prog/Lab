import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from band import Agent
from band_agents import CISOBandAdapter, CFOBandAdapter, CEOBandAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_real_band_agents")



async def run_agent(name: str, adapter, agent_id: str, api_key: str):
    logger.info(f"Starting Band Agent: {name} ({agent_id})")
    
    rest_url = os.getenv("BAND_REST_URL", "https://app.band.ai")
    ws_url = os.getenv("BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket")
    
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        rest_url=rest_url,
        ws_url=ws_url
    )
    async with agent:
        await agent.run_forever()


async def main():
    # Retrieve credentials from environment variables
    ciso_id = os.getenv("CISO_AGENT_ID")
    ciso_key = os.getenv("CISO_API_KEY")
    
    cfo_id = os.getenv("CFO_AGENT_ID")
    cfo_key = os.getenv("CFO_API_KEY")
    
    ceo_id = os.getenv("CEO_AGENT_ID")
    ceo_key = os.getenv("CEO_API_KEY")
    
    if not (ciso_id and ciso_key and cfo_id and cfo_key and ceo_id and ceo_key):
        print("=" * 80)
        print("Band of Agents Cloud Runner Configuration")
        print("=" * 80)
        print("To run the agents live on app.band.ai, configure the following environment variables:")
        print("  $env:CISO_AGENT_ID = '...'; $env:CISO_API_KEY = '...'")
        print("  $env:CFO_AGENT_ID = '...'; $env:CFO_API_KEY = '...'")
        print("  $env:CEO_AGENT_ID = '...'; $env:CEO_API_KEY = '...'")
        print("=" * 80)
        return

    ciso_adapter = CISOBandAdapter()
    cfo_adapter = CFOBandAdapter()
    ceo_adapter = CEOBandAdapter()

    # Run all agents in parallel
    await asyncio.gather(
        run_agent("CISO", ciso_adapter, ciso_id, ciso_key),
        run_agent("CFO", cfo_adapter, cfo_id, cfo_key),
        run_agent("CEO", ceo_adapter, ceo_id, ceo_key)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Cloud runner stopped by user.")
