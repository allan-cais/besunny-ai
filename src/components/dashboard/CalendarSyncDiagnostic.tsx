import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Calendar, RefreshCw, AlertTriangle, CheckCircle, XCircle, Database } from 'lucide-react';
import { calendarService } from '@/lib/calendar';
import { supabase } from '@/lib/supabase';

interface WebhookStatus {
  webhook_active: boolean;
  webhook_url?: string;
  last_sync?: string;
  sync_logs: any[];
  recent_errors: any[];
  expiration_time?: string;
  sync_token?: string;
}

const CalendarSyncDiagnostic: React.FC = () => {
  const [status, setStatus] = useState<WebhookStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        setError('Not authenticated');
        return;
      }

      console.log('Loading webhook status for user:', session.user.id);
      
      // First, let's test if we can access the table at all
      const { data: testData, error: testError } = await supabase
        .from('calendar_webhooks')
        .select('id')
        .limit(1);
      
      if (testError) {
        console.error('Table access test failed:', testError);
        setError(`Database access error: ${testError.message} (${testError.code})`);
        return;
      }

      // Now try the actual query
      const { data: webhookData, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', session.user.id)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      console.log('Webhook query result:', { webhookData, webhookError });

      if (webhookError) {
        if (webhookError.code === 'PGRST116') {
          // PGRST116 is "not found" which is expected if no webhook exists
          console.log('No webhook found - this is expected if webhook was never set up');
        } else {
          console.error('Webhook query failed:', webhookError);
          setError(`Webhook query failed: ${webhookError.message} (${webhookError.code})`);
          return;
        }
      }

      // Get sync logs
      const { data: syncLogs, error: syncLogsError } = await supabase
        .from('calendar_sync_logs')
        .select('*')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false })
        .limit(5);

      if (syncLogsError) {
        console.error('Sync logs query failed:', syncLogsError);
      }

      // Get recent errors
      const { data: recentErrors, error: errorsError } = await supabase
        .from('calendar_sync_logs')
        .select('*')
        .eq('user_id', session.user.id)
        .eq('status', 'failed')
        .order('created_at', { ascending: false })
        .limit(5);

      if (errorsError) {
        console.error('Errors query failed:', errorsError);
      }

      const webhookStatus = {
        webhook_active: !!webhookData,
        webhook_url: webhookData ? `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${session.user.id}` : undefined,
        last_sync: webhookData?.updated_at,
        sync_logs: syncLogs || [],
        recent_errors: recentErrors || [],
        expiration_time: webhookData?.expiration_time,
        sync_token: webhookData?.sync_token,
      };

      setStatus(webhookStatus);
    } catch (err) {
      console.error('Load status error:', err);
      setError(err.message || 'Failed to load status');
    } finally {
      setLoading(false);
    }
  };

  const setupWebhook = async () => {
    setActionLoading('setup');
    setError(null);
    setSuccess(null);
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        setError('Not authenticated');
        return;
      }

      const result = await calendarService.initializeCalendarSync(session.user.id);
      if (result.success) {
        setSuccess('Calendar webhook setup successful!');
        await loadStatus(); // Refresh status
      } else {
        setError(result.error || 'Failed to setup webhook');
      }
    } catch (err) {
      setError(err.message || 'Failed to setup webhook');
    } finally {
      setActionLoading(null);
    }
  };

  const triggerManualSync = async () => {
    setActionLoading('sync');
    setError(null);
    setSuccess(null);
    try {
      const result = await calendarService.triggerWebhookSync();
      if (result.ok) {
        setSuccess(`Manual sync completed! Processed: ${result.processed}, Created: ${result.created}, Updated: ${result.updated}`);
        await loadStatus(); // Refresh status
      } else {
        setError(result.error || 'Failed to trigger sync');
      }
    } catch (err) {
      setError(err.message || 'Failed to trigger sync');
    } finally {
      setActionLoading(null);
    }
  };

  const testWebhook = async () => {
    setActionLoading('test');
    setError(null);
    setSuccess(null);
    try {
      const result = await calendarService.testWebhookNotification();
      if (result.ok) {
        setSuccess('Webhook test successful!');
        await loadStatus(); // Refresh status
      } else {
        setError(result.error || 'Webhook test failed');
      }
    } catch (err) {
      setError(err.message || 'Webhook test failed');
    } finally {
      setActionLoading(null);
    }
  };

  const testDatabaseAccess = async () => {
    setActionLoading('db-test');
    setError(null);
    setSuccess(null);
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        setError('Not authenticated');
        return;
      }

      console.log('Testing database access for user:', session.user.id);

      // Test basic table access
      const { data: testData, error: testError } = await supabase
        .from('calendar_webhooks')
        .select('id, user_id, is_active')
        .eq('user_id', session.user.id);

      if (testError) {
        setError(`Database access failed: ${testError.message} (${testError.code})`);
        return;
      }

      console.log('Database access test result:', testData);
      setSuccess(`Database access successful! Found ${testData?.length || 0} webhook records for your user.`);
      
    } catch (err) {
      console.error('Database access test error:', err);
      setError(err.message || 'Database access test failed');
    } finally {
      setActionLoading(null);
    }
  };

  const testWebhookConnectivity = async () => {
    setActionLoading('connectivity');
    setError(null);
    setSuccess(null);
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        setError('Not authenticated');
        return;
      }

      console.log('Testing webhook connectivity for user:', session.user.id);

      // Get current webhook info from database
      const { data: webhookData, error: webhookError } = await supabase
        .from('calendar_webhooks')
        .select('*')
        .eq('user_id', session.user.id)
        .eq('google_calendar_id', 'primary')
        .eq('is_active', true)
        .single();

      if (webhookError || !webhookData) {
        setError('No active webhook found in database');
        return;
      }

      console.log('Webhook data from database:', webhookData);

      // Test the webhook URL directly
      const webhookUrl = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-calendar-webhook/notify?userId=${session.user.id}`;
      
      const testResponse = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          state: 'test',
          userId: session.user.id,
        }),
      });

      if (!testResponse.ok) {
        const errorText = await testResponse.text();
        setError(`Webhook URL test failed: ${testResponse.status} - ${errorText}`);
        return;
      }

      const testResult = await testResponse.json();
      console.log('Webhook connectivity test result:', testResult);

      if (testResult.ok) {
        setSuccess(`Webhook connectivity test successful! Webhook ID: ${webhookData.webhook_id}, Resource ID: ${webhookData.resource_id}`);
      } else {
        setError(`Webhook connectivity test failed: ${testResult.error}`);
      }

    } catch (err) {
      console.error('Webhook connectivity test error:', err);
      setError(err.message || 'Webhook connectivity test failed');
    } finally {
      setActionLoading(null);
    }
  };

  const verifyWebhookWithGoogle = async () => {
    setActionLoading('verify');
    setError(null);
    setSuccess(null);
    try {
      const session = (await supabase.auth.getSession()).data.session;
      if (!session) {
        setError('Not authenticated');
        return;
      }

      console.log('Verifying webhook with Google for user:', session.user.id);

      const result = await calendarService.verifyWebhookWithGoogle(session.user.id);
      
      if (result.success) {
        setSuccess(`Webhook verified and refreshed with Google! New Webhook ID: ${result.webhook_id}`);
        await loadStatus(); // Refresh status
      } else {
        setError(`Webhook verification failed: ${result.error}`);
      }

    } catch (err) {
      console.error('Webhook verification error:', err);
      setError(err.message || 'Webhook verification failed');
    } finally {
      setActionLoading(null);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = () => {
    if (loading) return <RefreshCw className="h-4 w-4 animate-spin" />;
    if (status?.webhook_active) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <XCircle className="h-4 w-4 text-red-500" />;
  };

  const getStatusBadge = () => {
    if (loading) return <Badge variant="secondary">Loading...</Badge>;
    if (status?.webhook_active) return <Badge variant="default" className="bg-green-500">Active</Badge>;
    return <Badge variant="destructive">Inactive</Badge>;
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Calendar Sync Diagnostic
        </CardTitle>
        <CardDescription>
          Check and troubleshoot Google Calendar webhook functionality
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Display */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium">Webhook Status:</span>
            {getStatusBadge()}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadStatus}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Status Details */}
        {status && (
          <div className="space-y-2 text-sm">
            {status.webhook_url && (
              <div>
                <span className="font-medium">Webhook URL:</span>
                <code className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded">
                  {status.webhook_url}
                </code>
              </div>
            )}
            
            {status.last_sync && (
              <div>
                <span className="font-medium">Last Sync:</span>
                <span className="ml-2">{formatDate(status.last_sync)}</span>
              </div>
            )}
            
            {status.expiration_time && (
              <div>
                <span className="font-medium">Expires:</span>
                <span className="ml-2">{formatDate(status.expiration_time)}</span>
              </div>
            )}

            {status.sync_logs.length > 0 && (
              <div>
                <span className="font-medium">Recent Sync Logs:</span>
                <div className="mt-1 space-y-1">
                  {status.sync_logs.slice(0, 3).map((log, index) => (
                    <div key={index} className="text-xs bg-gray-50 px-2 py-1 rounded">
                      {formatDate(log.created_at)} - {log.sync_type} ({log.status})
                    </div>
                  ))}
                </div>
              </div>
            )}

            {status.recent_errors.length > 0 && (
              <div>
                <span className="font-medium text-red-600">Recent Errors:</span>
                <div className="mt-1 space-y-1">
                  {status.recent_errors.slice(0, 3).map((error, index) => (
                    <div key={index} className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded">
                      {formatDate(error.created_at)} - {error.error_message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-4">
          {!status?.webhook_active && (
            <Button
              onClick={setupWebhook}
              disabled={actionLoading !== null}
              className="flex-1"
            >
              {actionLoading === 'setup' ? (
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Calendar className="h-4 w-4 mr-2" />
              )}
              Setup Webhook
            </Button>
          )}

          <Button
            variant="outline"
            onClick={triggerManualSync}
            disabled={actionLoading !== null}
            className="flex-1"
          >
            {actionLoading === 'sync' ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Manual Sync
          </Button>

          <Button
            variant="outline"
            onClick={testWebhook}
            disabled={actionLoading !== null}
            className="flex-1"
          >
            {actionLoading === 'test' ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <AlertTriangle className="h-4 w-4 mr-2" />
            )}
            Test Webhook
          </Button>
        </div>

        {/* Database Test Button */}
        <div className="pt-2">
          <Button
            variant="outline"
            onClick={testDatabaseAccess}
            disabled={actionLoading !== null}
            className="w-full"
            size="sm"
          >
            {actionLoading === 'db-test' ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Database className="w-4 h-4 mr-2" />
            )}
            Test Database Access
          </Button>
        </div>

        {/* Webhook Connectivity Test Button */}
        <div className="pt-2">
          <Button
            variant="outline"
            onClick={testWebhookConnectivity}
            disabled={actionLoading !== null}
            className="w-full"
            size="sm"
          >
            {actionLoading === 'connectivity' ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <AlertTriangle className="w-4 h-4 mr-2" />
            )}
            Test Webhook Connectivity
          </Button>
        </div>

        {/* Verify Webhook with Google Button */}
        <div className="pt-2">
          <Button
            variant="outline"
            onClick={verifyWebhookWithGoogle}
            disabled={actionLoading !== null}
            className="w-full"
            size="sm"
          >
            {actionLoading === 'verify' ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <CheckCircle className="w-4 h-4 mr-2" />
            )}
            Verify & Refresh Webhook
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default CalendarSyncDiagnostic; 