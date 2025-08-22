/**
 * OAuth Service
 * Clean, type-safe OAuth management for Google Workspace integration
 */

import config from '@/config/environment';
import { authService } from './auth.service';

export interface OAuthState {
  connecting: boolean;
  connected: boolean;
  error: string | null;
  success: string | null;
}

export interface OAuthResult {
  success: boolean;
  error?: string;
  message?: string;
}

export interface GoogleIntegrationStatus {
  connected: boolean;
  expiresAt?: string;
  email?: string;
  scopeMismatch?: boolean;
  isLoginProvider?: boolean;
}

export class OAuthService {
  private static instance: OAuthService;
  private oauthState: OAuthState = {
    connecting: false,
    connected: false,
    error: null,
    success: null,
  };
  private listeners: Set<(state: OAuthState) => void> = new Set();

  private constructor() {}

  public static getInstance(): OAuthService {
    if (!OAuthService.instance) {
      OAuthService.instance = new OAuthService();
    }
    return OAuthService.instance;
  }

  private updateState(updates: Partial<OAuthState>): void {
    this.oauthState = { ...this.oauthState, ...updates };
    this.notifyListeners();
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.oauthState));
  }

  public subscribe(listener: (state: OAuthState) => void): () => void {
    this.listeners.add(listener);
    listener(this.oauthState); // Initial call
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  public getState(): OAuthState {
    return { ...this.oauthState };
  }

  public async initiateGoogleWorkspaceAuth(): Promise<OAuthResult> {
    try {
      const user = authService.getCurrentUser();
      if (!user) {
        return { success: false, error: 'User not authenticated' };
      }

      const clientId = config.google.clientId;
      const redirectUri = config.google.redirectUri;
      
      if (!clientId) {
        return { success: false, error: 'Google OAuth client ID not configured' };
      }

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

      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
      
      // Redirect to Google OAuth
      window.location.href = authUrl;
      
      return { success: true };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initiate Google OAuth';
      return { success: false, error: errorMessage };
    }
  }

  public async handleOAuthCallback(code: string, state: string): Promise<OAuthResult> {
    try {
      this.updateState({ connecting: true, error: null, success: null });

      const user = authService.getCurrentUser();
      if (!user || state !== user.id) {
        this.updateState({ connecting: false, error: 'Invalid OAuth callback' });
        return { success: false, error: 'Invalid OAuth callback' };
      }

      const session = authService.getCurrentSession();
      if (!session?.access_token) {
        this.updateState({ connecting: false, error: 'No valid session found' });
        return { success: false, error: 'No valid session found' };
      }

      // Call Python backend to handle OAuth callback
      const result = await this.processOAuthCallback(code, session.access_token);
      
      if (result.success) {
        this.updateState({ 
          connecting: false, 
          connected: true, 
          success: result.message || 'Google Workspace connected successfully' 
        });
      } else {
        this.updateState({ 
          connecting: false, 
          error: result.error || 'Failed to connect Google Workspace' 
        });
      }

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'OAuth callback processing failed';
      this.updateState({ connecting: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  private async processOAuthCallback(code: string, accessToken: string): Promise<OAuthResult> {
    try {
      const backendUrl = `${config.pythonBackend.url}/api/v1/auth/google/workspace/oauth/callback`;
      
      const requestBody = {
        code,
        redirect_uri: config.google.redirectUri,
        supabase_access_token: accessToken
      };

      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { error: errorText };
        }
        
        return { 
          success: false, 
          error: errorData.error || `Backend request failed: ${response.status}` 
        };
      }

      const result = await response.json();
      
      if (result.success) {
        return { 
          success: true, 
          message: `Google Workspace connected successfully: ${result.email}` 
        };
      } else {
        return { 
          success: false, 
          error: result.error || 'Backend processing failed' 
        };
      }

    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Backend communication failed' 
      };
    }
  }

  public async disconnectGoogleWorkspace(): Promise<OAuthResult> {
    try {
      this.updateState({ connecting: true, error: null, success: null });

      const user = authService.getCurrentUser();
      if (!user) {
        this.updateState({ connecting: false, error: 'User not authenticated' });
        return { success: false, error: 'User not authenticated' };
      }

      // Call Python backend to handle disconnection
      const result = await this.processDisconnection(user.id);
      
      if (result.success) {
        this.updateState({ 
          connecting: false, 
          connected: false, 
          success: result.message || 'Google Workspace disconnected successfully' 
        });
      } else {
        this.updateState({ 
          connecting: false, 
          error: result.error || 'Failed to disconnect Google Workspace' 
        });
      }

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Disconnection failed';
      this.updateState({ connecting: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }

  private async processDisconnection(userId: string): Promise<OAuthResult> {
    try {
      const session = authService.getCurrentSession();
      if (!session?.access_token) {
        return { success: false, error: 'No valid session found' };
      }

      const backendUrl = `${config.pythonBackend.url}/api/v1/auth/google/workspace/disconnect`;
      
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ user_id: userId }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { error: errorText };
        }
        
        return { 
          success: false, 
          error: errorData.error || `Backend request failed: ${response.status}` 
        };
      }

      const result = await response.json();
      
      if (result.success) {
        return { 
          success: true, 
          message: 'Google Workspace disconnected successfully' 
        };
      } else {
        return { 
          success: false, 
          error: result.error || 'Backend processing failed' 
        };
      }

    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Backend communication failed' 
      };
    }
  }

  public async checkIntegrationStatus(): Promise<GoogleIntegrationStatus> {
    try {
      const user = authService.getCurrentUser();
      if (!user) {
        return { connected: false };
      }

      // This would typically call the backend to check the actual integration status
      // For now, we'll return a basic status
      return { connected: false };

    } catch (error) {
      return { connected: false };
    }
  }

  public clearMessages(): void {
    this.updateState({ error: null, success: null });
  }

  public updateError(error: string): void {
    this.updateState({ error });
  }

  public updateSuccess(success: string): void {
    this.updateState({ success });
  }

  public updateConnecting(connecting: boolean): void {
    this.updateState({ connecting });
  }
}

// Export singleton instance
export const oauthService = OAuthService.getInstance();
