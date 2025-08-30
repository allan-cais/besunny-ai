-- Create audit table for Google credentials to track connection/disconnection history
CREATE TABLE IF NOT EXISTS google_credentials_audit (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(50) NOT NULL,
    previous_status VARCHAR(20),
    disconnected_at TIMESTAMP,
    had_access_token BOOLEAN,
    had_refresh_token BOOLEAN,
    scope TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_google_credentials_audit_user_id ON google_credentials_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_google_credentials_audit_action ON google_credentials_audit(action);
CREATE INDEX IF NOT EXISTS idx_google_credentials_audit_created_at ON google_credentials_audit(created_at);

-- Verify the table was created
SELECT table_name, column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'google_credentials_audit'
ORDER BY ordinal_position;
