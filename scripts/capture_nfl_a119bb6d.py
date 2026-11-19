#!/usr/bin/env python3
"""Capture the official NFL Game Books and availability pages, with hashes.

This script is the durable capture tool for session ``a119bb6d``. It is
network-dependent and is meant to run on a scheduled GitHub Actions runner
(``.github/workflows/nfl-a119bb6d-capture.yml``) and locally by a developer who
has ordinary internet access.

What it captures, all from ``nfl.com`` only:

1. the league's own by-week schedule page, used to discover the official game
   centre URLs for that week (nothing is hard-coded);
2. each game's game centre page, used to find the league's "Download Game Book
   (PDF)" link;
3. that Game Book PDF, hashed with SHA-256 and converted to text;
4. the league injury-report hub and the week-specific injury-report URL;
5. the league's weekly game-day inactive-list article;
6. the league's dated schedule-change announcements.

Nothing is interpreted here beyond "which PDF belongs to which game". The
interpretation lives in ``src/nfl_a119bb6d/gamebook.py`` and is run against the
captured text separately, so the parser can be tested without a network.

The PDFs themselves are **not** committed to this repository: the game book
carries the league's own copyright statement. What is committed is the URL, the
SHA-256 and the extracted facts, which is enough for a reviewer to re-download
the file and confirm byte-for-byte that it is the document that was read.

Run:
    python3 scripts/capture_nfl_a119bb6d.py --weeks 10,11 --out /tmp/capture
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_a119bb6d.net import fetch  # noqa: E402

SEASON = 2026
GAME_CENTER_RE = re.compile(
    r"https://www\.nfl\.com/games/([a-z0-9\-]+-%d-reg-\d+)" % SEASON
)
GAMEBOOK_RE = re.compile(
    r"https://static\.www\.nfl\.com/image/upload/[^\"'\s]+/gamecenter/[0-9a-fA-F\-]+\.pdf"
)
STADIUM_RE = re.compile(r"STADIUM\s*([A-Z0-9 &'\.\-]+?)(?:LOCATION|$)")
LOCATION_RE = re.compile(r"LOCATION\s*([A-Z0-9 ,'\.\-]+?)(?:STADIUM|$)")


def write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def pdf_text(data: bytes) -> tuple[str, int]:
    """Return (text, page_count) for a PDF, or ('', 0) if it cannot be read."""
    try:
        from pypdf import PdfReader
    except Exception:  # pragma: no cover - dependency optional at capture time
        return "", 0
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n".join(pages), len(reader.pages)
    except Exception:
        return "", 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weeks", default="10", help="comma separated week numbers")
    ap.add_argument("--out", required=True, help="output directory for the capture")
    ap.add_argument("--season", type=int, default=SEASON)
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    log_rows = []

    def record(kind, url, result, path, note=""):
        log_rows.append(
            {
                "kind": kind,
                "url": url,
                "final_url": result.final_url,
                "http_status": result.status,
                "content_type": result.content_type,
                "bytes": len(result.body),
                "sha256": result.sha256,
                "fetched_at_utc": result.fetched_at_utc,
                "local_path": os.path.relpath(path, out) if path else "",
                "error": result.error,
                "note": note,
            }
        )

    def store(kind, name, url, *, binary=False, note=""):
        result = fetch(url)
        if result.ok:
            if binary:
                path = os.path.join(out, kind, name)
                write_bytes(path, result.body)
            else:
                path = os.path.join(out, kind, name)
                write_text(path, result.text())
        else:
            path = os.path.join(out, kind, name)
            write_text(path, "")
        record(kind, url, result, path, note)
        return result

    # 1. Discover the official game centre URLs from the league's schedule page.
    weeks = [w.strip() for w in args.weeks.split(",") if w.strip()]
    for week in weeks:
        sched_url = (
            f"https://www.nfl.com/schedules/{args.season}/by-week/week-{week}"
        )
        sched = store("schedule", f"week-{week}.html", sched_url, note="schedule page")
        slugs = sorted({m.group(1) for m in GAME_CENTER_RE.finditer(sched.text())})
        if not slugs:
            slugs = sorted(
                {
                    m.group(1)
                    for m in GAME_CENTER_RE.finditer(sched.text())
                    if f"reg-{week}" in m.group(1)
                }
            )
        print(f"week {week}: {len(slugs)} game centre URLs discovered")

        # 2. Game centre page -> Game Book PDF link.
        for slug in slugs:
            gc_url = f"https://www.nfl.com/games/{slug}"
            gc = store("gamecenter", f"{slug}.html", gc_url, note="game centre")
            pdfs = sorted(set(GAMEBOOK_RE.findall(gc.text())))
            if not pdfs:
                print(f"  {slug}: NO GAME BOOK LINK FOUND (html {len(gc.body)} bytes)")
                continue
            pdf_url = pdfs[0]
            pdf = fetch(pdf_url)
            pdf_path = os.path.join(out, "gamebooks", f"{slug}.pdf")
            if pdf.ok:
                write_bytes(pdf_path, pdf.body)
                text, pages = pdf_text(pdf.body)
                write_text(os.path.join(out, "gamebooks", f"{slug}.txt"), text)
                print(f"  {slug}: game book {len(pdf.body)} bytes, {pages} pages")
            else:
                text, pages = "", 0
                write_text(os.path.join(out, "gamebooks", f"{slug}.txt"), "")
                print(f"  {slug}: GAME BOOK FETCH FAILED {pdf.error}")
            record("gamebook", pdf_url, pdf, pdf_path, f"slug={slug}; pages={pages}")

    # 3. The injury-report hub, the week-specific URL, and the inactive article.
    store("pages", "injuries-hub.html", "https://www.nfl.com/injuries/",
          note="injury report hub")
    for week in weeks:
        store(
            "pages",
            f"injuries-reg{week}.html",
            f"https://www.nfl.com/injuries/league/{args.season}/reg{week}",
            note="week-specific injury report",
        )
        for pattern in (
            f"nfl-week-{week}-inactives-players-ruled-out-sunday-{args.season}-season",
            f"nfl-week-{week}-inactives-players-ruled-out-{args.season}-season",
            f"nfl-week-{week}-inactives",
        ):
            url = f"https://www.nfl.com/news/{pattern}"
            result = fetch(url)
            if result.ok and "404" not in result.text()[:4000]:
                path = os.path.join(out, "pages", f"inactives-week-{week}.html")
                write_text(path, result.text())
                record("inactives", url, result, path, f"week={week}")
                print(f"week {week}: inactive article {url}")
                break
        else:
            print(f"week {week}: no official inactive-list article found")

    # 4. The league's dated schedule announcements.
    for slug in ("week-11-schedule-change", "week-12-schedule-change"):
        store("pages", f"{slug}.html", f"https://www.nfl.com/news/{slug}",
              note="dated schedule announcement")

    log_path = os.path.join(out, "capture_log.csv")
    with open(log_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "kind", "url", "final_url", "http_status", "content_type", "bytes",
                "sha256", "fetched_at_utc", "local_path", "error", "note",
            ],
        )
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"capture log: {log_path} ({len(log_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
