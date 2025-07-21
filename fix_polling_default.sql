-- Fix polling_enabled default to false
ALTER TABLE "public"."meetings" ALTER COLUMN "polling_enabled" SET DEFAULT false;
-- Update existing meetings without bots to have polling disabled
UPDATE "public"."meetings" SET polling_enabled = false WHERE attendee_bot_id IS NULL;
