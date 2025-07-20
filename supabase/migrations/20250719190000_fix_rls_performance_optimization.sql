-- Fix RLS Performance Optimization
-- This migration addresses Auth RLS Initialization Plan performance issues
-- Based on actual remote database schema inspection

-- ============================================================================
-- AGENT LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Service role can manage agent logs" ON agent_logs;

-- Create optimized policies (service role only)
CREATE POLICY "Service role can manage agent logs" ON agent_logs
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- BOTS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own bots" ON bots;
DROP POLICY IF EXISTS "Users can insert own bots" ON bots;
DROP POLICY IF EXISTS "Users can update own bots" ON bots;
DROP POLICY IF EXISTS "Users can delete own bots" ON bots;

-- Create optimized policies
CREATE POLICY "Users can view own bots" ON bots
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own bots" ON bots
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own bots" ON bots
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own bots" ON bots
  FOR DELETE USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- CALENDAR SYNC LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own sync logs" ON calendar_sync_logs;
DROP POLICY IF EXISTS "Users can insert own sync logs" ON calendar_sync_logs;

-- Create optimized policies
CREATE POLICY "Users can view own sync logs" ON calendar_sync_logs
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own sync logs" ON calendar_sync_logs
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

-- ============================================================================
-- CALENDAR WEBHOOKS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own webhooks" ON calendar_webhooks;
DROP POLICY IF EXISTS "Users can insert own webhooks" ON calendar_webhooks;
DROP POLICY IF EXISTS "Users can update own webhooks" ON calendar_webhooks;
DROP POLICY IF EXISTS "Users can delete own webhooks" ON calendar_webhooks;

-- Create optimized policies
CREATE POLICY "Users can view own webhooks" ON calendar_webhooks
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own webhooks" ON calendar_webhooks
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own webhooks" ON calendar_webhooks
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own webhooks" ON calendar_webhooks
  FOR DELETE USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- CHAT SESSIONS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can read their own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can insert their own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can update their own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can delete their own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Service role can manage chat sessions" ON chat_sessions;

-- Create optimized policies
CREATE POLICY "Users can read their own chat sessions" ON chat_sessions
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert their own chat sessions" ON chat_sessions
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update their own chat sessions" ON chat_sessions
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete their own chat sessions" ON chat_sessions
  FOR DELETE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage chat sessions" ON chat_sessions
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- CHAT MESSAGES TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can read messages from their own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can insert messages to their own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can update messages from their own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Users can delete messages from their own sessions" ON chat_messages;
DROP POLICY IF EXISTS "Service role can manage chat messages" ON chat_messages;

