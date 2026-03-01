"""
Health Monitor — watches HP orb and fires bottomless potion when threshold crossed.
Respects the potion cooldown (D3 locks it for ~30s after use).
"""

from __future__ import annotations
import time

import config
from core.state import BotState
from core.event_bus import EventBus, bus
from io.image_recognizer import ImageRecognizer
from io.input_controller import InputController


class HealthMonitor:
    def __init__(
        self,
        state:       BotState,
        recognizer:  ImageRecognizer,
        controller:  InputController,
    ):
        self._state      = state
        self._recognizer = recognizer
        self._controller = controller
        self._last_check = 0.0

    def tick(self):
        """Called every main loop iteration; self-throttles via interval."""
        if not self._state.feat_health:
            return
        now = time.time()
        if now - self._last_check < config.HEALTH_CHECK_INTERVAL:
            return
        self._last_check = now

        pct = self._recognizer.detect_health_pct()
        if pct is None:
            return

        self._state.health_pct = pct
        bus.publish(EventBus.HEALTH_UPDATED, pct)

        if pct < config.HEALTH_THRESHOLD:
            bus.publish(EventBus.LOW_HEALTH, pct)
            self._maybe_use_potion()

    def _maybe_use_potion(self):
        now = time.time()
        if now - self._state.potion_last_used >= config.HEALTH_POTION_COOLDOWN:
            self._controller.use_potion()
            self._state.potion_last_used = now
            self._state.stats.potions_used += 1
            bus.publish(EventBus.POTION_USED, self._state.health_pct)
