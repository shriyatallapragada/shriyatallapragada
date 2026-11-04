#!/usr/bin/env python3
"""Generate a self-hosted GitHub contribution calendar SVG."""

from datetime import date
from html import escape
from pathlib import Path
import re
from urllib.request import Request, urlopen


USERNAME = "shriyatallapragada"
OUTPUT = Path("assets/github-contributions.svg")
COLORS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]


def main() -> None:
    request = Request(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={"User-Agent": "contribution-calendar-generator"},
    )
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    days = re.findall(
        r'<td[^>]*class="ContributionCalendar-day"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="([0-4])"',
        page,
    )
    if not days:
        raise RuntimeError("No contribution days found in GitHub's calendar response")

    # The calendar endpoint returns a year of dates, laid out in Sunday-first columns.
    entries = [(date.fromisoformat(day), int(level)) for day, level in days]
    first_sunday = entries[0][0]
    cell, gap, margin_x, margin_y = 11, 3, 44, 30
    weeks = (len(entries) + 6) // 7
    width = margin_x * 2 + weeks * (cell + gap) - gap
    height = margin_y * 2 + 7 * (cell + gap) - gap

    rects = []
    for day, level in entries:
        week = (day - first_sunday).days // 7
        weekday = (day.weekday() + 1) % 7
        x, y = margin_x + week * (cell + gap), margin_y + weekday * (cell + gap)
        label = f"{level} contributions on {day.isoformat()}"
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{COLORS[level]}"><title>{escape(label)}</title></rect>'
        )

    month_labels = []
    previous_month = None
    for day, _ in entries:
        if day.month != previous_month and day.weekday() == 6:
            week = (day - first_sunday).days // 7
            month_labels.append(
                f'<text x="{margin_x + week * (cell + gap)}" y="17">{day.strftime("%b")}</text>'
            )
            previous_month = day.month

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">GitHub contributions for {USERNAME}</title>
<desc id="desc">Daily contribution calendar for the past year, generated {date.today().isoformat()}.</desc>
<style>text{{font:11px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#57606a}} .day{{font-size:10px}}</style>
{''.join(month_labels)}
<text class="day" x="5" y="{margin_y + 10}">Mon</text><text class="day" x="5" y="{margin_y + 4 * (cell + gap) + 10}">Wed</text><text class="day" x="5" y="{margin_y + 6 * (cell + gap) + 10}">Fri</text>
{''.join(rects)}
</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
