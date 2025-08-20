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

# Accept build arguments for VITE_* environment variables
# Railway passes these during build time
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_PYTHON_BACKEND_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_GOOGLE_REDIRECT_URI

# Set as environment variables for the build process
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_PYTHON_BACKEND_URL=$VITE_PYTHON_BACKEND_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_GOOGLE_REDIRECT_URI=$VITE_GOOGLE_REDIRECT_URI

# Debug: Show build arguments during build
RUN echo "=== BUILD ARGUMENTS ===" && \
    echo "VITE_GOOGLE_CLIENT_ID: ${VITE_GOOGLE_CLIENT_ID:-NOT_SET}" && \
    echo "VITE_PYTHON_BACKEND_URL: ${VITE_PYTHON_BACKEND_URL:-NOT_SET}" && \
    echo "VITE_SUPABASE_URL: ${VITE_SUPABASE_URL:-NOT_SET}" && \
    echo "VITE_SUPABASE_ANON_KEY: ${VITE_SUPABASE_ANON_KEY:-NOT_SET}" && \
    echo "VITE_GOOGLE_REDIRECT_URI: ${VITE_GOOGLE_REDIRECT_URI:-NOT_SET}" && \
    echo "================================"

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
