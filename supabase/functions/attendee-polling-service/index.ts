import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const MASTER_ATTENDEE_API_KEY = Deno.env.get('MASTER_ATTENDEE_API_KEY');
const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const supabase = createClient(supabaseUrl, supabaseServiceKey);

function withCORS(response: Response): Response {
  for (const [key, value] of Object.entries(corsHeaders)) {
    response.headers.set(key, value);
  }
  return response;
}

async function getUserIdFromAuth(req: Request): Promise<string | null> {
  const authHeader = req.headers.get('Authorization');
  if (!authHeader) return null;
  
  const token = authHeader.replace('Bearer ', '');
  const { data: { user }, error } = await supabase.auth.getUser(token);
  
  if (error || !user) return null;
  return user.id;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;

  // Manual polling trigger (for testing)
  if (url.pathname.endsWith('/poll-now') && method === 'POST') {
    const userId = getUserIdFromAuth(req);
    if (!userId) {
      return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
    }

    try {
      const result = await pollAllMeetings();
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Get meetings that need polling
  if (url.pathname.endsWith('/get-pending') && method === 'GET') {
    const userId = getUserIdFromAuth(req);
    if (!userId) {
      return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
    }

    try {
      const { data, error } = await supabase.rpc('get_meetings_for_polling');
      if (error) throw error;
      
      return withCORS(new Response(JSON.stringify({ meetings: data }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Poll specific meeting
  if (url.pathname.endsWith('/poll-meeting') && method === 'POST') {
    const userId = getUserIdFromAuth(req);
    if (!userId) {
      return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
    }

    try {
      const { meetingId } = await req.json();
      if (!meetingId) {
        return withCORS(new Response(JSON.stringify({ error: 'Missing meetingId' }), { status: 400 }));
      }

      const result = await pollMeeting(meetingId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});

async function pollAllMeetings() {
  const { data: meetings, error } = await supabase.rpc('get_meetings_for_polling');
  if (error) throw error;

  const results = [];
  for (const meeting of meetings || []) {
    try {
      const result = await pollMeeting(meeting.id);
      results.push({ meetingId: meeting.id, ...result });
    } catch (error) {
      results.push({ meetingId: meeting.id, error: error.message });
    }
  }

  return results;
}

async function pollMeeting(meetingId: string) {
  // Get meeting details
  const { data: meeting, error: meetingError } = await supabase
    .from('meetings')
    .select('*')
    .eq('id', meetingId)
    .single();

  if (meetingError || !meeting) {
    throw new Error('Meeting not found');
  }

  if (!meeting.attendee_bot_id) {
    throw new Error('No bot ID associated with meeting');
  }

  // Get the bot record to get the actual Attendee API bot ID
  const { data: bot, error: botError } = await supabase
    .from('bots')
    .select('provider_bot_id')
    .eq('id', meeting.attendee_bot_id)
    .single();

  if (botError || !bot) {
    throw new Error('Bot record not found');
  }

  if (!bot.provider_bot_id) {
    throw new Error('No provider bot ID found in bot record');
  }

  // Update last_polled_at
  await supabase
    .from('meetings')
    .update({ last_polled_at: new Date().toISOString() })
    .eq('id', meetingId);

  // Check bot status via Attendee API using the provider_bot_id
  const botStatusResponse = await fetch(`https://app.attendee.dev/api/v1/bots/${bot.provider_bot_id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  if (!botStatusResponse.ok) {
    throw new Error(`Failed to get bot status: ${botStatusResponse.status}`);
  }

  const botData = await botStatusResponse.json();
  const newBotStatus = mapAttendeeStatusToBotStatus(botData.status);

  // Update bot status if it changed
  if (newBotStatus !== meeting.bot_status) {
    await supabase
      .from('meetings')
      .update({ 
        bot_status: newBotStatus,
        updated_at: new Date().toISOString()
      })
      .eq('id', meetingId);
  }

  // If bot is transcribing, capture real-time transcript
  if (newBotStatus === 'transcribing' && botData.transcript) {
    const realTimeTranscript = {
      timestamp: new Date().toISOString(),
      text: botData.transcript,
      is_final: false
    };

    await supabase
      .from('meetings')
      .update({
        real_time_transcript: realTimeTranscript,
        updated_at: new Date().toISOString()
      })
      .eq('id', meetingId);
  }

  // If meeting is completed, retrieve transcript
  if (newBotStatus === 'completed' && meeting.bot_status !== 'completed') {
    try {
      const transcriptResult = await retrieveTranscript(bot.provider_bot_id);
      
      await supabase
        .from('meetings')
        .update({
          transcript: transcriptResult.transcript,
          transcript_url: transcriptResult.transcript_url,
          transcript_metadata: transcriptResult.metadata,
          transcript_summary: transcriptResult.summary,
          transcript_duration_seconds: transcriptResult.duration_seconds,
          transcript_retrieved_at: new Date().toISOString(),
          final_transcript_ready: true, // Mark as final transcript ready
          updated_at: new Date().toISOString()
        })
        .eq('id', meetingId);

      return {
        status: 'completed',
        transcript_retrieved: true,
        transcript_summary: transcriptResult.summary
      };
    } catch (error) {
      console.error('Failed to retrieve transcript:', error);
      return {
        status: 'completed',
        transcript_retrieved: false,
        error: error.message
      };
    }
  }

  return {
    status: newBotStatus,
    transcript_retrieved: false
  };
}

async function retrieveTranscript(botId: string) {
  // Get transcript from Attendee API
  const transcriptResponse = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/transcript`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  if (!transcriptResponse.ok) {
    throw new Error(`Failed to get transcript: ${transcriptResponse.status}`);
  }

  const transcriptData = await transcriptResponse.json();
  
  // Extract transcript text
  const transcript = transcriptData.transcript || transcriptData.text || '';
  
  // Generate a simple summary (first 200 characters)
  const summary = transcript.length > 200 ? transcript.substring(0, 200) + '...' : transcript;
  
  // Calculate duration if available
  const duration_seconds = transcriptData.duration || transcriptData.duration_seconds || null;

  return {
    transcript,
    transcript_url: `https://app.attendee.dev/bots/${botId}/transcript`,
    metadata: {
      bot_id: botId,
      retrieved_at: new Date().toISOString(),
      word_count: transcript.split(' ').length,
      character_count: transcript.length
    },
    summary,
    duration_seconds
  };
}

function mapAttendeeStatusToBotStatus(attendeeStatus: string): string {
  switch (attendeeStatus?.toLowerCase()) {
    case 'scheduled':
    case 'pending':
      return 'bot_scheduled';
    case 'joined':
    case 'active':
      return 'bot_joined';
    case 'transcribing':
    case 'recording':
      return 'transcribing';
    case 'completed':
    case 'finished':
      return 'completed';
    case 'failed':
    case 'error':
      return 'failed';
    default:
      return 'pending';
  }
} 