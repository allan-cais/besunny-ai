import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

const OAuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const error = searchParams.get('error');
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (error) {
      // Redirect to integrations page with error
      navigate(`/integrations?error=${encodeURIComponent(error)}`);
      return;
    }

    if (code && state) {
      // Redirect to integrations page with code and state for processing
      navigate(`/integrations?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`);
      return;
    }

    // No valid parameters, redirect to integrations page
    navigate('/integrations');
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 font-mono flex items-center justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-lg p-6">
          <div className="text-center space-y-4">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-bold">Processing OAuth...</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Redirecting to integrations page...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback; 