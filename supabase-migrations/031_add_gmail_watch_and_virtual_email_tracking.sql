-- Add Gmail watch and virtual email detection tracking
-- This migration adds support for monitoring Gmail for virtual email usage

-- Track Gmail watches for users
CREATE TABLE IF NOT EXISTS gmail_watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  history_id TEXT NOT NULL,
  expiration TIMESTAMP WITH TIME ZONE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  watch_type TEXT DEFAULT 'polling' CHECK (watch_type IN ('push', 'polling', 'hybrid')),
  last_webhook_received TIMESTAMP WITH TIME ZONE,
  last_poll_at TIMESTAMP WITH TIME ZONE,
  webhook_failures INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  
  UNIQUE(user_email)
);

-- Track virtual email detections
CREATE TABLE IF NOT EXISTS virtual_email_detections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  virtual_email TEXT NOT NULL,
  username TEXT NOT NULL,
  email_type TEXT NOT NULL CHECK (email_type IN ('to', 'cc')),
  gmail_message_id TEXT NOT NULL,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  
  UNIQUE(gmail_message_id, virtual_email)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_gmail_watches_user_email ON gmail_watches(user_email);
CREATE INDEX IF NOT EXISTS idx_gmail_watches_active ON gmail_watches(is_active);
CREATE INDEX IF NOT EXISTS idx_virtual_email_detections_user_id ON virtual_email_detections(user_id);
CREATE INDEX IF NOT EXISTS idx_virtual_email_detections_username ON virtual_email_detections(username);
CREATE INDEX IF NOT EXISTS idx_virtual_email_detections_detected_at ON virtual_email_detections(detected_at);

-- Enable RLS
ALTER TABLE gmail_watches ENABLE ROW LEVEL SECURITY;
ALTER TABLE virtual_email_detections ENABLE ROW LEVEL SECURITY;

-- RLS Policies for gmail_watches
CREATE POLICY "Service can manage all gmail watches" ON gmail_watches
  FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for virtual_email_detections
CREATE POLICY "Users can view own virtual email detections" ON virtual_email_detections
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can insert virtual email detections" ON virtual_email_detections
  FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Function to clean up expired Gmail watches
CREATE OR REPLACE FUNCTION cleanup_expired_gmail_watches()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE gmail_watches 
  SET is_active = FALSE, updated_at = now()
  WHERE expiration < now() AND is_active = TRUE;
END;
$$;

-- Function to get user's virtual email address
CREATE OR REPLACE FUNCTION get_user_virtual_email(user_uuid UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  user_username TEXT;
BEGIN
  SELECT username INTO user_username
  FROM users
  WHERE id = user_uuid;
  
  IF user_username IS NULL THEN
    RETURN NULL;
  END IF;
  
  RETURN 'ai+' || user_username || '@besunny.ai';
END;
$$;

-- Function to extract username from virtual email
CREATE OR REPLACE FUNCTION extract_username_from_virtual_email(virtual_email TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  -- Extract username from ai+username@besunny.ai format
  IF virtual_email ~ '^ai\+[a-zA-Z0-9._-]+@besunny\.ai$' THEN
    RETURN substring(virtual_email from '^ai\+([a-zA-Z0-9._-]+)@besunny\.ai$');
  END IF;
  
  RETURN NULL;
END;
$$;

-- Add comments
COMMENT ON TABLE gmail_watches IS 'Tracks Gmail watch subscriptions for monitoring virtual email usage';
COMMENT ON TABLE virtual_email_detections IS 'Records when virtual email addresses are detected in Gmail messages';
COMMENT ON FUNCTION get_user_virtual_email IS 'Returns the virtual email address for a given user';
COMMENT ON FUNCTION extract_username_from_virtual_email IS 'Extracts username from virtual email address format'; 