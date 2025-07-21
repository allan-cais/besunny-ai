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

  // Main endpoint - poll all meetings
  if (url.pathname.endsWith('/attendee-polling-service') && method === 'POST') {
    try {
      const result = await pollAllMeetings();
      return withCORS(new Response(JSON.stringify({ success: true, result }), { status: 200 }));
    } catch (error) {
      return withCORS(new Response(JSON.stringify({ error: error.message }), { status: 500 }));
    }
  }

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
  console.log(`🚀 Starting to poll all meetings`);
  
  const { data: meetings, error } = await supabase.rpc('get_meetings_for_polling');
  if (error) {
    console.error(`❌ Error getting meetings for polling:`, error);
    throw error;
  }

  console.log(`📋 Found ${meetings?.length || 0} meetings to poll:`, meetings?.map(m => ({ id: m.id, title: m.title, status: m.bot_status })));

  const results = [];
  for (const meeting of meetings || []) {
    try {
      console.log(`🔄 Polling meeting: ${meeting.id} (${meeting.title})`);
      const result = await pollMeeting(meeting.id);
      results.push({ meetingId: meeting.id, ...result });
      console.log(`✅ Successfully polled meeting: ${meeting.id}`);
    } catch (error) {
      console.error(`❌ Error polling meeting ${meeting.id}:`, error);
      results.push({ meetingId: meeting.id, error: error.message });
    }
  }

  console.log(`🏁 Completed polling all meetings. Results:`, results);
  return results;
}

