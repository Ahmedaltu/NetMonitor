# Configuration Guide

> Complete configuration reference for NetMonitor

## 📄 Configuration File Overview

NetMonitor uses a YAML-based configuration system with Pydantic validation. The main configuration file is located at `app/config/config.yaml`.

---

## 🔧 Complete Configuration Reference

### Basic Structure

```yaml
# Agent identification and metadata
agent:
  id: string              # Unique agent identifier
  location: string        # Physical/logical location
  environment: string     # deployment environment (dev/staging/prod)

# Collection interval in seconds
interval: integer

# Target configuration
targets:
  ping:
    - address: string     # IP or hostname
      label: string       # Friendly name
  
# Exporter configurations
exporters:
  influx:
    enabled: boolean
    url: string
    org: string
    bucket: string
    token_env: string     # Environment variable name for token
  
  prometheus:
    enabled: boolean
    port: integer
    path: string

# AI/LLM configuration
ai:
  enabled: boolean
  ollama_url: string
  model: string

# Logging configuration
logging:
  level: string           # DEBUG, INFO, WARNING, ERROR
  format: string
  file: string
```

---

## 🎯 Agent Configuration

### Basic Agent Settings

```yaml
agent:
  id: "agent-001"
  location: "datacenter-1"
  environment: "production"
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | - | Unique identifier for this agent instance |
| `location` | string | No | "unknown" | Physical or logical location identifier |
| `environment` | string | No | "dev" | Deployment environment (dev/staging/prod) |

**Example Configurations:**

**Home Network:**
```yaml
agent:
  id: "home-monitor-01"
  location: "home-network"
  environment: "personal"
```

**Multi-Agent Deployment:**
```yaml
# Agent 1 - US East
agent:
  id: "agent-us-east-01"
  location: "aws-us-east-1"
  environment: "production"

# Agent 2 - EU West
agent:
  id: "agent-eu-west-01"
  location: "aws-eu-west-1"
  environment: "production"
```

---

## ⏱️ Collection Interval

```yaml
interval: 10  # seconds
```

**Recommended Values:**

| Use Case | Interval | Reasoning |
|----------|----------|-----------|
| Development | 10s | Quick feedback |
| Testing | 5s | High-frequency data |
| Production | 30-60s | Balanced resource usage |
| Low-frequency | 300s (5min) | Minimal overhead |

**Performance Impact:**

- **10s interval**: ~8,640 data points/day
- **60s interval**: ~1,440 data points/day
- **300s interval**: ~288 data points/day

> **Tip**: Start with 30s in production, adjust based on needs

---

## 🎯 Target Configuration

### Ping Targets

```yaml
targets:
  ping:
    - address: "8.8.8.8"
      label: "Google DNS"
      enabled: true
    
    - address: "1.1.1.1"
      label: "Cloudflare DNS"
      enabled: true
    
    - address: "api.example.com"
      label: "Production API"
      enabled: true
      timeout: 5
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `address` | string | Yes | - | IP address or hostname |
| `label` | string | No | address | Friendly name for dashboard |
| `enabled` | boolean | No | true | Enable/disable this target |
| `timeout` | integer | No | 3 | Ping timeout in seconds |

### Dynamic Target Changes

Targets can be changed at runtime via API:

```bash
curl -X POST http://localhost:8000/api/target \
  -H "Content-Type: application/json" \
  -d '{"target": "1.1.1.1"}'
```

---

## 📊 Exporter Configuration

### InfluxDB Exporter

```yaml
exporters:
  influx:
    enabled: true
    url: "http://localhost:8086"
    org: "net-monitor"
    bucket: "network"
    token_env: "INFLUX_TOKEN"
    batch_size: 100
    flush_interval: 1000  # milliseconds
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | false | Enable InfluxDB export |
| `url` | string | Yes* | - | InfluxDB server URL |
| `org` | string | Yes* | - | InfluxDB organization |
| `bucket` | string | Yes* | - | Target bucket name |
| `token_env` | string | No | "INFLUX_TOKEN" | Env var containing auth token |
| `batch_size` | integer | No | 100 | Batch write size |
| `flush_interval` | integer | No | 1000 | Max batch wait time (ms) |

*Required if enabled=true

**Setup Steps:**

1. **Create InfluxDB bucket:**
```bash
influx bucket create -n network -o net-monitor
```

2. **Generate token:**
```bash
influx auth create --org net-monitor --all-access
```

3. **Set environment variable:**
```bash
# Windows PowerShell
$env:INFLUX_TOKEN="your-token-here"

# Linux/macOS
export INFLUX_TOKEN="your-token-here"
```

4. **Enable in config:**
```yaml
exporters:
  influx:
    enabled: true
    url: "http://localhost:8086"
    org: "net-monitor"
    bucket: "network"
```

### Prometheus Exporter

```yaml
exporters:
  prometheus:
    enabled: true
    port: 8000
    path: "/metrics"
    namespace: "netmonitor"
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | true | Enable Prometheus export |
| `port` | integer | Yes* | 8000 | Metrics endpoint port |
| `path` | string | No | "/metrics" | Metrics endpoint path |
| `namespace` | string | No | "netmonitor" | Metric namespace prefix |

*Required if enabled=true

**Prometheus Scrape Configuration:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'netmonitor'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          environment: 'production'
          location: 'datacenter-1'
```

**Available Metrics:**

```
# Latency metrics
netmonitor_latency_ms{agent_id="agent-001"}
netmonitor_latency_mean_ms{agent_id="agent-001"}
netmonitor_latency_stddev_ms{agent_id="agent-001"}

# Packet loss
netmonitor_packet_loss_percent{agent_id="agent-001"}

# Jitter
netmonitor_jitter_ms{agent_id="agent-001"}

