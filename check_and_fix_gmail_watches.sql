-- Check and fix gmail_watches table RLS issues
-- This will resolve the 406 (Not Acceptable) error

-- First, check if RLS is enabled and what policies exist
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE tablename = 'gmail_watches';

-- Check existing policies
SELECT 
    schemaname, 
    tablename, 
    policyname, 
    permissive, 
    roles, 
    cmd, 
    qual, 
    with_check
FROM pg_policies 
WHERE tablename = 'gmail_watches';

-- Check if the table exists and its structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'gmail_watches'
ORDER BY ordinal_position;

-- If no policies exist, create them
DO $$
BEGIN
    -- Check if policies exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'gmail_watches' 
        AND policyname = 'Users can view own gmail watches'
    ) THEN
        -- Create SELECT policy
        EXECUTE 'CREATE POLICY "Users can view own gmail watches" ON gmail_watches
                FOR SELECT USING (
                    user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
                )';
        RAISE NOTICE 'Created SELECT policy for gmail_watches';
    ELSE
        RAISE NOTICE 'SELECT policy already exists for gmail_watches';
    END IF;

    -- Check if INSERT policy exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'gmail_watches' 
        AND policyname = 'Users can insert own gmail watches'
    ) THEN
        -- Create INSERT policy
        EXECUTE 'CREATE POLICY "Users can insert own gmail watches" ON gmail_watches
                FOR INSERT WITH CHECK (
                    user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
                )';
        RAISE NOTICE 'Created INSERT policy for gmail_watches';
    ELSE
        RAISE NOTICE 'INSERT policy already exists for gmail_watches';
    END IF;

    -- Check if UPDATE policy exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'gmail_watches' 
        AND policyname = 'Users can update own gmail watches'
    ) THEN
        -- Create UPDATE policy
        EXECUTE 'CREATE POLICY "Users can update own gmail watches" ON gmail_watches
                FOR UPDATE USING (
                    user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
                )';
        RAISE NOTICE 'Created UPDATE policy for gmail_watches';
    ELSE
        RAISE NOTICE 'UPDATE policy already exists for gmail_watches';
    END IF;

    -- Check if DELETE policy exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'gmail_watches' 
        AND policyname = 'Users can delete own gmail watches'
    ) THEN
        -- Create DELETE policy
        EXECUTE 'CREATE POLICY "Users can delete own gmail watches" ON gmail_watches
                FOR DELETE USING (
                    user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
                )';
        RAISE NOTICE 'Created DELETE policy for gmail_watches';
    ELSE
        RAISE NOTICE 'DELETE policy already exists for gmail_watches';
    END IF;
END $$;

-- Verify all policies were created
SELECT 
    schemaname, 
    tablename, 
    policyname, 
    permissive, 
    roles, 
    cmd, 
    qual, 
    with_check
FROM pg_policies 
WHERE tablename = 'gmail_watches'
ORDER BY policyname;
