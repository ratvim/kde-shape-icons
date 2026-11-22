"""
SVG Shape definitions and path generators for KDE Shape Icons.
Canvas size is 48x48, centered at (24, 24).
"""

SHAPES = {
    "circle": {
        "name": "Circle",
        "description": "Classic Material Design circular icon (Android / Pixel style)",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<circle cx="24" cy="24" r="21.5" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 24,2.5 A 21.5,21.5 0 1,0 24,45.5 A 21.5,21.5 0 1,0 24,2.5 Z",
        "inner_scale": 0.64,
        "inner_offset": 8.64
    },
    "squircle": {
        "name": "Squircle",
        "description": "Continuous-curvature superellipse (Apple iOS / macOS / OneUI style)",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<path d="M 24,3 C 34.5,3 41.5,4.5 43.5,6.5 C 45.5,8.5 45,15.5 45,24 C 45,32.5 45.5,39.5 43.5,41.5 C 41.5,43.5 34.5,45 24,45 C 13.5,45 6.5,43.5 4.5,41.5 C 2.5,39.5 3,32.5 3,24 C 3,15.5 2.5,8.5 4.5,6.5 C 6.5,4.5 13.5,3 24,3 Z" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 24,3 C 34.5,3 41.5,4.5 43.5,6.5 C 45.5,8.5 45,15.5 45,24 C 45,32.5 45.5,39.5 43.5,41.5 C 41.5,43.5 34.5,45 24,45 C 13.5,45 6.5,43.5 4.5,41.5 C 2.5,39.5 3,32.5 3,24 C 3,15.5 2.5,8.5 4.5,6.5 C 6.5,4.5 13.5,3 24,3 Z",
        "inner_scale": 0.65,
        "inner_offset": 8.4
    },
    "rounded_square": {
        "name": "Rounded Square",
        "description": "Material 3 standard rounded rectangle with smooth corner radius",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<rect x="3.5" y="3.5" width="41" height="41" rx="10.5" ry="10.5" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 14,3.5 L 34,3.5 A 10.5,10.5 0 0,1 44.5,14 L 44.5,34 A 10.5,10.5 0 0,1 34,44.5 L 14,44.5 A 10.5,10.5 0 0,1 3.5,34 L 3.5,14 A 10.5,10.5 0 0,1 14,3.5 Z",
        "inner_scale": 0.66,
        "inner_offset": 8.16
    },
    "hexagon": {
        "name": "Hexagon",
        "description": "Modern geometric hexagon with balanced vertical orientation",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<polygon points="24,2.8 42.4,13.4 42.4,34.6 24,45.2 5.6,34.6 5.6,13.4" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 24,2.8 L 42.4,13.4 L 42.4,34.6 L 24,45.2 L 5.6,34.6 L 5.6,13.4 Z",
        "inner_scale": 0.58,
        "inner_offset": 10.08
    },
    "pebble": {
        "name": "Pebble",
        "description": "Organic, smooth asymmetrical pebble / river stone shape",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<path d="M 24,3 C 36,3 44,11 44,23 C 44,38 36,45 22,45 C 10,45 3,36 3,24 C 3,11 11,3 24,3 Z" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 24,3 C 36,3 44,11 44,23 C 44,38 36,45 22,45 C 10,45 3,36 3,24 C 3,11 11,3 24,3 Z",
        "inner_scale": 0.63,
        "inner_offset": 8.88
    },
    "octagon": {
        "name": "Octagon",
        "description": "Tech chamfered octagon (cyberpunk / industrial aesthetic)",
        "svg": lambda bg="url(#kde-shape-bg-grad)", stroke="url(#kde-shape-border-stroke)", sw=1.4, filter_id="kde-shape-shadow": (
            f'<polygon points="15.5,2.8 32.5,2.8 45.2,15.5 45.2,32.5 32.5,45.2 15.5,45.2 2.8,32.5 2.8,15.5" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
            f'filter="url(#{filter_id})" />'
        ),
        "path_d": "M 15.5,2.8 L 32.5,2.8 L 45.2,15.5 L 45.2,32.5 L 32.5,45.2 L 15.5,45.2 L 2.8,32.5 L 2.8,15.5 Z",
        "inner_scale": 0.62,
        "inner_offset": 9.12
    }
}

def get_shape(name: str):
    name_clean = name.lower().replace("-", "_").strip() if name else "circle"
    if name_clean in SHAPES:
        return SHAPES[name_clean]
    raise ValueError(f"Unknown shape '{name}'. Available: {list(SHAPES.keys())}")

def list_shapes():
    return {k: {"name": v["name"], "description": v["description"]} for k, v in SHAPES.items()}
