# Multi-service Dockerfile for BeSunny.ai
# This builds both frontend and backend in one container for Railway deployment

# Use Node.js for building frontend and Python for backend
FROM node:18-alpine AS frontend-builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the frontend
RUN npm run build:production

# Python stage for backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/dist ./app/static

# Expose port
EXPOSE 8000

# Start the backend (which will serve both API and frontend)
CMD ["python", "start.py"]
