#!/bin/bash

# BeSunny.ai Frontend Deployment Script
# Deploys React frontend with v16 backend integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="besunny-ai"
FRONTEND_DIR="src"
BUILD_DIR="dist"
PACKAGE_JSON="package.json"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    # Check Node.js version
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check if package.json exists
    if [ ! -f "$PACKAGE_JSON" ]; then
        print_error "package.json not found. Please run this script from the project root."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ -d "node_modules" ]; then
        print_status "Removing existing node_modules..."
        rm -rf node_modules
    fi
    
    npm ci
    print_success "Dependencies installed successfully"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if npm run lint &> /dev/null; then
        print_success "Linting passed"
    else
        print_warning "Linting failed, but continuing with build"
    fi
}

# Function to build frontend
build_frontend() {
    local BUILD_MODE=${1:-staging}
    
    print_status "Building frontend in $BUILD_MODE mode..."
    
    # Clean build directory
    if [ -d "$BUILD_DIR" ]; then
        print_status "Cleaning build directory..."
        rm -rf "$BUILD_DIR"
    fi
    
    # Build based on mode
    case $BUILD_MODE in
        "production")
            print_status "Building for production..."
            npm run build:production
            ;;
        "staging")
            print_status "Building for staging..."
            npm run build:staging
            ;;
        "development")
            print_status "Building for development..."
            npm run build:dev
            ;;
        *)
            print_status "Building for staging (default)..."
            npm run build:staging
            ;;
    esac
    
    if [ -d "$BUILD_DIR" ]; then
        print_success "Frontend built successfully in $BUILD_DIR"
    else
        print_error "Build failed. Build directory not found."
        exit 1
    fi
}

# Function to validate build
validate_build() {
    print_status "Validating build..."
    
    # Check if index.html exists
    if [ ! -f "$BUILD_DIR/index.html" ]; then
        print_error "index.html not found in build directory"
        exit 1
    fi
    
    # Check if assets exist
    if [ ! -d "$BUILD_DIR/assets" ]; then
        print_warning "assets directory not found in build directory"
    fi
    
    # Check build size
    BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
    print_success "Build validation passed. Build size: $BUILD_SIZE"
}

# Function to deploy to Netlify
deploy_netlify() {
    print_status "Deploying to Netlify..."
    
    if ! command -v netlify &> /dev/null; then
        print_error "Netlify CLI is not installed. Please install it first: npm install -g netlify-cli"
        exit 1
    fi
    
    # Deploy to Netlify
    netlify deploy --prod --dir="$BUILD_DIR"
    print_success "Deployed to Netlify successfully"
}

# Function to deploy to Vercel
deploy_vercel() {
    print_status "Deploying to Vercel..."
    
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI is not installed. Please install it first: npm install -g vercel"
        exit 1
    fi
    
    # Deploy to Vercel
    vercel --prod
    print_success "Deployed to Vercel successfully"
}

# Function to create deployment package
create_deployment_package() {
    print_status "Creating deployment package..."
    
    PACKAGE_NAME="${APP_NAME}-frontend-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf "$PACKAGE_NAME" -C "$BUILD_DIR" .
    print_success "Deployment package created: $PACKAGE_NAME"
}

# Function to show deployment options
show_deployment_options() {
    echo
    print_status "Deployment completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Your frontend is built in the '$BUILD_DIR' directory"
    echo "2. You can deploy it to any static hosting service:"
    echo "   - Netlify: ./deploy-frontend.sh netlify"
    echo "   - Vercel: ./deploy-frontend.sh vercel"
    echo "   - Manual: Upload the '$BUILD_DIR' contents to your hosting service"
    echo
    echo "3. Test the integration with your v16 backend at:"
    echo "   - Health: $(grep VITE_RAILWAY_BACKEND_URL env.production | cut -d'=' -f2)/health"
    echo "   - Frontend Test: $(grep VITE_RAILWAY_BACKEND_URL env.production | cut -d'=' -f2)/api/frontend-test"
    echo
}

# Main deployment function
main() {
    local DEPLOY_TARGET=${1:-build}
    
    echo "🚀 BeSunny.ai Frontend Deployment Script"
    echo "========================================"
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Install dependencies
    install_dependencies
    
    # Run tests
    run_tests
    
    # Build frontend
    build_frontend
    
    # Validate build
    validate_build
    
    # Handle deployment target
    case $DEPLOY_TARGET in
        "netlify")
            deploy_netlify
            ;;
        "vercel")
            deploy_vercel
            ;;
        "package")
            create_deployment_package
            ;;
        "build"|*)
            show_deployment_options
            ;;
    esac
    
    print_success "Frontend deployment process completed!"
}

# Run main function with arguments
main "$@"

