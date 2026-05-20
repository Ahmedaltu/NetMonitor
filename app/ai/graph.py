"""
app/ai/graph.py

LangGraph-based diagnostic agent for NetMonitor.

Graph nodes (in order):
  1. classify_metrics   — rule-based health classification from threshold logic
  2. retrieve_context   — ChromaDB semantic retrieval based on observed symptoms
  3. analyze            — LLM generates structured JSON diagnosis with retrieved context
  4. validate           — post-processing sanitizer (carried over from original analyzer)

State flows linearly: classify → retrieve → analyze → validate → END

Why linear and not a loop?
  A looping graph (decide → re-retrieve → re-analyze) adds latency with llama3.2:1b,
  which is a small model. Linear is more reliable here; the validation node catches
  hallucinations deterministically without burning extra inference cycles.
"""

from __future__ import annotations

import json
from typing import Any, Optional, TypedDict

import requests
from langgraph.graph import StateGraph, END

from app.utils.logger import logger
from app.ai.vector_store import semantic_retrieve


# ── Graph State ───────────────────────────────────────────────────────────────

class DiagnosticState(TypedDict):
    """Shared state passed between all graph nodes."""
    # Inputs
    summary: dict                       # Raw metric summary from InfluxDB
    key_metrics: dict                   # Flattened mean values per metric
    analysis_context: dict              # Per-metric {value, status} dict
    ollama_url: str
    model_name: str
    timeout: int

    # Intermediate
    health_classification: str          # "healthy" | "warning" | "degraded"
    symptom_query: str                  # Natural language query for ChromaDB
    retrieved_chunks: list[dict]        # [{text, source, distance}, ...]
    knowledge_context: str              # Assembled context string for LLM prompt

    # Output
    analysis_text: str                  # Raw LLM response text
    analysis_structured: Optional[dict] # Parsed + sanitized JSON


# ── Threshold helpers (kept in sync with original analyzer.py) ────────────────

THRESHOLDS = {
    "latency":      {"warning": 50,   "degraded": 100, "direction": "high"},
    "jitter":       {"warning": 20,   "degraded": 30,  "direction": "high"},
    "packet_loss":  {"warning": 1,    "degraded": 3,   "direction": "high"},
    "quality_score":{"warning": 90,   "degraded": 75,  "direction": "low"},
    "availability": {"warning": 0.99, "degraded": 0.95,"direction": "low"},
}

KEY_METRICS = ["latency", "jitter", "packet_loss", "quality_score", "availability", "uptime"]

_HALLUCINATION_PHRASES = (
    "traffic volume", "has increased", "has decreased",
    "recent maintenance", "since last", "bandwidth exhaustion",
    "insufficient bandwidth", "outage", "congestion",
)
_VALID_HEALTH_STATUSES = {"healthy", "warning", "degraded"}
_VALID_CONFIDENCES = {"low", "medium", "high"}


def _metric_status(metric: str, value: float) -> str:
    t = THRESHOLDS.get(metric)
    if not t or value is None:
        return "ok"
    if t["direction"] == "high":
        if value > t["degraded"]:   return "degraded"
        if value > t["warning"]:    return "warning"
        return "ok"
    else:
        if value < t["degraded"]:   return "degraded"
        if value < t["warning"]:    return "warning"
        return "ok"


def _build_key_metrics(summary: dict) -> dict:
    return {k: round(summary[k]["mean"], 2) for k in KEY_METRICS if k in summary}


def _build_analysis_context(summary: dict) -> dict:
    ctx = {}
    for metric in KEY_METRICS:
        value = summary.get(metric, {}).get("mean")
        ctx[metric] = {"value": value, "status": _metric_status(metric, value)}
    return ctx


# ── Node 1: classify_metrics ─────────────────────────────────────────────────

def classify_metrics(state: DiagnosticState) -> DiagnosticState:
    """
    Deterministically classify overall health and build a natural-language
    symptom description for ChromaDB retrieval.
    No LLM involved — pure rule-based logic.
    """
    ctx = state["analysis_context"]
    statuses = [v["status"] for v in ctx.values()]

    if "degraded" in statuses:
        classification = "degraded"
    elif "warning" in statuses:
        classification = "warning"
    else:
        classification = "healthy"

    # Build symptom query: name the specific elevated metrics
    elevated = [
        m for m in KEY_METRICS
        if ctx.get(m, {}).get("status") in ("warning", "degraded")
    ]

    if elevated:
        metric_phrases = []
        for m in elevated:
            val = ctx[m].get("value")
            status = ctx[m].get("status")
            if val is not None:
                metric_phrases.append(f"{m} {status} at {val}")
            else:
                metric_phrases.append(f"{m} {status}")
        symptom_query = "network issue: " + ", ".join(metric_phrases)
    else:
        symptom_query = "network healthy, all metrics within normal thresholds"

    logger.debug("classify_metrics → %s | query: %r", classification, symptom_query)

    return {
        **state,
        "health_classification": classification,
        "symptom_query": symptom_query,
    }


