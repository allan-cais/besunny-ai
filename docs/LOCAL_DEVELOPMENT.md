# 🚀 BeSunny.ai Local Development Guide

This guide will help you set up and run BeSunny.ai locally for development and testing.

## 📋 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/) for version control
- Your existing `.env` files for both frontend and backend
- Remote database access (Supabase)

## 🏗️ Quick Start

### 1. **Start the Development Environment**

```bash
# Make the startup script executable (first time only)
chmod +x dev.sh

# Start all services
./dev.sh
```

This will:
- Build and start the backend, frontend, and Redis services
- Wait for all services to be ready
- Display the URLs for accessing your application

### 2. **Manual Start (Alternative)**

```bash
# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🌐 Service URLs

Once running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Redis**: localhost:6379

## 🔧 Development Workflow

### **Backend Development**

The backend runs with hot reloading enabled. Any changes to Python files will automatically restart the server.

```bash
# View backend logs
docker-compose logs -f backend

# Restart backend only
docker-compose restart backend

# Rebuild backend
docker-compose up --build -d backend
```

### **Frontend Development**

The frontend runs with Vite hot module replacement. Changes are reflected immediately in the browser.

```bash
# View frontend logs
docker-compose logs -f frontend

# Restart frontend only
docker-compose restart frontend

# Rebuild frontend
docker-compose up --build -d frontend
```

## 📁 Project Structure

```
besunny-ai/
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   ├── .env                # Backend environment variables
│   ├── env.example         # Example environment file
│   └── Dockerfile.dev      # Development Dockerfile
├── frontend/               # React TypeScript frontend
│   ├── src/                # Source code
│   ├── .env                # Frontend environment variables
│   └── Dockerfile.dev      # Development Dockerfile
├── docker-compose.yml      # Local development services
├── dev.sh                  # Development startup script
└── LOCAL_DEVELOPMENT.md    # This file
```

## 🔐 Environment Configuration

### **Backend Environment Variables**

Copy `backend/env.example` to `backend/.env` and configure:

```bash
# Required for basic functionality
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Required for AI services
OPENAI_API_KEY=your-openai-api-key

# Required for Google integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Required for vector embeddings
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment
```

### **Frontend Environment Variables**

Ensure your frontend `.env` has:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 🧪 Testing

### **Backend Testing**

```bash
# Run tests in the backend container
docker-compose exec backend pytest

# Run tests with coverage
docker-compose exec backend pytest --cov=app

# Run specific test file
docker-compose exec backend pytest tests/test_auth_services.py
```

### **Frontend Testing**

```bash
# Run tests in the frontend container
docker-compose exec frontend npm test

# Run tests in watch mode
docker-compose exec frontend npm run test:watch
```

## 🐛 Debugging

### **Backend Debugging**

The backend includes `debugpy` for remote debugging. You can:

1. Set breakpoints in your Python code
2. Connect your IDE's debugger to `localhost:5678`
3. Use `ipython` for interactive debugging

### **Frontend Debugging**

- Use browser DevTools for frontend debugging
- React DevTools extension for React component inspection
- Network tab for API call debugging

## 📊 Monitoring

### **Health Checks**

- Backend health: http://localhost:8000/health
- Backend status: http://localhost:8000/health/status
- Backend readiness: http://localhost:8000/health/ready

### **Logs**

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Port conflicts**: Ensure ports 3000, 8000, and 6379 are available
2. **Permission issues**: Make sure `dev.sh` is executable (`chmod +x dev.sh`)
3. **Build failures**: Try rebuilding with `docker-compose up --build -d`
4. **Environment issues**: Verify your `.env` files are properly configured

### **Reset Everything**

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
./dev.sh
```

## 🔄 Development Commands

```bash
# Start development environment
./dev.sh

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build -d

# Access service shell
docker-compose exec backend bash
docker-compose exec frontend sh

# View running services
docker-compose ps
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Vite Documentation](https://vitejs.dev/)

## 🆘 Need Help?

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables are set correctly
3. Ensure Docker Desktop is running
4. Try rebuilding: `docker-compose up --build -d`

---

**Happy coding! 🚀**
