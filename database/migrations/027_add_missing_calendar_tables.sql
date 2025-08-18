-- Migration: Add missing Calendar service tables
-- This migration adds tables that are referenced in the calendar service but missing from the database

-- Add calendar_events table if it doesn't exist
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    calendar_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    location TEXT,
    meeting_url TEXT,
    is_meeting BOOLEAN DEFAULT false,
    attendees JSONB DEFAULT '[]',
    status TEXT DEFAULT 'confirmed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(event_id, user_id)
);

-- Add indexes for calendar_events
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_event_id ON calendar_events(event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_is_meeting ON calendar_events(is_meeting);

-- Enable RLS on calendar_events
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for calendar_events
CREATE POLICY "Users can view own calendar events" ON calendar_events FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own calendar events" ON calendar_events FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own calendar events" ON calendar_events FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own calendar events" ON calendar_events FOR DELETE USING (auth.uid() = user_id);

-- Add trigger for updated_at on calendar_events
CREATE TRIGGER update_calendar_events_updated_at 
    BEFORE UPDATE ON calendar_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add calendar_sync_states table if it doesn't exist
CREATE TABLE IF NOT EXISTS calendar_sync_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    calendar_id TEXT NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, calendar_id)
);

-- Add indexes for calendar_sync_states
CREATE INDEX IF NOT EXISTS idx_calendar_sync_states_user_id ON calendar_sync_states(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_states_calendar_id ON calendar_sync_states(calendar_id);

-- Enable RLS on calendar_sync_states
ALTER TABLE calendar_sync_states ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for calendar_sync_states
CREATE POLICY "Users can view own calendar sync states" ON calendar_sync_states FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own calendar sync states" ON calendar_sync_states FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own calendar sync states" ON calendar_sync_states FOR UPDATE USING (auth.uid() = user_id);

-- Add trigger for updated_at on calendar_sync_states
CREATE TRIGGER update_calendar_sync_states_updated_at 
    BEFORE UPDATE ON calendar_sync_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add calendar_polling_results table if it doesn't exist
CREATE TABLE IF NOT EXISTS calendar_polling_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    calendar_id TEXT NOT NULL,
    events_processed INTEGER DEFAULT 0,
    events_created INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    events_deleted INTEGER DEFAULT 0,
    meetings_detected INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for calendar_polling_results
CREATE INDEX IF NOT EXISTS idx_calendar_polling_results_user_id ON calendar_polling_results(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_polling_results_timestamp ON calendar_polling_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_calendar_polling_results_success ON calendar_polling_results(success);

-- Enable RLS on calendar_polling_results
ALTER TABLE calendar_polling_results ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for calendar_polling_results
CREATE POLICY "Users can view own calendar polling results" ON calendar_polling_results FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own calendar polling results" ON calendar_polling_results FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Add user_activity_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL,
    activity_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for user_activity_logs
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_timestamp ON user_activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);

-- Enable RLS on user_activity_logs
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for user_activity_logs
CREATE POLICY "Users can view own activity logs" ON user_activity_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own activity logs" ON user_activity_logs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Add comments
COMMENT ON TABLE calendar_events IS 'Stores calendar events synced from Google Calendar';
COMMENT ON TABLE calendar_sync_states IS 'Stores sync state and tokens for calendar synchronization';
COMMENT ON TABLE calendar_polling_results IS 'Stores results of calendar polling operations';
COMMENT ON TABLE user_activity_logs IS 'Stores user activity for smart polling optimization';
