import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const MASTER_ATTENDEE_API_KEY = Deno.env.get('MASTER_ATTENDEE_API_KEY')!;
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

function withCORS(resp: Response) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
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

// Simplified status mapping
const STATUS_MAP = {
  'pending': 'bot_scheduled',
  'scheduled': 'bot_scheduled', 
  'joined': 'bot_joined',
  'transcribing': 'transcribing',
  'completed': 'completed',
  'failed': 'failed'
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return withCORS(new Response('ok', { status: 200 }));
  }

  const url = new URL(req.url);
  const method = req.method;
  const userId = getUserIdFromAuth(req);

  // Public endpoints (no auth required)
  if (url.pathname.endsWith('/poll-all') && method === 'POST') {
    try {
      const result = await pollAllMeetings();
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Protected endpoints
  if (!userId) {
    return withCORS(new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 }));
  }

  // Send bot to meeting
  if (url.pathname.endsWith('/send-bot') && method === 'POST') {
    try {
      const body = await req.json();
      const result = await sendBotToMeeting(body, userId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Get bot status
  if (url.pathname.endsWith('/bot-status') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) throw new Error('Missing bot_id');
      const result = await getBotStatus(botId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Get transcript
  if (url.pathname.endsWith('/transcript') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) throw new Error('Missing bot_id');
      const result = await getTranscript(botId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Auto-schedule bots
  if (url.pathname.endsWith('/auto-schedule') && method === 'POST') {
    try {
      const result = await autoScheduleBots(userId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Get chat messages
  if (url.pathname.endsWith('/chat-messages') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) throw new Error('Missing bot_id');
      const result = await getChatMessages(botId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Send chat message
  if (url.pathname.endsWith('/send-chat') && method === 'POST') {
    try {
      const body = await req.json();
      const result = await sendChatMessage(body.bot_id, body.message, body.to);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Get participant events
  if (url.pathname.endsWith('/participant-events') && method === 'GET') {
    try {
      const botId = url.searchParams.get('bot_id');
      if (!botId) throw new Error('Missing bot_id');
      const result = await getParticipantEvents(botId);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Pause recording
  if (url.pathname.endsWith('/pause-recording') && method === 'POST') {
    try {
      const body = await req.json();
      const result = await pauseRecording(body.bot_id);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  // Resume recording
  if (url.pathname.endsWith('/resume-recording') && method === 'POST') {
    try {
      const body = await req.json();
      const result = await resumeRecording(body.bot_id);
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

  return withCORS(new Response(JSON.stringify({ error: 'Not found' }), { status: 404 }));
});

// Core functions
async function pollAllMeetings() {
      // Starting to poll all meetings
  
  const { data: meetings, error } = await supabase
    .rpc('get_meetings_for_polling');
  
  if (error) throw error;

      // Found meetings to poll

  const results = [];
  for (const meeting of meetings || []) {
    try {
      const result = await pollMeeting(meeting.id);
      results.push({ meetingId: meeting.id, ...result });
    } catch (error) {
              // Error polling meeting
      results.push({ meetingId: meeting.id, error: error.message });
    }
  }

  return results;
}

async function pollMeeting(meetingId: string) {
  const { data: meeting, error } = await supabase
    .from('meetings')
    .select('*, bots(provider_bot_id)')
    .eq('id', meetingId)
    .single();

  if (error || !meeting) throw new Error('Meeting not found');
  if (!meeting.bots?.provider_bot_id) throw new Error('No provider bot ID');

  // Get bot status from Attendee API
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${meeting.bots.provider_bot_id}`, {
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const botData = await response.json();
  const newStatus = STATUS_MAP[botData.state] || 'failed';

  // Update status if changed
  if (newStatus !== meeting.bot_status) {
    await supabase
      .from('meetings')
      .update({ 
        bot_status: newStatus,
        updated_at: new Date().toISOString()
      })
      .eq('id', meetingId);
  }

  // Handle transcript retrieval
  if (newStatus === 'completed' && meeting.bot_status !== 'completed') {
    try {
      const transcript = await getTranscript(meeting.bots.provider_bot_id);
      await supabase
        .from('meetings')
        .update({
          transcript: transcript.text,
          transcript_metadata: transcript.metadata,
          transcript_participants: transcript.participants,
          transcript_speakers: transcript.speakers,
          transcript_segments: transcript.segments,
          transcript_audio_url: transcript.audio_url,
          transcript_recording_url: transcript.recording_url,
          transcript_retrieved_at: new Date().toISOString()
        })
        .eq('id', meetingId);
      
      return { status: newStatus, transcriptRetrieved: true };
    } catch (error) {
      // Failed to retrieve transcript
      return { status: newStatus, transcriptRetrieved: false };
    }
  }

  return { status: newStatus };
}

async function sendBotToMeeting(options: any, userId: string) {
  const { meeting_url, bot_name = 'AI Assistant', bot_chat_message = 'Hi, I\'m here to transcribe this meeting!' } = options;

  const payload = {
    meeting_url,
    bot_name,
    bot_chat_message: {
      to: 'everyone',
      message: bot_chat_message
    },
    join_at: new Date(Date.now() + 2 * 60 * 1000).toISOString() // Join in 2 minutes
  };

  const response = await fetch('https://app.attendee.dev/api/v1/bots', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const botData = await response.json();
  
  // Create bot record
  const { data: bot, error: botError } = await supabase
    .from('bots')
    .insert({
      user_id: userId,
      name: bot_name,
      provider: 'attendee',
      provider_bot_id: botData.id,
      is_active: true
    })
    .select()
    .single();

  if (botError) throw botError;

  return { botId: bot.id, attendeeBotId: botData.id };
}

async function getBotStatus(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}`, {
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return { status: STATUS_MAP[data.state], data };
}

async function getTranscript(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/transcript`, {
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  
  // Extract participants and speakers from transcript data
  const participants = new Set<string>();
  const speakers = new Set<string>();
  const segments: any[] = [];
  
  if (data.segments) {
    data.segments.forEach((segment: any) => {
      if (segment.speaker) {
        participants.add(segment.speaker);
        speakers.add(segment.speaker);
      }
      segments.push({
        start: segment.start,
        end: segment.end,
        speaker: segment.speaker,
        text: segment.text
      });
    });
  }
  
  return {
    text: data.transcript || '',
    metadata: {
      word_count: (data.transcript || '').split(' ').length,
      character_count: (data.transcript || '').length,
      retrieved_at: new Date().toISOString()
    },
    participants: Array.from(participants),
    speakers: Array.from(speakers),
    segments: segments,
    audio_url: data.audio_url || null,
    recording_url: data.recording_url || null
  };
}

async function autoScheduleBots(userId: string) {
  const { data: meetings, error } = await supabase
    .from('meetings')
    .select('*')
    .eq('user_id', userId)
    .eq('bot_status', 'pending')
    .not('meeting_url', 'is', null)
    .gte('start_time', new Date().toISOString());

  if (error) throw error;

  const results = [];
  for (const meeting of meetings || []) {
    try {
      const result = await sendBotToMeeting({
        meeting_url: meeting.meeting_url,
        bot_name: meeting.bot_name || 'AI Assistant',
        bot_chat_message: meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!'
      }, userId);

      await supabase
        .from('meetings')
        .update({
          attendee_bot_id: result.botId,
          bot_status: 'bot_scheduled',
          updated_at: new Date().toISOString()
        })
        .eq('id', meeting.id);

      results.push({ meetingId: meeting.id, success: true });
    } catch (error) {
      results.push({ meetingId: meeting.id, success: false, error: error.message });
    }
  }

  return results;
} 

async function getChatMessages(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/chat-messages`, {
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return data;
}

async function sendChatMessage(botId: string, message: string, to: string = 'everyone') {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/chat-messages`, {
    method: 'POST',
    headers: { 
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message, to })
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return data;
}

async function getParticipantEvents(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/participant-events`, {
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return data;
}

async function pauseRecording(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/pause-recording`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return data;
}

async function resumeRecording(botId: string) {
  const response = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/resume-recording`, {
    method: 'POST',
    headers: { 'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}` }
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);

  const data = await response.json();
  return data;
} 