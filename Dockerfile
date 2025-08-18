# Railway Full Stack v17 - Python Backend + Pre-built React Frontend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRECODE=1
ENV PYTHONPATH=/app/backend

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files first
COPY backend/ ./backend/

# Install Python dependencies
WORKDIR /app/backend
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Create static directory for frontend files
RUN mkdir -p /app/backend/app/static

# Copy pre-built frontend files (built locally)
COPY dist/ /app/backend/app/static/

# Set working directory to backend for the application
WORKDIR /app/backend

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port (Railway will set the actual port via $PORT)
EXPOSE $PORT

# Health check with longer start period and better error handling
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=10 \
    CMD curl -f http://localhost:$PORT/health || curl -f http://localhost:8000/health || exit 1

# Run application from backend directory
CMD ["python", "start_v17.py"]
