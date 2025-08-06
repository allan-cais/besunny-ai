import { useEffect, useCallback, useRef } from 'react';
import { adaptiveSyncStrategy, UserActivityState, SyncResult } from '../lib/adaptive-sync-strategy';
import { useAuth } from '../providers/AuthProvider';

export interface UseAdaptiveSyncOptions {
  enabled?: boolean;
  onSyncComplete?: (results: SyncResult[]) => void;
  onError?: (error: Error) => void;
  trackActivity?: boolean;
}

export interface UseAdaptiveSyncReturn {
  recordActivity: (activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general') => void;
  triggerSync: (service?: 'calendar' | 'drive' | 'gmail' | 'attendee') => Promise<void>;
  userState: UserActivityState | null;
  isInitialized: boolean;
  stats: { activeUsers: number; totalUsers: number; averageInterval: number };
}

export function useAdaptiveSync(options: UseAdaptiveSyncOptions = {}): UseAdaptiveSyncReturn {
  const {
    enabled = true,
    onSyncComplete,
    onError,
    trackActivity = true,
  } = options;

  const { user } = useAuth();
  const isInitialized = useRef(false);
  const activityTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize adaptive sync when user is authenticated
  useEffect(() => {
    if (!enabled || !user?.id) {
      return;
    }

    const initializeSync = async () => {
      try {
        await adaptiveSyncStrategy.initializeUser(user.id);
        isInitialized.current = true;
        
        // Record initial app load activity
        if (trackActivity) {
          adaptiveSyncStrategy.recordActivity(user.id, 'app_load');
        }
      } catch (error) {
        console.error('Failed to initialize adaptive sync:', error);
        if (onError) {
          onError(error instanceof Error ? error : new Error('Failed to initialize adaptive sync'));
        }
      }
    };

    initializeSync();

    // Cleanup when user changes or component unmounts
    return () => {
      if (user?.id) {
        adaptiveSyncStrategy.stopUser(user.id);
        isInitialized.current = false;
      }
    };
  }, [enabled, user?.id, trackActivity, onError]);

  // Track user activity automatically
  useEffect(() => {
    if (!enabled || !user?.id || !trackActivity || !isInitialized.current) {
      return;
    }

    const handleUserActivity = () => {
      adaptiveSyncStrategy.recordActivity(user.id, 'general');
    };

    // Track various user activities
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, handleUserActivity, { passive: true });
    });

    // Clear activity timeout on page visibility change
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        adaptiveSyncStrategy.recordActivity(user.id, 'general');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserActivity);
      });
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [enabled, user?.id, trackActivity]);

  // Record activity manually
  const recordActivity = useCallback((activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general') => {
    if (!user?.id || !isInitialized.current) {
      return;
    }

    adaptiveSyncStrategy.recordActivity(user.id, activityType);
  }, [user?.id]);

  // Trigger manual sync
  const triggerSync = useCallback(async (service?: 'calendar' | 'drive' | 'gmail' | 'attendee') => {
    if (!user?.id || !isInitialized.current) {
      return;
    }

    try {
      if (service) {
        // Trigger specific service sync
        switch (service) {
          case 'calendar':
            await adaptiveSyncStrategy['syncCalendar'](user.id);
            break;
          case 'drive':
            await adaptiveSyncStrategy['syncDrive'](user.id);
            break;
          case 'gmail':
            await adaptiveSyncStrategy['syncGmail'](user.id);
            break;
          case 'attendee':
            await adaptiveSyncStrategy['syncAttendee'](user.id);
            break;
        }
      } else {
        // Trigger full sync
        await adaptiveSyncStrategy['performBackgroundSync'](user.id);
      }
    } catch (error) {
      console.error('Manual sync failed:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('Manual sync failed'));
      }
    }
  }, [user?.id, onError]);

  // Get current user state
  const userState = user?.id ? adaptiveSyncStrategy.getUserState(user.id) : null;

  // Get sync statistics
  const stats = adaptiveSyncStrategy.getStats();

  return {
    recordActivity,
    triggerSync,
    userState,
    isInitialized: isInitialized.current,
    stats,
  };
}

// Specialized hooks for specific activities
export function useCalendarSync() {
  const { recordActivity, triggerSync, userState } = useAdaptiveSync();

  const viewCalendar = useCallback(() => {
    recordActivity('calendar_view');
  }, [recordActivity]);

  const createMeeting = useCallback(() => {
    recordActivity('meeting_create');
  }, [recordActivity]);

  const syncCalendar = useCallback(() => {
    return triggerSync('calendar');
  }, [triggerSync]);

  return {
    viewCalendar,
    createMeeting,
    syncCalendar,
    userState,
  };
}

export function useDriveSync() {
  const { recordActivity, triggerSync, userState } = useAdaptiveSync();

  const syncDrive = useCallback(() => {
    return triggerSync('drive');
  }, [triggerSync]);

  return {
    syncDrive,
    userState,
  };
}

export function useGmailSync() {
  const { recordActivity, triggerSync, userState } = useAdaptiveSync();

  const syncGmail = useCallback(() => {
    return triggerSync('gmail');
  }, [triggerSync]);

  return {
    syncGmail,
    userState,
  };
}

export function useAttendeeSync() {
  const { recordActivity, triggerSync, userState } = useAdaptiveSync();

  const syncAttendee = useCallback(() => {
    return triggerSync('attendee');
  }, [triggerSync]);

  return {
    syncAttendee,
    userState,
  };
} 