import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock

from app.core.agent import Agent, NetworkEvents
from app.core.health import AgentHealth, AgentState
from app.config.models import AlertsConfig, AlertThreshold


# ── NetworkEvents ──────────────────────────────────────────────

class TestNetworkEvents:

    def test_initial_state(self):
        ev = NetworkEvents()
        d = ev.to_dict()
        assert d["timeouts"] == 0
        assert d["packet_loss_count"] == 0
        assert d["high_jitter_count"] == 0
        assert d["recent"] == []

    def test_record_timeout(self):
        ev = NetworkEvents()
        ev.record_timeout("8.8.8.8")
        d = ev.to_dict()
        assert d["timeouts"] == 1
        assert d["recent"][0]["type"] == "timeout"

    def test_record_packet_loss(self):
        ev = NetworkEvents()
        ev.record_packet_loss("8.8.8.8", 25.0)
        d = ev.to_dict()
        assert d["packet_loss_count"] == 1
        assert "25.0%" in d["recent"][0]["message"]

    def test_record_high_jitter(self):
        ev = NetworkEvents()
        ev.record_high_jitter("8.8.8.8", 75.5)
        d = ev.to_dict()
        assert d["high_jitter_count"] == 1
        assert "75.5ms" in d["recent"][0]["message"]

    def test_reset(self):
        ev = NetworkEvents()
        ev.record_timeout("8.8.8.8")
        ev.record_packet_loss("8.8.8.8", 10.0)
        ev.reset()
        d = ev.to_dict()
        assert d["timeouts"] == 0
        assert d["recent"] == []

    def test_recent_limit(self):
        ev = NetworkEvents(max_events=3)
        for i in range(5):
            ev.record_timeout(f"host-{i}")
        assert len(ev.to_dict()["recent"]) == 3


# ── AgentHealth ────────────────────────────────────────────────

class TestAgentHealth:

    def test_initial_state(self):
        h = AgentHealth()
        assert h.state == AgentState.STARTING
        assert h.consecutive_failures == 0

    def test_mark_running(self):
        h = AgentHealth()
        h.mark_degraded("test")
        h.mark_running()
        assert h.state == AgentState.RUNNING
        assert h.consecutive_failures == 0

    def test_mark_degraded(self):
        h = AgentHealth()
        h.mark_degraded("some error")
        assert h.state == AgentState.DEGRADED
        assert h.last_error == "some error"
        assert h.consecutive_failures == 1

    def test_mark_error(self):
        h = AgentHealth()
        h.mark_error("crash")
        assert h.state == AgentState.ERROR

    def test_mark_stopped(self):
        h = AgentHealth()
        h.mark_stopped()
        assert h.state == AgentState.STOPPED


# ── Agent ──────────────────────────────────────────────────────

def _make_agent(**kwargs):
    defaults = dict(
        agent_id="test-agent",
        collectors=[],
        exporters=[],
        interval=1,
    )
    defaults.update(kwargs)
    return Agent(**defaults)


class TestAgentTarget:

    def test_default_target(self):
        agent = _make_agent()
        assert agent.get_target() == "8.8.8.8"

    def test_set_target(self):
        agent = _make_agent()
        agent.set_target("1.1.1.1")
        assert agent.get_target() == "1.1.1.1"


class TestAgentHistory:

    def test_empty_history(self):
        agent = _make_agent()
        assert agent.get_history() == []

    def test_history_stored(self):
        agent = _make_agent()
        from collections import deque
        agent.metrics_history["8.8.8.8"] = deque([{"latency": 10}], maxlen=200)
        assert agent.get_history("8.8.8.8") == [{"latency": 10}]


class TestAgentAlerting:

    def _alerts_config(self):
        return AlertsConfig(
            enabled=True,
            latency_ms=AlertThreshold(warning=100, critical=200),
            packet_loss_pct=AlertThreshold(warning=5, critical=20),
            jitter_ms=AlertThreshold(warning=30, critical=60),
            hysteresis_cycles=2,
        )

    def test_no_alerts_when_disabled(self):
        agent = _make_agent(alerts_config=None)
        agent._evaluate_alerts({"latency": 999})
        assert agent.get_alerts() == []

    def test_warning_alert(self):
        agent = _make_agent(alerts_config=self._alerts_config())
        agent._evaluate_alerts({"latency": 150, "packet_loss": 0, "jitter": 5})
        alerts = agent.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "warning"
        assert alerts[0]["metric"] == "latency"

    def test_critical_alert(self):
        agent = _make_agent(alerts_config=self._alerts_config())
        agent._evaluate_alerts({"latency": 250, "packet_loss": 0, "jitter": 5})
        alerts = agent.get_alerts()
        assert any(a["severity"] == "critical" for a in alerts)

    def test_multiple_alerts(self):
        agent = _make_agent(alerts_config=self._alerts_config())
        agent._evaluate_alerts({"latency": 150, "packet_loss": 0.10, "jitter": 40})
        alerts = agent.get_alerts()
        assert len(alerts) == 3  # latency warning, packet_loss warning, jitter warning

    def test_hysteresis_clears_after_cycles(self):
        cfg = self._alerts_config()
        agent = _make_agent(alerts_config=cfg)
        # Trigger alert
        agent._evaluate_alerts({"latency": 150, "packet_loss": 0, "jitter": 5})
        assert len(agent.get_alerts()) == 1
        # First normal cycle — alert should persist (hysteresis=2)
        agent._evaluate_alerts({"latency": 50, "packet_loss": 0, "jitter": 5})
        assert len(agent.get_alerts()) == 1
        # Second normal cycle — alert should clear
        agent._evaluate_alerts({"latency": 50, "packet_loss": 0, "jitter": 5})
        assert len(agent.get_alerts()) == 0

    def test_dismiss_alert(self):
        agent = _make_agent(alerts_config=self._alerts_config())
        agent._evaluate_alerts({"latency": 150, "packet_loss": 0, "jitter": 5})
        alert_id = agent.get_alerts()[0]["id"]
        agent.dismiss_alert(alert_id)
        assert agent.get_alerts() == []

    def test_clear_alerts(self):
        agent = _make_agent(alerts_config=self._alerts_config())
        agent._evaluate_alerts({"latency": 150, "packet_loss": 0.10, "jitter": 40})
        assert len(agent.get_alerts()) > 0
        agent.clear_alerts()
        assert agent.get_alerts() == []


