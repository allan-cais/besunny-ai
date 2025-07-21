-- Add missing next_poll_time field to meetings table
-- This field is referenced by the update_next_poll_time trigger but doesn't exist in the table

ALTER TABLE "public"."meetings" 
ADD COLUMN IF NOT EXISTS "next_poll_time" timestamp with time zone;

-- Add comment to explain the field
COMMENT ON COLUMN "public"."meetings"."next_poll_time" IS 'Next time to poll for real-time transcription updates'; 