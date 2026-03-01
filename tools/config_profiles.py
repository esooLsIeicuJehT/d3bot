"""
Config Profile Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Educational purpose: demonstrates serialisation, schema validation,
and runtime config hot-swapping without restarting the bot.

What it does:
  • Saves a named snapshot of all tuneable config.py values to ~/.d3bot_profiles/
  • Loads a saved profile back into config at runtime
  • Lists, diffs, and deletes profiles
  • Validates types before applying (prevents bad values crashing the bot)

Profiles are stored as plain JSON — human-readable and easily version-controlled.

Usage:
    from tools.config_profiles import ProfileManager
    pm = ProfileManager()
    pm.save("wizard_archon")        # save current config
    pm.load("wizard_archon")        # restore it later
    pm.diff("wizard_archon", "monk_inna")  # compare two profiles

CLI:
    python tools/config_profiles.py list
    python tools/config_profiles.py save my_build
    python tools/config_profiles.py load my_build
    python tools/config_profiles.py diff build_a build_b
"""

from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

PROFILES_DIR = os.path.expanduser("~/.d3bot_profiles")

# Keys we serialise — only scalar / simple-list values
SERIALISABLE_KEYS = [
    "SCREEN_WIDTH", "SCREEN_HEIGHT",
    "HEALTH_BAR_REGION", "RESOURCE_BAR_REGION", "MINIMAP_REGION",
    "HEALTH_COLOR_LOW", "HEALTH_COLOR_HIGH",
    "RESOURCE_COLOR_LOW", "RESOURCE_COLOR_HIGH",
    "GOBLIN_COLOR_LOW", "GOBLIN_COLOR_HIGH", "GOBLIN_MIN_PIXELS",
    "DEATH_DARK_THRESHOLD", "DEATH_REGION",
    "LOOP_INTERVAL", "HEALTH_CHECK_INTERVAL", "RESOURCE_CHECK_INTERVAL",
    "LOOT_SCAN_INTERVAL", "STATUS_LOG_INTERVAL",
    "HEALTH_POTION_COOLDOWN", "RESURRECTION_DELAY",
    "RANDOM_DELAY_MIN", "RANDOM_DELAY_MAX", "MAX_RUNTIME_MINUTES",
    "HEALTH_THRESHOLD", "RESOURCE_THRESHOLD",
    "DEFAULT_SKILL_ROTATION",
    "POTION_KEY", "CLICK_JITTER_PX",
    "AUTO_LOOT_ENABLED", "LOOT_PRIORITIES", "LOOT_RADIUS_PX",
    "LOOT_COLORS",
]


