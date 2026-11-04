#!/usr/bin/env python3
"""Generate a self-hosted GitHub contribution calendar SVG."""

from __future__ import annotations

from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen


USERNAME = "shriyatallapragada"
OUTPUT = Path("assets/github-contributions.svg")


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


def main() -> None:
    request = Request(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={"User-Agent": "contribution-calendar-generator"},
    )
    with urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    parser = ContributionParser()
    parser.feed(page)
    if parser.total is None:
        raise RuntimeError("Could not read the yearly contribution total from GitHub's calendar response")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="88" viewBox="0 0 300 88" role="img" aria-labelledby="title desc">
<title id="title">GitHub contributions for {USERNAME}</title>
<desc id="desc">{escape(parser.total)} contributions in the last year, updated {date.today().isoformat()}.</desc>
<rect x="1" y="1" width="298" height="86" rx="12" fill="#f6f8fa" stroke="#d0d7de"/>
<text x="22" y="57" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="38" font-weight="700" fill="#1f2328">{escape(parser.total)}</text>
<text x="92" y="40" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="14" font-weight="600" fill="#1f2328">GitHub contributions</text>
<text x="92" y="61" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="12" fill="#656d76">in the last year</text>
</svg>
'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
