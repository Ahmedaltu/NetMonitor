# app/exporters/prometheus.py

from prometheus_client import Gauge
from threading import Lock
from app.exporters.base import BaseExporter
from app.utils.logger import logger


class PrometheusExporter(BaseExporter):
    """
    Prometheus exporter that dynamically registers
    Gauge metrics and updates them on each export cycle.
    """

    def __init__(self):
        self._gauges = {}
        self._lock = Lock()
        logger.info("PrometheusExporter initialized")

    def export(self, metrics: dict):
        """
        Update Prometheus Gauges with current metric values.
        """

        with self._lock:
            for key, value in metrics.items():

                # Skip metadata fields
                if key in ("timestamp",):
                    continue

                if not isinstance(value, (int, float)):
                    continue

                if key not in self._gauges:
                    self._gauges[key] = Gauge(
                        name=key,
                        documentation=f"NetMonitor metric {key}"
                    )

                self._gauges[key].set(value)
