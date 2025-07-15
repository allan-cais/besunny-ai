import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from '@supabase/supabase-js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface GmailMessage {
  id: string;
  threadId: string;
  labelIds: string[];
  snippet: string;
  historyId: string;
  internalDate: string;
  payload: {
    partId: string;
    mimeType: string;
    filename: string;
    headers: Array<{
      name: string;
      value: string;
    }>;
    body: {
      data?: string;
      size: number;
    };
    parts?: Array<{
      partId: string;
      mimeType: string;
      filename: string;
      headers: Array<{
        name: string;
        value: string;
      }>;
      body: {
        data?: string;
        size: number;
      };
    }>;
  };
}

interface EmailProcessingResult {
  success: boolean;
  message: string;
  user_id?: string;
  document_id?: string;
  n8n_webhook_sent?: boolean;
}

function getHeaderValue(headers: Array<{ name: string; value: string }>, name: string): string | null {
  const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
  return header ? header.value : null;
}

function extractUsernameFromEmail(email: string): string | null {
  if (!email) return null;
  
  // Extract the part before @
  const parts = email.split('@');
  if (parts.length !== 2) return null;
  
  const localPart = parts[0];
  
  // Check if it contains a plus sign (plus-addressing)
  if (localPart.includes('+')) {
    const plusParts = localPart.split('+');
    if (plusParts.length >= 2) {
      return plusParts[1]; // Return the part after the plus sign
    }
  }
  
  return null;
}

async function findUserByUsername(supabase: any, username: string): Promise<string | null> {
  const { data, error } = await supabase
    .rpc('get_user_by_username', { search_username: username })
    .maybeSingle();
  
  if (error || !data) {
    return null;
  }
  
  return data.user_id;
}

async function createDocumentFromEmail(
  supabase: any, 
  userId: string, 
  gmailMessage: GmailMessage,
  subject: string,
  sender: string
): Promise<string> {
  // Create a document record
  const { data: document, error: docError } = await supabase
    .from('documents')
    .insert({
      project_id: null, // Will be assigned by n8n classification
      source: 'gmail',
      source_id: gmailMessage.id,
      title: subject || 'No Subject',
      author: sender,
      received_at: new Date(parseInt(gmailMessage.internalDate)).toISOString(),
      created_by: userId,
      summary: gmailMessage.snippet || ''
    })
    .select('id')
    .single();
  
  if (docError) {
    throw new Error(`Failed to create document: ${docError.message}`);
  }
  
  return document.id;
}

