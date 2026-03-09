# Latency statistics analytics for NetMonitor

from collections import deque


class LatencyStats:
    """Sliding-window latency percentile calculator."""

    def __init__(self, window_size: int = 100):
        self.history = deque(maxlen=window_size)

    def update(self, latency: float | None):
        if latency is not None:
            self.history.append(latency)

    def percentile(self, p: float) -> float:
        """Return the p-th percentile (0-100) of the current window."""
        if not self.history:
            return 0.0
        sorted_vals = sorted(self.history)
        k = (p / 100) * (len(sorted_vals) - 1)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_vals) else f
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])

    def get_percentiles(self) -> dict:
        """Return p50, p95, p99 percentiles."""
        return {
            "p50": round(self.percentile(50), 2),
            "p95": round(self.percentile(95), 2),
            "p99": round(self.percentile(99), 2),
        }
