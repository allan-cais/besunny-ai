# Google OAuth Login Implementation

This document describes the implementation of Google OAuth login functionality for the Kirit Askuno application.

## Overview

The application now supports two types of Google OAuth integration:

1. **Google OAuth Login** - Users can sign up and sign in using their Google account
2. **Google Workspace Integration** - Users can connect their Google Workspace (Gmail, Drive, Calendar) for data integration

## Architecture

### Database Schema

The `google_credentials` table has been extended with new columns to support both login and integration use cases:

- `login_provider` (BOOLEAN) - Indicates if this is a login provider (true) or workspace integration (false)
- `google_user_id` (TEXT) - Google's unique user ID for login providers
- `google_name` (TEXT) - User's display name from Google
- `google_picture` (TEXT) - User's profile picture URL from Google
- `login_created_at` (TIMESTAMP) - When the login provider was created

### Edge Functions

#### `google-oauth-login`
Handles the Google OAuth login flow:
- Exchanges authorization code for tokens
- Creates or links user accounts
- Returns a session for the authenticated user

#### `exchange-google-token` (existing)
Handles Google Workspace integration:
- Exchanges authorization code for tokens with full workspace scopes
- Stores credentials for Gmail, Drive, and Calendar access

## User Flow

### Google OAuth Login Flow

1. User clicks "Continue with Google" on login/signup page
2. User is redirected to Google OAuth consent screen
3. Google redirects back to `/oauth-login-callback` with authorization code
4. Edge function exchanges code for tokens and user info
5. User account is created or linked
6. User is redirected to dashboard with active session

### Google Workspace Integration Flow

1. User navigates to integrations page
2. If user has Google OAuth login, they see "ADD WORKSPACE INTEGRATION" button
3. If user has no Google connection, they see "CONNECT GOOGLE ACCOUNT" button
4. User is redirected to Google OAuth with workspace scopes
5. Google redirects back to `/integrations` with authorization code
6. Edge function exchanges code for tokens and stores workspace credentials
7. User can now access Gmail, Drive, and Calendar data

## Environment Variables

Add these environment variables to your Supabase project:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Redirect URIs
GOOGLE_REDIRECT_URI=https://your-domain.com/integrations
GOOGLE_LOGIN_REDIRECT_URI=https://your-domain.com/oauth-login-callback
```

## Google Cloud Console Setup

1. Create a new OAuth 2.0 client in Google Cloud Console
2. Add authorized redirect URIs:
   - `https://your-domain.com/oauth-login-callback` (for login)
   - `https://your-domain.com/integrations` (for workspace integration)
3. Configure OAuth consent screen with required scopes:
   - `userinfo.email` and `userinfo.profile` (for login)
   - `gmail.modify`, `drive`, `calendar` (for workspace integration)

## Frontend Components

### Updated Components

- `AuthProvider` - Added `signInWithGoogle` method
- `LoginForm` - Added "Continue with Google" button
- `SignUpForm` - Added "Continue with Google" button
- `IntegrationsPage` - Updated to show different UI for login vs integration

### New Components

- `OAuthLoginCallback` - Handles Google OAuth login callback

## Security Considerations

1. **Token Storage** - Access tokens are stored encrypted in the database
2. **Scope Separation** - Login and integration use different OAuth scopes
3. **Account Linking** - Existing email accounts are automatically linked to Google OAuth
4. **Session Management** - Sessions are created server-side for security

## Migration

The implementation is backward compatible:
- Existing Google Workspace integrations continue to work
- New login functionality is additive
- Database migration extends existing table structure

## Testing

1. Test Google OAuth login flow
2. Test account linking (existing email + Google OAuth)
3. Test workspace integration for OAuth login users
4. Test scope updates and reconnection flows
5. Test error handling and edge cases 