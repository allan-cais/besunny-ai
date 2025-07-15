-- Add virtual email address support
-- This migration adds username management and email processing capabilities

-- Add username column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS username_set_at TIMESTAMP WITH TIME ZONE;

-- Add index for username lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create table to track email processing
CREATE TABLE IF NOT EXISTS email_processing_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  gmail_message_id TEXT NOT NULL,
  inbound_address TEXT NOT NULL,
  extracted_username TEXT,
  subject TEXT,
  sender TEXT,
  received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  processed_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed', 'user_not_found')),
  error_message TEXT,
  document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
  n8n_webhook_sent BOOLEAN DEFAULT FALSE,
  n8n_webhook_response TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add indexes for email processing
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_user_id ON email_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_gmail_message_id ON email_processing_logs(gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_status ON email_processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_processing_logs_received_at ON email_processing_logs(received_at);

-- Enable RLS on email_processing_logs
ALTER TABLE email_processing_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for email_processing_logs
CREATE POLICY "Users can view own email processing logs" ON email_processing_logs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can insert email processing logs" ON email_processing_logs
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service can update email processing logs" ON email_processing_logs
  FOR UPDATE USING (true);

-- Create function to extract username from email address
CREATE OR REPLACE FUNCTION extract_username_from_email(email_address TEXT)
RETURNS TEXT AS $$
DECLARE
  username_part TEXT;
BEGIN
  -- Extract the part before @
  username_part := split_part(email_address, '@', 1);
  
  -- Check if it contains a plus sign (plus-addressing)
  IF username_part LIKE '%+%' THEN
    -- Extract the part after the plus sign
    username_part := split_part(username_part, '+', 2);
  END IF;
  
  -- Validate that the extracted username is alphanumeric only
  IF username_part !~ '^[a-zA-Z0-9]+$' THEN
    RETURN NULL;
  END IF;
  
  RETURN username_part;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function to get user by username
CREATE OR REPLACE FUNCTION get_user_by_username(search_username TEXT)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  name TEXT,
  username TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    u.id,
    u.email,
    u.name,
    u.username
  FROM users u
  WHERE u.username = search_username;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to set username for user
CREATE OR REPLACE FUNCTION set_user_username(user_uuid UUID, new_username TEXT)
RETURNS BOOLEAN AS $$
DECLARE
  username_exists BOOLEAN;
BEGIN
  -- Check if username is already taken
  SELECT EXISTS(SELECT 1 FROM users WHERE username = new_username AND id != user_uuid) INTO username_exists;
  
  IF username_exists THEN
    RETURN FALSE;
  END IF;
  
  -- Update the user's username
  UPDATE users 
  SET username = new_username, username_set_at = NOW()
  WHERE id = user_uuid;
  
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION extract_username_from_email(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_by_username(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION set_user_username(UUID, TEXT) TO authenticated;

-- Add trigger to update username_set_at when username is set
CREATE OR REPLACE FUNCTION update_username_set_at()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.username IS NOT NULL AND (OLD.username IS NULL OR OLD.username != NEW.username) THEN
    NEW.username_set_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_username_set_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_username_set_at(); 