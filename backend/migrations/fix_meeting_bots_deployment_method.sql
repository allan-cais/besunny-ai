-- Fix meeting_bots table - ensure deployment_method column exists
-- This migration ensures the deployment_method column exists in meeting_bots table

-- Add deployment_method column if it doesn't exist
ALTER TABLE meeting_bots 
ADD COLUMN IF NOT EXISTS deployment_method TEXT DEFAULT 'manual';

-- Add constraint if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'meeting_bots_deployment_method_check') THEN
        ALTER TABLE meeting_bots 
        ADD CONSTRAINT meeting_bots_deployment_method_check 
        CHECK (deployment_method = ANY (ARRAY['manual', 'automatic']));
    END IF;
END $$;

-- Update existing records to set default value
UPDATE meeting_bots SET deployment_method = 'manual' WHERE deployment_method IS NULL;

-- Add index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_meeting_bots_deployment_method ON meeting_bots(deployment_method);

-- Add comment
COMMENT ON COLUMN meeting_bots.deployment_method IS 'How the bot was deployed: manual (UI) or automatic (virtual email)';
