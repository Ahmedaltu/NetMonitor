# AI Integration Guide

> Complete guide to integrating AI-powered network diagnostics with NetMonitor

## 🧠 Overview

NetMonitor integrates with local Large Language Models (LLMs) via Ollama to provide natural language analysis and insights about network performance.

**Key Features:**
- Natural language network diagnostics
- Automated insight generation
- Pattern recognition
- Actionable recommendations
- Privacy-preserving (local LLM)
- No cloud dependencies

---

## 🏗️ Architecture

```mermaid
flowchart LR
    A[Agent Metrics] --> B[InfluxDB]
    B --> C[Analyzer]
    C --> D[Statistical Summary]
    D --> E[Prompt Generator]
    E --> F[Ollama LLM]
    F --> G[Natural Language Analysis]
    G --> H[API Response]
    H --> I[Dashboard]
```

---

## 🚀 Quick Start

### 1. Install Ollama

**Linux & macOS:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai/download)

### 2. Pull a Model

```bash
# Recommended: Phi-3 (small, fast)
ollama pull phi3

# Alternative: Llama 2 (larger, more capable)
ollama pull llama2

# Alternative: Mistral (good balance)
ollama pull mistral
```

### 3. Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

Expected response:
```json
{
  "models": [
    {
      "name": "phi3:latest",
      "modified_at": "2026-03-05T21:00:00.000Z",
      "size": 2300000000
    }
  ]
}
```

### 4. Configure NetMonitor

Edit `app/config/config.yaml`:

```yaml
ai:
  enabled: true
  ollama_url: "http://localhost:11434"
  model: "phi3"

exporters:
  influx:
    enabled: true  # Required for AI features
    url: "http://localhost:8086"
    org: "net-monitor"
    bucket: "network"
```

### 5. Set InfluxDB Token

```bash
# Windows PowerShell
$env:INFLUX_TOKEN="your-influxdb-token"

# Linux/macOS
export INFLUX_TOKEN="your-influxdb-token"
```

### 6. Test AI Integration

```bash
# Get AI analysis
curl "http://localhost:8000/explain?window=30"
```

---

## 📊 Analyzer Implementation

### Core Module: `app/ai/analyzer.py`

```python
# app/ai/analyzer.py

import os
import requests
from influxdb_client import InfluxDBClient
from app.utils.logger import logger

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

def fetch_recent_summary(settings, window_minutes: int = 30) -> dict:
    """
    Query recent metrics from InfluxDB and compute statistical summary.
    
    Args:
        settings: Application settings
        window_minutes: Time window for analysis
    
    Returns:
        dict: Statistical summary of metrics
    """
    token = os.getenv("INFLUX_TOKEN")
    if not token:
        raise ValueError("INFLUX_TOKEN not set")
    
    client = InfluxDBClient(
        url=settings.exporters.influx.url,
        token=token,
        org=settings.exporters.influx.org
    )
    
    query_api = client.query_api()
    
    # Flux query to retrieve recent data
    flux_query = f"""
    from(bucket: "{settings.exporters.influx.bucket}")
      |> range(start: -{window_minutes}m)
      |> filter(fn: (r) => r._measurement == "network_metrics")
    """
    
    try:
        tables = query_api.query(flux_query)
    except Exception as e:
        logger.error(f"Influx query failed: {e}")
        return {}
    
    # Aggregate metrics
    metrics = {}
    for table in tables:
        for record in table.records:
            field = record.get_field()
            value = record.get_value()
            
            if isinstance(value, (int, float)):
                metrics.setdefault(field, []).append(float(value))
    
    # Compute statistics
    summary = {}
    for key, values in metrics.items():
        if not values:
            continue
        
        summary[key] = {
            "mean": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
            "samples": len(values)
        }
    
    return summary


def generate_explanation(summary: dict) -> str:
    """
    Send metric summary to local LLM for analysis.
    
    Args:
        summary: Statistical summary of network metrics
    
    Returns:
        str: Natural language explanation
    """
    if not summary:
        return "No recent data available for analysis."
    
    # Construct prompt
    prompt = f"""
You are a network performance analyst.

Below is a structured summary of recent network metrics:

{summary}

Provide:
1. Overall network health assessment
2. Any signs of instability or issues
3. Possible technical causes
4. Recommendations if applicable

Be concise, technical, and objective.
"""
    
    # Send request to Ollama
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response generated")
        else:
            logger.error(f"Ollama request failed: {response.status_code}")
            return "AI analysis unavailable"
    
    except requests.Timeout:
        logger.error("Ollama request timed out")
        return "AI analysis timed out"
    
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return "AI analysis error"
```

