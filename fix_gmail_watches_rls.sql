-- Fix RLS policies for gmail_watches table
-- This will resolve the 406 (Not Acceptable) error

-- Drop existing policies if they exist (optional)
DROP POLICY IF EXISTS "Users can view own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can insert own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can update own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can delete own gmail watches" ON gmail_watches;

-- Create RLS policies for gmail_watches table
-- Users can view their own Gmail watch records
CREATE POLICY "Users can view own gmail watches" ON gmail_watches
    FOR SELECT USING (
        user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Users can insert their own Gmail watch records
CREATE POLICY "Users can insert own gmail watches" ON gmail_watches
    FOR INSERT WITH CHECK (
        user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Users can update their own Gmail watch records
CREATE POLICY "Users can update own gmail watches" ON gmail_watches
    FOR UPDATE USING (
        user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Users can delete their own Gmail watch records
CREATE POLICY "Users can delete own gmail watches" ON gmail_watches
    FOR DELETE USING (
        user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- Verify the policies were created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename = 'gmail_watches';
