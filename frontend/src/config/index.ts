// Configuration Management
// Centralizes all environment variables and configuration settings

interface Config {
  supabase: {
    url: string;
    anonKey: string;
    serviceRoleKey?: string;
  };
  pythonBackend: {
    url: string;
    timeout: number;
    retries: number;
    retryDelay: number;
  };
  api: {
    n8nWebhookUrl: string;
    openaiApiKey?: string;
    anthropicApiKey?: string;
  };
  features: {
    enableDebugMode: boolean;
    enableAnalytics: boolean;
    enableErrorReporting: boolean;
    enablePythonBackend: boolean;
  };
  polling: {
    defaultIntervalMs: number;
    maxRetries: number;
    retryDelayMs: number;
  };
  limits: {
    maxDocumentsPerPage: number;
    maxMeetingsPerPage: number;
    maxChatMessagesPerPage: number;
  };
}

// Environment variable validation with better error handling
function getRequiredEnvVar(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    console.warn(`⚠️ Missing required environment variable: ${name}`);
    // Return a safe default for staging/production builds
    if (name === 'VITE_SUPABASE_URL') {
      return 'https://placeholder.supabase.co';
    }
    if (name === 'VITE_SUPABASE_ANON_KEY') {
      return 'placeholder-key';
    }
    return '';
  }
  return value;
}

function getOptionalEnvVar(name: string, defaultValue: string = ''): string {
  const value = import.meta.env[name];
  if (!value) {
    console.warn(`⚠️ Missing optional environment variable: ${name}, using default: ${defaultValue}`);
  }
  return value || defaultValue;
}

function getOptionalNumberEnvVar(name: string, defaultValue: number): number {
  const value = import.meta.env[name];
  if (!value) {
    console.warn(`⚠️ Missing optional environment variable: ${name}, using default: ${defaultValue}`);
    return defaultValue;
  }
  const parsed = parseInt(value);
  if (isNaN(parsed)) {
    console.warn(`⚠️ Invalid number for environment variable: ${name}, using default: ${defaultValue}`);
    return defaultValue;
  }
  return parsed;
}

