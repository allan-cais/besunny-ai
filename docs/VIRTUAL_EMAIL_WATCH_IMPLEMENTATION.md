# Virtual Email Watch Implementation

This document describes the implementation of the virtual email watch system that monitors Gmail for when users are CC'd on emails with their `+{username}` alias, and automatically triggers Attendee bot scheduling for calendar events with virtual email attendees.

## Overview

The system consists of several components that work together to:

1. **Monitor Gmail** for emails that use virtual email addresses (`ai+{username}@besunny.ai`)
2. **Detect Calendar Events** with virtual email attendees and auto-schedule bots
3. **Process Drive File Sharing** with virtual email addresses
4. **Track and Log** all virtual email usage for analytics

## Architecture

### 1. Gmail Watch System

#### Components:
- **`setup-gmail-watch`** Edge Function: Sets up Gmail push notifications
- **`gmail-notification-handler`** Edge Function: Processes Gmail notifications
- **`gmail_watches`** Database Table: Tracks watch subscriptions
- **`virtual_email_detections`** Database Table: Logs detected virtual emails

#### Flow:
1. User sets up Gmail watch via frontend
2. Service account creates Gmail push notification subscription
3. Google sends notifications to our webhook when emails arrive
4. Handler processes notifications and detects virtual emails
5. Creates documents and sends to n8n for classification

### 2. Calendar Event Processing

#### Enhanced Calendar Sync:
- **Virtual Email Detection**: Scans calendar event attendees for `ai+{username}@besunny.ai`
- **Auto-Bot Scheduling**: Automatically schedules Attendee bots for meetings with virtual email attendees
- **Immediate Deployment**: Bots are scheduled immediately when virtual emails are detected

#### Flow:
1. Calendar sync processes events
2. Detects virtual email attendees
3. Finds corresponding user by username
4. Checks for Attendee API credentials
5. Schedules bot automatically
6. Updates meeting record with bot information

### 3. Drive File Sharing

#### Enhanced Drive Watch:
- **Virtual Email Detection**: Monitors file sharing with virtual email addresses
- **Automatic Capture**: Creates documents for shared files
- **Classification**: Sends to n8n for project classification

## Database Schema

### New Tables

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

### Enhanced Tables

#### `meetings` (existing)
- `auto_scheduled_via_email`: Boolean flag for auto-scheduled meetings
- `virtual_email_attendee`: Stores the virtual email that triggered scheduling
- `bot_deployment_method`: Tracks deployment method ('manual', 'automatic', 'scheduled')

## Edge Functions

### 1. `setup-gmail-watch`

**Purpose**: Sets up Gmail push notifications for a user

**Features**:
- Uses service account credentials for authentication
- Creates Gmail watch subscription
- Stores watch information in database
- Handles JWT token generation and exchange

**Environment Variables**:
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

### 2. `gmail-notification-handler`

**Purpose**: Processes Gmail push notifications

**Features**:
- Decodes notification payload
- Fetches Gmail message details
- Extracts email addresses from headers
- Detects virtual email usage
- Creates documents and sends to n8n
- Logs detections in database

**Environment Variables**:
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`
- `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY`
- `N8N_WEBHOOK_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Frontend Integration

### 1. Gmail Watch Service (`src/lib/gmail-watch-service.ts`)

**Features**:
- Setup Gmail watch for users
- Get watch status and expiration
- Retrieve virtual email detections
- Test detection functionality
- Get usage statistics

### 2. Enhanced Virtual Email Settings

**New Features**:
- Gmail watch setup button
- Watch status indicator
- Test detection functionality
- Recent detections display
- Statistics and analytics

## Service Account Setup

### 1. Google Cloud Console Configuration

1. **Create Service Account**:
   - Go to Google Cloud Console > IAM & Admin > Service Accounts
   - Create new service account with appropriate permissions

2. **Enable APIs**:
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Pub/Sub API

3. **Create and Download Key**:
   - Generate JSON key for service account
   - Store securely in environment variables

### 2. Environment Variables

Add these to your Supabase Edge Function environment:

```env
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/virtual-email
```

## Deployment Steps

### 1. Database Migration

