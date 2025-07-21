-- Fix the get_meetings_for_polling function to include pending and completed meetings
-- This will allow meetings with bot_status 'pending' and 'completed' to be polled

-- Drop and recreate the function with updated status list
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
    AND m.bot_status IN ('pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed')
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW())
    AND m.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role;

-- Test the function to see what meetings it now finds
SELECT 
  id,
  title,
  bot_status,
  polling_enabled,
  next_poll_at,
  CASE 
    WHEN next_poll_at IS NULL OR next_poll_at <= NOW() THEN 'ready_for_polling'
    ELSE 'waiting'
  END as polling_status
FROM meetings 
WHERE attendee_bot_id IS NOT NULL 
  AND bot_status IN ('pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed')
ORDER BY bot_status, next_poll_at; 