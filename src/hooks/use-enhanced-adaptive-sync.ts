import { useEffect, useCallback, useRef, useState } from 'react';
import { enhancedAdaptiveSyncStrategy, EnhancedUserActivityState, VirtualEmailActivity } from '../lib/enhanced-adaptive-sync-strategy';
import { useAuth } from '../providers/AuthProvider';

export interface UseEnhancedAdaptiveSyncOptions {
  enabled?: boolean;
  onSyncComplete?: (results: any[]) => void;
  onError?: (error: Error) => void;
  trackActivity?: boolean;
  trackVirtualEmailActivity?: boolean;
}

export interface UseEnhancedAdaptiveSyncReturn {
  recordActivity: (activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general' | 'virtual_email_detected') => void;
  triggerSync: (service?: 'calendar' | 'drive' | 'gmail' | 'attendee') => Promise<void>;
  recordVirtualEmailDetection: () => void;
  userState: EnhancedUserActivityState | null;
  virtualEmailActivity: VirtualEmailActivity | null;
  isInitialized: boolean;
  stats: { 
    activeUsers: number; 
    totalUsers: number; 
    averageInterval: number;
    usersWithVirtualEmailActivity: number;
    totalVirtualEmailDetections: number;
  };
}

export function useEnhancedAdaptiveSync(options: UseEnhancedAdaptiveSyncOptions = {}): UseEnhancedAdaptiveSyncReturn {
  const {
    enabled = true,
    onSyncComplete,
    onError,
    trackActivity = true,
    trackVirtualEmailActivity = true,
  } = options;

  const { user } = useAuth();
  const isInitialized = useRef(false);
  const activityTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [virtualEmailActivity, setVirtualEmailActivity] = useState<VirtualEmailActivity | null>(null);

  // Initialize enhanced adaptive sync when user is authenticated
  useEffect(() => {
    if (!enabled || !user?.id) {
      return;
    }

    const initializeSync = async () => {
      try {
        await enhancedAdaptiveSyncStrategy.initializeUser(user.id);
        isInitialized.current = true;
        
        // Get initial virtual email activity
        if (trackVirtualEmailActivity) {
          const activity = await enhancedAdaptiveSyncStrategy.getVirtualEmailActivityForUser(user.id);
          setVirtualEmailActivity(activity);
        }
        
        // Record initial app load activity
        if (trackActivity) {
          enhancedAdaptiveSyncStrategy.recordActivity(user.id, 'app_load');
        }
      } catch (error) {
        console.error('Failed to initialize enhanced adaptive sync:', error);
        if (onError) {
          onError(error instanceof Error ? error : new Error('Failed to initialize enhanced adaptive sync'));
        }
      }
    };

    initializeSync();

    // Cleanup when user changes or component unmounts
    return () => {
      if (user?.id) {
        enhancedAdaptiveSyncStrategy.stopUser(user.id);
        isInitialized.current = false;
      }
    };
  }, [enabled, user?.id, trackActivity, trackVirtualEmailActivity, onError]);

  // Track user activity automatically
  useEffect(() => {
    if (!enabled || !user?.id || !trackActivity || !isInitialized.current) {
      return;
    }

    const handleUserActivity = () => {
      enhancedAdaptiveSyncStrategy.recordActivity(user.id, 'general');
    };

    // Track various user activities
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, handleUserActivity, { passive: true });
    });

    // Clear activity timeout on page visibility change
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        enhancedAdaptiveSyncStrategy.recordActivity(user.id, 'general');
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

  // Update virtual email activity periodically
  useEffect(() => {
    if (!enabled || !user?.id || !trackVirtualEmailActivity || !isInitialized.current) {
      return;
    }

    const updateVirtualEmailActivity = async () => {
      try {
        const activity = await enhancedAdaptiveSyncStrategy.getVirtualEmailActivityForUser(user.id);
        setVirtualEmailActivity(activity);
      } catch (error) {
        console.error('Error updating virtual email activity:', error);
      }
    };

    // Update immediately
    updateVirtualEmailActivity();

    // Update every 5 minutes
    const interval = setInterval(updateVirtualEmailActivity, 5 * 60 * 1000);

    return () => {
      clearInterval(interval);
    };
  }, [enabled, user?.id, trackVirtualEmailActivity]);

  // Record activity manually
  const recordActivity = useCallback((activityType: 'app_load' | 'calendar_view' | 'meeting_create' | 'general' | 'virtual_email_detected') => {
    if (!user?.id || !isInitialized.current) {
      return;
    }

    enhancedAdaptiveSyncStrategy.recordActivity(user.id, activityType);
  }, [user?.id]);

  // Record virtual email detection specifically
  const recordVirtualEmailDetection = useCallback(() => {
    if (!user?.id || !isInitialized.current) {
      return;
    }

    enhancedAdaptiveSyncStrategy.recordVirtualEmailDetection(user.id);
    
    // Update virtual email activity immediately
    enhancedAdaptiveSyncStrategy.getVirtualEmailActivityForUser(user.id).then(activity => {
      setVirtualEmailActivity(activity);
    });
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
            await enhancedAdaptiveSyncStrategy['syncCalendar'](user.id);
            break;
          case 'drive':
            await enhancedAdaptiveSyncStrategy['syncDrive'](user.id);
            break;
          case 'gmail':
            await enhancedAdaptiveSyncStrategy['syncGmail'](user.id);
            break;
          case 'attendee':
            await enhancedAdaptiveSyncStrategy['syncAttendee'](user.id);
            break;
        }
      } else {
        // Trigger full sync
        await enhancedAdaptiveSyncStrategy['performBackgroundSync'](user.id);
      }
    } catch (error) {
      console.error('Manual sync failed:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('Manual sync failed'));
      }
    }
  }, [user?.id, onError]);

  // Get current user state
  const userState = user?.id ? enhancedAdaptiveSyncStrategy.getUserState(user.id) : null;

  // Get enhanced sync statistics
  const stats = enhancedAdaptiveSyncStrategy.getStats();

  return {
    recordActivity,
    triggerSync,
    recordVirtualEmailDetection,
    userState,
    virtualEmailActivity,
    isInitialized: isInitialized.current,
    stats,
  };
}

// Specialized hooks for specific activities
export function useEnhancedCalendarSync() {
  const { recordActivity, triggerSync, userState, virtualEmailActivity } = useEnhancedAdaptiveSync();

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
    virtualEmailActivity,
  };
}

export function useEnhancedGmailSync() {
  const { recordActivity, triggerSync, userState, virtualEmailActivity, recordVirtualEmailDetection } = useEnhancedAdaptiveSync();

  const syncGmail = useCallback(() => {
    return triggerSync('gmail');
  }, [triggerSync]);

  return {
    syncGmail,
    recordVirtualEmailDetection,
    userState,
    virtualEmailActivity,
  };
}

export function useEnhancedVirtualEmailSync() {
  const { recordVirtualEmailDetection, userState, virtualEmailActivity, stats } = useEnhancedAdaptiveSync({
    trackVirtualEmailActivity: true,
  });

  return {
    recordVirtualEmailDetection,
    userState,
    virtualEmailActivity,
    stats,
  };
} 