import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/providers/AuthProvider';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  ArrowLeft, 
  Mail, 
  HardDrive, 
  CheckCircle, 
  XCircle, 
  ExternalLink,
  Loader2,
  AlertCircle,
  Trash2
} from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface GoogleIntegrationStatus {
  connected: boolean;
  expiresAt?: string;
  email?: string;
}

const IntegrationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check for OAuth callback parameters
  useEffect(() => {
    const errorParam = searchParams.get('error');
    const successParam = searchParams.get('success');
    const emailParam = searchParams.get('email');

    if (errorParam) {
      setError(getErrorMessage(errorParam));
    } else if (successParam && emailParam) {
      setSuccess(`Successfully connected to Google account: ${emailParam}`);
      // Refresh the status
      loadGoogleStatus();
    }
  }, [searchParams]);

  // Load Google integration status on component mount
  useEffect(() => {
    if (user?.id) {
      loadGoogleStatus();
    }
  }, [user?.id]);

  const getErrorMessage = (errorCode: string): string => {
    switch (errorCode) {
      case 'oauth_denied':
        return 'Google OAuth was denied. Please try again.';
      case 'no_code':
        return 'No authorization code received from Google.';
      case 'no_user_id':
        return 'User ID not found. Please log in again.';
      case 'callback_failed':
        return 'Failed to complete OAuth process. Please try again.';
      default:
        return 'An unexpected error occurred during OAuth.';
    }
  };

  const loadGoogleStatus = async () => {
    if (!user?.id) {
      return;
    }
    try {
      setLoading(true);
      const { data: credentials, error } = await supabase
        .from('google_credentials')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle();
      if (error && error.code !== 'PGRST116') {
        setError('Failed to load Google integration status.');
        return;
      }
      if (credentials) {
        setGoogleStatus({
          connected: true,
          expiresAt: credentials.expires_at,
          email: credentials.google_email
        });
      } else {
        setGoogleStatus({ connected: false });
      }
    } catch (error) {
      setError('Failed to load Google integration status.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleConnect = () => {
    if (!user?.id) {
      setError('User not authenticated');
      return;
    }

    // Generate OAuth URL on the frontend
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/oauth/callback`;
    
    if (!clientId) {
      setError('Google OAuth client ID not configured');
      return;
    }

    const scopes = [
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/userinfo.email'
    ].join(' ');

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: scopes,
      access_type: 'offline',
      prompt: 'consent',
      state: user.id // Pass user ID as state for security
    });

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    window.location.href = authUrl;
  };

  const handleGoogleDisconnect = async () => {
    if (!user?.id) return;

    try {
      setDisconnecting(true);
      
      // Delete Google credentials directly from Supabase
      const { error } = await supabase
        .from('google_credentials')
        .delete()
        .eq('user_id', user.id);

      if (error) {
        setError('Failed to disconnect from Google');
        return;
      }

      setGoogleStatus({ connected: false });
      setSuccess('Successfully disconnected from Google');
    } catch (error) {
      setError('Failed to disconnect from Google');
    } finally {
      setDisconnecting(false);
    }
  };

  const formatExpiryDate = (expiresAt: string): string => {
    const date = new Date(expiresAt);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 font-mono">
      {/* Header */}
      <header className="border-b border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 px-4 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/dashboard')}
              className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              BACK TO DASHBOARD
            </Button>
            <div>
              <h1 className="text-xl font-bold">INTEGRATIONS</h1>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Connect your accounts and services
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Alerts */}
        {error && (
          <Alert variant="destructive" className="mb-6 border-red-500 bg-red-50 dark:bg-red-900/20">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-6 border-green-500 bg-green-50 dark:bg-green-900/20">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">{success}</AlertDescription>
          </Alert>
        )}

        {/* Google Integration */}
        <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                  <Mail className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle className="text-base font-bold">GOOGLE WORKSPACE</CardTitle>
                  <CardDescription className="text-xs text-gray-600 dark:text-gray-400">
                    Connect Gmail and Google Drive for data ingestion
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {googleStatus?.connected ? (
                  <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    CONNECTED
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400">
                    <XCircle className="w-3 h-3 mr-1" />
                    NOT CONNECTED
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span className="text-sm">Loading status...</span>
              </div>
            ) : googleStatus?.connected ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {googleStatus.email && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400">CONNECTED EMAIL</p>
                      <p className="text-sm font-mono">{googleStatus.email}</p>
                    </div>
                  )}
                  {googleStatus.expiresAt && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400">EXPIRES AT</p>
                      <p className="text-sm font-mono">{formatExpiryDate(googleStatus.expiresAt)}</p>
                    </div>
                  )}
                </div>
                
                <Separator className="bg-[#4a5565] dark:bg-zinc-700" />
                
                <div className="space-y-3">
                  <h4 className="text-sm font-bold">ACCESS PERMISSIONS</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs">Gmail (Read-only)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <HardDrive className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs">Google Drive (Read-only)</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={handleGoogleDisconnect}
                    disabled={disconnecting}
                    className="font-mono text-xs border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    {disconnecting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        DISCONNECTING...
                      </>
                    ) : (
                      <>
                        <Trash2 className="mr-2 h-4 w-4" />
                        DISCONNECT
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={loadGoogleStatus}
                    className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
                  >
                    REFRESH STATUS
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h4 className="text-sm font-bold text-blue-800 dark:text-blue-200 mb-2">
                    CONNECT YOUR GOOGLE ACCOUNT
                  </h4>
                  <p className="text-xs text-blue-700 dark:text-blue-300 mb-4">
                    Connect your Gmail and Google Drive to enable data ingestion and analysis. 
                    We'll request read-only access to your emails and files.
                  </p>
                  <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                    <li>• Read access to your Gmail messages</li>
                    <li>• Read access to your Google Drive files</li>
                    <li>• Secure token storage in our database</li>
                    <li>• Automatic data ingestion via n8n workflows</li>
                  </ul>
                </div>

                <Button
                  onClick={handleGoogleConnect}
                  className="font-mono text-xs bg-blue-600 hover:bg-blue-700 text-white border border-blue-600 hover:border-blue-700 transition-colors"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  CONNECT GOOGLE ACCOUNT
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Coming Soon Integrations */}
        <div className="mt-8">
          <h2 className="text-lg font-bold mb-4">COMING SOON</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 opacity-50">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                    <Mail className="w-4 h-4 text-gray-500" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-bold">OUTLOOK</CardTitle>
                    <CardDescription className="text-xs">Microsoft 365 integration</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 opacity-50">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                    <HardDrive className="w-4 h-4 text-gray-500" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-bold">DROPBOX</CardTitle>
                    <CardDescription className="text-xs">File storage integration</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 opacity-50">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                    <Mail className="w-4 h-4 text-gray-500" />
                  </div>
                  <div>
                    <CardTitle className="text-sm font-bold">SLACK</CardTitle>
                    <CardDescription className="text-xs">Team communication integration</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default IntegrationsPage; 