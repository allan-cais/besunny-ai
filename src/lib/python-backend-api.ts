// Python Backend API Client
// Provides integration with the Python backend services for BeSunny.ai

import { config } from '../config';
import type { 
  Meeting, 
  Document, 
  Project, 
  GoogleCalendarEvent,
  CalendarSyncRequest,
  CalendarWebhookRequest,
  MeetingBotRequest,
  DocumentCreate,
  DocumentUpdate,
  ProjectCreate,
  ProjectUpdate
} from '../types';

// Python backend configuration
const PYTHON_BACKEND_CONFIG = {
  baseUrl: import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
};

// API response wrapper
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

// Python backend API client
export class PythonBackendAPI {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor() {
    this.baseUrl = PYTHON_BACKEND_CONFIG.baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // Set authentication token
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  // Clear authentication token
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  // Make API call with retry logic
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), PYTHON_BACKEND_CONFIG.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
          message: errorText,
          status: response.status,
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
        status: response.status,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            success: false,
            error: 'Request timeout',
            status: 408,
          };
        }
        return {
          success: false,
          error: error.message,
          status: 500,
        };
      }
      
      return {
        success: false,
        error: 'Unknown error',
        status: 500,
      };
    }
  }

  // Calendar API endpoints
  async setupCalendarWebhook(request: CalendarWebhookRequest): Promise<ApiResponse<{ webhook_id: string }>> {
    return this.makeRequest('/api/v1/calendar/webhook', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async syncCalendarEvents(request: CalendarSyncRequest): Promise<ApiResponse<{ events_synced: number }>> {
    return this.makeRequest('/api/v1/calendar/sync', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getUserMeetings(projectId?: string, status?: string): Promise<ApiResponse<{ meetings: Meeting[]; total_count: number }>> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (status) params.append('status', status);
    
    return this.makeRequest(`/api/v1/calendar/meetings?${params.toString()}`);
  }

  async getMeetingDetails(meetingId: string): Promise<ApiResponse<Meeting>> {
    return this.makeRequest(`/api/v1/calendar/meetings/${meetingId}`);
  }

  async scheduleMeetingBot(meetingId: string, request: MeetingBotRequest): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest(`/api/v1/calendar/meetings/${meetingId}/bot`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getActiveWebhooks(): Promise<ApiResponse<any[]>> {
    return this.makeRequest('/api/v1/calendar/webhooks/active');
  }

  async getWebhookLogs(webhookId?: string, limit: number = 100): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (webhookId) params.append('webhook_id', webhookId);
    params.append('limit', limit.toString());
    
    return this.makeRequest(`/api/v1/calendar/webhooks/logs?${params.toString()}`);
  }

  async handleCalendarWebhook(webhookData: any): Promise<ApiResponse<{ status: string }>> {
    return this.makeRequest('/api/v1/calendar/webhook', {
      method: 'POST',
      body: JSON.stringify(webhookData),
    });
  }

  async cleanupExpiredWebhooks(): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest('/api/v1/calendar/cleanup/expired-webhooks', {
      method: 'POST',
    });
  }

  async getCalendarSyncStatus(userId: string): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/v1/calendar/status/${userId}`);
  }

  async getCalendarEventDetails(eventId: string, calendarId: string = 'primary'): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/v1/calendar/events/${eventId}?calendar_id=${calendarId}`);
  }

  // Documents API endpoints
  async createDocument(document: DocumentCreate): Promise<ApiResponse<Document>> {
    return this.makeRequest('/api/v1/documents', {
      method: 'POST',
      body: JSON.stringify(document),
    });
  }

  async getDocuments(
    projectId?: string,
    limit: number = 50,
    offset: number = 0,
    search?: string
  ): Promise<ApiResponse<{ documents: Document[]; total: number }>> {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (search) params.append('search', search);
    
    return this.makeRequest(`/api/v1/documents?${params.toString()}`);
  }

  async getDocument(documentId: string): Promise<ApiResponse<Document>> {
    return this.makeRequest(`/api/v1/documents/${documentId}`);
  }

  async updateDocument(documentId: string, updates: DocumentUpdate): Promise<ApiResponse<Document>> {
    return this.makeRequest(`/api/v1/documents/${documentId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteDocument(documentId: string): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest(`/api/v1/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async classifyDocument(documentId: string): Promise<ApiResponse<{ classification_result: any }>> {
    return this.makeRequest(`/api/v1/documents/${documentId}/classify`, {
      method: 'POST',
    });
  }

  // Projects API endpoints
  async createProject(project: ProjectCreate): Promise<ApiResponse<Project>> {
    return this.makeRequest('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(project),
    });
  }

  async getProjects(limit: number = 50, offset: number = 0): Promise<ApiResponse<{ projects: Project[]; total: number }>> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    return this.makeRequest(`/api/v1/projects?${params.toString()}`);
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return this.makeRequest(`/api/v1/projects/${projectId}`);
  }

  async updateProject(projectId: string, updates: ProjectUpdate): Promise<ApiResponse<Project>> {
    return this.makeRequest(`/api/v1/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteProject(projectId: string): Promise<ApiResponse<{ message: string }>> {
    return this.makeRequest(`/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  async getProjectDocuments(projectId: string): Promise<ApiResponse<{ documents: Document[]; total: number }>> {
    return this.makeRequest(`/api/v1/projects/${projectId}/documents`);
  }

  // Drive API endpoints
  async setupDriveWebhook(fileId: string): Promise<ApiResponse<{ webhook_id: string }>> {
    return this.makeRequest('/api/v1/drive/webhook', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId }),
    });
  }

  async getDriveFileChanges(fileId: string): Promise<ApiResponse<any[]>> {
    return this.makeRequest(`/api/v1/drive/files/${fileId}/changes`);
  }

  async syncDriveFiles(): Promise<ApiResponse<{ files_synced: number }>> {
    return this.makeRequest('/api/v1/drive/sync', {
      method: 'POST',
    });
  }

  // Email API endpoints
  async processInboundEmail(emailData: any): Promise<ApiResponse<{ document_id: string }>> {
    return this.makeRequest('/api/v1/emails/process', {
      method: 'POST',
      body: JSON.stringify(emailData),
    });
  }

  async getEmailProcessingStatus(emailId: string): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/v1/emails/${emailId}/status`);
  }

  // Classification API endpoints
  async classifyContent(content: string, contentType: string): Promise<ApiResponse<{ classification: any }>> {
    return this.makeRequest('/api/v1/classification/classify', {
      method: 'POST',
      body: JSON.stringify({ content, content_type: contentType }),
    });
  }

  // Attendee API endpoints
  async scheduleAttendeeBot(meetingId: string, botConfig: any): Promise<ApiResponse<{ bot_id: string }>> {
    return this.makeRequest('/api/v1/attendee/schedule', {
      method: 'POST',
      body: JSON.stringify({ meeting_id: meetingId, bot_config: botConfig }),
    });
  }

  async getAttendeeBotStatus(botId: string): Promise<ApiResponse<any>> {
    return this.makeRequest(`/api/v1/attendee/bots/${botId}/status`);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; service: string; version: string }>> {
    return this.makeRequest('/health');
  }

  // API v1 health check
  async apiHealthCheck(): Promise<ApiResponse<{ status: string; version: string; endpoints: string[] }>> {
    return this.makeRequest('/api/v1/health');
  }
}

// Create and export default instance
export const pythonBackendAPI = new PythonBackendAPI();

// Export the class for custom instances
export default PythonBackendAPI;
