"""
Locust load test suite for the Crisis Command Center backend.

Usage:
    # Terminal UI (default)
    locust -f locustfile.py --host http://localhost:8000

    # Headless (CI) — 30s warmup, 60s test, 10 concurrent users, 5 spawn rate
    # Results saved to load_test_stats.csv, load_test_history.csv, etc.
    locust -f locustfile.py --host http://localhost:8000 \
        --headless -u 10 -r 5 --run-time 90s \
        --csv=load_test

    # Web UI on port 8089
    locust -f locustfile.py --host http://localhost:8000 --web-port 8089
"""

import random
from locust import HttpUser, task, between, tag


# ── Helpers ──────────────────────────────────────────────────────────────────

SIMULATION_SCENARIO_IDS = [
    "INC-001",  # Customer Database Breach
    "INC-002",  # Regional Cloud Outage
    "INC-003",  # Enterprise Ransomware
    "INC-004",  # GDPR Compliance Violation
    "INC-005",  # Brand Reputation Crisis
    "INC-010",  # Perfect Storm (flagship)
]

WEBHOOK_PAYLOADS = [
    {
        "source": "Datadog",
        "event_type": "ransomware",
        "severity": "critical",
        "title": "LockBit 3.0 Detected on Production Endpoints",
        "description": "Ransomware signature detected on 48 endpoints in us-east-1.",
    },
    {
        "source": "AWS CloudWatch",
        "event_type": "outage",
        "severity": "high",
        "title": "us-east-1 Payment API Timeout",
        "description": "Payment API response time exceeded 15000ms threshold.",
    },
    {
        "source": "CrowdStrike",
        "event_type": "intrusion",
        "severity": "critical",
        "title": "Unauthorized Database Access Detected",
        "description": "SQL injection pattern on Customer PostgreSQL from external IP.",
    },
    {
        "source": "Sentry",
        "event_type": "error_spike",
        "severity": "medium",
        "title": "Checkout Error Rate Spikes to 35%",
        "description": "Error rate on /api/checkout endpoint exceeded 30% threshold.",
    },
    {
        "source": "PagerDuty",
        "event_type": "compliance",
        "severity": "high",
        "title": "GDPR Retention Limit Exceeded",
        "description": "Legacy backup volume contains 500K records past retention period.",
    },
]


# ── User Classes ─────────────────────────────────────────────────────────────


class HealthCheckUser(HttpUser):
    """Simulates a monitoring service polling the health endpoint."""

    wait_time = between(1, 3)

    @tag("health", "lightweight")
    @task(5)
    def get_health(self):
        """Poll the full health check endpoint."""
        with self.client.get(
            "/health",
            name="GET /health",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "healthy":
                    resp.success()
                else:
                    resp.failure(f"Unhealthy status: {data.get('status')}")
            elif resp.status_code == 429:
                resp.success()  # Rate limited is acceptable for health
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @tag("health", "lightweight")
    @task(2)
    def get_root(self):
        """Poll the root status endpoint."""
        with self.client.get("/", name="GET /") as resp:
            if resp.status_code == 200 and resp.json().get("status") == "online":
                resp.success()
            else:
                resp.failure(f"Root endpoint unexpected: {resp.status_code}")

    @tag("health", "lightweight")
    @task(3)
    def get_alerts(self):
        """Fetch the alert history list."""
        with self.client.get(
            "/api/incident/alerts",
            name="GET /api/incident/alerts",
        ) as resp:
            if resp.status_code == 200 and isinstance(resp.json(), list):
                resp.success()
            else:
                resp.failure(f"Alerts endpoint unexpected: {resp.status_code}")


class SimulationUser(HttpUser):
    """Simulates an operator starting simulation scenarios via WebSocket-like HTTP
    tasks. Since Locust doesn't natively support WebSocket, we use the
    /api/incident/trigger endpoint as a proxy for simulation initialization."""

    wait_time = between(5, 15)

    @tag("simulation", "medium")
    @task(3)
    def trigger_incident(self):
        """Trigger a new incident scenario via the webhook."""
        payload = random.choice(WEBHOOK_PAYLOADS)
        with self.client.post(
            "/api/incident/trigger",
            json=payload,
            name="POST /api/incident/trigger",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and data.get("scenario_id"):
                    resp.success()
                else:
                    resp.failure(f"Trigger succeeded but response malformed: {data}")
            elif resp.status_code == 429:
                resp.success()  # Rate limited is expected under load
            elif resp.status_code == 401:
                resp.success()  # Auth required is expected if API_KEY is set
            else:
                resp.failure(f"Trigger failed: {resp.status_code} - {resp.text}")


class MixedUser(HttpUser):
    """Realistic mixed workload — simulates an operator who monitors and triggers."""

    wait_time = between(2, 8)

    @tag("mixed", "lightweight")
    @task(5)
    def check_health(self):
        with self.client.get("/health", name="[mixed] GET /health") as resp:
            pass

    @tag("mixed", "lightweight")
    @task(3)
    def check_alerts(self):
        with self.client.get("/api/incident/alerts", name="[mixed] GET alerts") as resp:
            pass

    @tag("mixed", "heavy")
    @task(1)
    def trigger_incident(self):
        """Occasionally trigger an incident."""
        payload = random.choice(WEBHOOK_PAYLOADS)
        with self.client.post(
            "/api/incident/trigger",
            json=payload,
            name="[mixed] POST trigger",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 429, 401):
                resp.success()
            else:
                resp.failure(f"Unexpected: {resp.status_code}")
