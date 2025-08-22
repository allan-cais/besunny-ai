import React, { useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import LoginForm from '@/components/auth/LoginForm';
import SignUpForm from '@/components/auth/SignUpForm';
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm';

type AuthMode = 'login' | 'signup' | 'forgot-password';

const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const { user, initialized } = useAuth();
  const [searchParams] = useSearchParams();
  const returnTo = searchParams.get('returnTo') || '/dashboard';

  // Debug logging
  console.log('🔍 AuthPage Debug:', {
    hasUser: !!user,
    userId: user?.id,
    initialized,
    returnTo,
    pathname: window.location.pathname,
    timestamp: new Date().toISOString()
  });

  // If user is already authenticated, redirect to intended destination
  if (initialized && user) {
    console.log('🔍 AuthPage Debug: User authenticated, redirecting to:', returnTo);
    return <Navigate to={returnTo} replace />;
  }

  // Show loading spinner while checking authentication
  if (!initialized) {
    console.log('🔍 AuthPage Debug: Showing loading state');
    return (
      <div className="min-h-screen bg-white text-black font-mono flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  console.log('🔍 AuthPage Debug: Rendering auth form');

  const renderForm = () => {
    switch (mode) {
      case 'login':
        return (
          <LoginForm
            onSwitchToSignUp={() => setMode('signup')}
            onForgotPassword={() => setMode('forgot-password')}
          />
        );
      case 'signup':
        return (
          <SignUpForm
            onSwitchToLogin={() => setMode('login')}
          />
        );
      case 'forgot-password':
        return (
          <ForgotPasswordForm
            onBackToLogin={() => setMode('login')}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-white text-black font-mono flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">sunny.ai</h1>
          <div className="w-16 h-px bg-black mx-auto"></div>
        </div>
        {renderForm()}
      </div>
    </div>
  );
};

export default AuthPage; 