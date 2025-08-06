import { supabase } from './supabase';
import { calendarService } from './calendar';

export interface SyncStrategy {
  // Immediate: When user interacts with your app
  onAppLoad: 'sync immediately';
  onCalendarView: 'sync immediately'; 
  onMeetingCreate: 'sync after 2 seconds';
  
  // Fast: When user is actively using the app
  activeUser: 'sync every 30 seconds for 5 minutes after activity';
  
  // Normal: Background maintenance
  backgroundSync: 'sync every 5-10 minutes using sync tokens';
  
  // Smart: Adaptive based on change frequency
  adaptiveInterval: 'speed up when changes detected, slow down when quiet';
}

export interface UserActivityState {
  userId: string;
  lastActivity: Date;
  isActive: boolean;
  activityCount: number;
  lastSyncTime: Date;
  changeFrequency: 'high' | 'medium' | 'low';
  syncInterval: number; // in milliseconds
}

export interface SyncResult {
  success: boolean;
  type: 'calendar' | 'drive' | 'gmail' | 'attendee';
  processed: number;
  created: number;
  updated: number;
  deleted: number;
  skipped: boolean;
  error?: string;
  nextSyncIn?: number; // milliseconds until next sync
}

class AdaptiveSyncStrategy {
  private userStates = new Map<string, UserActivityState>();
  private syncIntervals = new Map<string, NodeJS.Timeout>();
  private activityTimeouts = new Map<string, NodeJS.Timeout>();
  
  // Sync intervals in milliseconds
  private readonly INTERVALS = {
    IMMEDIATE: 0,
    FAST: 30 * 1000, // 30 seconds
    NORMAL: 5 * 60 * 1000, // 5 minutes
    SLOW: 10 * 60 * 1000, // 10 minutes
    BACKGROUND: 15 * 60 * 1000, // 15 minutes
  };

  // Activity tracking
  private readonly ACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutes
  private readonly MAX_ACTIVITY_COUNT = 10;

  /**
   * Initialize sync strategy for a user
   */
  async initializeUser(userId: string): Promise<void> {
    if (this.userStates.has(userId)) {
      return; // Already initialized
    }

    const initialState: UserActivityState = {
      userId,
      lastActivity: new Date(),
      isActive: false,
      activityCount: 0,
      lastSyncTime: new Date(),
      changeFrequency: 'low',
      syncInterval: this.INTERVALS.NORMAL,
    };

    this.userStates.set(userId, initialState);
    
    // Start background sync
    this.startBackgroundSync(userId);
    
    console.log(`Adaptive sync initialized for user ${userId}`);
  }

  /**
   * Record user activity and adjust sync strategy
   */
  recordActivity(userId: string, activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general'): void {
    const state = this.userStates.get(userId);
    if (!state) {
      console.warn(`No sync state found for user ${userId}`);
      return;
    }

    const now = new Date();
    state.lastActivity = now;
    state.activityCount = Math.min(state.activityCount + 1, this.MAX_ACTIVITY_COUNT);

    // Clear existing activity timeout
    if (this.activityTimeouts.has(userId)) {
      clearTimeout(this.activityTimeouts.get(userId)!);
    }

    // Set activity timeout
    this.activityTimeouts.set(userId, setTimeout(() => {
      this.setUserInactive(userId);
    }, this.ACTIVITY_TIMEOUT));

    // Handle immediate sync triggers
    switch (activityType) {
      case 'app_load':
        this.triggerImmediateSync(userId, 'calendar');
        break;
      case 'calendar_view':
        this.triggerImmediateSync(userId, 'calendar');
        break;
      case 'meeting_create':
        // Delay sync by 2 seconds for meeting creation
        setTimeout(() => {
          this.triggerImmediateSync(userId, 'calendar');
        }, 2000);
        break;
      case 'general':
        this.adjustSyncStrategy(userId);
        break;
    }

    console.log(`Activity recorded for user ${userId}: ${activityType}`);
  }

