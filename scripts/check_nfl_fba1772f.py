#!/usr/bin/env python3
"""Offline integrity checks for the isolated fba1772f decision-guide pages."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "docs" / "nfl-fba1772f"
EXPECTED = {"index.html", "suggestions.html", "questions.html", "flagged.html", "sources.html"}


class LinksAndTables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.in_tbody = False
        self.in_row = False
        self.row_has_official_link = False
        self.rows = 0
        self.unlinked_rows = 0
        self.has_main = False
        self.has_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "title":
            self.has_title = True
        if tag == "main":
            self.has_main = True
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"] or "")
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_has_official_link = False
        if tag == "a" and self.in_row:
            href = attrs_dict.get("href") or ""
            if href.startswith("https://"):
                self.row_has_official_link = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_row:
            self.rows += 1
            if not self.row_has_official_link:
                self.unlinked_rows += 1
            self.in_row = False
        if tag == "tbody":
            self.in_tbody = False


def main() -> int:
    errors: list[str] = []
    actual = {p.name for p in PAGES.glob("*.html")}
    if actual != EXPECTED:
        errors.append(f"page set mismatch: expected {sorted(EXPECTED)}, got {sorted(actual)}")
    total_rows = 0
    for page in sorted(PAGES.glob("*.html")):
        parser = LinksAndTables()
        parser.feed(page.read_text(encoding="utf-8"))
        total_rows += parser.rows
        if not parser.has_title or not parser.has_main:
            errors.append(f"{page.name}: missing title or main landmark")
        if parser.unlinked_rows:
            errors.append(f"{page.name}: {parser.unlinked_rows}/{parser.rows} table rows lack an HTTPS source/context link")
        for href in parser.links:
            if href.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (page.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{page.name}: broken local link {href!r} -> {resolved.relative_to(ROOT) if ROOT in resolved.parents else resolved}")
    if errors:
        print("FAIL")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"OK: {len(actual)} pages, {total_rows} table rows each with an HTTPS context/source link; all local links resolve")
    print("Note: this offline checker does not fetch or validate external sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
