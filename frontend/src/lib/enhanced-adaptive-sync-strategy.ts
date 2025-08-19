import { supabase } from './supabase';
import { calendarService } from './calendar';

export interface EnhancedSyncStrategy {
  // Immediate: When user interacts with your app
  onAppLoad: 'sync immediately';
  onCalendarView: 'sync immediately'; 
  onMeetingCreate: 'sync after 2 seconds';
  onVirtualEmailDetected: 'sync immediately';
  
  // Fast: When user is actively using the app
  activeUser: 'sync every 30 seconds for 5 minutes after activity';
  
  // Normal: Background maintenance
  backgroundSync: 'sync every 5-10 minutes using sync tokens';
  
  // Smart: Adaptive based on change frequency and virtual email activity
  adaptiveInterval: 'speed up when changes detected or virtual emails active, slow down when quiet';
}

export interface VirtualEmailActivity {
  userId: string;
  virtualEmail: string;
  lastDetected: Date;
  detectionCount: number;
  recentActivity: boolean;
  autoScheduledMeetings: number;
}

export interface EnhancedUserActivityState {
  userId: string;
  lastActivity: Date;
  isActive: boolean;
  activityCount: number;
  lastSyncTime: Date;
  changeFrequency: 'high' | 'medium' | 'low';
  syncInterval: number; // in milliseconds
  virtualEmailActivity: VirtualEmailActivity | null;
  hasVirtualEmailAttendees: boolean;
  lastVirtualEmailDetection: Date | null;
}

export interface EnhancedSyncResult {
  success: boolean;
  type: 'calendar' | 'drive' | 'gmail' | 'attendee';
  processed: number;
  created: number;
  updated: number;
  deleted: number;
  skipped: boolean;
  virtualEmailsDetected: number;
  autoScheduledMeetings: number;
  error?: string;
  nextSyncIn?: number; // milliseconds until next sync
}

class EnhancedAdaptiveSyncStrategy {
  private userStates = new Map<string, EnhancedUserActivityState>();
  private syncIntervals = new Map<string, NodeJS.Timeout>();
  private activityTimeouts = new Map<string, NodeJS.Timeout>();
  private virtualEmailTimeouts = new Map<string, NodeJS.Timeout>();
  
  // Sync intervals in milliseconds
  private readonly INTERVALS = {
    IMMEDIATE: 0,
    FAST: 30 * 1000, // 30 seconds
    NORMAL: 5 * 60 * 1000, // 5 minutes
    SLOW: 10 * 60 * 1000, // 10 minutes
    BACKGROUND: 15 * 60 * 1000, // 15 minutes
    VIRTUAL_EMAIL_ACTIVE: 60 * 1000, // 1 minute when virtual emails are active
  };

  // Activity tracking
  private readonly ACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutes
  private readonly VIRTUAL_EMAIL_ACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes
  private readonly MAX_ACTIVITY_COUNT = 10;

  /**
   * Initialize enhanced sync strategy for a user
   */
  async initializeUser(userId: string): Promise<void> {
    if (this.userStates.has(userId)) {
      return; // Already initialized
    }

    // Get user's virtual email info
    const virtualEmailActivity = await this.getVirtualEmailActivity(userId);

    const initialState: EnhancedUserActivityState = {
      userId,
      lastActivity: new Date(),
      isActive: false,
      activityCount: 0,
      lastSyncTime: new Date(),
      changeFrequency: 'low',
      syncInterval: this.INTERVALS.NORMAL,
      virtualEmailActivity,
      hasVirtualEmailAttendees: false,
      lastVirtualEmailDetection: null,
    };

    this.userStates.set(userId, initialState);
    
    // Start background sync
    this.startBackgroundSync(userId);
    
  }

