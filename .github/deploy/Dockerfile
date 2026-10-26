# Production Dockerfile for AURA-Fleet Cloud Terminal
# Optimized for Render Web Services & Sandbox Evaluations

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Healthcheck for container stability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/telemetry || exit 1

EXPOSE 8000

# Start Uvicorn ASGI server with dynamic port support for Render
CMD ["sh", "-c", "uvicorn main:web_app --host 0.0.0.0 --port ${PORT:-8000}"]
