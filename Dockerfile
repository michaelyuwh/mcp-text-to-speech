# Multi-stage build for MCP Text-to-Speech Server
# Optimized for production deployment with offline TTS capabilities

# Build stage
FROM python:3.13-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies into virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache .

# Production stage
FROM python:3.13-slim as production

# Install runtime system dependencies for TTS
RUN apt-get update && apt-get install -y \
    # Audio system dependencies
    alsa-utils \
    pulseaudio \
    # espeak TTS engine
    espeak \
    espeak-data \
    # festival TTS engine
    festival \
    festvox-kallpc16k \
    # Audio codecs and utilities
    sox \
    libsox-fmt-mp3 \
    ffmpeg \
    # System utilities
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1001 ttsuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
WORKDIR /app
COPY . .

# Set proper permissions
RUN chown -R ttsuser:ttsuser /app

# Create directories for audio output
RUN mkdir -p /app/output /tmp/tts_cache && \
    chown -R ttsuser:ttsuser /app/output /tmp/tts_cache

# Switch to non-root user
USER ttsuser

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV TTS_CACHE_DIR=/tmp/tts_cache
ENV TTS_OUTPUT_DIR=/app/output

# Audio environment variables
ENV PULSE_RUNTIME_PATH=/tmp/pulse
ENV ALSA_CARD=0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from mcp_text_to_speech import OfflineTextToSpeechServer; print('OK')" || exit 1

# Expose MCP port (if needed for TCP mode)
EXPOSE 8000

# Default command - run auto-detection server
CMD ["python", "-m", "mcp_text_to_speech"]

# Build information
LABEL org.opencontainers.image.title="MCP Text-to-Speech Server"
LABEL org.opencontainers.image.description="Offline and online text-to-speech MCP server with multi-engine support"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="MCP TTS Developer"
LABEL org.opencontainers.image.source="https://github.com/yourusername/mcp-text-to-speech"
