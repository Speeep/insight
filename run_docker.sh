#!/bin/bash
set -e

IMAGE_NAME=insight
CONTAINER_NAME=insight-container

# Detect architecture
ARCH=$(uname -m)
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

echo "🚧 Building Docker image for $ARCH using $DOCKERFILE..."
docker build -t $IMAGE_NAME -f $DOCKERFILE .

if [ "$USE_X11" = true ]; then
    echo "🔑 Allowing Docker to access X11..."
    xhost +local:docker
fi

# Check if container is already running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Container '$CONTAINER_NAME' is already running. Attaching to it..."
    docker exec -it $CONTAINER_NAME /bin/bash

# Check if container exists but is stopped
elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Container '$CONTAINER_NAME' exists but is not running. Starting and attaching..."
    docker start $CONTAINER_NAME
    docker exec -it $CONTAINER_NAME /bin/bash

# Container does not exist, create and run it
else
    echo "Container '$CONTAINER_NAME' does not exist. Creating and starting..."
    if [ "$USE_X11" = true ]; then
        docker run -it --rm \
            --runtime nvidia \
            --gpus all \
            --privileged \
            --network host \
            -e DISPLAY=$DISPLAY \
            -e QT_X11_NO_MITSHM=1 \
            -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
            -v /dev:/dev \
            -v /sys:/sys \
	    -v /run/udev:/run/udev:ro \
            -v /tmp:/tmp \
            -v $(pwd):/workspace \
            --name $CONTAINER_NAME \
            $IMAGE_NAME /bin/bash
    else
        docker run -it --rm \
            --runtime nvidia \
            --gpus all \
            --privileged \
            --network host \
            -v /dev:/dev \
            -v /sys:/sys \
	    -v /run/udev:/run/udev:ro \
            -v /tmp:/tmp \
            -v $(pwd):/workspace \
            --name $CONTAINER_NAME \
            $IMAGE_NAME /bin/bash
    fi
fi

if [ "$USE_X11" = true ]; then
    echo "🔒 Revoking Docker X11 access..."
    xhost -local:docker
fi

