#!/usr/bin/env bash
# Build script for The Breeding Vat
# Builds all task-specific Docker images

set -e

echo "🧪 Building The Breeding Vat Docker Images"
echo "==========================================="

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

# Build UI image (includes orchestrator)
echo "📦 Building UI image (breeding-vat-ui:latest)..."
docker build \
    --file docker/Dockerfile.ui \
    --tag breeding-vat-ui:latest \
    --tag breeding-vat-ui:$(date +%Y%m%d-%H%M%S) \
    .

# Build task-specific images
echo "📦 Building merge image (breeding-vat-merge:latest)..."
docker build \
    --file docker/Dockerfile.merge \
    --tag breeding-vat-merge:latest \
    .

echo "📦 Building eval image (breeding-vat-eval:latest)..."
docker build \
    --file docker/Dockerfile.eval \
    --tag breeding-vat-eval:latest \
    .

echo "📦 Building SAE image (breeding-vat-sae:latest)..."
docker build \
    --file docker/Dockerfile.sae \
    --tag breeding-vat-sae:latest \
    .

echo ""
echo "✅ All images built successfully!"
echo ""
echo "Next steps:"
echo "  1. Start UI: docker compose up -d breeding-vat-ui"
echo "  2. Open:     http://localhost:8501"
echo ""
