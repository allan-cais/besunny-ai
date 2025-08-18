#!/bin/bash
# BeSunny.ai Full Stack Startup Script
# Optimized for maximum efficiency and reliability

set -e

echo "🚀 Starting BeSunny.ai Full Stack Application"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is available
port_available() {
    local port=$1
    if command_exists lsof; then
        ! lsof -i :$port >/dev/null 2>&1
    else
        ! netstat -an | grep ":$port " | grep LISTEN >/dev/null 2>&1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for service at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url/health" >/dev/null 2>&1; then
            echo "✅ Service is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Service failed to start within expected time"
    return 1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check npm
if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check pip
if ! command_exists pip3; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

echo "✅ All prerequisites are available"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm ci --silent
echo "✅ Frontend dependencies installed"

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
python3 -m pip install --quiet -r requirements.txt
cd ..
echo "✅ Backend dependencies installed"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  Warning: .env.local not found. Creating from template..."
    if [ -f "env.example" ]; then
        cp env.example .env.local
        echo "✅ Created .env.local from template"
        echo "⚠️  Please update .env.local with your actual configuration values"
    else
        echo "❌ env.example not found. Please create .env.local manually."
        exit 1
    fi
fi

# Start backend
echo "🐍 Starting Python backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo "🚀 Starting backend server..."
python3 start.py &
BACKEND_PID=$!

cd ..

# Wait for backend to be ready
if wait_for_service "http://localhost:8000"; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "⚛️  Starting React frontend..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to be ready
if wait_for_service "http://localhost:5173"; then
    echo "✅ Frontend is running on http://localhost:5173"
else
    echo "❌ Frontend failed to start"
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 BeSunny.ai Full Stack Application is running!"
echo "================================================"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "💚 Health:   http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ Frontend stopped"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ Backend stopped"
    fi
    
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait
