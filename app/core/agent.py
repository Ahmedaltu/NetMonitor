# app/core/agent.py

import asyncio
from datetime import datetime
from typing import List

from app.utils.logger import logger
from app.analytics.stability import StabilityAnalyzer
from app.core.health import AgentHealth, AgentState


class Agent:
    """
    Core orchestration engine.

    Responsibilities:
    - Run collectors concurrently
    - Apply analytics
    - Tag metadata
    - Dispatch metrics to exporters
    - Track internal health state
    - Manage lifecycle cleanly
    """

    def __init__(
        self,
        agent_id: str,
        collectors: List,
        exporters: List,
        interval: int = 10,
    ):
        self.agent_id = agent_id
        self.collectors = collectors
        self.exporters = exporters
        self.interval = interval

        self.stability = StabilityAnalyzer()
        self.health = AgentHealth()
        self.latest_metrics = {}  # Store latest collected metrics for API access

        self._running = False

    # --------------------------------------------------
    # Public Lifecycle
    # --------------------------------------------------

    async def start(self):
        logger.info(f" Agent {self.agent_id} starting...")
        self._running = True
        self.health.state = AgentState.STARTING

        try:
            while self._running:
                await self._cycle()
                self.health.last_cycle = datetime.utcnow()
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            logger.info("Agent task cancelled.")
        except Exception as e:
            logger.critical(f"Agent crashed: {e}")
            self.health.mark_error(str(e))
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info(f" Agent {self.agent_id} shutting down...")
        self._running = False
        self.health.mark_stopped()

    def stop(self):
        """
        External stop trigger (used by FastAPI lifespan shutdown).
        """
        self._running = False

    # --------------------------------------------------
    # Internal Cycle
    # --------------------------------------------------

    async def _cycle(self):
        metrics = await self._collect_metrics()

        if not metrics:
            logger.warning("No metrics collected this cycle")
            self.health.mark_degraded("No metrics collected")

        # Apply analytics
        self._apply_analytics(metrics)

        # Add metadata
        self._apply_metadata(metrics)

        # Export metrics
        await self._export(metrics)

        # Store latest metrics for API access
        self.latest_metrics = metrics.copy()

        # If not in hard error, mark healthy
        if self.health.state != AgentState.ERROR:
            self.health.mark_running()

    # --------------------------------------------------
    # Collection
    # --------------------------------------------------

    async def _collect_metrics(self) -> dict:
        tasks = [
            asyncio.to_thread(collector.collect)
            for collector in self.collectors
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = {}

        for collector, result in zip(self.collectors, results):
            if isinstance(result, Exception):
                error_msg = f"Collector {collector.name} failed: {result}"
                logger.error(error_msg)
                self.health.mark_degraded(error_msg)
            elif isinstance(result, dict):
                metrics.update(result)

        return metrics

    # --------------------------------------------------
    # Analytics
    # --------------------------------------------------

    def _apply_analytics(self, metrics: dict):
        latency = metrics.get("latency")

        if latency is not None:
            self.stability.update(latency)

        rolling_mean, rolling_std = self.stability.get_metrics()

        metrics["rolling_mean_latency"] = float(rolling_mean)
        metrics["rolling_std_latency"] = float(rolling_std)


    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def _apply_metadata(self, metrics: dict):
        metrics["agent_id"] = self.agent_id
        metrics["timestamp"] = datetime.utcnow().isoformat()

    # --------------------------------------------------
    # Export
    # --------------------------------------------------

    async def _export(self, metrics: dict):
        for exporter in self.exporters:
            try:
                await asyncio.to_thread(exporter.export, metrics)
            except Exception as e:
                error_msg = (
                    f"Exporter {exporter.__class__.__name__} failed: {e}"
                )
                logger.error(error_msg)
                self.health.mark_degraded(error_msg)
