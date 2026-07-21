#!/usr/bin/env python3
"""
fetch_contributions.py — pull a real, public GitHub contribution calendar
with no auth, no GraphQL API, no personal access token.

GitHub serves the calendar as an HTML fragment at:
    https://github.com/users/<username>/contributions
(the same fragment the profile page itself renders). We fetch it with
requests and parse the day cells with BeautifulSoup, then write
data/contributions.json with raw days plus a few derived stats.

Usage:
    python scripts/fetch_contributions.py [username]
Writes:
    data/contributions.json
"""
import json
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "RajanyakDas"
UA = "Mozilla/5.0 (compatible; profile-readme-bot/1.0)"


def fetch(username: str) -> dict:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    cells = soup.select("td.ContributionCalendar-day") or soup.select("rect.ContributionCalendar-day")
    for cell in cells:
        date = cell.get("data-date")
        count_attr = cell.get("data-count") or cell.get("data-level")
        level = cell.get("data-level")
        tooltip_id = cell.get("id")
        count = None
        if count_attr is not None:
            try:
                count = int(count_attr)
            except ValueError:
                count = None
        if date:
            days.append({
                "date": date,
                "count": count if count is not None else 0,
                "level": int(level) if level is not None else 0,
            })

    # tooltips carry the human-readable count text, use them to backfill counts
    tooltips = soup.select("tool-tip")
    tip_map = {}
    for tip in tooltips:
        for_id = tip.get("for")
        text = tip.get_text(strip=True)
        if for_id and text:
            tip_map[for_id] = text

    for cell, day in zip(cells, days):
        tid = cell.get("id")
        if tid and tid in tip_map:
            text = tip_map[tid]
            digits = "".join(ch for ch in text.split(" ")[0] if ch.isdigit())
            if digits:
                day["count"] = int(digits)
            elif "No contributions" in text:
                day["count"] = 0

    days.sort(key=lambda d: d["date"])

    total = sum(d["count"] for d in days)

    # streaks
    longest = current = 0
    best_streak = 0
    for d in days:
        if d["count"] > 0:
            current += 1
            best_streak = max(best_streak, current)
        else:
            current = 0
    # current streak = trailing run ending on the last day with data
    trailing = 0
    for d in reversed(days):
        if d["count"] > 0:
            trailing += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"]) if days else None

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "total_last_year": total,
        "longest_streak": best_streak,
        "current_streak": trailing,
        "best_day": best_day,
        "monthly_totals": monthly,
        "days": days,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    data = fetch(username)
    with open("data/contributions.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote data/contributions.json  "
          f"({len(data['days'])} days, {data['total_last_year']} contributions)")