  /**
   * Get virtual email activity for a user
   */
  private async getVirtualEmailActivity(userId: string): Promise<VirtualEmailActivity | null> {
    try {
      // Get user's username and virtual email
      const { data: user } = await supabase
        .from('users')
        .select('username')
        .eq('id', userId)
        .single();

      if (!user?.username) {
        return null;
      }

      const virtualEmail = `ai+${user.username}@besunny.ai`;

      // Get recent virtual email detections
      const { data: recentDetections } = await supabase
        .from('virtual_email_detections')
        .select('detected_at')
        .eq('user_id', userId)
        .gte('detected_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
        .order('detected_at', { ascending: false });

      // Get auto-scheduled meetings count
      const { data: autoScheduledMeetings } = await supabase
        .from('meetings')
        .select('id')
        .eq('user_id', userId)
        .eq('auto_scheduled_via_email', true)
        .gte('created_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString());

      const lastDetected = recentDetections?.[0]?.detected_at 
        ? new Date(recentDetections[0].detected_at)
        : null;

      const recentActivity = lastDetected && 
        (Date.now() - lastDetected.getTime()) < this.VIRTUAL_EMAIL_ACTIVITY_TIMEOUT;

      return {
        userId,
        virtualEmail,
        lastDetected: lastDetected || new Date(0),
        detectionCount: recentDetections?.length || 0,
        recentActivity,
        autoScheduledMeetings: autoScheduledMeetings?.length || 0,
      };
    } catch (error) {
              // Error getting virtual email activity
      return null;
    }
  }

  /**
   * Record user activity and adjust sync strategy
   */
  recordActivity(userId: string, activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general' | 'virtual_email_detected'): void {
    const state = this.userStates.get(userId);
    if (!state) {
      return;
    }

    const now = new Date();
    state.lastActivity = now;
    state.activityCount = Math.min(state.activityCount + 1, this.MAX_ACTIVITY_COUNT);

    // Handle virtual email detection
    if (activityType === 'virtual_email_detected') {
      state.lastVirtualEmailDetection = now;
      if (state.virtualEmailActivity) {
        state.virtualEmailActivity.lastDetected = now;
        state.virtualEmailActivity.detectionCount++;
        state.virtualEmailActivity.recentActivity = true;
      }
      
      // Set virtual email activity timeout
      this.setVirtualEmailActivityTimeout(userId);
    }

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
        this.triggerImmediateSync(userId, 'gmail');
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
      case 'virtual_email_detected':
        this.triggerImmediateSync(userId, 'gmail');
        this.triggerImmediateSync(userId, 'calendar');
        break;
      case 'general':
        this.adjustSyncStrategy(userId);
        break;
    }

  }

  /**
   * Set virtual email activity timeout
   */
  private setVirtualEmailActivityTimeout(userId: string): void {
    // Clear existing virtual email timeout
    if (this.virtualEmailTimeouts.has(userId)) {
      clearTimeout(this.virtualEmailTimeouts.get(userId)!);
    }

    // Set new timeout
    this.virtualEmailTimeouts.set(userId, setTimeout(() => {
      this.setVirtualEmailInactive(userId);
    }, this.VIRTUAL_EMAIL_ACTIVITY_TIMEOUT));
  }

  /**
   * Set virtual email as inactive
   */
  private setVirtualEmailInactive(userId: string): void {
    const state = this.userStates.get(userId);
    if (state?.virtualEmailActivity) {
      state.virtualEmailActivity.recentActivity = false;
      this.adjustSyncStrategy(userId);
    }
  }

  /**
   * Trigger immediate sync for a specific service
   */
  private async triggerImmediateSync(userId: string, service: 'calendar' | 'drive' | 'gmail' | 'attendee'): Promise<void> {
    
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
              // Immediate sync failed for user and service
    }
  }

  /**
   * Adjust sync strategy based on user activity and virtual email activity
   */
  private adjustSyncStrategy(userId: string): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    const now = new Date();
    const timeSinceLastActivity = now.getTime() - state.lastActivity.getTime();
    const timeSinceLastSync = now.getTime() - state.lastSyncTime.getTime();

    // Determine if user is active
    const isActive = timeSinceLastActivity < this.ACTIVITY_TIMEOUT && state.activityCount > 0;

    // Check virtual email activity
    const hasVirtualEmailActivity = state.virtualEmailActivity?.recentActivity || false;
    const hasRecentVirtualEmailDetection = state.lastVirtualEmailDetection && 
      (now.getTime() - state.lastVirtualEmailDetection.getTime()) < this.VIRTUAL_EMAIL_ACTIVITY_TIMEOUT;

    // Adjust sync interval based on activity and virtual email activity
    let newInterval = this.INTERVALS.NORMAL;

    if (hasVirtualEmailActivity || hasRecentVirtualEmailDetection) {
      // Virtual email is active - use fastest sync
      newInterval = this.INTERVALS.VIRTUAL_EMAIL_ACTIVE;
    } else if (isActive) {
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

  }

