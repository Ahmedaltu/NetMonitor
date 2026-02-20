import pytest
from app.collectors.ping import PingCollector
from app.collectors.traffic import TrafficCollector


def test_ping_collector_runs():
    collector = PingCollector()
    result = collector.collect()
    assert isinstance(result, dict)
    assert 'packet_loss' in result
    assert 'latency' in result


def test_traffic_collector_runs():
    collector = TrafficCollector()
    result = collector.collect()
    assert isinstance(result, dict)
    assert 'bytes_sent_rate' in result
    assert 'bytes_recv_rate' in result
