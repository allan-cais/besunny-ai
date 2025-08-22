import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUp: (email: string, password: string, name: string) => Promise<{ error: AuthError | null }>;
  signInWithGoogle: () => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Initialize session on mount
  const initializeSession = useCallback(async () => {
    console.log('🔍 AuthProvider Debug: Starting session initialization');
    try {
      // Get current session
      const { data: { session: currentSession }, error } = await supabase.auth.getSession();
      
      console.log('🔍 AuthProvider Debug: Session check result:', {
        hasSession: !!currentSession,
        hasError: !!error,
        errorMessage: error?.message,
        userId: currentSession?.user?.id,
        timestamp: new Date().toISOString()
      });
      
      if (error) {
        console.log('🔍 AuthProvider Debug: Session error, clearing state');
        setSession(null);
        setUser(null);
        setInitialized(true);
        return;
      }
      
      if (currentSession) {
        console.log('🔍 AuthProvider Debug: Setting session and user');
        setSession(currentSession);
        setUser(currentSession.user);
      } else {
        console.log('🔍 AuthProvider Debug: No session found, clearing state');
        setSession(null);
        setUser(null);
      }
      
      console.log('🔍 AuthProvider Debug: Session initialization complete');
      setInitialized(true);
    } catch (error) {
      console.error('🔍 AuthProvider Debug: Session initialization error:', error);
      setSession(null);
      setUser(null);
      setInitialized(true);
    }
  }, []);

  // Handle auth state changes
  const handleAuthStateChange = useCallback(async (event: string, newSession: Session | null) => {
    console.log('🔍 AuthProvider Debug: Auth state change:', {
      event,
      hasNewSession: !!newSession,
      userId: newSession?.user?.id,
      timestamp: new Date().toISOString()
    });
    
    setSession(newSession);
    setUser(newSession?.user ?? null);
  }, []);

  // Initialize on mount
  useEffect(() => {
    console.log('🔍 AuthProvider Debug: Initialization effect triggered:', {
      initialized,
      timestamp: new Date().toISOString()
    });
    
    if (!initialized) {
      console.log('🔍 AuthProvider Debug: Starting initialization');
      initializeSession();
    }
  }, [initialized, initializeSession]);

  // Set up auth state listener
  useEffect(() => {
    console.log('🔍 AuthProvider Debug: Auth state listener effect triggered:', {
      initialized,
      timestamp: new Date().toISOString()
    });
    
    if (!initialized) return;
    
    console.log('🔍 AuthProvider Debug: Setting up auth state listener');
    const { data: { subscription } } = supabase.auth.onAuthStateChange(handleAuthStateChange);

    return () => {
      console.log('🔍 AuthProvider Debug: Cleaning up auth state listener');
      subscription.unsubscribe();
    };
  }, [initialized, handleAuthStateChange]);

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      return { error };
    } catch (error) {
      return { error: error as AuthError };
    }
  }, []);

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name,
          },
        },
      });
      
      return { error };
    } catch (error) {
      return { error: error as AuthError };
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      const { error } = await supabase.auth.signOut();
      
      if (!error) {
        setSession(null);
        setUser(null);
      }
    } catch (error) {
      // Silent error handling
    }
  }, []);

  const resetPassword = useCallback(async (email: string) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      
      return { error };
    } catch (error) {
      return { error: error as AuthError };
    }
  }, []);

  const signInWithGoogle = useCallback(async () => {
    try {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
      const redirectUri = `${window.location.origin}/oauth-login-callback`;
      
      if (!clientId) {
        return { error: { message: 'Google OAuth client ID not configured' } as AuthError };
      }

      const scopes = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
      ].join(' ');

      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: scopes,
        access_type: 'offline',
        prompt: 'consent'
      });

      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
      window.location.href = authUrl;
      
      return { error: null };
    } catch (error) {
      return { error: error as AuthError };
    }
  }, []);

  const value = {
    user,
    session,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
  };



  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 