# Troubleshooting Guide

> Solutions to common issues and problems with NetMonitor

## 🔍 Quick Diagnosis

### Health Check Commands

```bash
# Agent health
curl http://localhost:8000/health

# Metrics availability
curl http://localhost:8000/api/metrics

# Prometheus metrics
curl http://localhost:8000/metrics

# System status
python -c "from app.config.loader import load_settings; print(load_settings())"
```

---

## 🚨 Common Issues

### Agent Won't Start

#### Symptom: Port Already in Use

```
Error: [Errno 48] Address already in use
```

**Solution 1: Find and kill process**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/macOS
lsof -i :8000
kill -9 <PID>
```

**Solution 2: Change port**
```yaml
# app/config/config.yaml
exporters:
  prometheus:
    port: 9090  # Use different port
```

---

#### Symptom: Python Version Incompatible

```
SyntaxError: invalid syntax
```

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.10+

# Use correct Python
python3.10 -m app.main

# Or recreate virtual environment
python3.10 -m venv .venv
```

---

#### Symptom: Missing Dependencies

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

---

### No Metrics Collected

#### Symptom: Empty Metrics Response

```json
{
  "latency": null,
  "packet_loss": null,
  "jitter": null
}
```

**Diagnosis:**
```bash
# Check collector status
python -c "from app.collectors import load_plugins; print([c.name for c in load_plugins()])"

# Test collector directly
python -c "from app.collectors.ping import PingCollector; print(PingCollector().collect('8.8.8.8'))"
```

**Common Causes:**

1. **Network unreachable**
   ```bash
   # Test connectivity
   ping 8.8.8.8
   ```

2. **Firewall blocking**
   ```bash
   # Windows: Allow ping
   netsh advfirewall firewall add rule name="ICMP Allow" protocol=icmpv4:8,any dir=in action=allow
   
   # Linux: Check iptables
   sudo iptables -L
   ```

3. **Collector errors**
   ```bash
   # Check logs
   tail -f logs/netmonitor.log
   
   # Enable debug logging
   # In config.yaml:
   logging:
     level: "DEBUG"
   ```

---

### InfluxDB Connection Issues

#### Symptom: Token Not Set

```
ValueError: INFLUX_TOKEN not set
```

**Solution:**
```bash
# Windows PowerShell
$env:INFLUX_TOKEN="your-token-here"

# Linux/macOS
export INFLUX_TOKEN="your-token-here"

# Verify
echo $env:INFLUX_TOKEN  # Windows
echo $INFLUX_TOKEN  # Linux/macOS

# Make permanent (Linux/macOS)
echo 'export INFLUX_TOKEN="your-token"' >> ~/.bashrc
source ~/.bashrc
```

---

#### Symptom: Connection Refused

```
Error: Connection refused to http://localhost:8086
```

**Diagnosis:**
```bash
# Check if InfluxDB is running
curl http://localhost:8086/health

# Windows: Check service
sc query InfluxDB

# Linux: Check service
systemctl status influxdb
```

**Solution:**
```bash
# Start InfluxDB
# Windows
net start InfluxDB

# Linux
sudo systemctl start influxdb

# macOS
brew services start influxdb
```

---

#### Symptom: Bucket Not Found

```
Error: bucket "network" not found
```

**Solution:**
```bash
# Create bucket
influx bucket create \
  --name network \
  --org net-monitor \
  --retention 7d

# List buckets
influx bucket list
```

---

### Ollama/AI Issues

#### Symptom: Ollama Connection Failed

```
Connection refused to http://localhost:11434
```

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
# Windows
ollama serve

# Linux
sudo systemctl start ollama

# macOS
brew services start ollama
```

---

#### Symptom: Model Not Found

```
Error: model 'phi3' not found
```

**Solution:**
```bash
# List available models
ollama list

# Pull required model
ollama pull phi3

# Verify
ollama run phi3 "hello"
```

---

#### Symptom: AI Analysis Timeout

```
AI analysis timed out
```

**Solutions:**

1. **Increase timeout:**
   ```python
   # In app/ai/analyzer.py
   timeout=60  # Increase from 30
   ```

2. **Use smaller model:**
   ```bash
   ollama pull phi3  # Instead of llama2
   ```

3. **Reduce data window:**
   ```bash
   curl "http://localhost:8000/explain?window=15"  # Instead of 30
   ```

---

### Frontend Issues

#### Symptom: CORS Error

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
```python
# In app/api/server.py, add your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "YOUR_FRONTEND_URL_HERE"  # Add this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### Symptom: Frontend Can't Connect

```
Failed to fetch: net::ERR_CONNECTION_REFUSED
```

**Diagnosis:**
```bash
# Check if agent is running
curl http://localhost:8000/health

# Check port
netstat -an | findstr :8000  # Windows
lsof -i :8000  # Linux/macOS
```

**Solution:**
1. Start the agent: `python -m app.main`
2. Verify port matches frontend config
3. Check firewall settings

---

### High Resource Usage

#### Symptom: High CPU

**Diagnosis:**
```bash
# Check collection interval
curl http://localhost:8000/api/agent/status

# Monitor process
# Windows
Get-Process python | Format-Table CPU

# Linux
top -p $(pgrep -f "python.*app.main")
```

