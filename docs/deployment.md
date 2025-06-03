# Deployment Guide

This guide covers deployment options for the University Chatbot system, from local development to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment Options](#cloud-deployment-options)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB available space
- **Network**: Stable internet connection for LLM API calls

### Software Dependencies

- Docker 20.10+ and Docker Compose 2.0+
- Python 3.11+ (for local development)
- Git
- SSL certificate (for production)

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot_db
REDIS_URL=redis://localhost:6379/0

# LLM Provider Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# Vector Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key
CORS_ORIGINS=["http://localhost:3000"]

# External Services
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=["pdf","txt","docx","doc"]
```

### Production Environment Variables

For production, add these additional variables:

```bash
# Production Settings
DEBUG=false
ENV=production
DOMAIN=your-domain.com

# SSL Configuration
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Database (Production)
DATABASE_URL=postgresql://user:password@prod-db:5432/chatbot_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (Production)
REDIS_URL=redis://prod-redis:6379/0
REDIS_POOL_SIZE=10

# Security (Production)
SECURE_COOKIES=true
HTTPS_ONLY=true
RATE_LIMIT_ENABLED=true
```

## Local Deployment

### Option 1: Python Virtual Environment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd university-chatbot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv unibot
   source unibot/bin/activate  # On Windows: unibot\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**:
   ```bash
   python scripts/setup_database.py
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option 2: Development with Docker

```bash
docker-compose up --build
```

## Docker Deployment

### Production Docker Setup

1. **Build the image**:
   ```bash
   docker build -t university-chatbot:latest .
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Docker Compose Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "80:8000"
      - "443:8000"
    environment:
      - ENV=production
      - DEBUG=false
    env_file:
      - .env.prod
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./ssl:/app/ssl
    depends_on:
      - db
      - redis
      - qdrant
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: "1.0"

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: chatbot_prod
      POSTGRES_USER: chatbot_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

## Production Deployment

### Server Setup

1. **Update system packages**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Install Docker Compose**:
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

### SSL Certificate Setup

#### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Option 2: Self-signed Certificate (Development)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/server.key -out ssl/server.crt
```

### Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 10M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
```

### Database Initialization

```bash
# Run database setup
docker-compose exec app python scripts/setup_database.py

# Create admin user
docker-compose exec app python scripts/create_admin_user.py

# Generate initial embeddings
docker-compose exec app python scripts/generate_embeddings.py
```

## Cloud Deployment Options

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and push to ECR**:
   ```bash
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-west-2.amazonaws.com
   docker build -t university-chatbot .
   docker tag university-chatbot:latest <account>.dkr.ecr.us-west-2.amazonaws.com/university-chatbot:latest
   docker push <account>.dkr.ecr.us-west-2.amazonaws.com/university-chatbot:latest
   ```

2. **Create ECS task definition**
3. **Deploy using ECS service**
4. **Use RDS for PostgreSQL**
5. **Use ElastiCache for Redis**

#### Using EC2

```bash
# Launch EC2 instance (t3.medium or larger)
# Install Docker and docker-compose
# Clone repository
# Set up environment variables
# Run with docker-compose
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/university-chatbot
gcloud run deploy --image gcr.io/PROJECT_ID/university-chatbot --platform managed
```

#### Using GKE (Google Kubernetes Engine)

```bash
# Create cluster
gcloud container clusters create chatbot-cluster --num-nodes=3

# Deploy application
kubectl apply -f k8s/
```

### Azure Deployment

#### Using Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name university-chatbot \
  --image university-chatbot:latest \
  --cpu 2 \
  --memory 4 \
  --port 8000
```

### Digital Ocean

#### Using App Platform

1. Create `app.yaml`:
   ```yaml
   name: university-chatbot
   services:
   - name: api
     source_dir: /
     github:
       repo: your-username/university-chatbot
       branch: main
     run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
     environment_slug: python
     instance_count: 2
     instance_size_slug: basic-xxs
     http_port: 8080
     env:
     - key: DEBUG
       value: "false"
   ```

## Monitoring and Logging

### Health Checks

The application provides several health check endpoints:

- `GET /health` - Basic health check
- `GET /health/database` - Database connectivity
- `GET /health/redis` - Redis connectivity
- `GET /health/llm` - LLM provider status

### Logging Configuration

Set up centralized logging:

```bash
# Using Docker logging driver
docker-compose.yml:
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Monitoring with Prometheus

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U chatbot_user chatbot_prod > backup_${DATE}.sql

# Upload to cloud storage
aws s3 cp backup_${DATE}.sql s3://your-backup-bucket/
```

### Data Volume Backup

```bash
# Backup Docker volumes
docker run --rm -v university-chatbot_postgres_data:/data -v $(pwd):/backup alpine tar cvf /backup/postgres_backup.tar /data
```

### Recovery Procedure

```bash
# Restore database
docker-compose exec -T db psql -U chatbot_user chatbot_prod < backup_20240603_120000.sql

# Restore volumes
docker run --rm -v university-chatbot_postgres_data:/data -v $(pwd):/backup alpine tar xvf /backup/postgres_backup.tar -C /
```

## Troubleshooting

### Common Issues

#### Application Won't Start

1. **Check logs**:
   ```bash
   docker-compose logs app
   ```

2. **Verify environment variables**:
   ```bash
   docker-compose exec app printenv
   ```

3. **Check port conflicts**:
   ```bash
   netstat -tulpn | grep :8000
   ```

#### Database Connection Issues

1. **Check database status**:
   ```bash
   docker-compose ps db
   docker-compose logs db
   ```

2. **Test connection**:
   ```bash
   docker-compose exec app python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
   ```

#### High Memory Usage

1. **Monitor resources**:
   ```bash
   docker stats
   ```

2. **Adjust container limits**:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

#### LLM API Errors

1. **Check API keys**:
   ```bash
   docker-compose exec app python scripts/test_api.py
   ```

2. **Monitor rate limits**
3. **Check network connectivity**

### Performance Optimization

#### Database Optimization

```sql
-- Add indexes for better query performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
```

#### Redis Configuration

```redis
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Application Tuning

```python
# In your main.py or config
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Adjust based on CPU cores
        worker_class="uvicorn.workers.UvicornWorker",
        access_log=False,  # Disable for better performance
        server_header=False
    )
```

### Security Checklist

- [ ] Environment variables properly set
- [ ] Database credentials secured
- [ ] API keys rotated regularly
- [ ] SSL/TLS certificates valid
- [ ] CORS origins configured
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] Logs sanitized (no sensitive data)
- [ ] Backup encryption enabled
- [ ] Network security groups configured

### Maintenance Tasks

#### Regular Tasks

1. **Weekly**:
   - Check system resources
   - Review application logs
   - Verify backup integrity

2. **Monthly**:
   - Update dependencies
   - Rotate API keys
   - Clean up old logs
   - Update SSL certificates

3. **Quarterly**:
   - Security audit
   - Performance review
   - Disaster recovery test

#### Update Procedure

```bash
# 1. Backup current deployment
docker-compose exec -T db pg_dump -U chatbot_user chatbot_prod > pre_update_backup.sql

# 2. Pull latest code
git pull origin main

# 3. Build new image
docker-compose build

# 4. Update with zero downtime
docker-compose up -d --no-deps app

# 5. Run migrations if needed
docker-compose exec app python scripts/migrate.py

# 6. Verify deployment
curl -f http://localhost:8000/health
```

For additional support or questions about deployment, please refer to the project documentation or contact the development team.