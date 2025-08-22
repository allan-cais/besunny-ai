/**
 * AppInitializer
 * Clean app initialization with seamless authentication state management
 */

import React, { useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';

interface AppInitializerProps {
  children: ReactNode;
}

export const AppInitializer: React.FC<AppInitializerProps> = ({ children }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Only handle navigation when we have a definitive auth state
    if (loading) return;

    // Handle authentication state changes
    if (isAuthenticated && user) {
      // User is authenticated
      if (location.pathname === '/auth') {
        // Redirect authenticated users away from auth page
        navigate('/dashboard', { replace: true });
      }
    } else if (!isAuthenticated && !user) {
      // User is not authenticated
      if (location.pathname !== '/auth' && !location.pathname.startsWith('/oauth')) {
        // Redirect unauthenticated users to auth page
        navigate('/auth', { replace: true });
      }
    }
    // If loading or uncertain state, don't redirect - let the page render naturally
  }, [loading, isAuthenticated, user, location.pathname, navigate]);

  // Always render children - let pages handle their own loading states naturally
  return <>{children}</>;
};
