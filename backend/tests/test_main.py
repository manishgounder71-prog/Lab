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


@pytest.fixture
def with_api_key():
    """Set API_KEY in environment for tests that need auth, then clean up."""
    import os
    original = os.environ.get("API_KEY")
    os.environ["API_KEY"] = "test-api-key-123"
    yield
    if original is None:
        del os.environ["API_KEY"]
    else:
        os.environ["API_KEY"] = original


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

    def test_root_head_endpoint(self, client):
        """HEAD / should return 200."""
        response = client.head("/")
        assert response.status_code == 200



class TestHealthEndpoint:
    """Verify /health returns full system status."""

    def test_health_returns_all_sections(self, client):
        """Health endpoint should include status, redis, rate_limit, auth, active_scenario, and uptime."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Top-level status
        assert data["status"] == "healthy"
        assert data["service"] == "Crisis Command Center Backend"
        assert data["version"] == "1.0.0"

        # Redis section
        assert "redis" in data
        assert "available" in data["redis"]
        assert "url_configured" in data["redis"]
        # In test env, Redis is not running
        assert data["redis"]["available"] is False
        assert data["redis"]["url_configured"] is False

        # Rate limit section
        assert "rate_limit" in data
        assert "configured_limit" in data["rate_limit"]
        assert data["rate_limit"]["configured_limit"] == "30/minute"

        # Auth section (does NOT expose the key)
        assert "auth" in data
        assert "api_key_configured" in data["auth"]
        assert data["auth"]["api_key_configured"] is False  # No API_KEY in test env

        # Active scenario section
        assert "active_scenario" in data
        assert data["active_scenario"]["state"] == "INITIAL"
        assert data["active_scenario"]["running"] is False
        assert data["active_scenario"]["connected_clients"] == 0
        assert data["active_scenario"]["alerts_history_count"] == 0

        # Uptime section
        assert "uptime" in data
        assert "started_at" in data["uptime"]
        assert data["uptime"]["started_at"] is not None

    def test_health_head_endpoint(self, client):
        """HEAD /health should return 200."""
        response = client.head("/health")
        assert response.status_code == 200



class TestRateLimiting:
    """Verify rate limiting middleware is wired up correctly.
    Uses a standalone mini FastAPI app to avoid interfering with the real app's rate limit counter.
    """

    def test_rate_limit_exceeded_returns_429(self):
        """With a 1/minute rate limit, the second request should return 429."""
        from fastapi import FastAPI, Request
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded

        # Create a standalone mini app with rate limiting
        limiter = Limiter(key_func=get_remote_address)
        test_app = FastAPI()
        test_app.state.limiter = limiter
        test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        @test_app.get("/test")
        @limiter.limit("1/minute")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        from fastapi.testclient import TestClient
        client = TestClient(test_app)

        # First request should succeed
        resp = client.get("/test")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.json()["status"] == "ok"

        # Second request should be rate limited
        resp = client.get("/test")
        assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # slowapi returns {"error": "Rate limit exceeded: ..."}
        assert "error" in data, f"Response should contain 'error' key: {data}"
        assert "Rate limit exceeded" in data["error"], f"Error should mention rate limit: {data}"


class TestTriggerEndpoint:
    """Verify /api/incident/trigger with API key authentication."""

    @staticmethod
    def _valid_payload():
        return {
            "source": "Datadog",
            "event_type": "ransomware",
            "severity": "critical",
            "title": "Test Alert",
            "description": "Simulated breach for testing",
        }

    def test_trigger_without_key_when_configured_returns_401(self, client, with_api_key):
        """When API_KEY is set, missing header returns 401."""
        response = client.post("/api/incident/trigger", json=self._valid_payload())
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_trigger_with_wrong_key_returns_401(self, client, with_api_key):
        """When API_KEY is set, wrong key returns 401."""
        response = client.post(
            "/api/incident/trigger",
            json=self._valid_payload(),
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_trigger_with_valid_key_succeeds(self, client, with_api_key):
        """When API_KEY is set, correct key returns 200."""
        response = client.post(
            "/api/incident/trigger",
            json=self._valid_payload(),
            headers={"X-API-Key": "test-api-key-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "scenario_id" in data

    def test_trigger_without_key_when_unconfigured_succeeds(self, client):
        """When API_KEY is not set, endpoint allows all requests (dev mode)."""
        response = client.post("/api/incident/trigger", json=self._valid_payload())
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestWebSocketAuth:
    """Verify WebSocket authentication via ?api_key query parameter."""

    @pytest.mark.asyncio
    async def test_ws_connect_without_key_when_configured_fails(self, with_api_key):
        """When API_KEY is set, connecting without ?api_key should close the socket."""
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect("/ws") as ws:
                    ws.receive_json()
            assert exc_info.value.code == 4001, f"Expected close code 4001, got {exc_info.value.code}"

    @pytest.mark.asyncio
    async def test_ws_connect_with_wrong_key_when_configured_fails(self, with_api_key):
        """When API_KEY is set, connecting with wrong key should close the socket."""
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect("/ws?api_key=wrong-key") as ws:
                    ws.receive_json()
            assert exc_info.value.code == 4001, f"Expected close code 4001, got {exc_info.value.code}"

    @pytest.mark.asyncio
    async def test_ws_connect_with_valid_key_when_configured_succeeds(self, with_api_key):
        """When API_KEY is set, correct key should allow connection."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws?api_key=test-api-key-123") as ws:
                data = ws.receive_json()
                assert data["type"] == "state_update"

    @pytest.mark.asyncio
    async def test_ws_connect_without_key_when_unconfigured_succeeds(self):
        """When API_KEY is not set, connections are allowed without key (dev mode)."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                data = ws.receive_json()
                assert data["type"] == "state_update"


class TestWebSocketEndpoints:
    """Verify WebSocket connection and message flow (in dev mode, no API_KEY)."""

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
