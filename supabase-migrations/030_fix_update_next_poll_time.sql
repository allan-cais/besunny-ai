-- Fix update_next_poll_time function that references removed next_poll_time field
-- This function is causing errors when updating meetings

-- Drop the problematic trigger first
DROP TRIGGER IF EXISTS trg_update_next_poll_time ON meetings;

-- Fix the update_next_poll_time function to not reference removed fields
CREATE OR REPLACE FUNCTION update_next_poll_time()
RETURNS TRIGGER AS $$
BEGIN
  -- Since next_poll_time field was removed, we just return NEW without modification
  -- The polling logic has been simplified and doesn't need this trigger anymore
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = 'public';

-- Recreate the trigger but only for bot_status changes (not project_id changes)
CREATE TRIGGER trg_update_next_poll_time 
BEFORE UPDATE ON meetings 
FOR EACH ROW 
WHEN (OLD.bot_status IS DISTINCT FROM NEW.bot_status)
EXECUTE FUNCTION update_next_poll_time(); 