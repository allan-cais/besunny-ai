// Calendar Service
// Core calendar functionality extracted from calendar.ts

import { supabase } from './supabase';
import type { 
  Meeting, 
  GoogleCalendarEvent, 
  GoogleCredentials, 
  AuthSession,
  CalendarSyncResult 
} from '../types';
import { errorUtils, createError } from './error-handling';
import { config } from '../config';

// Utility functions
function extractMeetingUrl(event: GoogleCalendarEvent): string | null {
  // Check for Google Meet URL in conferenceData
  if (event.conferenceData?.entryPoints) {
    const meetEntry = event.conferenceData.entryPoints.find(
      (entry) => entry.entryPointType === 'video'
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
async function getGoogleCredentials(userId: string): Promise<GoogleCredentials> {
  const { data, error } = await supabase
    .from('google_credentials')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();
  
  if (error || !data) {
    throw new Error('Google credentials not found');
  }
  
  // Check if token is expired and refresh if needed
  if (new Date(data.expiresAt) <= new Date()) {
    if (!data.refreshToken) {
      throw new Error('Token expired and no refresh token available');
    }
    
    // Refresh the token
    const refreshResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: config.api.openaiApiKey || '',
        client_secret: config.api.anthropicApiKey || '',
        refresh_token: data.refreshToken,
        grant_type: 'refresh_token',
      }),
    });
    
    if (!refreshResponse.ok) {
      const errorText = await refreshResponse.text();
      throw new Error(`Failed to refresh Google token: ${refreshResponse.status} - ${errorText}`);
    }
    
    const refreshData = await refreshResponse.json();
    
    // Update the credentials in the database
    const { error: updateError } = await supabase
      .from('google_credentials')
      .update({
        access_token: refreshData.accessToken,
        expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
      })
      .eq('user_id', userId);
    
    if (updateError) {
      throw new Error(`Failed to update credentials: ${updateError.message}`);
    }
    
    return {
      ...data,
      access_token: refreshData.accessToken,
      expires_at: new Date(Date.now() + refreshData.expires_in * 1000).toISOString(),
    };
  }
  
  return data;
}

// Calendar service class
export class CalendarService {
  // Get current week meetings
  async getCurrentWeekMeetings(session?: AuthSession): Promise<Meeting[]> {
    try {
      // Use provided session or get from auth
      const currentSession = session || (await supabase.auth.getSession()).data.session;
      if (!currentSession) {
        throw new Error('Not authenticated');
      }
      
      const now = new Date();
      const sevenDaysFromNow = new Date(now);
      sevenDaysFromNow.setDate(now.getDate() + 7); // 7 days from now
      sevenDaysFromNow.setHours(23, 59, 59, 999);
      
      const { data: meetings, error } = await supabase
        .from('meetings')
        .select('*')
        .eq('user_id', currentSession.user.id)
        .is('project_id', null) // Only unassigned meetings
        .gte('start_time', now.toISOString()) // From current time onwards (including in-progress meetings)
        .lte('start_time', sevenDaysFromNow.toISOString()) // Up to 7 days in the future
        .order('start_time', { ascending: true });
      
      if (error) {
        throw error;
      }
      
      return meetings || [];
    } catch (error) {
      throw error;
    }
  }

  // Get all current week meetings (including assigned ones)
  async getAllCurrentWeekMeetings(session?: AuthSession): Promise<Meeting[]> {
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
  }

  // Get sync status
  async getSyncStatus(session?: AuthSession): Promise<{
    webhook_active: boolean;
    last_sync?: string;
    sync_logs: Record<string, unknown>[];
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
      sync_logs: syncLogs || [],
      webhook_expires_at: webhook?.expiration_time,
    };
    
    return status;
  }

  // Setup webhook sync
  async setupWebhookSync(): Promise<{
    ok: boolean;
    webhook_id?: string;
    resource_id?: string;
    expiration?: number;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/calendar/webhook`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: session.user.id,
        calendar_id: 'primary'
      }),
    });
    
    const result = await response.json();
    return {
      ok: result.success,
      webhook_id: result.webhook_id,
      resource_id: result.webhook_id,
      expiration: result.expiration,
      error: result.message
    };
  }

  // Initial sync
  async initialSync(projectId?: string): Promise<CalendarSyncResult> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/calendar/sync`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: session.user.id,
        calendar_id: 'primary',
        sync_range_days: 60,
        project_id: projectId,
        sync_type: 'initial'
      }),
    });
    
    const result = await response.json();
    if (!result.success) throw new Error(result.message || 'Failed to sync calendar events');
    return result;
  }

  // Full sync
  async fullSync(projectId?: string, daysPast: number = 365, daysFuture: number = 60): Promise<CalendarSyncResult> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/calendar/sync`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: session.user.id,
        calendar_id: 'primary',
        sync_range_days: daysPast + daysFuture,
        project_id: projectId,
        sync_type: 'full'
      }),
    });
    
    const result = await response.json();
    if (!result.success) throw new Error(result.message || 'Failed to sync calendar events');
    return result;
  }

  // Get raw calendar events
  async getRawCalendarEvents(daysPast: number = 7, daysFuture: number = 60): Promise<{
    ok: boolean;
    events?: GoogleCalendarEvent[];
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/calendar/events/raw`);
    url.searchParams.set('user_id', session.user.id);
    url.searchParams.set('days_past', daysPast.toString());
    url.searchParams.set('days_future', daysFuture.toString());
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const result = await response.json();
    return {
      ok: result.success,
      events: result.events,
      error: result.message
    };
  }

  // Send bot to meeting
  async sendBotToMeeting(meetingId: string, configuration?: Record<string, unknown>): Promise<{
    ok: boolean;
    bot_id?: string;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const url = new URL(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/attendee/create-bot`);
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        meeting_url: meetingId,
        bot_name: configuration?.bot_name || 'Sunny AI Notetaker',
        bot_chat_message: configuration?.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!',
        user_id: session.user.id,
      }),
    });
    
    const result = await response.json();
    return {
      ok: result.success,
      bot_id: result.bot_id,
      error: result.error || result.message
    };
  }

  // Update meeting
  async updateMeeting(meetingId: string, updates: Partial<Meeting>): Promise<{
    ok: boolean;
    meeting?: Meeting;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const { data, error } = await supabase
      .from('meetings')
      .update(updates)
      .eq('id', meetingId)
      .eq('user_id', session.user.id)
      .select()
      .single();
    
    if (error) {
      return { ok: false, error: error.message };
    }
    
    return { ok: true, meeting: data };
  }

  // Delete meeting
  async deleteMeeting(meetingId: string): Promise<{
    ok: boolean;
    error?: string;
  }> {
    const session = (await supabase.auth.getSession()).data.session;
    if (!session) throw new Error('Not authenticated');
    
    const { error } = await supabase
      .from('meetings')
      .delete()
      .eq('id', meetingId)
      .eq('user_id', session.user.id);
    
    if (error) {
      return { ok: false, error: error.message };
    }
    
    return { ok: true };
  }
}

// Export singleton instance
export const calendarService = new CalendarService();
export default calendarService;
