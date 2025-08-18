#!/bin/bash

# BeSunny.ai Full Stack Startup Script
# This script starts the backend and frontend services

echo "🚀 Starting BeSunny.ai Full Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists in backend
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found in backend directory."
    echo "📝 Creating from template..."
    cp backend/env.supabase.example backend/.env
    echo "✅ Created backend/.env from template"
    echo "🔧 Please edit backend/.env with your actual API keys and configuration"
    echo "   Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY"
    echo "   Optional: OPENAI_API_KEY, GOOGLE_CLIENT_ID, PINECONE_API_KEY"
    echo ""
    echo "Press Enter when you've configured the .env file..."
    read
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    docker-compose -f backend/docker-compose.supabase.yml down
    echo "✅ Services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

echo "🐳 Starting backend services (Redis + Python Backend)..."
cd backend

# Start backend services with development profile
docker-compose --profile development up --build -d redis backend

# Wait for backend to be healthy
echo "⏳ Waiting for backend to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "⏳ Waiting for backend... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -eq $timeout ]; then
    echo "❌ Backend failed to start within $timeout seconds"
    docker-compose --profile development logs backend
    exit 1
fi

cd ..

echo "📦 Installing frontend dependencies..."
npm install

echo "🌐 Starting frontend..."
npm run dev &

# Store frontend PID
FRONTEND_PID=$!

echo ""
echo "🎉 Full Stack is starting up!"
echo ""
echo "📱 Frontend: http://localhost:3000 (or 5173)"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "💾 Redis: localhost:6379"
echo "🔍 Redis Commander: http://localhost:8081 (development only)"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait $FRONTEND_PID

# Cleanup will be handled by the trap
