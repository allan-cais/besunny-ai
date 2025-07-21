import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function getGoogleCredentials(userId: string): Promise<any> {
  const { data, error } = await supabase
    .from('google_credentials')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();
  
  if (error || !data) {
    throw new Error('Google credentials not found');
  }
  
  // Check if token is expired and refresh if needed
  if (new Date(data.expires_at) <= new Date()) {
    if (!data.refresh_token) {
      throw new Error('Token expired and no refresh token available');
    }
    
    // Refresh the token
    const refreshResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: Deno.env.get('GOOGLE_CLIENT_ID')!,
        client_secret: Deno.env.get('GOOGLE_CLIENT_SECRET')!,
        refresh_token: data.refresh_token,
        grant_type: 'refresh_token',
      }),
    });
    
    if (!refreshResponse.ok) {
      throw new Error('Failed to refresh Google token');
    }
    
    const refreshData = await refreshResponse.json();
    
    // Update the credentials in the database
    const { error: updateError } = await supabase
      .from('google_credentials')
      .update({
        access_token: refreshData.access_token,
        expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
      })
      .eq('user_id', userId);
    
    if (updateError) {
      throw new Error('Failed to update refreshed token');
    }
    
    return {
      ...data,
      access_token: refreshData.access_token,
      expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
    };
  }
  
  return data;
}

async function renewWebhook(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
  try {
    console.log('Renewing calendar watch for user:', userId);
    
    // Get current watch info
    const { data: webhook, error: fetchError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', userId)
      .eq('google_calendar_id', 'primary')
      .eq('is_active', true)
      .single();

    if (fetchError || !webhook) {
      console.log('No active watch found, setting up new one');
      return await setupNewWatch(userId);
    }

    // Check if renewal is needed (renew if expires within 24 hours)
    const expirationTime = new Date(webhook.expiration_time).getTime();
    const now = Date.now();
    const renewalThreshold = 24 * 60 * 60 * 1000; // 24 hours

    if (expirationTime - now > renewalThreshold) {
      console.log('Watch not expiring soon, no renewal needed');
      return { success: true, webhook_id: webhook.webhook_id };
    }

    // Stop existing watch
    await stopWatch(userId, webhook.webhook_id);

    // Set up new watch with current sync token
    return await setupNewWatch(userId, webhook.sync_token);
  } catch (error) {
    console.error('Watch renewal error:', error);
    return { success: false, error: error.message || String(error) };
  }
}

async function setupNewWatch(userId: string, syncToken?: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
  try {
    console.log('Setting up new calendar watch for user:', userId);
    
    const credentials = await getGoogleCredentials(userId);
    if (!credentials) {
      return { success: false, error: 'No Google credentials found' };
    }

    const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify?userId=${userId}`;
    const channelId = `calendar-watch-${userId}-${Date.now()}`;
    const expiration = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7 days

    const watchRequest: any = {
      id: channelId,
      type: 'web_hook',
      address: webhookUrl,
      params: {
        userId: userId,
      },
      expiration: expiration,
    };

    // Add sync token if available for incremental sync
    if (syncToken) {
      watchRequest.params.syncToken = syncToken;
    }

    const response = await fetch(
      'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(watchRequest),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Watch setup failed: ${response.status} - ${errorText}`);
    }

          const watchData = await response.json();
      console.log('Watch setup response:', watchData);

      // Validate and parse expiration date
      let expirationDate: Date;
      try {
        if (typeof watchData.expiration === 'number') {
          expirationDate = new Date(watchData.expiration);
        } else if (typeof watchData.expiration === 'string') {
          expirationDate = new Date(parseInt(watchData.expiration));
        } else {
          throw new Error(`Unexpected expiration type: ${typeof watchData.expiration}`);
        }
        
        if (isNaN(expirationDate.getTime())) {
          throw new Error(`Invalid expiration value: ${watchData.expiration}`);
        }
      } catch (dateError) {
        console.error('Date parsing error:', dateError);
        throw new Error(`Failed to parse expiration date: ${dateError.message}`);
      }

      // Store watch info in database
      const { error: dbError } = await supabase
        .from('calendar_webhooks')
        .upsert({
          user_id: userId,
          google_calendar_id: 'primary',
          webhook_id: watchData.id,
          resource_id: watchData.resourceId,
          expiration_time: expirationDate.toISOString(),
          sync_token: syncToken,
          is_active: true,
          last_sync_at: new Date().toISOString(),
        }, {
          onConflict: 'user_id,google_calendar_id',
        });

    if (dbError) {
      console.error('Database error storing watch:', dbError);
      return { success: false, error: `Database error: ${dbError.message}` };
    }

    console.log('Calendar watch setup successfully');
    return { success: true, webhook_id: watchData.id };
  } catch (error) {
    console.error('Watch setup error:', error);
    return { success: false, error: error.message || String(error) };
  }
}

