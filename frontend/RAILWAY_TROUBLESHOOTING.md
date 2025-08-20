# Railway Environment Variables Troubleshooting

## Problem
The staging site is showing missing environment variables in the console, particularly:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_PYTHON_BACKEND_URL`

## Root Cause
The issue is that Vite replaces `import.meta.env.VITE_*` variables at build time, so if they're not available during the build, they won't be available in the final bundle. Railway's environment variables are only available at runtime, not during the build process.

## Solution Implemented
I've implemented a runtime environment variable loader that:
1. Provides default configuration values for Railway production
2. Loads configuration from a runtime config file (`/runtime-config.json`)
3. Falls back to hardcoded production values when environment variables are missing
4. Allows dynamic configuration updates at runtime

## Solutions

### 1. Runtime Configuration (Recommended Solution)
The app now includes a runtime configuration system that works with Railway:

1. **Default Production Values**: The app includes hardcoded production values for Railway
2. **Runtime Config File**: `/runtime-config.json` can be updated by Railway deployment scripts
3. **Automatic Fallbacks**: When environment variables are missing, the app uses production defaults

**Current Production Defaults:**
- Supabase URL: `https://gkkmaeobxwvramtsjabu.supabase.co`
- Python Backend: `https://besunny-ai.railway.app`
- All other settings have sensible production defaults

### 2. Alternative: Verify Environment Variables in Railway Dashboard
If you prefer to use Railway environment variables:
1. Go to your Railway project dashboard
2. Navigate to the frontend service
3. Check the "Variables" tab
4. Ensure these variables are set:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_PYTHON_BACKEND_URL`

### 2. Check Build Configuration
The Dockerfile now supports different build modes:
```dockerfile
ARG BUILD_MODE=production
RUN npm run build:${BUILD_MODE}
```

### 3. Available Build Scripts
```bash
# For staging environment
npm run build:staging

# For Railway deployment
npm run build:railway

# For production
npm run build:production
```

### 4. Debug Environment Variables
Use the debug script to check environment variables:
```bash
npm run debug:env
```

### 5. Runtime Debugging
The app now includes enhanced debugging:
- Environment debug component (bottom-right corner)
- Railway environment test component (bottom-left corner)
- Console logging for Railway environment detection
- Detailed error messages for missing variables
- Runtime configuration testing and updates

**New Debug Features:**
- **Environment Debug**: Shows current configuration status
- **Railway Environment Test**: Comprehensive testing of environment variables
- **Runtime Config Update**: Button to reload configuration from runtime
- **Console Tests**: Detailed logging of environment variable status

### 6. Railway Configuration
Ensure your `railway.toml` has the correct service configuration:
```toml
[[services]]
name = "besunny-frontend"
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[services.besunny-frontend.build.environment]
NODE_ENV = "production"
```

### 7. Common Issues and Fixes

#### Issue: Variables not available during build
**Fix**: Use runtime environment variable loading instead of build-time

#### Issue: Variables not prefixed with VITE_
**Fix**: Ensure all client-side variables start with `VITE_`

#### Issue: Variables not persisting after deployment
**Fix**: Check Railway's variable persistence settings

### 8. Testing Locally
To test Railway-like behavior locally:
```bash
# Set environment variables
export VITE_SUPABASE_URL="your-supabase-url"
export VITE_SUPABASE_ANON_KEY="your-anon-key"
export VITE_PYTHON_BACKEND_URL="your-backend-url"

# Run the app
npm run dev
```

### 9. Monitoring and Debugging
The app now provides:
- Real-time environment variable status
- Detailed console logging
- Visual indicators for missing variables
- Test buttons to verify configuration

### 10. Next Steps
1. Verify all required variables are set in Railway dashboard
2. Redeploy the frontend service
3. Check the browser console for the new debug information
4. Use the environment debug component to verify status

## Support
If issues persist:
1. Check Railway deployment logs
2. Verify environment variable syntax
3. Ensure variables are properly scoped to the frontend service
4. Test with a simple variable first (e.g., `VITE_TEST=hello`)
