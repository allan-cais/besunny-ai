#!/bin/bash

# Test Build Script for BeSunny.ai Frontend
# This script tests the build process locally before deployment

echo "🧪 Testing Frontend Build Process..."
echo "===================================="

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

# Step 1: Check Node.js and npm
print_status "Step 1: Checking Node.js and npm..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install npm first."
    exit 1
fi

print_success "Node.js $(node --version) and npm $(npm --version) found"

# Step 2: Check if vite is available
print_status "Step 2: Checking if vite is available..."
if ! npx vite --version &> /dev/null; then
    print_warning "vite not found in npx. Checking package.json..."
    
    if grep -q '"vite"' package.json; then
        print_status "vite found in package.json. Installing dependencies..."
        npm install
    else
        print_error "vite not found in package.json. Please add it to devDependencies."
        exit 1
    fi
else
    VITE_VERSION=$(npx vite --version)
    print_success "vite $VITE_VERSION found"
fi

# Step 3: Clean previous build
print_status "Step 3: Cleaning previous build..."
if [ -d "dist" ]; then
    rm -rf dist
    print_success "Previous build cleaned"
fi

# Step 4: Install dependencies
print_status "Step 4: Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi

print_success "Dependencies installed"

# Step 5: Test build
print_status "Step 5: Testing build process..."
npm run build:production

if [ $? -ne 0 ]; then
    print_error "Build failed"
    exit 1
fi

# Step 6: Verify build output
print_status "Step 6: Verifying build output..."
if [ ! -d "dist" ]; then
    print_error "Build failed - dist folder not found"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    print_error "Build failed - index.html not found in dist folder"
    exit 1
fi

print_success "Build successful! dist/ folder created with:"
ls -la dist/

# Step 7: Test the build locally
print_status "Step 7: Testing build locally..."
if command -v python3 &> /dev/null; then
    print_status "Starting local server to test build..."
    cd dist && python3 -m http.server 3000 &
    SERVER_PID=$!
    
    print_status "Waiting for server to start..."
    sleep 3
    
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Local server test successful! Build is working."
        print_status "You can test at: http://localhost:3000"
        print_status "Press Ctrl+C to stop the test server"
        
        # Wait for user to stop
        wait $SERVER_PID
    else
        print_warning "Local server test failed, but build completed successfully"
        kill $SERVER_PID 2>/dev/null
    fi
else
    print_warning "Python not available for local testing, but build completed successfully"
fi

print_success "Build test completed successfully!"
echo ""
echo "🎉 Your frontend build process is working correctly!"
echo ""
echo "📁 Build output: dist/ folder"
echo "🚀 Ready for deployment to Railway!"
echo ""
echo "💡 Next steps:"
echo "   1. Push to your dev branch"
echo "   2. Railway will auto-deploy with this build process"
echo "   3. Your full stack app will be live!"
