import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

interface EnhancedSyncRequest {
  userId: string;
  service: 'calendar' | 'drive' | 'gmail' | 'attendee' | 'all';
  activityType?: 'app_load' | 'calendar_view' | 'meeting_create' | 'general' | 'virtual_email_detected';
  forceSync?: boolean;
  virtualEmailDetection?: {
    emailAddress: string;
    messageId: string;
    type: 'to' | 'cc';
  };
}

interface EnhancedSyncResult {
  success: boolean;
  type: 'calendar' | 'drive' | 'gmail' | 'attendee';
  processed: number;
  created: number;
  updated: number;
  deleted: number;
  skipped: boolean;
  virtualEmailsDetected: number;
  autoScheduledMeetings: number;
  error?: string;
  nextSyncIn?: number;
}

interface VirtualEmailActivity {
  userId: string;
  virtualEmail: string;
  lastDetected: Date;
  detectionCount: number;
  recentActivity: boolean;
  autoScheduledMeetings: number;
}

serve(async (req) => {
  // Handle CORS
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
    const { userId, service, activityType, forceSync, virtualEmailDetection }: EnhancedSyncRequest = await req.json();

    if (!userId) {
      return new Response(JSON.stringify({ error: 'userId is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Record user activity if provided
    if (activityType) {
      await recordUserActivity(supabase, userId, activityType);
    }

    // Handle virtual email detection
    if (virtualEmailDetection) {
      await processVirtualEmailDetection(supabase, userId, virtualEmailDetection);
    }

    // Perform sync based on service
    let results: EnhancedSyncResult[] = [];

    if (service === 'all') {
      results = await Promise.all([
        syncCalendar(supabase, userId, forceSync),
        syncDrive(supabase, userId, forceSync),
        syncGmail(supabase, userId, forceSync),
        syncAttendee(supabase, userId, forceSync),
      ]);
    } else {
      switch (service) {
        case 'calendar':
          results = [await syncCalendar(supabase, userId, forceSync)];
          break;
        case 'drive':
          results = [await syncDrive(supabase, userId, forceSync)];
          break;
        case 'gmail':
          results = [await syncGmail(supabase, userId, forceSync)];
          break;
        case 'attendee':
          results = [await syncAttendee(supabase, userId, forceSync)];
          break;
      }
    }

    // Update user activity state based on results
    await updateUserActivityState(supabase, userId, results);

    // Calculate next sync interval based on virtual email activity
    const nextSyncIn = calculateNextSyncInterval(supabase, userId, results);

    return new Response(JSON.stringify({
      success: true,
      results,
      nextSyncIn,
      virtualEmailActivity: await getVirtualEmailActivity(supabase, userId),
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Enhanced adaptive sync error:', error);
    return new Response(JSON.stringify({ 
      error: error.message,
      success: false 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
});

async function recordUserActivity(supabase: any, userId: string, activityType: string): Promise<void> {
  try {
    await supabase
      .from('user_activity_logs')
      .insert({
        user_id: userId,
        activity_type: activityType,
        timestamp: new Date().toISOString(),
      });
  } catch (error) {
    console.error('Error recording user activity:', error);
  }
}

async function processVirtualEmailDetection(supabase: any, userId: string, detection: any): Promise<void> {
  try {
    // Extract username from virtual email
    const username = extractUsernameFromVirtualEmail(detection.emailAddress);
    if (!username) {
      console.error('Invalid virtual email format:', detection.emailAddress);
      return;
    }

    // Record virtual email detection
    await supabase
      .from('virtual_email_detections')
      .insert({
        user_id: userId,
        virtual_email: detection.emailAddress,
        username,
        email_type: detection.type,
        gmail_message_id: detection.messageId,
        detected_at: new Date().toISOString(),
      });

    // Create document for the email
    const { data: document } = await supabase
      .from('documents')
      .insert({
        user_id: userId,
        title: `Email: ${detection.type.toUpperCase()} - ${detection.emailAddress}`,
        content: `Email received via ${detection.type} with virtual email address ${detection.emailAddress}`,
        source: 'gmail',
        source_id: detection.messageId,
        source_url: `https://mail.google.com/mail/u/0/#inbox/${detection.messageId}`,
        classification_status: 'pending',
        created_at: new Date().toISOString(),
      })
      .select()
      .single();

    // Send to n8n classification webhook
    const n8nWebhookUrl = Deno.env.get('N8N_CLASSIFICATION_WEBHOOK_URL');
    if (n8nWebhookUrl && document) {
      try {
        const response = await fetch(n8nWebhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_id: document.id,
            user_id: userId,
            virtual_email: detection.emailAddress,
            message_id: detection.messageId,
            email_type: detection.type,
          }),
        });

        if (response.ok) {
          // Update document with webhook response
          await supabase
            .from('documents')
            .update({ 
              classification_status: 'sent_to_n8n',
              updated_at: new Date().toISOString()
            })
            .eq('id', document.id);
        }
      } catch (error) {
        console.error('Error sending to n8n webhook:', error);
      }
    }

    console.log(`Virtual email detection processed: ${detection.emailAddress}`);
  } catch (error) {
    console.error('Error processing virtual email detection:', error);
  }
}

function extractUsernameFromVirtualEmail(virtualEmail: string): string | null {
  const match = virtualEmail.match(/^ai\+([^@]+)@besunny\.ai$/);
  return match ? match[1] : null;
}

async function updateUserActivityState(supabase: any, userId: string, results: EnhancedSyncResult[]): Promise<void> {
  try {
    const totalChanges = results.reduce((sum, result) => 
      sum + result.created + result.updated + result.deleted + result.virtualEmailsDetected, 0
    );

    const totalVirtualEmails = results.reduce((sum, result) => 
      sum + result.virtualEmailsDetected, 0
    );

    const totalAutoScheduled = results.reduce((sum, result) => 
      sum + result.autoScheduledMeetings, 0
    );

    // Update user sync state
    await supabase
      .from('user_sync_states')
      .upsert({
        user_id: userId,
        last_sync_at: new Date().toISOString(),
        change_frequency: totalChanges >= 3 ? 'high' : totalChanges >= 1 ? 'medium' : 'low',
        virtual_email_activity: totalVirtualEmails > 0,
        auto_scheduled_meetings: totalAutoScheduled,
        updated_at: new Date().toISOString(),
      });

    // Record sync performance
    await supabase
      .from('sync_performance_metrics')
      .insert({
        user_id: userId,
        sync_type: 'enhanced_adaptive',
        total_processed: results.reduce((sum, r) => sum + r.processed, 0),
        total_created: results.reduce((sum, r) => sum + r.created, 0),
        total_updated: results.reduce((sum, r) => sum + r.updated, 0),
        total_deleted: results.reduce((sum, r) => sum + r.deleted, 0),
        virtual_emails_detected: totalVirtualEmails,
        auto_scheduled_meetings: totalAutoScheduled,
        sync_duration_ms: 0, // Would be calculated in real implementation
        success: results.every(r => r.success),
        timestamp: new Date().toISOString(),
      });

  } catch (error) {
    console.error('Error updating user activity state:', error);
  }
}

async function getVirtualEmailActivity(supabase: any, userId: string): Promise<VirtualEmailActivity | null> {
  try {
    // Get user's username
    const { data: user } = await supabase
      .from('users')
      .select('username')
      .eq('id', userId)
      .single();

    if (!user?.username) {
      return null;
    }

    const virtualEmail = `ai+${user.username}@besunny.ai`;

    // Get recent virtual email detections
    const { data: recentDetections } = await supabase
      .from('virtual_email_detections')
      .select('detected_at')
      .eq('user_id', userId)
      .gte('detected_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
      .order('detected_at', { ascending: false });

    // Get auto-scheduled meetings count
    const { data: autoScheduledMeetings } = await supabase
      .from('meetings')
      .select('id')
      .eq('user_id', userId)
      .eq('auto_scheduled_via_email', true)
      .gte('created_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

    const lastDetected = recentDetections?.[0]?.detected_at 
      ? new Date(recentDetections[0].detected_at)
      : null;

    const recentActivity = lastDetected && 
      (Date.now() - lastDetected.getTime()) < 30 * 60 * 1000; // 30 minutes

    return {
      userId,
      virtualEmail,
      lastDetected: lastDetected || new Date(0),
      detectionCount: recentDetections?.length || 0,
      recentActivity,
      autoScheduledMeetings: autoScheduledMeetings?.length || 0,
    };
  } catch (error) {
    console.error('Error getting virtual email activity:', error);
    return null;
  }
}

function calculateNextSyncInterval(supabase: any, userId: string, results: EnhancedSyncResult[]): number {
  // Calculate next sync interval based on activity and virtual email detection
  const totalVirtualEmails = results.reduce((sum, result) => 
    sum + result.virtualEmailsDetected, 0
  );

  const totalChanges = results.reduce((sum, result) => 
    sum + result.created + result.updated + result.deleted, 0
  );

  // If virtual emails detected, sync more frequently
  if (totalVirtualEmails > 0) {
    return 60 * 1000; // 1 minute
  }

  // If changes detected, sync moderately
  if (totalChanges > 0) {
    return 5 * 60 * 1000; // 5 minutes
  }

  // Default background sync
  return 15 * 60 * 1000; // 15 minutes
}

async function syncCalendar(supabase: any, userId: string, forceSync?: boolean): Promise<EnhancedSyncResult> {
  try {
    // Get user's Google credentials
    const { data: credentials } = await supabase
      .from('google_credentials')
      .select('access_token, refresh_token')
      .eq('user_id', userId)
      .eq('service', 'calendar')
      .single();

    if (!credentials) {
      return {
        success: true,
        type: 'calendar',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: true,
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
      };
    }

    // Check for virtual email attendees in recent meetings
    const { data: recentMeetings } = await supabase
      .from('meetings')
      .select('id, auto_scheduled_via_email, virtual_email_attendee')
      .eq('user_id', userId)
      .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

    const virtualEmailMeetings = recentMeetings?.filter(m => m.auto_scheduled_via_email) || [];

    // This would normally sync with Google Calendar API
    // For now, return simplified result
    return {
      success: true,
      type: 'calendar',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: virtualEmailMeetings.length,
      autoScheduledMeetings: virtualEmailMeetings.length,
    };

  } catch (error) {
    return {
      success: false,
      type: 'calendar',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings: 0,
      error: error.message,
    };
  }
}

async function syncDrive(supabase: any, userId: string, forceSync?: boolean): Promise<EnhancedSyncResult> {
  try {
    // Get user's drive files
    const { data: files } = await supabase
      .from('drive_file_watches')
      .select('file_id, document_id')
      .eq('is_active', true);

    if (!files || files.length === 0) {
      return {
        success: true,
        type: 'drive',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: true,
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
      };
    }

    // This would normally check file metadata and compare with last sync
    return {
      success: true,
      type: 'drive',
      processed: files.length,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings: 0,
    };

  } catch (error) {
    return {
      success: false,
      type: 'drive',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings: 0,
      error: error.message,
    };
  }
}

async function syncGmail(supabase: any, userId: string, forceSync?: boolean): Promise<EnhancedSyncResult> {
  try {
    // Get user's Gmail watch status
    const { data: gmailWatch } = await supabase
      .from('gmail_watches')
      .select('user_email')
      .eq('is_active', true)
      .single();

    if (!gmailWatch) {
      return {
        success: true,
        type: 'gmail',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: true,
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
      };
    }

    // Get recent virtual email detections
    const { data: recentDetections } = await supabase
      .from('virtual_email_detections')
      .select('id, detected_at')
      .eq('user_id', userId)
      .gte('detected_at', new Date(Date.now() - 60 * 60 * 1000).toISOString()); // Last hour

    // Get pending email processing logs
    const { data: pendingEmails } = await supabase
      .from('email_processing_logs')
      .select('id, status')
      .eq('user_id', userId)
      .eq('status', 'pending');

    const virtualEmailsDetected = recentDetections?.length || 0;
    const processed = pendingEmails?.length || 0;

    return {
      success: true,
      type: 'gmail',
      processed,
      created: processed,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected,
      autoScheduledMeetings: 0,
    };

  } catch (error) {
    return {
      success: false,
      type: 'gmail',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings: 0,
      error: error.message,
    };
  }
}

async function syncAttendee(supabase: any, userId: string, forceSync?: boolean): Promise<EnhancedSyncResult> {
  try {
    // Get meetings that need polling
    const { data: meetings } = await supabase
      .from('meetings')
      .select('id, title, bot_status, auto_scheduled_via_email')
      .eq('user_id', userId)
      .eq('polling_enabled', true)
      .in('bot_status', ['bot_scheduled', 'bot_joined', 'transcribing']);

    if (!meetings || meetings.length === 0) {
      return {
        success: true,
        type: 'attendee',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: true,
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
      };
    }

    const autoScheduledMeetings = meetings.filter(m => m.auto_scheduled_via_email).length;

    // Poll each meeting (simplified implementation)
    let processed = 0;
    for (const meeting of meetings) {
      try {
        // This would normally call the attendee polling service
        processed++;
      } catch (error) {
        console.error(`Error polling meeting ${meeting.id}:`, error);
      }
    }

    return {
      success: true,
      type: 'attendee',
      processed,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings,
    };

  } catch (error) {
    return {
      success: false,
      type: 'attendee',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
      virtualEmailsDetected: 0,
      autoScheduledMeetings: 0,
      error: error.message,
    };
  }
} 