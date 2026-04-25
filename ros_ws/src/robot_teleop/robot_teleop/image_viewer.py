#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
import cv2
import numpy as np

class CompressedImageViewer(Node):
    def __init__(self):
        super().__init__('compressed_image_viewer')

        # Parameters for low-latency teleop viewing.
        self.declare_parameter('image_topic', '/realsense/color/image_raw/compressed')
        self.declare_parameter('display_rate_hz', 30.0)
        self.image_topic = str(self.get_parameter('image_topic').value)
        display_rate_hz = float(self.get_parameter('display_rate_hz').value)
        period = 1.0 / max(display_rate_hz, 1.0)

        # Keep only the latest frame and prefer fresh data over reliability.
        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
        )

        self._latest_msg = None

        # Subscribe to the RealSense compressed color feed.
        self.subscription = self.create_subscription(
            CompressedImage,
            self.image_topic,
            self.listener_callback,
            qos_profile)
        self.subscription  # prevent unused variable warning
        self._display_timer = self.create_timer(period, self.display_latest_frame)
        self.get_logger().info(f"Subscribed to {self.image_topic}")

    def listener_callback(self, msg: CompressedImage):
        # Replace any queued frame so teleop always shows freshest image.
        self._latest_msg = msg

    def display_latest_frame(self):
        if self._latest_msg is None:
            return
        try:
            # Convert from ROS2 CompressedImage msg to OpenCV image
            np_arr = np.frombuffer(self._latest_msg.data, np.uint8)
            image_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image_np is not None:
                cv2.imshow("RealSense Color Feed", image_np)
                cv2.waitKey(1)
            else:
                self.get_logger().warn("Failed to decode image")
        except Exception as e:
            self.get_logger().error(f"Exception in image callback: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = CompressedImageViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

