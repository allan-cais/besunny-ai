#!/bin/bash

# BeSunny.ai Docker Build Script
# Builds both frontend and backend Docker images

echo "🐳 Building BeSunny.ai Docker Images..."
echo "======================================"

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

# Build frontend image
print_status "Building frontend image..."
docker build -f Dockerfile.frontend -t besunny-frontend:latest .

if [ $? -eq 0 ]; then
    print_success "Frontend image built successfully"
else
    print_error "Frontend image build failed"
    exit 1
fi

# Build backend image
print_status "Building backend image..."
docker build -f Dockerfile.backend -t besunny-backend:latest .

if [ $? -eq 0 ]; then
    print_success "Backend image built successfully"
else
    print_error "Backend image build failed"
    exit 1
fi

print_success "All Docker images built successfully!"
echo ""
echo "🎉 Images created:"
echo "   - besunny-frontend:latest"
echo "   - besunny-backend:latest"
echo ""
echo "🚀 To run the services:"
echo "   docker-compose up"
echo ""
echo "   Or run individually:"
echo "   docker run -p 3000:80 besunny-frontend:latest"
echo "   docker run -p 8000:8000 besunny-backend:latest"
