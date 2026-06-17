"""
Redis-backed persistence for the Crisis Command Center backend.

Persists scenario state, simulation progress, alert history, and dynamic
scenario definitions so that the system survives server restarts.

Gracefully falls back to no-op mode if Redis is not available
(allows local development without a running Redis instance).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("persistence")

# Key prefixes
KEY_SCENARIO_STATE = "scenario:{id}:state"
KEY_SIMULATION = "scenario:{id}:sim"
KEY_SCENARIO_DEF = "scenario:{id}:definition"
KEY_ALERTS = "alerts_history"
KEY_SCENARIO_IDS = "scenario_ids"
KEY_ACTIVE_SCENARIO = "active_scenario_id"


class RedisPersistence:
    """Persistence layer backed by Redis. Falls back to no-op if unavailable."""

    def __init__(self, redis_url: Optional[str] = None, redis_client=None):
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")
        self._redis = redis_client
        self._available = redis_client is not None
        self._client_injected = redis_client is not None

    async def initialize(self) -> bool:
        """Connect to Redis. Returns True if connected, False if fallback."""
        # If a test client was injected, it's already connected
        if self._client_injected and self._redis is not None:
            self._available = True
            return True

        if not self._redis_url:
            logger.warning("REDIS_URL not set — persistence disabled (in-memory only)")
            return False

        try:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            # Ping to verify connectivity
            await self._redis.ping()
            self._available = True
            logger.info(f"Connected to Redis at {self._redis_url}")
            return True
        except Exception as e:
            logger.warning(f"Redis unavailable at {self._redis_url} — {e}. Running in-memory only.")
            self._redis = None
            self._available = False
            return False

    async def close(self):
        """Close the Redis connection."""
        if self._redis and not self._client_injected:
            await self._redis.aclose()
            self._redis = None
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    # ── Scenario State ─────────────────────────────────────────────────────

    async def save_state(self, scenario_id: str, state_payload: Dict[str, Any]):
        """Persist a scenario's full state payload."""
        if not self._available:
            return
        key = KEY_SCENARIO_STATE.format(id=scenario_id)
        await self._redis.set(key, json.dumps(state_payload, default=str))

    async def load_state(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Load a scenario's state payload, or None."""
        if not self._available:
            return None
        key = KEY_SCENARIO_STATE.format(id=scenario_id)
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    # ── Simulation Progress ────────────────────────────────────────────────

    async def save_simulation(self, scenario_id: str, sim_data: Dict[str, Any]):
        """Persist simulation progress (step index, running flag, etc.)."""
        if not self._available:
            return
        key = KEY_SIMULATION.format(id=scenario_id)
        await self._redis.set(key, json.dumps(sim_data, default=str))
        # Also track this as the active scenario
        await self._redis.set(KEY_ACTIVE_SCENARIO, scenario_id)

    async def load_simulation(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Load simulation progress, or None."""
        if not self._available:
            return None
        key = KEY_SIMULATION.format(id=scenario_id)
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def clear_simulation(self, scenario_id: str):
        """Remove simulation progress (on reset)."""
        if not self._available:
            return
        key = KEY_SIMULATION.format(id=scenario_id)
        await self._redis.delete(key)

    async def get_active_scenario_id(self) -> Optional[str]:
        """Get the ID of the last active scenario."""
        if not self._available:
            return None
        return await self._redis.get(KEY_ACTIVE_SCENARIO)

    # ── Scenario Definitions (for dynamic scenarios created via webhook) ───

    async def save_scenario_definition(self, scenario_id: str, definition: Dict[str, Any]):
        """Persist a ScenarioDefinition so it survives restarts."""
        if not self._available:
            return
        key = KEY_SCENARIO_DEF.format(id=scenario_id)
        await self._redis.set(key, json.dumps(definition, default=str))
        # Add to set of known scenario IDs
        await self._redis.sadd(KEY_SCENARIO_IDS, scenario_id)

    async def load_scenario_definition(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Load a persisted ScenarioDefinition, or None."""
        if not self._available:
            return None
        key = KEY_SCENARIO_DEF.format(id=scenario_id)
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def get_all_scenario_ids(self) -> List[str]:
        """Get all scenario IDs that have been persisted."""
        if not self._available:
            return []
        return list(await self._redis.smembers(KEY_SCENARIO_IDS) or [])

    # ── Alert History ──────────────────────────────────────────────────────

    async def push_alert(self, alert: Dict[str, Any]):
        """Push an alert to the front of the history list."""
        if not self._available:
            return
        await self._redis.lpush(KEY_ALERTS, json.dumps(alert, default=str))
        # Keep only the latest 100 alerts
        await self._redis.ltrim(KEY_ALERTS, 0, 99)

    async def load_alerts(self) -> List[Dict[str, Any]]:
        """Load all persisted alerts (most recent first)."""
        if not self._available:
            return []
        data = await self._redis.lrange(KEY_ALERTS, 0, -1)
        if data:
            return [json.loads(item) for item in data]
        return []

    # ── Full State Restoration ─────────────────────────────────────────────

    async def save_full_state(self, scenario_id: str, state_payload: Dict[str, Any],
                              sim_data: Dict[str, Any]):
        """Convenience: save state + simulation in one call."""
        if not self._available:
            return
        await self.save_state(scenario_id, state_payload)
        await self.save_simulation(scenario_id, sim_data)

    async def restore_state(self) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Restore the full application state on startup.

        Returns (active_scenario_id, state_payload, sim_data) or (None, None, None).
        """
        if not self._available:
            return None, None, None

        scenario_id = await self.get_active_scenario_id()
        if not scenario_id:
            return None, None, None

        state = await self.load_state(scenario_id)
        sim = await self.load_simulation(scenario_id)
        return scenario_id, state, sim

    async def restore_dynamic_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Restore all dynamic scenario definitions created via the webhook."""
        if not self._available:
            return {}
        ids = await self.get_all_scenario_ids()
        scenarios = {}
        for sid in ids:
            # Skip built-in scenarios (INC-001 through INC-010)
            if sid.startswith("INC-") and len(sid) == 7:
                continue
            defn = await self.load_scenario_definition(sid)
            if defn:
                scenarios[sid] = defn
        return scenarios
