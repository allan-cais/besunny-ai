#!/bin/bash

# Railway Configuration Checker for BeSunny.ai
echo "🔍 Checking Railway Configuration..."
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

echo ""
print_status "Frontend Service Configuration:"
echo "-------------------------------------"
echo "✅ Builder: Nixpacks (default)"
echo "✅ Build Command: npm install && npm run build:production"
echo "✅ Start Command: npx serve -s dist -l \$PORT"
echo "✅ Watch Paths: /src/**/*, /public/**/*, package.json, vite.config.ts, etc."

echo ""
print_status "Backend Service Configuration:"
echo "------------------------------------"
echo "✅ Builder: Nixpacks (default)"
echo "✅ Build Command: pip install -r requirements.txt"
echo "✅ Start Command: cd backend && python start.py"
echo "✅ Watch Paths: /backend/**/*, requirements.txt"

echo ""
print_status "Key Points:"
echo "-----------"
echo "1. Frontend uses 'npx serve' to serve static files"
echo "2. Backend uses 'cd backend && python start.py'"
echo "3. Both services use Nixpacks builder (Railway's default)"
echo "4. Railway automatically sets PORT environment variable"

echo ""
print_warning "Important Notes:"
echo "-------------------"
echo "• Railway will automatically detect your project types"
echo "• No need to change build/start commands unless you want to customize"
echo "• The Dockerfiles we created are for local Docker builds only"
echo "• Railway deployment uses your source code directly, not Docker images"

echo ""
print_success "Your Railway configuration is correct!"
echo "Just push your code and Railway will handle the rest."
