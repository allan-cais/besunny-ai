# Docker Setup for BeSunny.ai

This document explains how to build and run BeSunny.ai using Docker.

## Prerequisites

- Docker installed and running
- Docker Compose (usually comes with Docker Desktop)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Start both services:**
   ```bash
   docker-compose up
   ```

2. **Access the services:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

### Option 2: Build and Run Individually

1. **Build the images:**
   ```bash
   ./docker-build.sh
   ```

2. **Run the frontend:**
   ```bash
   docker run -p 3000:80 besunny-frontend:latest
   ```

3. **Run the backend:**
   ```bash
   docker run -p 8000:8000 besunny-backend:latest
   ```

## Dockerfile Details

### Frontend (`Dockerfile.frontend`)

- **Base Image**: `node:18-alpine` for building
- **Production Image**: `nginx:alpine` for serving
- **Multi-stage build** for optimized production image
- **Port**: 80 (mapped to 3000 on host)

### Backend (`Dockerfile.backend`)

- **Base Image**: `python:3.11-slim`
- **Includes**: System dependencies (gcc, g++)
- **Port**: 8000
- **Entry Point**: `python start.py`

## Environment Variables

### Frontend
- `VITE_RAILWAY_BACKEND_URL`: Backend API URL

### Backend
- `ENVIRONMENT`: Application environment
- `DEBUG`: Enable debug mode
- `HOST`: Server host
- `PORT`: Server port

## Troubleshooting

### Common Issues

1. **"npm: command not found"**
   - The Dockerfile now uses `node:18-alpine` which includes npm

2. **"pip: command not found"**
   - The Dockerfile now uses `python:3.11-slim` which includes pip

3. **Build fails**
   - Ensure Docker is running
   - Check that all source files are present
   - Verify package.json and requirements.txt exist

### Debug Commands

```bash
# Check Docker status
docker info

# View running containers
docker ps

# View container logs
docker logs <container_id>

# Enter container shell
docker exec -it <container_id> /bin/bash

# Remove all containers and images (clean slate)
docker system prune -a
```

## Development Workflow

1. **Make code changes**
2. **Rebuild images:**
   ```bash
   docker-compose build
   ```
3. **Restart services:**
   ```bash
   docker-compose up
   ```

## Production Deployment

For production, consider:

1. **Environment-specific builds**
2. **Health checks**
3. **Resource limits**
4. **Security scanning**
5. **Multi-architecture builds**

## File Structure

```
.
├── Dockerfile.frontend      # Frontend Docker configuration
├── Dockerfile.backend       # Backend Docker configuration
├── docker-compose.yml       # Multi-service orchestration
├── docker-build.sh          # Build script
├── .dockerignore            # Docker build exclusions
└── DOCKER_README.md         # This file
```

## Support

If you encounter issues:

1. Check this README
2. Verify Docker is running
3. Check container logs
4. Ensure all prerequisites are met
