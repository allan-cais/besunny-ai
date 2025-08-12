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

async function getGoogleServiceAccountCredentials(): Promise<any> {
  const privateKey = Deno.env.get('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY')!;
  const clientEmail = Deno.env.get('GOOGLE_SERVICE_ACCOUNT_EMAIL')!;
  
  return {
    type: 'service_account',
    project_id: Deno.env.get('GOOGLE_PROJECT_ID')!,
    private_key_id: Deno.env.get('GOOGLE_PRIVATE_KEY_ID')!,
    private_key: privateKey.replace(/\\n/g, '\n'),
    client_email: clientEmail,
    client_id: Deno.env.get('GOOGLE_CLIENT_ID')!,
    auth_uri: 'https://accounts.google.com/o/oauth2/auth',
    token_uri: 'https://oauth2.googleapis.com/token',
    auth_provider_x509_cert_url: 'https://www.googleapis.com/oauth2/v1/certs',
    client_x509_cert_url: `https://www.googleapis.com/robot/v1/metadata/x509/${encodeURIComponent(clientEmail)}`,
  };
}

async function generateGoogleJWT(credentials: any, scope: string): Promise<string> {
  const header = {
    alg: 'RS256',
    typ: 'JWT',
    kid: credentials.private_key_id,
  };

  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: credentials.client_email,
    scope: scope,
    aud: credentials.token_uri,
    exp: now + 3600, // 1 hour
    iat: now,
  };

  const encodedHeader = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const encodedPayload = btoa(JSON.stringify(payload)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

  // Import the private key and sign
  const key = await crypto.subtle.importKey(
    'pkcs8',
    new TextEncoder().encode(credentials.private_key),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    key,
    new TextEncoder().encode(`${encodedHeader}.${encodedPayload}`)
  );

  const encodedSignature = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');

  return `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
}

async function getAccessToken(jwt: string): Promise<string> {
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
    throw new Error(`Failed to get access token: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.access_token;
}

// Handle file deletion
async function handleFileDeletion(documentId: string, projectId: string, fileId: string): Promise<void> {
  try {
    // Handling file deletion for document
    
    // Update document status
    await supabase
      .from('documents')
      .update({
        status: 'deleted',
        watch_active: false,
        updated_at: new Date().toISOString(),
      })
      .eq('id', documentId);

    // Deactivate the watch
    await supabase
      .from('drive_file_watches')
      .update({
        is_active: false,
        updated_at: new Date().toISOString(),
      })
      .eq('document_id', documentId);

    // Send to n8n for cleanup
    await sendToN8nWebhook(documentId, projectId, fileId, 'deleted');
    
    // Successfully handled file deletion for document
  } catch (error) {
          // Error handling file deletion for document
    throw error;
  }
}

// Send to n8n webhook
async function sendToN8nWebhook(documentId: string, projectId: string, fileId: string, action: string): Promise<boolean> {
  try {
    const n8nWebhookUrl = Deno.env.get('N8N_WEBHOOK_URL');
    if (!n8nWebhookUrl) {
      // No N8N webhook URL configured, skipping n8n notification
      return false;
    }

    const payload = {
      document_id: documentId,
      project_id: projectId,
      file_id: fileId,
      action: action,
      source: 'drive_polling',
      timestamp: new Date().toISOString(),
    };

    const response = await fetch(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`N8N webhook failed: ${response.status} ${response.statusText}`);
    }

    // Successfully sent to n8n webhook for document
    return true;
  } catch (error) {
          // Error sending to n8n webhook for document
    return false;
  }
}

