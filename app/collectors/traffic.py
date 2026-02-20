import psutil
import time
from app.collectors.base import BaseCollector

class TrafficCollector(BaseCollector):
    name = "traffic"

    def __init__(self):
        self.last_counters = psutil.net_io_counters()
        self.last_time = time.time()

    def collect(self):
        current_time = time.time()
        current_counters = psutil.net_io_counters()

        time_diff = current_time - self.last_time
        bytes_sent_rate = (current_counters.bytes_sent - self.last_counters.bytes_sent) / time_diff
        bytes_recv_rate = (current_counters.bytes_recv - self.last_counters.bytes_recv) / time_diff
        packets_sent_rate = (current_counters.packets_sent - self.last_counters.packets_sent) / time_diff
        packets_recv_rate = (current_counters.packets_recv - self.last_counters.packets_recv) / time_diff

        self.last_counters = current_counters
        self.last_time = current_time

        return {
            "bytes_sent_rate": bytes_sent_rate,
            "bytes_recv_rate": bytes_recv_rate,
            "packets_sent_rate": packets_sent_rate,
            "packets_recv_rate": packets_recv_rate
        }
