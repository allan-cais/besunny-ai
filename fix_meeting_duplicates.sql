-- Fix meeting duplication issue by adding unique constraint and cleaning duplicates

-- First, clean up any existing duplicates by keeping the most recent one for each google_calendar_event_id
DELETE FROM meetings 
WHERE id NOT IN (
  SELECT DISTINCT ON (google_calendar_event_id, user_id) id
  FROM meetings 
  WHERE google_calendar_event_id IS NOT NULL
  ORDER BY google_calendar_event_id, user_id, updated_at DESC
);

-- Add unique constraint to prevent future duplicates
ALTER TABLE meetings 
ADD CONSTRAINT unique_google_calendar_event_per_user 
UNIQUE (google_calendar_event_id, user_id);

-- Add index for better performance on the unique constraint
CREATE INDEX IF NOT EXISTS idx_meetings_google_event_user_unique 
ON meetings(google_calendar_event_id, user_id);
