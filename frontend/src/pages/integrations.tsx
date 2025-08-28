import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import PageHeader from '@/components/dashboard/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  CheckCircle,
  XCircle,
  Loader2,
  Mail,
  HardDrive,
  Calendar,
  Settings,
  MessageSquare
} from 'lucide-react';
import { supabase } from '@/lib/supabase';

const IntegrationsPage: React.FC = () => {
  const { user, session, loading } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();

  // State for Google integration
  const [googleConnected, setGoogleConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isProcessingCallback, setIsProcessingCallback] = useState(false);

  // Check if user has Google credentials on component mount
  useEffect(() => {
    const checkGoogleConnection = async () => {
      if (user?.id) {
        try {
          const { data, error } = await supabase
            .from('google_credentials')
            .select('user_id')
            .eq('user_id', user.id)
            .eq('login_provider', false)
            .maybeSingle();
          
          if (!error && data) {
            setGoogleConnected(true);
          }
        } catch (error) {
          // Error checking Google connection
        }
      }
    };

    checkGoogleConnection();
  }, [user?.id]);

  // Handle OAuth callback parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const codeParam = urlParams.get('code');
    const stateParam = urlParams.get('state');

    if (errorParam) {
      // Clean up URL
      navigate('/integrations', { replace: true });
    } else if (codeParam && stateParam && user?.id && session?.access_token) {
      // Handle OAuth callback - exchange code for tokens
      handleOAuthCallback(codeParam, stateParam);
    }
  }, [searchParams, location.search, user?.id, session?.access_token, navigate]);

  const handleOAuthCallback = async (code: string, state: string) => {
    if (!user?.id || !session?.access_token) return;
    
    setIsProcessingCallback(true);
    
    try {
      // Call the backend to exchange the authorization code for tokens
      const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/auth/google/workspace/oauth/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          code,
          redirect_uri: `${window.location.origin}/integrations`,
          supabase_access_token: session.access_token,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to connect Google account');
      }

      const result = await response.json();
      
      if (result.success) {
        setGoogleConnected(true);
      } else {
        throw new Error(result.error || 'Failed to connect Google account');
      }
    } catch (error) {
      alert(`Failed to connect Google account: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessingCallback(false);
      // Clean up URL
      navigate('/integrations', { replace: true });
    }
  };

  const handleGoogleConnect = async () => {
    if (!user) return;
    
    setIsConnecting(true);
    
    // Google OAuth redirect for workspace integration
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/integrations`;
    
    if (clientId) {
      const scopes = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/calendar'
      ].join(' ');

      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: scopes,
        access_type: 'offline',
        prompt: 'consent',
        state: user.id
      });

      window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    } else {
      setIsConnecting(false);
      alert('Google OAuth not configured');
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!user?.id) return;
    
    try {
      // Call backend to disconnect Google account
      const response = await fetch(`${import.meta.env.VITE_PYTHON_BACKEND_URL}/api/v1/auth/google/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
        },
      });

      if (response.ok) {
        setGoogleConnected(false);
      } else {
        throw new Error('Failed to disconnect Google account');
      }
    } catch (error) {
      alert('Failed to disconnect Google account');
    }
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
                {googleConnected ? (
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
            {isConnecting || isProcessingCallback ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span className="text-sm">
                  {isConnecting ? 'Connecting to Google...' : 'Processing Google callback...'}
                </span>
              </div>
            ) : googleConnected ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <Mail className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium">Gmail Connected</span>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <HardDrive className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium">Drive Connected</span>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-medium">Calendar Connected</span>
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <Button
                    onClick={handleGoogleDisconnect}
                    variant="outline"
                    className="border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-900/20"
                  >
                    Disconnect Google Workspace
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Settings className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Connect Google Workspace</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                    Integrate your Gmail, Google Drive, and Calendar to automatically sync data and enhance your workflow.
                  </p>
                  <Button
                    onClick={handleGoogleConnect}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    Connect Google Workspace
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Other Integrations */}
        <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700">
          <CardHeader>
            <CardTitle className="text-base font-bold font-mono">OTHER INTEGRATIONS</CardTitle>
            <CardDescription className="text-xs text-gray-600 dark:text-gray-400 font-mono">
              Additional integrations coming soon
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">More integrations will be available soon</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default IntegrationsPage;
