# app/exporters/influx.py

import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
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

        self.write_api = self.client.write_api()

        logger.info("InfluxExporter initialized")

    def export(self, metrics: dict):
        point = Point("network_metrics")

        # Add fields
        for k, v in metrics.items():
            if k == "agent_id":
                point = point.tag("agent_id", v)
            elif isinstance(v, (int, float)):
                point = point.field(k, float(v))


        point = point.time(datetime.utcnow())

        self.write_api.write(
            bucket=self.bucket,
            org=self.org,
            record=point
        )
