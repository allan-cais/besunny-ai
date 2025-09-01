import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  redirectTo?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireAuth = true,
  redirectTo = '/auth'
}) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return null; // Return null for seamless loading during auth check
  }

  // If authentication is required and user is not authenticated
  if (requireAuth && !isAuthenticated) {
    // Redirect to login page, saving the attempted location
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location }} 
        replace 
      />
    );
  }

  // If authentication is not required and user is authenticated
  if (!requireAuth && isAuthenticated) {
    // Redirect to dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // User is authenticated and can access the route
  return <>{children}</>;
};

// Route guard hook for more complex logic
export const useRouteGuard = () => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  const canAccess = (requiredRole?: string) => {
    if (loading) return 'loading';
    if (!isAuthenticated) return 'unauthenticated';
    if (requiredRole && user?.user_metadata?.role !== requiredRole) return 'unauthorized';
    return 'authorized';
  };

  const redirectToLogin = () => {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  };

  const redirectToDashboard = () => {
    return <Navigate to="/dashboard" replace />;
  };

  return {
    canAccess,
    redirectToLogin,
    redirectToDashboard,
    user,
    loading,
    isAuthenticated,
    location,
  };
};
