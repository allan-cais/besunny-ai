# BeSunny.ai Development Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help dev dev-backend dev-frontend build start stop restart logs clean test test-backend test-frontend shell-backend shell-frontend

# Default target
help:
	@echo "🚀 BeSunny.ai Development Commands"
	@echo ""
	@echo "📱 Development:"
	@echo "  dev              Start full development environment"
	@echo "  dev-backend      Start only backend service"
	@echo "  dev-frontend     Start only frontend service"
	@echo "  build            Build all services"
	@echo "  start            Start all services (no rebuild)"
	@echo "  stop             Stop all services"
	@echo "  restart          Restart all services"
	@echo ""
	@echo "🔍 Monitoring:"
	@echo "  logs             View all service logs"
	@echo "  logs-backend     View backend logs"
	@echo "  logs-frontend    View frontend logs"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test             Run all tests"
	@echo "  test-backend     Run backend tests"
	@echo "  test-frontend    Run frontend tests"
	@echo ""
	@echo "🛠️  Utilities:"
	@echo "  shell-backend    Access backend container shell"
	@echo "  shell-frontend   Access frontend container shell"
	@echo "  clean            Clean up containers and images"
	@echo ""

# Development commands
dev:
	@echo "🚀 Starting full development environment..."
	@./dev.sh

dev-backend:
	@echo "🔧 Starting backend service..."
	@docker-compose up --build -d backend redis

dev-frontend:
	@echo "📱 Starting frontend service..."
	@docker-compose up --build -d frontend

# Build and start commands
build:
	@echo "🔨 Building all services..."
	@docker-compose build

start:
	@echo "▶️  Starting all services..."
	@docker-compose up -d

stop:
	@echo "⏹️  Stopping all services..."
	@docker-compose down

restart:
	@echo "🔄 Restarting all services..."
	@docker-compose restart

# Logging commands
logs:
	@echo "📋 Viewing all service logs..."
	@docker-compose logs -f

logs-backend:
	@echo "📋 Viewing backend logs..."
	@docker-compose logs -f backend

logs-frontend:
	@echo "📋 Viewing frontend logs..."
	@docker-compose logs -f frontend

# Testing commands
test:
	@echo "🧪 Running all tests..."
	@docker-compose exec backend pytest
	@docker-compose exec frontend npm test

test-backend:
	@echo "🧪 Running backend tests..."
	@docker-compose exec backend pytest

test-frontend:
	@echo "🧪 Running frontend tests..."
	@docker-compose exec frontend npm test

# Shell access commands
shell-backend:
	@echo "🐚 Accessing backend container shell..."
	@docker-compose exec backend bash

shell-frontend:
	@echo "🐚 Accessing frontend container shell..."
	@docker-compose exec frontend sh

# Cleanup commands
clean:
	@echo "🧹 Cleaning up containers and images..."
	@docker-compose down -v --rmi all
	@docker system prune -f

# Status command
status:
	@echo "📊 Service status:"
	@docker-compose ps
