-- Monitoring and Maintenance Utilities
-- This migration provides monitoring functions and maintenance procedures
-- Based on actual remote database schema inspection

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
  
  -- Clean up old sync tracking records
  DELETE FROM sync_tracking 
  WHERE created_at < now() - interval '1 day' * days_to_keep;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RETURN QUERY SELECT 'sync_tracking'::TEXT, deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check for performance issues
CREATE OR REPLACE FUNCTION check_performance_issues()
RETURNS TABLE(
  issue_type TEXT,
  table_name TEXT,
  issue_description TEXT,
  recommendation TEXT
) AS $$
BEGIN
  -- Check for tables without primary keys
  RETURN QUERY
  SELECT 
    'Missing Primary Key'::TEXT as issue_type,
    t.table_name,
    'Table has no primary key defined' as issue_description,
    'Add a primary key to improve query performance' as recommendation
  FROM information_schema.tables t
  LEFT JOIN information_schema.table_constraints tc 
    ON t.table_name = tc.table_name 
    AND tc.constraint_type = 'PRIMARY KEY'
  WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    AND tc.constraint_name IS NULL;
  
  -- Check for large tables without indexes
  RETURN QUERY
  SELECT 
    'Large Table Without Indexes'::TEXT as issue_type,
    schemaname||'.'||tablename as table_name,
    'Table has ' || n_tup_ins + n_tup_upd + n_tup_del || ' rows but no indexes' as issue_description,
    'Consider adding indexes for frequently queried columns' as recommendation
  FROM pg_stat_user_tables
  WHERE (n_tup_ins + n_tup_upd + n_tup_del) > 1000
    AND schemaname = 'public'
    AND NOT EXISTS (
      SELECT 1 FROM pg_indexes 
      WHERE tablename = pg_stat_user_tables.tablename 
        AND schemaname = 'public'
    );
  
  -- Check for unused indexes
  RETURN QUERY
  SELECT 
    'Unused Index'::TEXT as issue_type,
    schemaname||'.'||tablename as table_name,
    'Index ' || indexname || ' has never been used' as issue_description,
    'Consider dropping unused indexes to improve write performance' as recommendation
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0 
    AND schemaname = 'public'
    AND indexname NOT LIKE '%_pkey'
    AND indexname NOT LIKE '%_key';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SCHEDULED MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to perform daily maintenance
