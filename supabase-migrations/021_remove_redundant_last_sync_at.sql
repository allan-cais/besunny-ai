-- Remove redundant last_sync_at column from calendar_webhooks
-- The updated_at column (automatically updated by trigger) serves the same purpose

-- Drop the last_sync_at column
ALTER TABLE calendar_webhooks DROP COLUMN IF EXISTS last_sync_at;

-- Update any references to use updated_at instead
-- This migration removes the redundant column and relies on the existing updated_at trigger 