"""
Death Handler — detects the death screen and triggers resurrection flow.
On detection: pauses skill/loot features, waits, then presses Resurrect.
"""

from __future__ import annotations
import time

import config
from core.state import BotState, BotPhase
from core.event_bus import EventBus, bus
from interface.image_recognizer import ImageRecognizer
from interface.input_controller import InputController


class DeathHandler:
    def __init__(
        self,
        state:      BotState,
        recognizer: ImageRecognizer,
        controller: InputController,
    ):
        self._state      = state
        self._recognizer = recognizer
        self._controller = controller
        self._res_sent   = False

    def tick(self):
        if not self._state.feat_death:
            return

        dead = self._recognizer.detect_death_screen()

        if dead and self._state.get_phase() == BotPhase.RUNNING:
            self._on_death()
        elif not dead and self._state.get_phase() == BotPhase.RESURRECTING:
            self._on_resurrected()

    def _on_death(self):
        self._state.set_phase(BotPhase.DEAD)
        self._state.stats.deaths += 1
        self._res_sent = False
        bus.publish(EventBus.PLAYER_DIED, self._state.stats.deaths)

        time.sleep(config.RESURRECTION_DELAY)
        self._state.set_phase(BotPhase.RESURRECTING)

        # Press the accept/resurrect button (Enter or click center)
        self._controller.press_key(config.RESURRECT_KEY)
        self._res_sent = True

    def _on_resurrected(self):
        self._state.set_phase(BotPhase.RUNNING)
        bus.publish(EventBus.PLAYER_RESURRECTED)
        time.sleep(1.5)  # brief grace period before re-engaging