# ── Node 2: retrieve_context ──────────────────────────────────────────────────

def retrieve_context(state: DiagnosticState) -> DiagnosticState:
    """
    Semantic retrieval from ChromaDB.

    Retrieval strategy:
      - healthy:  1 chunk (just baselines/architecture — light context)
      - warning:  3 chunks
      - degraded: 5 chunks (maximum context for serious diagnosis)

    Distance threshold: skip chunks with cosine distance > 0.6 (low relevance).
    """
    classification = state["health_classification"]
    n_results = {"healthy": 1, "warning": 3, "degraded": 5}.get(classification, 3)

    try:
        chunks = semantic_retrieve(state["symptom_query"], n_results=n_results)
    except Exception as e:
        logger.error("ChromaDB retrieval failed: %s", e)
        chunks = []

    # Filter low-relevance chunks
    relevant_chunks = [c for c in chunks if c.get("distance", 1.0) <= 0.6]

    if not relevant_chunks and chunks:
        # All chunks exceeded threshold — use best one anyway rather than nothing
        relevant_chunks = [chunks[0]]
        logger.debug("All chunks exceeded distance threshold; using best match: %s", chunks[0]["source"])

    # Assemble knowledge context string
    sections = []
    for chunk in relevant_chunks:
        source_label = chunk["source"].replace("/", " / ").replace(".md", "")
        sections.append(f"### {source_label}\n{chunk['text'].strip()}")

    knowledge_context = "\n\n".join(sections) if sections else ""

    logger.debug(
        "retrieve_context → %d/%d chunks kept (threshold 0.6): %s",
        len(relevant_chunks), len(chunks),
        [c["source"] for c in relevant_chunks],
    )

    return {
        **state,
        "retrieved_chunks": relevant_chunks,
        "knowledge_context": knowledge_context,
    }


# ── Node 3: analyze ───────────────────────────────────────────────────────────

def analyze(state: DiagnosticState) -> DiagnosticState:
    """
    Call the local Ollama LLM with metric context + retrieved knowledge.
    Returns raw text and attempts JSON parse.
    """
    key_metrics = state["key_metrics"]
    ctx = state["analysis_context"]
    knowledge_context = state["knowledge_context"]

    knowledge_section = ""
    if knowledge_context:
        knowledge_section = (
            "\n\nOperational knowledge context (supporting reference only — "
            "do NOT invent causes not supported by the metric values; "
            "do not mention file names in your summary):\n"
            + knowledge_context
        )

    prompt = (
        "You are a network monitoring expert analyzing real-time collected metrics. "
        "Your analysis MUST be grounded strictly in the metric values and threshold status below.\n\n"
        "Rules:\n"
        "- Metrics are PRIMARY. Retrieved knowledge is SECONDARY and optional.\n"
        "- Do NOT infer congestion, packet loss, or outages unless metrics explicitly support it.\n"
        "- If health_status is 'healthy': likely_causes must be [] or benign observations only. "
        "Evidence must describe healthy metric values. Recommended checks must be low-impact.\n"
        "- If health_status is 'warning': describe only the specific elevated metrics.\n"
        "- If health_status is 'degraded': focused technical diagnosis on degraded metrics only.\n"
        "- NEVER recommend disproportionate or destructive actions.\n"
        "- Only reference incident patterns when at least two relevant metrics support them.\n"
        "- health_status: healthy=all within thresholds; warning=mildly elevated; degraded=clearly outside thresholds.\n\n"
        "Return ONLY a JSON object with exactly these fields:\n"
        "  health_status (healthy|warning|degraded),\n"
        "  summary (1-2 sentence technical diagnosis),\n"
        "  likely_causes (array of strings, empty if healthy),\n"
        "  evidence (array of strings citing specific metric values),\n"
        "  recommended_checks (array of strings, proportional to observations),\n"
        "  confidence (low|medium|high)\n\n"
        f"Metrics: {json.dumps(key_metrics)}\n"
        f"Status: {json.dumps(ctx)}"
        f"{knowledge_section}\n\n"
        "Respond ONLY with the JSON object, no extra text."
    )

    analysis_text = ""
    analysis_structured = None

    try:
        response = requests.post(
            state["ollama_url"],
            json={
                "model": state["model_name"],
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 256},
                "format": "json",
            },
            timeout=state["timeout"],
        )

        if response.status_code == 404:
            detail = response.json().get("error", "Not Found")
            analysis_text = (
                f"LLM error: {detail}. "
                f"Please run 'ollama pull {state['model_name']}' in your terminal."
            )
        else:
            response.raise_for_status()
            data = response.json()
            analysis_text = data.get("response", str(data))
            try:
                analysis_structured = json.loads(analysis_text)
            except json.JSONDecodeError:
                logger.warning("LLM response was not valid JSON: %r", analysis_text[:200])

    except requests.exceptions.ConnectionError:
        base = state["ollama_url"].rsplit("/api/", 1)[0]
        analysis_text = (
            f"LLM unavailable: Ollama is not running at {base}. "
            f"Start Ollama and ensure '{state['model_name']}' is pulled."
        )
    except requests.exceptions.ReadTimeout:
        analysis_text = (
            f"LLM timed out after {state['timeout']}s. "
            f"Model '{state['model_name']}' may be loading. Try again shortly."
        )
    except requests.exceptions.RequestException as e:
        analysis_text = f"LLM request failed: {e}"
    except Exception as e:
        analysis_text = f"LLM analysis failed: {e}"

    return {
        **state,
        "analysis_text": analysis_text,
        "analysis_structured": analysis_structured,
    }


