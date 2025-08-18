#!/bin/bash

# Build script for Railway deployment
# This script builds the frontend and prepares it for the backend to serve

echo "🚀 Building for Railway deployment..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not available. Installing Node.js..."
    # Try to install Node.js if not available
    if command -v apt-get &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
        yum install -y nodejs
    else
        echo "❌ Cannot install Node.js automatically. Please ensure Node.js is available."
        exit 1
    fi
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not available. Installing npm..."
    if command -v apt-get &> /dev/null; then
        apt-get install -y npm
    elif command -v yum &> /dev/null; then
        yum install -y npm
    else
        echo "❌ Cannot install npm automatically. Please ensure npm is available."
        exit 1
    fi
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm ci --only=production
fi

# Build the frontend
echo "📦 Building frontend..."
npm run build:staging

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Frontend build failed - dist directory not found"
    exit 1
fi

# Create backend static directory if it doesn't exist
echo "📁 Creating backend static directory..."
mkdir -p backend/app/static

# Copy built frontend to backend static directory
echo "📋 Copying built frontend to backend..."
cp -r dist/* backend/app/static/

echo "✅ Build complete! Frontend is now in backend/app/static/"
echo "🚀 Ready for Railway deployment!"
