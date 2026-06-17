"""Integration tests for the Redis-backed persistence layer.

Uses fakeredis (in-memory Redis mock) to verify that scenario state,
simulation progress, alert history, and dynamic scenario definitions
survive simulated server restarts.

All tests run without needing a running Docker/Redis instance.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

pytestmark = pytest.mark.asyncio


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def fake_redis_client():
    """Create a fakeredis client that mimics redis.asyncio.Redis."""
    from fakeredis import FakeAsyncRedis
    client = FakeAsyncRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def persistence(fake_redis_client):
    """RedisPersistence instance backed by fakeredis."""
    from persistence import RedisPersistence
    p = RedisPersistence(redis_client=fake_redis_client)
    # initialize() will detect the injected client and set available=True
    await p.initialize()
    assert p.is_available
    yield p
    await p.close()


@pytest_asyncio.fixture
async def manager_with_redis(persistence):
    """ScenarioManager wired up with a real RedisPersistence."""
    from scenario import ScenarioManager
    m = ScenarioManager(persistence=persistence)
    yield m


# ── Sample data builders ────────────────────────────────────────────────────


def make_state_payload(scenario_id: str = "INC-TEST-001", **overrides) -> Dict[str, Any]:
    payload = {
        "scenarioState": "DETECTION",
        "scenarioId": scenario_id,
        "scenarioTitle": "Test Scenario",
        "severity": "CRITICAL",
        "riskScore": 75,
        "revenueAtRisk": "$1.5M",
        "affectedUsers": 50000,
        "nodesCompromised": 4,
        "activeIncidentsCount": 1,
        "regionalStatus": [
            {"name": "US-EAST-1", "status": "OPTIMAL"},
            {"name": "EU-WEST-2", "status": "OPTIMAL"},
        ],
        "timeline": [{"time": "00:01", "title": "Alert", "description": "Test alert", "module": "ALERTS", "severity": "critical"}],
        "agents": [{"id": "detection", "name": "Detection Agent", "role": "IDS", "status": "ACTIVE", "lastMessage": "Monitoring"}],
        "debate": [],
        "auditLogs": [{"id": "1", "timestamp": "00:01", "agent": "Detection", "action": "INGEST", "details": "Test"}],
        "postMortem": None,
        "shutdownLabel": "SHUTDOWN",
        "isolationLabel": "ISOLATION",
        "simulationRunning": True,
    }
    payload.update(overrides)
    return payload


def make_sim_data(**overrides) -> Dict[str, Any]:
    data = {
        "current_step_index": 2,
        "scenario_state": "DETECTION",
        "is_running": True,
        "decision_made": None,
        "active_scenario_id": "INC-TEST-001",
    }
    data.update(overrides)
    return data


def make_alert(alert_id: str = "ALERT-001") -> Dict[str, Any]:
    return {
        "id": alert_id,
        "timestamp": "2026-06-17T12:00:00",
        "source": "Datadog",
        "event_type": "ransomware",
        "severity": "CRITICAL",
        "title": "Ransomware Detected",
        "description": "LockBit 3.0 detected",
        "status": "Active War Room Spawned",
    }


SAMPLE_DEFINITION = {
    "id": "INC-EXT-TEST",
    "title": "External Test Alert",
    "severity": "High",
    "description": "Test description",
    "estimated_impact": "Test impact",
    "agents_involved": ["Incident Detection Agent", "Cybersecurity Agent"],
    "initial_data": {"incident_id": "INC-EXT-TEST", "incident_type": "test", "severity": "High"},
    "shutdown_label": "SHUTDOWN",
    "isolation_label": "ISOLATION",
    "steps": [
        {
            "step_name": "DETECTION",
            "risk_score": 50,
            "revenue_at_risk": "$500K",
            "affected_users": 1000,
            "nodes_compromised": 1,
            "active_incidents": 1,
            "timeline_event": None,
            "audit_log": None,
            "agent_update": None,
            "debate_messages": [],
        }
    ],
    "resolutions": {
        "SHUTDOWN": {
            "step_name": "RESOLVED",
            "risk_score": 10,
            "revenue_at_risk": "$0",
            "affected_users": 0,
            "nodes_compromised": 0,
            "active_incidents": 0,
            "timeline_event": None,
            "audit_log": None,
            "agent_update": None,
            "debate_messages": [],
        },
        "ISOLATION": {
            "step_name": "RESOLVED",
            "risk_score": 30,
            "revenue_at_risk": "$100K",
            "affected_users": 0,
            "nodes_compromised": 0,
            "active_incidents": 0,
            "timeline_event": None,
            "audit_log": None,
            "agent_update": None,
            "debate_messages": [],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Test: RedisPersistence — Direct CRUD
# ═══════════════════════════════════════════════════════════════════════════════


class TestDirectPersistence:
    """Verify that RedisPersistence methods correctly save/load data."""

    async def test_save_and_load_state(self, persistence):
        """State payload should survive save+load cycle."""
        payload = make_state_payload("INC-TEST-001")
        await persistence.save_state("INC-TEST-001", payload)

        loaded = await persistence.load_state("INC-TEST-001")
        assert loaded is not None
        assert loaded["scenarioId"] == "INC-TEST-001"
        assert loaded["riskScore"] == 75
        assert loaded["simulationRunning"] is True
        assert len(loaded["timeline"]) == 1

    async def test_save_and_load_simulation(self, persistence):
        """Simulation progress should survive save+load cycle."""
        sim = make_sim_data()
        await persistence.save_simulation("INC-TEST-001", sim)

        loaded = await persistence.load_simulation("INC-TEST-001")
        assert loaded is not None
        assert loaded["current_step_index"] == 2
        assert loaded["scenario_state"] == "DETECTION"
        assert loaded["active_scenario_id"] == "INC-TEST-001"
        assert loaded["decision_made"] is None

    async def test_get_active_scenario_id(self, persistence):
        """After save_simulation, get_active_scenario_id should return the ID."""
        sim = make_sim_data()
        await persistence.save_simulation("INC-TEST-001", sim)

        active_id = await persistence.get_active_scenario_id()
        assert active_id == "INC-TEST-001"

    async def test_clear_simulation(self, persistence):
        """After clear_simulation, state should be gone."""
        payload = make_state_payload("INC-TEST-001")
        sim = make_sim_data()
        await persistence.save_full_state("INC-TEST-001", payload, sim)
        await persistence.clear_simulation("INC-TEST-001")

        loaded_state = await persistence.load_state("INC-TEST-001")
        loaded_sim = await persistence.load_simulation("INC-TEST-001")
        assert loaded_state is not None  # state persists separately
        assert loaded_sim is None  # sim is cleared

    async def test_save_and_load_state_non_existent(self, persistence):
        """Loading a non-existent scenario should return None."""
        loaded = await persistence.load_state("INC-NONEXISTENT")
        assert loaded is None

    async def test_save_and_load_scenario_definition(self, persistence):
        """Scenario definitions should survive save+load cycle."""
        await persistence.save_scenario_definition("INC-EXT-TEST", SAMPLE_DEFINITION)

        loaded = await persistence.load_scenario_definition("INC-EXT-TEST")
        assert loaded is not None
        assert loaded["id"] == "INC-EXT-TEST"
        assert loaded["title"] == "External Test Alert"

    async def test_restore_dynamic_scenarios_skips_builtin(self, persistence):
        """restore_dynamic_scenarios should skip built-in INC-001..INC-010."""
        await persistence.save_scenario_definition("INC-001", SAMPLE_DEFINITION)
        await persistence.save_scenario_definition("INC-EXT-001", SAMPLE_DEFINITION)

        restored = await persistence.restore_dynamic_scenarios()
        assert "INC-001" not in restored  # built-in, skipped
        assert "INC-EXT-001" in restored  # dynamic, included

    async def test_push_and_load_alerts(self, persistence):
        """Alerts should be pushable and retrievable (most recent first)."""
        alert1 = make_alert("ALERT-001")
        alert2 = make_alert("ALERT-002")
        await persistence.push_alert(alert1)
        await persistence.push_alert(alert2)

        alerts = await persistence.load_alerts()
        assert len(alerts) == 2
        # Most recent first (LPUSH)
        assert alerts[0]["id"] == "ALERT-002"
        assert alerts[1]["id"] == "ALERT-001"

    async def test_alerts_trimmed_to_100(self, persistence):
        """Alert history should trim to 100 entries."""
        for i in range(110):
            await persistence.push_alert(make_alert(f"ALERT-{i:03d}"))

        alerts = await persistence.load_alerts()
        assert len(alerts) == 100

    async def test_save_full_state(self, persistence):
        """save_full_state should persist both state and sim in one call."""
        payload = make_state_payload("INC-TEST-001")
        sim = make_sim_data()
        await persistence.save_full_state("INC-TEST-001", payload, sim)

        loaded_state = await persistence.load_state("INC-TEST-001")
        loaded_sim = await persistence.load_simulation("INC-TEST-001")
        assert loaded_state["scenarioId"] == "INC-TEST-001"
        assert loaded_sim["current_step_index"] == 2

    async def test_restore_state(self, persistence):
        """restore_state should return (id, state_payload, sim_data)."""
        payload = make_state_payload("INC-TEST-001")
        sim = make_sim_data()
        await persistence.save_full_state("INC-TEST-001", payload, sim)

        scenario_id, state_payload, sim_data = await persistence.restore_state()
        assert scenario_id == "INC-TEST-001"
        assert state_payload["riskScore"] == 75
        assert sim_data["current_step_index"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Simulated Restart — State survives new RedisPersistence instances
# ═══════════════════════════════════════════════════════════════════════════════


class TestSimulatedRestart:
    """Simulate a server restart: create new persistence instances that share
    the same underlying fakeredis store via a shared connection."""

    SHARED_SCENARIO_ID = "INC-RESTART-001"

    @pytest_asyncio.fixture
    async def shared_redis(self):
        """A single fakeredis instance shared across 'before restart' and 'after restart' phases."""
        from fakeredis import FakeAsyncRedis
        client = FakeAsyncRedis(decode_responses=True)
        yield client
        await client.aclose()

    @pytest_asyncio.fixture
    async def p1(self, shared_redis):
        """Phase 1 persistence — "before restart"."""
        from persistence import RedisPersistence
        p = RedisPersistence(redis_client=shared_redis)
        await p.initialize()
        yield p
        await p.close()

    @pytest_asyncio.fixture
    async def p2(self, shared_redis):
        """Phase 2 persistence — "after restart" (same fakeredis store)."""
        from persistence import RedisPersistence
        p = RedisPersistence(redis_client=shared_redis)
        await p.initialize()
        yield p
        await p.close()

    async def test_state_survives_restart(self, p1, p2):
        """State saved by p1 should be loadable by p2 (simulated restart)."""
        payload = make_state_payload(self.SHARED_SCENARIO_ID)
        sim = make_sim_data(active_scenario_id=self.SHARED_SCENARIO_ID)
        await p1.save_full_state(self.SHARED_SCENARIO_ID, payload, sim)

        # "Restart" — new persistence instance, same underlying Redis
        scenario_id, state, sim_data = await p2.restore_state()
        assert scenario_id == self.SHARED_SCENARIO_ID
        assert state["riskScore"] == 75
        assert sim_data["current_step_index"] == 2

    async def test_alerts_survive_restart(self, p1, p2):
        """Alert history saved by p1 should be loadable by p2."""
        await p1.push_alert(make_alert("ALERT-R1"))
        await p1.push_alert(make_alert("ALERT-R2"))

        alerts = await p2.load_alerts()
        assert len(alerts) == 2
        assert alerts[0]["id"] == "ALERT-R2"

    async def test_scenario_definitions_survive_restart(self, p1, p2):
        """Dynamic scenario definitions saved by p1 should be loadable by p2."""
        await p1.save_scenario_definition("INC-EXT-RESTART", SAMPLE_DEFINITION)

        restored = await p2.restore_dynamic_scenarios()
        assert "INC-EXT-RESTART" in restored
        assert restored["INC-EXT-RESTART"]["title"] == "External Test Alert"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: ScenarioManager with Persistence
# ═══════════════════════════════════════════════════════════════════════════════


class TestManagerWithPersistence:
    """Verify that ScenarioManager correctly persists and restores its state."""

    async def test_manager_restores_alerts(self, manager_with_redis, persistence):
        """Alerts added to Redis should be restored into manager.alerts_history."""
        alert = make_alert("ALERT-MGR-001")
        await persistence.push_alert(alert)

        await manager_with_redis.restore_from_persistence()
        assert len(manager_with_redis.alerts_history) == 1
        assert manager_with_redis.alerts_history[0]["id"] == "ALERT-MGR-001"

    async def test_manager_restores_scenario_state(self, manager_with_redis, persistence):
        """Saved state payload should be restored into manager.current_state_payload."""
        payload = make_state_payload("INC-001")
        sim = make_sim_data(active_scenario_id="INC-001")
        await persistence.save_full_state("INC-001", payload, sim)

        await manager_with_redis.restore_from_persistence()
        assert manager_with_redis.active_scenario_id == "INC-001"
        assert manager_with_redis.current_state_payload["riskScore"] == 75
        assert manager_with_redis.current_state_payload["scenarioState"] == "DETECTION"
        # Verify simulation is NOT auto-resumed (design decision)
        assert manager_with_redis.is_running is False

    async def test_start_simulation_persists_initial_state(self, manager_with_redis, persistence):
        """Calling start_simulation should persist the initial state to Redis."""
        manager_with_redis.start_simulation("INC-001")
        # Give the fire-and-forget persist task time to execute
        import asyncio
        await asyncio.sleep(0.05)

        loaded_state = await persistence.load_state("INC-001")
        assert loaded_state is not None
        assert loaded_state["scenarioId"] == "INC-001"
        assert loaded_state["simulationRunning"] is True

    async def test_reset_clears_persisted_simulation(self, manager_with_redis, persistence):
        """Calling reset should clear the simulation state from Redis."""
        # First persist some state
        payload = make_state_payload("INC-001")
        sim = make_sim_data(active_scenario_id="INC-001")
        await persistence.save_full_state("INC-001", payload, sim)

        # Restore and reset
        await manager_with_redis.restore_from_persistence()
        await manager_with_redis.reset()

        # Simulation should be cleared
        loaded_sim = await persistence.load_simulation("INC-001")
        assert loaded_sim is None

    async def test_submit_decision_persists_resolved_state(self, manager_with_redis, persistence):
        """After a decision is submitted, the resolved state should be persisted."""
        # Start simulation and fast-forward to DEBATE_ACTIVE
        manager_with_redis.step_delay = 0
        manager_with_redis.start_simulation("INC-001")
        import asyncio

        # Wait for simulation to reach DEBATE_ACTIVE
        for _ in range(20):
            if manager_with_redis.scenario_state == "DEBATE_ACTIVE":
                break
            await asyncio.sleep(0.05)

        assert manager_with_redis.scenario_state == "DEBATE_ACTIVE"

        # Submit decision
        await manager_with_redis.submit_decision("SHUTDOWN")
        await asyncio.sleep(0.05)

        # Verify resolved state is persisted
        loaded_state = await persistence.load_state("INC-001")
        assert loaded_state is not None
        assert loaded_state["scenarioState"] == "RESOLVED"
        assert loaded_state["riskScore"] == 12
        assert loaded_state["postMortem"] is not None
        assert loaded_state["simulationRunning"] is False

    async def test_resolved_state_survives_restart(self, manager_with_redis, persistence):
        """A resolved scenario should be loadable by a fresh manager instance."""
        from scenario import ScenarioManager

        # Persist a resolved state
        payload = make_state_payload("INC-001", scenarioState="RESOLVED", riskScore=12, simulationRunning=False)
        sim = make_sim_data(active_scenario_id="INC-001", is_running=False)
        await persistence.save_full_state("INC-001", payload, sim)

        # "Restart" with a fresh manager
        fresh_manager = ScenarioManager(persistence=persistence)
        await fresh_manager.restore_from_persistence()

        assert fresh_manager.active_scenario_id == "INC-001"
        assert fresh_manager.current_state_payload["scenarioState"] == "RESOLVED"
        assert fresh_manager.current_state_payload["riskScore"] == 12
        assert fresh_manager.is_running is False


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Graceful Fallback
# ═══════════════════════════════════════════════════════════════════════════════


class TestGracefulFallback:
    """Verify that RedisPersistence degrades gracefully when Redis is unavailable."""

    async def test_no_redis_url_returns_false(self):
        """Without a URL, initialize() should return False."""
        from persistence import RedisPersistence

        p = RedisPersistence(redis_url="")
        result = await p.initialize()
        assert result is False
        assert p.is_available is False
        await p.close()

    async def test_unavailable_persistence_is_noop(self):
        """Methods should be safe no-ops when Redis is unavailable."""
        from persistence import RedisPersistence

        p = RedisPersistence(redis_url="")
        await p.initialize()

        # None of these should raise
        await p.save_state("INC-001", {"test": "data"})
        result = await p.load_state("INC-001")
        assert result is None

        await p.save_full_state("INC-001", {"test": "data"}, {"step": 1})
        sid, state, sim = await p.restore_state()
        assert sid is None
        assert state is None
        assert sim is None

        await p.push_alert(make_alert())
        alerts = await p.load_alerts()
        assert alerts == []

        await p.clear_simulation("INC-001")
        await p.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_large_state_payload(self, persistence):
        """Large state payloads should survive save/load."""
        large_payload = make_state_payload(
            "INC-LARGE",
            timeline=[{"time": f"{i:02d}:00", "title": f"Event {i}", "description": "x" * 100, "module": "TEST", "severity": "low"} for i in range(500)],
        )
        await persistence.save_state("INC-LARGE", large_payload)
        loaded = await persistence.load_state("INC-LARGE")
        assert loaded is not None
        assert len(loaded["timeline"]) == 500

    async def test_special_characters_in_data(self, persistence):
        """Special characters and unicode should survive save/load."""
        payload = make_state_payload(
            "INC-ÜNICØDE",
            scenarioTitle="🔥 Multi-Crisis: 你好 & こんにちは! ${{exec}}'\"`;",
        )
        await persistence.save_state("INC-ÜNICØDE", payload)
        loaded = await persistence.load_state("INC-ÜNICØDE")
        assert loaded is not None
        assert "🔥" in loaded["scenarioTitle"]
        assert "你好" in loaded["scenarioTitle"]

    async def test_rapid_save_load_cycle(self, persistence):
        """Rapid consecutive saves should not lose data."""
        for i in range(50):
            payload = make_state_payload(f"INC-RAPID-{i:03d}", riskScore=i)
            await persistence.save_state(f"INC-RAPID-{i:03d}", payload)

        for i in range(50):
            loaded = await persistence.load_state(f"INC-RAPID-{i:03d}")
            assert loaded is not None
            assert loaded["riskScore"] == i

    async def test_empty_alerts_list(self, persistence):
        """Loading alerts when none exist should return empty list."""
        alerts = await persistence.load_alerts()
        assert alerts == []

    async def test_scenario_definition_roundtrip_through_agents(self, persistence):
        """A scenario definition saved via model_dump() should be reconstructable by ScenarioDefinition."""
        from agents import ScenarioDefinition

        # Simulate what main.py startup does
        await persistence.save_scenario_definition("INC-EXT-ROUNDTRIP", SAMPLE_DEFINITION)
        loaded = await persistence.load_scenario_definition("INC-EXT-ROUNDTRIP")
        reconstructed = ScenarioDefinition(**loaded)
        # The ID comes from the definition data itself, not the Redis key
        assert reconstructed.id == SAMPLE_DEFINITION["id"]
        assert reconstructed.title == SAMPLE_DEFINITION["title"]
        assert len(reconstructed.steps) == len(SAMPLE_DEFINITION["steps"])
