#!/bin/bash

# BeSunny.ai Build and Deploy Script
# Builds frontend locally and deploys to Railway

echo "🔨 Building and Deploying BeSunny.ai Full Stack v17..."
echo "===================================================="

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

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "This script must be run from the project root directory."
    exit 1
fi

# Step 1: Clean previous build
print_status "Step 1: Cleaning previous build..."
if [ -d "dist" ]; then
    rm -rf dist
    print_success "Previous build cleaned"
fi

# Step 2: Install dependencies
print_status "Step 2: Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

print_success "Dependencies installed"

# Step 3: Build frontend
print_status "Step 3: Building frontend..."
npm run build:production

if [ $? -ne 0 ]; then
    print_error "Frontend build failed"
    exit 1
fi

# Verify build
if [ ! -d "dist" ]; then
    print_error "Build failed - dist folder not found"
    exit 1
fi

print_success "Frontend built successfully in dist/ folder"

# Step 4: Deploy to Railway
print_status "Step 4: Deploying to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_warning "Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    print_success "Railway CLI found"
fi

# Login to Railway (if not already logged in)
if ! railway whoami &> /dev/null; then
    print_status "Please log in to Railway..."
    railway login
else
    print_success "Already logged in to Railway"
fi

# Deploy
print_status "Deploying to Railway..."
railway up

if [ $? -eq 0 ]; then
    print_success "Deployment successful!"
else
    print_error "Deployment failed"
    exit 1
fi

# Step 5: Get deployment info
print_status "Step 5: Getting deployment information..."
RAILWAY_STATUS=$(railway status --json 2>/dev/null)

if [ $? -eq 0 ]; then
    FRONTEND_URL=$(echo "$RAILWAY_STATUS" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -z "$FRONTEND_URL" ]; then
        FRONTEND_URL="your-railway-app.railway.app"
    fi
else
    FRONTEND_URL="your-railway-app.railway.app"
fi

print_success "Build and Deploy Complete!"
echo ""
echo "🎉 Your BeSunny.ai app is now live on Railway!"
echo ""
echo "📱 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend: Already running on Railway"
echo ""
echo "🧪 Test your deployment:"
echo "   - Frontend: $FRONTEND_URL"
echo "   - Backend Health: Check Railway dashboard"
echo ""
echo "💡 Next steps:"
echo "   - Test the frontend at: $FRONTEND_URL"
echo "   - Check Railway dashboard for logs"
echo "   - Verify backend connectivity"
echo ""
echo "🚀 Ready to use!"
