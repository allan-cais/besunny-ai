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

  // Find meetings that need auto-scheduling
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

  const results = [];
  
  for (const meeting of meetings || []) {
    try {
      // Use default configuration for auto-scheduled bots
      const defaultConfig = {
        bot_name: 'Sunny AI Assistant',
        bot_chat_message: {
          to: 'everyone',
          message: 'Hi, I\'m here to transcribe this meeting!',
        },
        language: 'en-US',
        auto_join: true,
        recording_enabled: true
      };

      // Send bot to meeting via Attendee API
      const response = await fetch('https://app.attendee.dev/api/v1/bots', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meeting_url: meeting.meeting_url,
          bot_name: defaultConfig.bot_name,
          bot_chat_message: defaultConfig.bot_chat_message,
          language: defaultConfig.language,
          auto_join: defaultConfig.auto_join,
          recording_enabled: defaultConfig.recording_enabled
        })
      });

      if (!response.ok) {
        throw new Error(`Attendee API error: ${response.status}`);
      }

      const botData = await response.json();
      const botId = botData.id || botData.bot_id;

      // Update meeting with bot details
      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: botId,
          bot_status: 'bot_scheduled',
          bot_deployment_method: 'automatic',
          bot_configuration: defaultConfig,
          updated_at: new Date().toISOString()
        })
        .eq('id', meeting.id);

      // Log the auto-scheduling
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: 'auto_bot_scheduling',
          status: 'completed',
          events_processed: 1,
          meetings_created: 1,
          error_message: `Auto-scheduled bot for meeting: ${meeting.title}`
        });

      results.push({
        meetingId: meeting.id,
        title: meeting.title,
        botId: botId,
        success: true
      });

    } catch (error) {
      console.error(`Failed to auto-schedule bot for meeting ${meeting.id}:`, error);
      
      // Log the error
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: 'auto_bot_scheduling',
          status: 'failed',
          events_processed: 1,
          meetings_created: 0,
          error_message: `Failed to auto-schedule bot for meeting ${meeting.title}: ${error.message}`
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
    successfulSchedules: results.filter(r => r.success).length,
    failedSchedules: results.filter(r => !r.success).length,
    results
  };
} 