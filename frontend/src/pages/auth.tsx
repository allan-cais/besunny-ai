import React, { useState } from 'react';
import LoginForm from '@/components/auth/LoginForm';
import SignUpForm from '@/components/auth/SignUpForm';
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm';

type AuthMode = 'login' | 'signup' | 'forgot-password';

const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');



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