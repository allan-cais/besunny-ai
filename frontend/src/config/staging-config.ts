// Staging configuration for BeSunny.ai
// Optimized for staging environment testing

export const stagingConfig = {
  // Core application settings
  app: {
    name: 'BeSunny.ai',
    version: '1.0.0',
    environment: 'staging'
  },

  // Backend configuration
  backend: {
    baseUrl: import.meta.env.VITE_PYTHON_BACKEND_URL || 'https://your-staging-backend-url.com',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000
  },

  // Supabase configuration - using the same Supabase instance
  supabase: {
    url: 'https://gkkmaeobxwvramtsjabu.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdra21hZW9ieHd2cmFtdHNqYWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4ODYxMzMsImV4cCI6MjA2NjQ2MjEzM30.S-bzk-Tq1Onm0cVoH-1Vt_UFFx_eGREcq5xyQtEkgXo',
    serviceRoleKey: import.meta.env.VITE_SUPABASE_SERVICE_ROLE_KEY || ''
  },

  // Feature flags
  features: {
    pythonBackend: true,
    analytics: false,
    errorReporting: false
  },

  // Performance settings
  performance: {
    pollingInterval: 30000,
    maxRetries: 3,
    retryDelay: 1000
  },

  // UI limits
  limits: {
    maxDocumentsPerPage: 50,
    maxMeetingsPerPage: 100,
    maxChatMessagesPerPage: 100
  },

  // API configuration
  api: {
    n8nWebhookUrl: 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook',
    openaiApiKey: import.meta.env.VITE_OPENAI_API_KEY || '',
    anthropicApiKey: import.meta.env.VITE_ANTHROPIC_API_KEY || ''
  },

  // Google OAuth configuration
  google: {
    clientId: '797594802013-pcv4l4ckj6d2sql3filtfdnf808m6h7m.apps.googleusercontent.com',
    redirectUri: 'https://your-staging-domain.com/integrations'
  }
};

// Configuration validation
export const validateStagingConfig = (): boolean => {
  const required = [
    stagingConfig.supabase.url,
    stagingConfig.supabase.anonKey
  ];

  for (const value of required) {
    if (!value) {
  
      return false;
    }
  }

  return true;
};

// Health check configuration
export const stagingHealthCheckConfig = {
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
export const stagingApiEndpoints = {
  health: '/health',
  healthStatus: '/health/status',
  healthReady: '/health/ready',
  healthLive: '/health/live',
  frontendTest: '/api/frontend-test'
};

// Error handling configuration
export const stagingErrorConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  timeout: 30000,
  showUserErrors: true,
  logErrors: true
};

// Performance monitoring configuration
export const stagingPerformanceConfig = {
  enableMetrics: true,
  sampleRate: 0.1, // 10% of requests
  maxMetrics: 1000,
  flushInterval: 60000 // 1 minute
};
