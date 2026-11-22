#!/usr/bin/env python3
"""
KDE Shape Icons — CLI tool and theme generator for KDE Plasma 6.
Enables Material Design circles, squircles, and geometric shapes with dynamic dark/light accent styling.
"""

import sys
import os
import json
import argparse

# Add current folder to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from generator.shapes import list_shapes, SHAPES
from generator.colors import (
    PRESET_COLORS,
    detect_kde_accent_color,
    detect_kde_theme_mode,
    get_style_palette
)
from generator.theme_builder import (
    build_icon_theme,
    apply_icon_theme,
    get_installed_base_themes
)

CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

def load_config() -> dict:
    defaults = {
        "theme_name": "KdeShape",
        "shape": "circle",
        "style": "accent_ring",
        "mode": "auto",
        "accent": "auto",
        "base_theme": "Papirus",
        "scale": None
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
        except Exception:
            pass
    return defaults

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")

def cmd_list(args):
    print("=" * 64)
    print("  KDE Plasma Environment & Customization Info")
    print("=" * 64)
    detected_accent = detect_kde_accent_color()
    detected_mode = detect_kde_theme_mode()
    print(f"  • Current KDE Theme Mode   : {detected_mode.upper()}")
    print(f"  • Detected KDE Accent Color: {detected_accent}")
    print("\nAvailable Shapes:")
    for k, v in list_shapes().items():
        print(f"  • {k:15}: {v['name']} — {v['description']}")

    print("\nAvailable Styles:")
    styles = {
        "accent_ring": "Neutral dark/light surface plate with crisp accent border ring (Material You style)",
        "accent_tint": "Surface plate subtly tinted with the accent color hue (12-15% tint)",
        "accent_filled": "Vibrant solid accent color background plate",
        "glassmorphism": "Translucent frosted surface with accent glow (glass look)",
        "minimal": "Minimalist monochrome surface with soft subtle border"
    }
    for k, v in styles.items():
        print(f"  • {k:15}: {v}")

    print("\nPreset Accent Colors:")
    for k, v in PRESET_COLORS.items():
        print(f"  • {k:15}: {v}")

    base_themes = get_installed_base_themes()
    print(f"\nInstalled Base Themes: {', '.join(base_themes[:6])}")
    print("=" * 64)

def cmd_generate(args):
    cfg = load_config()
    
    shape = args.shape or cfg.get("shape", "circle")
    style = args.style or cfg.get("style", "accent_ring")
    mode = args.mode or cfg.get("mode", "auto")
    accent = args.accent or cfg.get("accent", "auto")
    base_theme = args.base_theme or cfg.get("base_theme", "Papirus")
    
    # Capitalize shape name for theme naming
    shape_title = SHAPES.get(shape, {}).get("name", shape.title()).replace(" ", "")
    theme_name = args.name or f"KdeShape-{shape_title}"
    
    print(f"==> Generating Material Shape Icon Theme:")
    print(f"    • Theme Name : {theme_name}")
    print(f"    • Shape      : {shape}")
    print(f"    • Style      : {style}")
    print(f"    • Mode       : {mode}")
    print(f"    • Accent     : {accent}")
    print(f"    • Base Theme : {base_theme}")
    
    try:
        res = build_icon_theme(
            theme_name=theme_name,
            shape=shape,
            style=style,
            mode=mode,
            accent=accent,
            base_theme=base_theme,
            output_dir=args.output_dir
        )
        print(f"\n✅ Theme generated successfully at:")
        print(f"   {res['theme_path']}")
        print(f"   • Icons generated: {res['processed_icons']}")
        print(f"   • Symlinks linked: {res['symlinks']}")
        
        # Save last used settings
        cfg.update({
            "theme_name": theme_name,
            "shape": shape,
            "style": style,
            "mode": mode,
            "accent": accent,
            "base_theme": base_theme
        })
        save_config(cfg)
        
        if args.apply:
            print("\n==> Applying theme to KDE Plasma...")
            if apply_icon_theme(theme_name):
                print(f"✅ Active icon theme set to '{theme_name}'!")
            else:
                print(f"⚠️ Could not automatically set theme via kwriteconfig6.")
        else:
            print(f"\nTo apply this theme in KDE Plasma:")
            print(f"  python3 shape_icons.py apply --name {theme_name}")
            print(f"Or go to System Settings -> Colors & Themes -> Icons and select '{theme_name}'.")
            
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_apply(args):
    cfg = load_config()
    theme_name = args.name or cfg.get("theme_name", "KdeShape-Circle")
    print(f"==> Applying icon theme '{theme_name}' to KDE Plasma...")
    if apply_icon_theme(theme_name):
        print(f"✅ Success! Icon theme '{theme_name}' applied.")
    else:
        print(f"❌ Failed to apply icon theme '{theme_name}'.")

def cmd_preview(args):
    preview_file = os.path.join(SCRIPT_DIR, "preview", "index.html")
    if os.path.exists(preview_file):
        print(f"==> Interactive HTML preview is available at:")
        print(f"    file://{preview_file}")
        print("\nYou can open this file in your browser to preview all shapes and colors live!")
    else:
        print("❌ Preview file not found.")

def main():
    parser = argparse.ArgumentParser(
        description="KDE Shape Icons — Material Shapes & Dynamic Accent Shading for KDE Plasma 6"
    )
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List available shapes, styles, and detected KDE settings")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate a customized shaped icon theme")
    gen_parser.add_argument("--shape", choices=list(SHAPES.keys()), help="Shape (circle, squircle, rounded_square, hexagon, pebble, octagon)")
    gen_parser.add_argument("--style", choices=["accent_ring", "accent_tint", "accent_filled", "glassmorphism", "minimal"], help="Shading style")
    gen_parser.add_argument("--mode", choices=["auto", "dark", "light"], default="auto", help="Color theme mode (default: auto, follows KDE)")
    gen_parser.add_argument("--accent", help="Hex color code (e.g. #2cbd9e) or 'auto' to read from KDE")
    gen_parser.add_argument("--name", help="Theme name (default: KdeShape-<Shape>)")
    gen_parser.add_argument("--base-theme", help="Base icon theme to inherit from (default: breeze)")
    gen_parser.add_argument("--output-dir", help="Custom output directory (default: ~/.local/share/icons)")
    gen_parser.add_argument("--apply", action="store_true", help="Automatically apply the theme to KDE after generation")

    # apply
    apply_parser = subparsers.add_parser("apply", help="Apply a generated icon theme to KDE")
    apply_parser.add_argument("--name", help="Theme name to apply")

    # preview
    subparsers.add_parser("preview", help="Show path to interactive visual preview gallery")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "apply":
        cmd_apply(args)
    elif args.command == "preview":
        cmd_preview(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
