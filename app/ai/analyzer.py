# app/ai/analyzer.py


import os
import json
import requests
from influxdb_client import InfluxDBClient
from app.utils.logger import logger

# Default values (overridden by settings when available)
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"
DEFAULT_TIMEOUT = 60

# Module-level InfluxDB client cache — avoids reconnect on every /explain call.
# Keyed by (url, org) so a settings change creates a new client.
_influx_clients: dict = {}

def _get_influx_client(url: str, token: str, org: str) -> InfluxDBClient:
    key = (url, org)
    client = _influx_clients.get(key)
    if client is None:
        client = InfluxDBClient(url=url, token=token, org=org)
        _influx_clients[key] = client
        logger.debug("Created new InfluxDB client for %s / %s", url, org)
    return client

# -----------------------------------------------------
# Influx Summary Builder
# -----------------------------------------------------

def fetch_recent_summary(settings, window_minutes: int = 30) -> dict:
    """
    Query recent metrics from InfluxDB and compute
    basic statistical summary (mean, min, max).
    """
    token = os.getenv("INFLUX_TOKEN")
    if not token:
        logger.error("INFLUX_TOKEN not set. Falling back to settings.exporters.influx.token if available.")
        token = getattr(settings.exporters.influx, 'token', None)
    if not token:
        logger.error("No InfluxDB token found in environment or settings. Metrics query will fail.")
        return {"error": "No InfluxDB token configured."}

    client = _get_influx_client(
        url=settings.exporters.influx.url,
        token=token,
        org=settings.exporters.influx.org,
    )
    query_api = client.query_api()
    flux_query = f"""
from(bucket: "{settings.exporters.influx.bucket}")
  |> range(start: -{window_minutes}m)
  |> filter(fn: (r) => r._measurement == "network_metrics")
"""
    try:
        tables = query_api.query(flux_query)
    except Exception as e:
        logger.error(f"Influx query failed: {e}")
        return {"error": f"Influx query failed: {e}"}

    metrics: dict = {}
    for table in tables:
        for record in table.records:
            field = record.get_field()
            value = record.get_value()
            if isinstance(value, (int, float)):
                metrics.setdefault(field, []).append(float(value))

    summary = {}
    for key, values in metrics.items():
        if not values:
            continue
        summary[key] = {
            "mean": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
            "samples": len(values),
        }
    if not summary:
        logger.warning(
            "No metrics found in InfluxDB for the requested window (last %d minutes). "
            "Check collectors and exporters.",
            window_minutes,
        )
    return summary

# -----------------------------------------------------
# Threshold helpers and context
# -----------------------------------------------------

THRESHOLDS = {
    "latency": {"warning": 50, "degraded": 100, "direction": "high"},
    "jitter": {"warning": 20, "degraded": 30, "direction": "high"},
    "packet_loss": {"warning": 1, "degraded": 3, "direction": "high"},
    "quality_score": {"warning": 90, "degraded": 75, "direction": "low"},
    "availability": {"warning": 0.99, "degraded": 0.95, "direction": "low"},
    # uptime: no strict threshold
}

KEY_METRICS = ["latency", "jitter", "packet_loss", "quality_score", "availability", "uptime"]

def build_key_metrics(summary):
    return {k: round(summary[k]["mean"], 2) for k in KEY_METRICS if k in summary}

def metric_status(metric, value):
    t = THRESHOLDS.get(metric)
    if not t or value is None:
        return "ok"
    if t["direction"] == "high":
        if value > t["degraded"]:
            return "degraded"
        elif value > t["warning"]:
            return "warning"
        else:
            return "ok"
    else:  # direction == "low"
        if value < t["degraded"]:
            return "degraded"
        elif value < t["warning"]:
            return "warning"
        else:
            return "ok"

def build_analysis_context(summary):
    context = {}
    for metric in KEY_METRICS:
        value = summary.get(metric, {}).get("mean")
        context[metric] = {
            "value": value,
            "status": metric_status(metric, value)
        }
    return context

# -----------------------------------------------------
# LLM Explanation (returns (analysis_text, analysis_structured))
# -----------------------------------------------------

def generate_explanation(summary: dict, settings=None):
    """
    Send structured metric summary to local Ollama model.
    Returns (analysis_text, analysis_structured) tuple.
    """
    if not summary:
        return (
            "No recent data available for analysis.\n\n"
            "Hint: Check that collectors are running and exporting data. "
            "Review backend logs for collector/exporter errors.",
            None
        )
    if "error" in summary:
        return (f"Cannot analyze metrics: {summary['error']}", None)

    ollama_url = DEFAULT_OLLAMA_URL
    model_name = DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT
    if settings and hasattr(settings, 'ai'):
        raw_url = getattr(settings.ai, 'url', getattr(settings.ai, 'ollama_url', DEFAULT_OLLAMA_URL))
        ollama_url = str(raw_url).strip()
        raw_model = getattr(settings.ai, 'model', DEFAULT_MODEL)
        model_name = str(raw_model).strip()
        timeout = getattr(settings.ai, 'timeout', DEFAULT_TIMEOUT)

    if not ollama_url.rstrip('/').endswith('/api/generate'):
        ollama_url = ollama_url.rstrip('/') + '/api/generate'

    key_metrics = build_key_metrics(summary)
    context = build_analysis_context(summary)

    # Strict JSON-only prompt
    prompt = (
        "You are a network monitoring expert. "
        "Given the following metrics and their threshold-based status, "
        "analyze the network health and return ONLY a JSON object with these fields: "
        "health_status (one of: healthy, warning, degraded), "
        "summary (short technical diagnosis), "
        "likely_causes (array of strings), "
        "evidence (array of strings), "
        "recommended_checks (array of strings), "
        "confidence (one of: low, medium, high). "
        "Do not include generic advice like 'monitor over time'. "
        "Be technical and concise. "
        f"Metrics: {json.dumps(key_metrics)}. "
        f"Status: {json.dumps(context)}. "
        "Respond ONLY with the JSON object, no extra text."
    )

    try:
        req_json = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 256},
            "format": "json"
        }
        response = requests.post(
            ollama_url,
            json=req_json,
            timeout=timeout,
        )
        if response.status_code == 404:
            try:
                detail = response.json().get("error", "Not Found")
                return (f"LLM error: {detail}. Please run 'ollama pull {model_name}' in your terminal.", None)
            except Exception:
                return (f"LLM error 404: Endpoint {ollama_url} not found. "
                        f"Ensure model '{model_name}' is downloaded.", None)

        response.raise_for_status()
        data = response.json()
        text = data["response"] if "response" in data else str(data)
        try:
            analysis_structured = json.loads(text)
        except Exception:
            analysis_structured = None
        return (text, analysis_structured)
    except requests.exceptions.ConnectionError:
        ollama_base = ollama_url.rsplit("/api/", 1)[0]
        logger.error("Ollama is not reachable at %s", ollama_base)
        return (
            f"LLM unavailable: Ollama is not running at {ollama_base}. "
            f"Start Ollama and ensure the '{model_name}' model is pulled.",
            None
        )
    except requests.exceptions.ReadTimeout:
        logger.error("LLM timed out after %ss — model may still be loading", timeout)
        return (
            f"LLM timed out after {timeout}s. "
            f"The model '{model_name}' may be loading or too slow. Try again shortly.",
            None
        )
    except requests.exceptions.RequestException as e:
        logger.error("LLM request failed: %s", e)
        return (f"LLM analysis failed due to connection error: {e}", None)
    except Exception as e:
        logger.error("Unexpected LLM error: %s", e)
        return (f"LLM analysis failed due to internal error: {e}", None)
