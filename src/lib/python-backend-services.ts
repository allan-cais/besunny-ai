// Python Backend Services
// Comprehensive service layer that replaces Supabase edge functions with Python backend API calls

import { config } from '../config';
import { PythonBackendAPI } from './python-backend-api';
import type { 
  User, 
  Project, 
  Document, 
  Meeting, 
  ChatMessage, 
  ChatSession,
  GoogleCalendarEvent,
  CalendarSyncRequest,
  DocumentCreate,
  DocumentUpdate,
  ProjectCreate,
  ProjectUpdate,
  BotDeploymentRequest,
  ClassificationRequest,
  EmailProcessingResult
} from '../types';

// API response wrapper
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

// Python Backend Services
export class PythonBackendServices {
  private api: PythonBackendAPI;

  constructor() {
    this.api = new PythonBackendAPI();
  }

  // Set authentication token
  setAuthToken(token: string): void {
    this.api.setAuthToken(token);
  }

  // Clear authentication token
  clearAuthToken(): void {
    this.api.clearAuthToken();
  }

  // ============================================================================
  // AUTHENTICATION SERVICES
  // ============================================================================

  /**
   * Handle Google OAuth callback
   */
  async handleGoogleOAuthCallback(code: string): Promise<ApiResponse<any>> {
    return this.api.post('/auth/google/oauth/callback', { code });
  }

  /**
   * Refresh Google OAuth tokens
   */
  async refreshGoogleOAuthTokens(userId: string): Promise<ApiResponse<any>> {
    return this.api.post(`/auth/google/oauth/refresh?user_id=${userId}`);
  }

  /**
   * Exchange Google token
   */
  async exchangeGoogleToken(code: string): Promise<ApiResponse<any>> {
    return this.api.post('/auth/google/oauth/callback', { code });
  }

  // ============================================================================
  // PROJECT SERVICES
  // ============================================================================

  /**
   * Create a new project
   */
  async createProject(project: ProjectCreate): Promise<ApiResponse<Project>> {
    return this.api.post('/projects', project);
  }

  /**
   * Get all projects for the current user
   */
  async getProjects(limit: number = 100, offset: number = 0): Promise<ApiResponse<Project[]>> {
    return this.api.get(`/projects?limit=${limit}&offset=${offset}`);
  }

