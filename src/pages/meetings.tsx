import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, RefreshCw, Loader2, Wifi, WifiOff, Calendar } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';
import { Badge } from '@/components/ui/badge';

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
    sync_logs: any[];
  } | null>(null);
  const [pollingStatus, setPollingStatus] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);
  const [renewingWebhook, setRenewingWebhook] = useState(false);
  const [webhookSyncing, setWebhookSyncing] = useState(false);
  const [testingConnectivity, setTestingConnectivity] = useState(false);
  const [connectivityResult, setConnectivityResult] = useState<any>(null);

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

  const performManualSync = async () => {
    try {
      setSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      console.log('Starting manual sync...');
      
      // Perform a full sync that includes deletion detection
      const result = await calendarService.fullSync(undefined, 30, 60);
      
      console.log('Manual sync result:', result);
      
      setSyncSuccess(`Manual sync completed! Processed ${result.total_events} events, created ${result.new_meetings} new meetings, updated ${result.updated_meetings} meetings, and deleted ${result.deleted_meetings} orphaned meetings.`);
      
      // Reload meetings to show updated list
      await loadMeetings();
      await loadWebhookStatus(); // Refresh webhook status
    } catch (err: any) {
      console.error('Manual sync error:', err);
      setSyncError(err.message || 'Failed to perform manual sync');
    } finally {
      setSyncing(false);
    }
  };

  const renewWebhook = async () => {
    try {
      setRenewingWebhook(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const result = await calendarService.renewWebhook();
      
      if (result.ok) {
        setSyncSuccess('Webhook renewed successfully! Calendar sync should now work automatically.');
        await loadWebhookStatus(); // Refresh status
      } else {
        setSyncError(result.error || 'Failed to renew webhook');
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to renew webhook');
    } finally {
      setRenewingWebhook(false);
    }
  };

  const setupWebhook = async () => {
    try {
      setRenewingWebhook(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const result = await calendarService.setupWebhookSync();
      
      if (result.ok) {
        setSyncSuccess('Webhook setup successfully! Calendar sync should now work automatically.');
        await loadWebhookStatus(); // Refresh status
      } else {
        setSyncError(result.error || 'Failed to setup webhook');
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to setup webhook');
    } finally {
      setRenewingWebhook(false);
    }
  };

  const triggerWebhookSync = async () => {
    try {
      setWebhookSyncing(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      console.log('Starting webhook sync...');
      
      const result = await calendarService.triggerWebhookSync();
      
      console.log('Webhook sync result:', result);
      
      if (result.ok) {
        setSyncSuccess(`Webhook sync completed! Processed ${result.processed} events, created ${result.created} new meetings, updated ${result.updated} meetings.`);
        await loadMeetings(); // Reload meetings
        await loadWebhookStatus(); // Refresh webhook status
      } else {
        setSyncError(result.error || 'Failed to trigger webhook sync');
      }
    } catch (err: any) {
      console.error('Webhook sync error:', err);
      setSyncError(err.message || 'Failed to trigger webhook sync');
    } finally {
      setWebhookSyncing(false);
    }
  };

  const testWebhookConnectivity = async () => {
    try {
      setTestingConnectivity(true);
      setSyncError(null);
      setSyncSuccess(null);
      setConnectivityResult(null);
      
      console.log('Testing webhook connectivity...');
      
      const result = await calendarService.testWebhookConnectivity();
      
      console.log('Connectivity test result:', result);
      setConnectivityResult(result);
      
      if (result.connectivity_test) {
        setSyncSuccess('Webhook connectivity test PASSED! The webhook endpoint is working correctly.');
      } else {
        setSyncError('Webhook connectivity test FAILED! The webhook endpoint is not responding correctly.');
      }
      
      await loadWebhookStatus(); // Refresh webhook status
    } catch (err: any) {
      console.error('Connectivity test error:', err);
      setSyncError(err.message || 'Failed to test webhook connectivity');
    } finally {
      setTestingConnectivity(false);
    }
  };

  const handleMeetingUpdate = () => {
    loadMeetings();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const isWebhookExpired = () => {
    if (!webhookStatus?.webhook_expires_at) return true;
    return new Date(webhookStatus.webhook_expires_at) <= new Date();
  };

  const isWebhookExpiringSoon = () => {
    if (!webhookStatus?.webhook_expires_at) return false;
    const expiresAt = new Date(webhookStatus.webhook_expires_at);
    const now = new Date();
    const oneDayFromNow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    return expiresAt <= oneDayFromNow;
  };

  return (
    <div className="px-4 py-8 font-sans h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <PageHeader title="MEETINGS" path="~/sunny.ai/meetings" />
        
        {/* Sync Status and Controls */}
        <div className="flex items-center gap-3">
          {/* Webhook Status */}
          <div className="flex items-center gap-2">
            {webhookStatus?.webhook_active ? (
              <div className="flex items-center gap-1">
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600">Auto-sync active</span>
                {isWebhookExpired() && (
                  <Badge variant="destructive" className="text-xs">Expired</Badge>
                )}
                {isWebhookExpiringSoon() && !isWebhookExpired() && (
                  <Badge variant="secondary" className="text-xs">Expires soon</Badge>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-600">Auto-sync inactive</span>
              </div>
            )}
          </div>

          {/* Manual Sync Button */}
          <Button
            onClick={performManualSync}
            disabled={syncing}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            {syncing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {syncing ? 'Syncing...' : 'Sync Now'}
          </Button>

          {/* Webhook Sync Button */}
          {webhookStatus?.webhook_active && (
            <Button
              onClick={triggerWebhookSync}
              disabled={webhookSyncing}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              {webhookSyncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Wifi className="h-4 w-4" />
              )}
              {webhookSyncing ? 'Webhook Syncing...' : 'Webhook Sync'}
            </Button>
          )}

          {/* Webhook Connectivity Test Button */}
          <Button
            onClick={testWebhookConnectivity}
            disabled={testingConnectivity}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            {testingConnectivity ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4" />
            )}
            {testingConnectivity ? 'Testing...' : 'Test Connectivity'}
          </Button>

          {/* Webhook Setup/Renew Button */}
          {(!webhookStatus?.webhook_active || isWebhookExpired()) ? (
            <Button
              onClick={setupWebhook}
              disabled={renewingWebhook}
              variant="default"
              size="sm"
              className="flex items-center gap-2"
            >
              {renewingWebhook ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Calendar className="h-4 w-4" />
              )}
              {renewingWebhook ? 'Setting up...' : 'Setup Auto-sync'}
            </Button>
          ) : isWebhookExpiringSoon() ? (
            <Button
              onClick={renewWebhook}
              disabled={renewingWebhook}
              variant="secondary"
              size="sm"
              className="flex items-center gap-2"
            >
              {renewingWebhook ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {renewingWebhook ? 'Renewing...' : 'Renew Webhook'}
            </Button>
          ) : null}
        </div>
      </div>

      {/* Status Messages */}
      {syncError && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{syncError}</AlertDescription>
        </Alert>
      )}

      {syncSuccess && (
        <Alert className="mb-4 border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{syncSuccess}</AlertDescription>
        </Alert>
      )}

      {pollingStatus && (
        <Alert className="mb-4 border-blue-200 bg-blue-50">
          <RefreshCw className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">{pollingStatus}</AlertDescription>
        </Alert>
      )}

      {/* Webhook Status Details */}
      {webhookStatus && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border">
          <div className="text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span>
                <strong>Last sync:</strong> {webhookStatus.last_sync ? formatDate(webhookStatus.last_sync) : 'Never'}
              </span>
              {webhookStatus.webhook_expires_at && (
                <span>
                  <strong>Expires:</strong> {formatDate(webhookStatus.webhook_expires_at)}
                </span>
              )}
            </div>
            {webhookStatus.sync_logs.length > 0 && (
              <div className="mt-2">
                <strong>Recent sync activity:</strong>
                <div className="mt-1 space-y-1">
                  {webhookStatus.sync_logs.slice(0, 3).map((log: any) => (
                    <div key={log.id} className="text-xs">
                      {formatDate(log.created_at)} - {log.sync_type} sync: {log.meetings_created} created, {log.meetings_updated} updated
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Connectivity Test Results */}
      {connectivityResult && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="text-sm">
            <h4 className="font-semibold text-blue-800 mb-2">Webhook Connectivity Test Results</h4>
            <div className="space-y-1 text-blue-700">
              <div><strong>Webhook Active:</strong> {connectivityResult.webhook_active ? 'Yes' : 'No'}</div>
              <div><strong>Connectivity Test:</strong> {connectivityResult.connectivity_test ? 'PASSED' : 'FAILED'}</div>
              {connectivityResult.webhook_url && (
                <div><strong>Webhook URL:</strong> <code className="text-xs">{connectivityResult.webhook_url}</code></div>
              )}
              {connectivityResult.recent_errors.length > 0 && (
                <div>
                  <strong>Recent Errors:</strong>
                  <div className="mt-1 space-y-1">
                    {connectivityResult.recent_errors.slice(0, 3).map((error: any, index: number) => (
                      <div key={index} className="text-xs text-red-600">
                        {formatDate(error.created_at)} - {error.error_message}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
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