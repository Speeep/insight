from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_control",
            executable="motor_driver_node",
            name="motor_driver_node",
            output="screen",
        ),
        # Add more nodes here if needed (sensors, odometry, etc.)
    ])
