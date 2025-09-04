import threading
import time
from typing import List, Tuple, Optional

import serial

# Control packet protocol
CONTROL_START_BYTE = 0xAA
EFFORT_MIN = -100
EFFORT_MAX = 100

DRIVE_MODE_STRAIGHT = 1
DRIVE_MODE_ROTATE = 2
DRIVE_MODE_STRAFE = 3

# Feedback packet protocol (must match Arduino firmware)
FEEDBACK_START_BYTE = 0xBB
NUM_POTS = 4
FEEDBACK_PKT_LEN = 6  # [start][p1][p2][p3][p4][checksum]


class SerialComm:
    """
    Manages serial I/O for:
      - Sending a single drive command: [0xAA][effort int8][mode uint8][reserved=0x00][checksum]
        where checksum = XOR(effort, mode, reserved)
      - Receiving 4 potentiometer readings continuously as [0xBB][p1][p2][p3][p4][checksum]
    Thread-safe and designed to be used by a higher-level drivetrain.
    """

    def __init__(
        self,
        port: str = "/dev/arduino",
        baud: int = 115200,
        timeout: float = 0.1,
        feedback_start_byte: int = FEEDBACK_START_BYTE,
    ) -> None:
        self._port = port
        self._baud = baud
        self._timeout = timeout
        self._feedback_start_byte = feedback_start_byte & 0xFF

        try:
            self._ser = serial.Serial(self._port, self._baud, timeout=self._timeout)
        except serial.SerialException as e:
            raise RuntimeError(f"Could not open serial port {self._port}: {e}")

        self._send_lock = threading.Lock()
        self._pots_lock = threading.Lock()
        self._running = True

        self._latest_pots: List[int] = [0] * NUM_POTS
        self._buf = bytearray()

        self._feedback_thread = threading.Thread(target=self._feedback_loop, daemon=True)
        self._feedback_thread.start()

        self._wait_for_go_banner(grace_seconds=5.0)

    # -------------------------- Public API --------------------------

    def close(self) -> None:
        self._running = False
        try:
            if self._ser.is_open:
                self._ser.close()
        except Exception:
            pass

    def get_pots(self) -> Tuple[int, int, int, int]:
        with self._pots_lock:
            return tuple(self._latest_pots)  # type: ignore[return-value]

    def send_drive_command(self, effort: int, mode: int) -> None:
        """
        Send a single drive command using the protocol:
          [START=0xAA][effort int8][mode uint8][reserved=0x00][checksum]
        where checksum = XOR(effort, mode, reserved).
        """
        effort_clamped = max(EFFORT_MIN, min(EFFORT_MAX, int(effort)))
        mode_byte = int(mode) & 0xFF
        reserved = 0x00

        packet = bytearray(
            [CONTROL_START_BYTE, effort_clamped & 0xFF, mode_byte, reserved]
        )

        checksum = 0
        for b in packet[1:4]:  # XOR of effort, mode, reserved
            checksum ^= b
        packet.append(checksum & 0xFF)

        with self._send_lock:
            self._ser.write(packet)

    # ------------------------ Internal Logic ------------------------

    def _wait_for_go_banner(self, grace_seconds: float) -> None:
        """Wait briefly for an optional 'GO' banner; proceed regardless after grace period."""
        deadline = time.time() + max(0.0, grace_seconds)
        while time.time() < deadline:
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
            except Exception:
                line = ""
            if line == "GO":
                return

    def _feedback_loop(self) -> None:
        """Continuously decode feedback packets of the form [start][p1][p2][p3][p4][chk]."""
        while self._running:
            try:
                pkt = self._sync_and_read_packet()
                if not pkt:
                    continue
                # pkt length is guaranteed
                _, p1, p2, p3, p4, chk = pkt
                if self._verify_checksum(p1, p2, p3, p4, chk):
                    with self._pots_lock:
                        self._latest_pots = [p1, p2, p3, p4]
            except Exception:
                # Keep listening even on decode errors
                time.sleep(0.005)

    def _sync_and_read_packet(self) -> Optional[bytes]:
        # Pull in what's available
        chunk = self._ser.read(max(1, self._ser.in_waiting))
        if not chunk:
            return None
        self._buf.extend(chunk)

        # Find start byte and assemble full packet
        while True:
            try:
                start_idx = self._buf.index(self._feedback_start_byte)
            except ValueError:
                self._buf.clear()
                return None

            if len(self._buf) - start_idx >= FEEDBACK_PKT_LEN:
                pkt = bytes(self._buf[start_idx:start_idx + FEEDBACK_PKT_LEN])
                del self._buf[:start_idx + FEEDBACK_PKT_LEN]
                return pkt
            else:
                if start_idx > 0:
                    del self._buf[:start_idx]
                return None

    @staticmethod
    def _verify_checksum(p1: int, p2: int, p3: int, p4: int, chk: int) -> bool:
        return ((p1 ^ p2 ^ p3 ^ p4) & 0xFF) == (chk & 0xFF)
