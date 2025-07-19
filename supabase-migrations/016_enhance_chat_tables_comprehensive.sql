-- Comprehensive enhancement of chat_sessions and chat_messages tables
-- This migration improves security, performance, and data integrity for both tables

-- ============================================================================
-- CHAT_SESSIONS TABLE ENHANCEMENTS
-- ============================================================================

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

-- Create trigger for session activity tracking
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

-- Add constraints for data integrity
-- Ensure ended_at is after started_at
ALTER TABLE chat_sessions 
ADD CONSTRAINT check_chat_session_dates 
CHECK (ended_at IS NULL OR ended_at >= started_at);

-- Ensure session name is not empty if provided
ALTER TABLE chat_sessions 
ADD CONSTRAINT check_chat_session_name 
CHECK (name IS NULL OR length(trim(name)) > 0);

-- ============================================================================
-- CHAT_MESSAGES TABLE ENHANCEMENTS
-- ============================================================================

-- Note: RLS is already enabled on chat_messages table
-- Note: Basic RLS policies already exist, but we'll enhance them

-- Drop existing policies to recreate with improvements
DROP POLICY IF EXISTS "Users can view messages from own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can insert messages to own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can update messages from own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can delete messages from own sessions" ON chat_messages;

-- Create enhanced RLS policies for chat_messages
-- Users can only access messages from their own chat sessions
CREATE POLICY "Users can view messages from own sessions" ON chat_messages
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM chat_sessions 
      WHERE chat_sessions.id = chat_messages.session_id 
      AND chat_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert messages to own sessions" ON chat_messages
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM chat_sessions 
      WHERE chat_sessions.id = chat_messages.session_id 
      AND chat_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update messages from own sessions" ON chat_messages
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM chat_sessions 
      WHERE chat_sessions.id = chat_messages.session_id 
      AND chat_sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete messages from own sessions" ON chat_messages
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM chat_sessions 
      WHERE chat_sessions.id = chat_messages.session_id 
      AND chat_sessions.user_id = auth.uid()
    )
  );

-- Service role policy for backend operations
CREATE POLICY "Service role can manage chat messages" ON chat_messages
  FOR ALL USING (auth.role() = 'service_role');

-- Note: The following indexes already exist in the original migration:
-- - idx_chat_messages_session_id (for session lookups)
-- - idx_chat_messages_created_at (for chronological ordering)

-- Additional indexes for better performance
-- Index for role-based filtering (user, assistant, system)
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);

-- Index for finding messages by role within a session
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_role ON chat_messages(session_id, role);

-- Index for chronological ordering within sessions
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- Index for finding recent messages across all sessions
CREATE INDEX IF NOT EXISTS idx_chat_messages_recent ON chat_messages(created_at DESC);

-- Index for finding messages with used_chunks (for AI context)
CREATE INDEX IF NOT EXISTS idx_chat_messages_has_chunks ON chat_messages(session_id) WHERE used_chunks IS NOT NULL AND array_length(used_chunks, 1) > 0;

-- Composite index for common query patterns (session + role + date)
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_role_date ON chat_messages(session_id, role, created_at);

-- Create trigger for message activity tracking
CREATE OR REPLACE FUNCTION update_chat_messages_activity()
RETURNS TRIGGER AS $$
BEGIN
  -- Track when messages are modified (if we add updated_at later)
  -- For now, just ensure created_at is set properly
  IF NEW.created_at IS NULL THEN
    NEW.created_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_chat_messages_activity
BEFORE INSERT OR UPDATE ON chat_messages
FOR EACH ROW
EXECUTE FUNCTION update_chat_messages_activity();

-- Add constraints for data integrity
-- Ensure role is one of the allowed values
ALTER TABLE chat_messages 
ADD CONSTRAINT check_chat_message_role 
CHECK (role IN ('user', 'assistant', 'system'));

-- Ensure message is not empty if provided
ALTER TABLE chat_messages 
ADD CONSTRAINT check_chat_message_content 
CHECK (message IS NULL OR length(trim(message)) > 0);

-- Ensure used_chunks array is not empty if provided
ALTER TABLE chat_messages 
ADD CONSTRAINT check_chat_message_chunks 
CHECK (used_chunks IS NULL OR array_length(used_chunks, 1) > 0);

-- Add constraint to ensure session_id is not null
ALTER TABLE chat_messages 
ADD CONSTRAINT check_chat_message_session 
CHECK (session_id IS NOT NULL);

-- ============================================================================
-- UTILITY FUNCTIONS FOR CHAT ANALYTICS
-- ============================================================================

-- Function to get message count per session (useful for analytics)
CREATE OR REPLACE FUNCTION get_session_message_count(session_uuid UUID)
RETURNS INTEGER AS $$
BEGIN
  RETURN (
    SELECT COUNT(*) 
    FROM chat_messages 
    WHERE session_id = session_uuid
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get recent messages for a user (useful for dashboard)
CREATE OR REPLACE FUNCTION get_user_recent_messages(user_uuid UUID, limit_count INTEGER DEFAULT 10)
RETURNS TABLE(
  message_id UUID,
  session_id UUID,
  role TEXT,
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    cm.id,
    cm.session_id,
    cm.role,
    cm.message,
    cm.created_at
  FROM chat_messages cm
  JOIN chat_sessions cs ON cm.session_id = cs.id
  WHERE cs.user_id = user_uuid
  ORDER BY cm.created_at DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get active sessions for a user
CREATE OR REPLACE FUNCTION get_user_active_sessions(user_uuid UUID)
RETURNS TABLE(
  session_id UUID,
  session_name TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  message_count INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    cs.id,
    cs.name,
    cs.started_at,
    get_session_message_count(cs.id) as message_count
  FROM chat_sessions cs
  WHERE cs.user_id = user_uuid
    AND cs.ended_at IS NULL
  ORDER BY cs.started_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get session statistics for a user
CREATE OR REPLACE FUNCTION get_user_session_stats(user_uuid UUID)
RETURNS TABLE(
  total_sessions INTEGER,
  active_sessions INTEGER,
  total_messages INTEGER,
  avg_messages_per_session NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN cs.ended_at IS NULL THEN cs.id END) as active_sessions,
    COUNT(cm.id) as total_messages,
    ROUND(AVG(session_counts.message_count), 2) as avg_messages_per_session
  FROM chat_sessions cs
  LEFT JOIN chat_messages cm ON cs.id = cm.session_id
  LEFT JOIN (
    SELECT 
      session_id,
      COUNT(*) as message_count
    FROM chat_messages
    GROUP BY session_id
  ) session_counts ON cs.id = session_counts.session_id
  WHERE cs.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 