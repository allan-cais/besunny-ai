-- Migration: Add transcript processing fields and deployment method tracking
-- Date: 2024-01-15
-- Description: Add fields to support transcript processing workflows and bot deployment tracking

-- Add new fields to meetings table
ALTER TABLE meetings 
ADD COLUMN IF NOT EXISTS transcript_ready_for_classification BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS transcript_ready_for_embedding BOOLEAN DEFAULT false;

-- Update bot_status enum to include 'post_processing' state
ALTER TABLE meetings 
DROP CONSTRAINT IF EXISTS meetings_bot_status_check;

ALTER TABLE meetings 
ADD CONSTRAINT meetings_bot_status_check 
CHECK (bot_status = ANY (ARRAY['pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'post_processing', 'completed', 'failed']));

-- Add new fields to meeting_bots table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meeting_bots') THEN
        CREATE TABLE meeting_bots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            bot_id TEXT NOT NULL UNIQUE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            meeting_url TEXT NOT NULL,
            bot_name TEXT NOT NULL,
            status TEXT DEFAULT 'created',
            attendee_project_id TEXT,
            deployment_method TEXT DEFAULT 'manual' CHECK (deployment_method = ANY (ARRAY['manual', 'automatic'])),
            metadata JSONB,
            is_recording BOOLEAN DEFAULT false,
            is_paused BOOLEAN DEFAULT false,
            last_state_change TIMESTAMP WITH TIME ZONE,
            event_type TEXT,
            event_sub_type TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
    ELSE
        -- Add new fields to existing meeting_bots table
        ALTER TABLE meeting_bots 
        ADD COLUMN IF NOT EXISTS deployment_method TEXT DEFAULT 'manual',
        ADD COLUMN IF NOT EXISTS metadata JSONB,
        ADD COLUMN IF NOT EXISTS last_state_change TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS event_type TEXT,
        ADD COLUMN IF NOT EXISTS event_sub_type TEXT;
        
        -- Add constraint if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'meeting_bots_deployment_method_check') THEN
            ALTER TABLE meeting_bots 
            ADD CONSTRAINT meeting_bots_deployment_method_check 
            CHECK (deployment_method = ANY (ARRAY['manual', 'automatic']));
        END IF;
    END IF;
END $$;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_meetings_transcript_ready_classification ON meetings(transcript_ready_for_classification) WHERE transcript_ready_for_classification = true;
CREATE INDEX IF NOT EXISTS idx_meetings_transcript_ready_embedding ON meetings(transcript_ready_for_embedding) WHERE transcript_ready_for_embedding = true;
CREATE INDEX IF NOT EXISTS idx_meetings_bot_deployment_method ON meetings(bot_deployment_method);
CREATE INDEX IF NOT EXISTS idx_meeting_bots_deployment_method ON meeting_bots(deployment_method);
CREATE INDEX IF NOT EXISTS idx_meeting_bots_status ON meeting_bots(status);

-- Add comments
COMMENT ON COLUMN meetings.transcript_ready_for_classification IS 'Flag indicating transcript is ready for classification agent processing';
COMMENT ON COLUMN meetings.transcript_ready_for_embedding IS 'Flag indicating transcript is ready for vector embedding workflow';
COMMENT ON COLUMN meetings.bot_deployment_method IS 'How the bot was deployed: manual (UI), automatic (virtual email), or scheduled';

COMMENT ON COLUMN meeting_bots.deployment_method IS 'How the bot was deployed: manual (UI) or automatic (virtual email)';
COMMENT ON COLUMN meeting_bots.metadata IS 'Additional metadata about the bot deployment';
COMMENT ON COLUMN meeting_bots.event_type IS 'Type of event that triggered the last state change';
COMMENT ON COLUMN meeting_bots.event_sub_type IS 'Sub-type of event that triggered the last state change';

-- Update existing records to set default values
UPDATE meetings SET transcript_ready_for_classification = false WHERE transcript_ready_for_classification IS NULL;
UPDATE meetings SET transcript_ready_for_embedding = false WHERE transcript_ready_for_embedding IS NULL;
UPDATE meetings SET bot_deployment_method = 'manual' WHERE bot_deployment_method IS NULL;

-- Log migration completion
INSERT INTO schema_migrations (version, applied_at) VALUES ('003_add_transcript_processing_fields', NOW());
