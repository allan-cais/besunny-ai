/**
 * AuthProvider
 * Clean, type-safe authentication provider with proper session management
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService, type AuthState } from '@/services/auth.service';
import type { User, Session } from '@supabase/supabase-js';

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
  refreshSession: () => Promise<{ success: boolean; error?: string }>;
  isAuthenticated: boolean;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    // Subscribe to authentication state changes
    const unsubscribe = authService.subscribe((state) => {
      setAuthState(state);
    });

    // Cleanup subscription on unmount
    return unsubscribe;
  }, []);

  const signIn = async (email: string, password: string) => {
    const result = await authService.signIn(email, password);
    return { success: result.success, error: result.error };
  };

  const signUp = async (email: string, password: string, name?: string) => {
    const result = await authService.signUp(email, password, name);
    return { success: result.success, error: result.error };
  };

  const signInWithGoogle = async () => {
    const result = await authService.signInWithGoogle();
    return { success: result.success, error: result.error };
  };

  const signOut = async () => {
    const result = await authService.signOut();
    return { success: result.success, error: result.error };
  };

  const resetPassword = async (email: string) => {
    const result = await authService.resetPassword(email);
    return { success: result.success, error: result.error };
  };

  const refreshSession = async () => {
    const result = await authService.refreshSession();
    return { success: result.success, error: result.error };
  };

  const clearError = () => {
    setAuthState(prev => ({ ...prev, error: null }));
  };

  const contextValue: AuthContextType = {
    user: authState.user,
    session: authState.session,
    loading: authState.loading,
    error: authState.error,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
    refreshSession,
    isAuthenticated: authService.isAuthenticated(),
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 