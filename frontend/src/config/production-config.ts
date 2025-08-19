// Production configuration for BeSunny.ai
// Optimized for maximum efficiency and reliability

export const productionConfig = {
  // Core application settings
  app: {
    name: 'BeSunny.ai',
    version: '1.0.0',
    environment: 'production'
  },

  // Backend configuration
  backend: {
    baseUrl: import.meta.env.VITE_PYTHON_BACKEND_URL || 'http://localhost:8000',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000
  },

  // Supabase configuration
  supabase: {
    url: import.meta.env.VITE_SUPABASE_URL || '',
    anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
    serviceRoleKey: import.meta.env.VITE_SUPABASE_SERVICE_ROLE_KEY || ''
  },

  // Feature flags
  features: {
    pythonBackend: import.meta.env.VITE_ENABLE_PYTHON_BACKEND === 'true',
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    errorReporting: import.meta.env.VITE_ENABLE_ERROR_REPORTING === 'true'
  },

  // Performance settings
  performance: {
    pollingInterval: parseInt(import.meta.env.VITE_POLLING_INTERVAL_MS || '30000'),
    maxRetries: parseInt(import.meta.env.VITE_MAX_RETRIES || '3'),
    retryDelay: parseInt(import.meta.env.VITE_RETRY_DELAY_MS || '1000')
  },

  // UI limits
  limits: {
    maxDocumentsPerPage: parseInt(import.meta.env.VITE_MAX_DOCUMENTS_PER_PAGE || '50'),
    maxMeetingsPerPage: parseInt(import.meta.env.VITE_MAX_MEETINGS_PER_PAGE || '100'),
    maxChatMessagesPerPage: parseInt(import.meta.env.VITE_MAX_CHAT_MESSAGES_PER_PAGE || '100')
  }
};

// Configuration validation
export const validateConfig = (): boolean => {
  const required = [
    productionConfig.supabase.url,
    productionConfig.supabase.anonKey
  ];

  for (const value of required) {
    if (!value) {
      console.error('Missing required configuration:', value);
      return false;
    }
  }

  return true;
};

// Health check configuration - optimized for reliability
export const healthCheckConfig = {
  interval: 30000, // 30 seconds
  timeout: 10000,  // 10 seconds
  retries: 3,
  endpoints: [
    '/health',
    '/health/status',
    '/health/ready',
    '/health/live'
  ]
};

// API endpoints configuration
export const apiEndpoints = {
  health: '/health',
  healthStatus: '/health/status',
  healthReady: '/health/ready',
  healthLive: '/health/live',
  frontendTest: '/api/frontend-test'
};

// Error handling configuration
export const errorConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  timeout: 30000,
  showUserErrors: true,
  logErrors: true
};

// Performance monitoring configuration
export const performanceConfig = {
  enableMetrics: true,
  sampleRate: 0.1, // 10% of requests
  maxMetrics: 1000,
  flushInterval: 60000 // 1 minute
};

