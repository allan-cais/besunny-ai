#!/bin/bash

# BeSunny.ai Railway Full Stack v17 Deployment Script
# Specialized for Railway platform deployment

echo "🚂 Deploying BeSunny.ai Full Stack v17 on Railway..."
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Step 2: Get Backend URL
print_status "Step 2: Configuring Backend URL..."
read -p "Enter your Railway backend URL: " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    print_error "Backend URL is required for frontend configuration"
    exit 1
fi

print_status "Using backend URL: $BACKEND_URL"

# Step 3: Update Railway Configuration
print_status "Step 3: Updating Railway Configuration..."
print_status "Updating VITE_PYTHON_BACKEND_URL in railway.toml..."

# Update the railway.toml file with the actual backend URL
sed -i.bak "s|VITE_PYTHON_BACKEND_URL = \"https://your-railway-backend.railway.app\"|VITE_PYTHON_BACKEND_URL = \"$BACKEND_URL\"|" railway.toml

if [ $? -eq 0 ]; then
    print_success "Railway configuration updated with backend URL"
else
    print_warning "Failed to update railway.toml automatically. Please update manually."
fi

# Step 4: Test Backend Health
print_status "Step 4: Testing Backend Health..."
if command -v curl &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health" 2>/dev/null)
    if [[ $? -eq 0 && "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        print_success "Backend is healthy and responding"
        echo "Response: $HEALTH_RESPONSE" | head -c 200
        echo "..."
    else
        print_warning "Backend health check failed. Please ensure backend is running before continuing."
        read -p "Continue with deployment? (y/N): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled. Please fix backend issues first."
            exit 1
        fi
    fi
else
    print_warning "curl not available. Skipping backend health check."
fi

# Step 5: Build Frontend
print_status "Step 5: Building Frontend..."
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

# Step 6: Deploy to Railway
print_status "Step 6: Deploying Full Stack to Railway..."

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

# Step 7: Get Railway URLs
print_status "Step 7: Getting Railway URLs..."
RAILWAY_STATUS=$(railway status --json 2>/dev/null)

if [ $? -eq 0 ]; then
    # Try to extract URLs from railway status
    FRONTEND_URL=$(echo "$RAILWAY_STATUS" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -z "$FRONTEND_URL" ]; then
        FRONTEND_URL="your-railway-frontend.railway.app"
    fi
else
    FRONTEND_URL="your-railway-frontend.railway.app"
fi

print_success "Full Stack Railway Deployment Complete!"
echo ""
echo "🎉 Your BeSunny.ai Full Stack v17 is now live on Railway!"
echo ""
echo "🔧 Backend (Railway): $BACKEND_URL"
echo "📱 Frontend (Railway): $FRONTEND_URL"
echo ""
echo "🧪 Test Your Full Stack:"
echo "   Backend Health: $BACKEND_URL/health"
echo "   API Docs: $BACKEND_URL/docs"
echo "   Frontend Test: $BACKEND_URL/api/frontend-test"
echo "   V1 Health: $BACKEND_URL/v1/health"
echo "   Frontend App: $FRONTEND_URL"
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
echo "   1. Test your frontend at: $FRONTEND_URL"
echo "   2. Verify backend connectivity"
echo "   3. Test user authentication flow"
echo "   4. Monitor performance and logs"
echo "   5. Configure Supabase integration"
echo ""
echo "🎯 Your full BeSunny.ai application is now operational on Railway!"
echo ""
echo "💡 Pro Tips:"
echo "   - Use 'railway logs' to monitor deployment"
echo "   - Use 'railway status' to check service status"
echo "   - Use 'railway variables' to manage environment variables"
echo "   - Everything is now in one place on Railway!"
