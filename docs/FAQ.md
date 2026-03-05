# Frequently Asked Questions (FAQ)

> Common questions and answers about NetMonitor

## 🎯 General Questions

### What is NetMonitor?

NetMonitor is an async-first network monitoring agent that combines deterministic telemetry collection with optional local AI-powered diagnostics. It's designed for both real-time monitoring and historical analysis.

### What makes NetMonitor different from other monitoring tools?

- **Async architecture** for high-performance concurrent collection
- **Local AI integration** via Ollama (privacy-preserving)
- **Plugin-based collectors** for easy extensibility
- **Dual export** to both InfluxDB (push) and Prometheus (pull)
- **Modern stack** with FastAPI and React
- **Production-ready** health tracking and error handling

### Is NetMonitor production-ready?

Yes! NetMonitor includes:
- Health state tracking
- Error isolation and recovery
- Graceful shutdown
- Comprehensive logging
- Configuration validation
- Docker support

---

## 🔧 Installation & Setup

### What are the minimum system requirements?

- **CPU**: 1 core
- **RAM**: 512MB
- **Disk**: 1GB
- **OS**: Linux, macOS, or Windows
- **Python**: 3.10 or higher

### Do I need to install InfluxDB?

No, InfluxDB is optional. You can run NetMonitor with only the Prometheus exporter enabled. However, InfluxDB is required for AI analysis features.

### Do I need Ollama for AI features?

Yes, Ollama is required for AI-powered diagnostics. It runs locally, ensuring your data never leaves your infrastructure.

### Can I run NetMonitor without Docker?

Yes! NetMonitor can run as a standalone Python application. Docker is optional but recommended for easier deployment.

### How do I upgrade to the latest version?

```bash
# Pull latest code
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart agent
systemctl restart netmonitor  # or python -m app.main
```

---

## ⚙️ Configuration

### How do I change the collection interval?

Edit `app/config/config.yaml`:
```yaml
interval: 30  # seconds
```

Or dynamically via API:
```bash
curl -X POST http://localhost:8000/api/interval \
  -H "Content-Type: application/json" \
  -d '{"interval": 30}'
```

### How do I monitor multiple targets?

Currently, NetMonitor supports one ping target at a time, changeable at runtime. For multiple targets, deploy multiple agent instances with unique IDs.

**Planned feature**: Multi-target support in single agent.

### Can I disable certain collectors?

Yes, modify `app/collectors/__init__.py` to exclude specific collectors, or implement enable/disable logic in your configuration.

### How do I configure custom thresholds for alerts?

Thresholds can be configured in the analytics layer. Edit `app/analytics/stability.py` to adjust detection parameters.

---

## 🔌 Collectors

### What collectors are included?

- **PingCollector**: ICMP latency, packet loss, jitter
- **TrafficCollector**: Network interface statistics
- **IPerfCollector**: Bandwidth testing (requires iperf3)

### How do I create a custom collector?

Create a new file in `app/collectors/` implementing `BaseCollector`:

```python
from app.collectors.base import BaseCollector

class MyCollector(BaseCollector):
    name = "my_collector"
    
    def collect(self) -> dict:
        return {"my_metric": 42}
```

It will be auto-discovered and loaded. See [Collectors Guide](COLLECTORS.md) for details.

### Why aren't my collectors working?

Common issues:
1. Network connectivity problems
2. Firewall blocking ICMP/ports
3. Missing dependencies
4. Incorrect permissions

Run diagnostics:
```bash
python -c "from app.collectors import load_plugins; print([c.name for c in load_plugins()])"
```

---

## 📊 Data & Metrics

### What metrics does NetMonitor collect?

**Network metrics:**
- Latency (ICMP ping)
- Packet loss
- Jitter
- Bytes sent/received
- Packet counts
- Network errors

**Derived metrics:**
- Rolling mean latency
- Standard deviation
- Stability scores
- Health scores

### How long is data retained?

Depends on your backend:
- **InfluxDB**: Configurable retention policy (default 7 days)
- **Prometheus**: Configurable in prometheus.yml (default 15 days)

### Can I export to multiple destinations?

Yes! Enable multiple exporters:
```yaml
exporters:
  influx:
    enabled: true
  prometheus:
    enabled: true
```

Both will receive all metrics concurrently.

### How do I query historical data?

**InfluxDB (Flux):**
```python
from(bucket: "network")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "network_metrics")
```

**Prometheus (PromQL):**
```promql
network_latency_ms{agent_id="agent-001"}[24h]
```

---

## 🧠 AI Features

### What AI models are supported?

Any model available in Ollama:
- **phi3** (recommended): Small, fast, good quality
- **llama2**: Larger, more capable
- **mistral**: Good balance
- **codellama**: Code-focused

### Why is AI analysis slow?

Factors affecting speed:
1. **Model size**: Larger models are slower
2. **Hardware**: CPU vs GPU
3. **Data volume**: More data = longer analysis
4. **System load**: Other processes competing for resources

