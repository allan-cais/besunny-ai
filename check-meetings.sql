-- Check meetings and their polling status
SELECT 
  id,
  title,
  bot_status,
  attendee_bot_id,
  polling_enabled,
  last_polled_at,
  next_poll_at,
  created_at,
  updated_at
FROM meetings 
WHERE attendee_bot_id IS NOT NULL
ORDER BY updated_at DESC;

-- Check the polling status view
SELECT * FROM polling_status;

-- Check if any meetings need polling right now
SELECT 
  id,
  title,
  bot_status,
  next_poll_at,
  CASE 
    WHEN next_poll_at IS NULL OR next_poll_at <= NOW() THEN 'READY'
    ELSE 'WAITING'
  END as polling_status
FROM meetings 
WHERE polling_enabled = TRUE 
  AND attendee_bot_id IS NOT NULL
  AND bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing', 'completed')
ORDER BY next_poll_at ASC; 