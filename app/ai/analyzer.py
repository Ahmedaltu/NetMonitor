"""
app/ai/analyzer.py

Public API (unchanged from original — drop-in replacement):
  fetch_recent_summary(settings, window_minutes) → dict
  generate_explanation(summary, settings)        → (str, dict | None)

Internals: LangGraph graph (graph.py) + ChromaDB retrieval (vector_store.py)
replace the original single-shot Ollama call and static file loader.
"""

from __future__ import annotations

import os
from typing import Optional

from influxdb_client import InfluxDBClient

from app.utils.logger import logger
from app.ai.graph import (
    diagnostic_graph,
    _build_key_metrics,
    _build_analysis_context,
    DiagnosticState,
)

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:1b"
DEFAULT_TIMEOUT = 60

# ── InfluxDB client cache (unchanged from original) ───────────────────────────

_influx_clients: dict = {}


def _get_influx_client(url: str, token: str, org: str) -> InfluxDBClient:
    key = (url, org)
    client = _influx_clients.get(key)
    if client is None:
        client = InfluxDBClient(url=url, token=token, org=org)
        _influx_clients[key] = client
        logger.debug("Created new InfluxDB client for %s / %s", url, org)
    return client


# ── fetch_recent_summary (unchanged from original) ───────────────────────────

def fetch_recent_summary(settings, window_minutes: int = 30) -> dict:
    """
    Query recent metrics from InfluxDB and compute
    basic statistical summary (mean, min, max).
    """
    token = os.getenv("INFLUX_TOKEN")
    if not token:
        token = getattr(settings.exporters.influx, "token", None)
    if not token:
        logger.error("No InfluxDB token found in environment or settings.")
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
        logger.error("Influx query failed: %s", e)
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
            "No metrics found in InfluxDB for the last %d minutes. "
            "Check collectors and exporters.",
            window_minutes,
        )
    return summary


# ── generate_explanation ──────────────────────────────────────────────────────

def generate_explanation(summary: dict, settings=None):
    """
    Run the LangGraph diagnostic pipeline over the metric summary.

    Returns (analysis_text: str, analysis_structured: dict | None)
    — identical return signature to the original analyzer.
    """
    if not summary:
        return (
            "No recent data available for analysis.\n\n"
            "Hint: Check that collectors are running and exporting data. "
            "Review backend logs for collector/exporter errors.",
            None,
        )
    if "error" in summary:
        return (f"Cannot analyze metrics: {summary['error']}", None)

    # Resolve Ollama settings
    ollama_url = DEFAULT_OLLAMA_URL
    model_name = DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT

    if settings and hasattr(settings, "ai"):
        raw_url = getattr(settings.ai, "url", getattr(settings.ai, "ollama_url", DEFAULT_OLLAMA_URL))
        ollama_url = str(raw_url).strip()
        raw_model = getattr(settings.ai, "model", DEFAULT_MODEL)
        model_name = str(raw_model).strip()
        timeout = getattr(settings.ai, "timeout", DEFAULT_TIMEOUT)

    if not ollama_url.rstrip("/").endswith("/api/generate"):
        ollama_url = ollama_url.rstrip("/") + "/api/generate"

    # Build initial graph state
    initial_state: DiagnosticState = {
        # Inputs
        "summary": summary,
        "key_metrics": _build_key_metrics(summary),
        "analysis_context": _build_analysis_context(summary),
        "ollama_url": ollama_url,
        "model_name": model_name,
        "timeout": timeout,
        # Intermediate (empty — populated by graph nodes)
        "health_classification": "",
        "symptom_query": "",
        "retrieved_chunks": [],
        "knowledge_context": "",
        # Output (empty — populated by graph nodes)
        "analysis_text": "",
        "analysis_structured": None,
    }

    try:
        logger.info(
            "Running diagnostic graph: model=%s | metrics=%s",
            model_name,
            list(initial_state["key_metrics"].keys()),
        )
        final_state: DiagnosticState = diagnostic_graph.invoke(initial_state)
        logger.info(
            "Diagnostic graph complete: health=%s | chunks_used=%d",
            final_state.get("health_classification"),
            len(final_state.get("retrieved_chunks", [])),
        )
        return (
            final_state["analysis_text"],
            final_state["analysis_structured"],
        )

    except Exception as e:
        logger.error("Diagnostic graph failed: %s", e, exc_info=True)
        return (f"LLM analysis failed due to internal error: {e}", None)
