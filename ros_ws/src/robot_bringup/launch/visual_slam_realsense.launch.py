"""Custom Isaac ROS Visual SLAM + RealSense launch.

Mirrors the upstream isaac_ros_visual_slam_realsense.launch.py but:
  * fixes the RealSense node namespace so topics land at /camera/...
    (matching visual_slam_node's remappings without needing relays)
  * exposes image/imu jitter thresholds as launch arguments so we can
    tune them without forking the upstream launch
  * pins the RealSense device by serial number for deterministic selection
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue


# Pin the on-robot RealSense D455 by serial number. Override at launch time
# with realsense_serial:=<serial> if needed.
ROBOT_REALSENSE_SERIAL = '234222301624'


def generate_launch_description():
    realsense_serial = LaunchConfiguration('realsense_serial')
    image_jitter_threshold_ms = LaunchConfiguration('image_jitter_threshold_ms')
    imu_jitter_threshold_ms = LaunchConfiguration('imu_jitter_threshold_ms')

    # RealSense camera node. Namespace is empty so topics land under /camera/...
    realsense_camera_node = Node(
        name='camera',
        namespace='',
        package='realsense2_camera',
        executable='realsense2_camera_node',
        parameters=[{
            'serial_no': realsense_serial,
            'enable_infra1': True,
            'enable_infra2': True,
            'enable_color': False,
            'enable_depth': False,
            'depth_module.emitter_enabled': 0,
            'depth_module.depth_profile': '848x480x30',
            'enable_gyro': True,
            'enable_accel': True,
            'gyro_fps': 200,
            'accel_fps': 200,
            'unite_imu_method': 2,
        }],
        output='screen',
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': False,
            'rectified_images': True,
            'enable_imu_fusion': True,
            'gyro_noise_density': 0.000244,
            'gyro_random_walk': 0.000019393,
            'accel_noise_density': 0.001862,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'image_jitter_threshold_ms': ParameterValue(
                image_jitter_threshold_ms, value_type=float),
            'imu_jitter_threshold_ms': ParameterValue(
                imu_jitter_threshold_ms, value_type=float),
            'base_frame': 'camera_link',
            'imu_frame': 'camera_gyro_optical_frame',
            'enable_slam_visualization': True,
            'enable_landmarks_view': True,
            'enable_observations_view': True,
            'camera_optical_frames': [
                'camera_infra1_optical_frame',
                'camera_infra2_optical_frame',
            ],
        }],
        remappings=[
            ('visual_slam/image_0', '/camera/infra1/image_rect_raw'),
            ('visual_slam/camera_info_0', '/camera/infra1/camera_info'),
            ('visual_slam/image_1', '/camera/infra2/image_rect_raw'),
            ('visual_slam/camera_info_1', '/camera/infra2/camera_info'),
            ('visual_slam/imu', '/camera/imu'),
        ],
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[visual_slam_node],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'realsense_serial',
            default_value=ROBOT_REALSENSE_SERIAL,
            description='RealSense camera serial number for deterministic device selection.',
        ),
        DeclareLaunchArgument(
            'image_jitter_threshold_ms',
            default_value='35.0',
            description='Max allowed delta between consecutive image frames before VSLAM warns.',
        ),
        DeclareLaunchArgument(
            'imu_jitter_threshold_ms',
            default_value='35.0',
            description='Max allowed delta between consecutive IMU samples before VSLAM warns.',
        ),
        realsense_camera_node,
        visual_slam_launch_container,
    ])
