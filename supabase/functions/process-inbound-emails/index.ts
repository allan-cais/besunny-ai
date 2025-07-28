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

interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
  normalized_tags?: string[];
  categories?: string[];
  reference_keywords?: string[];
  notes?: string;
  classification_signals?: any;
  entity_patterns?: any;
  created_by: string;
}

interface Document {
  id: string;
  project_id: string | null;
  source: string;
  source_id: string;
  title: string;
  author: string;
  received_at: string;
  summary: string;
  mimetype?: string;
}

interface User {
  id: string;
  username?: string;
  email?: string;
}

interface ClassificationPayload {
  document_id: string;
  user_id: string;
  type: 'email' | 'drive_notification';
  source: string;
  title: string;
  author: string;
  received_at: string;
  content: string;
  metadata: {
    gmail_message_id?: string;
    filename?: string;
    mimetype?: string | null;
    notification_type?: string;
  };
  project_metadata: Array<{
    project_id: string;
    normalized_tags?: string[];
    categories?: string[];
    reference_keywords?: string[];
    notes?: string;
    classification_signals?: any;
    entity_patterns?: any;
  }>;
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

async function findUserByUsername(supabase: any, username: string): Promise<User | null> {
  const { data, error } = await supabase
    .rpc('get_user_by_username', { search_username: username })
    .maybeSingle();
  
  if (error || !data) {
    return null;
  }
  
  return {
    id: data.user_id,
    username: username,
    email: data.email
  };
}

async function createDocumentFromEmail(
  supabase: any, 
  userId: string, 
  gmailMessage: GmailMessage,
  subject: string,
  sender: string
): Promise<string> {
  // Create a document record
  // Note: project_id is initially null and will be assigned by the n8n classification agent
  // based on the content analysis and AI reasoning
  const { data: document, error: docError } = await supabase
    .from('documents')
    .insert({
      project_id: null, // Will be assigned by n8n classification agent based on content analysis
      source: 'gmail',
      source_id: gmailMessage.id,
      title: subject || 'No Subject',
      author: sender,
      received_at: new Date(parseInt(gmailMessage.internalDate)).toISOString(),
      created_by: userId,
      summary: gmailMessage.snippet || '',
      mimetype: gmailMessage.payload.mimeType || null
    })
    .select('id')
    .single();
  
  if (docError) {
    throw new Error(`Failed to create document: ${docError.message}`);
  }
  
  return document.id;
}

async function getActiveProjectsForUser(supabase: any, userId: string): Promise<Project[]> {
  const { data: projects, error } = await supabase
    .from('projects')
    .select(`
      id,
      name,
      description,
      status,
      normalized_tags,
      categories,
      reference_keywords,
      notes,
      classification_signals,
      entity_patterns,
      created_by
    `)
    .eq('created_by', userId)
    .in('status', ['active', 'in_progress'])
    .order('last_classification_at', { ascending: false, nullsLast: true });
  
  if (error) {
    console.error('Error fetching projects:', error);
    return [];
  }
  
  return projects || [];
}

function buildClassificationPayload({
  document,
  user,
  projects
}: {
  document: Document;
  user: User;
  projects: Project[];
}): ClassificationPayload {
  return {
    document_id: document.id,
    user_id: user.id,
    type: document.source === 'gmail' ? 'email' : 'drive_notification',
    source: document.source,
    title: document.title,
    author: document.author,
    received_at: document.received_at,
    content: document.summary,
    metadata: {
      gmail_message_id: document.source_id,
      filename: document.title,
      mimetype: document.mimetype || null,
      notification_type: document.source === 'drive_notification' ? 'drive_shared' : undefined
    },
    project_metadata: projects.map(project => ({
      project_id: project.id,
      normalized_tags: project.normalized_tags,
      categories: project.categories,
      reference_keywords: project.reference_keywords,
      notes: project.notes,
      classification_signals: project.classification_signals,
      entity_patterns: project.entity_patterns
    }))
  };
}

async function sendToN8nWebhook(
  payload: ClassificationPayload
): Promise<boolean> {
  const n8nWebhookUrl = Deno.env.get('N8N_CLASSIFICATION_WEBHOOK_URL');
  
  if (!n8nWebhookUrl) {
    console.warn('N8N webhook URL not configured');
    return false;
  }
  
  try {
    console.log('Sending classification payload to N8N:', JSON.stringify(payload, null, 2));
    
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
    
    const responseText = await response.text();
    console.log('N8N webhook response:', responseText);
    
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
    const user = await findUserByUsername(supabase, username);
    
    if (!user) {
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
      user.id,
      gmailMessage,
      subjectHeader || 'No Subject',
      fromHeader || 'Unknown Sender'
    );
    
    // Get the created document
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .single();
    
    if (docError || !document) {
      throw new Error(`Failed to retrieve created document: ${docError?.message}`);
    }
    
    // Get active projects for the user
    const projects = await getActiveProjectsForUser(supabase, user.id);
    
    // Build classification payload
    const classificationPayload = buildClassificationPayload({
      document,
      user,
      projects
    });
    
    // Send to N8N webhook
    const n8nSuccess = await sendToN8nWebhook(classificationPayload);
    
    // Log the processing
    await supabase
      .from('email_processing_logs')
      .insert({
        user_id: user.id,
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
      user_id: user.id,
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