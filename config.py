"""
D3 Bot Configuration
All tuneable parameters live here — single source of truth for the Context Flow.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import json
import os

CONFIG_FILE = os.path.expanduser("~/.d3bot_config.json")

# ─── Resolution & Region ────────────────────────────────────────────────────
SCREEN_WIDTH  = 1920
SCREEN_HEIGHT = 1080

# UI bar regions (x, y, w, h) — tune to your resolution
HEALTH_BAR_REGION    = (62,  1020, 155, 18)   # Red orb area
RESOURCE_BAR_REGION  = (1700, 1020, 155, 18)  # Blue/yellow orb area
MINIMAP_REGION       = (1720,  30, 190, 190)
GAME_REGION          = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

# ─── Color Thresholds (HSV) ─────────────────────────────────────────────────
# Health orb red
HEALTH_COLOR_LOW  = (0,   120, 100)
HEALTH_COLOR_HIGH = (10,  255, 255)

# Resource orb (class-dependent; defaults to mana blue)
RESOURCE_COLOR_LOW  = (100, 120, 100)
RESOURCE_COLOR_HIGH = (130, 255, 255)

# Loot tier colors (BGR for OpenCV)
LOOT_COLORS = {
    "legendary": (0,  128, 255),   # Orange  → highest priority
    "set":       (0,  255,   0),   # Green
    "rare":      (0,  255, 255),   # Yellow
    "magic":     (255, 50,  50),   # Blue
}
LOOT_COLOR_TOLERANCE = 30          # BGR distance tolerance

# Goblin detection — bright purple shimmer
GOBLIN_COLOR_LOW  = (130, 100, 150)
GOBLIN_COLOR_HIGH = (160, 255, 255)
GOBLIN_MIN_PIXELS = 200

# Death screen — dark overlay detection
DEATH_DARK_THRESHOLD = 30         # mean pixel brightness below this = likely dead
DEATH_REGION = (700, 400, 520, 120)  # where "You have died" text appears

# ─── Timing (seconds) ───────────────────────────────────────────────────────
LOOP_INTERVAL        = 0.05    # Main loop tick
HEALTH_CHECK_INTERVAL   = 0.3
RESOURCE_CHECK_INTERVAL = 0.5
LOOT_SCAN_INTERVAL   = 1.0
STATUS_LOG_INTERVAL  = 60.0

HEALTH_POTION_COOLDOWN  = 30.0  # Bottomless potion cooldown
RESURRECTION_DELAY      = 3.0

RANDOM_DELAY_MIN = 0.02
RANDOM_DELAY_MAX = 0.12

MAX_RUNTIME_MINUTES = 180

# ─── Trigger Thresholds ─────────────────────────────────────────────────────
HEALTH_THRESHOLD   = 0.45    # Use potion below 45%
RESOURCE_THRESHOLD = 0.15    # Pause attacking below 15%

# ─── Skill Rotation ─────────────────────────────────────────────────────────
# Each entry: (key, cooldown_seconds, description)
DEFAULT_SKILL_ROTATION: List[Tuple[str, float, str]] = [
    ("1", 0.0,   "Primary Attack"),
    ("2", 4.0,   "Secondary / AoE"),
    ("3", 8.0,   "Defensive / CC"),
    ("4", 12.0,  "Power Skill"),
    ("q", 20.0,  "Ultimate / Cooldown"),
    ("e", 30.0,  "Second Ultimate"),
]

# ─── Input ──────────────────────────────────────────────────────────────────
POTION_KEY   = "q"   # Bottomless potion (override per build)
ACCEPT_KEY   = "\n"
RESURRECT_KEY = "\n"

# Click jitter — adds human-like randomness to clicks
CLICK_JITTER_PX = 4

# ─── Loot Settings ──────────────────────────────────────────────────────────
AUTO_LOOT_ENABLED   = True
LOOT_PRIORITIES     = ["legendary", "set", "rare"]  # skip magic by default
LOOT_RADIUS_PX      = 120   # px from character center to scan

# ─── Rift / GR Settings ─────────────────────────────────────────────────────
RIFT_AUTO_ENTER     = False  # Requires further template images
RIFT_PROGRESS_KEY   = "p"   # Open progression UI

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_FILE  = os.path.expanduser("~/d3bot.log")
LOG_LEVEL = "DEBUG"

# ─── Persistence helper ──────────────────────────────────────────────────────
def load_user_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_user_config(data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