Solutions:
- Use smaller model (phi3 instead of llama2)
- Increase timeout
- Reduce analysis window
- Allocate more resources

### Is my data sent to the cloud for AI analysis?

No! All AI analysis happens locally via Ollama. Your data never leaves your infrastructure.

### Can I customize AI prompts?

Yes! Edit `app/ai/analyzer.py` to modify the prompt sent to the LLM. See [AI Integration Guide](AI_INTEGRATION.md).

---

## 🌐 API

### What API endpoints are available?

- `GET /health` - Agent health status
- `GET /api/metrics` - Current metrics
- `GET /api/metrics/history` - Historical data
- `GET /explain` - AI analysis
- `POST /api/target` - Change ping target
- `GET /metrics` - Prometheus metrics

Full documentation: [API Reference](API.md)

### How do I secure the API?

**Coming soon**: API key and JWT authentication.

**Current options:**
1. Network isolation (firewall rules)
2. VPN/private network
3. Reverse proxy with authentication
4. Custom middleware

### Is there rate limiting?

Not currently, but planned for future releases.

### Can I use the API from JavaScript?

Yes! CORS is enabled for frontend integration:

```javascript
const response = await fetch('http://localhost:8000/api/metrics');
const metrics = await response.json();
console.log(metrics.latency);
```

---

## 🐳 Docker

### How do I run NetMonitor in Docker?

```bash
docker-compose up -d
```

See [Docker documentation](DOCKER.md) for details.

### Can I run just NetMonitor without InfluxDB?

Yes, modify `docker-compose.yml` to remove InfluxDB service and disable it in configuration.

### How do I update the Docker image?

```bash
docker-compose pull
docker-compose up -d
```

---

## 🔍 Troubleshooting

### NetMonitor won't start - port already in use

```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/macOS
lsof -i :8000
kill -9 <pid>
```

Or change the port in configuration.

### No metrics are being collected

1. Check network connectivity: `ping 8.8.8.8`
2. Check firewall settings
3. View logs: `tail -f logs/netmonitor.log`
4. Enable debug logging: Set `level: DEBUG` in config

### InfluxDB connection failed

1. Verify InfluxDB is running: `curl http://localhost:8086/health`
2. Check token is set: `echo $INFLUX_TOKEN`
3. Verify bucket exists: `influx bucket list`
4. Check network connectivity

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more solutions.

---

## 🚀 Performance

### How much CPU does NetMonitor use?

Typical usage:
- **Idle**: <1%
- **Collecting**: 2-5%
- **AI analysis**: 10-30% (temporary spikes)

### How much RAM does NetMonitor use?

Typical usage:
- **Agent only**: ~50MB
- **With dependencies**: ~100-200MB
- **With AI model loaded**: +2-8GB (model dependent)

### How many requests can the API handle?

FastAPI with async support handles hundreds of concurrent requests. Actual throughput depends on:
- Hardware resources
- Collection interval
- Number of exporters
- Analytics complexity

### Can I scale NetMonitor horizontally?

Yes! Deploy multiple agent instances:
- Use unique agent IDs
- Point to shared InfluxDB/Prometheus
- Use load balancer for API access
- Each agent monitors independent targets

---

## 📈 Use Cases

### What is NetMonitor best suited for?

- **Home networks**: Monitor internet connection quality
- **Small businesses**: Track network performance
- **Development**: Test network conditions for applications
- **Edge deployments**: Monitor remote site connectivity
- **ISP monitoring**: Track provider performance
- **VPN monitoring**: Measure VPN endpoint latency

### Can NetMonitor replace Nagios/Zabbix?

NetMonitor is focused on network metrics and is more lightweight. For comprehensive infrastructure monitoring, use NetMonitor alongside traditional tools.

### Is NetMonitor suitable for enterprise use?

Yes, with considerations:
- Deploy multiple agents for redundancy
- Use robust InfluxDB/Prometheus setup
- Implement proper security measures
- Set up alerting (Prometheus Alertmanager)

---

## 🔮 Future Plans

### What features are planned?

- Multi-target support in single agent
- API authentication (API keys, JWT)
- Built-in alerting
- More collectors (HTTP, DNS, SNMP)
- Dashboard improvements
- Mobile app
- Plugin marketplace

### How can I contribute?

See [Development Guide](DEVELOPMENT.md) for contribution guidelines.

### Where can I request features?

Open an issue on GitHub with:
- Feature description
- Use case
- Expected behavior
- Implementation ideas (optional)

---

## 🔗 Additional Resources

- **[Quickstart Guide](QUICKSTART.md)** - Get started in 10 minutes
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Configuration](CONFIGURATION.md)** - Configuration reference
- **[API Reference](API.md)** - Complete API docs
- **[Troubleshooting](TROUBLESHOOTING.md)** - Problem solutions
- **[Development](DEVELOPMENT.md)** - Contributing guide

---

## 💬 Getting Help

**Can't find your question?**

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Search existing GitHub issues
3. Join our community discussions
4. Open a new issue with details

**Found a bug?**

Report it on GitHub with:
- System information
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs/screenshots