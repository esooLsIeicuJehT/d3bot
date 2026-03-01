"""
Image Recognizer — OpenCV pipeline for detecting game state from frames.
All detectors receive a BGR numpy array and return typed results.
"""

from __future__ import annotations
import numpy as np
from typing import Optional, List, Tuple
import os

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

import config
from io.screen_capture import ScreenCapture, Region


LootHit = Tuple[int, int, str]   # (x, y, tier_name)


class ImageRecognizer:
    """
    Stateless detector hub.  Each method:
      1. Grabs a specific region of the screen.
      2. Runs a focused CV pipeline.
      3. Returns a typed result (never raw frames).
    """

    def __init__(self, capture: ScreenCapture):
        self._cap = capture
        self._templates: dict[str, np.ndarray] = {}
        self._load_templates()

    # ── Orb Detectors ────────────────────────────────────────────────────────

    def detect_health_pct(self) -> Optional[float]:
        """Returns [0.0, 1.0] health fill or None on failure."""
        return self._detect_orb_fill(
            config.HEALTH_BAR_REGION,
            config.HEALTH_COLOR_LOW,
            config.HEALTH_COLOR_HIGH,
        )

    def detect_resource_pct(self) -> Optional[float]:
        """Returns [0.0, 1.0] resource fill or None on failure."""
        return self._detect_orb_fill(
            config.RESOURCE_BAR_REGION,
            config.RESOURCE_COLOR_LOW,
            config.RESOURCE_COLOR_HIGH,
        )

    def _detect_orb_fill(
        self,
        region: Region,
        hsv_low: tuple,
        hsv_high: tuple,
    ) -> Optional[float]:
        if not CV2_AVAILABLE:
            return None
        frame = self._cap.capture(region)
        if frame is None:
            return None
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            low  = np.array(hsv_low,  dtype=np.uint8)
            high = np.array(hsv_high, dtype=np.uint8)
            mask = cv2.inRange(hsv, low, high)
            filled_px = cv2.countNonZero(mask)
            total_px  = frame.shape[0] * frame.shape[1]
            return float(filled_px) / float(total_px) if total_px > 0 else 0.0
        except Exception:
            return None

    # ── Death Detection ───────────────────────────────────────────────────────

    def detect_death_screen(self) -> bool:
        """True if the death overlay is showing."""
        if not CV2_AVAILABLE:
            return False
        frame = self._cap.capture(config.DEATH_REGION)
        if frame is None:
            return False
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return float(gray.mean()) < config.DEATH_DARK_THRESHOLD
        except Exception:
            return False

    # ── Loot Detector ────────────────────────────────────────────────────────

    def detect_loot_items(self) -> List[LootHit]:
        """
        Scans a region around the character center for colored loot beams.
        Returns a list of (screen_x, screen_y, tier) sorted by priority.
        """
        if not CV2_AVAILABLE:
            return []

        cx = config.SCREEN_WIDTH  // 2
        cy = config.SCREEN_HEIGHT // 2
        r  = config.LOOT_RADIUS_PX

        region = (cx - r, cy - r, r * 2, r * 2)
        frame  = self._cap.capture(region)
        if frame is None:
            return []

        hits: List[LootHit] = []
        priority_order = config.LOOT_PRIORITIES

        for tier in priority_order:
            if tier not in config.LOOT_COLORS:
                continue
            bgr   = config.LOOT_COLORS[tier]
            tol   = config.LOOT_COLOR_TOLERANCE
            lower = np.array([max(0, c - tol) for c in bgr], dtype=np.uint8)
            upper = np.array([min(255, c + tol) for c in bgr], dtype=np.uint8)
            mask  = cv2.inRange(frame, lower, upper)

            # Find connected blobs → click center of each
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) < 10:
                    continue
                M = cv2.moments(cnt)
                if M["m00"] == 0:
                    continue
                lx = int(M["m10"] / M["m00"]) + (cx - r)
                ly = int(M["m01"] / M["m00"]) + (cy - r)
                hits.append((lx, ly, tier))

        return hits

    # ── Goblin Detector ───────────────────────────────────────────────────────

    def detect_goblin(self) -> bool:
        """True when a treasure goblin's shimmer is visible on screen."""
        if not CV2_AVAILABLE:
            return False
        frame = self._cap.capture()   # full screen scan
        if frame is None:
            return False
        try:
            hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            low  = np.array(config.GOBLIN_COLOR_LOW,  dtype=np.uint8)
            high = np.array(config.GOBLIN_COLOR_HIGH, dtype=np.uint8)
            mask = cv2.inRange(hsv, low, high)
            return int(cv2.countNonZero(mask)) >= config.GOBLIN_MIN_PIXELS
        except Exception:
            return False

    # ── Template Matching ─────────────────────────────────────────────────────

    def match_template(self, template_name: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Search for a named template on screen.
        Returns (x, y) of best match center or None.
        """
        if not CV2_AVAILABLE:
            return None
        tmpl = self._templates.get(template_name)
        if tmpl is None:
            return None
        frame = self._cap.capture()
        if frame is None:
            return None
        try:
            res = cv2.matchTemplate(frame, tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val >= threshold:
                th, tw = tmpl.shape[:2]
                cx = max_loc[0] + tw // 2
                cy = max_loc[1] + th // 2
                return (cx, cy)
        except Exception:
            pass
        return None

    def _load_templates(self):
        """Load PNG templates from assets/templates/ if they exist."""
        if not CV2_AVAILABLE:
            return
        tmpl_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "templates")
        if not os.path.isdir(tmpl_dir):
            return
        for fname in os.listdir(tmpl_dir):
            if fname.lower().endswith(".png"):
                path = os.path.join(tmpl_dir, fname)
                img  = cv2.imread(path)
                if img is not None:
                    name = os.path.splitext(fname)[0]
                    self._templates[name] = img
