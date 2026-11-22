"""
Theme builder that compiles and packages full KDE Plasma icon themes.
Supports standard system themes, hicolor themes, and user custom icons in ~/.local/share/icons.
"""

import os
import re
import shutil
import subprocess
import concurrent.futures
from .shapes import get_shape
from .colors import get_style_palette, detect_kde_accent_color, detect_kde_theme_mode
from .svg_processor import process_icon

EXCLUDED_EXACT_NAMES = {
    "go", "system", "audio", "video", "multimedia", "brightness",
    "preferences", "settings", "dialog", "edit", "view", "help",
    "window", "process", "network", "security", "notification", "notifications",
    "camera", "microphone", "input", "output", "display", "power", "battery",
    "trash", "indicator", "tray", "symbolic", "next", "previous", "forward",
    "back", "up", "down", "user", "folder", "document", "text", "empty",
    "checkmark", "contrast", "bluetooth", "lock", "wifi", "hotspot",
    "systemsettings", "gnome-settings"
}

EXCLUDED_PREFIXES = (
    "system-", "preferences-", "dialog-", "view-", "edit-", "document-",
    "folder-", "user-", "media-", "audio-", "video-", "camera-",
    "microphone-", "network-", "battery-", "brightness", "kdeconnect",
    "redshift", "indicator-", "tray-", "status-", "action-", "arrow-",
    "input-", "filename-", "help-", "emblem-", "list-", "checkmark-",
    "contrast-", "notifications-", "notification-"
)

EXCLUDED_SUBSTRINGS = (
    "-symbolic", "-tray", "indicator", "systray", "-status-", "-symbolic-rtl"
)

def is_excluded_icon(fname: str) -> bool:
    """Returns True if the icon is a system action/status/indicator that should NOT be shaped."""
    base = os.path.splitext(fname)[0].lower()
    if base in EXCLUDED_EXACT_NAMES:
        return True
    if any(base.startswith(p) for p in EXCLUDED_PREFIXES):
        return True
    if any(s in base for s in EXCLUDED_SUBSTRINGS):
        return True
    return False

def get_installed_base_themes() -> list[str]:
    """Returns available base icon themes on the system."""
    search_dirs = ["/usr/share/icons", os.path.expanduser("~/.local/share/icons")]
    themes = []
    for d in search_dirs:
        if os.path.exists(d):
            for entry in os.listdir(d):
                p = os.path.join(d, entry)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, "index.theme")):
                    if entry not in themes and not entry.startswith("KdeShape-"):
                        themes.append(entry)
    return themes