-- Create optimized policies
CREATE POLICY "Users can read messages from their own sessions" ON chat_messages
  FOR SELECT USING (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert messages to their own sessions" ON chat_messages
  FOR INSERT WITH CHECK (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update messages from their own sessions" ON chat_messages
  FOR UPDATE USING (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete messages from their own sessions" ON chat_messages
  FOR DELETE USING (
    session_id IN (
      SELECT id FROM chat_sessions WHERE user_id = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage chat messages" ON chat_messages
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DOCUMENT CHUNKS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view chunks in their projects" ON document_chunks;
DROP POLICY IF EXISTS "Users can insert chunks in their projects" ON document_chunks;
DROP POLICY IF EXISTS "Users can update chunks in their projects" ON document_chunks;
DROP POLICY IF EXISTS "Users can delete chunks in their projects" ON document_chunks;
DROP POLICY IF EXISTS "Service role can manage document chunks" ON document_chunks;

-- Create optimized policies
CREATE POLICY "Users can view chunks in their projects" ON document_chunks
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert chunks in their projects" ON document_chunks
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update chunks in their projects" ON document_chunks
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete chunks in their projects" ON document_chunks
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage document chunks" ON document_chunks
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DOCUMENT TAGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view document tags in their projects" ON document_tags;
DROP POLICY IF EXISTS "Users can insert document tags in their projects" ON document_tags;
DROP POLICY IF EXISTS "Users can update document tags in their projects" ON document_tags;
DROP POLICY IF EXISTS "Users can delete document tags in their projects" ON document_tags;
DROP POLICY IF EXISTS "Service role can manage document tags" ON document_tags;

-- Create optimized policies
CREATE POLICY "Users can view document tags in their projects" ON document_tags
  FOR SELECT USING (
    document_id IN (
      SELECT id FROM documents WHERE project_id IN (
        SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
      )
    )
  );

CREATE POLICY "Users can insert document tags in their projects" ON document_tags
  FOR INSERT WITH CHECK (
    document_id IN (
      SELECT id FROM documents WHERE project_id IN (
        SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
      )
    )
  );

CREATE POLICY "Users can update document tags in their projects" ON document_tags
  FOR UPDATE USING (
    document_id IN (
      SELECT id FROM documents WHERE project_id IN (
        SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
      )
    )
  );

CREATE POLICY "Users can delete document tags in their projects" ON document_tags
  FOR DELETE USING (
    document_id IN (
      SELECT id FROM documents WHERE project_id IN (
        SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
      )
    )
  );

CREATE POLICY "Service role can manage document tags" ON document_tags
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view documents in their projects" ON documents;
DROP POLICY IF EXISTS "Users can insert documents in their projects" ON documents;
DROP POLICY IF EXISTS "Users can update documents in their projects" ON documents;
DROP POLICY IF EXISTS "Users can delete documents in their projects" ON documents;
DROP POLICY IF EXISTS "Service role can manage documents" ON documents;

-- Create optimized policies
CREATE POLICY "Users can view documents in their projects" ON documents
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert documents in their projects" ON documents
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update documents in their projects" ON documents
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete documents in their projects" ON documents
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage documents" ON documents
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DRIVE FILE WATCHES TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own drive file watches" ON drive_file_watches;
DROP POLICY IF EXISTS "Service role can manage drive file watches" ON drive_file_watches;

-- Create optimized policies
CREATE POLICY "Users can view own drive file watches" ON drive_file_watches
  FOR SELECT USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage drive file watches" ON drive_file_watches
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- DRIVE WEBHOOK LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own drive webhook logs" ON drive_webhook_logs;
DROP POLICY IF EXISTS "Service role can manage drive webhook logs" ON drive_webhook_logs;

-- Create optimized policies
CREATE POLICY "Users can view own drive webhook logs" ON drive_webhook_logs
  FOR SELECT USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage drive webhook logs" ON drive_webhook_logs
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- EMAIL PROCESSING LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own email processing logs" ON email_processing_logs;
DROP POLICY IF EXISTS "Service role can manage email processing logs" ON email_processing_logs;

-- Create optimized policies
CREATE POLICY "Users can view own email processing logs" ON email_processing_logs
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage email processing logs" ON email_processing_logs
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- GOOGLE CREDENTIALS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Authenticated users can select own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Users can delete own google credentials" ON google_credentials;

-- Create optimized policies
CREATE POLICY "Users can view own google credentials" ON google_credentials
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Authenticated users can select own google credentials" ON google_credentials
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own google credentials" ON google_credentials
  FOR DELETE USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- KNOWLEDGE SPACES TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view knowledge spaces in their projects" ON knowledge_spaces;
DROP POLICY IF EXISTS "Users can insert knowledge spaces in their projects" ON knowledge_spaces;
DROP POLICY IF EXISTS "Users can update knowledge spaces in their projects" ON knowledge_spaces;
DROP POLICY IF EXISTS "Users can delete knowledge spaces in their projects" ON knowledge_spaces;
DROP POLICY IF EXISTS "Service role can manage knowledge spaces" ON knowledge_spaces;

-- Create optimized policies
CREATE POLICY "Users can view knowledge spaces in their projects" ON knowledge_spaces
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert knowledge spaces in their projects" ON knowledge_spaces
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update knowledge spaces in their projects" ON knowledge_spaces
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete knowledge spaces in their projects" ON knowledge_spaces
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage knowledge spaces" ON knowledge_spaces
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- MEETINGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can insert own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can update own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can delete own meetings" ON meetings;
DROP POLICY IF EXISTS "Service role can manage meetings" ON meetings;

-- Create optimized policies
CREATE POLICY "Users can view own meetings" ON meetings
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own meetings" ON meetings
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own meetings" ON meetings
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own meetings" ON meetings
  FOR DELETE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage meetings" ON meetings
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- PROJECT METADATA TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view metadata in their projects" ON project_metadata;
DROP POLICY IF EXISTS "Users can insert metadata in their projects" ON project_metadata;
DROP POLICY IF EXISTS "Users can update metadata in their projects" ON project_metadata;
DROP POLICY IF EXISTS "Users can delete metadata in their projects" ON project_metadata;
DROP POLICY IF EXISTS "Service role can manage project metadata" ON project_metadata;

-- Create optimized policies
CREATE POLICY "Users can view metadata in their projects" ON project_metadata
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert metadata in their projects" ON project_metadata
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update metadata in their projects" ON project_metadata
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete metadata in their projects" ON project_metadata
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage project metadata" ON project_metadata
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
DROP POLICY IF EXISTS "Users can insert own projects" ON projects;
DROP POLICY IF EXISTS "Users can update own projects" ON projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
DROP POLICY IF EXISTS "Service role can manage projects" ON projects;

-- Create optimized policies
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can insert own projects" ON projects
  FOR INSERT WITH CHECK (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Service role can manage projects" ON projects
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- RECEIPTS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view receipts in their projects" ON receipts;
DROP POLICY IF EXISTS "Users can insert receipts in their projects" ON receipts;
DROP POLICY IF EXISTS "Users can update receipts in their projects" ON receipts;
DROP POLICY IF EXISTS "Users can delete receipts in their projects" ON receipts;
DROP POLICY IF EXISTS "Service role can manage receipts" ON receipts;

-- Create optimized policies
CREATE POLICY "Users can view receipts in their projects" ON receipts
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert receipts in their projects" ON receipts
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update receipts in their projects" ON receipts
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete receipts in their projects" ON receipts
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage receipts" ON receipts
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Users can insert own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Users can update own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Users can delete own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Service role can manage subscriptions" ON subscriptions;

-- Create optimized policies
CREATE POLICY "Users can view own subscriptions" ON subscriptions
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own subscriptions" ON subscriptions
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own subscriptions" ON subscriptions
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own subscriptions" ON subscriptions
  FOR DELETE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage subscriptions" ON subscriptions
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- SUMMARIES TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view summaries in their projects" ON summaries;
DROP POLICY IF EXISTS "Users can insert summaries in their projects" ON summaries;
DROP POLICY IF EXISTS "Users can update summaries in their projects" ON summaries;
DROP POLICY IF EXISTS "Users can delete summaries in their projects" ON summaries;
DROP POLICY IF EXISTS "Service role can manage summaries" ON summaries;

-- Create optimized policies
CREATE POLICY "Users can view summaries in their projects" ON summaries
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can insert summaries in their projects" ON summaries
  FOR INSERT WITH CHECK (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can update summaries in their projects" ON summaries
  FOR UPDATE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete summaries in their projects" ON summaries
  FOR DELETE USING (
    project_id IN (
      SELECT id FROM projects WHERE created_by = (SELECT auth.uid())
    )
  );

CREATE POLICY "Service role can manage summaries" ON summaries
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- SYNC TRACKING TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own sync tracking" ON sync_tracking;
DROP POLICY IF EXISTS "Users can insert own sync tracking" ON sync_tracking;
DROP POLICY IF EXISTS "Users can update own sync tracking" ON sync_tracking;
DROP POLICY IF EXISTS "Users can delete own sync tracking" ON sync_tracking;
DROP POLICY IF EXISTS "Service role can manage sync tracking" ON sync_tracking;

-- Create optimized policies
CREATE POLICY "Users can view own sync tracking" ON sync_tracking
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own sync tracking" ON sync_tracking
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own sync tracking" ON sync_tracking
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own sync tracking" ON sync_tracking
  FOR DELETE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage sync tracking" ON sync_tracking
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- TAGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own tags" ON tags;
DROP POLICY IF EXISTS "Users can insert own tags" ON tags;
DROP POLICY IF EXISTS "Users can update own tags" ON tags;
DROP POLICY IF EXISTS "Users can delete own tags" ON tags;
DROP POLICY IF EXISTS "Service role can manage tags" ON tags;

-- Create optimized policies
CREATE POLICY "Users can view own tags" ON tags
  FOR SELECT USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can insert own tags" ON tags
  FOR INSERT WITH CHECK (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can update own tags" ON tags
  FOR UPDATE USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can delete own tags" ON tags
  FOR DELETE USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Service role can manage tags" ON tags
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- USER API KEYS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Allow user to read their api keys" ON user_api_keys;
DROP POLICY IF EXISTS "Allow user to insert their api keys" ON user_api_keys;
DROP POLICY IF EXISTS "Allow user to update their api keys" ON user_api_keys;
DROP POLICY IF EXISTS "Allow user to delete their api keys" ON user_api_keys;

-- Create optimized policies
CREATE POLICY "Allow user to read their api keys" ON user_api_keys
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Allow user to insert their api keys" ON user_api_keys
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Allow user to update their api keys" ON user_api_keys
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Allow user to delete their api keys" ON user_api_keys
  FOR DELETE USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- USERS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Service role can manage users" ON users;

-- Create optimized policies
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (id = (SELECT auth.uid()));

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (id = (SELECT auth.uid()));

CREATE POLICY "Service role can manage users" ON users
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Single-column indexes for user/project identification
-- Only keep user_id indexes for tables that actually have a user_id column
CREATE INDEX IF NOT EXISTS idx_bots_user_id ON bots(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_logs_user_id ON calendar_sync_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_user_id ON calendar_webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_google_credentials_user_id ON google_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_tracking_user_id ON sync_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_user ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_documents_project_created ON documents(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_created ON document_chunks(document_id, created_at);
CREATE INDEX IF NOT EXISTS idx_meetings_user_created ON meetings(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(user_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_active ON drive_file_watches(document_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_documents_watch_active ON documents(project_id) WHERE watch_active = true;
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_active ON calendar_webhooks(user_id) WHERE is_active = true; 