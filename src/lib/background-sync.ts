import { supabase } from './supabase';
import { calendarService } from './calendar';

class BackgroundSyncService {
  private syncInterval: NodeJS.Timeout | null = null;
  private isRunning = false;
  private currentUserId: string | null = null;
  private disabled = false;

  async initialize(userId?: string) {
    if (this.isRunning || this.disabled) return;
    
    this.currentUserId = userId || null;
    this.isRunning = true;
    
    // Wait a bit before running the first check to avoid blocking page load
    setTimeout(async () => {
      try {
        await this.checkAndSetupCalendarSync();
      } catch (error) {
        console.error('Background sync initial check failed:', error);
      }
    }, 2000); // Wait 2 seconds
    
    // Set up periodic checks
    this.syncInterval = setInterval(async () => {
      try {
        await this.checkAndSetupCalendarSync();
        await this.renewExpiringWebhooks();
      } catch (error) {
        console.error('Background sync periodic check failed:', error);
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
  }

  async stop() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
    this.isRunning = false;
    this.currentUserId = null;

  }

  private async checkAndSetupCalendarSync() {
    try {
      // Only check for the current user
      if (!this.currentUserId) {
        return;
      }

      // Check if current user has Google credentials
      const { data: credentials, error: credentialsError } = await supabase
        .from('google_credentials')
        .select('user_id')
        .eq('user_id', this.currentUserId)
        .maybeSingle();

      if (credentialsError) {
        console.error('Error checking Google credentials:', credentialsError);
        return;
      }

      if (!credentials) {
        return; // User doesn't have Google credentials
      }

      // Check if user has active webhook
      const { data: webhook, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('user_id')
        .eq('user_id', this.currentUserId)
        .eq('is_active', true)
        .maybeSingle();

      if (webhookError) {
        console.error('Error checking webhook status:', webhookError);
        return;
      }

      // If no active webhook, set up calendar sync
      if (!webhook) {
        try {
          await calendarService.initializeCalendarSync(this.currentUserId);
        } catch (error) {
          console.error('Failed to set up calendar sync:', error);
        }
      }
    } catch (error) {
      console.error('Error in checkAndSetupCalendarSync:', error);
    }
  }

  private async renewExpiringWebhooks() {
    try {
      // Only check for the current user
      if (!this.currentUserId) {
        return;
      }

      // Find webhook expiring in the next 24 hours for current user
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);

      const { data: webhook, error } = await supabase
        .from('calendar_webhooks')
        .select('user_id, webhook_id, expiration_time')
        .eq('user_id', this.currentUserId)
        .eq('is_active', true)
        .lt('expiration_time', tomorrow.toISOString())
        .maybeSingle();

      if (error) {
        console.error('Error checking for expiring webhook:', error);
        return;
      }

      if (!webhook) {
        return; // No expiring webhook
      }

      // Renew the expiring webhook
      try {
        await calendarService.renewWatch(this.currentUserId);
      } catch (error) {
        console.error('Failed to renew webhook:', error);
      }
    } catch (error) {
      console.error('Error in renewExpiringWebhooks:', error);
    }
  }

  // Manual sync for a specific user
  async syncUserCalendar(userId: string) {
    try {
      await calendarService.initializeCalendarSync(userId);
    } catch (error) {
      console.error(`Manual calendar sync failed for user ${userId}:`, error);
      throw error;
    }
  }

  disable() {
    this.disabled = true;
    this.stop();

  }

  // Re-enable method
  enable() {
    this.disabled = false;

  }
}

export const backgroundSyncService = new BackgroundSyncService();

// Disable background sync to prevent blocking
backgroundSyncService.disable(); 