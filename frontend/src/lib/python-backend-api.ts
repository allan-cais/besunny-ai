/**
 * Python Backend API Wrapper
 * Optimized for maximum efficiency and reliability
 */

import { productionConfig, healthCheckConfig } from '../config/production-config';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
  timestamp?: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  id: string;
  user_id: string;
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  language: string;
  timezone: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  status: 'active' | 'archived' | 'deleted';
}

export interface AIResponse {
  id: string;
  user_id: string;
  prompt: string;
  response: string;
  model: string;
  tokens_used: number;
  created_at: string;
}

export class PythonBackendAPI {
  private baseUrl: string;
  private timeout: number;
  private retries: number;
  private retryDelay: number;

  constructor() {
    this.baseUrl = productionConfig.backend.baseUrl;
    this.timeout = productionConfig.backend.timeout;
    this.retries = productionConfig.backend.retries;
    this.retryDelay = productionConfig.backend.retryDelay;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return {
          success: true,
          data,
          statusCode: response.status,
          timestamp: Date.now(),
        };
      } else {
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
          statusCode: response.status,
          timestamp: Date.now(),
        };
      }
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            success: false,
            error: 'Request timeout',
            timestamp: Date.now(),
          };
        }
        return {
          success: false,
          error: error.message,
          timestamp: Date.now(),
        };
      }
      
      return {
        success: false,
        error: 'Unknown error occurred',
        timestamp: Date.now(),
      };
    }
  }

  private async makeRequestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    let lastError: string = '';
    
    for (let attempt = 1; attempt <= this.retries; attempt++) {
      const response = await this.makeRequest<T>(endpoint, options);
      
      if (response.success) {
        return response;
      }
      
      lastError = response.error || 'Unknown error';
      
      // Don't retry on client errors (4xx)
      if (response.statusCode && response.statusCode >= 400 && response.statusCode < 500) {
        break;
      }
      
      // Wait before retrying (except on last attempt)
      if (attempt < this.retries) {
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      }
    }
    
    return {
      success: false,
      error: `Failed after ${this.retries} attempts. Last error: ${lastError}`,
      timestamp: Date.now(),
    };
  }

  // ============================================================================
  // HEALTH CHECKS
  // ============================================================================

  async checkHealth(): Promise<ApiResponse> {
    return this.makeRequest('/health');
  }

  async checkHealthStatus(): Promise<ApiResponse> {
    return this.makeRequest('/health/status');
  }

  async checkHealthReady(): Promise<ApiResponse> {
    return this.makeRequest('/health/ready');
  }

  async checkHealthLive(): Promise<ApiResponse> {
    return this.makeRequest('/health/live');
  }

  async checkFrontendTest(): Promise<ApiResponse> {
    return this.makeRequest('/api/frontend-test');
  }

  // ============================================================================
  // USER MANAGEMENT
  // ============================================================================

  async getUserProfile(userId: string): Promise<ApiResponse<UserProfile>> {
    return this.makeRequestWithRetry(`/api/v1/user/profile/${userId}`);
  }

  async updateUserProfile(userId: string, data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    return this.makeRequestWithRetry(`/api/v1/user/profile/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getUserPreferences(userId: string): Promise<ApiResponse<UserPreferences>> {
    return this.makeRequestWithRetry(`/api/v1/user/preferences/${userId}`);
  }

  async updateUserPreferences(userId: string, data: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> {
    return this.makeRequestWithRetry(`/api/v1/user/preferences/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // ============================================================================
  // PROJECT MANAGEMENT
  // ============================================================================

  async getProjects(userId: string): Promise<ApiResponse<Project[]>> {
    return this.makeRequestWithRetry(`/api/v1/projects?user_id=${userId}`);
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return this.makeRequestWithRetry(`/api/v1/projects/${projectId}`);
  }

  async createProject(data: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Project>> {
    return this.makeRequestWithRetry('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProject(projectId: string, data: Partial<Project>): Promise<ApiResponse<Project>> {
    return this.makeRequestWithRetry(`/api/v1/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(projectId: string): Promise<ApiResponse> {
    return this.makeRequestWithRetry(`/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // AI SERVICES
  // ============================================================================

  async generateAIResponse(prompt: string, userId: string, model?: string): Promise<ApiResponse<AIResponse>> {
    return this.makeRequestWithRetry('/api/v1/ai/generate', {
      method: 'POST',
      body: JSON.stringify({
        prompt,
        user_id: userId,
        model: model || 'gpt-4',
      }),
    });
  }

  async getAIHistory(userId: string, limit = 50): Promise<ApiResponse<AIResponse[]>> {
    return this.makeRequestWithRetry(`/api/v1/ai/history?user_id=${userId}&limit=${limit}`);
  }

  // ============================================================================
  // DOCUMENT MANAGEMENT
  // ============================================================================

  async getDocuments(userId: string, projectId?: string, limit = 50): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: limit.toString(),
    });
    
    if (projectId) {
      params.append('project_id', projectId);
    }
    
    return this.makeRequestWithRetry(`/api/v1/documents?${params}`);
  }

  async uploadDocument(file: File, userId: string, projectId?: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    
    if (projectId) {
      formData.append('project_id', projectId);
    }
    
    return this.makeRequestWithRetry('/api/v1/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set content-type for FormData
    });
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  async ping(): Promise<ApiResponse> {
    return this.makeRequest('/');
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  isHealthy(): boolean {
    // Basic health check - can be enhanced with actual health status
    return this.baseUrl.length > 0;
  }
}

// Export a default instance
export const pythonBackendAPI = new PythonBackendAPI();