# Health
netmonitor_agent_health{agent_id="agent-001",state="running"}
```

---

## 🧠 AI Configuration

```yaml
ai:
  enabled: true
  ollama_url: "http://localhost:11434"
  model: "phi3"
  timeout: 30
  max_retries: 3
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | false | Enable AI analysis |
| `ollama_url` | string | Yes* | - | Ollama server URL |
| `model` | string | Yes* | "phi3" | LLM model to use |
| `timeout` | integer | No | 30 | Request timeout (seconds) |
| `max_retries` | integer | No | 3 | Max retry attempts |

*Required if enabled=true

**Supported Models:**
- `phi3` - Recommended, good balance
- `llama2` - Larger, more capable
- `mistral` - Fast, efficient
- `codellama` - Code-focused

**Setup Ollama:**

```bash
# Pull model
ollama pull phi3

# Verify running
curl http://localhost:11434/api/tags
```

---

## 📝 Logging Configuration

```yaml
logging:
  level: "INFO"
  format: "detailed"
  file: "logs/netmonitor.log"
  rotation: "1 day"
  retention: 7
  console: true
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | string | "INFO" | Log level (DEBUG/INFO/WARNING/ERROR) |
| `format` | string | "detailed" | Log format (simple/detailed/json) |
| `file` | string | null | Log file path (null = no file logging) |
| `rotation` | string | "1 day" | Rotation interval |
| `retention` | integer | 7 | Days to keep old logs |
| `console` | boolean | true | Enable console output |

**Log Levels:**

```yaml
# Development
logging:
  level: "DEBUG"

# Production
logging:
  level: "INFO"

# Minimal logging
logging:
  level: "WARNING"
```

**Log Formats:**

**Simple:**
```
2026-03-05 21:30:00 - INFO - Agent agent-001 starting...
```

**Detailed:**
```
2026-03-05T21:30:00.123Z [INFO] app.core.agent - Agent agent-001 starting... (agent.py:95)
```

**JSON:**
```json
{"timestamp":"2026-03-05T21:30:00.123Z","level":"INFO","module":"app.core.agent","message":"Agent agent-001 starting...","line":95}
```

---

## 🔒 Security Configuration

### Environment Variables

Sensitive data should be stored in environment variables:

```yaml
exporters:
  influx:
    token_env: "INFLUX_TOKEN"  # References $INFLUX_TOKEN
```

**Setting Environment Variables:**

```bash
# Windows PowerShell
$env:INFLUX_TOKEN="your-token"
$env:OLLAMA_API_KEY="your-key"

# Linux/macOS
export INFLUX_TOKEN="your-token"
export OLLAMA_API_KEY="your-key"

# .env file (with python-dotenv)
INFLUX_TOKEN=your-token
OLLAMA_API_KEY=your-key
```

### API Security

```yaml
api:
  enabled: true
  auth:
    enabled: true
    type: "api_key"  # or "jwt"
    api_key_env: "API_KEY"
  
  cors:
    enabled: true
    origins:
      - "http://localhost:5173"
      - "https://dashboard.example.com"
  
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

---

## 📦 Complete Example Configurations

### Development Environment

```yaml
agent:
  id: "dev-agent-01"
  location: "laptop"
  environment: "dev"

interval: 10

exporters:
  influx:
    enabled: false
  
  prometheus:
    enabled: true
    port: 8000

ai:
  enabled: false

logging:
  level: "DEBUG"
  console: true
  file: null
```

### Production Environment

```yaml
agent:
  id: "prod-agent-us-east-01"
  location: "aws-us-east-1"
  environment: "production"

interval: 60

targets:
  ping:
    - address: "8.8.8.8"
      label: "Google DNS"
    - address: "api.production.com"
      label: "Production API"

exporters:
  influx:
    enabled: true
    url: "http://influxdb.internal:8086"
    org: "production"
    bucket: "network-metrics"
    token_env: "INFLUX_TOKEN"
  
  prometheus:
    enabled: true
    port: 9090

ai:
  enabled: true
  ollama_url: "http://ollama.internal:11434"
  model: "phi3"

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/netmonitor/app.log"
  rotation: "1 day"
  retention: 30
  console: false
```

### High-Frequency Monitoring

```yaml
agent:
  id: "hf-monitor-01"
  location: "edge-node"
  environment: "testing"

interval: 5  # High frequency

exporters:
  influx:
    enabled: true
    batch_size: 50  # Smaller batches
    flush_interval: 500  # Faster flush
  
  prometheus:
    enabled: true

logging:
  level: "WARNING"  # Reduce log volume
```

---

## 🔄 Configuration Reloading

### Manual Reload

Restart the agent to apply configuration changes:

```bash
# Kill existing process
pkill -f "python -m app.main"

# Restart
python -m app.main
```

### Planned: Hot Reload

```bash
# Send SIGHUP to reload config
kill -HUP <pid>
```

---

## ✅ Configuration Validation

### Validate Configuration

```python
from app.config.loader import load_settings

try:
    settings = load_settings()
    print("✓ Configuration valid")
    print(f"Agent ID: {settings.agent.id}")
    print(f"Interval: {settings.interval}s")
except Exception as e:
    print(f"✗ Configuration error: {e}")
```

### Common Validation Errors

**Missing required fields:**
```
ValidationError: agent.id: field required
```

**Invalid types:**
```
ValidationError: interval: value is not a valid integer
```

**Out of range:**
```
ValidationError: interval: ensure this value is greater than 0
```

---

## 🔗 Related Documentation

- **[Quickstart Guide](QUICKSTART.md)** - Getting started
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Exporters](EXPORTERS.md)** - Exporter details
- **[API Reference](API.md)** - Runtime configuration via API