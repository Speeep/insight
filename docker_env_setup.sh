# docker_env_setup.sh
if [[ $- == *i* ]]; then
    # ROS setup
    source /opt/ros/humble/setup.bash
    [ -f /workspace/ros_ws/install/setup.bash ] && source /workspace/ros_ws/install/setup.bash

    # Aliases
    alias eb="vim ~/.bashrc"
    alias sb="source ~/.bashrc"
    alias cb="cat /root/.bashrc"
    alias ca="cat /workspace/docker_env_setup.sh"
    alias c="clear"
    alias x="exit"
    alias h="history"
    alias rosenv="source /opt/ros/humble/setup.bash"
    alias sws="cd /workspace/ros_ws && rm -rf build install log && colcon build --symlink-install && source install/setup.bash"
    alias ws="cd /workspace/ros_ws"
    alias cbt="colcon build --symlink-install --packages-select"
    alias cl="colcon list"
    alias cln="rm -rf build install log"
    alias rl="ros2 launch"
    alias rn="ros2 run"
    alias rps="ros2 pkg search"
    alias rtopic="ros2 topic list"
    alias recho="ros2 topic echo"
    alias rinfo="ros2 topic info"
    alias rtype="ros2 topic type"
    alias rservice="ros2 service list"
    alias rcall="ros2 service call"
    alias raction="ros2 action list"
    alias rlist="ros2 pkg list"
    alias rparam="ros2 param list"
    alias rget="ros2 param get"
    alias rset="ros2 param set"
    alias rtf="ros2 run tf2_tools view_frames"
    alias rwt="watch -n1 ros2 topic list"
    alias rnodes="ros2 node list"
    alias start="rl robot_bringup robot_bringup_launch.py"
    alias teleop="rl robot_teleop robot_teleop_launch.py"
    alias rviz="rl robot_description rviz_launch.py"
fi

