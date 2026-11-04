#!/usr/bin/env python3
"""Generate a colorful card with a lifetime public contribution total."""

from __future__ import annotations

from datetime import date
from concurrent.futures import ThreadPoolExecutor
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen


USERNAME = "shriyatallapragada"
OUTPUT = Path("assets/github-contributions.svg")
FIRST_GITHUB_YEAR = 2008


class ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.total: str | None = None
        self._in_total = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "h2" and attributes.get("id") == "js-contribution-activity-description":
            self._in_total = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            self._in_total = False

    def handle_data(self, data: str) -> None:
        if self._in_total and self.total is None:
            match = re.search(r"\d[\d,]*", data.strip())
            if match:
                self.total = match.group().replace(",", "")


def contributions_for_year(year: int) -> int:
    request = Request(
        f"https://github.com/users/{USERNAME}/contributions?from={year}-01-01&to={year}-12-31",
        headers={"User-Agent": "contribution-calendar-generator"},
    )
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")
    parser = ContributionParser()
    parser.feed(page)
    if parser.total is None:
        raise RuntimeError(f"Could not read GitHub's contribution total for {year}")
    return int(parser.total)


def main() -> None:
    years = range(FIRST_GITHUB_YEAR, date.today().year + 1)
    with ThreadPoolExecutor(max_workers=6) as pool:
        total = sum(pool.map(contributions_for_year, years))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="100" viewBox="0 0 320 100" role="img" aria-labelledby="title desc">
<title id="title">GitHub contributions for {USERNAME}</title>
<desc id="desc">{total:,} public contributions across all years, updated {date.today().isoformat()}.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#3b5ccc"/><stop offset="55%" stop-color="#6951c8"/><stop offset="100%" stop-color="#a43e9b"/></linearGradient></defs>
<rect x="1" y="1" width="318" height="98" rx="16" fill="url(#bg)"/>
<circle cx="285" cy="18" r="42" fill="#ffffff" opacity="0.08"/><circle cx="310" cy="86" r="30" fill="#9ef0c2" opacity="0.18"/>
<text x="23" y="60" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="40" font-weight="750" fill="#ffffff">{total:,}</text>
<text x="24" y="82" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12" font-weight="600" letter-spacing="0.5" fill="#e6e6ff">PUBLIC CONTRIBUTIONS · ALL TIME</text>
<text x="285" y="57" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="25" fill="#ffffff">✦</text>
</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
