/**
 * Python Backend Services Wrapper
 * Optimized for maximum efficiency and reliability
 */

import { PythonBackendAPI, ApiResponse, UserProfile, UserPreferences, Project, AIResponse } from './python-backend-api';

export interface BackendHealthStatus {
  isConnected: boolean;
  isHealthy: boolean;
  lastCheck: number;
  responseTime: number;
  error?: string;
}

export interface BackendMetrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  lastRequestTime: number;
}

export class PythonBackendServices {
  private api: PythonBackendAPI;
  private healthStatus: BackendHealthStatus;
  private metrics: BackendMetrics;
  private healthCheckInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.api = new PythonBackendAPI();
    this.healthStatus = {
      isConnected: false,
      isHealthy: false,
      lastCheck: 0,
      responseTime: 0,
    };
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      lastRequestTime: 0,
    };
  }

  // ============================================================================
  // INITIALIZATION & HEALTH MONITORING
  // ============================================================================

  async initialize(): Promise<void> {
    try {
      // Initial health check
      await this.checkHealth();
      
      // Start periodic health monitoring
      this.startHealthMonitoring();
      
  
    } catch (error) {
      throw error;
    }
  }

  async destroy(): Promise<void> {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    
    this.healthStatus = {
      isConnected: false,
      isHealthy: false,
      lastCheck: 0,
      responseTime: 0,
    };
    

  }

  private startHealthMonitoring(): void {
    // Check health every 30 seconds
    this.healthCheckInterval = setInterval(async () => {
      try {
        await this.checkHealth();
      } catch (error) {

      }
    }, 30000);
  }

  // ============================================================================
  // HEALTH CHECKS
  // ============================================================================

  async checkHealth(): Promise<BackendHealthStatus> {
    const startTime = Date.now();
    
    try {
      const response = await this.api.checkHealth();
      const responseTime = Date.now() - startTime;
      
      this.healthStatus = {
        isConnected: true,
        isHealthy: response.success,
        lastCheck: Date.now(),
        responseTime,
        error: response.success ? undefined : response.error,
      };
      
      this.updateMetrics(response.success, responseTime);
      
      return this.healthStatus;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      this.healthStatus = {
        isConnected: false,
        isHealthy: false,
        lastCheck: Date.now(),
        responseTime,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
      
      this.updateMetrics(false, responseTime);
      
      return this.healthStatus;
    }
  }

  async checkComprehensiveHealth(): Promise<{
    main: ApiResponse;
    status: ApiResponse;
    ready: ApiResponse;
    live: ApiResponse;
    frontendTest: ApiResponse;
  }> {
    const [main, status, ready, live, frontendTest] = await Promise.allSettled([
      this.api.checkHealth(),
      this.api.checkHealthStatus(),
      this.api.checkHealthReady(),
      this.api.checkHealthLive(),
      this.api.checkFrontendTest(),
    ]);

    return {
      main: main.status === 'fulfilled' ? main.value : { success: false, error: 'Check failed' },
      status: status.status === 'fulfilled' ? status.value : { success: false, error: 'Check failed' },
      ready: ready.status === 'fulfilled' ? ready.value : { success: false, error: 'Check failed' },
      live: live.status === 'fulfilled' ? live.value : { success: false, error: 'Check failed' },
      frontendTest: frontendTest.status === 'fulfilled' ? frontendTest.value : { success: false, error: 'Check failed' },
    };
  }

  getHealthStatus(): BackendHealthStatus {
    return { ...this.healthStatus };
  }

  getMetrics(): BackendMetrics {
    return { ...this.metrics };
  }

  private updateMetrics(success: boolean, responseTime: number): void {
    this.metrics.totalRequests++;
    
    if (success) {
      this.metrics.successfulRequests++;
    } else {
      this.metrics.failedRequests++;
    }
    
    // Update average response time
    const totalTime = this.metrics.averageResponseTime * (this.metrics.totalRequests - 1) + responseTime;
    this.metrics.averageResponseTime = totalTime / this.metrics.totalRequests;
    
    this.metrics.lastRequestTime = Date.now();
  }

  // ============================================================================
  // USER MANAGEMENT
  // ============================================================================

  async getUserProfile(userId: string): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await this.api.getUserProfile(userId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async updateUserProfile(userId: string, data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await this.api.updateUserProfile(userId, data);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async getUserPreferences(userId: string): Promise<ApiResponse<UserPreferences>> {
    try {
      const response = await this.api.getUserPreferences(userId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async updateUserPreferences(userId: string, data: Partial<UserPreferences>): Promise<ApiResponse<UserPreferences>> {
    try {
      const response = await this.api.updateUserPreferences(userId, data);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  // ============================================================================
  // PROJECT MANAGEMENT
  // ============================================================================

  async getProjects(userId: string): Promise<ApiResponse<Project[]>> {
    try {
      const response = await this.api.getProjects(userId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    try {
      const response = await this.api.getProject(projectId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async createProject(data: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Project>> {
    try {
      const response = await this.api.createProject(data);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async updateProject(projectId: string, data: Partial<Project>): Promise<ApiResponse<Project>> {
    try {
      const response = await this.api.updateProject(projectId, data);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async deleteProject(projectId: string): Promise<ApiResponse> {
    try {
      const response = await this.api.deleteProject(projectId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  // ============================================================================
  // AI SERVICES
  // ============================================================================

  async generateAIResponse(prompt: string, userId: string, model?: string): Promise<ApiResponse<AIResponse>> {
    try {
      const response = await this.api.generateAIResponse(prompt, userId, model);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async getAIHistory(userId: string, limit = 50): Promise<ApiResponse<AIResponse[]>> {
    try {
      const response = await this.api.getAIHistory(userId, limit);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

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
    try {
      const response = await this.api.processProjectOnboarding(payload);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  // ============================================================================
  // DOCUMENT MANAGEMENT
  // ============================================================================

  async getDocuments(userId: string, projectId?: string, limit = 50): Promise<ApiResponse<any[]>> {
    try {
      const response = await this.api.getDocuments(userId, projectId, limit);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  async uploadDocument(file: File, userId: string, projectId?: string): Promise<ApiResponse<any>> {
    try {
      const response = await this.api.uploadDocument(file, userId, projectId);
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  async ping(): Promise<ApiResponse> {
    try {
      const response = await this.api.ping();
      this.updateMetrics(response.success, 0);
      return response;
    } catch (error) {
      this.updateMetrics(false, 0);
      throw error;
    }
  }

  getBaseUrl(): string {
    return this.api.getBaseUrl();
  }

  isHealthy(): boolean {
    return this.healthStatus.isHealthy;
  }

  isConnected(): boolean {
    return this.healthStatus.isConnected;
  }

  getLastHealthCheck(): number {
    return this.healthStatus.lastCheck;
  }

  getError(): string | undefined {
    return this.healthStatus.error;
  }
}

// Export singleton instance
export const pythonBackendServices = new PythonBackendServices();
