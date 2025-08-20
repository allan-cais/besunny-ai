import React, { useState } from 'react';
import { 
  checkRailwayEnvironmentVariables, 
  testRailwayEnvironmentVariables,
  isRailwayEnvironment,
  config,
  updateConfigFromRuntime
} from '@/config';

export const RailwayEnvironmentTest: React.FC = () => {
  const [testResults, setTestResults] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [debugMode, setDebugMode] = useState(false);

  const runEnvironmentTest = () => {
    setIsRunning(true);
    setTestResults([]);
    
    const results: string[] = [];
    
    // Test 1: Check if running in Railway environment
    const isRailway = isRailwayEnvironment();
    results.push(`🌐 Environment: ${isRailway ? 'Railway/Cloud' : 'Local'}`);
    
    // Test 2: Check environment variables
    const envCheck = checkRailwayEnvironmentVariables();
    const isRailway = isRailwayEnvironment();
    
    if (isRailway) {
      // In Railway, missing env vars is expected and normal
      results.push(`📋 Environment Variables: ⚠️ Using Runtime Config (Expected in Railway)`);
      if (envCheck.missing.length > 0) {
        results.push(`ℹ️ Missing from build: ${envCheck.missing.join(', ')}`);
      }
    } else {
      // In local dev, missing env vars might be an issue
      results.push(`📋 Environment Variables: ${envCheck.isLoaded ? '✅ All Required Loaded' : '❌ Missing Required'}`);
      if (envCheck.loaded.length > 0) {
        results.push(`✅ Loaded: ${envCheck.loaded.join(', ')}`);
      }
      if (envCheck.missing.length > 0) {
        results.push(`❌ Missing: ${envCheck.missing.join(', ')}`);
      }
    }
    
    // Test 3: Check specific config values
    results.push(`🔧 Supabase URL: ${config.supabase.url ? '✅ Set' : '❌ Not Set'}`);
    results.push(`🔑 Supabase Anon Key: ${config.supabase.anonKey ? '✅ Set' : '❌ Not Set'}`);
    results.push(`🐍 Python Backend URL: ${config.pythonBackend.url ? '✅ Set' : '❌ Not Set'}`);
    
    // Test 4: Check if URLs are valid
    try {
      if (config.supabase.url) {
        new URL(config.supabase.url);
        results.push(`🔗 Supabase URL Format: ✅ Valid`);
      } else {
        results.push(`🔗 Supabase URL Format: ❌ No URL to validate`);
      }
    } catch {
      results.push(`🔗 Supabase URL Format: ❌ Invalid URL format`);
    }
    
    try {
      if (config.pythonBackend.url) {
        new URL(config.pythonBackend.url);
        results.push(`🔗 Python Backend URL Format: ✅ Valid`);
      } else {
        results.push(`🔗 Python Backend URL Format: ❌ No URL to validate`);
      }
    } catch {
      results.push(`🔗 Python Backend URL Format: ❌ Invalid URL format`);
    }
    
    setTestResults(results);
    setIsRunning(false);
  };

  const runConsoleTest = () => {
    if (debugMode) {
      testRailwayEnvironmentVariables();
    } else {
      console.log('🧪 Debug mode disabled. Click "Enable Debug Mode" to run console tests.');
    }
  };

  return (
    <div className="fixed bottom-4 left-4 bg-black/90 text-white p-4 rounded-lg text-xs max-w-md z-50">
      <h3 className="font-bold mb-2">🚂 Railway Environment Test</h3>
      
      <div className="space-y-2">
        <button 
          onClick={runEnvironmentTest}
          disabled={isRunning}
          className="w-full px-3 py-2 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isRunning ? 'Running Test...' : 'Run Environment Test'}
        </button>
        
        <button 
          onClick={runConsoleTest}
          className="w-full px-3 py-2 bg-green-600 text-white text-xs rounded hover:bg-green-700"
        >
          Run Console Test
        </button>
        
        <button 
          onClick={() => updateConfigFromRuntime()}
          className="w-full px-3 py-2 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
        >
          Update Runtime Config
        </button>
        
        <button 
          onClick={() => setDebugMode(!debugMode)}
          className={`w-full px-3 py-2 text-xs rounded ${
            debugMode 
              ? 'bg-yellow-600 hover:bg-yellow-700' 
              : 'bg-gray-600 hover:bg-gray-700'
          }`}
        >
          {debugMode ? 'Disable' : 'Enable'} Debug Mode
        </button>
        
        {testResults.length > 0 && (
          <div className="mt-3 p-2 bg-gray-800 rounded">
            <strong>Test Results:</strong>
            <div className="mt-1 space-y-1">
              {testResults.map((result, index) => (
                <div key={index} className="text-xs">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="mt-2 text-xs text-gray-400">
          Check browser console for detailed logs
          {isRailwayEnvironment() && (
            <div className="mt-1 text-yellow-400">
              Note: Missing environment variables are expected in Railway
            </div>
          )}
          <div className="mt-1">
            Debug Mode: {debugMode ? '✅ Enabled' : '❌ Disabled'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RailwayEnvironmentTest;
