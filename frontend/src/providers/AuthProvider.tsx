import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase, handleSupabaseError } from '@/lib/supabase';
import config from '@/config/environment';
import { AuthState, LoginFormData, SignUpFormData } from '@/types';

// Auth context interface
interface AuthContextType extends AuthState {
  signIn: (data: LoginFormData) => Promise<{ success: boolean; error?: string }>;
  signUp: (data: SignUpFormData) => Promise<{ success: boolean; error?: string }>;
  signInWithGoogle: () => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<{ success: boolean; error?: string }>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  updateProfile: (updates: Partial<User>) => Promise<{ success: boolean; error?: string }>;
  clearError: () => void;
  refreshSession: () => Promise<void>;
}

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    error: null,
    isAuthenticated: false,
  });

  // Update state helper
  const updateState = useCallback((updates: Partial<AuthState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  // Refresh session
  const refreshSession = useCallback(async () => {
    try {
      const { data: { session }, error } = await supabase.auth.refreshSession();
      
      if (error) {
        console.error('Session refresh error:', error);
        updateState({ 
          user: null, 
          session: null, 
          isAuthenticated: false,
          error: handleSupabaseError(error)
        });
      } else if (session) {
        updateState({ 
          user: session.user, 
          session, 
          isAuthenticated: true,
          error: null
        });
      }
    } catch (err) {
      console.error('Session refresh failed:', err);
      updateState({ 
        user: null, 
        session: null, 
        isAuthenticated: false,
        error: 'Failed to refresh session'
      });
    }
  }, [updateState]);

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Get initial session
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Initial session error:', error);
          updateState({ 
            error: handleSupabaseError(error),
            loading: false 
          });
        } else if (session) {
          updateState({ 
            user: session.user, 
            session, 
            isAuthenticated: true,
            error: null,
            loading: false 
          });
        } else {
          updateState({ 
            user: null, 
            session: null, 
            isAuthenticated: false,
            error: null,
            loading: false 
          });
        }
      } catch (err) {
        console.error('Auth initialization failed:', err);
        updateState({ 
          error: 'Failed to initialize authentication',
          loading: false 
        });
      }
    };

    initializeAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {

        
        switch (event) {
          case 'INITIAL_SESSION':
            if (session) {
              updateState({ 
                user: session.user, 
                session, 
                isAuthenticated: true,
                error: null,
                loading: false 
              });
            } else {
              updateState({ 
                user: null, 
                session: null, 
                isAuthenticated: false,
                error: null,
                loading: false 
              });
            }
            break;
            
          case 'SIGNED_IN':
          case 'TOKEN_REFRESHED':
            if (session) {
              updateState({ 
                user: session.user, 
                session, 
                isAuthenticated: true,
                error: null,
                loading: false 
              });
            }
            break;
            
          case 'SIGNED_OUT':
            updateState({ 
              user: null, 
              session: null, 
              isAuthenticated: false,
              error: null,
              loading: false 
            });
            break;
            
          case 'USER_UPDATED':
            if (session) {
              updateState({ 
                user: session.user, 
                session,
                error: null 
              });
            }
            break;
            
          case 'PASSWORD_RECOVERY':
            // Handle password recovery if needed
            break;
            
          default:

        }
      }
    );

    return () => subscription.unsubscribe();
  }, [updateState]);

  // Sign in with email/password
  const signIn = useCallback(async (data: LoginFormData): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      

      
      const { data: authData, error } = await supabase.auth.signInWithPassword({
        email: data.email,
        password: data.password,
      });

      if (error) {
        console.error('Supabase auth error:', error);
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      if (authData.user && authData.session) {

        updateState({ 
          user: authData.user, 
          session: authData.session, 
          isAuthenticated: true,
          error: null,
          loading: false 
        });
        return { success: true };
      }

      return { success: false, error: 'Sign in failed' };
    } catch (err) {
      console.error('Sign in exception:', err);
      const errorMessage = 'Sign in failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Sign in with Google
  const signInWithGoogle = useCallback(async (): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth`,
          queryParams: {
            access_type: 'offline',
            prompt: 'consent',
          },
        },
      });

      if (error) {
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      return { success: true };
    } catch (err) {
      const errorMessage = 'Google sign in failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Sign up
  const signUp = useCallback(async (data: SignUpFormData): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      
      const { data: authData, error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: { 
            name: data.name,
            full_name: data.name,
          },
          emailRedirectTo: `${window.location.origin}/auth`,
        },
      });

      if (error) {
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      if (authData.user) {
        // Check if email confirmation is required
        if (authData.user.email_confirmed_at) {
          // User is already confirmed
          if (authData.session) {
            updateState({ 
              user: authData.user, 
              session: authData.session, 
              isAuthenticated: true,
              error: null,
              loading: false 
            });
            return { success: true };
          }
        } else {
          // Email confirmation required
          updateState({ 
            error: 'Please check your email to confirm your account',
            loading: false 
          });
          return { success: true, error: 'Please check your email to confirm your account' };
        }
      }

      return { success: false, error: 'Sign up failed' };
    } catch (err) {
      const errorMessage = 'Sign up failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Sign out
  const signOut = useCallback(async (): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      
      const { error } = await supabase.auth.signOut();

      if (error) {
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      updateState({ 
        user: null, 
        session: null, 
        isAuthenticated: false,
        error: null,
        loading: false 
      });
      
      return { success: true };
    } catch (err) {
      const errorMessage = 'Sign out failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Reset password
  const resetPassword = useCallback(async (email: string): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });
      
      if (error) {
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      updateState({ loading: false });
      return { success: true };
    } catch (err) {
      const errorMessage = 'Password reset failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Update profile
  const updateProfile = useCallback(async (updates: Partial<User>): Promise<{ success: boolean; error?: string }> => {
    try {
      updateState({ loading: true, error: null });
      
      const { data, error } = await supabase.auth.updateUser(updates);

      if (error) {
        const errorMessage = handleSupabaseError(error);
        updateState({ error: errorMessage, loading: false });
        return { success: false, error: errorMessage };
      }

      if (data.user) {
        updateState({ 
          user: data.user, 
          error: null,
          loading: false 
        });
        return { success: true };
      }

      return { success: false, error: 'Profile update failed' };
    } catch (err) {
      const errorMessage = 'Profile update failed';
      updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }, [updateState]);

  // Context value
  const value: AuthContextType = {
    ...state,
    signIn,
    signUp,
    signInWithGoogle,
    signOut,
    resetPassword,
    updateProfile,
    clearError,
    refreshSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export auth context for advanced usage
export { AuthContext };
