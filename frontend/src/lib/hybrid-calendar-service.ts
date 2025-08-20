// Hybrid Calendar Service
// Provides seamless integration with Python backend (Supabase Edge Functions migrated)
// Automatically falls back to Supabase if Python backend is unavailable

import { AuthSession } from '@supabase/supabase-js';
import { Meeting } from '../types';
import { features } from '../config';
import { pythonBackendAPI } from './python-backend-services';
import { supabaseCalendarService } from './calendar-service';

// Hybrid calendar service that automatically selects between Python backend and Supabase
// based on availability and feature flags
export const hybridCalendarService = {
  // Check if Python backend is available
  async isPythonBackendAvailable(): Promise<boolean> {
    try {
      const response = await pythonBackendAPI.healthCheck();
      return response.success && response.data?.isHealthy;
    } catch {
      return false;
    }
  },

  // Get current session for user context
  async getCurrentSession(): Promise<AuthSession | null> {
    try {
      const { data: { session } } = await supabaseCalendarService.supabase.auth.getSession();
      return session;
    } catch {
      return null;
    }
  },

  // Get current week meetings with automatic backend selection
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
      // Silently fall back to Supabase
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
      // Silently fall back to Supabase
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
      // Silently fall back to Supabase
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
      // Silently fall back to Supabase
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
                expiration: response.data.expiration,
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.setupWebhookSync();
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.setupWebhookSync();
    }
  },

  // Renew calendar webhook with automatic backend selection
  async renewWebhookSync(webhookId: string): Promise<{
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
            const response = await pythonBackendAPI.renewCalendarWebhook({
              webhook_id: webhookId,
              user_id: session.user.id,
              calendar_id: 'primary'
            });
            
            if (response.success && response.data) {
              return {
                ok: true,
                webhook_id: response.data.webhook_id,
                resource_id: response.data.webhook_id,
                expiration: response.data.expiration,
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.renewWebhookSync(webhookId);
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.renewWebhookSync(webhookId);
    }
  },

  // Delete calendar webhook with automatic backend selection
  async deleteWebhookSync(webhookId: string): Promise<{
    ok: boolean;
    error?: string;
  }> {
    try {
      // Try Python backend first if enabled
      if (features.isPythonBackendEnabled()) {
        const isAvailable = await this.isPythonBackendAvailable();
        if (isAvailable) {
          const response = await pythonBackendAPI.deleteCalendarWebhook(webhookId);
          if (response.success) {
            return { ok: true };
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.deleteWebhookSync(webhookId);
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.deleteWebhookSync(webhookId);
    }
  },

  // Get calendar webhook status with automatic backend selection
  async getWebhookStatus(webhookId: string): Promise<{
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
          const response = await pythonBackendAPI.getCalendarWebhookStatus(webhookId);
          if (response.success && response.data) {
            return {
              ok: true,
              webhook_id: response.data.webhook_id,
              resource_id: response.data.webhook_id,
              expiration: response.data.expiration,
            };
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getWebhookStatus(webhookId);
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.getWebhookStatus(webhookId);
    }
  },

  // Get all calendar webhooks with automatic backend selection
  async getAllWebhooks(): Promise<{
    ok: boolean;
    webhooks?: Array<{
      webhook_id: string;
      resource_id: string;
      expiration: number;
    }>;
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
            const response = await pythonBackendAPI.getAllCalendarWebhooks({
              user_id: session.user.id,
              calendar_id: 'primary'
            });
            
            if (response.success && response.data) {
              return {
                ok: true,
                webhooks: response.data.webhooks.map(webhook => ({
                  webhook_id: webhook.webhook_id,
                  resource_id: webhook.webhook_id,
                  expiration: webhook.expiration,
                })),
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.getAllWebhooks();
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.getAllWebhooks();
    }
  },

  // Sync calendar events with automatic backend selection
  async syncCalendarEvents(): Promise<{
    ok: boolean;
    synced_count?: number;
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
            const response = await pythonBackendAPI.syncCalendarEvents({
              user_id: session.user.id,
              calendar_id: 'primary'
            });
            
            if (response.success && response.data) {
              return {
                ok: true,
                synced_count: response.data.synced_count,
              };
            }
          }
        }
      }

      // Fall back to Supabase
      return await supabaseCalendarService.syncCalendarEvents();
    } catch (error) {
      // Silently fall back to Supabase
      return await supabaseCalendarService.syncCalendarEvents();
    }
  },
};
