# Google OAuth Integration Setup Guide

This guide will help you set up Google OAuth2 integration for Gmail and Google Drive access in your application.

## Prerequisites

- Google Cloud Console account
- Supabase project with service role key
- n8n instance (optional, for data ingestion workflows)

## Step 1: Google Cloud Console Setup

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for and enable:
     - "Gmail API"
     - "Google Drive API"
     - "Google+ API" (for user info)

### 1.2 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Configure the OAuth consent screen:
   - Add your domain to authorized domains
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/pubsub`
     - `https://www.googleapis.com/auth/calendar.readonly`
     - `https://www.googleapis.com/auth/contacts.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/drive`
5. Add authorized redirect URIs:
   - `http://localhost:3001/api/oauth/google/callback` (for development)
   - `https://yourdomain.com/api/oauth/google/callback` (for production)
6. Save the Client ID and Client Secret

## Step 2: Environment Variables

### 2.1 Server Environment Variables

Create a `.env` file in the `server/` directory:

```env
# Server Configuration
PORT=3001

# Frontend URL for OAuth redirects
FRONTEND_URL=http://localhost:5173

# N8N Webhook Configuration
N8N_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-rag-webhook

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3001/api/oauth/google/callback

# N8N Webhook for Google Integration
N8N_GOOGLE_WEBHOOK_URL=https://n8n.yourdomain.com/webhook/start-ingestion
```

### 2.2 Frontend Environment Variables

Create a `.env.local` file in the root directory:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_API_URL=http://localhost:3001
```

## Step 3: Database Setup

### 3.1 Existing Table Schema

The `google_credentials` table already exists in your Supabase instance with the following structure:

```sql
CREATE TABLE google_credentials (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  access_token TEXT,
  refresh_token TEXT,
  token_type TEXT,
  expires_at TIMESTAMP,
  scope TEXT,
  created_at TIMESTAMP DEFAULT now()
);
```

### 3.2 Enable Row Level Security (if not already enabled)

If RLS is not already enabled on the table, run the following in your Supabase SQL editor:

```sql
-- Enable Row Level Security
ALTER TABLE google_credentials ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own google credentials" ON google_credentials
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own google credentials" ON google_credentials
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own google credentials" ON google_credentials
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own google credentials" ON google_credentials
  FOR DELETE USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_google_credentials_user_id ON google_credentials(user_id);
```

## Step 4: Install Dependencies

### 4.1 Server Dependencies

```bash
cd server
npm install axios
```

### 4.2 Frontend Dependencies

The frontend should already have all required dependencies.

## Step 5: Start the Application

### 5.1 Start the Server

```bash
cd server
npm run dev
```

### 5.2 Start the Frontend

```bash
npm run dev
```

## Step 6: Test the Integration

1. Navigate to your application and log in
2. Click on your user avatar in the top right
3. Click "INTEGRATIONS" from the dropdown menu
4. Click "CONNECT GOOGLE ACCOUNT"
5. Complete the Google OAuth flow
6. Verify that the integration shows as "CONNECTED"

## API Endpoints

### OAuth Flow

- `GET /api/oauth/google` - Initiates Google OAuth flow
- `GET /api/oauth/google/callback` - Handles OAuth callback

### Management

- `GET /api/oauth/google/status/:userId` - Get connection status
- `DELETE /api/oauth/google/disconnect/:userId` - Disconnect Google account

## Security Considerations

1. **Service Role Key**: The server uses Supabase service role key to bypass RLS for OAuth operations. Keep this key secure.

2. **Token Storage**: Access tokens and refresh tokens are encrypted in the database.

3. **RLS Policies**: Row Level Security ensures users can only access their own credentials.

4. **HTTPS**: In production, always use HTTPS for OAuth redirects.

## Troubleshooting

### Common Issues

1. **"Google OAuth configuration missing"**
   - Check that all Google OAuth environment variables are set
   - Verify the redirect URI matches exactly

2. **"No authorization code received"**
   - Ensure the redirect URI is correctly configured in Google Cloud Console
   - Check that the OAuth consent screen is properly configured

3. **"Failed to store credentials"**
   - Verify Supabase service role key is correct
   - Check that the google_credentials table exists and RLS is configured

4. **"User ID not found"**
   - Ensure the user is authenticated before starting OAuth flow
   - Check that the state parameter is being passed correctly

### Debug Mode

Enable debug logging by setting the environment variable:

```env
DEBUG=google-oauth:*
```

## Production Deployment

1. Update redirect URIs in Google Cloud Console to use your production domain
2. Set production environment variables
3. Ensure HTTPS is enabled
4. Configure proper CORS settings
5. Set up monitoring and logging

## n8n Integration

The system automatically triggers an n8n webhook after successful OAuth completion. The webhook receives:

```json
{
  "user_id": "uuid",
  "access_token": "google-access-token",
  "refresh_token": "google-refresh-token", 
  "email": "user@example.com"
}
```

Configure your n8n workflow to handle this payload for data ingestion. 