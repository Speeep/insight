#!/usr/bin/env python3
import argparse
import serial
import sys
import time
import signal

# -----------------------------------------------------------------------------
# USAGE
#   python3 read_pots.py --port /dev/ttyACM0 --baud 115200 --start-byte 0x55
#
# DESCRIPTION
#   Listens to an Arduino that prints "GO" when ready and then streams compact
#   feedback packets:
#     [START][pot1][pot2][pot3][pot4][checksum]
#   where checksum = pot1 ^ pot2 ^ pot3 ^ pot4. Each pot is an 8-bit value.
#
# CONTROLS
#   Ctrl+C to stop.
#
# TIPS
#   - If you see frequent "desync/recovered" messages, verify --start-byte
#     matches FEEDBACK_START_BYTE in your Arduino sketch.
#   - If no output appears: confirm the port, permissions (dialout group),
#     and that the Arduino is actually calling sendFeedback().
# -----------------------------------------------------------------------------


def parse_hex_or_int(s: str) -> int:
    try:
        return int(s, 0)  # supports "85", "0x55", "055"
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer/hex value: {s}")

def make_args():
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Simple listener for Arduino potentiometer feedback packets."
    )
    p.add_argument("--port", default="/dev/ttyACM0", help="Serial device")
    p.add_argument("--baud", type=int, default=115200, help="Baud rate")
    p.add_argument("--start-byte", type=parse_hex_or_int, default=0xBB,
                   help="Feedback start byte (must match FEEDBACK_START_BYTE on Arduino)")
    p.add_argument("--timeout", type=float, default=0.2,
                   help="Serial read timeout in seconds")
    p.add_argument("--show-rate-every", type=int, default=100,
                   help="Print an average packet rate line every N packets (0 = never)")
    p.add_argument("--raw", action="store_true",
                   help="Print raw bytes as hex too")
    p.add_argument("--csv", action="store_true",
                   help="CSV output: ts_ms,p1,p2,p3,p4,ok")
    return p.parse_args()


class PotListener:
    PKT_LEN = 6  # [start][p1][p2][p3][p4][checksum]

    def __init__(self, ser: serial.Serial, start_byte: int, show_rate_every: int, raw: bool, csv: bool):
        self.ser = ser
        self.start_byte = start_byte & 0xFF
        self.show_rate_every = show_rate_every
        self.raw = raw
        self.csv = csv

        self._running = True
        self._buf = bytearray()
        self._pkt_count = 0
        self._t0 = time.time()

    def stop(self):
        self._running = False

    def wait_for_go(self):
        print("Waiting for Arduino 'GO' ...")
        # We read line-wise here in case the sketch prints "GO\n" on reset.
        # If your sketch does not print GO, this will time out repeatedly; we
        # fall back to packet sync after a short grace period.
        deadline = time.time() + 5.0  # 5s grace; still proceed if not seen
        while time.time() < deadline:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
            except Exception:
                line = ""
            if line:
                # Show anything seen during bring-up for visibility.
                # (Commonly you'll see the "GO" line here.)
                # Comment out the next line if you prefer silence.
                # print(f"[arduino] {line}")
                if line == "GO":
                    print("✅ Arduino is ready.")
                    return
        print("⚠️  Did not see 'GO' banner, proceeding to stream decode anyway...")

    def _sync_and_read_packet(self) -> bytes | None:
        """
        Read bytes until a full packet is assembled.
        Returns the 6-byte packet (as bytes) or None on timeout/partial.
        """
        # Pull in what's available
        chunk = self.ser.read(max(1, self.ser.in_waiting))
        if not chunk:
            return None
        self._buf.extend(chunk)

        # Search for start byte and try to assemble a full packet
        while True:
            # Find the next start byte
            try:
                start_idx = self._buf.index(self.start_byte)
            except ValueError:
                # No start byte in buffer; keep last few bytes to avoid growth
                self._buf.clear()
                return None

            # If we have enough bytes past start to form a packet, slice it out
            if len(self._buf) - start_idx >= self.PKT_LEN:
                pkt = bytes(self._buf[start_idx:start_idx + self.PKT_LEN])
                # Drop everything up to end of this packet
                del self._buf[:start_idx + self.PKT_LEN]
                return pkt
            else:
                # Not enough yet; drop earlier noise keep from start_idx
                if start_idx > 0:
                    del self._buf[:start_idx]
                return None

    @staticmethod
    def _verify_checksum(p1, p2, p3, p4, chk) -> bool:
        return ((p1 ^ p2 ^ p3 ^ p4) & 0xFF) == (chk & 0xFF)

    def _print_reading(self, ts_ms: int, p1, p2, p3, p4, ok, pkt_bytes: bytes | None):
        if self.csv:
            print(f"{ts_ms},{p1},{p2},{p3},{p4},{int(ok)}")
            return

        if self.raw and pkt_bytes is not None:
            hexs = " ".join(f"{b:02X}" for b in pkt_bytes)
            print(f"[{ts_ms:>8} ms] pots=({p1:3},{p2:3},{p3:3},{p4:3}) "
                  f"checksum={'OK' if ok else 'BAD'}   raw=[{hexs}]")
        else:
            print(f"[{ts_ms:>8} ms] pots=({p1:3},{p2:3},{p3:3},{p4:3}) "
                  f"checksum={'OK' if ok else 'BAD'}")

    def _maybe_print_rate(self):
        if self.show_rate_every <= 0:
            return
        if self._pkt_count % self.show_rate_every != 0:
            return
        dt = max(1e-6, time.time() - self._t0)
        rate = self._pkt_count / dt
        print(f"📈 Avg packets: {self._pkt_count} in {dt:.2f}s  →  {rate:.1f} Hz")

    def run(self):
        print("Listening for feedback packets...")
        while self._running:
            pkt = self._sync_and_read_packet()
            if not pkt:
                continue

            # pkt = [start][p1][p2][p3][p4][chk]
            if len(pkt) != self.PKT_LEN:
                # Shouldn't happen due to slicing, but guard anyway
                continue

            _, p1, p2, p3, p4, chk = pkt
            ok = self._verify_checksum(p1, p2, p3, p4, chk)
            ts_ms = int(time.time() * 1000)
            self._pkt_count += 1
            self._print_reading(ts_ms, p1, p2, p3, p4, ok, pkt)
            self._maybe_print_rate()


def main():
    args = make_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=args.timeout)
    except serial.SerialException as e:
        print(f"❌ Could not open {args.port} @ {args.baud}: {e}")
        sys.exit(1)

    listener = PotListener(
        ser=ser,
        start_byte=args.start_byte,
        show_rate_every=args.show_rate_every,
        raw=args.raw,
        csv=args.csv
    )

    def _handle_sigint(sig, frame):
        listener.stop()
    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        listener.wait_for_go()
        listener.run()
    finally:
        try:
            if ser.is_open:
                ser.close()
        except Exception:
            pass
        print("\n🛑 Closed.")

if __name__ == "__main__":
    main()

