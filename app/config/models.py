# app/config/models.py

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class AgentConfig(BaseModel):
    id: str = Field(..., description="Unique agent identifier")
    location: Optional[str] = None
    environment: Optional[str] = "dev"


class PingConfig(BaseModel):
    target: str = "8.8.8.8"
    targets: list[str] = []
    count: int = 4


class AIConfig(BaseModel):
    url: str = "http://localhost:11434/api/generate"
    model: str = "phi3"
    timeout: int = 60


class AlertThreshold(BaseModel):
    warning: float
    critical: float

    @model_validator(mode="after")
    def check_thresholds(self) -> "AlertThreshold":
        if self.warning >= self.critical:
            raise ValueError(
                f"warning threshold ({self.warning}) must be less than critical ({self.critical})"
            )
        return self


class AlertsConfig(BaseModel):
    enabled: bool = True
    latency_ms: AlertThreshold = AlertThreshold(warning=100.0, critical=200.0)
    packet_loss_pct: AlertThreshold = AlertThreshold(warning=5.0, critical=20.0)
    jitter_ms: AlertThreshold = AlertThreshold(warning=30.0, critical=50.0)
    hysteresis_cycles: int = 3


class HttpProbeEntry(BaseModel):
    url: str
    expected_status: int = 200
    timeout: int = 5


class DnsProbeEntry(BaseModel):
    hostname: str
    timeout: int = 3


class TracerouteConfig(BaseModel):
    enabled: bool = False
    interval_cycles: int = 6  # run every N agent cycles


class NotificationsWebhookConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    timeout: int = 10


class NotificationsConfig(BaseModel):
    webhook: NotificationsWebhookConfig = NotificationsWebhookConfig()


class ExporterInfluxConfig(BaseModel):
    enabled: bool = False  # disabled by default — requires INFLUX_TOKEN
    url: str = "http://localhost:8086"
    org: str = "net-monitor"
    bucket: str = "network"


class ExporterPrometheusConfig(BaseModel):
    enabled: bool = True
    port: int = 8000


class ExportersConfig(BaseModel):
    influx: ExporterInfluxConfig
    prometheus: ExporterPrometheusConfig


class Settings(BaseModel):
    agent: AgentConfig
    interval: int = 10
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ping: PingConfig = PingConfig()
    ai: AIConfig = AIConfig()
    alerts: AlertsConfig = AlertsConfig()
    notifications: NotificationsConfig = NotificationsConfig()
    http_probes: list[HttpProbeEntry] = []
    dns_probes: list[DnsProbeEntry] = []
    traceroute: TracerouteConfig = TracerouteConfig()
    exporters: ExportersConfig
