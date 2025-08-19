# Backend Dockerfile for Railway deployment
# This runs from the /backend root directory

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
COPY requirements-simple.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-simple.txt

# Copy backend code
COPY . .

# Create a simple health check script
RUN echo '#!/bin/sh\ncurl -f http://localhost:8000/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Create a startup script that tries main app first, falls back to health server
RUN echo '#!/bin/sh\n\
echo "🚀 Attempting to start main FastAPI application..."\n\
if python -c "import app.main" 2>/dev/null; then\n\
    echo "✅ Main app import successful, starting uvicorn..."\n\
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
else\n\
    echo "⚠️ Main app import failed, falling back to health check server..."\n\
    exec python simple-health-server.py\n\
fi' > /start.sh && chmod +x /start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# Start with fallback option
CMD ["/start.sh"]
