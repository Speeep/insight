from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    use_isaac_vslam = LaunchConfiguration('use_isaac_vslam')

    # Robot control launch.
    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('robot_control'),
                'launch',
                'robot_control_launch.py'
            )
        )
    )

    # Local D455 RealSense stream profile (used when not delegating to Isaac launch).
    realsense_local_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('realsense2_camera'),
                'launch',
                'rs_launch.py'
            )
        ),
        launch_arguments={
            'camera_namespace': '',
            'camera_name': 'realsense',
            'enable_color': 'true',
            'rgb_camera.color_profile': '640x480x30',
            'rgb_camera.color_format': 'RGB8',
            'enable_depth': 'true',
            'depth_module.depth_profile': '848x480x30',
            'enable_gyro': 'true',
            'enable_accel': 'true',
            'unite_imu_method': '1',
            'gyro_fps': '200',
            'accel_fps': '100',
            'enable_sync': 'true',
            'pointcloud.enable': 'false',
            'align_depth.enable': 'false',
        }.items(),
        condition=UnlessCondition(use_isaac_vslam),
    )

    # Preferred path when Isaac ROS Visual SLAM package is installed.
    # This official launch brings up RealSense + VSLAM together.
    isaac_vslam_launch = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'isaac_ros_visual_slam',
            'isaac_ros_visual_slam_realsense.launch.py'
        ],
        output='screen',
        condition=IfCondition(use_isaac_vslam),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_isaac_vslam',
            default_value='true',
            description='Run Isaac ROS VSLAM + RealSense launch (requires isaac_ros_visual_slam package).',
        ),
        control_launch,
        realsense_local_launch,
        isaac_vslam_launch,
    ])

