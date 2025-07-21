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
    
    console.log('Token expired, attempting refresh...');
    
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
    console.log('Token refreshed successfully');
    
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
  
  console.log('Token is still valid, expires at:', data.expires_at);
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
  polling_enabled?: boolean;
  real_time_transcript?: any;
  final_transcript_ready?: boolean;
  transcript_metadata?: any;
  bot_configuration?: any;
  // Auto-scheduling fields
  bot_deployment_method?: 'manual' | 'automatic' | 'scheduled';
  auto_scheduled_via_email?: boolean;
  virtual_email_attendee?: string;
  auto_bot_notification_sent?: boolean;
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
    
    // Get the most recent successful sync time from logs
    const lastSuccessfulSync = syncLogs?.find(log => 
      log.status === 'completed' && 
      (log.sync_type === 'webhook' || log.sync_type === 'manual' || log.sync_type === 'initial')
    );
    
    const status = {
      webhook_active: !!webhook,
      last_sync: lastSuccessfulSync?.created_at || webhook?.last_sync_at,
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

  // Get raw calendar events from Google (for debugging)
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

  // Test webhook notification specifically (for debugging real-time sync)
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
      last_sync: syncLogs?.find(log => log.status === 'completed')?.created_at || webhook?.last_sync_at,
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
      console.log('Initializing calendar sync for user:', userId);
      
      // Step 1: Get initial sync token
      const initialSyncResult = await this.performInitialSync(userId);
      if (!initialSyncResult.success) {
        return { success: false, error: `Initial sync failed: ${initialSyncResult.error}` };
      }
      
      // Step 2: Set up watch with sync token
      const watchResult = await this.setupWatch(userId, initialSyncResult.sync_token);
      if (!watchResult.success) {
        return { success: false, error: `Watch setup failed: ${watchResult.error}` };
      }
      
      console.log('Calendar sync initialized successfully');
      return { success: true, webhook_id: watchResult.webhook_id };
    } catch (error) {
      console.error('Calendar sync initialization error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Perform initial sync to get baseline state and sync token
  async performInitialSync(userId: string): Promise<{ success: boolean; error?: string; sync_token?: string }> {
    try {
      console.log('Performing initial sync for user:', userId);
      
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
        
        // If we get a 401, the token might be invalid even if it's not expired
        if (response.status === 401) {
          console.log('Got 401 error, token might be invalid. Attempting token refresh...');
          
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
          
          console.log(`Initial sync (retry) found ${events.length} events, nextSyncToken: ${nextSyncToken}`);
          
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
              sync_range_start: timeMin,
              sync_range_end: timeMax,
            });

          // If no nextSyncToken was returned, we need to get one by making a sync token request
          if (!nextSyncToken) {
            console.log('No nextSyncToken returned, requesting sync token...');
            
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
              console.log('Got sync token from sync token request:', syncToken);
              
              if (syncToken) {
                return { success: true, sync_token: syncToken };
              }
            }
            
            // If first approach didn't work, try second approach: make a small change and get sync token
            console.log('First approach failed, trying alternative method...');
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
              console.log('Got sync token from alternative request:', alternativeSyncToken);
              
              if (alternativeSyncToken) {
                return { success: true, sync_token: alternativeSyncToken };
              }
            }
            
            console.log('Both approaches failed to get sync token');
            return { success: false, error: 'Unable to get sync token. This can happen when there are no recent changes to sync. Try making a small change to your calendar and try again.' };
          }

          return { success: true, sync_token: nextSyncToken };
        }
        
        throw new Error(`Calendar API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const events = data.items || [];
      const nextSyncToken = data.nextSyncToken;
      
      console.log(`Initial sync found ${events.length} events, nextSyncToken: ${nextSyncToken}`);

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
          sync_range_start: timeMin,
          sync_range_end: timeMax,
        });

      // If no nextSyncToken was returned, we need to get one by making a sync token request
      if (!nextSyncToken) {
        console.log('No nextSyncToken returned, requesting sync token...');
        
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
          console.log('Got sync token from sync token request:', syncToken);
          
          if (syncToken) {
            return { success: true, sync_token: syncToken };
          }
        }
        
        // If first approach didn't work, try second approach: make a small change and get sync token
        console.log('First approach failed, trying alternative method...');
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
          console.log('Got sync token from alternative request:', alternativeSyncToken);
          
          if (alternativeSyncToken) {
            return { success: true, sync_token: alternativeSyncToken };
          }
        }
        
        console.log('Both approaches failed to get sync token');
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
      console.log('Setting up calendar watch for user:', userId);
      
      // First, ensure we have valid credentials
      let credentials;
      try {
        credentials = await getGoogleCredentials(userId);
        console.log('Credentials obtained successfully');
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
      console.log('Watch setup response:', watchData);

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

      // Store watch info in database
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
          last_sync_at: new Date().toISOString(),
        }, {
          onConflict: 'user_id,google_calendar_id',
        });

      if (dbError) {
        console.error('Database error storing watch:', dbError);
        return { success: false, error: `Database error: ${dbError.message}` };
      }

      console.log('Calendar watch setup successfully');
      return { success: true, webhook_id: watchData.id };
    } catch (error) {
      console.error('Watch setup error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Renew existing watch before expiration
  async renewWatch(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      console.log('Renewing calendar watch for user:', userId);
      
      // Get current watch info
      const { data: webhook, error: fetchError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', userId)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (fetchError || !webhook) {
        console.log('No active watch found, setting up new one');
        return await this.setupWatch(userId);
      }

      // Check if renewal is needed (renew if expires within 24 hours)
      const expirationTime = new Date(webhook.expiration_time).getTime();
      const now = Date.now();
      const renewalThreshold = 24 * 60 * 60 * 1000; // 24 hours

      if (expirationTime - now > renewalThreshold) {
        console.log('Watch not expiring soon, no renewal needed');
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
      console.log('Stopping calendar watch:', webhookId);
      
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
        console.warn(`Failed to stop watch: ${response.status} - ${errorText}`);
        // Don't throw error, just log warning
      }

      // Mark as inactive in database
      await supabase
        .from('calendar_webhooks')
        .update({ is_active: false })
        .eq('user_id', userId)
        .eq('webhook_id', webhookId);

      console.log('Calendar watch stopped successfully');
      return { success: true };
    } catch (error) {
      console.error('Stop watch error:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Perform incremental sync using sync token
  async performIncrementalSync(userId: string, syncToken: string): Promise<{ success: boolean; error?: string; next_sync_token?: string }> {
    try {
      console.log('Performing incremental sync for user:', userId);
      
      const credentials = await getGoogleCredentials(userId);
      if (!credentials) {
        return { success: false, error: 'No Google credentials found' };
      }

      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        `syncToken=${syncToken}&singleEvents=true&orderBy=startTime&showDeleted=true`,
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
          console.log('Sync token invalid, performing full sync');
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
      
      console.log(`Incremental sync found ${events.length} events, nextSyncToken: ${nextSyncToken}`);

      // Process events
      let processed = 0;
      let created = 0;
      let updated = 0;
      let deleted = 0;

      for (const event of events) {
        // Check if event is deleted/cancelled
        if (event.status === 'cancelled' || event.deleted) {
          console.log('Processing deleted event:', event.id);
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
      .select('id, bot_status, attendee_bot_id')
      .eq('google_calendar_event_id', event.id)
      .eq('user_id', userId)
      .maybeSingle();
    
    if (existingMeeting) {
      // Update existing meeting
      const { error: updateError } = await supabase
        .from('meetings')
        .update(meeting)
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
      console.log('Handling deleted event:', eventId, 'for user:', userId);
      
      // Find the meeting in our database
      const { data: meeting, error: findError } = await supabase
        .from('meetings')
        .select('id, title, bot_status')
        .eq('google_calendar_event_id', eventId)
        .eq('user_id', userId)
        .maybeSingle();
      
      if (findError) {
        console.error('Error finding meeting for deletion:', findError);
        return { success: false, error: findError.message };
      }
      
      if (!meeting) {
        console.log('No meeting found for deleted event:', eventId);
        return { success: true }; // Event not in our database, nothing to delete
      }
      
      // Check if meeting has active bot or transcript
      if (meeting.bot_status === 'bot_joined' || meeting.bot_status === 'transcribing') {
        console.log('Meeting has active bot, updating status instead of deleting:', meeting.id);
        
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
        
        console.log('Meeting marked as cancelled:', meeting.id);
        return { success: true };
      }
      
      // Delete the meeting if no active bot
      const { error: deleteError } = await supabase
        .from('meetings')
        .delete()
        .eq('id', meeting.id);
      
      if (deleteError) {
        console.error('Error deleting meeting:', deleteError);
        return { success: false, error: deleteError.message };
      }
      
      console.log('Meeting deleted successfully:', meeting.id, meeting.title);
      return { success: true };
    } catch (error) {
      console.error('Error handling deleted event:', error);
      return { success: false, error: error.message || String(error) };
    }
  },

  // Test Google Calendar API access
  async testCalendarAccess(userId: string): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('Testing calendar access for user:', userId);
      
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

      console.log('Calendar API access test successful');
      return { success: true };
    } catch (error) {
      console.error('Calendar access test error:', error);
      return { success: false, error: error.message || String(error) };
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
        last_sync: webhook.last_sync_at,
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
}; 