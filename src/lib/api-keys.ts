import { supabase } from './supabase';

export interface ApiKeyStatus {
  connected: boolean;
  service: string;
  last_updated?: string;
}

export const apiKeyService = {
  // Send a bot to a meeting via Edge Function (uses master API key)
  async sendBotToMeeting(meetingUrl: string, options: any = {}): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/send-bot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        meeting_url: meetingUrl,
        bot_name: options.bot_name || 'Sunny AI Assistant',
        ...options
      })
    });
    const result = await response.json();
    console.log('Attendee proxy response:', result);
    
    if (!result.ok) {
      console.error('Attendee proxy error:', result);
      throw new Error(result.error || 'Failed to send bot');
    }
    
    // The result.data should contain the Attendee API response
    if (!result.data) {
      console.error('No data in response:', result);
      throw new Error('No data received from Attendee API');
    }
    
    console.log('Attendee API data:', result.data);
    return result.data;
  },

  // Get meeting transcript via Edge Function (uses master API key)
  async getMeetingTranscript(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/transcript?bot_id=${encodeURIComponent(botId)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    const result = await response.json();
    if (!result.ok) throw new Error(result.error || 'Failed to get transcript');
    return result.data;
  },

  // Test master API key (for admin purposes)
  async testMasterApiKey(): Promise<boolean> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/test-key`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({}) // No API key needed, uses master key
    });
    const result = await response.json();
    return !!result.ok;
  }
}; 