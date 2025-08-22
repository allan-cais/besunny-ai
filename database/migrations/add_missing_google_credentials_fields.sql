-- Migration: Add missing fields to google_credentials table
-- Date: 2024-12-19
-- Description: Add missing fields needed for proper OAuth token storage

-- Add missing fields to google_credentials table
ALTER TABLE google_credentials 
ADD COLUMN IF NOT EXISTS expires_in INTEGER,
ADD COLUMN IF NOT EXISTS token_uri TEXT,
ADD COLUMN IF NOT EXISTS client_id TEXT,
ADD COLUMN IF NOT EXISTS client_secret TEXT,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();

-- Add comment explaining the new fields
COMMENT ON COLUMN google_credentials.expires_in IS 'Token expiration time in seconds';
COMMENT ON COLUMN google_credentials.token_uri IS 'Google OAuth token endpoint URI';
COMMENT ON COLUMN google_credentials.client_id IS 'Google OAuth client ID';
COMMENT ON COLUMN google_credentials.client_secret IS 'Google OAuth client secret';
COMMENT ON COLUMN google_credentials.updated_at IS 'Last update timestamp';

-- Create index on updated_at for efficient queries
CREATE INDEX IF NOT EXISTS idx_google_credentials_updated_at ON google_credentials(updated_at);

-- Update existing records to set updated_at to created_at if it's null
UPDATE google_credentials 
SET updated_at = created_at 
WHERE updated_at IS NULL;