class TestAgentCycle:

    @pytest.mark.asyncio
    async def test_cycle_collects_and_exports(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.return_value = {
            "latency": 15.0,
            "packet_loss": 0.0,
            "jitter": 2.0,
            "target": "8.8.8.8",
            "timeout": False,
        }

        mock_exporter = MagicMock()
        mock_exporter.export.return_value = None

        agent = _make_agent(collectors=[mock_collector], exporters=[mock_exporter])
        await agent._cycle()

        mock_collector.collect.assert_called_once()
        mock_exporter.export.assert_called_once()
        assert agent.latest_metrics["latency"] == 15.0

    @pytest.mark.asyncio
    async def test_cycle_records_events(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.return_value = {
            "latency": 15.0,
            "packet_loss": 0.5,
            "jitter": 80.0,
            "target": "8.8.8.8",
            "timeout": False,
        }
        agent = _make_agent(collectors=[mock_collector])
        await agent._cycle()

        events = agent.events.to_dict()
        assert events["packet_loss_count"] == 1
        assert events["high_jitter_count"] == 1

    @pytest.mark.asyncio
    async def test_cycle_handles_collector_failure(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.side_effect = RuntimeError("fail")

        agent = _make_agent(collectors=[mock_collector])
        await agent._cycle()

        # Cycle completes without crash; no valid metrics collected
        assert agent.latest_metrics.get("latency") is None


# ── Multi-Target ───────────────────────────────────────────────

class TestAgentMultiTarget:

    def test_default_targets(self):
        agent = _make_agent()
        assert agent.get_targets() == ["8.8.8.8"]

    def test_custom_targets(self):
        agent = _make_agent(targets=["1.1.1.1", "8.8.4.4"])
        assert agent.get_targets() == ["1.1.1.1", "8.8.4.4"]

    def test_add_target(self):
        agent = _make_agent()
        agent.add_target("9.9.9.9")
        assert "9.9.9.9" in agent.get_targets()

    def test_add_duplicate_target(self):
        agent = _make_agent(targets=["8.8.8.8", "1.1.1.1"])
        agent.add_target("8.8.8.8")
        assert agent.get_targets().count("8.8.8.8") == 1

    def test_remove_target(self):
        agent = _make_agent(targets=["8.8.8.8", "1.1.1.1"])
        agent.remove_target("1.1.1.1")
        assert "1.1.1.1" not in agent.get_targets()

    def test_cannot_remove_last_target(self):
        agent = _make_agent(targets=["8.8.8.8"])
        agent.remove_target("8.8.8.8")
        assert agent.get_targets() == ["8.8.8.8"]

    def test_remove_active_target_switches(self):
        agent = _make_agent(targets=["8.8.8.8", "1.1.1.1"])
        agent.set_target("8.8.8.8")
        agent.remove_target("8.8.8.8")
        assert agent.get_target() == "1.1.1.1"

    def test_set_target_adds_to_list(self):
        agent = _make_agent(targets=["8.8.8.8"])
        agent.set_target("9.9.9.9")
        assert "9.9.9.9" in agent.get_targets()

    @pytest.mark.asyncio
    async def test_cycle_stores_per_target_metrics(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.return_value = {
            "latency": 15.0,
            "packet_loss": 0.0,
            "jitter": 2.0,
            "target": "8.8.8.8",
            "timeout": False,
        }
        agent = _make_agent(collectors=[mock_collector])
        await agent._cycle()
        assert "8.8.8.8" in agent.all_targets_metrics


# ── Analytics Integration ──────────────────────────────────────

class TestAgentAnalytics:

    @pytest.mark.asyncio
    async def test_cycle_populates_quality_score(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.return_value = {
            "latency": 20.0,
            "packet_loss": 0.0,
            "jitter": 3.0,
            "target": "8.8.8.8",
            "timeout": False,
        }
        agent = _make_agent(collectors=[mock_collector])
        await agent._cycle()
        assert "quality_score" in agent.latest_metrics
        assert agent.latest_metrics["quality_score"] > 0

    @pytest.mark.asyncio
    async def test_cycle_populates_percentiles(self):
        mock_collector = MagicMock()
        mock_collector.name = "ping"
        mock_collector.collect.return_value = {
            "latency": 25.0,
            "packet_loss": 0.0,
            "jitter": 1.0,
            "target": "8.8.8.8",
            "timeout": False,
        }
        agent = _make_agent(collectors=[mock_collector])
        await agent._cycle()
        assert "latency_p50" in agent.latest_metrics
        assert "latency_p95" in agent.latest_metrics
        assert "latency_p99" in agent.latest_metrics
