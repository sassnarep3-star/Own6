#!/usr/bin/env python3
"""Fail-closed DFC0 decision-board freshness check; no external requests.

Counts are repository-register metadata only. Landing-page findings owned by a
concurrent integration are warnings, never facts or a failing gate here.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_dfc0c1bc"
BOARD = ROOT / "docs" / "nfl-dfc0c1bc" / "index.html"

# Frozen portal counters. Any source-register change requires a deliberate review.
EXPECTED = {
    "registers": 29,
    "suggestions": 197,
    "questions": 188,
    "gaps": 13,
    "paths": 16,
}
FILES = {
    "registers": "suggestions_inventory.csv",
    "suggestions": "suggestions_master.csv",
    "questions": "questions_master.csv",
    "gaps": "information_gaps.csv",
    "paths": "decision_paths.csv",
}
BOARD_TARGETS = ("suggestions.html", "questions.html", "gaps.html", "paths.html")


def csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def row_counts() -> dict[str, int]:
    return {key: csv_rows(DATA / filename) for key, filename in FILES.items()}


def _has_count_and_label(text: str, count: int, label: str) -> bool:
    normalized_text = text.casefold().replace("-", " ")
    normalized_label = label.casefold().replace("-", " ")
    return bool(re.search(rf"\b{count}\b", text)) and normalized_label in normalized_text


def portal_warnings() -> list[str]:
    """Return non-blocking landing issues that require the owning integration."""
    warnings: list[str] = []
    root = (ROOT / "index.html").read_text(encoding="utf-8")
    section_match = re.search(
        r"<section\b(?=[^>]*\bid=[\"']suggestions[\"'])[^>]*>.*?</section>",
        root,
        flags=re.IGNORECASE | re.DOTALL,
    )
    section = section_match.group(0) if section_match else ""
    if not section:
        warnings.append("U-F01: root portal has no #suggestions section")
    elif not all(f'href="docs/nfl-dfc0c1bc/{target}"' in section for target in BOARD_TARGETS):
        warnings.append("U-F01: root #suggestions does not directly expose the consolidated DFC0 review pages")
    if re.search(r"\b159\s+suggestions\b|\b176\s+(?:open\s+)?questions\b", root, re.I):
        warnings.append("U-F02: root portal still contains the stale 159/176 cross-pack counters")

    docs_hub = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    card_match = re.search(
        r"<a\b(?=[^>]*\bclass=[\"']category[\"'])(?=[^>]*\bhref=[\"']nfl-dfc0c1bc/index\.html[\"'])[^>]*>.*?</a>",
        docs_hub,
        flags=re.IGNORECASE | re.DOTALL,
    )
    card = card_match.group(0) if card_match else ""
    if not card or re.search(r"\b159\s+suggestions\b|\b176\s+(?:open\s+)?questions\b", card, re.I):
        warnings.append("U-F02: docs/index.html cross-pack card is missing or carries stale 159/176 counters")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "docs/nfl-dfc0c1bc/index.html" not in readme:
        warnings.append("U-F01: README Start-here section lacks a direct cross-pack board entry")
    if re.search(r"26 inventory rows|159 suggestions|176 questions|35 source rows", (DATA / "README.md").read_text(encoding="utf-8"), re.I):
        warnings.append("U-F03: DFC0 README counts differ from the committed register files")
    summary_path = ROOT / "NFL_DFC0C1BC_EXECUTIVE_SUMMARY.md"
    if summary_path.exists() and re.search(r"159 suggestions|176 questions", summary_path.read_text(encoding="utf-8"), re.I):
        warnings.append("U-F03: DFC0 executive summary contains superseded 159/176 counts")
    return warnings


def check() -> list[str]:
    errors: list[str] = []
    actual = row_counts()
    for key, expected in EXPECTED.items():
        if actual[key] != expected:
            errors.append(
                f"{FILES[key]} has {actual[key]} rows; portal pin is {expected}. "
                "Review before changing the pinned values."
            )

    if not BOARD.is_file():
        return errors + ["DFC0 generated index page is missing"]
    board = BOARD.read_text(encoding="utf-8")
    for key, label in (
        ("registers", "register"),
        ("suggestions", "suggestion"),
        ("questions", "question"),
        ("gaps", "information gap"),
        ("paths", "decision"),
    ):
        if not _has_count_and_label(board, EXPECTED[key], label):
            errors.append(
                f"DFC0 generated index does not state the pinned {key} count "
                f"({EXPECTED[key]}) with label '{label}'"
            )
    for target in BOARD_TARGETS:
        if f'href="{target}"' not in board:
            errors.append(f"DFC0 generated index does not link to {target}")
        elif not (BOARD.parent / target).is_file():
            errors.append(f"DFC0 generated index target is missing: {target}")
    return errors


def main() -> int:
    counts = row_counts()
    errors = check()
    warnings = portal_warnings()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        "OK — DFC0 page matches committed repository registers "
        f"({counts['registers']} registers; {counts['suggestions']} suggestions; "
        f"{counts['questions']} questions; {counts['gaps']} gaps; {counts['paths']} paths); "
        "direct review-page links resolve. No NFL factual or market claims checked."
    )
    for warning in warnings:
        print(f"WARNING / needs review: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
