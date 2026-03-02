"""
Screen Capture — mss-based screen reader for Fedora/X11/Wayland.
Returns numpy arrays for downstream OpenCV processing.
"""

from __future__ import annotations
import numpy as np
from typing import Optional, Tuple
import datetime
import os

try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


Region = Tuple[int, int, int, int]  # x, y, w, h


class ScreenCapture:
    """
    Unified screen capture with mss primary, PIL fallback.
    All captures return BGR numpy arrays (OpenCV-ready).
    """

    def __init__(self):
        self._sct = None
        if MSS_AVAILABLE:
            self._sct = mss.mss()

    # ── Public API ────────────────────────────────────────────────────────────

    def capture(self, region: Optional[Region] = None) -> Optional[np.ndarray]:
        """Capture a region (x,y,w,h) or the full screen if None."""
        if MSS_AVAILABLE and self._sct:
            return self._capture_mss(region)
        elif PIL_AVAILABLE:
            return self._capture_pil(region)
        return None

    def save_screenshot(self, directory: str = os.path.expanduser("~/d3bot_screenshots")) -> str:
        frame = self.capture()
        if frame is None:
            return ""
        os.makedirs(directory, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(directory, f"d3bot_{ts}.png")
        try:
            import cv2
            cv2.imwrite(path, frame)
        except Exception:
            pass
        return path

    # ── Backends ─────────────────────────────────────────────────────────────

    def _capture_mss(self, region: Optional[Region]) -> Optional[np.ndarray]:
        try:
            import cv2
            if region:
                x, y, w, h = region
                mon = {"left": x, "top": y, "width": w, "height": h}
            else:
                mon = self._sct.monitors[1]  # primary monitor
            img = self._sct.grab(mon)
            arr = np.array(img)          # BGRA
            return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        except Exception:
            return None

    def _capture_pil(self, region: Optional[Region]) -> Optional[np.ndarray]:
        try:
            import cv2
            if region:
                x, y, w, h = region
                shot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            else:
                shot = ImageGrab.grab()
            arr = np.array(shot.convert("RGB"))
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception:
            return None

    def __del__(self):
        if self._sct:
            try:
                self._sct.close()
            except Exception:
                pass
