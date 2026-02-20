# app/ai/analyzer.py

import os
import requests
from influxdb_client import InfluxDBClient
from app.utils.logger import logger


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"


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
        raise ValueError("INFLUX_TOKEN not set")

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
        return {}

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

    return summary


# -----------------------------------------------------
# LLM Explanation
# -----------------------------------------------------

def generate_explanation(summary: dict) -> str:
    """
    Send structured metric summary to local Ollama model.
    Returns natural language explanation.
    """

    if not summary:
        return "No recent data available for analysis."

    prompt = f"""
You are a network performance analyst.

Below is a structured summary of recent network metrics:

{summary}

Provide:
1. Overall network health assessment.
2. Any signs of instability.
3. Possible technical causes.
4. Recommendations if applicable.

Be concise, technical, and objective.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()
        return data.get("response", "No response from model.")

    except requests.exceptions.RequestException as e:
        logger.error(f"LLM request failed: {e}")
        return "LLM analysis failed due to connection error."

    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}")
        return "LLM analysis failed due to internal error."
