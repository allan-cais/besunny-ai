import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Poll calendar for a specific user
async function pollCalendarForUser(userId: string): Promise<{ processed: number; created: number; updated: number; deleted: number; skipped: boolean }> {
  try {
    const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/calendar-polling-service`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId }),
    });

    if (!response.ok) {
      throw new Error(`Calendar polling failed: ${response.status}`);
    }

    const result = await response.json();
    return {
      processed: result.processed || 0,
      created: result.created || 0,
      updated: result.updated || 0,
      deleted: result.deleted || 0,
      skipped: result.skipped || false,
    };
  } catch (error) {
          // Error polling calendar for user
    return { processed: 0, created: 0, updated: 0, deleted: 0, skipped: false };
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  }

  try {
    // Starting calendar polling cron job

    // Get all active calendar webhooks
    const { data: activeWebhooks, error } = await supabase
      .from('calendar_webhooks')
      .select('user_id')
      .eq('is_active', true)
      .eq('google_calendar_id', 'primary');

    if (error) {
      throw new Error(`Failed to get active calendar webhooks: ${error.message}`);
    }

    if (!activeWebhooks || activeWebhooks.length === 0) {
      // No active calendar webhooks found
      return new Response(JSON.stringify({
        success: true,
        message: 'No active calendar webhooks found',
        total_processed: 0,
        total_created: 0,
        total_updated: 0,
        total_deleted: 0,
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Found active calendar webhooks

    let totalProcessed = 0;
    let totalCreated = 0;
    let totalUpdated = 0;
    let totalDeleted = 0;
    let totalSkipped = 0;
    const results = [];

    // Poll calendar for each user
    for (const webhook of activeWebhooks) {
      try {
        const result = await pollCalendarForUser(webhook.user_id);
        totalProcessed += result.processed;
        totalCreated += result.created;
        totalUpdated += result.updated;
        totalDeleted += result.deleted;
        if (result.skipped) totalSkipped++;
        
        results.push({
          user_id: webhook.user_id,
          processed: result.processed,
          created: result.created,
          updated: result.updated,
          deleted: result.deleted,
          skipped: result.skipped,
        });

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        // Failed to poll calendar for user
        results.push({
          user_id: webhook.user_id,
          error: error.message,
        });
      }
    }

    // Calendar polling completed

    return new Response(JSON.stringify({
      success: true,
      message: `Calendar polling completed for ${activeWebhooks.length} users`,
      total_processed: totalProcessed,
      total_created: totalCreated,
      total_updated: totalUpdated,
      total_deleted: totalDeleted,
      total_skipped: totalSkipped,
      results,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    // Calendar polling cron job error
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to run calendar polling cron job' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}); 