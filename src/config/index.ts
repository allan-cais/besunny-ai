// Configuration Management
// Centralizes all environment variables and configuration settings

interface Config {
  supabase: {
    url: string;
    anonKey: string;
    serviceRoleKey?: string;
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

// Environment variable validation
function getRequiredEnvVar(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function getOptionalEnvVar(name: string, defaultValue: string = ''): string {
  return import.meta.env[name] || defaultValue;
}

// Build configuration object
export const config: Config = {
  supabase: {
    url: getRequiredEnvVar('VITE_SUPABASE_URL'),
    anonKey: getRequiredEnvVar('VITE_SUPABASE_ANON_KEY'),
    serviceRoleKey: getOptionalEnvVar('VITE_SUPABASE_SERVICE_ROLE_KEY'),
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
  },
  polling: {
    defaultIntervalMs: parseInt(getOptionalEnvVar('VITE_POLLING_INTERVAL_MS', '30000')),
    maxRetries: parseInt(getOptionalEnvVar('VITE_MAX_RETRIES', '3')),
    retryDelayMs: parseInt(getOptionalEnvVar('VITE_RETRY_DELAY_MS', '1000')),
  },
  limits: {
    maxDocumentsPerPage: parseInt(getOptionalEnvVar('VITE_MAX_DOCUMENTS_PER_PAGE', '50')),
    maxMeetingsPerPage: parseInt(getOptionalEnvVar('VITE_MAX_MEETINGS_PER_PAGE', '100')),
    maxChatMessagesPerPage: parseInt(getOptionalEnvVar('VITE_MAX_CHAT_MESSAGES_PER_PAGE', '100')),
  },
};

// API endpoint builders
export const apiEndpoints = {
  supabase: {
    functions: (functionName: string) => `${config.supabase.url}/functions/v1/${functionName}`,
    auth: `${config.supabase.url}/auth/v1`,
    rest: `${config.supabase.url}/rest/v1`,
    realtime: `${config.supabase.url}/realtime/v1`,
  },
  google: {
    calendar: 'https://www.googleapis.com/calendar/v3',
    gmail: 'https://www.googleapis.com/gmail/v1',
    drive: 'https://www.googleapis.com/drive/v3',
  },
} as const;

// Configuration validation
export function validateConfig(): void {
  try {
    // Validate required Supabase configuration
    if (!config.supabase.url || !config.supabase.anonKey) {
      throw new Error('Invalid Supabase configuration');
    }

    // Validate URL formats
    new URL(config.supabase.url);
    
    // Validate numeric configurations
    if (config.polling.defaultIntervalMs <= 0) {
      throw new Error('Invalid polling interval');
    }
    
    if (config.limits.maxDocumentsPerPage <= 0) {
      throw new Error('Invalid documents per page limit');
    }

    console.log('✅ Configuration validated successfully');
  } catch (error) {
    console.error('❌ Configuration validation failed:', error);
    throw error;
  }
}

// Development helpers
export const isDevelopment = import.meta.env.DEV;
export const isProduction = import.meta.env.PROD;
export const isTest = import.meta.env.MODE === 'test';

// Feature flags
export const features = {
  isEnabled: (feature: keyof Config['features']) => config.features[feature],
  isDebugMode: () => config.features.enableDebugMode,
  isAnalyticsEnabled: () => config.features.enableAnalytics,
  isErrorReportingEnabled: () => config.features.enableErrorReporting,
} as const;

// Export configuration for use in components
export default config;
