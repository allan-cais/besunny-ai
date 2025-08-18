-- Migration: Add enhanced user sync states table
-- This migration adds an enhanced table to track user sync state and preferences

-- Add enhanced user_sync_states table
CREATE TABLE IF NOT EXISTS user_sync_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL CHECK (service_type = ANY (ARRAY['calendar', 'drive', 'gmail', 'attendee', 'user', 'auth'])),
    last_sync_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    sync_frequency TEXT DEFAULT 'normal' CHECK (sync_frequency = ANY (ARRAY['immediate', 'fast', 'normal', 'slow', 'background'])),
    change_frequency TEXT CHECK (change_frequency = ANY (ARRAY['high', 'medium', 'low'])),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, service_type)
);

-- Add comment
COMMENT ON TABLE user_sync_states IS 'Stores user sync state and preferences for adaptive sync';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sync_states_user_id ON user_sync_states(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_service_type ON user_sync_states(service_type);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_last_sync_at ON user_sync_states(last_sync_at);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_sync_frequency ON user_sync_states(sync_frequency);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_change_frequency ON user_sync_states(change_frequency);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_is_active ON user_sync_states(is_active);

-- Enable RLS on user_sync_states
ALTER TABLE user_sync_states ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for user_sync_states
CREATE POLICY "Users can view own sync states" ON user_sync_states FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sync states" ON user_sync_states FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own sync states" ON user_sync_states FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own sync states" ON user_sync_states FOR DELETE USING (auth.uid() = user_id);

-- Add trigger for updated_at column
CREATE TRIGGER update_user_sync_states_updated_at 
    BEFORE UPDATE ON user_sync_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
