/**
 * Python Backend Configuration
 * Environment-specific configuration for Python backend services
 */

import { isRailwayEnvironment } from './index';

export interface PythonBackendConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  healthCheckInterval: number;
  enableLogging: boolean;
  enableMetrics: boolean;
}

// Environment detection
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;
const isStaging = import.meta.env.MODE === 'staging';

// Get environment variables
const getEnvVar = (key: string, defaultValue: string): string => {
  return import.meta.env[key] || defaultValue;
};

// Base configuration
const baseConfig: PythonBackendConfig = {
  baseUrl: '',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  healthCheckInterval: 60000, // 1 minute
  enableLogging: true,
  enableMetrics: true,
};

// Development configuration
const developmentConfig: PythonBackendConfig = {
  ...baseConfig,
  baseUrl: getEnvVar('VITE_PYTHON_BACKEND_URL', 'http://localhost:8000'),
  timeout: 60000, // Longer timeout for development
  retryAttempts: 5,
  healthCheckInterval: 30000, // More frequent health checks in development
  enableLogging: true,
  enableMetrics: true,
};

// Staging configuration
const stagingConfig: PythonBackendConfig = {
  ...baseConfig,
  baseUrl: getEnvVar('VITE_PYTHON_BACKEND_URL', ''),
  timeout: 30000,
  retryAttempts: 3,
  healthCheckInterval: 60000,
  enableLogging: true,
  enableMetrics: true,
};

// Production configuration
const productionConfig: PythonBackendConfig = {
  ...baseConfig,
  baseUrl: getEnvVar('VITE_PYTHON_BACKEND_URL', ''),
  timeout: 30000,
  retryAttempts: 3,
  healthCheckInterval: 120000, // Less frequent health checks in production
  enableLogging: false, // Disable verbose logging in production
  enableMetrics: true,
};

// Select configuration based on environment
let config: PythonBackendConfig;

if (isDevelopment) {
  config = developmentConfig;
} else if (isStaging) {
  config = stagingConfig;
} else if (isProduction) {
  config = productionConfig;
} else {
  // Fallback to development
  config = developmentConfig;
}

// Validate configuration
if (!config.baseUrl) {
  const isCloudEnvironment = isRailwayEnvironment();
  
  if (isCloudEnvironment) {
    // In cloud environment, use the runtime config default
    config.baseUrl = 'https://besunny-ai.railway.app';

  } else {

    config.baseUrl = 'http://localhost:8000';
  }
}

// Export configuration
export const pythonBackendConfig = config;

// Export environment info
export const environmentInfo = {
  isDevelopment,
  isProduction,
  isStaging,
  mode: import.meta.env.MODE,
  baseUrl: config.baseUrl,
};

// Export configuration getters
export const getPythonBackendConfig = (): PythonBackendConfig => config;

export const getBaseUrl = (): string => config.baseUrl;

export const getTimeout = (): number => config.timeout;

export const getRetryAttempts = (): number => config.retryAttempts;

export const getHealthCheckInterval = (): number => config.healthCheckInterval;

// Configuration validation
export const validateConfig = (): boolean => {
  const errors: string[] = [];
  
  if (!config.baseUrl) {
    errors.push('Base URL is required');
  }
  
  if (config.timeout <= 0) {
    errors.push('Timeout must be positive');
  }
  
  if (config.retryAttempts < 0) {
    errors.push('Retry attempts cannot be negative');
  }
  
  if (config.healthCheckInterval <= 0) {
    errors.push('Health check interval must be positive');
  }
  
  if (errors.length > 0) {

    return false;
  }
  
  return true;
};

// Configuration override for testing
export const overrideConfig = (overrides: Partial<PythonBackendConfig>): void => {
  Object.assign(config, overrides);
};

// Reset configuration to defaults
export const resetConfig = (): void => {
  if (isDevelopment) {
    Object.assign(config, developmentConfig);
  } else if (isStaging) {
    Object.assign(config, stagingConfig);
  } else if (isProduction) {
    Object.assign(config, productionConfig);
  }
};

// Log configuration (only in development)
if (isDevelopment) {
  
    ...config,
    environment: environmentInfo,
  });
}
