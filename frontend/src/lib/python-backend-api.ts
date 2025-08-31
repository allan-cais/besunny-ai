/**
 * Python Backend API Wrapper
 * Optimized for maximum efficiency and reliability
 */

import { config } from '../config';

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

// Global fetch interceptor to catch all HTTP requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  if (typeof url === 'string' && url.includes('backend-staging-6085.up.railway.app')) {
    // Convert HTTP to HTTPS if needed
    if (url.startsWith('http://')) {
      const httpsUrl = url.replace('http://', 'https://');
      console.log('🚨 HTTP TO HTTPS CONVERSION:', {
        originalUrl: url,
        convertedUrl: httpsUrl,
        stack: new Error().stack
      });
      args[0] = httpsUrl;
    }
    
    console.log('🚨 GLOBAL FETCH INTERCEPTOR:', {
      url: args[0],
      isHttps: args[0].toString().startsWith('https://'),
      isHttp: args[0].toString().startsWith('http://'),
      stack: new Error().stack
    });
  }
  return originalFetch.apply(this, args);
};

// Global XMLHttpRequest interceptor to catch any other HTTP requests
const originalXHROpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url, ...args) {
  if (typeof url === 'string' && url.includes('backend-staging-6085.up.railway.app')) {
    console.log('🚨 GLOBAL XMLHttpRequest INTERCEPTOR:', {
      method,
      url,
      isHttps: url.startsWith('https://'),
      isHttp: url.startsWith('http://'),
      stack: new Error().stack
    });
  }
  return originalXHROpen.call(this, method, url, ...args);
};

// DOM observer to catch any HTTP URLs in the page
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        
        // Check for HTTP URLs in various attributes
        const attributes = ['src', 'href', 'data-src', 'data-href'];
        attributes.forEach(attr => {
          const value = element.getAttribute(attr);
          if (value && value.includes('backend-staging-6085.up.railway.app') && value.startsWith('http://')) {
            console.log('🚨 DOM HTTP URL DETECTED:', {
              tagName: element.tagName,
              attribute: attr,
              value,
              element: element.outerHTML,
              stack: new Error().stack
            });
          }
        });
        
        // Check for inline styles with HTTP URLs
        const style = element.getAttribute('style');
        if (style && style.includes('backend-staging-6085.up.railway.app') && style.includes('http://')) {
          console.log('🚨 DOM HTTP URL IN STYLE:', {
            tagName: element.tagName,
            style,
            element: element.outerHTML,
            stack: new Error().stack
          });
        }
      }
    });
  });
});

// Start observing
observer.observe(document.body, {
  childList: true,
  subtree: true,
  attributes: true,
  attributeFilter: ['src', 'href', 'style']
});

// Also check existing elements
document.querySelectorAll('*').forEach(element => {
  const attributes = ['src', 'href', 'data-src', 'data-href'];
  attributes.forEach(attr => {
    const value = element.getAttribute(attr);
    if (value && value.includes('backend-staging-6085.up.railway.app') && value.startsWith('http://')) {
      console.log('🚨 EXISTING DOM HTTP URL:', {
        tagName: element.tagName,
        attribute: attr,
        value,
        element: element.outerHTML
      });
    }
  });
});

// Image interceptor
const originalImage = window.Image;
(window as any).Image = function(...args: any[]) {
  const img = new originalImage(...args);
  const originalSrc = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  Object.defineProperty(img, 'src', {
    set: function(value) {
      if (typeof value === 'string' && value.includes('backend-staging-6085.up.railway.app') && value.startsWith('http://')) {
        console.log('🚨 IMAGE HTTP URL:', {
          url: value,
          stack: new Error().stack
        });
      }
      return originalSrc.set.call(this, value);
    },
    get: function() {
      return originalSrc.get.call(this);
    }
  });
  return img;
};

// EventSource interceptor
const originalEventSource = window.EventSource;
(window as any).EventSource = function(url: string, ...args: any[]) {
  if (typeof url === 'string' && url.includes('backend-staging-6085.up.railway.app')) {
    console.log('🚨 EVENTSOURCE INTERCEPTOR:', {
      url,
      isHttps: url.startsWith('https://'),
      isHttp: url.startsWith('http://'),
      stack: new Error().stack
    });
  }
  return new originalEventSource(url, ...args);
};

export class PythonBackendAPI {
  private baseUrl: string;
  private timeout: number;
  private retries: number;
  private retryDelay: number;
  private instanceId: number; // Added for instance tracking

  constructor() {
    // Use dynamic configuration instead of hardcoded production config
    this.baseUrl = config.pythonBackend.url;
    this.timeout = config.pythonBackend.timeout;
    this.retries = config.pythonBackend.retries;
    this.retryDelay = config.pythonBackend.retryDelay;
    this.instanceId = Math.floor(Math.random() * 1000); // Simple instance ID
    
    // Debug logging
    console.log('🚀 PythonBackendAPI Constructor:');
    console.log('  Config URL:', config.pythonBackend.url);
    console.log('  Final Base URL:', this.baseUrl);
    console.log('  Timeout:', this.timeout);
    console.log('  Retries:', this.retries);
    console.log('  Retry Delay:', this.retryDelay);
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Debug: Log the exact URL being used
    console.log(`🌐 PythonBackendAPI makeRequest (Instance #${this.instanceId}):`);
    console.log('  Base URL:', this.baseUrl);
    console.log('  Endpoint:', endpoint);
    console.log('  Full URL:', url);
    console.log('  Is HTTPS:', url.startsWith('https://'));
    
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
    return this.makeRequestWithRetry('/api/v1/ai/project-onboarding', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
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
