-- Migration: Add webhook activity tracking table
-- This migration adds a table to track webhook activity and performance

-- Add webhook_activity_tracking table
CREATE TABLE IF NOT EXISTS webhook_activity_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service TEXT NOT NULL CHECK (service = ANY (ARRAY['calendar', 'drive', 'gmail', 'attendee'])),
    webhook_type TEXT NOT NULL CHECK (webhook_type = ANY (ARRAY['push', 'polling', 'hybrid'])),
    last_webhook_received TIMESTAMP WITH TIME ZONE,
    webhook_failures INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE webhook_activity_tracking IS 'Tracks webhook activity and performance for monitoring';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_webhook_activity_tracking_user_id ON webhook_activity_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_activity_tracking_service ON webhook_activity_tracking(service);
CREATE INDEX IF NOT EXISTS idx_webhook_activity_tracking_webhook_type ON webhook_activity_tracking(webhook_type);
CREATE INDEX IF NOT EXISTS idx_webhook_activity_tracking_is_active ON webhook_activity_tracking(is_active);
CREATE INDEX IF NOT EXISTS idx_webhook_activity_tracking_last_webhook_received ON webhook_activity_tracking(last_webhook_received);

-- Enable RLS on webhook_activity_tracking
ALTER TABLE webhook_activity_tracking ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for webhook_activity_tracking
CREATE POLICY "Users can view own webhook activity tracking" ON webhook_activity_tracking FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own webhook activity tracking" ON webhook_activity_tracking FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own webhook activity tracking" ON webhook_activity_tracking FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own webhook activity tracking" ON webhook_activity_tracking FOR DELETE USING (auth.uid() = user_id);

-- Add trigger for updated_at column
CREATE TRIGGER update_webhook_activity_tracking_updated_at 
    BEFORE UPDATE ON webhook_activity_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
