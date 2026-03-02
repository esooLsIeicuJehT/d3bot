"""
Skill Rotation — fires configured skills in cooldown order.
Each skill carries its own last-fired timestamp stored in BotState,
so the rotation survives pause/resume without state loss.
"""

from __future__ import annotations
import time
from typing import List, Tuple

import config
from core.state import BotState
from core.event_bus import EventBus, bus
from interface.input_controller import InputController


SkillDef = Tuple[str, float, str]   # (key, cooldown, label)


class SkillRotation:
    def __init__(
        self,
        state:      BotState,
        controller: InputController,
        skills:     List[SkillDef] = config.DEFAULT_SKILL_ROTATION,
    ):
        self._state      = state
        self._controller = controller
        self._skills     = skills
        self._cycle_idx  = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def tick(self, resource_available: bool = True):
        """Fire any skill whose cooldown has elapsed."""
        if not self._state.feat_skills:
            return
        if not resource_available:
            # Only allow primary (index 0, typically 0-cooldown) when low resource
            self._try_fire(0, force_primary=True)
            return

        fired_any = False
        for idx, (key, cd, label) in enumerate(self._skills):
            if self._is_ready(key, cd):
                self._fire(idx, key, label)
                fired_any = True

        if fired_any:
            self._cycle_idx += 1
            if self._cycle_idx % len(self._skills) == 0:
                self._state.stats.rotation_cycles += 1
                bus.publish(EventBus.ROTATION_CYCLE, self._state.stats.rotation_cycles)

    def update_skills(self, skills: List[SkillDef]):
        """Hot-swap skill list from GUI without restarting bot."""
        self._skills = skills

    def reset_cooldowns(self):
        self._state.last_skill_times.clear()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _is_ready(self, key: str, cooldown: float) -> bool:
        last = self._state.last_skill_times.get(key, 0.0)
        return time.time() - last >= cooldown

    def _fire(self, idx: int, key: str, label: str):
        self._controller.press_skill(key)
        self._state.last_skill_times[key] = time.time()
        self._state.stats.skills_fired += 1
        bus.publish(EventBus.SKILL_FIRED, {"key": key, "label": label, "idx": idx})

    def _try_fire(self, idx: int, force_primary: bool = False):
        if idx >= len(self._skills):
            return
        key, cd, label = self._skills[idx]
        if force_primary or self._is_ready(key, cd):
            self._fire(idx, key, label)
