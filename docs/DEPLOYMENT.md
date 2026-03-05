# Deployment Guide

> Production deployment strategies for NetMonitor

## 🎯 Deployment Overview

NetMonitor can be deployed in various configurations depending on your requirements:

- **Standalone**: Single agent on a monitoring host
- **Distributed**: Multiple agents across locations
- **Containerized**: Docker-based deployment
- **Cloud**: AWS, Azure, GCP deployment

---

## 📋 Pre-Deployment Checklist

### System Requirements

**Minimum:**
- 1 CPU core
- 512MB RAM
- 1GB disk space
- Network connectivity

**Recommended:**
- 2 CPU cores
- 1GB RAM
- 5GB disk space (with logs)
- Persistent storage for time-series data

### Software Requirements

- Python 3.10+
- InfluxDB 2.x (optional but recommended)
- Ollama (optional, for AI features)
- Prometheus (optional, for metrics scraping)
- Grafana (optional, for visualization)

### Network Requirements

- Outbound ICMP (ping)
- Outbound HTTP/HTTPS (for downloads)
- Inbound TCP 8000 (API/metrics endpoint)
- Inbound TCP 8086 (InfluxDB, if colocated)

---

## 🚀 Deployment Methods

### Method 1: Standalone Deployment

#### Step 1: Prepare System

```bash
# Update system
sudo apt update && sudo apt upgrade -y  # Debian/Ubuntu
sudo yum update -y  # RHEL/CentOS

# Install Python
sudo apt install python3.10 python3.10-venv  # Debian/Ubuntu
sudo yum install python3.10  # RHEL/CentOS
```

#### Step 2: Create Service User

```bash
# Create dedicated user
sudo useradd -r -s /bin/false netmonitor

# Create directories
sudo mkdir -p /opt/netmonitor
sudo mkdir -p /var/log/netmonitor
sudo chown -R netmonitor:netmonitor /opt/netmonitor
sudo chown -R netmonitor:netmonitor /var/log/netmonitor
```

#### Step 3: Install Application

```bash
# Clone repository
cd /opt/netmonitor
sudo -u netmonitor git clone https://github.com/your-org/netmonitor.git .

# Create virtual environment
sudo -u netmonitor python3.10 -m venv venv

# Install dependencies
sudo -u netmonitor venv/bin/pip install -r requirements.txt
```

#### Step 4: Configure

```bash
# Copy and edit configuration
sudo -u netmonitor cp app/config/config.yaml.example app/config/config.yaml
sudo -u netmonitor nano app/config/config.yaml
```

**Production config example:**
```yaml
agent:
  id: "prod-agent-01"
  location: "datacenter-1"
  environment: "production"

interval: 60

exporters:
  influx:
    enabled: true
    url: "http://influxdb.internal:8086"
    org: "production"
    bucket: "network-metrics"
  
  prometheus:
    enabled: true
    port: 8000

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/netmonitor/app.log"
```

#### Step 5: Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/netmonitor.service
```

**Service file:**
```ini
[Unit]
Description=NetMonitor Network Monitoring Agent
After=network.target influxdb.service
Wants=influxdb.service

[Service]
Type=simple
User=netmonitor
Group=netmonitor
WorkingDirectory=/opt/netmonitor
Environment="PATH=/opt/netmonitor/venv/bin"
Environment="INFLUX_TOKEN=your-token-here"
ExecStart=/opt/netmonitor/venv/bin/python -m app.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Step 6: Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable netmonitor

# Start service
sudo systemctl start netmonitor

# Check status
sudo systemctl status netmonitor

# View logs
sudo journalctl -u netmonitor -f
```

---

### Method 2: Docker Deployment

#### Step 1: Build Image

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 netmonitor

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=netmonitor:netmonitor app/ ./app/

# Switch to app user
USER netmonitor

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "app.main"]
```

```bash
# Build image
docker build -t netmonitor:latest .

# Tag for registry
docker tag netmonitor:latest your-registry/netmonitor:1.0.0
```

#### Step 2: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  netmonitor:
    image: netmonitor:latest
    container_name: netmonitor
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - INFLUX_TOKEN=${INFLUX_TOKEN}
    volumes:
      - ./app/config/config.yaml:/app/app/config/config.yaml:ro
      - ./logs:/app/logs
    networks:
      - monitoring
    depends_on:
      - influxdb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=changeme123
      - DOCKER_INFLUXDB_INIT_ORG=net-monitor
      - DOCKER_INFLUXDB_INIT_BUCKET=network
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=${INFLUX_TOKEN}
    volumes:
      - influxdb-data:/var/lib/influxdb2
    networks:
      - monitoring

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme123
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - monitoring

