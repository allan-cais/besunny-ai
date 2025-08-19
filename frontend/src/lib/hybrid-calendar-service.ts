// Hybrid Calendar Service
// Provides seamless integration between Supabase edge functions and Python backend
// Automatically falls back to Supabase if Python backend is unavailable

import { features } from '../config';
import { calendarService as supabaseCalendarService } from './calendar';
import { pythonBackendAPI } from './python-backend-api';
import type { Meeting, AuthSession } from '../types';

// Hybrid calendar service that can use either backend
export const hybridCalendarService = {
  // Check if Python backend is available
  async isPythonBackendAvailable(): Promise<boolean> {
    if (!features.isPythonBackendEnabled()) {
      return false;
    }

    try {
      const response = await pythonBackendAPI.healthCheck();
      return response.success && response.data?.status === 'healthy';
    } catch {
      return false;
    }
  },

  // Get current and upcoming meetings with automatic backend selection
  async getCurrentWeekMeetings(session?: AuthSession): Promise<Meeting[]> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.getUserMeetings();
          if (response.success && response.data) {
            return response.data.meetings;
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getCurrentWeekMeetings(session);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getCurrentWeekMeetings(session);
    }
  },

  // Get all current week meetings with automatic backend selection
  async getAllCurrentWeekMeetings(session?: AuthSession): Promise<Meeting[]> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.getUserMeetings();
          if (response.success && response.data) {
            return response.data.meetings;
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getAllCurrentWeekMeetings(session);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getAllCurrentWeekMeetings(session);
    }
  },

  // Get upcoming meetings with automatic backend selection
  async getUpcomingMeetings(): Promise<Meeting[]> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.getUserMeetings();
          if (response.success && response.data) {
            return response.data.meetings;
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getUpcomingMeetings();
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getUpcomingMeetings();
    }
  },

  // Get project meetings with automatic backend selection
  async getProjectMeetings(projectId: string): Promise<Meeting[]> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.getUserMeetings(projectId);
          if (response.success && response.data) {
            return response.data.meetings;
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getProjectMeetings(projectId);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getProjectMeetings(projectId);
    }
  },

  // Setup calendar webhook with automatic backend selection
  async setupWebhookSync(): Promise<{
    ok: boolean;
    webhook_id?: string;
    resource_id?: string;
    expiration?: number;
    error?: string;
  }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          // Get current user ID from session
          const session = await this.getCurrentSession();
          if (session?.user?.id) {
            const response = await pythonBackendAPI.setupCalendarWebhook({
              user_id: session.user.id,
              calendar_id: 'primary'
            });
            
            if (response.success && response.data) {
              return {
                ok: true,
                webhook_id: response.data.webhook_id,
                resource_id: response.data.webhook_id, // Python backend uses webhook_id as resource_id
                expiration: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.setupWebhookSync();
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.setupWebhookSync();
    }
  },

  // Get sync status with automatic backend selection
  async getSyncStatus(session?: AuthSession): Promise<{
    webhook_active: boolean;
    last_sync?: string;
    sync_logs: Record<string, unknown>[];
    webhook_expires_at?: string;
  }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const currentSession = session || await this.getCurrentSession();
          if (currentSession?.user?.id) {
            const response = await pythonBackendAPI.getCalendarSyncStatus(currentSession.user.id);
            if (response.success && response.data) {
              // Transform Python backend response to match Supabase format
              return {
                webhook_active: response.data.is_active || false,
                last_sync: response.data.last_sync_at,
                sync_logs: [], // Python backend doesn't provide sync logs in this endpoint
                webhook_expires_at: response.data.expiration_time,
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getSyncStatus(session);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getSyncStatus(session);
    }
  },

  // Renew webhook with automatic backend selection
  async renewWebhook(): Promise<{
    ok: boolean;
    webhook_id?: string;
    error?: string;
  }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const currentSession = await this.getCurrentSession();
          if (currentSession?.user?.id) {
            // Python backend doesn't have a direct renew endpoint, so we'll recreate
            const response = await pythonBackendAPI.setupCalendarWebhook({
              user_id: currentSession.user.id,
              calendar_id: 'primary'
            });
            
            if (response.success && response.data) {
              return {
                ok: true,
                webhook_id: response.data.webhook_id,
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.renewWebhook();
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.renewWebhook();
    }
  },

  // Update bot status (always use Supabase for now as it's database operation)
  async updateBotStatus(meetingId: string, botStatus: Meeting['bot_status'], attendeeBotId?: string): Promise<void> {
    return await supabaseCalendarService.updateBotStatus(meetingId, botStatus, attendeeBotId);
  },

  // Update meeting (always use Supabase for now as it's database operation)
  async updateMeeting(meetingId: string, updates: Partial<Meeting>): Promise<void> {
    return await supabaseCalendarService.updateMeeting(meetingId, updates);
  },

  // Associate meeting with project (always use Supabase for now as it's database operation)
  async associateMeetingWithProject(meetingId: string, projectId: string): Promise<void> {
    return await supabaseCalendarService.associateMeetingWithProject(meetingId, projectId);
  },

  // Delete meeting (always use Supabase for now as it's database operation)
  async deleteMeeting(meetingId: string): Promise<void> {
    return await supabaseCalendarService.deleteMeeting(meetingId);
  },

  // Bot management (always use Supabase for now as it's database operation)
  async createBot(botData: any): Promise<any> {
    return await supabaseCalendarService.createBot(botData);
  },

  async getUserBots(): Promise<any[]> {
    return await supabaseCalendarService.getUserBots();
  },

  async updateBot(botId: string, updates: any): Promise<void> {
    return await supabaseCalendarService.updateBot(botId, updates);
  },

  async deleteBot(botId: string): Promise<void> {
    return await supabaseCalendarService.deleteBot(botId);
  },

  // Advanced calendar operations with automatic backend selection
  async initializeCalendarSync(userId: string): Promise<{ success: boolean; error?: string; webhook_id?: string }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          // Python backend doesn't have this exact method, so we'll use setup webhook
          const response = await pythonBackendAPI.setupCalendarWebhook({
            user_id: userId,
            calendar_id: 'primary'
          });
          
          if (response.success && response.data) {
            return {
              success: true,
              webhook_id: response.data.webhook_id,
            };
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.initializeCalendarSync(userId);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.initializeCalendarSync(userId);
    }
  },

  // Get watch status with automatic backend selection
  async getWatchStatus(userId: string): Promise<{
    webhook_active: boolean;
    webhook_url?: string;
    last_sync?: string;
    sync_logs: Record<string, unknown>[];
    recent_errors: Record<string, unknown>[];
    expiration_time?: string;
    sync_token?: string;
  }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.getCalendarSyncStatus(userId);
          if (response.success && response.data) {
            // Transform Python backend response to match Supabase format
            return {
              webhook_active: response.data.is_active || false,
              webhook_url: `${features.isPythonBackendEnabled() ? (await import('../config')).config.pythonBackend.url : (await import('../config')).config.supabase.url}/api/v1/calendar/webhook`,
              last_sync: response.data.last_sync_at,
              sync_logs: [],
              recent_errors: [],
              expiration_time: response.data.expiration_time,
              sync_token: response.data.sync_token,
            };
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getWatchStatus(userId);
    } catch (error) {
      console.warn('Python backend failed, falling back to Supabase:', error);
      return await supabaseCalendarService.getWatchStatus(userId);
    }
  },

  // Helper method to get current session
  private async getCurrentSession(): Promise<AuthSession | null> {
    try {
      // Import supabase dynamically to avoid circular dependencies
      const { supabase } = await import('./supabase');
      const { data } = await supabase.auth.getSession();
      return data.session;
    } catch {
      return null;
    }
  },
};

// Export the hybrid service as the default calendar service
export default hybridCalendarService;