  /**
   * Trigger immediate sync for a specific service
   */
  private async triggerImmediateSync(userId: string, service: 'calendar' | 'drive' | 'gmail' | 'attendee'): Promise<void> {
    console.log(`Triggering immediate sync for user ${userId}, service: ${service}`);
    
    try {
      switch (service) {
        case 'calendar':
          await this.syncCalendar(userId);
          break;
        case 'drive':
          await this.syncDrive(userId);
          break;
        case 'gmail':
          await this.syncGmail(userId);
          break;
        case 'attendee':
          await this.syncAttendee(userId);
          break;
      }
    } catch (error) {
      console.error(`Immediate sync failed for user ${userId}, service ${service}:`, error);
    }
  }

  /**
   * Adjust sync strategy based on user activity and change frequency
   */
  private adjustSyncStrategy(userId: string): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    const now = new Date();
    const timeSinceLastActivity = now.getTime() - state.lastActivity.getTime();
    const timeSinceLastSync = now.getTime() - state.lastSyncTime.getTime();

    // Determine if user is active
    const isActive = timeSinceLastActivity < this.ACTIVITY_TIMEOUT && state.activityCount > 0;

    // Adjust sync interval based on activity and change frequency
    let newInterval = this.INTERVALS.NORMAL;

    if (isActive) {
      // Active user: faster sync
      newInterval = this.INTERVALS.FAST;
    } else if (state.changeFrequency === 'high') {
      // High change frequency: faster sync
      newInterval = this.INTERVALS.NORMAL;
    } else if (state.changeFrequency === 'low' && timeSinceLastSync > this.INTERVALS.SLOW) {
      // Low change frequency and no recent changes: slower sync
      newInterval = this.INTERVALS.SLOW;
    }

    // Update state
    state.isActive = isActive;
    state.syncInterval = newInterval;

    // Restart sync interval with new timing
    this.restartSyncInterval(userId, newInterval);

