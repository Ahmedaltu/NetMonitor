# NetMonitor Evaluations

This document stores formal evaluations of the NetMonitor system conducted by skill-based reviews (architecture reviews, product manager evaluations, security audits, etc.).

---

## Evaluation Log

| Date | Type | Conducted By | Decision / Outcome |
|------|------|-------------|-------------------|
| 2026-03-09 | Product Manager Evaluation | product-manager skill | 14 gaps identified, 10 features proposed, 3-phase roadmap |
| 2026-03-09 | Review Board — PM Evaluation | review-board skill | CONDITIONALLY APPROVED — 8 conditions applied, auth elevated to P1 |

---

## 2026-03-09 — Product Manager Evaluation

### Product Understanding

**What NetMonitor is:** An async network monitoring agent (Python/FastAPI backend + React dashboard) that collects ping latency, packet loss, jitter, and traffic throughput, exports to InfluxDB/Prometheus, and provides AI-powered analysis via a local LLM.

**Target user:** Network engineers, DevOps teams, and sysadmins who need continuous visibility into network health from one or more endpoints.

**Primary workflow:** Start agent → dashboard shows real-time latency/loss/jitter → change targets at runtime → view events → ask AI for analysis.

**What works well:**
- Core collect → analyze → export cycle is solid and async
- Plugin pattern for collectors/exporters is extensible
- React dashboard has good visual design with KPI cards, charts, events panel
- Runtime target changes without restart
- Dual export (push to InfluxDB, pull via Prometheus)
- Local LLM integration (no cloud dependency)

**What's incomplete:**
- 6 empty stub files (`scheduler.py`, `plugin_manager.py`, `routes.py`, `exceptions.py`, `scoring.py`, `latency_stats.py`)
- iPerf collector is a skeleton (not a `BaseCollector` subclass)
- `docker-compose.yml` is empty
- `AlertsPanel` component exists but is never rendered in the dashboard
- `/api/metrics/history` returns only current data
- Test coverage is ~20% (2 test files empty, 2 minimal)

### Gap Analysis

| # | Gap | Current State | Impact | Severity |
|---|-----|--------------|--------|----------|
| 0 | **Command injection via /api/target** | User-supplied ping target passed to `subprocess.run` without validation | Attacker on the network can inject OS commands via crafted target string | **Critical** |
| 1 | No metrics history on server | Frontend accumulates 30 points client-side; lost on refresh | Users lose all chart data on page reload | High |
| 2 | No alerting system | Events tracked but no thresholds, no notifications | Users must watch the dashboard to detect problems | High |
| 3 | AlertsPanel never rendered | Component fully built but not wired into App.jsx | Wasted work; users don't see a feature that's 90% done | High |
| 4 | Test coverage ~20% | 2 empty test files, 2 minimal; no exporter/analytics tests | Can't refactor safely; regressions go unnoticed | High |
| 5 | docker-compose.yml empty | Users must manually install InfluxDB, Prometheus, Grafana, Ollama | Getting started takes 30+ minutes instead of one command | High |
| 6 | No API authentication | All endpoints are public, no auth at all | Anyone on the network can change targets, reset events, read data | **High** |
| 7 | No exporter retry/buffering | InfluxDB write fails silently — data lost | Unreliable during network blips | Medium |
| 8 | AI analyzer not configurable | Ollama URL and model hardcoded in source | Users can't use a different model or remote Ollama instance | Medium |
| 9 | No multi-target monitoring | Agent monitors one ping target at a time | Users monitoring multiple hosts must run multiple agents | Medium |
| 10 | No structured logging | Text-based logs only | Can't integrate with log aggregators (ELK, Loki) | Low |
| 11 | Analytics mostly stubs | Only StabilityAnalyzer; scoring and latency_stats empty | No SLA tracking, percentiles, or quality scores | Medium |
| 12 | Frontend hardcoded to localhost | API_BASE = "http://localhost:8000" in App.jsx | Dashboard can't connect to remote agent without code change | Medium |
| 13 | InfluxDB token in plain text config | Token stored in config.yaml without encryption | Credentials exposed in version control or file access | Medium |

### Feature Proposals

#### Feature 1: Server-Side Metrics History

