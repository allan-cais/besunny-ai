-- Create email_processing_locks table to prevent duplicate email processing
CREATE TABLE IF NOT EXISTS email_processing_locks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'processing',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_email_processing_locks_message_id ON email_processing_locks(message_id);
CREATE INDEX IF NOT EXISTS idx_email_processing_locks_expires_at ON email_processing_locks(expires_at);

-- Create function to clean up expired locks
CREATE OR REPLACE FUNCTION cleanup_expired_email_locks()
RETURNS void AS $$
BEGIN
    DELETE FROM email_processing_locks 
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update updated_at
CREATE OR REPLACE FUNCTION update_email_processing_locks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_email_processing_locks_updated_at
    BEFORE UPDATE ON email_processing_locks
    FOR EACH ROW
    EXECUTE FUNCTION update_email_processing_locks_updated_at();

-- Add RLS policies
ALTER TABLE email_processing_locks ENABLE ROW LEVEL SECURITY;

-- Allow service role to manage locks
CREATE POLICY "Service role can manage email processing locks" ON email_processing_locks
    FOR ALL USING (auth.role() = 'service_role');

-- Allow authenticated users to read locks (for debugging)
CREATE POLICY "Authenticated users can read email processing locks" ON email_processing_locks
    FOR SELECT USING (auth.role() = 'authenticated');
