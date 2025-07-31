-- Fix the remaining two functions that reference polling_enabled
-- These functions are causing the error when updating meetings

-- 1. Fix trigger_set_next_poll_time function
CREATE OR REPLACE FUNCTION trigger_set_next_poll_time()
RETURNS TRIGGER AS $$
BEGIN
  -- Since polling_enabled field was removed, we just return NEW without modification
  -- The polling logic has been simplified and doesn't need this trigger anymore
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- 2. Fix trigger_meeting_poll function
CREATE OR REPLACE FUNCTION trigger_meeting_poll(meeting_id UUID)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  meeting_record RECORD;
BEGIN
  -- Get meeting details (removed polling_enabled check)
  SELECT * INTO meeting_record
  FROM meetings
  WHERE id = meeting_id
    AND attendee_bot_id IS NOT NULL;
  
  IF NOT FOUND THEN
    RETURN json_build_object(
      'success', false,
      'error', 'Meeting not found or not eligible for polling'
    );
  END IF;
  
  -- Since next_poll_at field was removed, we just return success
  RETURN json_build_object(
    'success', true,
    'meeting_id', meeting_id,
    'title', meeting_record.title,
    'bot_status', meeting_record.bot_status
  );
END;
$$;

-- 3. Grant permissions
GRANT EXECUTE ON FUNCTION trigger_set_next_poll_time() TO authenticated;
GRANT EXECUTE ON FUNCTION trigger_set_next_poll_time() TO service_role;
GRANT EXECUTE ON FUNCTION trigger_meeting_poll(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION trigger_meeting_poll(UUID) TO service_role;

-- 4. Verify no remaining references to polling_enabled
-- This query should now return no results
SELECT 
  routine_name,
  routine_definition
FROM information_schema.routines 
WHERE routine_definition LIKE '%polling_enabled%'
  AND routine_schema = 'public'; 