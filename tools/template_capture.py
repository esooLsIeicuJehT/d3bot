"""
Template Capture Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: teaches region-of-interest selection for
template matching — the foundation of UI element detection.

How it works:
  1. Takes a screenshot.
  2. Lets you draw a rectangle over any UI element (death screen,
     accept button, rift guardian HP bar, etc.).
  3. Crops and saves the selection as a PNG to assets/templates/.
  4. The saved PNG is automatically picked up by ImageRecognizer._load_templates().

Mouse controls (in the OpenCV window):
  Left-drag  → draw selection rectangle
  Enter / S  → save selected crop as template
  R          → refresh screenshot
  Q / ESC    → quit

Usage:
    python tools/template_capture.py
    python tools/template_capture.py my_screenshot.png
"""

from __future__ import annotations
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cv2
    import numpy as np
except ImportError:
    print("OpenCV not found. Run:  pip install opencv-python")
    sys.exit(1)

from io.screen_capture import ScreenCapture

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "templates")
WIN = "Template Capture — Draw rectangle, then press S to save | R=refresh | Q=quit"


class TemplateCapturer:
    def __init__(self, frame: np.ndarray):
        self.frame      = frame.copy()
        self.display    = frame.copy()
        self._drawing   = False
        self._start     = (-1, -1)
        self._end       = (-1, -1)
        self._selection = None   # (x1, y1, x2, y2)

    def _on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._drawing = True
            self._start   = (x, y)
            self._end     = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE and self._drawing:
            self._end     = (x, y)
            self.display  = self.frame.copy()
            x1, y1 = self._start
            cv2.rectangle(self.display, (x1, y1), (x, y), (0, 200, 255), 2)
            cv2.putText(
                self.display,
                f"({abs(x-x1)} × {abs(y-y1)})",
                (min(x1,x) + 4, min(y1,y) - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA,
            )

        elif event == cv2.EVENT_LBUTTONUP:
            self._drawing = False
            self._end     = (x, y)
            x1, y1 = self._start
            x2, y2 = x, y
            self._selection = (
                min(x1, x2), min(y1, y2),
                max(x1, x2), max(y1, y2),
            )
            # Keep rectangle drawn on display
            cv2.rectangle(self.display,
                          (self._selection[0], self._selection[1]),
                          (self._selection[2], self._selection[3]),
                          (0, 255, 128), 2)
            print(f"  Selection: x={self._selection[0]}, y={self._selection[1]}, "
                  f"w={self._selection[2]-self._selection[0]}, "
                  f"h={self._selection[3]-self._selection[1]}")

    def get_crop(self) -> np.ndarray | None:
        if not self._selection:
            return None
        x1, y1, x2, y2 = self._selection
        if x2 - x1 < 2 or y2 - y1 < 2:
            return None
        return self.frame[y1:y2, x1:x2]

    def save_crop(self, name: str) -> str | None:
        crop = self.get_crop()
        if crop is None:
            print("No valid selection to save.")
            return None
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        # Sanitise name
        safe = "".join(c for c in name if c.isalnum() or c in "_-")
        if not safe:
            ts = datetime.datetime.now().strftime("%H%M%S")
            safe = f"template_{ts}"
        path = os.path.join(TEMPLATES_DIR, safe + ".png")
        cv2.imwrite(path, crop)
        print(f"  Template saved: {path}")
        print(f"  Size: {crop.shape[1]}×{crop.shape[0]} px")
        return path


def run(image_path: str | None = None):
    cap = ScreenCapture()

    def _grab() -> np.ndarray:
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            return img if img is not None else np.zeros((768, 1024, 3), dtype=np.uint8)
        frame = cap.capture()
        return frame if frame is not None else np.zeros((768, 1024, 3), dtype=np.uint8)

    frame = _grab()
    capturer = TemplateCapturer(frame)

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, min(frame.shape[1], 1280), min(frame.shape[0], 720))
    cv2.setMouseCallback(WIN, capturer._on_mouse)

    print("\nTemplate Capture Tool")
    print("  1. Draw a rectangle over the UI element you want to detect.")
    print("  2. Press S and type a name (e.g. 'death_screen', 'accept_btn').")
    print("  3. The PNG is saved to assets/templates/ and auto-loaded by the bot.\n")

    while True:
        cv2.imshow(WIN, capturer.display)
        key = cv2.waitKey(30) & 0xFF

        if key in (ord('q'), 27):
            break

        elif key == ord('r'):
            frame    = _grab()
            capturer = TemplateCapturer(frame)
            cv2.setMouseCallback(WIN, capturer._on_mouse)
            print("Screenshot refreshed.")

        elif key in (ord('s'), 13):  # S or Enter
            crop = capturer.get_crop()
            if crop is None:
                print("Draw a selection first.")
                continue
            # Show preview
            cv2.imshow("Preview — press any key to confirm or ESC to cancel", crop)
            k2 = cv2.waitKey(0) & 0xFF
            cv2.destroyWindow("Preview — press any key to confirm or ESC to cancel")
            if k2 == 27:
                print("Cancelled.")
                continue
            name = input("  Enter template name (no spaces, no extension): ").strip()
            capturer.save_crop(name)

    cv2.destroyAllWindows()
    print("\nSaved templates:")
    if os.path.isdir(TEMPLATES_DIR):
        for f in sorted(os.listdir(TEMPLATES_DIR)):
            if f.endswith(".png"):
                print(f"  assets/templates/{f}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