volumes:
  influxdb-data:
  ollama-data:
  grafana-data:

networks:
  monitoring:
    driver: bridge
```

```bash
# Set environment variables
export INFLUX_TOKEN="your-secure-token"

# Start stack
docker-compose up -d

# View logs
docker-compose logs -f netmonitor

# Stop stack
docker-compose down
```

---

### Method 3: Kubernetes Deployment

#### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: netmonitor-config
  namespace: monitoring
data:
  config.yaml: |
    agent:
      id: "k8s-agent-01"
      location: "cluster-prod"
      environment: "production"
    
    interval: 60
    
    exporters:
      influx:
        enabled: true
        url: "http://influxdb:8086"
        org: "production"
        bucket: "network-metrics"
      
      prometheus:
        enabled: true
        port: 8000
```

#### Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: netmonitor-secrets
  namespace: monitoring
type: Opaque
stringData:
  INFLUX_TOKEN: "your-secure-token-here"
```

#### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: netmonitor
  namespace: monitoring
  labels:
    app: netmonitor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: netmonitor
  template:
    metadata:
      labels:
        app: netmonitor
    spec:
      containers:
      - name: netmonitor
        image: your-registry/netmonitor:1.0.0
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: INFLUX_TOKEN
          valueFrom:
            secretKeyRef:
              name: netmonitor-secrets
              key: INFLUX_TOKEN
        volumeMounts:
        - name: config
          mountPath: /app/app/config
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: netmonitor-config
```

#### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: netmonitor
  namespace: monitoring
  labels:
    app: netmonitor
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: netmonitor
```

#### ServiceMonitor (for Prometheus Operator)

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: netmonitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: netmonitor
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

```bash
# Deploy to Kubernetes
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f servicemonitor.yaml

# Check status
kubectl get pods -n monitoring
kubectl logs -f deployment/netmonitor -n monitoring
```

---

## 🔒 Security Hardening

### 1. API Authentication

```python
# app/api/security.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

### 2. TLS/SSL

```bash
# Generate self-signed certificate (dev only)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Production: Use Let's Encrypt
certbot certonly --standalone -d monitor.example.com
```

```python
# Run with HTTPS
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### 3. Firewall Rules

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 8000/tcp comment "NetMonitor API"
sudo ufw enable

# RHEL/CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 4. Secrets Management

```bash
# Use environment files
echo "INFLUX_TOKEN=secret" > .env
chmod 600 .env

# Or use secret management
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
```

---

## 📊 Monitoring the Monitor

### Health Checks

```bash
# Systemd timer for health checks
# /etc/systemd/system/netmonitor-healthcheck.service
[Unit]
Description=NetMonitor Health Check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/check-netmonitor-health.sh
```

```bash
#!/bin/bash
# /usr/local/bin/check-netmonitor-health.sh

HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s "$HEALTH_URL")
STATE=$(echo "$RESPONSE" | jq -r '.state')

if [ "$STATE" != "running" ]; then
    echo "NetMonitor unhealthy: $STATE"
    systemctl restart netmonitor
fi
```

### Log Rotation

```bash
# /etc/logrotate.d/netmonitor
/var/log/netmonitor/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 netmonitor netmonitor
    postrotate
        systemctl reload netmonitor
    endscript
}
```

---

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Backup configuration
cp /opt/netmonitor/app/config/config.yaml /opt/netmonitor/config.yaml.bak

# Pull latest code
cd /opt/netmonitor
sudo -u netmonitor git pull

# Update dependencies
sudo -u netmonitor venv/bin/pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart netmonitor
```

### Blue-Green Deployment

```bash
# Deploy new version to port 8001
sudo systemctl start netmonitor@8001

# Test new version
curl http://localhost:8001/health

# Switch traffic (in load balancer)
# ...

# Stop old version
sudo systemctl stop netmonitor@8000
```

---

## 🔗 Related Documentation

- **[Configuration Guide](CONFIGURATION.md)** - Configuration options
- **[Docker Setup](DOCKER.md)** - Docker-specific docs
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues
- **[Security](SECURITY.md)** - Security best practices