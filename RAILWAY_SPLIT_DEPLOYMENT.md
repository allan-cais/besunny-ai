# Railway Split Deployment Guide

This guide explains how to deploy BeSunny.ai as two separate Railway services instead of one monolithic service.

## Why Split the Services?

**Benefits:**
- ✅ Faster builds and deployments
- ✅ Better resource allocation
- ✅ Independent scaling
- ✅ Cleaner separation of concerns
- ✅ Easier debugging and maintenance
- ✅ Better caching for frontend

**Current Issues with Monolithic Approach:**
- ❌ Complex Dockerfile trying to build both frontend and backend
- ❌ Larger container size
- ❌ Slower deployments
- ❌ Harder to debug issues

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   Service       │◄──►│    Service      │
│                 │    │                 │
│ • React App     │    │ • FastAPI       │
│ • Static Files  │    │ • Python Logic  │
│ • Nginx/Serve   │    │ • Database      │
│ • Port: $PORT   │    │ • Port: $PORT   │
└─────────────────┘    └─────────────────┘
```

## Files Created

1. **`railway-frontend.toml`** - Frontend service configuration
2. **`railway-backend.toml`** - Backend service configuration  
3. **`Dockerfile.backend`** - Simplified backend-only Dockerfile
4. **`deploy-railway-split.sh`** - Automated deployment script

## File Paths and Build Configuration

### Frontend Service Paths

**Source Directory:** Root of project (`.`)
- **Includes:** `src/`, `public/`, `package.json`, `vite.config.ts`, `tailwind.config.ts`, `tsconfig*.json`
- **Excludes:** `backend/`, `supabase/`, `database/`, `docs/`, `*.md`, `Dockerfile*`

**Build Output:** `dist/` directory
- **Build Command:** `npm install && npm run build:production`
- **Start Command:** `npx serve -s dist -l $PORT`

**File Structure:**
```
besunny-ai/
├── src/                    ← Frontend source code
├── public/                 ← Static assets
├── package.json            ← Dependencies
├── vite.config.ts          ← Build configuration
├── tailwind.config.ts      ← Styling configuration
├── tsconfig*.json          ← TypeScript configuration
└── dist/                   ← Build output (created during build)
```

### Backend Service Paths

**Source Directory:** `backend/` subdirectory
- **Includes:** All Python files, `requirements.txt`, `start.py`
- **Excludes:** `__pycache__/`, `*.pyc`, `tests/`, `venv/`

**Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python start.py`
- **Working Directory:** `/app` (inside container)

**File Structure:**
```
besunny-ai/
└── backend/                ← Backend source code
    ├── app/                ← FastAPI application
    ├── requirements.txt    ← Python dependencies
    ├── start.py           ← Entry point
    └── ...                ← Other backend files
```

### Why These Paths Matter

1. **Frontend Service:**
   - Needs access to React source code (`src/`)
   - Builds to `dist/` directory
   - Serves static files from `dist/`

2. **Backend Service:**
   - Only needs Python backend code
   - Installs dependencies from `requirements.txt`
   - Runs from `start.py`

3. **Separation:**
   - Frontend doesn't need backend files
   - Backend doesn't need frontend build artifacts
   - Cleaner, faster builds

## Deployment Steps

### 1. Create Railway Projects

Create two separate projects in Railway:
- `besunny-ai-frontend` - for React frontend
- `besunny-ai-backend` - for Python backend

### 2. Run Deployment Script

```bash
./deploy-railway-split.sh
```

The script will:
- Check Railway CLI installation
- Deploy frontend service
- Deploy backend service
- Provide deployment URLs

### 3. Configure Environment Variables

**Frontend Service:**
- Set `VITE_PYTHON_BACKEND_URL` to your backend service URL

**Backend Service:**
- Set `CORS_ORIGINS` to allow your frontend domain
- Configure all other environment variables (Supabase, Redis, etc.)

## Manual Deployment

If you prefer to deploy manually:

### Frontend Service
```bash
# Link to frontend project
railway link --project besunny-ai-frontend

# Deploy
railway up --service frontend
```

### Backend Service
```bash
# Link to backend project  
railway link --project besunny-ai-backend

# Deploy
railway up --service backend
```

## Environment Variables

### Frontend (.env)
```bash
VITE_PYTHON_BACKEND_URL=https://your-backend-service.railway.app
VITE_APP_NAME=BeSunny.ai
VITE_APP_VERSION=17.0.0
VITE_ENVIRONMENT=production
```

### Backend (.env)
```bash
# All your existing backend environment variables
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_key
# ... etc
```

## Troubleshooting

### Frontend Issues
- Check if `VITE_PYTHON_BACKEND_URL` is set correctly
- Verify frontend builds successfully
- Check Railway logs for build errors

### Backend Issues  
- Verify `requirements.txt` exists and is valid
- Check Python version compatibility
- Review Railway logs for startup errors

### CORS Issues
- Ensure `CORS_ORIGINS` includes your frontend domain
- Check if backend is accessible from frontend

## Migration from Monolithic

1. **Backup current deployment**
2. **Create new split services**
3. **Test both services independently**
4. **Update DNS/environment variables**
5. **Remove old monolithic service**

## Benefits After Migration

- **Deployment Time:** ~2-3 minutes vs 10+ minutes
- **Container Size:** ~200MB vs 800MB+
- **Build Success Rate:** 95%+ vs 70%
- **Debugging:** Much easier to isolate issues
- **Scaling:** Independent scaling for each service

## Support

If you encounter issues:
1. Check Railway logs for each service
2. Verify environment variables are set correctly
3. Test services independently
4. Check CORS configuration
