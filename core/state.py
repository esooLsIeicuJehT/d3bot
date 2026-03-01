"""
Bot State — Single shared state object that flows through the entire Context.
All features read from and write to this state; nothing is duplicated.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import time
import threading


class BotPhase(Enum):
    IDLE         = auto()
    RUNNING      = auto()
    PAUSED       = auto()
    DEAD         = auto()
    RESURRECTING = auto()
    STOPPING     = auto()


@dataclass
class SessionStats:
    start_time:       float = field(default_factory=time.time)
    loops:            int   = 0
    potions_used:     int   = 0
    skills_fired:     int   = 0
    items_looted:     int   = 0
    goblins_spotted:  int   = 0
    deaths:           int   = 0
    rotation_cycles:  int   = 0

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def elapsed_str(self) -> str:
        s = int(self.elapsed())
        h, m, sec = s // 3600, (s % 3600) // 60, s % 60
        return f"{h:02d}:{m:02d}:{sec:02d}"


class BotState:
    """
    Central context object — passed by reference into every feature.
    Features mutate it; the engine reads it to orchestrate.
    """

    def __init__(self):
        self._lock = threading.RLock()

        self.phase:              BotPhase        = BotPhase.IDLE
        self.health_pct:         Optional[float] = None
        self.resource_pct:       Optional[float] = None
        self.potion_last_used:   float           = 0.0
        self.last_skill_times:   dict            = {}   # key → timestamp
        self.loot_items_visible: list            = []   # list of (x,y,tier)
        self.goblin_visible:     bool            = False
        self.stats:              SessionStats    = SessionStats()

        # Feature enable flags — GUI writes these, features read them
        self.feat_health:        bool = True
        self.feat_resource:      bool = True
        self.feat_skills:        bool = True
        self.feat_loot:          bool = True
        self.feat_death:         bool = True
        self.feat_goblin:        bool = True
        self.feat_antiafk:       bool = True

    # ── Thread-safe property helpers ─────────────────────────────────────────
    def set_phase(self, phase: BotPhase):
        with self._lock:
            self.phase = phase

    def get_phase(self) -> BotPhase:
        with self._lock:
            return self.phase

    def is_running(self) -> bool:
        with self._lock:
            return self.phase in (BotPhase.RUNNING, BotPhase.DEAD, BotPhase.RESURRECTING)

    def snapshot(self) -> dict:
        """Return a dict safe to read from the GUI thread."""
        with self._lock:
            return {
                "phase":       self.phase.name,
                "health_pct":  self.health_pct,
                "resource_pct":self.resource_pct,
                "stats":       {
                    "elapsed":        self.stats.elapsed_str(),
                    "loops":          self.stats.loops,
                    "potions_used":   self.stats.potions_used,
                    "skills_fired":   self.stats.skills_fired,
                    "items_looted":   self.stats.items_looted,
                    "goblins_spotted":self.stats.goblins_spotted,
                    "deaths":         self.stats.deaths,
                    "rotation_cycles":self.stats.rotation_cycles,
                },
                "features": {
                    "health":   self.feat_health,
                    "resource": self.feat_resource,
                    "skills":   self.feat_skills,
                    "loot":     self.feat_loot,
                    "death":    self.feat_death,
                    "goblin":   self.feat_goblin,
                    "antiafk":  self.feat_antiafk,
                },
            }
