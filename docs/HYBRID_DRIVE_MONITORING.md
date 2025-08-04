# Hybrid Drive Monitoring Implementation

This document describes the hybrid approach to Google Drive file monitoring that combines push notifications (primary) with smart polling (backup) for maximum reliability.

## Overview

The hybrid drive monitoring approach provides the best of both worlds:
- **Push Notifications**: Real-time updates when webhooks work properly
- **Smart Polling**: Backup mechanism that only runs when needed
- **Automatic Fallback**: Seamless transition between methods
- **Reliability**: Ensures no file changes are missed

## Architecture

### 1. Primary: Push Notifications
```
Google Drive → Webhook → Supabase Edge Function → Process File Changes
```

### 2. Backup: Smart Polling
```
Cron Job → Check Webhook Activity → Poll if Needed → Process File Changes
```

### 3. Hybrid Logic
```
if (last_webhook_received < 6_hours_ago) {
  poll_drive(); // Backup sync
} else {
  skip_polling(); // Webhook is working
}
```

## Database Schema

### Enhanced `drive_file_watches` Table
The existing table has been enhanced with additional fields:

```sql
-- Add fields for hybrid monitoring (if not already present)
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_webhook_received TIMESTAMP WITH TIME ZONE;
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS webhook_failures INTEGER DEFAULT 0;
```

**Key Fields:**
- `last_webhook_received`: Timestamp of last successful webhook
- `last_poll_at`: Timestamp of last polling operation
- `webhook_failures`: Count of consecutive webhook failures
- `expiration`: When the webhook expires
- `is_active`: Whether the watch is currently active

## Edge Functions

### 1. `drive-webhook-handler`
**Purpose**: Processes push notifications from Google Drive
**Features**:
- Updates `last_webhook_received` timestamp
- Processes file changes (update/delete)
- Maintains webhook activity tracking
- Handles file deletion and updates
- Sends notifications to n8n

### 2. `drive-polling-service`
**Purpose**: Smart polling with webhook activity awareness
**Logic**:
1. Check `last_webhook_received` timestamp
2. Skip polling if webhook was received within 6 hours
3. Only poll if webhook activity is stale
4. Update `last_poll_at` timestamp
5. Check file metadata for changes

### 3. `drive-polling-cron`
**Purpose**: Scheduled polling for all files
**Features**:
- Runs every 6 hours (configurable)
- Only polls files with stale webhook activity
- Provides detailed statistics
- Handles rate limiting

### 4. `subscribe-to-drive-file`
**Purpose**: Sets up file watches
**Features**:
- Creates Google Drive file watches
- Stores watch information in database
- Handles watch renewal

## Smart Polling Logic

### When to Poll
```javascript
const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);

if (lastWebhookReceived && lastWebhookReceived > sixHoursAgo) {
  // Skip polling - webhook is working
  return { processed: false, skipped: true };
} else {
  // Poll drive - webhook may be stale
  return pollDrive();
}
```

### File Change Detection
```javascript
// Check file metadata
const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,name,modifiedTime,trashed,size`);

// Compare with last known state
const lastSyncTime = document.last_synced_at;
const modifiedTime = new Date(fileMetadata.modifiedTime);

if (modifiedTime > lastSyncTime) {
  // File was modified
  return { changed: true, action: 'updated' };
}
```

### Benefits
- **Efficiency**: Avoids unnecessary API calls
- **Cost Savings**: Reduces Google Drive API quota usage
- **Performance**: Faster execution when webhooks are working
- **Reliability**: Ensures no gaps in monitoring

## Setup and Configuration

### 1. Environment Variables
```env
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_PRIVATE_KEY_ID=your-private-key-id
GOOGLE_CLIENT_ID=your-client-id
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/file-changes
```

### 2. Deploy Edge Functions
```bash
supabase functions deploy drive-webhook-handler
supabase functions deploy drive-polling-service
supabase functions deploy drive-polling-cron
supabase functions deploy subscribe-to-drive-file
```

### 3. Set up Cron Jobs
The GitHub Actions workflows are already configured:
- `drive-polling.yml`: Every 6 hours

## Usage Flow

### 1. File Watch Setup
1. User shares file with virtual email
2. System detects virtual email and creates document
3. System sets up Google Drive file watch
4. Watch information stored in database

### 2. Normal Operation (Webhook Working)
1. Google Drive sends webhook to notification handler
2. Handler processes file changes immediately
3. Updates `last_webhook_received` timestamp
4. Cron job skips polling (webhook recent)

### 3. Webhook Failure Scenario
1. Webhook fails or expires
2. No updates to `last_webhook_received`
3. After 6 hours, cron job detects stale webhook
4. Polling service performs backup sync
5. File changes are processed via polling

### 4. Recovery
1. Webhook renewal restores push notifications
2. Webhook handler updates timestamp
3. Polling automatically stops (smart logic)
4. System returns to webhook-only mode

## Monitoring and Analytics

### 1. Watch Status Queries
```sql
-- Check webhook activity
SELECT 
  file_id,
  document_id,
  last_webhook_received,
  last_poll_at,
  webhook_failures,
  is_active
