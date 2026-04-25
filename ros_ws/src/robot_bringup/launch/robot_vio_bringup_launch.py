from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


# Pin the on-robot RealSense D455 by serial number so the launch always
# binds to the same physical camera even if other RealSense devices appear.
ROBOT_REALSENSE_SERIAL = '234222301624'


def generate_launch_description():
    use_isaac_vslam = LaunchConfiguration('use_isaac_vslam')
    realsense_serial = LaunchConfiguration('realsense_serial')

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
    # Topics are forced to the /camera/... namespace so they match what VSLAM expects.
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
            'camera_name': 'camera',
            'serial_no': realsense_serial,
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
    # Force camera_namespace+camera_name so RealSense topics land at /camera/...
    # matching VSLAM subscriptions, and pin the camera serial.
    isaac_vslam_launch = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'isaac_ros_visual_slam',
            'isaac_ros_visual_slam_realsense.launch.py',
            'camera_namespace:=',
            'camera_name:=camera',
            ['serial_no:=', realsense_serial],
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
        DeclareLaunchArgument(
            'realsense_serial',
            default_value=ROBOT_REALSENSE_SERIAL,
            description='Pin the RealSense camera by serial number for deterministic device selection.',
        ),
        control_launch,
        realsense_local_launch,
        isaac_vslam_launch,
    ])
