# Automatic Watch Setup Implementation

This document describes the implementation of automatic watch setup for Gmail, Calendar, and Drive when users authenticate with Google and when virtual email addresses are used.

## Overview

The system now automatically sets up the following watches when users authenticate with Google:

1. **Gmail Watch**: Monitors for emails using virtual email addresses (`ai+{username}@besunny.ai`)
2. **Calendar Watch**: Monitors for calendar events with virtual email attendees
3. **Drive Watch**: Automatically sets up file watches when files are shared with virtual email addresses

## Automatic Setup Flow

### 1. Google OAuth Authentication

When a user completes Google OAuth authentication:

1. **OAuth Callback** (`src/pages/oauth-login-callback.tsx`)
   - Calls `calendarService.initializeCalendarSync()` to set up Calendar watch
   - Calls `gmailWatchService.setupGmailWatch()` to set up Gmail watch
   - Shows progress messages to user during setup

2. **Calendar Sync Setup** (`src/lib/calendar.ts`)
   - Creates Google Calendar webhook subscription
   - Stores webhook information in `calendar_webhooks` table
   - Enables real-time calendar event monitoring

3. **Gmail Watch Setup** (`src/lib/gmail-watch-service.ts`)
   - Uses service account to create Gmail push notification subscription
   - Stores watch information in `gmail_watches` table
   - Enables real-time email monitoring

### 2. Virtual Email Detection

When virtual email addresses are used:

#### Email CC/TO Detection
- **Gmail Notification Handler** (`supabase/functions/gmail-notification-handler/index.ts`)
  - Processes Gmail push notifications
  - Detects `ai+{username}@besunny.ai` in email headers
  - Creates documents and sends to n8n for classification
  - Logs detections in `virtual_email_detections` table

#### Calendar Attendee Detection
- **Enhanced Calendar Sync** (`supabase/functions/google-calendar/index.ts`)
  - Scans calendar event attendees for virtual email addresses
  - Automatically schedules Attendee bots for meetings with virtual email attendees
  - Updates meeting records with auto-scheduling information

#### Drive File Sharing Detection
- **Process Inbound Emails** (`supabase/functions/process-inbound-emails/index.ts`)
  - Detects Google Drive URLs in emails sent to virtual addresses
  - Automatically sets up Drive watches for shared files
  - Extracts file IDs from Drive URLs and creates watch subscriptions

- **Drive Webhook Handler** (`supabase/functions/drive-webhook-handler/index.ts`)
  - Processes Drive file change notifications
  - Automatically sets up watches for virtual email documents
  - Handles file updates and deletions

## Database Schema

### Enhanced Tables

#### `gmail_watches`
```sql
CREATE TABLE gmail_watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  history_id TEXT NOT NULL,
  expiration TIMESTAMP WITH TIME ZONE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_email)
);
```

#### `virtual_email_detections`
```sql
CREATE TABLE virtual_email_detections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  virtual_email TEXT NOT NULL,
  username TEXT NOT NULL,
  email_type TEXT NOT NULL CHECK (email_type IN ('to', 'cc')),
  gmail_message_id TEXT NOT NULL,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(gmail_message_id, virtual_email)
);
```

#### `calendar_webhooks` (existing)
- Enhanced to support virtual email attendee detection
- Stores sync tokens for incremental syncs

#### `drive_file_watches` (existing)
- Enhanced to support automatic setup for virtual email documents
- Tracks file watches for shared files

## Edge Functions

### 1. `setup-gmail-watch`
**Purpose**: Sets up Gmail push notifications using service account
**Automatic Setup**: Called during OAuth authentication
**Features**:
- JWT token generation for service account
- Gmail watch subscription creation
- Database storage of watch information

### 2. `gmail-notification-handler`
**Purpose**: Processes Gmail push notifications
**Automatic Detection**: Detects virtual email usage in emails
**Features**:
- Email header parsing
- Virtual email pattern matching
- Document creation and n8n integration

### 3. `google-calendar` (enhanced)
**Purpose**: Calendar sync with virtual email attendee detection
**Automatic Bot Scheduling**: Schedules Attendee bots for virtual email attendees
**Features**:
- Virtual email attendee scanning
- Automatic bot deployment
- Meeting record updates

### 4. `process-inbound-emails` (enhanced)
**Purpose**: Processes emails sent to virtual addresses
**Automatic Drive Watch**: Sets up Drive watches for shared files
**Features**:
- Drive URL detection in emails
- Automatic file watch setup
- Document creation and classification

### 5. `drive-webhook-handler` (enhanced)
**Purpose**: Processes Drive file change notifications
**Automatic Watch Setup**: Sets up watches for virtual email documents
**Features**:
- Virtual email document detection
- Automatic watch setup
- File change processing

### 6. `subscribe-to-drive-file` (enhanced)
**Purpose**: Creates Drive file watches
**Auto-Setup Support**: Supports automatic setup for virtual email documents
**Features**:
- Service account authentication
- Watch subscription creation
- Database storage

## Frontend Integration

### 1. OAuth Callback (`src/pages/oauth-login-callback.tsx`)
**Enhanced Features**:
- Automatic Calendar sync setup
- Automatic Gmail watch setup
- Progress messaging during setup
- Error handling and fallback

### 2. Gmail Watch Service (`src/lib/gmail-watch-service.ts`)
**Features**:
- Gmail watch setup and management
- Watch status checking
- Virtual email detection retrieval
- Statistics and analytics

