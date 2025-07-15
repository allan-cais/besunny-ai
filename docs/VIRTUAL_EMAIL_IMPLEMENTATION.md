# Virtual Email Addresses Implementation

This document describes the implementation of virtual inbound email addresses using Gmail plus-addressing for the Kirit Askuno application.

## Overview

The virtual email addresses feature allows each user to have their own unique email address in the format `inbound+{username}@sunny.ai`. When emails are sent to this address, they are automatically processed, stored as documents, and sent to the n8n classification webhook.

## Architecture

### Database Schema

#### New Tables and Columns

1. **users table extensions:**
   - `username` (TEXT, UNIQUE) - User's chosen username
   - `username_set_at` (TIMESTAMP) - When username was set

2. **email_processing_logs table:**
   - Tracks all email processing attempts
   - Links emails to users and documents
   - Records n8n webhook status

#### Database Functions

- `extract_username_from_email(email_address)` - Extracts username from plus-addressing
- `get_user_by_username(username)` - Finds user by username
- `set_user_username(user_uuid, new_username)` - Sets username with validation

### Edge Functions

#### `set-username`
- Handles username creation after user signup/login
- Validates username format and uniqueness
- Returns virtual email address

#### `process-inbound-emails`
- Processes Gmail messages from webhook
- Extracts usernames from plus-addressing
- Creates documents and sends to n8n

### Frontend Components

#### `UsernameSetupDialog`
- Modal dialog for username setup
- Real-time validation
- Feature explanation and instructions

#### `VirtualEmailSettings`
- Settings page component
- Displays virtual email address
- Usage instructions and copy functionality

#### `UsernameSetupManager`
- Manages when to show username setup dialog
- Checks user status on login

## User Flow

### 1. User Signup/Login
1. User creates account or logs in
2. `UsernameSetupManager` checks if username is set
3. If no username, shows `UsernameSetupDialog`
4. User chooses username and gets virtual email address

### 2. Email Processing
1. Email sent to `inbound+{username}@sunny.ai`
2. Email lands in `inbound@sunny.ai` mailbox
3. Gmail webhook triggers `process-inbound-emails`
4. Function extracts username from "To" header
5. Finds user by username
6. Creates document record
7. Sends payload to n8n webhook

### 3. Settings Management
1. User navigates to Settings page
2. Views virtual email address
3. Copies address to clipboard
4. Sees usage instructions

## Implementation Details

### Username Validation

Usernames must:
- Be 3-30 characters long
- Contain only letters, numbers, hyphens, and underscores
- Not start with a number
- Be unique across all users

### Email Processing Logic

1. **Extract username:** Parse `inbound+{username}@sunny.ai` format
2. **Find user:** Lookup user by username in database
3. **Create document:** Store email metadata in documents table
4. **Send to n8n:** Forward to classification webhook

### Security Features

- Row Level Security (RLS) on all tables
- JWT authentication for Edge Functions
- Username uniqueness validation
- Input sanitization and validation

## Environment Variables

Add these to your Supabase project:

```env
# N8N Classification Webhook
N8N_CLASSIFICATION_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-classification
```

## Database Migration

Run the following SQL in your Supabase dashboard:

```sql
-- Add virtual email address support
-- This migration adds username management and email processing capabilities

-- Add username column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS username_set_at TIMESTAMP WITH TIME ZONE;

-- Add index for username lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create table to track email processing
CREATE TABLE IF NOT EXISTS email_processing_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  gmail_message_id TEXT NOT NULL,
  inbound_address TEXT NOT NULL,
  extracted_username TEXT,
  subject TEXT,
  sender TEXT,
  received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  processed_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed', 'user_not_found')),
  error_message TEXT,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  n8n_webhook_sent BOOLEAN DEFAULT FALSE,
  n8n_webhook_response TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for email processing
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_user_id ON email_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_gmail_message_id ON email_processing_logs(gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_status ON email_processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_received_at ON email_processing_logs(received_at);

-- Enable RLS on email_processing_logs
ALTER TABLE email_processing_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for email_processing_logs
CREATE POLICY "Users can view own email processing logs" ON email_processing_logs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can insert email processing logs" ON email_processing_logs
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service can update email processing logs" ON email_processing_logs
  FOR UPDATE USING (true);

-- Create function to extract username from email address
CREATE OR REPLACE FUNCTION extract_username_from_email(email_address TEXT)
RETURNS TEXT AS $$
DECLARE
  username_part TEXT;
BEGIN
  -- Extract the part before @
  username_part := split_part(email_address, '@', 1);
  
  -- Check if it contains a plus sign (plus-addressing)
  IF username_part LIKE '%+%' THEN
    -- Extract the part after the plus sign
    username_part := split_part(username_part, '+', 2);
  END IF;
  
  RETURN username_part;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function to get user by username
CREATE OR REPLACE FUNCTION get_user_by_username(username TEXT)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  name TEXT,
  username TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.id,
    u.email,
    u.name,
    u.username
  FROM users u
  WHERE u.username = get_user_by_username.username;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to set username for user
CREATE OR REPLACE FUNCTION set_user_username(user_uuid UUID, new_username TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  username_exists BOOLEAN;
BEGIN
  -- Check if username is already taken
  SELECT EXISTS(SELECT 1 FROM users WHERE username = new_username AND id != user_uuid) INTO username_exists;
  
  IF username_exists THEN
    RETURN FALSE;
  END IF;
  
  -- Update the user's username
  UPDATE users 
  SET username = new_username, username_set_at = NOW()
  WHERE id = user_uuid;
  
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION extract_username_from_email(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_by_username(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION set_user_username(UUID, TEXT) TO authenticated;

-- Add trigger to update username_set_at when username is set
CREATE OR REPLACE FUNCTION update_username_set_at()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.username IS NOT NULL AND (OLD.username IS NULL OR OLD.username != NEW.username) THEN
    NEW.username_set_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_username_set_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_username_set_at();
```

