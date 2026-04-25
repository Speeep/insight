#!/bin/bash
set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_WS="$WORKSPACE_ROOT/ros_ws"
REPOS_FILE="$ROS_WS/third_party/isaac_ros_vslam.repos"
VENDORED_SRC_DIR="$ROS_WS/src/isaac_ros"

if [ ! -d "$ROS_WS" ]; then
  echo "❌ ros_ws not found at: $ROS_WS"
  exit 1
fi

if [ ! -f "$REPOS_FILE" ]; then
  echo "❌ Repos file not found: $REPOS_FILE"
  exit 1
fi

if ! command -v vcs >/dev/null 2>&1; then
  echo "📦 Installing vcstool..."
  apt-get update
  apt-get install -y python3-vcstool
fi

if ! command -v rosdep >/dev/null 2>&1; then
  echo "❌ rosdep not found. Install python3-rosdep in your environment first."
  exit 1
fi

mkdir -p "$VENDORED_SRC_DIR"

echo "📥 Importing Isaac ROS repositories into $VENDORED_SRC_DIR..."
vcs import "$VENDORED_SRC_DIR" < "$REPOS_FILE"

cd "$ROS_WS"

echo "🔧 Installing ROS dependencies via rosdep..."
rosdep update || true
rosdep install --from-paths src --ignore-src -r -y

echo "🏗️ Building workspace packages up to isaac_ros_visual_slam..."
colcon build --symlink-install --packages-up-to isaac_ros_visual_slam

echo "✅ Isaac ROS Visual SLAM vendoring setup complete."
echo "Next:"
echo "  cd $ROS_WS"
echo "  source install/setup.bash"
echo "  ros2 launch robot_bringup robot_vio_bringup_launch.py"

