import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

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

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;

  // Log all incoming requests for debugging
  console.log('=== PUBLIC WEBHOOK FUNCTION CALLED ===');
  console.log('Method:', method);
  console.log('URL:', req.url);
  console.log('Headers:', Object.fromEntries(req.headers.entries()));

  // Webhook verification endpoint (GET /verify)
  if (url.pathname.endsWith('/verify') && method === 'GET') {
    const challenge = url.searchParams.get('challenge');
    if (challenge) {
      return withCORS(new Response(challenge, { status: 200 }));
    }
    return withCORS(new Response('No challenge provided', { status: 400 }));
  }

  // Webhook notification endpoint (POST /notify)
  if (url.pathname.endsWith('/notify') && method === 'POST') {
    try {
      console.log('=== WEBHOOK NOTIFICATION RECEIVED ===');
      console.log('Timestamp:', new Date().toISOString());
      console.log('URL:', req.url);
      console.log('Headers:', Object.fromEntries(req.headers.entries()));
      
      // Try to parse body as JSON (for test/manual sync requests)
      let body: any = null;
      try {
        body = await req.json();
        console.log('Body:', JSON.stringify(body, null, 2));
      } catch (parseError) {
        console.log('No JSON body found - this is likely a real Google Calendar webhook');
        // For real Google Calendar webhooks, the body is empty and info is in headers
      }
      
      // Extract user ID from webhook URL params or headers
      let userId = url.searchParams.get('userId');
        
      // If not in URL, try to extract from webhook body or headers
      if (!userId) {
        // Check for X-Goog-Channel-ID header
        const channelId = req.headers.get('X-Goog-Channel-ID');
        if (channelId) {
          console.log('Channel ID from header:', channelId);
          // Try to find user by channel ID in database
          const { data: webhook } = await supabase
            .from('calendar_webhooks')
            .select('user_id')
            .eq('webhook_id', channelId)
            .eq('is_active', true)
            .single();
          
          if (webhook) {
            userId = webhook.user_id;
            console.log('Found user ID from channel ID:', userId);
          }
        }
      }
      
      if (!userId) {
        console.error('Could not determine userId from webhook notification');
        // Log this as a failed webhook for debugging
        await supabase
          .from('calendar_sync_logs')
          .insert({
            user_id: null,
            sync_type: 'webhook',
            status: 'failed',
            error_message: 'Could not determine userId from webhook notification',
            events_processed: 0,
          });
        
        return withCORS(new Response(JSON.stringify({ 
          ok: true, 
          message: 'Webhook received but userId not found' 
        }), { status: 200 }));
      }
      
      console.log('Processing webhook notification for user:', userId);
      
      // Update webhook activity tracking
      await supabase
        .from('calendar_webhooks')
        .update({ 
          last_webhook_received: new Date().toISOString(),
          webhook_failures: 0,
          updated_at: new Date().toISOString()
        })
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary');
      
      // Get user's Google credentials
      const credentials = await getGoogleCredentials(userId);
      
      // Get current webhook info to check if we have a sync token
      const { data: webhook } = await supabase
        .from('calendar_webhooks')
        .select('sync_token')
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();
      
      // Get the changed events from Google Calendar
      const calendarResponse = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `timeMin=${new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()}&timeMax=${new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString()}&singleEvents=true&orderBy=startTime`,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );
      
      if (!calendarResponse.ok) {
        throw new Error(`Calendar API error: ${calendarResponse.status}`);
      }
      
      const calendarData = await calendarResponse.json();
      const events = calendarData.items || [];
      
      let processed = 0;
      let created = 0;
      let updated = 0;
      let errors = 0;
      
      // Process each event
      for (const event of events) {
        try {
          // Process the calendar event (simplified for now)
          console.log('Processing event:', event.id);
          processed++;
          
          // For now, just log the event
          console.log('Event processed:', {
            id: event.id,
            summary: event.summary,
            start: event.start,
            end: event.end
          });
          
        } catch (error) {
          console.error('Error processing event:', error);
          errors++;
        }
      }
      
      // Log the sync operation
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: 'webhook',
          status: 'completed',
          events_processed: processed,
          meetings_created: created,
          meetings_updated: updated,
          sync_range_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          sync_range_end: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
        });
      
      console.log(`Webhook processing completed: ${processed} processed, ${created} created, ${updated} updated, ${errors} errors`);
      
      return withCORS(new Response(JSON.stringify({
        ok: true,
        processed,
        created,
        updated,
        errors,
      }), { status: 200 }));
      
    } catch (error) {
      console.error('Webhook processing error:', error);
      
      // Log the error for debugging
      try {
        await supabase
          .from('calendar_sync_logs')
          .insert({
            user_id: null,
            sync_type: 'webhook',
            status: 'failed',
            error_message: error.message || String(error),
            events_processed: 0,
          });
      } catch (logError) {
        console.error('Failed to log webhook error:', logError);
      }
      
      return withCORS(new Response(JSON.stringify({
        ok: false,
        error: error.message || String(error),
      }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});
