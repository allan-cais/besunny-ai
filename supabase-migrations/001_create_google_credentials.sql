-- Create google_credentials table for storing Google OAuth tokens
-- Note: This table already exists in your Supabase instance
-- This migration is for reference only

CREATE TABLE IF NOT EXISTS google_credentials (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  access_token TEXT,
  refresh_token TEXT,
  token_type TEXT,
  expires_at TIMESTAMP,
  scope TEXT,
  created_at TIMESTAMP DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE google_credentials ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only access their own credentials
CREATE POLICY "Users can view own google credentials" ON google_credentials
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own google credentials" ON google_credentials
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own google credentials" ON google_credentials
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own google credentials" ON google_credentials
  FOR DELETE USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_google_credentials_user_id ON google_credentials(user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_google_credentials_updated_at 
  BEFORE UPDATE ON google_credentials 
  FOR EACH ROW 
  EXECUTE FUNCTION update_updated_at_column(); 