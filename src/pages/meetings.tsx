import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, RefreshCw, Loader2, Wifi, WifiOff } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
  const { getProjectsForUser } = useSupabase();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [webhookStatus, setWebhookStatus] = useState<{
    webhook_active: boolean;
    last_sync?: string;
    webhook_expires_at?: string;
  } | null>(null);
  const [pollingStatus, setPollingStatus] = useState<string | null>(null);
  // const [renewingWebhook, setRenewingWebhook] = useState(false);
  // const [webhookError, setWebhookError] = useState<string | null>(null);
  // const [webhookSuccess, setWebhookSuccess] = useState<string | null>(null);
  // const [syncing, setSyncing] = useState(false);
  // const [syncError, setSyncError] = useState<string | null>(null);
  // const [syncSuccess, setSyncSuccess] = useState<string | null>(null);

  // Set up automatic polling
  const { pollNow } = useAttendeePolling({
    enabled: true,
    intervalMs: 30000, // Poll every 30 seconds
    onPollingComplete: (results) => {
      if (results.length > 0) {
        setPollingStatus(`Polled ${results.length} meetings`);
        // Reload meetings to show updated status
        loadMeetings();
        setTimeout(() => setPollingStatus(null), 3000);
      }
    },
    onError: (error) => {
      console.error('Polling error:', error);
      setPollingStatus('Polling failed');
      setTimeout(() => setPollingStatus(null), 3000);
    }
  });

  useEffect(() => {
    loadMeetings();
    loadProjects();
    loadWebhookStatus();
  }, [user?.id]);

  const loadProjects = async () => {
    if (!user?.id) return;
    
    try {
      const userProjects = await getProjectsForUser(user.id);
      setProjects(userProjects);
    } catch (error) {
      console.error('Error loading user projects:', error);
    }
  };

  const loadMeetings = async () => {
    try {
      setLoading(true);
      // Load upcoming meetings only (current and future)
      const loadedMeetings = await calendarService.getUpcomingMeetings();
      setMeetings(loadedMeetings);
    } catch (err: any) {
      console.error('Failed to load meetings:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadWebhookStatus = async () => {
    try {
      const status = await calendarService.getSyncStatus();
      setWebhookStatus(status);
    } catch (err: any) {
      console.error('Failed to load webhook status:', err);
    }
  };

  // const renewWebhook = async () => {
  //   try {
  //     setRenewingWebhook(true);
  //     setWebhookError(null);
  //     setWebhookSuccess(null);
      
  //     const result = await calendarService.renewWebhook();
      
  //     if (result.ok) {
  //       setWebhookSuccess('Webhook renewed successfully!');
  //       await loadWebhookStatus(); // Refresh status
  //     } else {
  //       setWebhookError(result.error || 'Failed to renew webhook');
  //     }
  //   } catch (err: any) {
  //     setWebhookError(err.message || 'Failed to renew webhook');
  //   } finally {
  //     setRenewingWebhook(false);
  //   }
  // };

  // const performFullSync = async () => {
  //   try {
  //     setSyncing(true);
  //     setSyncError(null);
  //     setSyncSuccess(null);
      
  //     // Perform a full sync that includes deletion detection
  //     const result = await calendarService.fullSync(undefined, 30, 60);
      
  //     setSyncSuccess(`Full sync completed! Processed ${result.total_events} events, created ${result.new_meetings} new meetings, updated ${result.updated_meetings} meetings, and deleted ${result.deleted_meetings} orphaned meetings.`);
      
  //     // Reload meetings to show updated list
  //     await loadMeetings();
  //   } catch (err: any) {
  //     setSyncError(err.message || 'Failed to perform full sync');
  //   } finally {
  //     setSyncing(false);
  //   }
  // };

  const handleMeetingUpdate = () => {
    loadMeetings();
  };

  return (
    <div className="px-4 py-8 font-sans h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <PageHeader title="MEETINGS" path="~/sunny.ai/meetings" />
      </div>
      
      <div className="flex-1 min-h-0">
        <CalendarView
          meetings={meetings}
          onMeetingUpdate={handleMeetingUpdate}
          projects={projects}
        />
      </div>
    </div>
  );
};

export default MeetingsPage; 