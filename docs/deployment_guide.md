# Deployment Guide

This guide covers deploying the EDI Compliance Rules Engine in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.8+
- 512MB RAM
- 100MB disk space

**Recommended:**
- Python 3.10+
- 2GB RAM
- 500MB disk space (with logs and output)

### Software Dependencies

- Python 3.8 or higher
- pip package manager
- Git (for cloning repository)
- Virtual environment tool (venv or virtualenv)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/itsbrianhughes/PROJECT-4-EDI-COMPLIANCE-RULES-ENGINE.git
cd PROJECT-4-EDI-COMPLIANCE-RULES-ENGINE
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
# Run parser tests
python tests/test_parser.py

# Run validation tests
python tests/test_validator.py

# Run UI demo
python demo_ui_workflow.py
```

### 5. Start Streamlit UI

```bash
streamlit run src/ui/streamlit_app.py
```

Access at: `http://localhost:8501`

## Production Deployment

### Option 1: Systemd Service (Linux)

#### 1. Create Service User

```bash
sudo useradd -r -s /bin/false edi-validator
sudo mkdir -p /opt/edi-validator
sudo chown edi-validator:edi-validator /opt/edi-validator
```

#### 2. Deploy Application

```bash
# Copy application to /opt
sudo cp -r . /opt/edi-validator/
sudo chown -R edi-validator:edi-validator /opt/edi-validator

# Install dependencies
cd /opt/edi-validator
sudo -u edi-validator python -m venv venv
sudo -u edi-validator venv/bin/pip install -r requirements.txt
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/edi-validator.service`:

```ini
[Unit]
Description=EDI Compliance Validator Web UI
After=network.target

[Service]
Type=simple
User=edi-validator
Group=edi-validator
WorkingDirectory=/opt/edi-validator
Environment="PATH=/opt/edi-validator/venv/bin"
ExecStart=/opt/edi-validator/venv/bin/streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable edi-validator
sudo systemctl start edi-validator
sudo systemctl status edi-validator
```

#### 5. Configure Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/edi-validator`:

```nginx
server {
    listen 80;
    server_name edi-validator.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/edi-validator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Option 2: Gunicorn + Nginx (Python App)

While Streamlit doesn't use Gunicorn directly, you can run the validation engine as a Flask/FastAPI app:

#### Create Flask Wrapper (`src/api/app.py`):

```python
from flask import Flask, request, jsonify
from src.validator.validation_engine import ValidationEngine
from src.reporting.report_generator import ReportGenerator

app = Flask(__name__)

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json
    edi_text = data.get('edi_text')
    doc_type = data.get('doc_type')
    retailer = data.get('retailer')

    engine = ValidationEngine()
    result = engine.validate_text(edi_text, doc_type, retailer)

    generator = ReportGenerator(result)

    return jsonify({
        'compliant': result.is_compliant(),
        'errors': result.error_count(),
        'warnings': result.warning_count(),
        'report': generator.generate_json_report()
    })

if __name__ == '__main__':
    app.run()
```

Run with Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 src.api.app:app
```

## Docker Deployment

### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create output directory
RUN mkdir -p output

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Create Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  edi-validator:
    build: .
    container_name: edi-validator
    ports:
      - "8501:8501"
    volumes:
      - ./output:/app/output
      - ./samples:/app/samples:ro
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_HEADLESS=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 3. Build and Run

```bash
# Build image
docker build -t edi-validator:latest .

# Run container
docker run -d -p 8501:8501 --name edi-validator edi-validator:latest

# Or use docker-compose
docker-compose up -d
```

### 4. Docker Commands

```bash
# View logs
docker logs -f edi-validator

# Stop container
docker stop edi-validator

# Restart container
docker restart edi-validator

# Remove container
docker rm -f edi-validator

# Update and redeploy
docker-compose pull
docker-compose up -d
```

## Cloud Deployment

### AWS Elastic Beanstalk

#### 1. Install EB CLI

```bash
pip install awsebcli
```

#### 2. Initialize EB Application

```bash
eb init -p python-3.10 edi-validator
```

#### 3. Create Environment

```bash
eb create edi-validator-prod
```

#### 4. Deploy

```bash
eb deploy
```

### Google Cloud Run

#### 1. Build Container

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/edi-validator
```

#### 2. Deploy

```bash
gcloud run deploy edi-validator \
  --image gcr.io/PROJECT_ID/edi-validator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501
```

### Azure Container Instances

#### 1. Build and Push Image

```bash
az acr build --registry myregistry --image edi-validator:latest .
```

#### 2. Deploy Container

```bash
az container create \
  --resource-group myResourceGroup \
  --name edi-validator \
  --image myregistry.azurecr.io/edi-validator:latest \
  --dns-name-label edi-validator \
  --ports 8501
```

### Heroku

#### 1. Create `Procfile`

```
web: streamlit run src/ui/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

#### 2. Deploy

```bash
heroku create edi-validator
git push heroku main
heroku open
```

## Environment Configuration

### Environment Variables

Create `.env` file (not committed to git):

```bash
# Application Settings
APP_ENV=production
DEBUG=false

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# File Paths
EDI_SAMPLES_DIR=/app/samples
EDI_OUTPUT_DIR=/app/output

# Validation Settings
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=txt,edi,x12

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/edi-validator.log
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = false
```

## Security Considerations

