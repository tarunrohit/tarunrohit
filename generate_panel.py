#!/usr/bin/env python3
"""
generate_panel.py
Composes the full "terminal" hero graphic for a GitHub profile README:
a bordered terminal window containing the dot-matrix portrait (from
ascii_to_svg.py) on the left and a neofetch-style system-info panel on
the right, populated with real resume content. Emits a dark and a light
theme variant so the README's <picture>/<source> tag can swap between
them based on the viewer's OS theme.
"""
import re
from ascii_to_svg import build_portrait_grid

PORTRAIT_COLS = 34
PORTRAIT_ROWS = 40
PORTRAIT_CELL = 8
PADDING = 22
CHROME_H = 34
TEXT_PANEL_W = 620
FONT_SIZE = 12.5
LINE_H = 19.5
CHAR_W = 7.45  # approx width of one monospace char at FONT_SIZE

PORTRAIT_W = PORTRAIT_COLS * PORTRAIT_CELL
PORTRAIT_H = PORTRAIT_ROWS * PORTRAIT_CELL


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def kv(label, value, label_w=12, dots_to=25):
    head = f"{label}:".ljust(label_w)
    dots = "." * max(dots_to - len(head), 3)
    return f"{head}{dots} {value}"


def portrait_dots_markup(grid, dot_color, edge_threshold=14, gamma=0.8):
    """Same tone/edge -> dot-radius logic as ascii_to_svg.grid_to_svg, but
    returns bare <circle> elements (no outer <svg>/<rect>) for embedding."""
    rows, cols = len(grid), len(grid[0])
    fg_tones = [t for row in grid for (t, e) in row if e > edge_threshold]
    if not fg_tones:
        fg_tones = [t for row in grid for (t, e) in row]
    fg_min, fg_max = min(fg_tones), max(fg_tones)
    fg_range = max(fg_max - fg_min, 1)

    max_r = PORTRAIT_CELL * 0.48
    out = []
    for r in range(rows):
        for c in range(cols):
            tone, edge = grid[r][c]
            if edge <= edge_threshold:
                continue
            norm = (tone - fg_min) / fg_range
            darkness = (1 - norm) ** gamma
            radius = max_r * darkness
            if radius < 0.4:
                continue
            cx = c * PORTRAIT_CELL + PORTRAIT_CELL / 2
            cy = r * PORTRAIT_CELL + PORTRAIT_CELL / 2
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.2f}" fill="{dot_color}"/>')
    return "\n".join(out)


def build_info_lines():
    lines = []
    lines.append(("section", "SYSTEM.INFO"))
    lines.append(("kv", kv("Subject", "Tarun Rohit Sai Pithani")))
    lines.append(("kv", kv("Role", "Software Development Engineer")))
    lines.append(("kv", kv("Focus", "Agentic AI / GenAI Developer")))
    lines.append(("kv", kv("Origin", "Nashik, India")))
    lines.append(("kv", kv("Education", "NIT Srinagar - B.Tech ECE '25")))
    lines.append(("kv", kv("Status", "Shipping AI-assisted products")))
    lines.append(("gap", ""))
    lines.append(("kv", kv("ToolChain", "VS Code, Git, Azure DevOps")))
    lines.append(("kv", kv("Core.AI", "LLM Integration (Gemini, Claude)")))
    lines.append(("kv", kv("Core.Agents", "Multi-Agent Orchestration (MCP, A2A)")))
    lines.append(("kv", kv("Core.Backend", "Node.js, Express, FastAPI, Flask")))
    lines.append(("kv", kv("Core.Frontend", "React, Flutter, HTML/CSS")))
    lines.append(("kv", kv("Core.Vision", "OpenCV, OCR, Google Cloud Vision")))
    lines.append(("gap", ""))
    lines.append(("section", "- Contact"))
    lines.append(("kv", kv("Mail", "rohittarun9@gmail.com")))
    lines.append(("kv", kv("LinkedIn", "linkedin.com/in/tarun-rohitsai-pithani-b65828261")))
    lines.append(("kv", kv("GitHub", "github.com/tarunrohit")))
    lines.append(("gap", ""))
    lines.append(("section", "- Live Stats"))
    lines.append(("plain", "See GitHub stats & streak badges below in README ↓"))
    return lines


