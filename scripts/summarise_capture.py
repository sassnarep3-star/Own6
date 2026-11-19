#!/usr/bin/env python3
"""Render the capture manifest as a GitHub Actions job summary.

The manifest is the audit record of a capture run: which URL was read, when it
was read, how many bytes came back and what their SHA-256 was. This script
only formats it; it never changes a value.

Run: python3 scripts/summarise_capture.py capture/capture_log.csv
"""

from __future__ import annotations

import csv
import os
import sys

SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: summarise_capture.py <capture_log.csv>")
        return 2
    with open(sys.argv[1], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    lines = [
        "### Official NFL capture manifest",
        "",
        f"{len(rows)} documents read. Each row is one HTTP response.",
        "",
        "| kind | url | status | bytes | sha256 (first 16) | read (UTC) |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        status = row["http_status"] or row["error"] or "?"
        lines.append(
            "| {kind} | {url} | {status} | {bytes} | {sha} | {when} |".format(
                kind=row["kind"],
                url=row["url"][:80],
                status=status,
                bytes=row["bytes"],
                sha=row["sha256"][:16],
                when=row["fetched_at_utc"],
            )
        )
    text = "\n".join(lines) + "\n"
    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
