import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  console.log('=== MANAGE-CALENDAR-WEBHOOK FUNCTION CALLED ===');
  console.log('Method:', req.method);
  console.log('URL:', req.url);
  console.log('Headers:', Object.fromEntries(req.headers.entries()));

  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    console.log('Handling CORS preflight request');
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Create Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Get authorization header
    const authHeader = req.headers.get('Authorization')
    console.log('Auth header present:', !!authHeader);
    
    if (!authHeader) {
      console.log('Missing authorization header');
      return new Response(
        JSON.stringify({ error: 'Missing authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Verify JWT and get user
    console.log('Verifying JWT...');
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''))
    if (authError || !user) {
      console.log('JWT verification failed:', authError);
      return new Response(
        JSON.stringify({ error: 'Invalid token' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log('JWT verified for user:', user.id);

    const url = new URL(req.url)
    const action = url.searchParams.get('action')
    console.log('Action requested:', action);

    if (action === 'stop') {
      return await handleStopWebhook(supabase, user.id)
    } else if (action === 'recreate') {
      return await handleRecreateWebhook(supabase, user.id)
    } else if (action === 'verify') {
      return await handleVerifyWebhook(supabase, user.id)
    } else {
      console.log('Invalid action:', action);
      return new Response(
        JSON.stringify({ error: 'Invalid action. Use stop, recreate, or verify' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

  } catch (error) {
    console.error('Error in manage-calendar-webhook:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function getGoogleCredentials(supabase: any, userId: string): Promise<any> {
  console.log('Getting Google credentials for user:', userId);
  
  const { data, error } = await supabase
    .from('google_credentials')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error || !data) {
    console.log('Google credentials not found:', error);
    throw new Error('Google credentials not found')
  }

  console.log('Found credentials, checking expiration...');
  console.log('Current time:', Math.floor(Date.now() / 1000));
  console.log('Token expires at:', data.expires_at);

  // Check if token needs refresh (refresh if expired or expires within 5 minutes)
  const now = Math.floor(Date.now() / 1000)
  const fiveMinutesFromNow = now + (5 * 60)
  
  if (data.expires_at && data.expires_at <= fiveMinutesFromNow) {
    console.log('Token needs refresh, refreshing...');
    
    // Refresh token
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
    })

    if (!refreshResponse.ok) {
      const errorText = await refreshResponse.text();
      console.log('Token refresh failed:', refreshResponse.status, errorText);
      throw new Error(`Failed to refresh Google token: ${refreshResponse.status} - ${errorText}`)
    }

    const refreshData = await refreshResponse.json()
    console.log('Token refreshed successfully');
    
    // Update credentials in database
    const { error: updateError } = await supabase
      .from('google_credentials')
      .update({
        access_token: refreshData.access_token,
        expires_at: Math.floor(Date.now() / 1000) + refreshData.expires_in,
      })
      .eq('user_id', userId)

    if (updateError) {
      console.log('Failed to update credentials in database:', updateError);
    }

    return {
      ...data,
      access_token: refreshData.access_token,
      expires_at: Math.floor(Date.now() / 1000) + refreshData.expires_in,
    }
  }

  console.log('Token is still valid');
  return data
}

async function handleStopWebhook(supabase: any, userId: string) {
  try {
    // Get current webhook info
    const { data: webhookData, error: webhookError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', userId)
      .eq('google_calendar_id', 'primary')
      .eq('is_active', true)
      .single()

    if (webhookError || !webhookData) {
      return new Response(
        JSON.stringify({ success: false, error: 'No active webhook found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Get Google credentials
    const credentials = await getGoogleCredentials(supabase, userId)

    // Stop the webhook with Google
    console.log('Stopping webhook with Google:', webhookData.webhook_id, webhookData.resource_id);
    const stopResponse = await fetch(
      `https://www.googleapis.com/calendar/v3/calendars/primary/events/stop`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: webhookData.webhook_id,
          resourceId: webhookData.resource_id,
        }),
      }
    )

    if (stopResponse.ok) {
      // Mark webhook as inactive in database
      await supabase
        .from('calendar_webhooks')
        .update({ is_active: false })
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')

      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Webhook stopped successfully',
          webhook_id: webhookData.webhook_id 
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    } else {
      const errorText = await stopResponse.text()
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: `Failed to stop webhook: ${stopResponse.status} - ${errorText}` 
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

  } catch (error) {
    console.error('Error stopping webhook:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message || String(error) }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleRecreateWebhook(supabase: any, userId: string) {
  try {
    console.log('Recreating webhook for user:', userId);
    
    // Get Google credentials
    const credentials = await getGoogleCredentials(supabase, userId)
    console.log('Got credentials, access token length:', credentials.access_token?.length);

    // Create new webhook
    const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify?userId=${userId}`
    const channelId = `calendar-watch-${userId}-${Date.now()}`
    const expiration = Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days

    console.log('Creating webhook with URL:', webhookUrl);
    console.log('Channel ID:', channelId);

    const watchRequest = {
      id: channelId,
      type: 'web_hook',
      address: webhookUrl,
      params: {
        userId: userId,
      },
      expiration: expiration,
    }

    console.log('Making Google API call to create webhook...');
    const createResponse = await fetch(
      'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(watchRequest),
      }
    )
    
    console.log('Google API response status:', createResponse.status);

    if (!createResponse.ok) {
      const errorText = await createResponse.text()
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: `Failed to create webhook: ${createResponse.status} - ${errorText}` 
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const watchData = await createResponse.json()
    console.log('Google webhook response:', watchData);
    
    // Handle expiration time properly
    let expirationDate: Date;
    if (watchData.expiration) {
      // Google returns expiration as milliseconds since epoch
      expirationDate = new Date(parseInt(watchData.expiration));
      console.log('Parsed expiration date:', expirationDate.toISOString());
    } else {
      // Fallback: use our calculated expiration
      expirationDate = new Date(expiration);
      console.log('Using fallback expiration date:', expirationDate.toISOString());
    }

    // Get sync token for initial sync
    const syncResponse = await fetch(
      'https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=1',
      {
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
        },
      }
    )

    let syncToken = null
    if (syncResponse.ok) {
      const syncData = await syncResponse.json()
      syncToken = syncData.nextSyncToken
    }

    console.log('Storing webhook in database...');
    // Store webhook info in database
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
      }, {
        onConflict: 'user_id,google_calendar_id'
      })

    if (dbError) {
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: `Database error: ${dbError.message}` 
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Webhook recreated successfully',
        webhook_id: watchData.id,
        resource_id: watchData.resourceId,
        expiration: expirationDate.toISOString()
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error recreating webhook:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message || String(error) }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
}

async function handleVerifyWebhook(supabase: any, userId: string) {
  try {
    // Get current webhook info
    const { data: webhookData, error: webhookError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', userId)
      .eq('google_calendar_id', 'primary')
      .eq('is_active', true)
      .single()

    if (webhookError || !webhookData) {
      return new Response(
        JSON.stringify({ success: false, error: 'No active webhook found' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Get Google credentials
    const credentials = await getGoogleCredentials(supabase, userId)

    // Try to stop the current webhook to verify it exists
    const stopResponse = await fetch(
      `https://www.googleapis.com/calendar/v3/calendars/primary/events/stop`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${credentials.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: webhookData.webhook_id,
          resourceId: webhookData.resource_id,
        }),
      }
    )

    if (stopResponse.ok) {
      // Webhook exists, now recreate it
      const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/google-calendar-webhook/notify?userId=${userId}`
      const channelId = `calendar-watch-${userId}-${Date.now()}`
      const expiration = Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days

      const watchRequest = {
        id: channelId,
        type: 'web_hook',
        address: webhookUrl,
        params: {
          userId: userId,
        },
        expiration: expiration,
      }

      const createResponse = await fetch(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(watchRequest),
        }
      )

      if (!createResponse.ok) {
        const errorText = await createResponse.text()
        return new Response(
          JSON.stringify({ 
            success: false, 
            error: `Failed to recreate webhook: ${createResponse.status} - ${errorText}` 
          }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      const watchData = await createResponse.json()
      const expirationDate = new Date(watchData.expiration)

      // Update database with new webhook info
      const { error: updateError } = await supabase
        .from('calendar_webhooks')
        .update({
          webhook_id: watchData.id,
          resource_id: watchData.resourceId,
          expiration_time: expirationDate.toISOString(),
          is_active: true,
        })
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')

      if (updateError) {
        return new Response(
          JSON.stringify({ 
            success: false, 
            error: `Database update failed: ${updateError.message}` 
          }),
          { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true, 
          message: 'Webhook verified and refreshed',
          webhook_id: watchData.id,
          resource_id: watchData.resourceId,
          expiration: expirationDate.toISOString()
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    } else {
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: 'Webhook not found or invalid with Google' 
        }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

  } catch (error) {
    console.error('Error verifying webhook:', error)
    return new Response(
      JSON.stringify({ success: false, error: error.message || String(error) }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
} 