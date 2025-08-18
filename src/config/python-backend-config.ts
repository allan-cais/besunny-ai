// Python Backend Configuration
// Centralizes configuration for Python backend integration

export const PYTHON_BACKEND_CONFIG = {
  // Base configuration with safe fallbacks
  baseUrl: import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000',
  timeout: parseInt(import.meta.env.VITE_PYTHON_BACKEND_TIMEOUT || '30000') || 30000,
  retries: parseInt(import.meta.env.VITE_PYTHON_BACKEND_RETRIES || '3') || 3,
  retryDelay: parseInt(import.meta.env.VITE_PYTHON_BACKEND_RETRY_DELAY || '1000') || 1000,
  
  // Feature flags with safe fallbacks
  isEnabled: import.meta.env.VITE_ENABLE_PYTHON_BACKEND === 'true',
  
  // API endpoints with safe fallbacks
  endpoints: {
    base: import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000',
    api: `${import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000'}/api/v1`,
    health: `${import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000'}/health`,
    websockets: `${import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000'}/ws`,
  },
  
  // Service-specific endpoints
  services: {
    auth: {
      googleOAuth: '/auth/google/oauth/callback',
      googleTokenRefresh: '/auth/google/oauth/refresh',
    },
    projects: '/projects',
    documents: '/documents',
    attendee: '/attendee',
    calendar: '/calendar',
    drive: '/drive',
    emails: '/emails',
    classification: '/classification',
    ai: '/ai',
    embeddings: '/embeddings',
    meetingIntelligence: '/meeting-intelligence',
    user: '/user',
    gmailWatch: '/gmail-watch',
    driveSubscription: '/drive-subscription',
    microservices: '/microservices',
  },
  
  // Health check configuration
  health: {
    checkInterval: 30000, // 30 seconds
    timeout: 10000, // 10 seconds
    retries: 3,
  },
  
  // Authentication configuration
  auth: {
    tokenHeader: 'Authorization',
    tokenPrefix: 'Bearer',
    refreshThreshold: 5 * 60 * 1000, // 5 minutes before expiry
  },
  
  // Error handling configuration
  errors: {
    maxRetries: 3,
    backoffMultiplier: 2,
    maxBackoffDelay: 30000, // 30 seconds
  },
} as const;

// Helper functions with safe fallbacks
export const getPythonBackendUrl = (endpoint: string): string => {
  try {
    return `${PYTHON_BACKEND_CONFIG.baseUrl}${endpoint}`;
  } catch (error) {
    console.warn('⚠️ Error building Python backend URL:', error);
    return `http://localhost:8000${endpoint}`;
  }
};

export const getPythonBackendApiUrl = (endpoint: string): string => {
  try {
    return `${PYTHON_BACKEND_CONFIG.endpoints.api}${endpoint}`;
  } catch (error) {
    console.warn('⚠️ Error building Python backend API URL:', error);
    return `http://localhost:8000/api/v1${endpoint}`;
  }
};

export const isPythonBackendEnabled = (): boolean => {
  try {
    return PYTHON_BACKEND_CONFIG.isEnabled || false;
  } catch (error) {
    console.warn('⚠️ Error checking Python backend status:', error);
    return false;
  }
};

export const isPythonBackendAvailable = async (): Promise<boolean> => {
  try {
    if (!isPythonBackendEnabled()) {
      return false;
    }
    
    const response = await fetch(PYTHON_BACKEND_CONFIG.endpoints.health, {
      method: 'GET',
      signal: AbortSignal.timeout(PYTHON_BACKEND_CONFIG.health.timeout),
    });
    return response.ok;
  } catch (error) {
    console.warn('⚠️ Python backend health check failed:', error);
    return false;
  }
};
