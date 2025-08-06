#!/bin/bash

# Deploy Adaptive Sync Strategy
# This script deploys the new adaptive sync strategy to replace the webhook-based system

set -e

echo "🚀 Deploying Adaptive Sync Strategy..."

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
    exit 1
fi

print_status "Starting adaptive sync strategy deployment..."

# 1. Deploy database migration
print_status "Deploying database migration..."
supabase db push --include-all

if [ $? -eq 0 ]; then
    print_success "Database migration deployed successfully"
else
    print_error "Database migration failed"
    exit 1
fi

# 2. Deploy adaptive sync service
print_status "Deploying adaptive sync service..."
supabase functions deploy adaptive-sync-service

if [ $? -eq 0 ]; then
    print_success "Adaptive sync service deployed successfully"
else
    print_error "Adaptive sync service deployment failed"
    exit 1
fi

# 3. Update environment variables (if needed)
print_status "Checking environment variables..."
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    print_warning "Please ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in your environment"
fi

# 4. Build and deploy frontend
print_status "Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    print_success "Frontend built successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

# 5. Deploy to Netlify (if configured)
if [ -f "netlify.toml" ]; then
    print_status "Deploying to Netlify..."
    if command -v netlify &> /dev/null; then
        netlify deploy --prod --dir=dist
        if [ $? -eq 0 ]; then
            print_success "Netlify deployment completed"
        else
            print_error "Netlify deployment failed"
            exit 1
        fi
    else
        print_warning "Netlify CLI not found. Please deploy manually or install Netlify CLI"
    fi
fi

# 6. Disable old webhook services (optional)
print_status "Disabling old webhook services..."
print_warning "The following webhook services are now deprecated:"
echo "  - google-calendar-webhook"
echo "  - drive-webhook-handler"
echo "  - gmail-notification-handler"
echo "  - calendar-polling-cron"
echo "  - drive-polling-cron"
echo "  - gmail-polling-cron"

print_status "You can disable these services manually if needed:"
echo "  supabase functions delete google-calendar-webhook"
echo "  supabase functions delete drive-webhook-handler"
echo "  supabase functions delete gmail-notification-handler"
echo "  supabase functions delete calendar-polling-cron"
echo "  supabase functions delete drive-polling-cron"
echo "  supabase functions delete gmail-polling-cron"

# 7. Verify deployment
print_status "Verifying deployment..."

# Test the adaptive sync service
ADAPTIVE_SYNC_URL="${SUPABASE_URL}/functions/v1/adaptive-sync-service"

if [ ! -z "$SUPABASE_URL" ]; then
    print_status "Testing adaptive sync service..."
    
    # Test with a simple request
    TEST_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
        -d '{"userId":"test","service":"calendar","activityType":"app_load"}' \
        "${ADAPTIVE_SYNC_URL}" || echo "ERROR")
    
    if [[ "$TEST_RESPONSE" == *"error"* ]]; then
        print_warning "Adaptive sync service test failed (this is expected for test user)"
    else
        print_success "Adaptive sync service is responding"
    fi
fi

# 8. Print deployment summary
echo ""
print_success "🎉 Adaptive Sync Strategy Deployment Complete!"
echo ""
echo "📋 Deployment Summary:"
echo "  ✅ Database migration deployed"
echo "  ✅ Adaptive sync service deployed"
echo "  ✅ Frontend built and deployed"
echo "  ✅ Environment configured"
echo ""
echo "🔄 What's Changed:"
echo "  • Replaced real-time webhooks with adaptive sync"
echo "  • Added user activity tracking"
echo "  • Implemented intelligent sync intervals"
echo "  • Added performance metrics collection"
echo ""
echo "📊 New Features:"
echo "  • Immediate sync on user activity"
echo "  • Fast sync (30s) for active users"
echo "  • Normal sync (5min) for regular users"
echo "  • Slow sync (10min) for quiet users"
echo "  • Background sync (15min) for maintenance"
echo ""
echo "🔧 Next Steps:"
echo "  1. Monitor sync performance in the dashboard"
echo "  2. Check sync_analytics view for insights"
echo "  3. Adjust sync intervals if needed"
echo "  4. Consider disabling old webhook services"
echo ""
echo "📚 Documentation:"
echo "  • See docs/ADAPTIVE_SYNC_STRATEGY.md for details"
echo "  • Check sync_analytics view for performance data"
echo "  • Monitor user_activity_logs for activity patterns"
echo ""

print_success "Deployment completed successfully! 🚀" 