from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Teleop node in xterm
        Node(
            package="robot_teleop",
            executable="wasdqe_teleop",
            name="wasdqe_teleop",
            output="screen",
            prefix="xterm -e",
        ),
        
        # Image viewer node in xterm
        Node(
            package='robot_teleop',
            executable='image_viewer',
            name='image_viewer',
            output='screen',
            prefix='xterm -e'
        ),

    ])

