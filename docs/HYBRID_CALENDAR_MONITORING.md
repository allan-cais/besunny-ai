# Hybrid Calendar Monitoring Implementation

This document describes the hybrid approach to Google Calendar monitoring that combines push notifications (primary) with smart polling (backup) for maximum reliability.

## Overview

The hybrid calendar monitoring approach provides the best of both worlds:
- **Push Notifications**: Real-time updates when webhooks work properly
- **Smart Polling**: Backup mechanism that only runs when needed
- **Automatic Fallback**: Seamless transition between methods
- **Reliability**: Ensures no calendar events are missed

## Architecture

### 1. Primary: Push Notifications
```
Google Calendar → Webhook → Supabase Edge Function → Process Events
```

### 2. Backup: Smart Polling
```
Cron Job → Check Webhook Activity → Poll if Needed → Process Events
```

### 3. Hybrid Logic
```
if (last_webhook_received < 6_hours_ago) {
  poll_calendar(); // Backup sync
} else {
  skip_polling(); // Webhook is working
}
```

## Database Schema

### Enhanced `calendar_webhooks` Table
The existing table has been enhanced with additional fields:

```sql
-- Add fields for hybrid monitoring (if not already present)
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS last_webhook_received TIMESTAMP WITH TIME ZONE;
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS webhook_failures INTEGER DEFAULT 0;
```

**Key Fields:**
- `last_webhook_received`: Timestamp of last successful webhook
- `last_poll_at`: Timestamp of last polling operation
- `webhook_failures`: Count of consecutive webhook failures
- `sync_token`: For efficient incremental sync
- `is_active`: Whether the webhook is currently active

## Edge Functions

### 1. `google-calendar-webhook`
**Purpose**: Processes push notifications from Google Calendar
**Features**:
- Updates `last_webhook_received` timestamp
- Processes calendar events (create/update/delete)
- Maintains sync tokens for incremental sync
- Handles meeting URL extraction and bot scheduling

### 2. `calendar-polling-service`
**Purpose**: Smart polling with webhook activity awareness
**Logic**:
1. Check `last_webhook_received` timestamp
2. Skip polling if webhook was received within 6 hours
3. Only poll if webhook activity is stale
4. Update `last_poll_at` timestamp
5. Use sync tokens for efficient incremental sync

### 3. `calendar-polling-cron`
**Purpose**: Scheduled polling for all users
**Features**:
- Runs every 6 hours (configurable)
- Only polls users with stale webhook activity
- Provides detailed statistics
- Handles rate limiting

### 4. `renew-calendar-watches`
**Purpose**: Renews webhooks before expiration
**Features**:
- Runs every 12 hours
- Checks webhook expiration times
- Automatically renews expiring webhooks
- Maintains sync tokens during renewal

## Smart Polling Logic

### When to Poll
```javascript
const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);

if (lastWebhookReceived && lastWebhookReceived > sixHoursAgo) {
  // Skip polling - webhook is working
  return { processed: 0, created: 0, updated: 0, deleted: 0, skipped: true };
} else {
  // Poll calendar - webhook may be stale
  return pollCalendar();
}
```

### Benefits
- **Efficiency**: Avoids unnecessary API calls
- **Cost Savings**: Reduces Google Calendar API quota usage
- **Performance**: Faster execution when webhooks are working
- **Reliability**: Ensures no gaps in monitoring

## Setup and Configuration

### 1. Environment Variables
```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 2. Deploy Edge Functions
```bash
supabase functions deploy google-calendar-webhook
supabase functions deploy calendar-polling-service
supabase functions deploy calendar-polling-cron
supabase functions deploy renew-calendar-watches
```

### 3. Set up Cron Jobs
The GitHub Actions workflows are already configured:
- `calendar-polling.yml`: Every 6 hours
- `renew-calendar-watches.yml`: Every 12 hours

## Usage Flow

### 1. User Authentication
1. User completes Google OAuth
2. System sets up calendar webhook
3. Initial sync performed to get baseline state
4. Sync token stored for incremental updates

### 2. Normal Operation (Webhook Working)
1. Google Calendar sends webhook to notification handler
2. Handler processes events immediately
3. Updates `last_webhook_received` timestamp
4. Cron job skips polling (webhook recent)

### 3. Webhook Failure Scenario
1. Webhook fails or expires
2. No updates to `last_webhook_received`
3. After 6 hours, cron job detects stale webhook
4. Polling service performs backup sync
5. Events are processed via polling

### 4. Recovery
1. Webhook renewal restores push notifications
2. Webhook handler updates timestamp
3. Polling automatically stops (smart logic)
4. System returns to webhook-only mode

## Monitoring and Analytics

### 1. Webhook Status Queries
```sql
-- Check webhook activity
SELECT 
  user_id,
  last_webhook_received,
  last_poll_at,
  webhook_failures,
  is_active
