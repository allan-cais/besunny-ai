import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { supabase } from '@/lib/supabase';

const OAuthLoginCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const error = searchParams.get('error');
      const code = searchParams.get('code');

      if (error) {
        setStatus('error');
        setMessage(getErrorMessage(error));
        setTimeout(() => navigate('/auth'), 3000);
        return;
      }

      if (!code) {
        setStatus('error');
        setMessage('No authorization code received');
        setTimeout(() => navigate('/auth'), 3000);
        return;
      }

      try {
        setStatus('loading');
        setMessage('Authenticating with Google...');

        // Call the Google OAuth login edge function
        const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/google-oauth-login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || 'Authentication failed');
        }

        if (result.success && result.session) {
          // Set the session in Supabase client
          const { error: sessionError } = await supabase.auth.setSession(result.session);
          
          if (sessionError) {
            throw new Error('Failed to set session');
          }

          setStatus('success');
          setMessage('Successfully authenticated! Setting up Google services...');
          
          // Set up automatic calendar sync and Gmail watch
          try {
            const { calendarService } = await import('@/lib/calendar');
            const { gmailWatchService } = await import('@/lib/gmail-watch-service');
            
            // Set up calendar sync
            const syncResult = await calendarService.initializeCalendarSync(result.session.user.id);
            
            if (syncResult.success) {
              // Check if we actually have meetings in the database
              const allMeetings = await calendarService.getAllCurrentWeekMeetings();
              
              if (allMeetings.length === 0) {
                const manualResult = await calendarService.manualSyncWithoutCleanup(result.session.user.id);
                
                if (manualResult.success) {
                  setMessage('Calendar sync completed! Setting up Gmail watch...');
                } else {
                  setMessage('Calendar sync partially completed. Setting up Gmail watch...');
                }
              } else {
                setMessage('Calendar sync configured! Setting up Gmail watch...');
              }
            } else {
              // Calendar sync failed
              setMessage('Calendar sync failed, but authentication successful. Setting up Gmail watch...');
            }
            
            // Set up Gmail watch for virtual email detection
            if (result.session.user.email) {
              try {
                const gmailResult = await gmailWatchService.setupGmailWatch(result.session.user.email);
                if (gmailResult.success) {
                  setMessage('Gmail watch configured! Redirecting to dashboard...');
                } else {
                  setMessage('Calendar sync configured! Gmail watch can be set up later. Redirecting...');
                }
              } catch (gmailError) {
                // Gmail watch setup failed
                setMessage('Calendar sync configured! Gmail watch can be set up later. Redirecting...');
              }
            } else {
              setMessage('Calendar sync configured! Gmail watch can be set up later. Redirecting...');
            }
          } catch (syncError) {
            // Google services setup failed
            // Continue anyway - services can be set up later
            setMessage('Authentication successful! Services can be configured later. Redirecting...');
          }
          
          // Redirect to dashboard after a short delay
          setTimeout(() => navigate('/dashboard'), 2000);
        } else {
          throw new Error(result.message || 'Authentication failed');
        }
      } catch (error) {
        // OAuth login error
        setStatus('error');
        setMessage(error.message || 'Authentication failed');
        setTimeout(() => navigate('/auth'), 3000);
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate]);

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
        return 'An unexpected error occurred during authentication.';
    }
  };

  return (
    <div className="min-h-screen bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 font-mono flex items-center justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-lg p-6">
          <div className="text-center space-y-4">
            {status === 'loading' && (
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600 dark:text-blue-400" />
            )}
            {status === 'success' && (
              <CheckCircle className="w-8 h-8 mx-auto text-green-600 dark:text-green-400" />
            )}
            {status === 'error' && (
              <XCircle className="w-8 h-8 mx-auto text-red-600 dark:text-red-400" />
            )}
            
            <h2 className="text-lg font-bold">
              {status === 'loading' && 'Processing Authentication...'}
              {status === 'success' && 'Authentication Successful!'}
              {status === 'error' && 'Authentication Failed'}
            </h2>
            
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {message}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OAuthLoginCallback; 