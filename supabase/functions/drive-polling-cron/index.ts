import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Poll drive for a specific file
async function pollDriveForFile(fileId: string, documentId: string): Promise<{ processed: boolean; action?: string; skipped: boolean; error?: string }> {
  try {
    const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/drive-polling-service`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fileId, documentId }),
    });

    if (!response.ok) {
      throw new Error(`Drive polling failed: ${response.status}`);
    }

    const result = await response.json();
    return {
      processed: result.processed || false,
      action: result.action,
      skipped: result.skipped || false,
      error: result.error,
    };
  } catch (error) {
          // Error polling drive for file
    return { processed: false, error: error.message, skipped: false };
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
    // Starting drive polling cron job

    // Get all active drive file watches
    const { data: activeWatches, error } = await supabase
      .from('drive_file_watches')
      .select('file_id, document_id')
      .eq('is_active', true);

    if (error) {
      throw new Error(`Failed to get active drive file watches: ${error.message}`);
    }

    if (!activeWatches || activeWatches.length === 0) {
      // No active drive file watches found
      return new Response(JSON.stringify({
        success: true,
        message: 'No active drive file watches found',
        total_processed: 0,
        total_actions: 0,
        total_skipped: 0,
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Found active drive file watches

    let totalProcessed = 0;
    let totalActions = 0;
    let totalSkipped = 0;
    const results = [];

    // Poll drive for each file
    for (const watch of activeWatches) {
      try {
        const result = await pollDriveForFile(watch.file_id, watch.document_id);
        if (result.processed) totalProcessed++;
        if (result.action) totalActions++;
        if (result.skipped) totalSkipped++;
        
        results.push({
          file_id: watch.file_id,
          document_id: watch.document_id,
          processed: result.processed,
          action: result.action,
          skipped: result.skipped,
          error: result.error,
        });

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        // Failed to poll drive for file
        results.push({
          file_id: watch.file_id,
          document_id: watch.document_id,
          error: error.message,
        });
      }
    }

    // Drive polling completed

    return new Response(JSON.stringify({
      success: true,
      message: `Drive polling completed for ${activeWatches.length} files`,
      total_processed: totalProcessed,
      total_actions: totalActions,
      total_skipped: totalSkipped,
      results,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    // Drive polling cron job error
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to run drive polling cron job' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}); 