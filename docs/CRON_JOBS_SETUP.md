# Cron Jobs Setup Guide

This document describes all the cron jobs configured as GitHub Actions workflows for the Kirit Askuno application.

## Overview

All cron jobs are implemented as GitHub Actions workflows that run on scheduled intervals. This approach provides:
- **Reliability**: GitHub Actions has high uptime and automatic retries
- **Monitoring**: Built-in logging and failure notifications
- **Flexibility**: Easy to modify schedules and add manual triggers
- **Security**: Uses GitHub secrets for sensitive configuration

## Required GitHub Secrets

Make sure these secrets are configured in your GitHub repository:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `REFRESH_GOOGLE_TOKEN_URL`: URL for the refresh Google token function

## Cron Jobs Overview

### 1. Attendee Meeting Polling
**File**: `.github/workflows/attendee-polling.yml`
**Schedule**: Every 2 minutes
**Purpose**: Polls active meetings for attendee bot status updates

```yaml
schedule:
  - cron: '*/2 * * * *'  # Every 2 minutes
```

**Function**: Calls `attendee-service/poll-all` edge function

### 2. Gmail Polling Cron
**File**: `.github/workflows/gmail-polling.yml`
**Schedule**: Every 6 hours
**Purpose**: Polls Gmail for virtual email detection (backup to webhooks)

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

**Function**: Calls `gmail-polling-cron` edge function

### 3. Calendar Polling Cron
**File**: `.github/workflows/calendar-polling.yml`
**Schedule**: Every 6 hours
**Purpose**: Polls Google Calendar for event changes (backup to webhooks)

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

**Function**: Calls `calendar-polling-cron` edge function

### 4. Drive Polling Cron
**File**: `.github/workflows/drive-polling.yml`
**Schedule**: Every 6 hours
**Purpose**: Polls Google Drive for file changes (backup to webhooks)

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

**Function**: Calls `drive-polling-cron` edge function

### 5. Renew Calendar Watches
**File**: `.github/workflows/renew-calendar-watches.yml`
**Schedule**: Every 12 hours
**Purpose**: Renews Google Calendar webhooks before they expire

```yaml
schedule:
  - cron: '0 */12 * * *'  # Every 12 hours
```

**Function**: Calls `renew-calendar-watches` edge function

### 6. Renew Calendar Webhooks
**File**: `.github/workflows/renew-calendar-webhooks.yml`
**Schedule**: Every 6 days
**Purpose**: Renews calendar webhooks on a longer interval

```yaml
schedule:
  - cron: '0 0 */6 * *'  # Every 6 days at midnight
```

**Function**: Calls `renew-calendar-webhooks` edge function

### 7. Refresh Google Tokens
**File**: `.github/workflows/refresh-google-tokens.yml`
**Schedule**: Every 45 minutes
**Purpose**: Refreshes Google OAuth tokens before they expire

```yaml
schedule:
  - cron: '*/45 * * * *'  # Every 45 minutes
```

**Function**: Calls `refresh-google-token` edge function

### 8. Database Maintenance
**File**: `.github/workflows/maintenance.yml`
**Schedule**: Daily, Weekly, and Monthly
**Purpose**: Performs database maintenance tasks

```yaml
schedule:
  - cron: '0 2 * * *'    # Daily at 2 AM UTC
  - cron: '0 3 * * 0'    # Weekly on Sundays at 3 AM UTC
  - cron: '0 4 1 * *'    # Monthly on 1st at 4 AM UTC
```

**Functions**: 
- `perform_daily_maintenance`
- `perform_weekly_maintenance`
- `perform_monthly_maintenance`

## Manual Triggering

All workflows support manual triggering via the GitHub Actions UI:

1. Go to your repository's "Actions" tab
2. Select the workflow you want to run
3. Click "Run workflow"
4. Choose the branch and any input parameters
5. Click "Run workflow"

## Monitoring and Troubleshooting

### Check Workflow Status
1. Go to GitHub Actions tab in your repository
2. View recent runs and their status
3. Click on any run to see detailed logs

### Common Issues

#### Workflow Not Running
- Check if the repository has GitHub Actions enabled
- Verify the cron syntax is correct
- Ensure the workflow file is in the `.github/workflows/` directory

#### Authentication Errors
- Verify `SUPABASE_SERVICE_ROLE_KEY` is set correctly
- Check that the service role has necessary permissions
- Ensure the Supabase URL is correct

#### Function Not Found
- Verify the edge function is deployed to Supabase
- Check the function name in the workflow matches the deployed function
- Ensure the function is accessible via the service role

## Cron Expression Reference

| Expression | Description |
|------------|-------------|
| `*/2 * * * *` | Every 2 minutes |
| `*/45 * * * *` | Every 45 minutes |
| `0 */6 * * *` | Every 6 hours |
| `0 */12 * * *` | Every 12 hours |
| `0 0 */6 * *` | Every 6 days at midnight |
| `0 2 * * *` | Daily at 2 AM UTC |
| `0 3 * * 0` | Weekly on Sundays at 3 AM UTC |
| `0 4 1 * *` | Monthly on 1st at 4 AM UTC |

## Adding New Cron Jobs

To add a new cron job:

1. Create a new workflow file in `.github/workflows/`
2. Define the schedule using cron syntax
3. Add the necessary steps to call your edge function
4. Configure required secrets
5. Test the workflow manually before relying on the schedule

Example template:
```yaml
name: New Cron Job

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  run-job:
    runs-on: ubuntu-latest
    steps:
    - name: Execute Job
      run: |
        curl -X POST \
          -H "Authorization: Bearer ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" \
          -H "Content-Type: application/json" \
          "${{ secrets.SUPABASE_URL }}/functions/v1/your-function"
```

## Performance Considerations

- **Rate Limiting**: Be mindful of API rate limits when setting frequent schedules
- **Resource Usage**: Monitor GitHub Actions minutes usage
- **Database Load**: Consider the impact of maintenance jobs on database performance
- **Error Handling**: Implement proper error handling and retry logic

## Security Best Practices

- Use service role keys only for automated tasks
- Regularly rotate service role keys
- Monitor workflow logs for any security issues
- Use least privilege principle for function permissions 