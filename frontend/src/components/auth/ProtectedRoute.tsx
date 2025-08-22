import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, initialized } = useAuth();
  const location = useLocation();

  // Debug logging
  console.log('🔍 ProtectedRoute Debug:', {
    hasUser: !!user,
    userId: user?.id,
    initialized,
    pathname: location.pathname,
    timestamp: new Date().toISOString()
  });

  // Show loading spinner while checking authentication
  if (!initialized) {
    console.log('🔍 ProtectedRoute Debug: Not initialized yet, showing loading state');
    return (
      <div className="min-h-screen bg-white text-black font-mono flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // If user is not authenticated, redirect to auth page with return URL
  if (!user) {
    console.log('🔍 ProtectedRoute Debug: No user, redirecting to auth with return URL:', location.pathname);
    return <Navigate to={`/auth?returnTo=${encodeURIComponent(location.pathname)}`} replace />;
  }

  // If user is authenticated, render the protected content
  console.log('🔍 ProtectedRoute Debug: User authenticated, rendering children');
  return <>{children}</>;
};

export default ProtectedRoute; 