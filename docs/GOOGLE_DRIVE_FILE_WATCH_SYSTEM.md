# Google Drive File Watch System

This document describes the implementation of the Google Drive File Watch System for real-time file change detection and synchronization.

## Overview

The Google Drive File Watch System enables real-time monitoring of Google Drive files that are shared with a user's virtual email address. When files are updated or deleted in Google Drive, the system automatically detects these changes and triggers appropriate actions including:

- Updating document status in the database
- Triggering n8n workflows for file re-synchronization
- Deleting associated Pinecone vector chunks for deleted files
- Providing real-time status indicators in the UI

## Architecture

### Components

1. **Database Schema** (`supabase-migrations/009_add_google_drive_file_watch.sql`)
   - `drive_file_watches` table for tracking active watches
   - `drive_webhook_logs` table for audit trail
   - Enhanced `documents` table with watch status fields

2. **Edge Functions**
   - `subscribe-to-drive-file`: Creates Google Drive file watches
   - `drive-webhook-handler`: Processes Google Drive webhook notifications

3. **Frontend Components**
   - `FileWatchStatus`: Status indicator component
   - `GoogleDriveWatchManager`: Management interface
   - Enhanced `DataFeed`: Shows watch status in activity feed

4. **Utility Functions**
   - `drive-watch.ts`: Helper functions and hooks
   - URL parsing and file ID extraction

## Database Schema

### New Tables

#### `drive_file_watches`
```sql
CREATE TABLE drive_file_watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,  -- same as document_id
  resource_id TEXT NOT NULL, -- from Google response
  expiration TIMESTAMP WITH TIME ZONE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

#### `drive_webhook_logs`
```sql
CREATE TABLE drive_webhook_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  resource_state TEXT NOT NULL, -- 'update', 'delete', etc.
  webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  n8n_webhook_sent BOOLEAN DEFAULT FALSE,
  n8n_webhook_response TEXT,
  n8n_webhook_sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Enhanced `documents` Table
```sql
ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'active' CHECK (status IN ('active', 'updated', 'deleted', 'error'));
ALTER TABLE documents ADD COLUMN file_id TEXT; -- Google Drive file ID
ALTER TABLE documents ADD COLUMN last_synced_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE documents ADD COLUMN watch_active BOOLEAN DEFAULT FALSE;
```

## Edge Functions

### 1. subscribe-to-drive-file

**Purpose**: Creates Google Drive file watches using the Google Drive API.

**Endpoint**: `POST /functions/v1/subscribe-to-drive-file`

**Request Body**:
```json
{
  "user_id": "string",
  "document_id": "string", 
  "file_id": "string"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully subscribed to Google Drive file changes",
  "watch_id": "uuid",
  "resource_id": "string",
  "expiration": "timestamp"
}
```

**Behavior**:
- Validates input parameters
- Checks for existing watches to prevent duplicates
- Calls Google Drive `files.watch` API
- Stores watch information in database
- Updates document status

### 2. drive-webhook-handler

**Purpose**: Processes Google Drive webhook notifications.

**Endpoint**: `POST /functions/v1/drive-webhook-handler`

**Expected Headers**:
- `X-Goog-Resource-ID`: Resource identifier
- `X-Goog-Resource-State`: State change type ('update', 'delete', etc.)
- `X-Goog-Channel-ID`: Channel ID (document_id)

**Behavior**:
- Extracts webhook headers
- Looks up document by channel ID
- Handles file deletions (marks as deleted, removes chunks)
- Handles file updates (triggers n8n webhook)
- Logs all webhook events

## Frontend Integration

### FileWatchStatus Component

Displays the current watch status with appropriate badges:

- **No Watch**: No Google Drive link
- **Watch Active**: Monitoring file for changes
- **Recently Updated**: File was recently synced
- **Deleted from Drive**: File was deleted
- **Watch Error**: Error in watch setup

### GoogleDriveWatchManager Component

Provides a user interface for:

- Adding Google Drive URLs to documents
- Subscribing to file changes
- Unsubscribing from file changes
- Viewing current watch status

### DataFeed Integration

The main activity feed now shows:

- File watch status badges on document cards
- Last sync timestamps
- Visual indicators for different file states

