"""
KDE Shape Icons Generator Package
"""

from .shapes import SHAPES, get_shape, list_shapes
from .colors import PRESET_COLORS, detect_kde_accent_color, detect_kde_theme_mode, get_style_palette
from .svg_processor import process_icon
from .theme_builder import build_icon_theme, apply_icon_theme, get_installed_base_themes

__all__ = [
    "SHAPES",
    "get_shape",
    "list_shapes",
    "PRESET_COLORS",
    "detect_kde_accent_color",
    "detect_kde_theme_mode",
    "get_style_palette",
    "process_icon",
    "build_icon_theme",
    "apply_icon_theme",
    "get_installed_base_themes"
]

