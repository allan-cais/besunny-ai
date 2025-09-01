import { AppConfig } from '@/types';

// Environment detection
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;
const isStaging = import.meta.env.MODE === 'staging';

// Get environment
const getEnvironment = (): AppConfig['environment'] => {
  if (isStaging) return 'staging';
  if (isProduction) return 'production';
  return 'development';
};

// Environment-specific configurations
const configs = {
  development: {
    apiUrl: import.meta.env.VITE_API_URL || 'https://backend-staging-6085.up.railway.app',
    supabaseUrl: import.meta.env.VITE_SUPABASE_URL || 'https://localhost:54321',
    supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || 'development-key',
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || 'development-client-id',
    openaiApiKey: import.meta.env.VITE_OPENAI_API_KEY,
  },
  staging: {
    apiUrl: import.meta.env.VITE_API_URL || 'https://staging-api.besunny.ai',
    supabaseUrl: import.meta.env.VITE_SUPABASE_URL || 'https://staging.supabase.co',
    supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    openaiApiKey: import.meta.env.VITE_OPENAI_API_KEY,
  },
  production: {
    apiUrl: import.meta.env.VITE_API_URL || 'https://api.besunny.ai',
    supabaseUrl: import.meta.env.VITE_SUPABASE_URL || 'https://production.supabase.co',
    supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    openaiApiKey: import.meta.env.VITE_OPENAI_API_KEY,
  },
};

// Get current configuration
const getConfig = (): AppConfig => {
  const environment = getEnvironment();
  const baseConfig = configs[environment];
  
  return {
    environment,
    ...baseConfig,
  };
};

// Validate configuration
const validateConfig = (config: AppConfig): void => {
  const requiredFields = [
    'supabaseUrl',
    'supabaseAnonKey',
    'googleClientId',
  ];

  const missingFields = requiredFields.filter(field => !config[field as keyof AppConfig]);
  
  if (missingFields.length > 0) {
    if (isProduction) {
      throw new Error(`Missing required environment variables: ${missingFields.join(', ')}`);
    }
  }
};

// Export configuration
const config = getConfig();

// Validate in non-development environments
if (!isDevelopment) {
  validateConfig(config);
}

export default config;

// Export individual values for convenience
export const {
  environment,
  apiUrl,
  supabaseUrl,
  supabaseAnonKey,
  googleClientId,
  openaiApiKey,
} = config;

// Export utility functions
export const isDev = isDevelopment;
export const isProd = isProduction;
export const isStagingEnv = isStaging;

// Export environment checks
export const isLocalhost = () => {
  if (typeof window === 'undefined') return false;
  return window.location.hostname === 'localhost' || 
         window.location.hostname === '127.0.0.1';
};

export const isSecureContext = () => {
  if (typeof window === 'undefined') return false;
  return window.isSecureContext;
};

// Export feature flags
export const featureFlags = {
  aiClassification: isDevelopment || isStaging || import.meta.env.VITE_ENABLE_AI_CLASSIFICATION === 'true',
  realTimeUpdates: isDevelopment || isStaging || import.meta.env.VITE_ENABLE_REALTIME === 'true',
  advancedAnalytics: isDevelopment || isStaging || import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  webhookTesting: isDevelopment || isStaging,
  debugMode: isDevelopment,
};
