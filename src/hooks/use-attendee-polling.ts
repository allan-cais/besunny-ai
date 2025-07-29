import { useState, useEffect, useCallback, useRef } from 'react';
import { attendeePollingService, PollingResult } from '@/lib/attendee-polling';

interface UseAttendeePollingOptions {
  enabled?: boolean;
  intervalMs?: number;
  onPollingComplete?: (results: PollingResult[]) => void;
  onError?: (error: Error) => void;
}

interface UseAttendeePollingReturn {
  pollNow: () => Promise<PollingResult[]>;
  isPolling: boolean;
  lastPollTime: Date | null;
  error: Error | null;
}

export function useAttendeePolling(options: UseAttendeePollingOptions = {}): UseAttendeePollingReturn {
  const {
    enabled = true,
    intervalMs = 30000, // Default 30 seconds
    onPollingComplete,
    onError
  } = options;

  const [isPolling, setIsPolling] = useState(false);
  const [lastPollTime, setLastPollTime] = useState<Date | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const pollNow = useCallback(async (): Promise<PollingResult[]> => {
    if (isPolling) {
      return [];
    }

    try {
      setIsPolling(true);
      setError(null);
      
      const results = await attendeePollingService.pollAllMeetings();
      
      setLastPollTime(new Date());
      
      if (onPollingComplete) {
        onPollingComplete(results);
      }
      
      return results;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Polling failed');
      setError(error);
      
      if (onError) {
        onError(error);
      }
      
      return [];
    } finally {
      setIsPolling(false);
    }
  }, [isPolling, onPollingComplete, onError]);

  // Set up automatic polling
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Initial poll
    pollNow();

    // Set up interval
    intervalRef.current = setInterval(() => {
      pollNow();
    }, intervalMs);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, intervalMs, pollNow]);

  return {
    pollNow,
    isPolling,
    lastPollTime,
    error
  };
} 