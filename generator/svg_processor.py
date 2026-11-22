"""
SVG processor that wraps standard system icons inside Material shapes.
Supports SVG, SVGZ, and PNG source icons.
Compatible with Qt SVG Tiny 1.2 (no nested <svg> elements).
"""

import os
import re
import gzip
import base64
import math
import io
try:
    import cairo
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False
from .shapes import get_shape

def parse_viewbox(content: str) -> tuple[float, float, float, float]:
    """Parses (min_x, min_y, width, height) from SVG viewBox or width/height attributes."""
    vb_match = re.search(r'viewBox=[\"\']([^\"\']+)[\"\']', content)
    if vb_match:
        parts = re.split(r'[\s,]+', vb_match.group(1).strip())
        if len(parts) >= 4:
            try:
                return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            except ValueError:
                pass

    w_match = re.search(r'width=[\"\']([0-9\.]+)px?[\"\']', content)
    h_match = re.search(r'height=[\"\']([0-9\.]+)px?[\"\']', content)
    w = float(w_match.group(1)) if w_match else 48.0
    h = float(h_match.group(1)) if h_match else 48.0
    return 0.0, 0.0, w, h

def extract_viewbox(content: str) -> str:
    """Legacy helper returning viewBox string."""
    min_x, min_y, w, h = parse_viewbox(content)
    return f"{min_x} {min_y} {w} {h}"

def detect_icon_shape(content: str) -> str:
    """
    Detects whether an SVG icon's base plate is 'circle', 'square', or 'freeform'.
    """
    # 1. Circle tag check (r >= 15 or rx/ry >= 15)
    for m in re.finditer(r'<circle[^>]+r=[\"\']([0-9\.]+)[\"\']', content):
        if float(m.group(1)) >= 15.0:
            return "circle"
    for m in re.finditer(r'<ellipse[^>]+rx=[\"\']([0-9\.]+)[\"\'][^>]+ry=[\"\']([0-9\.]+)[\"\']', content):
        if float(m.group(1)) >= 15.0 and float(m.group(2)) >= 15.0:
            return "circle"

    # 2. Path-based circular arc check (A or a with radius 16..26)
    if re.search(r'[aA]\s*(?:1[6-9]|2[0-6])[\s,]+(?:1[6-9]|2[0-6])', content):
        return "circle"

    # 3. Path-based circular boundary check (Bezier curves spanning cardinal circle points, e.g. Firefox)
    if re.search(r'(?:[cC]\s*[^zZ]*\b(?:24|23\.\d+|24\.\d+)\s*,\s*4[45]\b)|(?:\b4[45]\s*,\s*(?:24|23\.\d+|24\.\d+)\b)', content):
        return "circle"

    # 4. Rect tag check (width and height >= 26)
    for m in re.finditer(r'<rect[^>]+width=[\"\']([0-9\.]+)[\"\'][^>]+height=[\"\']([0-9\.]+)[\"\']', content):
        if float(m.group(1)) >= 26.0 and float(m.group(2)) >= 26.0:
            return "square"

    # 5. Path-based rect/squircle check with H/h and V/v lines >= 26
    if re.search(r'[hH]\s*(?:2[6-9]|3[0-9]|4[0-4])\b.*[vV]\s*(?:2[6-9]|3[0-9]|4[0-4])\b', content, re.DOTALL):
        return "square"
    if re.search(r'[vV]\s*(?:2[6-9]|3[0-9]|4[0-4])\b.*[hH]\s*(?:2[6-9]|3[0-9]|4[0-4])\b', content, re.DOTALL):
        return "square"

    return "freeform"

def compute_adaptive_scale(shape_name: str, detected_shape: str) -> float:
    """
    Computes adaptive scale factor so that every application emblem is centered
    and framed cleanly within the theme shape plate and border ring.
    - Square icons inside Circle: diagonal fits inside circle diameter (scale ~0.63)
      so four corners never touch or poke past the border.
    - Circle/Freeform icons: balanced scale (~0.74 - 0.76) so the background plate
      and border ring are consistently visible across all applications.
    """
    sel = shape_name.lower().replace("-", "_").strip() if shape_name else "circle"

    if sel == "circle":
        if detected_shape == "circle":
            return 0.76   # Circular emblem framed with clean margin showing the theme plate
        elif detected_shape == "square":
            return 0.63   # Diagonal fits safely inside circle diameter (48 * 0.63 * sqrt(2) ~ 42.7)
        else:
            return 0.72   # Freeform glyph centered cleanly

    elif sel in ("squircle", "rounded_square"):
        if detected_shape in ("square", "squircle"):
            return 0.78
        elif detected_shape == "circle":
            return 0.78
        else:
            return 0.72

    elif sel in ("hexagon", "octagon"):
        return 0.66

    else:  # pebble or other
        return 0.68

