-- Adaptive Sync Strategy Migration
-- This migration replaces the real-time webhooks model with an adaptive sync strategy

-- Create user activity logs table
CREATE TABLE IF NOT EXISTS user_activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  activity_type TEXT NOT NULL CHECK (activity_type IN ('app_load', 'calendar_view', 'meeting_create', 'general')),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create user sync states table
CREATE TABLE IF NOT EXISTS user_sync_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  last_sync_time TIMESTAMP WITH TIME ZONE,
  change_frequency TEXT DEFAULT 'low' CHECK (change_frequency IN ('high', 'medium', 'low')),
  last_activity_time TIMESTAMP WITH TIME ZONE DEFAULT now(),
  sync_interval_ms INTEGER DEFAULT 300000, -- 5 minutes default
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id)
);

-- Create sync performance metrics table
CREATE TABLE IF NOT EXISTS sync_performance_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  service_type TEXT NOT NULL CHECK (service_type IN ('calendar', 'drive', 'gmail', 'attendee')),
  sync_type TEXT NOT NULL CHECK (sync_type IN ('immediate', 'fast', 'normal', 'slow', 'background')),
  processed_count INTEGER DEFAULT 0,
  created_count INTEGER DEFAULT 0,
  updated_count INTEGER DEFAULT 0,
  deleted_count INTEGER DEFAULT 0,
  skipped BOOLEAN DEFAULT false,
  duration_ms INTEGER,
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_timestamp ON user_activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);

