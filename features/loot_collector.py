"""
Loot Collector — detects dropped items by beam color and clicks them.
Priority order is configurable in config.LOOT_PRIORITIES.
"""

from __future__ import annotations
import time

import config
from core.state import BotState
from core.event_bus import EventBus, bus
from io.image_recognizer import ImageRecognizer
from io.input_controller import InputController


class LootCollector:
    def __init__(
        self,
        state:      BotState,
        recognizer: ImageRecognizer,
        controller: InputController,
    ):
        self._state      = state
        self._recognizer = recognizer
        self._controller = controller
        self._last_scan  = 0.0

    def tick(self):
        if not self._state.feat_loot:
            return
        now = time.time()
        if now - self._last_scan < config.LOOT_SCAN_INTERVAL:
            return
        self._last_scan = now

        items = self._recognizer.detect_loot_items()
        self._state.loot_items_visible = items

        if items:
            bus.publish(EventBus.LOOT_DETECTED, items)
            self._collect(items)

    def _collect(self, items):
        for x, y, tier in items:
            if tier not in config.LOOT_PRIORITIES:
                continue
            self._controller.click_loot(x, y)
            self._state.stats.items_looted += 1
            bus.publish(EventBus.LOOT_COLLECTED, {"x": x, "y": y, "tier": tier})
            time.sleep(0.15)   # brief pause between pickups
