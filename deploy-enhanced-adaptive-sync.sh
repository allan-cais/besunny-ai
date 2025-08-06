#!/bin/bash

# Enhanced Adaptive Sync Framework Deployment Script
# This script deploys the enhanced adaptive sync system with virtual email integration

set -e

echo "🚀 Deploying Enhanced Adaptive Sync Framework with Virtual Email Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    print_error "Supabase CLI is not installed. Please install it first."
    print_status "Install with: npm install -g supabase"
    exit 1
fi

# Check if user is logged into Supabase
if ! supabase status &> /dev/null; then
    print_error "Not connected to Supabase. Please run 'supabase login' first."
    exit 1
fi

print_status "Starting deployment of Enhanced Adaptive Sync Framework..."

# Step 1: Build the frontend
print_status "Building frontend with enhanced adaptive sync..."
npm run build

if [ $? -eq 0 ]; then
    print_success "Frontend build completed successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

# Step 2: Deploy the enhanced adaptive sync service
print_status "Deploying enhanced adaptive sync service..."
supabase functions deploy enhanced-adaptive-sync-service

if [ $? -eq 0 ]; then
    print_success "Enhanced adaptive sync service deployed successfully"
else
    print_error "Failed to deploy enhanced adaptive sync service"
    exit 1
fi

# Step 3: Test the enhanced adaptive sync service
print_status "Testing enhanced adaptive sync service..."

# Get Supabase URL and anon key
SUPABASE_URL=$(supabase status --output json | jq -r '.api.url')
SUPABASE_ANON_KEY=$(supabase status --output json | jq -r '.api.anon_key')

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    print_warning "Could not get Supabase URL or anon key. Skipping service test."
else
    # Test the enhanced adaptive sync service
    TEST_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "userId": "test-user-id",
            "service": "gmail",
            "activityType": "virtual_email_detected",
            "virtualEmailDetection": {
                "emailAddress": "ai+testuser@besunny.ai",
                "messageId": "test-message-id",
                "type": "to"
            }
        }' \
        "$SUPABASE_URL/functions/v1/enhanced-adaptive-sync-service")

    if echo "$TEST_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        print_success "Enhanced adaptive sync service test passed"
    else
        print_warning "Enhanced adaptive sync service test failed or returned unexpected response"
        print_status "Response: $TEST_RESPONSE"
    fi
fi

# Step 4: Deploy frontend (if Netlify CLI is available)
if command -v netlify &> /dev/null; then
    print_status "Deploying frontend to Netlify..."
    netlify deploy --prod --dir=dist
    
    if [ $? -eq 0 ]; then
        print_success "Frontend deployed to Netlify successfully"
    else
        print_error "Failed to deploy frontend to Netlify"
        print_status "You can manually deploy by pushing to your Git repository or uploading the dist folder"
    fi
else
    print_warning "Netlify CLI not found. Skipping frontend deployment."
    print_status "To deploy frontend:"
    print_status "1. Push changes to your Git repository (if connected to Netlify)"
    print_status "2. Or install Netlify CLI: npm install -g netlify-cli"
    print_status "3. Or manually upload the dist folder to Netlify"
fi

# Step 5: Verify deployment
print_status "Verifying deployment..."

# Check if enhanced adaptive sync service is accessible
if [ ! -z "$SUPABASE_URL" ]; then
    HEALTH_CHECK=$(curl -s -X POST \
        -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
        -H "Content-Type: application/json" \
        -d '{"userId": "health-check", "service": "all"}' \
        "$SUPABASE_URL/functions/v1/enhanced-adaptive-sync-service")

    if echo "$HEALTH_CHECK" | jq -e '.success' > /dev/null 2>&1; then
        print_success "Enhanced adaptive sync service is healthy and responding"
    else
        print_warning "Enhanced adaptive sync service health check failed"
        print_status "Response: $HEALTH_CHECK"
    fi
fi

# Step 6: Display deployment summary
echo ""
print_success "🎉 Enhanced Adaptive Sync Framework Deployment Complete!"
echo ""
print_status "Deployment Summary:"
echo "  ✅ Enhanced adaptive sync strategy (src/lib/enhanced-adaptive-sync-strategy.ts)"
echo "  ✅ Enhanced React hooks (src/hooks/use-enhanced-adaptive-sync.ts)"
echo "  ✅ Enhanced edge function (supabase/functions/enhanced-adaptive-sync-service)"
echo "  ✅ Frontend build completed"
echo "  ✅ Enhanced adaptive sync service deployed"
echo ""
print_status "Key Features Deployed:"
echo "  🎯 Virtual email activity tracking"
echo "  ⚡ Smart interval management (1min - 15min)"
echo "  🔄 Enhanced Gmail and Calendar integration"
echo "  📊 Performance metrics and analytics"
echo "  🤖 Auto-scheduled meeting detection"
echo ""
print_status "Next Steps:"
echo "  1. Update your components to use the enhanced hooks:"
echo "     import { useEnhancedAdaptiveSync } from '@/hooks/use-enhanced-adaptive-sync';"
echo ""
echo "  2. Test virtual email detection:"
echo "     Send an email to ai+username@besunny.ai and verify detection"
echo ""
echo "  3. Monitor sync performance:"
echo "     Check the enhanced sync statistics in your dashboard"
echo ""
print_status "Documentation: docs/ENHANCED_ADAPTIVE_SYNC_VIRTUAL_EMAIL_INTEGRATION.md"
echo ""

# Step 7: Optional: Show usage examples
print_status "Quick Usage Examples:"

echo ""
echo "1. Basic Enhanced Adaptive Sync:"
echo "   const { recordVirtualEmailDetection, virtualEmailActivity } = useEnhancedAdaptiveSync();"
echo ""
echo "2. Virtual Email Detection:"
echo "   recordVirtualEmailDetection();"
echo ""
echo "3. Check Virtual Email Activity:"
echo "   if (virtualEmailActivity?.recentActivity) {"
echo "     console.log('Virtual email activity detected!');"
echo "   }"
echo ""
echo "4. Manual Sync Trigger:"
echo "   const { triggerSync } = useEnhancedAdaptiveSync();"
echo "   await triggerSync('gmail');"
echo ""

print_success "Enhanced Adaptive Sync Framework is ready to use! 🚀" 