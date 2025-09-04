#!/usr/bin/env python3

import serial
import time
import signal
import sys
import termios
import tty
import select
import threading

# ==== CONFIGURATION ====
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
PACKET_START_BYTE = 0xAA      # Must match PACKET_START_BYTE on the Arduino
MOTOR_COUNT = 8
EFFORT_MIN = -100
EFFORT_MAX = 100
EFFORT_STEP = 1
SEND_INTERVAL = 0.1  # seconds

# Motor names in the exact protocol order (first 4 drives, then 4 turns)
MOTOR_NAMES = [
    "Front Right Drive",   # 0
    "Back Left Drive",     # 1
    "Back Right Drive",    # 2
    "Front Left Drive",    # 3
    "Left Back Turn",      # 4
    "Right Back Turn",     # 5
    "Right Front Turn",    # 6
    "Front Left Turn"      # 7
]
# ========================

# Initialize serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"❌ Could not open serial port {SERIAL_PORT}: {e}")
    sys.exit(1)

# Wait for "GO" from Arduino robustly
print("Waiting for Arduino 'GO' signal...")
while True:
    raw_line = ser.readline()
    try:
        line = raw_line.decode().strip()
        if line == "GO":
            print("✅ Arduino is ready!")
            break
    except UnicodeDecodeError:
        continue

# Start background thread to drain any further incoming feedback silently
def _drain_feedback():
    while True:
        try:
            n = ser.in_waiting
            if n:
                ser.read(n)  # discard feedback packets from Arduino
        except Exception:
            pass
        time.sleep(0.01)

drainer = threading.Thread(target=_drain_feedback, daemon=True)
drainer.start()

# Global flag to ensure shutdown runs once
shutdown_called = False

# Handle Ctrl+C and cleanup
def shutdown(sig, frame):
    global shutdown_called
    if shutdown_called:
        return
    shutdown_called = True
    print("\n🛑 Exiting...")
    try:
        if ser.is_open:
            ser.close()
    except Exception as e:
        print(f"⚠️ Error closing serial: {e}")
    try:
        restore_terminal()
    except Exception as e:
        print(f"⚠️ Error restoring terminal: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

# Terminal input functions
def get_key(timeout=0.1):
    dr, _, _ = select.select([sys.stdin], [], [], timeout)
    if dr:
        return sys.stdin.read(1)
    return None

def setup_terminal():
    global old_settings
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

def restore_terminal():
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

# Send packet to all motors
def send_motor_batch(efforts):
    assert len(efforts) == MOTOR_COUNT
    packet = bytearray()
    packet.append(PACKET_START_BYTE)  # Start byte

    # 8 efforts (int8_t each, two's complement)
    for e in efforts:
        e = max(EFFORT_MIN, min(EFFORT_MAX, e))
        packet.append(e & 0xFF)

    # Reserved byte (index 9 on the Arduino side)
    packet.append(0x00)

    # Checksum = XOR of bytes 1..9 (8 efforts + reserved)
    checksum = 0
    for b in packet[1:10]:
        checksum ^= b
    packet.append(checksum)

    ser.write(packet)

# Main interactive loop
selected_motor = 0
effort = 0
efforts = [0] * MOTOR_COUNT

setup_terminal()

print("\n🧪 Deadband Testing Mode\n")
print("Controls:")
print("  W / S : Switch motor up/down")
print("  D / A : Increase / Decrease effort")
print("  R     : Reset current motor effort to 0")
print("  Q     : Quit\n")

print(f"🔀 Selected motor: {MOTOR_NAMES[selected_motor]} (index {selected_motor}) | Effort: {effort}")

last_send_time = time.time()

try:
    while True:
        now = time.time()
        if now - last_send_time >= SEND_INTERVAL:
            # Only one motor active at a time:
            for i in range(MOTOR_COUNT):
                efforts[i] = effort if i == selected_motor else 0
            try:
                send_motor_batch(efforts)
            except Exception as e:
                print(f"⚠️ Serial write failed: {e}")
                shutdown(None, None)
            last_send_time = now

        key = get_key()
        if key:
            key = key.lower()
            if key == 'w':  # Up: next motor
                selected_motor = (selected_motor + 1) % MOTOR_COUNT
                effort = efforts[selected_motor]  # sync effort with current motor
                print(f"🔀 Switched to motor {selected_motor}: {MOTOR_NAMES[selected_motor]} | Effort: {effort}")
            elif key == 's':  # Down: previous motor
                selected_motor = (selected_motor - 1) % MOTOR_COUNT
                effort = efforts[selected_motor]
                print(f"🔀 Switched to motor {selected_motor}: {MOTOR_NAMES[selected_motor]} | Effort: {effort}")
            elif key == 'd':  # Increase effort
                effort = min(EFFORT_MAX, effort + EFFORT_STEP)
                efforts = [0] * MOTOR_COUNT
                efforts[selected_motor] = effort
                print(f"➡️  Motor {selected_motor} effort: {effort}")
            elif key == 'a':  # Decrease effort
                effort = max(EFFORT_MIN, effort - EFFORT_STEP)
                efforts = [0] * MOTOR_COUNT
                efforts[selected_motor] = effort
                print(f"⬅️  Motor {selected_motor} effort: {effort}")
            elif key == 'r':  # Reset current motor
                effort = 0
                efforts[selected_motor] = 0
                print(f"🔁 Reset effort for motor {MOTOR_NAMES[selected_motor]} to 0")
            elif key == 'q':  # Quit
                break

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
finally:
    shutdown(None, None)

