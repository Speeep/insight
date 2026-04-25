from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Robot control launch
    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('robot_control'),
                'launch',
                'robot_control_launch.py'))
    )

    # RealSense D455-oriented launch profile for teleop:
    # - keep a lightweight color stream for driving
    # - enable IMU so VIO work can start next
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('realsense2_camera'),
                'launch',
                'rs_launch.py')),
        launch_arguments={
            'camera_namespace': '',
            'camera_name': 'realsense',
            'enable_color': 'true',
            'rgb_camera.color_profile': '640x480x30',   # resolution + fps
            'rgb_camera.color_format': 'RGB8',          # color encoding
            'enable_depth': 'false',
            'enable_gyro': 'true',
            'enable_accel': 'true',
            'unite_imu_method': '1',
            'gyro_fps': '200',
            'accel_fps': '100',
            'enable_sync': 'false',
        }.items()
    )

    return LaunchDescription([
        control_launch,
        realsense_launch,
    ])
