# Netlify Deployment Guide with Supabase Edge Functions

## Overview

This guide will help you deploy your Google OAuth application to Netlify with secure token exchange using Supabase Edge Functions.

## Prerequisites

1. Your code is pushed to a GitHub repository
2. You have a Netlify account
3. Google OAuth credentials are configured
4. Supabase project is set up
5. Supabase Edge Function is deployed (see `SUPABASE_EDGE_FUNCTION_SETUP.md`)

## Deployment Steps

### 1. Deploy Supabase Edge Function

First, follow the guide in `SUPABASE_EDGE_FUNCTION_SETUP.md` to:

1. Install Supabase CLI
2. Deploy the `exchange-google-token` Edge Function
3. Set Edge Function environment variables

### 2. Connect to Netlify

1. Go to [Netlify](https://netlify.com) and sign in
2. Click "New site from Git"
3. Choose your GitHub repository
4. Configure the build settings:
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
   - **Node version**: `18` (or your preferred version)

### 3. Environment Variables

In your Netlify dashboard, go to **Site settings** > **Environment variables** and add:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

**Note**: The client secret is now stored securely in the Supabase Edge Function, not in the frontend.

### 4. Google OAuth Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add your Netlify domain to authorized redirect URIs:
   - `https://your-app-name.netlify.app/oauth/callback`
   - `https://your-custom-domain.com/oauth/callback` (if using custom domain)

### 5. Deploy

1. Click "Deploy site" in Netlify
2. Wait for the build to complete
3. Your site will be available at `https://your-app-name.netlify.app`

## Testing the Deployment

1. Visit your Netlify site
2. Sign up/log in with Supabase auth
3. Navigate to the integrations page
4. Test the Google OAuth connection
5. Verify that credentials are stored in Supabase

## Custom Domain (Optional)

1. In Netlify dashboard, go to **Domain settings**
2. Click "Add custom domain"
3. Follow the DNS configuration instructions
4. Update your Google OAuth redirect URI to include the custom domain
5. Update the Edge Function's `GOOGLE_REDIRECT_URI` environment variable

## Security Benefits

✅ **Client Secret Secure**: Stored only on Supabase servers
✅ **Authentication Required**: Uses Supabase JWT tokens
✅ **CORS Protected**: Proper CORS headers configured
✅ **Error Handling**: Comprehensive error handling and logging
✅ **Production Ready**: Secure token exchange

## Architecture

```
Frontend (Netlify) → Supabase Edge Function → Google OAuth API
                ↓
            Supabase Database
```

## Troubleshooting

### Build Failures
- Check that all dependencies are in `package.json`
- Verify Node.js version compatibility
- Check build logs in Netlify dashboard

### OAuth Issues
- Verify redirect URIs in Google Cloud Console
- Check environment variables are set correctly
- Ensure Supabase RLS policies are configured
- Verify Edge Function is deployed and accessible

### Edge Function Errors
- Check Edge Function logs in Supabase dashboard
- Verify Edge Function environment variables are set
- Test the function locally with `supabase functions serve`

### Runtime Errors
- Check browser console for errors
- Verify Supabase connection
- Test OAuth flow step by step
- Check Edge Function response in Network tab

## Monitoring

- Use Netlify's built-in analytics
- Monitor Supabase logs for database operations
- Check Google Cloud Console for OAuth usage
- Monitor Edge Function invocations and errors

## Updates

To update your deployment:
1. Push changes to your GitHub repository
2. Update Edge Function if needed: `supabase functions deploy exchange-google-token`
3. Netlify will automatically rebuild and deploy
4. Test the changes on the live site 