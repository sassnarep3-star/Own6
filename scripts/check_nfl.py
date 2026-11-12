#!/usr/bin/env python3
"""Evidence and internal-link checks for the NFL-only static dashboard."""
from __future__ import annotations

import csv
import html.parser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl"
SITE = ROOT / "docs" / "nfl"
EXPECTED_PAGES = {
    "index.html", "strategies.html", "injuries.html", "correlations.html",
    "validation.html", "leaderboard.html", "questions.html", "suggestions.html",
    "sources.html", "flagged.html",
}
OFFICIAL_HOSTS = (
    "nfl.com", "operations.nfl.com", "nextgenstats.nfl.com", "aglc.ca", "gamesenseab.ca",
    "laws-lois.justice.gc.ca", "scikit-learn.org", "scipy.org",
    "statsmodels.org", "nist.gov",
)
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def is_official_https(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(host == suffix or host.endswith("." + suffix) for suffix in OFFICIAL_HOSTS)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HtmlAudit(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.h1_count = 0
        self.table_rows: list[bool] = []
        self.in_tbody = False
        self.in_row = False
        self.row_has_official = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        if attrs_dict.get("id"):
            self.ids.add(attrs_dict["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and attrs_dict.get("href"):
            href = attrs_dict["href"]
            self.links.append(href)
            if self.in_row and is_official_https(href):
                self.row_has_official = True
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_has_official = False

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_row:
            self.table_rows.append(self.row_has_official)
            self.in_row = False
        if tag == "tbody":
            self.in_tbody = False


def check_sources() -> dict[str, dict[str, str]]:
    path = DATA / "sources.csv"
    sources = load_csv(path)
    if not sources:
        fail("sources.csv is empty")
    result: dict[str, dict[str, str]] = {}
    for line, row in enumerate(sources, start=2):
        source_id = row.get("source_id", "")
        if not source_id or source_id in result:
            fail(f"sources.csv:{line}: missing or duplicate source_id {source_id!r}")
        result[source_id] = row
        if not is_official_https(row.get("url", "")):
            fail(f"sources.csv:{line}: URL is not an approved official HTTPS source: {row.get('url', '')!r}")
        if row.get("status") == "unverified-blank" and not row.get("limits", "").strip():
            fail(f"sources.csv:{line}: unverified-blank source needs an explicit limitation")
    return result


def check_data(sources: dict[str, dict[str, str]]) -> int:
    expected = {
        "strategies.csv": ("strategy_id", "source_id"),
        "signals.csv": ("signal_id", "source_id"),
        "injury_fields.csv": ("field", "source_id"),
        "correlations.csv": ("correlation_id", "source_id"),
        "gates.csv": ("gate_id", "source_id"),
        "leaderboard.csv": ("strategy_id", "source_id"),
        "questions.csv": ("question_id", "source_id"),
        "suggestions.csv": ("suggestion_id", "source_id"),
        "flags.csv": ("flag_id", "source_id"),
    }
    count = 0
    for filename, (key_field, source_field) in expected.items():
        path = DATA / filename
        if not path.exists():
            fail(f"missing data file {filename}")
            continue
        rows = load_csv(path)
        if not rows:
            fail(f"{filename}: no data rows")
        seen: set[str] = set()
        for line, row in enumerate(rows, start=2):
            count += 1
            key = row.get(key_field, "")
            sid = row.get(source_field, "")
            if not key or key in seen:
                fail(f"{filename}:{line}: missing or duplicate {key_field} {key!r}")
            seen.add(key)
            if sid not in sources:
                fail(f"{filename}:{line}: unknown source_id {sid!r}")
            elif not is_official_https(sources[sid].get("url", "")):
                fail(f"{filename}:{line}: its source link is not official HTTPS")
        if filename == "correlations.csv":
            for line, row in enumerate(rows, start=2):
                if row.get("reported value", "").strip():
                    fail(f"{filename}:{line}: empirical correlation must remain blank without verified paired data")
        if filename == "leaderboard.csv":
            for line, row in enumerate(rows, start=2):
                for field in ("rank", "score", "performance result", "reward status"):
                    if row.get(field, "").strip():
                        fail(f"{filename}:{line}: {field} must remain blank; no candidate is qualified")
                if row.get("qualification") != "not eligible":
                    fail(f"{filename}:{line}: candidate cannot be eligible without all evidence gates")
        if filename == "injury_fields.csv":
            for line, row in enumerate(rows, start=2):
                if row.get("live value", "").strip():
                    fail(f"{filename}:{line}: unverified/live NFL field must remain blank in this framework")
    return count


def check_site(sources: dict[str, dict[str, str]]) -> tuple[int, int]:
    pages = {path.name for path in SITE.glob("*.html")}
    if pages != EXPECTED_PAGES:
        fail(f"NFL page set mismatch: missing={sorted(EXPECTED_PAGES-pages)} extra={sorted(pages-EXPECTED_PAGES)}")
    parsers: dict[str, HtmlAudit] = {}
    local_count = 0
    for path in sorted(SITE.glob("*.html")):
        content = path.read_text(encoding="utf-8")
        parser = HtmlAudit()
        parser.feed(content)
        parsers[path.name] = parser
        if parser.h1_count != 1:
            fail(f"{path.name}: expected one h1, got {parser.h1_count}")
        if "<<<<<<<" in content or ">>>>>>>" in content:
            fail(f"{path.name}: merge conflict markers found")
        if "<input" in content.lower():
            fail(f"{path.name}: unexpected manual-input field")
        if path.name != "index.html" and not parser.table_rows:
            fail(f"{path.name}: missing data table")
        for index, sourced in enumerate(parser.table_rows, start=1):
            if not sourced:
                fail(f"{path.name}: table row {index} lacks an official HTTPS source")
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme:
                if not is_official_https(href):
                    fail(f"{path.name}: external link is not an approved official HTTPS URL: {href}")
                continue
            if href.startswith("//"):
                fail(f"{path.name}: protocol-relative URL is forbidden: {href}")
                continue
            if parsed.path:
                target = (SITE / path.name).parent / unquote(parsed.path)
                if not target.resolve().exists():
                    fail(f"{path.name}: broken internal link {href}")
                else:
                    local_count += 1
                    target_name = target.resolve().name
                    if parsed.fragment and target_name in parsers and parsed.fragment not in parsers[target_name].ids:
                        fail(f"{path.name}: broken fragment link {href}")
    if not (SITE / "assets" / "style.css").exists():
        fail("missing NFL stylesheet")
    return sum(len(p.table_rows) for p in parsers.values()), local_count


def main() -> int:
    sources = check_sources()
    data_rows = check_data(sources)
    html_rows, local_links = check_site(sources)
    if ERRORS:
        print("NFL CHECK FAILED")
        for error in ERRORS:
            print(" -", error)
        return 1
    print(f"OK: {len(sources)} source records; {data_rows} evidence rows; {html_rows} rendered table rows each have an official HTTPS source; internal links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