async function sendToN8nWebhook(
  userId: string,
  documentId: string,
  gmailMessage: GmailMessage,
  subject: string,
  sender: string,
  username: string
): Promise<boolean> {
  const n8nWebhookUrl = Deno.env.get('N8N_CLASSIFICATION_WEBHOOK_URL');
  
  if (!n8nWebhookUrl) {
    console.warn('N8N webhook URL not configured');
    return false;
  }
  
  try {
    const payload = {
      user_id: userId,
      document_id: documentId,
      gmail_message_id: gmailMessage.id,
      subject: subject,
      sender: sender,
      username: username,
      snippet: gmailMessage.snippet,
      received_at: new Date(parseInt(gmailMessage.internalDate)).toISOString(),
      source: 'gmail',
      type: 'email'
    };
    
    const response = await fetch(n8nWebhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      console.error(`N8N webhook failed: ${response.status} ${response.statusText}`);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('Failed to send to N8N webhook:', error);
    return false;
  }
}

async function processInboundEmail(
  supabase: any,
  gmailMessage: GmailMessage
): Promise<EmailProcessingResult> {
  try {
    // Extract email headers
    const toHeader = getHeaderValue(gmailMessage.payload.headers, 'to');
    const subjectHeader = getHeaderValue(gmailMessage.payload.headers, 'subject');
    const fromHeader = getHeaderValue(gmailMessage.payload.headers, 'from');
    
    if (!toHeader) {
      return {
        success: false,
        message: 'No "To" header found in email'
      };
    }
    
    // Extract username from the "To" address
    const username = extractUsernameFromEmail(toHeader);
    
    if (!username) {
      return {
        success: false,
        message: 'No valid username found in email address'
      };
    }
    
    // Find user by username
    const userId = await findUserByUsername(supabase, username);
    
    if (!userId) {
      // Log the attempt but don't create a document
      await supabase
        .from('email_processing_logs')
        .insert({
          gmail_message_id: gmailMessage.id,
          inbound_address: toHeader,
          extracted_username: username,
          subject: subjectHeader,
          sender: fromHeader,
          status: 'user_not_found',
          error_message: `User not found for username: ${username}`
        });
      
      return {
        success: false,
        message: `User not found for username: ${username}`
      };
    }
    
    // Create document
    const documentId = await createDocumentFromEmail(
      supabase,
      userId,
      gmailMessage,
      subjectHeader || 'No Subject',
      fromHeader || 'Unknown Sender'
    );
    
    // Send to N8N webhook
    const n8nSuccess = await sendToN8nWebhook(
      userId,
      documentId,
      gmailMessage,
      subjectHeader || 'No Subject',
      fromHeader || 'Unknown Sender',
      username
    );
    
    // Log the processing
    await supabase
      .from('email_processing_logs')
      .insert({
        user_id: userId,
        gmail_message_id: gmailMessage.id,
        inbound_address: toHeader,
        extracted_username: username,
        subject: subjectHeader,
        sender: fromHeader,
        processed_at: new Date().toISOString(),
        status: 'processed',
        document_id: documentId,
        n8n_webhook_sent: n8nSuccess,
        n8n_webhook_response: n8nSuccess ? 'success' : 'failed'
      });
    
    return {
      success: true,
      message: `Email processed successfully for user: ${username}`,
      user_id: userId,
      document_id: documentId,
      n8n_webhook_sent: n8nSuccess
    };
    
  } catch (error) {
    console.error('Error processing inbound email:', error);
    
    // Log the error
    await supabase
      .from('email_processing_logs')
      .insert({
        gmail_message_id: gmailMessage.id,
        inbound_address: getHeaderValue(gmailMessage.payload.headers, 'to') || 'unknown',
        extracted_username: extractUsernameFromEmail(getHeaderValue(gmailMessage.payload.headers, 'to') || ''),
        subject: getHeaderValue(gmailMessage.payload.headers, 'subject'),
        sender: getHeaderValue(gmailMessage.payload.headers, 'from'),
        status: 'failed',
        error_message: error.message
      });
    
    return {
      success: false,
      message: `Error processing email: ${error.message}`
    };
  }
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Validate request method
    if (req.method !== 'POST') {
      throw new Error('Method not allowed');
    }

    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error('Server configuration error');
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Parse request body
    const { messages } = await req.json();
    
    if (!messages || !Array.isArray(messages)) {
      throw new Error('Missing or invalid messages array');
    }

    const results: EmailProcessingResult[] = [];
    
    // Process each message
    for (const message of messages) {
      const result = await processInboundEmail(supabase, message);
      results.push(result);
    }
    
    const successCount = results.filter(r => r.success).length;
    const failureCount = results.length - successCount;

    return new Response(
      JSON.stringify({
        success: true,
        message: `Processed ${messages.length} messages: ${successCount} successful, ${failureCount} failed`,
        results,
        summary: {
          total: messages.length,
          successful: successCount,
          failed: failureCount
        }
      }),
      {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );

  } catch (error) {
    console.error('Process inbound emails error:', error);
    
    const errorResponse = {
      success: false,
      error: error.message,
      message: 'Failed to process inbound emails'
    };

    return new Response(
      JSON.stringify(errorResponse),
      {
        status: 400,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
}); 