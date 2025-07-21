-- Enable real-time subscriptions for meetings table
-- This allows the frontend to receive real-time updates when meeting data changes

-- Add meetings table to the real-time publication
ALTER PUBLICATION "supabase_realtime" ADD TABLE "public"."meetings";

-- Verify the table is now included in real-time
-- You can check this in the Supabase dashboard under Database > Replication 