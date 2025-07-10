-- Add calendar sync tracking and webhook management
-- This migration adds support for real-time calendar sync

-- Track calendar webhook subscriptions
CREATE TABLE IF NOT EXISTS calendar_webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  google_calendar_id TEXT NOT NULL DEFAULT 'primary',
  webhook_id TEXT UNIQUE, -- Google's webhook ID
  resource_id TEXT, -- Google's resource ID
  expiration_time TIMESTAMP WITH TIME ZONE,
  sync_token TEXT, -- For incremental syncs
  last_sync_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  
  UNIQUE(user_id, google_calendar_id)
);

-- Track sync operations for debugging and monitoring
CREATE TABLE IF NOT EXISTS calendar_sync_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sync_type TEXT NOT NULL CHECK (sync_type IN ('initial', 'incremental', 'webhook', 'manual')),
  status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
  events_processed INTEGER DEFAULT 0,
  meetings_created INTEGER DEFAULT 0,
  meetings_updated INTEGER DEFAULT 0,
  meetings_deleted INTEGER DEFAULT 0,
  error_message TEXT,
  sync_range_start TIMESTAMP WITH TIME ZONE,
  sync_range_end TIMESTAMP WITH TIME ZONE,
  duration_ms INTEGER, -- How long the sync took
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_user_id ON calendar_webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_active ON calendar_webhooks(is_active);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_logs_user_id ON calendar_sync_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_logs_created_at ON calendar_sync_logs(created_at);

-- Enable RLS
ALTER TABLE calendar_webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_sync_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for calendar_webhooks
CREATE POLICY "Users can view own webhooks"
  ON calendar_webhooks FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own webhooks"
  ON calendar_webhooks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own webhooks"
  ON calendar_webhooks FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own webhooks"
  ON calendar_webhooks FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for calendar_sync_logs
CREATE POLICY "Users can view own sync logs"
  ON calendar_sync_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sync logs"
  ON calendar_sync_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_calendar_webhooks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_calendar_webhooks_updated_at
BEFORE UPDATE ON calendar_webhooks
FOR EACH ROW
EXECUTE FUNCTION update_calendar_webhooks_updated_at(); 