CREATE INDEX IF NOT EXISTS idx_user_sync_states_user_id ON user_sync_states(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_last_sync_time ON user_sync_states(last_sync_time);
CREATE INDEX IF NOT EXISTS idx_user_sync_states_change_frequency ON user_sync_states(change_frequency);

CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_user_id ON sync_performance_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_service_type ON sync_performance_metrics(service_type);
CREATE INDEX IF NOT EXISTS idx_sync_performance_metrics_timestamp ON sync_performance_metrics(timestamp);

-- Add RLS policies
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sync_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_performance_metrics ENABLE ROW LEVEL SECURITY;

-- User activity logs policies
CREATE POLICY "Users can view their own activity logs" ON user_activity_logs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own activity logs" ON user_activity_logs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can manage all activity logs" ON user_activity_logs
  FOR ALL USING (auth.role() = 'service_role');

-- User sync states policies
CREATE POLICY "Users can view their own sync states" ON user_sync_states
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own sync states" ON user_sync_states
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sync states" ON user_sync_states
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can manage all sync states" ON user_sync_states
  FOR ALL USING (auth.role() = 'service_role');

-- Sync performance metrics policies
CREATE POLICY "Users can view their own sync metrics" ON sync_performance_metrics
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all sync metrics" ON sync_performance_metrics
  FOR ALL USING (auth.role() = 'service_role');

-- Create functions for adaptive sync strategy

-- Function to get user activity summary
CREATE OR REPLACE FUNCTION get_user_activity_summary(user_uuid UUID, hours_back INTEGER DEFAULT 24)
RETURNS TABLE(
  activity_type TEXT,
  count BIGINT,
  last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ual.activity_type,
    COUNT(*) as count,
    MAX(ual.timestamp) as last_activity
  FROM user_activity_logs ual
  WHERE ual.user_id = user_uuid
    AND ual.timestamp > NOW() - INTERVAL '1 hour' * hours_back
  GROUP BY ual.activity_type
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to determine optimal sync interval
CREATE OR REPLACE FUNCTION calculate_optimal_sync_interval(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  activity_count BIGINT;
  change_freq TEXT;
  optimal_interval INTEGER;
BEGIN
  -- Get recent activity count
  SELECT COUNT(*) INTO activity_count
  FROM user_activity_logs
  WHERE user_id = user_uuid
    AND timestamp > NOW() - INTERVAL '1 hour';
  
  -- Get current change frequency
  SELECT change_frequency INTO change_freq
  FROM user_sync_states
  WHERE user_id = user_uuid;
  
  -- Calculate optimal interval based on activity and change frequency
  IF activity_count > 20 THEN
    optimal_interval := 30000; -- 30 seconds for very active users
  ELSIF activity_count > 10 THEN
    optimal_interval := 60000; -- 1 minute for active users
  ELSIF change_freq = 'high' THEN
    optimal_interval := 300000; -- 5 minutes for high change frequency
  ELSIF change_freq = 'medium' THEN
    optimal_interval := 600000; -- 10 minutes for medium change frequency
  ELSE
    optimal_interval := 900000; -- 15 minutes for low activity/change frequency
  END IF;
  
  RETURN optimal_interval;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to record sync performance
CREATE OR REPLACE FUNCTION record_sync_performance(
  user_uuid UUID,
  service_type TEXT,
  sync_type TEXT,
  processed_count INTEGER DEFAULT 0,
  created_count INTEGER DEFAULT 0,
  updated_count INTEGER DEFAULT 0,
  deleted_count INTEGER DEFAULT 0,
  skipped BOOLEAN DEFAULT false,
  duration_ms INTEGER DEFAULT NULL,
  success BOOLEAN DEFAULT true,
  error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  metric_id UUID;
BEGIN
  INSERT INTO sync_performance_metrics (
    user_id,
    service_type,
    sync_type,
    processed_count,
    created_count,
    updated_count,
    deleted_count,
    skipped,
    duration_ms,
    success,
    error_message
  ) VALUES (
    user_uuid,
    service_type,
    sync_type,
    processed_count,
    created_count,
    updated_count,
    deleted_count,
    skipped,
    duration_ms,
    success,
    error_message
  ) RETURNING id INTO metric_id;
  
  RETURN metric_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_user_activity_summary(UUID, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_activity_summary(UUID, INTEGER) TO service_role;

GRANT EXECUTE ON FUNCTION calculate_optimal_sync_interval(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION calculate_optimal_sync_interval(UUID) TO service_role;

GRANT EXECUTE ON FUNCTION record_sync_performance(UUID, TEXT, TEXT, INTEGER, INTEGER, INTEGER, INTEGER, BOOLEAN, INTEGER, BOOLEAN, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION record_sync_performance(UUID, TEXT, TEXT, INTEGER, INTEGER, INTEGER, INTEGER, BOOLEAN, INTEGER, BOOLEAN, TEXT) TO service_role;

-- Create view for sync analytics
CREATE OR REPLACE VIEW sync_analytics AS
SELECT 
  u.id as user_id,
  u.email,
  uss.last_sync_time,
  uss.change_frequency,
  uss.sync_interval_ms,
  uss.is_active,
  COUNT(ual.id) as activity_count_24h,
  COUNT(spm.id) as sync_count_24h,
  AVG(spm.duration_ms) as avg_sync_duration_ms,
  SUM(CASE WHEN spm.success THEN 1 ELSE 0 END) as successful_syncs,
  SUM(CASE WHEN NOT spm.success THEN 1 ELSE 0 END) as failed_syncs
FROM auth.users u
LEFT JOIN user_sync_states uss ON u.id = uss.user_id
LEFT JOIN user_activity_logs ual ON u.id = ual.user_id 
  AND ual.timestamp > NOW() - INTERVAL '24 hours'
LEFT JOIN sync_performance_metrics spm ON u.id = spm.user_id 
  AND spm.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY u.id, u.email, uss.last_sync_time, uss.change_frequency, uss.sync_interval_ms, uss.is_active;

-- Grant select permissions on the view
GRANT SELECT ON sync_analytics TO authenticated;
GRANT SELECT ON sync_analytics TO service_role;

-- Add comments for documentation
COMMENT ON TABLE user_activity_logs IS 'Tracks user activity for adaptive sync strategy';
COMMENT ON TABLE user_sync_states IS 'Stores user sync state and preferences for adaptive sync';
COMMENT ON TABLE sync_performance_metrics IS 'Tracks sync performance and metrics for optimization';
COMMENT ON VIEW sync_analytics IS 'Analytics view for monitoring sync performance and user activity'; 