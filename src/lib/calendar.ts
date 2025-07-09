import { supabase } from './supabase';

export interface Meeting {
  id: string;
  user_id: string;
  project_id?: string;
  google_calendar_event_id?: string;
  title: string;
  description?: string;
  meeting_url?: string;
  start_time: string;
  end_time: string;
  attendee_bot_id?: string; // Now references bots(id) as UUID
  bot_name?: string;
  bot_chat_message?: string;
  transcript?: string;
  transcript_url?: string;
  status: 'pending' | 'bot_scheduled' | 'bot_joined' | 'transcribing' | 'completed' | 'failed' | 'accepted' | 'declined' | 'tentative' | 'needsAction';
  created_at: string;
  updated_at: string;
}

export interface Bot {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  avatar_url?: string;
  provider: string;
  provider_bot_id?: string;
  settings?: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const calendarService = {
  // Fetch calendar events and sync with meetings table
  async syncCalendarEvents(projectId?: string): Promise<{ meetings: Meeting[]; total_events: number; meetings_with_urls: number }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/events`);
    if (projectId) {
      url.searchParams.set('project_id', projectId);
    }
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    if (!result.ok) throw new Error(result.error || 'Failed to sync calendar events');
    return result;
  },

  // Get meetings for a specific project
  async getProjectMeetings(projectId: string): Promise<Meeting[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/meetings`);
    url.searchParams.set('project_id', projectId);
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    if (!result.ok) throw new Error(result.error || 'Failed to get project meetings');
    return result.meetings || [];
  },

  // Get all upcoming meetings for the user
  async getUpcomingMeetings(): Promise<Meeting[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/meetings`);
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    if (!result.ok) throw new Error(result.error || 'Failed to get upcoming meetings');
    return result.meetings || [];
  },

  // Update meeting status
  async updateMeetingStatus(meetingId: string, status: Meeting['status'], attendeeBotId?: string): Promise<void> {
    const { error } = await supabase
      .from('meetings')
      .update({
        status,
        attendee_bot_id: attendeeBotId,
        updated_at: new Date().toISOString(),
      })
      .eq('id', meetingId);
    
    if (error) throw error;
  },

  // Associate a meeting with a project
  async associateMeetingWithProject(meetingId: string, projectId: string): Promise<void> {
    const { error } = await supabase
      .from('meetings')
      .update({
        project_id: projectId === '' ? null : projectId,
        updated_at: new Date().toISOString(),
      })
      .eq('id', meetingId);
    
    if (error) throw error;
  },

  // Delete a meeting
  async deleteMeeting(meetingId: string): Promise<void> {
    const { error } = await supabase
      .from('meetings')
      .delete()
      .eq('id', meetingId);
    
    if (error) throw error;
  },

  // Create a new bot
  async createBot(botData: Omit<Bot, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Bot> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const { data, error } = await supabase
      .from('bots')
      .insert({
        ...botData,
        user_id: session.user.id,
      })
      .select()
      .single();
    
    if (error) throw error;
    return data;
  },

  // Get user's bots
  async getUserBots(): Promise<Bot[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const { data, error } = await supabase
      .from('bots')
      .select('*')
      .eq('user_id', session.user.id)
      .eq('is_active', true)
      .order('created_at', { ascending: false });
    
    if (error) throw error;
    return data || [];
  },

  // Update bot
  async updateBot(botId: string, updates: Partial<Bot>): Promise<void> {
    const { error } = await supabase
      .from('bots')
      .update({
        ...updates,
        updated_at: new Date().toISOString(),
      })
      .eq('id', botId);
    
    if (error) throw error;
  },

  // Delete bot
  async deleteBot(botId: string): Promise<void> {
    const { error } = await supabase
      .from('bots')
      .delete()
      .eq('id', botId);
    
    if (error) throw error;
  },
}; 