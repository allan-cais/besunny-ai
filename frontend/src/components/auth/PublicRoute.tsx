import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface PublicRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({ 
  children, 
  redirectTo = '/dashboard'
}) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return null; // Return null for seamless loading during auth check
  }

  // If user is authenticated, redirect to dashboard (or specified route)
  if (isAuthenticated) {
    // Check if there's a redirect location from a protected route
    const from = location.state?.from?.pathname;
    const redirectPath = from || redirectTo;
    
    return <Navigate to={redirectPath} replace />;
  }

  // User is not authenticated, can access public route
  return <>{children}</>;
};

// Public route hook for more complex logic
export const usePublicRoute = () => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  const shouldRedirect = () => {
    if (loading) return false;
    return isAuthenticated;
  };

  const getRedirectPath = () => {
    const from = location.state?.from?.pathname;
    return from || '/dashboard';
  };

  return {
    shouldRedirect,
    getRedirectPath,
    user,
    loading,
    isAuthenticated,
    location,
  };
};
