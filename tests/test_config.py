import os
import tempfile
import yaml
import pytest
import sys

from app.config import config as config_module
from app.config.loader import load_settings

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


def test_load_settings_defaults(tmp_path):
    """Test that load_settings() parses YAML into Pydantic Settings with defaults."""
    cfg = {
        'agent': {'id': 'test-agent'},
        'exporters': {
            'influx': {'enabled': False},
            'prometheus': {'enabled': True, 'port': 9090}
        }
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(cfg))

    settings = load_settings(str(config_file))
    assert settings.agent.id == 'test-agent'
    assert settings.interval == 10  # default
    assert settings.ping.target == '8.8.8.8'  # default
    assert settings.ping.count == 4  # default
    assert settings.exporters.prometheus.port == 9090
    assert settings.exporters.influx.enabled is False


def test_load_settings_with_ping_config(tmp_path):
    """Test that load_settings() reads ping config from YAML."""
    cfg = {
        'agent': {'id': 'ping-test'},
        'ping': {'target': '1.1.1.1', 'count': 8},
        'exporters': {
            'influx': {'enabled': False},
            'prometheus': {'enabled': True}
        }
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(cfg))

    settings = load_settings(str(config_file))
    assert settings.ping.target == '1.1.1.1'
    assert settings.ping.count == 8


def test_load_settings_env_overrides(tmp_path, monkeypatch):
    """Test that environment variables override YAML values."""
    cfg = {
        'agent': {'id': 'original-id'},
        'interval': 10,
        'ping': {'target': '8.8.8.8', 'count': 4},
        'exporters': {
            'influx': {'enabled': False, 'url': 'http://localhost:8086'},
            'prometheus': {'enabled': True}
        }
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(cfg))

    monkeypatch.setenv('AGENT_ID', 'env-agent')
    monkeypatch.setenv('INTERVAL', '30')
    monkeypatch.setenv('INFLUX_URL', 'http://remote:8086')
    monkeypatch.setenv('PING_TARGET', '1.0.0.1')
    monkeypatch.setenv('PING_COUNT', '10')

    settings = load_settings(str(config_file))
    assert settings.agent.id == 'env-agent'
    assert settings.interval == 30
    assert settings.exporters.influx.url == 'http://remote:8086'
    assert settings.ping.target == '1.0.0.1'
    assert settings.ping.count == 10


def test_load_settings_file_not_found():
    """Test that load_settings() raises FileNotFoundError for missing config."""
    with pytest.raises(FileNotFoundError):
        load_settings("/nonexistent/config.yaml")
