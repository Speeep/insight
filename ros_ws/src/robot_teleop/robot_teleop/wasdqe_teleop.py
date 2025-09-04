#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from pynput import keyboard
import os


class WASDQETeleop(Node):
    def __init__(self):
        super().__init__('wasdqe_teleop')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        # Streaming rate (Hz) and behavior
        self.declare_parameter('publish_rate_hz', 10.0)
        self.declare_parameter('stream_zeros', True)
        self.publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self.stream_zeros = bool(self.get_parameter('stream_zeros').value)

        self.linear_speed = 0.5
        self.angular_speed = 0.5

        # Track current and previous velocities to only publish on change
        self.vel = {"linear_x": 0.0, "linear_y": 0.0, "angular_z": 0.0}
        self.prev_vel = self.vel.copy()

        self.get_logger().info("WASDQE Teleop Node Started")
        self.get_logger().info("Controls: W=forward, S=backward, "
                               "A=left strafe, D=right strafe, "
                               "Q=rotate CCW, E=rotate CW")

        # Timer to continuously publish current twist at a fixed rate
        period = 1.0 / self.publish_rate_hz if self.publish_rate_hz > 0 else 0.05
        self._timer = self.create_timer(period, self._timer_publish)

    def _publish_current(self):
        twist = Twist()
        twist.linear.x = self.vel["linear_x"]
        twist.linear.y = self.vel["linear_y"]
        twist.angular.z = self.vel["angular_z"]
        self.publisher_.publish(twist)

    def publish_if_changed(self):
        if self.vel != self.prev_vel:
            self._publish_current()
            self.prev_vel = self.vel.copy()

            # Clear terminal and print a single status line
            os.system('clear')  # use 'cls' if running on Windows
            print(f"Current Twist: "
                  f"linear.x={self.vel['linear_x']:.2f}, "
                  f"linear.y={self.vel['linear_y']:.2f}, "
                  f"angular.z={self.vel['angular_z']:.2f}")

    def _timer_publish(self):
        # Always publish current command at a fixed rate when active
        active = (self.vel["linear_x"] != 0.0 or
                  self.vel["linear_y"] != 0.0 or
                  self.vel["angular_z"] != 0.0)
        if active or self.stream_zeros:
            self._publish_current()

    def on_press(self, key):
        try:
            if key.char == 'w':
                self.vel["linear_x"] = self.linear_speed
            elif key.char == 's':
                self.vel["linear_x"] = -self.linear_speed
            elif key.char == 'a':
                self.vel["linear_y"] = self.linear_speed
            elif key.char == 'd':
                self.vel["linear_y"] = -self.linear_speed
            elif key.char == 'q':
                self.vel["angular_z"] = self.angular_speed
            elif key.char == 'e':
                self.vel["angular_z"] = -self.angular_speed
        except AttributeError:
            pass
        self.publish_if_changed()

    def on_release(self, key):
        try:
            if key.char in ['w', 's']:
                self.vel["linear_x"] = 0.0
            elif key.char in ['a', 'd']:
                self.vel["linear_y"] = 0.0
            elif key.char in ['q', 'e']:
                self.vel["angular_z"] = 0.0
        except AttributeError:
            pass
        self.publish_if_changed()


def main(args=None):
    rclpy.init(args=args)
    node = WASDQETeleop()

    # Start keyboard listener
    listener = keyboard.Listener(
        on_press=node.on_press,
        on_release=node.on_release
    )
    listener.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