def extract_namespaces(content: str) -> dict[str, str]:
    """Collects and deduplicates all xmlns namespace definitions from source SVG."""
    namespaces = {
        "xmlns": "http://www.w3.org/2000/svg",
        "xmlns:xlink": "http://www.w3.org/1999/xlink"
    }
    svg_match = re.search(r'<svg([^>]*)>', content, flags=re.IGNORECASE)
    if svg_match:
        for m in re.finditer(r'(xmlns(?::[a-zA-Z0-9_-]+)?)=[\"\']([^\"\']+)[\"\']', svg_match.group(1)):
            namespaces[m.group(1)] = m.group(2)
    return namespaces

def wrap_svg_icon(source_path: str, shape_name: str, palette: dict, custom_scale: float = None) -> str:
    """Transforms a vector SVG/SVGZ icon into a Material shaped icon compatible with Qt SVG."""
    shape_info = get_shape(shape_name)

    # Read source data
    with open(source_path, "rb") as f:
        data = f.read()
    if source_path.endswith(".svgz"):
        try:
            data = gzip.decompress(data)
        except Exception:
            pass
    raw_content = data.decode("utf-8", errors="ignore")

    # Extract viewBox & namespaces
    min_x, min_y, vb_w, vb_h = parse_viewbox(raw_content)
    namespaces = extract_namespaces(raw_content)
    ns_str = " ".join(f'{k}="{v}"' for k, v in namespaces.items())

    # Clean up inner XML (remove XML decl, doctype, comments, metadata)
    cleaned = re.sub(r'<\?xml[^>]*\?>', '', raw_content, flags=re.IGNORECASE)
    cleaned = re.sub(r'<!DOCTYPE[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<metadata>.*?</metadata>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Extract inner content between the first <svg ...> and the last </svg>
    svg_open_match = re.search(r'<svg[^>]*>', cleaned, flags=re.IGNORECASE)
    if svg_open_match:
        inner = cleaned[svg_open_match.end():]
        svg_close_idx = inner.rfind('</svg>')
        if svg_close_idx != -1:
            inner = inner[:svg_close_idx]
    else:
        inner = cleaned

    # Compute sizing & offsets for Qt SVG Tiny 1.2 compatibility
    # Qt's QSvgRenderer explicitly drops nested <svg> elements.
    # We instead wrap the inner glyphs inside a <g transform="translate(offset_x, offset_y) scale(scale_factor)">.
    max_dim = max(vb_w, vb_h) if max(vb_w, vb_h) > 0 else 48.0
    detected_shape = detect_icon_shape(raw_content)
    scale = custom_scale if custom_scale is not None else compute_adaptive_scale(shape_name, detected_shape)

    target_size = 48.0 * scale
    scale_factor = target_size / max_dim
    scaled_w = vb_w * scale_factor
    scaled_h = vb_h * scale_factor

    offset_x = (48.0 - scaled_w) / 2.0 - (min_x * scale_factor)
    offset_y = (48.0 - scaled_h) / 2.0 - (min_y * scale_factor)

    # Generate background shape element
    sw = palette.get("border_width", 1.4)
    shape_element = shape_info["svg"](
        bg="url(#kde-shape-bg-grad)",
        stroke="url(#kde-shape-border-stroke)",
        sw=sw,
        filter_id="kde-shape-shadow"
    )

    overlay_border = shape_info["svg"](
        bg="none",
        stroke="url(#kde-shape-border-stroke)",
        sw=sw,
        filter_id=""
    )
    overlay_border = re.sub(r'filter="[^"]*"', '', overlay_border)

    # Generate SVG markup
    border_color = palette["border_color"]
    border_opacity = palette.get("border_opacity", 1.0)
    bg_top = palette["bg_top"]
    bg_bottom = palette["bg_bottom"]
    shadow_color = palette.get("shadow_color", "#000000")
    shadow_opacity = palette.get("shadow_opacity", 0.35)
    shadow_dy = palette.get("shadow_dy", 1.5)
    shadow_blur = palette.get("shadow_blur", 1.5)

    svg = f'''<svg {ns_str} width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <!-- Material Elevation Shadow -->
    <filter id="kde-shape-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="{shadow_dy}" stdDeviation="{shadow_blur}" flood-color="{shadow_color}" flood-opacity="{shadow_opacity}"/>
    </filter>
    <!-- Background Surface Gradient -->
    <linearGradient id="kde-shape-bg-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bg_top}"/>
      <stop offset="100%" stop-color="{bg_bottom}"/>
    </linearGradient>
    <!-- Adaptive Border Stroke -->
    <linearGradient id="kde-shape-border-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{border_color}" stop-opacity="{border_opacity}"/>
      <stop offset="100%" stop-color="{border_color}" stop-opacity="{border_opacity * 0.85:.2f}"/>
    </linearGradient>
  </defs>

  <!-- Background Shape Plate -->
  {shape_element}

  <!-- Centered Scaled Inner Icon Glyph (Qt SVG Tiny 1.2 compatible) -->
  <g transform="translate({offset_x:.3f}, {offset_y:.3f}) scale({scale_factor:.4f})">
    {inner}
  </g>

  <!-- Overlay Border Ring -->
  {overlay_border}
</svg>'''
    return svg

def mask_and_composite_png(source_path: str, shape_name: str, custom_scale: float = None) -> tuple[str, float, float, float]:
    """
    Loads PNG with PyCairo.
    Detects if PNG has opaque corners (card-style icon like ZEE5).
    If opaque corners, clips it to the chosen vector shape boundary with subpixel anti-aliasing.
    If transparent corners (emblem like Gemini, Gmail, Netflix), scales and centers it cleanly.
    Returns (base64_png_data, x_offset, y_offset, size).
    """
    sel = shape_name.lower().replace("-", "_").strip() if shape_name else "circle"

    if not HAS_CAIRO:
        with open(source_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        scale = custom_scale if custom_scale is not None else (0.63 if sel == "circle" else 0.76)
        size = round(48.0 * scale, 2)
        offset = round((48.0 - size) / 2.0, 2)
        return b64, offset, offset, size

    try:
        src_surf = cairo.ImageSurface.create_from_png(source_path)
    except Exception:
        with open(source_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        scale = 0.63
        size = round(48.0 * scale, 2)
        offset = round((48.0 - size) / 2.0, 2)
        return b64, offset, offset, size

    src_w = src_surf.get_width()
    src_h = src_surf.get_height()
    buf = src_surf.get_data()

    # Check 4 corner pixels for opacity
    a_tl = buf[3]
    a_tr = buf[(src_w - 1) * 4 + 3]
    a_bl = buf[((src_h - 1) * src_w) * 4 + 3]
    a_br = buf[((src_h - 1) * src_w + (src_w - 1)) * 4 + 3]
    is_card = (a_tl > 30 and a_tr > 30 and a_bl > 30 and a_br > 30)

    # Use 96x96 canvas for crisp anti-aliased clipping
    canvas_dim = 96
    out_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, canvas_dim, canvas_dim)
    cr = cairo.Context(out_surf)
    cr.scale(canvas_dim / 48.0, canvas_dim / 48.0)

    if is_card:
        # Full-bleed square card icon (e.g. ZEE5):
        # Clip to shape boundary with smooth anti-aliased subpixel edges
        if sel == "circle":
            cr.arc(24, 24, 21.0, 0, 2 * math.pi)
            cr.close_path()
            cr.clip()
            img_size = 42.0
            img_x = 3.0
            img_y = 3.0
        elif sel == "squircle":
            cr.move_to(24, 3)
            cr.curve_to(34.5, 3, 41.5, 4.5, 43.5, 6.5)
            cr.curve_to(45.5, 8.5, 45, 15.5, 45, 24)
            cr.curve_to(45, 32.5, 45.5, 39.5, 43.5, 41.5)
            cr.curve_to(41.5, 43.5, 34.5, 45, 24, 45)
            cr.curve_to(13.5, 45, 6.5, 43.5, 4.5, 41.5)
            cr.curve_to(2.5, 39.5, 3, 32.5, 3, 24)
            cr.curve_to(3, 15.5, 2.5, 8.5, 4.5, 6.5)
            cr.curve_to(6.5, 4.5, 13.5, 3, 24, 3)
            cr.close_path()
            cr.clip()
            img_size = 42.0
            img_x = 3.0
            img_y = 3.0
        elif sel == "rounded_square":
            x, y, w, h, r = 3.5, 3.5, 41.0, 41.0, 10.5
            cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
            cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
            cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
            cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
            cr.close_path()
            cr.clip()
            img_size = 41.0
            img_x = 3.5
            img_y = 3.5
        elif sel == "hexagon":
            cr.move_to(24, 2.8)
            cr.line_to(42.4, 13.4)
            cr.line_to(42.4, 34.6)
            cr.line_to(24, 45.2)
            cr.line_to(5.6, 34.6)
            cr.line_to(5.6, 13.4)
            cr.close_path()
            cr.clip()
            img_size = 37.0
            img_x = 5.5
            img_y = 5.5
        elif sel == "octagon":
            cr.move_to(15.5, 2.8)
            cr.line_to(32.5, 2.8)
            cr.line_to(45.2, 15.5)
            cr.line_to(45.2, 32.5)
            cr.line_to(32.5, 45.2)
            cr.line_to(15.5, 45.2)
            cr.line_to(2.8, 32.5)
            cr.line_to(2.8, 15.5)
            cr.close_path()
            cr.clip()
            img_size = 42.0
            img_x = 3.0
            img_y = 3.0
        else:  # pebble
            cr.arc(24, 24, 21.0, 0, 2 * math.pi)
            cr.close_path()
            cr.clip()
            img_size = 42.0
            img_x = 3.0
            img_y = 3.0

        scale = img_size / max(src_w, src_h)
        cr.translate(img_x, img_y)
        cr.scale(scale, scale)
        cr.set_source_surface(src_surf, 0, 0)
        cr.paint()

        bio = io.BytesIO()
        out_surf.write_to_png(bio)
        b64 = base64.b64encode(bio.getvalue()).decode("ascii")
        return b64, 0.0, 0.0, 48.0

    else:
        # Floating transparent emblem (Gemini, Gmail, Netflix, WhatsApp)
        scale = custom_scale if custom_scale is not None else (0.74 if sel == "circle" else 0.78)
        inner_size = round(48.0 * scale, 2)
        offset = round((48.0 - inner_size) / 2.0, 2)
        with open(source_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return b64, offset, offset, inner_size

def wrap_png_icon(source_path: str, shape_name: str, palette: dict, custom_scale: float = None) -> str:
    """Wraps a raster PNG icon centered inside a vector Material shape."""
    shape_info = get_shape(shape_name)

    b64, offset_x, offset_y, inner_size = mask_and_composite_png(source_path, shape_name, custom_scale)

    sw = palette.get("border_width", 1.4)
    shape_element = shape_info["svg"](
        bg="url(#kde-shape-bg-grad)",
        stroke="url(#kde-shape-border-stroke)",
        sw=sw,
        filter_id="kde-shape-shadow"
    )

    border_color = palette["border_color"]
    border_opacity = palette.get("border_opacity", 1.0)
    bg_top = palette["bg_top"]
    bg_bottom = palette["bg_bottom"]
    shadow_color = palette.get("shadow_color", "#000000")
    shadow_opacity = palette.get("shadow_opacity", 0.35)
    shadow_dy = palette.get("shadow_dy", 1.5)
    shadow_blur = palette.get("shadow_blur", 1.5)

    overlay_border = shape_info["svg"](
        bg="none",
        stroke="url(#kde-shape-border-stroke)",
        sw=sw,
        filter_id=""
    )
    overlay_border = re.sub(r'filter="[^"]*"', '', overlay_border)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <filter id="kde-shape-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="{shadow_dy}" stdDeviation="{shadow_blur}" flood-color="{shadow_color}" flood-opacity="{shadow_opacity}"/>
    </filter>
    <linearGradient id="kde-shape-bg-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bg_top}"/>
      <stop offset="100%" stop-color="{bg_bottom}"/>
    </linearGradient>
    <linearGradient id="kde-shape-border-stroke" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{border_color}" stop-opacity="{border_opacity}"/>
      <stop offset="100%" stop-color="{border_color}" stop-opacity="{border_opacity * 0.85:.2f}"/>
    </linearGradient>
  </defs>

  <!-- Background Shape Plate -->
  {shape_element}

  <!-- Centered Inner PNG Glyph -->
  <image x="{offset_x}" y="{offset_y}" width="{inner_size}" height="{inner_size}" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{b64}" href="data:image/png;base64,{b64}"/>

  <!-- Overlay Border Ring -->
  {overlay_border}
</svg>'''
    return svg

def process_icon(source_path: str, shape_name: str, palette: dict, custom_scale: float = None) -> str:
    """Processes an icon file (SVG, SVGZ, or PNG) and returns shaped SVG markup."""
    lower = source_path.lower()
    if lower.endswith(".png"):
        return wrap_png_icon(source_path, shape_name, palette, custom_scale)
    return wrap_svg_icon(source_path, shape_name, palette, custom_scale)
