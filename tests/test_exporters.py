import pytest
from unittest.mock import MagicMock, patch
from prometheus_client import CollectorRegistry
from app.exporters.prometheus import PrometheusExporter
from app.exporters.manager import load_exporters


def _make_exporter():
    """Create a PrometheusExporter with an isolated registry to avoid global collisions."""
    exp = PrometheusExporter()
    exp._registry = CollectorRegistry()  # isolated
    return exp


class TestPrometheusExporter:

    def test_init(self):
        exp = PrometheusExporter()
        assert exp._gauges == {}

    def test_export_numeric_values(self):
        exp = _make_exporter()
        # Patch Gauge creation to use our isolated registry
        from prometheus_client import Gauge
        orig_gauges = exp._gauges
        exp.export({"test_lat": 25.0, "test_jit": 3.5})
        assert "test_lat" in exp._gauges
        assert "test_jit" in exp._gauges

    def test_export_skips_non_numeric(self):
        exp = _make_exporter()
        exp.export({"agent_id": "test", "test_lat2": 10.0})
        assert "agent_id" not in exp._gauges
        assert "test_lat2" in exp._gauges

    def test_export_skips_timestamp(self):
        exp = _make_exporter()
        exp.export({"timestamp": 1234567890, "test_lat3": 10.0})
        assert "timestamp" not in exp._gauges

    def test_export_updates_existing(self):
        exp = _make_exporter()
        exp.export({"test_lat4": 10.0})
        exp.export({"test_lat4": 20.0})
        assert len(exp._gauges) == 1


class TestLoadExporters:

    def test_no_exporters_enabled(self):
        settings = MagicMock()
        settings.exporters.influx.enabled = False
        settings.exporters.prometheus.enabled = False
        result = load_exporters(settings)
        assert result == []

    def test_prometheus_enabled(self):
        settings = MagicMock()
        settings.exporters.influx.enabled = False
        settings.exporters.prometheus.enabled = True
        result = load_exporters(settings)
        assert len(result) == 1
        assert isinstance(result[0], PrometheusExporter)

    def test_influx_enabled_no_token_raises(self, monkeypatch):
        monkeypatch.delenv("INFLUX_TOKEN", raising=False)
        settings = MagicMock()
        settings.exporters.influx.enabled = True
        settings.exporters.influx.url = "http://localhost:8086"
        settings.exporters.influx.org = "org"
        settings.exporters.influx.bucket = "bucket"
        settings.exporters.prometheus.enabled = False
        with pytest.raises(Exception):
            load_exporters(settings)
