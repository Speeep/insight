#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np

class CompressedImageViewer(Node):
    def __init__(self):
        super().__init__('compressed_image_viewer')

        # Subscribe to the RealSense compressed color feed
        self.subscription = self.create_subscription(
            CompressedImage,
            '/realsense/color/image_raw/compressed',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.get_logger().info("Subscribed to /realsense/color/image_raw/compressed")

    def listener_callback(self, msg: CompressedImage):
        try:
            # Convert from ROS2 CompressedImage msg to OpenCV image
            np_arr = np.frombuffer(msg.data, np.uint8)
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

