# app/config/models.py

from pydantic import BaseModel, Field
from typing import Optional


class AgentConfig(BaseModel):
    id: str = Field(..., description="Unique agent identifier")
    location: Optional[str] = None
    environment: Optional[str] = "dev"


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
    exporters: ExportersConfig
