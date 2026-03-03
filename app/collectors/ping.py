def ping_host(host):
    result = subprocess.run(
        ["ping", "-n", str(PING_COUNT), host],
        capture_output=True,
        text=True
    )

    times = re.findall(r"time[=<](\d+)ms", result.stdout)

    if not times:
        return None, 1.0, None, None

    times = list(map(float, times))
    loss_ratio = 1 - (len(times) / PING_COUNT)
    mean_latency = sum(times) / len(times)

    jitter = statistics.stdev(times) if len(times) > 1 else 0

    times_sorted = sorted(times)
    p25 = times_sorted[int(0.25 * len(times))]
    p75 = times_sorted[int(0.75 * len(times))]
    delay_spread = p75 - p25

    return mean_latency, loss_ratio, jitter, delay_spread

import subprocess
import re
import statistics
from app.config.config import PING_COUNT, PING_TARGET
from app.collectors.base import BaseCollector

class PingCollector(BaseCollector):
    name = "ping"

    def __init__(self, target: str = None):
        self.target = target or PING_TARGET

    def collect(self, target: str = None):
        ping_target = target or self.target
        result = subprocess.run(
            ["ping", "-n", str(PING_COUNT), ping_target],
            capture_output=True,
            text=True
        )

        times = re.findall(r"time[=<](\d+)ms", result.stdout)

        if not times:
            return {
                "latency": None,
                "packet_loss": 1.0,
                "jitter": None,
                "delay_spread": None,
                "target": ping_target,
                "timeout": True
            }

        times = list(map(float, times))
        loss_ratio = 1 - (len(times) / PING_COUNT)
        mean_latency = sum(times) / len(times)
        jitter = statistics.stdev(times) if len(times) > 1 else 0
        times_sorted = sorted(times)
        p25 = times_sorted[int(0.25 * len(times))]
        p75 = times_sorted[int(0.75 * len(times))]
        delay_spread = p75 - p25

        return {
            "latency": mean_latency,
            "packet_loss": loss_ratio,
            "jitter": jitter,
            "delay_spread": delay_spread,
            "target": ping_target,
            "timeout": False
        }
