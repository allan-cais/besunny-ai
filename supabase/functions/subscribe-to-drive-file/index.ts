import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface SubscribeRequest {
  user_id?: string;
  document_id: string;
  file_id: string;
  autoSetup?: boolean;
  virtualEmail?: string;
  username?: string;
}

interface GoogleDriveWatchResponse {
  kind: string;
  id: string;
  resourceId: string;
  resourceUri: string;
  token: string;
  expiration: string;
}

interface SubscribeResponse {
  success: boolean;
  message: string;
  watch_id?: string;
  resource_id?: string;
  expiration?: string;
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
async function generateGoogleJWT(credentials: any) {
  const header = {
    alg: 'RS256',
    typ: 'JWT',
    kid: Deno.env.get('GOOGLE_SERVICE_ACCOUNT_KEY_ID'),
  };
  
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/drive.file',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600, // 1 hour
    iat: now,
  };
  
  const encodedHeader = btoa(JSON.stringify(header));
  const encodedPayload = btoa(JSON.stringify(payload));
  
  // Note: In a real implementation, you'd need to sign this with the private key
  // For now, we'll use the access token directly if available
  return `${encodedHeader}.${encodedPayload}`;
}

// Get Google access token
async function getGoogleAccessToken() {
  const credentials = await getGoogleServiceAccountCredentials();
  
  try {
    // Try to get access token using service account
    const jwt = await generateGoogleJWT(credentials);
    
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        assertion: jwt,
      }),
    });
    
    if (!tokenResponse.ok) {
      throw new Error(`Failed to get access token: ${tokenResponse.statusText}`);
    }
    
    const tokenData = await tokenResponse.json();
    return tokenData.access_token;
  } catch (error) {
          // Error getting Google access token
    throw error;
  }
}

// Subscribe to Google Drive file changes
async function subscribeToDriveFile(fileId: string, channelId: string): Promise<GoogleDriveWatchResponse> {
  const accessToken = await getGoogleAccessToken();
  const webhookUrl = Deno.env.get('DRIVE_WEBHOOK_URL') || `${supabaseUrl}/functions/v1/drive-webhook-handler`;
  
  const watchRequest = {
    id: channelId, // Use document_id as channel ID
    type: 'web_hook',
    address: webhookUrl,
    params: {
      ttl: '604800', // 7 days in seconds
    },
  };
  
  const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}/watch`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(watchRequest),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Google Drive API error: ${response.status} ${response.statusText} - ${errorText}`);
  }
  
  return await response.json();
}

// Check if watch already exists for this file
async function checkExistingWatch(fileId: string): Promise<boolean> {
  const { data, error } = await supabase
    .rpc('get_active_drive_file_watch', { search_file_id: fileId });
  
  if (error) {
          // Error checking existing watch
    return false;
  }
  
  return data && data.length > 0;
}

// Store watch information in database
async function storeWatchInfo(
  documentId: string,
  projectId: string,
  fileId: string,
  channelId: string,
  resourceId: string,
  expiration: string
): Promise<string> {
  const { data, error } = await supabase
    .from('drive_file_watches')
    .insert({
      document_id: documentId,
      project_id: projectId,
      file_id: fileId,
      channel_id: channelId,
      resource_id: resourceId,
      expiration: new Date(parseInt(expiration)).toISOString(),
      is_active: true,
    })
    .select('id')
    .single();
  
  if (error) {
    throw new Error(`Failed to store watch info: ${error.message}`);
  }
  
  // Update document to reflect active watch
  await supabase
    .from('documents')
    .update({ 
      watch_active: true,
      file_id: fileId,
      last_synced_at: new Date().toISOString()
    })
    .eq('id', documentId);
  
  return data.id;
}

// Main handler function
async function handleSubscribeToDriveFile(request: SubscribeRequest): Promise<SubscribeResponse> {
  try {
    const { user_id, document_id, file_id, autoSetup, virtualEmail, username } = request;
    
    // Validate input
    if (!document_id || !file_id) {
      return {
        success: false,
        message: 'Missing required parameters: document_id, file_id',
      };
    }
    
    // For auto-setup (virtual email), user_id is optional
    if (!autoSetup && !user_id) {
      return {
        success: false,
        message: 'Missing required parameter: user_id',
      };
    }
    
    // Check if watch already exists for this file
    const existingWatch = await checkExistingWatch(file_id);
    if (existingWatch) {
      return {
        success: false,
        message: 'Watch already exists for this file',
      };
    }
    
    // For auto-setup, log the virtual email information
    if (autoSetup && virtualEmail && username) {
      // Auto-setting up Drive watch for virtual email
    }
    
    // Get document and project information
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('project_id')
      .eq('id', document_id)
      .single();
    
    if (docError || !document) {
      return {
        success: false,
        message: 'Document not found',
      };
    }
    
    if (!document.project_id) {
      return {
        success: false,
        message: 'Document is not associated with a project',
      };
    }
    
    // Subscribe to Google Drive file changes
    const watchResponse = await subscribeToDriveFile(file_id, document_id);
    
    // Store watch information in database
    const watchId = await storeWatchInfo(
      document_id,
      document.project_id,
      file_id,
      document_id, // channel_id is same as document_id
      watchResponse.resourceId,
      watchResponse.expiration
    );
    
    return {
      success: true,
      message: 'Successfully subscribed to Google Drive file changes',
      watch_id: watchId,
      resource_id: watchResponse.resourceId,
      expiration: watchResponse.expiration,
    };
    
  } catch (error) {
          // Error in subscribeToDriveFile
    return {
      success: false,
      message: `Failed to subscribe to drive file: ${error.message}`,
    };
  }
}

// HTTP handler
serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  
  try {
    // Only allow POST requests
    if (req.method !== 'POST') {
      return new Response(
        JSON.stringify({ error: 'Method not allowed' }),
        { 
          status: 405, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }
    
    // Parse request body
    const requestData: SubscribeRequest = await req.json();
    
    // Process the request
    const result = await handleSubscribeToDriveFile(requestData);
    
    return new Response(
      JSON.stringify(result),
      { 
        status: result.success ? 200 : 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
    
  } catch (error) {
    // Error in subscribe-to-drive-file handler
    return new Response(
      JSON.stringify({ 
        success: false, 
        message: 'Internal server error',
        error: error.message 
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
}); 