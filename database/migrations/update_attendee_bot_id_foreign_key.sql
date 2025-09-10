-- Update attendee_bot_id foreign key to reference meeting_bots.bot_id instead of bots.id
-- This migration changes the foreign key relationship to properly link meetings to their bots

-- First, drop the existing foreign key constraint if it exists
DO $$ 
BEGIN
    -- Check if the foreign key constraint exists and drop it
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'meetings_attendee_bot_id_fkey' 
        AND table_name = 'meetings'
    ) THEN
        ALTER TABLE meetings DROP CONSTRAINT meetings_attendee_bot_id_fkey;
    END IF;
END $$;

-- Drop the meetings_for_polling view temporarily since it depends on attendee_bot_id
DROP VIEW IF EXISTS meetings_for_polling;

-- Change the attendee_bot_id column type from uuid to text to match meeting_bots.bot_id
ALTER TABLE meetings 
ALTER COLUMN attendee_bot_id TYPE TEXT USING attendee_bot_id::TEXT;

-- Add the new foreign key constraint to reference meeting_bots.bot_id
ALTER TABLE meetings 
ADD CONSTRAINT meetings_attendee_bot_id_fkey 
FOREIGN KEY (attendee_bot_id) REFERENCES meeting_bots(bot_id) ON DELETE SET NULL;

-- Recreate the meetings_for_polling view
CREATE VIEW meetings_for_polling AS
SELECT 
    id,
    user_id,
    title,
    meeting_url,
    attendee_bot_id,
    bot_status,
    start_time,
    end_time,
    created_at,
    updated_at
FROM meetings 
WHERE attendee_bot_id IS NOT NULL 
AND bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing');

-- Add comment to clarify the relationship
COMMENT ON COLUMN meetings.attendee_bot_id IS 'References meeting_bots.bot_id - the bot assigned to this meeting';