CREATE OR REPLACE FUNCTION perform_daily_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Analyze tables to update statistics
  PERFORM analyze_all_tables();
  
  -- Clean up old data (keep last 30 days by default)
  PERFORM cleanup_old_data(30);
  
  -- Log maintenance activity
  PERFORM log_maintenance_activity('daily', 'started', 'Daily maintenance started');
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(
    (SELECT id FROM maintenance_logs WHERE maintenance_type = 'daily' ORDER BY created_at DESC LIMIT 1),
    'completed',
    'Daily maintenance completed successfully'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to perform weekly maintenance
CREATE OR REPLACE FUNCTION perform_weekly_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Perform daily maintenance first
  PERFORM perform_daily_maintenance();
  
  -- Vacuum tables to reclaim space
  PERFORM vacuum_all_tables();
  
  -- Log maintenance activity
  PERFORM log_maintenance_activity('weekly', 'started', 'Weekly maintenance started');
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(
    (SELECT id FROM maintenance_logs WHERE maintenance_type = 'weekly' ORDER BY created_at DESC LIMIT 1),
    'completed',
    'Weekly maintenance completed successfully'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to perform monthly maintenance
CREATE OR REPLACE FUNCTION perform_monthly_maintenance()
RETURNS VOID AS $$
BEGIN
  -- Perform weekly maintenance first
  PERFORM perform_weekly_maintenance();
  
  -- Reindex all indexes
  PERFORM reindex_all_indexes();
  
  -- Clean up old data (keep last 90 days)
  PERFORM cleanup_old_data(90);
  
  -- Log maintenance activity
  PERFORM log_maintenance_activity('monthly', 'started', 'Monthly maintenance started');
  
  -- Mark as completed
  PERFORM complete_maintenance_activity(
    (SELECT id FROM maintenance_logs WHERE maintenance_type = 'monthly' ORDER BY created_at DESC LIMIT 1),
    'completed',
    'Monthly maintenance completed successfully'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- MAINTENANCE LOGGING
-- ============================================================================

-- Create maintenance logs table
CREATE TABLE IF NOT EXISTS maintenance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  maintenance_type TEXT NOT NULL CHECK (maintenance_type IN ('daily', 'weekly', 'monthly')),
  status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
  details JSONB,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for maintenance logs
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_type_status ON maintenance_logs(maintenance_type, status);
CREATE INDEX IF NOT EXISTS idx_maintenance_logs_created_at ON maintenance_logs(created_at);

-- Function to log maintenance activity
CREATE OR REPLACE FUNCTION log_maintenance_activity(
  maintenance_type_param TEXT,
  status_param TEXT DEFAULT 'started',
  details_param JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
  log_id UUID;
BEGIN
  INSERT INTO maintenance_logs (maintenance_type, status, details)
  VALUES (maintenance_type_param, status_param, details_param)
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
    status = status_param,
    details = COALESCE(details_param, details),
    completed_at = now()
  WHERE id = log_id_param;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- PERFORMANCE ALERTS
-- ============================================================================

-- Function to check for performance alerts
CREATE OR REPLACE FUNCTION check_performance_alerts()
RETURNS TABLE(
  alert_type TEXT,
  severity TEXT,
  message TEXT,
  recommendation TEXT
) AS $$
BEGIN
  -- Check for slow queries
  RETURN QUERY
  SELECT 
    'Slow Query'::TEXT as alert_type,
    CASE 
      WHEN mean_time > 1000 THEN 'HIGH'
      WHEN mean_time > 100 THEN 'MEDIUM'
      ELSE 'LOW'
    END as severity,
    'Query taking ' || ROUND(mean_time, 2) || 'ms on average' as message,
    'Consider optimizing query or adding indexes' as recommendation
  FROM pg_stat_statements
  WHERE mean_time > 100
  ORDER BY mean_time DESC
  LIMIT 5;
  
  -- Check for connection usage
  RETURN QUERY
  SELECT 
    'High Connection Usage'::TEXT as alert_type,
    CASE 
      WHEN connection_usage_percent > 80 THEN 'HIGH'
      WHEN connection_usage_percent > 60 THEN 'MEDIUM'
      ELSE 'LOW'
    END as severity,
    'Database using ' || connection_usage_percent || '% of available connections' as message,
    'Consider connection pooling or increasing max_connections' as recommendation
  FROM get_connection_stats()
  WHERE connection_usage_percent > 50;
  
  -- Check for low cache hit ratios
  RETURN QUERY
  SELECT 
    'Low Cache Hit Ratio'::TEXT as alert_type,
    CASE 
      WHEN cache_hit_ratio < 80 THEN 'HIGH'
      WHEN cache_hit_ratio < 90 THEN 'MEDIUM'
      ELSE 'LOW'
    END as severity,
    'Table ' || table_name || ' has ' || cache_hit_ratio || '% cache hit ratio' as message,
    'Consider increasing shared_buffers or optimizing queries' as recommendation
  FROM get_cache_hit_ratios()
  WHERE cache_hit_ratio < 90;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant execute permissions on monitoring functions
GRANT EXECUTE ON FUNCTION get_slow_queries(INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION get_table_sizes() TO authenticated;
GRANT EXECUTE ON FUNCTION get_index_usage_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_connection_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_cache_hit_ratios() TO authenticated;
GRANT EXECUTE ON FUNCTION check_performance_issues() TO authenticated;
GRANT EXECUTE ON FUNCTION check_performance_alerts() TO authenticated;

-- Grant execute permissions on maintenance functions (service role only)
GRANT EXECUTE ON FUNCTION analyze_all_tables() TO service_role;
GRANT EXECUTE ON FUNCTION vacuum_all_tables() TO service_role;
GRANT EXECUTE ON FUNCTION reindex_all_indexes() TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_data(INTEGER) TO service_role;
GRANT EXECUTE ON FUNCTION perform_daily_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_weekly_maintenance() TO service_role;
GRANT EXECUTE ON FUNCTION perform_monthly_maintenance() TO service_role;

-- Grant permissions on maintenance logs table
GRANT SELECT ON maintenance_logs TO authenticated;
GRANT INSERT, UPDATE ON maintenance_logs TO service_role;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION get_slow_queries(INTEGER) IS 'Get the slowest queries from pg_stat_statements';
COMMENT ON FUNCTION get_table_sizes() IS 'Get size information for all tables';
COMMENT ON FUNCTION get_index_usage_stats() IS 'Get usage statistics for all indexes';
COMMENT ON FUNCTION get_connection_stats() IS 'Get current connection usage statistics';
COMMENT ON FUNCTION get_cache_hit_ratios() IS 'Get cache hit ratios for all tables';
COMMENT ON FUNCTION check_performance_issues() IS 'Check for common performance issues';
COMMENT ON FUNCTION check_performance_alerts() IS 'Check for performance alerts and warnings';
COMMENT ON FUNCTION perform_daily_maintenance() IS 'Perform daily maintenance tasks';
COMMENT ON FUNCTION perform_weekly_maintenance() IS 'Perform weekly maintenance tasks';
COMMENT ON FUNCTION perform_monthly_maintenance() IS 'Perform monthly maintenance tasks';
COMMENT ON TABLE maintenance_logs IS 'Log of maintenance activities and their status'; 