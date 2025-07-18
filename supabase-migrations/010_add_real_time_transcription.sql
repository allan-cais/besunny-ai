-- Add real-time transcription and polling support
-- This migration adds fields for capturing real-time transcription data
-- while only displaying the final transcript in the UI

-- Add polling and real-time transcription fields to meetings table
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS last_polled_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS next_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS polling_enabled BOOLEAN DEFAULT TRUE;

-- Add real-time transcription fields
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS real_time_transcript JSONB;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS final_transcript_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS transcript_metadata JSONB;

-- Add indexes for polling and transcription
CREATE INDEX IF NOT EXISTS idx_meetings_last_polled_at ON meetings(last_polled_at);
CREATE INDEX IF NOT EXISTS idx_meetings_next_poll_at ON meetings(next_poll_at);
CREATE INDEX IF NOT EXISTS idx_meetings_polling_enabled ON meetings(polling_enabled);
CREATE INDEX IF NOT EXISTS idx_meetings_final_transcript_ready ON meetings(final_transcript_ready);

-- Add bot configuration fields
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS bot_configuration JSONB;

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS get_meetings_for_polling();

-- Create function to get meetings that need polling
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role; 