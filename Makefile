.PHONY: help build run stop clean logs test setup dev prod

help:
	@echo "Stock Market Intelligence Platform - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup         - Initial setup (creates .env, runs scripts)"
	@echo "  make dev           - Start development environment"
	@echo "  make prod          - Start production environment"
	@echo ""
	@echo "Useful:"
	@echo "  make build         - Build all Docker images"
	@echo "  make logs          - View Docker logs"
	@echo "  make clean         - Stop and remove containers/volumes"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run code linting"
	@echo ""

setup:
	@echo "Setting up project..."
	@chmod +x scripts/setup.sh
	@bash scripts/setup.sh

dev:
	@echo "Starting development environment..."
	docker-compose up -d
	@echo "✅ Dev environment started"
	@echo "Services: http://localhost:8080 (API Gateway)"

prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

build:
	@echo "Building Docker images..."
	docker-compose build --no-cache

run:
	@docker-compose up -d

stop:
	@docker-compose stop

logs:
	@docker-compose logs -f

test:
	@echo "Running tests..."
	cd backend/api-gateway && mvn test
	cd mcp-servers/stock-data-server && python -m pytest

lint:
	@echo "Running linters..."
	cd backend/api-gateway && mvn checkstyle:check
	cd mcp-servers && flake8 .

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "✅ Containers and volumes removed"

clean-all: clean
	@echo "Removing all images..."
	docker-compose down -v --remove-orphans --rmi all

health:
	@docker-compose ps
	@echo ""
	@curl -s http://localhost:8080/health | jq .
	@curl -s http://localhost:5001/health | jq .
