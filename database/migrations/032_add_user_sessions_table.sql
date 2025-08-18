-- Migration 032: Add user_sessions table for OAuth session management
-- This table stores user OAuth sessions and tokens for authentication

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT UNIQUE NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add comments
COMMENT ON TABLE user_sessions IS 'Stores user OAuth sessions and authentication tokens';
COMMENT ON COLUMN user_sessions.session_id IS 'Unique session identifier';
COMMENT ON COLUMN user_sessions.access_token IS 'OAuth access token for the session';
COMMENT ON COLUMN user_sessions.refresh_token IS 'OAuth refresh token for the session';
COMMENT ON COLUMN user_sessions.expires_at IS 'When the session expires';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- Enable Row Level Security
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON user_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON user_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON user_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Create trigger for updated_at column
CREATE TRIGGER update_user_sessions_updated_at 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add expires_at column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN google_credentials.expires_at IS 'When the OAuth tokens expire';
    END IF;
END $$;

-- Add expires_in column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'expires_in'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN expires_in INTEGER;
        COMMENT ON COLUMN google_credentials.expires_in IS 'OAuth token expiration time in seconds';
    END IF;
END $$;

-- Add token_type column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'token_type'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN token_type TEXT DEFAULT 'Bearer';
        COMMENT ON COLUMN google_credentials.token_type IS 'Type of OAuth token';
    END IF;
END $$;

-- Add scope column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'scope'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN scope TEXT;
        COMMENT ON COLUMN google_credentials.scope IS 'OAuth token scope';
    END IF;
END $$;

-- Add token_uri column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'token_uri'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN token_uri TEXT DEFAULT 'https://oauth2.googleapis.com/token';
        COMMENT ON COLUMN google_credentials.token_uri IS 'OAuth token URI';
    END IF;
END $$;

-- Add client_id column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'client_id'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN client_id TEXT;
        COMMENT ON COLUMN google_credentials.client_id IS 'OAuth client ID';
    END IF;
END $$;

-- Add client_secret column to google_credentials if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'google_credentials' 
        AND column_name = 'client_secret'
    ) THEN
        ALTER TABLE google_credentials ADD COLUMN client_secret TEXT;
        COMMENT ON COLUMN google_credentials.client_secret IS 'OAuth client secret';
    END IF;
END $$;

-- Create view for active sessions
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT 
    us.id,
    us.user_id,
    us.session_id,
    us.access_token,
    us.refresh_token,
    us.expires_at,
    us.is_active,
    us.created_at,
    us.updated_at,
    u.email as user_email,
    u.username
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.is_active = true 
  AND (us.expires_at IS NULL OR us.expires_at > now());

-- Add comment to view
COMMENT ON VIEW active_user_sessions IS 'View of all active user OAuth sessions';

-- Create view for expired sessions
CREATE OR REPLACE VIEW expired_user_sessions AS
SELECT 
    us.id,
    us.user_id,
    us.session_id,
    us.access_token,
    us.refresh_token,
    us.expires_at,
    us.is_active,
    us.created_at,
    us.updated_at,
    u.email as user_email,
    u.username
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.expires_at IS NOT NULL 
  AND us.expires_at <= now();

-- Add comment to view
COMMENT ON VIEW expired_user_sessions IS 'View of all expired user OAuth sessions';
