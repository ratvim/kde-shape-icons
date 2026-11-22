#!/usr/bin/env bash
# ==============================================================================
#  KDE Shape Icons — Material Shape Icon Theme Installer for KDE Plasma 6
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3)"

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Error: python3 is required but was not found in PATH."
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  KDE Shape Icons — Material Theme Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# If arguments were passed directly, pass them to shape_icons.py generate
if [ "$#" -gt 0 ]; then
    echo "==> Running with provided options..."
    "$PYTHON_BIN" "$SCRIPT_DIR/shape_icons.py" generate "$@"
    exit 0
fi

# Interactive mode
echo ""
echo "Select icon shape:"
echo "  1) Circle (Classic Material Design circular icon)"
echo "  2) Squircle (Continuous curvature superellipse - iOS / OneUI)"
echo "  3) Rounded Square (Material 3 standard rounded rectangle)"
echo "  4) Hexagon (Geometric modern hexagon)"
echo "  5) Pebble (Asymmetric organic pebble shape)"
echo "  6) Octagon (Tech chamfered octagon)"
read -rp "Enter choice [1-6, default: 1]: " shape_choice

case "$shape_choice" in
    2) SHAPE="squircle" ;;
    3) SHAPE="rounded_square" ;;
    4) SHAPE="hexagon" ;;
    5) SHAPE="pebble" ;;
    6) SHAPE="octagon" ;;
    *) SHAPE="circle" ;;
esac

echo ""
echo "Select theme mode:"
echo "  1) Auto (Follow current KDE Dark / Light theme setting)"
echo "  2) Dark (Material dark surface)"
echo "  3) Light (Material light surface)"
read -rp "Enter choice [1-3, default: 1]: " mode_choice

case "$mode_choice" in
    2) MODE="dark" ;;
    3) MODE="light" ;;
    *) MODE="auto" ;;
esac

echo ""
echo "Select shading style:"
echo "  1) Accent Ring (Neutral surface + vibrant accent border ring)"
echo "  2) Accent Tint (Surface subtly tinted with 12-15% accent color)"
echo "  3) Accent Fill (Full solid accent color plate)"
echo "  4) Glassmorphism (Frosted glass look with accent glow)"
echo "  5) Minimal (Monochrome surface with soft subtle border)"
read -rp "Enter choice [1-5, default: 1]: " style_choice

case "$style_choice" in
    2) STYLE="accent_tint" ;;
    3) STYLE="accent_filled" ;;
    4) STYLE="glassmorphism" ;;
    5) STYLE="minimal" ;;
    *) STYLE="accent_ring" ;;
esac

echo ""
echo "Accent Color:"
echo "  1) Auto (Detect from KDE AccentColor setting)"
echo "  2) Custom hex code"
read -rp "Enter choice [1-2, default: 1]: " accent_choice

if [ "$accent_choice" = "2" ]; then
    read -rp "Enter hex color code (e.g. #3584e4): " ACCENT
    if [ -z "$ACCENT" ]; then
        ACCENT="auto"
    fi
else
    ACCENT="auto"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "==> Generating $SHAPE ($STYLE) icon theme..."
"$PYTHON_BIN" "$SCRIPT_DIR/shape_icons.py" generate \
    --shape "$SHAPE" \
    --style "$STYLE" \
    --mode "$MODE" \
    --accent "$ACCENT" \
    --apply

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All done! Your new shape icons are generated and active."