// Check file metadata and detect changes
async function checkFileChanges(fileId: string, accessToken: string): Promise<{ changed: boolean; action?: string; metadata?: any }> {
  try {
    const response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,name,modifiedTime,trashed,size`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return { changed: true, action: 'deleted' };
      }
      throw new Error(`Drive API error: ${response.status} ${response.statusText}`);
    }

    const fileMetadata = await response.json();
    
    // Check if file is trashed
    if (fileMetadata.trashed) {
      return { changed: true, action: 'deleted', metadata: fileMetadata };
    }

    // Get the last known state from our database
    const { data: document } = await supabase
      .from('documents')
      .select('last_synced_at, status')
      .eq('file_id', fileId)
      .single();

    if (!document) {
      return { changed: false };
    }

    // Check if file was modified since last sync
    const lastSyncTime = document.last_synced_at ? new Date(document.last_synced_at) : new Date(0);
    const modifiedTime = new Date(fileMetadata.modifiedTime);

    if (modifiedTime > lastSyncTime) {
      return { changed: true, action: 'updated', metadata: fileMetadata };
    }

    return { changed: false, metadata: fileMetadata };
  } catch (error) {
          // Error checking file changes for file
    throw error;
  }
}

// Smart drive polling with webhook activity check
async function pollDriveForFile(fileId: string, documentId: string): Promise<{ processed: boolean; action?: string; skipped: boolean; error?: string }> {
  try {
    // Get current drive watch status
    const { data: watchStatus } = await supabase
      .from('drive_file_watches')
      .select('last_webhook_received, is_active, project_id')
      .eq('file_id', fileId)
      .eq('is_active', true)
      .single();
    
    if (!watchStatus) {
      // No active drive watch found for file
      return { processed: false, skipped: true };
    }
    
    // Smart polling: Skip if webhook was received recently (within 6 hours)
    if (watchStatus.last_webhook_received) {
      const lastWebhookTime = new Date(watchStatus.last_webhook_received);
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);
      
      if (lastWebhookTime > sixHoursAgo) {
        // Skipping polling for file - webhook received recently
        return { processed: false, skipped: true };
      }
    }
    
    // Get Google service account credentials
    const credentials = await getGoogleServiceAccountCredentials();
    
    // Generate JWT for Drive API access
    const jwt = await generateGoogleJWT(credentials, 'https://www.googleapis.com/auth/drive.readonly');
    
    // Exchange JWT for access token
    const accessToken = await getAccessToken(jwt);
    
    // Check for file changes
    const changeResult = await checkFileChanges(fileId, accessToken);
    
    if (!changeResult.changed) {
      // No changes detected for file
      
      // Update last poll time
      await supabase
        .from('drive_file_watches')
        .update({ last_poll_at: new Date().toISOString() })
        .eq('file_id', fileId);
      
      return { processed: true, skipped: false };
    }
    
    // Changes detected for file
    
    // Handle the change
    if (changeResult.action === 'deleted') {
      await handleFileDeletion(documentId, watchStatus.project_id, fileId);
    } else if (changeResult.action === 'updated') {
      // Update document status and send to n8n
      await supabase
        .from('documents')
        .update({
          status: 'updated',
          last_synced_at: new Date().toISOString(),
        })
        .eq('id', documentId);
      
      await sendToN8nWebhook(documentId, watchStatus.project_id, fileId, 'updated');
    }
    
    // Update last poll time
    await supabase
      .from('drive_file_watches')
      .update({ last_poll_at: new Date().toISOString() })
      .eq('file_id', fileId);
    
    // Log the polling activity
    await supabase.rpc('log_drive_polling_activity', {
      p_document_id: documentId,
      p_file_id: fileId,
      p_polling_result: JSON.stringify({
        action: changeResult.action,
        n8n_webhook_sent: true,
        n8n_webhook_response: 'success'
      })
    });
    
    // Drive polling completed for file
    
    return { processed: true, action: changeResult.action, skipped: false };
  } catch (error) {
          // Error polling drive for file
    
    // Log the error
    await supabase.rpc('log_drive_polling_activity', {
      p_document_id: documentId,
      p_file_id: fileId,
      p_polling_result: JSON.stringify({
        error_message: error.message
      })
    });
    
    return { processed: false, error: error.message, skipped: false };
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Only allow POST
    if (req.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    const { fileId, documentId } = await req.json();
    
    if (!fileId || !documentId) {
      return new Response(JSON.stringify({ error: 'Missing fileId or documentId' }), { 
        status: 400, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      });
    }

    // Starting drive polling for file

    const result = await pollDriveForFile(fileId, documentId);

    // Drive polling completed for file

    return new Response(JSON.stringify({
      success: true,
      message: `Drive polling completed for file ${fileId}`,
      ...result,
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    // Drive polling service error
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to run drive polling service' 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}); 