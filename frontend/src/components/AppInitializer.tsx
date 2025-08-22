/**
 * AppInitializer
 * Clean app initialization with proper authentication state management
 */

import React, { useEffect, useState, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import config from '@/config/environment';

interface AppInitializerProps {
  children: ReactNode;
}

export const AppInitializer: React.FC<AppInitializerProps> = ({ children }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (loading) return; // Wait for auth to initialize

    // Handle authentication state changes
    if (isAuthenticated && user) {
      // User is authenticated
      if (location.pathname === '/auth') {
        // Redirect authenticated users away from auth page
        navigate('/dashboard', { replace: true });
      }
    } else {
      // User is not authenticated
      if (location.pathname !== '/auth' && !location.pathname.startsWith('/oauth')) {
        // Redirect unauthenticated users to auth page
        navigate('/auth', { replace: true });
      }
    }

    setInitialized(true);
  }, [loading, isAuthenticated, user, location.pathname, navigate]);

  // Show loading state while initializing
  if (loading || !initialized) {
    return (
      <div className="min-h-screen bg-stone-100 dark:bg-zinc-800 text-[#4a5565] dark:text-zinc-50 font-mono flex items-center justify-center">
        <div className="max-w-md w-full mx-auto p-6">
          <div className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-lg p-6">
            <div className="text-center space-y-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
              <h2 className="text-lg font-bold">Initializing...</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Setting up your workspace
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render children once initialized
  return <>{children}</>;
};
