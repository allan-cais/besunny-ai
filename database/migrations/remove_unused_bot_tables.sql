-- Remove unused bot tables
-- This migration removes the 'bots' and 'bot_scheduling_logs' tables
-- that are not used in the current codebase

-- Drop the unused tables
DROP TABLE IF EXISTS bot_scheduling_logs CASCADE;
DROP TABLE IF EXISTS bots CASCADE;

-- Add comment for documentation
COMMENT ON SCHEMA public IS 'Removed unused bot tables: bots, bot_scheduling_logs - replaced by meeting_bots table';
