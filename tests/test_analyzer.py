"""
Tests for app/ai/analyzer.py

Covers the two changes introduced in the recent commit:
  1. Module-level InfluxDB client cache (_get_influx_client / _influx_clients)
  2. Removal of the pre-LLM Ollama health-check GET; direct POST with proper
     per-exception handling (ConnectionError, ReadTimeout, generic RequestException)

All external I/O (InfluxDB, requests, os.getenv) is mocked so these tests
run fully offline.
"""
import importlib
import sys
import types
from unittest.mock import MagicMock, patch, call

import pytest
import requests

# ---------------------------------------------------------------------------
# Helpers — build a minimal fake "settings" object so we don't need the full
# app config stack loaded.
# ---------------------------------------------------------------------------

def _make_settings(
    influx_url="http://influx:8086",
    influx_org="myorg",
    influx_bucket="netmon",
    influx_token=None,
    ai_url="http://localhost:11434/api/generate",
    ai_model="phi3",
    ai_timeout=60,
):
    settings = MagicMock()
    settings.exporters.influx.url = influx_url
    settings.exporters.influx.org = influx_org
    settings.exporters.influx.bucket = influx_bucket
    settings.exporters.influx.token = influx_token
    settings.ai.url = ai_url
    settings.ai.model = ai_model
    settings.ai.timeout = ai_timeout
    return settings


# ---------------------------------------------------------------------------
# Fixture: reset the module-level _influx_clients cache between tests so
# cache tests remain independent of each other.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_influx_cache():
    from app.ai import analyzer
    analyzer._influx_clients.clear()
    yield
    analyzer._influx_clients.clear()


# ===========================================================================
# 1.  _get_influx_client — client caching
# ===========================================================================

class TestGetInfluxClient:

    def test_first_call_creates_client(self):
        from app.ai.analyzer import _get_influx_client, _influx_clients
        with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
            _get_influx_client("http://influx:8086", "tok", "org1")
            MockClient.assert_called_once_with(
                url="http://influx:8086", token="tok", org="org1"
            )
        assert ("http://influx:8086", "org1") in _influx_clients

    def test_second_call_returns_cached_client(self):
        from app.ai.analyzer import _get_influx_client
        with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
            c1 = _get_influx_client("http://influx:8086", "tok", "org1")
            c2 = _get_influx_client("http://influx:8086", "tok", "org1")
            # InfluxDBClient constructor should only have been called once
            MockClient.assert_called_once()
        assert c1 is c2

    def test_different_org_creates_separate_client(self):
        from app.ai.analyzer import _get_influx_client
        with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
            _get_influx_client("http://influx:8086", "tok", "org1")
            _get_influx_client("http://influx:8086", "tok", "org2")
            assert MockClient.call_count == 2

    def test_different_url_creates_separate_client(self):
        from app.ai.analyzer import _get_influx_client
        with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
            _get_influx_client("http://influx-a:8086", "tok", "org1")
            _get_influx_client("http://influx-b:8086", "tok", "org1")
            assert MockClient.call_count == 2

    def test_token_change_reuses_cached_client(self):
        """Key is (url, org) only — token changes do NOT bust the cache."""
        from app.ai.analyzer import _get_influx_client
        with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
            _get_influx_client("http://influx:8086", "token-A", "org1")
            _get_influx_client("http://influx:8086", "token-B", "org1")
            # Cache key does not include token, so only one client created
            MockClient.assert_called_once()


# ===========================================================================
# 2.  fetch_recent_summary
# ===========================================================================

