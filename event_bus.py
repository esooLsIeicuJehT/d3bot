"""
Event Bus — Lightweight pub/sub that decouples features from the engine.
Features publish events; the engine and GUI subscribe to react.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Callable, Any
import threading


class EventBus:
    """Thread-safe publish/subscribe event bus."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event: str, callback: Callable):
        with self._lock:
            self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable):
        with self._lock:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb != callback
            ]

    def publish(self, event: str, data: Any = None):
        with self._lock:
            callbacks = list(self._subscribers.get(event, []))
        for cb in callbacks:
            try:
                cb(data)
            except Exception:
                pass  # Prevent one bad subscriber from killing the bus

    # ── Named events ──────────────────────────────────────────────────────────
    # Consumers import these strings directly instead of using magic literals.
    HEALTH_UPDATED       = "health.updated"
    RESOURCE_UPDATED     = "resource.updated"
    POTION_USED          = "health.potion_used"
    LOW_HEALTH           = "health.low"
    LOW_RESOURCE         = "resource.low"
    SKILL_FIRED          = "skill.fired"
    ROTATION_CYCLE       = "skill.rotation_cycle"
    LOOT_DETECTED        = "loot.detected"
    LOOT_COLLECTED       = "loot.collected"
    GOBLIN_DETECTED      = "goblin.detected"
    PLAYER_DIED          = "player.died"
    PLAYER_RESURRECTED   = "player.resurrected"
    BOT_STARTED          = "bot.started"
    BOT_STOPPED          = "bot.stopped"
    RUNTIME_LIMIT        = "bot.runtime_limit"
    STATUS_UPDATE        = "bot.status_update"
    FEATURE_TOGGLED      = "feature.toggled"


# Singleton used across the whole app
bus = EventBus()
