import { supabase } from './supabase';

// Utility functions
function extractMeetingUrl(event: any): string | null {
  // Check for Google Meet URL in conferenceData
  if (event.conferenceData?.entryPoints) {
    const meetEntry = event.conferenceData.entryPoints.find(
      (entry: any) => entry.entryPointType === 'video'
    );
    if (meetEntry?.uri) {
      return meetEntry.uri;
    }
  }
  
  // Check for Google Meet URL in description
  if (event.description) {
    const meetRegex = /https:\/\/meet\.google\.com\/[a-z-]+/i;
    const match = event.description.match(meetRegex);
    if (match) {
      return match[0];
    }
  }
  
  // Check for other video conferencing URLs
  const videoUrls = [
    /https:\/\/zoom\.us\/j\/\d+/i,
    /https:\/\/teams\.microsoft\.com\/l\/meetup-join\/[^\\s]+/i,
    /https:\/\/meet\.google\.com\/[a-z-]+/i,
  ];
  
  if (event.description) {
    for (const regex of videoUrls) {
      const match = event.description.match(regex);
      if (match) {
        return match[0];
      }
    }
  }
  
  return null;
}

function stripHtml(html: string): string {
  if (!html) return '';
  const tmp = html.replace(/<[^>]+>/g, ' ');
  return tmp.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, ' ').trim();
}