## Environment Variables

Add these to your Supabase project:

```env
# Google Service Account (for Drive API access)
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...
GOOGLE_SERVICE_ACCOUNT_KEY_ID=your-key-id

# N8N Webhook for file synchronization
N8N_DRIVESYNC_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-drivesync

# Drive webhook URL (optional, defaults to function URL)
DRIVE_WEBHOOK_URL=https://your-project.supabase.co/functions/v1/drive-webhook-handler
```

## Usage Flow

### 1. User Shares File with Virtual Email

1. User shares a Google Drive file with their virtual email address
2. Email is processed by `process-inbound-emails` function
3. Document is created in the database
4. User can optionally subscribe to file changes

### 2. Subscribe to File Changes

1. User navigates to document settings
2. Pastes Google Drive URL in `GoogleDriveWatchManager`
3. System extracts file ID and calls `subscribe-to-drive-file`
4. Google Drive watch is created and stored in database
5. Document status is updated to show active watch

### 3. File Changes Detected

1. User modifies file in Google Drive
2. Google sends webhook to `drive-webhook-handler`
3. System updates document status to 'updated'
4. n8n webhook is triggered for file re-sync
5. Pinecone vectors are updated with new content

### 4. File Deletion

1. User deletes file from Google Drive
2. Google sends webhook with 'deleted' state
3. System marks document as 'deleted'
4. Associated Pinecone chunks are removed
5. Watch is deactivated

## Security Features

- **Row Level Security (RLS)**: All tables have appropriate RLS policies
- **Service Account Authentication**: Uses Google service account for API access
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Comprehensive error handling and logging
- **Audit Trail**: All webhook events are logged for debugging

## Monitoring and Maintenance

### Scheduled Cleanup

Set up a scheduled function to clean up expired watches:

```sql
SELECT cron.schedule('cleanup-expired-drive-watches', '0 2 * * *', 'SELECT deactivate_expired_drive_watches();');
```

### Webhook Logs

Monitor the `drive_webhook_logs` table for:

- Failed webhook deliveries
- n8n webhook failures
- Error patterns

### Watch Expiration

Google Drive watches expire after 7 days. The system:

- Automatically deactivates expired watches
- Updates document status to reflect inactive watches
- Provides UI indicators for expired watches

## Troubleshooting

### Common Issues

1. **Watch Creation Fails**
   - Check Google service account credentials
   - Verify file permissions in Google Drive
   - Check webhook URL accessibility

2. **Webhook Not Received**
   - Verify webhook URL is publicly accessible
   - Check Google Drive API quotas
   - Review webhook logs for errors

3. **n8n Sync Fails**
   - Verify `N8N_DRIVESYNC_WEBHOOK_URL` is correct
   - Check n8n workflow configuration
   - Review webhook response logs

### Debug Queries

```sql
-- Check active watches
SELECT * FROM drive_file_watches WHERE is_active = true;

-- Check recent webhook events
SELECT * FROM drive_webhook_logs ORDER BY created_at DESC LIMIT 10;

-- Find documents with watch issues
SELECT * FROM documents WHERE status = 'error' OR (file_id IS NOT NULL AND watch_active = false);
```

## Future Enhancements

1. **Batch Operations**: Support for subscribing to multiple files at once
2. **Watch Renewal**: Automatic renewal of expiring watches
3. **Advanced Filtering**: Filter webhook events by file type or change type
4. **Notification System**: User notifications for file changes
5. **Analytics Dashboard**: Monitor watch statistics and performance

## API Reference

### Database Functions

- `get_active_drive_file_watch(file_id)`: Get active watch by file ID
- `deactivate_expired_drive_watches()`: Clean up expired watches
- `get_document_by_channel_id(channel_id)`: Get document by channel ID

### Frontend Hooks

- `useDriveWatch()`: Hook for managing file watches
- `extractGoogleDriveFileId(url)`: Extract file ID from Drive URL
- `hasActiveDriveWatch(document)`: Check if document has active watch

## Support

For issues or questions about the Google Drive File Watch System:

1. Check the webhook logs in the database
2. Review the edge function logs in Supabase dashboard
3. Verify environment variables are correctly set
4. Test with a simple Google Drive file first 