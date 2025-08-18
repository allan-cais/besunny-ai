#!/bin/bash

# Build script for Railway deployment
# This script builds the frontend and prepares it for the backend to serve

echo "🚀 Building for Railway deployment..."

# Build the frontend
echo "📦 Building frontend..."
npm run build:staging

# Create backend static directory if it doesn't exist
echo "📁 Creating backend static directory..."
mkdir -p backend/app/static

# Copy built frontend to backend static directory
echo "📋 Copying built frontend to backend..."
cp -r dist/* backend/app/static/

echo "✅ Build complete! Frontend is now in backend/app/static/"
echo "🚀 Ready for Railway deployment!"
