"""Tests for ScenarioManager — initialization, simulation lifecycle, and decision flow."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from scenario import ScenarioManager
from agents import SCENARIOS


@pytest.fixture
def manager():
    """Create a fresh ScenarioManager for each test with step_delay set to 0."""
    m = ScenarioManager()
    m.step_delay = 0
    return m


class TestInitialization:
    """Verify ScenarioManager initial state."""

    def test_initial_state_values(self, manager):
        assert manager.scenario_state == "INITIAL"
        assert manager.is_running is False
        assert manager.current_step_index == -1
        assert manager.active_scenario_id == "INC-001"
        assert manager.decision_made is None
        assert manager.loop_task is None

    def test_no_active_connections_on_init(self, manager):
        assert len(manager.active_connections) == 0

    def test_initial_state_payload_structure(self, manager):
        payload = manager.current_state_payload
        assert payload["scenarioState"] == "INITIAL"
        assert payload["simulationRunning"] is False
        assert payload["riskScore"] == 0
        assert payload["revenueAtRisk"] == "$0"
        assert payload["affectedUsers"] == 0
        assert payload["nodesCompromised"] == 0
        assert payload["activeIncidentsCount"] == 0
        assert payload["timeline"] == []
        assert payload["debate"] == []
        assert payload["auditLogs"] == []
        assert payload["postMortem"] is None
        assert payload["scenarioId"] == "INC-001"

    def test_initial_regional_status(self, manager):
        regions = manager.current_state_payload["regionalStatus"]
        assert len(regions) == 4
        for region in regions:
            assert region["status"] == "OPTIMAL"

    def test_initial_agents_are_idle(self, manager):
        for agent in manager.current_state_payload["agents"]:
            assert agent["status"] == "IDLE"

    def test_initial_state_has_correct_agents_for_inc001(self, manager):
        """INC-001 should have 10 agents involved."""
        agents = manager.current_state_payload["agents"]
        assert len(agents) == 10

    def test_get_initial_state_for_different_scenario(self):
        """_get_initial_state should respect the active_scenario_id."""
        m = ScenarioManager()
        m.active_scenario_id = "INC-003"
        payload = m._get_initial_state()
        assert payload["scenarioTitle"] == "Enterprise Ransomware Incident"
        assert payload["shutdownLabel"] == "REBUILD BACKUPS"
        assert payload["isolationLabel"] == "PAY THE RANSOM"


class TestConnectionManagement:
    """Verify WebSocket connection tracking."""

    @pytest.mark.asyncio
    async def test_connect_adds_connection(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)
        assert mock_ws in manager.active_connections
        mock_ws.send_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_sends_initial_state(self, manager):
        mock_ws = AsyncMock()
        await manager.connect(mock_ws)
        # Verify state_update message was sent
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "state_update"
        assert call_args["payload"]["scenarioState"] == "INITIAL"

    def test_disconnect_removes_connection(self, manager):
        mock_ws = MagicMock()
        manager.active_connections.add(mock_ws)
        manager.disconnect(mock_ws)
        assert mock_ws not in manager.active_connections

    def test_disconnect_nonexistent_does_not_error(self, manager):
        """Disconnecting a connection that isn't tracked should not raise."""
        manager.disconnect(MagicMock())  # Should not raise

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, manager):
        ws1, ws2 = AsyncMock(), AsyncMock()
        await manager.connect(ws1)
        await manager.connect(ws2)
        assert len(manager.active_connections) == 2

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self, manager):
        ws1, ws2 = AsyncMock(), AsyncMock()
        ws1.send_json = AsyncMock()
        ws2.send_json = AsyncMock()
        manager.active_connections.add(ws1)
        manager.active_connections.add(ws2)

        await manager.broadcast({"type": "test", "payload": {}})

        ws1.send_json.assert_awaited_once_with({"type": "test", "payload": {}})
        ws2.send_json.assert_awaited_once_with({"type": "test", "payload": {}})

    @pytest.mark.asyncio
    async def test_broadcast_handles_dead_connections(self, manager):
        dead_ws = MagicMock()
        dead_ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        alive_ws = AsyncMock()
        alive_ws.send_json = AsyncMock()

        manager.active_connections.add(dead_ws)
        manager.active_connections.add(alive_ws)

        await manager.broadcast({"type": "test"})

        # Dead connection should be removed
        assert dead_ws not in manager.active_connections
        assert alive_ws in manager.active_connections


class TestSimulationLifecycle:
    """Verify simulation start, progression, and cancellation."""

    @pytest.mark.asyncio
    async def test_start_simulation_sets_running(self, manager):
        with patch.object(manager, "_run_loop", new_callable=AsyncMock):
            manager.start_simulation("INC-001")
            assert manager.is_running is True
            assert manager.current_step_index == 0
            assert manager.decision_made is None

    @pytest.mark.asyncio
    async def test_start_simulation_sets_simulation_running_flag(self, manager):
        with patch.object(manager, "_run_loop", new_callable=AsyncMock):
            manager.start_simulation("INC-001")
            assert manager.current_state_payload["simulationRunning"] is True

    @pytest.mark.asyncio
    async def test_start_simulation_with_different_scenario(self, manager):
        with patch.object(manager, "_run_loop", new_callable=AsyncMock):
            manager.start_simulation("INC-010")
            assert manager.active_scenario_id == "INC-010"
            assert manager.current_state_payload["scenarioTitle"] == "Enterprise Perfect Storm"

    @pytest.mark.asyncio
    async def test_restart_cancels_previous_loop(self, manager):
        mock_task = MagicMock()
        manager.loop_task = mock_task
        with patch.object(manager, "_run_loop", new_callable=AsyncMock):
            manager.start_simulation("INC-001")
            mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_restores_initial_state(self, manager):
        # Start simulation
        with patch.object(manager, "_run_loop", new_callable=AsyncMock):
            manager.start_simulation("INC-001")
            manager.scenario_state = "DETECTION"

        # Reset
        await manager.reset()

        assert manager.is_running is False
        assert manager.scenario_state == "INITIAL"
        assert manager.current_state_payload["scenarioState"] == "INITIAL"
        assert manager.current_state_payload["simulationRunning"] is False
        assert manager.current_state_payload["riskScore"] == 0

    @pytest.mark.asyncio
    async def test_reset_without_running_loop(self, manager):
        """Reset should work even if no loop was running."""
        await manager.reset()  # Should not raise
        assert manager.scenario_state == "INITIAL"


