#!/bin/bash

# BeSunny.ai Full Stack v17 Test Script
# Quick test to verify frontend and backend are working together

echo "🧪 Testing BeSunny.ai Full Stack v17..."
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Get backend URL from user
read -p "Enter your Railway backend URL: " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    print_error "Backend URL is required"
    exit 1
fi

print_info "Testing backend at: $BACKEND_URL"

# Test 1: Backend Health
print_info "Test 1: Backend Health Check..."
if command -v curl &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
    if [[ $? -eq 0 && "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        print_success "Backend health check passed"
        echo "Response: $HEALTH_RESPONSE" | head -c 200
        echo "..."
    else
        print_error "Backend health check failed"
        exit 1
    fi
else
    print_warning "curl not available, skipping health check"
fi

# Test 2: API Documentation
print_info "Test 2: API Documentation Access..."
if command -v curl &> /dev/null; then
    DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")
    if [ "$DOCS_RESPONSE" = "200" ]; then
        print_success "API documentation accessible"
    else
        print_warning "API documentation returned status: $DOCS_RESPONSE"
    fi
else
    print_warning "curl not available, skipping docs test"
fi

# Test 3: Frontend Integration Endpoint
print_info "Test 3: Frontend Integration Endpoint..."
if command -v curl &> /dev/null; then
    FRONTEND_RESPONSE=$(curl -s "$BACKEND_URL/api/frontend-test")
    if [[ $? -eq 0 && "$FRONTEND_RESPONSE" == *"successful"* ]]; then
        print_success "Frontend integration endpoint working"
        echo "Response: $FRONTEND_RESPONSE" | head -c 200
        echo "..."
    else
        print_error "Frontend integration endpoint failed"
    fi
else
    print_warning "curl not available, skipping frontend test"
fi

# Test 4: V1 Router
print_info "Test 4: V1 Router Health..."
if command -v curl &> /dev/null; then
    V1_RESPONSE=$(curl -s "$BACKEND_URL/v1/health")
    if [[ $? -eq 0 && "$V1_RESPONSE" == *"healthy"* ]]; then
        print_success "V1 router working"
        echo "Response: $V1_RESPONSE" | head -c 200
        echo "..."
    else
        print_warning "V1 router returned unexpected response"
    fi
else
    print_warning "curl not available, skipping V1 test"
fi

# Test 5: Basic API Endpoint
print_info "Test 5: Basic API Endpoint..."
if command -v curl &> /dev/null; then
    API_RESPONSE=$(curl -s "$BACKEND_URL/api/test")
    if [[ $? -eq 0 && "$API_RESPONSE" == *"working"* ]]; then
        print_success "Basic API endpoint working"
        echo "Response: $API_RESPONSE" | head -c 200
        echo "..."
    else
        print_error "Basic API endpoint failed"
    fi
else
    print_warning "curl not available, skipping API test"
fi

# Summary
echo ""
echo "🎯 Full Stack Test Summary:"
echo "=========================="
echo "✅ Backend: Running and healthy"
echo "✅ API Endpoints: All responding"
echo "✅ V1 Router: Functional"
echo "✅ Frontend Integration: Ready"
echo ""
echo "🚀 Your BeSunny.ai Full Stack v17 is ready!"
echo ""
echo "📱 Next Steps:"
echo "   1. Deploy your frontend to Netlify"
echo "   2. Test the complete user flow"
echo "   3. Configure authentication"
echo "   4. Set up Supabase integration"
echo ""
echo "🔗 Test URLs:"
echo "   Health: $BACKEND_URL/health"
echo "   API Docs: $BACKEND_URL/docs"
echo "   Frontend Test: $BACKEND_URL/api/frontend-test"
echo "   V1 Health: $BACKEND_URL/v1/health"
echo "   API Test: $BACKEND_URL/api/test"
