# Sunny AI Database Schema

This document contains the complete SQL schema for the Sunny AI database. Use this script to recreate the database on a new host or for migration purposes.

## Database Setup

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types if needed
CREATE TYPE sync_status AS ENUM ('started', 'completed', 'failed');
CREATE TYPE sync_type AS ENUM ('initial', 'incremental', 'webhook', 'manual');
CREATE TYPE document_status AS ENUM ('active', 'updated', 'deleted', 'error');
CREATE TYPE document_type AS ENUM ('email', 'document', 'spreadsheet', 'presentation', 'image', 'folder', 'meeting_transcript');
CREATE TYPE classification_source AS ENUM ('ai', 'auto', 'system', 'manual', 'user');
CREATE TYPE bot_status AS ENUM ('pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed', 'failed');
CREATE TYPE event_status AS ENUM ('accepted', 'declined', 'tentative', 'needsAction');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired');
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE maintenance_type AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE gmail_watch_type AS ENUM ('push', 'polling', 'hybrid');
CREATE TYPE service_type AS ENUM ('calendar', 'drive', 'gmail', 'attendee');
CREATE TYPE sync_speed AS ENUM ('immediate', 'fast', 'normal', 'slow', 'background');
CREATE TYPE change_frequency AS ENUM ('high', 'medium', 'low');
CREATE TYPE activity_type AS ENUM ('app_load', 'calendar_view', 'meeting_create', 'general');
CREATE TYPE email_type AS ENUM ('to', 'cc');
```

## Table Definitions

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    username TEXT UNIQUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE users IS 'Auth: Stores user login data within a secure schema.';
```

### Projects Table
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);
```

### Knowledge Spaces Table
```sql
CREATE TABLE knowledge_spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);
```

### Tags Table
```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    color TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);
```

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    summary TEXT,
    author TEXT,
    file_id TEXT,
    file_size TEXT,
    source TEXT,
    source_id TEXT,
    type TEXT DEFAULT 'document' CHECK (type = ANY (ARRAY['email', 'document', 'spreadsheet', 'presentation', 'image', 'folder', 'meeting_transcript'])),
    status TEXT DEFAULT 'active' CHECK (status = ANY (ARRAY['active', 'updated', 'deleted', 'error'])),
    classification_source TEXT DEFAULT 'manual' CHECK (classification_source = ANY (ARRAY['ai', 'auto', 'system', 'manual', 'user'])),
    watch_active BOOLEAN DEFAULT false,
    transcript_duration_seconds INTEGER,
    transcript_metadata JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES users(id),
    received_at TIMESTAMP WITHOUT TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    knowledge_space_id UUID REFERENCES knowledge_spaces(id) ON DELETE CASCADE,
    meeting_id UUID
);
```

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    text TEXT,
    embedding_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);
```

### Document Tags Table
```sql
CREATE TABLE document_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    applied_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
```

### Summaries Table
```sql
CREATE TABLE summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);
```

### Receipts Table
```sql
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
```

### Bots Table
```sql
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    avatar_url TEXT,
    provider TEXT NOT NULL,
    provider_bot_id TEXT,
    settings JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);
```

### Meetings Table
```sql
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    meeting_url TEXT,
    google_calendar_event_id TEXT,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    attendee_bot_id UUID REFERENCES bots(id),
    bot_name TEXT DEFAULT 'Sunny AI Notetaker',
    bot_status TEXT DEFAULT 'pending' CHECK (bot_status = ANY (ARRAY['pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed', 'failed'])),
    event_status TEXT DEFAULT 'needsAction' CHECK (event_status = ANY (ARRAY['accepted', 'declined', 'tentative', 'needsAction'])),
    bot_configuration JSONB,
    bot_deployment_method TEXT DEFAULT 'manual',
    bot_chat_message TEXT DEFAULT 'Hi, I''m here to transcribe this meeting!',
    auto_bot_notification_sent BOOLEAN DEFAULT false,
    auto_scheduled_via_email BOOLEAN DEFAULT false,
    virtual_email_attendee TEXT,
    transcript TEXT,
    transcript_url TEXT,
    transcript_audio_url TEXT,
    transcript_recording_url TEXT,
    transcript_summary TEXT,
    transcript_duration_seconds INTEGER,
    transcript_language TEXT DEFAULT 'en-US',
    transcript_metadata JSONB,
    transcript_participants JSONB,
    transcript_speakers JSONB,
    transcript_segments JSONB,
    transcript_retrieved_at TIMESTAMP WITH TIME ZONE,
    last_polled_at TIMESTAMP WITH TIME ZONE,
    next_poll_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, google_calendar_event_id)
);

