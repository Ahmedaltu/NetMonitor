# app/config/models.py

from pydantic import BaseModel, Field
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


class AlertsConfig(BaseModel):
    enabled: bool = True
    latency_ms: AlertThreshold = AlertThreshold(warning=100.0, critical=200.0)
    packet_loss_pct: AlertThreshold = AlertThreshold(warning=5.0, critical=20.0)
    jitter_ms: AlertThreshold = AlertThreshold(warning=30.0, critical=50.0)
    hysteresis_cycles: int = 3


class ExporterInfluxConfig(BaseModel):
    enabled: bool = True
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
    ping: PingConfig = PingConfig()
    ai: AIConfig = AIConfig()
    alerts: AlertsConfig = AlertsConfig()
    exporters: ExportersConfig
