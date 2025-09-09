-- Update meeting_bots table for transcript handling and project classification
-- This migration adds transcript storage and fixes project_id foreign key

-- Add transcript column to store meeting transcripts
ALTER TABLE meeting_bots 
ADD COLUMN IF NOT EXISTS transcript TEXT;

-- Add comment for the transcript column
COMMENT ON COLUMN meeting_bots.transcript IS 'Meeting transcript content retrieved from Attendee.dev API';

-- Drop the old attendee_project_id column if it exists
ALTER TABLE meeting_bots 
DROP COLUMN IF EXISTS attendee_project_id;

-- Add new project_id column with foreign key to projects table
ALTER TABLE meeting_bots 
ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE SET NULL;

-- Add comment for the project_id column
COMMENT ON COLUMN meeting_bots.project_id IS 'Project ID for classified meetings, references projects table';

-- Add index on project_id for better query performance
CREATE INDEX IF NOT EXISTS idx_meeting_bots_project_id ON meeting_bots(project_id);

-- Add index on status for filtering active/ended bots
CREATE INDEX IF NOT EXISTS idx_meeting_bots_status ON meeting_bots(status);

-- Add comment to clarify the updated table structure
COMMENT ON TABLE meeting_bots IS 'Meeting bot deployments with transcript storage and project classification support';
