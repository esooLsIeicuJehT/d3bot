"""
Performance Profiler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: teaches loop-timing analysis and bottleneck detection.

Wraps each feature's tick() with a timing decorator, accumulates samples,
and produces a profiling report showing:
  • Mean / min / max tick duration per feature
  • % of total loop time consumed by each feature
  • Samples that exceeded a configurable jitter threshold (spikes)
  • Rolling average to spot degradation over time

How to integrate:
    # In core/bot_engine.py, replace direct feature construction with:
    from tools.profiler import Profiler
    prof = Profiler()
    self._health = prof.wrap("HealthMonitor", HealthMonitor(...))
    # Then in _tick():
    prof.report()   # prints every N samples

Or run standalone after a session to analyse a saved .jsonl log.
"""

from __future__ import annotations
import time
import statistics
import threading
from collections import defaultdict, deque
from typing import Any


SPIKE_THRESHOLD_MS = 50.0    # Flag ticks longer than this
REPORT_EVERY_N     = 500     # Print report every N combined ticks
HISTORY_WINDOW     = 200     # Rolling average window (samples)


class FeatureStats:
    """Accumulates timing samples for a single feature."""

    def __init__(self, name: str):
        self.name    = name
        self._lock   = threading.Lock()
        self._samples: list[float] = []
        self._rolling: deque[float] = deque(maxlen=HISTORY_WINDOW)
        self._spikes: list[float] = []
        self._call_count = 0

    def record(self, duration_ms: float):
        with self._lock:
            self._samples.append(duration_ms)
            self._rolling.append(duration_ms)
            self._call_count += 1
            if duration_ms > SPIKE_THRESHOLD_MS:
                self._spikes.append(duration_ms)

    @property
    def count(self) -> int:
        with self._lock:
            return self._call_count

    def stats(self) -> dict:
        with self._lock:
            if not self._samples:
                return {"name": self.name, "count": 0}
            return {
                "name":        self.name,
                "count":       self._call_count,
                "mean_ms":     round(statistics.mean(self._samples),    3),
                "median_ms":   round(statistics.median(self._samples),  3),
                "min_ms":      round(min(self._samples),                3),
                "max_ms":      round(max(self._samples),                3),
                "stdev_ms":    round(statistics.stdev(self._samples) if len(self._samples) > 1 else 0.0, 3),
                "rolling_avg": round(statistics.mean(self._rolling),    3) if self._rolling else 0.0,
                "spikes":      len(self._spikes),
                "total_ms":    round(sum(self._samples),                2),
            }


class Profiler:
    """
    Wraps feature objects to time their tick() methods transparently.
    Features don't need to know they're being profiled.
    """

    def __init__(self):
        self._features: dict[str, FeatureStats] = {}
        self._tick_count = 0
        self._lock = threading.Lock()

    def wrap(self, name: str, feature: Any) -> Any:
        """
        Returns a proxy object whose tick() is timed.
        All other attributes/methods are passed through unchanged.
        """
        stats = FeatureStats(name)
        with self._lock:
            self._features[name] = stats
        return _TimedProxy(feature, stats)

    def tick(self):
        """Call once per engine loop to track overall tick count."""
        with self._lock:
            self._tick_count += 1
            if self._tick_count % REPORT_EVERY_N == 0:
                self.print_report()

    def report(self) -> list[dict]:
        with self._lock:
            return [f.stats() for f in self._features.values()]

    def print_report(self):
        rows = self.report()
        if not rows or not rows[0].get("count"):
            return

        total_ms = sum(r.get("total_ms", 0) for r in rows)

        print("\n" + "─" * 70)
        print(f"  Performance Report  (tick #{self._tick_count})")
        print("─" * 70)
        print(f"  {'Feature':<22} {'Calls':>6} {'Mean':>8} {'Max':>8} {'Spikes':>7} {'%Total':>7}")
        print("─" * 70)

        for r in sorted(rows, key=lambda x: -x.get("total_ms", 0)):
            if not r.get("count"):
                continue
            pct = (r["total_ms"] / total_ms * 100) if total_ms > 0 else 0
            spike_flag = " ⚠" if r.get("spikes", 0) > 0 else ""
            print(
                f"  {r['name']:<22} {r['count']:>6} "
                f"{r['mean_ms']:>6.2f}ms {r['max_ms']:>6.2f}ms "
                f"{r['spikes']:>6}{spike_flag:2}  {pct:>5.1f}%"
            )

        print("─" * 70)
        print(f"  Total measured CPU time: {total_ms:.1f} ms across {self._tick_count} loops")
        print(f"  Spike threshold: >{SPIKE_THRESHOLD_MS:.0f}ms   Rolling window: {HISTORY_WINDOW} samples")
        print("─" * 70 + "\n")

    def export_json(self, path: str):
        import json
        with open(path, "w") as f:
            json.dump({"ticks": self._tick_count, "features": self.report()}, f, indent=2)
        print(f"Profiler data exported: {path}")


class _TimedProxy:
    """
    Transparent proxy — delegates everything to the wrapped object.
    Only tick() is intercepted for timing.
    """

    def __init__(self, target: Any, stats: FeatureStats):
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_stats",  stats)

    def tick(self, *args, **kwargs):
        t0  = time.perf_counter()
        ret = object.__getattribute__(self, "_target").tick(*args, **kwargs)
        ms  = (time.perf_counter() - t0) * 1000.0
        object.__getattribute__(self, "_stats").record(ms)
        return ret

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_target"), name)

    def __setattr__(self, name: str, value: Any):
        setattr(object.__getattribute__(self, "_target"), name, value)
