# Hybrid Gmail Monitoring Implementation

This document describes the hybrid approach to Gmail monitoring that combines push notifications (primary) with smart polling (backup) for maximum reliability.

## Overview

The hybrid approach provides the best of both worlds:
- **Push Notifications**: Real-time updates when webhooks work properly
- **Smart Polling**: Backup mechanism that only runs when needed
- **Automatic Fallback**: Seamless transition between methods
- **Reliability**: Ensures no virtual emails are missed

## Architecture

### 1. Primary: Push Notifications
```
Gmail → Webhook → Supabase Edge Function → Process Virtual Emails
```

### 2. Backup: Smart Polling
```
Cron Job → Check Webhook Activity → Poll if Needed → Process Virtual Emails
```

### 3. Hybrid Logic
```
if (last_webhook_received < 6_hours_ago) {
  poll_gmail(); // Backup sync
} else {
  skip_polling(); // Push is working
}
```

## Database Schema

### Enhanced `gmail_watches` Table
```sql
CREATE TABLE gmail_watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  history_id TEXT NOT NULL,
  expiration TIMESTAMP WITH TIME ZONE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  watch_type TEXT DEFAULT 'polling' CHECK (watch_type IN ('push', 'polling', 'hybrid')),
  last_webhook_received TIMESTAMP WITH TIME ZONE,
  last_poll_at TIMESTAMP WITH TIME ZONE,
  webhook_failures INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_email)
);
```

**New Fields:**
- `watch_type`: Tracks whether push notifications, polling, or hybrid is being used
- `last_webhook_received`: Timestamp of last successful webhook
- `last_poll_at`: Timestamp of last polling operation
- `webhook_failures`: Count of consecutive webhook failures

## Edge Functions

### 1. `setup-gmail-watch`
**Purpose**: Sets up Gmail monitoring with hybrid approach
**Logic**:
1. Try to set up push notifications first
2. If push fails, fall back to polling
3. Store watch type and initial history ID

### 2. `gmail-notification-handler`
**Purpose**: Processes push notifications from Gmail
**Features**:
- Updates `last_webhook_received` timestamp
- Resets `webhook_failures` counter
- Processes virtual email detection
- Creates documents and sends to n8n

### 3. `gmail-polling-service`
**Purpose**: Smart polling with webhook activity awareness
**Logic**:
1. Check `last_webhook_received` timestamp
2. Skip polling if webhook was received within 6 hours
3. Only poll if webhook activity is stale
4. Update `last_poll_at` timestamp

### 4. `gmail-polling-cron`
**Purpose**: Scheduled polling for all users
**Features**:
- Runs every 6 hours (configurable)
- Only polls users with stale webhook activity
- Provides detailed statistics
- Handles rate limiting

## Smart Polling Logic

### When to Poll
```javascript
const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);

if (lastWebhookReceived && lastWebhookReceived > sixHoursAgo) {
  // Skip polling - webhook is working
  return { processed: 0, detections: 0, skipped: true };
} else {
  // Poll Gmail - webhook may be stale
  return pollGmail();
}
```

### Benefits
- **Efficiency**: Avoids unnecessary API calls
- **Cost Savings**: Reduces Gmail API quota usage
- **Performance**: Faster execution when webhooks are working
- **Reliability**: Ensures no gaps in monitoring

## Setup and Configuration

### 1. Environment Variables
```env
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/classification
```

### 2. Deploy Edge Functions
```bash
supabase functions deploy setup-gmail-watch
supabase functions deploy gmail-notification-handler
supabase functions deploy gmail-polling-service
supabase functions deploy gmail-polling-cron
```

### 3. Set up Cron Job
```bash
# Add to your cron job scheduler (every 6 hours)
0 */6 * * * curl -X POST https://your-project.supabase.co/functions/v1/gmail-polling-cron \
  -H "Authorization: Bearer your-service-role-key"
```

## Usage Flow

### 1. User Authentication
1. User completes Google OAuth
2. System attempts push notification setup
3. If push fails, falls back to polling
4. Watch type is recorded in database

### 2. Normal Operation (Push Working)
1. Gmail sends webhook to notification handler
2. Handler processes virtual emails immediately
3. Updates `last_webhook_received` timestamp
4. Cron job skips polling (webhook recent)

