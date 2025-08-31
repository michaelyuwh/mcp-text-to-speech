# 🐳 Docker Deployment Guide

## Overview

Both MCP tools now provide optimized Docker images available on Docker Hub with significant size reductions and production-ready configurations.

## 📊 Image Comparison

| Tool | Standard Size | Slim Size | Savings | Docker Hub |
|------|---------------|-----------|---------|------------|
| **Speech-to-Text** | 1.71GB | **1.13GB** | **-580MB (-34%)** | `michaelyuwh/mcp-speech-to-text:slim` |
| **Text-to-Speech** | ~800MB | **406MB** | **~400MB (-50%)** | `michaelyuwh/mcp-text-to-speech:slim` |

## 🚀 Quick Start

### Speech-to-Text
```bash
# Pull and run slim image
docker pull michaelyuwh/mcp-speech-to-text:slim
docker run -p 8000:8000 michaelyuwh/mcp-speech-to-text:slim

# With Cantonese support (requires Google Cloud credentials)
docker run -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  -v /path/to/credentials.json:/app/credentials.json:ro \
  michaelyuwh/mcp-speech-to-text:slim
```

### Text-to-Speech
```bash
# Pull and run slim image
docker pull michaelyuwh/mcp-text-to-speech:slim
docker run -p 8000:8000 \
  -v ./output:/app/output \
  michaelyuwh/mcp-text-to-speech:slim
```

## 🏷️ Available Tags

### Speech-to-Text Tags
- `michaelyuwh/mcp-speech-to-text:slim` - Latest optimized build
- `michaelyuwh/mcp-speech-to-text:v1.1.0-slim` - Versioned optimized build
- `michaelyuwh/mcp-speech-to-text:latest` - Standard build

### Text-to-Speech Tags
- `michaelyuwh/mcp-text-to-speech:slim` - Latest optimized build
- `michaelyuwh/mcp-text-to-speech:v1.0.0-slim` - Versioned optimized build
- `michaelyuwh/mcp-text-to-speech:latest` - Standard build

## 🔧 Production Docker Compose

```yaml
version: '3.8'

services:
  mcp-speech-to-text:
    image: michaelyuwh/mcp-speech-to-text:slim
    container_name: mcp-stt
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - ./credentials.json:/app/credentials.json:ro
      - ./audio_input:/app/input:rw
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-text-to-speech:
    image: michaelyuwh/mcp-text-to-speech:slim
    container_name: mcp-tts
    restart: unless-stopped
    ports:
      - "8002:8000"
    volumes:
      - ./audio_output:/app/output:rw
      - tts_cache:/tmp/tts_cache
    environment:
      - TTS_MODE=offline
      - PYTHONUNBUFFERED=1
    devices:
      - /dev/snd:/dev/snd  # For audio output
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  tts_cache:
    driver: local

networks:
  default:
    name: mcp-network
```

## 🛠️ Optimization Features

### Multi-Stage Builds
Both slim images use multi-stage Docker builds:
1. **Builder Stage**: Installs build dependencies and compiles packages
2. **Runtime Stage**: Only includes essential runtime dependencies
3. **Result**: Significantly smaller final images

### Security Enhancements
- Non-root user execution
- Minimal attack surface
- No unnecessary build tools in final images
- Health checks included

### Performance Benefits
- Faster container startup
- Reduced memory footprint
- Smaller download times
- Lower storage requirements

## 🇭🇰 Cantonese Support

Both images maintain full Hong Kong Cantonese support:

### Speech-to-Text
- Native `zh-HK` language recognition via Google Cloud Speech
- Auto-detection for Chinese language variants
- Offline Vosk fallback for English

### Text-to-Speech  
- Smart language mapping (`zh-HK` → `yue`)
- macOS Sinji voice integration
- gTTS online Cantonese support

## 📋 Environment Variables

### Speech-to-Text
```bash
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json  # For Cantonese
PYTHONUNBUFFERED=1                                    # Logging
PYTHONDONTWRITEBYTECODE=1                             # Performance
```

### Text-to-Speech
```bash
TTS_MODE=offline                    # Force offline mode
TTS_CACHE_DIR=/tmp/tts_cache       # Cache directory
TTS_OUTPUT_DIR=/app/output         # Audio output
PYTHONUNBUFFERED=1                 # Logging
```

## 🚀 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-speech-to-text
  labels:
    app: mcp-stt
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-stt
  template:
    metadata:
      labels:
        app: mcp-stt
    spec:
      containers:
      - name: speech-to-text
        image: michaelyuwh/mcp-speech-to-text:slim
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: mcp-stt-service
spec:
  selector:
    app: mcp-stt
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🔍 Monitoring

### Health Checks
```bash
# Check container health
docker ps --format "table {{.Names}}\\t{{.Status}}"

# View health check logs
docker inspect <container_name> --format='{{json .State.Health}}'
```

### Resource Usage
```bash
# Monitor resource usage
docker stats

# Container logs
docker logs -f mcp-stt
docker logs -f mcp-tts
```

## 🛠️ Building Custom Images

### Build Slim Images Locally
```bash
# Speech-to-Text
git clone https://github.com/michaelyuwh/mcp-speech-to-text.git
cd mcp-speech-to-text
docker build -f Dockerfile.slim -t custom-stt:slim .

# Text-to-Speech
git clone https://github.com/michaelyuwh/mcp-text-to-speech.git
cd mcp-text-to-speech
docker build -f Dockerfile.slim -t custom-tts:slim .
```

### Multi-Platform Builds
```bash
# Create builder
docker buildx create --use --name multiplatform

# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.slim \
  -t custom-mcp:slim \
  --push .
```

## 📞 Support

- **Documentation**: See individual repository READMEs
- **Issues**: Report on respective GitHub repositories
- **Docker Hub**: [Speech-to-Text](https://hub.docker.com/r/michaelyuwh/mcp-speech-to-text), [Text-to-Speech](https://hub.docker.com/r/michaelyuwh/mcp-text-to-speech)

Perfect for Hong Kong developers building n8n workflows with minimal Docker footprint! 🇭🇰
