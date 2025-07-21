-- Fix the get_meetings_for_polling function to work with service role
-- The issue is that auth.uid() returns NULL when using service_role

DROP FUNCTION IF EXISTS get_meetings_for_polling();

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
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing', 'completed')
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW());
    -- Removed: AND m.user_id = auth.uid();
    -- This was causing the function to return no results when called with service_role
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role;

-- Test the function
SELECT 'Testing get_meetings_for_polling function:' as test_message;
SELECT * FROM get_meetings_for_polling(); 