### 3. Webhook Failure Scenario
1. Webhook fails or expires
2. No updates to `last_webhook_received`
3. After 6 hours, cron job detects stale webhook
4. Polling service performs backup sync
5. Virtual emails are processed via polling

### 4. Recovery
1. Push notifications resume working
2. Webhook handler updates timestamp
3. Polling automatically stops (smart logic)
4. System returns to push-only mode

## Monitoring and Analytics

### 1. Watch Status Queries
```sql
-- Check watch types
SELECT watch_type, COUNT(*) 
FROM gmail_watches 
WHERE is_active = true 
GROUP BY watch_type;

-- Check webhook activity
SELECT 
  user_email,
  watch_type,
  last_webhook_received,
  last_poll_at,
  webhook_failures
FROM gmail_watches 
WHERE is_active = true;
```

### 2. Performance Metrics
```sql
-- Polling efficiency
SELECT 
  COUNT(*) as total_polls,
  COUNT(*) FILTER (WHERE skipped = true) as skipped_polls,
  ROUND(
    COUNT(*) FILTER (WHERE skipped = true) * 100.0 / COUNT(*), 
    2
  ) as efficiency_percent
FROM gmail_polling_logs 
WHERE created_at > NOW() - INTERVAL '7 days';
```

### 3. Reliability Metrics
```sql
-- Webhook vs polling detection rates
SELECT 
  'webhook' as source,
  COUNT(*) as detections
FROM virtual_email_detections 
WHERE detected_at > NOW() - INTERVAL '7 days'
  AND gmail_message_id IN (
    SELECT gmail_message_id 
    FROM gmail_webhook_logs 
    WHERE created_at > NOW() - INTERVAL '7 days'
  )

UNION ALL

SELECT 
  'polling' as source,
  COUNT(*) as detections
FROM virtual_email_detections 
WHERE detected_at > NOW() - INTERVAL '7 days'
  AND gmail_message_id NOT IN (
    SELECT gmail_message_id 
    FROM gmail_webhook_logs 
    WHERE created_at > NOW() - INTERVAL '7 days'
  );
```

## Troubleshooting

### Common Issues

1. **Push Notifications Not Working**:
   - Check domain verification in Google Cloud Console
   - Verify webhook URL is accessible
   - Check service account permissions

2. **Polling Always Running**:
   - Check `last_webhook_received` timestamps
   - Verify webhook handler is updating timestamps
   - Check for webhook failures

3. **High API Usage**:
   - Increase polling interval (6 hours → 12 hours)
   - Check for duplicate webhook processing
   - Monitor skipped vs actual polls

### Debug Commands

```bash
# Check webhook activity
supabase db query "
SELECT user_email, last_webhook_received, last_poll_at, webhook_failures 
FROM gmail_watches 
WHERE is_active = true;
"

# Check recent detections
supabase db query "
SELECT * FROM virtual_email_detections 
ORDER BY detected_at DESC 
LIMIT 10;
"

# Test polling manually
curl -X POST https://your-project.supabase.co/functions/v1/gmail-polling-service \
  -H "Authorization: Bearer your-service-role-key" \
  -H "Content-Type: application/json" \
  -d '{"userEmail": "user@example.com"}'
```

## Best Practices

### 1. Polling Frequency
- **Development**: Every 1 hour (faster feedback)
- **Production**: Every 6 hours (cost efficient)
- **High Volume**: Every 12 hours (API quota management)

### 2. Webhook Timeout
- **Default**: 6 hours (reasonable gap detection)
- **High Reliability**: 3 hours (faster recovery)
- **Cost Optimized**: 12 hours (fewer polls)

### 3. Error Handling
- Track webhook failures
- Implement exponential backoff
- Alert on consecutive failures

### 4. Monitoring
- Set up alerts for webhook failures
- Monitor polling efficiency
- Track API quota usage

## Future Enhancements

1. **Adaptive Polling**: Adjust frequency based on webhook reliability
2. **Webhook Health Checks**: Proactive webhook validation
3. **User Notifications**: Alert users when fallback polling is used
4. **Analytics Dashboard**: Real-time monitoring interface
5. **Auto-Recovery**: Automatic webhook renewal on failures

## Support

For issues or questions:
1. Check edge function logs in Supabase dashboard
2. Review webhook activity timestamps
3. Monitor polling efficiency metrics
4. Verify service account permissions
5. Check Google Cloud Console for domain verification 