### 3. Virtual Email Settings (`src/components/VirtualEmailSettings.tsx`)
**Enhanced Features**:
- Gmail watch status indicator
- Setup and test buttons
- Recent detections display
- Watch management controls

## Service Account Configuration

### Required Environment Variables
```env
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/classification
N8N_DRIVESYNC_WEBHOOK_URL=https://your-n8n-instance.com/webhook/drivesync
```

### Google Cloud Console Setup
1. **Service Account Creation**:
   - Create service account with appropriate permissions
   - Download JSON key file
   - Store key securely in environment variables

2. **API Enablement**:
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Pub/Sub API

3. **Domain Verification**:
   - Add your domain to authorized domains
   - Configure OAuth consent screen

## Usage Flow

### 1. User Authentication
1. User clicks "Connect Google Account"
2. Completes OAuth flow
3. System automatically sets up:
   - Calendar watch for event monitoring
   - Gmail watch for virtual email detection
4. User sees success message and is redirected to dashboard

### 2. Virtual Email Usage
1. Someone sends email with `ai+username@besunny.ai` in CC/TO
2. Gmail sends notification to webhook
3. System detects virtual email and creates document
4. If email contains Drive URLs, automatic Drive watches are set up
5. Document is sent to n8n for classification

### 3. Calendar Event with Virtual Email Attendee
1. Calendar event is created with `ai+username@besunny.ai` as attendee
2. Calendar sync processes the event
3. System detects virtual email attendee
4. Automatically schedules Attendee bot for the meeting
5. Meeting appears in dashboard with bot scheduled

### 4. Drive File Sharing
1. File is shared with `ai+username@besunny.ai`
2. Email notification is sent to virtual address
3. System processes email and detects Drive URLs
4. Automatic Drive watches are set up for shared files
5. File changes are monitored in real-time

## Monitoring and Maintenance

### 1. Watch Status Monitoring
```sql
-- Check Gmail watch status
SELECT * FROM gmail_watches WHERE is_active = true;

-- Check Calendar webhook status
SELECT * FROM calendar_webhooks WHERE is_active = true;

-- Check Drive watch status
SELECT * FROM drive_file_watches WHERE is_active = true;
```

### 2. Virtual Email Detection Analytics
```sql
-- Recent detections
SELECT * FROM virtual_email_detections 
ORDER BY detected_at DESC 
LIMIT 10;

-- Detection statistics
SELECT 
  COUNT(*) as total_detections,
  COUNT(*) FILTER (WHERE detected_at > NOW() - INTERVAL '7 days') as recent_detections,
  COUNT(*) FILTER (WHERE email_type = 'to') as to_detections,
  COUNT(*) FILTER (WHERE email_type = 'cc') as cc_detections
FROM virtual_email_detections;
```

### 3. Auto-Scheduled Meetings
```sql
-- Check auto-scheduled meetings
SELECT * FROM meetings 
WHERE auto_scheduled_via_email = true 
ORDER BY created_at DESC;
```

## Error Handling

### 1. OAuth Setup Failures
- Calendar sync failures are logged but don't block authentication
- Gmail watch failures are logged but don't block authentication
- Users can manually set up services later

### 2. Watch Expiration
- Gmail watches expire after 7 days
- Calendar webhooks expire after 7 days
- Drive watches expire after 7 days
- Automatic renewal functions handle expiration

### 3. Service Account Issues
- JWT token generation errors are logged
- Token exchange failures are handled gracefully
- Fallback to manual setup when automatic setup fails

## Security Considerations

### 1. Service Account Security
- Private keys stored securely in environment variables
- Minimal required permissions for service account
- Regular key rotation recommended

### 2. Data Privacy
- All detections are user-specific
- RLS policies ensure data isolation
- Virtual email addresses are user-specific

### 3. API Security
- Edge functions use service role for database access
- JWT tokens for Google API authentication
- Secure webhook endpoints

## Troubleshooting

### Common Issues

1. **Gmail Watch Not Working**:
   - Check service account permissions
   - Verify Pub/Sub topic and subscription
   - Check edge function logs

2. **Calendar Sync Issues**:
   - Verify OAuth scopes include calendar access
   - Check webhook URL configuration
   - Review calendar sync logs

3. **Drive Watch Issues**:
   - Verify service account has Drive API access
   - Check file sharing permissions
   - Review Drive webhook logs

### Debug Commands

```bash
# Check watch status
supabase db query "SELECT * FROM gmail_watches WHERE user_email = 'user@example.com';"

# Check recent detections
supabase db query "SELECT * FROM virtual_email_detections ORDER BY detected_at DESC LIMIT 5;"

# Check auto-scheduled meetings
supabase db query "SELECT * FROM meetings WHERE auto_scheduled_via_email = true;"
```

## Future Enhancements

1. **Batch Processing**: Handle multiple emails in single notification
2. **Advanced Analytics**: Detailed usage statistics and trends
3. **Email Content Analysis**: Extract meeting information from emails
4. **Integration with Other Services**: Slack, Teams, etc.
5. **Smart Renewal**: Proactive watch renewal before expiration
6. **User Notifications**: Notify users when virtual emails are detected

## Support

For issues or questions:
1. Check edge function logs in Supabase dashboard
2. Review database tables for data consistency
3. Test watch setup manually
4. Verify service account permissions and configuration
5. Check OAuth scopes and consent screen settings 