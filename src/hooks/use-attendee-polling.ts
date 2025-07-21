import { useEffect, useRef, useCallback } from 'react';
import { attendeePollingService } from '@/lib/attendee-polling';
import { useAuth } from '@/providers/AuthProvider';

interface UseAttendeePollingOptions {
  enabled?: boolean;
  intervalMs?: number;
  onPollingComplete?: (results: any[]) => void;
  onError?: (error: Error) => void;
}

export const useAttendeePolling = (options: UseAttendeePollingOptions = {}) => {
  const { enabled = true, intervalMs = 30000, onPollingComplete, onError } = options;
  const { user } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  const pollMeetings = useCallback(async () => {
    if (!user?.id || isPollingRef.current) return;

    try {
      isPollingRef.current = true;
      const results = await attendeePollingService.pollAllMeetings();
      onPollingComplete?.(results);
    } catch (error) {
      console.error('Error polling meetings:', error);
      onError?.(error as Error);
    } finally {
      isPollingRef.current = false;
    }
  }, [user?.id, onPollingComplete, onError]);

  const startPolling = useCallback(() => {
    if (!enabled || !user?.id) return;

    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Poll immediately
    pollMeetings();

    // Set up interval for regular polling
    intervalRef.current = setInterval(pollMeetings, intervalMs);
  }, [enabled, user?.id, intervalMs, pollMeetings]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (enabled && user?.id) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [enabled, user?.id, startPolling, stopPolling]);

  // Manual polling function
  const pollNow = useCallback(async () => {
    await pollMeetings();
  }, [pollMeetings]);

  return {
    pollNow,
    startPolling,
    stopPolling,
    isPolling: isPollingRef.current
  };
}; 