- **Problem:** Dashboard chart data is accumulated client-side (max 30 points) and lost on every page refresh.
- **Proposal:** Add an in-memory ring buffer in the Agent (deque of last N cycles) and expose it via `/api/metrics/history`. When InfluxDB is enabled, support time-range queries.
- **User Story:** As a network engineer, I want metrics history to persist across page refreshes, so that I don't lose visibility when switching browser tabs.
- **Acceptance Criteria:**
  - [ ] Agent stores last 200 metric snapshots in memory
  - [ ] History buffer uses target-keyed storage (`{target: deque}`) to support future multi-target without rewrite
  - [ ] `/api/metrics/history` returns the full buffer with timestamps
  - [ ] Frontend loads history on page open (not just from polling start)
  - [ ] Frontend merges server history with live polling data (server history replaces client buffer on load; polling appends; dedup by timestamp)
  - [ ] History survives frontend refresh but not agent restart
- **Scope:** In-memory buffer only. Persistent storage via InfluxDB query is out of scope (Phase 2). Single-agent only — multi-agent deployments require InfluxDB query-based history (Phase 2).
- **Dependencies:** None

#### Feature 2: Threshold-Based Alerting

- **Problem:** Events are tracked (timeouts, packet loss, jitter) but there's no way to define thresholds or get notified. AlertsPanel exists but is never rendered.
- **Proposal:** Add configurable alert rules (latency > X, packet_loss > Y) that generate alerts with severity levels. Wire AlertsPanel into the dashboard. Expose alerts via API.
- **User Story:** As a network operator, I want to define alert thresholds for latency and packet loss, so that I'm notified when the network degrades beyond acceptable limits.
- **Acceptance Criteria:**
  - [ ] Alert thresholds configurable in config.yaml
  - [ ] Alerts generated when metrics exceed thresholds
  - [ ] Alerts have severity: critical/warning/info
  - [ ] `/api/alerts` endpoint returns active alerts with schema: `{id, severity, metric, threshold, actual_value, message, timestamp, acknowledged}`
  - [ ] AlertsPanel rendered in dashboard with real alert data
  - [ ] Alerts clear automatically when metric stays normal for N consecutive cycles (default 3) to prevent alert storms on flapping metrics
- **Scope:** In-app alerts only. Webhook/email/Slack notifications are Phase 2.
- **Dependencies:** None (AlertsPanel already built)

#### Feature 3: Docker Compose Full Stack

- **Problem:** Getting started requires manually installing InfluxDB, Prometheus, Grafana, and Ollama. The docker-compose.yml is empty.
- **Proposal:** Implement docker-compose.yml with all services with proper networking, volumes, and env vars.
- **User Story:** As a new user, I want to run `docker compose up` and have the entire monitoring stack running, so that I can evaluate NetMonitor in under 5 minutes.
- **Acceptance Criteria:**
  - [ ] `docker compose up` starts all services
  - [ ] InfluxDB pre-configured with bucket and org
  - [ ] Prometheus scrapes NetMonitor /metrics endpoint
  - [ ] Grafana provisioned with data sources
  - [ ] Ollama service included with health check
  - [ ] Health checks for all services
  - [ ] All containers run as non-root user
  - [ ] Secrets (InfluxDB token, API keys) managed via `.env` file or Docker secrets — not hardcoded in config.yaml
- **Scope:** Development/evaluation stack. Production Kubernetes deployment is out of scope.
- **Dependencies:** None

#### Feature 4: Test Coverage to 70%+

- **Problem:** Test coverage is ~20%. Two test files are empty. Core paths like agent cycle, exporter writes, and health transitions are untested.
- **Proposal:** Write tests for the 4 untested/undertested areas: Agent cycle, exporters (mocked I/O), analytics, and API endpoints.
- **User Story:** As a developer, I want comprehensive tests, so that I can refactor and add features without regressions.
- **Acceptance Criteria:**
  - [ ] test_analytics.py — tests for StabilityAnalyzer
  - [ ] test_exporters.py — tests for InfluxExporter and PrometheusExporter with mocked backends
  - [ ] test_main.py — expanded to test full Agent cycle
  - [ ] API endpoint tests using FastAPI TestClient
  - [ ] `pytest --cov` reports >= 70% line coverage
- **Scope:** Unit and integration tests. E2E/Selenium tests are out of scope.
- **Dependencies:** None

#### Feature 5: Wire AlertsPanel into Dashboard

- **Problem:** The AlertsPanel React component is fully implemented but never rendered in App.jsx. Zero-effort win.
- **Proposal:** Import and render AlertsPanel in the dashboard layout, connected to events data.
- **User Story:** As a dashboard user, I want to see an alerts panel, so that network issues are surfaced prominently.
- **Acceptance Criteria:**
  - [ ] AlertsPanel rendered in App.jsx dashboard grid
  - [ ] Shows alerts from agent events as interim data source
  - [ ] Dismiss and clear-all buttons work
