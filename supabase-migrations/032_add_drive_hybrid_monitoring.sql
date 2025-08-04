-- Add hybrid monitoring fields to drive_file_watches table
-- This migration adds fields to track webhook activity and enable smart polling

-- Add fields for hybrid monitoring
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_webhook_received TIMESTAMP WITH TIME ZONE;
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS webhook_failures INTEGER DEFAULT 0;

-- Create indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_last_webhook_received ON drive_file_watches(last_webhook_received);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_last_poll_at ON drive_file_watches(last_poll_at);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_webhook_failures ON drive_file_watches(webhook_failures);

-- Create a view to monitor drive watch status
CREATE OR REPLACE VIEW drive_watch_status AS
SELECT 
  dfw.id,
  dfw.document_id,
  dfw.project_id,
  dfw.file_id,
  dfw.channel_id,
  dfw.resource_id,
  dfw.expiration,
  dfw.is_active,
  dfw.last_webhook_received,
  dfw.last_poll_at,
  dfw.webhook_failures,
  d.title as document_title,
  d.status as document_status,
  CASE 
    WHEN dfw.last_webhook_received IS NULL OR dfw.last_webhook_received < NOW() - INTERVAL '6 hours' THEN 'ready_for_polling'
    ELSE 'webhook_active'
  END as polling_status
FROM drive_file_watches dfw
JOIN documents d ON dfw.document_id = d.id
WHERE dfw.is_active = TRUE;

-- Grant select permissions on the view
GRANT SELECT ON drive_watch_status TO authenticated;
GRANT SELECT ON drive_watch_status TO service_role;

-- Create function to log drive polling activity
CREATE OR REPLACE FUNCTION log_drive_polling_activity(
  p_document_id UUID,
  p_file_id TEXT,
  p_polling_result JSONB
)
RETURNS VOID AS $$
BEGIN
  INSERT INTO drive_webhook_logs (
    document_id,
    project_id,
    file_id,
    channel_id,
    resource_id,
    resource_state,
    webhook_received_at,
    n8n_webhook_sent,
    n8n_webhook_response,
    error_message
  )
  SELECT 
    p_document_id,
    d.project_id,
    p_file_id,
    dfw.channel_id,
    dfw.resource_id,
    'polling',
    NOW(),
    (p_polling_result->>'n8n_webhook_sent')::BOOLEAN,
    p_polling_result->>'n8n_webhook_response',
    p_polling_result->>'error_message'
  FROM documents d
  JOIN drive_file_watches dfw ON d.id = dfw.document_id
  WHERE d.id = p_document_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION log_drive_polling_activity(UUID, TEXT, JSONB) TO service_role; 