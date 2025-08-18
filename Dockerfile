# Railway Full Stack v17 - Python Backend + React Frontend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRECODE=1
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=development

# Set work directory
WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy package files for frontend
COPY package*.json ./

# Install ALL frontend dependencies (including dev dependencies for build)
RUN npm ci --include=dev

# Copy frontend source
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./
COPY vite.config.ts ./
COPY tailwind.config.ts ./
COPY tsconfig*.json ./
COPY postcss.config.js ./

# Verify vite is available and build frontend
RUN npx vite --version && npm run build:production

# Copy backend files
COPY backend/ ./backend/

# Install Python dependencies
WORKDIR /app/backend
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Create static directory and copy frontend build
RUN mkdir -p /app/backend/app/static
RUN cp -r /app/dist/* /app/backend/app/static/

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
