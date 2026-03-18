# app/ai/analyzer.py

import os
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
# LLM Explanation
# -----------------------------------------------------

def generate_explanation(summary: dict, settings=None) -> str:
    """
    Send structured metric summary to local Ollama model.
    Returns natural language explanation.
    """

    if not summary:
        return (
            "No recent data available for analysis.\n\n"
            "Hint: Check that collectors are running and exporting data. "
            "Review backend logs for collector/exporter errors."
        )

    # Read config from settings, fall back to defaults
    ollama_url = DEFAULT_OLLAMA_URL
    model_name = DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT
    if settings and hasattr(settings, 'ai'):
        ollama_url = getattr(settings.ai, 'url', DEFAULT_OLLAMA_URL)
        model_name = getattr(settings.ai, 'model', DEFAULT_MODEL)
        timeout = getattr(settings.ai, 'timeout', DEFAULT_TIMEOUT)

    # Limit summary to key metrics for prompt readability
    key_metrics = {
        k: round(v["mean"], 2) if isinstance(v, dict) else v
        for k, v in summary.items()
        if k in ("latency", "packet_loss", "jitter", "quality_score", "uptime", "availability")
    }
    prompt = (
        f"Network stats (means): {key_metrics}. "
        "In 3 bullet points: health status, any issues, one recommendation."
    )

    try:
        response = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 200},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if "response" not in data or not isinstance(data["response"], str):
            logger.error("Malformed LLM response: %s", data)
            return "LLM analysis failed: malformed response."
        return data["response"]
    except requests.exceptions.ConnectionError:
        ollama_base = ollama_url.rsplit("/api/", 1)[0]
        logger.error("Ollama is not reachable at %s", ollama_base)
        return (
            f"LLM unavailable: Ollama is not running at {ollama_base}. "
            f"Start Ollama and ensure the '{model_name}' model is pulled."
        )
    except requests.exceptions.ReadTimeout:
        logger.error("LLM timed out after %ss — model may still be loading", timeout)
        return (
            f"LLM timed out after {timeout}s. "
            f"The model '{model_name}' may be loading or too slow. Try again shortly."
        )
    except requests.exceptions.RequestException as e:
        logger.error("LLM request failed: %s", e)
        return f"LLM analysis failed due to connection error: {e}"
    except Exception as e:
        logger.error("Unexpected LLM error: %s", e)
        return f"LLM analysis failed due to internal error: {e}"
