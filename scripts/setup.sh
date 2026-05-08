#!/bin/bash

# Initialize Stock Market Intelligence Platform
# This script sets up the initial environment and databases

set -e

echo "=========================================="
echo "Stock Market Intelligence Platform Setup"
echo "=========================================="

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not installed"
    exit 1
fi

echo "✅ Prerequisites OK"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual values"
    echo "⚠️  Especially: API keys, database passwords, LLM credentials"
fi

# Start Docker Compose
echo ""
echo "Starting Docker Compose..."
docker-compose up -d

# Wait for databases to be healthy
echo ""
echo "Waiting for databases to be healthy..."
sleep 30

# Check health
echo ""
echo "Checking service health..."
docker-compose ps

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Services running:"
echo "- API Gateway:        http://localhost:8080"
echo "- User Service:       http://localhost:8081"
echo "- Recommendation:     http://localhost:8082"
echo "- Portfolio Service:  http://localhost:8083"
echo "- Stock Data MCP:     http://localhost:5001"
echo "- Sentiment MCP:      http://localhost:5002"
echo "- Prediction MCP:     http://localhost:5003"
echo "- PostgreSQL:         localhost:5432"
echo "- TimescaleDB:        localhost:5433"
echo "- MongoDB:            localhost:27017"
echo "- Redis:              localhost:6379"
echo "- Prometheus:         http://localhost:9090"
echo "- Grafana:            http://localhost:3001"
echo ""
echo "Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run: docker-compose up -d"
echo "3. Check health: docker-compose ps"
echo "4. View logs: docker-compose logs -f api-gateway"
echo ""
