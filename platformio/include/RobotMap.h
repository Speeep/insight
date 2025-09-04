#pragma once

// Motor PWM pin assignments
// FRONT_RIGHT: green + purple
#define RIGHT_FRONT_R_PWM 2
#define RIGHT_FRONT_L_PWM 3
// BACK_LEFT: green + blue
#define LEFT_BACK_R_PWM 4
#define LEFT_BACK_L_PWM 5
// BACK_RIGHT: yellow + purple
#define RIGHT_BACK_R_PWM 10
#define RIGHT_BACK_L_PWM 11
// FRONT_LEFT: orange + green
#define LEFT_FRONT_R_PWM 6
#define LEFT_FRONT_L_PWM 7

// Turn motor digital pin assignments (use non-PWM pins only)
// 3 - Left Turn Motor (yellow + green)
#define LEFT_BACK_TURN_R_DIGITAL 22
#define LEFT_BACK_TURN_L_DIGITAL 23
// 4 - Right Back Turn Motor (orange + blue)
#define RIGHT_BACK_TURN_R_DIGITAL 24
#define RIGHT_BACK_TURN_L_DIGITAL 25
// 7 - Right Front Turn Motor (white + blue)
#define RIGHT_FRONT_TURN_R_DIGITAL 26
#define RIGHT_FRONT_TURN_L_DIGITAL 27
// 8 - Front Left Turn Motor (blue + purple)
#define LEFT_FRONT_TURN_R_DIGITAL 28
#define LEFT_FRONT_TURN_L_DIGITAL 29

// Feedback pins (four potentiometers)
#define RIGHT_BACK_POT A0
#define RIGHT_FRONT_POT A1
#define LEFT_FRONT_POT A2
#define LEFT_BACK_POT A3

// Other constants
#define WATCHDOG_TIMEOUT_MS 500
#define STATUS_INTERVAL_MS 50

// Serial receive timeout
#define SERIAL_RECEIVE_TIMEOUT_MS 100

// Effort and PWM mapping
#define EFFORT_MIN -100
#define EFFORT_MAX 100
#define PWM_MIN 0
#define PWM_MAX 255

// Deadband values for each motor
#define FRONT_RIGHT_DEADBAND 30
#define BACK_LEFT_DEADBAND 30
#define LEFT_TURN_DEADBAND 25
#define RIGHT_TURN_DEADBAND 25
#define BACK_RIGHT_DEADBAND 30
#define FRONT_LEFT_DEADBAND 30
#define LEFT_EXTRA_DEADBAND 30

// Protocol constants
#define PACKET_START_BYTE 0xAA
#define FEEDBACK_START_BYTE 0xBB
#define MOTOR_COUNT 8
#define PACKET_LENGTH 5

// Motor direction flags
#define REVERSED true
#define NOT_REVERSED false

// ============================
// Drivetrain/Turning Constants
// ============================

// Drivetrain modes
// 1 = Straight, 2 = Rotate (Point Turn), 3 = Strafe
#define DRIVE_MODE_STRAIGHT 1
#define DRIVE_MODE_ROTATE 2
#define DRIVE_MODE_STRAFE 3

// Potentiometer control parameters (8-bit domain)
#define POT_TOLERANCE_STOP 5
#define POT_TOLERANCE_REENGAGE 7
#define POT_EDGE_GUARD 10
#define POT_FAULT_EXTREME_LOW 0
#define POT_FAULT_EXTREME_HIGH 255
#define POT_FAULT_CONSECUTIVE_SAMPLES 5

// Target pot raw setpoints per mode and pod (8-bit, 0..255)
// Naming convention: FL = Front Left, FR = Front Right, BL = Back Left, BR = Back Right

// Straight (all forward)
#define FL_POT_STRAIGHT 127
#define FR_POT_STRAIGHT 127
#define BL_POT_STRAIGHT 127
#define BR_POT_STRAIGHT 127

// Rotate / Point Turn (left back & right front ~76; left front & right back ~179)
#define FL_POT_ROTATE 179
#define FR_POT_ROTATE 76
#define BL_POT_ROTATE 76
#define BR_POT_ROTATE 179

// Strafe (left back & right front ~42; left front & right back ~212)
#define FL_POT_STRAFE 212
#define FR_POT_STRAFE 42
#define BL_POT_STRAFE 42
#define BR_POT_STRAFE 212
