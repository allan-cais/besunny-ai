#!/bin/bash

# Railway Force Clean Deployment Script
# Forces Railway to use our new configs and clears any cached configuration

set -e

echo "🚀 Force Clean Deployment for BeSunny.ai..."

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

echo "🧹 Clearing any cached Railway configuration..."
echo "📋 Current Railway projects:"
railway projects

echo ""
echo "🔧 Please ensure you have two separate Railway projects:"
echo "   1. besunny-ai-frontend (for React frontend)"
echo "   2. besunny-ai-backend (for Python backend)"
echo ""
read -p "Press Enter when you're ready to deploy..."

echo ""
echo "🌐 Deploying Frontend Service (Force Clean)..."

# Force unlink any existing project
echo "🔗 Unlinking any existing project..."
railway unlink 2>/dev/null || true

# Deploy frontend with explicit config
echo "📁 Linking to frontend project..."
railway link --project besunny-ai-frontend

echo "🚀 Deploying frontend with force clean..."
railway up --service frontend --config .railway/railway-frontend.toml --force

echo ""
echo "🐍 Deploying Backend Service (Force Clean)..."

# Force unlink any existing project
echo "🔗 Unlinking any existing project..."
railway unlink 2>/dev/null || true

# Deploy backend with explicit config
echo "📁 Linking to backend project..."
railway link --project besunny-ai-backend

echo "🚀 Deploying backend with force clean..."
railway up --service backend --config .railway/railway-backend.toml --force

echo ""
echo "✅ Force Clean Deployment complete!"
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
echo "🔍 What we fixed:"
echo "   - Excluded Supabase functions (deno.json files)"
echo "   - Forced technology detection (Node.js vs Python)"
echo "   - Used --force flag to clear cached configuration"
echo "   - Explicit config file usage"
echo ""
echo "🎉 Happy coding!"
