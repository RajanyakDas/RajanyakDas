#!/usr/bin/env python3
"""
make_info_card.py — a neofetch-style panel (title bar + colored key/value
rows) that fades and slides in line by line, like it's printing next to
the ASCII portrait.

Edit CONTENT below with your own role, stack, and highlights.

Env:
    STATIC=1   emit a frozen (non-animated) frame, useful for local
               Quick Look previews.

Usage:
    python scripts/make_info_card.py
Writes:
    info-card.svg
"""
import os

STATIC = os.environ.get("STATIC") == "1"

USERNAME = "rajanyakdas"
HOSTNAME = "github"

CONTENT = [
    ("Now", "Building things that live at the intersection of code & design"),
    ("Prev", "Shipped projects across web, tooling, and automation"),
    ("Stack", "Python · TypeScript · React · Node · SQL"),
    ("Highlights", "Open source contributor · Automation enthusiast · Always learning"),
]

TITLE = f"{USERNAME}@{HOSTNAME}"

BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
DIM_COLOR = "#8b949e"
DOT_RED = "#ff5f56"
DOT_YELLOW = "#ffbd2e"
DOT_GREEN = "#27c93f"

LINE_H = 34
PAD_X = 24
PAD_TOP = 70
WIDTH = 490
STAGGER = 0.28
DUR = 0.5


def escape_xml(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def build_svg() -> str:
    n_rows = len(CONTENT)
    height = PAD_TOP + n_rows * LINE_H + 30

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    parts.append(f'''<style>
      .titlebar {{ fill: {TITLEBAR}; }}
      .panel {{ fill: {BG}; stroke: {BORDER}; stroke-width: 1; }}
      .title-text {{ fill: {DIM_COLOR}; font-size: 12px; }}
      .label {{ fill: {LABEL_COLOR}; font-size: 14px; font-weight: 600; }}
      .value {{ fill: {VALUE_COLOR}; font-size: 13px; }}
      .row {{ opacity: {"1" if STATIC else "0"}; }}
    </style>''')

    # panel background + border, rounded
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" '
        f'rx="10" class="panel"/>'
    )
    # title bar
    parts.append(f'<path d="M0.5 10.5 a10 10 0 0 1 10 -10 h{WIDTH - 21} '
                  f'a10 10 0 0 1 10 10 v27 h-{WIDTH - 1} z" class="titlebar"/>')
    # traffic-light dots
    for i, color in enumerate([DOT_RED, DOT_YELLOW, DOT_GREEN]):
        parts.append(f'<circle cx="{20 + i * 18}" cy="19" r="6" fill="{color}"/>')
    parts.append(f'<text x="{WIDTH/2}" y="23" text-anchor="middle" class="title-text">'
                 f'{escape_xml(TITLE)} — neofetch</text>')

    # user@host header line inside panel
    header_y = PAD_TOP - 20
    parts.append(
        f'<text x="{PAD_X}" y="{header_y}" font-size="15" font-weight="700" fill="{LABEL_COLOR}">'
        f'{escape_xml(USERNAME)}</text>'
        f'<tspan fill="{DIM_COLOR}">@{escape_xml(HOSTNAME)}</tspan>'
    )
    parts.append(
        f'<line x1="{PAD_X}" y1="{header_y + 8}" x2="{WIDTH - PAD_X}" y2="{header_y + 8}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    for i, (label, value) in enumerate(CONTENT):
        y = PAD_TOP + i * LINE_H
        row_group_attrs = 'class="row"'
        if not STATIC:
            begin = i * STAGGER
            anim = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{DUR}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.2 0 0.2 1"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-14 0" to="0 0" begin="{begin:.2f}s" dur="{DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            )
        else:
            anim = ""
        parts.append(f'<g {row_group_attrs}>')
        parts.append(
            f'<text x="{PAD_X}" y="{y}" class="label">{escape_xml(label)}</text>'
        )
        parts.append(
            f'<text x="{PAD_X + 108}" y="{y}" class="value">{escape_xml(value)}</text>'
        )
        parts.append(anim)
        parts.append('</g>')

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    svg = build_svg()
    with open("info-card.svg", "w") as f:
        f.write(svg)
    print(f"wrote info-card.svg ({'static' if STATIC else 'animated'})")
