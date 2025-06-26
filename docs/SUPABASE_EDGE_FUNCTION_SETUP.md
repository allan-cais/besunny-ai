# Supabase Edge Function Setup Guide

## Overview

This guide will help you deploy the Google OAuth Edge Function to Supabase for secure token exchange.

## Prerequisites

1. Supabase CLI installed: `npm install -g supabase`
2. Supabase project created
3. Google OAuth credentials configured

## Setup Steps

### 1. Install Supabase CLI

```bash
npm install -g supabase
```

### 2. Login to Supabase

```bash
supabase login
```

### 3. Link Your Project

```bash
supabase link --project-ref your-project-ref
```

### 4. Set Environment Variables

In your Supabase dashboard, go to **Settings** > **Edge Functions** and add these environment variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
GOOGLE_REDIRECT_URI=https://your-app.netlify.app/oauth/callback
```

### 5. Deploy the Edge Function

```bash
supabase functions deploy exchange-google-token
```

### 6. Verify Deployment

Check that the function is deployed in your Supabase dashboard under **Edge Functions**.

## Testing the Edge Function

You can test the function locally:

```bash
supabase functions serve exchange-google-token --env-file .env.local
```

## Security Benefits

✅ **Client Secret Secure**: Stored only on Supabase servers
✅ **Authentication Required**: Uses Supabase JWT tokens
✅ **CORS Protected**: Proper CORS headers configured
✅ **Error Handling**: Comprehensive error handling and logging

## Environment Variables Explained

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for database access
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret (now secure!)
- `GOOGLE_REDIRECT_URI`: Your app's OAuth callback URL

## Troubleshooting

### Function Not Found
- Ensure the function is deployed: `supabase functions deploy exchange-google-token`
- Check the function name matches exactly

### Authentication Errors
- Verify the service role key is correct
- Check that the user has a valid session

### Google OAuth Errors
- Verify client ID and secret are correct
- Check redirect URI matches exactly
- Ensure Google OAuth is enabled for your project

### CORS Errors
- The function includes proper CORS headers
- Check that your frontend domain is allowed

## Monitoring

- Check function logs in Supabase dashboard
- Monitor function invocations and errors
- Set up alerts for function failures 