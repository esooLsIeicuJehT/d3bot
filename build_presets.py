"""
Class Build Presets
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pre-configured skill rotations, resource types, and thresholds
for each Diablo 3 class.  The GUI Presets tab lets you load any
preset with one click — it hot-swaps config values at runtime
without restarting the bot.

Each preset contains:
  skill_rotation : list of (key, cooldown_s, label)
  resource_type  : human label for the resource bar colour hint
  resource_hsv_low / high : HSV range override for the resource orb
  health_threshold    : HP% to use potion
  resource_threshold  : resource% to pause skills
  notes               : description string shown in GUI
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any


SkillDef = Tuple[str, float, str]

PRESETS: Dict[str, Dict[str, Any]] = {

    # ── Wizard — Archon ──────────────────────────────────────────────────────
    "Wizard — Archon": {
        "class":    "Wizard",
        "resource_type": "Arcane Power",
        "resource_hsv_low":  (120, 100, 100),
        "resource_hsv_high": (150, 255, 255),
        "health_threshold":   0.40,
        "resource_threshold": 0.10,
        "skill_rotation": [
            ("1", 0.0,  "Magic Missile (Primary)"),
            ("2", 4.0,  "Arcane Orb"),
            ("3", 8.0,  "Slow Time"),
            ("4", 15.0, "Archon"),
            ("q", 20.0, "Teleport"),
            ("e", 60.0, "Black Hole"),
        ],
        "notes": "Classic Archon build. Key skill is [4] Archon — has 15s CD in non-Archon form. "
                 "Teleport [q] is your mobility. Black Hole [e] on elites.",
    },

    # ── Necromancer — Bone Spear ─────────────────────────────────────────────
    "Necromancer — Bone Spear": {
        "class":    "Necromancer",
        "resource_type": "Essence",
        "resource_hsv_low":  (130, 80, 80),
        "resource_hsv_high": (160, 255, 255),
        "health_threshold":   0.50,
        "resource_threshold": 0.20,
        "skill_rotation": [
            ("1", 0.0,  "Grim Scythe (Generator)"),
            ("2", 0.0,  "Bone Spear"),
            ("3", 12.0, "Simulacrum"),
            ("4", 30.0, "Land of the Dead"),
            ("q", 8.0,  "Frailty / Curse"),
            ("e", 20.0, "Bone Armor"),
        ],
        "notes": "Spam [1] to generate Essence → dump into Bone Spear [2]. "
                 "Land of the Dead [4] = burst window, pair with Simulacrum [3].",
    },

    # ── Barbarian — Whirlwind ────────────────────────────────────────────────
    "Barbarian — Whirlwind": {
        "class":    "Barbarian",
        "resource_type": "Fury",
        "resource_hsv_low":  (10, 150, 150),
        "resource_hsv_high": (25, 255, 255),
        "health_threshold":   0.55,
        "resource_threshold": 0.05,   # Fury generates in combat, rarely low
        "skill_rotation": [
            ("1", 0.0,  "Frenzy / Bash (Generator)"),
            ("2", 0.0,  "Whirlwind (Hold)"),
            ("3", 8.0,  "War Cry"),
            ("4", 20.0, "Wrath of the Berserker"),
            ("q", 15.0, "Sprint"),
            ("e", 30.0, "Call of the Ancients"),
        ],
        "notes": "WW Barb — keep [2] Whirlwind channelled always. "
                 "WOTB [4] is your power window. War Cry [3] for defense.",
    },

    # ── Demon Hunter — Multishot ─────────────────────────────────────────────
    "Demon Hunter — Multishot": {
        "class":    "Demon Hunter",
        "resource_type": "Hatred / Discipline",
        "resource_hsv_low":  (0, 80, 80),
        "resource_hsv_high": (10, 200, 200),
        "health_threshold":   0.45,
        "resource_threshold": 0.15,
        "skill_rotation": [
            ("1", 0.0,  "Hungering Arrow (Generator)"),
            ("2", 0.0,  "Multishot"),
            ("3", 12.0, "Vengeance"),
            ("4", 6.0,  "Rain of Vengeance"),
            ("q", 8.0,  "Vault (Mobility)"),
            ("e", 15.0, "Companion"),
        ],
        "notes": "Spam Multishot [2] — Vengeance [3] refunds Hatred. "
                 "Vault [q] for repositioning. Prioritise Discipline for Vault.",
    },

    # ── Monk — Inna's Mantra ─────────────────────────────────────────────────
    "Monk — Inna's Mantra": {
        "class":    "Monk",
        "resource_type": "Spirit",
        "resource_hsv_low":  (25, 100, 150),
        "resource_hsv_high": (40, 255, 255),
        "health_threshold":   0.45,
        "resource_threshold": 0.15,
        "skill_rotation": [
            ("1", 0.0,  "Fists of Thunder (Generator)"),
            ("2", 0.0,  "Lashing Tail Kick"),
            ("3", 0.0,  "Mantra of Salvation"),
            ("4", 20.0, "Epiphany"),
            ("q", 6.0,  "Dashing Strike"),
            ("e", 30.0, "Inner Sanctuary"),
        ],
        "notes": "Inna summons allied Mystic Allies passively. "
                 "Epiphany [4] = huge Spirit regen + mobility. Dash [q] frequently.",
    },

    # ── Crusader — Blessed Shield ─────────────────────────────────────────────
    "Crusader — Blessed Shield": {
        "class":    "Crusader",
        "resource_type": "Wrath",
        "resource_hsv_low":  (20, 100, 150),
        "resource_hsv_high": (35, 255, 255),
        "health_threshold":   0.50,
        "resource_threshold": 0.20,
        "skill_rotation": [
            ("1", 0.0,  "Punish (Generator)"),
            ("2", 0.0,  "Blessed Shield"),
            ("3", 8.0,  "Laws of Valor"),
            ("4", 20.0, "Akarat's Champion"),
            ("q", 12.0, "Iron Skin"),
            ("e", 15.0, "Consecration"),
        ],
        "notes": "Akarat's Champion [4] is your most important cooldown — near 100% uptime with CDR. "
                 "Iron Skin [q] for survivability on elites.",
    },

    # ── Witch Doctor — Mundunugu ──────────────────────────────────────────────
    "Witch Doctor — Mundunugu": {
        "class":    "Witch Doctor",
        "resource_type": "Mana",
        "resource_hsv_low":  (55, 60, 80),
        "resource_hsv_high": (80, 220, 220),
        "health_threshold":   0.45,
        "resource_threshold": 0.25,
        "skill_rotation": [
            ("1", 0.0,  "Grasp of the Dead"),
            ("2", 0.0,  "Big Bad Voodoo"),
            ("3", 8.0,  "Spirit Walk"),
            ("4", 15.0, "Piranhas"),
            ("q", 12.0, "Horrify"),
            ("e", 30.0, "Soul Harvest"),
        ],
        "notes": "Big Bad Voodoo [2] — place before engaging. "
                 "Spirit Walk [3] for escape / immunity. Piranhas [4] on elites for debuff.",
    },
}


def get_preset(name: str) -> Dict[str, Any] | None:
    return PRESETS.get(name)


def list_presets() -> List[str]:
    return list(PRESETS.keys())


def apply_preset(name: str) -> bool:
    """Apply a preset's values to the live config module. Returns True on success."""
    import config as cfg
    preset = PRESETS.get(name)
    if not preset:
        return False

    cfg.DEFAULT_SKILL_ROTATION = preset["skill_rotation"]
    cfg.HEALTH_THRESHOLD       = preset["health_threshold"]
    cfg.RESOURCE_THRESHOLD     = preset["resource_threshold"]
    if "resource_hsv_low" in preset:
        cfg.RESOURCE_COLOR_LOW  = preset["resource_hsv_low"]
        cfg.RESOURCE_COLOR_HIGH = preset["resource_hsv_high"]
    return True
