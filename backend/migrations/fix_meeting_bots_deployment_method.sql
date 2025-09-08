-- Fix meeting_bots table - ensure deployment_method column exists
-- This migration ensures the deployment_method column exists in meeting_bots table

-- Add deployment_method column if it doesn't exist
ALTER TABLE meeting_bots 
ADD COLUMN IF NOT EXISTS deployment_method TEXT DEFAULT 'manual';

-- Add metadata column if it doesn't exist
ALTER TABLE meeting_bots 
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add constraint if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'meeting_bots_deployment_method_check') THEN
        ALTER TABLE meeting_bots 
        ADD CONSTRAINT meeting_bots_deployment_method_check 
        CHECK (deployment_method = ANY (ARRAY['manual', 'automatic']));
    END IF;
END $$;

-- Update existing records to set default value
UPDATE meeting_bots SET deployment_method = 'manual' WHERE deployment_method IS NULL;

-- Add index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_meeting_bots_deployment_method ON meeting_bots(deployment_method);

-- Create attendee_webhook_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS attendee_webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bot_id TEXT,
    trigger TEXT NOT NULL,
    webhook_data JSONB NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for attendee_webhook_logs
CREATE INDEX IF NOT EXISTS idx_attendee_webhook_logs_user_id ON attendee_webhook_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_attendee_webhook_logs_webhook_id ON attendee_webhook_logs(webhook_id);
CREATE INDEX IF NOT EXISTS idx_attendee_webhook_logs_bot_id ON attendee_webhook_logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_attendee_webhook_logs_processed ON attendee_webhook_logs(processed);

-- Enable RLS on attendee_webhook_logs
ALTER TABLE attendee_webhook_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for attendee_webhook_logs (allow service role to insert/update)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'attendee_webhook_logs' AND policyname = 'Service role can manage attendee_webhook_logs') THEN
        CREATE POLICY "Service role can manage attendee_webhook_logs" ON attendee_webhook_logs
            FOR ALL USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Create RLS policy for meeting_bots (allow service role to insert/update)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'meeting_bots' AND policyname = 'Service role can manage meeting_bots') THEN
        CREATE POLICY "Service role can manage meeting_bots" ON meeting_bots
            FOR ALL USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Create RLS policy for users to read their own webhook logs
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'attendee_webhook_logs' AND policyname = 'Users can read their own webhook logs') THEN
        CREATE POLICY "Users can read their own webhook logs" ON attendee_webhook_logs
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policy for users to read their own meeting bots
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'meeting_bots' AND policyname = 'Users can read their own meeting bots') THEN
        CREATE POLICY "Users can read their own meeting bots" ON meeting_bots
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

-- Add comments
COMMENT ON COLUMN meeting_bots.deployment_method IS 'How the bot was deployed: manual (UI) or automatic (virtual email)';
COMMENT ON COLUMN meeting_bots.metadata IS 'Additional metadata about the bot deployment';
COMMENT ON TABLE attendee_webhook_logs IS 'Logs for Attendee.dev webhook events';
