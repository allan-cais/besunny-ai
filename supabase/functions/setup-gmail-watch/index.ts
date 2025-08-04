import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface GmailWatchResponse {
  historyId: string;
  expiration: string;
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Get Google service account credentials
async function getGoogleServiceAccountCredentials() {
  const serviceAccountEmail = Deno.env.get('GOOGLE_SERVICE_ACCOUNT_EMAIL');
  const serviceAccountPrivateKey = Deno.env.get('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY');
  
  if (!serviceAccountEmail || !serviceAccountPrivateKey) {
    throw new Error('Google service account credentials not configured');
  }
  
  return {
    client_email: serviceAccountEmail,
    private_key: serviceAccountPrivateKey.replace(/\\n/g, '\n'),
  };
}

// Generate JWT token for Google API authentication
async function generateGoogleJWT(credentials: any, subject?: string) {
  const header = {
    alg: 'RS256',
    typ: 'JWT'
  };
  
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
    ...(subject && { sub: subject })
  };
  
  const encodedHeader = btoa(JSON.stringify(header));
  const encodedPayload = btoa(JSON.stringify(payload));
  
  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    await crypto.subtle.importKey(
      'pkcs8',
      new TextEncoder().encode(credentials.private_key),
      { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
      false,
      ['sign']
    ),
    new TextEncoder().encode(`${encodedHeader}.${encodedPayload}`)
  );
  
  const encodedSignature = btoa(String.fromCharCode(...new Uint8Array(signature)));
  return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
}

// Exchange JWT for access token
async function getAccessToken(jwt: string) {
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Token exchange failed: ${response.status}`);
  }
  
  const data = await response.json();
  return data.access_token;
}

// Set up Gmail watch for a user (hybrid approach: push notifications + polling backup)
async function setupGmailWatch(userEmail: string, accessToken: string): Promise<GmailWatchResponse> {
  // First, try to set up push notifications (primary method)
  try {
    const webhookUrl = `${Deno.env.get('SUPABASE_URL')}/functions/v1/gmail-notification-handler`;
    
    const watchResponse = await fetch(`https://gmail.googleapis.com/gmail/v1/users/${userEmail}/watch`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        labelIds: ['INBOX'],
        labelFilterAction: 'include',
        topicName: webhookUrl,
      }),
    });
    
    if (watchResponse.ok) {
      const watchData = await watchResponse.json();
      console.log(`Push notification watch set up successfully for ${userEmail}`);
      return {
        historyId: watchData.historyId,
        expiration: new Date(parseInt(watchData.expiration)).toISOString(),
      };
    } else {
      console.warn(`Push notification watch failed for ${userEmail}, falling back to polling`);
    }
  } catch (error) {
    console.warn(`Push notification setup failed for ${userEmail}:`, error);
  }
  
  // Fallback: Get current history ID for polling
  const profileResponse = await fetch(`https://gmail.googleapis.com/gmail/v1/users/${userEmail}/profile`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  
  if (!profileResponse.ok) {
    const errorText = await profileResponse.text();
    throw new Error(`Failed to get Gmail profile: ${profileResponse.status} - ${errorText}`);
  }
  
  const profileData = await profileResponse.json();
  const historyId = profileData.historyId;
  
  console.log(`Using polling-based watch for ${userEmail} with history ID: ${historyId}`);
  return {
    historyId: historyId,
    expiration: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
  };
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
    const { userEmail } = await req.json();
    
    if (!userEmail) {
      return new Response(JSON.stringify({ error: 'userEmail is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get service account credentials
    const credentials = await getGoogleServiceAccountCredentials();
    
    // Generate JWT for the specific user
    const jwt = await generateGoogleJWT(credentials, userEmail);
    
    // Exchange JWT for access token
    const accessToken = await getAccessToken(jwt);
    
    // Set up Gmail watch
    const watchResponse = await setupGmailWatch(userEmail, accessToken);
    
    // Store watch information in database
    await supabase
      .from('gmail_watches')
      .upsert({
        user_email: userEmail,
        history_id: watchResponse.historyId,
        expiration: watchResponse.expiration,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

    return new Response(JSON.stringify({
      success: true,
      historyId: watchResponse.historyId,
      expiration: watchResponse.expiration,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Gmail watch setup error:', error);
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to setup Gmail watch' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}); 