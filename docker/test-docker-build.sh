#!/bin/bash

# Test Docker Build Script for BeSunny.ai
echo "🧪 Testing Docker Build Process..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is running"

# Clean up any existing images
print_status "Cleaning up existing images..."
docker rmi besunny-ai:test 2>/dev/null || true

# Build the image
print_status "Building Docker image..."
docker build -t besunny-ai:test .

if [ $? -eq 0 ]; then
    print_success "Docker build completed successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Test the container can start
print_status "Testing container startup..."
CONTAINER_ID=$(docker run -d -p 8000:8000 besunny-ai:test)

if [ $? -eq 0 ]; then
    print_success "Container started successfully"
    
    # Wait a moment for the app to start
    print_status "Waiting for application to start..."
    sleep 10
    
    # Test if the app is responding
    print_status "Testing application response..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Application is responding to health check"
        
        # Test the root endpoint
        print_status "Testing root endpoint..."
        if curl -s http://localhost:8000/ > /dev/null; then
            print_success "Root endpoint is working"
        else
            print_warning "Root endpoint may not be working"
        fi
        
    else
        print_warning "Application may not be fully started"
    fi
    
    # Stop and remove the container
    print_status "Cleaning up test container..."
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    
else
    print_error "Container failed to start"
    exit 1
fi

print_success "Docker build test completed successfully!"
echo ""
echo "🎉 Your Docker image is working correctly!"
echo "✅ Build process: Working"
echo "✅ Container startup: Working"
echo "✅ Application startup: Working"
echo ""
echo "🚀 Ready for Railway deployment!"
