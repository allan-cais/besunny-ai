-- Maintenance Functions Migration
-- Creates maintenance_logs table and related functions for system maintenance

-- ============================================================================
-- DROP EXISTING MAINTENANCE FUNCTIONS FIRST
-- ============================================================================
DROP FUNCTION IF EXISTS complete_maintenance_activity(UUID);
DROP FUNCTION IF EXISTS log_maintenance_activity(TEXT, TEXT, JSONB);
DROP FUNCTION IF EXISTS cleanup_old_data();
DROP FUNCTION IF EXISTS perform_daily_maintenance();
DROP FUNCTION IF EXISTS perform_weekly_maintenance();
DROP FUNCTION IF EXISTS perform_monthly_maintenance();
DROP FUNCTION IF EXISTS schedule_maintenance(TEXT, TIMESTAMP WITH TIME ZONE);
DROP FUNCTION IF EXISTS get_maintenance_status(UUID);

-- ============================================================================
-- CREATE MAINTENANCE LOGS TABLE
-- ============================================================================

-- Create maintenance_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS maintenance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_type TEXT NOT NULL,
  description TEXT,
  details JSONB,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on maintenance_logs
ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for maintenance_logs
CREATE POLICY "Service role can manage maintenance logs" ON maintenance_logs
  FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions
GRANT ALL ON TABLE maintenance_logs TO service_role;
GRANT SELECT ON TABLE maintenance_logs TO authenticated;

-- Create indexes for maintenance_logs
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_activity_type ON maintenance_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_status ON maintenance_logs(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_started_at ON maintenance_logs(started_at);

-- ============================================================================
-- CREATE MAINTENANCE FUNCTIONS
-- ============================================================================

-- Create complete_maintenance_activity function
CREATE OR REPLACE FUNCTION complete_maintenance_activity(activity_id UUID)
RETURNS VOID AS $$
BEGIN
  UPDATE maintenance_logs 
  SET 
    completed_at = NOW(),
    status = 'completed'
  WHERE id = activity_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create log_maintenance_activity function
CREATE OR REPLACE FUNCTION log_maintenance_activity(
  activity_type TEXT,
  description TEXT DEFAULT NULL,
  details JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  activity_id UUID;
BEGIN
  INSERT INTO maintenance_logs (
    activity_type,
    description,
    details,
    started_at,
    status
  ) VALUES (
    activity_type,
    description,
    details,
    NOW(),
    'running'
  ) RETURNING id INTO activity_id;
  
  RETURN activity_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create cleanup_old_data function
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER := 0;
BEGIN
  -- Clean up old maintenance logs (older than 90 days)
  DELETE FROM maintenance_logs 
  WHERE created_at < NOW() - INTERVAL '90 days';
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create perform_daily_maintenance function
CREATE OR REPLACE FUNCTION perform_daily_maintenance()
RETURNS VOID AS $$
DECLARE
  activity_id UUID;
BEGIN
  -- Log the maintenance activity
  activity_id := log_maintenance_activity('daily', 'Daily maintenance routine');
  
  -- Perform maintenance tasks
  PERFORM analyze_all_tables();
  PERFORM cleanup_old_data();
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(activity_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create perform_weekly_maintenance function
CREATE OR REPLACE FUNCTION perform_weekly_maintenance()
RETURNS VOID AS $$
DECLARE
  activity_id UUID;
BEGIN
  -- Log the maintenance activity
  activity_id := log_maintenance_activity('weekly', 'Weekly maintenance routine');
  
  -- Perform maintenance tasks
  PERFORM vacuum_all_tables();
  PERFORM reindex_all_indexes();
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(activity_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create perform_monthly_maintenance function
CREATE OR REPLACE FUNCTION perform_monthly_maintenance()
RETURNS VOID AS $$
DECLARE
  activity_id UUID;
BEGIN
  -- Log the maintenance activity
  activity_id := log_maintenance_activity('monthly', 'Monthly maintenance routine');
  
  -- Perform comprehensive maintenance
  PERFORM perform_weekly_maintenance();
  PERFORM refresh_performance_views();
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(activity_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ============================================================================
-- CREATE MAINTENANCE SCHEDULING FUNCTIONS
-- ============================================================================

-- Create schedule_maintenance function
CREATE OR REPLACE FUNCTION schedule_maintenance(
  maintenance_type TEXT,
  scheduled_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS UUID AS $$
DECLARE
  activity_id UUID;
BEGIN
  -- Log the scheduled maintenance
  activity_id := log_maintenance_activity(
    maintenance_type, 
    'Scheduled ' || maintenance_type || ' maintenance',
    jsonb_build_object('scheduled_time', scheduled_time)
  );
  
  RETURN activity_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create get_maintenance_status function
CREATE OR REPLACE FUNCTION get_maintenance_status(activity_id UUID DEFAULT NULL)
RETURNS TABLE(
  id UUID,
  activity_type TEXT,
  description TEXT,
  status TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  duration INTERVAL
) AS $$
BEGIN
  IF activity_id IS NULL THEN
    -- Return recent maintenance activities
    RETURN QUERY
    SELECT 
      ml.id,
      ml.activity_type,
      ml.description,
      ml.status,
      ml.started_at,
      ml.completed_at,
      COALESCE(ml.completed_at - ml.started_at, NOW() - ml.started_at) as duration
    FROM maintenance_logs ml
    ORDER BY ml.started_at DESC
    LIMIT 50;
  ELSE
    -- Return specific maintenance activity
    RETURN QUERY
    SELECT 
      ml.id,
      ml.activity_type,
      ml.description,
      ml.status,
      ml.started_at,
      ml.completed_at,
      COALESCE(ml.completed_at - ml.started_at, NOW() - ml.started_at) as duration
    FROM maintenance_logs ml
    WHERE ml.id = activity_id;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ============================================================================
-- GRANT PERMISSIONS FOR MAINTENANCE FUNCTIONS
-- ============================================================================

-- Grant execute permissions to service role
GRANT EXECUTE ON FUNCTION complete_maintenance_activity(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION log_maintenance_activity(TEXT, TEXT, JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO service_role;
GRANT EXECUTE ON FUNCTION perform_daily_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_weekly_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_monthly_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION schedule_maintenance(TEXT, TIMESTAMP WITH TIME ZONE) TO service_role;
GRANT EXECUTE ON FUNCTION get_maintenance_status(UUID) TO service_role;

-- Grant read permissions to authenticated users
GRANT EXECUTE ON FUNCTION get_maintenance_status(UUID) TO authenticated; 