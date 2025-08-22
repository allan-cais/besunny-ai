/**
 * Authentication Service
 * Clean, type-safe authentication management
 */

import { supabase } from '@/lib/supabase';
import config from '@/config/environment';
import type { User, Session, AuthError } from '@supabase/supabase-js';

export interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
}

export interface AuthResult {
  success: boolean;
  user?: User;
  session?: Session;
  error?: string;
}

export class AuthenticationService {
  private static instance: AuthenticationService;
  private authState: AuthState = {
    user: null,
    session: null,
    loading: true,
    error: null,
  };
  private listeners: Set<(state: AuthState) => void> = new Set();

  private constructor() {
    this.initialize();
  }

  public static getInstance(): AuthenticationService {
    if (!AuthenticationService.instance) {
      AuthenticationService.instance = new AuthenticationService();
    }
    return AuthenticationService.instance;
  }

  private async initialize(): Promise<void> {
    try {
      // Get initial session
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (error) {
        this.updateState({ error: error.message });
        return;
      }

      if (session) {
        this.updateState({ 
          user: session.user, 
          session, 
          loading: false 
        });
      } else {
        this.updateState({ loading: false });
      }

      // Listen for auth changes
      supabase.auth.onAuthStateChange(async (event, session) => {
        if (config.features.enableDebugMode) {
          console.log('Auth state change:', event, session?.user?.email);
        }

        switch (event) {
          case 'SIGNED_IN':
            this.updateState({ 
              user: session?.user || null, 
              session, 
              loading: false,
              error: null 
            });
            break;
          
          case 'SIGNED_OUT':
            this.updateState({ 
              user: null, 
              session: null, 
              loading: false,
              error: null 
            });
            break;
          
          case 'TOKEN_REFRESHED':
            this.updateState({ 
              session, 
              loading: false,
              error: null 
            });
            break;
          
          case 'USER_UPDATED':
            this.updateState({ 
              user: session?.user || null, 
              session, 
              loading: false,
              error: null 
            });
            break;
        }
      });

    } catch (error) {
      this.updateState({ 
        error: error instanceof Error ? error.message : 'Authentication initialization failed',
        loading: false 
      });
    }
  }

  private updateState(updates: Partial<AuthState>): void {
    this.authState = { ...this.authState, ...updates };
    this.notifyListeners();
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.authState));
  }

  public subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.add(listener);
    listener(this.authState); // Initial call
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  public getState(): AuthState {
    return { ...this.authState };
  }

  public async signIn(email: string, password: string): Promise<AuthResult> {
    try {
      this.updateState({ loading: true, error: null });
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        this.updateState({ error: error.message, loading: false });
        return { success: false, error: error.message };
      }

      return { 
        success: true, 
        user: data.user || undefined,
        session: data.session || undefined 
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign in failed';
      this.updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signUp(email: string, password: string, name?: string): Promise<AuthResult> {
    try {
      this.updateState({ loading: true, error: null });
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: name ? { name } : undefined,
        },
      });

      if (error) {
        this.updateState({ error: error.message, loading: false });
        return { success: false, error: error.message };
      }

      return { 
        success: true, 
        user: data.user || undefined,
        session: data.session || undefined 
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign up failed';
      this.updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signInWithGoogle(): Promise<AuthResult> {
    try {
      this.updateState({ loading: true, error: null });
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/oauth-login-callback`,
        },
      });

      if (error) {
        this.updateState({ error: error.message, loading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Google sign in failed';
      this.updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signOut(): Promise<AuthResult> {
    try {
      this.updateState({ loading: true, error: null });
      
      const { error } = await supabase.auth.signOut();

      if (error) {
        this.updateState({ error: error.message, loading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign out failed';
      this.updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async resetPassword(email: string): Promise<AuthResult> {
    try {
      this.updateState({ loading: true, error: null });
      
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });

      if (error) {
        this.updateState({ error: error.message, loading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      this.updateState({ error: errorMessage, loading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async refreshSession(): Promise<AuthResult> {
    try {
      const { data, error } = await supabase.auth.refreshSession();

      if (error) {
        return { success: false, error: error.message };
      }

      return { 
        success: true, 
        user: data.user || undefined,
        session: data.session || undefined 
      };

    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Session refresh failed' 
      };
    }
  }

  public isAuthenticated(): boolean {
    return !!this.authState.user && !!this.authState.session;
  }

  public getCurrentUser(): User | null {
    return this.authState.user;
  }

  public getCurrentSession(): Session | null {
    return this.authState.session;
  }

  public getAccessToken(): string | null {
    return this.authState.session?.access_token || null;
  }
}

// Export singleton instance
export const authService = AuthenticationService.getInstance();