---

## 🎯 Using the AI Features

### Via API: GET /explain

```bash
# Get 30-minute analysis
curl "http://localhost:8000/explain?window=30"
```

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
    },
    "jitter": {
      "mean": 2.3,
      "max": 5.1,
      "min": 0.8,
      "samples": 180
    }
  },
  "analysis": "Network performance is stable with consistent latency averaging 15.2ms. No packet loss detected over the 30-minute window. Jitter is within acceptable range (mean 2.3ms), indicating a healthy connection suitable for real-time applications. The network appears to have good quality with no immediate concerns."
}
```

### Via Python API

```python
from app.ai.analyzer import fetch_recent_summary, generate_explanation
from app.config.loader import load_settings

# Load configuration
settings = load_settings()

# Get summary
summary = fetch_recent_summary(settings, window_minutes=30)

# Generate analysis
analysis = generate_explanation(summary)

print(f"Summary: {summary}")
print(f"Analysis: {analysis}")
```

---

## 🎨 Frontend Integration

### React Component Example

```jsx
// src/components/AIInsightsPanel.jsx

import { useState, useEffect } from 'react';

function AIInsightsPanel() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [window, setWindow] = useState(30);
  
  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/explain?window=${window}`
      );
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to fetch analysis:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchAnalysis();
    const interval = setInterval(fetchAnalysis, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [window]);
  
  return (
    <div className="ai-insights-panel">
      <h2>🧠 AI Network Analysis</h2>
      
      <div className="window-selector">
        <label>Analysis Window:</label>
        <select value={window} onChange={(e) => setWindow(e.target.value)}>
          <option value={15}>15 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={60}>1 hour</option>
          <option value={360}>6 hours</option>
        </select>
      </div>
      
      {loading ? (
        <div className="loading">Analyzing network data...</div>
      ) : analysis ? (
        <div className="analysis-content">
          <div className="summary">
            <h3>Statistical Summary</h3>
            <pre>{JSON.stringify(analysis.summary, null, 2)}</pre>
          </div>
          
          <div className="insights">
            <h3>AI Insights</h3>
            <p>{analysis.analysis}</p>
          </div>
        </div>
      ) : (
        <div className="no-data">No analysis available</div>
      )}
      
      <button onClick={fetchAnalysis}>Refresh Analysis</button>
    </div>
  );
}

export default AIInsightsPanel;
```

---

## ⚙️ Advanced Configuration

### Custom Prompts

Modify the prompt in `app/ai/analyzer.py`:

```python
def generate_explanation(summary: dict, focus: str = "general") -> str:
    """
    Generate analysis with specific focus.
    
    Args:
        summary: Metric summary
        focus: Analysis focus (general, latency, packet_loss, bandwidth)
    """
    prompts = {
        "general": """
            Provide general network health assessment.
        """,
        
        "latency": """
            Focus specifically on latency patterns and trends.
            Identify any anomalies or concerning patterns.
        """,
        
        "packet_loss": """
            Analyze packet loss patterns.
            Determine potential causes and impact on applications.
        """,
        
        "bandwidth": """
            Evaluate bandwidth utilization and capacity.
            Identify bottlenecks or constraints.
        """
    }
    
    prompt = f"""
    You are a network performance analyst.
    
    Metrics: {summary}
    
    {prompts.get(focus, prompts["general"])}
    """
    
    # ... rest of implementation
```

### Model Selection

Different models for different needs:

```python
# Fast, small model (2GB)
MODEL_NAME = "phi3"

# More capable, larger (4GB)
MODEL_NAME = "mistral"

# Most capable, largest (7GB)
MODEL_NAME = "llama2"

# Code-focused
MODEL_NAME = "codellama"
```

### Streaming Responses

For real-time analysis updates:

