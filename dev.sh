#!/bin/bash

# BeSunny.ai Local Development Startup Script
# This script sets up and starts the local development environment

set -e

echo "🚀 Starting BeSunny.ai Local Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found. Please create backend/.env with your configuration."
    exit 1
fi

if [ ! -f "frontend/.env" ]; then
    echo "❌ Frontend .env file not found. Please create frontend/.env with your configuration."
    exit 1
fi

echo "✅ Environment files found"

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."

# Wait for backend to be ready
echo "🔄 Waiting for backend to be ready..."
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    echo "   Backend not ready yet, waiting..."
    sleep 2
done

echo "✅ Backend is ready!"

# Wait for frontend to be ready
echo "🔄 Waiting for frontend to be ready..."
until curl -f http://localhost:3000 > /dev/null 2>&1; do
    echo "   Frontend not ready yet, waiting..."
    sleep 2
done

echo "✅ Frontend is ready!"

echo ""
echo "🎉 BeSunny.ai Local Development Environment is Ready!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔍 Redis: localhost:6379"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Rebuild services: docker-compose up --build -d"
echo ""
echo "🚀 Happy coding!"
