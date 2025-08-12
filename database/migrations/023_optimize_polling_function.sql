-- Optimized polling function that stops polling completed meetings with transcripts
-- but continues polling completed meetings without transcripts (for transcript retrieval)

-- Drop and recreate the function with optimized logic
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
    AND (
      -- Active meetings (not completed)
      m.bot_status IN ('pending', 'bot_scheduled', 'bot_joined', 'transcribing')
      OR
      -- Completed meetings that need transcript retrieval
      (m.bot_status = 'completed' 
       AND m.transcript_retrieved_at IS NULL
       AND m.last_polled_at IS NOT NULL
       AND m.last_polled_at > NOW() - INTERVAL '1 hour') -- Stop polling completed meetings after 1 hour
    )
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW())
    AND m.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role;

-- Function created successfully 