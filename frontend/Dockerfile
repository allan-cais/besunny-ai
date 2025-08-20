# Frontend Dockerfile for Railway monorepo deployment
# This runs from the frontend/ directory

FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application (use production mode by default, but can be overridden)
ARG BUILD_MODE=production

# Pass through all VITE_* environment variables to the build process
# This is crucial for Railway to inject environment variables during build
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}
ENV VITE_PYTHON_BACKEND_URL=${VITE_PYTHON_BACKEND_URL}
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
ENV VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}
ENV VITE_GOOGLE_REDIRECT_URI=${VITE_GOOGLE_REDIRECT_URI}

# Build with explicit production mode
RUN npm run build:production

# Clean up to save space
RUN rm -rf node_modules

# Production stage with nginx
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration to conf.d directory (overrides default server)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