FROM calendar_webhooks 
WHERE is_active = true;

-- Check polling efficiency
SELECT 
  COUNT(*) as total_polls,
  COUNT(*) FILTER (WHERE last_poll_at IS NOT NULL) as actual_polls,
  ROUND(
    COUNT(*) FILTER (WHERE last_poll_at IS NOT NULL) * 100.0 / COUNT(*), 
    2
  ) as efficiency_percent
FROM calendar_webhooks 
WHERE created_at > NOW() - INTERVAL '7 days';
```

### 2. Performance Metrics
```sql
-- Sync performance
SELECT 
  sync_type,
  COUNT(*) as sync_count,
  AVG(events_processed) as avg_events_processed,
  AVG(meetings_created) as avg_meetings_created,
  AVG(meetings_updated) as avg_meetings_updated
FROM calendar_sync_logs 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY sync_type;
```

### 3. Reliability Metrics
```sql
-- Webhook vs polling detection rates
SELECT 
  'webhook' as source,
  COUNT(*) as events_processed
FROM calendar_sync_logs 
WHERE sync_type = 'webhook' 
  AND created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
  'polling' as source,
  COUNT(*) as events_processed
FROM calendar_sync_logs 
WHERE sync_type IN ('incremental', 'full') 
  AND created_at > NOW() - INTERVAL '7 days';
```

## Error Handling

### 1. Webhook Failures
- Track consecutive failures in `webhook_failures` field
- Automatically increase polling frequency if webhooks consistently fail
- Alert administrators if failure rate exceeds threshold

### 2. API Rate Limiting
- Implement exponential backoff for API calls
- Respect Google Calendar API quotas
- Use sync tokens to minimize API usage

### 3. Token Expiration
- Automatic token refresh in polling service
- Graceful handling of expired tokens
- User notification when re-authentication is needed

## Best Practices

### 1. Performance
- Use sync tokens for incremental sync whenever possible
- Implement proper error handling and retry logic
- Monitor API quota usage

### 2. Reliability
- Set up monitoring for webhook health
- Implement fallback mechanisms
- Regular testing of both webhook and polling paths

### 3. Security
- Use service role keys only for automated tasks
- Implement proper authentication checks
- Monitor for suspicious activity

## Troubleshooting

### Common Issues

#### Webhooks Not Working
1. Check webhook URL accessibility
2. Verify Google Calendar API permissions
3. Check webhook expiration times
4. Review webhook setup logs

#### Polling Not Triggering
1. Verify cron job schedules
2. Check GitHub Actions logs
3. Ensure edge functions are deployed
4. Verify service role permissions

#### Sync Token Issues
1. Check for 410 errors (invalid sync token)
2. Verify sync token storage
3. Review incremental sync logs
4. Consider full sync if needed

### Debug Commands
```bash
# Check webhook status
curl -X GET "https://your-project.supabase.co/rest/v1/calendar_webhooks?select=*" \
  -H "Authorization: Bearer your-service-role-key"

# Test polling manually
curl -X POST "https://your-project.supabase.co/functions/v1/calendar-polling-service" \
  -H "Authorization: Bearer your-service-role-key" \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-id-here"}'

# Check sync logs
curl -X GET "https://your-project.supabase.co/rest/v1/calendar_sync_logs?select=*&order=created_at.desc&limit=10" \
  -H "Authorization: Bearer your-service-role-key"
```

## Future Enhancements

### 1. Advanced Monitoring
- Real-time webhook health dashboard
- Predictive failure detection
- Automated alerting system

### 2. Performance Optimization
- Batch processing for multiple users
- Intelligent polling frequency adjustment
- Caching layer for frequently accessed data

### 3. Enhanced Reliability
- Multi-region webhook endpoints
- Circuit breaker pattern implementation
- Advanced retry strategies 