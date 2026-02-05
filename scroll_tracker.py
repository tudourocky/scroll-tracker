"""
Scroll Wheel Tracker
Tracks your mouse scroll wheel activity with session and all-time statistics.
Data is persisted to a local JSON file so stats accumulate across sessions.

Usage:
    python scroll_tracker.py

Press Ctrl+C to stop tracking and save your session.
"""

import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from pynput import mouse

# ── Config ───────────────────────────────────────────────────────────────────

DATA_FILE = Path(__file__).parent / "scroll_data.json"
DISPLAY_REFRESH_INTERVAL = 0.25  # seconds between display refreshes


# ── Data persistence ─────────────────────────────────────────────────────────

def load_data() -> dict:
    """Load saved scroll data from disk, or return defaults."""
    defaults = {
        "total_scroll_up": 0,
        "total_scroll_down": 0,
        "total_clicks": 0,
        "total_sessions": 0,
        "total_time_seconds": 0.0,
        "first_session": None,
        "last_session": None,
    }
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            for key, value in defaults.items():
                data.setdefault(key, value)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_data(data: dict) -> None:
    """Write scroll data to disk."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Display helpers ──────────────────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def format_duration(seconds: float) -> str:
    """Turn seconds into a human-readable string like '2h 14m 03s'."""
    td = timedelta(seconds=int(seconds))
    parts = []
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        parts.append(f"{hours}h")
    if minutes or hours:
        parts.append(f"{minutes:02d}m")
    parts.append(f"{secs:02d}s")
    return " ".join(parts)


def scroll_bar(up: int, down: int, width: int = 30) -> str:
    """Render a simple ratio bar showing up vs down scrolls."""
    total = up + down
    if total == 0:
        return "[" + " " * width + "]"
    up_portion = round(up / total * width)
    down_portion = width - up_portion
    return "[" + "^" * up_portion + "v" * down_portion + "]"


def render_display(session: dict, alltime: dict, session_start: float):
    """Draw the live dashboard to the terminal."""
    session_elapsed = time.time() - session_start
    alltime_elapsed = alltime["total_time_seconds"] + session_elapsed

    session_total = session["up"] + session["down"]
    alltime_total = (
        alltime["total_scroll_up"]
        + alltime["total_scroll_down"]
        + session_total
    )

    # Scrolls per minute for this session
    session_minutes = session_elapsed / 60
    spm = session_total / session_minutes if session_minutes > 0.05 else 0

    lines = [
        "",
        "  ╔══════════════════════════════════════════════════╗",
        "  ║            SCROLL WHEEL TRACKER                  ║",
        "  ╠══════════════════════════════════════════════════╣",
        "  ║  SESSION                                         ║",
        f"  ║   Scroll Up    : {session['up']:<10}                    ║",
        f"  ║   Scroll Down  : {session['down']:<10}                    ║",
        f"  ║   Total Clicks : {session_total:<10}                    ║",
        f"  ║   Duration     : {format_duration(session_elapsed):<10}                    ║",
        f"  ║   Scrolls/min  : {spm:<10.1f}                    ║",
        f"  ║   Direction    : {scroll_bar(session['up'], session['down'])} ║",
        "  ╠══════════════════════════════════════════════════╣",
        "  ║  ALL TIME                                        ║",
        f"  ║   Scroll Up    : {alltime['total_scroll_up'] + session['up']:<10}                    ║",
        f"  ║   Scroll Down  : {alltime['total_scroll_down'] + session['down']:<10}                    ║",
        f"  ║   Total Clicks : {alltime_total:<10}                    ║",
        f"  ║   Sessions     : {alltime['total_sessions'] + 1:<10}                    ║",
        f"  ║   Total Time   : {format_duration(alltime_elapsed):<10}                    ║",
        "  ╠══════════════════════════════════════════════════╣",
        "  ║  Press Ctrl+C to stop and save                   ║",
        "  ╚══════════════════════════════════════════════════╝",
        "",
    ]
    clear_screen()
    print("\n".join(lines))


# ── Main tracker ─────────────────────────────────────────────────────────────

def main():
    alltime = load_data()

    session = {"up": 0, "down": 0}
    session_start = time.time()
    lock = threading.Lock()
    running = threading.Event()
    running.set()

    # ── Scroll callback ──────────────────────────────────────────────────
    def on_scroll(_x, _y, _dx, dy):
        with lock:
            if dy > 0:
                session["up"] += 1
            elif dy < 0:
                session["down"] += 1

    # ── Start listener ───────────────────────────────────────────────────
    listener = mouse.Listener(on_scroll=on_scroll)
    listener.start()

    print("  Scroll Wheel Tracker is running... (Ctrl+C to stop)\n")

    try:
        while running.is_set():
            with lock:
                render_display(session, alltime, session_start)
            time.sleep(DISPLAY_REFRESH_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        running.clear()
        listener.stop()

        # ── Save session data ────────────────────────────────────────────
        session_elapsed = time.time() - session_start
        now = datetime.now().isoformat()

        alltime["total_scroll_up"] += session["up"]
        alltime["total_scroll_down"] += session["down"]
        alltime["total_clicks"] += session["up"] + session["down"]
        alltime["total_sessions"] += 1
        alltime["total_time_seconds"] += session_elapsed
        if alltime["first_session"] is None:
            alltime["first_session"] = now
        alltime["last_session"] = now

        save_data(alltime)

        clear_screen()
        total = session["up"] + session["down"]
        print()
        print("  Session saved!")
        print(f"  You scrolled {total} times in {format_duration(session_elapsed)}.")
        print(f"  (Up: {session['up']}  Down: {session['down']})")
        print(f"\n  Data stored in: {DATA_FILE}")
        print()


if __name__ == "__main__":
    main()
