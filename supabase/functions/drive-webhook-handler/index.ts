import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface DriveWebhookHeaders {
  'X-Goog-Resource-ID': string;
  'X-Goog-Resource-State': string;
  'X-Goog-Channel-ID': string;
  'X-Goog-Channel-Token'?: string;
  'X-Goog-Channel-Expiration'?: string;
}

interface DocumentInfo {
  document_id: string;
  project_id: string;
  file_id: string;
  title: string;
  status: string;
}

interface WebhookLogEntry {
  document_id: string;
  project_id: string;
  file_id: string;
  channel_id: string;
  resource_id: string;
  resource_state: string;
  n8n_webhook_sent: boolean;
  n8n_webhook_response?: string;
  n8n_webhook_sent_at?: string;
  error_message?: string;
}

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseServiceKey);

// Get document information by channel ID
async function getDocumentByChannelId(channelId: string): Promise<DocumentInfo | null> {
  const { data, error } = await supabase
    .rpc('get_document_by_channel_id', { search_channel_id: channelId });
  
  if (error || !data || data.length === 0) {
          // Error getting document by channel ID
    return null;
  }
  
  return {
    document_id: data[0].document_id,
    project_id: data[0].project_id,
    file_id: data[0].file_id,
    title: data[0].title,
    status: data[0].status,
  };
}

// Check if document was created via virtual email sharing
async function checkVirtualEmailDocument(documentId: string): Promise<{ isVirtualEmail: boolean; virtualEmail?: string; username?: string }> {
  try {
    const { data, error } = await supabase
      .from('documents')
      .select('source, source_id, title')
      .eq('id', documentId)
      .single();
    
    if (error || !data) {
      return { isVirtualEmail: false };
    }
    
    // Check if document was created via virtual email
    const virtualEmailPattern = /ai\+([^@]+)@besunny\.ai/;
    const titleMatch = data.title?.match(virtualEmailPattern);
    
    if (titleMatch) {
      return {
        isVirtualEmail: true,
        virtualEmail: titleMatch[0],
        username: titleMatch[1]
      };
    }
    
    // Check if source indicates virtual email processing
    if (data.source === 'gmail' && data.source_id) {
      // Check virtual email detections table
      const { data: detection } = await supabase
        .from('virtual_email_detections')
        .select('virtual_email, username')
        .eq('document_id', documentId)
        .single();
      
      if (detection) {
        return {
          isVirtualEmail: true,
          virtualEmail: detection.virtual_email,
          username: detection.username
        };
      }
    }
    
    return { isVirtualEmail: false };
  } catch (error) {
          // Error checking virtual email document
    return { isVirtualEmail: false };
  }
}