## Deployment

### 1. Deploy Edge Functions

```bash
# Deploy set-username function
supabase functions deploy set-username

# Deploy process-inbound-emails function
supabase functions deploy process-inbound-emails
```

### 2. Set Environment Variables

In your Supabase dashboard, go to Settings > Edge Functions and add:

```
N8N_CLASSIFICATION_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-classification
```

### 3. Run Database Migration

Execute the SQL migration in your Supabase SQL editor.

## Testing

### Test Username Setup

1. Create a new user account
2. Verify username setup dialog appears
3. Set a username and verify virtual email address is generated
4. Check that username is stored in database

### Test Email Processing

1. Send an email to `inbound+{username}@sunny.ai`
2. Check email_processing_logs table for processing record
3. Verify document is created in documents table
4. Check n8n webhook receives payload

### Test Settings Page

1. Navigate to Settings > Virtual Email
2. Verify virtual email address is displayed
3. Test copy to clipboard functionality
4. Verify usage instructions are shown

## API Endpoints

### Set Username
```
POST /functions/v1/set-username
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "username": "user123"
}
```

### Process Inbound Emails
```
POST /functions/v1/process-inbound-emails
Content-Type: application/json

{
  "messages": [
    {
      "id": "gmail_message_id",
      "payload": {
        "headers": [
          {"name": "to", "value": "inbound+user123@sunny.ai"},
          {"name": "subject", "value": "Test Email"},
          {"name": "from", "value": "sender@example.com"}
        ]
      }
    }
  ]
}
```

## n8n Webhook Payload

The system sends the following payload to the n8n classification webhook:

```json
{
  "user_id": "uuid",
  "document_id": "uuid",
  "gmail_message_id": "gmail_message_id",
  "subject": "Email Subject",
  "sender": "sender@example.com",
  "username": "user123",
  "snippet": "Email snippet",
  "received_at": "2024-01-15T10:30:00Z",
  "source": "gmail",
  "type": "email"
}
```

## Monitoring

### Key Metrics to Track

1. **Username setup completion rate**
2. **Email processing success rate**
3. **n8n webhook delivery success**
4. **User engagement with virtual email addresses**

### Logs to Monitor

1. `email_processing_logs` table
2. Edge Function logs in Supabase dashboard
3. n8n webhook delivery logs

## Troubleshooting

### Common Issues

1. **Username already taken**
   - Check users table for existing username
   - Verify uniqueness constraint

2. **Email processing fails**
   - Check email_processing_logs for error messages
   - Verify Gmail webhook configuration
   - Check Edge Function logs

3. **n8n webhook not receiving data**
   - Verify N8N_CLASSIFICATION_WEBHOOK_URL environment variable
   - Check webhook URL is accessible
   - Monitor webhook response in logs

### Debug Commands

```sql
-- Check username status
SELECT username, username_set_at FROM users WHERE id = 'user_uuid';

-- Check email processing logs
SELECT * FROM email_processing_logs WHERE user_id = 'user_uuid' ORDER BY created_at DESC;

-- Check for failed processing
SELECT * FROM email_processing_logs WHERE status = 'failed' ORDER BY created_at DESC;
```

## Future Enhancements

1. **Username change functionality** (currently disabled)
2. **Email processing analytics dashboard**
3. **Bulk email processing**
4. **Email content extraction and storage**
5. **Advanced filtering and search**
6. **Email threading support** 