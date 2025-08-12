import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

interface GmailHistory {
  historyId: string;
  messagesAdded?: Array<{
    message: {
      id: string;
      threadId: string;
    };
  }>;
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

// Get Gmail message details
async function getGmailMessage(userEmail: string, accessToken: string, messageId: string) {
  const response = await fetch(
    `https://gmail.googleapis.com/gmail/v1/users/${userEmail}/messages/${messageId}?format=full`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    }
  );
  
  if (!response.ok) {
    throw new Error(`Failed to get Gmail message: ${response.status}`);
  }
  
  return await response.json();
}

// Extract email addresses from Gmail message headers
function extractEmailAddresses(headers: any[], headerName: string): string[] {
  const header = headers.find(h => h.name.toLowerCase() === headerName.toLowerCase());
  if (!header) return [];
  
  // Parse email addresses from header value
  const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
  const matches = header.value.match(emailRegex);
  return matches || [];
}

// Check if email contains virtual email addresses
function checkForVirtualEmails(toEmails: string[], ccEmails: string[]): Array<{ email: string; username: string; type: 'to' | 'cc' }> {
  const virtualEmailPattern = /ai\+([^@]+)@besunny\.ai/;
  const virtualEmails: Array<{ email: string; username: string; type: 'to' | 'cc' }> = [];
  
  // Check TO addresses
  for (const email of toEmails) {
    const match = email.match(virtualEmailPattern);
    if (match) {
      virtualEmails.push({
        email,
        username: match[1],
        type: 'to'
      });
    }
  }
  
  // Check CC addresses
  for (const email of ccEmails) {
    const match = email.match(virtualEmailPattern);
    if (match) {
      virtualEmails.push({
        email,
        username: match[1],
        type: 'cc'
      });
    }
  }
  
  return virtualEmails;
}

// Process virtual email detection
async function processVirtualEmailDetection(userEmail: string, messageId: string, virtualEmails: Array<{ email: string; username: string; type: 'to' | 'cc' }>) {
  for (const virtualEmail of virtualEmails) {
    // Find the user by username
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('id, email')
      .ilike('email', `%${virtualEmail.username}%`)
      .single();
    
    if (userError || !user) {
              // User not found for virtual email
      continue;
    }
    
    // Create a document record for the email
    const { data: document, error: docError } = await supabase
      .from('documents')
      .insert({
        user_id: user.id,
        title: `Email: ${virtualEmail.type.toUpperCase()} - ${virtualEmail.email}`,
        content: `Email received via ${virtualEmail.type} with virtual email address ${virtualEmail.email}`,
        source: 'gmail',
        source_id: messageId,
        source_url: `https://mail.google.com/mail/u/0/#inbox/${messageId}`,
        classification_status: 'pending',
        created_at: new Date().toISOString(),
      })
      .select()
      .single();
    
    if (docError) {
              // Error creating document
      continue;
    }
    
    // Send to n8n for classification
    try {
      const n8nResponse = await fetch(Deno.env.get('N8N_WEBHOOK_URL') || '', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'virtual_email_detection',
          user_id: user.id,
          document_id: document.id,
          virtual_email: virtualEmail.email,
          username: virtualEmail.username,
          email_type: virtualEmail.type,
          message_id: messageId,
          timestamp: new Date().toISOString(),
        }),
      });
      
      if (!n8nResponse.ok) {
        // Failed to send to n8n
      }
    } catch (error) {
              // Error sending to n8n
    }
    
    // Log the virtual email detection
    await supabase
      .from('virtual_email_detections')
      .insert({
        user_id: user.id,
        virtual_email: virtualEmail.email,
        username: virtualEmail.username,
        email_type: virtualEmail.type,
        gmail_message_id: messageId,
        document_id: document.id,
        detected_at: new Date().toISOString(),
      });
  }
}

// Poll Gmail for new messages (smart polling with webhook activity check)
async function pollGmailForUser(userEmail: string): Promise<{ processed: number; detections: number; skipped: boolean }> {
  try {
    // Get current Gmail watch status
    const { data: watchStatus } = await supabase
      .from('gmail_watches')
      .select('history_id, last_webhook_received, watch_type')
      .eq('user_email', userEmail)
      .eq('is_active', true)
      .single();
    
    if (!watchStatus) {
      // No active Gmail watch found
      return { processed: 0, detections: 0, skipped: true };
    }
    
    // Smart polling: Skip if webhook was received recently (within 6 hours)
    if (watchStatus.last_webhook_received) {
      const lastWebhookTime = new Date(watchStatus.last_webhook_received);
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000);
      
      if (lastWebhookTime > sixHoursAgo) {
        // Skipping polling - webhook received recently
        return { processed: 0, detections: 0, skipped: true };
      }
    }
    
    // Get service account credentials
    const credentials = await getGoogleServiceAccountCredentials();
    
    // Generate JWT for the specific user
    const jwt = await generateGoogleJWT(credentials, userEmail);
    
    // Exchange JWT for access token
    const accessToken = await getAccessToken(jwt);
    
    if (!watchStatus) {
      // No active Gmail watch found
      return { processed: 0, detections: 0 };
    }
    
    // Get Gmail history since last check
    const historyResponse = await fetch(
      `https://gmail.googleapis.com/gmail/v1/users/${userEmail}/history?startHistoryId=${watchStatus.history_id}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    );
    
    if (!historyResponse.ok) {
      if (historyResponse.status === 404) {
        // History ID is too old, need to get a new one
        // History ID is too old
        return { processed: 0, detections: 0 };
      }
      throw new Error(`Failed to get Gmail history: ${historyResponse.status}`);
    }
    
    const historyData: GmailHistory = await historyResponse.json();
    
    let processed = 0;
    let detections = 0;
    
    // Process new messages
    if (historyData.messagesAdded) {
      for (const messageAdded of historyData.messagesAdded) {
        try {
          const message = await getGmailMessage(userEmail, accessToken, messageAdded.message.id);
          
          // Extract email addresses
          const toEmails = extractEmailAddresses(message.payload.headers, 'to');
          const ccEmails = extractEmailAddresses(message.payload.headers, 'cc');
          
          // Check for virtual emails
          const virtualEmails = checkForVirtualEmails(toEmails, ccEmails);
          
          if (virtualEmails.length > 0) {
            // Found virtual emails in message
            await processVirtualEmailDetection(userEmail, messageAdded.message.id, virtualEmails);
            detections += virtualEmails.length;
          }
          
          processed++;
        } catch (error) {
          // Error processing message
        }
      }
    }
    
    // Update the history ID and polling timestamp for next poll
    if (historyData.historyId) {
      await supabase
        .from('gmail_watches')
        .update({ 
          history_id: historyData.historyId,
          last_poll_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .eq('user_email', userEmail);
    }
    
    return { processed, detections, skipped: false };
  } catch (error) {
    // Error polling Gmail
    return { processed: 0, detections: 0, skipped: false };
  }
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

    // Polling Gmail for user
    
    const result = await pollGmailForUser(userEmail);
    
    return new Response(JSON.stringify({
      success: true,
      processed: result.processed,
      detections: result.detections,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    // Gmail polling service error
    return new Response(JSON.stringify({ 
      error: error.message || 'Failed to poll Gmail' 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}); 