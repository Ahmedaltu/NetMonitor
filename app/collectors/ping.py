import platform
import re
import statistics
import subprocess

from app.collectors.base import BaseCollector


class PingCollector(BaseCollector):
    name = "ping"
    _is_windows = platform.system().lower() == "windows"

    def __init__(self, settings=None):
        if settings and hasattr(settings, 'ping'):
            self.target = settings.ping.target
            self.count = settings.ping.count
        else:
            self.target = "8.8.8.8"
            self.count = 4

    def collect(self, target: str = None):
        ping_target = target or self.target

        if self._is_windows:
            cmd = ["ping", "-n", str(self.count), ping_target]
        else:
            cmd = ["ping", "-c", str(self.count), ping_target]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.count * 5 + 5,
            )
        except subprocess.TimeoutExpired:
            return {
                "latency": None,
                "packet_loss": 1.0,
                "jitter": None,
                "delay_spread": None,
                "target": ping_target,
                "timeout": True,
            }

        # Matches "time=12ms", "time<1ms" (Windows) and "time=12.3 ms" (Linux/macOS)
        times = re.findall(r"time[=<](\d+(?:\.\d+)?)\s*ms", result.stdout)

        if not times:
            return {
                "latency": None,
                "packet_loss": 1.0,
                "jitter": None,
                "delay_spread": None,
                "target": ping_target,
                "timeout": True,
            }

        times = list(map(float, times))
        loss_ratio = 1 - (len(times) / self.count)
        mean_latency = sum(times) / len(times)
        jitter = statistics.stdev(times) if len(times) > 1 else 0.0

        if len(times) >= 2:
            qs = statistics.quantiles(times, n=4)  # [Q1, Q2, Q3]
            delay_spread = qs[2] - qs[0]
        else:
            delay_spread = 0.0

        return {
            "latency": mean_latency,
            "packet_loss": loss_ratio,
            "jitter": jitter,
            "delay_spread": delay_spread,
            "target": ping_target,
            "timeout": False,
        }
