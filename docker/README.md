# Docker Configuration Files

This directory contains all Docker-related configuration files for BeSunny.ai.

## 📁 Files Overview

### **Dockerfiles (Backup)**
- `Dockerfile.backup` - Original combined frontend/backend Dockerfile
- `Dockerfile.frontend.backup` - Frontend-only Dockerfile
- `Dockerfile.backend.backup` - Backend-only Dockerfile
- `Dockerfile.optimized.backup` - Size-optimized combined Dockerfile
- `Dockerfile.frontend.railway.backup` - Railway-optimized frontend
- `Dockerfile.backend.railway.backup` - Railway-optimized backend

### **Docker Compose**
- `docker-compose.yml` - Local development setup
- `docker-compose.railway.yml` - Railway deployment setup

### **Build Scripts**
- `docker-build.sh` - Local Docker build script
- `test-docker-build.sh` - Docker build testing script

### **Configuration**
- `.dockerignore` - Docker build exclusions

## 🚀 **When to Use These Files**

### **For Local Development:**
```bash
cd docker
./docker-build.sh
docker-compose up
```

### **For Railway Deployment:**
**DO NOT USE** - Railway auto-detects and builds from source code automatically.

### **For Other Platforms:**
- **Heroku**: Use `Dockerfile.optimized.backup`
- **AWS ECS**: Use `Dockerfile.frontend.backup` + `Dockerfile.backend.backup`
- **Google Cloud Run**: Use `Dockerfile.optimized.backup`

## ⚠️ **Important Notes**

1. **Railway Deployment**: These files are NOT used for Railway
2. **Source Building**: Railway builds directly from your source code
3. **Size Limits**: Railway has 4GB image size limits
4. **Auto-Detection**: Railway automatically detects Node.js and Python projects

## 🔧 **Restoring for Local Use**

If you want to use Docker locally:
```bash
cd docker
cp Dockerfile.frontend.backup ../Dockerfile.frontend
cp Dockerfile.backend.backup ../Dockerfile.backend
cd ..
docker build -f Dockerfile.frontend -t besunny-frontend .
docker build -f Dockerfile.backend -t besunny-backend .
```

## 📚 **Documentation**

- **Railway Deployment**: See main project README
- **Local Docker**: See `DOCKER_README.md` in project root
- **Troubleshooting**: Check build logs for specific errors
