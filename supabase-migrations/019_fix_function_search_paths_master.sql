-- Master SQL file to fix all function search path mutable warnings
-- This migration adds explicit search_path settings to all functions for security

-- ============================================================================
-- 1. UPDATE TRIGGER FUNCTIONS
-- ============================================================================

-- Fix update_drive_file_watches_updated_at function
CREATE OR REPLACE FUNCTION update_drive_file_watches_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_subscriptions_updated_at function
CREATE OR REPLACE FUNCTION update_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_calendar_webhooks_updated_at function
CREATE OR REPLACE FUNCTION update_calendar_webhooks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_bots_updated_at function
CREATE OR REPLACE FUNCTION update_bots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_meetings_updated_at function
CREATE OR REPLACE FUNCTION update_meetings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_timestamp function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_next_poll_time function
CREATE OR REPLACE FUNCTION update_next_poll_time()
RETURNS TRIGGER AS $$
BEGIN
  NEW.next_poll_time = NOW() + INTERVAL '5 minutes';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_chat_sessions_activity function
CREATE OR REPLACE FUNCTION update_chat_sessions_activity()
RETURNS TRIGGER AS $$
BEGIN
  -- Update ended_at when session is marked as ended
  IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
    NEW.ended_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_chat_messages_activity function
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix update_username_set_at function
CREATE OR REPLACE FUNCTION update_username_set_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.username_set_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- ============================================================================
-- 2. UPDATE UTILITY FUNCTIONS
-- ============================================================================

