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
  const { user, session, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Only handle navigation when authentication state is stable
    // This prevents premature redirects during session restoration
    if (loading) return;

    // Debug logging in development
    if (import.meta.env.DEV) {
      console.log('AppInitializer: Auth state check', {
        user: !!user,
        session: !!session,
        loading,
        pathname: location.pathname,
        willRedirect: false
      });
    }

    // Wait for both user and session to be available before making decisions
    // This prevents premature redirects during session restoration
    if (user && session) {
      // User is fully authenticated with valid session
      if (location.pathname === '/auth') {
        // Only redirect away from auth page if user is authenticated
        if (import.meta.env.DEV) {
          console.log('AppInitializer: Redirecting authenticated user from /auth to /dashboard');
        }
        navigate('/dashboard', { replace: true });
      } else {
        if (import.meta.env.DEV) {
          console.log('AppInitializer: User authenticated, staying on current page:', location.pathname);
        }
      }
      // Don't redirect authenticated users from other pages - let them stay where they are
    } else if (!user && !session && !loading) {
      // User is definitely not authenticated (not just loading)
      if (location.pathname !== '/auth' && !location.pathname.startsWith('/oauth')) {
        // Only redirect to auth if user is not authenticated and not already on auth/oauth pages
        if (import.meta.env.DEV) {
          console.log('AppInitializer: Redirecting unauthenticated user to /auth from:', location.pathname);
        }
        navigate('/auth', { replace: true });
      }
    } else {
      if (import.meta.env.DEV) {
        console.log('AppInitializer: Auth state uncertain, not redirecting', {
          user: !!user,
          session: !!session,
          loading,
          pathname: location.pathname
        });
      }
    }
    // If loading or uncertain state, don't redirect - let the page render naturally
  }, [loading, user, session, location.pathname, navigate]);

  // Always render children - let pages handle their own loading states naturally
  return <>{children}</>;
};