- **Scope:** Wire existing component. Building the alert rules engine is Feature 2.
- **Dependencies:** None

#### Feature 6: Configurable AI Analyzer

- **Problem:** Ollama URL (localhost:11434) and model (phi3) are hardcoded. Users can't use a different model or remote instance.
- **Proposal:** Add `ai` section to config.yaml and Settings model with url, model, and timeout fields.
- **User Story:** As a user with a different LLM setup, I want to configure the AI model and endpoint, so that I can use my preferred model.
- **Acceptance Criteria:**
  - [ ] config.yaml has ai: section with url, model, timeout fields
  - [ ] AIConfig Pydantic model with defaults matching current behavior
  - [ ] analyzer.py reads from settings instead of hardcoded constants
  - [ ] Env var overrides: OLLAMA_URL, OLLAMA_MODEL
- **Scope:** Configuration only. Multi-model support or cloud LLM integration is out of scope.
- **Dependencies:** None

#### Feature 7: Multi-Target Ping Monitoring

- **Problem:** Agent monitors only one ping target at a time. Switching targets loses data for the previous one.
- **Proposal:** Allow a list of ping targets in config. PingCollector runs against all targets per cycle, metrics tagged by target.
- **User Story:** As a network engineer monitoring multiple endpoints, I want to track latency to several hosts simultaneously.
- **Acceptance Criteria:**
  - [ ] ping.targets config accepts a list of hosts
  - [ ] Each cycle pings all configured targets
  - [ ] Metrics tagged with target label
  - [ ] Dashboard shows per-target metrics
  - [ ] Runtime add/remove targets via API
- **Scope:** Multiple ping targets. Multi-collector-type targets (HTTP, DNS) are out of scope.
- **Dependencies:** Feature 1 (history buffer needs per-target storage)

#### Feature 5b: Frontend API Base URL Fix

