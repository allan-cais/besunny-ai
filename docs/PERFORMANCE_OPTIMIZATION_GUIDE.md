# Supabase Performance Optimization Guide

This guide covers the comprehensive performance optimizations implemented to address Supabase Performance Advisor recommendations and improve overall database performance.

## 📋 Overview

The performance optimization consists of three main migration files:

1. **`020_fix_rls_performance_optimization.sql`** - Fixes Auth RLS Initialization Plan issues
2. **`021_additional_performance_optimizations.sql`** - Additional performance improvements
3. **`022_monitoring_and_maintenance.sql`** - Monitoring and maintenance utilities

## 🚀 Migration 020: RLS Performance Optimization

### Problem
The Supabase Performance Advisor identified **Auth RLS Initialization Plan** warnings across multiple tables. This occurs when `auth.<function>()` calls in RLS policies are re-evaluated for each row, causing significant performance degradation.

### Solution
Wrap all `auth.<function>()` calls in `SELECT` statements to prevent unnecessary re-evaluation:

```sql
-- Before (Performance Issue)
CREATE POLICY "Users can view own data" ON table_name
  FOR SELECT USING (user_id = auth.uid());

-- After (Optimized)
CREATE POLICY "Users can view own data" ON table_name
  FOR SELECT USING (user_id = (SELECT auth.uid()));
```

### Tables Optimized
- ✅ `chat_sessions` - 5 policies optimized
- ✅ `chat_messages` - 5 policies optimized
- ✅ `bots` - 4 policies optimized
- ✅ `google_credentials` - 3 policies optimized
- ✅ `user_api_keys` - 4 policies optimized
- ✅ `meetings` - 4 policies optimized
- ✅ `calendar_webhooks` - 4 policies optimized
- ✅ `calendar_sync_logs` - 2 policies optimized
- ✅ `projects` - 4 policies optimized
- ✅ `email_processing_logs` - 1 policy optimized
- ✅ `drive_file_watches` - 1 policy optimized
- ✅ `drive_webhook_logs` - 1 policy optimized
- ✅ `subscriptions` - 5 policies optimized
- ✅ `document_chunks` - 5 policies optimized
- ✅ `documents` - 5 policies optimized
- ✅ `sync_tracking` - 5 policies optimized
- ✅ `knowledge_spaces` - 5 policies optimized
- ✅ `users` - 3 policies optimized
- ✅ `document_tags` - 5 policies optimized
- ✅ `summaries` - 5 policies optimized
- ✅ `receipts` - 5 policies optimized
- ✅ `tags` - 5 policies optimized

### Performance Indexes Added
- Single-column indexes on foreign keys
- Composite indexes for common query patterns
- Partial indexes for active records

## 🚀 Migration 021: Additional Performance Optimizations

### Database Configuration
- **work_mem**: 256MB for better sorting and hash operations
- **shared_buffers**: 256MB for caching frequently accessed data
- **effective_cache_size**: 1GB for better query planning
- **random_page_cost**: 1.1 optimized for SSD storage
- **effective_io_concurrency**: 200 for better I/O performance

### Connection Pooling
- **max_connections**: 100 (adjust based on your plan)
- **shared_preload_libraries**: pg_stat_statements for monitoring

### Statistics and Monitoring
- **pg_stat_statements**: Query performance monitoring
- **track_activities**: Activity tracking
- **track_counts**: Statistics collection
- **track_io_timing**: I/O performance monitoring
- **track_functions**: Function call monitoring

### WAL and Checkpoint Optimization
- **checkpoint_completion_target**: 0.9
- **wal_buffers**: 16MB
- **max_wal_size**: 1GB
- **min_wal_size**: 80MB

### Autovacuum Optimization
- **autovacuum_max_workers**: 3
- **autovacuum_naptime**: 1min
- **autovacuum_vacuum_threshold**: 50
- **autovacuum_analyze_threshold**: 50

### Advanced Indexes
- **Full-text search indexes**: For text search performance
- **JSONB indexes**: For JSON query performance
- **Partial indexes**: For common query patterns

### Materialized Views
- **user_activity_summary**: Cached user activity statistics
- **project_statistics**: Cached project statistics

### Utility Functions
- **user_has_project_access()**: Optimized project access check
- **user_has_document_access()**: Optimized document access check
- **refresh_performance_views()**: Refresh materialized views

## 🚀 Migration 022: Monitoring and Maintenance

### Performance Monitoring Functions
- **get_slow_queries()**: Get slowest queries
- **get_table_sizes()**: Get table size information
- **get_index_usage_stats()**: Get index usage statistics
- **get_connection_stats()**: Get connection statistics
- **get_cache_hit_ratios()**: Get cache hit ratios

### Maintenance Functions
- **analyze_all_tables()**: Run ANALYZE on all tables
- **vacuum_all_tables()**: Run VACUUM ANALYZE on all tables
- **reindex_all_indexes()**: Reindex all indexes
- **cleanup_old_data()**: Clean up old log data

