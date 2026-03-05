# Development Guide

> Guide for developers contributing to NetMonitor

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment tool
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/netmonitor.git
cd netmonitor

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**requirements-dev.txt:**
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
isort>=5.12.0
```

---

## 📁 Project Structure

```
netmonitor/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── collectors/          # Metric collectors
│   │   ├── __init__.py
│   │   ├── base.py         # Base collector interface
│   │   ├── ping.py
│   │   ├── traffic.py
│   │   └── iperf.py
│   ├── analytics/           # Analytics engine
│   │   ├── latency_stats.py
│   │   ├── scoring.py
│   │   └── stability.py
│   ├── exporters/           # Data exporters
│   │   ├── base.py
│   │   ├── influx.py
│   │   ├── prometheus.py
│   │   └── manager.py
│   ├── core/               # Core orchestration
│   │   ├── agent.py        # Main agent
│   │   ├── health.py       # Health tracking
│   │   ├── scheduler.py
│   │   └── plugin_manager.py
│   ├── api/                # REST API
│   │   ├── server.py       # FastAPI app
│   │   └── routes.py       # API routes
│   ├── ai/                 # AI integration
│   │   └── analyzer.py
│   ├── config/             # Configuration
│   │   ├── config.yaml
│   │   ├── loader.py
│   │   └── models.py       # Pydantic models
│   └── utils/              # Utilities
│       ├── logger.py
│       └── exceptions.py
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_analytics.py
│   ├── test_exporters.py
│   └── test_api.py
├── docs/                   # Documentation
├── docker/                 # Docker configs
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pytest.ini             # Pytest configuration
├── .gitignore
└── README.md
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_collectors.py

# Run specific test
pytest tests/test_collectors.py::test_ping_collector

# Run with verbose output
pytest -v

# Run with debug output
pytest -s
```

### Writing Tests

**Unit Test Example:**
```python
# tests/test_collectors.py

import pytest
from app.collectors.ping import PingCollector

def test_ping_collector_success():
    """Test successful ping collection"""
    collector = PingCollector()
    metrics = collector.collect("8.8.8.8")
    
    assert "latency" in metrics
    assert "packet_loss" in metrics
    assert isinstance(metrics["latency"], (float, type(None)))
    assert 0 <= metrics["packet_loss"] <= 100

def test_ping_collector_timeout():
    """Test ping timeout handling"""
    collector = PingCollector()
    collector.timeout = 0.001  # Force timeout
    metrics = collector.collect("192.0.2.1")  # Non-routable IP
    
    assert metrics["packet_loss"] == 100
    assert metrics["latency"] is None

@pytest.mark.asyncio
async def test_agent_cycle():
    """Test agent collection cycle"""
    from app.core.agent import Agent
    from app.collectors.ping import PingCollector
    
    agent = Agent(
        agent_id="test-agent",
        collectors=[PingCollector()],
        exporters=[],
        interval=1
    )
    
    await agent._cycle()
    assert agent.latest_metrics is not None
```

**Integration Test Example:**
```python
# tests/test_api.py

from fastapi.testclient import TestClient
from app.api.server import create_app
from app.core.agent import Agent

def test_health_endpoint():
    """Test health endpoint"""
    agent = Agent(agent_id="test", collectors=[], exporters=[], interval=10)
    app = create_app(agent, settings)
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "agent_id" in data
    assert "state" in data

def test_metrics_endpoint():
    """Test metrics endpoint"""
    # ... implementation
```

### Test Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## 🎨 Code Style

### Formatting with Black

```bash
# Format all code
black app/ tests/

# Check formatting
black app/ tests/ --check

# Format specific file
black app/main.py
```

### Import Sorting with isort

```bash
# Sort imports
isort app/ tests/

# Check import sorting
isort app/ tests/ --check-only
```

### Linting with Flake8

```bash
# Lint code
flake8 app/ tests/

# With specific rules
flake8 app/ --max-line-length=100
```

**Setup.cfg:**
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv
ignore = E203, W503

[isort]
profile = black
line_length = 100

[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
```

---

## 🔧 Development Workflow

### Feature Development

1. **Create feature branch:**
```bash
git checkout -b feature/new-collector
```

2. **Implement feature:**
```python
# app/collectors/dns_check.py
from app.collectors.base import BaseCollector

class DNSCheckCollector(BaseCollector):
    name = "dns_check"
    
    def collect(self) -> dict:
        # Implementation
        pass
```

