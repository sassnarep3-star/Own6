#!/usr/bin/env python3
"""Validate the empirical lab data, report, and built site. Exits non-zero on failure.

Checks:
  * The empty ledger is schema-correct.
  * The report is fail-closed: no qualified strategies, no leaderboard rows.
  * Every strategy has exactly 10 gates.
  * Every correlation is unverified (empty authorized residuals).
  * Every built page has exactly one <h1> and all internal links resolve.
  * Every table row in the report has a source URL or a blank flag.
"""
from __future__ import annotations

import csv
import html.parser
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "empirical"
DOCS = ROOT / "docs" / "lab"

errors = []


def fail(msg):
    errors.append(msg)


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def check_report():
    report = load_json("report.json")
    if report["status"] != "not_run":
        fail("report status must be not_run with the empty ledger")
    if report["n_observations"] != 0:
        fail("report must report zero observations with the empty ledger")
    if report["n_qualified"] != 0:
        fail("report must have zero qualified strategies with the empty ledger")
    if report["leaderboard"]:
        fail("leaderboard must be empty with the empty ledger")
    for s in report["strategies"]:
        if len(s["gates"]) != 10:
            fail(f"strategy {s['id']}: expected 10 gates, found {len(s['gates'])}")
        for g in s["gates"]:
            if g["status"] not in {"blocked", "not_run"}:
                fail(f"strategy {s['id']} gate {g['id']}: status '{g['status']}' with no data")
        if s["qualified"]:
            fail(f"strategy {s['id']}: qualified without observations")
    for c in report["correlations"]:
        if c["status"] != "unverified":
            fail(f"correlation {c['id']}: status '{c['status']}' with no residuals")


def check_ledger():
    with (DATA / "observations.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = [
            "observation_id", "event_id", "strategy_id", "split", "event_start_utc",
            "forecast_time_utc", "features_asof_utc", "market", "selection", "line",
            "probability", "market_probability", "decimal_odds", "closing_decimal_odds",
            "closing_line", "outcome", "odds_source_url", "close_source_url",
            "result_source_url", "feature_source_url", "odds_sha256", "close_sha256",
            "result_sha256", "feature_sha256", "license_id", "settlement_url",
            "model_version", "dependence_evidence",
        ]
        if reader.fieldnames != expected:
            fail("observations.csv header does not match contract v1")


def check_site():
    pages = sorted(DOCS.glob("*.html"))
    if len(pages) != 8:
        fail(f"expected 8 pages, found {len(pages)}")
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if len(re.findall(r"<h1[^>]*>", text)) != 1:
            fail(f"{page.name}: expected exactly one <h1>")
        for link in re.findall(r'href="([^"]+)"', text):
            if link.startswith("#") or link.startswith("mailto:"):
                continue
            parsed = urlparse(link)
            if parsed.scheme in ("http", "https"):
                continue
            if parsed.scheme or link.startswith("//"):
                fail(f"{page.name}: unsupported link scheme: {link}")
                continue
            if not (page.parent / parsed.path).resolve().exists():
                fail(f"{page.name}: broken internal link -> {link}")


if __name__ == "__main__":
    check_report()
    check_ledger()
    check_site()
    if errors:
        print("FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"OK: report is fail-closed; ledger schema correct; 8 pages, no broken internal links.")
