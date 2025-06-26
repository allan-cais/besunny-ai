import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { supabase } from '@/lib/supabase';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';

const OAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, session } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  // Standalone getSession() test
  useEffect(() => {
    supabase.auth.getSession().then((result) => {
      console.log('Standalone getSession:', result);
    });
  }, []);

  // Debug: Log user on mount
  console.log('OAuthCallback user:', user);

  useEffect(() => {
    if (!user) {
      console.log('OAuthCallback: user not loaded yet');
      return;
    }
    console.log('OAuthCallback: user loaded, running callback logic');

    const code = searchParams.get('code');
    const error = searchParams.get('error');
    console.log('OAuthCallback: code:', code, 'error:', error);

    if (error) {
      setStatus('error');
      setError('OAuth was denied or failed');
      return;
    }

    if (!code) {
      setStatus('error');
      setError('No authorization code received');
      return;
    }

    if (!user?.id) {
      setStatus('error');
      setError('User not authenticated');
      return;
    }

    const handleOAuthCallback = async () => {
      console.log('OAuthCallback: inside handleOAuthCallback');
      // Use session from AuthProvider context
      if (!session?.access_token) {
        setStatus('error');
        setError('No valid session found');
        return;
      }
      console.log('OAuthCallback: session:', session);

      // Call the Supabase Edge Function for secure token exchange
      console.log('OAuthCallback: calling edge function...');
      const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/exchange-google-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
          'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY
        },
        body: JSON.stringify({ code })
      });

      console.log('OAuthCallback: edge function response:', response);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Edge function error:', errorData);
        throw new Error(errorData.error || 'Failed to exchange code for tokens');
      }

      const data = await response.json();
      console.log('OAuth callback response:', data);
      setEmail(data.email);
      setStatus('success');

      setTimeout(() => {
        navigate('/integrations?success=true&email=' + encodeURIComponent(data.email));
      }, 2000);
    };

    try {
      console.log('OAuthCallback: about to call handleOAuthCallback');
      handleOAuthCallback();
    } catch (err) {
      console.error('OAuthCallback: error calling handleOAuthCallback', err);
    }
  }, [searchParams, user, session, navigate]);

  const handleBackToIntegrations = () => {
    navigate('/integrations');
  };

  return (
    <div className="min-h-screen bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 font-mono flex items-center justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-lg p-6">
          {status === 'loading' && (
            <div className="text-center space-y-4">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600 dark:text-blue-400" />
              <h2 className="text-lg font-bold">Processing OAuth...</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Exchanging authorization code for tokens...
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center space-y-4">
              <CheckCircle className="w-8 h-8 mx-auto text-green-600 dark:text-green-400" />
              <h2 className="text-lg font-bold">OAuth Successful!</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Successfully connected to Google account
              </p>
              {email && (
                <p className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                  {email}
                </p>
              )}
              <p className="text-xs text-gray-500">
                Redirecting to integrations page...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center space-y-4">
              <XCircle className="w-8 h-8 mx-auto text-red-600 dark:text-red-400" />
              <h2 className="text-lg font-bold">OAuth Failed</h2>
              <Alert variant="destructive" className="border-red-500 bg-red-50 dark:bg-red-900/20">
                <AlertDescription className="text-xs">{error}</AlertDescription>
              </Alert>
              <Button
                onClick={handleBackToIntegrations}
                className="font-mono text-xs border border-[#4a5565] dark:border-zinc-700 hover:bg-[#4a5565] hover:text-stone-100 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 transition-colors"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                BACK TO INTEGRATIONS
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback; 