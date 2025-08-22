/**
 * IntegrationsPage
 * Clean, type-safe Google Workspace integration management
 */

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/providers/AuthProvider';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { 
  ArrowLeft, 
  Mail, 
  HardDrive, 
  CheckCircle, 
  XCircle, 
  ExternalLink,
  Loader2,
  AlertCircle,
  Trash2,
  RefreshCw,
  Calendar,
  Users,
  MessageSquare
} from 'lucide-react';
import { oauthService, type GoogleIntegrationStatus } from '@/services/oauth.service';
import PageHeader from '@/components/dashboard/PageHeader';

const IntegrationsPage: React.FC = () => {
  const { user, session, loading } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [oauthState, setOauthState] = useState(oauthService.getState());

  // Subscribe to OAuth state changes
  useEffect(() => {
    const unsubscribe = oauthService.subscribe((state) => {
      setOauthState(state);
    });

    return unsubscribe;
  }, []);

  // Handle OAuth callback parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const codeParam = urlParams.get('code');
    const stateParam = urlParams.get('state');

    if (errorParam) {
      // Handle OAuth error
      oauthService.updateError(getErrorMessage(errorParam));
      // Clean up URL
      navigate('/integrations', { replace: true });
    } else if (codeParam && stateParam && user?.id) {
      // Handle OAuth callback
      handleOAuthCallback(codeParam, stateParam);
    }
  }, [searchParams, location.search, user?.id, navigate]);

  // Load Google integration status when user changes
  useEffect(() => {
    if (!user?.id) return;
    loadGoogleStatus();
  }, [user?.id]);

  const getErrorMessage = (errorCode: string): string => {
    switch (errorCode) {
      case 'access_denied':
        return 'Google OAuth was denied. Please try again.';
      case 'invalid_request':
        return 'Invalid OAuth request. Please try again.';
      case 'server_error':
        return 'Google server error. Please try again later.';
      case 'temporarily_unavailable':
        return 'Google service temporarily unavailable. Please try again later.';
      default:
        return 'An unexpected error occurred during OAuth.';
    }
  };

  const loadGoogleStatus = async () => {
    if (!user?.id) return;
    
    try {
      setStatusLoading(true);
      const status = await oauthService.checkIntegrationStatus();
      setGoogleStatus(status);
    } catch (error) {
      console.error('Failed to load Google status:', error);
      setGoogleStatus({ connected: false });
    } finally {
      setStatusLoading(false);
    }
  };

  const handleGoogleConnect = async () => {
    if (!user?.id) return;
    
    try {
      const result = await oauthService.initiateGoogleWorkspaceAuth();
      if (!result.success) {
        oauthService.updateError(result.error || 'Failed to initiate Google OAuth');
      }
    } catch (error) {
      oauthService.updateError('Failed to connect to Google');
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    if (!user?.id || state !== user.id) {
      oauthService.updateError('Invalid OAuth callback');
      return;
    }

    try {
      const result = await oauthService.handleOAuthCallback(code, state);
      
      if (result.success) {
        // Reload Google status
        await loadGoogleStatus();
        // Clean up URL
        navigate('/integrations', { replace: true });
      }
    } catch (error) {
      oauthService.updateError('Failed to process OAuth callback');
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!user?.id) return;

    try {
      const result = await oauthService.disconnectGoogleWorkspace();
      
      if (result.success) {
        // Reload Google status
        await loadGoogleStatus();
      }
    } catch (error) {
      oauthService.updateError('Failed to disconnect from Google');
    }
  };

  const clearMessages = () => {
    oauthService.clearMessages();
  };

  return (
    <div className="px-4 pt-12 pb-8 font-mono h-full flex flex-col">
      <PageHeader
        title="INTEGRATIONS"
        path="Connect your Google Workspace for seamless data integration"
      />

      {/* Debug Info - Remove this after testing */}
      {import.meta.env.DEV && (
        <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-xs">
          <strong>Debug Info:</strong><br />
          User: {user?.id ? '✅' : '❌'}<br />
          Session: {session?.access_token ? '✅' : '❌'}<br />
          Path: {location.pathname}<br />
          Loading: {loading ? '✅' : '❌'}
        </div>
      )}

      <div className="flex-1 overflow-y-auto scrollbar-hide space-y-6">
        {/* Error Alert */}
        {oauthState.error && (
          <Alert variant="destructive" className="border-red-500 bg-red-50 dark:bg-red-900/20">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-red-800 dark:text-red-200">
              {oauthState.error}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearMessages}
                className="ml-2 h-auto p-1 text-red-600 hover:text-red-800"
              >
                Dismiss
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Success Alert */}
        {oauthState.success && (
          <Alert className="border-green-500 bg-green-50 dark:bg-green-900/20">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription className="text-green-800 dark:text-green-200">
              {oauthState.success}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearMessages}
                className="ml-2 h-auto p-1 text-green-600 hover:text-green-800"
              >
                Dismiss
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Google Workspace Integration */}
        <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <img
                    src="https://www.gstatic.com/marketing-cms/assets/images/d5/dc/cfe9ce8b4425b410b49b7f2dd3f3/g.webp=s96-fcrop64=1,00000000ffffffff-rw"
                    alt="Google Logo"
                    className="w-7 h-7"
                  />
                </div>
                <div>
                  <CardTitle className="text-base font-bold font-mono">
                    GOOGLE WORKSPACE
                  </CardTitle>
                  <CardDescription className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                    Connect Gmail, Google Drive, and Calendar for comprehensive data integration
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {googleStatus?.connected ? (
                  <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 font-mono font-bold">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    CONNECTED
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400 font-mono font-bold">
                    <XCircle className="w-3 h-3 mr-1" />
                    NOT CONNECTED
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {statusLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span className="text-sm">Loading status...</span>
              </div>
            ) : oauthState.connecting ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span className="text-sm">Connecting to Google...</span>
              </div>
            ) : googleStatus?.connected ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {googleStatus.email && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 font-mono">
                        CONNECTED EMAIL
                      </p>
                      <p className="text-sm font-mono">{googleStatus.email}</p>
                    </div>
                  )}
                  {googleStatus.expiresAt && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 font-mono">
                        EXPIRES AT
                      </p>
                      <p className="text-sm font-mono">
                        {new Date(googleStatus.expiresAt).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>

                <Separator className="bg-[#4a5565] dark:bg-zinc-700" />

                <div className="space-y-3">
                  <h4 className="text-sm font-bold font-mono">ACCESS PERMISSIONS</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Gmail (Read, Modify & Send)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <HardDrive className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Google Drive (Full Access)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Google Calendar (Full Access)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Google Account Email (userinfo.email)</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={handleGoogleDisconnect}
                    disabled={oauthState.connecting}
                    className="font-mono text-xs border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    DISCONNECT
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleGoogleConnect}
                    disabled={oauthState.connecting}
                    className="font-mono text-xs border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    RECONNECT
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12">
                <Button
                  onClick={handleGoogleConnect}
                  disabled={oauthState.connecting}
                  className="font-mono text-xs bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md shadow-md"
                  size="lg"
                >
                  <Mail className="mr-2 h-4 w-4" />
                  CONNECT GOOGLE ACCOUNT
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Coming Soon Integrations */}
        <div className="mt-8">
          <h2 className="text-lg font-bold font-mono mb-4">COMING SOON</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="opacity-60">
              <CardHeader>
                <CardTitle className="font-mono font-bold">OUTLOOK</CardTitle>
                <CardDescription className="font-mono">
                  Microsoft 365 integration
                </CardDescription>
              </CardHeader>
            </Card>
            <Card className="opacity-60">
              <CardHeader>
                <CardTitle className="font-mono font-bold">DROPBOX</CardTitle>
                <CardDescription className="font-mono">
                  File storage integration
                </CardDescription>
              </CardHeader>
            </Card>
            <Card className="opacity-60">
              <CardHeader>
                <CardTitle className="font-mono font-bold">SLACK</CardTitle>
                <CardDescription className="font-mono">
                  Team communication integration
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationsPage; 