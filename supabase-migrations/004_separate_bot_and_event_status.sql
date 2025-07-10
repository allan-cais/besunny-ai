-- Separate bot status and event status into distinct columns
-- This migration properly separates the two different types of status tracking

-- Add new columns for separate status tracking
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS event_status TEXT DEFAULT 'needsAction' CHECK (
  event_status IN (
    'accepted',
    'declined', 
    'tentative',
    'needsAction'
  )
);

ALTER TABLE meetings ADD COLUMN IF NOT EXISTS bot_status TEXT DEFAULT 'pending' CHECK (
  bot_status IN (
    'pending',
    'bot_scheduled',
    'bot_joined',
    'transcribing',
    'completed',
    'failed'
  )
);

-- Migrate existing data from the old status column
-- We'll assume existing records are bot_status since that was the original intent
UPDATE meetings 
SET bot_status = status 
WHERE status IN ('pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'completed', 'failed');

-- Set event_status to 'accepted' for meetings that were created by the user (they're the creator)
UPDATE meetings 
SET event_status = 'accepted' 
WHERE google_calendar_event_id IS NOT NULL;

-- Drop the old status column
ALTER TABLE meetings DROP COLUMN IF EXISTS status;

-- Create indexes for the new status columns
CREATE INDEX IF NOT EXISTS idx_meetings_event_status ON meetings(event_status);
CREATE INDEX IF NOT EXISTS idx_meetings_bot_status ON meetings(bot_status);

-- Drop the old status index if it exists
DROP INDEX IF EXISTS idx_meetings_status; 