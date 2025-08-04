import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Poll Gmail for a specific user
async function pollGmailForUser(userEmail: string): Promise<{ processed: number; detections: number; skipped: boolean }> {
  try {
    const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/gmail-polling-service`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userEmail }),
    });

    if (!response.ok) {
      throw new Error(`Gmail polling failed: ${response.status}`);
    }

    const result = await response.json();
    return {
      processed: result.processed || 0,
      detections: result.detections || 0,
      skipped: result.skipped || false,
    };
  } catch (error) {
    console.error(`Error polling Gmail for ${userEmail}:`, error);
    return { processed: 0, detections: 0, skipped: false };
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
    console.log('Starting Gmail polling cron job...');

    // Get all active Gmail watches
    const { data: activeWatches, error } = await supabase
      .from('gmail_watches')
      .select('user_email')
      .eq('is_active', true);

    if (error) {
      throw new Error(`Failed to get active Gmail watches: ${error.message}`);
    }

    if (!activeWatches || activeWatches.length === 0) {
      console.log('No active Gmail watches found');
      return new Response(JSON.stringify({
        success: true,
        message: 'No active Gmail watches found',
        total_processed: 0,
        total_detections: 0,
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    console.log(`Found ${activeWatches.length} active Gmail watches`);

    let totalProcessed = 0;
    let totalDetections = 0;
    let totalSkipped = 0;
    const results = [];

    // Poll Gmail for each user
    for (const watch of activeWatches) {
      try {
        const result = await pollGmailForUser(watch.user_email);
        totalProcessed += result.processed;
        totalDetections += result.detections;
        if (result.skipped) totalSkipped++;
        
        results.push({
          user_email: watch.user_email,
          processed: result.processed,
          detections: result.detections,
          skipped: result.skipped,
        });

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Failed to poll Gmail for ${watch.user_email}:`, error);
        results.push({
          user_email: watch.user_email,
          error: error.message,
        });
      }
    }

    console.log(`Gmail polling completed: ${totalProcessed} messages processed, ${totalDetections} virtual emails detected, ${totalSkipped} skipped`);

    return new Response(JSON.stringify({
      success: true,
      message: `Gmail polling completed for ${activeWatches.length} users`,
      total_processed: totalProcessed,
      total_detections: totalDetections,
      total_skipped: totalSkipped,
      results,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Gmail polling cron job error:', error);
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to run Gmail polling cron job' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}); 