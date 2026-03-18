# app/config/loader.py

import os
import yaml
from pathlib import Path
from .models import Settings


def _int_env(name: str) -> int | None:
    val = os.getenv(name)
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"Environment variable {name}={val!r} must be an integer")


def load_settings(config_path: str = "app/config/config.yaml") -> Settings:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        raw_config = yaml.safe_load(f)

    settings = Settings(**raw_config)

    # ---- Environment Overrides ----
    if os.getenv("AGENT_ID"):
        settings.agent.id = os.getenv("AGENT_ID")

    interval = _int_env("INTERVAL")
    if interval is not None:
        settings.interval = interval

    if os.getenv("INFLUX_URL"):
        settings.exporters.influx.url = os.getenv("INFLUX_URL")

    if os.getenv("PING_TARGET"):
        settings.ping.target = os.getenv("PING_TARGET")

    ping_count = _int_env("PING_COUNT")
    if ping_count is not None:
        settings.ping.count = ping_count

    if os.getenv("OLLAMA_URL"):
        settings.ai.url = os.getenv("OLLAMA_URL")

    if os.getenv("OLLAMA_MODEL"):
        settings.ai.model = os.getenv("OLLAMA_MODEL")

    if os.getenv("API_HOST"):
        settings.api_host = os.getenv("API_HOST")

    api_port = _int_env("API_PORT")
    if api_port is not None:
        settings.api_port = api_port

    return settings