```python
def generate_explanation_stream(summary: dict):
    """Stream analysis tokens as they're generated"""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True  # Enable streaming
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            yield data.get("response", "")
```

---

## 🔧 Troubleshooting

### Ollama Not Running

**Symptom:**
```
Connection refused to http://localhost:11434
```

**Solution:**
```bash
# Check if Ollama is running
ollama serve

# Or restart Ollama service
systemctl restart ollama  # Linux
brew services restart ollama  # macOS
```

### Model Not Found

**Symptom:**
```
Error: model 'phi3' not found
```

**Solution:**
```bash
# Pull the model
ollama pull phi3

# List available models
ollama list
```

### InfluxDB Connection Failed

**Symptom:**
```
INFLUX_TOKEN not set
```

**Solution:**
```bash
# Set the token
export INFLUX_TOKEN="your-token"

# Verify
echo $INFLUX_TOKEN
```

### Slow Responses

**Symptom:** AI analysis takes >30 seconds

**Solutions:**
1. **Use smaller model:**
   ```bash
   ollama pull phi3  # 2GB instead of llama2 7GB
   ```

2. **Increase timeout:**
   ```python
   timeout=60  # Increase from 30
   ```

3. **Reduce data window:**
   ```bash
   curl "http://localhost:8000/explain?window=15"  # Instead of 30
   ```

### Poor Analysis Quality

**Solutions:**
1. **Use larger model:**
   ```bash
   ollama pull llama2
   ```

2. **Improve prompt engineering:**
   ```python
   prompt = """
   You are an expert network engineer with 20 years of experience.
   
   Analyze the following metrics in detail...
   """
   ```

3. **Provide more context:**
   ```python
   prompt = f"""
   Network: Production environment
   Location: {settings.agent.location}
   Time: Last {window} minutes
   
   Metrics: {summary}
   """
   ```

---

## 🎯 Best Practices

### 1. Model Selection

| Use Case | Recommended Model | Size | Speed |
|----------|------------------|------|-------|
| Development | phi3 | 2GB | Fast |
| Production | mistral | 4GB | Medium |
| Deep Analysis | llama2 | 7GB | Slow |

### 2. Analysis Frequency

```python
# Development: On-demand
# Production: Every 5-10 minutes
# Alerting: On threshold breach
```

### 3. Prompt Engineering

**Good prompt:**
```python
prompt = f"""
Role: Network performance analyst
Task: Analyze metrics and identify issues
Context: {summary}
Format: Structured analysis with recommendations
Constraints: Be concise and technical
"""
```

**Poor prompt:**
```python
prompt = f"What's wrong with this? {summary}"
```

### 4. Error Handling

```python
def generate_explanation(summary: dict) -> str:
    try:
        # AI generation
        return analysis
    except requests.Timeout:
        return "Analysis timed out. Network data appears stable based on metrics."
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "AI analysis unavailable. Manual review recommended."
```

---

## 📊 Performance Considerations

### Resource Usage

| Model | RAM | CPU | Response Time |
|-------|-----|-----|---------------|
| phi3 | 2GB | Low | 2-5s |
| mistral | 4GB | Medium | 5-10s |
| llama2 | 7GB | High | 10-20s |

### Optimization Tips

1. **Cache responses:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def generate_explanation(summary_hash: str) -> str:
       # ... implementation
   ```

2. **Batch analysis:**
   ```python
   # Analyze multiple time windows together
   windows = [15, 30, 60]
   analyses = [analyze(w) for w in windows]
   ```

3. **Preload models:**
   ```bash
   # Keep model in memory
   ollama run phi3 "hello"
   ```

---

## 🔐 Privacy & Security

### Local Processing

All AI analysis happens locally:
- No cloud API calls
- No data leaves your infrastructure
- Complete control over model and data

### Data Retention

```yaml
influx:
  retention_days: 7  # Limit data retention
```

---

## 🔗 Related Documentation

- **[Configuration Guide](CONFIGURATION.md)** - AI configuration
- **[API Reference](API.md)** - /explain endpoint
- **[Architecture](ARCHITECTURE.md)** - AI integration design
- **[Deployment](DEPLOYMENT.md)** - Production AI deployment