-- Comprehensive fix for bot polling issues
-- This script addresses multiple problems with the bot polling system

-- 1. Fix conflicting default values for polling_enabled
ALTER TABLE "public"."meetings" ALTER COLUMN "polling_enabled" SET DEFAULT false;

-- 2. Update existing meetings with bots to have polling enabled
UPDATE "public"."meetings" 
SET polling_enabled = true 
WHERE attendee_bot_id IS NOT NULL 
  AND bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing', 'completed');

-- 3. Fix the get_meetings_for_polling function to include completed meetings
-- This ensures we can detect when meetings transition to completed
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
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW())
    AND m.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO authenticated;
GRANT EXECUTE ON FUNCTION get_meetings_for_polling() TO service_role;

-- 4. Create a function to set next poll time based on bot status
CREATE OR REPLACE FUNCTION set_next_poll_time(meeting_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_status TEXT;
  poll_interval_minutes INTEGER;
BEGIN
  -- Get current bot status
  SELECT bot_status INTO current_status
  FROM meetings
  WHERE id = meeting_id;
  
  -- Set poll interval based on status
  CASE current_status
    WHEN 'bot_scheduled' THEN
      poll_interval_minutes := 2; -- Poll every 2 minutes for scheduled bots
    WHEN 'bot_joined' THEN
      poll_interval_minutes := 1; -- Poll every minute for joined bots
    WHEN 'transcribing' THEN
      poll_interval_minutes := 30; -- Poll every 30 seconds for transcribing bots
    WHEN 'completed' THEN
      poll_interval_minutes := 5; -- Poll every 5 minutes for completed bots (to get transcript)
    ELSE
      poll_interval_minutes := 5; -- Default 5 minutes
  END CASE;
  
  -- Update next poll time
  UPDATE meetings
  SET next_poll_at = NOW() + INTERVAL '1 minute' * poll_interval_minutes
  WHERE id = meeting_id;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION set_next_poll_time(UUID) TO service_role;

-- 5. Create a trigger to automatically set next poll time when bot status changes
CREATE OR REPLACE FUNCTION trigger_set_next_poll_time()
RETURNS TRIGGER AS $$
BEGIN
  -- Only set next poll time if polling is enabled and bot status changed
  IF NEW.polling_enabled = TRUE 
     AND NEW.attendee_bot_id IS NOT NULL 
     AND (NEW.bot_status != OLD.bot_status OR OLD.bot_status IS NULL) THEN
    PERFORM set_next_poll_time(NEW.id);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS trg_set_next_poll_time ON meetings;
CREATE TRIGGER trg_set_next_poll_time
  AFTER UPDATE ON meetings
  FOR EACH ROW
  EXECUTE FUNCTION trigger_set_next_poll_time();

-- 6. Update the polling status view to include completed meetings
DROP VIEW IF EXISTS polling_status;
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
  AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing', 'completed');

-- Grant select permissions on the view
GRANT SELECT ON polling_status TO authenticated;

-- 7. Create a function to manually trigger polling for a specific meeting
CREATE OR REPLACE FUNCTION trigger_meeting_poll(meeting_id UUID)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  meeting_record RECORD;
BEGIN
  -- Get meeting details
  SELECT * INTO meeting_record
  FROM meetings
  WHERE id = meeting_id
    AND polling_enabled = TRUE
    AND attendee_bot_id IS NOT NULL;
  
  IF NOT FOUND THEN
    RETURN json_build_object(
      'success', false,
      'error', 'Meeting not found or not eligible for polling'
    );
  END IF;
  
  -- Set next poll time to now to make it eligible for polling
  UPDATE meetings
  SET next_poll_at = NOW()
  WHERE id = meeting_id;
  
  RETURN json_build_object(
    'success', true,
    'meeting_id', meeting_id,
    'title', meeting_record.title,
    'bot_status', meeting_record.bot_status,
    'next_poll_at', NOW()
  );
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION trigger_meeting_poll(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION trigger_meeting_poll(UUID) TO service_role;

-- 8. Add missing columns that might not exist
ALTER TABLE "public"."meetings" 
ADD COLUMN IF NOT EXISTS "transcript_summary" text,
ADD COLUMN IF NOT EXISTS "transcript_duration_seconds" integer,
ADD COLUMN IF NOT EXISTS "transcript_retrieved_at" timestamp with time zone;

-- 9. Create an index to improve polling performance
CREATE INDEX IF NOT EXISTS idx_meetings_polling_performance 
ON meetings(polling_enabled, attendee_bot_id, bot_status, next_poll_at) 
WHERE polling_enabled = TRUE AND attendee_bot_id IS NOT NULL;

-- 10. Log the fix
INSERT INTO calendar_sync_logs (
  user_id,
  sync_type,
  status,
  events_processed,
  meetings_created,
  error_message
) VALUES (
  '00000000-0000-0000-0000-000000000000', -- System user
  'polling_system_fix',
  'completed',
  0,
  0,
  'Applied comprehensive bot polling system fixes'
); 