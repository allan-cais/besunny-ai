/**
 * Classification Helpers
 * 
 * Shared utilities for email and drive notification classification
 * Used by process-inbound-emails and drive-webhook-handler edge functions
 */

export interface Project {
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

export interface Document {
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

export interface User {
  id: string;
  username?: string;
  email?: string;
}

export interface ClassificationPayload {
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

export interface ClassificationResponse {
  success: boolean;
  classified_project_id?: string;
  confidence_score?: number;
  classification_reason?: string;
  alternative_projects?: Array<{
    project_id: string;
    confidence_score: number;
    reason: string;
  }>;
  error?: string;
}

/**
 * Extract username from email address using plus-addressing
 * Example: inbound+johndoe@sunny.ai -> johndoe
 */
export function extractUsernameFromEmail(email: string): string | null {
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

/**
 * Get header value from email headers array
 */
export function getHeaderValue(headers: Array<{ name: string; value: string }>, name: string): string | null {
  const header = headers.find(h => h.name.toLowerCase() === name.toLowerCase());
  return header ? header.value : null;
}

/**
 * Find user by username using Supabase RPC function
 */
export async function findUserByUsername(supabase: any, username: string): Promise<User | null> {
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

/**
 * Get active projects for a user with classification metadata
 */
export async function getActiveProjectsForUser(supabase: any, userId: string): Promise<Project[]> {
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

/**
 * Build classification payload for N8N webhook
 * This is the core function that constructs the payload sent to the classification agent
 */
export function buildClassificationPayload({
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

/**
 * Send classification payload to N8N webhook
 */
export async function sendToN8nWebhook(
  payload: ClassificationPayload,
  webhookUrl?: string
): Promise<boolean> {
  const n8nWebhookUrl = webhookUrl || Deno.env.get('N8N_CLASSIFICATION_WEBHOOK_URL');
  
  if (!n8nWebhookUrl) {
    console.warn('N8N webhook URL not configured');
    return false;
  }
  
  try {

    
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

    
    return true;
  } catch (error) {
    console.error('Failed to send to N8N webhook:', error);
    return false;
  }
}

/**
 * Update document with classified project_id
 */
export async function updateDocumentClassification(
  supabase: any,
  documentId: string,
  projectId: string | null,
  classificationResponse?: ClassificationResponse
): Promise<void> {
  try {
    // Update document with classified project_id
    await supabase
      .from('documents')
      .update({ 
        project_id: projectId,
        updated_at: new Date().toISOString()
      })
      .eq('id', documentId);
    
    // If classification was successful, update project tracking
    if (projectId && classificationResponse?.success) {
      await supabase
        .from('projects')
        .update({ 
          last_classification_at: new Date().toISOString(),
          pinecone_document_count: supabase.sql`pinecone_document_count + 1`
        })
        .eq('id', projectId);
      
      // Update classification feedback if provided
      if (classificationResponse.confidence_score) {
        const feedback = {
          last_classification: {
            document_id: documentId,
            confidence_score: classificationResponse.confidence_score,
            reason: classificationResponse.classification_reason,
            timestamp: new Date().toISOString()
          }
        };
        
        await supabase
          .from('projects')
          .update({ 
            classification_feedback: supabase.sql`COALESCE(classification_feedback, '{}'::jsonb) || ${JSON.stringify(feedback)}::jsonb`
          })
          .eq('id', projectId);
      }
    }
  } catch (error) {
    console.error('Error updating document classification:', error);
    throw error;
  }
}

/**
 * Create document from email data
 */
export async function createDocumentFromEmail(
  supabase: any, 
  userId: string, 
  gmailMessage: any,
  subject: string,
  sender: string
): Promise<string> {
  const { data: document, error: docError } = await supabase
    .from('documents')
    .insert({
      project_id: null, // Will be assigned by n8n classification agent
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

/**
 * Create document from drive notification
 */
export async function createDocumentFromDriveNotification(
  supabase: any,
  userId: string,
  fileId: string,
  fileName: string,
  fileMimeType: string,
  notificationType: string = 'drive_shared'
): Promise<string> {
  const { data: document, error: docError } = await supabase
    .from('documents')
    .insert({
      project_id: null, // Will be assigned by n8n classification agent
      source: 'drive_notification',
      source_id: fileId,
      title: fileName,
      author: 'Google Drive', // Could be enhanced to get actual sharer
      received_at: new Date().toISOString(),
      created_by: userId,
      summary: `File shared via Google Drive: ${fileName}`,
      mimetype: fileMimeType
    })
    .select('id')
    .single();
  
  if (docError) {
    throw new Error(`Failed to create document: ${docError.message}`);
  }
  
  return document.id;
}

/**
 * Log processing event
 */
export async function logProcessingEvent(
  supabase: any,
  logData: {
    user_id?: string;
    gmail_message_id?: string;
    inbound_address?: string;
    extracted_username?: string;
    subject?: string;
    sender?: string;
    status: string;
    document_id?: string;
    n8n_webhook_sent?: boolean;
    n8n_webhook_response?: string;
    error_message?: string;
  }
): Promise<void> {
  try {
    await supabase
      .from('email_processing_logs')
      .insert({
        ...logData,
        processed_at: new Date().toISOString()
      });
  } catch (error) {
    console.error('Error logging processing event:', error);
  }
}

/**
 * Example usage for email processing:
 * 
 * ```typescript
 * // Extract username and find user
 * const username = extractUsernameFromEmail('inbound+johndoe@sunny.ai');
 * const user = await findUserByUsername(supabase, username);
 * 
 * // Create document
 * const documentId = await createDocumentFromEmail(supabase, user.id, gmailMessage, subject, sender);
 * 
 * // Get projects and build payload
 * const projects = await getActiveProjectsForUser(supabase, user.id);
 * const document = await getDocument(supabase, documentId);
 * const payload = buildClassificationPayload({ document, user, projects });
 * 
 * // Send to classification agent
 * const success = await sendToN8nWebhook(payload);
 * 
 * // Log the event
 * await logProcessingEvent(supabase, {
 *   user_id: user.id,
 *   gmail_message_id: gmailMessage.id,
 *   status: 'processed',
 *   document_id: documentId,
 *   n8n_webhook_sent: success
 * });
 * ```
 */ 