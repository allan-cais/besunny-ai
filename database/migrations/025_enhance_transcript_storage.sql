-- Fix transcript storage in meetings table
-- Add missing columns for better transcript handling

-- Add columns for enhanced transcript metadata
ALTER TABLE meetings 
ADD COLUMN IF NOT EXISTS transcript_participants JSONB,
ADD COLUMN IF NOT EXISTS transcript_speakers JSONB,
ADD COLUMN IF NOT EXISTS transcript_segments JSONB,
ADD COLUMN IF NOT EXISTS transcript_audio_url TEXT,
ADD COLUMN IF NOT EXISTS transcript_recording_url TEXT,
ADD COLUMN IF NOT EXISTS transcript_processing_status TEXT DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS transcript_quality_score NUMERIC(3,2),
ADD COLUMN IF NOT EXISTS transcript_language TEXT DEFAULT 'en-US',
ADD COLUMN IF NOT EXISTS transcript_confidence_score NUMERIC(3,2);

-- Add check constraint for processing status using DO block
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'meetings_transcript_processing_status_check'
    ) THEN
        ALTER TABLE meetings 
        ADD CONSTRAINT meetings_transcript_processing_status_check 
        CHECK (transcript_processing_status IN ('pending', 'processing', 'completed', 'failed', 'not_available'));
    END IF;
END $$;

-- Add index for transcript queries
CREATE INDEX IF NOT EXISTS idx_meetings_transcript_retrieved_at 
ON meetings(transcript_retrieved_at DESC);

CREATE INDEX IF NOT EXISTS idx_meetings_transcript_processing_status 
ON meetings(transcript_processing_status);

-- Add comment for documentation
COMMENT ON COLUMN meetings.transcript_participants IS 'Array of participant information from transcript';
COMMENT ON COLUMN meetings.transcript_speakers IS 'Array of unique speakers identified in transcript';
COMMENT ON COLUMN meetings.transcript_segments IS 'Detailed transcript segments with timestamps and speaker info';
COMMENT ON COLUMN meetings.transcript_audio_url IS 'URL to the audio recording if available';
COMMENT ON COLUMN meetings.transcript_recording_url IS 'URL to the video recording if available';
COMMENT ON COLUMN meetings.transcript_processing_status IS 'Status of transcript processing';
COMMENT ON COLUMN meetings.transcript_quality_score IS 'Quality score of transcript (0.00-1.00)';
COMMENT ON COLUMN meetings.transcript_language IS 'Language of the transcript';
COMMENT ON COLUMN meetings.transcript_confidence_score IS 'Confidence score of transcription (0.00-1.00)';

-- Update existing completed meetings to have proper processing status
UPDATE meetings 
SET transcript_processing_status = CASE 
  WHEN transcript_retrieved_at IS NOT NULL THEN 'completed'
  WHEN bot_status = 'completed' THEN 'pending'
  ELSE 'not_available'
END
WHERE transcript_processing_status IS NULL;

-- Migration completed successfully 