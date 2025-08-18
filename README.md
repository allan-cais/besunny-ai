# BeSunny.ai - Intelligent Workspace

A modern, intelligent development workspace built with React, TypeScript, Python FastAPI, and Supabase.

## 🚀 **Quick Start - One Command**

```bash
npm run dev:fullstack
```

This single command starts your entire full-stack application:
- ✅ **Frontend**: React app with hot reloading
- ✅ **Backend**: Python FastAPI server
- ✅ **Redis**: Caching and session management
- ✅ **All dependencies and health checks**

## 🏗️ **Architecture**

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python FastAPI + Celery + Redis
- **Database**: Supabase (PostgreSQL + Auth)
- **Infrastructure**: Docker Compose with profiles

## 🔧 **Prerequisites**

- **Docker** - For backend services
- **Node.js 18+** - For frontend
- **Supabase Project** - Your database and auth provider

## 📋 **Setup**

### 1. **Configure Environment Variables**
```bash
cd backend
cp env.example .env
```

Edit `backend/.env` with your actual values:
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Optional but recommended
OPENAI_API_KEY=sk-your-openai-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
PINECONE_API_KEY=your-pinecone-api-key
```

### 2. **Start Full Stack**
```bash
npm run dev:fullstack
```

## 🎮 **Available Commands**

| Command | Description |
|---------|-------------|
| `npm run dev:fullstack` | Start everything (recommended) |
| `npm run dev:backend` | Start only backend services |
| `npm run dev:backend:logs` | View backend logs |
| `npm run dev:backend:stop` | Stop backend services |
| `npm run prod:deploy` | Deploy production stack |
| `npm run prod:scale` | Scale production services |

## 🌐 **Access Points**

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React app |
| **Backend API** | http://localhost:8000 | Python FastAPI |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | Backend status |
| **Redis Commander** | http://localhost:8081 | Redis debugging |

## 🐳 **Docker Profiles**

### **Development Profile** (`--profile development`)
- Redis + Backend + Celery + Redis Commander
- Lightweight setup for local development

### **Production Profile** (`--profile production`)
- Redis + Backend + Celery + Nginx + Prometheus + Grafana
- Full-featured setup for production deployment

## 🔄 **Environment Switching**

### **Development Mode:**
```bash
ENVIRONMENT=development
DEBUG=true
WORKERS=1
ENABLE_METRICS=false
```

### **Production Mode:**
```bash
ENVIRONMENT=production
DEBUG=false
WORKERS=8
ENABLE_METRICS=true
```

## 🏗️ **Project Structure**

```
├── src/                    # React frontend
├── backend/               # Python backend
│   ├── app/              # FastAPI application
│   ├── docker-compose.yml # Unified Docker setup
│   └── env.example       # Environment template
├── start-fullstack.sh    # Startup script
└── package.json          # NPM scripts
```

## 🚀 **Deployment**

### **Local Testing:**
```bash
npm run test:full          # Test production stack locally
```

### **Production Deploy:**
```bash
npm run prod:deploy        # Deploy production stack
npm run prod:scale         # Scale to 3 backends + 2 workers
```

## 🆘 **Troubleshooting**

### **Backend Won't Start:**
```bash
npm run dev:backend:logs   # Check logs
npm run dev:backend:stop   # Stop services
npm run dev:backend        # Restart
```

### **Port Conflicts:**
```bash
lsof -i :8000              # Check if port 8000 is in use
lsof -i :6379              # Check if port 6379 is in use
```

## 🎯 **Key Features**

- **Unified Setup**: One Docker Compose file for both development and production
- **Profile-Based**: Switch between environments with simple flags
- **Health Checks**: Automatic service health monitoring
- **Hot Reloading**: Frontend and backend development with live updates
- **Production Ready**: Test production stack locally before deployment

**Your complete full-stack development environment in one unified setup!** 🚀
