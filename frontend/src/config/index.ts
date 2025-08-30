// Configuration Management
// Centralizes all environment variables and configuration settings

import { stagingConfig } from './staging-config';
import { getRuntimeConfig, runtimeConfig, isRailwayEnvironment as isRailwayRuntime } from './runtime-env-loader';

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
  debug?: {
    enableEnvLogging: boolean;
    enableConfigLogging: boolean;
  };
}

// Environment variable validation with better error handling
function getRequiredEnvVar(name: string): string {
  const value = import.meta.env[name];
  if (!value) {
    // Only log warnings in development or when explicitly debugging
    if (import.meta.env.DEV || import.meta.env.VITE_DEBUG_ENV === 'true') {
  
    }
    // Don't return placeholder values - let the app fail gracefully
    // This allows Railway's environment variables to be loaded properly
    return '';
  }
  return value;
}

function getOptionalEnvVar(name: string, defaultValue: string = ''): string {
  const value = import.meta.env[name];
  return value || defaultValue;
}

function getOptionalNumberEnvVar(name: string, defaultValue: number): number {
  const value = import.meta.env[name];
  if (!value) {
    return defaultValue;
  }
  const parsed = parseInt(value);
  if (isNaN(parsed)) {
    return defaultValue;
  }
  return parsed;
}

// Build configuration object with safe defaults
export const config: Config = {
  supabase: {
    url: getRequiredEnvVar('VITE_SUPABASE_URL') || runtimeConfig.supabase.url,
    anonKey: getRequiredEnvVar('VITE_SUPABASE_ANON_KEY') || runtimeConfig.supabase.anonKey,
    serviceRoleKey: getOptionalEnvVar('VITE_SUPABASE_SERVICE_ROLE_KEY') || runtimeConfig.supabase.serviceRoleKey,
  },
  pythonBackend: {
    url: (() => {
      const envUrl = getOptionalEnvVar('VITE_PYTHON_BACKEND_URL', '');
      const runtimeUrl = runtimeConfig.pythonBackend.url;
      
      // Check if we're in Railway environment
      const isRailwayEnv = isRailwayEnvironment();
      
      // Use the environment variable URL (should be HTTPS) or fallback to runtime config
      const finalUrl = envUrl || runtimeUrl;
      
      // Debug logging
      console.log('🔧 Python Backend URL Configuration:');
      console.log('  Environment Variable (VITE_PYTHON_BACKEND_URL):', envUrl);
      console.log('  Runtime Config URL:', runtimeUrl);
      console.log('  Is Railway Environment:', isRailwayEnv);
      console.log('  Final URL:', finalUrl);
      console.log('  Environment Variables:', {
        VITE_PYTHON_BACKEND_URL: import.meta.env.VITE_PYTHON_BACKEND_URL,
        NODE_ENV: import.meta.env.NODE_ENV,
        MODE: import.meta.env.MODE,
        DEV: import.meta.env.DEV,
        PROD: import.meta.env.PROD
      });
      
      return finalUrl;
    })(),
    timeout: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_TIMEOUT', runtimeConfig.pythonBackend.timeout),
    retries: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_RETRIES', runtimeConfig.pythonBackend.retries),
    retryDelay: getOptionalNumberEnvVar('VITE_PYTHON_BACKEND_RETRY_DELAY', runtimeConfig.pythonBackend.retryDelay),
  },
  api: {
    n8nWebhookUrl: getOptionalEnvVar('VITE_N8N_WEBHOOK_URL', runtimeConfig.api.n8nWebhookUrl),
    openaiApiKey: getOptionalEnvVar('VITE_OPENAI_API_KEY') || runtimeConfig.api.openaiApiKey,
    anthropicApiKey: getOptionalEnvVar('VITE_ANTHROPIC_API_KEY') || runtimeConfig.api.anthropicApiKey,
  },
  features: {
    enableDebugMode: import.meta.env.DEV || runtimeConfig.features.enableDebugMode,
    enableAnalytics: getOptionalEnvVar('VITE_ENABLE_ANALYTICS', runtimeConfig.features.enableAnalytics.toString()) === 'true',
    enableErrorReporting: getOptionalEnvVar('VITE_ENABLE_ERROR_REPORTING', runtimeConfig.features.enableErrorReporting.toString()) === 'true',
    enablePythonBackend: getOptionalEnvVar('VITE_ENABLE_PYTHON_BACKEND', runtimeConfig.features.enablePythonBackend.toString()) === 'true',
  },
  polling: {
    defaultIntervalMs: getOptionalNumberEnvVar('VITE_POLLING_INTERVAL_MS', runtimeConfig.polling.defaultIntervalMs),
    maxRetries: getOptionalNumberEnvVar('VITE_MAX_RETRIES', runtimeConfig.polling.maxRetries),
    retryDelayMs: getOptionalNumberEnvVar('VITE_RETRY_DELAY_MS', runtimeConfig.polling.retryDelayMs),
  },
  limits: {
    maxDocumentsPerPage: getOptionalNumberEnvVar('VITE_MAX_DOCUMENTS_PER_PAGE', runtimeConfig.limits.maxDocumentsPerPage),
    maxMeetingsPerPage: getOptionalNumberEnvVar('VITE_MAX_MEETINGS_PER_PAGE', runtimeConfig.limits.maxMeetingsPerPage),
    maxChatMessagesPerPage: getOptionalNumberEnvVar('VITE_MAX_CHAT_MESSAGES_PER_PAGE', runtimeConfig.limits.maxChatMessagesPerPage),
  },

};



