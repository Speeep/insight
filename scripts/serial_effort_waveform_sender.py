#!/usr/bin/env python3

import serial
import time
import signal
import sys

# Configuration
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
MOTOR_COUNT = 7
EFFORT_MIN = -100
EFFORT_MAX = 100
CYCLE_DURATION = 20.0
STEP_INTERVAL = 0.05

# Derived
HALF_CYCLE = CYCLE_DURATION / 2
EFFORT_RANGE = EFFORT_MAX - EFFORT_MIN
STEPS_PER_HALF = int(HALF_CYCLE / STEP_INTERVAL)

# Serial setup
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"❌ Could not open serial port {SERIAL_PORT}: {e}")
    print("💡 Make sure the device is plugged in and the path is correct!")
    sys.exit(1)

# Wait for "GO" signal from Arduino
print("Waiting for Arduino 'GO' signal...")
while True:
    line = ser.readline().decode().strip()
    if line == "GO":
        print("Arduino is ready!")
        break

# Signal handler to close serial gracefully
def shutdown(sig, frame):
    print("\nExiting...")
    ser.close()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

# Send full packet of 7 efforts
def send_motor_batch(efforts):
    assert len(efforts) == MOTOR_COUNT
    packet = bytearray()
    packet.append(0xAA)

    for e in efforts:
        e = max(EFFORT_MIN, min(EFFORT_MAX, e))
        packet.append(e & 0xFF if e < 0 else e)

    packet.append(0x00)  # Reserved byte
    checksum = 0
    for b in packet[1:16]:
        checksum ^= b
    packet.append(checksum)

    ser.write(packet)

# Read 5-byte feedback message from Arduino
def try_read_feedback():
    if ser.in_waiting >= 5:
        start = ser.read(1)
        if start == b'\xBB':
            data = ser.read(4)
            if len(data) == 4:
                pot1, pot2, digital, checksum = data
                if checksum == (pot1 ^ pot2 ^ digital):
                    print(f"[Feedback] Pot1: {pot1}, Pot2: {pot2}, Digital: {digital}")
                else:
                    print("⚠️ Feedback checksum mismatch")

# Main waveform loop
print("🎉 Sending ramp waveform to all motors! 🎉")
print("Press Ctrl+C to stop.")
tick = 0

while True:
    # Compute effort value for this step
    phase = (tick % (2 * STEPS_PER_HALF)) / STEPS_PER_HALF
    if phase <= 1:
        effort = int(EFFORT_MIN + EFFORT_RANGE * phase)
    else:
        effort = int(EFFORT_MAX - EFFORT_RANGE * (phase - 1))

    send_motor_batch([effort] * MOTOR_COUNT)
    try_read_feedback()
    tick += 1
    time.sleep(STEP_INTERVAL)
