# app/api/server.py

import hmac
import os
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import asyncio
from app.utils.logger import logger
from app.ai.analyzer import fetch_recent_summary, generate_explanation

_API_KEY: str | None = os.environ.get("NETMONITOR_API_KEY")


def _check_api_key(request: Request) -> None:
    """Enforce API-key auth on mutation endpoints when a key is configured."""
    if _API_KEY is None:
        return  # auth disabled
    provided = request.headers.get("X-API-Key", "")
    if not provided:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not hmac.compare_digest(provided, _API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")

# Hostname/IP validation: alphanumeric, hyphens, dots, colons (IPv6)
_VALID_TARGET_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.\:]{0,253}[a-zA-Z0-9])?$'
)


def _validate_target(target: str) -> bool:
    """Validate that a ping target is a safe hostname or IP address."""
    if not target or len(target) > 255:
        return False
    return bool(_VALID_TARGET_RE.match(target))


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
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass

    app = FastAPI(lifespan=lifespan)

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
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
        summary = await asyncio.to_thread(fetch_recent_summary, settings, window_minutes=window)
        if "error" in summary:
            raise HTTPException(status_code=503, detail=summary["error"])
        explanation = await asyncio.to_thread(generate_explanation, summary, settings=settings)
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
            "latency_p50": metrics.get("latency_p50"),
            "latency_p95": metrics.get("latency_p95"),
            "latency_p99": metrics.get("latency_p99"),
            "quality_score": metrics.get("quality_score"),
            "throughput": metrics.get("throughput"),
            "error_rate": metrics.get("error_rate"),
            "availability": metrics.get("availability"),
            "anomaly_score": metrics.get("anomaly_score"),
            "uptime": metrics.get("uptime"),
            "timestamp": metrics.get("timestamp"),
            "agent_id": metrics.get("agent_id"),
        }

    @app.get("/api/metrics/history")
    async def get_metrics_history(target: str | None = None):
        """Return server-side metrics history buffer for charts."""
        t = target or agent.get_target()
        history = agent.get_history(t)
        return {
            "target": t,
            "history": history,
            "count": len(history),
        }

    @app.get("/metrics")
    async def prometheus_metrics():
        """Expose metrics in Prometheus format for scraping."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/events")
    async def get_events():
        """Return network events (timeouts, packet loss, high jitter)."""
        return agent.events.to_dict()

    @app.get("/api/alerts")
    async def get_alerts():
        """Return active threshold-based alerts."""
        return {"alerts": agent.get_alerts()}

    @app.post("/api/alerts/dismiss")
    async def dismiss_alert(alert_id: str, request: Request):
        """Dismiss a specific alert."""
        _check_api_key(request)
        agent.dismiss_alert(alert_id)
        return {"status": "ok"}

    @app.post("/api/alerts/clear")
    async def clear_alerts(request: Request):
        """Clear all active alerts."""
        _check_api_key(request)
        agent.clear_alerts()
        return {"status": "ok"}

    @app.post("/api/events/reset")
    async def reset_events(request: Request):
        """Reset event counters."""
        _check_api_key(request)
        agent.events.reset()
        return {"status": "ok"}

    @app.get("/api/target")
    async def get_target():
        """Get current ping target."""
        return {"target": agent.get_target()}

    @app.get("/api/targets")
    async def get_targets():
        """Get all monitored targets with their latest metrics."""
        targets = agent.get_targets()
        result = []
        for t in targets:
            m = agent.all_targets_metrics.get(t, {})
            result.append({
                "target": t,
                "active": t == agent.get_target(),
                "latency": m.get("latency"),
                "packet_loss": m.get("packet_loss"),
                "quality_score": m.get("quality_score"),
            })
        return {"targets": result}

    @app.post("/api/targets/add")
    async def add_target(target: str, request: Request):
        """Add a target to the monitoring list."""
        _check_api_key(request)
        if not _validate_target(target):
            raise HTTPException(
                status_code=400,
                detail="Invalid target. Must be a valid hostname or IP address."
            )
        agent.add_target(target)
        return {"targets": agent.get_targets()}

    @app.post("/api/targets/remove")
    async def remove_target(target: str, request: Request):
        """Remove a target from the monitoring list."""
        _check_api_key(request)
        if not _validate_target(target):
            raise HTTPException(
                status_code=400,
                detail="Invalid target. Must be a valid hostname or IP address."
            )
        agent.remove_target(target)
        return {"targets": agent.get_targets()}

    @app.post("/api/target")
    async def set_target(target: str, request: Request):
        """Set ping target for monitoring."""
        _check_api_key(request)
        if not _validate_target(target):
            raise HTTPException(
                status_code=400,
                detail="Invalid target. Must be a valid hostname or IP address."
            )
        agent.set_target(target)
        return {"target": agent.get_target()}

    # ── Traceroute endpoints ──────────────────────────────────
    @app.post("/api/traceroute")
    async def traceroute(request: Request, target: str | None = None):
        """Run on-demand traceroute to a target."""
        _check_api_key(request)
        t = target or agent.get_target()
        if not _validate_target(t):
            raise HTTPException(status_code=400, detail="Invalid target.")
        result = await agent.run_traceroute(t)
        return {
            "target": t,
            "traceroute": {
                "target": t,
                "hops": result.get("traceroute_hops", []),
                "hop_count": result.get("traceroute_hop_count", 0),
                "complete": result.get("traceroute_complete", False),
            },
        }

    @app.get("/api/traceroute/latest")
    async def traceroute_latest(target: str | None = None):
        """Return last cached traceroute result."""
        if target:
            data = agent.latest_traceroute.get(target)
            return {"target": target, "traceroute": data}
        return {"traceroutes": agent.latest_traceroute}

    # ── Probe result endpoints ────────────────────────────────
    @app.get("/api/probes/http")
    async def http_probes():
        """Return latest HTTP probe results from collector metrics."""
        m = agent.latest_metrics
        probes = m.get("http_probes", {})
        return {"probes": probes}

    @app.get("/api/probes/dns")
    async def dns_probes():
        """Return latest DNS probe results from collector metrics."""
        m = agent.latest_metrics
        dns = m.get("dns_probes", {})
        return {"probes": dns}

    # ── Notification test endpoint ────────────────────────────
    @app.post("/api/notifications/test")
    async def test_notification(request: Request):
        """Send a test webhook notification."""
        _check_api_key(request)
        if not agent.notifier:
            raise HTTPException(status_code=400, detail="No webhook notifier configured.")
        test_alert = {
            "severity": "info",
            "metric": "test",
            "actual_value": 0,
            "message": "Test notification from NetMonitor",
        }
        try:
            await asyncio.to_thread(agent.notifier.notify, "__test__", test_alert)
            return {"status": "sent"}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc))

    return app
