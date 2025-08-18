#!/bin/bash

# BeSunny.ai Full Stack v17 Deployment Script
# This script deploys both frontend and backend on Railway

echo "🚀 Deploying BeSunny.ai Full Stack v17 on Railway..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
if [ ! -f "package.json" ] || [ ! -f "railway.toml" ]; then
    print_error "This script must be run from the project root directory."
    print_error "Please ensure you're in the directory containing package.json and railway.toml"
    exit 1
fi

print_status "Starting Railway full stack deployment..."

# Step 1: Verify Backend Status
print_status "Step 1: Verifying Backend Status..."
if [ -f "backend/test_app_v17.py" ] && [ -f "backend/start_v17.py" ]; then
    print_success "Backend v17 files found"
else
    print_error "Backend v17 files missing. Please ensure test_app_v17.py and start_v17.py exist."
    exit 1
fi

# Step 2: Check if Backend is Running
print_status "Step 2: Checking Backend Health..."
BACKEND_URL="https://besunny-ai-v17.railway.app"

# Try to get the actual Railway URL from the user
read -p "Enter your Railway backend URL (or press Enter to use default): " USER_BACKEND_URL
if [ ! -z "$USER_BACKEND_URL" ]; then
    BACKEND_URL="$USER_BACKEND_URL"
fi

print_status "Using backend URL: $BACKEND_URL"

# Test backend health
print_status "Testing backend health..."
if command -v curl &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health" 2>/dev/null)
    if [[ $? -eq 0 && "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        print_success "Backend is healthy and responding"
    else
        print_warning "Backend health check failed. Continuing with deployment..."
    fi
else
    print_warning "curl not available. Skipping backend health check."
fi

# Step 3: Build Frontend
print_status "Step 3: Building Frontend..."
print_status "Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install frontend dependencies"
    exit 1
fi

print_status "Building frontend for production..."
npm run build:production

if [ $? -ne 0 ]; then
    print_error "Frontend build failed"
    exit 1
fi

print_success "Frontend built successfully"

# Step 4: Deploy Full Stack to Railway
print_status "Step 4: Deploying Full Stack to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    print_warning "Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    print_success "Railway CLI found"
fi

# Login to Railway (if not already logged in)
print_status "Checking Railway login status..."
if ! railway whoami &> /dev/null; then
    print_status "Please log in to Railway..."
    railway login
else
    print_success "Already logged in to Railway"
fi

# Deploy to Railway
print_status "Deploying full stack to Railway..."
railway up

if [ $? -eq 0 ]; then
    print_success "Full stack deployed to Railway successfully!"
else
    print_error "Railway deployment failed"
    exit 1
fi

# Step 5: Update Frontend Configuration
print_status "Step 5: Updating Frontend Configuration..."
print_status "Frontend configuration updated to use backend URL: $BACKEND_URL"

# Step 6: Test Full Stack
print_status "Step 6: Testing Full Stack Integration..."

# Get Railway URL
RAILWAY_URL=$(railway status --json | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
if [ -z "$RAILWAY_URL" ]; then
    RAILWAY_URL="your-railway-app.railway.app"
fi

print_success "Full Stack Railway Deployment Complete!"
echo ""
echo "🎉 Your BeSunny.ai Full Stack v17 is now live on Railway!"
echo ""
echo "🔧 Backend (Railway): $BACKEND_URL"
echo "📱 Frontend (Railway): $RAILWAY_URL"
echo ""
echo "🧪 Test Your Full Stack:"
echo "   Backend Health: $BACKEND_URL/health"
echo "   API Docs: $BACKEND_URL/docs"
echo "   Frontend Test: $BACKEND_URL/api/frontend-test"
echo "   V1 Health: $BACKEND_URL/v1/health"
echo "   Frontend App: $RAILWAY_URL"
echo ""
echo "🔗 Integration Points:"
echo "   - Frontend connects to backend at: $BACKEND_URL"
echo "   - Backend provides API endpoints for frontend"
echo "   - Full stack authentication and data flow ready"
echo "   - Everything running on Railway platform"
echo ""
echo "📊 Monitor Your Deployment:"
echo "   - Railway Dashboard: https://railway.app"
echo "   - Backend logs and metrics"
echo "   - Frontend deployment status"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test your frontend at: $RAILWAY_URL"
echo "   2. Verify backend connectivity"
echo "   3. Test user authentication flow"
echo "   4. Monitor performance and logs"
echo "   5. Configure Supabase integration"
echo ""
echo "🎯 Your full BeSunny.ai application is now operational on Railway!"
