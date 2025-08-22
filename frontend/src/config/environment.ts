/**
 * Environment Configuration
 * Clean, type-safe environment variable management
 */

export interface EnvironmentConfig {
  // App Configuration
  mode: 'development' | 'staging' | 'production';
  isDevelopment: boolean;
  isStaging: boolean;
  isProduction: boolean;
  
  // Supabase Configuration
  supabase: {
    url: string;
    anonKey: string;
  };
  
  // Python Backend Configuration
  pythonBackend: {
    url: string;
    timeout: number;
    retryAttempts: number;
    healthCheckInterval: number;
  };
  
  // Google OAuth Configuration
  google: {
    clientId: string;
    redirectUri: string;
  };
  
  // Feature Flags
  features: {
    enablePythonBackend: boolean;
    enableDebugMode: boolean;
    enableMetrics: boolean;
  };
}

// Environment variable getter with validation
function getRequiredEnvVar(key: string): string {
  const value = import.meta.env[key];
  if (!value) {
    throw new Error(`Required environment variable ${key} is not set`);
  }
  return value;
}

function getOptionalEnvVar(key: string, defaultValue: string = ''): string {
  return import.meta.env[key] || defaultValue;
}

// Base configuration
const baseConfig: Omit<EnvironmentConfig, 'mode' | 'isDevelopment' | 'isStaging' | 'isProduction'> = {
  supabase: {
    url: getRequiredEnvVar('VITE_SUPABASE_URL'),
    anonKey: getRequiredEnvVar('VITE_SUPABASE_ANON_KEY'),
  },
  pythonBackend: {
    url: getOptionalEnvVar('VITE_PYTHON_BACKEND_URL', 'https://besunny-1.railway.app'),
    timeout: 30000,
    retryAttempts: 3,
    healthCheckInterval: 60000,
  },
  google: {
    clientId: getRequiredEnvVar('VITE_GOOGLE_CLIENT_ID'),
    redirectUri: getOptionalEnvVar('VITE_GOOGLE_REDIRECT_URI', `${window.location.origin}/integrations`),
  },
  features: {
    enablePythonBackend: getOptionalEnvVar('VITE_ENABLE_PYTHON_BACKEND', 'true') === 'true',
    enableDebugMode: import.meta.env.DEV,
    enableMetrics: true,
  },
};

// Environment-specific overrides
const environmentOverrides = {
  development: {
    pythonBackend: {
      url: 'http://localhost:8000',
      timeout: 60000,
      retryAttempts: 5,
      healthCheckInterval: 30000,
    },
    features: {
      enablePythonBackend: true,
      enableDebugMode: true,
      enableMetrics: true,
    },
  },
  staging: {
    pythonBackend: {
      url: getOptionalEnvVar('VITE_PYTHON_BACKEND_URL', 'https://besunny-1.railway.app'),
      timeout: 30000,
      retryAttempts: 3,
      healthCheckInterval: 60000,
    },
    features: {
      enablePythonBackend: true,
      enableDebugMode: false,
      enableMetrics: true,
    },
  },
  production: {
    pythonBackend: {
      url: getOptionalEnvVar('VITE_PYTHON_BACKEND_URL', 'https://besunny-1.railway.app'),
      timeout: 30000,
      retryAttempts: 3,
      healthCheckInterval: 120000,
    },
    features: {
      enablePythonBackend: true,
      enableDebugMode: false,
      enableMetrics: true,
    },
  },
};

// Determine current environment
const currentMode = import.meta.env.MODE as EnvironmentConfig['mode'] || 'development';

// Merge configurations
const config: EnvironmentConfig = {
  mode: currentMode,
  isDevelopment: currentMode === 'development',
  isStaging: currentMode === 'staging',
  isProduction: currentMode === 'production',
  ...baseConfig,
  ...environmentOverrides[currentMode],
};

// Configuration validation
function validateConfig(config: EnvironmentConfig): void {
  const errors: string[] = [];
  
  if (!config.supabase.url) errors.push('Supabase URL is required');
  if (!config.supabase.anonKey) errors.push('Supabase anon key is required');
  if (!config.google.clientId) errors.push('Google client ID is required');
  if (!config.pythonBackend.url) errors.push('Python backend URL is required');
  
  if (errors.length > 0) {
    throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
  }
}

// Validate configuration on import
validateConfig(config);

export default config;
