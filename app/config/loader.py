# app/config/loader.py

import os
import yaml
from pathlib import Path
from .models import Settings


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

    if os.getenv("INTERVAL"):
        settings.interval = int(os.getenv("INTERVAL"))

    if os.getenv("INFLUX_URL"):
        settings.exporters.influx.url = os.getenv("INFLUX_URL")

    if os.getenv("PING_TARGET"):
        settings.ping.target = os.getenv("PING_TARGET")

    if os.getenv("PING_COUNT"):
        settings.ping.count = int(os.getenv("PING_COUNT"))

    if os.getenv("OLLAMA_URL"):
        settings.ai.url = os.getenv("OLLAMA_URL")

    if os.getenv("OLLAMA_MODEL"):
        settings.ai.model = os.getenv("OLLAMA_MODEL")

    return settings
