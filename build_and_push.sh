#!/bin/bash

# Usage: ./build_and_push.sh [version_tag]
# Example: ./build_and_push.sh v1.0
# Default tag is 'latest'

export TAG=${1:-latest}
DOCKER_USER="zuzyadocker" # Hardcoded as requested
REPO_NAME="idea-validator"

echo "🐳 Building and Pushing images to $DOCKER_USER/$REPO_NAME"
echo "🔖 Tag: $TAG"

# Check if logged in (basic check)
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running."
    exit 1
fi

echo "📦 Building images..."
# Explicitly build first to ensure latest code is captured
# FORCE LINUX/AMD64 for VPS compatibility (since you are building on macOS)
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker-compose build

echo "🚀 Pushing to registry..."
# Push images defined in docker-compose.yml
docker-compose push

echo "✅ Done! Images pushed:"
echo "   - $DOCKER_USER/$REPO_NAME:backend-$TAG"
echo "   - $DOCKER_USER/$REPO_NAME:frontend-$TAG"
echo ""
echo "Now run 'deploy.sh $TAG' on your VPS."
