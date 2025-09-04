#! /usr/bin/env python3

import curses
import time
from typing import Tuple

try:
    from robot.serial_comm import (
        SerialComm,
        DRIVE_MODE_STRAIGHT,
        DRIVE_MODE_ROTATE,
        DRIVE_MODE_STRAFE,
        EFFORT_MIN,
        EFFORT_MAX,
    )
except Exception:
    from serial_comm import (
        SerialComm,
        DRIVE_MODE_STRAIGHT,
        DRIVE_MODE_ROTATE,
        DRIVE_MODE_STRAFE,
        EFFORT_MIN,
        EFFORT_MAX,
    )


def clamp(value: int, lo: int, hi: int) -> int:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def mode_name(mode: int) -> str:
    if mode == DRIVE_MODE_STRAIGHT:
        return "STRAIGHT"
    if mode == DRIVE_MODE_ROTATE:
        return "ROTATE"
    if mode == DRIVE_MODE_STRAFE:
        return "STRAFE"
    return f"UNKNOWN({mode})"


def draw_ui(stdscr: "curses._CursesWindow", effort: int, mode: int, pots: Tuple[int, int, int, int]) -> None:
    stdscr.erase()
    stdscr.addstr(0, 0, "Teleop Controls:")
    stdscr.addstr(1, 0, "  1: Straight (effort=0)   2: Rotate (effort=0)   3: Strafe (effort=0)")
    stdscr.addstr(2, 0, "  W/S: Straight +/- effort  A/D: Strafe +/- effort  Q/E: Rotate +/- effort")
    stdscr.addstr(3, 0, "  Space: EMERGENCY STOP (effort=0)   X: Quit   Arrows: Adjust effort +/- 5")
    stdscr.addstr(5, 0, f"Mode   : {mode_name(mode)}  ({mode})")
    stdscr.addstr(6, 0, f"Effort : {effort:4d}  (range {EFFORT_MIN}..{EFFORT_MAX})")
    stdscr.addstr(8, 0, "Pots   : FR BR FL BL")
    stdscr.addstr(9, 0, f"          {pots[0]:3d} {pots[1]:3d} {pots[2]:3d} {pots[3]:3d}")
    stdscr.refresh()


def teleop(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    ser = SerialComm()  # uses default /dev/ttyACM0 at 115200

    effort = 0
    mode = DRIVE_MODE_STRAIGHT
    last_send = 0.0
    send_period_s = 0.05  # 20 Hz
    default_drive_effort = 50

    try:
        while True:
            ch = stdscr.getch()
            if ch != -1:
                if ch in (ord('x'), ord('X')):
                    break
                elif ch == curses.KEY_UP:
                    effort = clamp(effort + 5, EFFORT_MIN, EFFORT_MAX)
                elif ch == curses.KEY_DOWN:
                    effort = clamp(effort - 5, EFFORT_MIN, EFFORT_MAX)
                elif ch == ord(' '):
                    effort = 0
                elif ch == ord('1'):
                    mode = DRIVE_MODE_STRAIGHT
                    effort = 0
                elif ch == ord('2'):
                    mode = DRIVE_MODE_ROTATE
                    effort = 0
                elif ch == ord('3'):
                    mode = DRIVE_MODE_STRAFE
                    effort = 0
                elif ch in (ord('w'), ord('W')):
                    mode = DRIVE_MODE_STRAIGHT
                    effort = clamp(default_drive_effort, EFFORT_MIN, EFFORT_MAX)
                elif ch in (ord('s'), ord('S')):
                    mode = DRIVE_MODE_STRAIGHT
                    effort = clamp(-default_drive_effort, EFFORT_MIN, EFFORT_MAX)
                elif ch in (ord('a'), ord('A')):
                    mode = DRIVE_MODE_STRAFE
                    effort = clamp(default_drive_effort, EFFORT_MIN, EFFORT_MAX)
                elif ch in (ord('d'), ord('D')):
                    mode = DRIVE_MODE_STRAFE
                    effort = clamp(-default_drive_effort, EFFORT_MIN, EFFORT_MAX)
                elif ch in (ord('q'), ord('Q')):
                    mode = DRIVE_MODE_ROTATE
                    effort = clamp(default_drive_effort, EFFORT_MIN, EFFORT_MAX)
                elif ch in (ord('e'), ord('E')):
                    mode = DRIVE_MODE_ROTATE
                    effort = clamp(-default_drive_effort, EFFORT_MIN, EFFORT_MAX)

            now = time.time()
            if now - last_send >= send_period_s:
                ser.send_drive_command(effort, mode)
                last_send = now

            pots = ser.get_pots()
            draw_ui(stdscr, effort, mode, pots)
            time.sleep(0.01)
    finally:
        ser.close()


def main() -> None:
    curses.wrapper(teleop)


if __name__ == "__main__":
    main()


