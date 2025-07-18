-- Setup automated polling via scheduled function
-- This migration creates a function that can be called by external schedulers

-- Create a function that triggers the polling
CREATE OR REPLACE FUNCTION trigger_attendee_polling()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result json;
BEGIN
  -- Call the polling function for all meetings that need polling
  SELECT json_agg(
    json_build_object(
      'meeting_id', m.id,
      'title', m.title,
      'bot_status', m.bot_status
    )
  ) INTO result
  FROM meetings m
  WHERE m.polling_enabled = TRUE
    AND m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW());
  
  -- Return the meetings that were polled
  RETURN COALESCE(result, '[]'::json);
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION trigger_attendee_polling() TO service_role;
GRANT EXECUTE ON FUNCTION trigger_attendee_polling() TO authenticated;

-- Create a view to monitor polling status
CREATE OR REPLACE VIEW polling_status AS
SELECT 
  m.id,
  m.title,
  m.bot_status,
  m.last_polled_at,
  m.next_poll_at,
  m.polling_enabled,
  CASE 
    WHEN m.next_poll_at IS NULL OR m.next_poll_at <= NOW() THEN 'ready_for_polling'
    ELSE 'waiting'
  END as polling_status
FROM meetings m
WHERE m.polling_enabled = TRUE
  AND m.attendee_bot_id IS NOT NULL
  AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing');

-- Grant select permissions on the view
GRANT SELECT ON polling_status TO authenticated; 