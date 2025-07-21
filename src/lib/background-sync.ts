import { supabase } from './supabase';
import { calendarService } from './calendar';

class BackgroundSyncService {
  private syncInterval: NodeJS.Timeout | null = null;
  private isRunning = false;

  async initialize() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    console.log('Background sync service initialized');
    
    // Check for users who need calendar sync setup
    await this.checkAndSetupCalendarSync();
    
    // Set up periodic checks
    this.syncInterval = setInterval(async () => {
      await this.checkAndSetupCalendarSync();
      await this.renewExpiringWebhooks();
    }, 5 * 60 * 1000); // Check every 5 minutes
  }

  async stop() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
    this.isRunning = false;
    console.log('Background sync service stopped');
  }

  private async checkAndSetupCalendarSync() {
    try {
      // Find users with Google credentials but no active webhook
      const { data: users, error } = await supabase
        .from('google_credentials')
        .select('user_id')
        .not('user_id', 'in', `(
          SELECT user_id FROM calendar_webhooks WHERE is_active = true
        )`);

      if (error) {
        console.error('Error checking for users needing calendar sync:', error);
        return;
      }

      if (!users || users.length === 0) {
        return;
      }

      console.log(`Found ${users.length} users needing calendar sync setup`);

      // Set up calendar sync for each user
      for (const user of users) {
        try {
          await calendarService.initializeCalendarSync(user.user_id);
          console.log(`Calendar sync set up for user: ${user.user_id}`);
        } catch (error) {
          console.error(`Failed to set up calendar sync for user ${user.user_id}:`, error);
        }
      }
    } catch (error) {
      console.error('Error in checkAndSetupCalendarSync:', error);
    }
  }

  private async renewExpiringWebhooks() {
    try {
      // Find webhooks expiring in the next 24 hours
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);

      const { data: expiringWebhooks, error } = await supabase
        .from('calendar_webhooks')
        .select('user_id, webhook_id')
        .eq('is_active', true)
        .lt('expiration_time', tomorrow.toISOString());

      if (error) {
        console.error('Error checking for expiring webhooks:', error);
        return;
      }

      if (!expiringWebhooks || expiringWebhooks.length === 0) {
        return;
      }

      console.log(`Found ${expiringWebhooks.length} webhooks expiring soon`);

      // Renew each expiring webhook
      for (const webhook of expiringWebhooks) {
        try {
          await calendarService.renewWatch(webhook.user_id);
          console.log(`Webhook renewed for user: ${webhook.user_id}`);
        } catch (error) {
          console.error(`Failed to renew webhook for user ${webhook.user_id}:`, error);
        }
      }
    } catch (error) {
      console.error('Error in renewExpiringWebhooks:', error);
    }
  }

  // Manual sync for a specific user
  async syncUserCalendar(userId: string) {
    try {
      await calendarService.initializeCalendarSync(userId);
      console.log(`Manual calendar sync completed for user: ${userId}`);
    } catch (error) {
      console.error(`Manual calendar sync failed for user ${userId}:`, error);
      throw error;
    }
  }
}

export const backgroundSyncService = new BackgroundSyncService(); 