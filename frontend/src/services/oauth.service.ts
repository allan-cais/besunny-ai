/**
 * OAuth Service - Minimal & Clean
 */

import config from '@/config/environment';
import { authService } from './auth.service';

interface OAuthState {
  connecting: boolean;
  connected: boolean;
  error: string | null;
  success: string | null;
}

type OAuthListener = (state: OAuthState) => void;

class OAuthService {
  private state: OAuthState = {
    connecting: false,
    connected: false,
    error: null,
    success: null
  };

  private listeners: Set<OAuthListener> = new Set();

  private updateState(updates: Partial<OAuthState>): void {
    this.state = { ...this.state, ...updates };
    this.notifyListeners();
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  public subscribe(listener: OAuthListener): () => void {
    this.listeners.add(listener);
    listener(this.state);
    return () => this.listeners.delete(listener);
  }

  public getState(): OAuthState {
    return { ...this.state };
  }

  public async initiateGoogleWorkspaceAuth(): Promise<{ success: boolean; error?: string }> {
    try {
      const user = authService.getCurrentUser();
      if (!user) return { success: false, error: 'User not authenticated' };

      const clientId = config.google.clientId;
      const redirectUri = config.google.redirectUri;
      
      if (!clientId) return { success: false, error: 'Google OAuth not configured' };

      const scopes = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/calendar'
      ].join(' ');

      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: scopes,
        access_type: 'offline',
        prompt: 'consent',
        state: user.id
      });

      window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
      return { success: true };

    } catch (error) {
      return { success: false, error: 'Failed to initiate OAuth' };
    }
  }

  public async handleOAuthCallback(code: string, state: string): Promise<{ success: boolean; error?: string }> {
    try {
      const user = authService.getCurrentUser();
      const session = authService.getCurrentSession();
      
      if (!user || !session?.access_token) {
        return { success: false, error: 'Not authenticated' };
      }

      const response = await fetch(`${config.pythonBackend.url}/api/v1/auth/google/workspace/oauth/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ code, redirect_uri: config.google.redirectUri }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        this.updateState({ connected: true, success: 'Connected successfully!', error: null });
        return { success: true };
      } else {
        throw new Error(result.error || 'Connection failed');
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Callback failed';
      this.updateState({ error: errorMessage, success: null });
      return { success: false, error: errorMessage };
    }
  }

  public async disconnectGoogleWorkspace(): Promise<{ success: boolean; error?: string }> {
    try {
      const user = authService.getCurrentUser();
      const session = authService.getCurrentSession();
      
      if (!user || !session?.access_token) {
        return { success: false, error: 'Not authenticated' };
      }

      const response = await fetch(`${config.pythonBackend.url}/api/v1/auth/google/workspace/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ user_id: user.id }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      this.updateState({ connected: false, success: 'Disconnected successfully!', error: null });
      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Disconnect failed';
      this.updateState({ error: errorMessage, success: null });
      return { success: false, error: errorMessage };
    }
  }

  public async checkIntegrationStatus(): Promise<{ connected: boolean }> {
    try {
      const user = authService.getCurrentUser();
      const session = authService.getCurrentSession();
      
      if (!user || !session?.access_token) {
        return { connected: false };
      }

      const response = await fetch(`${config.pythonBackend.url}/api/v1/auth/google/workspace/status`, {
        headers: { 'Authorization': `Bearer ${session.access_token}` },
      });

      if (!response.ok) return { connected: false };

      const result = await response.json();
      const connected = result.connected || false;
      
      this.updateState({ connected });
      return { connected };

    } catch (error) {
      return { connected: false };
    }
  }

  public clearMessages(): void {
    this.updateState({ error: null, success: null });
  }

  public updateError(error: string): void {
    this.updateState({ error, success: null });
  }

  public updateSuccess(success: string): void {
    this.updateState({ success, error: null });
  }

  public updateConnecting(connecting: boolean): void {
    this.updateState({ connecting });
  }
}

export const oauthService = new OAuthService();
