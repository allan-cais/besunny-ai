-- Simple Security Fix Migration
-- Addresses function_search_path_mutable and materialized_view_in_api warnings
-- Without the complex maintenance functions that are causing issues

-- ============================================================================
-- FIX FUNCTION SEARCH PATH MUTABLE WARNINGS
-- ============================================================================

-- Drop existing triggers first (they depend on functions)
DROP TRIGGER IF EXISTS trg_refresh_user_activity_chat_sessions ON chat_sessions;
DROP TRIGGER IF EXISTS trg_refresh_user_activity_chat_messages ON chat_messages;
DROP TRIGGER IF EXISTS trg_refresh_user_activity_projects ON projects;
DROP TRIGGER IF EXISTS trg_refresh_user_activity_documents ON documents;
DROP TRIGGER IF EXISTS trg_refresh_project_stats_documents ON documents;
DROP TRIGGER IF EXISTS trg_refresh_project_stats_chunks ON document_chunks;
DROP TRIGGER IF EXISTS trg_refresh_project_stats_knowledge_spaces ON knowledge_spaces;

-- Drop existing functions to recreate with proper search_path
DROP FUNCTION IF EXISTS user_has_project_access(UUID);
DROP FUNCTION IF EXISTS user_has_document_access(UUID);
DROP FUNCTION IF EXISTS refresh_performance_views();
DROP FUNCTION IF EXISTS refresh_user_activity_summary();
DROP FUNCTION IF EXISTS refresh_project_statistics();
DROP FUNCTION IF EXISTS get_slow_queries(INTEGER);
DROP FUNCTION IF EXISTS get_table_sizes();
DROP FUNCTION IF EXISTS get_index_usage_stats();
DROP FUNCTION IF EXISTS reindex_all_indexes();
DROP FUNCTION IF EXISTS get_connection_stats();
DROP FUNCTION IF EXISTS get_cache_hit_ratios();
DROP FUNCTION IF EXISTS check_performance_issues();
DROP FUNCTION IF EXISTS check_performance_alerts();
DROP FUNCTION IF EXISTS analyze_all_tables();
DROP FUNCTION IF EXISTS vacuum_all_tables();

