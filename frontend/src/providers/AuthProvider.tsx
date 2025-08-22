/**
 * AuthProvider - Simple & Clean
 * Just exposes the authentication service to React components
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { authService } from '@/services/auth.service';
import type { User, Session } from '@supabase/supabase-js';

// Simple context interface
interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signUp: (email: string, password: string, name?: string) => Promise<{ success: boolean; error?: string }>;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<{ success: boolean; error?: string }>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  isAuthenticated: boolean;
  clearError: () => void;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Subscribe to auth service state
  const [authState, setAuthState] = React.useState(() => authService.getState());

  React.useEffect(() => {
    const unsubscribe = authService.subscribe((state) => {
      setAuthState(state);
    });

    return unsubscribe;
  }, []);

  // Simple context value
  const value: AuthContextType = {
    user: authState.user,
    session: authState.session,
    loading: authState.isLoading,
    error: authState.error,
    signIn: authService.signIn.bind(authService),
    signUp: authService.signUp.bind(authService),
    signInWithGoogle: authService.signInWithGoogle.bind(authService),
    signOut: authService.signOut.bind(authService),
    resetPassword: authService.resetPassword.bind(authService),
    isAuthenticated: authService.isAuthenticated(),
    clearError: authService.clearError.bind(authService),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 