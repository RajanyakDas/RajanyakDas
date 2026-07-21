#!/usr/bin/env python3
"""
make_ascii_svg.py — convert source-prepped.png into a monochrome ASCII
portrait that "types" itself in, row by row, as an animated SVG.

Design choices:
  - Monochrome (one light-gray fill). Per-character rainbow coloring is
    exactly what makes most ASCII portraits look like noisy static.
  - High contrast source -> busy backgrounds wash out to the space glyph,
    so only the subject prints.
  - Each row is wrapped in a clip-path that wipes left-to-right, with a
    small block "cursor" riding the wipe edge, staggered top to bottom.
    The whole thing prints once and freezes -- no looping.

Usage:
    python scripts/make_ascii_svg.py
Reads:
    source-prepped.png
Writes:
    avi-ascii.svg
"""
import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense); leading space = blank
COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11.5
FONT_SIZE = 12
FILL = "#8fa1b3"          # single monochrome tone
CURSOR_FILL = "#c9d6e3"
ROW_STAGGER = 0.035        # seconds between row starts
ROW_DURATION = 0.5         # seconds each row takes to wipe in


def image_to_ascii(path: str, cols: int, rows: int) -> list[str]:
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0  # 0=black .. 1=white
    ramp_len = len(RAMP)
    lines = []
    for y in range(rows):
        line_chars = []
        for x in range(cols):
            brightness = arr[y, x]
            # invert: bright -> low density index (near start of ramp)
            idx = int((1.0 - brightness) * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def build_svg(lines: list[str]) -> str:
    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20
    total_duration = (ROWS - 1) * ROW_STAGGER + ROW_DURATION

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">'
    )
    parts.append(
        '<style>'
        f'.row {{ fill: {FILL}; }}'
        f'.cursor {{ fill: {CURSOR_FILL}; }}'
        '</style>'
    )
    parts.append(f'<rect width="100%" height="100%" fill="transparent"/>')

    row_width_px = COLS * CHAR_W

    for i, line in enumerate(lines):
        y = 20 + i * CHAR_H
        start = i * ROW_STAGGER
        end = start + ROW_DURATION
        clip_id = f"clip{i}"
        text_content = escape_xml(line.rstrip()) or " "

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="10" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_width_px:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            f'</rect>'
        )
        parts.append('</clipPath>')

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'<text class="row" x="10" y="{y:.1f}" xml:space="preserve">{text_content}</text>'
        )
        parts.append('</g>')

        # cursor block riding the wipe edge, fades out when its row finishes
        parts.append(
            f'<rect class="cursor" x="10" y="{y - CHAR_H + 2:.1f}" '
            f'width="{CHAR_W:.1f}" height="{CHAR_H - 2:.1f}" opacity="0">'
            f'<animate attributeName="x" from="10" to="{10 + row_width_px:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.2 0 0.2 1"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.05;0.9;1" begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" '
            f'fill="freeze"/>'
            f'</rect>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    lines = image_to_ascii("source-prepped.png", COLS, ROWS)
    svg = build_svg(lines)
    with open("avi-ascii.svg", "w") as f:
        f.write(svg)
    print(f"wrote avi-ascii.svg  ({COLS}x{ROWS} chars, {len(svg)} bytes)")