- **Problem:** `API_BASE = "http://localhost:8000"` is hardcoded in App.jsx (Gap #12). Dashboard cannot connect to a remote agent without changing source code.
- **Proposal:** Replace hardcoded URL with `window.location.origin` fallback or Vite environment variable (`VITE_API_BASE`).
- **User Story:** As a user deploying NetMonitor on a remote server, I want the dashboard to connect to the agent automatically without editing source code.
- **Acceptance Criteria:**
  - [ ] `API_BASE` reads from `import.meta.env.VITE_API_BASE` with fallback to `window.location.origin`
  - [ ] Docker Compose (Feature 3) sets the env var appropriately
  - [ ] No code changes needed for localhost development (default works)
- **Scope:** Environment variable only. Full frontend config system is out of scope.
- **Dependencies:** None

#### Feature 8: API Authentication

- **Problem:** All API endpoints are public. Anyone on the network can read metrics, change targets, reset events.
- **Proposal:** Add API key authentication via header (X-API-Key) with the key stored as an env var. Optional — disabled by default.
- **User Story:** As an operator deploying NetMonitor on a shared network, I want API endpoints protected.
- **Acceptance Criteria:**
  - [ ] API_KEY env var enables auth when set
  - [ ] All mutation endpoints (POST) require valid API key
  - [ ] Read endpoints optionally require key (configurable)
  - [ ] Missing API key returns `401 Unauthorized`; invalid API key returns `403 Forbidden`
  - [ ] API key minimum length: 32 characters; timing-safe comparison
  - [ ] No auth overhead when API_KEY is not set
- **Scope:** API key auth only. OAuth/JWT/RBAC is out of scope.
- **Dependencies:** None

#### Feature 9b: Analytics Stubs Resolution

- **Problem:** `scoring.py` and `latency_stats.py` are empty/near-empty stub files identified as Gap #11 but not addressed by any feature proposal. Empty files confuse contributors and represent unresolved technical debt.
- **Proposal:** Implement basic analytics: latency percentiles (p50/p95/p99) in `latency_stats.py` and a composite network quality score (0-100) in `scoring.py`.
- **User Story:** As a network engineer, I want percentile latency stats and a quality score, so that I can quickly assess network health beyond simple averages.
- **Acceptance Criteria:**
  - [ ] `latency_stats.py` computes p50, p95, p99 from metric history
  - [ ] `scoring.py` computes a 0-100 quality score based on latency, loss, and jitter
  - [ ] Both exposed via `/api/metrics` or `/api/analytics` endpoint
  - [ ] Tests for both modules in `test_analytics.py`
- **Scope:** Basic statistical analysis. ML-based anomaly detection is out of scope.
- **Dependencies:** Feature 1 (needs metric history buffer for percentile calculation)

### Prioritization

| # | Feature | User Value | Effort | Priority | Rationale |
|---|---------|-----------|--------|----------|-----------|
| 5 | Wire AlertsPanel | High | Very Low | P0 | Zero-effort win — component already built |
| 5b | Frontend API Base URL Fix | Medium | Very Low | P0 | Required for Docker/remote deployments; one-line fix |
| 1 | Metrics History Buffer | High | Low | P0 | Core workflow broken — lose data on refresh |
| 3 | Docker Compose Full Stack | High | Medium | P0 | First-run experience critical |
| 4 | Test Coverage 70%+ | High | Medium | P1 | Enables safe iteration |
| 2 | Threshold Alerting | High | Medium | P1 | Monitoring without alerts is just watching |
| 6 | Configurable AI | Medium | Low | P1 | Small effort, big flexibility |
| 9b | Analytics Stubs Resolution | Medium | Medium | P2 | Resolves empty stub debt; depends on F1 |
| 8 | API Authentication | High | Low | **P1** | Public mutation endpoints are a live vulnerability on any shared network |
| 7 | Multi-Target Monitoring | High | High | P2 | High value but significant changes |

### Roadmap

#### Phase 1 — Foundation (P0)

1. **Wire AlertsPanel** — Render existing component in App.jsx, connect to events data. (~30 min)
1b. **Frontend API Base URL Fix** — Replace hardcoded `API_BASE` with env var + fallback. (~15 min)
2. **Metrics History Buffer** — Add target-keyed deque(maxlen=200) to Agent, update /api/metrics/history, update frontend with merge strategy. (~2-3 hours)
3. **Docker Compose** — Full docker-compose.yml with netmonitor + influxdb + prometheus + grafana + ollama. Non-root containers, secrets via `.env`. (~3-4 hours)

**Shippable outcome:** User can `docker compose up`, open dashboard, see live charts that survive refresh, and see alerts.

#### Phase 2 — Core Experience (P1)

4. **Test Coverage 70%+** — Tests for agent cycle, exporters, analytics, API endpoints. (~4-6 hours)
5. **Threshold Alerting** — Alert rules in config, severity engine with hysteresis, /api/alerts endpoint with defined schema, AlertsPanel with real data. (~4-6 hours)
6. **Configurable AI** — AIConfig model, config.yaml section, env var overrides. (~1-2 hours)
7. **API Authentication** — API key auth via X-API-Key header, 401/403 semantics, timing-safe comparison. (~2-3 hours)

**Shippable outcome:** Tested, alerting on real thresholds, AI configurable per environment, API secured.

#### Phase 3 — Growth (P2+)

8. **Multi-Target Monitoring** — List of ping targets, per-target metrics, dashboard with target selector UX. (~6-8 hours)
9. **Exporter Retry/Buffering** — InfluxDB client built-in retry options. (~1-2 hours)
10. **Analytics Stubs Resolution** — Implement latency percentiles (p50/p95/p99) and composite quality score (0-100). (~4-6 hours)

**Shippable outcome:** Production-grade monitoring with resilience, multi-target support, and rich analytics.

### Verdict

NetMonitor is a **solid alpha**. The core engine, dashboard, and plugin architecture work well. The biggest gaps are completion gaps, not design flaws. Phase 1 items would transform the user experience with relatively low effort.

---

### Review Board Addendum (2026-03-09)

**Review type:** Multi-role review board (5 roles: Code Reviewer, Architect, API Designer, Frontend Developer, Security Auditor)

**Decision:** CONDITIONALLY APPROVED — All 5 roles voted APPROVE WITH CONDITIONS.

**Key changes applied:**
1. Added **Gap #0: Command injection** via `/api/target` — user input passed to `subprocess.run` without validation (Critical severity)
2. Elevated **Gap #6 (API auth) severity** from Medium to High
3. Elevated **Feature 8 (API Auth) from P2 to P1** — moved into Phase 2 roadmap
4. Updated **Feature 1 AC** — target-keyed storage, frontend merge strategy, single-agent limitation noted
5. Updated **Feature 2 AC** — defined alert response schema, added hysteresis for alert auto-clear
6. Updated **Feature 3 AC** — added Ollama service, non-root containers, secrets management
7. Updated **Feature 8 AC** — 401/403 HTTP semantics, key length minimum, timing-safe comparison
8. Added **Feature 5b** — Frontend API base URL fix (P0, ~15 min)
9. Added **Feature 9b** — Analytics stubs resolution with concrete deliverables (P2)
10. Added **Gap #13** — InfluxDB token stored in plain text config
