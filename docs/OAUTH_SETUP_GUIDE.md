# Google OAuth Setup Guide for Netlify with Supabase Edge Functions

## Quick Setup for Secure OAuth

### 1. Environment Variables

Create a `.env.local` file in the root directory (for local development):

```env
# Frontend Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Google OAuth Configuration (Frontend)
VITE_GOOGLE_CLIENT_ID=your-google-client-id-here
```

**For Netlify deployment, add these as environment variables in your Netlify dashboard:**
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_GOOGLE_CLIENT_ID`

### 2. Supabase Edge Function Setup

Follow the detailed guide in `SUPABASE_EDGE_FUNCTION_SETUP.md` to:

1. Install Supabase CLI
2. Deploy the Edge Function
3. Set Edge Function environment variables:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   GOOGLE_CLIENT_ID=your-google-client-id-here
   GOOGLE_CLIENT_SECRET=your-google-client-secret-here
   GOOGLE_REDIRECT_URI=https://your-app.netlify.app/oauth/callback
   ```

### 3. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" > "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add these redirect URIs:
   - `http://localhost:5173/oauth/callback` (for local development)
   - `https://your-netlify-app.netlify.app/oauth/callback` (for production)
6. Save the changes

### 4. Supabase Configuration

Make sure your `google_credentials` table exists with the correct schema:

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

Enable Row Level Security (RLS) and create policies:

```sql
ALTER TABLE google_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own google credentials" ON google_credentials
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own google credentials" ON google_credentials
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own google credentials" ON google_credentials
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own google credentials" ON google_credentials
  FOR DELETE USING (auth.uid() = user_id);
```

### 5. Deploy to Netlify

1. Push your code to GitHub
2. Connect your repository to Netlify
3. Set the build command: `npm run build`
4. Set the publish directory: `dist`
5. Add the environment variables in Netlify dashboard
6. Deploy!

### 6. Test the OAuth Flow

1. Navigate to your Netlify app and log in
2. Go to the integrations page
3. Click "CONNECT GOOGLE ACCOUNT"
4. Complete the Google OAuth flow
5. You should be redirected back and see your connected Google account

## How It Works (Secure Edge Function)

1. **Frontend generates OAuth URL** with your client ID
2. **User is redirected to Google** for authorization
3. **Google redirects back** to `/oauth/callback` with a code
4. **Frontend calls Supabase Edge Function** with the code
5. **Edge Function exchanges code for tokens** securely on Supabase servers
6. **Edge Function stores credentials** in Supabase database
7. **User sees success** and their connected Google account

## Security Benefits

✅ **Client Secret Secure**: Stored only on Supabase servers
✅ **Authentication Required**: Uses Supabase JWT tokens
✅ **CORS Protected**: Proper CORS headers configured
✅ **Error Handling**: Comprehensive error handling and logging
✅ **Netlify Compatible**: Works with static hosting
✅ **Production Ready**: Secure token exchange

## API Endpoints

- **Supabase Edge Function**: `/functions/v1/exchange-google-token`
- **Frontend**: Direct Supabase queries for status and disconnect

## Troubleshooting

- Make sure your redirect URI matches exactly in Google Cloud Console
- Check that all environment variables are set in Netlify
- Ensure your Supabase RLS policies allow user access
- Verify the `google_credentials` table exists with the correct schema
- Check that the Edge Function is deployed and accessible
- Check browser console for any CORS or API errors
- Verify Edge Function environment variables are set correctly 