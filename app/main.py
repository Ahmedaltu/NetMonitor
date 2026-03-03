import asyncio

INTERVAL_SECONDS = 10  # Default value for test patching compatibility

async def main_loop():
    """
    Minimal async loop for test compatibility.
    """
    try:
        while True:
            await asyncio.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        pass
INTERVAL_SECONDS = 10  # Default value for test patching compatibility
# app/main.py

import uvicorn
from app.config.loader import load_settings
from app.core.agent import Agent
from app.collectors import load_plugins
from app.exporters.manager import load_exporters
from app.api.server import create_app
from app.utils.logger import logger


def main():
    settings = load_settings()

    collectors = load_plugins()
    exporters = load_exporters(settings)

    agent = Agent(
        agent_id=settings.agent.id,
        collectors=collectors,
        exporters=exporters,
        interval=settings.interval
    )

    app = create_app(agent, settings)

    logger.info("Starting FastAPI server...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.exporters.prometheus.port
    )


if __name__ == "__main__":
    main()
