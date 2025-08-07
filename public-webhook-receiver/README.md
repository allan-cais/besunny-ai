# Google Calendar Webhook Receiver

This is a public webhook receiver that acts as a proxy between Google Calendar webhooks and your Supabase Edge Function.

## Deployment to Netlify

### 1. Deploy to Netlify

You can deploy this in several ways:

**Option A: Deploy via Netlify CLI**
```bash
# Install Netlify CLI if you haven't already
npm install -g netlify-cli

# Navigate to this directory
cd public-webhook-receiver

# Deploy
netlify deploy --prod
```

**Option B: Deploy via Git**
1. Push this directory to a Git repository
2. Connect the repository to Netlify
3. Set the build settings:
   - Build command: (leave empty)
   - Publish directory: (leave empty)
   - Functions directory: `.`

**Option C: Deploy via Netlify UI**
1. Go to your Netlify dashboard
2. Drag and drop this folder to deploy

### 2. Set Environment Variables

In your Netlify dashboard, go to **Site settings** → **Environment variables** and add:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

### 3. Get Your Webhook URL

After deployment, your webhook URL will be:
```
https://your-site.netlify.app/.netlify/functions/webhook
```

Or with the redirect:
```
https://your-site.netlify.app/api/webhook
```

## Update Your Google Calendar Webhook

Once deployed, update your Google Calendar webhook setup to use the new URL:

1. Go to your Google Calendar API setup
2. Update the webhook URL to point to your Netlify function
3. The webhook will now forward requests to your Supabase function with proper authentication

## Testing

You can test the webhook by sending a request to your Netlify function:

```bash
curl -X POST "https://your-site.netlify.app/.netlify/functions/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Goog-Channel-ID: test-channel" \
  -H "X-Goog-Resource-State: exists" \
  -d '{}'
```

## How It Works

1. **Google Calendar** sends webhook notifications to your Netlify function
2. **Netlify function** receives the webhook (no authentication required)
3. **Netlify function** forwards the request to your Supabase function with proper authentication
4. **Supabase function** processes the webhook and updates your database

This approach solves the authentication issue by using a public endpoint (Netlify) as a proxy to your authenticated endpoint (Supabase). 