  /**
   * Get a specific project by ID
   */
  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return this.api.get(`/projects/${projectId}`);
  }

  /**
   * Update a project
   */
  async updateProject(projectId: string, updates: ProjectUpdate): Promise<ApiResponse<Project>> {
    return this.api.put(`/projects/${projectId}`, updates);
  }

  /**
   * Delete a project
   */
  async deleteProject(projectId: string): Promise<ApiResponse<void>> {
    return this.api.delete(`/projects/${projectId}`);
  }

  /**
   * Process project onboarding with AI
   */
  async processProjectOnboarding(payload: {
    project_id: string;
    user_id: string;
    summary: {
      project_name: string;
      overview: string;
      keywords: string[];
      deliverables: string;
      contacts: {
        internal_lead: string;
        agency_lead: string;
        client_lead: string;
      };
      shoot_date: string;
      location: string;
      references: string;
    };
  }): Promise<ApiResponse<any>> {
    return this.api.post('/ai/projects/onboarding', payload);
  }

  // ============================================================================
  // DOCUMENT SERVICES
  // ============================================================================

  /**
   * Create a new document
   */
  async createDocument(document: DocumentCreate): Promise<ApiResponse<Document>> {
    return this.api.post('/documents', document);
  }

  /**
   * Get documents for a project
   */
  async getProjectDocuments(projectId: string, limit: number = 50, offset: number = 0): Promise<ApiResponse<Document[]>> {
    return this.api.get(`/documents?project_id=${projectId}&limit=${limit}&offset=${offset}`);
  }

  /**
   * Get a specific document by ID
   */
  async getDocument(documentId: string): Promise<ApiResponse<Document>> {
    return this.api.get(`/documents/${documentId}`);
  }

  /**
   * Update a document
   */
  async updateDocument(documentId: string, updates: DocumentUpdate): Promise<ApiResponse<Document>> {
    return this.api.put(`/documents/${documentId}`, updates);
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<ApiResponse<void>> {
    return this.api.delete(`/documents/${documentId}`);
  }

  /**
   * Classify a document using AI
   */
  async classifyDocument(request: ClassificationRequest): Promise<ApiResponse<any>> {
    return this.api.post('/classification/documents/classify', request);
  }

  /**
   * Analyze document content
   */
  async analyzeDocument(content: string, analysisType: string = 'comprehensive', projectContext?: string): Promise<ApiResponse<any>> {
    return this.api.post('/ai/documents/analyze', {
      content,
      analysis_type: analysisType,
      project_context: projectContext
    });
  }

  // ============================================================================
  // ATTENDEE SERVICES
  // ============================================================================

  /**
   * Send a bot to a meeting
   */
  async sendBotToMeeting(request: BotDeploymentRequest): Promise<ApiResponse<any>> {
    return this.api.post('/attendee/send-bot', request);
  }

  /**
   * Get bot status
   */
  async getBotStatus(botId: string): Promise<ApiResponse<any>> {
    return this.api.get(`/attendee/bot-status/${botId}`);
  }

  /**
   * Get meeting transcript
   */
  async getTranscript(botId: string): Promise<ApiResponse<any>> {
    return this.api.get(`/attendee/transcript/${botId}`);
  }

  /**
   * Poll all meetings
   */
  async pollAllMeetings(): Promise<ApiResponse<any[]>> {
    return this.api.post('/attendee/poll-all');
  }

  /**
   * Auto-schedule bots
   */
  async autoScheduleBots(forceSchedule: boolean = false): Promise<ApiResponse<any>> {
    return this.api.post('/attendee/auto-schedule', { force_schedule: forceSchedule });
  }

  // ============================================================================
  // CALENDAR SERVICES
  // ============================================================================

  /**
   * Get calendar events
   */
  async getCalendarEvents(limit: number = 100, offset: number = 0): Promise<ApiResponse<GoogleCalendarEvent[]>> {
    return this.api.get(`/calendar/events?limit=${limit}&offset=${offset}`);
  }

  /**
   * Sync calendar
   */
  async syncCalendar(request: CalendarSyncRequest): Promise<ApiResponse<any>> {
    return this.api.post('/calendar/sync', request);
  }

  /**
   * Get calendar webhook status
   */
  async getCalendarWebhookStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/calendar/webhook/status');
  }

  /**
   * Renew calendar webhooks
   */
  async renewCalendarWebhooks(): Promise<ApiResponse<any>> {
    return this.api.post('/calendar/webhook/renew');
  }

  // ============================================================================
  // DRIVE SERVICES
  // ============================================================================

  /**
   * Get drive files
   */
  async getDriveFiles(limit: number = 100, offset: number = 0): Promise<ApiResponse<any[]>> {
    return this.api.get(`/drive/files?limit=${limit}&offset=${offset}`);
  }

  /**
   * Subscribe to drive file changes
   */
  async subscribeToDriveFile(fileId: string): Promise<ApiResponse<any>> {
    return this.api.post('/drive/subscription', { file_id: fileId });
  }

  /**
   * Get drive webhook status
   */
  async getDriveWebhookStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/drive/webhook/status');
  }

  /**
   * Renew drive watches
   */
  async renewDriveWatches(): Promise<ApiResponse<any>> {
    return this.api.post('/drive/watch/renew');
  }

  // ============================================================================
  // EMAIL SERVICES
  // ============================================================================

  /**
   * Process inbound emails
   */
  async processInboundEmails(messages: any[]): Promise<ApiResponse<EmailProcessingResult[]>> {
    return this.api.post('/emails/process', messages);
  }

  /**
   * Get emails
   */
  async getEmails(projectId?: string, limit: number = 100, offset: number = 0): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    if (projectId) params.append('project_id', projectId);
    
    return this.api.get(`/emails?${params.toString()}`);
  }

  /**
   * Setup Gmail watch
   */
  async setupGmailWatch(): Promise<ApiResponse<any>> {
    return this.api.post('/gmail-watch/setup');
  }

  /**
   * Get Gmail watch status
   */
  async getGmailWatchStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/gmail-watch/status');
  }

  // ============================================================================
  // USER SERVICES
  // ============================================================================

  /**
   * Set username
   */
  async setUsername(username: string): Promise<ApiResponse<any>> {
    return this.api.post('/user/set-username', { username });
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.api.get('/user/me');
  }

  /**
   * Update user profile
   */
  async updateUserProfile(updates: Partial<User>): Promise<ApiResponse<User>> {
    return this.api.put('/user/me', updates);
  }

  // ============================================================================
  // AI SERVICES
  // ============================================================================

  /**
   * Get AI service status
   */
  async getAIStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/ai/status');
  }

  /**
   * Process AI request
   */
  async processAIRequest(request: any): Promise<ApiResponse<any>> {
    return this.api.post('/ai/process', request);
  }

  /**
   * Get embeddings for text
   */
  async getEmbeddings(text: string): Promise<ApiResponse<any>> {
    return this.api.post('/embeddings/generate', { text });
  }

  // ============================================================================
  // MICROSERVICES STATUS
  // ============================================================================

  /**
   * Get microservices status
   */
  async getMicroservicesStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/microservices/registry/status');
  }

  /**
   * Get API gateway status
   */
  async getAPIGatewayStatus(): Promise<ApiResponse<any>> {
    return this.api.get('/microservices/gateway/status');
  }

  // ============================================================================
  // HEALTH CHECKS
  // ============================================================================

  /**
   * Check backend health
   */
  async checkHealth(): Promise<ApiResponse<any>> {
    return this.api.get('/health');
  }

  /**
   * Check AI services health
   */
  async checkAIHealth(): Promise<ApiResponse<any>> {
    return this.api.get('/health/ai');
  }

  /**
   * Check microservices health
   */
  async checkMicroservicesHealth(): Promise<ApiResponse<any>> {
    return this.api.get('/health/microservices');
  }
}

// Export singleton instance
export const pythonBackendServices = new PythonBackendServices();
