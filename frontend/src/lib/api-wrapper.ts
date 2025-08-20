// API Wrapper Utility
// Provides consistent API call patterns and error handling

import { apiEndpoints, config } from '../config';
import { createError, ErrorType, ErrorSeverity, errorUtils } from './error-handling';
import type { ApiResponse } from '../types';

// API call options
export interface ApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

// Default API options
const defaultOptions: Required<ApiCallOptions> = {
  method: 'GET',
  headers: {},
  body: undefined,
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
};

// API wrapper class
export class ApiWrapper {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl?: string, defaultHeaders?: Record<string, string>) {
    this.baseUrl = baseUrl || '';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...defaultHeaders,
    };
  }

  // Make API call with retry logic
  async call<T = any>(
    endpoint: string,
    options: ApiCallOptions = {}
  ): Promise<ApiResponse<T>> {
    const opts = { ...defaultOptions, ...options };
    const url = this.buildUrl(endpoint);
    
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= opts.retries; attempt++) {
      try {
        const response = await this.makeRequest<T>(url, opts);
        
        if (response.success) {
          return response;
        }
        
        // If it's a client error (4xx), don't retry
        if (response.status && response.status >= 400 && response.status < 500) {
          return response;
        }
        
        // For server errors (5xx), retry
        if (attempt < opts.retries) {
          await this.delay(opts.retryDelay * Math.pow(2, attempt)); // Exponential backoff
          continue;
        }
        
        return response;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // If it's a network error, retry
        if (attempt < opts.retries) {
          await this.delay(opts.retryDelay * Math.pow(2, attempt));
          continue;
        }
      }
    }
    
    // All retries failed
    throw createError.network(
      `API call failed after ${opts.retries} retries: ${lastError?.message || 'Unknown error'}`,
      { action: 'api_call', endpoint, method: opts.method }
    );
  }

  // Make the actual HTTP request
  private async makeRequest<T>(
    url: string,
    options: Required<ApiCallOptions>
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout);

    try {
      const response = await fetch(url, {
        method: options.method,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const responseText = await response.text();
      let responseData: T;

      try {
        responseData = responseText ? JSON.parse(responseText) : undefined;
      } catch {
        responseData = responseText as T;
      }

      if (!response.ok) {
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
          message: responseText,
          status: response.status,
          statusText: response.statusText,
          data: responseData,
        };
      }

      return {
        success: true,
        data: responseData,
        status: response.status,
        statusText: response.statusText,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw createError.network(
            'Request timeout',
            { action: 'api_call', endpoint: url, method: options.method }
          );
        }
        throw error;
      }
      
      throw new Error(String(error));
    }
  }

  // Build full URL
  private buildUrl(endpoint: string): string {
    if (endpoint.startsWith('http')) {
      return endpoint;
    }
    return `${this.baseUrl}${endpoint}`;
  }

  // Delay utility for retries
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Convenience methods
  async get<T = any>(endpoint: string, options?: Omit<ApiCallOptions, 'method'>): Promise<ApiResponse<T>> {
    return this.call<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T = any>(endpoint: string, data?: any, options?: Omit<ApiCallOptions, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.call<T>(endpoint, { ...options, method: 'POST', body: data });
  }

  async put<T = any>(endpoint: string, data?: any, options?: Omit<ApiCallOptions, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.call<T>(endpoint, { ...options, method: 'PUT', body: data });
  }

  async delete<T = any>(endpoint: string, options?: Omit<ApiCallOptions, 'method'>): Promise<ApiResponse<T>> {
    return this.call<T>(endpoint, { ...options, method: 'DELETE' });
  }

  async patch<T = any>(endpoint: string, data?: any, options?: Omit<ApiCallOptions, 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.call<T>(endpoint, { ...options, method: 'PATCH', body: data });
  }
}

// Supabase API wrapper (Legacy - Edge Functions migrated to Python backend)
export class SupabaseApiWrapper extends ApiWrapper {
  constructor() {
    super(config.supabase.url);
  }

  // Note: Supabase Edge Functions have been migrated to Python backend
  // Use the Python backend API endpoints instead
  
  // Legacy method - now redirects to Python backend
  async callFunction<T = any>(
    functionName: string,
    data?: any,
    options?: Omit<ApiCallOptions, 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    throw new Error(`Supabase Edge Function ${functionName} has been migrated to Python backend. Please update your code to use the appropriate Python backend endpoint.`);
  }

  // Legacy method - now redirects to Python backend
  async callFunctionWithAuth<T = any>(
    functionName: string,
    accessToken: string,
    data?: any,
    options?: Omit<ApiCallOptions, 'method' | 'body' | 'headers'>
  ): Promise<ApiResponse<T>> {
    throw new Error(`Supabase Edge Function ${functionName} has been migrated to Python backend. Please update your code to use the appropriate Python backend endpoint.`);
  }
}

// Google API wrapper
export class GoogleApiWrapper extends ApiWrapper {
  constructor() {
    super();
  }

  // Call Google Calendar API
  async callCalendarApi<T = any>(
    endpoint: string,
    accessToken: string,
    options?: Omit<ApiCallOptions, 'method' | 'headers'>
  ): Promise<ApiResponse<T>> {
    const url = `${apiEndpoints.google.calendar}${endpoint}`;
    return this.get<T>(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        ...options?.headers,
      },
    });
  }

  // Call Google Gmail API
  async callGmailApi<T = any>(
    endpoint: string,
    accessToken: string,
    options?: Omit<ApiCallOptions, 'method' | 'headers'>
  ): Promise<ApiResponse<T>> {
    const url = `${apiEndpoints.google.gmail}${endpoint}`;
    return this.get<T>(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        ...options?.headers,
      },
    });
  }

  // Call Google Drive API
  async callDriveApi<T = any>(
    endpoint: string,
    accessToken: string,
    options?: Omit<ApiCallOptions, 'method' | 'headers'>
  ): Promise<ApiResponse<T>> {
    const url = `${apiEndpoints.google.drive}${endpoint}`;
    return this.get<T>(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        ...options?.headers,
      },
    });
  }
}

// Create default instances
export const supabaseApi = new SupabaseApiWrapper();
export const googleApi = new GoogleApiWrapper();

// Export default API wrapper
export default new ApiWrapper();