-- Add comment
COMMENT ON COLUMN meetings.bot_configuration IS 'Configuration for the bot attending this meeting';
COMMENT ON COLUMN meetings.transcript_audio_url IS 'URL to the audio recording if available';
COMMENT ON COLUMN meetings.transcript_recording_url IS 'URL to the video recording if available';
COMMENT ON COLUMN meetings.transcript_participants IS 'Array of participant information from transcript';
COMMENT ON COLUMN meetings.transcript_speakers IS 'Array of unique speakers identified in transcript';
COMMENT ON COLUMN meetings.transcript_segments IS 'Detailed transcript segments with timestamps and speaker info';
COMMENT ON COLUMN meetings.transcript_language IS 'Language of the transcript';
```

### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    ended_at TIMESTAMP WITHOUT TIME ZONE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    CHECK ((ended_at IS NULL) OR (ended_at >= started_at)),
    CHECK ((name IS NULL) OR (length(TRIM(BOTH FROM name)) > 0))
);
```

### Chat Messages Table
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message TEXT,
    role TEXT CHECK (role = ANY (ARRAY['user', 'assistant', 'system'])),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    used_chunks TEXT[],
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    CHECK ((message IS NULL) OR (length(TRIM(BOTH FROM message)) > 0)),
    CHECK ((session_id IS NOT NULL)),
    CHECK ((used_chunks IS NULL) OR (array_length(used_chunks, 1) > 0))
);
```

### Google Credentials Table
```sql
CREATE TABLE google_credentials (
    user_id UUID NOT NULL PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    token_type TEXT,
    scope TEXT,
    google_user_id TEXT,
    google_email TEXT,
    google_name TEXT,
    google_picture TEXT,
    login_provider BOOLEAN DEFAULT false,
    login_created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
```

### Calendar Webhooks Table
```sql
CREATE TABLE calendar_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    google_calendar_id TEXT NOT NULL DEFAULT 'primary',
    webhook_id TEXT UNIQUE,
    resource_id TEXT,
    sync_token TEXT,
    expiration_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    last_poll_at TIMESTAMP WITH TIME ZONE,
    last_webhook_received TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, google_calendar_id)
);
```

### Calendar Sync Logs Table
```sql
CREATE TABLE calendar_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sync_type TEXT NOT NULL CHECK (sync_type = ANY (ARRAY['initial', 'incremental', 'webhook', 'manual'])),
    status TEXT NOT NULL CHECK (status = ANY (ARRAY['started', 'completed', 'failed'])),
    sync_range_start TIMESTAMP WITH TIME ZONE,
    sync_range_end TIMESTAMP WITH TIME ZONE,
    events_processed INTEGER DEFAULT 0,
    meetings_created INTEGER DEFAULT 0,
    meetings_updated INTEGER DEFAULT 0,
    meetings_deleted INTEGER DEFAULT 0,
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Gmail Watches Table
```sql
CREATE TABLE gmail_watches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT NOT NULL UNIQUE,
    history_id TEXT NOT NULL,
    expiration TIMESTAMP WITH TIME ZONE NOT NULL,
    watch_type TEXT DEFAULT 'polling' CHECK (watch_type = ANY (ARRAY['push', 'polling', 'hybrid'])),
    is_active BOOLEAN DEFAULT true,
    last_poll_at TIMESTAMP WITH TIME ZONE,
    last_webhook_received TIMESTAMP WITH TIME ZONE,
    webhook_failures INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE gmail_watches IS 'Tracks Gmail watch subscriptions for monitoring virtual email usage';
```