FROM drive_file_watches 
WHERE is_active = true;

-- Check polling efficiency
SELECT 
  COUNT(*) as total_polls,
  COUNT(*) FILTER (WHERE last_poll_at IS NOT NULL) as actual_polls,
  ROUND(
    COUNT(*) FILTER (WHERE last_poll_at IS NOT NULL) * 100.0 / COUNT(*), 
    2
  ) as efficiency_percent
FROM drive_file_watches 
WHERE created_at > NOW() - INTERVAL '7 days';
```

### 2. Performance Metrics
```sql
-- Webhook vs polling detection rates
SELECT 
  'webhook' as source,
  COUNT(*) as events_processed
FROM drive_webhook_logs 
WHERE resource_state != 'polling' 
  AND webhook_received_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
  'polling' as source,
  COUNT(*) as events_processed
FROM drive_webhook_logs 
WHERE resource_state = 'polling' 
  AND webhook_received_at > NOW() - INTERVAL '7 days';
```

### 3. File Change Statistics
```sql
-- File change types
SELECT 
  resource_state,
  COUNT(*) as change_count,
  AVG(EXTRACT(EPOCH FROM (webhook_received_at - created_at))) as avg_processing_time_seconds
FROM drive_webhook_logs 
WHERE webhook_received_at > NOW() - INTERVAL '7 days'
GROUP BY resource_state;
```

## Error Handling

### 1. Webhook Failures
- Track consecutive failures in `webhook_failures` field
- Automatically increase polling frequency if webhooks consistently fail
- Alert administrators if failure rate exceeds threshold

### 2. API Rate Limiting
- Implement exponential backoff for API calls
- Respect Google Drive API quotas
- Use efficient metadata queries to minimize API usage

### 3. File Access Issues
- Handle 404 errors for deleted files
- Graceful handling of permission changes
- User notification when re-authentication is needed

## Best Practices

### 1. Performance
- Use metadata-only queries for change detection
- Implement proper error handling and retry logic
- Monitor API quota usage

### 2. Reliability
- Set up monitoring for webhook health
- Implement fallback mechanisms
- Regular testing of both webhook and polling paths

### 3. Security
- Use service account keys only for automated tasks
- Implement proper authentication checks
- Monitor for suspicious activity

## Troubleshooting

### Common Issues

#### Webhooks Not Working
1. Check webhook URL accessibility
2. Verify Google Drive API permissions
3. Check webhook expiration times
4. Review webhook setup logs

#### Polling Not Triggering
1. Verify cron job schedules
2. Check GitHub Actions logs
3. Ensure edge functions are deployed
4. Verify service role permissions

#### File Access Issues
1. Check service account permissions
2. Verify file sharing settings
3. Review API quota usage
4. Check for permission changes

### Debug Commands
```bash
# Check watch status
curl -X GET "https://your-project.supabase.co/rest/v1/drive_file_watches?select=*" \
  -H "Authorization: Bearer your-service-role-key"

# Test polling manually
curl -X POST "https://your-project.supabase.co/functions/v1/drive-polling-service" \
  -H "Authorization: Bearer your-service-role-key" \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file-id-here", "documentId": "document-id-here"}'

# Check webhook logs
curl -X GET "https://your-project.supabase.co/rest/v1/drive_webhook_logs?select=*&order=webhook_received_at.desc&limit=10" \
  -H "Authorization: Bearer your-service-role-key"
```

## Future Enhancements

### 1. Advanced Monitoring
- Real-time webhook health dashboard
- Predictive failure detection
- Automated alerting system

### 2. Performance Optimization
- Batch processing for multiple files
- Intelligent polling frequency adjustment
- Caching layer for frequently accessed metadata

### 3. Enhanced Reliability
- Multi-region webhook endpoints
- Circuit breaker pattern implementation
- Advanced retry strategies

### 4. File Type Support
- Enhanced support for different file types
- Custom processing for specific file formats
- Integration with document processing pipelines 