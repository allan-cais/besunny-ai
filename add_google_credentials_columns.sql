-- Add missing columns to google_credentials table for soft delete functionality
-- Note: updated_at column already exists, so we're only adding the new ones

ALTER TABLE google_credentials 
ADD COLUMN status VARCHAR(20) DEFAULT 'connected',
ADD COLUMN disconnected_at TIMESTAMP;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'google_credentials' 
AND column_name IN ('status', 'disconnected_at', 'updated_at')
ORDER BY column_name;