class ProfileManager:
    def __init__(self, profiles_dir: str = PROFILES_DIR):
        os.makedirs(profiles_dir, exist_ok=True)
        self._dir = profiles_dir

    # ── Core operations ───────────────────────────────────────────────────────

    def save(self, name: str) -> str:
        """Snapshot current config values to a named profile."""
        data = {}
        for key in SERIALISABLE_KEYS:
            val = getattr(config, key, None)
            if val is not None:
                data[key] = val
        path = self._path(name)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Profile saved: {path}")
        return path

    def load(self, name: str) -> bool:
        """Load a profile into the live config module."""
        path = self._path(name)
        if not os.path.exists(path):
            print(f"Profile not found: {name}")
            return False

        with open(path) as f:
            data: dict = json.load(f)

        errors = self._validate(data)
        if errors:
            print("Validation errors — profile NOT loaded:")
            for e in errors:
                print(f"  • {e}")
            return False

        for key, val in data.items():
            setattr(config, key, val)

        print(f"Profile loaded: {name}")
        return True

    def list_profiles(self) -> list[str]:
        return sorted(
            f[:-5] for f in os.listdir(self._dir) if f.endswith(".json")
        )

    def delete(self, name: str):
        path = self._path(name)
        if os.path.exists(path):
            os.remove(path)
            print(f"Profile deleted: {name}")
        else:
            print(f"Profile not found: {name}")

    def diff(self, name_a: str, name_b: str):
        """Print keys that differ between two profiles."""
        a = self._read(name_a)
        b = self._read(name_b)
        if a is None or b is None:
            return

        all_keys = set(a) | set(b)
        diffs = []
        for k in sorted(all_keys):
            va, vb = a.get(k, "‹missing›"), b.get(k, "‹missing›")
            if va != vb:
                diffs.append((k, va, vb))

        if not diffs:
            print(f"Profiles '{name_a}' and '{name_b}' are identical.")
            return

        print(f"\nDiff: '{name_a}'  vs  '{name_b}'")
        print("─" * 60)
        for k, va, vb in diffs:
            print(f"  {k}:")
            print(f"    {name_a}: {va}")
            print(f"    {name_b}: {vb}")
        print("─" * 60)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _path(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in "_-")
        return os.path.join(self._dir, safe + ".json")

    def _read(self, name: str) -> dict | None:
        path = self._path(name)
        if not os.path.exists(path):
            print(f"Profile not found: {name}")
            return None
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _validate(data: dict) -> list[str]:
        """Basic type/range checks to prevent bad values crashing the bot."""
        errors = []
        float_keys = [
            "HEALTH_THRESHOLD", "RESOURCE_THRESHOLD", "LOOP_INTERVAL",
            "HEALTH_CHECK_INTERVAL", "RESOURCE_CHECK_INTERVAL", "LOOT_SCAN_INTERVAL",
            "HEALTH_POTION_COOLDOWN", "RANDOM_DELAY_MIN", "RANDOM_DELAY_MAX",
        ]
        for k in float_keys:
            if k in data:
                try:
                    v = float(data[k])
                    if v < 0:
                        errors.append(f"{k} must be >= 0 (got {v})")
                except (TypeError, ValueError):
                    errors.append(f"{k} must be a number (got {data[k]!r})")

        for thresh in ["HEALTH_THRESHOLD", "RESOURCE_THRESHOLD"]:
            if thresh in data:
                v = data[thresh]
                if isinstance(v, (int, float)) and not (0.0 <= v <= 1.0):
                    errors.append(f"{thresh} must be between 0.0 and 1.0 (got {v})")

        for region_key in ["HEALTH_BAR_REGION", "RESOURCE_BAR_REGION"]:
            if region_key in data:
                r = data[region_key]
                if not (isinstance(r, (list, tuple)) and len(r) == 4):
                    errors.append(f"{region_key} must be a list of 4 ints [x,y,w,h]")

        return errors


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pm = ProfileManager()

    if len(sys.argv) < 2 or sys.argv[1] == "list":
        profiles = pm.list_profiles()
        if profiles:
            print("\nSaved profiles:")
            for p in profiles:
                print(f"  • {p}")
        else:
            print("No profiles saved yet.")
        print(f"  (stored in {PROFILES_DIR})")

    elif sys.argv[1] == "save" and len(sys.argv) >= 3:
        pm.save(sys.argv[2])

    elif sys.argv[1] == "load" and len(sys.argv) >= 3:
        if pm.load(sys.argv[2]):
            print("Note: config changes only affect the current process.")
            print("      Restart the bot to apply to a fresh session.")

    elif sys.argv[1] == "delete" and len(sys.argv) >= 3:
        pm.delete(sys.argv[2])

    elif sys.argv[1] == "diff" and len(sys.argv) >= 4:
        pm.diff(sys.argv[2], sys.argv[3])

    else:
        print("Usage:")
        print("  python tools/config_profiles.py list")
        print("  python tools/config_profiles.py save  <name>")
        print("  python tools/config_profiles.py load  <name>")
        print("  python tools/config_profiles.py delete <name>")
        print("  python tools/config_profiles.py diff  <name_a> <name_b>")