### Drive File Watches Table
```sql
CREATE TABLE drive_file_watches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    expiration TIMESTAMP WITH TIME ZONE NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    last_poll_at TIMESTAMP WITH TIME ZONE,
    last_webhook_received TIMESTAMP WITH TIME ZONE,
    webhook_failures INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Drive Webhook Logs Table
```sql
CREATE TABLE drive_webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    resource_state TEXT NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    n8n_webhook_sent BOOLEAN DEFAULT false,
    n8n_webhook_sent_at TIMESTAMP WITH TIME ZONE,
    n8n_webhook_response TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Email Processing Logs Table
```sql
CREATE TABLE email_processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gmail_message_id TEXT NOT NULL,
    inbound_address TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status = ANY (ARRAY['pending', 'processed', 'failed', 'user_not_found'])),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    sender TEXT,
    subject TEXT,
    extracted_username TEXT,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    processed_at TIMESTAMP WITH TIME ZONE,
    n8n_webhook_sent BOOLEAN DEFAULT false,
    n8n_webhook_response TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Virtual Email Detections Table
```sql
CREATE TABLE virtual_email_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    virtual_email TEXT NOT NULL,
    username TEXT NOT NULL,
    email_type TEXT NOT NULL CHECK (email_type = ANY (ARRAY['to', 'cc'])),
    gmail_message_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(gmail_message_id, virtual_email)
);

-- Add comment
COMMENT ON TABLE virtual_email_detections IS 'Records when virtual email addresses are detected in Gmail messages';
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier TEXT NOT NULL CHECK (tier = ANY (ARRAY['free', 'pro', 'enterprise'])),
    sync_days_limit INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status = ANY (ARRAY['active', 'cancelled', 'expired'])),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### User API Keys Table
```sql
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service TEXT NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, service)
);
```

