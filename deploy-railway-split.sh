#!/bin/bash

# Railway Split Deployment Script
# Deploys frontend and backend as separate services

set -e

echo "🚀 Deploying BeSunny.ai as separate Railway services..."

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
echo "🔧 Please create two separate Railway projects:"
echo "   1. besunny-ai-frontend (for React frontend)"
echo "   2. besunny-ai-backend (for Python backend)"
echo ""
read -p "Press Enter when you've created both projects..."

echo ""
echo "🌐 Deploying Frontend Service..."

# Deploy frontend
echo "📁 Switching to frontend project..."
railway link --project besunny-ai-frontend
echo "🚀 Deploying frontend..."
railway up --service frontend --config .railway/railway-frontend.toml

echo ""
echo "🐍 Deploying Backend Service..."

# Deploy backend
echo "📁 Switching to backend project..."
railway link --project besunny-ai-backend
echo "🚀 Deploying backend..."
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
echo "🎉 Happy coding!"
