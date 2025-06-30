# New Google OAuth Implementation

## Overview

This is a fresh, modern, and robust Google OAuth2 implementation for Gmail and Google Drive integration. The implementation uses Supabase Edge Functions for secure token exchange and maintains the existing `google_credentials` table structure.

## Architecture

### Frontend (React + TypeScript)
- **Integrations Page**: Clean UI for connecting/disconnecting Google accounts
- **OAuth Callback**: Handles Google OAuth redirects
- **State Management**: Robust error handling and loading states

### Backend (Supabase Edge Functions)
- **exchange-google-token**: Secure token exchange and credential storage
- **Database**: Uses existing `google_credentials` table with RLS policies

### Security Features
- JWT-based authentication for Edge Function calls
- Row Level Security (RLS) on database
- Token revocation on disconnect
- Secure credential storage

## Setup Instructions

### 1. Environment Variables

Add these to your `.env` file:

```env
# Supabase Configuration
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Google OAuth Configuration (Frontend)
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GOOGLE_CLIENT_SECRET=your-google-client-secret
VITE_GOOGLE_REDIRECT_URI=http://localhost:5173/integrations
```

**Important:** Variables prefixed with `VITE_` are accessible by the frontend React app, while variables without the prefix are only accessible by backend services (like Edge Functions).

### 2. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable APIs:
   - Gmail API
   - Google Drive API
   - Google+ API (for user info)
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5173/integrations`
   - Scopes: `gmail.modify`, `drive.readonly`, `userinfo.email`, `pubsub`

### 3. Deploy Edge Function

```bash
# Deploy the exchange-google-token function
supabase functions deploy exchange-google-token

# Set environment variables for the function (no VITE_ prefix for backend)
supabase secrets set GOOGLE_CLIENT_ID=your-client-id
supabase secrets set GOOGLE_CLIENT_SECRET=your-client-secret
supabase secrets set GOOGLE_REDIRECT_URI=http://localhost:5173/integrations
```

**Note:** Edge Functions use environment variables without the `VITE_` prefix, which are set as Supabase secrets.

### 4. Test the Implementation

```bash
# Run the test script
node test-new-google-oauth.js
```

## OAuth Flow

1. **User clicks "Connect Google Account"**
   - Frontend generates OAuth URL with required scopes
   - User is redirected to Google for authorization

2. **Google redirects back**
   - Google redirects to `/integrations` with authorization code
   - Frontend extracts code and state parameters

3. **Token Exchange**
   - Frontend calls Edge Function with authorization code
   - Edge Function exchanges code for access/refresh tokens
   - Credentials are stored in Supabase database

4. **Success**
   - User sees connected status
   - Can disconnect or refresh status

## API Endpoints

### Edge Function
- **POST** `/functions/v1/exchange-google-token`
  - Exchanges authorization code for tokens
  - Stores credentials in database
  - Returns success/error response

### Frontend Routes
- **GET** `/integrations` - Main integrations page
- **GET** `/oauth/callback` - OAuth redirect handler

## Database Schema

Uses existing `google_credentials` table:

```sql
CREATE TABLE google_credentials (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  access_token TEXT,
  refresh_token TEXT,
  token_type TEXT,
  expires_at TIMESTAMP,
  scope TEXT,
  google_email TEXT,
  created_at TIMESTAMP DEFAULT now()
);
```

## Features

### ✅ Implemented
- Clean, modern UI with loading states
- Secure token exchange via Edge Function
- Token revocation on disconnect
- Error handling and user feedback
- Status checking and refresh
- Responsive design with dark mode

### 🔄 OAuth Scopes
- `gmail.modify` - Read and modify Gmail
- `drive.readonly` - Read Google Drive files
- `userinfo.email` - Get user email
- `pubsub` - Google Pub/Sub access

### 🛡️ Security
- JWT authentication for API calls
- Row Level Security (RLS) policies
- Token revocation at Google
- Secure credential storage
- State parameter validation

## Troubleshooting

### Common Issues

1. **"OAuth configuration missing"**
   - Check environment variables are set
   - Verify Edge Function secrets are configured

2. **"Invalid token"**
   - Ensure user is authenticated
   - Check JWT token is valid

3. **"Failed to exchange token"**
   - Verify Google OAuth credentials
   - Check redirect URI matches exactly

4. **"Database error"**
   - Verify RLS policies are configured
   - Check service role key permissions

### Debug Mode

Enable detailed logging in the Edge Function by checking Supabase logs:

```bash
supabase functions logs exchange-google-token
```

### Testing

Use the provided test script:

```bash
node test-new-google-oauth.js
```

## Migration from Old Implementation

This implementation is a complete rebuild that:

1. **Keeps** the existing `google_credentials` table
2. **Rebuilds** the Edge Function with modern practices
3. **Refreshes** the frontend with clean, maintainable code
4. **Maintains** the same UI/UX design
5. **Improves** error handling and state management

## Next Steps

1. Deploy the Edge Function
2. Test the complete OAuth flow
3. Verify token exchange and storage
4. Test disconnect functionality
5. Monitor for any issues

## Support

If you encounter issues:

1. Check the test script output
2. Review Edge Function logs
3. Verify environment variables
4. Test with a fresh Google account
5. Check browser console for errors 