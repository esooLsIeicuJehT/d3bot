"""
Event Replay Logger
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: structured event recording and replay analysis.
Teaches: event sourcing patterns, time-series analysis, JSON I/O.

What it does:
  • Subscribes to every EventBus event.
  • Writes a timestamped JSON-lines file (one event per line).
  • On load, can replay the log to reconstruct session statistics,
    plot event frequency, or debug timing issues.

Output format (JSON Lines):
  {"t": 1712345678.23, "event": "health.updated", "data": 0.72}
  {"t": 1712345679.01, "event": "skill.fired", "data": {"key": "1", ...}}

Usage:
    # In main.py / BotEngine startup:
    from tools.event_replay_logger import EventReplayLogger
    replay_log = EventReplayLogger()
    replay_log.start()          # begins recording
    ...
    replay_log.stop()           # flushes and closes

    # Post-session analysis:
    python tools/event_replay_logger.py session_20240415_143022.jsonl
"""

from __future__ import annotations
import json
import os
import sys
import time
import threading
import queue
import datetime
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.event_bus import EventBus, bus

# All events we subscribe to
ALL_EVENTS = [
    EventBus.HEALTH_UPDATED, EventBus.RESOURCE_UPDATED,
    EventBus.POTION_USED, EventBus.LOW_HEALTH, EventBus.LOW_RESOURCE,
    EventBus.SKILL_FIRED, EventBus.ROTATION_CYCLE,
    EventBus.LOOT_DETECTED, EventBus.LOOT_COLLECTED,
    EventBus.GOBLIN_DETECTED, EventBus.PLAYER_DIED, EventBus.PLAYER_RESURRECTED,
    EventBus.BOT_STARTED, EventBus.BOT_STOPPED, EventBus.FEATURE_TOGGLED,
    EventBus.STATUS_UPDATE, EventBus.RUNTIME_LIMIT,
]

LOG_DIR = os.path.expanduser("~/d3bot_sessions")


class EventReplayLogger:
    """
    Asynchronous event logger — writes to disk from a background thread
    so the main loop is never blocked by file I/O.
    """

    def __init__(self, log_dir: str = LOG_DIR):
        os.makedirs(log_dir, exist_ok=True)
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path  = os.path.join(log_dir, f"session_{ts}.jsonl")
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._writer, daemon=True, name="EventLogger")
        self._thread.start()
        for event in ALL_EVENTS:
            bus.subscribe(event, self._make_handler(event))
        print(f"[EventLogger] Recording → {self._path}")

    def stop(self):
        self._running = False
        self._queue.put(None)   # sentinel
        if self._thread:
            self._thread.join(timeout=3)
        print(f"[EventLogger] Session saved: {self._path}")

    # ── Internals ─────────────────────────────────────────────────────────────

    def _make_handler(self, event_name: str):
        def _handler(data: Any):
            self._queue.put({"t": time.time(), "event": event_name, "data": self._serialise(data)})
        return _handler

    @staticmethod
    def _serialise(data: Any) -> Any:
        if data is None or isinstance(data, (bool, int, float, str)):
            return data
        if isinstance(data, dict):
            return {k: EventReplayLogger._serialise(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [EventReplayLogger._serialise(v) for v in data]
        return str(data)

    def _writer(self):
        with open(self._path, "w") as f:
            while self._running:
                try:
                    item = self._queue.get(timeout=0.5)
                    if item is None:
                        break
                    f.write(json.dumps(item) + "\n")
                    f.flush()
                except queue.Empty:
                    continue


# ── Post-session Analysis ─────────────────────────────────────────────────────

class SessionAnalyser:
    """
    Loads a .jsonl session log and produces a statistical summary.
    Educational: demonstrates time-series grouping and frequency analysis.
    """

    def __init__(self, path: str):
        self.path   = path
        self.events = self._load(path)

    @staticmethod
    def _load(path: str) -> list[dict]:
        records = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def summary(self) -> dict:
        if not self.events:
            return {}

        start = self.events[0]["t"]
        end   = self.events[-1]["t"]
        dur   = end - start

        counts: dict[str, int] = {}
        for ev in self.events:
            counts[ev["event"]] = counts.get(ev["event"], 0) + 1

        potions = counts.get(EventBus.POTION_USED, 0)
        skills  = counts.get(EventBus.SKILL_FIRED, 0)
        loot    = counts.get(EventBus.LOOT_COLLECTED, 0)
        deaths  = counts.get(EventBus.PLAYER_DIED, 0)

        per_hour = lambda n: round(n / dur * 3600, 1) if dur > 0 else 0

        return {
            "session_path":     self.path,
            "duration_seconds": round(dur, 1),
            "duration_human":   _fmt_seconds(int(dur)),
            "total_events":     len(self.events),
            "event_counts":     counts,
            "rates_per_hour": {
                "potions": per_hour(potions),
                "skills":  per_hour(skills),
                "loot":    per_hour(loot),
                "deaths":  per_hour(deaths),
            },
        }

    def print_summary(self):
        s = self.summary()
        if not s:
            print("No events found.")
            return

        print("\n" + "═" * 52)
        print(f"  Session Analysis — {os.path.basename(self.path)}")
        print("═" * 52)
        print(f"  Duration       : {s['duration_human']}")
        print(f"  Total events   : {s['total_events']}")
        print()
        print("  Event Counts:")
        for ev, cnt in sorted(s["event_counts"].items(), key=lambda x: -x[1]):
            print(f"    {ev:<35} {cnt:>5}")
        print()
        print("  Rates (per hour):")
        for k, v in s["rates_per_hour"].items():
            print(f"    {k:<15} {v:>8.1f}")
        print("═" * 52 + "\n")

    def event_timeline(self, event_name: str) -> list[float]:
        """Return list of relative timestamps (seconds from session start) for one event."""
        if not self.events:
            return []
        t0 = self.events[0]["t"]
        return [e["t"] - t0 for e in self.events if e["event"] == event_name]

    def export_csv(self, path: str):
        """Export all events to CSV for analysis in LibreOffice / pandas."""
        import csv
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "relative_s", "event", "data"])
            t0 = self.events[0]["t"] if self.events else 0
            for ev in self.events:
                w.writerow([
                    ev["t"],
                    round(ev["t"] - t0, 3),
                    ev["event"],
                    json.dumps(ev.get("data")),
                ])
        print(f"CSV exported: {path}")


def _fmt_seconds(s: int) -> str:
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}h {m:02d}m {sec:02d}s"


# ── CLI Entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # List available sessions
        sessions = sorted([
            f for f in os.listdir(LOG_DIR) if f.endswith(".jsonl")
        ]) if os.path.isdir(LOG_DIR) else []

        if not sessions:
            print(f"No sessions found in {LOG_DIR}")
            print("Usage: python tools/event_replay_logger.py session_*.jsonl")
            sys.exit(0)

        print(f"\nAvailable sessions in {LOG_DIR}:")
        for s in sessions:
            print(f"  {s}")
        print(f"\nUsage: python tools/event_replay_logger.py {sessions[-1]}")
        sys.exit(0)

    path = sys.argv[1]
    if not os.path.exists(path):
        path = os.path.join(LOG_DIR, sys.argv[1])

    analyser = SessionAnalyser(path)
    analyser.print_summary()

    if "--csv" in sys.argv:
        csv_path = path.replace(".jsonl", ".csv")
        analyser.export_csv(csv_path)
