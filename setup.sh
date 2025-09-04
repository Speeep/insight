#!/bin/bash
set -e

echo "🚀 Installing NVIDIA Container Toolkit and configuring Docker runtime..."

sudo apt update
sudo apt install -y nvidia-container-toolkit

echo "🔧 Configuring nvidia-container-toolkit to work with Docker..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "✅ NVIDIA container runtime is now configured."
echo "You can now build and run your Insight Docker container."