```bash
# Run the new migration
supabase db push
```

### 2. Deploy Edge Functions

```bash
# Deploy the new functions
supabase functions deploy setup-gmail-watch
supabase functions deploy gmail-notification-handler
```

### 3. Set Environment Variables

```bash
# Set environment variables for each function
supabase secrets set GOOGLE_SERVICE_ACCOUNT_EMAIL=your-email
supabase secrets set GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="your-key"
supabase secrets set N8N_WEBHOOK_URL=your-webhook-url
```

### 4. Gmail Polling Setup (Optional)

For Gmail monitoring, the system uses polling instead of push notifications to avoid Pub/Sub complexity:

1. **Set up Cron Job** (optional):
   ```bash
   # Add to your cron job scheduler to run every 5 minutes
   curl -X POST https://your-project.supabase.co/functions/v1/gmail-polling-cron \
     -H "Authorization: Bearer your-service-role-key"
   ```

2. **Manual Polling** (alternative):
   - Users can manually trigger Gmail polling from the UI
   - System polls Gmail history API for new messages
   - No additional Google Cloud setup required

## Usage Flow

### 1. User Setup

1. User visits Virtual Email Settings
2. Clicks "Setup Gmail Watch"
3. System creates Gmail push notification subscription
4. User sees "Gmail Watch Active" badge

### 2. Email Detection

1. Someone sends email with `ai+username@besunny.ai` in CC
2. Gmail sends push notification to our webhook
3. Handler processes notification and detects virtual email
4. Creates document and sends to n8n for classification
5. User sees detection in recent detections list

### 3. Calendar Auto-Scheduling

1. Calendar event is created with `ai+username@besunny.ai` as attendee
2. Calendar sync processes the event
3. System detects virtual email attendee
4. Automatically schedules Attendee bot for the meeting
5. Meeting appears in user's dashboard with bot scheduled

## Monitoring and Analytics

### 1. Database Queries

**Recent Detections**:
```sql
SELECT * FROM virtual_email_detections 
WHERE user_id = 'user-uuid' 
ORDER BY detected_at DESC 
LIMIT 10;
```

**Detection Statistics**:
```sql
SELECT 
  COUNT(*) as total_detections,
  COUNT(*) FILTER (WHERE detected_at > NOW() - INTERVAL '7 days') as recent_detections,
  COUNT(*) FILTER (WHERE email_type = 'to') as to_detections,
  COUNT(*) FILTER (WHERE email_type = 'cc') as cc_detections
FROM virtual_email_detections;
```

### 2. Logs and Debugging

- Edge function logs in Supabase dashboard
- Gmail watch status in `gmail_watches` table
- Virtual email detections in `virtual_email_detections` table
- Meeting auto-scheduling in `meetings` table

## Security Considerations

### 1. Service Account Security
- Store private key securely in environment variables
- Use minimal required permissions
- Rotate keys regularly

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

2. **Virtual Emails Not Detected**:
   - Verify email format (`ai+username@besunny.ai`)
   - Check Gmail watch status
   - Review notification handler logs

3. **Auto-Scheduling Not Working**:
   - Verify Attendee API credentials
   - Check calendar sync logs
   - Ensure virtual email attendee format is correct

### Debug Commands

```bash
# Check Gmail watch status
supabase db query "SELECT * FROM gmail_watches WHERE user_email = 'user@example.com';"

# Check recent detections
supabase db query "SELECT * FROM virtual_email_detections ORDER BY detected_at DESC LIMIT 5;"

# Check auto-scheduled meetings
supabase db query "SELECT * FROM meetings WHERE auto_scheduled_via_email = true;"
```

## Future Enhancements

1. **Drive File Sharing Detection**: Extend to monitor Google Drive sharing
2. **Batch Processing**: Handle multiple emails in single notification
3. **Advanced Analytics**: Detailed usage statistics and trends
4. **Email Content Analysis**: Extract meeting information from emails
5. **Integration with Other Services**: Slack, Teams, etc.

## Support

For issues or questions:
1. Check edge function logs in Supabase dashboard
2. Review database tables for data consistency
3. Test Gmail watch setup manually
4. Verify service account permissions and configuration 