def render_svg(grid, theme):
    if theme == "dark":
        bg = "#0b0f17"
        panel_bg = "#0d1420"
        border = "#1e293b"
        chrome_bg = "#111827"
        title_col = "#94a3b8"
        section_col = "#5eead4"
        label_col = "#94a3b8"
        value_col = "#e2e8f0"
        leader_col = "#334155"
        plain_col = "#64748b"
        dot_color = "#5eead4"
        badge_bg = "#134e4a"
        badge_fg = "#5eead4"
    else:
        bg = "#f8fafc"
        panel_bg = "#ffffff"
        border = "#cbd5e1"
        chrome_bg = "#e2e8f0"
        title_col = "#475569"
        section_col = "#0f766e"
        label_col = "#475569"
        value_col = "#0f172a"
        leader_col = "#cbd5e1"
        plain_col = "#64748b"
        dot_color = "#0f172a"
        badge_bg = "#ccfbf1"
        badge_fg = "#0f766e"

    lines = build_info_lines()
    text_h = len(lines) * LINE_H
    content_h = max(PORTRAIT_H, text_h)
    width = PADDING * 3 + PORTRAIT_W + TEXT_PANEL_W
    height = CHROME_H + PADDING * 2 + content_h

    portrait_x = PADDING
    portrait_y = CHROME_H + PADDING
    text_x = PADDING * 2 + PORTRAIT_W
    text_y = CHROME_H + PADDING + 14

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                  f'viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, '
                  f'Menlo, Consolas, \'Liberation Mono\', monospace">')

    # window chrome
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="{panel_bg}" stroke="{border}"/>')
    parts.append(f'<path d="M0,12 a12,12 0 0 1 12,-12 h{width - 24} a12,12 0 0 1 12,12 v{CHROME_H - 12} '
                  f'h-{width} z" fill="{chrome_bg}"/>')
    for i, col in enumerate(["#f87171", "#fbbf24", "#34d399"]):
        parts.append(f'<circle cx="{22 + i * 18}" cy="{CHROME_H / 2}" r="5.5" fill="{col}"/>')
    parts.append(f'<text x="{width / 2}" y="{CHROME_H / 2 + 4}" fill="{title_col}" font-size="12" '
                  f'text-anchor="middle">tarun@devos ~ % ./profile.sh</text>')
    parts.append(f'<rect x="{width - 92}" y="{CHROME_H / 2 - 10}" width="70" height="20" rx="10" fill="{badge_bg}"/>')
    parts.append(f'<text x="{width - 57}" y="{CHROME_H / 2 + 4}" fill="{badge_fg}" font-size="10" '
                  f'text-anchor="middle" letter-spacing="1">ONLINE</text>')

    # portrait
    parts.append(f'<g transform="translate({portrait_x},{portrait_y})">')
    parts.append(portrait_dots_markup(grid, dot_color))
    parts.append('</g>')
    parts.append(f'<text x="{portrait_x}" y="{portrait_y - 6}" fill="{title_col}" font-size="10.5" '
                  f'letter-spacing="1">VISUAL.MAP</text>')

    # divider
    div_x = text_x - PADDING / 2
    parts.append(f'<line x1="{div_x}" y1="{portrait_y - 4}" x2="{div_x}" y2="{portrait_y + content_h}" '
                  f'stroke="{border}"/>')

    # text panel
    y = text_y
    for kind, text in lines:
        if kind == "section":
            parts.append(f'<text x="{text_x}" y="{y}" fill="{section_col}" font-size="{FONT_SIZE}" '
                          f'font-weight="bold" letter-spacing="0.5">{esc(text)}</text>')
        elif kind == "kv":
            # split "label: dots value" back apart so label/value get distinct colors
            m = re.match(r"^(\S.*?:\s*)([.]+)(\s.*)$", text)
            if m:
                label_part, dots_part, value_part = m.groups()
                x_cursor = text_x
                parts.append(f'<text x="{x_cursor}" y="{y}" fill="{label_col}" font-size="{FONT_SIZE}">'
                              f'{esc(label_part)}<tspan fill="{leader_col}">{esc(dots_part)}</tspan>'
                              f'<tspan fill="{value_col}">{esc(value_part)}</tspan></text>')
            else:
                parts.append(f'<text x="{text_x}" y="{y}" fill="{value_col}" font-size="{FONT_SIZE}">{esc(text)}</text>')
        elif kind == "plain":
            parts.append(f'<text x="{text_x}" y="{y}" fill="{plain_col}" font-size="{FONT_SIZE}" '
                          f'font-style="italic">{esc(text)}</text>')
        y += LINE_H

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    grid = build_portrait_grid("headshot.jpg", PORTRAIT_COLS, PORTRAIT_ROWS, crop_box="auto")
    dark = render_svg(grid, "dark")
    light = render_svg(grid, "light")
    with open("dark.svg", "w") as f:
        f.write(dark)
    with open("light.svg", "w") as f:
        f.write(light)
    print("Wrote dark.svg and light.svg")


if __name__ == "__main__":
    main()