  /**
   * Start background sync for a user
   */
  private startBackgroundSync(userId: string): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    const interval = this.INTERVALS.BACKGROUND;
    this.restartSyncInterval(userId, interval);

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
        (result.value.created > 0 || result.value.updated > 0 || result.value.deleted > 0 || result.value.virtualEmailsDetected > 0)
      ).length;

      this.updateChangeFrequency(userId, changes);
      state.lastSyncTime = new Date();

      // Update virtual email activity
      await this.updateVirtualEmailActivity(userId);

    } catch (error) {
              // Background sync failed for user
    }
  }

  /**
   * Update virtual email activity
   */
  private async updateVirtualEmailActivity(userId: string): Promise<void> {
    try {
      const virtualEmailActivity = await this.getVirtualEmailActivity(userId);
      const state = this.userStates.get(userId);
      
      if (state && virtualEmailActivity) {
        state.virtualEmailActivity = virtualEmailActivity;
        state.hasVirtualEmailAttendees = virtualEmailActivity.autoScheduledMeetings > 0;
      }
    } catch (error) {
              // Error updating virtual email activity
    }
  }

  /**
   * Update change frequency based on recent activity
   */
  private updateChangeFrequency(userId: string, changeCount: number): void {
    const state = this.userStates.get(userId);
    if (!state) return;

    // Consider virtual email activity in frequency calculation
    const virtualEmailActivity = state.virtualEmailActivity?.detectionCount || 0;
    const totalActivity = changeCount + virtualEmailActivity;

    if (totalActivity >= 3) {
      state.changeFrequency = 'high';
    } else if (totalActivity >= 1) {
      state.changeFrequency = 'medium';
    } else {
      state.changeFrequency = 'low';
    }
  }

  /**
   * Enhanced calendar sync with virtual email attendee detection
   */
  private async syncCalendar(userId: string): Promise<EnhancedSyncResult> {
    try {
      // Use existing calendar service with sync tokens
      const result = await calendarService.performIncrementalSync(userId);
      
      // Check for virtual email attendees in recent meetings
      const { data: recentMeetings } = await supabase
        .from('meetings')
        .select('id, auto_scheduled_via_email, virtual_email_attendee')
        .eq('user_id', userId)
        .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

      const virtualEmailMeetings = recentMeetings?.filter(m => m.auto_scheduled_via_email) || [];
      
      return {
        success: result.success,
        type: 'calendar',
        processed: 0, // Calendar service doesn't return these metrics
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: !result.success,
        virtualEmailsDetected: virtualEmailMeetings.length,
        autoScheduledMeetings: virtualEmailMeetings.length,
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
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Enhanced drive sync
   */
  private async syncDrive(userId: string): Promise<EnhancedSyncResult> {
    try {
      // Get user's drive files
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
          virtualEmailsDetected: 0,
          autoScheduledMeetings: 0,
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
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
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
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check if Gmail watches table is accessible
   */
  private async checkGmailWatchesAccess(): Promise<boolean> {
    try {
      const { error } = await supabase
        .from('gmail_watches')
        .select('id')
        .limit(1);
      
      return !error || error.code !== '406';
    } catch (error) {
      return false;
    }
  }

  /**
   * Enhanced Gmail sync with virtual email detection
   */
  private async syncGmail(userId: string): Promise<EnhancedSyncResult> {
    try {
      // Get user's Gmail watch status - filter by user's email to match RLS policy
      const { data: { user } } = await supabase.auth.getUser();
      if (!user?.email) {
        return {
          success: true,
          type: 'gmail',
          processed: 0,
          created: 0,
          updated: 0,
          deleted: 0,
          skipped: true,
          virtualEmailsDetected: 0,
          autoScheduledMeetings: 0,
        };
      }

      const { data: gmailWatch, error: gmailWatchError } = await supabase
        .from('gmail_watches')
        .select('user_email')
        .eq('user_email', user.email)
        .eq('is_active', true)
        .single();

      // Handle RLS access issues gracefully
      if (gmailWatchError) {
        if (gmailWatchError.code === '406' || gmailWatchError.message?.includes('Not Acceptable')) {
          return {
            success: true,
            type: 'gmail',
            processed: 0,
            created: 0,
            updated: 0,
            deleted: 0,
            skipped: true,
            virtualEmailsDetected: 0,
            autoScheduledMeetings: 0,
          };
        }
        throw gmailWatchError;
      }

      if (!gmailWatch) {
        return {
          success: true,
          type: 'gmail',
          processed: 0,
          created: 0,
          updated: 0,
          deleted: 0,
          skipped: true,
          virtualEmailsDetected: 0,
          autoScheduledMeetings: 0,
        };
      }

      // Get recent virtual email detections
      const { data: recentDetections } = await supabase
        .from('virtual_email_detections')
        .select('id, detected_at')
        .eq('user_id', userId)
        .gte('detected_at', new Date(Date.now() - 60 * 60 * 1000).toISOString()); // Last hour

      // Get pending email processing logs
      const { data: pendingEmails } = await supabase
        .from('email_processing_logs')
        .select('id, status')
        .eq('user_id', userId)
        .eq('status', 'pending');

      const virtualEmailsDetected = recentDetections?.length || 0;
      const processed = pendingEmails?.length || 0;

      return {
        success: true,
        type: 'gmail',
        processed,
        created: processed,
        updated: 0,
        deleted: 0,
        skipped: false,
        virtualEmailsDetected,
        autoScheduledMeetings: 0,
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
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Enhanced attendee sync
   */
  private async syncAttendee(userId: string): Promise<EnhancedSyncResult> {
    try {
      // Get meetings that need polling
      const { data: meetings } = await supabase
        .from('meetings')
        .select('id, title, bot_status, auto_scheduled_via_email')
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
          virtualEmailsDetected: 0,
          autoScheduledMeetings: 0,
        };
      }

      const autoScheduledMeetings = meetings.filter(m => m.auto_scheduled_via_email).length;

      // Poll each meeting (simplified implementation)
      let processed = 0;
      for (const meeting of meetings) {
        try {
          // This would normally call the attendee polling service
          // For now, we'll just mark as processed
          processed++;
        } catch (error) {
          // Error polling meeting
        }
      }

      return {
        success: true,
        type: 'attendee',
        processed,
        created: 0,
        updated: 0,
        deleted: 0,
        skipped: false,
        virtualEmailsDetected: 0,
        autoScheduledMeetings,
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
        virtualEmailsDetected: 0,
        autoScheduledMeetings: 0,
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

    // Clear virtual email timeout
    if (this.virtualEmailTimeouts.has(userId)) {
      clearTimeout(this.virtualEmailTimeouts.get(userId)!);
      this.virtualEmailTimeouts.delete(userId);
    }

    // Remove state
    this.userStates.delete(userId);

  }

  /**
   * Get current sync state for a user
   */
  getUserState(userId: string): EnhancedUserActivityState | null {
    return this.userStates.get(userId) || null;
  }

  /**
   * Get enhanced sync statistics
   */
  getStats(): { 
    activeUsers: number; 
    totalUsers: number; 
    averageInterval: number;
    usersWithVirtualEmailActivity: number;
    totalVirtualEmailDetections: number;
  } {
    const states = Array.from(this.userStates.values());
    const activeUsers = states.filter(s => s.isActive).length;
    const totalUsers = states.length;
    const averageInterval = states.length > 0 
      ? states.reduce((sum, s) => sum + s.syncInterval, 0) / states.length 
      : 0;
    
    const usersWithVirtualEmailActivity = states.filter(s => 
      s.virtualEmailActivity?.recentActivity
    ).length;
    
    const totalVirtualEmailDetections = states.reduce((sum, s) => 
      sum + (s.virtualEmailActivity?.detectionCount || 0), 0
    );

    return { 
      activeUsers, 
      totalUsers, 
      averageInterval,
      usersWithVirtualEmailActivity,
      totalVirtualEmailDetections
    };
  }

  /**
   * Record virtual email detection
   */
  recordVirtualEmailDetection(userId: string): void {
    this.recordActivity(userId, 'virtual_email_detected');
  }

  /**
   * Get virtual email activity for a user
   */
  async getVirtualEmailActivityForUser(userId: string): Promise<VirtualEmailActivity | null> {
    return await this.getVirtualEmailActivity(userId);
  }

  /**
   * Trigger manual sync for a specific service or all services
   */
  async triggerSync(userId: string, service?: 'calendar' | 'drive' | 'gmail' | 'attendee'): Promise<EnhancedSyncResult[]> {
    if (!this.userStates.has(userId)) {
      throw new Error(`User ${userId} not initialized for enhanced sync`);
    }

    try {
      if (service) {
        // Trigger specific service sync
        const result = await this[`sync${service.charAt(0).toUpperCase() + service.slice(1)}`](userId);
        return [result];
      } else {
        // Trigger full sync
        const results = await Promise.all([
          this.syncCalendar(userId),
          this.syncDrive(userId),
          this.syncGmail(userId),
          this.syncAttendee(userId),
        ]);
        return results;
      }
    } catch (error) {
              // Manual sync failed for user
      throw error;
    }
  }
}

// Export singleton instance
export const enhancedAdaptiveSyncStrategy = new EnhancedAdaptiveSyncStrategy(); 