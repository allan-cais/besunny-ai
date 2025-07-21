-- Enhance transcript storage in meetings table
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

-- Add check constraint for processing status (drop first if exists)
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

-- Show current transcript status for the completed meeting
SELECT 
  id,
  title,
  bot_status,
  transcript_retrieved_at,
  transcript_processing_status,
  transcript_duration_seconds,
  CASE 
    WHEN transcript IS NOT NULL THEN 'Has transcript text'
    ELSE 'No transcript text'
  END as transcript_text_status,
  CASE 
    WHEN real_time_transcript IS NOT NULL THEN 'Has raw transcript data'
    ELSE 'No raw transcript data'
  END as raw_transcript_status,
  CASE 
    WHEN transcript_metadata IS NOT NULL THEN 'Has metadata'
    ELSE 'No metadata'
  END as metadata_status
FROM meetings 
WHERE id = '4a9ad0d8-e8df-4ac1-b533-1d6be21d009e'; 