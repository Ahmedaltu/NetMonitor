# Design Principles

> Core design decisions and architectural patterns in NetMonitor

## 🎯 Overview

NetMonitor is built on a foundation of well-established software engineering principles that prioritize maintainability, performance, and extensibility.

---

## 🏗️ Architectural Principles

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:

```
┌─────────────────────────────────────┐
│     Presentation (API/UI)           │  ← User interaction
├─────────────────────────────────────┤
│     Application (Agent Core)        │  ← Orchestration
├─────────────────────────────────────┤
│     Domain (Analytics)              │  ← Business logic
├─────────────────────────────────────┤
│     Data (Collectors/Exporters)     │  ← Data I/O
└─────────────────────────────────────┘
```

**Benefits:**
- Changes isolated to single layer
- Easy to test individual components
- Clear dependencies
- Simple to reason about

**Example:**
```python
# Collectors: Only data acquisition
class PingCollector(BaseCollector):
    def collect(self) -> dict:
        return {"latency": 15.3}

# Analytics: Only transformations
class StabilityAnalyzer:
    def analyze(self, metrics: dict) -> float:
        return calculate_stability(metrics)

# Agent: Only orchestration
class Agent:
    async def _cycle(self):
        metrics = await self._collect_metrics()
        self._apply_analytics(metrics)
        await self._export(metrics)
```

---

### 2. Async-First Design

All I/O operations are asynchronous to maximize concurrency:

**Principle:** Never block the event loop

```python
# Bad: Blocking I/O
def collect_all():
    results = []
    for collector in collectors:
        results.append(collector.collect())  # Blocks
    return results

# Good: Concurrent async
async def collect_all():
    tasks = [asyncio.to_thread(c.collect) for c in collectors]
    return await asyncio.gather(*tasks)  # Concurrent
```

**Benefits:**
- Higher throughput
- Better resource utilization
- Responsive API
- Scalable architecture

**Real-world impact:**
```
Synchronous:  Collector A (2s) → Collector B (2s) → Collector C (2s) = 6s
Asynchronous: [Collector A, B, C] (all parallel) = 2s
```

---

### 3. Fail-Fast with Graceful Degradation

**Principle:** Validate early, but continue operating when possible

```python
# Fail fast on startup
def __init__(self, settings):
    if not settings.agent.id:
        raise ValueError("Agent ID required")  # Hard stop
    
    self.token = os.getenv("INFLUX_TOKEN")
    if not self.token:
        raise ValueError("INFLUX_TOKEN not set")  # Hard stop

# Graceful degradation during runtime
async def _collect_metrics(self):
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for collector, result in zip(collectors, results):
        if isinstance(result, Exception):
            logger.error(f"Collector {collector.name} failed")
            # Continue with other collectors
        else:
            metrics.update(result)
```

**When to fail fast:**
- Configuration errors
- Missing dependencies
- Invalid initialization

**When to degrade gracefully:**
- Collector failures
- Export timeouts
- Transient errors

---

### 4. Plugin Architecture

**Principle:** Extensibility through well-defined interfaces

```python
# Interface
class BaseCollector(ABC):
    @abstractmethod
    def collect(self) -> dict:
        pass

# Plugins auto-discovered
def load_plugins() -> List[BaseCollector]:
    # Scan directory, import, instantiate
    return discovered_plugins
```

**Benefits:**
- Add features without modifying core
- Community contributions
- Domain-specific extensions
- A/B testing new implementations

**Zero-configuration plugin loading:**
```
app/collectors/
├── base.py           # Interface
├── ping.py           # Auto-loaded
├── traffic.py        # Auto-loaded
└── custom_collector.py  # Your plugin - auto-loaded!
```

---

### 5. Configuration as Code

**Principle:** Typed, validated configuration

```python
# Pydantic models for validation
class AgentConfig(BaseModel):
    id: str = Field(..., min_length=1)
    location: str = "unknown"
    environment: str = "dev"

class Settings(BaseModel):
    agent: AgentConfig
    interval: int = Field(10, gt=0)
    exporters: ExporterSettings

# Load and validate
settings = Settings.parse_file("config.yaml")
```

