#!/bin/bash

# Test script to simulate Gmail webhook for document sharing
# This script tests the webhook endpoint using curl

echo "🚀 Testing Gmail webhook for document sharing simulation"
echo "=================================================="

# Configuration
BACKEND_URL="http://localhost:8000"
WEBHOOK_ENDPOINT="$BACKEND_URL/api/v1/webhooks/gmail/gmail"
TEST_ENDPOINT="$BACKEND_URL/api/v1/webhooks/gmail/gmail-test"

# Sample data
SAMPLE_MESSAGE_ID="test_message_$(date +%s)"
SAMPLE_DRIVE_FILE_ID="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

echo "Backend URL: $BACKEND_URL"
echo "Target email: ai+allan@besunny.ai"
echo "Sample Drive file: $SAMPLE_DRIVE_FILE_ID"
echo "Sample message ID: $SAMPLE_MESSAGE_ID"
echo ""

# Function to encode message ID as Gmail would
encode_message_id() {
    echo -n "$1" | base64 | tr -d '\n' | tr -d '='
}

# Test 1: Basic webhook endpoint test
echo "Test 1: Basic webhook endpoint test"
echo "-----------------------------------"
echo "Testing: $TEST_ENDPOINT"

response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$TEST_ENDPOINT")
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_CODE:/d')

echo "Response: $response_body"
echo "HTTP Code: $http_code"

if [ "$http_code" = "200" ]; then
    echo "✅ Basic webhook endpoint is working"
else
    echo "❌ Basic webhook endpoint failed"
    echo "Make sure the backend server is running on port 8000"
    exit 1
fi

echo ""

# Test 2: Gmail webhook with mock data
echo "Test 2: Gmail webhook with mock data"
echo "------------------------------------"
echo "Testing: $WEBHOOK_ENDPOINT"

# Create webhook payload
ENCODED_MESSAGE_ID=$(encode_message_id "$SAMPLE_MESSAGE_ID")
WEBHOOK_PAYLOAD=$(cat <<EOF
{
  "message": {
    "data": "$ENCODED_MESSAGE_ID",
    "messageId": "test_webhook_message_id",
    "publishTime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "subscription": "projects/besunny-ai/subscriptions/gmail-webhook"
}
EOF
)

echo "Webhook payload:"
echo "$WEBHOOK_PAYLOAD" | jq .
echo ""

echo "Sending webhook request..."

response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test_token" \
    -d "$WEBHOOK_PAYLOAD" \
    "$WEBHOOK_ENDPOINT")

http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_CODE:/d')

echo "Response: $response_body"
echo "HTTP Code: $http_code"

if [ "$http_code" = "200" ] || [ "$http_code" = "202" ]; then
    echo "✅ Gmail webhook endpoint accepted the request"
else
    echo "❌ Gmail webhook endpoint failed"
    echo "Check the backend logs for error details"
fi

echo ""

# Test 3: Health check
echo "Test 3: Backend health check"
echo "----------------------------"
echo "Testing: $BACKEND_URL/health"

response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$BACKEND_URL/health")
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
response_body=$(echo "$response" | sed '/HTTP_CODE:/d')

echo "Response: $response_body"
echo "HTTP Code: $http_code"

if [ "$http_code" = "200" ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

echo ""

# Summary
echo "=================================================="
echo "TEST SUMMARY"
echo "=================================================="
echo "Basic Webhook: $([ "$http_code" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "Gmail Webhook: $([ "$http_code" = "200" ] || [ "$http_code" = "202" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "Backend Health: $([ "$http_code" = "200" ] && echo "✅ PASS" || echo "❌ FAIL")"

echo ""
echo "Next steps:"
echo "1. Check the backend server logs for any processing messages"
echo "2. If the webhook was accepted, check the database for new entries"
echo "3. Look for any error messages in the server logs"
echo "=================================================="
