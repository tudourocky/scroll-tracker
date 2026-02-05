# scroll-tracker

A small Python app that tracks your mouse scroll wheel activity in real-time.

## Features

- **Live dashboard** — see scroll-up, scroll-down, total clicks, scrolls/min, and a direction bar updated in real time
- **Session stats** — stats for the current tracking session
- **All-time stats** — cumulative stats that persist across sessions in a local JSON file
- **Graceful exit** — press `Ctrl+C` to stop; your session is automatically saved

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scroll_tracker.py
```

Scroll your mouse wheel and watch the dashboard update. Press **Ctrl+C** to stop — your session will be saved to `scroll_data.json` and merged into all-time totals.

## How it works

The tracker uses the [pynput](https://pypi.org/project/pynput/) library to listen for mouse scroll events in the background. A live terminal UI refreshes every 250 ms showing your current and cumulative statistics.
