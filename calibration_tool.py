"""
HSV Calibration Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: teaches how HSV color masking works.
Lets you visually tune the HEALTH_COLOR_*, RESOURCE_COLOR_*,
GOBLIN_COLOR_* and LOOT_COLOR_* values in config.py by dragging
sliders and seeing the mask update live.

How it works:
  1. Takes a screenshot (or loads a PNG you supply).
  2. Converts to HSV.
  3. Applies cv2.inRange(hsv, low, high) in real time.
  4. Shows: original | HSV | mask | masked result — 4 panels.
  5. When happy, press S to print the config lines to stdout.

Usage:
    python tools/calibration_tool.py                  # live screenshot
    python tools/calibration_tool.py screenshot.png   # from file
"""

import sys
import os

# Project root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cv2
    import numpy as np
except ImportError:
    print("OpenCV not found. Run:  pip install opencv-python")
    sys.exit(1)

from io.screen_capture import ScreenCapture


# ── Slider state ─────────────────────────────────────────────────────────────
_sliders = {
    "H_low":  0,   "H_high": 179,
    "S_low":  0,   "S_high": 255,
    "V_low":  0,   "V_high": 255,
}
WIN = "D3 Bot — HSV Calibrator  |  S=save  Q=quit  R=new screenshot"


def _on_change(name):
    def _cb(val):
        _sliders[name] = val
    return _cb


def _build_panel(bgr: np.ndarray) -> np.ndarray:
    """Build the 4-panel display: original | hsv | mask | result."""
    low  = np.array([_sliders["H_low"],  _sliders["S_low"],  _sliders["V_low"]],  dtype=np.uint8)
    high = np.array([_sliders["H_high"], _sliders["S_high"], _sliders["V_high"]], dtype=np.uint8)

    hsv    = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask   = cv2.inRange(hsv, low, high)
    result = cv2.bitwise_and(bgr, bgr, mask=mask)
    hsv_vis = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)   # show HSV as colour for intuition

    # Resize all to same height for side-by-side display
    h = 300
    def _resize(img):
        ratio = h / img.shape[0]
        return cv2.resize(img, (int(img.shape[1] * ratio), h))

    # Annotate panels
    panels = []
    for img, title in [
        (bgr,    "Original"),
        (hsv_vis,"HSV View"),
        (cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), "Mask"),
        (result, "Masked Result"),
    ]:
        r = _resize(img)
        cv2.putText(r, title, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 1, cv2.LINE_AA)
        panels.append(r)

    row = np.hstack(panels)

    # Overlay: pixel count and HSV range text
    filled = int(np.count_nonzero(mask))
    total  = mask.size
    info = (f"Filled: {filled}/{total} ({filled/total*100:.1f}%)   "
            f"HSV_low=({_sliders['H_low']},{_sliders['S_low']},{_sliders['V_low']})  "
            f"HSV_high=({_sliders['H_high']},{_sliders['S_high']},{_sliders['V_high']})")
    cv2.putText(row, info, (8, row.shape[0] - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1, cv2.LINE_AA)
    return row


def _print_config():
    print("\n── Copy these lines into config.py ──────────────────────────────")
    print(f"COLOR_LOW  = ({_sliders['H_low']}, {_sliders['S_low']}, {_sliders['V_low']})")
    print(f"COLOR_HIGH = ({_sliders['H_high']}, {_sliders['S_high']}, {_sliders['V_high']})")
    print("─────────────────────────────────────────────────────────────────\n")


def run(image_path: str | None = None):
    cap = ScreenCapture()

    def _grab() -> np.ndarray:
        if image_path and os.path.exists(image_path):
            return cv2.imread(image_path)
        frame = cap.capture()
        if frame is None:
            print("Screen capture failed — creating blank test image")
            return np.zeros((600, 800, 3), dtype=np.uint8)
        return frame

    frame = _grab()

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, 1280, 600)

    # Create sliders
    for name, val in _sliders.items():
        mx = 179 if "H" in name else 255
        cv2.createTrackbar(name, WIN, val, mx, _on_change(name))

    print(f"\nCalibration tool running.")
    print(f"  Drag sliders to isolate the colour you want to detect.")
    print(f"  S = print config values   R = new screenshot   Q = quit\n")

    while True:
        panel = _build_panel(frame)
        cv2.imshow(WIN, panel)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            _print_config()
        elif key == ord('r'):
            frame = _grab()
            print("Screenshot refreshed.")

    cv2.destroyAllWindows()
    print("Calibration tool closed.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    run(path)
