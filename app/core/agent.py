# app/core/agent.py

import asyncio
from datetime import datetime
from typing import List

from app.utils.logger import logger
from app.analytics.stability import StabilityAnalyzer
from app.analytics.latency_stats import LatencyStats
from app.analytics.scoring import compute_quality_score
from app.core.health import AgentHealth, AgentState
from collections import deque
from threading import Lock


class NetworkEvents:
    """Track network events like timeouts, high latency, etc."""
    
    def __init__(self, max_events=100):
        self.timeouts = 0
        self.high_jitter_count = 0
        self.packet_loss_count = 0
        self.recent = deque(maxlen=max_events)
        self._lock = Lock()
    
    def record_timeout(self, target: str):
        with self._lock:
            self.timeouts += 1
            self.recent.appendleft({
                'type': 'timeout',
                'time': datetime.utcnow().strftime('%H:%M:%S'),
                'message': f'Timeout to {target}'
            })
    
    def record_packet_loss(self, target: str, loss_pct: float):
        with self._lock:
            self.packet_loss_count += 1
            self.recent.appendleft({
                'type': 'packet_loss',
                'time': datetime.utcnow().strftime('%H:%M:%S'),
                'message': f'{loss_pct:.1f}% packet loss to {target}'
            })
    
    def record_high_jitter(self, target: str, jitter: float):
        with self._lock:
            self.high_jitter_count += 1
            self.recent.appendleft({
                'type': 'high_jitter',
                'time': datetime.utcnow().strftime('%H:%M:%S'),
                'message': f'High jitter ({jitter:.1f}ms) to {target}'
            })
    
    def to_dict(self):
        with self._lock:
            return {
                'timeouts': self.timeouts,
                'packet_loss_count': self.packet_loss_count,
                'high_jitter_count': self.high_jitter_count,
                'recent': list(self.recent)[:10]
            }
    
    def reset(self):
        with self._lock:
            self.timeouts = 0
            self.high_jitter_count = 0
            self.packet_loss_count = 0
            self.recent.clear()


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
        alerts_config=None,
        targets: List[str] | None = None,
    ):
        self.agent_id = agent_id
        self.collectors = collectors
        self.exporters = exporters
        self.interval = interval

        self.stability = StabilityAnalyzer()
        self.latency_stats = LatencyStats()
        self.health = AgentHealth()
        self.latest_metrics = {}  # Store latest collected metrics for API access
        self.all_targets_metrics = {}  # {target: latest_metrics_dict}
        self.metrics_history = {}  # {target: deque(maxlen=200)} per-target history
        self.events = NetworkEvents()  # Track network events

        # Multi-target support
        self._targets = list(targets) if targets else ["8.8.8.8"]
        self.current_target = self._targets[0]
        self._target_index = 0
        self._target_lock = Lock()

        # Alerting
        self.alerts_config = alerts_config
        self.active_alerts = {}  # {alert_key: alert_dict}
        self._normal_streak = {}  # {alert_key: consecutive_normal_count}
        self._alert_counter = 0

        self._running = False
    
    def set_target(self, target: str):
        """Change the active ping target at runtime."""
        with self._target_lock:
            self.current_target = target
            if target not in self._targets:
                self._targets.append(target)
            logger.info(f"Ping target changed to: {target}")
    
    def get_target(self):
        """Get current ping target."""
        with self._target_lock:
            return self.current_target

    def get_targets(self):
        """Return list of all monitored targets."""
        with self._target_lock:
            return list(self._targets)

    def add_target(self, target: str):
        """Add a target to the monitoring list."""
        with self._target_lock:
            if target not in self._targets:
                self._targets.append(target)
                logger.info(f"Target added: {target}")

    def remove_target(self, target: str):
        """Remove a target from the monitoring list."""
        with self._target_lock:
            if target in self._targets and len(self._targets) > 1:
                self._targets.remove(target)
                if self.current_target == target:
                    self.current_target = self._targets[0]
                    self._target_index = 0
                logger.info(f"Target removed: {target}")

    def get_history(self, target=None):
        """Get metrics history for a target (or current target)."""
        t = target or self.get_target()
        return list(self.metrics_history.get(t, []))

    def get_alerts(self):
        """Return list of active alerts."""
        return list(self.active_alerts.values())

    def dismiss_alert(self, alert_id):
        """Dismiss a specific alert by id."""
        to_remove = [k for k, v in self.active_alerts.items() if v.get("id") == alert_id]
        for k in to_remove:
            del self.active_alerts[k]
            self._normal_streak.pop(k, None)

    def clear_alerts(self):
        """Clear all active alerts."""
        self.active_alerts.clear()
        self._normal_streak.clear()

    # --------------------------------------------------
    # Public Lifecycle
    # --------------------------------------------------

    async def start(self):
        logger.info(f" Agent {self.agent_id} starting...")
        self._running = True
        self.health.state = AgentState.STARTING

        try:
            while self._running:
                # Round-robin through all targets each interval
                targets = self.get_targets()
                for target in targets:
                    if not self._running:
                        break
                    with self._target_lock:
                        self.current_target = target
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

        # Store per-target latest metrics
        target = metrics.get("target", self.get_target())
        self.all_targets_metrics[target] = metrics.copy()

        # Append to per-target history buffer
        target = metrics.get("target", self.get_target())
        if target not in self.metrics_history:
            self.metrics_history[target] = deque(maxlen=200)
        self.metrics_history[target].append(metrics.copy())

        # Evaluate alert thresholds
        self._evaluate_alerts(metrics)

        # If not in hard error, mark healthy
        if self.health.state != AgentState.ERROR:
            self.health.mark_running()

    # --------------------------------------------------
    # Collection
    # --------------------------------------------------

    async def _collect_metrics(self) -> dict:
        target = self.get_target()
        tasks = []
        for collector in self.collectors:
            # Pass target to ping collector
            if hasattr(collector, 'collect') and collector.name == 'ping':
                tasks.append(asyncio.to_thread(collector.collect, target))
            else:
                tasks.append(asyncio.to_thread(collector.collect))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = {}

        for collector, result in zip(self.collectors, results):
            if isinstance(result, Exception):
                error_msg = f"Collector {collector.name} failed: {result}"
                logger.error(error_msg)
                self.health.mark_degraded(error_msg)
            elif isinstance(result, dict):
                metrics.update(result)

        # Record events based on metrics
        self._record_events(metrics, target)

        return metrics

    def _record_events(self, metrics: dict, target: str):
        """Record network events based on collected metrics."""
        # Check for timeout
        if metrics.get('timeout'):
            self.events.record_timeout(target)
        
        # Check for packet loss
        packet_loss = metrics.get('packet_loss', 0)
        if packet_loss and packet_loss > 0:
            self.events.record_packet_loss(target, packet_loss * 100)
        
        # Check for high jitter (>50ms threshold)
        jitter = metrics.get('jitter')
        if jitter and jitter > 50:
            self.events.record_high_jitter(target, jitter)

    # --------------------------------------------------
    # Analytics
    # --------------------------------------------------

    def _apply_analytics(self, metrics: dict):
        latency = metrics.get("latency")

        if latency is not None:
            self.stability.update(latency)
            self.latency_stats.update(latency)

        rolling_mean, rolling_std = self.stability.get_metrics()

        metrics["rolling_mean_latency"] = float(rolling_mean)
        metrics["rolling_std_latency"] = float(rolling_std)

        # Latency percentiles
        percentiles = self.latency_stats.get_percentiles()
        metrics["latency_p50"] = percentiles["p50"]
        metrics["latency_p95"] = percentiles["p95"]
        metrics["latency_p99"] = percentiles["p99"]

        # Composite quality score
        metrics["quality_score"] = compute_quality_score(
            latency, metrics.get("packet_loss"), metrics.get("jitter")
        )


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

    # --------------------------------------------------
    # Alerting
    # --------------------------------------------------

    def _evaluate_alerts(self, metrics: dict):
        """Evaluate metrics against configured alert thresholds."""
        if not self.alerts_config or not self.alerts_config.enabled:
            return

        checks = [
            ("latency", metrics.get("latency"), self.alerts_config.latency_ms, "ms"),
            ("packet_loss", (metrics.get("packet_loss") or 0) * 100, self.alerts_config.packet_loss_pct, "%"),
            ("jitter", metrics.get("jitter"), self.alerts_config.jitter_ms, "ms"),
        ]

        hysteresis = self.alerts_config.hysteresis_cycles
        now = datetime.utcnow().strftime('%H:%M:%S')

        for metric_name, value, threshold, unit in checks:
            if value is None:
                continue

            alert_key = metric_name
            severity = None

            if value >= threshold.critical:
                severity = "critical"
            elif value >= threshold.warning:
                severity = "warning"

            if severity:
                # Reset normal streak — metric is in alert state
                self._normal_streak[alert_key] = 0
                self._alert_counter += 1
                self.active_alerts[alert_key] = {
                    "id": f"alert-{alert_key}-{self._alert_counter}",
                    "severity": severity,
                    "metric": metric_name,
                    "threshold": getattr(threshold, severity),
                    "actual_value": round(value, 2),
                    "message": f"{metric_name} is {value:.1f}{unit} (threshold: {getattr(threshold, severity)}{unit})",
                    "timestamp": now,
                    "acknowledged": False,
                }
            else:
                # Metric is normal — increment streak
                self._normal_streak[alert_key] = self._normal_streak.get(alert_key, 0) + 1
                if self._normal_streak.get(alert_key, 0) >= hysteresis:
                    self.active_alerts.pop(alert_key, None)
