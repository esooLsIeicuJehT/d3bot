"""
Region Editor (GUI Tab)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Embedded inside the main GUI — shows a live screenshot and lets you
drag-set every detection region directly on it.

Flow:
  1. Click "Refresh Screenshot" to grab the current screen.
  2. Select a region type from the dropdown.
  3. Left-drag on the screenshot image to draw the rectangle.
  4. Click "Apply Region" → writes the (x,y,w,h) to config at runtime.

No OpenCV window needed — everything runs in tkinter.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, Tuple

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

import config
from io.screen_capture import ScreenCapture

CANVAS_W = 800
CANVAS_H = 450

REGION_OPTIONS = [
    ("Health Bar",    "HEALTH_BAR_REGION"),
    ("Resource Bar",  "RESOURCE_BAR_REGION"),
    ("Minimap",       "MINIMAP_REGION"),
    ("Death Screen",  "DEATH_REGION"),
    ("Game Region",   "GAME_REGION"),
]

REGION_COLORS = {
    "HEALTH_BAR_REGION":   "#00d68f",
    "RESOURCE_BAR_REGION": "#ffa726",
    "MINIMAP_REGION":      "#888888",
    "DEATH_REGION":        "#ef5350",
    "GAME_REGION":         "#e94560",
}

# ── Palette (to match main GUI) ───────────────────────────────────────────────
DARK_BG  = "#1a1a2e"
PANEL_BG = "#16213e"
TEXT_FG  = "#eaeaea"
DIM_FG   = "#666688"
ACCENT   = "#e94560"
ACCENT2  = "#0f3460"
GREEN    = "#00d68f"
ORANGE   = "#ffa726"


class RegionEditor(tk.Frame):
    """
    Drop-in tkinter Frame — embed directly inside a Notebook tab.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)
        self._cap        = ScreenCapture()
        self._raw_img    = None   # PIL Image at full res
        self._tk_img     = None   # PhotoImage for canvas
        self._scale_x    = 1.0
        self._scale_y    = 1.0
        self._drag_start: Optional[Tuple[int,int]] = None
        self._drag_rect  = None
        self._active_region_key = tk.StringVar(value=REGION_OPTIONS[0][1])
        self._status_var = tk.StringVar(value="Click 'Refresh Screenshot' to begin.")

        self._build_ui()
        self._draw_existing_regions()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top toolbar
        toolbar = tk.Frame(self, bg=PANEL_BG, pady=4)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="📷  Refresh Screenshot", command=self._grab_screenshot,
                  font=("Courier New", 9), bg=ACCENT2, fg=TEXT_FG, relief="flat",
                  cursor="hand2", padx=8).pack(side="left", padx=6)

        tk.Label(toolbar, text="Region:", font=("Courier New", 9),
                 fg=DIM_FG, bg=PANEL_BG).pack(side="left", padx=(12, 2))

        combo = ttk.Combobox(toolbar, textvariable=self._active_region_key,
                             values=[k for _, k in REGION_OPTIONS],
                             font=("Courier New", 9), width=22, state="readonly")
        # Show human labels in the box
        combo["values"] = [f"{lbl}  ({key})" for lbl, key in REGION_OPTIONS]
        combo.bind("<<ComboboxSelected>>", self._on_combo_select)
        combo.current(0)
        combo.pack(side="left", padx=2)

        tk.Button(toolbar, text="✔  Apply Region", command=self._apply_region,
                  font=("Courier New", 9), bg=GREEN, fg="#000", relief="flat",
                  cursor="hand2", padx=8).pack(side="left", padx=8)

        tk.Button(toolbar, text="🔄 Reset All", command=self._reset_regions,
                  font=("Courier New", 9), bg="#333", fg=TEXT_FG, relief="flat",
                  cursor="hand2", padx=6).pack(side="right", padx=6)

        # Canvas
        canvas_frame = tk.Frame(self, bg="#000")
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self._canvas = tk.Canvas(canvas_frame, width=CANVAS_W, height=CANVAS_H,
                                 bg="#0a0a14", cursor="crosshair",
                                 highlightthickness=1, highlightbackground=ACCENT2)
        self._canvas.pack(fill="both", expand=True)

        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_release)

        # Current selection info
        info = tk.Frame(self, bg=PANEL_BG, pady=4)
        info.pack(fill="x", padx=8)
        self._sel_var = tk.StringVar(value="No selection")
        tk.Label(info, textvariable=self._sel_var, font=("Courier New", 9),
                 fg=GREEN, bg=PANEL_BG).pack(side="left", padx=6)
        tk.Label(info, textvariable=self._status_var, font=("Courier New", 9),
                 fg=DIM_FG, bg=PANEL_BG).pack(side="right", padx=6)

        # Existing regions table
        self._build_region_table()

    def _build_region_table(self):
        tbl_frame = tk.Frame(self, bg=PANEL_BG, pady=4)
        tbl_frame.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(tbl_frame, text="Current Regions:", font=("Courier New", 9, "bold"),
                 fg=ACCENT, bg=PANEL_BG).pack(anchor="w", padx=6)

        cols = tk.Frame(tbl_frame, bg=PANEL_BG)
        cols.pack(fill="x", padx=6)

        self._region_vars: dict[str, tk.StringVar] = {}
        for lbl, key in REGION_OPTIONS:
            row = tk.Frame(cols, bg=PANEL_BG)
            row.pack(fill="x", pady=1)
            color = REGION_COLORS.get(key, TEXT_FG)
            tk.Label(row, text=f"■ {lbl}:", font=("Courier New", 8),
                     fg=color, bg=PANEL_BG, width=16, anchor="w").pack(side="left")
            var = tk.StringVar(value=self._fmt_region(key))
            self._region_vars[key] = var
            tk.Label(row, textvariable=var, font=("Courier New", 8),
                     fg=TEXT_FG, bg=PANEL_BG).pack(side="left")

    @staticmethod
    def _fmt_region(key: str) -> str:
        val = getattr(config, key, None)
        if val is None:
            return "—"
        return f"x={val[0]}  y={val[1]}  w={val[2]}  h={val[3]}"

    # ── Screenshot ────────────────────────────────────────────────────────────

    def _grab_screenshot(self):
        self._status_var.set("Capturing…")
        self.update()

        def _do():
            frame = self._cap.capture()
            if frame is None:
                self._status_var.set("Capture failed — check mss/PIL install")
                return
            try:
                import cv2
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
            except Exception:
                self._status_var.set("cv2 not available — using blank")
                pil = Image.new("RGB", (1920, 1080), (20, 20, 40))

            self._raw_img = pil
            self.after(0, self._update_canvas)

        threading.Thread(target=_do, daemon=True).start()

    def _update_canvas(self):
        if self._raw_img is None:
            return
        cw = self._canvas.winfo_width()  or CANVAS_W
        ch = self._canvas.winfo_height() or CANVAS_H
        thumb = self._raw_img.copy()
        thumb.thumbnail((cw, ch), Image.LANCZOS)

        self._scale_x = self._raw_img.width  / thumb.width
        self._scale_y = self._raw_img.height / thumb.height

        self._tk_img = ImageTk.PhotoImage(thumb)
        self._canvas.config(width=thumb.width, height=thumb.height)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._tk_img)
        self._draw_existing_regions()
        self._status_var.set(f"Screenshot: {self._raw_img.width}×{self._raw_img.height}  "
                             f"(scaled {thumb.width}×{thumb.height})  — drag to set a region")

    def _draw_existing_regions(self):
        """Draw all current config regions as coloured outlines on the canvas."""
        for lbl, key in REGION_OPTIONS:
            val = getattr(config, key, None)
            if val is None:
                continue
            x, y, w, h = val
            # Scale to canvas space
            cx = int(x / self._scale_x)
            cy = int(y / self._scale_y)
            cw = int(w / self._scale_x)
            ch = int(h / self._scale_y)
            color = REGION_COLORS.get(key, TEXT_FG)
            self._canvas.create_rectangle(cx, cy, cx + cw, cy + ch,
                                          outline=color, width=2, tags="regions")
            self._canvas.create_text(cx + 4, cy + 4, text=lbl, anchor="nw",
                                     fill=color, font=("Courier New", 7), tags="regions")

    # ── Drag-select ───────────────────────────────────────────────────────────

    def _on_press(self, event):
        self._drag_start = (event.x, event.y)
        if self._drag_rect:
            self._canvas.delete(self._drag_rect)
            self._drag_rect = None

    def _on_drag(self, event):
        if not self._drag_start:
            return
        x0, y0 = self._drag_start
        color = REGION_COLORS.get(self._active_region_key.get(), ACCENT)
        if self._drag_rect:
            self._canvas.delete(self._drag_rect)
        self._drag_rect = self._canvas.create_rectangle(
            x0, y0, event.x, event.y, outline=color, width=2, dash=(4, 2)
        )
        # Update selection label
        sx = int(min(x0, event.x) * self._scale_x)
        sy = int(min(y0, event.y) * self._scale_y)
        sw = int(abs(event.x - x0) * self._scale_x)
        sh = int(abs(event.y - y0) * self._scale_y)
        self._sel_var.set(f"Selection: x={sx}  y={sy}  w={sw}  h={sh}")
        self._pending = (sx, sy, sw, sh)

    def _on_release(self, event):
        # Solidify the dashed rect
        if self._drag_rect:
            color = REGION_COLORS.get(self._active_region_key.get(), ACCENT)
            self._canvas.itemconfig(self._drag_rect, dash=())

    # ── Apply / Reset ─────────────────────────────────────────────────────────

    def _on_combo_select(self, event):
        # Parse "Label  (KEY)" format back to just KEY
        sel = self._active_region_key.get()
        if "(" in sel:
            key = sel.split("(")[-1].rstrip(")")
            self._active_region_key.set(key)

    def _apply_region(self):
        key = self._active_region_key.get()
        if not hasattr(self, "_pending") or self._pending is None:
            self._status_var.set("Draw a region first!")
            return
        x, y, w, h = self._pending
        if w < 2 or h < 2:
            self._status_var.set("Selection too small — draw a larger rectangle.")
            return
        setattr(config, key, (x, y, w, h))
        self._region_vars[key].set(self._fmt_region(key))
        self._pending = None
        self._canvas.delete("regions")
        self._draw_existing_regions()
        self._status_var.set(f"✔ {key} set to ({x},{y},{w},{h})")

    def _reset_regions(self):
        from importlib import reload
        import config as _cfg
        reload(_cfg)
        for key, var in self._region_vars.items():
            var.set(self._fmt_region(key))
        self._draw_existing_regions()
        self._status_var.set("Regions reset to config.py defaults.")
