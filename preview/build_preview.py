#!/usr/bin/env python3
"""
Builds an interactive, self-contained HTML preview for KDE Shape Icons.
Allows live previewing of shapes, dark/light themes, accent colors, and styles.
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from generator.shapes import SHAPES
from generator.colors import PRESET_COLORS, detect_kde_accent_color, detect_kde_theme_mode
from generator.svg_processor import extract_namespaces, extract_viewbox

def load_sample_icon_svg(fname: str) -> tuple[str, str]:
    breeze_apps = "/usr/share/icons/breeze/apps/48"
    path = os.path.join(breeze_apps, fname)
    if os.path.islink(path):
        target = os.readlink(path)
        path = os.path.join(breeze_apps, target)
        
    if not os.path.exists(path):
        return ("0 0 48 48", "<circle cx='24' cy='24' r='10' fill='#888'/>")
        
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    vb = extract_viewbox(content)
    cleaned = re.sub(r'<\?xml[^>]*\?>', '', content, flags=re.IGNORECASE)
    cleaned = re.sub(r'<!DOCTYPE[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<metadata>.*?</metadata>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    inner = re.sub(r'^\s*<svg[^>]*>', '', cleaned.strip(), flags=re.IGNORECASE)
    inner = re.sub(r'</svg>\s*$', '', inner.strip(), flags=re.IGNORECASE)
    return (vb, inner)

def generate_preview_html():
    samples = [
        ("Files", "system-file-manager.svg"),
        ("Terminal", "utilities-terminal.svg"),
        ("Settings", "systemsettings.svg"),
        ("Calculator", "accessories-calculator.svg"),
        ("Text Editor", "kwrite.svg"),
        ("Screenshot", "ksnapshot.svg"),
        ("Archive", "ark.svg"),
        ("Music", "amarok.svg")
    ]
    
    sample_data = []
    for label, fname in samples:
        vb, inner = load_sample_icon_svg(fname)
        sample_data.append({"label": label, "vb": vb, "inner": inner})
        
    default_accent = detect_kde_accent_color()
    default_mode = detect_kde_theme_mode()
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KDE Shape Icons — Live Visual Designer</title>
  <style>
    :root {{
      --accent: {default_accent};
      --bg: #0f1117;
      --card-bg: #1a1d26;
      --card-border: rgba(255, 255, 255, 0.08);
      --text-main: #f0f3f6;
      --text-sub: #9aa0a6;
    }}
    body.light-mode {{
      --bg: #f5f7fa;
      --card-bg: #ffffff;
      --card-border: rgba(0, 0, 0, 0.08);
      --text-main: #1a1d20;
      --text-sub: #5f6368;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", Ubuntu, sans-serif;
    }}
    body {{
      background: var(--bg);
      color: var(--text-main);
      padding: 32px 24px;
      transition: background 0.25s ease, color 0.25s ease;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1080px;
      margin: 0 auto;
    }}
    header {{
      text-align: center;
      margin-bottom: 32px;
    }}
    header h1 {{
      font-size: 32px;
      font-weight: 700;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
    }}
    .badge {{
      font-size: 13px;
      padding: 4px 10px;
      border-radius: 20px;
      background: var(--accent);
      color: #000;
      font-weight: 600;
    }}
    header p {{
      color: var(--text-sub);
      font-size: 15px;
    }}
    .control-panel {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 32px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
    }}
    .control-group {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .control-group label {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-sub);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .btn-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .btn-toggle {{
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: rgba(125, 125, 125, 0.08);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-toggle:hover {{
      background: rgba(125, 125, 125, 0.16);
    }}
    .btn-toggle.active {{
      background: var(--accent);
      color: #000;
      font-weight: 600;
      border-color: var(--accent);
    }}
    .color-swatches {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .swatch {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      cursor: pointer;
      border: 2px solid transparent;
      transition: transform 0.15s, border-color 0.15s;
    }}
    .swatch:hover {{
      transform: scale(1.15);
    }}
    .swatch.active {{
      border-color: #ffffff;
      box-shadow: 0 0 0 2px var(--accent);
    }}
    input[type="color"] {{
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      background: none;
    }}
    .grid-preview {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
      gap: 24px;
      padding: 36px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      margin-bottom: 32px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    }}
    .icon-card {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      transition: transform 0.2s ease;
    }}
    .icon-card:hover {{
      transform: translateY(-4px);
    }}
    .icon-wrapper {{
      width: 64px;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
    }}
    .icon-wrapper svg {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}
    .icon-label {{
      font-size: 13px;
      font-weight: 500;
      color: var(--text-main);
      text-align: center;
    }}
    .command-box {{
      background: #151820;
      border: 1px solid #282d3c;
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 14px;
      color: #58a6ff;
    }}
    .copy-btn {{
      padding: 8px 16px;
      border-radius: 8px;
      background: var(--accent);
      color: #000;
      font-weight: 600;
      border: none;
      cursor: pointer;
      font-size: 13px;
      transition: opacity 0.2s;
      white-space: nowrap;
    }}
    .copy-btn:hover {{
      opacity: 0.9;
    }}
  </style>
</head>
<body class="{'' if default_mode == 'dark' else 'light-mode'}">
  <div class="container">
    <header>
      <h1>
        KDE Shape Icons
        <span class="badge">Plasma 6</span>
      </h1>
      <p>Material Design custom shapes & dynamic dark/light accent styling for KDE Plasma</p>
    </header>

    <div class="control-panel">
      <!-- Shape Selection -->
      <div class="control-group">
        <label>Shape</label>
        <div class="btn-row" id="shapeButtons">
          <button class="btn-toggle active" data-shape="circle">Circle</button>
          <button class="btn-toggle" data-shape="squircle">Squircle</button>
          <button class="btn-toggle" data-shape="rounded_square">Rounded Square</button>
          <button class="btn-toggle" data-shape="hexagon">Hexagon</button>
          <button class="btn-toggle" data-shape="pebble">Pebble</button>
          <button class="btn-toggle" data-shape="octagon">Octagon</button>
        </div>
      </div>

      <!-- Theme Mode -->
      <div class="control-group">
        <label>Theme Mode</label>
        <div class="btn-row" id="modeButtons">
          <button class="btn-toggle {'active' if default_mode == 'dark' else ''}" data-mode="dark">Dark</button>
          <button class="btn-toggle {'active' if default_mode == 'light' else ''}" data-mode="light">Light</button>
        </div>
      </div>

      <!-- Style -->
      <div class="control-group">
        <label>Shade Style</label>
        <div class="btn-row" id="styleButtons">
          <button class="btn-toggle active" data-style="accent_ring">Accent Ring</button>
          <button class="btn-toggle" data-style="accent_tint">Accent Tint</button>
          <button class="btn-toggle" data-style="accent_filled">Accent Fill</button>
          <button class="btn-toggle" data-style="glassmorphism">Glass</button>
          <button class="btn-toggle" data-style="minimal">Minimal</button>
        </div>
      </div>

      <!-- Accent Color -->
      <div class="control-group">
        <label>Accent Color</label>
        <div class="color-swatches" id="colorSwatches">
          <div class="swatch active" data-color="{default_accent}" style="background: {default_accent};" title="KDE Current Accent"></div>
          <div class="swatch" data-color="#3584e4" style="background: #3584e4;" title="Ocean Blue"></div>
          <div class="swatch" data-color="#7b52ab" style="background: #7b52ab;" title="Royal Purple"></div>
          <div class="swatch" data-color="#ff7800" style="background: #ff7800;" title="Sunset Orange"></div>
          <div class="swatch" data-color="#e01b24" style="background: #e01b24;" title="Crimson Red"></div>
          <div class="swatch" data-color="#ec407a" style="background: #ec407a;" title="Neon Pink"></div>
          <input type="color" id="customColor" value="{default_accent}" title="Custom color picker">
        </div>
      </div>
    </div>

    <!-- Live Grid Preview -->
    <div class="grid-preview" id="gridPreview">
      <!-- Icon cards rendered via JS -->
    </div>

    <!-- Generated Command -->
    <div class="command-box">
      <span id="cmdText">python3 shape_icons.py generate --shape circle --style accent_ring --mode {default_mode} --accent {default_accent} --apply</span>
      <button class="copy-btn" id="copyBtn">Copy Command</button>
    </div>
  </div>

  <script>
    const sampleIcons = {sample_data};

    const shapePaths = {{
      circle: (bg, stroke, sw) => `<circle cx="24" cy="24" r="21.5" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}"/>`,
      squircle: (bg, stroke, sw) => `<path d="M 24,2.5 C 36.8,2.5 45.5,11.2 45.5,24 C 45.5,36.8 36.8,45.5 24,45.5 C 11.2,45.5 2.5,36.8 2.5,24 C 2.5,11.2 11.2,2.5 24,2.5 Z" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}"/>`,
      rounded_square: (bg, stroke, sw) => `<rect x="3" y="3" width="42" height="42" rx="11" ry="11" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}"/>`,
      hexagon: (bg, stroke, sw) => `<polygon points="24,2.8 42.4,13.4 42.4,34.6 24,45.2 5.6,34.6 5.6,13.4" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}" stroke-linejoin="round"/>`,
      pebble: (bg, stroke, sw) => `<path d="M 24,2.5 C 38.5,2.5 45.5,10.5 45.5,24 C 45.5,38 37.5,45.5 24,45.5 C 10.5,45.5 2.5,37 2.5,24 C 2.5,10 11,2.5 24,2.5 Z" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}"/>`,
      octagon: (bg, stroke, sw) => `<polygon points="15.5,2.8 32.5,2.8 45.2,15.5 45.2,32.5 32.5,45.2 15.5,45.2 2.8,32.5 2.8,15.5" fill="${{bg}}" stroke="${{stroke}}" stroke-width="${{sw}}" stroke-linejoin="round"/>`
    }};

    let state = {{
      shape: 'circle',
      mode: '{default_mode}',
      style: 'accent_ring',
      accent: '{default_accent}'
    }};

    function hexToRgb(hex) {{
      const clean = hex.replace('#', '');
      const num = parseInt(clean, 16);
      return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
    }}

    function blend(hex1, hex2, ratio) {{
      const [r1, g1, b1] = hexToRgb(hex1);
      const [r2, g2, b2] = hexToRgb(hex2);
      const r = Math.round(r1 * (1 - ratio) + r2 * ratio);
      const g = Math.round(g1 * (1 - ratio) + g2 * ratio);
      const b = Math.round(b1 * (1 - ratio) + b2 * ratio);
      return `rgb(${{r}}, ${{g}}, ${{b}})`;
    }}

    function renderIcons() {{
      const grid = document.getElementById('gridPreview');
      grid.innerHTML = '';
      
      const isDark = (state.mode === 'dark');
      document.body.className = isDark ? '' : 'light-mode';
      document.documentElement.style.setProperty('--accent', state.accent);

      let bgTop, bgBottom, stroke, strokeWidth = 1.4;

      if (state.style === 'accent_filled') {{
        bgTop = state.accent;
        bgBottom = blend(state.accent, '#000000', 0.2);
        stroke = isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.15)';
      }} else if (state.style === 'accent_tint') {{
        bgTop = isDark ? blend('#161822', state.accent, 0.16) : blend('#ffffff', state.accent, 0.08);
        bgBottom = isDark ? blend('#10121a', state.accent, 0.12) : blend('#edf2f7', state.accent, 0.12);
        stroke = state.accent;
      }} else if (state.style === 'glassmorphism') {{
        bgTop = isDark ? 'rgba(32, 37, 51, 0.85)' : 'rgba(255, 255, 255, 0.85)';
        bgBottom = isDark ? 'rgba(20, 23, 34, 0.85)' : 'rgba(238, 242, 247, 0.85)';
        stroke = state.accent;
      }} else if (state.style === 'minimal') {{
        bgTop = isDark ? '#222630' : '#ffffff';
        bgBottom = isDark ? '#191c24' : '#f2f4f8';
        stroke = isDark ? '#323846' : '#d8dde6';
      }} else {{ // accent_ring
        bgTop = isDark ? '#222630' : '#ffffff';
        bgBottom = isDark ? '#171a22' : '#edf1f6';
        stroke = state.accent;
      }}

      sampleIcons.forEach((item, idx) => {{
        const card = document.createElement('div');
        card.className = 'icon-card';

        const shapeFn = shapePaths[state.shape] || shapePaths.circle;
        const gradId = `shape-grad-${{idx}}`;

        card.innerHTML = `
          <div class="icon-wrapper">
            <svg width="48" height="48" viewBox="0 0 48 48">
              <defs>
                <linearGradient id="${{gradId}}" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stop-color="${{bgTop}}"/>
                  <stop offset="100%" stop-color="${{bgBottom}}"/>
                </linearGradient>
              </defs>
              ${{shapeFn(`url(#${{gradId}})`, stroke, strokeWidth)}}
              <svg x="8.5" y="8.5" width="31" height="31" viewBox="${{item.vb}}" preserveAspectRatio="xMidYMid meet">
                ${{item.inner}}
              </svg>
            </svg>
          </div>
          <span class="icon-label">${{item.label}}</span>
        `;
        grid.appendChild(card);
      }});

      // Update command box
      const cmd = `python3 shape_icons.py generate --shape ${{state.shape}} --style ${{state.style}} --mode ${{state.mode}} --accent "${{state.accent}}" --apply`;
      document.getElementById('cmdText').innerText = cmd;
    }}

    // Event listeners
    document.getElementById('shapeButtons').addEventListener('click', (e) => {{
      if (e.target.dataset.shape) {{
        document.querySelectorAll('#shapeButtons .btn-toggle').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        state.shape = e.target.dataset.shape;
        renderIcons();
      }}
    }});

    document.getElementById('modeButtons').addEventListener('click', (e) => {{
      if (e.target.dataset.mode) {{
        document.querySelectorAll('#modeButtons .btn-toggle').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        state.mode = e.target.dataset.mode;
        renderIcons();
      }}
    }});

    document.getElementById('styleButtons').addEventListener('click', (e) => {{
      if (e.target.dataset.style) {{
        document.querySelectorAll('#styleButtons .btn-toggle').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        state.style = e.target.dataset.style;
        renderIcons();
      }}
    }});

    document.getElementById('colorSwatches').addEventListener('click', (e) => {{
      if (e.target.dataset.color) {{
        document.querySelectorAll('.swatch').forEach(s => s.classList.remove('active'));
        e.target.classList.add('active');
        state.accent = e.target.dataset.color;
        document.getElementById('customColor').value = state.accent;
        renderIcons();
      }}
    }});

    document.getElementById('customColor').addEventListener('input', (e) => {{
      state.accent = e.target.value;
      document.querySelectorAll('.swatch').forEach(s => s.classList.remove('active'));
      renderIcons();
    }});

    document.getElementById('copyBtn').addEventListener('click', () => {{
      const text = document.getElementById('cmdText').innerText;
      navigator.clipboard.writeText(text);
      const btn = document.getElementById('copyBtn');
      btn.innerText = 'Copied!';
      setTimeout(() => btn.innerText = 'Copy Command', 2000);
    }});

    // Initial render
    renderIcons();
  </script>
</body>
</html>'''

    out_file = os.path.join(SCRIPT_DIR, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Generated preview at: {out_file}")

if __name__ == "__main__":
    generate_preview_html()
