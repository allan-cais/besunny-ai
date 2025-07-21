# GitHub Actions Setup for Attendee Polling Cron

## Overview

This guide explains how to set up the GitHub Actions workflow to replace the Supabase edge function cron job for attendee bot polling.

## Files Created

1. **`.github/workflows/attendee-polling-cron.yml`** - The GitHub Actions workflow
2. **`fix_bot_polling_issues.sql`** - Database fixes to apply

## Setup Steps

### 1. Apply Database Fixes

Run the following SQL in your Supabase SQL Editor:

```sql
-- Copy and paste the contents of fix_bot_polling_issues.sql
-- This will fix all the polling system issues
```

### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

#### Required Secrets:

- **`SUPABASE_URL`**
  - Value: Your Supabase project URL (e.g., `https://gkkmaeobxwvramtsjabu.supabase.co`)
  - Found in: Supabase Dashboard → Settings → API

- **`SUPABASE_SERVICE_ROLE_KEY`**
  - Value: Your Supabase service role key
  - Found in: Supabase Dashboard → Settings → API → Project API keys → `service_role` key
  - ⚠️ **Important**: This is the service role key, not the anon key

### 3. Deploy the Edge Function

The `attendee-polling-service` edge function has already been deployed. The GitHub Action will call the existing `attendee-polling-cron` edge function.

### 4. Test the Workflow

1. Go to your GitHub repository → Actions
2. Find the "Attendee Bot Polling Cron" workflow
3. Click "Run workflow" to manually trigger it
4. Check the logs to ensure it's working correctly

## Workflow Details

### Schedule
- **Frequency**: Every 2 minutes (`*/2 * * * *`)
- **Manual Trigger**: Available via "workflow_dispatch"

### What It Does
1. Calls the `attendee-polling-cron` edge function
2. The edge function polls all meetings that need polling
3. Updates bot statuses and retrieves transcripts
4. Logs success/failure

### Monitoring

#### GitHub Actions
- View workflow runs in: Repository → Actions → "Attendee Bot Polling Cron"
- Check logs for any errors or issues

#### Supabase
- Monitor edge function logs in: Supabase Dashboard → Edge Functions → `attendee-polling-cron`
- Check database for polling activity

#### Frontend Debug Panel
- Use the Polling Debug Panel in your app to monitor real-time polling status
- Located at: Meetings page (temporarily added for debugging)

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Check that all GitHub secrets are set correctly
   - Verify the secret names match exactly

2. **"Unauthorized" errors**
   - Ensure you're using the `service_role` key, not the `anon` key
   - Check that the Supabase URL is correct

3. **"Function not found" errors**
   - Verify the `attendee-polling-cron` edge function is deployed
   - Check the function name in the workflow

4. **No meetings being polled**
   - Check the database fixes have been applied
   - Verify meetings have `polling_enabled = true`
   - Use the debug panel to check polling status

### Debugging Steps

1. **Check GitHub Actions logs**
   - Go to Actions → "Attendee Bot Polling Cron" → Latest run
   - Look for error messages in the logs

2. **Check Supabase Edge Function logs**
   - Go to Supabase Dashboard → Edge Functions → `attendee-polling-cron`
   - Check the function logs for errors

3. **Use the Debug Panel**
   - Navigate to your app's Meetings page
   - Use the Polling Debug Panel to manually trigger polls
   - Check the status of individual meetings

4. **Check Database**
   ```sql
   -- Check polling status
   SELECT * FROM polling_status;
   
   -- Check meetings that need polling
   SELECT * FROM meetings 
   WHERE polling_enabled = true 
     AND attendee_bot_id IS NOT NULL 
     AND (next_poll_at IS NULL OR next_poll_at <= NOW());
   ```

## Migration from Edge Function Cron

### Before (Edge Function Cron)
- Cron job was handled by Supabase edge function
- Limited visibility into execution
- Harder to debug and monitor

### After (GitHub Actions)
- Cron job handled by GitHub Actions
- Better visibility and logging
- Easier to debug and monitor
- Can be manually triggered
- Better error handling and notifications

## Cost Considerations

### GitHub Actions
- Free tier: 2,000 minutes/month
- This workflow runs every 2 minutes = 720 runs/day = 21,600 runs/month
- **Cost**: ~$0.008 per 1,000 minutes after free tier

### Supabase Edge Functions
- Free tier: 500,000 invocations/month
- This reduces edge function usage since the cron logic is now in GitHub Actions

## Next Steps

1. **Apply the database fixes** using the SQL file
2. **Set up GitHub secrets** as described above
3. **Test the workflow** manually first
4. **Monitor the system** for a few days
5. **Remove the debug panel** from the Meetings page once confident
6. **Set up notifications** (optional) for workflow failures

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Check Supabase edge function logs
4. Use the debug panel for manual testing
5. Verify all secrets are correctly configured 