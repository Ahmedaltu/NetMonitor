# app/exporters/influx.py

import os
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
from app.exporters.base import BaseExporter
from app.utils.logger import logger


class InfluxExporter(BaseExporter):

    def __init__(self, settings):
        self.url = settings.exporters.influx.url
        self.org = settings.exporters.influx.org
        self.bucket = settings.exporters.influx.bucket

        self.token = os.getenv("INFLUX_TOKEN")
        if not self.token:
            raise ValueError("INFLUX_TOKEN environment variable not set")

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )

        write_options = WriteOptions(
            batch_size=10,
            flush_interval=5_000,
            jitter_interval=1_000,
            retry_interval=3_000,
            max_retries=5,
            max_retry_delay=30_000,
            exponential_base=2,
        )
        self.write_api = self.client.write_api(write_options=write_options)

        logger.info("InfluxExporter initialized (batch + retry enabled)")

    def export(self, metrics: dict):
        point = Point("network_metrics")

        for k, v in metrics.items():
            if k in ("agent_id", "target") and isinstance(v, str):
                point = point.tag(k, v)
            elif isinstance(v, (int, float)):
                point = point.field(k, float(v))

        point = point.time(datetime.now(timezone.utc))

        self.write_api.write(
            bucket=self.bucket,
            org=self.org,
            record=point
        )

    def close(self):
        """Flush pending writes and close the InfluxDB client."""
        try:
            self.write_api.close()
        finally:
            self.client.close()
