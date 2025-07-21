-- Check transcript status for the completed meeting
SELECT 
  id,
  title,
  bot_status,
  attendee_bot_id,
  transcript_url,
  transcript_retrieved_at,
  final_transcript_ready,
  transcript_summary,
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

-- Also check the bot record to get the provider_bot_id
SELECT 
  b.id,
  b.name,
  b.provider_bot_id,
  b.provider,
  b.settings
FROM bots b
JOIN meetings m ON b.id = m.attendee_bot_id
WHERE m.id = '4a9ad0d8-e8df-4ac1-b533-1d6be21d009e'; 