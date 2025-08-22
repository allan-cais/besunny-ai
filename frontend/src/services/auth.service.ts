/**
 * Authentication Service - Simple & Reliable
 * Handles user authentication, session management, and page refresh
 */

import { createClient, type User, type Session, type AuthError } from '@supabase/supabase-js';
import config from '@/config/environment';

// Create Supabase client with proper configuration
const supabase = createClient(
  config.supabase.url,
  config.supabase.anonKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: 'pkce'
    }
  }
);

// Simple authentication state
interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  error: string | null;
}

// Event listeners for state changes
type AuthListener = (state: AuthState) => void;

class AuthenticationService {
  private state: AuthState = {
    user: null,
    session: null,
    isLoading: false,
    error: null
  };

  private listeners: Set<AuthListener> = new Set();
  private isInitialized = false;

  constructor() {
    this.initialize();
  }

  private async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    try {
      // Get current session
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (error) {
        this.updateState({ error: error.message });
        return;
      }

      // Set initial state
      this.updateState({
        user: session?.user || null,
        session: session || null,
        isLoading: false
      });

      // Listen for auth changes
      supabase.auth.onAuthStateChange((event, session) => {
        switch (event) {
          case 'SIGNED_IN':
            this.updateState({
              user: session?.user || null,
              session: session || null,
              isLoading: false,
              error: null
            });
            break;
          
          case 'SIGNED_OUT':
            this.updateState({
              user: null,
              session: null,
              isLoading: false,
              error: null
            });
            break;
          
          case 'TOKEN_REFRESHED':
            this.updateState({
              session: session || null,
              isLoading: false,
              error: null
            });
            break;
          
          case 'USER_UPDATED':
            this.updateState({
              user: session?.user || null,
              session: session || null,
              isLoading: false,
              error: null
            });
            break;
        }
      });

      this.isInitialized = true;
    } catch (error) {
      this.updateState({ 
        error: error instanceof Error ? error.message : 'Failed to initialize',
        isLoading: false 
      });
    }
  }

  private updateState(updates: Partial<AuthState>): void {
    this.state = { ...this.state, ...updates };
    this.notifyListeners();
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  // Public methods
  public subscribe(listener: AuthListener): () => void {
    this.listeners.add(listener);
    // Call immediately with current state
    listener(this.state);
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  public getState(): AuthState {
    return { ...this.state };
  }

  public async signIn(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    try {
      this.updateState({ isLoading: true, error: null });
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        this.updateState({ error: error.message, isLoading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign in failed';
      this.updateState({ error: errorMessage, isLoading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signUp(email: string, password: string, name?: string): Promise<{ success: boolean; error?: string }> {
    try {
      this.updateState({ isLoading: true, error: null });
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { name }
        }
      });

      if (error) {
        this.updateState({ error: error.message, isLoading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign up failed';
      this.updateState({ error: errorMessage, isLoading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signInWithGoogle(): Promise<{ success: boolean; error?: string }> {
    try {
      this.updateState({ isLoading: true, error: null });
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth`
        }
      });

      if (error) {
        this.updateState({ error: error.message, isLoading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Google sign in failed';
      this.updateState({ error: errorMessage, isLoading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async signOut(): Promise<{ success: boolean; error?: string }> {
    try {
      this.updateState({ isLoading: true, error: null });
      
      const { error } = await supabase.auth.signOut();

      if (error) {
        this.updateState({ error: error.message, isLoading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sign out failed';
      this.updateState({ error: errorMessage, isLoading: false });
      return { success: false, error: errorMessage };
    }
  }

  public async resetPassword(email: string): Promise<{ success: boolean; error?: string }> {
    try {
      this.updateState({ isLoading: true, error: null });
      
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth`
      });

      if (error) {
        this.updateState({ error: error.message, isLoading: false });
        return { success: false, error: error.message };
      }

      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      this.updateState({ error: errorMessage, isLoading: false });
      return { success: false, error: errorMessage };
    }
  }

  public clearError(): void {
    this.updateState({ error: null });
  }

  public isAuthenticated(): boolean {
    return !!(this.state.user && this.state.session);
  }

  public getCurrentUser(): User | null {
    return this.state.user;
  }

  public getCurrentSession(): Session | null {
    return this.state.session;
  }
}

// Export singleton instance
export const authService = new AuthenticationService();
