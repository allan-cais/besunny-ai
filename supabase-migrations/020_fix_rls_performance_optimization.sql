-- Fix Auth RLS Initialization Plan Performance Issues
-- This migration optimizes RLS policies by wrapping auth function calls in SELECT statements
-- to prevent unnecessary re-evaluation for each row
-- Only includes tables that actually exist in the database

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
-- MEETINGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can insert own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can update own meetings" ON meetings;
DROP POLICY IF EXISTS "Users can delete own meetings" ON meetings;

-- Create optimized policies
CREATE POLICY "Users can view own meetings" ON meetings
  FOR SELECT USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can insert own meetings" ON meetings
  FOR INSERT WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own meetings" ON meetings
  FOR UPDATE USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can delete own meetings" ON meetings
  FOR DELETE USING (user_id = (SELECT auth.uid()));

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
-- PROJECTS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
DROP POLICY IF EXISTS "Users can insert own projects" ON projects;
DROP POLICY IF EXISTS "Users can update own projects" ON projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON projects;

-- Create optimized policies
CREATE POLICY "Users can view own projects" ON projects
  FOR SELECT USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can insert own projects" ON projects
  FOR INSERT WITH CHECK (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can update own projects" ON projects
  FOR UPDATE USING (created_by = (SELECT auth.uid()));

CREATE POLICY "Users can delete own projects" ON projects
  FOR DELETE USING (created_by = (SELECT auth.uid()));

-- ============================================================================
-- EMAIL PROCESSING LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own email processing logs" ON email_processing_logs;

-- Create optimized policies
CREATE POLICY "Users can view own email processing logs" ON email_processing_logs
  FOR SELECT USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- DRIVE FILE WATCHES TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own drive file watches" ON drive_file_watches;

-- Create optimized policies
CREATE POLICY "Users can view own drive file watches" ON drive_file_watches
  FOR SELECT USING (user_id = (SELECT auth.uid()));

-- ============================================================================
-- DRIVE WEBHOOK LOGS TABLE
-- ============================================================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own drive webhook logs" ON drive_webhook_logs;

-- Create optimized policies
CREATE POLICY "Users can view own drive webhook logs" ON drive_webhook_logs
  FOR SELECT USING (user_id = (SELECT auth.uid()));

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
-- PERFORMANCE INDEXES
-- ============================================================================

-- Add performance indexes for commonly queried columns
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_bots_user_id ON bots(user_id);
CREATE INDEX IF NOT EXISTS idx_google_credentials_user_id ON google_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_user_id ON calendar_webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_logs_user_id ON calendar_sync_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_user_id ON email_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_user_id ON drive_file_watches(user_id);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_user_id ON drive_webhook_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_created_by ON tags(created_by);

-- Composite indexes for better performance on common query patterns
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_user ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_meetings_user_created ON meetings(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(user_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_active ON drive_file_watches(user_id) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_calendar_webhooks_active ON calendar_webhooks(user_id) WHERE active = true; 