// Get Google credentials from database
async function getGoogleCredentials(userId: string): Promise<any> {
  const { data, error } = await supabase
    .from('google_credentials')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();
  
  if (error || !data) {
    throw new Error('Google credentials not found');
  }
  
  // Check if token is expired and refresh if needed
  if (new Date(data.expires_at) <= new Date()) {
    if (!data.refresh_token) {
      throw new Error('Token expired and no refresh token available');
    }
    
    
    
    // Refresh the token
    const refreshResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID!,
        client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET!,
        refresh_token: data.refresh_token,
        grant_type: 'refresh_token',
      }),
    });
    
    if (!refreshResponse.ok) {
      const errorText = await refreshResponse.text();
      console.error('Token refresh failed:', refreshResponse.status, errorText);
      throw new Error(`Failed to refresh Google token: ${refreshResponse.status} - ${errorText}`);
    }
    
    const refreshData = await refreshResponse.json();
    
    
    // Update the credentials in the database
    const { error: updateError } = await supabase
      .from('google_credentials')
      .update({
        access_token: refreshData.access_token,
        expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
      })
      .eq('user_id', userId);
    
    if (updateError) {
      console.error('Failed to update token in database:', updateError);
      throw new Error('Failed to update refreshed token');
    }
    
    return {
      ...data,
      access_token: refreshData.access_token,
      expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
    };
  }
  
  
  return data;
}

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
      // Real-time transcription fields
    last_polled_at?: string;
    next_poll_at?: string;
    real_time_transcript?: any;
    final_transcript_ready?: boolean;
  transcript_metadata?: any;
  bot_configuration?: any;
  // Auto-scheduling fields
  bot_deployment_method?: 'manual' | 'automatic' | 'scheduled';
  auto_scheduled_via_email?: boolean;
  virtual_email_attendee?: string;
  auto_bot_notification_sent?: boolean;
  // Enhanced transcript fields
  transcript_summary?: string;
  transcript_duration_seconds?: number;
  transcript_retrieved_at?: string;
  transcript_participants?: string[];
  transcript_speakers?: string[];
  transcript_segments?: any[];
  transcript_audio_url?: string;
  transcript_recording_url?: string;
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
    async getCurrentWeekMeetings(session?: any): Promise<Meeting[]> {
    try {
      // Use provided session or get from auth
      const currentSession = session || (await supabase.auth.getSession()).data.session;
      if (!currentSession) {
        throw new Error('Not authenticated');
      }
      
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
        .eq('user_id', currentSession.user.id)
        .is('project_id', null) // Only unassigned meetings
        .gte('start_time', startOfWeek.toISOString())
        .lte('start_time', endOfWeek.toISOString())
        .order('start_time', { ascending: true });
      
      if (error) {
        throw error;
      }
      
      return meetings || [];
    } catch (error) {
      throw error;
    }
  },

  // Get ALL meetings for the current week (including assigned ones) - for debugging
  async getAllCurrentWeekMeetings(session?: any): Promise<Meeting[]> {
    // Use provided session or get from auth
    const currentSession = session || (await supabase.auth.getSession()).data.session;
    if (!currentSession) throw new Error('Not authenticated');
    
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
      .eq('user_id', currentSession.user.id)
      .gte('start_time', startOfWeek.toISOString())
      .lte('start_time', endOfWeek.toISOString())
      .order('start_time', { ascending: true });
    
    if (error) throw error;
    return meetings || [];
  },

  // Get sync status and logs
  async getSyncStatus(session?: any): Promise<{
    webhook_active: boolean;
    last_sync?: string;
    sync_logs: any[];
    webhook_expires_at?: string;
  }> {
    // Use provided session or get from auth
    const currentSession = session || (await supabase.auth.getSession()).data.session;
    if (!currentSession) throw new Error('Not authenticated');
    
    // Get webhook status
    const { data: webhook, error: webhookError } = await supabase
      .from('calendar_webhooks')
      .select('*')
      .eq('user_id', currentSession.user.id)
      .eq('is_active', true)
      .maybeSingle();
    
    // Get recent sync logs
    const { data: syncLogs } = await supabase
      .from('calendar_sync_logs')
      .select('*')
      .eq('user_id', currentSession.user.id)
      .order('created_at', { ascending: false })
      .limit(10);
    
    // Get the most recent successful sync time from logs
    const lastSuccessfulSync = syncLogs?.find(log => 
      log.status === 'completed' && 
      (log.sync_type === 'webhook' || log.sync_type === 'manual' || log.sync_type === 'initial')
    );
    
    const status = {
      webhook_active: !!webhook,
      last_sync: lastSuccessfulSync?.created_at || webhook?.updated_at,
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
    
    // Filter for upcoming meetings only (current time and future)
    const now = new Date();
    
    const { data: meetings, error } = await supabase
      .from('meetings')
      .select('*')
      .eq('user_id', session.user.id)
      .gte('start_time', now.toISOString()) // Only meetings starting from now onwards
      .order('start_time', { ascending: true });
    
    if (error) {
      console.error('Error fetching upcoming meetings:', error);
      throw error;
    }
    

    
    return meetings || [];
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

  // Update meeting with any fields
  async updateMeeting(meetingId: string, updates: Partial<Meeting>): Promise<void> {
    const { error } = await supabase
      .from('meetings')
      .update({
        ...updates,
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

  // Manually trigger webhook sync to catch up on missed meetings
  async triggerWebhookSync(): Promise<{
    ok: boolean;
    processed?: number;
    created?: number;
    updated?: number;
    errors?: number;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        state: 'sync',
        userId: session.user.id,
        resourceId: 'manual-trigger',
      }),
    });
    
    const result = await response.json();
    return result;
  },

  // Get raw calendar events from Google
  async getRawCalendarEvents(daysPast: number = 7, daysFuture: number = 60): Promise<{
    ok: boolean;
    events?: any[];
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar/raw-events`);
    url.searchParams.set('days_past', daysPast.toString());
    url.searchParams.set('days_future', daysFuture.toString());
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    return result;
  },

  // Simulate a webhook notification (for testing real-time sync)
  async simulateWebhookNotification(): Promise<{
    ok: boolean;
    processed?: number;
    created?: number;
    updated?: number;
    errors?: number;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify`);
    url.searchParams.set('userId', session.user.id);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        // Simulate a real webhook notification (no state: 'sync')
        timestamp: new Date().toISOString(),
      }),
    });
    
    const result = await response.json();
    return result;
  },

  // Test webhook notification specifically
  async testWebhookNotification(): Promise<{
    ok: boolean;
    message?: string;
    timestamp?: string;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        state: 'test',
        userId: session.user.id,
      }),
    });
    
    const result = await response.json();
    return result;
  },

  // Test webhook connectivity and get detailed status
  async testWebhookConnectivity(): Promise<{
    webhook_active: boolean;
    webhook_url?: string;
    last_sync?: string;
    sync_logs: any[];
    recent_errors: any[];
    webhook_expires_at?: string;
    connectivity_test?: boolean;
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
      .limit(20);
    
    // Get recent errors
    const recentErrors = syncLogs?.filter(log => log.status === 'failed') || [];
    
    // Test webhook connectivity by sending a test notification
    let connectivityTest = false;
    try {
      const testResult = await this.simulateWebhookNotification();
      connectivityTest = testResult.ok;
    } catch (error) {
      console.error('Webhook connectivity test failed:', error);
    }
    
    const status = {
      webhook_active: !!webhook,
      webhook_url: webhook ? `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${session.user.id}` : undefined,
      last_sync: syncLogs?.find(log => log.status === 'completed')?.created_at || webhook?.updated_at,
      sync_logs: syncLogs || [],
      recent_errors: recentErrors,
      webhook_expires_at: webhook?.expiration_time,
      connectivity_test: connectivityTest,
    };
    
    return status;
  },

  // Enhanced calendar service with watch functionality
  async initializeCalendarSync(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
  
      
      // Check if we already have an active webhook
      const { data: existingWebhook, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('is_active', true)
        .maybeSingle();
      
      if (webhookError) {
        console.error('Error checking for existing webhook:', webhookError);
      }
      
      
      
      if (existingWebhook) {
        
        
        // Check if we have any meetings in the database
        const { data: existingMeetings, error: meetingsError } = await supabase
          .from('meetings')
          .select('id')
          .eq('user_id', userId)
          .limit(1);
        
        if (meetingsError) {
          console.error('Error checking existing meetings:', meetingsError);
        }
        
        
        
        if (!existingMeetings || existingMeetings.length === 0) {
          
          
          // Step 1: Get initial sync token
          const initialSyncResult = await this.performInitialSync(userId);
          
          if (!initialSyncResult.success) {
            return { success: false, error: `Initial sync failed: ${initialSyncResult.error}` };
          }
          
          // Step 2: Update the existing webhook with the new sync token
          const { error: updateError } = await supabase
            .from('calendar_webhooks')
            .update({
              sync_token: initialSyncResult.sync_token,
              updated_at: new Date().toISOString()
            })
            .eq('id', existingWebhook.id);
          
          if (updateError) {
            console.error('Error updating webhook with sync token:', updateError);
          }
          
          return { success: true, webhook_id: existingWebhook.webhook_id };
        } else {
          return { success: true, webhook_id: existingWebhook.webhook_id };
        }
      }
      
      
      // Step 1: Get initial sync token (only if no webhook exists)
      const initialSyncResult = await this.performInitialSync(userId);
      
      if (!initialSyncResult.success) {
        return { success: false, error: `Initial sync failed: ${initialSyncResult.error}` };
      }
      
      // Step 2: Set up watch with sync token
      const watchResult = await this.setupWatch(userId, initialSyncResult.sync_token);
      
      if (!watchResult.success) {
        return { success: false, error: `Watch setup failed: ${watchResult.error}` };
      }
      
      return { success: true, webhook_id: watchResult.webhook_id };
    } catch (error) {
      console.error('Calendar sync initialization error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Perform initial sync to get baseline state and sync token
  async performInitialSync(userId: string): Promise<{ success: boolean; error?: string; sync_token?: string }> {
    try {
      
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        console.error('No Google credentials found for user:', userId);
        return { success: false, error: 'No Google credentials found' };
      }
      

      // Get events from the past 7 days to future 60 days
      const timeMin = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
      const timeMax = new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString();
      
      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `timeMin=${timeMin}&timeMax=${timeMax}&singleEvents=true&orderBy=startTime`,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        
        // If we get a 401, the token might be invalid even if it's not expired
        if (response.status === 401) {

          
          // Force a token refresh
          const refreshedCredentials = await getGoogleCredentials(userId);
          
          // Retry the request with the refreshed token
          const retryResponse = await fetch(
            `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
            `timeMin=${timeMin}&timeMax=${timeMax}&singleEvents=true&orderBy=startTime`,
            {
              headers: {
                'Authorization': `Bearer ${refreshedCredentials.access_token}`,
              },
            }
          );
          
          if (!retryResponse.ok) {
            const retryErrorText = await retryResponse.text();
            throw new Error(`Calendar API error after token refresh: ${retryResponse.status} - ${retryErrorText}`);
          }
          
          const retryData = await retryResponse.json();
          const events = retryData.items || [];
          const nextSyncToken = retryData.nextSyncToken;
          

          
          // Process events and continue with the rest of the function...
          let processed = 0;
          let created = 0;
          let updated = 0;

          for (const event of events) {
            const result = await this.processCalendarEvent(event, userId, refreshedCredentials);
            processed++;
            
            if (result.action === 'created') {
              created++;
            } else if (result.action === 'updated') {
              updated++;
            }
          }

          // Clean up orphaned meetings that no longer exist in Google Calendar
          const existingEventIds = new Set(events.map(event => event.id));
          const cleanupResult = await this.cleanupOrphanedMeetings(userId, existingEventIds);

          // Log the initial sync
          await supabase
            .from('calendar_sync_logs')
            .insert({
              user_id: userId,
              sync_type: 'initial',
              status: 'completed',
              events_processed: processed,
              meetings_created: created,
              meetings_updated: updated,
              meetings_deleted: cleanupResult.deleted + cleanupResult.cancelled,
            });

          // If no nextSyncToken was returned, we need to get one by making a sync token request
          if (!nextSyncToken) {
            // Try first approach: empty sync token request
            const syncTokenResponse = await fetch(
              `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
              `singleEvents=true&syncToken=`,
              {
                headers: {
                  'Authorization': `Bearer ${refreshedCredentials.access_token}`,
                },
              }
            );
            
            if (syncTokenResponse.ok) {
              const syncTokenData = await syncTokenResponse.json();
              const syncToken = syncTokenData.nextSyncToken;
              
              if (syncToken) {
                return { success: true, sync_token: syncToken };
              }
            }
            
            // If first approach didn't work, try second approach: make a small change and get sync token
  
            const alternativeResponse = await fetch(
              `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
              `timeMin=${encodeURIComponent(new Date().toISOString())}&timeMax=${encodeURIComponent(new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString())}&singleEvents=true`,
              {
                headers: {
                  'Authorization': `Bearer ${refreshedCredentials.access_token}`,
                },
              }
            );
            
            if (alternativeResponse.ok) {
              const alternativeData = await alternativeResponse.json();
              const alternativeSyncToken = alternativeData.nextSyncToken;
  
              
              if (alternativeSyncToken) {
                return { success: true, sync_token: alternativeSyncToken };
              }
            }
            

            return { success: false, error: 'Unable to get sync token. This can happen when there are no recent changes to sync. Try making a small change to your calendar and try again.' };
          }

          return { success: true, sync_token: nextSyncToken };
        }
        
        throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const events = data.items || [];
      const nextSyncToken = data.nextSyncToken;
      
      

      // Process events and store in database
      let processed = 0;
      let created = 0;
      let updated = 0;

      for (const event of events) {
        const result = await this.processCalendarEvent(event, userId, credentials);
        processed++;
        
        if (result.action === 'created') {
          created++;
        } else if (result.action === 'updated') {
          updated++;
        }
      }

      // Clean up orphaned meetings that no longer exist in Google Calendar
      const existingEventIds = new Set(events.map(event => event.id));
      const cleanupResult = await this.cleanupOrphanedMeetings(userId, existingEventIds);

      // Log the initial sync
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: 'initial',
          status: 'completed',
          events_processed: processed,
          meetings_created: created,
          meetings_updated: updated,
          meetings_deleted: cleanupResult.deleted + cleanupResult.cancelled,
        });

      // If no nextSyncToken was returned, we need to get one by making a sync token request
      if (!nextSyncToken) {
        // Try first approach: empty sync token request
        const syncTokenResponse = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
          `singleEvents=true&syncToken=`,
          {
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
            },
          }
        );
        
        if (syncTokenResponse.ok) {
          const syncTokenData = await syncTokenResponse.json();
          const syncToken = syncTokenData.nextSyncToken;
          
          if (syncToken) {
            return { success: true, sync_token: syncToken };
          }
        }
        
        // If first approach didn't work, try second approach: make a small change and get sync token
        const alternativeResponse = await fetch(
          `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
          `timeMin=${encodeURIComponent(new Date().toISOString())}&timeMax=${encodeURIComponent(new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString())}&singleEvents=true`,
          {
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
            },
          }
        );
        
        if (alternativeResponse.ok) {
          const alternativeData = await alternativeResponse.json();
          const alternativeSyncToken = alternativeData.nextSyncToken;
          
          if (alternativeSyncToken) {
            return { success: true, sync_token: alternativeSyncToken };
          }
        }
        
        return { success: false, error: 'Unable to get sync token. This can happen when there are no recent changes to sync. Try making a small change to your calendar and try again.' };
      }

      return { success: true, sync_token: nextSyncToken };
    } catch (error) {
      console.error('Initial sync error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Set up Google Calendar watch with sync token
  async setupWatch(userId: string, syncToken?: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      
      
      // First, ensure we have valid credentials
      let credentials;
      try {
        credentials = await getGoogleCredentials(userId);

      } catch (credError) {
        console.error('Failed to get valid credentials:', credError);
        return { success: false, error: `Authentication failed: ${credError.message}. Please reconnect your Google account.` };
      }
      
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      const webhookUrl = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${userId}`;
      const channelId = `calendar-watch-${userId}-${Date.now()}`;
      const expiration = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7 days

      const watchRequest: any = {
        id: channelId,
        type: 'web_hook',
        address: webhookUrl,
        params: {
          userId: userId,
        },
        expiration: expiration,
      };

      // Add sync token if available for incremental sync
      if (syncToken) {
        watchRequest.params.syncToken = syncToken;
      }

      const response = await fetch(
        'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(watchRequest),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Watch setup failed: ${response.status} - ${errorText}`);
      }

      const watchData = await response.json();
      

      // Validate and parse expiration date
      let expirationDate: Date;
      try {
        if (typeof watchData.expiration === 'number') {
          expirationDate = new Date(watchData.expiration);
        } else if (typeof watchData.expiration === 'string') {
          expirationDate = new Date(parseInt(watchData.expiration));
        } else {
          throw new Error(`Unexpected expiration type: ${typeof watchData.expiration}`);
        }
        
        if (isNaN(expirationDate.getTime())) {
          throw new Error(`Invalid expiration value: ${watchData.expiration}`);
        }
      } catch (dateError) {
        console.error('Date parsing error:', dateError);
        throw new Error(`Failed to parse expiration date: ${dateError.message}`);
      }

      // Store watch info in database - use upsert to create if doesn't exist
      const { error: dbError } = await supabase
        .from('calendar_webhooks')
        .upsert({
          user_id: userId,
          google_calendar_id: 'primary',
          webhook_id: watchData.id,
          resource_id: watchData.resourceId,
          expiration_time: expirationDate.toISOString(),
          sync_token: syncToken,
          is_active: true,
        }, {
          onConflict: 'user_id,google_calendar_id'
        });

      if (dbError) {
        console.error('Database error storing watch:', dbError);
        return { success: false, error: `Database error: ${dbError.message}` };
      }

      return { success: true, webhook_id: watchData.id };
    } catch (error) {
      console.error('Watch setup error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Renew existing watch before expiration
  async renewWatch(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      
      // Get current watch info
      const { data: webhook, error: fetchError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (fetchError || !webhook) {
        return await this.setupWatch(userId);
      }

      // Check if renewal is needed (renew if expires within 24 hours)
      const expirationTime = new Date(webhook.expiration_time).getTime();
      const now = Date.now();
      const renewalThreshold = 24 * 60 * 60 * 1000; // 24 hours

      if (expirationTime - now > renewalThreshold) {
        return { success: true, webhook_id: webhook.webhook_id };
      }

      // Stop existing watch
      await this.stopWatch(userId, webhook.webhook_id);

      // Set up new watch with current sync token
      return await this.setupWatch(userId, webhook.sync_token);
    } catch (error) {
      console.error('Watch renewal error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Stop existing watch
  async stopWatch(userId: string, webhookId: string): Promise<{ success: boolean; error?: string }> {
    try {
      
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      const response = await fetch(
        'https://www.googleapis.com/calendar/v3/channels/stop',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id: webhookId,
            resourceId: webhookId, // Use webhookId as resourceId for stop
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        // Don't throw error, just log warning
      }

      // Mark as inactive in database
      await supabase
        .from('calendar_webhooks')
        .update({ is_active: false })
        .eq('user_id', userId)
        .eq('webhook_id', webhookId);

      return { success: true };
    } catch (error) {
      console.error('Stop watch error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Perform incremental sync using sync token
  async performIncrementalSync(userId: string, syncToken?: string): Promise<{ success: boolean; error?: string; next_sync_token?: string }> {
    try {
      
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      // If no sync token provided, do a full sync
      if (!syncToken) {
        const fullSyncResult = await this.performInitialSync(userId);
        return fullSyncResult;
      }

      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `syncToken=${syncToken}&singleEvents=true&showDeleted=true`,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        
        // If sync token is invalid, we need to do a full sync
        if (response.status === 410) {
          const fullSyncResult = await this.performInitialSync(userId);
          if (fullSyncResult.success) {
            // Update webhook with new sync token
            await supabase
              .from('calendar_webhooks')
              .update({ sync_token: fullSyncResult.sync_token })
              .eq('user_id', userId);
          }
          return fullSyncResult;
        }
        
        throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const events = data.items || [];
      const nextSyncToken = data.nextSyncToken;
      
      

      // Process events
      let processed = 0;
      let created = 0;
      let updated = 0;
      let deleted = 0;

      for (const event of events) {
        // Check if event is deleted/cancelled
        if (event.status === 'cancelled' || event.deleted) {
          const deleteResult = await this.handleDeletedEvent(userId, event.id);
          if (deleteResult.success) {
            deleted++;
          }
          processed++;
        } else {
          const result = await this.processCalendarEvent(event, userId, credentials);
          processed++;
          
          if (result.action === 'created') {
            created++;
          } else if (result.action === 'updated') {
            updated++;
          } else if (result.action === 'deleted') {
            deleted++;
          }
        }
      }

      // Log the incremental sync
      await supabase
        .from('calendar_sync_logs')
        .insert({
          user_id: userId,
          sync_type: 'incremental',
          status: 'completed',
          events_processed: processed,
          meetings_created: created,
          meetings_updated: updated,
          meetings_deleted: deleted,
        });

      // Update sync token in database
      await supabase
        .from('calendar_webhooks')
        .update({ 
          sync_token: nextSyncToken,
          last_sync_at: new Date().toISOString()
        })
        .eq('user_id', userId);

      return { success: true, next_sync_token: nextSyncToken };
    } catch (error) {
      console.error('Incremental sync error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Process individual calendar event
  async processCalendarEvent(event: any, userId: string, credentials: any): Promise<{ action: string; meetingId?: string }> {
    const meetingUrl = extractMeetingUrl(event);
    
    if (!meetingUrl) {
      return { action: 'skipped_no_url' };
    }
    
    // Determine attendee status
    let attendeeStatus = 'needsAction';
    if (Array.isArray(event.attendees)) {
      const selfAttendee = event.attendees.find((a: any) => a.self);
      if (selfAttendee && selfAttendee.responseStatus) {
        attendeeStatus = selfAttendee.responseStatus;
      }
    } else if (event.creator && event.creator.email === credentials.google_email) {
      attendeeStatus = 'accepted';
    }
    
    const meeting = {
      user_id: userId,
      google_calendar_event_id: event.id,
      title: event.summary || 'Untitled Meeting',
      description: stripHtml(event.description || ''),
      meeting_url: meetingUrl,
      start_time: event.start.dateTime || event.start.date,
      end_time: event.end.dateTime || event.end.date,
      event_status: attendeeStatus,
      bot_status: 'pending',
    };
    
    // Check if meeting already exists
    const { data: existingMeeting } = await supabase
      .from('meetings')
      .select('id, bot_status, attendee_bot_id, bot_configuration, bot_deployment_method, auto_scheduled_via_email, virtual_email_attendee')
      .eq('google_calendar_event_id', event.id)
      .eq('user_id', userId)
      .maybeSingle();
    
    if (existingMeeting) {
      // Update existing meeting, but preserve bot-related fields
      const { error: updateError } = await supabase
        .from('meetings')
        .update({
          ...meeting,
          bot_status: existingMeeting.bot_status,
          attendee_bot_id: existingMeeting.attendee_bot_id,
          bot_configuration: existingMeeting.bot_configuration,
          bot_deployment_method: existingMeeting.bot_deployment_method,
          auto_scheduled_via_email: existingMeeting.auto_scheduled_via_email,
          virtual_email_attendee: existingMeeting.virtual_email_attendee,
        })
        .eq('id', existingMeeting.id);
      
      if (updateError) {
        console.error('Error updating meeting:', updateError);
        return { action: 'error_update', meetingId: existingMeeting.id };
      }
      
      return { action: 'updated', meetingId: existingMeeting.id };
    } else {
      // Create new meeting
      const { data: newMeeting, error: insertError } = await supabase
        .from('meetings')
        .insert(meeting)
        .select('id')
        .single();
      
      if (insertError) {
        console.error('Error creating meeting:', insertError);
        return { action: 'error_create' };
      }
      
      return { action: 'created', meetingId: newMeeting.id };
    }
  },

  // Handle deleted calendar event
  async handleDeletedEvent(userId: string, eventId: string): Promise<{ success: boolean; error?: string }> {
    try {
      
      // Find all meetings with this event ID
      const { data: meetings, error: findError } = await supabase
        .from('meetings')
        .select('*')
        .eq('google_calendar_event_id', eventId)
        .eq('user_id', userId);

      if (findError) {
        console.error('Error finding meeting for deletion:', findError);
        return { success: false, error: findError.message };
      }

      if (!meetings || meetings.length === 0) {
        return { success: true }; // Event not in our database, nothing to delete
      }

      // If there are multiple meetings with the same event ID, delete all of them
      if (meetings.length > 1) {
        const meetingIds = meetings.map(m => m.id);
        
        // Check if any meeting has an active bot
        const hasActiveBot = meetings.some(m => 
          m.bot_status === 'bot_joined' || m.bot_status === 'transcribing'
        );

        if (hasActiveBot) {
          // Update all meetings to cancelled status instead of deleting
          const { error: updateError } = await supabase
            .from('meetings')
            .update({
              event_status: 'declined',
              bot_status: 'failed',
              updated_at: new Date().toISOString(),
            })
            .in('id', meetingIds);

          if (updateError) {
            console.error('Error updating cancelled meetings:', updateError);
            return { success: false, error: updateError.message };
          }
        } else {
          // Delete all meetings
          const { error: deleteError } = await supabase
            .from('meetings')
            .delete()
            .in('id', meetingIds);

          if (deleteError) {
            console.error('Error deleting meetings:', deleteError);
            return { success: false, error: deleteError.message };
          }
        }

        return { success: true };
      }

      // Single meeting case
      const meeting = meetings[0];
      
      // Check if meeting has active bot
      const hasActiveBot = meeting.bot_status === 'bot_joined' || meeting.bot_status === 'transcribing';
      
      if (hasActiveBot) {
        // Update meeting status to cancelled instead of deleting
        const { error: updateError } = await supabase
          .from('meetings')
          .update({
            event_status: 'declined',
            bot_status: 'failed',
            updated_at: new Date().toISOString(),
          })
          .eq('id', meeting.id);

        if (updateError) {
          console.error('Error updating cancelled meeting:', updateError);
          return { success: false, error: updateError.message };
        }
      } else {
        // Delete meeting if no active bot
        const { error: deleteError } = await supabase
          .from('meetings')
          .delete()
          .eq('id', meeting.id);

        if (deleteError) {
          console.error('Error deleting meeting:', deleteError);
          return { success: false, error: deleteError.message };
        }
      }

      return { success: true };
    } catch (error) {
      console.error('Error handling deleted event:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Clean up orphaned meetings that no longer exist in Google Calendar
  async cleanupOrphanedMeetings(userId: string, existingEventIds: Set<string>): Promise<{ deleted: number; cancelled: number; error?: string }> {
    try {
      
      // Get all meetings for this user that have google_calendar_event_id
      const { data: meetings, error: findError } = await supabase
        .from('meetings')
        .select('id, google_calendar_event_id, title, bot_status, attendee_bot_id, project_id, transcript')
        .eq('user_id', userId)
        .not('google_calendar_event_id', 'is', null);
      
      if (findError) {
        console.error('Error finding meetings for cleanup:', findError);
        return { deleted: 0, cancelled: 0, error: findError.message };
      }
      
      if (!meetings || meetings.length === 0) {
        return { deleted: 0, cancelled: 0 };
      }

      let deleted = 0;
      let cancelled = 0;

      for (const meeting of meetings) {
        // Check if the meeting exists in the current Google Calendar response
        if (!existingEventIds.has(meeting.google_calendar_event_id)) {
          // Meeting no longer exists in Google Calendar
          
          // Check if the meeting has important data that should be preserved
          const hasImportantData = 
            meeting.bot_status && meeting.bot_status !== 'pending' || // Has active bot
            meeting.project_id || // Assigned to project
            meeting.transcript || // Has transcript
            meeting.attendee_bot_id; // Has bot ID
          
          if (hasImportantData) {
            // Meeting has important data, mark as cancelled instead of deleting
            await this.updateMeeting(meeting.id, { 
              event_status: 'declined',
              bot_status: meeting.bot_status === 'pending' ? 'failed' : meeting.bot_status,
              updated_at: new Date().toISOString()
            });
            cancelled++;
          } else {
            // No important data, safe to delete
            await this.deleteMeeting(meeting.id);
            deleted++;
          }
        }
      }

      return { deleted, cancelled };
    } catch (error) {
      console.error('Error cleaning up orphaned meetings:', error);
      return { deleted: 0, cancelled: 0, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  },

  // Test Google Calendar API access
  async testCalendarAccess(userId: string): Promise<{ success: boolean; error?: string }> {
    try {
      // Testing calendar access for user
      
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      // Test with a simple calendar API call
      const response = await fetch(
        'https://www.googleapis.com/calendar/v3/calendars/primary',
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Calendar API test failed:', response.status, errorText);
        return { success: false, error: `Calendar API test failed: ${response.status} - ${errorText}` };
      }

              // Calendar API access test successful
      return { success: true };
    } catch (error) {
      console.error('Calendar access test error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Manual sync without cleanup (for debugging)
  async manualSyncWithoutCleanup(userId: string): Promise<{ success: boolean; error?: string; processed?: number }> {
    try {
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      // Get events from the past 7 days to future 60 days
      const timeMin = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
      const timeMax = new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString();
      
      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `timeMin=${timeMin}&timeMax=${timeMax}&singleEvents=true&orderBy=startTime`,
        {
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const events = data.items || [];
      
      let processed = 0;
      let created = 0;
      let updated = 0;

      for (const event of events) {
        const result = await this.processCalendarEvent(event, userId, credentials);
        processed++;
        
        if (result.action === 'created') {
          created++;
        } else if (result.action === 'updated') {
          updated++;
        }
      }

      return { success: true, processed };
    } catch (error) {
      console.error('Manual sync error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Force initial sync even if webhook exists (for debugging)
  async forceInitialSync(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      
      // Step 1: Get initial sync token (force sync regardless of webhook)
      const initialSyncResult = await this.performInitialSync(userId);
      
      if (!initialSyncResult.success) {
        return { success: false, error: `Initial sync failed: ${initialSyncResult.error}` };
      }
      
      // Step 2: Set up watch with sync token
      const watchResult = await this.setupWatch(userId, initialSyncResult.sync_token);
      
      if (!watchResult.success) {
        return { success: false, error: `Watch setup failed: ${watchResult.error}` };
      }
      
      return { success: true, webhook_id: watchResult.webhook_id };
    } catch (error) {
      console.error('Force initial sync error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Clear webhook and force fresh setup (for debugging)
  async clearWebhookAndResync(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      
      // Step 1: Get existing webhook
      const { data: existingWebhook } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('is_active', true)
        .maybeSingle();
      
      if (existingWebhook) {
        
        // Stop the existing webhook
        const stopResult = await this.stopWatch(userId, existingWebhook.webhook_id);
        if (!stopResult.success) {
        }
        
        // Mark webhook as inactive
        await supabase
          .from('calendar_webhooks')
          .update({ is_active: false })
          .eq('id', existingWebhook.id);
      }
      
      // Step 2: Perform fresh initial sync
      const initialSyncResult = await this.performInitialSync(userId);
      
      if (!initialSyncResult.success) {
        return { success: false, error: `Initial sync failed: ${initialSyncResult.error}` };
      }
      
      // Step 3: Set up new watch
      const watchResult = await this.setupWatch(userId, initialSyncResult.sync_token);
      
      if (!watchResult.success) {
        return { success: false, error: `Watch setup failed: ${watchResult.error}` };
      }
      
      return { success: true, webhook_id: watchResult.webhook_id };
    } catch (error) {
      console.error('Clear and resync error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Clean up all calendar data for a user (when disconnecting Google)
  async cleanupCalendarData(userId: string): Promise<{ success: boolean; error?: string; deleted: { meetings: number; webhooks: number; syncLogs: number } }> {
    try {
      
      let deletedMeetings = 0;
      let deletedWebhooks = 0;
      let deletedSyncLogs = 0;
      
      // Step 1: Stop and delete webhooks
      const { data: webhooks, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId);
      
      if (webhookError) {
        console.error('Error fetching webhooks:', webhookError);
      } else if (webhooks && webhooks.length > 0) {
        for (const webhook of webhooks) {
          // Stop the webhook with Google
          if (webhook.is_active) {
            try {
              const stopResult = await this.stopWatch(userId, webhook.webhook_id);
              if (!stopResult.success) {
              }
            } catch (error) {
            }
          }
        }
        
        // Delete all webhooks for this user
        const { error: deleteWebhookError } = await supabase
          .from('calendar_webhooks')
          .delete()
          .eq('user_id', userId);
        
        if (deleteWebhookError) {
          console.error('Error deleting webhooks:', deleteWebhookError);
        } else {
          deletedWebhooks = webhooks.length;
        }
      }
      
      // Step 2: Delete all meetings for this user
      const { data: meetings, error: meetingsError } = await supabase
        .from('meetings')
        .select('id')
        .eq('user_id', userId);
      
      if (meetingsError) {
        console.error('Error fetching meetings:', meetingsError);
      } else if (meetings && meetings.length > 0) {
        const { error: deleteMeetingsError } = await supabase
          .from('meetings')
          .delete()
          .eq('user_id', userId);
        
        if (deleteMeetingsError) {
          console.error('Error deleting meetings:', deleteMeetingsError);
        } else {
          deletedMeetings = meetings.length;
        }
      }
      
      // Step 3: Delete sync logs for this user
      const { data: syncLogs, error: syncLogsError } = await supabase
        .from('calendar_sync_logs')
        .select('id')
        .eq('user_id', userId);
      
      if (syncLogsError) {
        console.error('Error fetching sync logs:', syncLogsError);
      } else if (syncLogs && syncLogs.length > 0) {
        const { error: deleteSyncLogsError } = await supabase
          .from('calendar_sync_logs')
          .delete()
          .eq('user_id', userId);
        
        if (deleteSyncLogsError) {
          console.error('Error deleting sync logs:', deleteSyncLogsError);
        } else {
          deletedSyncLogs = syncLogs.length;
        }
      }
      
      
      return {
        success: true,
        deleted: {
          meetings: deletedMeetings,
          webhooks: deletedWebhooks,
          syncLogs: deletedSyncLogs
        }
      };
    } catch (error) {
      console.error('Calendar cleanup error:', error);
      return { 
        success: false, 
        error: error.message || String(error),
        deleted: { meetings: 0, webhooks: 0, syncLogs: 0 }
      };
    }
  },

  // Get watch status and sync information
  async getWatchStatus(userId: string): Promise<{
    webhook_active: boolean;
    webhook_url?: string;
    last_sync?: string;
    sync_logs: any[];
    recent_errors: any[];
    expiration_time?: string;
    sync_token?: string;
  }> {
    try {
      const { data: webhook, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (webhookError || !webhook) {
        return {
          webhook_active: false,
          sync_logs: [],
          recent_errors: [],
        };
      }

      // Get recent sync logs
      const { data: syncLogs } = await supabase
        .from('calendar_sync_logs')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(5);

      // Get recent errors
      const { data: recentErrors } = await supabase
        .from('calendar_sync_logs')
        .select('*')
        .eq('user_id', userId)
        .eq('status', 'failed')
        .order('created_at', { ascending: false })
        .limit(5);

      return {
        webhook_active: webhook.is_active,
        webhook_url: `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${userId}`,
        last_sync: webhook.updated_at,
        sync_logs: syncLogs || [],
        recent_errors: recentErrors || [],
        expiration_time: webhook.expiration_time,
        sync_token: webhook.sync_token,
      };
    } catch (error) {
      console.error('Error getting watch status:', error);
      return {
        webhook_active: false,
        sync_logs: [],
        recent_errors: [],
      };
    }
  },

  // Verify webhook registration with Google
  async verifyWebhookWithGoogle(userId: string): Promise<{ 
    success: boolean; 
    error?: string; 
    webhook_active?: boolean;
    webhook_id?: string;
    resource_id?: string;
    expiration?: string;
  }> {
    try {
      const credentials = await getGoogleCredentials(userId);
      
      // Get current webhook info from database
      const { data: webhookData, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (webhookError || !webhookData) {
        return { success: false, error: 'No active webhook found in database' };
      }

      // Try to stop the current webhook to verify it exists
      const stopResponse = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events/stop`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${credentials.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id: webhookData.webhook_id,
            resourceId: webhookData.resource_id,
          }),
        }
      );

      if (stopResponse.ok) {
        // Webhook exists, now recreate it
        const webhookUrl = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${userId}`;
        const channelId = `calendar-watch-${userId}-${Date.now()}`;
        const expiration = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7 days

        const watchRequest = {
          id: channelId,
          type: 'web_hook',
          address: webhookUrl,
          params: {
            userId: userId,
          },
          expiration: expiration,
        };

        const createResponse = await fetch(
          'https://www.googleapis.com/calendar/v3/calendars/primary/events/watch',
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${credentials.access_token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(watchRequest),
          }
        );

        if (!createResponse.ok) {
          const errorText = await createResponse.text();
          return { success: false, error: `Failed to recreate webhook: ${createResponse.status} - ${errorText}` };
        }

        const watchData = await createResponse.json();
        
        // Update database with new webhook info
        const expirationDate = new Date(watchData.expiration);
        const { error: updateError } = await supabase
          .from('calendar_webhooks')
          .update({
            webhook_id: watchData.id,
            resource_id: watchData.resourceId,
            expiration_time: expirationDate.toISOString(),
            is_active: true,
          })
          .eq('user_id', userId)
          .eq('google_calendar_id', 'primary');

        if (updateError) {
          return { success: false, error: `Database update failed: ${updateError.message}` };
        }

        return { 
          success: true, 
          webhook_active: true,
          webhook_id: watchData.id,
          resource_id: watchData.resourceId,
          expiration: expirationDate.toISOString()
        };
      } else {
        return { success: false, error: 'Webhook not found or invalid with Google' };
      }
    } catch (error) {
      console.error('Webhook verification error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },
}; 