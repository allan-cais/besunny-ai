-- Fix all remaining polling_enabled references in the database
-- This script will find and fix all functions, triggers, and views that reference the removed polling_enabled field

-- 1. Drop all triggers that might reference polling_enabled
DROP TRIGGER IF EXISTS trg_update_next_poll_time ON meetings;

-- 2. Drop all functions that reference polling_enabled
DROP FUNCTION IF EXISTS get_meetings_for_polling() CASCADE;
DROP FUNCTION IF EXISTS trigger_attendee_polling() CASCADE;
DROP FUNCTION IF EXISTS update_next_poll_time() CASCADE;

-- 3. Drop all views that reference polling_enabled
DROP VIEW IF EXISTS polling_status CASCADE;

-- 4. Create clean versions of the functions without polling_enabled references

-- Create clean get_meetings_for_polling function
CREATE OR REPLACE FUNCTION get_meetings_for_polling()
RETURNS TABLE(
  id UUID,
  user_id UUID,
  attendee_bot_id UUID,
  bot_status TEXT,
  title TEXT,
  meeting_url TEXT,
  updated_at TIMESTAMP WITH TIME ZONE
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
    m.updated_at
  FROM meetings m
  WHERE m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
    AND m.user_id = auth.uid()
  ORDER BY m.updated_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Create clean trigger_attendee_polling function
CREATE OR REPLACE FUNCTION trigger_attendee_polling()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_agg(
    json_build_object(
      'meeting_id', m.id,
      'title', m.title,
      'bot_status', m.bot_status
    )
  ) INTO result
  FROM meetings m
  WHERE m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing');
  
  RETURN COALESCE(result, '[]'::json);
END;
$$;

-- Create clean update_next_poll_time function (does nothing now)
CREATE OR REPLACE FUNCTION update_next_poll_time()
RETURNS TRIGGER AS $$
BEGIN
  -- Since next_poll_time field was removed, we just return NEW without modification
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- 5. Create clean polling_status view
CREATE OR REPLACE VIEW polling_status AS
SELECT 
  m.id,
  m.title,
  m.bot_status,
  m.updated_at,
  CASE 
    WHEN m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing') THEN 'active'
    WHEN m.bot_status = 'completed' THEN 'completed'
    ELSE 'inactive'
  END as polling_status
FROM meetings m
WHERE m.attendee_bot_id IS NOT NULL
  AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing', 'completed');

-- 6. Grant permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role;
GRANT EXECUTE ON FUNCTION trigger_attendee_polling() TO service_role;
GRANT EXECUTE ON FUNCTION trigger_attendee_polling() TO authenticated;
GRANT SELECT ON polling_status TO authenticated;

-- 7. Recreate the trigger but only for bot_status changes (not project_id changes)
CREATE TRIGGER trg_update_next_poll_time 
BEFORE UPDATE ON meetings 
FOR EACH ROW 
WHEN (OLD.bot_status IS DISTINCT FROM NEW.bot_status)
EXECUTE FUNCTION update_next_poll_time();

-- 8. Verify no remaining references to polling_enabled
-- This query should return no results if all references are fixed
SELECT 
  routine_name,
  routine_definition
FROM information_schema.routines 
WHERE routine_definition LIKE '%polling_enabled%'
  AND routine_schema = 'public'; 