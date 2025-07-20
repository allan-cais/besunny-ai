-- Additional Performance Optimizations
-- This migration addresses additional performance improvements beyond RLS optimization
-- Based on actual remote database schema inspection

-- ============================================================================
-- QUERY OPTIMIZATION SETTINGS
-- ============================================================================

-- Set work_mem for better query performance (adjust based on your plan)
-- This helps with sorting and hash operations
-- ALTER SYSTEM SET work_mem = '256MB'; -- Cannot run inside transaction block

-- Set shared_buffers to 25% of available RAM (typical recommendation)
-- This caches frequently accessed data
-- ALTER SYSTEM SET shared_buffers = '256MB'; -- Cannot run inside transaction block

-- Set effective_cache_size to 75% of available RAM
-- This helps the query planner make better decisions
-- ALTER SYSTEM SET effective_cache_size = '1GB'; -- Cannot run inside transaction block

-- Optimize random_page_cost for SSD storage
-- ALTER SYSTEM SET random_page_cost = 1.1; -- Cannot run inside transaction block

-- Set effective_io_concurrency for better I/O performance
-- ALTER SYSTEM SET effective_io_concurrency = 200; -- Cannot run inside transaction block

-- ============================================================================
-- CONNECTION POOLING OPTIMIZATIONS
-- ============================================================================

-- Set max_connections (adjust based on your plan limits)
-- ALTER SYSTEM SET max_connections = 100; -- Cannot run inside transaction block

-- Set shared_preload_libraries for connection pooling
-- ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements'; -- Cannot run inside transaction block

-- ============================================================================
-- STATISTICS AND MONITORING
-- ============================================================================

-- Enable pg_stat_statements for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Set track_activities for better monitoring
-- ALTER SYSTEM SET track_activities = on; -- Cannot run inside transaction block

-- Set track_counts for statistics collection
-- ALTER SYSTEM SET track_counts = on; -- Cannot run inside transaction block

-- Set track_io_timing for I/O performance monitoring
-- ALTER SYSTEM SET track_io_timing = on; -- Cannot run inside transaction block

-- ALTER SYSTEM SET track_functions = 'all'; -- Cannot run inside a transaction block; run manually as superuser if needed

-- ============================================================================
-- WAL AND CHECKPOINT OPTIMIZATIONS
-- ============================================================================

-- Optimize checkpoint settings
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9; -- Cannot run inside transaction block
-- ALTER SYSTEM SET wal_buffers = '16MB'; -- Cannot run inside transaction block
-- ALTER SYSTEM SET max_wal_size = '1GB'; -- Cannot run inside transaction block
-- ALTER SYSTEM SET min_wal_size = '80MB'; -- Cannot run inside transaction block

-- ============================================================================
-- AUTOVACUUM OPTIMIZATIONS
-- ============================================================================

-- Optimize autovacuum settings for better performance
-- ALTER SYSTEM SET autovacuum = on; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_max_workers = 3; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_naptime = '1min'; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_vacuum_threshold = 50; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_analyze_threshold = 50; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.2; -- Cannot run inside transaction block
-- ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.1; -- Cannot run inside transaction block

-- ============================================================================
-- ADDITIONAL PERFORMANCE INDEXES
-- ============================================================================

-- Full-text search indexes for better text search performance
-- Note: to_tsvector function is not IMMUTABLE, so these indexes cannot be created
-- Consider using trigram indexes instead for text search performance
-- CREATE INDEX IF NOT EXISTS idx_chat_messages_content_fts ON chat_messages USING gin(to_tsvector('english', message));
-- CREATE INDEX IF NOT EXISTS idx_documents_title_fts ON documents USING gin(to_tsvector('english', title));

-- JSONB indexes for better JSON query performance
-- Note: documents and chat_messages don't have metadata columns
-- Only document_chunks has a metadata column
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin ON document_chunks USING gin(metadata);

-- Partial indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(user_id, started_at) WHERE ended_at IS NULL;
-- Note: now() is not IMMUTABLE, so these partial indexes cannot be created
-- CREATE INDEX IF NOT EXISTS idx_meetings_upcoming ON meetings(user_id, start_time) WHERE start_time > now();
-- CREATE INDEX IF NOT EXISTS idx_documents_recent ON documents(project_id, created_at) WHERE created_at > now() - interval '30 days';

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
  MAX(cs.started_at) as last_chat_activity,
  MAX(p.created_at) as last_project_activity
FROM users u
LEFT JOIN chat_sessions cs ON u.id = cs.user_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
LEFT JOIN projects p ON u.id = p.created_by
LEFT JOIN documents d ON p.id = d.project_id
GROUP BY u.id, u.email;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_activity_summary_user_id ON user_activity_summary(user_id);

-- Create materialized view for project statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS project_statistics AS
SELECT 
  p.id as project_id,
  p.name as project_name,
  p.created_by as user_id,
  COUNT(DISTINCT d.id) as documents_count,
  COUNT(DISTINCT dc.id) as chunks_count,
  COUNT(DISTINCT ks.id) as knowledge_spaces_count,
  -- Note: document_chunks doesn't have token_count column
  -- SUM(dc.token_count) as total_tokens,
  MAX(d.created_at) as last_document_activity
FROM projects p
LEFT JOIN documents d ON p.id = d.project_id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN knowledge_spaces ks ON p.id = ks.project_id
GROUP BY p.id, p.name, p.created_by;

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
    WHERE id = project_uuid AND created_by = (SELECT auth.uid())
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
    WHERE d.id = document_uuid AND p.created_by = (SELECT auth.uid())
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

CREATE TRIGGER trg_refresh_user_activity_documents
  AFTER INSERT OR UPDATE OR DELETE ON documents
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

CREATE TRIGGER trg_refresh_project_stats_knowledge_spaces
  AFTER INSERT OR UPDATE OR DELETE ON knowledge_spaces
  FOR EACH ROW EXECUTE FUNCTION refresh_project_statistics();

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