async function pollMeeting(meetingId: string) {
  console.log(`🔍 Starting to poll meeting: ${meetingId}`);
  
  // Get meeting details
  const { data: meeting, error: meetingError } = await supabase
    .from('meetings')
    .select('*')
    .eq('id', meetingId)
    .single();

  if (meetingError || !meeting) {
    console.error(`❌ Meeting not found: ${meetingId}`, meetingError);
    throw new Error('Meeting not found');
  }

  console.log(`📋 Meeting details:`, {
    id: meeting.id,
    title: meeting.title,
    current_bot_status: meeting.bot_status,
    attendee_bot_id: meeting.attendee_bot_id,
    polling_enabled: meeting.polling_enabled
  });

  if (!meeting.attendee_bot_id) {
    console.error(`❌ No bot ID associated with meeting: ${meetingId}`);
    throw new Error('No bot ID associated with meeting');
  }

  // Get the bot record to get the actual Attendee API bot ID
  const { data: bot, error: botError } = await supabase
    .from('bots')
    .select('provider_bot_id')
    .eq('id', meeting.attendee_bot_id)
    .single();

  if (botError || !bot) {
    console.error(`❌ Bot record not found for bot ID: ${meeting.attendee_bot_id}`, botError);
    throw new Error('Bot record not found');
  }

  if (!bot.provider_bot_id) {
    console.error(`❌ No provider bot ID found in bot record: ${meeting.attendee_bot_id}`);
    throw new Error('No provider bot ID found in bot record');
  }

  console.log(`🤖 Bot details:`, {
    bot_id: meeting.attendee_bot_id,
    provider_bot_id: bot.provider_bot_id
  });

  // Update last_polled_at and set next poll time
  await supabase
    .from('meetings')
    .update({ 
      last_polled_at: new Date().toISOString(),
      next_poll_at: new Date(Date.now() + 2 * 60 * 1000).toISOString() // Poll again in 2 minutes
    })
    .eq('id', meetingId);

  console.log(`⏰ Updated polling timestamps for meeting: ${meetingId}`);

  // Check bot status via Attendee API using the provider_bot_id
  console.log(`🌐 Making API call to Attendee API for bot: ${bot.provider_bot_id}`);
  
  const botStatusResponse = await fetch(`https://app.attendee.dev/api/v1/bots/${bot.provider_bot_id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  console.log(`📡 API Response status: ${botStatusResponse.status} ${botStatusResponse.statusText}`);

  if (!botStatusResponse.ok) {
    const errorText = await botStatusResponse.text();
    console.error(`❌ Failed to get bot status:`, {
      status: botStatusResponse.status,
      statusText: botStatusResponse.statusText,
      error: errorText
    });
    throw new Error(`Failed to get bot status: ${botStatusResponse.status} - ${errorText}`);
  }

  const botData = await botStatusResponse.json();
  console.log(`📊 Raw API response data:`, JSON.stringify(botData, null, 2));

  // Use 'state' field instead of 'status' field from the API response
  const attendeeStatus = botData.state || botData.status;
  const newBotStatus = mapAttendeeStatusToBotStatus(attendeeStatus);
  console.log(`🔄 Status mapping:`, {
    attendee_status: attendeeStatus,
    mapped_status: newBotStatus,
    previous_status: meeting.bot_status
  });

  // Update bot status if it changed
  if (newBotStatus !== meeting.bot_status) {
    console.log(`🔄 Updating bot status from "${meeting.bot_status}" to "${newBotStatus}"`);
    
    const { data: updateData, error: updateError } = await supabase
      .from('meetings')
      .update({ 
        bot_status: newBotStatus,
        updated_at: new Date().toISOString()
      })
      .eq('id', meetingId)
      .select('id, bot_status, updated_at'); // Select to verify the update
    
    if (updateError) {
      console.error(`❌ Failed to update bot status:`, updateError);
      throw new Error(`Database update failed: ${updateError.message}`);
    }
    
    console.log(`✅ Bot status update result:`, updateData);
    
    // Verify the update by fetching the meeting again
    const { data: verifyData, error: verifyError } = await supabase
      .from('meetings')
      .select('id, bot_status, updated_at')
      .eq('id', meetingId)
      .single();
    
    if (verifyError) {
      console.error(`❌ Failed to verify update:`, verifyError);
    } else {
      console.log(`🔍 Verification - Current bot status in DB:`, verifyData);
    }
    
    console.log(`✅ Bot status updated successfully`);
  } else {
    console.log(`ℹ️ Bot status unchanged: ${newBotStatus}`);
  }

  // If bot is transcribing, capture real-time transcript
  if (newBotStatus === 'transcribing' && botData.transcript) {
    console.log(`📝 Capturing real-time transcript`);
    
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
    
    console.log(`✅ Real-time transcript captured`);
  }

  // If meeting is completed, retrieve transcript
  if (newBotStatus === 'completed' && meeting.bot_status !== 'completed') {
    console.log(`🎯 Meeting completed! Retrieving final transcript`);
    
    try {
      const transcriptResult = await retrieveTranscript(bot.provider_bot_id);
      console.log(`📄 Transcript retrieved:`, {
        word_count: transcriptResult.metadata.word_count,
        character_count: transcriptResult.metadata.character_count,
        duration_seconds: transcriptResult.duration_seconds
      });
      
      await supabase
        .from('meetings')
        .update({
          transcript: transcriptResult.transcript,
          transcript_url: transcriptResult.transcript_url,
          transcript_metadata: transcriptResult.metadata, // Store metadata with participants info
          real_time_transcript: transcriptResult.transcript_data, // Store full raw transcript data
          transcript_summary: transcriptResult.summary,
          transcript_duration_seconds: transcriptResult.duration_seconds,
          transcript_retrieved_at: new Date().toISOString(),
          final_transcript_ready: true, // Mark as final transcript ready
          updated_at: new Date().toISOString()
        })
        .eq('id', meetingId);

      console.log(`✅ Final transcript saved to database`);

      // Verify the transcript update
      const { data: transcriptVerifyData, error: transcriptVerifyError } = await supabase
        .from('meetings')
        .select('id, bot_status, transcript_retrieved_at, final_transcript_ready')
        .eq('id', meetingId)
        .single();
      
      if (transcriptVerifyError) {
        console.error(`❌ Failed to verify transcript update:`, transcriptVerifyError);
      } else {
        console.log(`🔍 Transcript verification - Current state in DB:`, transcriptVerifyData);
      }

      return {
        status: 'completed',
        transcript_retrieved: true,
        transcript_summary: transcriptResult.summary
      };
    } catch (error) {
      console.error('❌ Failed to retrieve transcript:', error);
      return {
        status: 'completed',
        transcript_retrieved: false,
        error: error.message
      };
    }
  }

  console.log(`✅ Polling completed for meeting: ${meetingId}`);
  return {
    status: newBotStatus,
    transcript_retrieved: false
  };
}

async function retrieveTranscript(botId: string) {
  console.log(`📄 Retrieving transcript for bot: ${botId}`);
  
  // Get transcript from Attendee API
  const transcriptResponse = await fetch(`https://app.attendee.dev/api/v1/bots/${botId}/transcript`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${MASTER_ATTENDEE_API_KEY}`,
      'Content-Type': 'application/json',
    },
  });

  console.log(`📡 Transcript API Response status: ${transcriptResponse.status} ${transcriptResponse.statusText}`);

  if (!transcriptResponse.ok) {
    const errorText = await transcriptResponse.text();
    console.error(`❌ Failed to get transcript:`, {
      status: transcriptResponse.status,
      statusText: transcriptResponse.statusText,
      error: errorText
    });
    throw new Error(`Failed to get transcript: ${transcriptResponse.status} - ${errorText}`);
  }

  const transcriptData = await transcriptResponse.json();
  console.log(`📊 Raw transcript API response:`, JSON.stringify(transcriptData, null, 2));
  
  // Handle the transcript data format from Attendee API
  // The API returns an array of transcript entries with speaker information
  let transcript = '';
  let participants = new Set<string>();
  let totalDuration = 0;
  let wordCount = 0;
  let characterCount = 0;
  
  if (Array.isArray(transcriptData)) {
    // Process each transcript entry
    transcriptData.forEach((entry: any) => {
      if (entry.transcription?.transcript) {
        const speakerName = entry.speaker_name || 'Unknown Speaker';
        const timestamp = new Date(entry.timestamp_ms).toISOString();
        const duration = entry.duration_ms || 0;
        
        // Add speaker to participants set
        participants.add(speakerName);
        
        // Add to transcript with speaker and timestamp
        transcript += `[${timestamp}] ${speakerName}: ${entry.transcription.transcript}\n`;
        
        // Update counts
        const words = entry.transcription.transcript.split(' ').length;
        wordCount += words;
        characterCount += entry.transcription.transcript.length;
        totalDuration += duration;
      }
    });
  } else if (transcriptData.transcript) {
    // Fallback for simple transcript format
    transcript = transcriptData.transcript;
    wordCount = transcript.split(' ').length;
    characterCount = transcript.length;
    totalDuration = transcriptData.duration || 0;
  }
  
  // Generate a summary from the first few entries
  let summary = '';
  if (Array.isArray(transcriptData) && transcriptData.length > 0) {
    const firstEntries = transcriptData.slice(0, 3);
    summary = firstEntries
      .map((entry: any) => `${entry.speaker_name || 'Unknown'}: ${entry.transcription?.transcript || ''}`)
      .join(' ');
    if (summary.length > 200) {
      summary = summary.substring(0, 200) + '...';
    }
  } else {
    summary = transcript.length > 200 ? transcript.substring(0, 200) + '...' : transcript;
  }

  const result = {
    transcript,
    transcript_url: `https://app.attendee.dev/bots/${botId}/transcript`,
    transcript_data: transcriptData, // Store the full raw transcript data
    metadata: {
      bot_id: botId,
      retrieved_at: new Date().toISOString(),
      word_count: wordCount,
      character_count: characterCount,
      duration_seconds: Math.round(totalDuration / 1000),
      participants: Array.from(participants),
      entry_count: Array.isArray(transcriptData) ? transcriptData.length : 1
    },
    summary,
    duration_seconds: Math.round(totalDuration / 1000)
  };

  console.log(`✅ Transcript processed:`, {
    word_count: result.metadata.word_count,
    character_count: result.metadata.character_count,
    duration_seconds: result.duration_seconds,
    participants: result.metadata.participants,
    entry_count: result.metadata.entry_count,
    summary_length: result.summary.length
  });

  return result;
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
    case 'ended': // Add support for "ended" state
      return 'completed';
    case 'failed':
    case 'error':
      return 'failed';
    default:
      return 'pending';
  }
} 