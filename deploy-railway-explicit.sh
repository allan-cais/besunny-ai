#!/bin/bash

# Railway Explicit Deployment Script
# Forces Railway to use specific config files for each service

set -e

echo "🚀 Deploying BeSunny.ai with explicit Railway configurations..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged into Railway. Please run: railway login"
    exit 1
fi

echo "📋 Current Railway projects:"
railway projects

echo ""
echo "🔧 Please ensure you have two separate Railway projects:"
echo "   1. besunny-ai-frontend (for React frontend)"
echo "   2. besunny-ai-backend (for Python backend)"
echo ""
read -p "Press Enter when you're ready to deploy..."

echo ""
echo "🌐 Deploying Frontend Service..."

# Deploy frontend with explicit config
echo "📁 Linking to frontend project..."
railway link --project besunny-ai-frontend

echo "🚀 Deploying frontend with explicit config..."
railway up --service frontend --config .railway/railway-frontend.toml

echo ""
echo "🐍 Deploying Backend Service..."

# Deploy backend with explicit config
echo "📁 Linking to backend project..."
railway link --project besunny-ai-backend

echo "🚀 Deploying backend with explicit config..."
railway up --service backend --config .railway/railway-backend.toml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your services are now deployed at:"
echo "   Frontend: https://besunny-ai-frontend.railway.app"
echo "   Backend:  https://besunny-ai-backend.railway.app"
echo ""
echo "📝 Next steps:"
echo "   1. Update VITE_PYTHON_BACKEND_URL in frontend environment"
echo "   2. Configure CORS_ORIGINS in backend to allow frontend domain"
echo "   3. Set up your environment variables in Railway dashboard"
echo ""
echo "🔍 Troubleshooting:"
echo "   - Check Railway logs for each service"
echo "   - Verify the correct config files are being used"
echo "   - Ensure environment variables are set correctly"
echo ""
echo "🎉 Happy coding!"
