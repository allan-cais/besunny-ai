/**
 * AppInitializer - Dead Simple
 * Only redirects when absolutely necessary, never blocks page renders
 */

import React, { useEffect, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';

interface AppInitializerProps {
  children: ReactNode;
}

export const AppInitializer: React.FC<AppInitializerProps> = ({ children }) => {
  const { user, session, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Don't do anything while loading
    if (loading) return;

    // Only redirect in these specific cases:
    
    // 1. User is authenticated but on auth page
    if (user && session && location.pathname === '/auth') {
      navigate('/dashboard', { replace: true });
      return;
    }

    // 2. User is not authenticated but on protected page
    if (!user && !session && 
        location.pathname !== '/auth' && 
        !location.pathname.startsWith('/oauth')) {
      navigate('/auth', { replace: true });
      return;
    }

    // In all other cases, do nothing - let the user stay where they are
  }, [loading, user, session, location.pathname, navigate]);

  // Always render children immediately - never block
  return <>{children}</>;
};
