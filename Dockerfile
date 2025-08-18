# Default Dockerfile for BeSunny.ai
# This builds the frontend by default
# For backend, use: docker build -f Dockerfile.backend .

FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build:production

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