async function stopWatch(userId: string, webhookId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('Stopping calendar watch:', webhookId);
    
    const credentials = await getGoogleCredentials(userId);
    if (!credentials) {
      return { success: false, error: 'No Google credentials found' };
    }

    const response = await fetch(
      'https://www.googleapis.com/calendar/v3/channels/stop',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: webhookId,
          resourceId: webhookId, // Use webhookId as resourceId for stop
        }),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.warn(`Failed to stop watch: ${response.status} - ${errorText}`);
      // Don't throw error, just log warning
    }

    // Mark as inactive in database
    await supabase
      .from('calendar_webhooks')
      .update({ is_active: false })
      .eq('user_id', userId)
      .eq('webhook_id', webhookId);

    console.log('Calendar watch stopped successfully');
    return { success: true };
  } catch (error) {
    console.error('Stop watch error:', error);
    return { success: false, error: error.message || String(error) };
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Only allow POST (for cron job or admin use)
    if (req.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    console.log('Starting calendar watch renewal process...');

    // Find all active webhooks that need renewal
    const { data: webhooks, error } = await supabase
      .from('calendar_webhooks')
      .select('user_id, webhook_id, expiration_time, sync_token')
      .eq('is_active', true)
      .eq('google_calendar_id', 'primary');

    if (error) {
      throw new Error('Failed to query webhooks: ' + error.message);
    }

    if (!webhooks || webhooks.length === 0) {
      console.log('No active webhooks found');
      return new Response(JSON.stringify({ 
        renewed: 0, 
        failed: 0,
        message: 'No active webhooks found' 
      }), { status: 200, headers: corsHeaders });
    }

    console.log(`Found ${webhooks.length} active webhooks to check`);

    let renewed = 0;
    let failed = 0;
    const results: any[] = [];

    for (const webhook of webhooks) {
      try {
        const result = await renewWebhook(webhook.user_id);
        
        if (result.success) {
          renewed++;
          results.push({ 
            user_id: webhook.user_id, 
            webhook_id: result.webhook_id,
            renewed: true 
          });
        } else {
          failed++;
          results.push({ 
            user_id: webhook.user_id, 
            error: result.error 
          });
        }
      } catch (err: any) {
        failed++;
        results.push({ 
          user_id: webhook.user_id, 
          error: err.message || String(err) 
        });
      }
    }

    console.log(`Watch renewal completed: ${renewed} renewed, ${failed} failed`);

    return new Response(JSON.stringify({
      renewed,
      failed,
      total: webhooks.length,
      results,
      message: `Renewed ${renewed} watches, ${failed} failed`
    }), { 
      status: 200, 
      headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
    });

  } catch (error: any) {
    console.error('Watch renewal error:', error);
    return new Response(JSON.stringify({
      error: error.message || String(error),
      renewed: 0,
      failed: 0
    }), { 
      status: 500, 
      headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
    });
  }
}); 