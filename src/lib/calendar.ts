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
  event_status: 'accepted' | 'declined' | 'tentative' | 'needsAction';
  bot_status: 'pending' | 'bot_scheduled' | 'bot_joined' | 'transcribing' | 'completed' | 'failed';
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
  // Initial sync: Today forward only (for bot functionality)
  async initialSync(projectId?: string): Promise<{ 
    meetings: Meeting[]; 
    total_events: number; 
    meetings_with_urls: number;
    new_meetings: number;
    updated_meetings: number;
    deleted_meetings: number;
    sync_range: {
      start_date: string;
      end_date: string;
      days_past: number;
      days_future: number;
    };
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/events`);
    if (projectId) {
      url.searchParams.set('project_id', projectId);
    }
    // Initial sync: 0 days past (today only), 60 days future
    url.searchParams.set('days_past', '0');
    url.searchParams.set('days_future', '60');
    
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

  // Full sync: Historical data + future (for complete database)
  async fullSync(projectId?: string, daysPast: number = 365, daysFuture: number = 60): Promise<{ 
    meetings: Meeting[]; 
    total_events: number; 
    meetings_with_urls: number;
    new_meetings: number;
    updated_meetings: number;
    deleted_meetings: number;
    sync_range: {
      start_date: string;
      end_date: string;
      days_past: number;
      days_future: number;
    };
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/events`);
    if (projectId) {
      url.searchParams.set('project_id', projectId);
    }
    url.searchParams.set('days_past', daysPast.toString());
    url.searchParams.set('days_future', daysFuture.toString());
    
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

  // Setup real-time webhook sync
  async setupWebhookSync(): Promise<{
    ok: boolean;
    webhook_id?: string;
    resource_id?: string;
    expiration?: number;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/setup`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId: session.user.id }),
    });
    
    const result = await response.json();
    return result;
  },

  // Get current week meetings (for UI display)
  async getCurrentWeekMeetings(): Promise<Meeting[]> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay()); // Start of current week (Sunday)
    startOfWeek.setHours(0, 0, 0, 0);
    
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 7); // End of current week
    endOfWeek.setHours(23, 59, 59, 999);
    
    const { data: meetings, error } = await supabase
      .from('meetings')
      .select('*')
      .eq('user_id', session.user.id)
      .gte('start_time', startOfWeek.toISOString())
      .lte('start_time', endOfWeek.toISOString())
      .order('start_time', { ascending: true });
    
    if (error) throw error;
    return meetings || [];
  },

  // Get sync status and logs
  async getSyncStatus(): Promise<{
    webhook_active: boolean;
    last_sync?: string;
    sync_logs: any[];
    webhook_expires_at?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    // Get webhook status
    const { data: webhook, error: webhookError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', session.user.id)
      .eq('is_active', true)
      .maybeSingle();
    
    // Get recent sync logs
    const { data: syncLogs } = await supabase
      .from('calendar_sync_logs')
      .select('*')
      .eq('user_id', session.user.id)
      .order('created_at', { ascending: false })
      .limit(10);
    
    const status = {
      webhook_active: !!webhook,
      last_sync: webhook?.last_sync_at,
      webhook_expires_at: webhook?.expiration_time,
      sync_logs: syncLogs || [],
    };
    return status;
  },

  // Renew webhook subscription
  async renewWebhook(): Promise<{
    ok: boolean;
    webhook_id?: string;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/renew-calendar-webhooks/renew`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId: session.user.id }),
    });
    
    const result = await response.json();
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

  // Update bot status
  async updateBotStatus(meetingId: string, botStatus: Meeting['bot_status'], attendeeBotId?: string): Promise<void> {
    const { error } = await supabase
      .from('meetings')
      .update({
        bot_status: botStatus,
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