# Backend Dockerfile for Railway deployment
# Multi-stage build to avoid compilation issues

# Build stage - use full Python image for building packages
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend-service/requirements.txt .

# Install packages and create wheels (including dependencies)
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Final stage - use Alpine for smaller image
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production
ENV DEBUG=false
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app

# Set Python build environment variables
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    curl \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    build-base \
    postgresql-dev \
    && rm -rf /var/cache/apk/*

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels

# Copy requirements
COPY backend-service/requirements.txt .

# Install packages from wheels, fallback to pip for missing ones
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --find-links /wheels -r requirements.txt && \
    rm -rf /wheels

# Copy backend code
COPY . .

# Create a simple health check script
RUN echo '#!/bin/sh\ncurl -f http://localhost:8000/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# Start the FastAPI application directly
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
