// Runtime Environment Variable Loader
// This allows loading environment variables at runtime from Railway instead of build time

interface RuntimeEnvConfig {
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

// Default configuration values
const defaultConfig: RuntimeEnvConfig = {
  supabase: {
    url: 'https://gkkmaeobxwvramtsjabu.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdra21hZW9ieHd2cmFtdHNqYWJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA4ODYxMzMsImV4cCI6MjA2NjQ2MjEzM30.S-bzk-Tq1Onm0cVoH-1Vt_UFFx_eGREcq5xyQtEkgXo',
    serviceRoleKey: '',
  },
  pythonBackend: {
    url: 'https://besunny-ai.railway.app',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000,
  },
  api: {
    n8nWebhookUrl: 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook',
    openaiApiKey: '',
    anthropicApiKey: '',
  },
  features: {
    enableDebugMode: false,
    enableAnalytics: false,
    enableErrorReporting: false,
    enablePythonBackend: true,
  },
  polling: {
    defaultIntervalMs: 30000,
    maxRetries: 3,
    retryDelayMs: 1000,
  },
  limits: {
    maxDocumentsPerPage: 50,
    maxMeetingsPerPage: 100,
    maxChatMessagesPerPage: 100,
  },
};

// Function to load environment variables from Railway at runtime
async function loadRuntimeEnvironmentVariables(): Promise<RuntimeEnvConfig> {
  try {
    // Check if we're running in Railway/cloud environment
    const isCloudEnvironment = window.location.hostname !== 'localhost' && 
                              window.location.hostname !== '127.0.0.1';
    
    if (!isCloudEnvironment) {
      console.log('🏠 Running locally, using default config');
      return defaultConfig;
    }
    
    console.log('🌐 Running in cloud environment, attempting to load runtime config');
    
    // Try to load from a runtime config endpoint (if available)
    // This could be a simple JSON file or API endpoint
    try {
      const response = await fetch('/runtime-config.json');
      if (response.ok) {
        const runtimeConfig = await response.json();
        console.log('✅ Loaded runtime configuration');
        return { ...defaultConfig, ...runtimeConfig };
      }
    } catch (error) {
      console.log('⚠️ No runtime config file found, using defaults');
    }
    
    // For now, use the default config but log that we're in production
    console.log('🚂 Using Railway production configuration');
    return defaultConfig;
    
  } catch (error) {
    console.error('❌ Error loading runtime environment variables:', error);
    console.log('🔄 Falling back to default configuration');
    return defaultConfig;
  }
}

// Function to check if we're in a Railway environment
export function isRailwayEnvironment(): boolean {
  return typeof window !== 'undefined' && 
         window.location.hostname !== 'localhost' && 
         window.location.hostname !== '127.0.0.1';
}

// Function to get the current environment configuration
let cachedConfig: RuntimeEnvConfig | null = null;

export async function getRuntimeConfig(): Promise<RuntimeEnvConfig> {
  if (cachedConfig) {
    return cachedConfig;
  }
  
  cachedConfig = await loadRuntimeEnvironmentVariables();
  return cachedConfig;
}

// Function to force reload the configuration
export async function reloadRuntimeConfig(): Promise<RuntimeEnvConfig> {
  cachedConfig = null;
  return await getRuntimeConfig();
}

// Export default config for immediate use
export const runtimeConfig = defaultConfig;

// Export the loader function
export { loadRuntimeEnvironmentVariables };
