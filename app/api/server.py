# app/api/server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    @app.get("/health")
    async def health():
        return {
            "agent_id": agent.agent_id,
            "state": agent.health.state,
            "last_error": agent.health.last_error,
            "last_cycle": agent.health.last_cycle,
           "consecutive_failures": agent.health.consecutive_failures
        }




    @app.get("/explain")
    async def explain(window: int = 30):
        summary = fetch_recent_summary(settings, window_minutes=window)
        explanation = generate_explanation(summary)
        return {
            "window_minutes": window,
            "summary": summary,
            "analysis": explanation
        }

    @app.get("/api/agent/status")
    async def agent_status(window: str = "5m"):
        # Map health state to dashboard values
        health_state = agent.health.state.value if hasattr(agent.health.state, 'value') else str(agent.health.state)
        return {
            "agentId": agent.agent_id,
            "healthState": health_state,
            "window": window
        }

    @app.get("/api/metrics")
    async def get_metrics():
        """Return latest collected metrics for dashboard display."""
        metrics = agent.latest_metrics
        return {
            "latency": metrics.get("latency"),
            "packet_loss": metrics.get("packet_loss"),
            "jitter": metrics.get("jitter"),
            "delay_spread": metrics.get("delay_spread"),
            "rolling_mean_latency": metrics.get("rolling_mean_latency"),
            "rolling_std_latency": metrics.get("rolling_std_latency"),
            "timestamp": metrics.get("timestamp"),
            "agent_id": metrics.get("agent_id"),
        }

    @app.get("/api/metrics/history")
    async def get_metrics_history():
        """Return metrics history for charts (last 20 data points)."""
        # For now, return the latest metrics - in production this would query InfluxDB
        # The frontend will accumulate history client-side
        metrics = agent.latest_metrics
        return {
            "current": {
                "latency": metrics.get("latency"),
                "packet_loss": metrics.get("packet_loss"),
                "jitter": metrics.get("jitter"),
                "delay_spread": metrics.get("delay_spread"),
                "rolling_mean_latency": metrics.get("rolling_mean_latency"),
            },
            "timestamp": metrics.get("timestamp"),
        }


    return app