-- Fix get_active_drive_file_watch function
CREATE OR REPLACE FUNCTION get_active_drive_file_watch(search_file_id TEXT)
RETURNS TABLE(
  id UUID,
  document_id UUID,
  project_id UUID,
  file_id TEXT,
  channel_id TEXT,
  resource_id TEXT,
  expiration TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dfw.id,
    dfw.document_id,
    dfw.project_id,
    dfw.file_id,
    dfw.channel_id,
    dfw.resource_id,
    dfw.expiration,
    dfw.is_active
  FROM drive_file_watches dfw
  WHERE dfw.file_id = search_file_id 
    AND dfw.is_active = TRUE
    AND dfw.expiration > NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix deactivate_expired_drive_watches function
CREATE OR REPLACE FUNCTION deactivate_expired_drive_watches()
RETURNS INTEGER AS $$
DECLARE
  affected_rows INTEGER;
BEGIN
  UPDATE drive_file_watches 
  SET is_active = FALSE, updated_at = NOW()
  WHERE expiration < NOW() AND is_active = TRUE;
  
  GET DIAGNOSTICS affected_rows = ROW_COUNT;
  
  -- Also update documents to reflect inactive watches
  UPDATE documents 
  SET watch_active = FALSE, updated_at = NOW()
  WHERE id IN (
    SELECT document_id FROM drive_file_watches 
    WHERE expiration < NOW() AND is_active = FALSE
  );
  
  RETURN affected_rows;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_document_by_channel_id function
CREATE OR REPLACE FUNCTION get_document_by_channel_id(search_channel_id TEXT)
RETURNS TABLE(
  document_id UUID,
  project_id UUID,
  file_id TEXT,
  title TEXT,
  status TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.id,
    d.project_id,
    d.file_id,
    d.title,
    d.status
  FROM documents d
  WHERE d.id::TEXT = search_channel_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_meetings_for_polling function
CREATE OR REPLACE FUNCTION get_meetings_for_polling()
RETURNS TABLE(
  id UUID,
  user_id UUID,
  attendee_bot_id UUID,
  bot_status TEXT,
  title TEXT,
  meeting_url TEXT,
  next_poll_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    m.id,
    m.user_id,
    m.attendee_bot_id,
    m.bot_status,
    m.title,
    m.meeting_url,
    m.next_poll_at
  FROM meetings m
  WHERE m.polling_enabled = TRUE
    AND m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW())
    AND m.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix auto_schedule_bot_for_virtual_email function
CREATE OR REPLACE FUNCTION auto_schedule_bot_for_virtual_email()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
DECLARE
  meeting_record RECORD;
BEGIN
  -- Find meetings that have virtual email attendees but no bot scheduled yet
  FOR meeting_record IN
    SELECT 
      m.id,
      m.title,
      m.meeting_url,
      m.start_time,
      m.end_time,
      m.user_id,
      m.google_calendar_event_id
    FROM meetings m
    WHERE m.auto_scheduled_via_email = TRUE
      AND m.bot_deployment_method = 'scheduled'
      AND m.bot_status = 'pending'
      AND m.meeting_url IS NOT NULL
      AND m.start_time > NOW() -- Only future meetings
  LOOP
    -- Update meeting to indicate bot is being scheduled
    UPDATE meetings 
    SET 
      bot_deployment_method = 'automatic',
      bot_status = 'bot_scheduled',
      updated_at = NOW()
    WHERE id = meeting_record.id;
    
    -- Log the auto-scheduling
    INSERT INTO calendar_sync_logs (
      user_id, 
      sync_type, 
      status, 
      events_processed,
      meetings_created,
      error_message
    ) VALUES (
      meeting_record.user_id,
      'auto_bot_scheduling',
      'completed',
      1,
      1,
      'Auto-scheduled bot for meeting: ' || meeting_record.title
    );
  END LOOP;
END;
$$;

-- ============================================================================
-- 3. UPDATE AUTHENTICATION FUNCTIONS
-- ============================================================================

-- Fix handle_google_oauth_login function
CREATE OR REPLACE FUNCTION handle_google_oauth_login(
  google_user_id TEXT,
  google_email TEXT,
  google_name TEXT,
  google_picture TEXT,
  access_token TEXT,
  refresh_token TEXT,
  token_type TEXT,
  expires_at TIMESTAMP WITH TIME ZONE,
  scope TEXT
) RETURNS UUID AS $$
DECLARE
  user_id UUID;
  existing_user_id UUID;
BEGIN
  -- Check if a user already exists with this Google user ID
  SELECT gc.user_id INTO existing_user_id
  FROM google_credentials gc
  WHERE gc.google_user_id = handle_google_oauth_login.google_user_id
    AND gc.login_provider = TRUE;
  
  IF existing_user_id IS NOT NULL THEN
    -- Update existing credentials
    UPDATE google_credentials
    SET 
      access_token = handle_google_oauth_login.access_token,
      refresh_token = handle_google_oauth_login.refresh_token,
      token_type = handle_google_oauth_login.token_type,
      expires_at = handle_google_oauth_login.expires_at,
      scope = handle_google_oauth_login.scope,
      google_email = handle_google_oauth_login.google_email,
      google_name = handle_google_oauth_login.google_name,
      google_picture = handle_google_oauth_login.google_picture,
      updated_at = NOW()
    WHERE user_id = existing_user_id;
    
    RETURN existing_user_id;
  ELSE
    -- Check if a user exists with this email (for linking existing accounts)
    SELECT id INTO existing_user_id
    FROM auth.users
    WHERE email = handle_google_oauth_login.google_email;
    
    IF existing_user_id IS NOT NULL THEN
      -- Link existing user account to Google OAuth
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        existing_user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN existing_user_id;
    ELSE
      -- Create new user account
      INSERT INTO auth.users (
        email,
        email_confirmed_at,
        raw_user_meta_data
      ) VALUES (
        handle_google_oauth_login.google_email,
        NOW(),
        jsonb_build_object(
          'name', handle_google_oauth_login.google_name,
          'picture', handle_google_oauth_login.google_picture,
          'provider', 'google'
        )
      ) RETURNING id INTO user_id;
      
      -- Insert Google credentials
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN user_id;
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_by_google_id function
CREATE OR REPLACE FUNCTION get_user_by_google_id(google_user_id TEXT)
RETURNS TABLE(user_id UUID, email TEXT, name TEXT, picture TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    gc.user_id,
    gc.google_email,
    gc.google_name,
    gc.google_picture
  FROM google_credentials gc
  WHERE gc.google_user_id = get_user_by_google_id.google_user_id
    AND gc.login_provider = TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix extract_username_from_email function
CREATE OR REPLACE FUNCTION extract_username_from_email(email_address TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN split_part(email_address, '@', 1);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_by_username function
CREATE OR REPLACE FUNCTION get_user_by_username(search_username TEXT)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  name TEXT,
  username TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.id,
    u.email,
    u.name,
    u.username
  FROM users u
  WHERE u.username = search_username;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix set_user_username function
CREATE OR REPLACE FUNCTION set_user_username(user_uuid UUID, new_username TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  -- Check if username is already taken
  IF EXISTS (SELECT 1 FROM users WHERE username = new_username AND id != user_uuid) THEN
    RETURN FALSE;
  END IF;
  
  -- Update the username
  UPDATE users 
  SET username = new_username, username_set_at = NOW()
  WHERE id = user_uuid;
  
  RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- ============================================================================
-- 4. UPDATE CHAT UTILITY FUNCTIONS
-- ============================================================================

-- Fix get_session_message_count function
CREATE OR REPLACE FUNCTION get_session_message_count(session_uuid UUID)
RETURNS INTEGER AS $$
BEGIN
  RETURN (
    SELECT COUNT(*) 
    FROM chat_messages 
    WHERE session_id = session_uuid
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_recent_messages function
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_active_sessions function
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_session_stats function
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- ============================================================================
-- 5. UPDATE PROJECT UTILITY FUNCTIONS
-- ============================================================================

-- Fix user_has_project_access function
CREATE OR REPLACE FUNCTION user_has_project_access(project_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM projects 
    WHERE id = project_uuid AND created_by = auth.uid()
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Fix get_user_project_ids function
CREATE OR REPLACE FUNCTION get_user_project_ids()
RETURNS TABLE(project_id UUID) AS $$
BEGIN
  RETURN QUERY
  SELECT id FROM projects WHERE created_by = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- ============================================================================
-- 6. VERIFICATION QUERIES (for testing)
-- ============================================================================

-- Uncomment these queries to verify functions are working properly
/*
-- Test function calls
SELECT get_session_message_count('00000000-0000-0000-0000-000000000000');
SELECT get_user_project_ids();
SELECT user_has_project_access('00000000-0000-0000-0000-000000000000');
SELECT extract_username_from_email('test@example.com');
*/ 