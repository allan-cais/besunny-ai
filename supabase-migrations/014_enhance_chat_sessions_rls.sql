-- Enhance Row Level Security policies and optimizations for chat_sessions table
-- This migration improves security, performance, and data integrity

-- Note: RLS is already enabled on chat_sessions table
-- Note: Basic RLS policies already exist, but we'll enhance them

-- Drop existing policies to recreate with improvements
DROP POLICY IF EXISTS "Users can view own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can insert own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can update own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can delete own chat sessions" ON chat_sessions;

-- Create enhanced RLS policies for chat_sessions
CREATE POLICY "Users can view own chat sessions" ON chat_sessions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chat sessions" ON chat_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chat sessions" ON chat_sessions
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own chat sessions" ON chat_sessions
  FOR DELETE USING (auth.uid() = user_id);

-- Service role policy for backend operations
CREATE POLICY "Service role can manage chat sessions" ON chat_sessions
  FOR ALL USING (auth.role() = 'service_role');

-- Note: The following indexes already exist in the original migration:
-- - idx_chat_sessions_user_id (for RLS performance)
-- - idx_chat_sessions_project_id (for project filtering)

-- Additional indexes for better performance
-- Index for date range queries (started_at)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_started_at ON chat_sessions(started_at);

-- Index for finding active sessions (not ended)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_active ON chat_sessions(started_at) WHERE ended_at IS NULL;

-- Index for finding sessions by date range
CREATE INDEX IF NOT EXISTS idx_chat_sessions_date_range ON chat_sessions(started_at, ended_at);

-- Index for name searches (if sessions are named)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_name ON chat_sessions(name) WHERE name IS NOT NULL;

-- Composite index for common query patterns (user + project + date)
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_project_date ON chat_sessions(user_id, project_id, started_at);

-- Create trigger for automatic updated_at timestamp updates (if not exists)
-- Note: chat_sessions doesn't have updated_at column, but we can add it if needed
-- For now, we'll create a trigger to track session activity

CREATE OR REPLACE FUNCTION update_chat_sessions_activity()
RETURNS TRIGGER AS $$
BEGIN
  -- Update ended_at when session is marked as ended
  IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
    NEW.ended_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_chat_sessions_activity
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION update_chat_sessions_activity();

-- Add constraint to ensure ended_at is after started_at
ALTER TABLE chat_sessions 
ADD CONSTRAINT check_chat_session_dates 
CHECK (ended_at IS NULL OR ended_at >= started_at);

-- Add constraint to ensure session name is not empty if provided
ALTER TABLE chat_sessions 
ADD CONSTRAINT check_chat_session_name 
CHECK (name IS NULL OR length(trim(name)) > 0); 