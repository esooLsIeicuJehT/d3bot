# D3 Bot Framework — Educational Research Tool

> ⚠️ **WARNING**: Automating Diablo 3 violates Blizzard's Terms of Service.
> This project is for **educational/research purposes only**. Use on a dedicated
> test account. The authors accept no responsibility for bans or account actions.

---

## Architecture (Context Flow)

```
 ┌─────────────────────────────────────────────────────────┐
 │                     main.py (GUI)                        │
 │   tkinter UI  ←──── EventBus ←────── BotState.snapshot  │
 └───────────────────────────┬─────────────────────────────┘
                             │ creates
 ┌───────────────────────────▼─────────────────────────────┐
 │                   core/bot_engine.py                     │
 │   Orchestrates tick() on each feature every LOOP_INTERVAL│
 └──┬────────────┬────────────┬────────────┬───────────────┘
    │            │            │            │
    ▼            ▼            ▼            ▼
 features/    features/    features/    features/
 health_      skill_       loot_        death_
 monitor.py   rotation.py  collector.py handler.py
    │            │            │
    └────────────┴────────────┘
                 │ all read from
    ┌────────────▼────────────┐
    │   core/state.py         │   ← Single shared context object
    │   BotState (thread-safe)│
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │   io/ layer             │
    │  ScreenCapture          │
    │  ImageRecognizer        │
    │  InputController        │
    └─────────────────────────┘
```

## Features

| Feature          | What it does                                              |
|-----------------|-----------------------------------------------------------|
| Health Monitor  | Detects HP orb %, fires bottomless potion below threshold |
| Resource Monitor| Tracks Mana/Fury/etc., pauses skills when critically low  |
| Skill Rotation  | Fires each skill on its individual cooldown timer         |
| Auto Loot       | Detects item beams by color tier, clicks to collect       |
| Death Handler   | Detects death screen, waits, presses resurrect            |
| Goblin Detector | Spots treasure goblin shimmer, fires alert event          |
| Anti-AFK        | Random micro-movements every 45–90s to prevent idle kick  |

## Setup (Fedora)

```bash
git clone <repo>
cd d3bot
bash setup_fedora.sh
source .venv/bin/activate
python main.py
```

### Wayland note
```bash
export GDK_BACKEND=x11
python main.py
```

## Tuning

All parameters live in `config.py`:
- **Bar regions** (`HEALTH_BAR_REGION`, `RESOURCE_BAR_REGION`) — adjust (x,y,w,h) to your screen resolution
- **Color ranges** — HSV tuples for health/resource orbs. Use `assets/templates/` for OpenCV template images
- **Skill rotation** — edit `DEFAULT_SKILL_ROTATION` or use the GUI Skill Editor
- **Loot priorities** — set `LOOT_PRIORITIES` to `["legendary","set"]` to skip rares

## Template Images

Drop PNG files into `assets/templates/` for template-match detection:
- `death_screen.png` — a crop of the "You have died" UI
- `rift_guardian.png` — the rift guardian health bar
- `accept_button.png` — any accept/OK dialog button

## GUI Hotkeys

| Key  | Action          |
|------|-----------------|
| F5   | Start bot       |
| F6   | Pause / Resume  |
| F7   | Stop bot        |
| ESC  | Emergency stop  |
