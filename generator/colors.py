"""
Color calculations, KDE accent detection, and dark/light shading styles.
"""

import os
import re
import configparser

PRESET_COLORS = {
    "kde_teal": "#2cbd9e",       # KDE default emerald / teal
    "ocean_blue": "#3584e4",     # GNOME / KDE blue
    "deep_purple": "#7b52ab",    # Vibrant purple
    "sunset_orange": "#ff7800",  # Warm sunset orange
    "crimson_red": "#e01b24",    # Bold crimson
    "cyber_amber": "#f5c211",    # Cyberpunk warm amber
    "neon_pink": "#ec407a",      # Bright magenta/pink
    "mint_green": "#00c853",     # Material vibrant green
    "sky_cyan": "#00b0ff",       # Vibrant cyan
    "slate_neutral": "#6c757d"   # Clean slate gray
}

def detect_kde_accent_color() -> str:
    """Reads KDE's current accent color from ~/.config/kdeglobals."""
    kdeglobals = os.path.expanduser("~/.config/kdeglobals")
    if os.path.exists(kdeglobals):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(kdeglobals)
            accent = config.get("General", "AccentColor", fallback=None)
            if accent:
                parts = [int(p.strip()) for p in accent.split(",") if p.strip().isdigit()]
                if len(parts) >= 3:
                    return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        except Exception:
            pass
    return PRESET_COLORS["kde_teal"]

def detect_kde_theme_mode() -> str:
    """Determines whether KDE is currently using a Dark or Light theme."""
    kdeglobals = os.path.expanduser("~/.config/kdeglobals")
    if os.path.exists(kdeglobals):
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(kdeglobals)
            scheme = config.get("General", "ColorScheme", fallback="").lower()
            if "dark" in scheme or "black" in scheme or "night" in scheme:
                return "dark"
        except Exception:
            pass
    return "light"

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    elif len(h) < 6:
        h = h.ljust(6, "0")
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except Exception:
        return 44, 189, 158  # Default KDE teal fallback

def rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"

def blend_colors(hex1: str, hex2: str, weight2: float) -> str:
    """Blends two hex colors. weight2 is the ratio of hex2 (0.0 to 1.0)."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    w1 = 1.0 - weight2
    return rgb_to_hex(r1 * w1 + r2 * weight2, g1 * w1 + g2 * weight2, b1 * w1 + g2 * weight2)

def adjust_brightness(hex_str: str, factor: float) -> str:
    """Darkens (< 1.0) or lightens (> 1.0) a hex color."""
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(r * factor, g * factor, b * factor)

def get_style_palette(style: str, mode: str, accent: str):
    """
    Computes background stops, border/stroke, and shadow properties
    based on style ('accent_ring', 'accent_tint', 'accent_filled', 'glassmorphism', 'minimal'),
    mode ('dark' or 'light'), and the chosen accent hex color.
    """
    style = style.lower().strip() if style else "accent_ring"
    mode = mode.lower().strip() if mode else "auto"
    accent = accent.strip() if accent else "auto"

    if mode == "auto":
        mode = detect_kde_theme_mode()

    if accent == "auto":
        accent = detect_kde_accent_color()
    elif accent in PRESET_COLORS:
        accent = PRESET_COLORS[accent]
    elif not accent.startswith("#"):
        accent = "#" + accent

    is_dark = (mode == "dark")

    if style == "accent_filled":
        # Full vibrant accent plate
        top = adjust_brightness(accent, 1.12 if is_dark else 1.08)
        bottom = adjust_brightness(accent, 0.88 if is_dark else 0.92)
        border = "#ffffff" if is_dark else "#000000"
        border_opacity = 0.22 if is_dark else 0.15
        shadow_color = "#000000"
        shadow_opacity = 0.35 if is_dark else 0.22
    elif style == "accent_tint":
        # Surface subtly tinted with the accent color
        if is_dark:
            dark_base = "#151821"
            top = blend_colors(dark_base, accent, 0.16)
            bottom = blend_colors("#10121a", accent, 0.12)
            border = accent
            border_opacity = 0.85
            shadow_color = "#000000"
            shadow_opacity = 0.38
        else:
            light_base = "#ffffff"
            top = blend_colors(light_base, accent, 0.08)
            bottom = blend_colors("#f0f3f7", accent, 0.12)
            border = accent
            border_opacity = 0.80
            shadow_color = "#000000"
            shadow_opacity = 0.12
    elif style == "glassmorphism":
        # Translucent glassmorphism with accent frosted border
        if is_dark:
            top = "#202533"
            bottom = "#141722"
            border = accent
            border_opacity = 0.70
            shadow_color = "#000000"
            shadow_opacity = 0.40
        else:
            top = "#ffffff"
            bottom = "#eef2f7"
            border = accent
            border_opacity = 0.65
            shadow_color = "#000000"
            shadow_opacity = 0.14
    elif style == "minimal":
        # Minimalist neutral plate with subtle border
        if is_dark:
            top = "#222630"
            bottom = "#191c24"
            border = "#323846"
            border_opacity = 0.90
            shadow_color = "#000000"
            shadow_opacity = 0.30
        else:
            top = "#ffffff"
            bottom = "#f2f4f8"
            border = "#d8dde6"
            border_opacity = 0.85
            shadow_color = "#000000"
            shadow_opacity = 0.10
    else:  # Default: 'accent_ring' (Standard Material)
        # Neutral dark/light surface plate with crisp accent border ring
        if is_dark:
            top = "#222630"
            bottom = "#171a22"
            border = accent
            border_opacity = 0.95
            shadow_color = "#000000"
            shadow_opacity = 0.35
        else:
            top = "#ffffff"
            bottom = "#edf1f6"
            border = accent
            border_opacity = 0.90
            shadow_color = "#000000"
            shadow_opacity = 0.12

    return {
        "mode": mode,
        "style": style,
        "accent": accent,
        "bg_top": top,
        "bg_bottom": bottom,
        "border_color": border,
        "border_opacity": border_opacity,
        "border_width": 1.4,
        "shadow_color": shadow_color,
        "shadow_opacity": shadow_opacity,
        "shadow_dy": 1.5,
        "shadow_blur": 1.5
    }