class TestRunLoop:
    """Test the _run_loop method which drives the simulation."""

    @pytest.mark.asyncio
    async def test_run_loop_reaches_debate_active(self, manager):
        """_run_loop should simulate through all steps until DEBATE_ACTIVE."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        # Set up state manually instead of start_simulation (which creates_task)
        manager.is_running = True
        manager.current_step_index = 0
        manager.active_scenario_id = "INC-001"
        manager.current_state_payload["simulationRunning"] = True

        # Run the loop directly — processes all steps until DEBATE_ACTIVE
        await manager._run_loop()

        # Should have stopped at DEBATE_ACTIVE
        assert manager.scenario_state == "DEBATE_ACTIVE"
        # Should have progressed risk score from 0 to 96
        assert manager.current_state_payload["riskScore"] >= 95
        # Should have broadcast at least 5 times (1 initial + 4 steps)
        assert mock_ws.send_json.call_count >= 5
        # Timeline should contain events from the simulation
        assert len(manager.current_state_payload["timeline"]) >= 4

    @pytest.mark.asyncio
    async def test_loop_cancelled_on_stop(self, manager):
        """Test that cancellation of the loop task works."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.start_simulation("INC-001")
        assert manager.loop_task is not None

        # Cancel the task
        manager.loop_task.cancel()

        try:
            await manager.loop_task
        except asyncio.CancelledError:
            pass

        # The loop task should be cancelled
        assert manager.loop_task.cancelled()


class TestDecisionFlow:
    """Test the submit_decision flow for both SHUTDOWN and ISOLATION."""

    @pytest.mark.asyncio
    async def test_submit_shutdown_sets_resolved(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        # Manually set state to DEBATE_ACTIVE so decision is accepted
        manager.scenario_state = "DEBATE_ACTIVE"
        manager.active_scenario_id = "INC-001"

        await manager.submit_decision("SHUTDOWN")

        assert manager.current_state_payload["scenarioState"] == "RESOLVED"
        assert manager.current_state_payload["riskScore"] == 12  # INC-001 SHUTDOWN
        assert manager.current_state_payload["simulationRunning"] is False
        assert manager.current_state_payload["postMortem"] is not None

    @pytest.mark.asyncio
    async def test_submit_isolation_sets_resolved(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DEBATE_ACTIVE"
        manager.active_scenario_id = "INC-001"

        await manager.submit_decision("ISOLATION")

        assert manager.current_state_payload["scenarioState"] == "RESOLVED"
        assert manager.current_state_payload["riskScore"] == 45  # INC-001 ISOLATION
        # Revenue should still be at risk for isolation
        assert manager.current_state_payload["revenueAtRisk"] == "$1.2M"

    @pytest.mark.asyncio
    async def test_submit_decision_ignored_when_not_in_debate(self, manager):
        """Decision should be ignored if not in DEBATE_ACTIVE state."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DETECTION"
        await manager.submit_decision("SHUTDOWN")

        # Should not have changed scenario state
        assert manager.scenario_state == "DETECTION"

    @pytest.mark.asyncio
    async def test_submit_shutdown_sets_agents_sleeping(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DEBATE_ACTIVE"
        await manager.submit_decision("SHUTDOWN")

        for agent in manager.current_state_payload["agents"]:
            assert agent["status"] == "SLEEPING"

    @pytest.mark.asyncio
    async def test_submit_decision_broadcasts_final_state(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DEBATE_ACTIVE"
        await manager.submit_decision("SHUTDOWN")

        # Should have broadcast the final state
        mock_ws.send_json.assert_called()
        last_call = mock_ws.send_json.call_args[0][0]
        assert last_call["type"] == "state_update"
        assert last_call["payload"]["scenarioState"] == "RESOLVED"

    @pytest.mark.asyncio
    async def test_post_mortem_has_required_fields(self, manager):
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DEBATE_ACTIVE"
        await manager.submit_decision("SHUTDOWN")

        pm = manager.current_state_payload["postMortem"]
        assert pm is not None
        assert "rootCause" in pm
        assert "timelineAnalysis" in pm
        assert "businessImpact" in pm
        assert "complianceReport" in pm
        assert "lessonsLearned" in pm
        assert "preventionPlan" in pm

    @pytest.mark.asyncio
    async def test_post_mortem_contains_scenario_description(self, manager):
        """The post-mortem rootCause should reference the scenario description."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        manager.scenario_state = "DEBATE_ACTIVE"
        manager.active_scenario_id = "INC-003"
        await manager.submit_decision("SHUTDOWN")

        pm = manager.current_state_payload["postMortem"]
        assert "ransomware" in pm["rootCause"].lower()
