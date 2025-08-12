import { serve } from 'std/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  resp.headers.set('Access-Control-Allow-Headers', 'authorization, x-client-info, apikey, content-type');
  return resp;
}

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
    const credentials = await getGoogleCredentials(userId);
    const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify?userId=${userId}`;
    
    // First, try to stop any existing webhook
    try {
      const { data: existingWebhook } = await supabase
        .from('calendar_webhooks')
        .select('webhook_id, resource_id')
        .eq('user_id', userId)
        .eq('is_active', true)
        .maybeSingle();
      
      if (existingWebhook?.webhook_id) {
        // Stop the existing webhook
        const stopResponse = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events/stop`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              id: existingWebhook.webhook_id,
              resourceId: existingWebhook.resource_id,
            }),
          }
        );
        
        if (!stopResponse.ok) {
          // Failed to stop existing webhook
        }
      }
    } catch (stopError) {
              // Error stopping existing webhook
      // Continue anyway - the new webhook might still work
    }
    
    // Generate a unique channel ID with timestamp
    const uniqueId = `calendar-webhook-${userId}-${Date.now()}`;
    
    // Set up the webhook subscription
    const webhookResponse = await fetch(
      'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: uniqueId,
          type: 'web_hook',
          address: webhookUrl,
          params: {
            userId: userId,
          },
          expiration: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days in ms
        }),
      }
    );
    
    if (!webhookResponse.ok) {
      const errorText = await webhookResponse.text();
      throw new Error(`Failed to setup webhook: ${webhookResponse.status} - ${errorText}`);
    }
    
    const webhookData = await webhookResponse.json();
    

    
    // Validate expiration value
    if (!webhookData.expiration) {
      throw new Error('No expiration value received from Google API');
    }
    
    // Convert expiration to proper date
    let expirationDate: Date;
    try {
      if (typeof webhookData.expiration === 'number') {
        expirationDate = new Date(webhookData.expiration);
      } else if (typeof webhookData.expiration === 'string') {
        expirationDate = new Date(parseInt(webhookData.expiration));
      } else {
        throw new Error(`Unexpected expiration type: ${typeof webhookData.expiration}`);
      }
      
      if (isNaN(expirationDate.getTime())) {
        throw new Error(`Invalid expiration value: ${webhookData.expiration}`);
      }
    } catch (dateError) {
              // Date parsing error
      throw new Error(`Failed to parse expiration date: ${dateError.message}`);
    }
    
    // Store webhook info in database - use update to preserve created_at
    const { data: upsertData, error: upsertError } = await supabase
      .from('calendar_webhooks')
      .update({
        webhook_id: webhookData.id,
        resource_id: webhookData.resourceId,
        expiration_time: expirationDate.toISOString(),
        is_active: true,
      })
      .eq('user_id', userId)
      .eq('google_calendar_id', 'primary')
      .select();
    
    if (upsertError) {
      // Database upsert error
      throw new Error(`Failed to save webhook to database: ${upsertError.message}`);
    }
    
    return { success: true, webhook_id: webhookData.id };
  } catch (error) {
    return { success: false, error: error.message || String(error) };
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;

  // Manual renewal endpoint (POST /renew)
  if (url.pathname.endsWith('/renew') && method === 'POST') {
    try {
      const { userId } = await req.json();
      
      if (!userId) {
        return withCORS(new Response(JSON.stringify({ error: 'Missing userId' }), { status: 400 }));
      }
      
      const result = await renewWebhook(userId);
      
      if (result.success) {
        return withCORS(new Response(JSON.stringify({
          ok: true,
          webhook_id: result.webhook_id,
          message: 'Webhook renewed successfully',
        }), { status: 200 }));
      } else {
        return withCORS(new Response(JSON.stringify({
          ok: false,
          error: result.error,
        }), { status: 500 }));
      }
      
    } catch (error) {
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: error.message || String(error),
      }), { status: 500 }));
    }
  }

  // Automatic renewal endpoint (POST /auto-renew)
  if (url.pathname.endsWith('/auto-renew') && method === 'POST') {
    try {
      // Find all webhooks that expire in the next 24 hours or are already expired
      const now = new Date();
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      
      const { data: expiringWebhooks, error } = await supabase
        .from('calendar_webhooks')
        .select('user_id, expiration_time, is_active')
        .or(`expiration_time.lt.${now.toISOString()},expiration_time.lt.${tomorrow.toISOString()}`)
        .eq('is_active', true);
      
      if (error) {
        throw new Error('Failed to query expiring webhooks: ' + error.message);
      }
      
      if (!expiringWebhooks || expiringWebhooks.length === 0) {
        return withCORS(new Response(JSON.stringify({
          ok: true,
          renewed: 0,
          message: 'No webhooks need renewal',
        }), { status: 200 }));
      }
      
      let renewed = 0;
      let failed = 0;
      const results: any[] = [];
      
      for (const webhook of expiringWebhooks) {
        const result = await renewWebhook(webhook.user_id);
        
        if (result.success) {
          renewed++;
          results.push({ user_id: webhook.user_id, renewed: true, webhook_id: result.webhook_id });
        } else {
          failed++;
          results.push({ user_id: webhook.user_id, error: result.error });
        }
      }
      
      return withCORS(new Response(JSON.stringify({
        ok: true,
        renewed,
        failed,
        total: expiringWebhooks.length,
        results,
      }), { status: 200 }));
      
    } catch (error) {
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: error.message || String(error),
      }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
}); 