3. **Write tests:**
```python
# tests/test_collectors.py
def test_dns_check_collector():
    collector = DNSCheckCollector()
    metrics = collector.collect()
    assert "dns_response_time" in metrics
```

4. **Run tests:**
```bash
pytest tests/test_collectors.py::test_dns_check_collector
```

5. **Format code:**
```bash
black app/collectors/dns_check.py tests/test_collectors.py
isort app/collectors/dns_check.py tests/test_collectors.py
flake8 app/collectors/dns_check.py
```

6. **Commit changes:**
```bash
git add app/collectors/dns_check.py tests/test_collectors.py
git commit -m "feat: add DNS check collector"
```

7. **Push and create PR:**
```bash
git push origin feature/new-collector
# Create pull request on GitHub
```

---

## 🐛 Debugging

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

### VS Code Debug Configuration

**.vscode/launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: NetMonitor",
      "type": "python",
      "request": "launch",
      "module": "app.main",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Logging for Debugging

```python
from app.utils.logger import logger

# Debug logging
logger.debug(f"Collector metrics: {metrics}")

# With context
logger.debug(f"Processing target {target}", extra={
    "target": target,
    "metrics": metrics
})
```

---

## 📦 Creating a New Collector

### Step-by-Step Guide

1. **Create collector file:**
```python
# app/collectors/http_check.py

from app.collectors.base import BaseCollector
from app.utils.logger import logger
import requests
import time

class HTTPCheckCollector(BaseCollector):
    """Check HTTP endpoint availability and response time"""
    
    name = "http_check"
    
    def __init__(self):
        self.url = "https://api.example.com/health"
        self.timeout = 5
    
    def collect(self) -> dict:
        """
        Check HTTP endpoint.
        
        Returns:
            dict: Response time and status metrics
        """
        try:
            start = time.time()
            response = requests.get(self.url, timeout=self.timeout)
            duration = (time.time() - start) * 1000
            
            return {
                "http_response_time_ms": duration,
                "http_status_code": response.status_code,
                "http_available": 1 if response.ok else 0
            }
        except Exception as e:
            logger.error(f"HTTP check failed: {e}")
            return {
                "http_response_time_ms": None,
                "http_status_code": 0,
                "http_available": 0
            }
```

2. **Add tests:**
```python
# tests/test_collectors.py

def test_http_check_collector():
    from app.collectors.http_check import HTTPCheckCollector
    
    collector = HTTPCheckCollector()
    collector.url = "https://httpbin.org/get"
    metrics = collector.collect()
    
    assert "http_response_time_ms" in metrics
    assert "http_status_code" in metrics
    assert metrics["http_status_code"] == 200
```

3. **Run and verify:**
```bash
pytest tests/test_collectors.py::test_http_check_collector
python -m app.main
```

---

## 🔄 Continuous Integration

### GitHub Actions

**.github/workflows/test.yml:**
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 📝 Documentation

### Documenting Code

```python
def collect(self, target: str = "8.8.8.8") -> dict:
    """
    Collect network metrics via ICMP ping.
    
    Args:
        target: IP address or hostname to ping
    
    Returns:
        dict: Dictionary containing:
            - latency (float): Round-trip time in ms
            - packet_loss (float): Packet loss percentage (0-100)
            - jitter (float): Latency variation in ms
    
    Raises:
        TimeoutError: If ping operation times out
    
    Example:
        >>> collector = PingCollector()
        >>> metrics = collector.collect("8.8.8.8")
        >>> print(metrics["latency"])
        15.3
    """
```

### Updating Documentation

```bash
# Add new documentation
cd docs
nano NEW_FEATURE.md

# Update existing docs
nano COLLECTORS.md
```

---

## 🤝 Contributing

### Contribution Workflow

1. Fork repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Update documentation
6. Run tests and linting
7. Submit pull request

### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Add tests
- `chore`: Maintenance

**Examples:**
```bash
git commit -m "feat(collectors): add DNS check collector"
git commit -m "fix(agent): handle timeout in collection cycle"
git commit -m "docs(api): update API reference"
```

---

## 🔗 Related Documentation

- **[Architecture](ARCHITECTURE.md)** - System design
- **[Testing Guide](TESTING.md)** - Detailed testing docs
- **[Plugin Development](PLUGIN_DEVELOPMENT.md)** - Advanced plugin creation
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues