import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const MASTER_ATTENDEE_API_KEY = Deno.env.get('MASTER_ATTENDEE_API_KEY');
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  resp.headers.set('Access-Control-Allow-Headers', 'authorization, x-client-info, apikey, content-type');
  return resp;
}

function getUserIdFromAuth(req: Request): string | null {
  const auth = req.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return null;
  const jwt = auth.replace('Bearer ', '');
  const payload = JSON.parse(atob(jwt.split('.')[1]));
  return payload.sub || null;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;
  const userId = getUserIdFromAuth(req);
  
  if (!userId) {
    return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
  }

  // Auto-schedule bots for meetings with virtual email attendees
  if (url.pathname.endsWith('/schedule') && method === 'POST') {
    try {
      const result = await autoScheduleBotsForUser(userId);
      return withCORS(new Response(JSON.stringify({
        success: true,
        result
      }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({
        success: false,
        error: error.message
      }), { status: 500 }));
    }
  }

  // Get meetings that need auto-scheduling
  if (url.pathname.endsWith('/pending') && method === 'GET') {
    try {
      const { data: meetings, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('user_id', userId)
        .eq('auto_scheduled_via_email', true)
        .eq('bot_deployment_method', 'scheduled')
        .eq('bot_status', 'pending')
        .not('meeting_url', 'is', null)
        .gte('start_time', new Date().toISOString());

      if (error) throw error;

      return withCORS(new Response(JSON.stringify({
        success: true,
        meetings: meetings || []
      }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({
        success: false,
        error: error.message
      }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});

async function autoScheduleBotsForUser(userId: string) {
  if (!MASTER_ATTENDEE_API_KEY) {
    throw new Error('Master Attendee API key not configured');
  }

  // Find meetings that need auto-scheduling (virtual email) OR manual scheduling that are ready
  const { data: meetings, error } = await supabase
    .from('meetings')
    .select('*')
    .eq('user_id', userId)
    .or(`and(auto_scheduled_via_email.eq.true,bot_deployment_method.eq.scheduled,bot_status.eq.pending),and(bot_deployment_method.eq.scheduled,bot_status.eq.pending)`)
    .not('meeting_url', 'is', null)
    .gte('start_time', new Date().toISOString());

  if (error) throw error;

  const results = [];
  
  for (const meeting of meetings || []) {
    try {
      // Use stored configuration or default configuration
      const config = meeting.bot_configuration || {
        bot_name: 'Sunny AI Assistant',
        bot_chat_message: {
          to: 'everyone',
          message: 'Hi, I\'m here to transcribe this meeting!',
        },
        transcription_language: 'en-US',
        auto_join: true,
        recording_enabled: true
      };

      // Calculate join time (2 minutes before meeting start)
      const meetingStartTime = new Date(meeting.start_time);
      const joinAtTime = new Date(meetingStartTime.getTime() - 2 * 60 * 1000); // 2 minutes before

      console.log(`Scheduling bot for meeting ${meeting.id} to join at ${joinAtTime.toISOString()}`);

      // Build basic bot configuration - only essential options
      const botOptions: any = {
        // Basic required fields
        meeting_url: meeting.meeting_url,
        bot_name: config.bot_name,
        
        // Chat message configuration
        bot_chat_message: {
          to: config.bot_chat_message?.to || 'everyone',
          message: config.bot_chat_message?.message || 'Hi, I\'m here to transcribe this meeting!',
        },
        
        // Future scheduling
        join_at: joinAtTime.toISOString(),
        
        // Advanced features - left as defaults (not included in API call)
        // transcription_settings, recording_settings, teams_settings, debug_settings,
        // automatic_leave_settings, webhooks, metadata, deduplication_key, custom_settings
        // will all use Attendee API defaults
      };
      
      // Note: transcription_settings.language is not supported by Attendee API
      // Language will use API defaults

      // Send bot to meeting via Attendee API with basic configuration
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(botOptions)
      });

      if (!response.ok) {
        throw new Error(`Attendee API error: ${response.status}`);
      }

      const botData = await response.json();
      const attendeeBotId = botData.id || botData.bot_id;

      if (!attendeeBotId) {
        throw new Error('No bot ID returned from Attendee API');
      }

      // Create a bot record in the bots table with basic settings
      const { data: botRecord, error: botError } = await supabase
        .from('bots')
        .insert({
          user_id: userId,
          name: config.bot_name,
          description: 'Basic auto-created bot for meeting transcription',
          provider: 'attendee',
          provider_bot_id: attendeeBotId,
          settings: {
            attendee_bot_id: attendeeBotId,
            created_via: meeting.auto_scheduled_via_email ? 'auto_scheduling' : 'manual_deployment',
            meeting_id: meeting.id,
            configuration: config,
            join_at: joinAtTime.toISOString(),
            meeting_start_time: meeting.start_time,
            // Advanced settings not stored - using API defaults
          },
          is_active: true
        })
        .select()
        .single();

      if (botError) {
        throw new Error(`Failed to create bot record: ${botError.message}`);
      }

      // Update meeting with bot UUID and status
      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: botRecord.id, // Use the UUID from the bots table
          bot_status: 'bot_scheduled',
          bot_deployment_method: meeting.auto_scheduled_via_email ? 'automatic' : 'manual',
          bot_configuration: config,
          updated_at: new Date().toISOString()
        })
        .eq('id', meeting.id);

      // Log the deployment
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: meeting.auto_scheduled_via_email ? 'auto_bot_scheduling' : 'manual_bot_deployment',
          status: 'completed',
          events_processed: 1,
          meetings_created: 1,
          error_message: `${meeting.auto_scheduled_via_email ? 'Auto-scheduled' : 'Manually deployed'} bot for meeting: ${meeting.title} (joins at ${joinAtTime.toISOString()})`
        });

      results.push({
        meetingId: meeting.id,
        title: meeting.title,
        botId: botRecord.id, // Use the UUID from the bots table
        success: true,
        deploymentType: meeting.auto_scheduled_via_email ? 'automatic' : 'manual',
        joinAt: joinAtTime.toISOString()
      });

    } catch (error) {
      console.error(`Failed to deploy bot for meeting ${meeting.id}:`, error);
      
      // Log the error
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: meeting.auto_scheduled_via_email ? 'auto_bot_scheduling' : 'manual_bot_deployment',
          status: 'failed',
          events_processed: 1,
          meetings_created: 0,
          error_message: `Failed to deploy bot for meeting ${meeting.title}: ${error.message}`
        });

      results.push({
        meetingId: meeting.id,
        title: meeting.title,
        success: false,
        error: error.message
      });
    }
  }

  return {
    totalMeetings: meetings?.length || 0,
    successfulDeployments: results.filter(r => r.success).length,
    failedDeployments: results.filter(r => !r.success).length,
    results
  };
} 