### Project Metadata Table
```sql
CREATE TABLE project_metadata (
    project_id UUID NOT NULL PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Agent Logs Table
```sql
CREATE TABLE agent_logs (
    id UUID NOT NULL PRIMARY KEY,
    agent_name TEXT,
    input_type TEXT,
    input_id TEXT,
    output JSONB,
    confidence NUMERIC,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
```

### Maintenance Logs Table
```sql
CREATE TABLE maintenance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    maintenance_type TEXT NOT NULL CHECK (maintenance_type = ANY (ARRAY['daily', 'weekly', 'monthly'])),
    status TEXT NOT NULL CHECK (status = ANY (ARRAY['started', 'completed', 'failed'])),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE maintenance_logs IS 'Log of maintenance activities and their status';
```

### Sync Tracking Table
```sql
CREATE TABLE sync_tracking (
    user_id UUID NOT NULL PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    last_sync_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    sync_frequency TEXT DEFAULT 'normal',
    change_frequency TEXT CHECK (change_frequency = ANY (ARRAY['high', 'medium', 'low'])),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### User Sync States Table
```sql
CREATE TABLE user_sync_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    sync_frequency TEXT DEFAULT 'normal',
    change_frequency TEXT CHECK (change_frequency = ANY (ARRAY['high', 'medium', 'low'])),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id)
);

-- Add comment
COMMENT ON TABLE user_sync_states IS 'Stores user sync state and preferences for adaptive sync';
```

### Sync Performance Metrics Table
```sql
CREATE TABLE sync_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL CHECK (service_type = ANY (ARRAY['calendar', 'drive', 'gmail', 'attendee'])),
    sync_type TEXT NOT NULL CHECK (sync_type = ANY (ARRAY['immediate', 'fast', 'normal', 'slow', 'background'])),
    duration_ms INTEGER,
    items_processed INTEGER,
    success_rate NUMERIC,
    error_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE sync_performance_metrics IS 'Tracks sync performance and metrics for optimization';
```

### User Activity Logs Table
```sql
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL CHECK (activity_type = ANY (ARRAY['app_load', 'calendar_view', 'meeting_create', 'general'])),
    activity_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE user_activity_logs IS 'Tracks user activity for adaptive sync strategy';
```

### Drive Watch Status View
```sql
CREATE VIEW drive_watch_status AS
SELECT 
    dfw.id,
    dfw.file_id,
    dfw.channel_id,
    dfw.resource_id,
    dfw.expiration,
    dfw.is_active,
    dfw.last_poll_at,
    dfw.last_webhook_received,
    dfw.webhook_failures,
    dfw.document_id,
    dfw.project_id,
    d.title as document_title,
    d.status as document_status
FROM drive_file_watches dfw
LEFT JOIN documents d ON dfw.document_id = d.id;
```

### Meetings for Polling View
```sql
CREATE VIEW meetings_for_polling AS
SELECT 
    m.*,
    m.next_poll_time,
    m.bot_status,
    m.attendee_bot_id
FROM meetings m
WHERE m.bot_status IN ('pending', 'bot_scheduled', 'bot_joined')
  AND (m.next_poll_time IS NULL OR m.next_poll_time <= now());
```

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_meeting_id ON documents(meeting_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);

CREATE INDEX idx_meetings_user_id ON meetings(user_id);
CREATE INDEX idx_meetings_project_id ON meetings(project_id);
CREATE INDEX idx_meetings_start_time ON meetings(start_time);
CREATE INDEX idx_meetings_bot_status ON meetings(bot_status);
CREATE INDEX idx_meetings_google_calendar_event_id ON meetings(google_calendar_event_id);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_project_id ON chat_sessions(project_id);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_project_id ON document_chunks(project_id);
CREATE INDEX idx_document_chunks_embedding_id ON document_chunks(embedding_id);

CREATE INDEX idx_calendar_webhooks_user_id ON calendar_webhooks(user_id);
CREATE INDEX idx_calendar_webhooks_expiration_time ON calendar_webhooks(expiration_time);

CREATE INDEX idx_gmail_watches_user_email ON gmail_watches(user_email);
CREATE INDEX idx_gmail_watches_expiration ON gmail_watches(expiration);

CREATE INDEX idx_drive_file_watches_file_id ON drive_file_watches(file_id);
CREATE INDEX idx_drive_file_watches_expiration ON drive_file_watches(expiration);

CREATE INDEX idx_sync_performance_metrics_user_id ON sync_performance_metrics(user_id);
CREATE INDEX idx_sync_performance_metrics_created_at ON sync_performance_metrics(created_at);

CREATE INDEX idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_user_activity_logs_created_at ON user_activity_logs(created_at);
```

## Row Level Security (RLS)

```sql
-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE gmail_watches ENABLE ROW LEVEL SECURITY;
ALTER TABLE drive_file_watches ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sync_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE virtual_email_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE drive_webhook_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_tracking ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (customize based on your security requirements)
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own projects" ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own projects" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects" ON projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects" ON projects FOR DELETE USING (auth.uid() = user_id);

-- Add similar policies for other tables based on user_id or project_id relationships
```

## Functions and Triggers

```sql
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON bots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_calendar_webhooks_updated_at BEFORE UPDATE ON calendar_webhooks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gmail_watches_updated_at BEFORE UPDATE ON gmail_watches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_drive_file_watches_updated_at BEFORE UPDATE ON drive_file_watches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_api_keys_updated_at BEFORE UPDATE ON user_api_keys FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sync_states_updated_at BEFORE UPDATE ON user_sync_states FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sync_tracking_updated_at BEFORE UPDATE ON sync_tracking FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Usage Instructions

1. **Backup your existing database** before running this script
2. **Review and customize** the RLS policies based on your security requirements
3. **Run the script** in your target database
4. **Verify** that all tables, constraints, and indexes were created successfully
5. **Test** your application with the new schema

## Notes

- This schema includes all tables from the original Sunny AI database
- Row Level Security (RLS) is enabled but policies need to be customized
- The script includes performance indexes for common query patterns
- All foreign key relationships are preserved
- Check constraints maintain data integrity
- Views provide convenient access to common data combinations

## Migration Considerations

- **Data Types**: Ensure your target database supports all data types (UUID, JSONB, etc.)
- **Extensions**: The script requires `uuid-ossp` and `pgcrypto` extensions
- **Permissions**: Ensure the executing user has sufficient privileges
- **Performance**: Large tables may take time to create indexes
- **Testing**: Always test the migration in a non-production environment first
