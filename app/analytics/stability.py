from collections import deque
import statistics

class StabilityAnalyzer:
    def __init__(self, window_size=20):
        self.latency_history = deque(maxlen=window_size)

    def update(self, latency):
        if latency is not None:
            self.latency_history.append(latency)

    def get_metrics(self):
        if not self.latency_history:
            return 0, 0

        mean = sum(self.latency_history) / len(self.latency_history)
        std = statistics.stdev(self.latency_history) if len(self.latency_history) > 1 else 0

        return mean, std
