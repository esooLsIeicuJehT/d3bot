"""
Dry Run Controller
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A drop-in replacement for InputController that logs every intended action
to the EventBus (and optionally a file) instead of actually pressing keys
or moving the mouse.

Educational purpose:
  • Safely test the full detection + decision pipeline without touching the game.
  • Verify skill rotation timing, loot detection priority, and potion cadence
    by watching the dry-run log — before committing to live input.

Usage — in main.py _on_start(), check the dry-run toggle:
    if self._dry_run.get():
        engine = BotEngine(state, input_override=DryRunController())
    else:
        engine = BotEngine(state)

BotEngine.__init__ accepts an optional input_override parameter.
"""

from __future__ import annotations
import time
import logging
from typing import Optional

from core.event_bus import bus, EventBus

log = logging.getLogger("d3bot.dryrun")

# We publish a dedicated event so the GUI log can colour-code dry-run lines
DRYRUN_EVENT = "dryrun.action"


class DryRunController:
    """
    Mimics InputController's public interface exactly.
    All methods log their intended action instead of executing it.
    """

    def __init__(self):
        self._action_count = 0
        log.info("[DRY RUN] Input controller active — no real inputs will be sent.")

    # ── Key actions ───────────────────────────────────────────────────────────

    def press_key(self, key: str, hold: float = 0.0):
        self._act(f"KEYPRESS  key={key!r}  hold={hold:.2f}s")

    def use_potion(self):
        self._act("POTION    (bottomless potion key)")

    def press_skill(self, key: str):
        self._act(f"SKILL     key={key!r}")

    # ── Mouse actions ─────────────────────────────────────────────────────────

    def move_to(self, x: int, y: int):
        self._act(f"MOVE      ({x}, {y})")

    def left_click(self, x: Optional[int] = None, y: Optional[int] = None):
        if x is not None:
            self._act(f"L_CLICK   ({x}, {y})")
        else:
            self._act("L_CLICK   (current position)")

    def right_click(self, x: int, y: int):
        self._act(f"R_CLICK   ({x}, {y})")

    # ── Composite intents ─────────────────────────────────────────────────────

    def click_loot(self, x: int, y: int):
        self._act(f"LOOT      click at ({x}, {y})")

    def emergency_stop(self):
        self._act("EMERGENCY STOP")

    # ── Internal ─────────────────────────────────────────────────────────────

    def _act(self, description: str):
        self._action_count += 1
        ts  = time.strftime("%H:%M:%S")
        msg = f"[DRY RUN #{self._action_count:04d}] {ts}  {description}"
        log.info(msg)
        bus.publish(DRYRUN_EVENT, description)
