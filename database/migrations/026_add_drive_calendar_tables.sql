-- Migration: Add Drive and Calendar service tables
-- This migration adds any missing tables needed for the Drive and Calendar services

-- Add calendar_webhook_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS calendar_webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    resource_state TEXT NOT NULL,
    resource_uri TEXT,
    state TEXT,
    expiration TEXT,
    webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    n8n_webhook_sent BOOLEAN DEFAULT false,
    n8n_webhook_sent_at TIMESTAMP WITH TIME ZONE,
    n8n_webhook_response TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for calendar_webhook_logs
CREATE INDEX IF NOT EXISTS idx_calendar_webhook_logs_webhook_id ON calendar_webhook_logs(webhook_id);
CREATE INDEX IF NOT EXISTS idx_calendar_webhook_logs_event_id ON calendar_webhook_logs(event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_webhook_logs_created_at ON calendar_webhook_logs(created_at);

-- Enable RLS on calendar_webhook_logs
ALTER TABLE calendar_webhook_logs ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for calendar_webhook_logs
CREATE POLICY "Users can view own calendar webhook logs" ON calendar_webhook_logs FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM calendar_webhooks cw 
    WHERE cw.webhook_id = calendar_webhook_logs.webhook_id 
    AND cw.user_id = auth.uid()
  )
);

CREATE POLICY "Users can insert own calendar webhook logs" ON calendar_webhook_logs FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM calendar_webhooks cw 
    WHERE cw.webhook_id = calendar_webhook_logs.webhook_id 
    AND cw.user_id = auth.uid()
  )
);

-- Add trigger for updated_at on calendar_webhook_logs
CREATE TRIGGER update_calendar_webhook_logs_updated_at 
    BEFORE UPDATE ON calendar_webhook_logs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE calendar_webhook_logs IS 'Log of calendar webhook processing for N8N integration';
