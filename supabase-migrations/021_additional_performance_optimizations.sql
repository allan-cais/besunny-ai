-- Additional Performance Optimizations
-- This migration addresses additional performance improvements beyond RLS optimization

-- ============================================================================
-- QUERY OPTIMIZATION SETTINGS
-- ============================================================================

-- Set work_mem for better query performance (adjust based on your plan)
-- This helps with sorting and hash operations
ALTER SYSTEM SET work_mem = '256MB';

-- Set shared_buffers to 25% of available RAM (typical recommendation)
-- This caches frequently accessed data
ALTER SYSTEM SET shared_buffers = '256MB';

-- Set effective_cache_size to 75% of available RAM
-- This helps the query planner make better decisions
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Optimize random_page_cost for SSD storage
ALTER SYSTEM SET random_page_cost = 1.1;

-- Set effective_io_concurrency for better I/O performance
ALTER SYSTEM SET effective_io_concurrency = 200;

-- ============================================================================
-- CONNECTION POOLING OPTIMIZATIONS
-- ============================================================================

-- Set max_connections (adjust based on your plan limits)
ALTER SYSTEM SET max_connections = 100;

-- Set shared_preload_libraries for connection pooling
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- ============================================================================
-- STATISTICS AND MONITORING
-- ============================================================================

-- Enable pg_stat_statements for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set track_activities for better monitoring
ALTER SYSTEM SET track_activities = on;

-- Set track_counts for statistics collection
ALTER SYSTEM SET track_counts = on;

-- Set track_io_timing for I/O performance monitoring
ALTER SYSTEM SET track_io_timing = on;

-- Set track_functions for function call monitoring
ALTER SYSTEM SET track_functions = all;

-- ============================================================================
-- WAL AND CHECKPOINT OPTIMIZATIONS
-- ============================================================================

-- Optimize checkpoint settings
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET max_wal_size = '1GB';
ALTER SYSTEM SET min_wal_size = '80MB';

-- ============================================================================
-- AUTOVACUUM OPTIMIZATIONS
-- ============================================================================

-- Optimize autovacuum settings for better performance
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.2;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.1;

-- ============================================================================
-- ADDITIONAL PERFORMANCE INDEXES
-- ============================================================================

-- Full-text search indexes for better text search performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_content_fts ON chat_messages USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_documents_title_fts ON documents USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_content_fts ON documents USING gin(to_tsvector('english', content));

-- JSONB indexes for better JSON query performance
CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_chat_messages_metadata_gin ON chat_messages USING gin(metadata);

-- Partial indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(user_id, created_at) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_meetings_upcoming ON meetings(user_id, start_time) WHERE start_time > now();
CREATE INDEX IF NOT EXISTS idx_documents_recent ON documents(project_id, created_at) WHERE created_at > now() - interval '30 days';

-- ============================================================================
-- MATERIALIZED VIEWS FOR COMPLEX QUERIES
-- ============================================================================

-- Create materialized view for user activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_summary AS
SELECT 
  u.id as user_id,
  u.email,
  COUNT(DISTINCT cs.id) as chat_sessions_count,
  COUNT(DISTINCT cm.id) as messages_count,
  COUNT(DISTINCT p.id) as projects_count,
  COUNT(DISTINCT d.id) as documents_count,
  MAX(cs.created_at) as last_chat_activity,
  MAX(p.created_at) as last_project_activity
FROM users u
LEFT JOIN chat_sessions cs ON u.id = cs.user_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
LEFT JOIN projects p ON u.id = p.user_id
LEFT JOIN documents d ON p.id = d.project_id
GROUP BY u.id, u.email;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_activity_summary_user_id ON user_activity_summary(user_id);

-- Create materialized view for project statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS project_statistics AS
SELECT 
  p.id as project_id,
  p.name as project_name,
  p.user_id,
  COUNT(DISTINCT d.id) as documents_count,
  COUNT(DISTINCT dc.id) as chunks_count,
  COUNT(DISTINCT ks.id) as knowledge_spaces_count,
  SUM(dc.token_count) as total_tokens,
  MAX(d.created_at) as last_document_activity
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN knowledge_spaces ks ON p.id = ks.project_id
GROUP BY p.id, p.name, p.user_id;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_statistics_project_id ON project_statistics(project_id);

-- ============================================================================
-- FUNCTION OPTIMIZATIONS
-- ============================================================================

-- Create optimized function for user project access check
CREATE OR REPLACE FUNCTION user_has_project_access(project_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM projects 
    WHERE id = project_uuid AND user_id = (SELECT auth.uid())
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Create optimized function for user document access check
CREATE OR REPLACE FUNCTION user_has_document_access(document_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS(
    SELECT 1 FROM documents d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = document_uuid AND p.user_id = (SELECT auth.uid())
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY user_activity_summary;
  REFRESH MATERIALIZED VIEW CONCURRENTLY project_statistics;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- TRIGGERS FOR MATERIALIZED VIEW REFRESH
-- ============================================================================

-- Create function to refresh user activity summary
CREATE OR REPLACE FUNCTION refresh_user_activity_summary()
RETURNS TRIGGER AS $$
BEGIN
  -- Refresh the materialized view asynchronously
  PERFORM pg_notify('refresh_user_activity', '');
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for user activity summary refresh
CREATE TRIGGER trg_refresh_user_activity_chat_sessions
  AFTER INSERT OR UPDATE OR DELETE ON chat_sessions
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

CREATE TRIGGER trg_refresh_user_activity_chat_messages
  AFTER INSERT OR UPDATE OR DELETE ON chat_messages
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

CREATE TRIGGER trg_refresh_user_activity_projects
  AFTER INSERT OR UPDATE OR DELETE ON projects
  FOR EACH ROW EXECUTE FUNCTION refresh_user_activity_summary();

-- Create function to refresh project statistics
CREATE OR REPLACE FUNCTION refresh_project_statistics()
RETURNS TRIGGER AS $$
BEGIN
  -- Refresh the materialized view asynchronously
  PERFORM pg_notify('refresh_project_stats', '');
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for project statistics refresh
CREATE TRIGGER trg_refresh_project_stats_documents
  AFTER INSERT OR UPDATE OR DELETE ON documents
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics();

CREATE TRIGGER trg_refresh_project_stats_chunks
  AFTER INSERT OR UPDATE OR DELETE ON document_chunks
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics();

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant execute permissions on utility functions
GRANT EXECUTE ON FUNCTION user_has_project_access(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION user_has_document_access(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION refresh_performance_views() TO service_role;

-- Grant select permissions on materialized views
GRANT SELECT ON user_activity_summary TO authenticated;
GRANT SELECT ON project_statistics TO authenticated;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON MATERIALIZED VIEW user_activity_summary IS 'Cached view of user activity statistics for performance';
COMMENT ON MATERIALIZED VIEW project_statistics IS 'Cached view of project statistics for performance';
COMMENT ON FUNCTION user_has_project_access(UUID) IS 'Optimized function to check if user has access to a project';
COMMENT ON FUNCTION user_has_document_access(UUID) IS 'Optimized function to check if user has access to a document';
COMMENT ON FUNCTION refresh_performance_views() IS 'Function to refresh all performance materialized views';

-- ============================================================================
-- RELOAD CONFIGURATION
-- ============================================================================

-- Reload the configuration
SELECT pg_reload_conf(); 