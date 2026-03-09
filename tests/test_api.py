import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.api.server import create_app, _validate_target, _check_api_key


# ── Target Validation ──────────────────────────────────────────

class TestValidateTarget:

    @pytest.mark.parametrize("target", [
        "8.8.8.8",
        "1.1.1.1",
        "google.com",
        "sub.domain.example.com",
        "my-host",
        "192.168.1.1",
        "2001:db8::1",
    ])
    def test_valid_targets(self, target):
        assert _validate_target(target) is True

    @pytest.mark.parametrize("target", [
        "",
        "a" * 256,
        "host; rm -rf /",
        "host && echo pwned",
        "$(whoami)",
        "host | cat /etc/passwd",
        "host`id`",
        "host name with spaces",
    ])
    def test_invalid_targets(self, target):
        assert _validate_target(target) is False


# ── API Endpoints ──────────────────────────────────────────────

def _make_client():
    agent = MagicMock()
    agent.agent_id = "test-agent"
    agent.health.state = "running"
    agent.health.last_error = None
    agent.health.last_cycle = None
    agent.health.consecutive_failures = 0
    agent.latest_metrics = {
        "latency": 15.0,
        "packet_loss": 0.0,
        "jitter": 2.0,
        "timestamp": "2024-01-01T00:00:00",
        "agent_id": "test-agent",
    }
    agent.get_target.return_value = "8.8.8.8"
    agent.get_history.return_value = [{"latency": 10}]
    agent.events.to_dict.return_value = {
        "timeouts": 0, "packet_loss_count": 0,
        "high_jitter_count": 0, "recent": []
    }
    agent.get_alerts.return_value = []

    settings = MagicMock()
    app = create_app(agent, settings)
    return TestClient(app, raise_server_exceptions=False), agent


class TestAPIEndpoints:

    def test_health(self):
        client, _ = _make_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["agent_id"] == "test-agent"

    def test_get_metrics(self):
        client, _ = _make_client()
        resp = client.get("/api/metrics")
        assert resp.status_code == 200
        assert resp.json()["latency"] == 15.0

    def test_get_metrics_history(self):
        client, agent = _make_client()
        resp = client.get("/api/metrics/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["target"] == "8.8.8.8"
        assert data["count"] == 1

    def test_get_events(self):
        client, _ = _make_client()
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert resp.json()["timeouts"] == 0

    def test_get_alerts(self):
        client, _ = _make_client()
        resp = client.get("/api/alerts")
        assert resp.status_code == 200
        assert resp.json()["alerts"] == []

    def test_get_target(self):
        client, _ = _make_client()
        resp = client.get("/api/target")
        assert resp.status_code == 200
        assert resp.json()["target"] == "8.8.8.8"

    def test_set_target_valid(self):
        client, agent = _make_client()
        agent.get_target.return_value = "1.1.1.1"
        resp = client.post("/api/target?target=1.1.1.1")
        assert resp.status_code == 200
        agent.set_target.assert_called_once_with("1.1.1.1")

    def test_set_target_injection_rejected(self):
        client, _ = _make_client()
        resp = client.post("/api/target?target=8.8.8.8;+rm+-rf+/")
        assert resp.status_code == 400

    def test_post_events_reset(self):
        client, agent = _make_client()
        resp = client.post("/api/events/reset")
        assert resp.status_code == 200
        agent.events.reset.assert_called_once()

    def test_post_alerts_dismiss(self):
        client, agent = _make_client()
        resp = client.post("/api/alerts/dismiss?alert_id=alert-1")
        assert resp.status_code == 200
        agent.dismiss_alert.assert_called_once_with("alert-1")

    def test_post_alerts_clear(self):
        client, agent = _make_client()
        resp = client.post("/api/alerts/clear")
        assert resp.status_code == 200
        agent.clear_alerts.assert_called_once()

    def test_prometheus_metrics(self):
        client, _ = _make_client()
        resp = client.get("/metrics")
        assert resp.status_code == 200


# ── API Key Auth ───────────────────────────────────────────────

class TestAPIKeyAuth:

    def test_no_key_configured_allows_access(self):
        """When NETMONITOR_API_KEY is unset, all requests pass."""
        client, agent = _make_client()
        with patch("app.api.server._API_KEY", None):
            resp = client.post("/api/events/reset")
            assert resp.status_code == 200

    def test_missing_key_returns_401(self):
        """When API key is configured, missing header → 401."""
        client, _ = _make_client()
        with patch("app.api.server._API_KEY", "secret-key-12345678901234567890"):
            resp = client.post("/api/events/reset")
            assert resp.status_code == 401

    def test_wrong_key_returns_403(self):
        """When API key is configured, wrong header → 403."""
        client, _ = _make_client()
        with patch("app.api.server._API_KEY", "secret-key-12345678901234567890"):
            resp = client.post(
                "/api/events/reset",
                headers={"X-API-Key": "wrong-key"}
            )
            assert resp.status_code == 403

    def test_correct_key_allows_access(self):
        """When API key is configured, correct header → 200."""
        key = "secret-key-12345678901234567890"
        client, _ = _make_client()
        with patch("app.api.server._API_KEY", key):
            resp = client.post(
                "/api/events/reset",
                headers={"X-API-Key": key}
            )
            assert resp.status_code == 200

    def test_get_endpoints_not_gated(self):
        """GET endpoints should work even with API key configured."""
        client, _ = _make_client()
        with patch("app.api.server._API_KEY", "secret-key-12345678901234567890"):
            resp = client.get("/health")
            assert resp.status_code == 200
            resp = client.get("/api/metrics")
            assert resp.status_code == 200


# ── Multi-Target API ───────────────────────────────────────────

class TestTargetsAPI:

    def test_get_targets(self):
        client, agent = _make_client()
        agent.get_targets.return_value = ["8.8.8.8", "1.1.1.1"]
        agent.all_targets_metrics = {"8.8.8.8": {"latency": 10, "packet_loss": 0, "quality_score": 95}}
        resp = client.get("/api/targets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["targets"]) == 2
        assert data["targets"][0]["target"] == "8.8.8.8"

    def test_add_target_valid(self):
        client, agent = _make_client()
        agent.get_targets.return_value = ["8.8.8.8", "9.9.9.9"]
        with patch("app.api.server._API_KEY", None):
            resp = client.post("/api/targets/add?target=9.9.9.9")
        assert resp.status_code == 200
        agent.add_target.assert_called_once_with("9.9.9.9")

    def test_add_target_invalid(self):
        client, _ = _make_client()
        with patch("app.api.server._API_KEY", None):
            resp = client.post("/api/targets/add?target=;rm+-rf+/")
        assert resp.status_code == 400

    def test_remove_target(self):
        client, agent = _make_client()
        agent.get_targets.return_value = ["8.8.8.8"]
        with patch("app.api.server._API_KEY", None):
            resp = client.post("/api/targets/remove?target=1.1.1.1")
        assert resp.status_code == 200
        agent.remove_target.assert_called_once_with("1.1.1.1")

    def test_add_target_requires_api_key(self):
        client, _ = _make_client()
        key = "secret-key-12345678901234567890"
        with patch("app.api.server._API_KEY", key):
            resp = client.post("/api/targets/add?target=9.9.9.9")
        assert resp.status_code == 401

    def test_history_with_target_param(self):
        client, agent = _make_client()
        agent.get_history.return_value = [{"latency": 5}]
        resp = client.get("/api/metrics/history?target=1.1.1.1")
        assert resp.status_code == 200
        agent.get_history.assert_called_with("1.1.1.1")
