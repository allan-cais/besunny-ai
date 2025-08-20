import { supabase } from './supabase';

export interface ApiKeyStatus {
  connected: boolean;
  service: string;
  last_updated?: string;
}

export const apiKeyService = {
  // Send a bot to a meeting via Edge Function (uses master API key)
  async sendBotToMeeting(meetingUrl: string, options: { bot_chat_message?: { message: string; to?: string } } = {}): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Validate required fields
    if (!meetingUrl) {
      throw new Error('Meeting URL is required');
    }
    
    // Ensure bot_chat_message is properly formatted
    const payload = {
      meeting_url: meetingUrl,
      ...options
    };
    
    // Validate bot_chat_message structure
    if (payload.bot_chat_message && typeof payload.bot_chat_message === 'object') {
      if (!payload.bot_chat_message.message) {
        throw new Error('bot_chat_message.message is required');
      }
      if (!payload.bot_chat_message.to) {
        payload.bot_chat_message.to = 'everyone';
      }
    } else {
      // Set default bot_chat_message if not provided
      payload.bot_chat_message = {
        to: 'everyone',
        message: 'Hi, I\'m here to transcribe this meeting!'
      };
    }
    

    
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/send-bot`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload)
    });
    const result = await response.json();

    
    if (!result.ok) {
      // Attendee proxy error
      // Full error response data
      
      // Try to extract more detailed error information
      if (result.data && result.data.non_field_errors) {
        throw new Error(`Attendee API validation error: ${result.data.non_field_errors.join(', ')}`);
      } else if (result.data && result.data.error) {
        throw new Error(`Attendee API error: ${result.data.error}`);
      } else if (result.data && typeof result.data === 'object') {
    
        // Error data keys
        throw new Error(`Attendee API error: ${JSON.stringify(result.data)}`);
      } else if (result.error) {
        throw new Error(result.error);
      } else {
        throw new Error('Failed to send bot');
      }
    }
    
    // The result.data should contain the Attendee API response
    if (!result.data) {
      // No data in response
      throw new Error('No data received from Attendee API');
    }
    

    return result.data;
  },

  // Get bot details
  async getBotDetails(botId: string): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/bot-status/${botId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to get bot details');
    }
    
    return result;
  },

  // Update a scheduled bot (e.g., change join time)
  async updateScheduledBot(botId: string, updates: Record<string, unknown>): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Bot updates are now handled through the attendee service
    // This functionality may need to be implemented in the Python backend
    console.warn('Bot updates are not yet implemented in the Python backend. Please use the attendee service directly.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Bot updates are not yet implemented in the Python backend. Please use the attendee service directly.'
    };
  },

  // Delete a scheduled bot
  async deleteScheduledBot(botId: string): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Bot deletion is now handled through the attendee service
    // This functionality may need to be implemented in the Python backend
    console.warn('Bot deletion is not yet implemented in the Python backend. Please use the attendee service directly.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Bot deletion is not yet implemented in the Python backend. Please use the attendee service directly.'
    };
  },

  // Get meeting transcript
  async getMeetingTranscript(botId: string, updatedAfter?: string): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/transcript/${botId}`;
    if (updatedAfter) {
      url += `?updated_after=${encodeURIComponent(updatedAfter)}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to get transcript');
    }
    
    return result;
  },

  // Get chat messages
  async getChatMessages(botId: string, cursor?: string, updatedAfter?: string): Promise<Record<string, unknown>> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/chat-messages/${botId}`;
    const params = new URLSearchParams();
    if (cursor) {
      params.append('cursor', cursor);
    }
    if (updatedAfter) {
      params.append('updated_after', updatedAfter);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to get chat messages');
    }
    
    return result;
  },

  // Send a chat message
  async sendChatMessage(botId: string, message: string, to: string = 'everyone', toUserUuid?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/send-chat`, {
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
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to send chat message');
    }
    
    return result;
  },

  // Output speech
  async outputSpeech(botId: string, text: string, voiceSettings: any): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Speech output is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Speech output is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Speech output is not yet implemented in the Python backend.'
    };
  },

  // Output audio
  async outputAudio(botId: string, audioData: string, type: string = 'audio/mp3'): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Audio output is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Audio output is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Audio output is not yet implemented in the Python backend.'
    };
  },

  // Output image
  async outputImage(botId: string, imageData: string, type: string = 'image/png'): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Image output is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Image output is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Image output is not yet implemented in the Python backend.'
    };
  },

  // Output video
  async outputVideo(botId: string, videoUrl: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Note: Video output is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Video output is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Video output is not yet implemented in the Python backend.'
    };
  },

  // Get participant events
  async getParticipantEvents(botId: string, after?: string, before?: string, cursor?: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    let url = `${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/participant-events/${botId}`;
    const params = new URLSearchParams();
    if (after) {
      params.append('after', after);
    }
    if (before) {
      params.append('before', before);
    }
    if (cursor) {
      params.append('cursor', cursor);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to get participant events');
    }
    
    return result;
  },

  // Pause recording
  async pauseRecording(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/pause-recording/${botId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to pause recording');
    }
    
    return result;
  },

  // Resume recording
  async resumeRecording(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/resume-recording/${botId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      }
    });
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || 'Failed to resume recording');
    }
    
    return result;
  },

  // Get recording URL
  async getRecordingUrl(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    // Note: Recording URL retrieval is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Recording URL retrieval is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Recording URL retrieval is not yet implemented in the Python backend.'
    };
  },

  // Leave meeting
  async leaveMeeting(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    // Note: Leave meeting functionality is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Leave meeting functionality is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Leave meeting functionality is not yet implemented in the Python backend.'
    };
  },

  // Delete bot data
  async deleteBotData(botId: string): Promise<any> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    // Note: Bot data deletion is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('Bot data deletion is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return {
      success: false,
      message: 'Bot data deletion is not yet implemented in the Python backend.'
    };
  },

  // Test API key (existing function)
  async testApiKey(service: string, apiKey: string): Promise<boolean> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    // Note: API key testing is not yet implemented in the Python backend
    // This functionality may need to be implemented or integrated with external services
    console.warn('API key testing is not yet implemented in the Python backend.');
    
    // For now, return a placeholder response
    return false;
  }
}; 