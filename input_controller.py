"""
Input Controller — Linux-native input via pynput.
All actions inject random jitter and micro-delays for human-like timing.
"""

from __future__ import annotations
import time
import random
import subprocess
import math
from typing import Optional

import config

try:
    from pynput.mouse import Button, Controller as MouseController
    from pynput.keyboard import Key, Controller as KeyboardController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


def _jitter(value: int, amount: int = config.CLICK_JITTER_PX) -> int:
    return value + random.randint(-amount, amount)


def _micro_delay():
    time.sleep(random.uniform(config.RANDOM_DELAY_MIN, config.RANDOM_DELAY_MAX))


class InputController:
    """
    Thin, deterministic input layer.
    Callers specify intent (press_skill, click_loot); this class handles
    the human-like noise injection and fallback to xdotool on Wayland.
    """

    def __init__(self):
        self._mouse: Optional[MouseController]    = None
        self._kbd:   Optional[KeyboardController] = None
        self._use_xdotool = False

        if PYNPUT_AVAILABLE:
            try:
                self._mouse = MouseController()
                self._kbd   = KeyboardController()
            except Exception:
                self._use_xdotool = True
        else:
            self._use_xdotool = True

    # ── Key Actions ───────────────────────────────────────────────────────────

    def press_key(self, key: str, hold: float = 0.0):
        """Press and release a keyboard key."""
        _micro_delay()
        if self._use_xdotool:
            self._xdo_key(key)
            return
        try:
            self._kbd.press(key)
            if hold > 0:
                time.sleep(hold)
            self._kbd.release(key)
        except Exception:
            self._xdo_key(key)

    def use_potion(self):
        self.press_key(config.POTION_KEY)

    def press_skill(self, key: str):
        self.press_key(key)

    # ── Mouse Actions ─────────────────────────────────────────────────────────

    def move_to(self, x: int, y: int):
        jx, jy = _jitter(x), _jitter(y)
        _micro_delay()
        if self._use_xdotool:
            self._xdo_move(jx, jy)
            return
        try:
            # Smooth interpolation (8 steps)
            cx, cy = self._mouse.position
            steps  = 8
            for i in range(1, steps + 1):
                nx = int(cx + (jx - cx) * i / steps)
                ny = int(cy + (jy - cy) * i / steps)
                self._mouse.position = (nx, ny)
                time.sleep(0.005)
        except Exception:
            self._xdo_move(jx, jy)

    def left_click(self, x: Optional[int] = None, y: Optional[int] = None):
        if x is not None and y is not None:
            self.move_to(x, y)
        _micro_delay()
        if self._use_xdotool:
            if x and y:
                self._xdo_click(x, y)
            return
        try:
            self._mouse.press(Button.left)
            time.sleep(random.uniform(0.04, 0.09))
            self._mouse.release(Button.left)
        except Exception:
            if x and y:
                self._xdo_click(x, y)

    def right_click(self, x: int, y: int):
        self.move_to(x, y)
        _micro_delay()
        if self._use_xdotool:
            subprocess.run(["xdotool", "click", "3"], check=False)
            return
        try:
            self._mouse.press(Button.right)
            time.sleep(random.uniform(0.04, 0.09))
            self._mouse.release(Button.right)
        except Exception:
            pass

    # ── Composite Intents ─────────────────────────────────────────────────────

    def click_loot(self, x: int, y: int):
        """Click a loot item at screen position."""
        self.left_click(x, y)

    def emergency_stop(self):
        """Release all held inputs."""
        if self._mouse and PYNPUT_AVAILABLE:
            try:
                self._mouse.release(Button.left)
                self._mouse.release(Button.right)
            except Exception:
                pass

    # ── xdotool Fallback ─────────────────────────────────────────────────────

    def _xdo_key(self, key: str):
        try:
            subprocess.run(["xdotool", "key", key], check=False, timeout=1)
        except Exception:
            pass

    def _xdo_move(self, x: int, y: int):
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=False, timeout=1)
        except Exception:
            pass

    def _xdo_click(self, x: int, y: int):
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=False, timeout=1)
        except Exception:
            pass