# ── Node 4: validate ──────────────────────────────────────────────────────────

def validate(state: DiagnosticState) -> DiagnosticState:
    """
    Deterministic post-processing sanitizer.
    Normalises field types, strips hallucinations from healthy-state outputs,
    and grounds evidence in actual metric values.
    Mirrors the original sanitize_structured_analysis() logic exactly.
    """
    raw = state["analysis_structured"]
    summary = state["summary"]
    key_metrics = state["key_metrics"]
    ctx = state["analysis_context"]

    if raw is None:
        return state

    result = dict(raw)

    # Field type normalisation
    if result.get("health_status") not in _VALID_HEALTH_STATUSES:
        result["health_status"] = "warning"
    if not isinstance(result.get("summary"), str):
        result["summary"] = ""
    if not isinstance(result.get("likely_causes"), list):
        result["likely_causes"] = []
    if not isinstance(result.get("evidence"), list):
        result["evidence"] = []
    if not isinstance(result.get("recommended_checks"), list):
        result["recommended_checks"] = []
    if result.get("confidence") not in _VALID_CONFIDENCES:
        result["confidence"] = "medium"

    # Healthy-state deeper sanitisation
    if result["health_status"] == "healthy":
        all_clear = all(
            ctx.get(m, {}).get("status") == "ok"
            for m in ("latency", "jitter", "packet_loss")
        )
        if all_clear:
            result["likely_causes"] = []
        else:
            result["likely_causes"] = [
                c for c in result["likely_causes"]
                if isinstance(c, str) and not any(p in c.lower() for p in _HALLUCINATION_PHRASES)
            ]

        grounded = []
        if (lat := key_metrics.get("latency")) is not None:
            grounded.append(f"Latency within acceptable range ({lat} ms mean)")
        if (loss := key_metrics.get("packet_loss")) is not None:
            grounded.append(f"Packet loss remains low ({loss}%)")
        if (avail := key_metrics.get("availability")) is not None:
            grounded.append(f"Availability stable ({avail})")
        if (jitter := key_metrics.get("jitter")) is not None:
            if ctx.get("jitter", {}).get("status") in ("warning", "degraded"):
                grounded.append(f"Jitter mildly elevated ({jitter} ms) — not indicative of major issue")

        result["evidence"] = grounded or result["evidence"]

        safe_checks = ["Continue routine monitoring"]
        if ctx.get("jitter", {}).get("status") in ("warning", "degraded"):
            safe_checks.append("Review jitter trends if variability persists")
        safe_checks.append("Compare against short-term baseline if metrics trend upward")
        result["recommended_checks"] = safe_checks

    return {**state, "analysis_structured": result}


# ── Graph Assembly ────────────────────────────────────────────────────────────

def build_graph() -> Any:
    """Build and compile the LangGraph diagnostic graph."""
    graph = StateGraph(DiagnosticState)

    graph.add_node("classify_metrics", classify_metrics)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("analyze", analyze)
    graph.add_node("validate", validate)

    graph.set_entry_point("classify_metrics")
    graph.add_edge("classify_metrics", "retrieve_context")
    graph.add_edge("retrieve_context", "analyze")
    graph.add_edge("analyze", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


# Module-level compiled graph — import this in analyzer.py
diagnostic_graph = build_graph()
