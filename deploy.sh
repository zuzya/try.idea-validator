#!/bin/bash

# Usage: ./deploy.sh [version_tag]
# Example: ./deploy.sh v1.0
# Default tag is 'latest'

export TAG=${1:-latest}

echo "🦄 Deploying AI Unicorn Validator (Tag: $TAG)..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your API keys before deploying."
    echo "Required: OPENAI_API_KEY, GEMINI_API_KEY, TAVILY_API_KEY, LANGCHAIN_API_KEY"
    exit 1
fi

# Load env vars
source .env

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ Warning: OPENAI_API_KEY is missing in .env"
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️ Warning: GEMINI_API_KEY is missing in .env"
fi

echo "📦 Pulling specific version: $TAG..."
docker compose pull

echo "🚀 Starting Containers..."
docker compose up -d

echo "✅ Deployment Complete!"
echo "🌍 Frontend: http://localhost:5173 (or your VPS IP:5173)"
echo "🔌 Backend API: http://localhost:8010 (or your VPS IP:8010)"
echo "📜 Logs: docker compose logs -f"
