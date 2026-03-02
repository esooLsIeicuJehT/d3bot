"""
Resource Monitor — tracks primary resource (Mana/Fury/Wrath/etc.).
Pauses skill fire when critically low to allow natural regen.
"""

from __future__ import annotations
import time

import config
from core.state import BotState
from core.event_bus import EventBus, bus
from interface.image_recognizer import ImageRecognizer


class ResourceMonitor:
    def __init__(self, state: BotState, recognizer: ImageRecognizer):
        self._state      = state
        self._recognizer = recognizer
        self._last_check = 0.0

    def tick(self):
        if not self._state.feat_resource:
            return
        now = time.time()
        if now - self._last_check < config.RESOURCE_CHECK_INTERVAL:
            return
        self._last_check = now

        pct = self._recognizer.detect_resource_pct()
        if pct is None:
            return

        self._state.resource_pct = pct
        bus.publish(EventBus.RESOURCE_UPDATED, pct)

        if pct < config.RESOURCE_THRESHOLD:
            bus.publish(EventBus.LOW_RESOURCE, pct)

    @property
    def has_resource(self) -> bool:
        pct = self._state.resource_pct
        return pct is None or pct >= config.RESOURCE_THRESHOLD
