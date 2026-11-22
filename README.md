# KDE Shape Icons 🎨

> **Material Design shapes and dynamic dark/light accent styling for KDE Plasma 6.**  
> Wraps existing system application icons into uniform geometric shapes (Circles, Squircles, Rounded Squares, Hexagons, Pebbles, and Octagons) with accent-reactive border rings, depth shadows, and adaptive dark/light surface shades.

---

## 🌟 Key Features

* **Multiple Material Shapes**: Choose from **Circle**, **Squircle** (continuous-curvature iOS/OneUI style), **Rounded Square** (Material 3), **Hexagon**, **Pebble**, and **Octagon**.
* **System Accent Color Follower**: Automatically reads your KDE Plasma system accent color from `kdeglobals` (or accepts any custom hex color code).
* **Dark & Light Surface Shading**:
  * **Dark Mode**: Deep slate background (`#1b1e26` / `#13151b`) with vibrant accent border rings and soft elevation drop shadows.
  * **Light Mode**: Crisp light surface (`#ffffff` / `#edf1f6`) with matching accent borders.
* **Versatile Shading Styles**:
  * `accent_ring` *(Recommended / Material You)*: Neutral surface plate with a crisp accent-colored border ring.
  * `accent_tint`: Surface plate subtly tinted with a 12–15% blend of your accent color.
  * `accent_filled`: Vibrant solid accent color background plate.
  * `glassmorphism`: Translucent frosted surface with an accent glow.
  * `minimal`: Clean monochrome surface with soft subtle borders.
* **100% Vector Quality**: Pure SVG transformation with SVG coordinate isolation. All icons scale crisply at any DPI without blur or distortion.
* **Seamless Fallback**: Inherits from your base theme (Breeze) and `hicolor`. Non-app icons (folders, status icons, actions) continue to work normally.
* **Live Visual Designer**: Includes an interactive browser-based preview tool where you can test shapes, colors, and styles in real-time.

---

## 🚀 Quick Start

### 1. Interactive Preview
Open the interactive HTML preview in any browser to test all shapes and colors live:
```bash
xdg-open preview/index.html
```
*(Or navigate to [preview/index.html](file:///home/vimrat/Projects/MyApplication/kde_shape_icons/preview/index.html) in your browser)*.

---

### 2. Interactive Installer
Run the step-by-step installer script:
```bash
./install.sh
```
Follow the interactive prompts to choose your shape, mode, style, and accent color. It builds the icon theme in `~/.local/share/icons/` and immediately applies it to KDE Plasma.

---

### 3. Command Line Interface (`shape_icons.py`)

#### View Environment & Available Options
```bash
python3 shape_icons.py list
```

#### Generate & Apply a Circle Theme (Dark Mode, Auto Accent)
```bash
python3 shape_icons.py generate --shape circle --mode dark --style accent_ring --apply
```

#### Generate a Squircle Theme with Custom Accent Color
```bash
python3 shape_icons.py generate --shape squircle --style accent_tint --accent "#3584e4" --apply
```

#### Generate a Rounded Square Theme
```bash
python3 shape_icons.py generate --shape rounded_square --mode auto --apply
```

#### Apply an Existing Theme
```bash
python3 shape_icons.py apply --name KdeShape-Squircle
```

---

## 📐 Available Shapes

| Shape | Internal Scale | Description |
| :--- | :---: | :--- |
| `circle` | `64%` | Classic Material Design circle (Android / Pixel / ChromeOS) |
| `squircle` | `65%` | Continuous-curvature superellipse (Apple iOS / macOS / Samsung OneUI) |
| `rounded_square` | `66%` | Material 3 standard rounded rectangle with smooth corner radius |
| `hexagon` | `58%` | Modern geometric hexagon with balanced vertical orientation |
| `pebble` | `63%` | Organic, asymmetrical smooth pebble / teardrop shape |
| `octagon` | `62%` | Tech chamfered octagon (cyberpunk / industrial aesthetic) |

---

## 🎨 Shading Styles

| Style | Description |
| :--- | :--- |
| `accent_ring` | Neutral dark/light surface plate with crisp accent border ring |
| `accent_tint` | Surface plate subtly tinted with the accent color hue |
| `accent_filled` | Full solid accent color background plate |
| `glassmorphism` | Frosted translucent surface with accent glow |
| `minimal` | Monochrome surface with soft subtle border |

---

## ⚙️ How It Works

1. **SVG Coordinate Isolation**: Each source icon's inner XML is centered and scaled within a standard 48×48 SVG canvas. A nested `<svg preserveAspectRatio="xMidYMid meet">` ensures zero distortion.
2. **Material Elevation & Surface Shading**: Linear gradients and SVG `<feDropShadow>` filters provide subtle depth elevation.
3. **KDE Plasma Integration**: The theme is installed directly to `~/.local/share/icons/<theme-name>` with standard FreeDesktop `index.theme` inheritance. KDE's cache is updated via `kwriteconfig6` and `kbuildsycoca6`.

