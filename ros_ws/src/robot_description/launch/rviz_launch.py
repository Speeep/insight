from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('robot_description')

    urdf_file = os.path.join(pkg_share, 'urdf', 'robot.urdf')
    rviz_config_file = os.path.join(pkg_share, 'config', 'robot.rviz')

    assert os.path.exists(urdf_file), f"URDF not found: {urdf_file}"
    assert os.path.exists(rviz_config_file), f"RViz config not found: {rviz_config_file}"

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': open(urdf_file).read()}]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        ),
    ])