class TestFetchRecentSummary:

    def _mock_query_api(self, records):
        """Build a fake tables/records structure for the Influx query_api."""
        fake_record = MagicMock()
        fake_record.get_field.side_effect = [r[0] for r in records]
        fake_record.get_value.side_effect = [r[1] for r in records]
        # Rebuild as individual mocks so side_effect iterates correctly
        fake_records = []
        for field, value in records:
            r = MagicMock()
            r.get_field.return_value = field
            r.get_value.return_value = value
            fake_records.append(r)

        fake_table = MagicMock()
        fake_table.records = fake_records

        fake_client = MagicMock()
        fake_client.query_api.return_value.query.return_value = [fake_table]
        return fake_client

    def test_returns_error_when_no_token(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings(influx_token=None)
        with patch.dict("os.environ", {}, clear=True):
            # Ensure INFLUX_TOKEN is not set
            import os
            os.environ.pop("INFLUX_TOKEN", None)
            result = fetch_recent_summary(settings)
        assert "error" in result

    def test_env_token_takes_precedence(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "env-token"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                mock_qapi = MagicMock()
                mock_qapi.query.return_value = []
                MockClient.return_value.query_api.return_value = mock_qapi
                fetch_recent_summary(settings)
            # Client was constructed with the env token
            MockClient.assert_called_once_with(
                url=settings.exporters.influx.url,
                token="env-token",
                org=settings.exporters.influx.org,
            )

    def test_influx_client_reused_across_calls(self):
        """fetch_recent_summary must not create a new client on every call."""
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "tok"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                mock_qapi = MagicMock()
                mock_qapi.query.return_value = []
                MockClient.return_value.query_api.return_value = mock_qapi
                fetch_recent_summary(settings)
                fetch_recent_summary(settings)
            # Key behavioural guarantee of the cache: only ONE client
            assert MockClient.call_count == 1

    def test_returns_computed_summary(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "tok"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                records = [
                    ("latency", 10.0),
                    ("latency", 20.0),
                    ("latency", 30.0),
                ]
                client = self._mock_query_api(records)
                MockClient.return_value = client
                result = fetch_recent_summary(settings)

        assert "latency" in result
        assert result["latency"]["mean"] == pytest.approx(20.0)
        assert result["latency"]["max"] == 30.0
        assert result["latency"]["min"] == 10.0
        assert result["latency"]["samples"] == 3

    def test_non_numeric_values_skipped(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "tok"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                records = [
                    ("latency", 15.0),
                    ("label", "some-string"),  # should be ignored
                ]
                client = self._mock_query_api(records)
                MockClient.return_value = client
                result = fetch_recent_summary(settings)

        assert "latency" in result
        assert "label" not in result

    def test_influx_query_exception_returns_error_dict(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "tok"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                mock_qapi = MagicMock()
                mock_qapi.query.side_effect = RuntimeError("connection refused")
                MockClient.return_value.query_api.return_value = mock_qapi
                result = fetch_recent_summary(settings)

        assert "error" in result
        assert "connection refused" in result["error"]

    def test_empty_result_returns_empty_dict(self):
        from app.ai.analyzer import fetch_recent_summary
        settings = _make_settings()
        with patch.dict("os.environ", {"INFLUX_TOKEN": "tok"}):
            with patch("app.ai.analyzer.InfluxDBClient") as MockClient:
                mock_qapi = MagicMock()
                mock_qapi.query.return_value = []
                MockClient.return_value.query_api.return_value = mock_qapi
                result = fetch_recent_summary(settings)
        assert result == {}


# ===========================================================================
# 3.  generate_explanation — no health-check GET, direct POST with error handling
# ===========================================================================

class TestGenerateExplanation:

    GOOD_SUMMARY = {
        "latency": {"mean": 25.0, "max": 40.0, "min": 10.0, "samples": 10},
        "packet_loss": {"mean": 0.5, "max": 2.0, "min": 0.0, "samples": 10},
        "jitter": {"mean": 3.0, "max": 8.0, "min": 1.0, "samples": 10},
    }

    def test_empty_summary_returns_hint_message(self):
        from app.ai.analyzer import generate_explanation
        result = generate_explanation({})
        assert "No recent data" in result
        assert "Hint" in result

    def test_successful_llm_call_returns_response(self):
        from app.ai.analyzer import generate_explanation
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "All good."}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp) as mock_post:
            result = generate_explanation(self.GOOD_SUMMARY)
        assert result == "All good."
        # Exactly one POST — no prior GET health-check
        assert mock_post.call_count == 1
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "http://localhost:11434/api/generate"

    def test_no_get_request_is_made(self):
        """Confirm the removed health-check GET is gone: only POST is called."""
        from app.ai.analyzer import generate_explanation
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Fine."}
        with patch("app.ai.analyzer.requests.get") as mock_get, \
             patch("app.ai.analyzer.requests.post", return_value=mock_resp):
            generate_explanation(self.GOOD_SUMMARY)
        mock_get.assert_not_called()

    def test_post_payload_contains_num_predict(self):
        from app.ai.analyzer import generate_explanation
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "ok"}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp) as mock_post:
            generate_explanation(self.GOOD_SUMMARY)
        payload = mock_post.call_args[1]["json"]
        assert payload["options"]["num_predict"] == 200
        assert payload["stream"] is False

    def test_connection_error_returns_friendly_message(self):
        from app.ai.analyzer import generate_explanation
        with patch("app.ai.analyzer.requests.post",
                   side_effect=requests.exceptions.ConnectionError("refused")):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "not running" in result or "unavailable" in result.lower() or "LLM unavailable" in result

    def test_read_timeout_returns_friendly_message(self):
        from app.ai.analyzer import generate_explanation
        with patch("app.ai.analyzer.requests.post",
                   side_effect=requests.exceptions.ReadTimeout()):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "timed out" in result.lower()

    def test_generic_request_exception_returns_message(self):
        from app.ai.analyzer import generate_explanation
        with patch("app.ai.analyzer.requests.post",
                   side_effect=requests.exceptions.RequestException("boom")):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "connection error" in result.lower()

    def test_unexpected_exception_returns_message(self):
        from app.ai.analyzer import generate_explanation
        with patch("app.ai.analyzer.requests.post",
                   side_effect=ValueError("unexpected")):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "internal error" in result.lower()

    def test_malformed_response_missing_key(self):
        from app.ai.analyzer import generate_explanation
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "wrong key"}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "malformed" in result.lower()

    def test_malformed_response_non_string(self):
        from app.ai.analyzer import generate_explanation
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": 12345}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp):
            result = generate_explanation(self.GOOD_SUMMARY)
        assert "malformed" in result.lower()

    def test_settings_override_url_model_timeout(self):
        from app.ai.analyzer import generate_explanation
        settings = _make_settings(
            ai_url="http://my-ollama:11434/api/generate",
            ai_model="llama3",
            ai_timeout=30,
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "custom"}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp) as mock_post:
            result = generate_explanation(self.GOOD_SUMMARY, settings=settings)
        assert result == "custom"
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://my-ollama:11434/api/generate"
        assert call_args[1]["json"]["model"] == "llama3"
        assert call_args[1]["timeout"] == 30

    def test_only_key_metrics_included_in_prompt(self):
        """Non-whitelisted fields should be filtered out of the prompt."""
        from app.ai.analyzer import generate_explanation
        summary_with_extra = {
            **self.GOOD_SUMMARY,
            "some_internal_counter": {"mean": 999, "max": 999, "min": 999, "samples": 1},
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "ok"}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp) as mock_post:
            generate_explanation(summary_with_extra)
        prompt = mock_post.call_args[1]["json"]["prompt"]
        assert "some_internal_counter" not in prompt
        assert "latency" in prompt

    def test_settings_missing_ai_attr_uses_defaults(self):
        from app.ai.analyzer import generate_explanation, DEFAULT_OLLAMA_URL, DEFAULT_MODEL, DEFAULT_TIMEOUT
        settings = MagicMock(spec=[])  # no 'ai' attribute at all
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "fallback"}
        with patch("app.ai.analyzer.requests.post", return_value=mock_resp) as mock_post:
            result = generate_explanation(self.GOOD_SUMMARY, settings=settings)
        assert result == "fallback"
        call_args = mock_post.call_args
        assert call_args[0][0] == DEFAULT_OLLAMA_URL
        assert call_args[1]["json"]["model"] == DEFAULT_MODEL
        assert call_args[1]["timeout"] == DEFAULT_TIMEOUT
