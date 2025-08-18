#!/bin/bash

# Railway Nuclear Deployment Script
# Completely resets Railway configuration and forces use of our new configs

set -e

echo "🚀 Nuclear Deployment for BeSunny.ai..."
echo "⚠️  This will completely reset Railway configuration"

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
read -p "Press Enter when you're ready for nuclear deployment..."

echo ""
echo "🧹 Nuclear cleanup starting..."

# Force unlink any existing project
echo "🔗 Unlinking any existing project..."
railway unlink 2>/dev/null || true

# Clear any cached configuration
echo "🗑️  Clearing cached configuration..."
rm -rf .railway/cache 2>/dev/null || true

echo ""
echo "🌐 Deploying Frontend Service (Nuclear Reset)..."

# Deploy frontend with explicit config
echo "📁 Linking to frontend project..."
railway link --project besunny-ai-frontend

echo "🚀 Deploying frontend with nuclear reset..."
railway up --service frontend --config railway-frontend-service.toml --force

echo ""
echo "🐍 Deploying Backend Service (Nuclear Reset)..."

# Force unlink any existing project
echo "🔗 Unlinking any existing project..."
railway unlink 2>/dev/null || true

# Deploy backend with explicit config
echo "📁 Linking to backend project..."
railway link --project besunny-ai-backend

echo "🚀 Deploying backend with nuclear reset..."
railway up --service backend --config railway-backend-service.toml --force

echo ""
echo "✅ Nuclear Deployment complete!"
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
echo "🔍 What we did (Nuclear Reset):"
echo "   - Completely unlinked all projects"
echo "   - Cleared cached configuration"
echo "   - Used --force flag for deployment"
echo "   - Explicit config file usage"
echo "   - Removed all Dockerfile interference"
echo ""
echo "🎉 Happy coding!"
