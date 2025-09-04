from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_teleop",
            executable="wasdqe_teleop",
            name="wasdqe_teleop",
            output="screen",
            prefix="xterm -e",
        )
    ])

