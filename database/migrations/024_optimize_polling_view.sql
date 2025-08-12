-- Fix the polling_status view to match the optimized polling function
-- This will show only meetings that actually need polling

-- Drop the existing view first
DROP VIEW IF EXISTS polling_status;

-- Create the view with optimized logic
CREATE VIEW polling_status AS
SELECT 
  m.id,
  m.title,
  m.bot_status,
  m.last_polled_at,
  m.next_poll_at,
  m.polling_enabled,
  m.transcript_retrieved_at,
  CASE 
    WHEN m.bot_status = 'completed' AND m.transcript_retrieved_at IS NOT NULL THEN 'completed_with_transcript'
    WHEN m.bot_status = 'completed' AND m.transcript_retrieved_at IS NULL THEN 'completed_needs_transcript'
    WHEN m.next_poll_at IS NULL OR m.next_poll_at <= NOW() THEN 'ready_for_polling'
    ELSE 'waiting'
  END as polling_status
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
  );

-- Grant select permissions on the view
GRANT SELECT ON polling_status TO authenticated;

-- View created successfully 