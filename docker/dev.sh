#!/usr/bin/env bash
# Development helper for The Breeding Vat

set -e

COMMAND=${1:-help}

case $COMMAND in
    up)
        echo "🚀 Starting The Breeding Vat UI..."
        docker compose --file docker/docker-compose.yml up -d breeding-vat-ui
        echo "✅ UI started"
        echo "📊 Streamlit:  http://localhost:8501"
        ;;
    up-dev)
        echo "🧪 Starting with Jupyter dev environment..."
        docker compose --file docker/docker-compose.yml --profile dev up -d
        echo "✅ Services started"
        echo "📊 Streamlit:  http://localhost:8501"
        echo "📓 Jupyter:    http://localhost:8888 (token: check logs)"
        ;;
    down)
        echo "🛑 Stopping services..."
        docker compose --file docker/docker-compose.yml down
        echo "✅ Stopped"
        ;;
    logs)
        docker compose --file docker/docker-compose.yml logs -f
        ;;
    logs-ui)
        docker compose --file docker/docker-compose.yml logs -f breeding-vat-ui
        ;;
    shell)
        SERVICE=${2:-breeding-vat-ui}
        docker compose --file docker/docker-compose.yml exec $SERVICE bash
        ;;
    build)
        bash docker/build.sh
        ;;
    ps)
        docker compose --file docker/docker-compose.yml ps
        ;;
    help)
        echo "Usage: ./docker/dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  up           Start UI"
        echo "  up-dev       Start with Jupyter"
        echo "  down         Stop services"
        echo "  logs         Stream logs"
        echo "  logs-ui      Stream UI logs"
        echo "  shell        Enter container shell"
        echo "  build        Build images"
        echo "  ps           List containers"
        echo "  help         Show this help"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './docker/dev.sh help' for usage."
        exit 1
        ;;
esac
