import { supabase } from './supabase';

export interface AttendeeService {
  // Send bot to meeting
  sendBotToMeeting(options: {
    meeting_url: string;
    bot_name?: string;
    bot_chat_message?: string;
    start_time?: string;
  }): Promise<{ botId: string; attendeeBotId: string }>;

  // Get bot status
  getBotStatus(botId: string): Promise<{ status: string; data: any }>;

  // Get transcript
  getTranscript(botId: string): Promise<{ text: string; metadata: any }>;

  // Get chat messages
  getChatMessages(botId: string): Promise<any>;

  // Send chat message
  sendChatMessage(botId: string, message: string, to?: string): Promise<any>;

  // Get participant events
  getParticipantEvents(botId: string): Promise<any>;

  // Pause recording
  pauseRecording(botId: string): Promise<any>;

  // Resume recording
  resumeRecording(botId: string): Promise<any>;

  // Auto-schedule bots for user
  autoScheduleBots(): Promise<Array<{ meetingId: string; success: boolean; error?: string }>>;

  // Poll all meetings (for cron jobs)
  pollAllMeetings(): Promise<Array<{ meetingId: string; status?: string; error?: string }>>;
}

class AttendeeServiceImpl implements AttendeeService {
  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');

    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const result = await response.json();
    if (!result.success) throw new Error(result.error || 'Request failed');
    
    return result.result;
  }

  async sendBotToMeeting(options: {
    meeting_url: string;
    bot_name?: string;
    bot_chat_message?: string;
    start_time?: string;
  }) {
    console.log('=== ATTENDEE SERVICE SEND BOT DEBUG ===');
    console.log('Options received:', options);
    console.log('start_time value:', options.start_time);
    console.log('start_time type:', typeof options.start_time);
    
    return this.makeRequest('/send-bot', {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  async getBotStatus(botId: string) {
    return this.makeRequest(`/bot-status?bot_id=${botId}`);
  }

  async getTranscript(botId: string) {
    return this.makeRequest(`/transcript?bot_id=${botId}`);
  }

  async getChatMessages(botId: string) {
    return this.makeRequest(`/chat-messages?bot_id=${botId}`);
  }

  async sendChatMessage(botId: string, message: string, to?: string) {
    return this.makeRequest(`/send-chat-message?bot_id=${botId}`, {
      method: 'POST',
      body: JSON.stringify({ message, to }),
    });
  }

  async getParticipantEvents(botId: string) {
    return this.makeRequest(`/participant-events?bot_id=${botId}`);
  }

  async pauseRecording(botId: string) {
    return this.makeRequest(`/pause-recording?bot_id=${botId}`, { method: 'POST' });
  }

  async resumeRecording(botId: string) {
    return this.makeRequest(`/resume-recording?bot_id=${botId}`, { method: 'POST' });
  }

  async autoScheduleBots() {
    return this.makeRequest('/auto-schedule', { method: 'POST' });
  }

  async pollAllMeetings() {
    // This endpoint doesn't require auth (for cron jobs)
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/poll-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    const result = await response.json();
    if (!result.success) throw new Error(result.message || 'Polling failed');
    
    return result.result;
  }
}

export const attendeeService = new AttendeeServiceImpl(); 