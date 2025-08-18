/**
 * Python Backend API Integration Service
 * Connects React frontend to Python backend v15 APIs
 */

export interface PythonBackendConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  full_name: string;
  timezone: string;
  preferences: UserPreferences;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  privacy: {
    profile_visibility: 'public' | 'private' | 'team';
    data_sharing: boolean;
  };
  ai_preferences: {
    model_preference: string;
    response_length: 'short' | 'medium' | 'long';
    creativity_level: 'low' | 'medium' | 'high';
  };
}

export interface Project {
  id: string;
  name: string;
  description: string;
  visibility: 'private' | 'team' | 'public';
  owner_id: string;
  members: ProjectMember[];
  created_at: string;
  updated_at: string;
}

export interface ProjectMember {
  user_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  permissions: string[];
}

export interface AIOrchestrationRequest {
  prompt: string;
  context?: string;
  project_id?: string;
  user_id: string;
  model_preference?: string;
}

export interface AIOrchestrationResponse {
  response: string;
  model_used: string;
  tokens_used: number;
  confidence_score: number;
  suggestions?: string[];
}

export class PythonBackendAPI {
  private config: PythonBackendConfig;
  private authToken: string | null = null;

  constructor(config: PythonBackendConfig) {
    this.config = config;
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = null;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
      signal: AbortSignal.timeout(this.config.timeout),
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // Health Check
  async checkHealth(): Promise<ApiResponse> {
    return this.makeRequest('/health');
  }

  // User Management APIs
  async getUserProfile(userId: string): Promise<ApiResponse<UserProfile>> {
    return this.makeRequest(`/v1/user/profile/${userId}`);
  }

  async updateUserProfile(
    userId: string,
    profile: Partial<UserProfile>
  ): Promise<ApiResponse<UserProfile>> {
    return this.makeRequest(`/v1/user/profile/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
  }

  async updateUserPreferences(
    userId: string,
    preferences: Partial<UserPreferences>
  ): Promise<ApiResponse<UserPreferences>> {
    return this.makeRequest(`/v1/user/preferences/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Project Management APIs
  async getProjects(userId: string): Promise<ApiResponse<Project[]>> {
    return this.makeRequest(`/v1/projects/user/${userId}`);
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return this.makeRequest(`/v1/projects/${projectId}`);
  }

  async createProject(project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Project>> {
    return this.makeRequest('/v1/projects', {
      method: 'POST',
      body: JSON.stringify(project),
    });
  }

  async updateProject(
    projectId: string,
    updates: Partial<Project>
  ): Promise<ApiResponse<Project>> {
    return this.makeRequest(`/v1/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteProject(projectId: string): Promise<ApiResponse> {
    return this.makeRequest(`/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  async addProjectMember(
    projectId: string,
    member: Omit<ProjectMember, 'user_id'>
  ): Promise<ApiResponse<ProjectMember>> {
    return this.makeRequest(`/v1/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify(member),
    });
  }

  async removeProjectMember(
    projectId: string,
    userId: string
  ): Promise<ApiResponse> {
    return this.makeRequest(`/v1/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  }

  // AI Orchestration APIs
  async orchestrateAI(request: AIOrchestrationRequest): Promise<ApiResponse<AIOrchestrationResponse>> {
    return this.makeRequest('/v1/ai/orchestrate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getAIHistory(userId: string): Promise<ApiResponse<AIOrchestrationResponse[]>> {
    return this.makeRequest(`/v1/ai/history/${userId}`);
  }

  // Performance Monitoring APIs
  async getSystemHealth(): Promise<ApiResponse> {
    return this.makeRequest('/v1/performance/health');
  }

  async getServiceHealth(): Promise<ApiResponse> {
    return this.makeRequest('/v1/performance/services');
  }

  // Utility Methods
  async retryRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    maxRetries: number = this.config.retryAttempts
  ): Promise<ApiResponse<T>> {
    let lastError: string | undefined;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      const result = await this.makeRequest<T>(endpoint, options);
      
      if (result.success) {
        return result;
      }
      
      lastError = result.error;
      
      if (attempt < maxRetries) {
        // Exponential backoff
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    return {
      success: false,
      error: `Request failed after ${maxRetries} attempts. Last error: ${lastError}`,
    };
  }

  // Batch Operations
  async batchGetProjects(projectIds: string[]): Promise<ApiResponse<Project[]>> {
    return this.makeRequest('/v1/projects/batch', {
      method: 'POST',
      body: JSON.stringify({ project_ids: projectIds }),
    });
  }

  async batchUpdateUsers(updates: Array<{ userId: string; updates: Partial<UserProfile> }>): Promise<ApiResponse<UserProfile[]>> {
    return this.makeRequest('/v1/user/batch-update', {
      method: 'PUT',
      body: JSON.stringify({ updates }),
    });
  }
}

// Default configuration
export const defaultPythonBackendConfig: PythonBackendConfig = {
  baseUrl: process.env.NODE_ENV === 'production' 
    ? 'https://your-railway-app.railway.app' 
    : 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
};

// Create and export default instance
export const pythonBackendAPI = new PythonBackendAPI(defaultPythonBackendConfig);

// Export types for use in components
export type {
  UserProfile,
  UserPreferences,
  Project,
  ProjectMember,
  AIOrchestrationRequest,
  AIOrchestrationResponse,
};
