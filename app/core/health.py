# app/core/health.py

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class AgentState(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentHealth:
    state: AgentState = AgentState.STARTING
    last_error: str | None = None
    last_cycle: datetime | None = None
    consecutive_failures: int = 0

    def mark_running(self):
        self.state = AgentState.RUNNING
        self.consecutive_failures = 0

    def mark_degraded(self, error: str):
        self.state = AgentState.DEGRADED
        self.last_error = error
        self.consecutive_failures += 1

    def mark_error(self, error: str):
        self.state = AgentState.ERROR
        self.last_error = error

    def mark_stopped(self):
        self.state = AgentState.STOPPED
