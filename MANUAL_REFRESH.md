# Manual Transcript Refresh for Specific Bots

Since we can't deploy the function right now, here are alternative ways to refresh the transcripts for the two specific bots:

## Bot Details
- **Meeting ID**: `4c9e584d-2046-47ef-9aa4-0996dc702f9f` (Bot ID: `bot_bYTBc0t6J0fy758d`)
- **Meeting ID**: `bdbe523c-7eb2-4e64-9dac-2747bf3dc0ca` (Bot ID: `bot_KekwtuOP1VjaMJMV`)

## Option 1: Trigger GitHub Actions Workflow
1. Go to your GitHub repository
2. Navigate to Actions → Attendee Meeting Polling
3. Click "Run workflow" to trigger the cron job manually
4. This will poll all meetings and capture the new features

## Option 2: Wait for Next Cron Run
The GitHub Actions workflow runs every 2 minutes, so the transcripts will be automatically refreshed with the new features within the next few minutes.

## Option 3: Manual Database Update (if needed)
If you need to force a refresh, you can temporarily update the `bot_status` of these meetings to trigger polling:

```sql
UPDATE meetings 
SET bot_status = 'transcribing', updated_at = NOW()
WHERE id IN (
  '4c9e584d-2046-47ef-9aa4-0996dc702f9f',
  'bdbe523c-7eb2-4e64-9dac-2747bf3dc0ca'
);
```

## What Will Happen
Once the polling runs (either manually or via cron), the transcripts will be updated with:
- ✅ Speaker segments with timestamps
- ✅ Participant lists and analytics
- ✅ Audio recording URLs
- ✅ Enhanced metadata

The new Phase 1 features will then be available in the UI! 