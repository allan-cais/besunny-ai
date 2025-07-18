-- Add automatic bot scheduling via virtual email detection
-- This migration adds fields to track automatic vs manual bot deployment

-- Add fields to track bot deployment method
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS bot_deployment_method TEXT DEFAULT 'manual' CHECK (
  bot_deployment_method IN ('manual', 'automatic', 'scheduled')
);

-- Add field to track if bot was auto-scheduled via virtual email
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS auto_scheduled_via_email BOOLEAN DEFAULT FALSE;

-- Add field to store the virtual email address that triggered auto-scheduling
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS virtual_email_attendee TEXT;

-- Add field to track if user has been notified about auto-scheduled bot
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS auto_bot_notification_sent BOOLEAN DEFAULT FALSE;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_meetings_bot_deployment_method ON meetings(bot_deployment_method);
CREATE INDEX IF NOT EXISTS idx_meetings_auto_scheduled_via_email ON meetings(auto_scheduled_via_email);

-- Create function to auto-schedule bot for meetings with virtual email attendees
CREATE OR REPLACE FUNCTION auto_schedule_bot_for_virtual_email()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  meeting_record RECORD;
BEGIN
  -- Find meetings that have virtual email attendees but no bot scheduled yet
  FOR meeting_record IN
    SELECT 
      m.id,
      m.title,
      m.meeting_url,
      m.start_time,
      m.end_time,
      m.user_id,
      m.google_calendar_event_id
    FROM meetings m
    WHERE m.auto_scheduled_via_email = TRUE
      AND m.bot_deployment_method = 'scheduled'
      AND m.bot_status = 'pending'
      AND m.meeting_url IS NOT NULL
      AND m.start_time > NOW() -- Only future meetings
  LOOP
    -- Update meeting to indicate bot is being scheduled
    UPDATE meetings 
    SET 
      bot_deployment_method = 'automatic',
      bot_status = 'bot_scheduled',
      updated_at = NOW()
    WHERE id = meeting_record.id;
    
    -- Log the auto-scheduling
    INSERT INTO calendar_sync_logs (
      user_id, 
      sync_type, 
      status, 
      events_processed,
      meetings_created,
      error_message
    ) VALUES (
      meeting_record.user_id,
      'auto_bot_scheduling',
      'completed',
      1,
      1,
      'Auto-scheduled bot for meeting: ' || meeting_record.title
    );
  END LOOP;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION auto_schedule_bot_for_virtual_email() TO service_role; 