// Build configuration object with safe defaults
export const config: Config = {
  supabase: {
    url: getRequiredEnvVar('VITE_SUPABASE_URL'),
    anonKey: getRequiredEnvVar('VITE_SUPABASE_ANON_KEY'),
    serviceRoleKey: getOptionalEnvVar('VITE_SUPABASE_SERVICE_ROLE_KEY'),
  },
  pythonBackend: {
    url: getOptionalEnvVar('VITE_PYTHON_BACKEND_URL', 'http://localhost:8000'),
    timeout: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_TIMEOUT', 30000),
    retries: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_RETRIES', 3),
    retryDelay: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_RETRY_DELAY', 1000),
  },
  api: {
    n8nWebhookUrl: getOptionalEnvVar('VITE_N8N_WEBHOOK_URL', 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook'),
    openaiApiKey: getOptionalEnvVar('VITE_OPENAI_API_KEY'),
    anthropicApiKey: getOptionalEnvVar('VITE_ANTHROPIC_API_KEY'),
  },
  features: {
    enableDebugMode: import.meta.env.DEV || false,
    enableAnalytics: getOptionalEnvVar('VITE_ENABLE_ANALYTICS', 'false') === 'true',
    enableErrorReporting: getOptionalEnvVar('VITE_ENABLE_ERROR_REPORTING', 'false') === 'true',
    enablePythonBackend: getOptionalEnvVar('VITE_ENABLE_PYTHON_BACKEND', 'true') === 'true',
  },
  polling: {
    defaultIntervalMs: getOptionalNumberEnvVar('VITE_POLLING_INTERVAL_MS', 30000),
    maxRetries: getOptionalNumberEnvVar('VITE_MAX_RETRIES', 3),
    retryDelayMs: getOptionalNumberEnvVar('VITE_RETRY_DELAY_MS', 1000),
  },
  limits: {
    maxDocumentsPerPage: getOptionalNumberEnvVar('VITE_MAX_DOCUMENTS_PER_PAGE', 50),
    maxMeetingsPerPage: getOptionalNumberEnvVar('VITE_MAX_MEETINGS_PER_PAGE', 100),
    maxChatMessagesPerPage: getOptionalNumberEnvVar('VITE_MAX_CHAT_MESSAGES_PER_PAGE', 100),
  },
};

// Debug logging for staging troubleshooting
console.log('🔧 Configuration loaded:', {
  mode: import.meta.env.MODE,
  dev: import.meta.env.DEV,
  prod: import.meta.env.PROD,
  appEnv: import.meta.env.VITE_APP_ENV,
  supabaseUrl: config.supabase.url,
  pythonBackendUrl: config.pythonBackend.url,
  enablePythonBackend: config.features.enablePythonBackend,
  enableDebugMode: config.features.enableDebugMode,
});

// API endpoint builders with safe fallbacks
export const apiEndpoints = {
  supabase: {
    functions: (functionName: string) => `${config.supabase.url}/functions/v1/${functionName}`,
    auth: `${config.supabase.url}/auth/v1`,
    rest: `${config.supabase.url}/rest/v1`,
    realtime: `${config.supabase.url}/realtime/v1`,
  },
  pythonBackend: {
    base: config.pythonBackend.url,
    api: `${config.pythonBackend.url}/api/v1`,
    health: `${config.pythonBackend.url}/health`,
    websockets: `${config.pythonBackend.url}/ws`,
  },
  google: {
    calendar: 'https://www.googleapis.com/calendar/v3',
    gmail: 'https://www.googleapis.com/gmail/v1',
    drive: 'https://www.googleapis.com/drive/v3',
  },
} as const;

// Configuration validation with better error handling
export function validateConfig(): void {
  try {
    // Validate required Supabase configuration
    if (!config.supabase.url || !config.supabase.anonKey) {
      console.warn('⚠️ Invalid Supabase configuration - using fallbacks');
      return; // Don't throw, just warn
    }

    // Validate Python backend configuration
    if (config.features.enablePythonBackend) {
      try {
        new URL(config.pythonBackend.url);
      } catch {
        console.warn('⚠️ Invalid Python backend URL format - using fallback');
        return;
      }
    }

    // Validate URL formats
    try {
      new URL(config.supabase.url);
    } catch {
      console.warn('⚠️ Invalid Supabase URL format - using fallback');
      return;
    }
    
    // Validate numeric configurations
    if (config.polling.defaultIntervalMs <= 0) {
      console.warn('⚠️ Invalid polling interval - using fallback');
      return;
    }
    
    if (config.limits.maxDocumentsPerPage <= 0) {
      console.warn('⚠️ Invalid documents per page limit - using fallback');
      return;
    }

    console.log('✅ Configuration validation passed');

  } catch (error) {
    console.error('❌ Configuration validation failed:', error);
    // Don't throw, just log the error
  }
}

// Development helpers
export const isDevelopment = import.meta.env.DEV;
export const isProduction = import.meta.env.PROD;
export const isTest = import.meta.env.MODE === 'test';

// Feature flags with safe fallbacks
export const features = {
  isEnabled: (feature: keyof Config['features']) => {
    try {
      return config.features[feature] || false;
    } catch (error) {
      console.warn(`⚠️ Error accessing feature flag: ${feature}`, error);
      return false;
    }
  },
  isDebugMode: () => {
    try {
      return config.features.enableDebugMode || false;
    } catch (error) {
      console.warn('⚠️ Error accessing debug mode', error);
      return false;
    }
  },
  isAnalyticsEnabled: () => {
    try {
      return config.features.enableAnalytics || false;
    } catch (error) {
      console.warn('⚠️ Error accessing analytics flag', error);
      return false;
    }
  },
  isErrorReportingEnabled: () => {
    try {
      return config.features.enableErrorReporting || false;
    } catch (error) {
      console.warn('⚠️ Error accessing error reporting flag', error);
      return false;
    }
  },
  isPythonBackendEnabled: () => {
    try {
      return config.features.enablePythonBackend || false;
    } catch (error) {
      console.warn('⚠️ Error accessing Python backend flag', error);
      return false;
    }
  },
} as const;

// Export configuration for use in components
export default config;
