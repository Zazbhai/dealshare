#!/bin/bash
# Build script for Docker image

set -e

echo "Building Docker image for Deal Share Automation..."

# Build for Linux AMD64
docker buildx build \
  --platform linux/amd64 \
  -t deal-share-automation:latest \
  -t deal-share-automation:$(date +%Y%m%d) \
  .

echo "Build complete!"
echo "To run: docker run -d -p 5000:5000 --name deal-share-automation deal-share-automation:latest"

