from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


# VSLAM expects ~45 Hz input by default (22 ms jitter threshold). Our
# RealSense streams run at 30 Hz, so frame deltas of ~33 ms are normal
# but trigger noisy WARN logs. Raise the threshold to match 30 Hz input.
VSLAM_JITTER_THRESHOLD_MS = 35.0


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

    # Preferred path: delegate camera + VSLAM bringup to the Isaac launch.
    # Pass serial pinning via env var (the upstream launch may not expose
    # camera_namespace as a launch arg, so we don't try to override it here).
    isaac_vslam_launch = ExecuteProcess(
        cmd=[
            'ros2', 'launch', 'isaac_ros_visual_slam',
            'isaac_ros_visual_slam_realsense.launch.py',
        ],
        additional_env={'RS_SERIAL_NO': ROBOT_REALSENSE_SERIAL},
        output='screen',
        condition=IfCondition(use_isaac_vslam),
    )

    # The Isaac realsense launch publishes RealSense topics under
    # /camera/camera/... but visual_slam_node subscribes to /camera/...
    # Bridge those topics with topic_tools relay so VSLAM gets data.
    relay_topics = [
        ('/camera/camera/infra1/image_rect_raw', '/camera/infra1/image_rect_raw'),
        ('/camera/camera/infra1/camera_info', '/camera/infra1/camera_info'),
        ('/camera/camera/infra2/image_rect_raw', '/camera/infra2/image_rect_raw'),
        ('/camera/camera/infra2/camera_info', '/camera/infra2/camera_info'),
        ('/camera/camera/imu', '/camera/imu'),
    ]
    relay_nodes = [
        Node(
            package='topic_tools',
            executable='relay',
            name=f'relay_{src.strip("/").replace("/", "_")}',
            arguments=[src, dst],
            output='log',
            condition=IfCondition(use_isaac_vslam),
        )
        for src, dst in relay_topics
    ]

    # Override VSLAM jitter threshold a few seconds after launch so the node
    # has time to come up before we set the param.
    set_jitter_threshold = TimerAction(
        period=8.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    'ros2', 'param', 'set', '/visual_slam_node',
                    'image_jitter_threshold_ms', str(VSLAM_JITTER_THRESHOLD_MS),
                ],
                output='screen',
            )
        ],
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
        *relay_nodes,
        set_jitter_threshold,
    ])
