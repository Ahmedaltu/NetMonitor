# NetMonitor — Project Memory

## What this project is
NetMonitor is a modular, async-first network monitoring agent and dashboard. It collects real-time network telemetry using plugin-based collectors, exports metrics to InfluxDB and Prometheus, and provides AI-assisted diagnostics via a local LLM. The system features a FastAPI backend, React dashboard, and is designed for extensibility, observability, and production readiness.

## Live URLs
- [Local API] http://localhost:8000
- [Local Dashboard] http://localhost:5173
- [Prometheus Metrics] http://localhost:8000/metrics
- [API Docs] http://localhost:8000/docs

## Stack
- Python 3.10+ (FastAPI, asyncio, Pydantic, Uvicorn)
- React 18+ (Vite, TailwindCSS, Chart.js)
- InfluxDB 2.x (time-series storage)
- Prometheus (metrics scraping)
- Docker & Docker Compose
- Ollama (optional, for AI diagnostics)
- PyYAML, requests, psutil

## Environment Variables
- AGENT_ID: Unique agent identifier
- INTERVAL: Collection interval (seconds)
- PING_TARGET: Default ping target
- PING_COUNT: Number of pings per cycle
- INFLUX_URL: InfluxDB server URL
- INFLUX_TOKEN: InfluxDB API token (secret)
- OLLAMA_URL: Local LLM API endpoint
- OLLAMA_MODEL: LLM model name
- API_HOST: API server host
- API_PORT: API server port
- NETMONITOR_API_KEY: API key for protected endpoints

## Project Structure
- app/main.py — Entrypoint, starts agent and API
- app/api/server.py — FastAPI server, all REST endpoints
- app/ai/analyzer.py — AI/LLM analytics and InfluxDB summary
- app/collectors/ — Plugin-based collectors (ping, http, dns, traceroute, etc.)
- app/exporters/ — Exporters for InfluxDB, Prometheus
- app/core/ — Agent core, health, plugin manager, scheduler
- app/config/ — Pydantic models, YAML loader, config.yaml
- app/notifications/ — Webhook notifier
- app/utils/ — Logger, exceptions
- frontend/ — React dashboard (App.jsx, components, index.html)
- docker/ — Dockerfile, docker-compose, Prometheus config, Grafana provisioning
- docs/ — Architecture, API, configuration, deployment, design, troubleshooting, FAQ
- tests/ — Pytest-based backend tests
- requirements.txt — Python dependencies
- README.md — Project overview

## API Endpoints
- GET /health → Agent health and status
- GET /api/agent/status → Agent ID and health state
- GET /api/metrics → Latest collected metrics
- GET /api/metrics/history → Metrics history for charts
- GET /api/events → Network events (timeouts, loss, jitter)
- GET /api/alerts → Active alerts
- POST /api/alerts/dismiss → Dismiss alert (API key required)
- POST /api/alerts/clear → Clear all alerts (API key required)
- POST /api/events/reset → Reset event counters (API key required)
- GET /api/target → Current ping target
- GET /api/targets → All monitored targets
- POST /api/targets/add → Add monitoring target (API key required)
- POST /api/targets/remove → Remove target (API key required)
- POST /api/target → Set current target (API key required)
- POST /api/traceroute → Run traceroute (API key required)
- GET /api/traceroute/latest → Last traceroute result
- GET /explain → AI analysis of recent metrics
- GET /metrics → Prometheus metrics

## Architecture Decisions
- Async-first design for high concurrency and performance
- Plugin-based collectors/exporters for extensibility
- Typed config with Pydantic and YAML for safety
- Local LLM integration for privacy-preserving AI
- Dual export: push (InfluxDB) and pull (Prometheus)
- React dashboard for real-time UX
- Docker for reproducible deployment

## Known Issues & Solutions
| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill process or change API_PORT |
| InfluxDB token missing | Set INFLUX_TOKEN env var |
| AI analysis fails | Check Ollama is running and reachable |
| Metrics missing | Check collectors and exporters logs |
| CORS errors in frontend | Ensure API and dashboard run on allowed origins |

## Coding Conventions
- Use async/await for all I/O and network code
- Type all config and API models with Pydantic
- One collector/exporter per file, inherit from base class
- Use logging for all errors and warnings
- Never hardcode secrets or tokens
- Always validate user input (API, config)
- Write docstrings for all public functions/classes
- Use TailwindCSS for frontend styling
- Keep API response formats consistent
- One focused fix per commit

## Recent Changes
- [2026-03-24] Initial Claude agent system setup and project memory
- [2026-03-23] Added AI analysis endpoint and frontend panel
- [2026-03-22] Improved Prometheus exporter and metrics history
- [2026-03-21] Refactored config loader for env overrides
- [2026-03-20] Added Docker Compose and Grafana provisioning
- [2026-03-19] Enhanced collector plugin system
- [2026-03-18] Added alerting and event tracking
- [2026-03-17] Created React dashboard with live charts
- [2026-03-16] Added InfluxDB exporter and health tracking
- [2026-03-15] Project scaffolding and initial commit

## Next Steps
- [ ] Add more collector plugins (SNMP, HTTP, DNS)
- [ ] Improve test coverage for backend and frontend
- [ ] Add user authentication for dashboard
- [ ] Enhance AI analysis with anomaly detection
- [ ] Document custom exporter/collector development
- [ ] Add Grafana dashboards and alerting
- [ ] Optimize frontend performance
- [ ] Harden API security and rate limiting
- [ ] Add deployment scripts for cloud providers
- [ ] Review and refactor code for maintainability
