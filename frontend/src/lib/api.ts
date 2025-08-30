import { supabase } from './supabase';
import { ApiResponse, PaginatedResponse } from '@/types';
import { config } from '@/config';  // Updated to use the main config

// API base configuration
const API_CONFIG = {
  baseUrl: config.pythonBackend.url,  // Use the same backend URL
  timeout: 30000,
  retries: 3,
};

// HTTP methods
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// Request options interface
interface RequestOptions {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
}

// API error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Base API client
class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = API_CONFIG.timeout,
      retries = API_CONFIG.retries,
    } = options;

    // Debug logging for API client
    console.log('🔧 ApiClient request:', {
      method,
      endpoint,
      baseUrl: API_CONFIG.baseUrl,
      fullUrl: `${API_CONFIG.baseUrl}${endpoint}`,
      isHttps: API_CONFIG.baseUrl.startsWith('https://')
    });

    // Get current session for authentication
    const { data: { session } } = await supabase.auth.getSession();
    
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // Add authorization header if session exists
    if (session?.access_token) {
      requestHeaders['Authorization'] = `Bearer ${session.access_token}`;
    }

    const requestOptions: RequestInit = {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    };

    // Retry logic with exponential backoff
    let lastError: Error;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(`${API_CONFIG.baseUrl}${endpoint}`, {
          ...requestOptions,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          let errorData: any;
          try {
            errorData = await response.json();
          } catch {
            errorData = { message: 'Unknown error' };
          }

          throw new ApiError(
            errorData.message || `HTTP ${response.status}`,
            response.status,
            errorData.code,
            errorData.details
          );
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        }

        return {} as T;
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on client errors (4xx)
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          throw error;
        }
        
        // Don't retry on abort (timeout)
        if (error.name === 'AbortError') {
          throw new ApiError('Request timeout', 408);
        }
        
        // Last attempt
        if (attempt === retries) {
          throw lastError;
        }
        
        // Wait before retry with exponential backoff
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError!;
  }

  // Generic methods
  async get<T>(endpoint: string, options?: Omit<RequestOptions, 'method'>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body: data });
  }

  async put<T>(endpoint: string, data?: any, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body: data });
  }

  async patch<T>(endpoint: string, data?: any, options?: Omit<RequestOptions, 'method' | 'body'>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body: data });
  }

  async delete<T>(endpoint: string, options?: Omit<RequestOptions, 'method'>): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Create API client instance
export const apiClient = new ApiClient();

// API service classes
export class AuthService {
  static async refreshToken(): Promise<{ access_token: string; refresh_token: string }> {
    const { data, error } = await supabase.auth.refreshSession();
    if (error) throw error;
    if (!data.session) throw new Error('No session data');
    
    return {
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token,
    };
  }

  static async updateProfile(updates: any): Promise<any> {
    const { data, error } = await supabase.auth.updateUser(updates);
    if (error) throw error;
    return data;
  }
}

export class ProjectService {
  static async getProjects(): Promise<PaginatedResponse<any>> {
    return apiClient.get('/api/v1/projects');
  }

  static async getProject(id: string): Promise<any> {
    return apiClient.get(`/api/v1/projects/${id}`);
  }

  static async createProject(project: any): Promise<any> {
    return apiClient.post('/api/v1/projects', project);
  }

  static async updateProject(id: string, updates: any): Promise<any> {
    return apiClient.put(`/api/v1/projects/${id}`, updates);
  }

  static async deleteProject(id: string): Promise<void> {
    return apiClient.delete(`/api/v1/projects/${id}`);
  }
}

export class DocumentService {
  static async getDocuments(projectId?: string): Promise<PaginatedResponse<any>> {
    const endpoint = projectId 
      ? `/api/v1/documents?project_id=${projectId}`
      : '/api/v1/documents';
    return apiClient.get(endpoint);
  }

  static async getDocument(id: string): Promise<any> {
    return apiClient.get(`/api/v1/documents/${id}`);
  }

  static async uploadDocument(file: File, projectId?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) {
      formData.append('project_id', projectId);
    }
    
    return apiClient.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  static async updateDocument(id: string, updates: any): Promise<any> {
    return apiClient.put(`/api/v1/documents/${id}`, updates);
  }

  static async deleteDocument(id: string): Promise<void> {
    return apiClient.delete(`/api/v1/documents/${id}`);
  }
}

export class MeetingService {
  static async getMeetings(projectId?: string): Promise<PaginatedResponse<any>> {
    const endpoint = projectId 
      ? `/api/v1/meetings?project_id=${projectId}`
      : '/api/v1/meetings';
    return apiClient.get(endpoint);
  }

  static async getMeeting(id: string): Promise<any> {
    return apiClient.get(`/api/v1/meetings/${id}`);
  }

  static async createMeeting(meeting: any): Promise<any> {
    return apiClient.post('/api/v1/meetings', meeting);
  }

  static async updateMeeting(id: string, updates: any): Promise<any> {
    return apiClient.put(`/api/v1/meetings/${id}`, updates);
  }

  static async deleteMeeting(id: string): Promise<void> {
    return apiClient.delete(`/api/v1/meetings/${id}`);
  }

  static async getTranscript(meetingId: string): Promise<any> {
    return apiClient.get(`/api/v1/meetings/${meetingId}/transcript`);
  }
}

export class EmailService {
  static async getEmails(projectId?: string): Promise<PaginatedResponse<any>> {
    const endpoint = projectId 
      ? `/api/v1/emails?project_id=${projectId}`
      : '/api/v1/emails';
    return apiClient.get(endpoint);
  }

  static async getEmail(id: string): Promise<any> {
    return apiClient.get(`/api/v1/emails/${id}`);
  }

  static async markAsRead(id: string): Promise<any> {
    return apiClient.patch(`/api/v1/emails/${id}`, { read: true });
  }

  static async deleteEmail(id: string): Promise<void> {
    return apiClient.delete(`/api/v1/emails/${id}`);
  }
}

export class AIService {
  static async classifyDocument(documentId: string): Promise<any> {
    return apiClient.post(`/api/v1/ai/classify`, { document_id: documentId });
  }

  static async processDocument(documentId: string): Promise<any> {
    return apiClient.post(`/api/v1/ai/process`, { document_id: documentId });
  }

  static async chat(message: string, context?: any): Promise<any> {
    return apiClient.post('/api/v1/ai/chat', { message, context });
  }
}

export class IntegrationService {
  static async getGoogleIntegrations(): Promise<any[]> {
    return apiClient.get('/api/v1/integrations/google');
  }

  static async connectGoogle(service: string, code: string): Promise<any> {
    return apiClient.post('/api/v1/integrations/google/connect', { service, code });
  }

  static async disconnectGoogle(service: string): Promise<void> {
    return apiClient.delete(`/api/v1/integrations/google/${service}`);
  }

  static async syncGoogleData(service: string): Promise<any> {
    return apiClient.post(`/api/v1/integrations/google/${service}/sync`);
  }
}

// Export all services
export const api = {
  auth: AuthService,
  projects: ProjectService,
  documents: DocumentService,
  meetings: MeetingService,
  emails: EmailService,
  ai: AIService,
  integrations: IntegrationService,
};

// Export default API client
export default apiClient;
