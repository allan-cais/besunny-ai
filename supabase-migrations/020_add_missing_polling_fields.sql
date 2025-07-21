-- Add missing polling fields to meetings table
-- These fields are referenced by triggers but don't exist in the table

ALTER TABLE "public"."meetings" 
ADD COLUMN IF NOT EXISTS "next_poll_time" timestamp with time zone,
ADD COLUMN IF NOT EXISTS "last_polled_at" timestamp with time zone,
ADD COLUMN IF NOT EXISTS "polling_enabled" boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS "real_time_transcript" jsonb,
ADD COLUMN IF NOT EXISTS "final_transcript_ready" boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS "transcript_metadata" jsonb,
ADD COLUMN IF NOT EXISTS "bot_configuration" jsonb,
ADD COLUMN IF NOT EXISTS "bot_deployment_method" text DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS "auto_scheduled_via_email" boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS "virtual_email_attendee" text,
ADD COLUMN IF NOT EXISTS "auto_bot_notification_sent" boolean DEFAULT false;

-- Add comment to explain the fields
COMMENT ON COLUMN "public"."meetings"."next_poll_time" IS 'Next time to poll for real-time transcription updates';
COMMENT ON COLUMN "public"."meetings"."last_polled_at" IS 'Last time the meeting was polled for transcription updates';
COMMENT ON COLUMN "public"."meetings"."polling_enabled" IS 'Whether real-time transcription polling is enabled for this meeting';
COMMENT ON COLUMN "public"."meetings"."real_time_transcript" IS 'Real-time transcription data';
COMMENT ON COLUMN "public"."meetings"."final_transcript_ready" IS 'Whether the final transcript is ready';
COMMENT ON COLUMN "public"."meetings"."transcript_metadata" IS 'Metadata about the transcription process';
COMMENT ON COLUMN "public"."meetings"."bot_configuration" IS 'Configuration for the bot attending this meeting';
COMMENT ON COLUMN "public"."meetings"."bot_deployment_method" IS 'How the bot was deployed (manual/automatic/scheduled)';
COMMENT ON COLUMN "public"."meetings"."auto_scheduled_via_email" IS 'Whether the bot was auto-scheduled via email';
COMMENT ON COLUMN "public"."meetings"."virtual_email_attendee" IS 'Virtual email address used for auto-scheduling';
COMMENT ON COLUMN "public"."meetings"."auto_bot_notification_sent" IS 'Whether auto-bot notification was sent'; 