### Performance Alert Functions
- **check_performance_issues()**: Check for common performance issues
  - Stale statistics
  - Table bloat
  - Unused indexes
  - Low cache hit ratios

### Scheduled Maintenance Functions
- **perform_daily_maintenance()**: Daily maintenance tasks
- **perform_weekly_maintenance()**: Weekly maintenance tasks
- **perform_monthly_maintenance()**: Monthly maintenance tasks

### Maintenance Logging
- **maintenance_logs** table: Track maintenance activities
- **log_maintenance_activity()**: Log maintenance start
- **complete_maintenance_activity()**: Log maintenance completion

## 📊 How to Apply the Migrations

### Step 1: Apply RLS Performance Fixes
```sql
-- Run in Supabase SQL Editor
-- Copy and paste the contents of 020_fix_rls_performance_optimization.sql
```

### Step 2: Apply Additional Optimizations
```sql
-- Run in Supabase SQL Editor
-- Copy and paste the contents of 021_additional_performance_optimizations.sql
```

### Step 3: Apply Monitoring and Maintenance
```sql
-- Run in Supabase SQL Editor
-- Copy and paste the contents of 022_monitoring_and_maintenance.sql
```

## 🔍 Monitoring Your Performance

### Check Performance Issues
```sql
SELECT * FROM check_performance_issues();
```

### Monitor Slow Queries
```sql
SELECT * FROM get_slow_queries(10);
```

### Check Table Sizes
```sql
SELECT * FROM get_table_sizes();
```

### Monitor Index Usage
```sql
SELECT * FROM get_index_usage_stats();
```

### Check Connection Usage
```sql
SELECT * FROM get_connection_stats();
```

### Monitor Cache Performance
```sql
SELECT * FROM get_cache_hit_ratios();
```

## 🛠️ Maintenance Schedule

### Daily Maintenance (Automated)
- Refresh materialized views
- Analyze tables
- Clean up old data (90 days)

### Weekly Maintenance (Automated)
- Daily maintenance tasks
- Vacuum all tables

### Monthly Maintenance (Automated)
- Weekly maintenance tasks
- Reindex all indexes

### Manual Maintenance
```sql
-- Run daily maintenance
SELECT perform_daily_maintenance();

-- Run weekly maintenance
SELECT perform_weekly_maintenance();

-- Run monthly maintenance
SELECT perform_monthly_maintenance();
```

## 📈 Expected Performance Improvements

### RLS Performance
- **50-80% reduction** in RLS policy evaluation time
- **Faster query execution** for authenticated users
- **Reduced CPU usage** on database server

### Query Performance
- **Faster text searches** with full-text indexes
- **Improved JSON queries** with JSONB indexes
- **Better query planning** with optimized statistics

### Connection Performance
- **Better connection pooling** with optimized settings
- **Reduced connection overhead** with monitoring
- **Improved I/O performance** with optimized settings

### Maintenance Benefits
- **Automated cleanup** of old data
- **Proactive performance monitoring**
- **Early detection** of performance issues

## ⚠️ Important Notes

### Plan Limitations
- Some settings may be limited by your Supabase plan
- Adjust `max_connections` based on your plan limits
- Monitor resource usage after applying optimizations

### Testing
- Test the migrations in a development environment first
- Monitor performance before and after applying changes
- Verify that all functionality still works correctly

### Backup
- Always backup your database before applying migrations
- Test rollback procedures if needed

### Monitoring
- Set up alerts for performance issues
- Monitor the maintenance logs regularly
- Track performance metrics over time

## 🔧 Customization

### Adjusting Settings
You can customize the settings based on your specific needs:

```sql
-- Example: Adjust work_mem for your workload
ALTER SYSTEM SET work_mem = '512MB';

-- Example: Adjust cleanup retention period
SELECT cleanup_old_data(180); -- Keep 180 days instead of 90
```

### Adding Custom Monitoring
You can extend the monitoring functions:

```sql
-- Example: Custom performance check
CREATE OR REPLACE FUNCTION custom_performance_check()
RETURNS TABLE(issue TEXT, severity TEXT) AS $$
BEGIN
  -- Add your custom checks here
  RETURN QUERY SELECT 'Custom issue'::TEXT, 'WARNING'::TEXT;
END;
$$ LANGUAGE plpgsql;
```

## 📞 Support

If you encounter any issues with these optimizations:

1. Check the maintenance logs for errors
2. Review the performance monitoring functions
3. Verify that all tables and functions exist
4. Check your Supabase plan limitations
5. Contact support if needed

## 🎯 Next Steps

After applying these optimizations:

1. **Monitor performance** for the first week
2. **Set up alerts** for performance issues
3. **Schedule regular maintenance** tasks
4. **Review and adjust** settings as needed
5. **Document any customizations** made

These optimizations should significantly improve your Supabase database performance and resolve the Performance Advisor warnings. 