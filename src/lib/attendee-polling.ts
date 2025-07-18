import { supabase } from './supabase';

export interface PollingResult {
  meetingId: string;
  status: string;
  transcript_retrieved: boolean;
  transcript_summary?: string;
  error?: string;
}

export interface MeetingForPolling {
  id: string;
  user_id: string;
  attendee_bot_id: string;
  bot_status: string;
  title: string;
  meeting_url: string;
  next_poll_at: string;
}

export const attendeePollingService = {
  // Get meetings that need polling
  async getMeetingsForPolling(): Promise<MeetingForPolling[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-polling-service/get-pending`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    if (!result.meetings) throw new Error('Failed to get meetings for polling');
    
    return result.meetings;
  },

  // Poll all meetings that need polling
  async pollAllMeetings(): Promise<PollingResult[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-polling-service/poll-now`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
    });
    
    const result = await response.json();
    if (!result.success) throw new Error(result.error || 'Failed to poll meetings');
    
    return result.result;
  },

  // Poll a specific meeting
  async pollMeeting(meetingId: string): Promise<PollingResult> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-polling-service/poll-meeting`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ meetingId }),
    });
    
    const result = await response.json();
    if (!result.success) throw new Error(result.error || 'Failed to poll meeting');
    
    return { meetingId, ...result.result };
  },

  // Start automatic polling for a user
  async startAutomaticPolling(): Promise<void> {
    // This would typically be called when a user has active meetings
    // For now, we'll just poll once
    await this.pollAllMeetings();
  },

  // Get meetings with transcripts for the data feed
  async getMeetingsWithTranscripts(): Promise<any[]> {
    const { data, error } = await supabase
      .from('meetings')
      .select(`
        id,
        title,
        description,
        meeting_url,
        start_time,
        end_time,
        transcript,
        transcript_summary,
        transcript_metadata,
        transcript_duration_seconds,
        transcript_retrieved_at,
        bot_status,
        project_id,
        created_at
      `)
      .not('transcript', 'is', null)
      .order('transcript_retrieved_at', { ascending: false });

    if (error) throw error;
    return data || [];
  }
}; 