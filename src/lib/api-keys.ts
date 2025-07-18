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

  // Get bot details
  async getBotDetails(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/bot-details?bot_id=${botId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to get bot details');
    }
    
    return result.data;
  },

  // Update a scheduled bot (e.g., change join time)
  async updateScheduledBot(botId: string, updates: any): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/update-bot`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        updates
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to update bot');
    }
    
    return result.data;
  },

  // Delete a scheduled bot
  async deleteScheduledBot(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/delete-bot`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to delete bot');
    }
    
    return result.data;
  },

  // Get meeting transcript
  async getMeetingTranscript(botId: string, updatedAfter?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/transcript?bot_id=${botId}`;
    if (updatedAfter) {
      url += `&updated_after=${encodeURIComponent(updatedAfter)}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to get transcript');
    }
    
    return result.data;
  },

  // Get chat messages
  async getChatMessages(botId: string, cursor?: string, updatedAfter?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/chat-messages?bot_id=${botId}`;
    if (cursor) url += `&cursor=${encodeURIComponent(cursor)}`;
    if (updatedAfter) url += `&updated_after=${encodeURIComponent(updatedAfter)}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to get chat messages');
    }
    
    return result.data;
  },

  // Send a chat message
  async sendChatMessage(botId: string, message: string, to: string = 'everyone', toUserUuid?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/send-chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        message,
        to,
        ...(toUserUuid && { to_user_uuid: toUserUuid })
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to send chat message');
    }
    
    return result.data;
  },

  // Output speech
  async outputSpeech(botId: string, text: string, voiceSettings: any): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        text,
        text_to_speech_settings: voiceSettings
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to output speech');
    }
    
    return result.data;
  },

  // Output audio
  async outputAudio(botId: string, audioData: string, type: string = 'audio/mp3'): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/output-audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        type,
        data: audioData
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to output audio');
    }
    
    return result.data;
  },

  // Output image
  async outputImage(botId: string, imageData: string, type: string = 'image/png'): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/output-image`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        type,
        data: imageData
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to output image');
    }
    
    return result.data;
  },

  // Output video
  async outputVideo(botId: string, videoUrl: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/output-video`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId,
        url: videoUrl
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to output video');
    }
    
    return result.data;
  },

  // Get participant events
  async getParticipantEvents(botId: string, after?: string, before?: string, cursor?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/participant-events?bot_id=${botId}`;
    if (after) url += `&after=${encodeURIComponent(after)}`;
    if (before) url += `&before=${encodeURIComponent(before)}`;
    if (cursor) url += `&cursor=${encodeURIComponent(cursor)}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to get participant events');
    }
    
    return result.data;
  },

  // Pause recording
  async pauseRecording(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/pause-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to pause recording');
    }
    
    return result.data;
  },

  // Resume recording
  async resumeRecording(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/resume-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to resume recording');
    }
    
    return result.data;
  },

  // Get recording URL
  async getRecordingUrl(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/recording?bot_id=${botId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to get recording URL');
    }
    
    return result.data;
  },

  // Leave meeting
  async leaveMeeting(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/leave-meeting`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to leave meeting');
    }
    
    return result.data;
  },

  // Delete bot data
  async deleteBotData(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/delete-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        bot_id: botId
      })
    });
    const result = await response.json();
    
    if (!result.ok) {
      throw new Error(result.error || 'Failed to delete bot data');
    }
    
    return result.data;
  },

  // Test API key (existing function)
  async testApiKey(service: string, apiKey: string): Promise<boolean> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-proxy/test-key`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({ apiKey })
    });
    const result = await response.json();
    return result.ok;
  }
}; 