    console.log(`Sync strategy adjusted for user ${userId}: interval=${newInterval}ms, active=${isActive}, frequency=${state.changeFrequency}`);
  }

  /**
   * Set user as inactive and adjust sync strategy
   */
  private setUserInactive(userId: string): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    state.isActive = false;
    state.activityCount = 0;
    this.adjustSyncStrategy(userId);

    console.log(`User ${userId} marked as inactive`);
  }

  /**
   * Start background sync for a user
   */
  private startBackgroundSync(userId: string): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    const interval = this.INTERVALS.BACKGROUND;
    this.restartSyncInterval(userId, interval);

    console.log(`Background sync started for user ${userId} with ${interval}ms interval`);
  }

  /**
   * Restart sync interval with new timing
   */
  private restartSyncInterval(userId: string, interval: number): void {
    // Clear existing interval
    if (this.syncIntervals.has(userId)) {
      clearInterval(this.syncIntervals.get(userId)!);
    }

    // Set new interval
    this.syncIntervals.set(userId, setInterval(async () => {
      await this.performBackgroundSync(userId);
    }, interval));
  }

  /**
   * Perform background sync for all services
   */
  private async performBackgroundSync(userId: string): Promise<void> {
    const state = this.userStates.get(userId);
    if (!state) return;

    console.log(`Performing background sync for user ${userId}`);

    try {
      // Sync all services
      const results = await Promise.allSettled([
        this.syncCalendar(userId),
        this.syncDrive(userId),
        this.syncGmail(userId),
        this.syncAttendee(userId),
      ]);

      // Update change frequency based on results
      const changes = results.filter(result => 
        result.status === 'fulfilled' && 
        result.value && 
        (result.value.created > 0 || result.value.updated > 0 || result.value.deleted > 0)
      ).length;

      this.updateChangeFrequency(userId, changes);
      state.lastSyncTime = new Date();

      console.log(`Background sync completed for user ${userId}: ${changes} services had changes`);
    } catch (error) {
      console.error(`Background sync failed for user ${userId}:`, error);
    }
  }

  /**
   * Update change frequency based on recent activity
   */
  private updateChangeFrequency(userId: string, changeCount: number): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    // Simple frequency calculation based on change count
    if (changeCount >= 3) {
      state.changeFrequency = 'high';
    } else if (changeCount >= 1) {
      state.changeFrequency = 'medium';
    } else {
      state.changeFrequency = 'low';
    }
  }

  /**
   * Sync calendar events
   */
  private async syncCalendar(userId: string): Promise<SyncResult> {
    try {
      // Use existing calendar service with sync tokens
      const result = await calendarService.performIncrementalSync(userId);
      
      return {
        success: result.success,
        type: 'calendar',
        processed: 0, // Calendar service doesn't return these metrics
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: !result.success,
        error: result.error,
      };
    } catch (error) {
      return {
        success: false,
        type: 'calendar',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Sync drive files
   */
  private async syncDrive(userId: string): Promise<SyncResult> {
    try {
      // Get user's drive files that need syncing
      const { data: files } = await supabase
        .from('drive_file_watches')
        .select('file_id, document_id')
        .eq('is_active', true);

      if (!files || files.length === 0) {
        return {
          success: true,
          type: 'drive',
          processed: 0,
          created: 0,
          updated: 0,
          deleted: 0,
          skipped: true,
        };
      }

      // For now, just mark as processed since the actual polling is handled by edge functions
      return {
        success: true,
        type: 'drive',
        processed: files.length,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
      };
    } catch (error) {
      return {
        success: false,
        type: 'drive',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Sync Gmail messages
   */
  private async syncGmail(userId: string): Promise<SyncResult> {
    try {
      // Get user's Gmail watch status
      const { data: gmailWatch } = await supabase
        .from('gmail_watches')
        .select('user_email')
        .eq('is_active', true)
        .single();

      if (!gmailWatch) {
        return {
          success: true,
          type: 'gmail',
          processed: 0,
          created: 0,
          updated: 0,
          deleted: 0,
          skipped: true,
        };
      }

      // For now, just mark as processed since the actual polling is handled by edge functions
      return {
        success: true,
        type: 'gmail',
        processed: 1,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
      };
    } catch (error) {
      return {
        success: false,
        type: 'gmail',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Sync attendee meetings
   */
  private async syncAttendee(userId: string): Promise<SyncResult> {
    try {
      // Get meetings that need polling
      const { data: meetings } = await supabase
        .from('meetings')
        .select('id, title, bot_status')
        .eq('user_id', userId)
        .eq('polling_enabled', true)
        .in('bot_status', ['bot_scheduled', 'bot_joined', 'transcribing']);

      if (!meetings || meetings.length === 0) {
        return {
          success: true,
          type: 'attendee',
          processed: 0,
          created: 0,
          updated: 0,
          deleted: 0,
          skipped: true,
        };
      }

      let processed = 0;
      let created = 0;
      let updated = 0;
      let deleted = 0;

      // Poll each meeting
      for (const meeting of meetings) {
        try {
          // Call attendee polling service
          const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/attendee-service/poll-meeting`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
            },
            body: JSON.stringify({ meetingId: meeting.id }),
          });

          if (response.ok) {
            processed++;
            // Note: Attendee service doesn't return detailed metrics
          }
        } catch (error) {
          console.error(`Error polling meeting ${meeting.id}:`, error);
        }
      }

      return {
        success: true,
        type: 'attendee',
        processed,
        created,
        updated,
        deleted,
        skipped: false,
      };
    } catch (error) {
      return {
        success: false,
        type: 'attendee',
        processed: 0,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Stop sync for a user
   */
  stopUser(userId: string): void {
    // Clear intervals
    if (this.syncIntervals.has(userId)) {
      clearInterval(this.syncIntervals.get(userId)!);
      this.syncIntervals.delete(userId);
    }

    // Clear activity timeout
    if (this.activityTimeouts.has(userId)) {
      clearTimeout(this.activityTimeouts.get(userId)!);
      this.activityTimeouts.delete(userId);
    }

    // Remove state
    this.userStates.delete(userId);

    console.log(`Sync stopped for user ${userId}`);
  }

  /**
   * Get current sync state for a user
   */
  getUserState(userId: string): UserActivityState | null {
    return this.userStates.get(userId) || null;
  }

  /**
   * Get sync statistics
   */
  getStats(): { activeUsers: number; totalUsers: number; averageInterval: number } {
    const states = Array.from(this.userStates.values());
    const activeUsers = states.filter(s => s.isActive).length;
    const totalUsers = states.length;
    const averageInterval = states.length > 0 
      ? states.reduce((sum, s) => sum + s.syncInterval, 0) / states.length 
      : 0;

    return { activeUsers, totalUsers, averageInterval };
  }
}

// Export singleton instance
export const adaptiveSyncStrategy = new AdaptiveSyncStrategy(); 