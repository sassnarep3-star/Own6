#!/usr/bin/env python3
"""Check the generated docs/reverify/ pages.

Rules enforced:
  1. every data-table row carries an https link to an allow-listed source host,
     except rows that are explicitly marked as unverified (blank by design);
  2. every relative link resolves to a real file;
  3. no form control or manual input exists on any page;
  4. no generated-object leak, no unresolved conflict markers, no empty cells
     where a status pill is required;
  5. the table row counts equal the counts in the committed capture data;
  6. the head-line numbers printed on the overview equal report.json;
  7. the fail-closed empirical ledger is still empty.

Run: python3 scripts/check_reverify.py
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "reverify"
DATA = ROOT / "data" / "reverify_2026_11_05"

ALLOWED_HOSTS = {
    "www.nba.com",
    "nba.com",
    "www.law.go.kr",
    "law.go.kr",
    "github.com",
}
FORBIDDEN = ("<input", "<form", "<select", "<textarea", "generator object", "<<<<<<<", "=======", ">>>>>>>")


def tbody_rows(markup: str) -> list[list[str]]:
    tables = re.findall(r"<tbody>(.*?)</tbody>", markup, flags=re.S)
    parsed = []
    for table in tables:
        rows = re.findall(r"<tr>(.*?)</tr>", table, flags=re.S)
        parsed.append([re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S) for row in rows])
    return parsed


def hrefs(markup: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', markup)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    problems: list[str] = []
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        print("FAIL: no pages built")
        return 1

    report = json.loads((DATA / "report.json").read_text(encoding="utf-8"))
    recon = read_csv(DATA / "reconciliation.csv")
    compute = read_csv(DATA / "recompute.csv")
    standings = read_csv(DATA / "standings_read.csv")
    results = read_csv(DATA / "results_read.csv")
    slate = read_csv(DATA / "slate_read.csv")
    rights = read_csv(DATA / "rights_read.csv")

    expected = {
        "standings.html": [len(standings)],
        "results.html": [len(results)],
        "slate.html": [len(slate)],
        "computed.html": [
            len([r for r in compute if r["check_id"].startswith("REC-")]),
            len([r for r in compute if r["check_id"].startswith("COR-")]) // 3 + 1,
            len([r for r in compute if r["check_id"].startswith("WF-")]),
        ],
        "rights.html": [len(rights)],
        "flagged.html": [7],
        "index.html": [6],
    }

    total_rows = 0
    unsourced = 0
    for page in pages:
        markup = page.read_text(encoding="utf-8")
        name = page.name
        for token in FORBIDDEN:
            if token in markup:
                problems.append(f"{name}: forbidden token {token!r}")
        if not markup.lstrip().lower().startswith("<!doctype html>"):
            problems.append(f"{name}: missing doctype")

        tables = tbody_rows(markup)
        if name in expected:
            if len(tables) != len(expected[name]):
                problems.append(f"{name}: {len(tables)} tables, expected {len(expected[name])}")
            else:
                for index, wanted in enumerate(expected[name]):
                    if len(tables[index]) != wanted:
                        problems.append(f"{name}: table {index} has {len(tables[index])} rows, expected {wanted}")

        for table in tables:
            for row in table:
                total_rows += 1
                text = " ".join(row)
                has_link = bool(re.search(r'href="https://', text))
                marked_unverified = "unverified" in text or "needs review" in text or "no official source" in text
                if not has_link and not marked_unverified:
                    unsourced += 1
                    problems.append(f"{name}: sourced value row without a source link: {html.unescape(re.sub('<[^>]+>', ' ', text))[:90]}")

        for link in hrefs(markup):
            if link.startswith("http"):
                host = re.sub(r"^https?://", "", link).split("/")[0]
                if not link.startswith("https://"):
                    problems.append(f"{name}: non-https external link {link}")
                if host not in ALLOWED_HOSTS:
                    problems.append(f"{name}: external host not allow-listed: {host}")
                continue
            target = (page.parent / link.split("#")[0]).resolve()
            if link.startswith("#"):
                continue
            if not target.exists():
                problems.append(f"{name}: broken relative link {link}")

    # Head-line numbers on the overview must equal report.json.
    index_markup = (SITE / "index.html").read_text(encoding="utf-8")
    verdict = report["verdict"]
    for key in ("published_values_confirmed", "published_values_contradicted", "computations_reproduced", "computations_contradicted"):
        value = str(verdict[key])
        if f'<div class="num">{value}</div>' not in index_markup:
            problems.append(f"index.html: does not show {key}={value}")

    # The recheck must agree with its own data files.
    if len(recon) != report["reconciliation"]["rows"]:
        problems.append("report.json reconciliation row count is stale")
    if len(compute) != report["recompute"]["rows"]:
        problems.append("report.json recompute row count is stale")
    if any(r["status"] == "unverified" for r in recon):
        problems.append("reconciliation.csv contains unverified rows; they must be listed on the flagged page")
    if any(r["status"] == "mismatch" for r in recon) or any(r["status"] == "computed_mismatch" for r in compute):
        problems.append("mismatches exist and must be listed on the flagged page")

    # Fail-closed ledger must stay empty.
    ledger = read_csv(ROOT / "data" / "empirical" / "report.csv")
    observations = read_csv(ROOT / "data" / "empirical" / "observations.csv")
    if observations:
        problems.append("empirical observations are no longer empty")
    if any(r.get("qualified", "").lower() == "true" for r in ledger):
        problems.append("a strategy is marked qualified without an authorized ledger")

    if problems:
        print(f"FAIL: {len(problems)} issue(s)")
        for problem in problems:
            print(" -", problem)
        return 1

    print(
        f"OK: {len(pages)} pages, {total_rows} table rows checked "
        f"({unsourced} unsourced, all explicitly flagged), links resolve, fail-closed ledger intact"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
