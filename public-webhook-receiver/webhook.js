// Public Webhook Receiver for Google Calendar Webhooks
// Deploy this to Netlify Functions
// This will be your public webhook endpoint that Google can reach

exports.handler = async function(event, context) {
  // Set CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Content-Type': 'application/json'
  };
  
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ message: 'CORS preflight handled' })
    };
  }
  
  // Google webhook received
  
  // Parse body if it exists
  let body = {};
  if (event.body) {
    try {
      body = JSON.parse(event.body);
    } catch (e) {
      // No JSON body or parse error
    }
  }
  
  // Extract Google webhook headers
  const channelId = event.headers['x-goog-channel-id'];
  const resourceState = event.headers['x-goog-resource-state'];
  const resourceId = event.headers['x-goog-resource-id'];
  const resourceUri = event.headers['x-goog-resource-uri'];
  
      // Webhook details extracted
  
  // For sync events, just return OK
  if (resourceState === 'sync') {
    // Sync event received
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ ok: true, message: 'Sync event processed' })
    };
  }
  
  try {
    // Forward to your Supabase Edge Function with proper auth
    const supabaseUrl = process.env.SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    if (!supabaseUrl || !serviceRoleKey) {
      // Missing environment variables
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Configuration error' })
      };
    }
    
    // Forwarding to Supabase function
    
    const response = await fetch(`${supabaseUrl}/functions/v1/google-calendar-webhook/notify`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${serviceRoleKey}`,
        'Content-Type': 'application/json',
        'X-Goog-Channel-ID': channelId || '',
        'X-Goog-Resource-State': resourceState || '',
        'X-Goog-Resource-ID': resourceId || '',
        'X-Goog-Resource-URI': resourceUri || ''
      },
      body: JSON.stringify({
        state: 'google_webhook',
        channelId,
        resourceState,
        resourceId,
        resourceUri,
        originalHeaders: event.headers,
        timestamp: new Date().toISOString()
      })
    });
    
    const result = await response.json();
          // Supabase function response
    
    if (response.ok) {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ 
          ok: true, 
          forwarded: true, 
          message: 'Webhook forwarded successfully',
          result 
        })
      };
    } else {
      // Supabase function error
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ 
          ok: true, 
          forwarded: false, 
          error: 'Supabase function error',
          details: result 
        })
      };
    }
    
  } catch (error) {
    // Error forwarding webhook
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ 
        ok: true, 
        forwarded: false, 
        error: 'Forwarding failed',
        details: error.message 
      })
    };
  }
}; 