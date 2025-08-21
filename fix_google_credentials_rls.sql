-- Fix RLS policies for google_credentials table
-- This table stores Google OAuth tokens and needs proper user access control

-- First, ensure RLS is enabled
ALTER TABLE google_credentials ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies (if they exist)
DROP POLICY IF EXISTS "Users can view own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Users can insert own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Users can update own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Users can delete own google credentials" ON google_credentials;
DROP POLICY IF EXISTS "Service can manage all google credentials" ON google_credentials;

-- Create policies for user access based on user_id
-- Users can only access google_credentials where user_id matches their authenticated user ID
CREATE POLICY "Users can view own google credentials" ON google_credentials
    FOR SELECT USING (
        user_id = (SELECT auth.uid())
    );

CREATE POLICY "Users can insert own google credentials" ON google_credentials
    FOR INSERT WITH CHECK (
        user_id = (SELECT auth.uid())
    );

CREATE POLICY "Users can update own google credentials" ON google_credentials
    FOR UPDATE USING (
        user_id = (SELECT auth.uid())
    );

CREATE POLICY "Users can delete own google credentials" ON google_credentials
    FOR DELETE USING (
        user_id = (SELECT auth.uid())
    );

-- Service role policy for backend operations
CREATE POLICY "Service can manage all google credentials" ON google_credentials
    FOR ALL USING (
        (SELECT auth.jwt() ->> 'role') = 'service_role'
    );

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'google_credentials';
