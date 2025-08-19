import React from 'react';
import { config, features } from '@/config';
import { pythonBackendConfig } from '@/config/python-backend-config';

interface EnvironmentDebugProps {
  show?: boolean;
}

export const EnvironmentDebug: React.FC<EnvironmentDebugProps> = ({ show = false }) => {
  if (!show && import.meta.env.PROD) {
    return null;
  }

  const envVars = {
    'VITE_APP_ENV': import.meta.env.VITE_APP_ENV,
    'VITE_SUPABASE_URL': import.meta.env.VITE_SUPABASE_URL,
    'VITE_SUPABASE_ANON_KEY': import.meta.env.VITE_SUPABASE_ANON_KEY ? '***SET***' : 'NOT SET',
    'VITE_PYTHON_BACKEND_URL': import.meta.env.VITE_PYTHON_BACKEND_URL,
    'VITE_ENABLE_PYTHON_BACKEND': import.meta.env.VITE_ENABLE_PYTHON_BACKEND,
    'MODE': import.meta.env.MODE,
    'DEV': import.meta.env.DEV,
    'PROD': import.meta.env.PROD,
  };

  return (
    <div className="fixed bottom-4 right-4 bg-black/90 text-white p-4 rounded-lg text-xs max-w-md z-50">
      <h3 className="font-bold mb-2">🔧 Environment Debug</h3>
      
      <div className="space-y-1">
        <div><strong>Mode:</strong> {import.meta.env.MODE}</div>
        <div><strong>Environment:</strong> {import.meta.env.VITE_APP_ENV || 'NOT SET'}</div>
        
        <div className="mt-2">
          <strong>Environment Variables:</strong>
          {Object.entries(envVars).map(([key, value]) => (
            <div key={key} className="ml-2">
              {key}: {value || 'undefined'}
            </div>
          ))}
        </div>

        <div className="mt-2">
          <strong>Config Status:</strong>
          <div className="ml-2">
            Supabase URL: {config.supabase.url ? '✅' : '❌'}
          </div>
          <div className="ml-2">
            Python Backend: {features.isPythonBackendEnabled() ? '✅' : '❌'}
          </div>
          <div className="ml-2">
            Debug Mode: {features.isDebugMode() ? '✅' : '❌'}
          </div>
        </div>

        <div className="mt-2">
          <strong>Python Backend Config:</strong>
          <div className="ml-2">
            Base URL: {pythonBackendConfig.baseUrl}
          </div>
          <div className="ml-2">
            Timeout: {pythonBackendConfig.timeout}ms
          </div>
          <div className="ml-2">
            Retry Attempts: {pythonBackendConfig.retryAttempts}
          </div>
          <div className="ml-2">
            Health Check Interval: {pythonBackendConfig.healthCheckInterval}ms
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnvironmentDebug;
