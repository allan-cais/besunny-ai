-- Migration: Add sync performance metrics table
-- This migration adds a table to track the performance of cron jobs and sync operations

-- Add sync_performance_metrics table
CREATE TABLE IF NOT EXISTS sync_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL CHECK (service_type = ANY (ARRAY['calendar', 'drive', 'gmail', 'attendee', 'user', 'auth'])),
    sync_type TEXT NOT NULL CHECK (sync_type = ANY (ARRAY['immediate', 'fast', 'normal', 'slow', 'background'])),
    duration_ms INTEGER,
    items_processed INTEGER,
    success_rate NUMERIC,
    error_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comment
COMMENT ON TABLE sync_performance_metrics IS 'Tracks sync performance and metrics for optimization';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_user_id ON sync_performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_service_type ON sync_performance_metrics(service_type);
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_created_at ON sync_performance_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_sync_type ON sync_performance_metrics(sync_type);

-- Enable RLS on sync_performance_metrics
ALTER TABLE sync_performance_metrics ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for sync_performance_metrics
CREATE POLICY "Users can view own sync performance metrics" ON sync_performance_metrics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sync performance metrics" ON sync_performance_metrics FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own sync performance metrics" ON sync_performance_metrics FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own sync performance metrics" ON sync_performance_metrics FOR DELETE USING (auth.uid() = user_id);

-- Add trigger for updated_at column
CREATE TRIGGER update_sync_performance_metrics_updated_at 
    BEFORE UPDATE ON sync_performance_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
