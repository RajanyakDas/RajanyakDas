#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded, colored boxes.

Reveal: a diagonal, line-after-line slide-down (CSS keyframes that play
once on load, then freeze -- no looping "glow"). Includes a Less->More
legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
Reads:
    data/contributions.json
Writes:
    contrib-heatmap.svg
"""
import json
from datetime import datetime

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end, used for exceptional days)

CELL = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 34
RIGHT_PAD = 20
BOTTOM_PAD = 46

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count: int, max_count: int) -> int:
    if count == 0:
        return 0
    if max_count <= 0:
        return 1
    # exceptional days (top 5%) get the neon level 5
    if max_count >= 10 and count >= max(max_count, 1):
        ratio = count / max_count
        if ratio >= 0.95 and count > 6:
            return 5
    ratio = count / max_count
    if ratio > 0.75:
        return 4
    if ratio > 0.5:
        return 3
    if ratio > 0.25:
        return 2
    return 1


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    """Bucket days into 53 columns of 7 (Sun-Sat), padding the first week."""
    if not days:
        return []
    first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead_pad = (first_date.weekday() + 1) % 7  # weekday(): Mon=0..Sun=6 -> Sun=0

    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * lead_pad

    for day in days:
        current_week.append(day)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)
    return weeks


def build_svg(data: dict) -> str:
    days = data["days"]
    max_count = max((d["count"] for d in days), default=0)
    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * (CELL + GAP) + RIGHT_PAD
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )
    parts.append(f'''<style>
      .box {{ opacity: 0; }}
      @keyframes reveal {{
        from {{ opacity: 0; transform: translate(-6px, -6px); }}
        to   {{ opacity: 1; transform: translate(0, 0); }}
      }}
      .box.animate {{ animation: reveal 0.4s cubic-bezier(0.2,0,0.2,1) forwards; }}
      .month-label {{ fill: #8b949e; font-size: 10px; }}
      .footer {{ fill: #8b949e; font-size: 12px; }}
      .legend-label {{ fill: #8b949e; font-size: 10px; }}
    </style>''')

    # month labels along the top
    last_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            month = int(day["date"][5:7]) - 1
            if month != last_month:
                x = LEFT_PAD + wi * (CELL + GAP)
                parts.append(
                    f'<text x="{x}" y="{TOP_PAD - 10}" class="month-label">'
                    f'{MONTH_NAMES[month]}</text>'
                )
                last_month = month
            break

    # day cells, diagonal stagger by (week index + day index)
    max_delay_steps = n_weeks + 7
    total_anim_span = 1.6  # seconds over which the whole grid reveals
    step = total_anim_span / max(max_delay_steps, 1)

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            if day is None:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                    f'rx="2" fill="{PALETTE[0]}" opacity="0.25"/>'
                )
                continue
            level = level_for(day["count"], max_count)
            color = PALETTE[level]
            delay = (wi + di) * step
            title = f'{day["count"]} contributions on {day["date"]}'
            parts.append(
                f'<rect class="box animate" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" style="animation-delay:{delay:.3f}s">'
                f'<title>{title}</title></rect>'
            )

    # legend: Less -> More
    legend_y = height - 18
    legend_x = width - RIGHT_PAD - (len(PALETTE) * (CELL + GAP)) - 60
    parts.append(f'<text x="{legend_x - 34}" y="{legend_y + 9}" class="legend-label">Less</text>')
    for i, color in enumerate(PALETTE):
        lx = legend_x + i * (CELL + GAP)
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{legend_x + len(PALETTE) * (CELL + GAP) + 6}" y="{legend_y + 9}" '
        f'class="legend-label">More</text>'
    )

    # stats footer
    total = data.get("total_last_year", 0)
    streak = data.get("longest_streak", 0)
    footer = f'{total} contributions in the last year · longest streak {streak} days'
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y + 9}" class="footer">{footer}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    with open("data/contributions.json") as f:
        data = json.load(f)
    svg = build_svg(data)
    with open("contrib-heatmap.svg", "w") as f:
        f.write(svg)
    print(f"wrote contrib-heatmap.svg  ({len(data['days'])} days plotted)")
