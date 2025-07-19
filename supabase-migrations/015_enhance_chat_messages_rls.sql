-- Enhance Row Level Security policies and optimizations for chat_messages table
-- This migration improves security, performance, and data integrity

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

-- Create trigger for automatic updated_at timestamp updates
-- Note: chat_messages doesn't have updated_at column, but we can add it if needed
-- For now, we'll create a trigger to track message modifications

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

-- Create a function to get message count per session (useful for analytics)
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

-- Create a function to get recent messages for a user (useful for dashboard)
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