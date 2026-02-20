import os
import tempfile
import yaml
import pytest
import sys

from app.config import config as config_module

def test_config_loads_yaml(monkeypatch):
    # Create a temporary YAML config
    cfg = {
        'influx': {'org': 'test-org', 'bucket': 'test-bucket', 'url': 'http://localhost:9999', 'token': 'test-token'},
        'ping': {'target': '1.1.1.1', 'count': 2},
        'interval_seconds': 5
    }
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.yaml') as f:
        yaml.dump(cfg, f)
        f.flush()
        monkeypatch.setenv('INFLUX_TOKEN', '')
        loaded = config_module.load_config(f.name)
        assert loaded["ORG"] == 'test-org'
        assert loaded["BUCKET"] == 'test-bucket'
        assert loaded["PING_TARGET"] == '1.1.1.1'
        assert loaded["PING_COUNT"] == 2
        assert loaded["INTERVAL_SECONDS"] == 5
        assert loaded["TOKEN"] == 'test-token'
    os.unlink(f.name)
