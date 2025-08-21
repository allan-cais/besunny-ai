-- Fix RLS policies for gmail_watches table
-- This table stores Gmail watch subscriptions and needs proper user access control

-- First, ensure RLS is enabled
ALTER TABLE gmail_watches ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies (if they exist)
DROP POLICY IF EXISTS "Users can view own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can insert own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can update own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Users can delete own gmail watches" ON gmail_watches;
DROP POLICY IF EXISTS "Service can manage all gmail watches" ON gmail_watches;

-- Create policies for user access based on email
-- Users can only access gmail_watches where user_email matches their authenticated email
CREATE POLICY "Users can view own gmail watches" ON gmail_watches
    FOR SELECT USING (
        user_email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
    );

CREATE POLICY "Users can insert own gmail watches" ON gmail_watches
    FOR INSERT WITH CHECK (
        user_email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
    );

CREATE POLICY "Users can update own gmail watches" ON gmail_watches
    FOR UPDATE USING (
        user_email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
    );

CREATE POLICY "Users can delete own gmail watches" ON gmail_watches
    FOR DELETE USING (
        user_email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
    );

-- Service role policy for backend operations
CREATE POLICY "Service can manage all gmail watches" ON gmail_watches
    FOR ALL USING (
        (SELECT auth.jwt() ->> 'role') = 'service_role'
    );

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'gmail_watches';
