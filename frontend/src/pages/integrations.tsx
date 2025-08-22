import React, { useState, useEffect, useRef } from 'react';
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
import { supabase } from '@/lib/supabase';
// import AttendeeIntegration from '@/components/integrations/AttendeeIntegration';
import { ApiKeyStatus } from '@/lib/api-keys';
import PageHeader from '@/components/dashboard/PageHeader';

interface GoogleIntegrationStatus {
  connected: boolean;
  expiresAt?: string;
  email?: string;
  scopeMismatch?: boolean;
  isLoginProvider?: boolean;
}

const IntegrationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  // const [attendeeStatus, setAttendeeStatus] = useState<ApiKeyStatus | null>(null);
  const hasHandledCallback = useRef(false);
  
  // Track location changes to see where redirects are coming from
  useEffect(() => {
    console.log('🔍 OAuth Debug - Location changed:', {
      pathname: location.pathname,
      search: location.search,
      hash: location.hash,
      fullUrl: window.location.href,
      timestamp: new Date().toISOString()
    });
    
    // Also log the raw URL search params to see what Google is sending back
    if (location.search) {
      console.log('🔍 OAuth Debug - Raw search params:', location.search);
      console.log('🔍 OAuth Debug - Parsed search params:', Object.fromEntries(new URLSearchParams(location.search)));
    }
  }, [location]);

  // Check for OAuth callback parameters
  useEffect(() => {
    console.log('🔍 OAuth Debug - useEffect triggered with searchParams:', {
      error: searchParams.get('error'),
      code: searchParams.get('code')?.substring(0, 20) + '...',
      state: searchParams.get('state'),
      allParams: Object.fromEntries(searchParams.entries()),
      timestamp: new Date().toISOString()
    });
    
    // Also log the raw location search to see what's actually in the URL
    console.log('🔍 OAuth Debug - Raw location.search:', window.location.search);
    console.log('🔍 OAuth Debug - Raw URLSearchParams:', Object.fromEntries(new URLSearchParams(window.location.search)));
    
    // Use window.location.search directly to get OAuth parameters
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const codeParam = urlParams.get('code');
    const stateParam = urlParams.get('state');

    console.log('🔍 OAuth Debug - Parsed URL params:', {
      error: errorParam,
      code: codeParam?.substring(0, 20) + '...',
      state: stateParam,
      codeLength: codeParam?.length || 0,
      stateLength: stateParam?.length || 0,
      hasError: !!errorParam,
      hasCode: !!codeParam,
      hasState: !!stateParam,
      timestamp: new Date().toISOString()
    });

    if (errorParam) {
      console.log('🔍 OAuth Debug - Error parameter found:', errorParam);
      setError(getErrorMessage(errorParam));
      setSuccess(null);
    } else if (codeParam && stateParam && !hasHandledCallback.current) {
      console.log('🔍 OAuth Debug - Code and state found, calling handleOAuthCallback');
      hasHandledCallback.current = true;
      setError(null);
      setSuccess(null);
      handleOAuthCallback(codeParam, stateParam);
    } else {
      console.log('🔍 OAuth Debug - No OAuth parameters or already handled');
      console.log('🔍 OAuth Debug - Debug info:', {
        hasCode: !!codeParam,
        hasState: !!stateParam,
        codeLength: codeParam?.length || 0,
        stateLength: stateParam?.length || 0,
        alreadyHandled: hasHandledCallback.current,
        timestamp: new Date().toISOString()
      });
    }
  }, [searchParams, location.search]); // Add location.search as dependency

  // Additional effect to check for OAuth parameters on component mount
  useEffect(() => {
    console.log('🔍 OAuth Debug - Component mount effect - checking URL for OAuth params');
    console.log('🔍 OAuth Debug - Mount effect timestamp:', new Date().toISOString());
    
    // Check if we have OAuth parameters in the URL on mount
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const codeParam = urlParams.get('code');
    const stateParam = urlParams.get('state');

    console.log('🔍 OAuth Debug - Mount check - URL params:', {
      error: errorParam,
      code: codeParam?.substring(0, 20) + '...',
      state: stateParam,
      hasParams: !!(errorParam || codeParam || stateParam),
      fullUrl: window.location.href,
      search: window.location.search
    });

    // If we have OAuth parameters and haven't handled them yet, process them
    if ((errorParam || (codeParam && stateParam)) && !hasHandledCallback.current) {
      console.log('🔍 OAuth Debug - Mount check - Found OAuth params, processing...');
      
      if (errorParam) {
        console.log('🔍 OAuth Debug - Mount check - Processing error parameter');
        setError(getErrorMessage(errorParam));
        setSuccess(null);
        hasHandledCallback.current = true;
      } else if (codeParam && stateParam) {
        console.log('🔍 OAuth Debug - Mount check - Processing code and state parameters');
        hasHandledCallback.current = true;
        setError(null);
        setSuccess(null);
        handleOAuthCallback(codeParam, stateParam);
      }
    } else {
      console.log('🔍 OAuth Debug - Mount check - No OAuth params or already handled');
    }
  }, []); // Only run on mount

  // Debug effect to show environment variables
  useEffect(() => {
    console.log('🔍 OAuth Debug - Environment effect triggered:', {
      timestamp: new Date().toISOString()
    });
    
    console.log('🔍 OAuth Debug - Environment variables:', {
      VITE_GOOGLE_CLIENT_ID: import.meta.env.VITE_GOOGLE_CLIENT_ID ? 'Set' : 'Not set',
      VITE_PYTHON_BACKEND_URL: import.meta.env.VITE_PYTHON_BACKEND_URL || 'Not set',
      NODE_ENV: import.meta.env.NODE_ENV,
      MODE: import.meta.env.MODE,
      DEV: import.meta.env.DEV,
      PROD: import.meta.env.PROD
    });
    
    console.log('🔍 OAuth Debug - Current location:', {
      origin: window.location.origin,
      pathname: window.location.pathname,
      search: window.location.search,
      href: window.location.href
    });
  }, []);

  // Load Google integration status when user changes
  useEffect(() => {
    console.log('🔍 OAuth Debug - User effect triggered:', { 
      userId: user?.id, 
      hasUser: !!user?.id,
      userEmail: user?.email,
      timestamp: new Date().toISOString()
    });
    
    if (!user?.id) {
      console.log('🔍 OAuth Debug - No user, setting error');
      setPageLoading(false);
      setError('User session not found. Please log in again.');
    } else {
      console.log('🔍 OAuth Debug - User found, loading Google status');
      loadGoogleStatus();
      setPageLoading(false);
    }
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
      setLoading(true);
      setError(null);
      
      // Check for both integration and login credentials
      const { data: credentials, error } = await supabase
        .from('google_credentials')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle();
        
      if (error && error.code !== 'PGRST116') {
        throw new Error(error.message);
      }
      
      if (credentials) {
        // Check if this is a login provider or integration
        const isLoginProvider = credentials.login_provider === true;
        
        if (isLoginProvider) {
          // For login providers, show connected status but with limited scope info
          setGoogleStatus({
            connected: true,
            expiresAt: credentials.expires_at,
            email: credentials.google_email,
            scopeMismatch: false, // Login providers don't need scope matching
            isLoginProvider: true
          });
        } else {
          // For integrations, check scope matching
          const currentScopes = [
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar'
          ].join(' ');
          
          function normalizeScopes(scopeString: string) {
            return scopeString
              .split(/\s+/)
              .filter(Boolean)
              .filter(scope => scope !== 'openid')
              .sort()
              .join(' ');
          }
          
          const normalizedStored = normalizeScopes(credentials.scope);
          const normalizedCurrent = normalizeScopes(currentScopes);
          const scopeMismatch = normalizedStored !== normalizedCurrent;
          
          setGoogleStatus({
            connected: true,
            expiresAt: credentials.expires_at,
            email: credentials.google_email,
            scopeMismatch,
            isLoginProvider: false
          });
        }
      } else {
        setGoogleStatus({ connected: false });
      }
    } catch (error) {
      // Error loading Google status
      setError('Failed to load Google integration status');
      setGoogleStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleConnect = async () => {
    if (!user?.id) {
      setError('User not authenticated');
      return;
    }

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/integrations`; // Using existing Google Cloud Console config
    
    console.log('🔍 OAuth Debug - handleGoogleConnect called:', {
      userId: user.id,
      clientId: clientId?.substring(0, 20) + '...',
      redirectUri,
      origin: window.location.origin
    });
    
    if (!clientId) {
      setError('Google OAuth client ID not configured');
      return;
    }

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

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    
    console.log('🔍 OAuth Debug - OAuth URL parameters:', {
      client_id: clientId?.substring(0, 20) + '...',
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: scopes,
      access_type: 'offline',
      prompt: 'consent',
      state: user.id
    });
    
    console.log('🔍 OAuth Debug - Full OAuth URL:', authUrl);
    console.log('🔍 OAuth Debug - Redirecting to Google OAuth...');
    
    window.location.href = authUrl;
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    console.log('🔍 OAuth Debug - handleOAuthCallback called with:', { 
      code: code?.substring(0, 20) + '...', 
      state, 
      userId: user?.id,
      hasUser: !!user?.id,
      userEmail: user?.email,
      timestamp: new Date().toISOString()
    });
    
    if (!user?.id || state !== user.id) {
      console.log('🔍 OAuth Debug - Invalid callback:', { 
        hasUser: !!user?.id, 
        stateMatches: state === user?.id,
        providedState: state,
        expectedState: user?.id
      });
      setError('Invalid OAuth callback');
      setSuccess(null);
      return;
    }

    try {
      console.log('🔍 OAuth Debug - Starting OAuth process...');
      setConnecting(true);
      setError(null);
      setSuccess(null);
      
      // DEBUG MODE: Prevent any redirects and show detailed logging
      console.log('🔍 OAuth Debug - DEBUG MODE: Will prevent redirects to see what happens');

        // For existing users, use workspace OAuth to connect Google account
        const supabaseSession = await supabase.auth.getSession();
        const supabaseAccessToken = supabaseSession.data.session?.access_token;
        
        console.log('🔍 OAuth Debug - Frontend:', {
          userId: user?.id,
          hasSupabaseSession: !!supabaseSession.data.session,
          hasAccessToken: !!supabaseAccessToken,
          accessTokenLength: supabaseAccessToken?.length || 0,
          code: code,
          redirectUri: `${window.location.origin}/integrations`
        });
        
        // Additional debugging for session details
        if (supabaseSession.data.session) {
          console.log('🔍 OAuth Debug - Session details:', {
            userId: supabaseSession.data.session.user.id,
            email: supabaseSession.data.session.user.email,
            expiresAt: supabaseSession.data.session.expires_at,
            tokenType: supabaseSession.data.session.token_type
          });
        }
        
        if (!supabaseAccessToken) {
          setError('Supabase session not found');
          return;
        }
        
        const requestBody = { 
          code,
          redirect_uri: `${window.location.origin}/integrations`,
          supabase_access_token: supabaseAccessToken
        };
        
        console.log('🔍 OAuth Debug - Request Body:', requestBody);
        
        // Get the Python backend URL with fallback
        const pythonBackendUrl = import.meta.env.VITE_PYTHON_BACKEND_URL || 'https://besunny-1.railway.app';
        const backendUrl = `${pythonBackendUrl}/api/v1/auth/google/workspace/oauth/callback`;
        
        console.log('🔍 OAuth Debug - Backend URL:', backendUrl);
        console.log('🔍 OAuth Debug - Environment variable VITE_PYTHON_BACKEND_URL:', import.meta.env.VITE_PYTHON_BACKEND_URL);
        
        // Log the complete request details
        console.log('🔍 OAuth Debug - Complete request details:', {
          method: 'POST',
          url: backendUrl,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseAccessToken?.substring(0, 20)}...`,
          },
          body: requestBody
        });
        
        // First check if the backend is accessible
        try {
          console.log('🔍 OAuth Debug - Checking backend health...');
          const healthResponse = await fetch(`${pythonBackendUrl}/health`);
          console.log('🔍 OAuth Debug - Backend health check status:', healthResponse.status);
          
          if (!healthResponse.ok) {
            throw new Error(`Backend health check failed: ${healthResponse.status}`);
          }
          
          const healthData = await healthResponse.json();
          console.log('🔍 OAuth Debug - Backend health response:', healthData);
        } catch (healthError) {
          console.error('🔍 OAuth Debug - Backend health check failed:', healthError);
          setError(`Backend is not accessible: ${healthError.message}`);
          return;
        }
        
        const workspaceResponse = await fetch(backendUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${supabaseAccessToken}`,
          },
          body: JSON.stringify(requestBody),
        });
        
        console.log('🔍 OAuth Debug - Response Status:', workspaceResponse.status);
        console.log('🔍 OAuth Debug - Response Status Text:', workspaceResponse.statusText);
        console.log('🔍 OAuth Debug - Response Headers:', Object.fromEntries(workspaceResponse.headers.entries()));
        console.log('🔍 OAuth Debug - Response OK:', workspaceResponse.ok);
        console.log('🔍 OAuth Debug - Response Type:', workspaceResponse.type);

        // Log the raw response text for debugging
        const responseText = await workspaceResponse.text();
        console.log('🔍 OAuth Debug - Raw response text:', responseText);
        console.log('🔍 OAuth Debug - Response text length:', responseText.length);
        
        let workspaceResult;
        try {
          workspaceResult = JSON.parse(responseText);
          console.log('🔍 OAuth Debug - Parsed response:', workspaceResult);
        } catch (parseError) {
          console.error('🔍 OAuth Debug - Failed to parse response as JSON:', parseError);
          console.error('🔍 OAuth Debug - Response text that failed to parse:', responseText);
          setError('Invalid response from backend');
          return;
        }

        if (!workspaceResponse.ok) {
          console.error('🔍 OAuth Debug - Response not OK:', {
            status: workspaceResponse.status,
            statusText: workspaceResponse.statusText,
            result: workspaceResult
          });
          setError(workspaceResult.error || 'Failed to connect Google account');
          setSuccess(null);
          return;
        }

        if (workspaceResult.success) {
          // Google account connected successfully
          const successMessage = `Google account connected successfully: ${workspaceResult.email}`;
          console.log('🔍 OAuth Debug - Success!', {
            message: successMessage,
            result: workspaceResult,
            responseStatus: workspaceResponse.status,
            responseHeaders: Object.fromEntries(workspaceResponse.headers.entries())
          });
          
          setSuccess(successMessage);
          setError(null);
          
          // Load updated Google status
          console.log('🔍 OAuth Debug - Loading updated Google status...');
          await loadGoogleStatus();
          
          // Remove code/state from URL to prevent re-triggering
          console.log('🔍 OAuth Debug - Navigating to integrations page...');
          
          // DEBUG MODE: Comment out navigation to see what happens
          // navigate('/integrations', { replace: true });
          console.log('🔍 OAuth Debug - DEBUG MODE: Navigation commented out to prevent redirect');
          
          console.log('🔍 OAuth Debug - Navigation completed');
        } else {
          console.log('🔍 OAuth Debug - OAuth failed:', {
            result: workspaceResult,
            responseStatus: workspaceResponse.status,
            responseHeaders: Object.fromEntries(workspaceResponse.headers.entries())
          });
          setError(workspaceResult.error || 'Failed to connect Google account');
          setSuccess(null);
        }
    } catch (error) {
      console.log('🔍 OAuth Debug - Error in OAuth process:', error);
      console.error('🔍 OAuth Debug - Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack,
        cause: error.cause
      });
      setError('Failed to complete OAuth process');
      setSuccess(null);
    } finally {
      console.log('🔍 OAuth Debug - OAuth process completed, setting connecting to false');
      setConnecting(false);
    }
  };

  const handleGoogleDisconnect = async () => {
    if (!user?.id) return;

    try {
      setDisconnecting(true);
      setError(null);
      
      // Get current credentials for token revocation
      const { data: credentials } = await supabase
        .from('google_credentials')
        .select('access_token, refresh_token, login_provider')
        .eq('user_id', user.id)
        .maybeSingle();

      // Don't allow disconnecting login providers from integrations page
      if (credentials?.login_provider) {
        setError('Cannot disconnect login provider from integrations page. Please use your account settings to manage login providers.');
        return;
      }

      // Revoke tokens at Google (if available)
      if (credentials?.access_token) {
        try {
          await fetch('https://oauth2.googleapis.com/revoke', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ token: credentials.access_token }),
          });
        } catch (error) {
        }
      }

      if (credentials?.refresh_token) {
        try {
          await fetch('https://oauth2.googleapis.com/revoke', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ token: credentials.refresh_token }),
          });
        } catch (error) {
        }
      }

      // Clean up calendar data before deleting credentials
      try {
        const { calendarService } = await import('@/lib/calendar');
        const cleanupResult = await calendarService.cleanupCalendarData(user.id);
        
        if (cleanupResult.success) {
        } else {
        }
      } catch (cleanupError) {
      }

      // Delete credentials from database (only integration credentials, not login providers)
      const { error: deleteError } = await supabase
        .from('google_credentials')
        .delete()
        .eq('user_id', user.id)
        .eq('login_provider', false);

      if (deleteError) {
        throw new Error(deleteError.message);
      }

      setGoogleStatus({ connected: false });
      setSuccess('Successfully disconnected from Google and cleaned up calendar data');
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      // Disconnect error
      setError(error.message || 'Failed to disconnect from Google');
    } finally {
      setDisconnecting(false);
    }
  };

  const formatExpiryDate = (expiresAt: string): string => {
    const date = new Date(expiresAt);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  if (!user?.id) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-gray-600">Please log in to access integrations.</p>
        </div>
      </div>
    );
  }

  if (pageLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 pt-12 pb-8 flex-1 flex flex-col overflow-hidden font-mono">


      {/* Error Alert */}
      {error && (
        <Alert className="mb-6 border-red-500 bg-red-50 dark:bg-red-900/20">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-red-800 dark:text-red-200">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {success && (
        <Alert className="mb-6 border-green-500 bg-green-50 dark:bg-green-900/20">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            {success}
          </AlertDescription>
        </Alert>
      )}

      {/* Scope Mismatch Warning */}
      {googleStatus?.connected && googleStatus?.scopeMismatch && (
        <Alert className="mb-6 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-yellow-800 dark:text-yellow-200">
            <strong>Scope Update Required:</strong> Your Google integration was connected with different permissions than currently requested. Click "RECONNECT" to update your permissions with the latest scopes.
          </AlertDescription>
        </Alert>
      )}

      {/* Debug Panel - Only show in development or when debugging */}
      {(import.meta.env.DEV || import.meta.env.VITE_DEBUG_ENV === 'true') && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
            🔍 OAuth Debug Panel
          </h3>
          <div className="text-xs text-yellow-700 dark:text-yellow-300 space-y-1">
            <div>User ID: {user?.id || 'Not set'}</div>
            <div>Google Client ID: {import.meta.env.VITE_GOOGLE_CLIENT_ID ? 'Set' : 'Not set'}</div>
            <div>Python Backend URL: {import.meta.env.VITE_PYTHON_BACKEND_URL || 'Not set'}</div>
            <div>Current URL: {window.location.href}</div>
            <div>OAuth State: {hasHandledCallback.current ? 'Already handled' : 'Ready to handle'}</div>
            <div>URL Parameters: {window.location.search || 'None'}</div>
            <div>Code Param: {new URLSearchParams(window.location.search).get('code') ? 'Present' : 'None'}</div>
            <div>State Param: {new URLSearchParams(window.location.search).get('state') ? 'Present' : 'None'}</div>
            {error && <div className="text-red-600">Error: {error}</div>}
            {success && <div className="text-green-600">Success: {success}</div>}
          </div>
          <div className="mt-3 space-x-2">
            <button
              onClick={() => {
                console.log('🔍 OAuth Debug - Manual OAuth trigger clicked');
                hasHandledCallback.current = false;
                handleGoogleConnect();
              }}
              className="px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              Manual OAuth Trigger
            </button>
            <button
              onClick={() => {
                console.log('🔍 OAuth Debug - Reset OAuth state clicked');
                hasHandledCallback.current = false;
                setError(null);
                setSuccess(null);
              }}
              className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Reset OAuth State
            </button>
            <button
              onClick={async () => {
                console.log('🔍 OAuth Debug - Backend health check clicked');
                try {
                  const pythonBackendUrl = import.meta.env.VITE_PYTHON_BACKEND_URL || 'https://besunny-1.railway.app';
                  const response = await fetch(`${pythonBackendUrl}/health`);
                  const data = await response.json();
                  console.log('🔍 OAuth Debug - Backend health check result:', data);
                  setSuccess(`Backend health check: ${data.status}`);
                } catch (error) {
                  console.error('🔍 OAuth Debug - Backend health check failed:', error);
                  setError(`Backend health check failed: ${error.message}`);
                }
              }}
              className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Test Backend
            </button>
            <button
              onClick={() => {
                console.log('🔍 OAuth Debug - Simulate OAuth callback clicked');
                // Simulate OAuth callback parameters
                const mockCode = 'mock_oauth_code_' + Date.now();
                const mockState = user?.id || 'mock_state';
                
                // Set URL parameters to simulate OAuth callback
                const url = new URL(window.location.href);
                url.searchParams.set('code', mockCode);
                url.searchParams.set('state', mockState);
                window.history.replaceState({}, '', url.toString());
                
                // Trigger the OAuth processing
                hasHandledCallback.current = false;
                handleOAuthCallback(mockCode, mockState);
              }}
              className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
            >
              Simulate OAuth Callback
            </button>
            <button
              onClick={() => {
                console.log('🔍 OAuth Debug - Clear URL parameters clicked');
                // Clear URL parameters
                const url = new URL(window.location.href);
                url.searchParams.delete('code');
                url.searchParams.delete('state');
                url.searchParams.delete('error');
                window.history.replaceState({}, '', url.toString());
                
                // Reset OAuth state
                hasHandledCallback.current = false;
                setError(null);
                setSuccess(null);
              }}
              className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
            >
              Clear URL Params
            </button>
          </div>
        </div>
      )}

      {/* Google Integration Section */}
      <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 mb-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
                <img src="https://www.gstatic.com/marketing-cms/assets/images/d5/dc/cfe9ce8b4425b410b49b7f2dd3f3/g.webp=s96-fcrop64=1,00000000ffffffff-rw" alt="Google Logo" className="w-7 h-7" />
              </div>
              <div>
                <CardTitle className="text-base font-bold font-mono">GOOGLE WORKSPACE</CardTitle>
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
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span className="text-sm">Loading status...</span>
            </div>
          ) : connecting ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span className="text-sm">Connecting to Google...</span>
            </div>
          ) : googleStatus?.connected ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {googleStatus.email && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400 font-mono">CONNECTED EMAIL</p>
                    <p className="text-sm font-mono">{googleStatus.email}</p>
                  </div>
                )}
                {googleStatus.expiresAt && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400 font-mono">EXPIRES AT</p>
                    <p className="text-sm font-mono">{formatExpiryDate(googleStatus.expiresAt)}</p>
                  </div>
                )}
              </div>
              
              <Separator className="bg-[#4a5565] dark:bg-zinc-700" />
              
              {googleStatus.isLoginProvider ? (
                // Show login provider info
                <div className="space-y-3">
                  <h4 className="text-sm font-bold font-mono">LOGIN PROVIDER</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Google Account Authentication</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Mail className="w-4 h-4 text-green-600 dark:text-green-400" />
                      <span className="text-xs font-mono">Email & Profile Access</span>
                    </div>
                  </div>
                  <div className="mt-3 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                    <p className="text-xs text-green-800 dark:text-green-200 font-mono">
                      <span className="font-mono font-bold">Login Account:</span>
                      <span className="font-mono"> This Google account is used for authentication. To add workspace integration (Gmail, Drive, Calendar), click "ADD WORKSPACE INTEGRATION" below.</span>
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-3 pt-4">
                    <Button
                      variant="outline"
                      onClick={handleGoogleConnect}
                      disabled={connecting}
                      className="font-mono text-xs border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                    >
                      {connecting ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          CONNECTING...
                        </>
                      ) : (
                        <>
                          <Mail className="mr-2 h-4 w-4" />
                          ADD WORKSPACE INTEGRATION
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              ) : (
                // Show integration info
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
                  <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
                    <p className="text-xs text-blue-800 dark:text-blue-200 font-mono">
                      <span className="font-mono font-bold">Note:</span>
                      <span className="font-mono"> Only the above permissions are requested. If you've updated scopes in Google Cloud Console, click "RECONNECT" to refresh your permissions with the new scopes.</span>
                    </p>
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
                      onClick={handleGoogleConnect}
                      disabled={connecting}
                      className="font-mono text-xs border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                    >
                      {connecting ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          RECONNECTING...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4" />
                          RECONNECT (UPDATE SCOPES)
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12">
              <Button
                onClick={handleGoogleConnect}
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



      {/* Attendee Integration Card - Hidden for now, using master API key */}
      {/* <AttendeeIntegration onStatusChange={setAttendeeStatus} /> */}

      {/* Other Integrations */}
      <div className="mt-8">
        <h2 className="text-lg font-bold font-mono mb-4">COMING SOON</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="font-mono font-bold">OUTLOOK</CardTitle>
              <CardDescription className="font-mono">Microsoft 365 integration</CardDescription>
            </CardHeader>
          </Card>
          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="font-mono font-bold">DROPBOX</CardTitle>
              <CardDescription className="font-mono">File storage integration</CardDescription>
            </CardHeader>
          </Card>
          <Card className="opacity-60">
            <CardHeader>
              <CardTitle className="font-mono font-bold">SLACK</CardTitle>
              <CardDescription className="font-mono">Team communication integration</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default IntegrationsPage; 