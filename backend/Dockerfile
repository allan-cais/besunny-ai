# Backend Dockerfile for Railway deployment
# This runs from the backend/ directory

FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production
ENV DEBUG=false
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    curl \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY backend-service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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
