#!/usr/bin/env bash
# ============================================================
#  D3 Bot — Fedora Linux Setup Script
#  Run once: bash setup_fedora.sh
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   D3 Bot — Fedora Dependency Installer   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── System packages ──────────────────────────────────────────
echo "[1/4] Installing system packages via dnf..."
sudo dnf install -y \
    python3-pip \
    python3-tkinter \
    python3-devel \
    gcc \
    xdotool \
    libXtst-devel \
    scrot \
    2>/dev/null || true

# ── Python virtual environment ───────────────────────────────
echo "[2/4] Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# ── Python packages ──────────────────────────────────────────
echo "[3/4] Installing Python packages..."
pip install --upgrade pip -q
pip install \
    mss \
    opencv-python-headless \
    numpy \
    pynput \
    Pillow \
    --quiet

# ── Assets directory ─────────────────────────────────────────
echo "[4/4] Creating assets/templates directory..."
mkdir -p assets/templates

echo ""
echo "✅  Setup complete!"
echo ""
echo "To run the bot:"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "NOTE: On Wayland, set: export GDK_BACKEND=x11"
echo "      before running if you have input issues."
echo ""
