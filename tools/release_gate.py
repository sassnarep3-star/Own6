#!/usr/bin/env python3
"""Offline release safety gate for the published root and all docs/ HTML pages.

Checks merge markers, leaked Python generator reprs, escaping/broken internal
links, and official-source links on landing-page table rows. Link presence is
NOT verification that the cited page supports a particular factual claim; that
requires the separate human/source audit. No network calls or data scraping.
"""
from __future__ import annotations

import html.parser
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".py", ".js", ".md", ".json", ".csv", ".yml", ".yaml", ".css", ".txt"}
MARKER = re.compile(r"^(?:<{7}(?:\s|$)|={7}$|>{7}(?:\s|$))", re.MULTILINE)
OFFICIAL_HOSTS = {"www.nba.com", "official.nba.com", "github.com", "docs.github.com"}


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.in_body_row = False
        self.in_tbody = False
        self.row = 0
        self.row_cells = 0
        self.row_links: list[str] = []
        self.rows: list[tuple[int, int, list[str]]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_body_row = True
            self.row += 1
            self.row_cells = 0
            self.row_links = []
        elif tag == "td" and self.in_body_row:
            self.row_cells += 1
        elif tag == "a" and self.in_body_row and attrs.get("href"):
            self.row_links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_body_row:
            self.rows.append((self.row, self.row_cells, self.row_links))
            self.in_body_row = False
        elif tag == "tbody":
            self.in_tbody = False


def check_release(root: Path, tracked: list[Path] | None = None) -> list[str]:
    root = root.resolve()
    if tracked is None:
        tracked = [Path(p) for p in subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=root
        ).decode().split("\0") if p]
    errors: list[str] = []
    for relative in tracked:
        path = root / relative
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in MARKER.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{relative}:{line}: unresolved merge marker")

    pages = [root / "index.html", *sorted((root / "docs").rglob("*.html"))]
    for path in pages:
        if not path.is_file():
            errors.append(f"{path.relative_to(root)}: missing published page")
            continue
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        if "<generator object" in text:
            errors.append(f"{rel}: Python generator repr leaked into HTML")
        parser = Page()
        parser.feed(text)
        for link in parser.links:
            parsed = urlparse(link)
            if parsed.scheme in {"https", "mailto", "tel", "data"}:
                continue
            if parsed.scheme or parsed.netloc or link.startswith("//"):
                errors.append(f"{rel}: unsupported/external insecure link: {link}")
                continue
            if not parsed.path and parsed.fragment:
                continue  # same-page anchor; does not depend on an external file
            if not parsed.path:
                continue
            # GitHub Pages publishes at /Own6/; root-absolute paths can escape it.
            if parsed.path.startswith("/"):
                errors.append(f"{rel}: root-absolute link is not project-relative: {link}")
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f"{rel}: broken or escaping internal link: {link}")
        if rel.as_posix() == "docs/index.html":
            for row, cells, links in parser.rows:
                if not cells:
                    errors.append(f"{rel}: table row {row} has no cells")
                if not any(urlparse(link).scheme == "https" and
                           urlparse(link).hostname in OFFICIAL_HOSTS for link in links):
                    errors.append(f"{rel}: table row {row} has no official HTTPS source link")
    return errors


if __name__ == "__main__":
    issues = check_release(ROOT)
    for issue in issues:
        print("FAIL", issue)
    print(f"Release gate: {len(issues)} issue(s) across published HTML and tracked text")
    sys.exit(bool(issues))
