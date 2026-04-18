#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-insight}"

# Detect architecture
ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ]; then
  DOCKERFILE="Dockerfile.x86_64"
elif [ "$ARCH" = "aarch64" ]; then
  DOCKERFILE="Dockerfile.aarch64"
else
  echo "❌ Unsupported architecture: $ARCH"
  exit 1
fi

echo "🚧 Building Docker image '$IMAGE_NAME' for $ARCH using $DOCKERFILE..."
docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" .

echo "✅ Build complete: $IMAGE_NAME"

