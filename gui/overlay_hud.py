"""
In-Game Overlay HUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A small transparent always-on-top window you can position anywhere on
screen — visible while Diablo 3 runs in borderless windowed mode.

Shows live:
  • Bot phase + runtime
  • HP bar  (colour-coded)
  • Resource bar
  • Last event fired
  • Skills on cooldown
  • Potion / death counters

Drag it by left-clicking the title bar area.
Right-click anywhere → context menu (toggle opacity, close).
"""

from __future__ import annotations
import tkinter as tk
import time
from typing import Optional

from core.state import BotState, BotPhase
from core.event_bus import EventBus, bus

# ── Colours ───────────────────────────────────────────────────────────────────
_BG       = "#0d0d1a"
_FG       = "#eaeaea"
_GREEN    = "#00d68f"
_ORANGE   = "#ffa726"
_RED      = "#ef5350"
_DIM      = "#666688"
_ACCENT   = "#e94560"
_TITLE_BG = "#16213e"

_PHASE_COLORS = {
    "RUNNING":      _GREEN,
    "PAUSED":       _ORANGE,
    "IDLE":         _DIM,
    "DEAD":         _RED,
    "RESURRECTING": _ORANGE,
    "STOPPING":     _RED,
}


class OverlayHUD(tk.Toplevel):
    """Transparent, draggable, always-on-top HUD window."""

    def __init__(self, parent: tk.Misc, state: BotState):
        super().__init__(parent)
        self._state      = state
        self._last_event = "—"
        self._drag_x     = 0
        self._drag_y     = 0
        self._opacity    = 0.82

        self._configure_window()
        self._build_ui()
        self._subscribe_events()
        self._schedule_refresh()

    # ── Window config ────────────────────────────────────────────────────────

    def _configure_window(self):
        self.title("D3 HUD")
        self.overrideredirect(True)          # no OS title bar
        self.wm_attributes("-topmost", True) # always on top
        self.wm_attributes("-alpha", self._opacity)
        self.configure(bg=_BG)
        self.geometry("260x220+20+20")

        # Drag support
        self.bind("<ButtonPress-1>",   self._on_drag_start)
        self.bind("<B1-Motion>",        self._on_drag_move)

        # Right-click context menu
        self._menu = tk.Menu(self, tearoff=0, bg=_TITLE_BG, fg=_FG,
                             activebackground=_ACCENT, activeforeground="white")
        self._menu.add_command(label="Opacity +10%", command=lambda: self._change_opacity(+0.1))
        self._menu.add_command(label="Opacity -10%", command=lambda: self._change_opacity(-0.1))
        self._menu.add_separator()
        self._menu.add_command(label="Close HUD",    command=self.destroy)
        self.bind("<Button-3>", lambda e: self._menu.tk_popup(e.x_root, e.y_root))

    # ── UI Build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar (drag handle) ───────────────────────────────────────────
        title_bar = tk.Frame(self, bg=_TITLE_BG, cursor="fleur")
        title_bar.pack(fill="x")
        title_bar.bind("<ButtonPress-1>", self._on_drag_start)
        title_bar.bind("<B1-Motion>",      self._on_drag_move)

        tk.Label(title_bar, text="⚔ D3 BOT", font=("Courier New", 9, "bold"),
                 fg=_ACCENT, bg=_TITLE_BG).pack(side="left", padx=6, pady=2)
        self._phase_lbl = tk.Label(title_bar, text="● IDLE",
                                   font=("Courier New", 8, "bold"),
                                   fg=_DIM, bg=_TITLE_BG)
        self._phase_lbl.pack(side="right", padx=6)

        body = tk.Frame(self, bg=_BG, padx=8, pady=4)
        body.pack(fill="both", expand=True)

        # Runtime
        row0 = tk.Frame(body, bg=_BG)
        row0.pack(fill="x", pady=1)
        tk.Label(row0, text="Runtime:", font=("Courier New", 8), fg=_DIM, bg=_BG, width=10, anchor="w").pack(side="left")
        self._runtime_lbl = tk.Label(row0, text="00:00:00", font=("Courier New", 8, "bold"), fg=_FG, bg=_BG)
        self._runtime_lbl.pack(side="left")

        # HP bar
        self._hp_bar  = self._make_bar(body, "HP", _GREEN)

        # Resource bar
        self._res_bar = self._make_bar(body, "Res", _ORANGE)

        # Separator
        tk.Frame(body, bg=_TITLE_BG, height=1).pack(fill="x", pady=4)

        # Stats row
        stats = tk.Frame(body, bg=_BG)
        stats.pack(fill="x")
        self._stat_lbls: dict[str, tk.Label] = {}
        for key, icon in [("potions_used","💊"), ("deaths","💀"), ("items_looted","💰"), ("goblins_spotted","👺")]:
            col = tk.Frame(stats, bg=_BG)
            col.pack(side="left", expand=True)
            tk.Label(col, text=icon, font=("Courier New", 10), bg=_BG).pack()
            lbl = tk.Label(col, text="0", font=("Courier New", 9, "bold"), fg=_GREEN, bg=_BG)
            lbl.pack()
            self._stat_lbls[key] = lbl

        # Last event
        tk.Frame(body, bg=_TITLE_BG, height=1).pack(fill="x", pady=4)
        ev_row = tk.Frame(body, bg=_BG)
        ev_row.pack(fill="x")
        tk.Label(ev_row, text="Last:", font=("Courier New", 8), fg=_DIM, bg=_BG, width=6, anchor="w").pack(side="left")
        self._event_lbl = tk.Label(ev_row, text="—", font=("Courier New", 8),
                                   fg=_ACCENT, bg=_BG, wraplength=180, anchor="w")
        self._event_lbl.pack(side="left", fill="x")

    def _make_bar(self, parent, label_text: str, color: str):
        row = tk.Frame(parent, bg=_BG)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=f"{label_text}:", font=("Courier New", 8), fg=_DIM,
                 bg=_BG, width=5, anchor="w").pack(side="left")
        canvas = tk.Canvas(row, width=180, height=12, bg="#0a0a14",
                           highlightthickness=0)
        canvas.pack(side="left")
        bar  = canvas.create_rectangle(0, 0, 0, 12, fill=color, outline="")
        text = canvas.create_text(90, 6, text="—", fill=_FG, font=("Courier New", 7))
        return {"canvas": canvas, "bar": bar, "text": text, "color": color, "width": 180}

    def _set_bar(self, bar_info: dict, pct: Optional[float]):
        c = bar_info["canvas"]
        if pct is None:
            c.itemconfig(bar_info["text"], text="N/A")
            c.coords(bar_info["bar"], 0, 0, 0, 12)
            return
        w = int(bar_info["width"] * max(0.0, min(1.0, pct)))
        color = _GREEN if pct > 0.5 else (_ORANGE if pct > 0.25 else _RED)
        c.coords(bar_info["bar"], 0, 0, w, 12)
        c.itemconfig(bar_info["bar"], fill=color)
        c.itemconfig(bar_info["text"], text=f"{pct*100:.0f}%")

    # ── Events ───────────────────────────────────────────────────────────────

    def _subscribe_events(self):
        def _set_last(msg):
            self._last_event = msg
        bus.subscribe(EventBus.POTION_USED,       lambda p: _set_last(f"💊 Potion ({p*100:.0f}%)"))
        bus.subscribe(EventBus.PLAYER_DIED,        lambda _: _set_last("💀 Died — resurrecting"))
        bus.subscribe(EventBus.PLAYER_RESURRECTED, lambda _: _set_last("✅ Resurrected"))
        bus.subscribe(EventBus.GOBLIN_DETECTED,    lambda _: _set_last("👺 GOBLIN!"))
        bus.subscribe(EventBus.LOOT_COLLECTED,     lambda d: _set_last(f"💰 {d.get('tier','?')} loot"))
        bus.subscribe(EventBus.SKILL_FIRED,        lambda d: _set_last(f"⚡ {d.get('label','?')} [{d.get('key','?')}]"))
        bus.subscribe(EventBus.LOW_HEALTH,         lambda p: _set_last(f"⚠ Low HP: {p*100:.0f}%"))

    # ── Refresh ──────────────────────────────────────────────────────────────

    def _schedule_refresh(self):
        try:
            self._refresh()
        except tk.TclError:
            return
        self.after(400, self._schedule_refresh)

    def _refresh(self):
        snap  = self._state.snapshot()
        phase = snap["phase"]
        stats = snap["stats"]

        # Phase label
        color = _PHASE_COLORS.get(phase, _DIM)
        self._phase_lbl.config(text=f"● {phase}", fg=color)

        # Runtime
        self._runtime_lbl.config(text=stats.get("elapsed", "00:00:00"))

        # Bars
        self._set_bar(self._hp_bar,  snap.get("health_pct"))
        self._set_bar(self._res_bar, snap.get("resource_pct"))

        # Stats icons
        for key, lbl in self._stat_lbls.items():
            lbl.config(text=str(stats.get(key, 0)))

        # Last event
        self._event_lbl.config(text=self._last_event)

    # ── Drag ────────────────────────────────────────────────────────────────

    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _change_opacity(self, delta: float):
        self._opacity = max(0.2, min(1.0, self._opacity + delta))
        self.wm_attributes("-alpha", self._opacity)