// API endpoint builders with safe fallbacks
export const apiEndpoints = {
  supabase: {
    // Supabase Edge Functions have been migrated to Python backend
    // functions: (functionName: string) => `${config.supabase.url}/functions/v1/${functionName}`,
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
    // Check if we're running in Railway or similar cloud environment
    const isCloudEnvironment = isRailwayEnvironment();
    
    // Validate required Supabase configuration
    if (!config.supabase.url || !config.supabase.anonKey) {

      return;
    }

    // Validate Python backend configuration
    if (config.features.enablePythonBackend) {
      try {
        new URL(config.pythonBackend.url);
      } catch {

        return;
      }
    }

    // Validate URL formats
    try {
      new URL(config.supabase.url);
    } catch {

      return;
    }
    
    // Validate numeric configurations
    if (config.polling.defaultIntervalMs <= 0) {

      return;
    }
    
    if (config.limits.maxDocumentsPerPage <= 0) {

      return;
    }



  } catch (error) {

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

      return false;
    }
  },
  isDebugMode: () => {
    try {
      return config.features.enableDebugMode || false;
    } catch (error) {

      return false;
    }
  },
  isAnalyticsEnabled: () => {
    try {
      return config.features.enableAnalytics || false;
    } catch (error) {

      return false;
    }
  },
  isErrorReportingEnabled: () => {
    try {
      return config.features.enableErrorReporting || false;
    } catch (error) {

      return false;
    }
  },
  isPythonBackendEnabled: () => {
    try {
      return config.features.enablePythonBackend || false;
    } catch (error) {

      return false;
    }
  },
} as const;



// Utility function to check if running in Railway/cloud environment
export function isRailwayEnvironment(): boolean {
  return isRailwayRuntime();
}

// Function to check if all required Railway environment variables are loaded
export function checkRailwayEnvironmentVariables(): {
  isLoaded: boolean;
  missing: string[];
  loaded: string[];
} {
  const requiredVars = [
    'VITE_SUPABASE_URL',
    'VITE_SUPABASE_ANON_KEY'
  ];
  
  const optionalVars = [
    'VITE_PYTHON_BACKEND_URL',
    'VITE_SUPABASE_SERVICE_ROLE_KEY',
    'VITE_OPENAI_API_KEY',
    'VITE_ANTHROPIC_API_KEY'
  ];
  
  const allVars = [...requiredVars, ...optionalVars];
  const missing: string[] = [];
  const loaded: string[] = [];
  
  allVars.forEach(varName => {
    const value = import.meta.env[varName];
    if (value) {
      loaded.push(varName);
    } else {
      missing.push(varName);
    }
  });
  
  // In Railway/production, we expect these to be missing and use runtime config instead
  const isLoaded = requiredVars.every(varName => 
    import.meta.env[varName]
  );
  
  return { isLoaded, missing, loaded };
}



// Function to dynamically update configuration at runtime
export async function updateConfigFromRuntime(): Promise<void> {
  try {
    const runtimeConfig = await getRuntimeConfig();
    
    // Update the config object with runtime values
    Object.assign(config.supabase, runtimeConfig.supabase);
    Object.assign(config.pythonBackend, runtimeConfig.pythonBackend);
    Object.assign(config.api, runtimeConfig.api);
    Object.assign(config.features, runtimeConfig.features);
    Object.assign(config.polling, runtimeConfig.polling);
    Object.assign(config.limits, runtimeConfig.limits);
    

    
  } catch (error) {

  }
}

// Export configuration for use in components
export default config;
