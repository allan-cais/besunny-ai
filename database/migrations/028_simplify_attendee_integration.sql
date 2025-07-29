-- Simplify attendee integration by removing unnecessary complexity
-- This migration consolidates the polling logic and removes redundant fields

-- Drop dependent views and triggers first
DROP VIEW IF EXISTS polling_status CASCADE;
DROP TRIGGER IF EXISTS trg_update_next_poll_time ON meetings;

-- Remove complex polling fields that aren't needed
ALTER TABLE meetings 
DROP COLUMN IF EXISTS next_poll_at,
DROP COLUMN IF EXISTS polling_enabled,
DROP COLUMN IF EXISTS real_time_transcript,
DROP COLUMN IF EXISTS final_transcript_ready,
DROP COLUMN IF EXISTS poll_interval_minutes;

-- Simplify bot status to essential states only
ALTER TABLE meetings 
ALTER COLUMN bot_status TYPE TEXT;

-- Drop existing constraint if it exists, then add the new one
ALTER TABLE meetings 
DROP CONSTRAINT IF EXISTS meetings_bot_status_check;

ALTER TABLE meetings 
ADD CONSTRAINT meetings_bot_status_check 
CHECK (bot_status IN ('pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed', 'failed'));

-- Add a simple index for efficient polling queries
CREATE INDEX IF NOT EXISTS idx_meetings_polling 
ON meetings(attendee_bot_id, bot_status, updated_at) 
WHERE attendee_bot_id IS NOT NULL;

-- Create a simplified view for meetings that need polling
CREATE OR REPLACE VIEW meetings_for_polling AS
SELECT 
  id,
  user_id,
  attendee_bot_id,
  bot_status,
  title,
  meeting_url,
  updated_at
FROM meetings 
WHERE attendee_bot_id IS NOT NULL
  AND bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
ORDER BY updated_at DESC;

-- Grant permissions
GRANT SELECT ON meetings_for_polling TO authenticated;
GRANT SELECT ON meetings_for_polling TO service_role;

-- Drop the old complex polling function
DROP FUNCTION IF EXISTS get_meetings_for_polling();

-- Drop the old polling status view
DROP VIEW IF EXISTS polling_status;

-- Create a simple function to get meetings for polling
CREATE OR REPLACE FUNCTION get_meetings_for_polling()
RETURNS TABLE(
  id UUID,
  user_id UUID,
  attendee_bot_id UUID,
  bot_status TEXT,
  title TEXT,
  meeting_url TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    m.id,
    m.user_id,
    m.attendee_bot_id,
    m.bot_status,
    m.title,
    m.meeting_url
  FROM meetings m
  WHERE m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
  ORDER BY m.updated_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role; 