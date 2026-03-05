# NetMonitor Quickstart Guide

> Get NetMonitor up and running in 10 minutes

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+**
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Node.js 18+** (for frontend dashboard, optional)

### Optional Services

- **InfluxDB 2.x** - For time-series data storage
- **Ollama** - For AI-powered diagnostics
- **Docker & Docker Compose** - For containerized deployment

---

## 🚀 Quick Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/netmonitor.git
cd netmonitor
```

### 2️⃣ Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure the Agent

Create or edit `app/config/config.yaml`:

```yaml
agent:
  id: "agent-001"
  location: "home"
  environment: "dev"

interval: 10  # Collection interval in seconds

exporters:
  influx:
    enabled: false  # Set to true if using InfluxDB
    url: "http://localhost:8086"
    org: "net-monitor"
    bucket: "network"

  prometheus:
    enabled: true
    port: 8000
```

### 5️⃣ Run the Agent

```bash
python -m app.main
```

You should see output like:

```
INFO - Starting FastAPI server...
INFO - Agent agent-001 starting...
INFO - Starting Agent background task...
```

---

## ✅ Verify Installation

### Check Health Endpoint

Open your browser or use curl:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "agent_id": "agent-001",
  "state": "running",
  "last_error": null,
  "last_cycle": "2026-03-05T21:30:00",
  "consecutive_failures": 0
}
```

### Check Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics
```

Response:

```json
{
  "latency": 15.3,
  "packet_loss": 0,
  "jitter": 2.1,
  "delay_spread": 5.2,
  "rolling_mean_latency": 14.8,
  "rolling_std_latency": 1.2,
  "timestamp": "2026-03-05T21:30:00",
  "agent_id": "agent-001"
}
```

### View Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

---

## 🎨 Frontend Dashboard (Optional)

### Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

---

## 🐳 Quick Docker Setup

If you prefer Docker:

```bash
cd docker
docker-compose up -d
```

This will start:
- NetMonitor agent
- InfluxDB (optional)
- Grafana (optional)

---

## 🧪 Test the Setup

### Run Unit Tests

```bash
pytest tests/
```

### Test Specific Collector

```python
python -c "from app.collectors.ping import PingCollector; print(PingCollector().collect('8.8.8.8'))"
```

---

## 🔧 Common Configuration Tasks

### Change Collection Interval

Edit `app/config/config.yaml`:

```yaml
interval: 30  # Collect every 30 seconds
```

### Enable InfluxDB Export

1. Set environment variable:

```bash
# Windows PowerShell
$env:INFLUX_TOKEN="your-token-here"

# Linux/macOS
export INFLUX_TOKEN="your-token-here"
```

2. Update config:

```yaml
exporters:
  influx:
    enabled: true
    url: "http://localhost:8086"
    org: "your-org"
    bucket: "network"
```

### Change Prometheus Port

```yaml
exporters:
  prometheus:
    enabled: true
    port: 9090  # Change from default 8000
```

### Add Custom Ping Target

```bash
curl -X POST "http://localhost:8000/api/target" \
  -H "Content-Type: application/json" \
  -d '{"target": "1.1.1.1"}'
```

---

## 🎯 Next Steps

Now that you have NetMonitor running:

1. **[Configure Exporters](EXPORTERS.md)** - Set up InfluxDB or Prometheus
2. **[Explore the API](API.md)** - Learn about available endpoints
3. **[Enable AI Analysis](AI_INTEGRATION.md)** - Set up Ollama for diagnostics
4. **[Customize Collectors](COLLECTORS.md)** - Add or modify metric collectors
5. **[Deploy to Production](DEPLOYMENT.md)** - Production deployment guide

---

## 🐛 Troubleshooting Quick Start

### Agent Won't Start

**Check Python version:**
```bash
python --version  # Should be 3.10+
```

**Check if port is available:**
```bash
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000
```

### No Metrics Collected

**Check collectors are loaded:**
```bash
python -c "from app.collectors import load_plugins; print(load_plugins())"
```

**Verify network connectivity:**
```bash
ping 8.8.8.8
```

### InfluxDB Connection Failed

**Verify token:**
```bash
# Windows PowerShell
echo $env:INFLUX_TOKEN

# Linux/macOS
echo $INFLUX_TOKEN
```

**Test connection:**
```bash
curl -I http://localhost:8086/api/v2/ping
```

### Frontend Can't Connect

**Check CORS settings in `app/api/server.py`:**
```python
allow_origins=[
    "http://localhost:5173",  # Add your frontend URL
]
```

---

## 📚 Additional Resources

- **[Full Configuration Reference](CONFIGURATION.md)**
- **[Architecture Overview](ARCHITECTURE.md)**
- **[Complete API Documentation](API.md)**
- **[Troubleshooting Guide](TROUBLESHOOTING.md)**

---

## 💡 Tips for Success

> **Tip**: Start with Prometheus exporter enabled (simpler than InfluxDB)

> **Tip**: Use the default 10-second interval for testing, increase for production

> **Tip**: Check logs in the console for detailed operational information

> **Tip**: Frontend dashboard provides real-time visualization

---

**You're all set! NetMonitor is now collecting and monitoring your network metrics.** 🎉

For more advanced configuration and features, continue to the full documentation.