**Benefits:**
- Catch errors at startup
- IDE autocomplete
- Self-documenting
- Type safety

**Traditional approach problems:**
```python
# Errors discovered at runtime
config = yaml.load("config.yaml")
interval = config.get("interval", 10)  # Typo? Wrong type?
agent_id = config["agent"]["id"]  # KeyError at runtime
```

**NetMonitor approach:**
```python
# Errors discovered at load time
settings = load_settings()  # Validates entire configuration
settings.interval  # IDE knows this is int
settings.agent.id  # IDE knows this is str
```

---

### 6. Observable by Design

**Principle:** Every component provides visibility

```python
class Agent:
    def __init__(self):
        self.health = AgentHealth()  # Health tracking
        self.events = NetworkEvents()  # Event tracking
        self.latest_metrics = {}  # State visibility
```

**Observability layers:**

1. **Logging:** Structured, leveled logging
```python
logger.info("Agent started", extra={"agent_id": self.agent_id})
logger.error("Collection failed", extra={"collector": name, "error": str(e)})
```

2. **Health states:** Internal state machine
```python
class AgentState(Enum):
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"
```

3. **Metrics about metrics:** Self-monitoring
```python
# Track agent performance
{
    "collection_duration_ms": 234,
    "export_duration_ms": 45,
    "cycle_count": 1234
}
```

4. **Event tracking:** Notable occurrences
```python
self.events.record_timeout(target)
self.events.record_packet_loss(target, loss_pct)
```

---

### 7. Immutable Data Flow

**Principle:** Metrics flow through pipeline without modification

```python
# Each stage returns new data, doesn't modify input
metrics = collect()           # {latency: 15.3}
enhanced = analyze(metrics)   # {latency: 15.3, mean: 14.8}
tagged = tag(enhanced)        # {latency: 15.3, mean: 14.8, agent_id: "001"}
```

**Benefits:**
- Predictable behavior
- Easy to debug
- Safe concurrency
- Reversible operations

**Anti-pattern (avoided):**
```python
metrics = collect()
analyze(metrics)  # Modifies metrics in-place
tag(metrics)      # Modifies metrics in-place
export(metrics)   # What's in metrics now?
```

---

### 8. Dependency Inversion

**Principle:** High-level modules don't depend on low-level modules

```python
# Agent depends on abstraction (BaseCollector)
class Agent:
    def __init__(self, collectors: List[BaseCollector]):
        self.collectors = collectors  # Abstraction

# Concrete implementations injected at runtime
ping = PingCollector()
traffic = TrafficCollector()
agent = Agent(collectors=[ping, traffic])
```

**Benefits:**
- Easy mocking for tests
- Swappable implementations
- Loose coupling
- Dependency injection

**Testing made easy:**
```python
# Mock collector for testing
class MockCollector(BaseCollector):
    def collect(self):
        return {"latency": 10.0}

# Test with mock
agent = Agent(collectors=[MockCollector()])
```

---

## 🔐 Security Principles

### 1. Least Privilege

Run with minimum required permissions:
```bash
# Dedicated user with minimal rights
sudo -u netmonitor python -m app.main
```

### 2. Defense in Depth

Multiple security layers:
- Network isolation
- Environment variable secrets
- Configuration validation
- Input sanitization
- Error message sanitization

### 3. Secure by Default

```python
# Production-safe defaults
class Settings(BaseModel):
    logging: LoggingConfig = LoggingConfig(
        level="INFO"  # Not DEBUG
    )
    api: APIConfig = APIConfig(
        auth_enabled=True  # Require auth
    )
```

---

## 📊 Performance Principles

### 1. Do Less, More Often

```python
# Prefer frequent small operations
interval = 30  # Collect every 30s

# Over infrequent large operations  
interval = 600  # Collect every 10 minutes (delayed insights)
```

