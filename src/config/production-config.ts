/**
 * Production Configuration for BeSunny.ai Frontend
 * Connects to deployed v16 backend on Railway
 */

export interface ProductionConfig {
  backend: {
    baseUrl: string;
    healthEndpoint: string;
    apiVersion: string;
  };
  frontend: {
    buildMode: 'staging' | 'production';
    analytics: boolean;
    errorReporting: boolean;
  };
  features: {
    userManagement: boolean;
    projectManagement: boolean;
    aiOrchestration: boolean;
    realTimeUpdates: boolean;
  };
}

// Get the current Railway backend URL from environment
const getBackendUrl = (): string => {
  // Check if we're in production/staging environment
  if (import.meta.env.PROD) {
    // In production, use the Railway URL
    return import.meta.env.VITE_RAILWAY_BACKEND_URL || 'https://besunny-ai-production.up.railway.app';
  } else if (import.meta.env.MODE === 'staging') {
    // In staging, use staging Railway URL
    return import.meta.env.VITE_RAILWAY_STAGING_URL || 'https://besunny-ai-staging.up.railway.app';
  } else {
    // In development, use local backend
    return 'http://localhost:8000';
  }
};

// Production configuration
export const productionConfig: ProductionConfig = {
  backend: {
    baseUrl: getBackendUrl(),
    healthEndpoint: '/health',
    apiVersion: 'v1',
  },
  frontend: {
    buildMode: import.meta.env.MODE === 'production' ? 'production' : 'staging',
    analytics: import.meta.env.PROD,
    errorReporting: import.meta.env.PROD,
  },
  features: {
    userManagement: true,
    projectManagement: true,
    aiOrchestration: true,
    realTimeUpdates: true,
  },
};

// Environment-specific overrides
export const getConfig = (): ProductionConfig => {
  const config = { ...productionConfig };
  
  // Override for development
  if (import.meta.env.DEV) {
    config.backend.baseUrl = 'http://localhost:8000';
    config.frontend.analytics = false;
    config.frontend.errorReporting = false;
  }
  
  return config;
};

// Configuration validation
export const validateConfig = (): boolean => {
  const config = getConfig();
  
  if (!config.backend.baseUrl) {
    console.error('Backend URL is required');
    return false;
  }
  
  if (!config.backend.baseUrl.startsWith('http')) {
    console.error('Backend URL must be a valid HTTP URL');
    return false;
  }
  
  return true;
};

// Health check configuration
export const healthCheckConfig = {
  interval: 30000, // 30 seconds
  timeout: 10000,  // 10 seconds
  retries: 3,
  endpoints: [
    '/health',
    '/status',
    '/api/frontend-test'
  ]
};

// API endpoints configuration
export const apiEndpoints = {
  health: '/health',
  status: '/status',
  frontendTest: '/api/frontend-test',
  user: {
    profile: '/v1/user/profile',
    preferences: '/v1/user/preferences',
    update: '/v1/user/update',
  },
  project: {
    list: '/v1/projects',
    create: '/v1/projects',
    get: '/v1/projects',
    update: '/v1/projects',
    delete: '/v1/projects',
    members: '/v1/projects/members',
  },
  ai: {
    orchestrate: '/v1/ai/orchestrate',
    history: '/v1/ai/history',
  },
  performance: {
    health: '/v1/performance/health',
    services: '/v1/performance/services',
  }
};

// Export configuration getters
export const getBackendConfig = () => getConfig().backend;
export const getFrontendConfig = () => getConfig().frontend;
export const getFeatureConfig = () => getConfig().features;

// Log configuration in development
if (import.meta.env.DEV) {
  console.log('🔧 Production Configuration:', {
    backend: getConfig().backend,
    frontend: getConfig().frontend,
    features: getConfig().features,
  });
}