**Solutions:**

1. **Increase collection interval:**
   ```yaml
   interval: 60  # Instead of 10
   ```

2. **Disable unnecessary collectors:**
   ```python
   # In app/collectors/__init__.py
   # Comment out heavy collectors
   ```

3. **Reduce batch operations:**
   ```yaml
   exporters:
     influx:
       batch_size: 50  # Reduce from 100
   ```

---

#### Symptom: High Memory

**Diagnosis:**
```bash
# Check memory usage
# Windows
Get-Process python | Format-Table WS

# Linux
ps aux | grep "python.*app.main"
```

**Solutions:**

1. **Limit data retention:**
   ```python
   # In app/analytics/latency_stats.py
   window_size=20  # Reduce from default
   ```

2. **Clear event history:**
   ```bash
   curl -X POST http://localhost:8000/api/events/reset
   ```

---

### Prometheus Scraping Fails

#### Symptom: Metrics Endpoint Returns 404

```
curl: (22) The requested URL returned error: 404
```

**Solution:**
```bash
# Verify endpoint path
curl http://localhost:8000/metrics

# Check configuration
# Should be /metrics not /prometheus/metrics
```

---

#### Symptom: No Metrics in Prometheus

**Diagnosis:**
```bash
# Check Prometheus scrape config
cat prometheus.yml

# Check Prometheus targets
# Open: http://localhost:9090/targets
```

**Solution:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'netmonitor'
    static_configs:
      - targets: ['localhost:8000']  # Correct port
    scrape_interval: 30s
```

---

## 🔧 Diagnostic Tools

### Configuration Validator

```python
# validate_config.py
from app.config.loader import load_settings
from pydantic import ValidationError

try:
    settings = load_settings()
    print("✓ Configuration valid")
    print(f"  Agent ID: {settings.agent.id}")
    print(f"  Interval: {settings.interval}s")
    print(f"  InfluxDB: {settings.exporters.influx.enabled}")
    print(f"  Prometheus: {settings.exporters.prometheus.enabled}")
except ValidationError as e:
    print("✗ Configuration invalid")
    print(e)
```

### Collector Tester

```python
# test_collectors.py
from app.collectors import load_plugins

collectors = load_plugins()
print(f"Found {len(collectors)} collectors")

for collector in collectors:
    print(f"\nTesting {collector.name}...")
    try:
        if collector.name == "ping":
            metrics = collector.collect("8.8.8.8")
        else:
            metrics = collector.collect()
        
        if metrics:
            print(f"  ✓ Success: {list(metrics.keys())}")
        else:
            print(f"  ✗ No metrics returned")
    except Exception as e:
        print(f"  ✗ Error: {e}")
```

### Connection Tester

```python
# test_connections.py
import requests
from influxdb_client import InfluxDBClient
import os

# Test InfluxDB
try:
    client = InfluxDBClient(
        url="http://localhost:8086",
        token=os.getenv("INFLUX_TOKEN"),
        org="net-monitor"
    )
    health = client.health()
    print(f"✓ InfluxDB: {health.status}")
except Exception as e:
    print(f"✗ InfluxDB: {e}")

# Test Ollama
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        print("✓ Ollama: Running")
    else:
        print(f"✗ Ollama: Status {response.status_code}")
except Exception as e:
    print(f"✗ Ollama: {e}")

# Test NetMonitor API
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ NetMonitor: {data['state']}")
    else:
        print(f"✗ NetMonitor: Status {response.status_code}")
except Exception as e:
    print(f"✗ NetMonitor: {e}")
```

---

## 📋 Debug Checklist

When troubleshooting, work through this checklist:

- [ ] Python version 3.10 or higher
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list`)
- [ ] Configuration file valid
- [ ] Port 8000 available
- [ ] Network connectivity (can ping targets)
- [ ] InfluxDB running (if enabled)
- [ ] INFLUX_TOKEN set (if using InfluxDB)
- [ ] Ollama running (if using AI)
- [ ] Model pulled (if using AI)
- [ ] Logs checked for errors
- [ ] Firewall not blocking

---

## 📝 Getting Help

### Collecting Debug Information

```bash
# System info
python --version
pip list

# Configuration
cat app/config/config.yaml

# Recent logs
tail -n 100 logs/netmonitor.log

# Health status
curl http://localhost:8000/health

# Test connectivity
ping 8.8.8.8
curl http://localhost:8086/health
curl http://localhost:11434/api/tags
```

### Reporting Issues

When reporting issues, include:

1. **System information:**
   - OS and version
   - Python version
   - NetMonitor version

2. **Configuration:**
   - Config file (sanitized)
   - Environment variables (sanitized)

3. **Error messages:**
   - Full error text
   - Stack trace
   - Relevant log entries

4. **Steps to reproduce:**
   - What you did
   - What you expected
   - What happened

---

## 🔗 Related Documentation

- **[Quickstart Guide](QUICKSTART.md)** - Initial setup
- **[Configuration Guide](CONFIGURATION.md)** - Configuration details
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Development Guide](DEVELOPMENT.md)** - Development setup