"""
Goblin Detector — scans for the purple shimmer of Treasure Goblins.
When spotted, publishes an event and briefly prioritizes the goblin location.
"""

from __future__ import annotations
import time

from core.state import BotState
from core.event_bus import EventBus, bus
from interface.image_recognizer import ImageRecognizer


class GoblinDetector:
    def __init__(self, state: BotState, recognizer: ImageRecognizer):
        self._state      = state
        self._recognizer = recognizer
        self._last_alert = 0.0
        self._alert_cooldown = 10.0   # don't spam alerts

    def tick(self):
        if not self._state.feat_goblin:
            return

        visible = self._recognizer.detect_goblin()
        self._state.goblin_visible = visible

        if visible:
            now = time.time()
            if now - self._last_alert > self._alert_cooldown:
                self._last_alert = now
                self._state.stats.goblins_spotted += 1
                bus.publish(EventBus.GOBLIN_DETECTED, self._state.stats.goblins_spotted)