// Handle file deletion
async function handleFileDeletion(documentId: string, projectId: string, fileId: string): Promise<void> {
  try {
    // Update document status to deleted
    await supabase
      .from('documents')
      .update({ 
        status: 'deleted',
        watch_active: false,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId);
    
    // Deactivate the watch
    await supabase
      .from('drive_file_watches')
      .update({ 
        is_active: false,
        updated_at: new Date().toISOString()
      })
      .eq('document_id', documentId);
    
    // Note: Pinecone deletion would be handled by n8n workflow
    // We could also delete document_chunks here if needed
    await supabase
      .from('document_chunks')
      .delete()
      .eq('document_id', documentId);
    
    // File deletion handled for document
  } catch (error) {
          // Error handling file deletion
    throw error;
  }
}

// Send to n8n webhook for file sync
async function sendToN8nWebhook(documentId: string, projectId: string, fileId: string): Promise<boolean> {
  const n8nWebhookUrl = Deno.env.get('N8N_DRIVESYNC_WEBHOOK_URL');
  
  if (!n8nWebhookUrl) {
    // N8N drivesync webhook URL not configured
    return false;
  }
  
  try {
    const payload = {
      document_id: documentId,
      project_id: projectId,
      file_id: fileId,
      action: 'sync',
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
      // N8N webhook failed
      return false;
    }
    
    const responseText = await response.text();
          // N8N webhook response
    return true;
  } catch (error) {
          // Failed to send to N8N webhook
    return false;
  }
}

// Log webhook event
async function logWebhookEvent(logEntry: WebhookLogEntry): Promise<void> {
  try {
    await supabase
      .from('drive_webhook_logs')
      .insert(logEntry);
  } catch (error) {
          // Error logging webhook event
  }
}

// Main webhook handler
async function handleDriveWebhook(headers: DriveWebhookHeaders): Promise<{ success: boolean; message: string }> {
  try {
    const { 'X-Goog-Resource-ID': resourceId, 'X-Goog-Resource-State': resourceState, 'X-Goog-Channel-ID': channelId } = headers;
    
    // Received Drive webhook
    
    // Validate required headers
    if (!resourceId || !resourceState || !channelId) {
      return {
        success: false,
        message: 'Missing required headers: X-Goog-Resource-ID, X-Goog-Resource-State, X-Goog-Channel-ID',
      };
    }
    
    // Get document information
    const documentInfo = await getDocumentByChannelId(channelId);
    if (!documentInfo) {
      return {
        success: false,
        message: `Document not found for channel ID: ${channelId}`,
      };
    }
    
    const { document_id, project_id, file_id, title, status } = documentInfo;
    
    // Check if this is a virtual email document and set up automatic Drive watch if needed
    const virtualEmailInfo = await checkVirtualEmailDocument(document_id);
    if (virtualEmailInfo.isVirtualEmail && !status.includes('watch_active')) {
              // Setting up automatic Drive watch for virtual email document
      
      // Set up automatic Drive watch for this file
      try {
        const watchResponse = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/subscribe-to-drive-file`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            documentId: document_id,
            projectId: project_id,
            fileId: file_id,
            autoSetup: true,
            virtualEmail: virtualEmailInfo.virtualEmail,
            username: virtualEmailInfo.username,
          }),
        });
        
        if (watchResponse.ok) {
          // Automatic Drive watch set up for virtual email document
        } else {
                      // Failed to set up automatic Drive watch for document
        }
      } catch (error) {
                    // Error setting up automatic Drive watch
      }
    }
    
    // Handle different resource states
    if (resourceState === 'deleted') {
      await handleFileDeletion(document_id, project_id, file_id);
      
      // Log the webhook event
      await logWebhookEvent({
        document_id,
        project_id,
        file_id,
        channel_id: channelId,
        resource_id: resourceId,
        resource_state: resourceState,
        n8n_webhook_sent: false, // No n8n webhook for deletions
        n8n_webhook_response: 'File deleted - no sync needed',
        n8n_webhook_sent_at: new Date().toISOString(),
      });

      // Update last webhook received timestamp
      await supabase
        .from('drive_file_watches')
        .update({ 
          last_webhook_received: new Date().toISOString(),
          webhook_failures: 0 // Reset failure counter on successful webhook
        })
        .eq('file_id', file_id);
      
      return {
        success: true,
        message: `File deletion handled for document: ${title}`,
      };
    } else {
      // Handle updates (sync, change, etc.)
      const n8nSuccess = await sendToN8nWebhook(document_id, project_id, file_id);
      
      // Update document status and last synced timestamp
      await supabase
        .from('documents')
        .update({ 
          status: 'updated',
          last_synced_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .eq('id', document_id);
      
      // Log the webhook event
      await logWebhookEvent({
        document_id,
        project_id,
        file_id,
        channel_id: channelId,
        resource_id: resourceId,
        resource_state: resourceState,
        n8n_webhook_sent: n8nSuccess,
        n8n_webhook_response: n8nSuccess ? 'success' : 'failed',
        n8n_webhook_sent_at: new Date().toISOString(),
        error_message: n8nSuccess ? undefined : 'Failed to send to n8n webhook',
      });

      // Update last webhook received timestamp
      await supabase
        .from('drive_file_watches')
        .update({ 
          last_webhook_received: new Date().toISOString(),
          webhook_failures: 0 // Reset failure counter on successful webhook
        })
        .eq('file_id', file_id);
      
      return {
        success: true,
        message: `File update handled for document: ${title}. N8N sync: ${n8nSuccess ? 'success' : 'failed'}`,
      };
    }
    
  } catch (error) {
          // Error in handleDriveWebhook
    return {
      success: false,
      message: `Failed to handle Drive webhook: ${error.message}`,
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
    
    // Extract headers
    const headers: DriveWebhookHeaders = {
      'X-Goog-Resource-ID': req.headers.get('X-Goog-Resource-ID') || '',
      'X-Goog-Resource-State': req.headers.get('X-Goog-Resource-State') || '',
      'X-Goog-Channel-ID': req.headers.get('X-Goog-Channel-ID') || '',
      'X-Goog-Channel-Token': req.headers.get('X-Goog-Channel-Token') || undefined,
      'X-Goog-Channel-Expiration': req.headers.get('X-Goog-Channel-Expiration') || undefined,
    };
    
    // Process the webhook
    const result = await handleDriveWebhook(headers);
    
    // Return success response (Google expects 200 OK)
    return new Response(
      JSON.stringify(result),
      { 
        status: 200, // Always return 200 to Google
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
    
  } catch (error) {
    // Error in drive-webhook-handler
    
    // Still return 200 to Google even on error to prevent retries
    return new Response(
      JSON.stringify({ 
        success: false, 
        message: 'Internal server error',
        error: error.message 
      }),
      { 
        status: 200, // Google expects 200 OK
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
}); 