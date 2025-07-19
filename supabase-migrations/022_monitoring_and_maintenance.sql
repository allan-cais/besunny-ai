-- Monitoring and Maintenance Utilities
-- This migration provides monitoring functions and maintenance procedures

-- ============================================================================
-- PERFORMANCE MONITORING FUNCTIONS
-- ============================================================================

-- Function to get slow queries
CREATE OR REPLACE FUNCTION get_slow_queries(limit_count INTEGER DEFAULT 10)
RETURNS TABLE(
  query TEXT,
  calls BIGINT,
  total_time DOUBLE PRECISION,
  mean_time DOUBLE PRECISION,
  rows BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get table sizes
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(
  table_name TEXT,
  table_size TEXT,
  index_size TEXT,
  total_size TEXT,
  row_count BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    schemaname||'.'||tablename as table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    n_tup_ins + n_tup_upd + n_tup_del as row_count
  FROM pg_stat_user_tables
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get index usage statistics
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE(
  table_name TEXT,
  index_name TEXT,
  index_size TEXT,
  index_scans BIGINT,
  index_tuples_read BIGINT,
  index_tuples_fetched BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    schemaname||'.'||tablename as table_name,
    indexname as index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as index_scans,
    idx_tup_read as index_tuples_read,
    idx_tup_fetch as index_tuples_fetched
  FROM pg_stat_user_indexes
  ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get connection statistics
CREATE OR REPLACE FUNCTION get_connection_stats()
RETURNS TABLE(
  database_name TEXT,
  active_connections INTEGER,
  max_connections INTEGER,
  connection_usage_percent NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    datname as database_name,
    numbackends as active_connections,
    setting::INTEGER as max_connections,
    ROUND((numbackends::NUMERIC / setting::NUMERIC) * 100, 2) as connection_usage_percent
  FROM pg_stat_database
  CROSS JOIN pg_settings
  WHERE name = 'max_connections'
  ORDER BY numbackends DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get cache hit ratios
CREATE OR REPLACE FUNCTION get_cache_hit_ratios()
RETURNS TABLE(
  table_name TEXT,
  heap_blks_read BIGINT,
  heap_blks_hit BIGINT,
  cache_hit_ratio NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    schemaname||'.'||tablename as table_name,
    heap_blks_read,
    heap_blks_hit,
    CASE 
      WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
      ELSE ROUND((heap_blks_hit::NUMERIC / (heap_blks_hit + heap_blks_read)::NUMERIC) * 100, 2)
    END as cache_hit_ratio
  FROM pg_statio_user_tables
  ORDER BY cache_hit_ratio ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to analyze all tables
CREATE OR REPLACE FUNCTION analyze_all_tables()
RETURNS VOID AS $$
DECLARE
  table_record RECORD;
BEGIN
  FOR table_record IN 
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE schemaname = 'public'
  LOOP
    EXECUTE 'ANALYZE ' || quote_ident(table_record.schemaname) || '.' || quote_ident(table_record.tablename);
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to vacuum all tables
CREATE OR REPLACE FUNCTION vacuum_all_tables()
RETURNS VOID AS $$
DECLARE
  table_record RECORD;
BEGIN
  FOR table_record IN 
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE schemaname = 'public'
  LOOP
    EXECUTE 'VACUUM ANALYZE ' || quote_ident(table_record.schemaname) || '.' || quote_ident(table_record.tablename);
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to reindex all indexes
CREATE OR REPLACE FUNCTION reindex_all_indexes()
RETURNS VOID AS $$
DECLARE
  index_record RECORD;
BEGIN
  FOR index_record IN 
    SELECT schemaname, tablename, indexname
    FROM pg_indexes 
    WHERE schemaname = 'public'
  LOOP
    EXECUTE 'REINDEX INDEX ' || quote_ident(index_record.schemaname) || '.' || quote_ident(index_record.indexname);
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 90)
RETURNS TABLE(
  table_name TEXT,
  deleted_count BIGINT
) AS $$
DECLARE
  cleanup_record RECORD;
  deleted_count BIGINT;
BEGIN
  -- Clean up old chat messages
  DELETE FROM chat_messages 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'chat_messages'::TEXT, deleted_count;
  
  -- Clean up old email processing logs
  DELETE FROM email_processing_logs 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'email_processing_logs'::TEXT, deleted_count;
  
  -- Clean up old calendar sync logs
  DELETE FROM calendar_sync_logs 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'calendar_sync_logs'::TEXT, deleted_count;
  
  -- Clean up old drive webhook logs
  DELETE FROM drive_webhook_logs 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'drive_webhook_logs'::TEXT, deleted_count;
  
  -- Clean up old agent logs
  DELETE FROM agent_logs 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'agent_logs'::TEXT, deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- PERFORMANCE ALERT FUNCTIONS
-- ============================================================================

-- Function to check for performance issues
CREATE OR REPLACE FUNCTION check_performance_issues()
RETURNS TABLE(
  issue_type TEXT,
  description TEXT,
  severity TEXT,
  recommendation TEXT
) AS $$
BEGIN
  -- Check for tables without recent VACUUM
  RETURN QUERY
  SELECT 
    'Stale Statistics'::TEXT as issue_type,
    'Table ' || schemaname || '.' || tablename || ' has not been analyzed recently' as description,
    'WARNING'::TEXT as severity,
    'Run ANALYZE on this table' as recommendation
  FROM pg_stat_user_tables
  WHERE last_analyze < now() - interval '7 days'
  OR last_analyze IS NULL;
  
  -- Check for tables with high bloat
  RETURN QUERY
  SELECT 
    'Table Bloat'::TEXT as issue_type,
    'Table ' || schemaname || '.' || tablename || ' may have high bloat' as description,
    'WARNING'::TEXT as severity,
    'Run VACUUM on this table' as recommendation
  FROM pg_stat_user_tables
  WHERE n_dead_tup > n_live_tup * 0.1;
  
  -- Check for unused indexes
  RETURN QUERY
  SELECT 
    'Unused Index'::TEXT as issue_type,
    'Index ' || indexname || ' on ' || schemaname || '.' || tablename || ' has no scans' as description,
    'INFO'::TEXT as severity,
    'Consider dropping this index if not needed' as recommendation
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0;
  
  -- Check for low cache hit ratios
  RETURN QUERY
  SELECT 
    'Low Cache Hit Ratio'::TEXT as issue_type,
    'Table ' || schemaname || '.' || tablename || ' has low cache hit ratio' as description,
    'WARNING'::TEXT as severity,
    'Consider increasing shared_buffers or optimizing queries' as recommendation
  FROM pg_statio_user_tables
  WHERE (heap_blks_hit::NUMERIC / NULLIF(heap_blks_hit + heap_blks_read, 0)::NUMERIC) < 0.8;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SCHEDULED MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to perform daily maintenance
CREATE OR REPLACE FUNCTION perform_daily_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Refresh materialized views
  PERFORM refresh_performance_views();
  
  -- Analyze tables that haven't been analyzed recently
  PERFORM analyze_all_tables();
  
  -- Clean up old data (keep 90 days)
  PERFORM cleanup_old_data(90);
  
  -- Log maintenance completion
  INSERT INTO agent_logs (level, message, created_at)
  VALUES ('INFO', 'Daily maintenance completed successfully', now());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to perform weekly maintenance
CREATE OR REPLACE FUNCTION perform_weekly_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Perform daily maintenance
  PERFORM perform_daily_maintenance();
  
  -- Vacuum all tables
  PERFORM vacuum_all_tables();
  
  -- Log maintenance completion
  INSERT INTO agent_logs (level, message, created_at)
  VALUES ('INFO', 'Weekly maintenance completed successfully', now());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to perform monthly maintenance
CREATE OR REPLACE FUNCTION perform_monthly_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Perform weekly maintenance
  PERFORM perform_weekly_maintenance();
  
  -- Reindex all indexes
  PERFORM reindex_all_indexes();
  
  -- Log maintenance completion
  INSERT INTO agent_logs (level, message, created_at)
  VALUES ('INFO', 'Monthly maintenance completed successfully', now());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant execute permissions on monitoring functions
GRANT EXECUTE ON FUNCTION get_slow_queries(INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION get_table_sizes() TO service_role;
GRANT EXECUTE ON FUNCTION get_index_usage_stats() TO service_role;
GRANT EXECUTE ON FUNCTION get_connection_stats() TO service_role;
GRANT EXECUTE ON FUNCTION get_cache_hit_ratios() TO service_role;

-- Grant execute permissions on maintenance functions
GRANT EXECUTE ON FUNCTION analyze_all_tables() TO service_role;
GRANT EXECUTE ON FUNCTION vacuum_all_tables() TO service_role;
GRANT EXECUTE ON FUNCTION reindex_all_indexes() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data(INTEGER) TO service_role;

-- Grant execute permissions on alert functions
GRANT EXECUTE ON FUNCTION check_performance_issues() TO service_role;

-- Grant execute permissions on scheduled maintenance functions
GRANT EXECUTE ON FUNCTION perform_daily_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_weekly_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_monthly_maintenance() TO service_role;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION get_slow_queries(INTEGER) IS 'Get the slowest queries from pg_stat_statements';
COMMENT ON FUNCTION get_table_sizes() IS 'Get size information for all tables';
COMMENT ON FUNCTION get_index_usage_stats() IS 'Get index usage statistics';
COMMENT ON FUNCTION get_connection_stats() IS 'Get database connection statistics';
COMMENT ON FUNCTION get_cache_hit_ratios() IS 'Get cache hit ratios for all tables';
COMMENT ON FUNCTION analyze_all_tables() IS 'Run ANALYZE on all tables to update statistics';
COMMENT ON FUNCTION vacuum_all_tables() IS 'Run VACUUM ANALYZE on all tables';
COMMENT ON FUNCTION reindex_all_indexes() IS 'Reindex all indexes to rebuild them';
COMMENT ON FUNCTION cleanup_old_data(INTEGER) IS 'Clean up old data from log tables';
COMMENT ON FUNCTION check_performance_issues() IS 'Check for common performance issues';
COMMENT ON FUNCTION perform_daily_maintenance() IS 'Perform daily maintenance tasks';
COMMENT ON FUNCTION perform_weekly_maintenance() IS 'Perform weekly maintenance tasks';
COMMENT ON FUNCTION perform_monthly_maintenance() IS 'Perform monthly maintenance tasks';

-- ============================================================================
-- CREATE MAINTENANCE LOG TABLE
-- ============================================================================

-- Create table to log maintenance activities
CREATE TABLE IF NOT EXISTS maintenance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  maintenance_type TEXT NOT NULL,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  completed_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'running',
  details JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS on maintenance_logs
ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for maintenance_logs
CREATE POLICY "Service role can manage maintenance logs" ON maintenance_logs
  FOR ALL USING (auth.role() = 'service_role');

-- Create index on maintenance_logs
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_type_status ON maintenance_logs(maintenance_type, status);
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_created_at ON maintenance_logs(created_at);

-- Function to log maintenance activities
CREATE OR REPLACE FUNCTION log_maintenance_activity(
  maintenance_type_param TEXT,
  details_param JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  log_id UUID;
BEGIN
  INSERT INTO maintenance_logs (maintenance_type, details)
  VALUES (maintenance_type_param, details_param)
  RETURNING id INTO log_id;
  
  RETURN log_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to complete maintenance activity
CREATE OR REPLACE FUNCTION complete_maintenance_activity(
  log_id_param UUID,
  status_param TEXT DEFAULT 'completed',
  details_param JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
  UPDATE maintenance_logs
  SET 
    completed_at = now(),
    status = status_param,
    details = COALESCE(details_param, details)
  WHERE id = log_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions on logging functions
GRANT EXECUTE ON FUNCTION log_maintenance_activity(TEXT, JSONB) TO service_role;
GRANT EXECUTE ON FUNCTION complete_maintenance_activity(UUID, TEXT, JSONB) TO service_role; 