# app/ai/analyzer.py

import os
import requests
from influxdb_client import InfluxDBClient
from app.utils.logger import logger


# Default values (overridden by settings when available)
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3"
DEFAULT_TIMEOUT = 60


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

    client = InfluxDBClient(
        url=settings.exporters.influx.url,
        token=token,
        org=settings.exporters.influx.org
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

    metrics = {}

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
        logger.warning("No metrics found in InfluxDB for the requested window (last %d minutes). Check collectors and exporters.", window_minutes)
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
        return "No recent data available for analysis.\n\nHint: Check that collectors are running and exporting data. Review backend logs for collector/exporter errors."

    # Read config from settings, fall back to defaults
    ollama_url = DEFAULT_OLLAMA_URL
    model_name = DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT
    if settings and hasattr(settings, 'ai'):
        ollama_url = getattr(settings.ai, 'url', DEFAULT_OLLAMA_URL)
        model_name = getattr(settings.ai, 'model', DEFAULT_MODEL)
        timeout = getattr(settings.ai, 'timeout', DEFAULT_TIMEOUT)

    # Limit summary to key metrics for prompt readability
    key_metrics = {k: v for k, v in summary.items() if k in ["latency", "packet_loss", "jitter", "quality_score", "throughput", "error_rate", "availability", "anomaly_score", "uptime"]}
    prompt = f"""
You are a network performance analyst.

Below is a structured summary of recent network metrics:

{key_metrics}

Provide:
1. Overall network health assessment.
2. Any signs of instability.
3. Possible technical causes.
4. Recommendations if applicable.

Be concise, technical, and objective.
"""

    import asyncio
    async def _call_llm():
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(
                ollama_url,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=timeout
            ))
            response.raise_for_status()
            data = response.json()
            # Validate response structure
            if "response" not in data or not isinstance(data["response"], str):
                logger.error(f"Malformed LLM response: {data}")
                return "LLM analysis failed: malformed response."
            return data["response"]
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request failed: {e}")
            return f"LLM analysis failed due to connection error: {e}"
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            return f"LLM analysis failed due to internal error: {e}"

    # Run async LLM call
    return asyncio.run(_call_llm())
