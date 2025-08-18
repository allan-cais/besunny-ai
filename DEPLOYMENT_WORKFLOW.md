# 🚀 **Deployment Workflow: Dev → Main Strategy**

## 🎯 **Overview**

This project uses a **two-environment deployment strategy**:
- **`dev` branch** → **Netlify** (Staging/Testing)
- **`main` branch** → **Railway** (Production)

## 🔄 **Workflow Steps**

### 1. **Development & Testing (dev branch)**
```bash
# Create feature branch from dev
git checkout dev
git pull origin dev
git checkout -b feature/new-feature

# Develop and test locally
npm run dev:fullstack

# Commit and push to dev branch
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create PR to dev branch
# Test on Netlify staging environment
```

### 2. **Staging Deployment (Netlify)**
- **Trigger**: Push to `dev` branch
- **Build Command**: `npm run build:staging`
- **Environment**: Uses `env.staging` variables
- **Purpose**: Test new features before production

### 3. **Production Deployment (Railway)**
```bash
# After testing on staging, merge to main
git checkout main
git pull origin main
git merge dev
git push origin main

# Railway automatically deploys from main branch
```

## 🏗️ **Environment Configuration**

### **Staging (Netlify - dev branch)**
```bash
# env.staging
VITE_APP_ENV=staging
VITE_PYTHON_BACKEND_URL=https://your-staging-backend.railway.app
VITE_ENABLE_PYTHON_BACKEND=true
VITE_ENABLE_DEBUG_MODE=true
VITE_ENABLE_ANALYTICS=false
```

### **Production (Railway - main branch)**
```bash
# env.production  
VITE_APP_ENV=production
VITE_PYTHON_BACKEND_URL=https://your-production-backend.railway.app
VITE_ENABLE_PYTHON_BACKEND=true
VITE_ENABLE_DEBUG_MODE=false
VITE_ENABLE_ANALYTICS=true
```

## 🔧 **Build Commands**

| Environment | Command | Output |
|-------------|---------|---------|
| **Development** | `npm run dev` | Local dev server |
| **Staging** | `npm run build:staging` | Netlify deployment |
| **Production** | `npm run build:production` | Railway deployment |

## 🌐 **Deployment URLs**

### **Staging (Netlify)**
- **Frontend**: `https://your-staging-app.netlify.app`
- **Backend**: `https://your-staging-backend.railway.app`
- **Database**: Staging Supabase project

### **Production (Railway)**
- **Frontend**: `https://your-production-app.railway.app`
- **Backend**: `https://your-production-backend.railway.app`
- **Database**: Production Supabase project

## 📋 **Environment Variables Setup**

### **Netlify (Staging)**
Set these in Netlify dashboard:
```bash
VITE_SUPABASE_URL=https://your-staging-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-staging-anon-key
VITE_PYTHON_BACKEND_URL=https://your-staging-backend.railway.app
VITE_ENABLE_PYTHON_BACKEND=true
VITE_APP_ENV=staging
```

### **Railway (Production)**
Set these in Railway dashboard:
```bash
VITE_SUPABASE_URL=https://your-production-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-production-anon-key
VITE_PYTHON_BACKEND_URL=https://your-production-backend.railway.app
VITE_ENABLE_PYTHON_BACKEND=true
VITE_APP_ENV=production
```

## 🚨 **Important Notes**

### **Branch Protection**
- **dev branch**: Allow pushes from feature branches
- **main branch**: Require PR reviews and status checks

### **Environment Separation**
- **Never** commit `.env` files to git
- **Always** use environment variables in deployment platforms
- **Test** staging environment before merging to main

### **Database Considerations**
- **Staging**: Use separate Supabase project
- **Production**: Use production Supabase project
- **Migrations**: Test on staging before production

## 🔍 **Troubleshooting**

### **Staging Issues**
```bash
# Check Netlify build logs
# Verify environment variables
# Test locally with staging config
npm run build:staging
npm run preview
```

### **Production Issues**
```bash
# Check Railway deployment logs
# Verify environment variables
# Test locally with production config
npm run build:production
npm run preview
```

## 📊 **Monitoring & Rollback**

### **Health Checks**
- **Staging**: Monitor Netlify deployment status
- **Production**: Monitor Railway deployment status
- **Backend**: Check `/health` endpoints

### **Rollback Strategy**
- **Staging**: Revert to previous commit on dev branch
- **Production**: Revert to previous commit on main branch
- **Database**: Use Supabase point-in-time recovery if needed

## 🎉 **Success Checklist**

Before merging dev → main:
- [ ] Feature tested locally
- [ ] Feature tested on staging (Netlify)
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Performance acceptable
- [ ] Security review completed

**Your deployment workflow is now fully configured for smooth dev → main deployments!** 🚀
