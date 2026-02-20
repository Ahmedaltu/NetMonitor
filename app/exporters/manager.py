# app/exporters/manager.py

from typing import List
from app.exporters.base import BaseExporter
from app.utils.logger import logger


def load_exporters(settings) -> List[BaseExporter]:
    """
    Instantiate and return all enabled exporters
    based on configuration.
    """

    exporters: List[BaseExporter] = []

    # -----------------------------
    # InfluxDB Exporter
    # -----------------------------
    if settings.exporters.influx.enabled:
        try:
            from app.exporters.influx import InfluxExporter

            influx_exporter = InfluxExporter(settings)
            exporters.append(influx_exporter)

            logger.info("InfluxExporter enabled")

        except Exception as e:
            logger.error(f"Failed to initialize InfluxExporter: {e}")
            raise

    # -----------------------------
    # Prometheus Exporter
    # -----------------------------
    if settings.exporters.prometheus.enabled:
        try:
            from app.exporters.prometheus import PrometheusExporter

            prometheus_exporter = PrometheusExporter()
            exporters.append(prometheus_exporter)

            logger.info("PrometheusExporter enabled")

        except Exception as e:
            logger.error(f"Failed to initialize PrometheusExporter: {e}")
            raise

    if not exporters:
        logger.warning("No exporters enabled in configuration")

    return exporters
