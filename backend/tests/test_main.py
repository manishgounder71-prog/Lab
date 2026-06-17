"""Integration tests for FastAPI main app — HTTP REST and WebSocket endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(autouse=True)
def speed_up_simulation():
    """Override step delay of global manager to 0 and reset it for all main app tests."""
    from main import manager
    original_delay = manager.step_delay
    manager.step_delay = 0
    manager.reset_sync()
    yield
    manager.reset_sync()
    manager.step_delay = original_delay


@pytest.fixture
def client():
    """FastAPI TestClient for HTTP endpoint tests."""
    with TestClient(app) as c:
        yield c


class TestHttpEndpoints:
    """Verify HTTP REST endpoints."""

    def test_root_endpoint(self, client):
        """GET / should return online status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == "Crisis Command Center Backend"

    def test_cors_headers(self, client):
        """CORS middleware should allow all origins."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should return 200 with appropriate headers
        assert response.status_code == 200
        # Verify allow-origin header (CORS allows *)
        assert "access-control-allow-origin" in response.headers


class TestWebSocketEndpoints:
    """Verify WebSocket connection and message flow."""

    @pytest.mark.asyncio
    async def test_websocket_connect_receives_initial_state(self):
        """On connect, client should immediately receive the current state."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                # Should receive state_update immediately
                data = ws.receive_json()
                assert data["type"] == "state_update"
                assert data["payload"]["scenarioState"] == "INITIAL"
                assert data["payload"]["simulationRunning"] is False

    @pytest.mark.asyncio
    async def test_start_demo_triggers_simulation(self):
        """Sending start_demo should trigger the simulation."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                # Receive initial state
                ws.receive_json()

                # Send start_demo
                ws.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})

                # Should receive state update with simulation running
                data = ws.receive_json()
                assert data["type"] == "state_update"
                assert data["payload"]["simulationRunning"] is True

    @pytest.mark.asyncio
    async def test_start_scenario_specific(self):
        """Sending start_scenario with a specific ID should activate that scenario."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                # Receive initial state
                ws.receive_json()

                # Start INC-003
                ws.send_json({
                    "action": "start_scenario",
                    "payload": {"scenario_id": "INC-003"},
                })

                data = ws.receive_json()
                assert data["payload"]["scenarioTitle"] == "Enterprise Ransomware Incident"
                assert data["payload"]["simulationRunning"] is True

    @pytest.mark.asyncio
    async def test_simulation_progresses_through_steps(self):
        """Simulation should automatically progress through DETECTION -> INVESTIGATION -> RISK_LEGAL -> DEBATE_ACTIVE."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                # Receive initial state
                ws.receive_json()

                # Start scenario
                ws.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})

                # Should progress through phases (3.5s between each)
                expected_states = ["DETECTION", "INVESTIGATION", "RISK_LEGAL", "DEBATE_ACTIVE"]
                for expected in expected_states:
                    data = ws.receive_json()
                    assert data["payload"]["scenarioState"] == expected, (
                        f"Expected {expected}, got {data['payload']['scenarioState']}"
                    )

    @pytest.mark.asyncio
    async def test_submit_shutdown_decision(self):
        """Sending SHUTDOWN decision at DEBATE_ACTIVE should resolve the scenario."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                # Receive initial state
                ws.receive_json()

                # Start scenario and wait for DEBATE_ACTIVE
                ws.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})
                for _ in range(4):
                    data = ws.receive_json()

                # Now in DEBATE_ACTIVE — submit decision
                ws.send_json({"action": "submit_decision", "payload": {"decision": "SHUTDOWN"}})

                # Receive resolution
                data = ws.receive_json()
                assert data["payload"]["scenarioState"] == "RESOLVED"
                assert data["payload"]["riskScore"] == 12
                assert data["payload"]["postMortem"] is not None
                assert data["payload"]["simulationRunning"] is False

    @pytest.mark.asyncio
    async def test_submit_isolation_decision(self):
        """Sending ISOLATION decision should resolve with higher risk."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                ws.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})
                for _ in range(4):
                    ws.receive_json()

                ws.send_json({"action": "submit_decision", "payload": {"decision": "ISOLATION"}})
                data = ws.receive_json()

                assert data["payload"]["scenarioState"] == "RESOLVED"
                assert data["payload"]["riskScore"] == 45

    @pytest.mark.asyncio
    async def test_reset_resets_simulation(self):
        """Reset action should restore initial state."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                ws.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})
                for _ in range(4):
                    ws.receive_json()

                # Reset
                ws.send_json({"action": "reset"})
                data = ws.receive_json()

                assert data["payload"]["scenarioState"] == "INITIAL"
                assert data["payload"]["simulationRunning"] is False
                assert data["payload"]["riskScore"] == 0

    @pytest.mark.asyncio
    async def test_invalid_action_does_not_crash(self):
        """Sending an unknown action should not crash the server."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                # Send unknown action
                ws.send_json({"action": "unknown_action", "payload": {}})
                # Server should still be responsive
                ws.send_json({"action": "reset"})
                data = ws.receive_json()
                assert data["type"] == "state_update"

    @pytest.mark.asyncio
    async def test_malformed_json_does_not_crash(self):
        """Sending malformed JSON should not crash the server."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                # Send malformed JSON
                ws.send_text("not valid json")
                # Server should still be responsive
                ws.send_json({"action": "reset"})
                data = ws.receive_json()
                assert data["type"] == "state_update"

    @pytest.mark.asyncio
    async def test_multiple_clients_receive_broadcasts(self):
        """Multiple connected clients should all receive state updates."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            # Connect two clients
            with client.websocket_connect("/ws") as ws1, \
                 client.websocket_connect("/ws") as ws2:
                # Both receive initial state
                ws1.receive_json()
                ws2.receive_json()

                # Start demo from ws1
                ws1.send_json({"action": "start_demo", "payload": {"scenario_id": "INC-001"}})

                # Both should receive the DETECTION update
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                assert data1["payload"]["scenarioState"] == "DETECTION"
                assert data2["payload"]["scenarioState"] == "DETECTION"

    @pytest.mark.asyncio
    async def test_decision_with_invalid_action(self):
        """Sending submit_decision without being in DEBATE_ACTIVE should be ignored."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()

                # Try to submit decision before starting
                ws.send_json({"action": "submit_decision", "payload": {"decision": "SHUTDOWN"}})

                # Should still be in initial state
                ws.send_json({"action": "reset"})
                data = ws.receive_json()
                assert data["payload"]["scenarioState"] == "INITIAL"
