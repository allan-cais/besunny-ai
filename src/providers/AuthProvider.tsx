import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import { backgroundSyncService } from '@/lib/background-sync';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let unsubscribed = false;

    // Restore session from storage
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (unsubscribed) return;
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
      if (!session) {
        localStorage.clear();
        sessionStorage.clear();
      }
    }).catch(() => {
      if (unsubscribed) return;
      setSession(null);
      setUser(null);
      setLoading(false);
      localStorage.clear();
      sessionStorage.clear();
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (unsubscribed) return;
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
      
      // Initialize background sync when user is authenticated
      if (session?.user) {
        try {
          await backgroundSyncService.initialize();
        } catch (error) {
          console.error('Failed to initialize background sync:', error);
        }
      } else {
        // Stop background sync when user signs out
        try {
          await backgroundSyncService.stop();
        } catch (error) {
          console.error('Failed to stop background sync:', error);
        }
      }
    });

    return () => {
      unsubscribed = true;
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  const signUp = async (email: string, password: string, name: string) => {
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
  };

  const signOut = async () => {
    try {
      const response = await supabase.auth.signOut();
      if (response.error) {
        console.error('Supabase signOut error:', response.error);
      }
    } catch (error) {
      console.error('Error in signOut:', error);
    }
  };

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error };
  };

  const signInWithGoogle = async () => {
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
  };

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {loading ? (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <span>Loading session...</span>
        </div>
      ) : children}
    </AuthContext.Provider>
  );
}; 