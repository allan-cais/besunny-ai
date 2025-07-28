-- Migration to sync documents table with transcripts and enhance data integration
-- This migration ensures all data (emails, drive files, transcripts) are stored in the documents table

-- Add new fields to documents table for better transcript and data integration
ALTER TABLE documents ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'document' CHECK (type IN ('email', 'document', 'spreadsheet', 'presentation', 'image', 'folder', 'meeting_transcript'));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS transcript_duration_seconds INTEGER;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS transcript_metadata JSONB;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS meeting_id UUID REFERENCES meetings(id) ON DELETE SET NULL;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_meeting_id ON documents(meeting_id);

-- Create a function to sync existing meeting transcripts to documents table
CREATE OR REPLACE FUNCTION sync_meeting_transcripts_to_documents()
RETURNS void AS $$
DECLARE
    meeting_record RECORD;
    document_id UUID;
BEGIN
    -- Loop through all meetings that have transcripts but no corresponding document
    FOR meeting_record IN 
        SELECT 
            m.id as meeting_id,
            m.title,
            m.transcript,
            m.transcript_summary,
            m.transcript_metadata,
            m.transcript_duration_seconds,
            m.transcript_retrieved_at,
            m.project_id,
            m.user_id,
            m.created_at
        FROM meetings m
        WHERE m.transcript IS NOT NULL 
        AND m.transcript != ''
        AND NOT EXISTS (
            SELECT 1 FROM documents d 
            WHERE d.meeting_id = m.id 
            AND d.type = 'meeting_transcript'
        )
    LOOP
        -- Insert document record for this transcript
        INSERT INTO documents (
            id,
            project_id,
            type,
            source,
            source_id,
            title,
            summary,
            author,
            received_at,
            created_at,
            created_by,
            meeting_id,
            transcript_duration_seconds,
            transcript_metadata,
            status
        ) VALUES (
            gen_random_uuid(),
            meeting_record.project_id,
            'meeting_transcript',
            'attendee_bot',
            meeting_record.meeting_id,
            COALESCE(meeting_record.title, 'Meeting Transcript'),
            COALESCE(meeting_record.transcript_summary, LEFT(meeting_record.transcript, 200) || '...'),
            'Meeting Attendee Bot',
            meeting_record.transcript_retrieved_at,
            meeting_record.created_at,
            meeting_record.user_id,
            meeting_record.meeting_id,
            meeting_record.transcript_duration_seconds,
            meeting_record.transcript_metadata,
            'active'
        ) RETURNING id INTO document_id;
        
        RAISE NOTICE 'Created document % for meeting transcript %', document_id, meeting_record.meeting_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the sync function
SELECT sync_meeting_transcripts_to_documents();

-- Drop the function after use
DROP FUNCTION sync_meeting_transcripts_to_documents(); 