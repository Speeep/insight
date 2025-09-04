#!/usr/bin/env python3
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import JointState

# Use the existing low-level serial class + drive mode constants
from robot_control.serial_comm import (
    SerialComm,
    DRIVE_MODE_STRAIGHT,
    DRIVE_MODE_ROTATE,
    DRIVE_MODE_STRAFE,
    EFFORT_MIN,
    EFFORT_MAX,
)

def clamp(v: int, lo: int, hi: int) -> int:
    return lo if v < lo else hi if v > hi else v


class MotorDriverNode(Node):
    """
    One unified node:
      • Subscribes to /cmd_vel and sends serial drive commands
      • Publishes wheel pod potentiometer readings to /wheelpod_angles
      • Periodically re-sends the last command to satisfy Arduino watchdog
    """

    def __init__(self):
        super().__init__('motor_driver_node')

        # ---- Parameters you can tune
        self.declare_parameter('command_rate_hz', 20.0)      # how often to send serial commands
        self.declare_parameter('cmd_vel_timeout_s', 0.5)     # stop if no cmd_vel within this time
        self.declare_parameter('scale_linear_to_effort', 100.0)   # m/s -> effort scale
        self.declare_parameter('scale_strafe_to_effort', 100.0)   # m/s -> effort scale
        self.declare_parameter('scale_angular_to_effort', 100.0)  # rad/s -> effort scale

        self.command_rate_hz = float(self.get_parameter('command_rate_hz').value)
        self.cmd_vel_timeout_s = float(self.get_parameter('cmd_vel_timeout_s').value)
        self.k_lin = float(self.get_parameter('scale_linear_to_effort').value)
        self.k_strafe = float(self.get_parameter('scale_strafe_to_effort').value)
        self.k_ang = float(self.get_parameter('scale_angular_to_effort').value)

        # ---- Serial comms (existing class, unchanged)
        self.ser = SerialComm()

        # ---- ROS I/O
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.wheelpod_pub = self.create_publisher(Float32MultiArray, '/wheelpod_angles', 10)
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        # /wheelpod_angles order: [Front Right, Back Right, Front Left, Back Left]

        # ---- Visualization mapping (raw 0..255 -> radians)
        # Center fixed at 127 (straight), limit to +/- 90 deg
        # Scale: radians per raw count. 270 deg / 255 counts.
        self.declare_parameter('pot_rad_per_count', -4.712389 / 255.0)
        self.pot_rad_per_count = float(self.get_parameter('pot_rad_per_count').value)

        # ---- State for watchdog-friendly periodic sending
        self.last_mode = DRIVE_MODE_STRAIGHT
        self.last_effort = 0
        self.last_cmd_time = time.time()

        # ---- Timer for periodic control + feedback publish
        period = 1.0 / self.command_rate_hz if self.command_rate_hz > 0 else 0.05
        self.timer = self.create_timer(period, self.control_loop)

    # --------- Callbacks ---------

    def cmd_vel_callback(self, msg: Twist):
        """
        Map Twist to a drive mode + effort.
        Priority: x (forward/back) > y (strafe) > z (rotate).
        Tune the scale params above to match your robot.
        """
        # Choose mode
        if abs(msg.linear.x) > 1e-6:
            mode = DRIVE_MODE_STRAIGHT
            raw_effort = msg.linear.x * self.k_lin
        elif abs(msg.linear.y) > 1e-6:
            mode = DRIVE_MODE_STRAFE
            raw_effort = msg.linear.y * self.k_strafe
        elif abs(msg.angular.z) > 1e-6:
            mode = DRIVE_MODE_ROTATE
            raw_effort = msg.angular.z * self.k_ang
        else:
            mode = self.last_mode
            raw_effort = 0.0

        effort = clamp(int(raw_effort), EFFORT_MIN, EFFORT_MAX)

        # Update state; actual sending happens in control_loop() at a fixed rate
        self.last_mode = mode
        self.last_effort = effort
        self.last_cmd_time = time.time()

    # --------- Periodic loop ---------

    def control_loop(self):
        """
        Runs at command_rate_hz:
          • Re-send last (mode, effort) unless cmd_vel timed out (then send stop)
          • Publish latest potentiometer readings as /wheelpod_angles
        """
        # Feed Arduino watchdog with the latest command (or stop on timeout)
        now = time.time()
        if (now - self.last_cmd_time) > self.cmd_vel_timeout_s:
            mode_to_send = self.last_mode
            effort_to_send = 0
        else:
            mode_to_send = self.last_mode
            effort_to_send = self.last_effort

        try:
            self.ser.send_drive_command(effort_to_send, mode_to_send)
        except Exception as e:
            self.get_logger().error(f"Failed to send drive command: {e}")

        # Publish wheel pod angles
        try:
            pots = self.ser.get_pots()  # (FR, BR, FL, BL)
            msg = Float32MultiArray()
            # Order: [Front Right, Back Right, Front Left, Back Left]
            msg.data = [float(p) for p in pots]
            self.wheelpod_pub.publish(msg)

            # Also publish JointState for visualization in RViz
            js = JointState()
            js.header.stamp = self.get_clock().now().to_msg()
            js.name = [
                'chassis_to_front_right_pod',
                'chassis_to_back_right_pod',
                'chassis_to_front_left_pod',
                'chassis_to_back_left_pod',
            ]
            # Map raw (0..255) -> radians around fixed center (127)
            fr, br, fl, bl = [float(p) for p in pots]
            def map_raw(raw):
                angle = (raw - 127.0) * self.pot_rad_per_count
                # Clamp to URDF joint limits +/- 90 deg
                if angle < -1.5708:
                    angle = -1.5708
                if angle > 1.5708:
                    angle = 1.5708
                return angle
            # Apply fixed directionality: FR and BL decrease toward strafe (negative),
            # BR and FL increase toward strafe (positive)
            js.position = [
                map_raw(fr),
                map_raw(br),
                map_raw(fl),
                map_raw(bl),
            ]
            self.joint_pub.publish(js)
        except Exception as e:
            self.get_logger().warn(f"Failed to publish wheelpod angles: {e}")

    # --------- Cleanup ---------

    def destroy_node(self):
        try:
            self.ser.close()
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

