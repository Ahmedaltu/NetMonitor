# app/api/server.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import asyncio
from app.utils.logger import logger
from app.ai.analyzer import fetch_recent_summary, generate_explanation


def create_app(agent, settings):

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("Starting Agent background task...")
        agent_task = asyncio.create_task(agent.start())

        yield

        # Shutdown
        logger.info("Shutting down Agent...")
        agent.stop()
        await agent_task

    app = FastAPI(lifespan=lifespan)


    @app.get("/health")
    async def health():
        return {
            "agent_id": agent.agent_id,
            "state": agent.health.state,
            "last_error": agent.health.last_error,
            "last_cycle": agent.health.last_cycle,
           "consecutive_failures": agent.health.consecutive_failures
        }



    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    


    @app.get("/explain")
    async def explain(window: int = 30):
        summary = fetch_recent_summary(settings, window_minutes=window)
        explanation = generate_explanation(summary)

        return {
            "window_minutes": window,
            "summary": summary,
            "analysis": explanation
       }


    return app
