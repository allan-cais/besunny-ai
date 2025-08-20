# Railway Environment Variables Troubleshooting

## Problem
The staging site is showing missing environment variables in the console, particularly:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_PYTHON_BACKEND_URL`

## Root Cause
The issue is likely that Railway's environment variables are not being properly loaded during the build process or at runtime.

## Solutions

### 1. Verify Environment Variables in Railway Dashboard
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
- Console logging for Railway environment detection
- Detailed error messages for missing variables

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
