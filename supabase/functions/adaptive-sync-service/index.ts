import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
}

interface SyncRequest {
  userId: string;
  service: 'calendar' | 'drive' | 'gmail' | 'attendee' | 'all';
  activityType?: 'app_load' | 'calendar_view' | 'meeting_create' | 'general';
  forceSync?: boolean;
}

interface SyncResult {
  success: boolean;
  type: 'calendar' | 'drive' | 'gmail' | 'attendee';
  processed: number;
  created: number;
  updated: number;
  deleted: number;
  skipped: boolean;
  error?: string;
  nextSyncIn?: number;
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: corsHeaders,
    });
  }

  try {
    const { userId, service, activityType, forceSync }: SyncRequest = await req.json();

    if (!userId) {
      return new Response(
        JSON.stringify({ error: 'userId is required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    console.log(`Adaptive sync request for user ${userId}, service: ${service}, activity: ${activityType}`);

    // Record activity if provided
    if (activityType) {
      await recordUserActivity(supabase, userId, activityType);
    }

    // Perform sync based on service
    let results: SyncResult[] = [];

    if (service === 'all' || service === 'calendar') {
      const calendarResult = await syncCalendar(supabase, userId, forceSync);
      results.push(calendarResult);
    }

    if (service === 'all' || service === 'drive') {
      const driveResult = await syncDrive(supabase, userId, forceSync);
      results.push(driveResult);
    }

    if (service === 'all' || service === 'gmail') {
      const gmailResult = await syncGmail(supabase, userId, forceSync);
      results.push(gmailResult);
    }

    if (service === 'all' || service === 'attendee') {
      const attendeeResult = await syncAttendee(supabase, userId, forceSync);
      results.push(attendeeResult);
    }

    // Update user activity state
    await updateUserActivityState(supabase, userId, results);

    return new Response(
      JSON.stringify({
        success: true,
        results,
        timestamp: new Date().toISOString(),
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Adaptive sync error:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
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

async function updateUserActivityState(supabase: any, userId: string, results: SyncResult[]): Promise<void> {
  try {
    const changes = results.filter(r => r.created > 0 || r.updated > 0 || r.deleted > 0).length;
    const changeFrequency = changes >= 3 ? 'high' : changes >= 1 ? 'medium' : 'low';

    await supabase
      .from('user_sync_states')
      .upsert({
        user_id: userId,
        last_sync_time: new Date().toISOString(),
        change_frequency: changeFrequency,
        last_activity_time: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
  } catch (error) {
    console.error('Error updating user activity state:', error);
  }
}

async function syncCalendar(supabase: any, userId: string, forceSync?: boolean): Promise<SyncResult> {
  try {
    // Check if we should skip sync based on recent activity
    if (!forceSync) {
      const { data: lastSync } = await supabase
        .from('user_sync_states')
        .select('last_sync_time')
        .eq('user_id', userId)
        .single();

      if (lastSync?.last_sync_time) {
        const lastSyncTime = new Date(lastSync.last_sync_time);
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
        
        if (lastSyncTime > fiveMinutesAgo) {
          return {
            success: true,
            type: 'calendar',
            processed: 0,
            created: 0,
            updated: 0,
            deleted: 0,
            skipped: true,
          };
        }
      }
    }

    // Get user's Google credentials
    const { data: credentials } = await supabase
      .from('google_credentials')
      .select('access_token, refresh_token')
      .eq('user_id', userId)
      .single();

    if (!credentials) {
      return {
        success: false,
        type: 'calendar',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        error: 'No Google credentials found',
      };
    }

    // Get current sync token
    const { data: webhook } = await supabase
      .from('calendar_webhooks')
      .select('sync_token')
      .eq('user_id', userId)
      .eq('is_active', true)
      .single();

    let processed = 0;
    let created = 0;
    let updated = 0;
    let deleted = 0;

    // Perform incremental sync if we have a sync token
    if (webhook?.sync_token) {
      try {
        const response = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
          `syncToken=${webhook.sync_token}&singleEvents=true&showDeleted=true`,
          {
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          const events = data.items || [];
          const nextSyncToken = data.nextSyncToken;

          // Process events
          for (const event of events) {
            processed++;
            if (event.status === 'cancelled' || event.deleted) {
              deleted++;
            } else {
              // Process event (simplified for this example)
              const existingMeeting = await supabase
                .from('meetings')
                .select('id')
                .eq('google_event_id', event.id)
                .single();

              if (existingMeeting.data) {
                updated++;
              } else {
                created++;
              }
            }
          }

          // Update sync token
          await supabase
            .from('calendar_webhooks')
            .update({ sync_token: nextSyncToken })
            .eq('user_id', userId);
        }
      } catch (error) {
        console.error('Calendar sync error:', error);
      }
    }

    return {
      success: true,
      type: 'calendar',
      processed,
      created,
      updated,
      deleted,
      skipped: false,
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
      error: error.message,
    };
  }
}

async function syncDrive(supabase: any, userId: string, forceSync?: boolean): Promise<SyncResult> {
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
      };
    }

    let processed = 0;
    let created = 0;
    let updated = 0;
    let deleted = 0;

    // Check each file for changes (simplified implementation)
    for (const file of files) {
      try {
        // This would normally check file metadata and compare with last sync
        // For now, we'll just mark as processed
        processed++;
      } catch (error) {
        console.error(`Error checking drive file ${file.file_id}:`, error);
      }
    }

    return {
      success: true,
      type: 'drive',
      processed,
      created,
      updated,
      deleted,
      skipped: false,
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
      error: error.message,
    };
  }
}

async function syncGmail(supabase: any, userId: string, forceSync?: boolean): Promise<SyncResult> {
  try {
    // Get user's Gmail watch status
    const { data: gmailWatch } = await supabase
      .from('gmail_watches')
      .select('user_email, history_id')
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
      };
    }

    // This would normally poll Gmail API for new messages
    // For now, we'll return a simplified result
    return {
      success: true,
      type: 'gmail',
      processed: 0,
      created: 0,
      updated: 0,
      deleted: 0,
      skipped: false,
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
      error: error.message,
    };
  }
}

async function syncAttendee(supabase: any, userId: string, forceSync?: boolean): Promise<SyncResult> {
  try {
    // Get meetings that need polling
    const { data: meetings } = await supabase
      .from('meetings')
      .select('id, title, bot_status')
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
      };
    }

    let processed = 0;

    // Poll each meeting (simplified implementation)
    for (const meeting of meetings) {
      try {
        // This would normally call the attendee polling service
        // For now, we'll just mark as processed
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
      error: error.message,
    };
  }
} 