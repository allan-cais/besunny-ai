-- Google Drive File Watch System Migration
-- This migration adds support for real-time Google Drive file monitoring

-- Add status column to documents table for tracking file states
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active' CHECK (status IN ('active', 'updated', 'deleted', 'error'));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_id TEXT; -- Google Drive file ID
ALTER TABLE documents ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS watch_active BOOLEAN DEFAULT FALSE;

-- Create indexes for documents table
CREATE INDEX IF NOT EXISTS idx_documents_file_id ON documents(file_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_watch_active ON documents(watch_active);
CREATE INDEX IF NOT EXISTS idx_documents_last_synced_at ON documents(last_synced_at);

-- Create drive_file_watches table
CREATE TABLE IF NOT EXISTS drive_file_watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,  -- same as document_id
  resource_id TEXT NOT NULL, -- from Google response
  expiration TIMESTAMP WITH TIME ZONE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for drive_file_watches table
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_document_id ON drive_file_watches(document_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_project_id ON drive_file_watches(project_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_file_id ON drive_file_watches(file_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_channel_id ON drive_file_watches(channel_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_resource_id ON drive_file_watches(resource_id);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_expiration ON drive_file_watches(expiration);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_is_active ON drive_file_watches(is_active);
CREATE INDEX IF NOT EXISTS idx_drive_file_watches_created_at ON drive_file_watches(created_at);

-- Create unique constraint to prevent duplicate watches for the same file_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_drive_file_watches_file_id_unique ON drive_file_watches(file_id) WHERE is_active = TRUE;

-- Enable RLS on drive_file_watches
ALTER TABLE drive_file_watches ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for drive_file_watches
CREATE POLICY "Users can view own drive file watches" ON drive_file_watches
  FOR SELECT USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

CREATE POLICY "Service can insert drive file watches" ON drive_file_watches
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service can update drive file watches" ON drive_file_watches
  FOR UPDATE USING (true);

CREATE POLICY "Service can delete drive file watches" ON drive_file_watches
  FOR DELETE USING (true);

-- Create drive_webhook_logs table for tracking webhook events
CREATE TABLE IF NOT EXISTS drive_webhook_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  file_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  resource_state TEXT NOT NULL, -- 'update', 'delete', etc.
  webhook_received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  n8n_webhook_sent BOOLEAN DEFAULT FALSE,
  n8n_webhook_response TEXT,
  n8n_webhook_sent_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes for drive_webhook_logs table
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_document_id ON drive_webhook_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_project_id ON drive_webhook_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_file_id ON drive_webhook_logs(file_id);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_resource_state ON drive_webhook_logs(resource_state);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_webhook_received_at ON drive_webhook_logs(webhook_received_at);
CREATE INDEX IF NOT EXISTS idx_drive_webhook_logs_n8n_webhook_sent ON drive_webhook_logs(n8n_webhook_sent);

-- Enable RLS on drive_webhook_logs
ALTER TABLE drive_webhook_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for drive_webhook_logs
CREATE POLICY "Users can view own drive webhook logs" ON drive_webhook_logs
  FOR SELECT USING (
    document_id IN (
      SELECT d.id FROM documents d
      JOIN projects p ON d.project_id = p.id
      WHERE p.created_by = auth.uid()
    )
  );

CREATE POLICY "Service can insert drive webhook logs" ON drive_webhook_logs
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service can update drive webhook logs" ON drive_webhook_logs
  FOR UPDATE USING (true);

-- Create function to update updated_at timestamp for drive_file_watches
CREATE OR REPLACE FUNCTION update_drive_file_watches_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for drive_file_watches updated_at
CREATE TRIGGER trg_update_drive_file_watches_updated_at
  BEFORE UPDATE ON drive_file_watches
  FOR EACH ROW
  EXECUTE FUNCTION update_drive_file_watches_updated_at();

-- Create function to get active drive file watch by file_id
CREATE OR REPLACE FUNCTION get_active_drive_file_watch(search_file_id TEXT)
RETURNS TABLE(
  id UUID,
  document_id UUID,
  project_id UUID,
  file_id TEXT,
  channel_id TEXT,
  resource_id TEXT,
  expiration TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dfw.id,
    dfw.document_id,
    dfw.project_id,
    dfw.file_id,
    dfw.channel_id,
    dfw.resource_id,
    dfw.expiration,
    dfw.is_active
  FROM drive_file_watches dfw
  WHERE dfw.file_id = search_file_id 
    AND dfw.is_active = TRUE
    AND dfw.expiration > NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to deactivate expired watches
CREATE OR REPLACE FUNCTION deactivate_expired_drive_watches()
RETURNS INTEGER AS $$
DECLARE
  affected_rows INTEGER;
BEGIN
  UPDATE drive_file_watches 
  SET is_active = FALSE, updated_at = NOW()
  WHERE expiration < NOW() AND is_active = TRUE;
  
  GET DIAGNOSTICS affected_rows = ROW_COUNT;
  
  -- Also update documents to reflect inactive watches
  UPDATE documents 
  SET watch_active = FALSE, updated_at = NOW()
  WHERE id IN (
    SELECT document_id FROM drive_file_watches 
    WHERE expiration < NOW() AND is_active = FALSE
  );
  
  RETURN affected_rows;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get document info by channel_id
CREATE OR REPLACE FUNCTION get_document_by_channel_id(search_channel_id TEXT)
RETURNS TABLE(
  document_id UUID,
  project_id UUID,
  file_id TEXT,
  title TEXT,
  status TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.id,
    d.project_id,
    d.file_id,
    d.title,
    d.status
  FROM documents d
  WHERE d.id::TEXT = search_channel_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_active_drive_file_watch(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION deactivate_expired_drive_watches() TO authenticated;
GRANT EXECUTE ON FUNCTION get_document_by_channel_id(TEXT) TO authenticated;

-- Grant permissions to service role
GRANT EXECUTE ON FUNCTION get_active_drive_file_watch(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION deactivate_expired_drive_watches() TO service_role;
GRANT EXECUTE ON FUNCTION get_document_by_channel_id(TEXT) TO service_role;

-- Grant table permissions
GRANT ALL ON TABLE drive_file_watches TO authenticated;
GRANT ALL ON TABLE drive_file_watches TO service_role;
GRANT ALL ON TABLE drive_webhook_logs TO authenticated;
GRANT ALL ON TABLE drive_webhook_logs TO service_role;

-- Create a scheduled function to clean up expired watches (optional)
-- This can be set up in Supabase dashboard under Database > Functions > Scheduled Functions
-- SELECT cron.schedule('cleanup-expired-drive-watches', '0 2 * * *', 'SELECT deactivate_expired_drive_watches();'); 