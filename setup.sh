#!/bin/bash
set -euo pipefail

echo "🚀 Installing NVIDIA Container Toolkit and configuring Docker runtime..."

if ! command -v curl >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y curl
fi

if ! command -v gpg >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y gnupg
fi

echo "📦 Adding NVIDIA Container Toolkit apt repository..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

sudo apt update
sudo apt install -y nvidia-container-toolkit

echo "🔧 Configuring nvidia-container-toolkit to work with Docker..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "✅ NVIDIA container runtime is now configured."
echo "You can now build and run your Insight Docker container."
