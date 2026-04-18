#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-insight}"
CONTAINER_NAME="${CONTAINER_NAME:-insight-container}"

# Detect architecture
ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ]; then
    DOCKERFILE="Dockerfile.x86_64"
    USE_X11=true
elif [ "$ARCH" = "aarch64" ]; then
    DOCKERFILE="Dockerfile.aarch64"
    USE_X11=false
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "❌ Docker image '$IMAGE_NAME' not found."
    echo "Build it first with: ./build_docker.sh"
    exit 1
fi

if [ "$USE_X11" = true ]; then
    echo "🔑 Allowing Docker to access X11..."
    xhost +local:docker
fi

# Check if container is already running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Container '$CONTAINER_NAME' is already running. Attaching to it..."
    docker exec -it "$CONTAINER_NAME" /bin/bash

# Check if container exists but is stopped
elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Container '$CONTAINER_NAME' exists but is not running. Starting and attaching..."
    docker start "$CONTAINER_NAME" >/dev/null
    docker exec -it "$CONTAINER_NAME" /bin/bash

# Container does not exist, create and run it
else
    echo "Container '$CONTAINER_NAME' does not exist. Creating and starting..."
    if [ "$USE_X11" = true ]; then
        docker run -it \
            --runtime nvidia \
            --gpus all \
            --privileged \
            --network host \
            -e DISPLAY="${DISPLAY:-:0}" \
            -e QT_X11_NO_MITSHM=1 \
            -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
            -v /dev:/dev \
            -v /sys:/sys \
	    -v /run/udev:/run/udev:ro \
            -v /tmp:/tmp \
            -v "$(pwd)":/workspace \
            --name "$CONTAINER_NAME" \
            "$IMAGE_NAME" /bin/bash
    else
        docker run -it \
            --runtime nvidia \
            --gpus all \
            --privileged \
            --network host \
            -v /dev:/dev \
            -v /sys:/sys \
	    -v /run/udev:/run/udev:ro \
            -v /tmp:/tmp \
            -v "$(pwd)":/workspace \
            --name "$CONTAINER_NAME" \
            "$IMAGE_NAME" /bin/bash
    fi
fi

if [ "$USE_X11" = true ]; then
    echo "🔒 Revoking Docker X11 access..."
    xhost -local:docker
fi

