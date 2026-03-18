# app/main.py

import uvicorn
from app.config.loader import load_settings
from app.core.agent import Agent
from app.collectors import load_plugins
from app.exporters.manager import load_exporters
from app.notifications.webhook import WebhookNotifier
from app.api.server import create_app
from app.utils.logger import logger


def main():
    settings = load_settings()

    collectors = load_plugins(settings)
    exporters = load_exporters(settings)

    # Build targets list: merge ping.targets with ping.target
    targets = list(settings.ping.targets) if settings.ping.targets else []
    if settings.ping.target and settings.ping.target not in targets:
        targets.insert(0, settings.ping.target)
    if not targets:
        targets = ["8.8.8.8"]

    # Webhook notifier
    notifier = None
    if settings.notifications and settings.notifications.webhook and settings.notifications.webhook.enabled:
        notifier = WebhookNotifier(settings.notifications.webhook)
        logger.info("Webhook notifications enabled → %s", settings.notifications.webhook.url)

    agent = Agent(
        agent_id=settings.agent.id,
        collectors=collectors,
        exporters=exporters,
        interval=settings.interval,
        alerts_config=settings.alerts,
        targets=targets,
        notifier=notifier,
        traceroute_config=settings.traceroute,
    )

    app = create_app(agent, settings)

    logger.info("Starting FastAPI server...")

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    main()
