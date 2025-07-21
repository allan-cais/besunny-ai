import React, { useState, useEffect } from 'react';
import CalendarView from '@/components/dashboard/CalendarView';
import { calendarService, Meeting } from '@/lib/calendar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, RefreshCw, Loader2, Wifi, WifiOff, Calendar, Clock, AlertTriangle, Play, Eye, Square, Download, Bug } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';
import { useAttendeePolling } from '@/hooks/use-attendee-polling';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { supabase } from '@/lib/supabase';

const MeetingsPage: React.FC = () => {
  const { user } = useAuth();
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
  const [testingWebhookNotification, setTestingWebhookNotification] = useState(false);

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
      const userProjects = await supabase
        .from('projects')
        .select('*')
        .eq('user_id', user.id);

      if (userProjects.data) {
        setProjects(userProjects.data);
      }
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

  const testWebhookNotification = async () => {
    try {
      setTestingWebhookNotification(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      console.log('Testing webhook notification...');
      
      const result = await calendarService.testWebhookNotification();
      
      console.log('Webhook notification test result:', result);
      
      if (result.ok) {
        setSyncSuccess(`Test webhook notification sent successfully! Timestamp: ${result.timestamp}`);
        await loadWebhookStatus(); // Refresh webhook status to show the test log
      } else {
        setSyncError(result.error || 'Failed to send test webhook notification');
      }
    } catch (err: any) {
      console.error('Webhook notification test error:', err);
      setSyncError(err.message || 'Failed to test webhook notification');
    } finally {
      setTestingWebhookNotification(false);
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

  const handleInitializeSync = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      const result = await calendarService.initializeCalendarSync(session.user.id);
      
      if (result.success) {
        setSyncSuccess(`Calendar sync initialized successfully! Webhook ID: ${result.webhook_id}`);
        await loadWebhookStatus();
      } else {
        setSyncError(`Failed to initialize sync: ${result.error}`);
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to initialize calendar sync');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupWatch = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      const result = await calendarService.setupWatch(session.user.id);
      
      if (result.success) {
        setSyncSuccess(`Watch setup successfully! Webhook ID: ${result.webhook_id}`);
        await loadWebhookStatus();
      } else {
        setSyncError(`Failed to setup watch: ${result.error}`);
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to setup watch');
    } finally {
      setLoading(false);
    }
  };

  const handleRenewWatch = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      const result = await calendarService.renewWatch(session.user.id);
      
      if (result.success) {
        setSyncSuccess(`Watch renewed successfully! Webhook ID: ${result.webhook_id}`);
        await loadWebhookStatus();
      } else {
        setSyncError(`Failed to renew watch: ${result.error}`);
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to renew watch');
    } finally {
      setLoading(false);
    }
  };

  const handleStopWatch = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      // Get current webhook ID
      const { data: webhook } = await supabase
        .from('calendar_webhooks')
        .select('webhook_id')
        .eq('user_id', session.user.id)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (!webhook?.webhook_id) {
        setSyncError('No active watch found');
        return;
      }

      const result = await calendarService.stopWatch(session.user.id, webhook.webhook_id);
      
      if (result.success) {
        setSyncSuccess('Watch stopped successfully');
        await loadWebhookStatus();
      } else {
        setSyncError(`Failed to stop watch: ${result.error}`);
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to stop watch');
    } finally {
      setLoading(false);
    }
  };

  const handleTestCalendarAccess = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      const result = await calendarService.testCalendarAccess(session.user.id);
      
      if (result.success) {
        setSyncSuccess('Calendar access test successful! Your Google credentials are valid.');
      } else {
        setSyncError(`Calendar access test failed: ${result.error}`);
      }
    } catch (err: any) {
      setSyncError(err.message || 'Failed to test calendar access');
    } finally {
      setLoading(false);
    }
  };

  const handleForceSync = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      // Get current webhook to check sync token
      const { data: webhook, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('sync_token, webhook_id, is_active')
        .eq('user_id', session.user.id)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .maybeSingle();

      if (webhookError) {
        console.error('Error fetching webhook:', webhookError);
        setSyncError('Error fetching webhook status');
        return;
      }

      if (!webhook) {
        setSyncError('No active webhook found. Please setup watch first.');
        return;
      }

      console.log('Current webhook status:', webhook);

      if (!webhook.sync_token) {
        // No sync token means the watch is not properly set up
        setSyncError('No sync token found. The watch is not properly configured. Please click "Setup Watch" to establish a proper watch with sync token.');
        return;
      }

      // We have a sync token, do incremental sync
      console.log('Found sync token, performing incremental sync...');
      const result = await calendarService.performIncrementalSync(session.user.id, webhook.sync_token);
      if (result.success) {
        setSyncSuccess(`Force sync completed! Processed events with new sync token.`);
        await loadWebhookStatus();
      } else {
        setSyncError(`Force sync failed: ${result.error}`);
      }
    } catch (err: any) {
      console.error('Force sync error:', err);
      setSyncError(err.message || 'Failed to force sync');
    } finally {
      setLoading(false);
    }
  };

  const handleDebugWebhook = async () => {
    try {
      setLoading(true);
      setSyncError(null);
      setSyncSuccess(null);
      
      const session = (await supabase.auth.getSession()).data.session;
      if (!session?.user?.id) {
        setSyncError('Not authenticated');
        return;
      }

      // Get all webhook records for this user
      const { data: webhooks, error } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', session.user.id);

      if (error) {
        console.error('Error fetching webhooks:', error);
        setSyncError('Error fetching webhook data');
        return;
      }

      console.log('All webhook records for user:', webhooks);
      
      if (webhooks && webhooks.length > 0) {
        const activeWebhook = webhooks.find(w => w.is_active);
        if (activeWebhook) {
          setSyncSuccess(`Found active webhook: ${activeWebhook.webhook_id}. Sync token: ${activeWebhook.sync_token ? 'Present' : 'Missing'}`);
        } else {
          setSyncError('No active webhook found');
        }
      } else {
        setSyncError('No webhook records found');
      }
    } catch (err: any) {
      console.error('Debug webhook error:', err);
      setSyncError(err.message || 'Failed to debug webhook');
    } finally {
      setLoading(false);
    }
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

          {/* Test Webhook Notification Button */}
          <Button
            onClick={testWebhookNotification}
            disabled={testingWebhookNotification}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            {testingWebhookNotification ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            {testingWebhookNotification ? 'Testing...' : 'Test Notification'}
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

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Meetings</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{meetings.length}</div>
            <p className="text-xs text-muted-foreground">
              {meetings.filter(m => m.meeting_url).length} with video URLs
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sync Status</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {webhookStatus?.webhook_active ? (
                <span className="text-green-600">Active</span>
              ) : (
                <span className="text-red-600">Inactive</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {webhookStatus?.last_sync ? `Last sync: ${new Date(webhookStatus.last_sync).toLocaleString()}` : 'Never synced'}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Watch Expiration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {webhookStatus?.webhook_expires_at ? (
                <span className={new Date(webhookStatus.webhook_expires_at) < new Date(Date.now() + 24 * 60 * 60 * 1000) ? 'text-red-600' : 'text-green-600'}>
                  {new Date(webhookStatus.webhook_expires_at).toLocaleDateString()}
                </span>
              ) : (
                <span className="text-gray-500">N/A</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {webhookStatus?.webhook_expires_at ? 
                `${Math.ceil((new Date(webhookStatus.webhook_expires_at).getTime() - Date.now()) / (24 * 60 * 60 * 1000))} days left` : 
                'No active watch'
              }
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Errors</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {webhookStatus?.sync_logs?.filter((log: any) => log.status === 'failed').length || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {webhookStatus?.sync_logs?.filter((log: any) => log.status === 'failed').length ? 'Sync errors detected' : 'No recent errors'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Sync Controls */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Calendar Sync Controls
          </CardTitle>
          <CardDescription>
            Manage Google Calendar real-time sync and watch functionality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
            <Button
              onClick={handleInitializeSync}
              disabled={loading}
              className="w-full"
              variant="default"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              Initialize Sync
            </Button>
            
            <Button
              onClick={handleSetupWatch}
              disabled={loading}
              className="w-full"
              variant="outline"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Eye className="mr-2 h-4 w-4" />}
              Setup Watch
            </Button>
            
            <Button
              onClick={handleRenewWatch}
              disabled={loading}
              className="w-full"
              variant="outline"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Renew Watch
            </Button>
            
            <Button
              onClick={handleStopWatch}
              disabled={loading}
              className="w-full"
              variant="destructive"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Square className="mr-2 h-4 w-4" />}
              Stop Watch
            </Button>
          </div>
          
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-5">
            <Button
              onClick={performManualSync}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
              Manual Sync
            </Button>
            
            <Button
              onClick={testWebhookConnectivity}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wifi className="mr-2 h-4 w-4" />}
              Test Connectivity
            </Button>

            <Button
              onClick={handleTestCalendarAccess}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle className="mr-2 h-4 w-4" />}
              Test Calendar Access
            </Button>

            <Button
              onClick={handleForceSync}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Force Sync
            </Button>

            <Button
              onClick={handleDebugWebhook}
              disabled={loading}
              className="w-full"
              variant="outline"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Bug className="mr-2 h-4 w-4" />}
              Debug Webhook
            </Button>
          </div>
        </CardContent>
      </Card>

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

      {/* Enhanced Sync Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Calendar Sync Controls
          </CardTitle>
          <CardDescription>
            Manage Google Calendar real-time sync and watch functionality
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
            <Button
              onClick={handleInitializeSync}
              disabled={loading}
              className="w-full"
              variant="default"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              Initialize Sync
            </Button>
            
            <Button
              onClick={handleSetupWatch}
              disabled={loading}
              className="w-full"
              variant="outline"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Eye className="mr-2 h-4 w-4" />}
              Setup Watch
            </Button>
            
            <Button
              onClick={handleRenewWatch}
              disabled={loading}
              className="w-full"
              variant="outline"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              Renew Watch
            </Button>
            
            <Button
              onClick={handleStopWatch}
              disabled={loading}
              className="w-full"
              variant="destructive"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Square className="mr-2 h-4 w-4" />}
              Stop Watch
            </Button>
          </div>
          
          <div className="grid gap-2 md:grid-cols-2">
            <Button
              onClick={performManualSync}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
              Manual Sync
            </Button>
            
            <Button
              onClick={testWebhookConnectivity}
              disabled={loading}
              className="w-full"
              variant="secondary"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wifi className="mr-2 h-4 w-4" />}
              Test Connectivity
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MeetingsPage; 