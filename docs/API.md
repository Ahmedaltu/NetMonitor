# API Reference

> Complete REST API documentation for NetMonitor

## 🌐 API Overview

NetMonitor provides a RESTful API built with FastAPI for real-time monitoring, control, and diagnostics.

**Base URL:** `http://localhost:8000` (default)

**Features:**
- Real-time metrics access
- Agent health monitoring
- AI-powered diagnostics
- Runtime configuration
- Prometheus metrics endpoint
- CORS-enabled for frontend integration

---

## 📋 Table of Contents

- [Health & Status Endpoints](#health--status-endpoints)
- [Metrics Endpoints](#metrics-endpoints)
- [Control Endpoints](#control-endpoints)
- [AI Analysis Endpoints](#ai-analysis-endpoints)
- [Prometheus Endpoints](#prometheus-endpoints)
- [Event Endpoints](#event-endpoints)

---

## 🏥 Health & Status Endpoints

### GET /health

Get agent health and operational status.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "agent_id": "agent-001",
  "state": "running",
  "last_error": null,
  "last_cycle": "2026-03-05T21:30:00.000Z",
  "consecutive_failures": 0,
  "uptime_seconds": 3600
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Unique agent identifier |
| `state` | string | Current state: `starting`, `running`, `degraded`, `error`, `stopped` |
| `last_error` | string\|null | Last error message if any |
| `last_cycle` | string | ISO timestamp of last collection cycle |
| `consecutive_failures` | integer | Count of consecutive failed cycles |
| `uptime_seconds` | integer | Seconds since agent started |

**Agent States:**

| State | Description |
|-------|-------------|
| `starting` | Agent initializing |
| `running` | Normal operation |
| `degraded` | Some collectors failing |
| `error` | Critical failure |
| `stopped` | Agent shut down |

---

### GET /api/agent/status

Get agent operational status with additional context.

**Request:**
```bash
curl http://localhost:8000/api/agent/status?window=5m
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `window` | string | No | "5m" | Time window context |

**Response:**
```json
{
  "agentId": "agent-001",
  "healthState": "running",
  "window": "5m",
  "location": "datacenter-1",
  "environment": "production"
}
```

---

## 📊 Metrics Endpoints

### GET /api/metrics

Get the most recent collected metrics.

**Request:**
```bash
curl http://localhost:8000/api/metrics
```

**Response:**
```json
{
  "latency": 15.3,
  "packet_loss": 0,
  "jitter": 2.1,
  "delay_spread": 5.2,
  "rolling_mean_latency": 14.8,
  "rolling_std_latency": 1.2,
  "timestamp": "2026-03-05T21:30:00.000Z",
  "agent_id": "agent-001"
}
```

**Metric Descriptions:**

| Metric | Unit | Description |
|--------|------|-------------|
| `latency` | ms | Current ping latency |
| `packet_loss` | % | Packet loss percentage |
| `jitter` | ms | Latency variation |
| `delay_spread` | ms | Max - min latency in window |
| `rolling_mean_latency` | ms | Moving average latency |
| `rolling_std_latency` | ms | Standard deviation of latency |
| `bytes_sent` | bytes | Network bytes sent |
| `bytes_recv` | bytes | Network bytes received |

---

### GET /api/metrics/history

Get historical metrics data.

**Request:**
```bash
curl http://localhost:8000/api/metrics/history?limit=20
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Number of data points |
| `start` | string | No | - | Start timestamp (ISO 8601) |
| `end` | string | No | now | End timestamp (ISO 8601) |

**Response:**
```json
{
  "current": {
    "latency": 15.3,
    "packet_loss": 0,
    "jitter": 2.1
  },
  "history": [
    {
      "timestamp": "2026-03-05T21:30:00.000Z",
      "latency": 15.3,
      "packet_loss": 0,
      "jitter": 2.1
    },
    {
      "timestamp": "2026-03-05T21:29:00.000Z",
      "latency": 14.8,
      "packet_loss": 0,
      "jitter": 1.9
    }
  ]
}
```

---

### GET /api/metrics/summary

Get statistical summary of metrics.

**Request:**
```bash
curl http://localhost:8000/api/metrics/summary?window=1h
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `window` | string | No | "1h" | Time window (5m, 1h, 24h) |

**Response:**
```json
{
  "window": "1h",
  "latency": {
    "mean": 15.2,
    "min": 12.1,
    "max": 23.4,
    "p50": 14.8,
    "p95": 19.2,
    "p99": 22.1,
    "samples": 360
  },
  "packet_loss": {
    "mean": 0.1,
    "max": 2.0,
    "samples": 360
  }
}
```

---

## 🎮 Control Endpoints

### POST /api/target

Change the ping target at runtime.

**Request:**
```bash
curl -X POST http://localhost:8000/api/target \
  -H "Content-Type: application/json" \
  -d '{"target": "1.1.1.1"}'
```

**Request Body:**
```json
{
  "target": "1.1.1.1",
  "label": "Cloudflare DNS"
}
```

**Response:**
```json
{
  "success": true,
  "previous_target": "8.8.8.8",
  "new_target": "1.1.1.1",
  "message": "Ping target changed successfully"
}
```

---

### GET /api/target

Get current ping target.

**Request:**
```bash
curl http://localhost:8000/api/target
```

**Response:**
```json
{
  "target": "8.8.8.8",
  "label": "Google DNS",
  "active_since": "2026-03-05T20:00:00.000Z"
}
```

---

### POST /api/interval

Change collection interval at runtime.

**Request:**
```bash
curl -X POST http://localhost:8000/api/interval \
  -H "Content-Type: application/json" \
  -d '{"interval": 30}'
```

**Request Body:**
```json
{
  "interval": 30
}
```

**Response:**
```json
{
  "success": true,
  "previous_interval": 10,
  "new_interval": 30,
  "message": "Collection interval updated"
}
```

---

### POST /api/events/reset

Reset event counters.

**Request:**
```bash
curl -X POST http://localhost:8000/api/events/reset
```

**Response:**
```json
{
  "success": true,
  "message": "Event counters reset"
}
```

---

## 🧠 AI Analysis Endpoints

### GET /explain

Get AI-powered network analysis and diagnostics.

**Request:**
```bash
curl http://localhost:8000/explain?window=30
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `window` | integer | No | 30 | Analysis window in minutes |

**Response:**
```json
{
  "window_minutes": 30,
  "summary": {
    "latency": {
      "mean": 15.2,
      "max": 23.4,
      "min": 12.1,
      "samples": 180
    },
    "packet_loss": {
      "mean": 0.0,
      "max": 0.0,
      "samples": 180
    }
  },
  "analysis": "Network performance is stable with consistent latency averaging 15.2ms. No packet loss detected. Jitter is within acceptable range, indicating a healthy connection. The network appears suitable for real-time applications."
}
```

**Analysis Components:**

1. **Summary**: Statistical overview of recent metrics
2. **Analysis**: Natural language interpretation by LLM
3. **Insights**: Actionable recommendations

**Prerequisites:**
- InfluxDB must be configured and running
- Ollama must be running with model loaded
- AI must be enabled in configuration

---

### POST /explain/ask

Ask specific questions about network performance.

**Request:**
```bash
curl -X POST http://localhost:8000/explain/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is latency spiking?", "window": 15}'
```

**Request Body:**
```json
{
  "question": "Why is latency spiking?",
  "window": 15,
  "include_context": true
}
```

**Response:**
```json
{
  "question": "Why is latency spiking?",
  "answer": "Latency spikes observed in the last 15 minutes correlate with increased packet loss (2-3%). This suggests network congestion or path issues. Consider checking: 1) Local network load, 2) ISP status, 3) Routing path changes.",
  "confidence": 0.85,
  "data_points": 90
}
```

---

## 📈 Prometheus Endpoints

### GET /metrics

Prometheus-compatible metrics exposition.

**Request:**
```bash
curl http://localhost:8000/metrics
```

**Response:**
```
# HELP netmonitor_latency_ms Current network latency in milliseconds
# TYPE netmonitor_latency_ms gauge
netmonitor_latency_ms{agent_id="agent-001"} 15.3

# HELP netmonitor_packet_loss_percent Packet loss percentage
# TYPE netmonitor_packet_loss_percent gauge
netmonitor_packet_loss_percent{agent_id="agent-001"} 0.0

# HELP netmonitor_jitter_ms Network jitter in milliseconds
# TYPE netmonitor_jitter_ms gauge
netmonitor_jitter_ms{agent_id="agent-001"} 2.1

# HELP netmonitor_agent_health Agent health status
# TYPE netmonitor_agent_health gauge
netmonitor_agent_health{agent_id="agent-001",state="running"} 1
```

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'netmonitor'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
```

---

## 📡 Event Endpoints

### GET /api/events

Get network events (timeouts, packet loss, jitter).

**Request:**
```bash
curl http://localhost:8000/api/events?limit=10
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Max events to return |
| `type` | string | No | all | Event type filter |

**Response:**
```json
{
  "timeouts": 5,
  "packet_loss_count": 2,
  "high_jitter_count": 1,
  "recent": [
    {
      "type": "packet_loss",
      "time": "21:30:00",
      "message": "2.5% packet loss to 8.8.8.8"
    },
    {
      "type": "timeout",
      "time": "21:25:15",
      "message": "Timeout to 8.8.8.8"
    },
    {
      "type": "high_jitter",
      "time": "21:20:30",
      "message": "High jitter (15.2ms) to 8.8.8.8"
    }
  ]
}
```

**Event Types:**

| Type | Description | Threshold |
|------|-------------|-----------|
| `timeout` | Ping timeout occurred | No response |
| `packet_loss` | Packet loss detected | >0% |
| `high_jitter` | High jitter detected | >10ms |

---

### GET /api/events/stats

Get event statistics over time window.

**Request:**
```bash
curl http://localhost:8000/api/events/stats?window=1h
```

**Response:**
```json
{
  "window": "1h",
  "total_events": 8,
  "timeouts": 5,
  "packet_loss_events": 2,
  "high_jitter_events": 1,
  "event_rate": 0.133,
  "most_common": "timeout"
}
```

---

## 💡 Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Get current metrics
response = requests.get(f"{BASE_URL}/api/metrics")
metrics = response.json()
print(f"Latency: {metrics['latency']}ms")

# Change target
response = requests.post(
    f"{BASE_URL}/api/target",
    json={"target": "1.1.1.1"}
)
print(response.json())

# Get AI analysis
response = requests.get(f"{BASE_URL}/explain?window=30")
analysis = response.json()
print(f"Analysis: {analysis['analysis']}")
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = 'http://localhost:8000';

// Fetch metrics
async function getMetrics() {
  const response = await fetch(`${BASE_URL}/api/metrics`);
  const metrics = await response.json();
  return metrics;
}

// Change target
async function changeTarget(target: string) {
  const response = await fetch(`${BASE_URL}/api/target`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target })
  });
  return response.json();
}

// Get AI analysis
async function getAnalysis(window: number = 30) {
  const response = await fetch(`${BASE_URL}/explain?window=${window}`);
  return response.json();
}
```

### Shell Script Example

```bash
#!/bin/bash

API_URL="http://localhost:8000"

# Function to get metrics
get_metrics() {
  curl -s "$API_URL/api/metrics" | jq .
}

# Function to check health
check_health() {
  curl -s "$API_URL/health" | jq -r '.state'
}

# Monitor loop
while true; do
  STATE=$(check_health)
  if [ "$STATE" != "running" ]; then
    echo "WARNING: Agent state is $STATE"
  fi
  
  LATENCY=$(curl -s "$API_URL/api/metrics" | jq -r '.latency')
  echo "Current latency: ${LATENCY}ms"
  
  sleep 30
done
```

---

## 🔒 Authentication (Future)

### API Key Authentication

**Coming soon:**

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/metrics
```

### JWT Authentication

**Coming soon:**

```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -d '{"username":"user","password":"pass"}' | jq -r '.token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/metrics
```

---

## ⚡ Rate Limiting

**Current:** No rate limiting
**Planned:** 60 requests/minute per client

---

## 🔗 Related Documentation

- **[Quickstart Guide](QUICKSTART.md)** - Getting started
- **[Configuration](CONFIGURATION.md)** - API configuration
- **[AI Integration](AI_INTEGRATION.md)** - AI endpoints details
- **[Frontend](FRONTEND.md)** - Dashboard integration