### 2. Measure, Then Optimize

```python
# Profile before optimizing
import cProfile
cProfile.run('agent._cycle()')

# Add instrumentation
start = time.time()
metrics = collect()
duration = time.time() - start
logger.debug(f"Collection took {duration}s")
```

### 3. Cache Expensive Operations

```python
@lru_cache(maxsize=100)
def calculate_statistics(metrics_hash):
    # Expensive calculation cached
    return stats
```

---

## 🧪 Testing Principles

### 1. Test Pyramid

```
       /\
      /E2E\      Few: End-to-end tests
     /------\
    / Integ. \   Some: Integration tests
   /----------\
  /   Unit     \ Many: Unit tests
 /--------------\
```

### 2. Test Behavior, Not Implementation

```python
# Good: Tests behavior
def test_ping_collector_measures_latency():
    collector = PingCollector()
    metrics = collector.collect("8.8.8.8")
    assert "latency" in metrics
    assert isinstance(metrics["latency"], (float, type(None)))

# Bad: Tests implementation
def test_ping_collector_uses_subprocess():
    collector = PingCollector()
    assert hasattr(collector, '_run_subprocess')  # Too specific
```

### 3. Fail Clearly

```python
# Good: Clear failure message
assert metrics["latency"] > 0, \
    f"Expected positive latency, got {metrics['latency']}"

# Bad: Unclear failure
assert metrics["latency"] > 0  # AssertionError (why?)
```

---

## 📝 Code Quality Principles

### 1. Explicit is Better Than Implicit

```python
# Good: Clear intent
def collect(self, target: str = "8.8.8.8") -> dict:
    return ping(target)

# Bad: Unclear
def collect(self, t="8.8.8.8"):
    return ping(t)
```

### 2. Flat is Better Than Nested

```python
# Good: Early returns
def process(data):
    if not data:
        return None
    
    if not data.valid:
        return None
    
    return data.process()

# Bad: Deep nesting
def process(data):
    if data:
        if data.valid:
            return data.process()
        else:
            return None
    else:
        return None
```

### 3. DRY (Don't Repeat Yourself)

```python
# Good: Single source of truth
DEFAULT_TIMEOUT = 5

class PingCollector:
    timeout = DEFAULT_TIMEOUT

class HTTPCollector:
    timeout = DEFAULT_TIMEOUT

# Bad: Repetition
class PingCollector:
    timeout = 5

class HTTPCollector:
    timeout = 5  # What if we want to change this?
```

---

## 🔮 Future-Proofing

### 1. Version All APIs

```python
@app.get("/v1/metrics")  # Versioned
async def get_metrics_v1():
    return metrics

# Later, add v2 without breaking v1
@app.get("/v2/metrics")
async def get_metrics_v2():
    return enhanced_metrics
```

### 2. Feature Flags

```python
if settings.features.get("new_collector_enabled"):
    collectors.append(NewCollector())
```

### 3. Graceful Deprecation

```python
@deprecated(version="2.0", alternative="new_collect")
def collect_old(self):
    warnings.warn("Use new_collect() instead")
    return self.new_collect()
```

---

## 🎨 Design Patterns Used

### Strategy Pattern
```python
# Different export strategies
class InfluxExporter(BaseExporter): ...
class PrometheusExporter(BaseExporter): ...
```

### Observer Pattern
```python
# Health monitoring
class AgentHealth:
    def notify_state_change(self):
        for observer in self.observers:
            observer.on_state_change(self.state)
```

### Factory Pattern
```python
# Plugin loading
def load_plugins() -> List[BaseCollector]:
    return [PluginFactory.create(p) for p in discovered]
```

### Singleton Pattern
```python
# Logger instance
logger = logging.getLogger(__name__)
```

---

## 🔗 Related Documentation

- **[Architecture](ARCHITECTURE.md)** - System architecture
- **[Development](DEVELOPMENT.md)** - Development practices
- **[Testing](TESTING.md)** - Testing strategies