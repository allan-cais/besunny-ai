#!/bin/bash

# BeSunny.ai Backend v17 Deployment Script
# This script helps deploy the v17 backend to Railway

echo "🚀 Deploying BeSunny.ai Backend v17 to Railway..."

# Check if we're in the right directory
if [ ! -f "railway.toml" ]; then
    echo "❌ Error: railway.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found."
    exit 1
fi

# Check if test_app_v17.py exists
if [ ! -f "backend/test_app_v17.py" ]; then
    echo "❌ Error: test_app_v17.py not found in backend directory."
    exit 1
fi

# Check if start_v17.py exists
if [ ! -f "backend/start_v17.py" ]; then
    echo "❌ Error: start_v17.py not found in backend directory."
    exit 1
fi

echo "✅ All required files found"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI found"
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway login status..."
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
else
    echo "✅ Already logged in to Railway"
fi

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your v17 backend should now be running on Railway"
echo "🔗 Check the Railway dashboard for your deployment URL"
echo "📊 Monitor the deployment logs for any issues"
echo ""
echo "🧪 Test your deployment:"
echo "   - Health check: <your-url>/health"
echo "   - API docs: <your-url>/docs"
echo "   - Frontend test: <your-url>/api/frontend-test"
echo "   - V1 health: <your-url>/v1/health"
echo ""
echo "🎉 BeSunny.ai Backend v17 is now live!"