def locate_base_apps_dir(base_theme: str = "Papirus") -> str:
    """Finds the primary apps directory for the chosen base theme."""
    candidates = [
        os.path.expanduser(f"~/.local/share/icons/{base_theme}/48x48/apps"),
        os.path.expanduser(f"~/.local/share/icons/{base_theme}/apps/48"),
        f"/usr/share/icons/{base_theme}/48x48/apps",
        f"/usr/share/icons/{base_theme}/apps/48",
        f"/usr/share/icons/{base_theme}/apps/scalable",
        f"/usr/share/icons/{base_theme}/scalable/apps",
        os.path.expanduser("~/.local/share/icons/Papirus/48x48/apps"),
        os.path.expanduser("~/.local/share/icons/Papirus-Dark/48x48/apps"),
        os.path.expanduser("~/.local/share/icons/Papirus-Light/48x48/apps"),
        "/usr/share/icons/breeze/apps/48",
        "/usr/share/icons/breeze-dark/apps/48",
        "/usr/share/icons/hicolor/scalable/apps",
        "/usr/share/icons/hicolor/48x48/apps"
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    return None

def find_custom_and_hicolor_icons() -> dict[str, str]:
    """
    Collects custom application icons from ~/.local/share/icons/hicolor, ~/.var/app (Chrome/Flatpak),
    and system hicolor locations to ensure custom app icons are shaped.
    Returns mapping of {base_filename_with_ext: full_file_path}.
    """
    search_dirs = [
        os.path.expanduser("~/.local/share/icons/hicolor"),
        os.path.expanduser("~/.var/app/com.google.Chrome/data/icons/hicolor"),
        os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor"),
        "/var/lib/flatpak/exports/share/icons/hicolor",
        "/usr/share/icons/hicolor"
    ]

    found_icons = {}
    for base in search_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            # Never scan inside generated KdeShape themes or base themes
            if any(x in root for x in ["KdeShape", "Papirus", "breeze"]):
                continue
            # Only focus on apps directories
            if "apps" not in root and root != base:
                continue
            for f in files:
                if f.endswith((".svg", ".svgz", ".png")):
                    if is_excluded_icon(f):
                        continue
                    name = os.path.splitext(f)[0]
                    # Prefer SVG over PNG, and higher resolution PNGs if multiple exist
                    if name not in found_icons:
                        found_icons[name] = (f, os.path.join(root, f))
                    elif f.endswith(".svg"):
                        found_icons[name] = (f, os.path.join(root, f))
    
    # Also inspect ~/.local/share/applications/*.desktop for direct icon paths
    app_dir = os.path.expanduser("~/.local/share/applications")
    if os.path.exists(app_dir):
        for f in os.listdir(app_dir):
            if f.endswith(".desktop"):
                desktop_path = os.path.join(app_dir, f)
                try:
                    with open(desktop_path, "r", encoding="utf-8", errors="ignore") as fp:
                        for line in fp:
                            line = line.strip()
                            if line.startswith("Icon=") and "/" in line:
                                icon_path = line.split("=", 1)[1].strip()
                                if os.path.exists(icon_path) and icon_path.endswith((".png", ".svg", ".svgz")):
                                    base_name = os.path.splitext(os.path.basename(icon_path))[0]
                                    found_icons[base_name] = (os.path.basename(icon_path), icon_path)
                except Exception:
                    pass

    return {fname: fpath for _, (fname, fpath) in found_icons.items()}

def harvest_all_desktop_icons(base_theme: str = "Papirus") -> dict[str, str]:
    """
    Scans all application desktop files on the system (~/.local/share/applications,
    /usr/share/applications, /var/lib/flatpak/exports, ~/.local/share/flatpak/exports)
    and resolves their icons from the base theme (apps, actions, devices, categories, places),
    hicolor, or pixmaps.
    This guarantees that EVERY desktop application in the launcher/drawer has a shaped icon.
    """
    theme_search_roots = [
        os.path.expanduser(f"~/.local/share/icons/{base_theme}"),
        f"/usr/share/icons/{base_theme}",
        "/usr/share/pixmaps",
        os.path.expanduser("~/.local/share/icons/hicolor"),
        "/usr/share/icons/hicolor",
        os.path.expanduser("~/.var/app/com.google.Chrome/data/icons/hicolor")
    ]

    icon_index = {}
    for root in theme_search_roots:
        if not os.path.exists(root):
            continue
        for r, _, files in os.walk(root):
            if any(x in r for x in ["KdeShape", "breeze"]):
                continue
            for f in files:
                if f.endswith((".svg", ".svgz", ".png")):
                    b = os.path.splitext(f)[0]
                    if b not in icon_index:
                        icon_index[b] = (f, os.path.join(r, f))
                    elif f.endswith(".svg") and not icon_index[b][0].endswith(".svg"):
                        icon_index[b] = (f, os.path.join(r, f))
                    elif f.endswith(".png") and any(res in r for res in ["512", "256"]):
                        icon_index[b] = (f, os.path.join(r, f))

    app_dirs = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications",
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications")
    ]

    harvested = {}
    for ad in app_dirs:
        if not os.path.exists(ad):
            continue
        for f in os.listdir(ad):
            if not f.endswith(".desktop"):
                continue
            p = os.path.join(ad, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    for line in fp:
                        if line.startswith("Icon="):
                            val = line.split("=", 1)[1].strip()
                            if not val or is_excluded_icon(val):
                                continue
                            b = os.path.splitext(os.path.basename(val))[0]
                            if b in harvested:
                                continue

                            if os.path.isabs(val) and os.path.exists(val) and val.endswith((".svg", ".svgz", ".png")):
                                harvested[b] = (os.path.basename(val), val)
                            elif b in icon_index:
                                harvested[b] = icon_index[b]
            except Exception:
                pass

    return {fname: fpath for _, (fname, fpath) in harvested.items()}

def _process_single_icon(args):
    src_file, fname, apps_48_dir, shape, palette, scale = args
    try:
        shaped_svg = process_icon(src_file, shape, palette, custom_scale=scale)
        out_name = os.path.splitext(fname)[0] + ".svg"
        out_path = os.path.join(apps_48_dir, out_name)
        with open(out_path, "w", encoding="utf-8") as f_out:
            f_out.write(shaped_svg)
        return True, fname, out_name
    except Exception:
        return False, fname, None

def update_local_desktop_files(revert: bool = False):
    """
    Updates ~/.local/share/applications/*.desktop files that use hardcoded absolute Icon= paths
    so they reference theme icon names instead (enabling theme shaping), saving original in X-Original-Icon.
    If revert is True, restores original absolute paths.
    """
    app_dir = os.path.expanduser("~/.local/share/applications")
    if not os.path.exists(app_dir):
        return

    for f in os.listdir(app_dir):
        if not f.endswith(".desktop"):
            continue
        p = os.path.join(app_dir, f)
        try:
            with open(p, "r", encoding="utf-8") as fp:
                lines = fp.readlines()
            modified = False
            new_lines = []
            if revert:
                # Restore original
                orig_icon = None
                for line in lines:
                    if line.startswith("X-Original-Icon="):
                        orig_icon = line.split("=", 1)[1].strip()
                if orig_icon:
                    for line in lines:
                        if line.startswith("Icon="):
                            new_lines.append(f"Icon={orig_icon}\n")
                            modified = True
                        elif not line.startswith("X-Original-Icon="):
                            new_lines.append(line)
            else:
                # Replace absolute path with icon name
                for line in lines:
                    if line.startswith("Icon=") and "/" in line:
                        full_icon = line.split("=", 1)[1].strip()
                        icon_base = os.path.splitext(os.path.basename(full_icon))[0]
                        new_lines.append(f"X-Original-Icon={full_icon}\n")
                        new_lines.append(f"Icon={icon_base}\n")
                        modified = True
                    else:
                        new_lines.append(line)

            if modified:
                with open(p, "w", encoding="utf-8") as fp:
                    fp.writelines(new_lines)
        except Exception:
            pass

def build_icon_theme(
    theme_name: str = "KdeShape",
    shape: str = "circle",
    style: str = "accent_ring",
    mode: str = "auto",
    accent: str = "auto",
    base_theme: str = "breeze",
    output_dir: str = None,
    scale: float = None,
    include_hicolor: bool = True
) -> dict:
    """
    Builds a complete Material Shape icon theme for KDE Plasma.
    """
    if mode == "auto":
        mode = detect_kde_theme_mode()
    if accent == "auto":
        accent = detect_kde_accent_color()

    palette = get_style_palette(style=style, mode=mode, accent=accent)
    shape_info = get_shape(shape)

    if output_dir:
        theme_root = os.path.join(output_dir, theme_name)
    else:
        theme_root = os.path.expanduser(f"~/.local/share/icons/{theme_name}")

    apps_48_dir = os.path.join(theme_root, "apps", "48")
    apps_scalable_dir = os.path.join(theme_root, "apps", "scalable")

    if os.path.exists(theme_root):
        shutil.rmtree(theme_root)
    os.makedirs(apps_48_dir, exist_ok=True)

    # 1. Write index.theme with complete inheritance chain
    inherits_chain = [base_theme]
    for fallback in ["Papirus", "Papirus-Dark", "breeze", "breeze-dark", "hicolor"]:
        if fallback not in inherits_chain:
            inherits_chain.append(fallback)
    inherits_str = ",".join(inherits_chain)

    index_theme_content = f"""[Icon Theme]
Name={theme_name}
Comment=Material {shape_info['name']} Icons ({mode.capitalize()} mode, {style.replace('_', ' ').title()})
Inherits={inherits_str}
DisplayDepth=32
Example=accessories-calculator

Directories=apps/48,apps/scalable

[apps/48]
Size=48
Context=Applications
Type=Fixed

[apps/scalable]
Size=48
MinSize=16
MaxSize=256
Context=Applications
Type=Scalable
"""
    with open(os.path.join(theme_root, "index.theme"), "w", encoding="utf-8") as f:
        f.write(index_theme_content)

    # 2. Gather source icons from base theme
    base_apps = locate_base_apps_dir(base_theme)
    if not base_apps:
        raise FileNotFoundError(f"Could not locate base app icons for theme '{base_theme}'")

    processed_count = 0
    symlink_count = 0
    skipped_count = 0

    seen_files = set()
    pending_symlinks = []
    tasks = []

    # First: Primary base theme apps
    for fname in os.listdir(base_apps):
        if is_excluded_icon(fname):
            continue

        src_file = os.path.join(base_apps, fname)
        dst_file = os.path.join(apps_48_dir, fname)

        if os.path.islink(src_file):
            link_target = os.readlink(src_file)
            if not is_excluded_icon(link_target):
                pending_symlinks.append((fname, link_target, dst_file, src_file))
                seen_files.add(fname)
            continue

        if fname.endswith((".svg", ".svgz", ".png")):
            tasks.append((src_file, fname, apps_48_dir, shape, palette, scale))
            seen_files.add(fname)

    # Second: Custom and hicolor icons (antigravity, Chrome web apps, Flatpak apps, etc.)
    custom_icons = find_custom_and_hicolor_icons()
    for fname, src_file in custom_icons.items():
        if fname in seen_files or is_excluded_icon(fname):
            continue
        base_name = os.path.splitext(fname)[0]
        if f"{base_name}.svg" in seen_files:
            continue

        dst_file = os.path.join(apps_48_dir, fname)
        if os.path.islink(src_file):
            link_target = os.readlink(src_file)
            if not is_excluded_icon(link_target):
                pending_symlinks.append((fname, link_target, dst_file, src_file))
                seen_files.add(fname)
            continue

        tasks.append((src_file, fname, apps_48_dir, shape, palette, scale))
        seen_files.add(fname)

    # Third: Universal desktop application icons (ensures every desktop app on the system is shaped)
    desktop_icons = harvest_all_desktop_icons(base_theme)
    for fname, src_file in desktop_icons.items():
        if fname in seen_files or is_excluded_icon(fname):
            continue
        base_name = os.path.splitext(fname)[0]
        if f"{base_name}.svg" in seen_files:
            continue

        dst_file = os.path.join(apps_48_dir, fname)
        if os.path.islink(src_file):
            link_target = os.readlink(src_file)
            if not is_excluded_icon(link_target):
                pending_symlinks.append((fname, link_target, dst_file, src_file))
                seen_files.add(fname)
            continue

        tasks.append((src_file, fname, apps_48_dir, shape, palette, scale))
        seen_files.add(fname)

    # Process all icons concurrently across threads for rapid generation (< 1-2 seconds)
    max_workers = min(16, (os.cpu_count() or 4) * 2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for success, fname, out_name in executor.map(_process_single_icon, tasks):
            if success:
                if out_name:
                    seen_files.add(out_name)
                processed_count += 1
            else:
                skipped_count += 1

    # Resolve pending symlinks
    for fname, target, dst_file, src_file in pending_symlinks:
        if is_excluded_icon(fname) or is_excluded_icon(target):
            continue
        target_clean = os.path.splitext(target)[0] + ".svg" if not target.endswith(".svg") else target
        dst_clean = os.path.splitext(dst_file)[0] + ".svg" if not dst_file.endswith(".svg") else dst_file
        target_name = os.path.basename(target_clean)

        if os.path.exists(dst_clean):
            continue

        if os.path.exists(os.path.join(apps_48_dir, target_name)):
            try:
                os.symlink(target_name, dst_clean)
                symlink_count += 1
            except Exception:
                pass
        else:
            try:
                real_src = os.path.realpath(src_file)
                if os.path.exists(real_src) and real_src.endswith((".svg", ".svgz", ".png")):
                    shaped_svg = process_icon(real_src, shape, palette, custom_scale=scale)
                    with open(dst_clean, "w", encoding="utf-8") as f_out:
                        f_out.write(shaped_svg)
                    processed_count += 1
            except Exception:
                pass

    # 3. Create scalable symlink to apps/48
    if not os.path.exists(apps_scalable_dir):
        try:
            os.symlink("48", apps_scalable_dir)
        except Exception:
            os.makedirs(apps_scalable_dir, exist_ok=True)

    # 4. Update GTK icon cache if tool exists
    gtk_cache_tool = shutil.which("gtk-update-icon-cache")
    if gtk_cache_tool:
        try:
            subprocess.run([gtk_cache_tool, "-f", "-t", theme_root], capture_output=True, timeout=5)
        except Exception:
            pass

    # 5. Enable desktop files to use icon theme
    update_local_desktop_files(revert=False)

    return {
        "theme_name": theme_name,
        "theme_path": theme_root,
        "shape": shape,
        "style": style,
        "mode": mode,
        "accent": accent,
        "processed_icons": processed_count,
        "symlinks": symlink_count,
        "skipped": skipped_count
    }

def apply_icon_theme(theme_name: str) -> bool:
    """Sets the active icon theme in KDE Plasma 6."""
    kwriteconfig = shutil.which("kwriteconfig6") or shutil.which("kwriteconfig5")
    if kwriteconfig:
        ret = subprocess.run([
            kwriteconfig,
            "--file", "kdeglobals",
            "--group", "Icons",
            "--key", "Theme",
            theme_name
        ], capture_output=True)

        icon_cache = os.path.expanduser("~/.cache/icon-cache.kcache")
        if os.path.exists(icon_cache):
            try:
                os.remove(icon_cache)
            except Exception:
                pass

        kbuildsycoca = shutil.which("kbuildsycoca6") or shutil.which("kbuildsycoca5")
        if kbuildsycoca:
            subprocess.run([kbuildsycoca, "--noincremental"], capture_output=True)

        try:
            import dbus
            bus = dbus.SessionBus()
            for path in ['/', '/KIconLoader']:
                try:
                    msg = dbus.lowlevel.SignalMessage(path, 'org.kde.KIconLoader', 'iconChanged')
                    msg.append(0, signature='i')
                    bus.send_message(msg)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            subprocess.run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], capture_output=True, timeout=2)
        except Exception:
            pass

        return (ret.returncode == 0)
    return False