-- Fix user_has_project_access function
CREATE OR REPLACE FUNCTION user_has_project_access(project_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM projects 
    WHERE id = project_uuid AND created_by = (SELECT auth.uid())
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = public;

-- Fix user_has_document_access function
CREATE OR REPLACE FUNCTION user_has_document_access(document_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = document_uuid AND p.created_by = (SELECT auth.uid())
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE SET search_path = public;

-- Fix refresh_performance_views function
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY user_activity_summary;
  REFRESH MATERIALIZED VIEW CONCURRENTLY project_statistics;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix refresh_user_activity_summary function
CREATE OR REPLACE FUNCTION refresh_user_activity_summary()
RETURNS TRIGGER AS $$
BEGIN
  -- Refresh the materialized view asynchronously
  PERFORM pg_notify('refresh_user_activity', '');
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Fix refresh_project_statistics function
CREATE OR REPLACE FUNCTION refresh_project_statistics()
RETURNS TRIGGER AS $$
BEGIN
  -- Refresh the materialized view asynchronously
  PERFORM pg_notify('refresh_project_statistics', '');
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Fix get_slow_queries function
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
  ORDER BY total_time DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix get_table_sizes function
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(
  table_name TEXT,
  table_size TEXT,
  index_size TEXT,
  total_size TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    schemaname||'.'||tablename as table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) + pg_indexes_size(schemaname||'.'||tablename)) as total_size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix get_index_usage_stats function
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE(
  index_name TEXT,
  table_name TEXT,
  index_scans BIGINT,
  index_tuples_read BIGINT,
  index_tuples_fetched BIGINT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    indexrelname as index_name,
    tablename as table_name,
    idx_scan as index_scans,
    idx_tup_read as index_tuples_read,
    idx_tup_fetch as index_tuples_fetched
  FROM pg_stat_user_indexes
  ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix reindex_all_indexes function
CREATE OR REPLACE FUNCTION reindex_all_indexes()
RETURNS VOID AS $$
DECLARE
  index_record RECORD;
BEGIN
  FOR index_record IN 
    SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
  LOOP
    EXECUTE 'REINDEX INDEX ' || index_record.indexname;
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix get_connection_stats function
CREATE OR REPLACE FUNCTION get_connection_stats()
RETURNS TABLE(
  state TEXT,
  count INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    state,
    count(*)
  FROM pg_stat_activity
  GROUP BY state
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix get_cache_hit_ratios function
CREATE OR REPLACE FUNCTION get_cache_hit_ratios()
RETURNS TABLE(
  table_name TEXT,
  heap_blks_read BIGINT,
  heap_blks_hit BIGINT,
  hit_ratio NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    schemaname||'.'||tablename as table_name,
    heap_blks_read,
    heap_blks_hit,
    CASE 
      WHEN (heap_blks_hit + heap_blks_read) = 0 THEN 0
      ELSE ROUND((heap_blks_hit::NUMERIC / (heap_blks_hit + heap_blks_read)) * 100, 2)
    END as hit_ratio
  FROM pg_statio_user_tables
  ORDER BY hit_ratio DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix check_performance_issues function
CREATE OR REPLACE FUNCTION check_performance_issues()
RETURNS TABLE(
  issue_type TEXT,
  description TEXT,
  severity TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    'slow_queries' as issue_type,
    'Queries taking longer than 1 second detected' as description,
    'WARNING' as severity
  WHERE EXISTS (
    SELECT 1 FROM pg_stat_statements 
    WHERE mean_time > 1000
  );
  
  RETURN QUERY
  SELECT 
    'low_cache_hit_ratio' as issue_type,
    'Cache hit ratio below 80% detected' as description,
    'WARNING' as severity
  WHERE EXISTS (
    SELECT 1 FROM pg_statio_user_tables
    WHERE (heap_blks_hit::NUMERIC / NULLIF(heap_blks_hit + heap_blks_read, 0)) < 0.8
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix check_performance_alerts function
CREATE OR REPLACE FUNCTION check_performance_alerts()
RETURNS TABLE(
  alert_type TEXT,
  message TEXT,
  created_at TIMESTAMP
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    'performance_alert' as alert_type,
    'Performance issues detected' as message,
    NOW() as created_at
  WHERE EXISTS (
    SELECT 1 FROM check_performance_issues()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix analyze_all_tables function
CREATE OR REPLACE FUNCTION analyze_all_tables()
RETURNS VOID AS $$
DECLARE
  table_record RECORD;
BEGIN
  FOR table_record IN 
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  LOOP
    EXECUTE 'ANALYZE ' || table_record.tablename;
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Fix vacuum_all_tables function
CREATE OR REPLACE FUNCTION vacuum_all_tables()
RETURNS VOID AS $$
DECLARE
  table_record RECORD;
BEGIN
  FOR table_record IN 
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  LOOP
    EXECUTE 'VACUUM ANALYZE ' || table_record.tablename;
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ============================================================================
-- SECURE MATERIALIZED VIEWS (RLS not supported on materialized views)
-- ============================================================================

-- Note: Materialized views don't support RLS in PostgreSQL
-- Instead, we'll secure access through functions and proper permissions

-- Revoke direct access to materialized views from public and anon
REVOKE ALL ON user_activity_summary FROM public, anon;
REVOKE ALL ON project_statistics FROM public, anon;

-- Grant access only to authenticated users and service role
GRANT SELECT ON user_activity_summary TO authenticated, service_role;
GRANT SELECT ON project_statistics TO authenticated, service_role;

-- Create secure wrapper functions for accessing materialized views
CREATE OR REPLACE FUNCTION get_user_activity_summary(user_uuid UUID DEFAULT NULL)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  chat_sessions_count BIGINT,
  messages_count BIGINT,
  projects_count BIGINT,
  documents_count BIGINT,
  last_chat_activity TIMESTAMP WITHOUT TIME ZONE,
  last_project_activity TIMESTAMP WITHOUT TIME ZONE
) AS $$
BEGIN
  -- If no user_uuid provided, use current user
  IF user_uuid IS NULL THEN
    user_uuid := (SELECT auth.uid());
  END IF;
  
  -- Only allow users to see their own data or service role to see all
  IF user_uuid = (SELECT auth.uid()) OR auth.role() = 'service_role' THEN
    RETURN QUERY
    SELECT * FROM user_activity_summary
    WHERE user_activity_summary.user_id = user_uuid;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE FUNCTION get_project_statistics(project_uuid UUID DEFAULT NULL)
RETURNS TABLE(
  project_id UUID,
  project_name TEXT,
  user_id UUID,
  documents_count BIGINT,
  chunks_count BIGINT,
  knowledge_spaces_count BIGINT,
  last_document_activity TIMESTAMP WITHOUT TIME ZONE
) AS $$
BEGIN
  -- If no project_uuid provided, return all projects for current user
  IF project_uuid IS NULL THEN
    RETURN QUERY
    SELECT * FROM project_statistics
    WHERE project_statistics.user_id = (SELECT auth.uid());
  ELSE
    -- Check if user has access to this specific project
    IF EXISTS (
      SELECT 1 FROM projects 
      WHERE id = project_uuid AND created_by = (SELECT auth.uid())
    ) OR auth.role() = 'service_role' THEN
      RETURN QUERY
      SELECT * FROM project_statistics
      WHERE project_statistics.project_id = project_uuid;
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- ============================================================================
-- RECREATE TRIGGERS WITH UPDATED FUNCTIONS
-- ============================================================================

-- Recreate triggers for user activity summary refresh
CREATE TRIGGER trg_refresh_user_activity_chat_sessions
  AFTER INSERT OR UPDATE OR DELETE ON chat_sessions
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

CREATE TRIGGER trg_refresh_user_activity_chat_messages
  AFTER INSERT OR UPDATE OR DELETE ON chat_messages
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

CREATE TRIGGER trg_refresh_user_activity_projects
  AFTER INSERT OR UPDATE OR DELETE ON projects
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

CREATE TRIGGER trg_refresh_user_activity_documents
  AFTER INSERT OR UPDATE OR DELETE ON documents
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

-- Recreate triggers for project statistics refresh
CREATE TRIGGER trg_refresh_project_stats_documents
  AFTER INSERT OR UPDATE OR DELETE ON documents
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics();

CREATE TRIGGER trg_refresh_project_stats_chunks
  AFTER INSERT OR UPDATE OR DELETE ON document_chunks
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics();

CREATE TRIGGER trg_refresh_project_stats_knowledge_spaces
  AFTER INSERT OR UPDATE OR DELETE ON knowledge_spaces
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics(); 