"""
Anti-AFK — periodically sends micro inputs to prevent idle detection.
Interval is randomized with a wide window to avoid pattern detection.
"""

from __future__ import annotations
import time
import random

from core.state import BotState
from interface.input_controller import InputController
import config


class AntiAFK:
    def __init__(self, state: BotState, controller: InputController):
        self._state      = state
        self._controller = controller
        self._next_action = self._random_interval()

    def tick(self):
        if not self._state.feat_antiafk:
            return
        now = time.time()
        if now < self._next_action:
            return

        self._next_action = now + self._random_interval()
        self._do_action()

    def _do_action(self):
        # Tiny random mouse nudge — just enough to reset AFK timer
        cx = config.SCREEN_WIDTH  // 2
        cy = config.SCREEN_HEIGHT // 2
        dx = random.randint(-8, 8)
        dy = random.randint(-8, 8)
        self._controller.move_to(cx + dx, cy + dy)

    @staticmethod
    def _random_interval() -> float:
        return random.uniform(45.0, 90.0)
