"""
Detection Visualizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: makes the CV pipeline *visible*.
Opens an OpenCV window showing a live annotated view of:
  • Health bar region + detected fill %
  • Resource bar region + detected fill %
  • Loot scan radius + detected item blobs (coloured by tier)
  • Goblin detection pixel count
  • Minimap region outline

This is the single most useful debugging tool when tuning
config.py detection parameters — you can see exactly what
the bot "sees" before you let it act.

Usage:
    python tools/detection_visualizer.py
    Press Q to quit, S to save a frame, SPACE to pause.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cv2
    import numpy as np
except ImportError:
    print("OpenCV not found. Run:  pip install opencv-python")
    sys.exit(1)

import config
from io.screen_capture import ScreenCapture
from io.image_recognizer import ImageRecognizer


WIN = "D3 Bot — Detection Visualizer   Q=quit  S=save  SPACE=pause"

# Overlay colours (BGR)
COL_HEALTH   = (60,  200, 60)
COL_RESOURCE = (220, 140, 40)
COL_LOOT     = {"legendary": (0, 128, 255), "set": (0, 255, 0),
                "rare": (0, 255, 255), "magic": (255, 80, 80)}
COL_GOBLIN   = (220, 50, 220)
COL_REGION   = (80,  80, 80)
COL_TEXT     = (230, 230, 230)


def _draw_region_box(frame, region, color, label):
    x, y, w, h = region
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)
    cv2.putText(frame, label, (x + 2, y - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)


def _draw_fill_bar(frame, region, pct, color, label):
    x, y, w, h = region
    # Border
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)
    # Fill
    if pct is not None:
        fw = int(w * pct)
        cv2.rectangle(frame, (x, y), (x + fw, y + h), color, -1)
    # Text overlay
    text = f"{label}: {pct*100:.1f}%" if pct is not None else f"{label}: N/A"
    cv2.putText(frame, text, (x, y + h + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)


def _draw_loot_hits(frame, hits):
    cx = config.SCREEN_WIDTH  // 2
    cy = config.SCREEN_HEIGHT // 2
    r  = config.LOOT_RADIUS_PX

    # Scan radius circle
    cv2.circle(frame, (cx, cy), r, COL_REGION, 1)
    cv2.putText(frame, "Loot radius", (cx - r, cy - r - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, COL_REGION, 1, cv2.LINE_AA)

    for lx, ly, tier in hits:
        col = COL_LOOT.get(tier, (255, 255, 255))
        cv2.circle(frame, (lx, ly), 10, col, 2)
        cv2.putText(frame, tier, (lx + 12, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1, cv2.LINE_AA)


def _draw_goblin(frame, visible):
    if visible:
        cv2.putText(frame, "GOBLIN DETECTED!", (20, 60),
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, COL_GOBLIN, 2, cv2.LINE_AA)


def _draw_hud(frame, fps, paused):
    h, w = frame.shape[:2]
    cv2.putText(frame, f"FPS: {fps:.1f}  {'[PAUSED]' if paused else ''}",
                (w - 180, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COL_TEXT, 1, cv2.LINE_AA)
    cv2.putText(frame, "Q=quit  S=save  SPACE=pause",
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, COL_REGION, 1, cv2.LINE_AA)


def run():
    cap  = ScreenCapture()
    recog = ImageRecognizer(cap)

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, 1280, 720)

    paused    = False
    frame_buf = None
    fps       = 0.0
    t0        = time.time()
    fc        = 0

    print("\nDetection Visualizer running.")
    print("  All detected regions are drawn live on screen.")
    print("  This lets you verify your config.py values before running the bot.\n")

    while True:
        if not paused:
            raw = cap.capture()
            if raw is None:
                time.sleep(0.1)
                continue

            # Clone so we don't mutate the capture buffer
            frame = raw.copy()

            # ── Run detectors ───────────────────────────────────────────────
            hp_pct  = recog.detect_health_pct()
            res_pct = recog.detect_resource_pct()
            loot    = recog.detect_loot_items()
            goblin  = recog.detect_goblin()

            # ── Annotate ────────────────────────────────────────────────────
            _draw_region_box(frame, config.HEALTH_BAR_REGION,   COL_HEALTH,   "HP region")
            _draw_region_box(frame, config.RESOURCE_BAR_REGION, COL_RESOURCE, "Resource region")
            _draw_region_box(frame, config.MINIMAP_REGION,      COL_REGION,   "Minimap")

            _draw_fill_bar(frame, config.HEALTH_BAR_REGION,   hp_pct,  COL_HEALTH,   "HP")
            _draw_fill_bar(frame, config.RESOURCE_BAR_REGION, res_pct, COL_RESOURCE, "Resource")

            _draw_loot_hits(frame, loot)
            _draw_goblin(frame, goblin)

            # FPS
            fc += 1
            elapsed = time.time() - t0
            if elapsed >= 1.0:
                fps = fc / elapsed
                fc  = 0
                t0  = time.time()

            _draw_hud(frame, fps, paused)
            frame_buf = frame

        if frame_buf is not None:
            cv2.imshow(WIN, frame_buf)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            paused = not paused
            print("Paused" if paused else "Resumed")
        elif key == ord('s') and frame_buf is not None:
            import datetime
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.expanduser(f"~/d3bot_debug_{ts}.png")
            cv2.imwrite(path, frame_buf)
            print(f"Frame saved: {path}")

    cv2.destroyAllWindows()
    print("Visualizer closed.")


if __name__ == "__main__":
    run()