### 1. Input Validation

Already implemented:
- File type restrictions (`.txt`, `.edi`, `.x12`)
- UTF-8 encoding validation
- Maximum file size limits (Streamlit default: 200MB)

### 2. Network Security

```nginx
# Add to Nginx config for HTTPS
server {
    listen 443 ssl http2;
    server_name edi-validator.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config
}
```

### 3. Authentication (Optional)

Add basic auth to Nginx:

```nginx
location / {
    auth_basic "EDI Validator";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://localhost:8501;
    # ... rest of proxy config
}
```

Create password file:

```bash
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

### 4. Rate Limiting

Add to Nginx:

```nginx
limit_req_zone $binary_remote_addr zone=validator:10m rate=10r/s;

server {
    location / {
        limit_req zone=validator burst=20;
        # ... rest of config
    }
}
```

### 5. Firewall Rules

```bash
# Allow only HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Monitoring and Logging

### Application Logging

Configure logging in `config/settings.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/edi-validator.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

#### Streamlit Health Endpoint

```bash
curl http://localhost:8501/_stcore/health
```

#### Custom Health Check Script

Create `healthcheck.py`:

```python
import sys
from src.validator.validation_engine import ValidationEngine

try:
    engine = ValidationEngine()
    result = engine.validate_file("samples/edi_850_valid.txt", "850")
    if result is not None:
        sys.exit(0)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
```

### Monitoring Tools

#### Prometheus + Grafana

1. Install Prometheus Python client:

```bash
pip install prometheus-client
```

2. Add metrics to application
3. Configure Prometheus to scrape metrics
4. Create Grafana dashboards

#### Simple Uptime Monitoring

Use external services:
- UptimeRobot
- Pingdom
- StatusCake

Configure to check: `http://your-domain.com/_stcore/health`

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/edi-validator"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" /opt/edi-validator

# Backup output directory
tar -czf "$BACKUP_DIR/output_$DATE.tar.gz" /opt/edi-validator/output

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
```

Add to cron:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/edi-validator/backup.sh
```

### Recovery

```bash
# Stop service
sudo systemctl stop edi-validator

# Restore application
tar -xzf /backups/edi-validator/app_YYYYMMDD_HHMMSS.tar.gz -C /

# Restore output
tar -xzf /backups/edi-validator/output_YYYYMMDD_HHMMSS.tar.gz -C /

# Start service
sudo systemctl start edi-validator
```

## Performance Tuning

### Streamlit Configuration

Optimize for production in `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 10  # MB
maxMessageSize = 10  # MB
enableWebsocketCompression = true

[runner]
fastReruns = true
```

### System Optimization

```bash
# Increase file descriptors
echo "edi-validator soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "edi-validator hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize TCP settings
sudo sysctl -w net.core.somaxconn=1024
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=1024
```

## Troubleshooting

### Issue: Application won't start

**Check:**
```bash
# View systemd logs
sudo journalctl -u edi-validator -n 50

# Check if port is in use
sudo lsof -i :8501

# Verify Python environment
/opt/edi-validator/venv/bin/python --version
```

### Issue: High memory usage

**Solution:**
- Limit concurrent users
- Increase server RAM
- Implement session cleanup
- Use external caching (Redis)

### Issue: Slow validation

**Check:**
- File size (larger files take longer)
- Retailer rules (more rules = slower)
- Server resources (CPU, RAM)

**Optimize:**
- Use faster storage (SSD)
- Increase CPU allocation
- Profile code for bottlenecks

### Issue: Permission errors

```bash
# Fix ownership
sudo chown -R edi-validator:edi-validator /opt/edi-validator

# Fix permissions
sudo chmod -R 755 /opt/edi-validator
sudo chmod -R 777 /opt/edi-validator/output
```

## Updating the Application

### Manual Update

```bash
cd /opt/edi-validator
sudo -u edi-validator git pull origin main
sudo -u edi-validator venv/bin/pip install -r requirements.txt
sudo systemctl restart edi-validator
```

### Automated Update Script

Create `update.sh`:

```bash
#!/bin/bash
set -e

cd /opt/edi-validator

# Backup current version
tar -czf /backups/pre-update-$(date +%Y%m%d).tar.gz .

# Pull updates
sudo -u edi-validator git pull origin main

# Update dependencies
sudo -u edi-validator venv/bin/pip install -r requirements.txt

# Restart service
sudo systemctl restart edi-validator

# Verify
sleep 5
curl -f http://localhost:8501/_stcore/health || {
    echo "Health check failed, rolling back..."
    tar -xzf /backups/pre-update-*.tar.gz -C /opt/edi-validator
    sudo systemctl restart edi-validator
    exit 1
}

echo "Update successful!"
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/edi-validator
            git pull origin main
            venv/bin/pip install -r requirements.txt
            sudo systemctl restart edi-validator
```

## Summary

This deployment guide covers:
- ✅ Local development setup
- ✅ Production deployment (Systemd, Nginx)
- ✅ Docker containerization
- ✅ Cloud deployment (AWS, GCP, Azure, Heroku)
- ✅ Environment configuration
- ✅ Security best practices
- ✅ Monitoring and logging
- ✅ Backup and recovery
- ✅ Performance tuning
- ✅ Troubleshooting
- ✅ CI/CD integration

Choose the deployment method that best fits your infrastructure and requirements.
