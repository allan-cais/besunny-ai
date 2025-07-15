-- Add Google OAuth login support to existing google_credentials table
-- This migration extends the table to support both integration and login use cases

-- Add new columns for OAuth login functionality
ALTER TABLE google_credentials ADD COLUMN IF NOT EXISTS login_provider BOOLEAN DEFAULT FALSE;
ALTER TABLE google_credentials ADD COLUMN IF NOT EXISTS google_user_id TEXT;
ALTER TABLE google_credentials ADD COLUMN IF NOT EXISTS google_name TEXT;
ALTER TABLE google_credentials ADD COLUMN IF NOT EXISTS google_picture TEXT;
ALTER TABLE google_credentials ADD COLUMN IF NOT EXISTS login_created_at TIMESTAMP WITH TIME ZONE DEFAULT now();

-- Add index for Google user ID lookups
CREATE INDEX IF NOT EXISTS idx_google_credentials_google_user_id ON google_credentials(google_user_id);

-- Add index for login provider lookups
CREATE INDEX IF NOT EXISTS idx_google_credentials_login_provider ON google_credentials(login_provider);

-- Create a function to handle Google OAuth login user creation
CREATE OR REPLACE FUNCTION handle_google_oauth_login(
  google_user_id TEXT,
  google_email TEXT,
  google_name TEXT,
  google_picture TEXT,
  access_token TEXT,
  refresh_token TEXT,
  token_type TEXT,
  expires_at TIMESTAMP WITH TIME ZONE,
  scope TEXT
) RETURNS UUID AS $$
DECLARE
  user_id UUID;
  existing_user_id UUID;
BEGIN
  -- Check if a user already exists with this Google user ID
  SELECT gc.user_id INTO existing_user_id
  FROM google_credentials gc
  WHERE gc.google_user_id = handle_google_oauth_login.google_user_id
    AND gc.login_provider = TRUE;
  
  IF existing_user_id IS NOT NULL THEN
    -- Update existing credentials
    UPDATE google_credentials
    SET 
      access_token = handle_google_oauth_login.access_token,
      refresh_token = handle_google_oauth_login.refresh_token,
      token_type = handle_google_oauth_login.token_type,
      expires_at = handle_google_oauth_login.expires_at,
      scope = handle_google_oauth_login.scope,
      google_email = handle_google_oauth_login.google_email,
      google_name = handle_google_oauth_login.google_name,
      google_picture = handle_google_oauth_login.google_picture,
      updated_at = NOW()
    WHERE user_id = existing_user_id;
    
    RETURN existing_user_id;
  ELSE
    -- Check if a user exists with this email (for linking existing accounts)
    SELECT id INTO existing_user_id
    FROM auth.users
    WHERE email = handle_google_oauth_login.google_email;
    
    IF existing_user_id IS NOT NULL THEN
      -- Link existing user account to Google OAuth
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        existing_user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN existing_user_id;
    ELSE
      -- Create new user account
      INSERT INTO auth.users (
        email,
        email_confirmed_at,
        raw_user_meta_data
      ) VALUES (
        handle_google_oauth_login.google_email,
        NOW(),
        jsonb_build_object(
          'name', handle_google_oauth_login.google_name,
          'picture', handle_google_oauth_login.google_picture,
          'provider', 'google'
        )
      ) RETURNING id INTO user_id;
      
      -- Insert Google credentials
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN user_id;
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION handle_google_oauth_login(UUID) TO authenticated;

-- Create a function to get user by Google user ID
CREATE OR REPLACE FUNCTION get_user_by_google_id(google_user_id TEXT)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  name TEXT,
  picture TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    gc.user_id,
    gc.google_email,
    gc.google_name,
    gc.google_picture
  FROM google_credentials gc
  WHERE gc.google_user_id = get_user_by_google_id.google_user_id
    AND gc.login_provider = TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_user_by_google_id(TEXT) TO authenticated; 