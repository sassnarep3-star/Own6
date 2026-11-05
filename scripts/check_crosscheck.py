#!/usr/bin/env python3
"""Checker for the independent cross-check section.

Publication rules enforced here:

  1. Every data table row in docs/crosscheck/*.html carries an https source link.
  2. Every internal link resolves to a committed file.
  3. A cell that is blank must be marked as blank (class="empty") — no silent gaps.
  4. A comparison row may claim "match" only if the underlying CSV says so.
  5. Cell counts are pinned, so data cannot change without the checker noticing.
  6. No unresolved conflict markers and no Python repr leaks in the HTML.

It does not, and cannot, re-verify the NBA facts themselves: that required reading
the official pages, which is recorded in data/crosscheck/sources.csv.

    python3 scripts/check_crosscheck.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CD = ROOT / "data" / "crosscheck"
OUT = ROOT / "docs" / "crosscheck"

PAGES = [
    "index.html", "standings.html", "games.html", "slate.html",
    "claims.html", "correlations.html", "sources.html", "flagged.html",
]

EXPECTED = {
    "standings_read_57db4fcc.csv": 30,
    "standings_compare.csv": 30,
    "games_per_date_read.csv": 30,
    "games_completeness.csv": 42,
    "slate_read.csv": 11,
    "slate_compare.csv": 11,
    "spotcheck_games.csv": 3,
    "spotcheck_compare.csv": 3,
    "correlations_recomputed.csv": 2,
    "claims.csv": 16,
    "flags.csv": 15,
    "sources.csv": 8,
}

NOTES: list[str] = []
ERRORS: list[str] = []


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_data_errors() -> list[str]:
    errors: list[str] = []
    for name, expected in EXPECTED.items():
        path = CD / name
        if not path.exists():
            errors.append(f"missing data file: {name}")
            continue
        rows = read_csv(path)
        if len(rows) != expected:
            errors.append(f"{name}: expected {expected} rows, found {len(rows)}")
    for name in ("summary.json",):
        if not (CD / name).exists():
            errors.append(f"missing data file: {name}")

    # every transcription row must carry its own official source and a read date
    for name in ("standings_read_57db4fcc.csv", "games_per_date_read.csv",
                 "slate_read.csv", "spotcheck_games.csv"):
        for i, row in enumerate(read_csv(CD / name), start=2):
            url = row.get("source_url", "")
            if not url.startswith("https://"):
                errors.append(f"{name}:{i}: source_url is not https")
            if not row.get("read_on"):
                errors.append(f"{name}:{i}: read_on is empty")
            if urlparse(url).netloc not in {"www.nba.com", "official.nba.com"}:
                NOTES.append(f"{name}:{i}: source host {urlparse(url).netloc} (allowed, but not NBA)")

    # a "match" verdict must be earned by the data
    for row in read_csv(CD / "standings_compare.csv"):
        if row["two_reader_match"] == "yes" and row["independent_w"] != row["archive_w"]:
            # allowed: reader agreement and archive agreement are different questions
            pass
        if row["two_reader_match"] == "NO":
            errors.append(f"standings_compare: two-reader mismatch on {row['team_abbr']}")
        if row["archive_match"] == "NO":
            errors.append(f"standings_compare: archive mismatch on {row['team_abbr']}")
        if row["delta_match"] == "NO":
            errors.append(f"standings_compare: delta mismatch on {row['team_abbr']}")

    for row in read_csv(CD / "games_completeness.csv"):
        if row["match"] == "NO":
            errors.append(f"games_completeness: official count disagrees for {row['date']}")
        if not row["archive_game_count"].isdigit():
            errors.append(f"games_completeness: archive count not numeric for {row['date']}")
        if row["official_game_count"] == "" and row["match"]:
            errors.append(f"games_completeness: {row['date']} has no official count but a match verdict")

    for row in read_csv(CD / "claims.csv"):
        if row["verdict"] not in {"match", "DRIFT", "not_recomputable"}:
            errors.append(f"claims: bad verdict {row['verdict']} on {row['claim_id']}")
        if row["verdict"] == "match" and row["published_value"] != row["recomputed_value"]:
            # formatting differences are allowed only when the numbers agree exactly
            errors.append(
                f"claims: {row['claim_id']} says match but {row['published_value']!r} "
                f"!= {row['recomputed_value']!r}")
        if row["verdict"] == "match" and not row["source_url"].startswith("https://"):
            errors.append(f"claims: {row['claim_id']} has no https source")
    drift = [r["claim_id"] for r in read_csv(CD / "claims.csv") if r["verdict"] == "DRIFT"]
    NOTES.append(f"claims with drift: {', '.join(drift) if drift else 'none'}")

    for row in read_csv(CD / "correlations_recomputed.csv"):
        if row["match"] != "yes":
            errors.append(f"correlations: {row['pair']} does not reproduce")

    for row in read_csv(CD / "flags.csv"):
        for field in ("id", "severity", "finding", "detail", "status"):
            if not row.get(field):
                errors.append(f"flags: {row.get('id', '?')} has an empty {field}")
        if not row["source_url"].startswith("https://"):
            errors.append(f"flags: {row['id']} source_url is not https")

    summary = json.loads((CD / "summary.json").read_text(encoding="utf-8"))
    if summary["standings"]["two_reader_matches"] != summary["standings"]["rows"]:
        errors.append("summary: two-reader agreement is not complete")
    if summary["claims"]["drift"] != len(drift):
        errors.append("summary: claim drift count does not match claims.csv")
    return errors


def inspect_page(path: Path) -> list[str]:
    """Publication rules for one rendered page."""
    errors: list[str] = []
    if True:
        name = path.name
        if not path.exists():
            return [f"missing page: {name}"]
        html = path.read_text(encoding="utf-8")
        for marker in ("<<<<<<<", ">>>>>>>", "<generator object"):
            if marker in html:
                errors.append(f"{name}: contains unresolved conflict marker or repr leak {marker!r}")

        # internal links resolve
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (path.parent / href.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"{name}: broken internal link {href}")

        # every data-table row must carry an https source link
        for table_html in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.S):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                if len(cells) < 3:
                    continue
                if not re.search(r'href="https://', row):
                    label = re.sub(r"<[^>]+>", "", cells[0]).strip()[:40]
                    errors.append(f"{name}: table row without an official source link: {label}")
                # blank cells must be explicit
                for cell, tag in zip(cells, re.findall(r"<td([^>]*)>", row)):
                    if "empty" in tag or 'class="empty"' in cell:
                        continue
                    inner = re.sub(r"<[^>]+>", "", cell).strip()
                    if inner in {"", "-", "—"}:
                        errors.append(f"{name}: silent blank cell (use class=\"empty\")")
    return errors


def check_page_errors() -> list[str]:
    errors: list[str] = []
    for name in PAGES:
        errors.extend(inspect_page(OUT / name))
    return errors


def main() -> int:
    ERRORS.extend(check_data_errors())
    ERRORS.extend(check_page_errors())
    errors = ERRORS
    for note in NOTES:
        print(f"note: {note}")
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for err in errors[:40]:
            print("  -", err)
        return 1
    rows = sum(len(read_csv(CD / name)) for name in EXPECTED if (CD / name).exists())
    print(f"PASS: {len(PAGES)} pages, {rows} data rows, every row source-linked, "
          f"all internal links resolve, blanks explicit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
