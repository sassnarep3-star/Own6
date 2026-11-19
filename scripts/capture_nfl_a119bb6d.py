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
    r"(?:https://www\.nfl\.com)?/games/([a-z0-9\-]+-%d-reg-\d+)" % SEASON
)
GAMEBOOK_RE = re.compile(
    r"https://static\.www\.nfl\.com/image/upload/[^\"'\s]+/gamecenter/[0-9a-fA-F\-]+\.pdf"
)
STADIUM_RE = re.compile(r"STADIUM\s*([A-Z0-9 &'\.\-]+?)(?:LOCATION|$)")
LOCATION_RE = re.compile(r"LOCATION\s*([A-Z0-9 ,'\.\-]+?)(?:STADIUM|$)")

#: The 32 club slugs the league uses in ``/teams/<slug>/`` URLs.
CLUB_SLUGS = [
    "arizona-cardinals", "atlanta-falcons", "baltimore-ravens", "buffalo-bills",
    "carolina-panthers", "chicago-bears", "cincinnati-bengals", "cleveland-browns",
    "dallas-cowboys", "denver-broncos", "detroit-lions", "green-bay-packers",
    "houston-texans", "indianapolis-colts", "jacksonville-jaguars",
    "kansas-city-chiefs", "las-vegas-raiders", "los-angeles-chargers",
    "los-angeles-rams", "miami-dolphins", "minnesota-vikings",
    "new-england-patriots", "new-orleans-saints", "new-york-giants", "new-york-jets",
    "philadelphia-eagles", "pittsburgh-steelers", "san-francisco-49ers",
    "seattle-seahawks", "tampa-bay-buccaneers", "tennessee-titans",
    "washington-commanders",
]


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
    ap.add_argument(
        "--archive-seasons",
        default="",
        help="comma separated past seasons whose weekly injury reports are archived",
    )
    ap.add_argument(
        "--archive-last-reg",
        type=int,
        default=18,
        help="number of regular-season weeks archived per past season",
    )
    ap.add_argument(
        "--rosters",
        action="store_true",
        help="capture the 32 official club roster pages (roster status per player)",
    )
    ap.add_argument(
        "--no-gamebooks",
        action="store_true",
        help="skip the game centre and Game Book capture (injury pages only)",
    )
    ap.add_argument(
        "--diagnostic",
        default="",
        help="write a bounded structural diagnostic of one Game Book to this path",
    )
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
        slugs = sorted(
            {
                m.group(1)
                for m in GAME_CENTER_RE.finditer(sched.text())
                if m.group(1).endswith(f"reg-{week}")
            }
        )
        print(f"week {week}: {len(slugs)} game centre URLs discovered")
        if not slugs:
            print(f"week {week}: no '/games/<slug>-reg-{week}' link found in the page")

        # 2. Game centre page -> Game Book PDF link.
        for slug in (slugs if not args.no_gamebooks else []):
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

    # 3b. The weekly injury reports of past seasons. The archive exists at the
    #     same /injuries/league/{season}/reg{week} route, which is what makes the
    #     empirical calibration of a designation possible at all.
    for season in [s.strip() for s in args.archive_seasons.split(",") if s.strip()]:
        for reg in range(1, args.archive_last_reg + 1):
            url = f"https://www.nfl.com/injuries/league/{season}/reg{reg}"
            result = fetch(url)
            path = os.path.join(out, "archive", f"injuries-{season}-reg{reg}.html")
            if result.ok:
                write_text(path, result.text())
            else:
                write_text(path, "")
            record("archive", url, result, path, f"season={season}; reg={reg}")
        print(f"season {season}: {args.archive_last_reg} weekly injury reports captured")

    # 3c. The 32 club roster pages. They carry the club's own roster status
    #     (Active / Reserve / Injured Reserve / Practice Squad), which is the
    #     only way to stop "not listed on the injury report" from being read
    #     as "available".
    if args.rosters:
        for slug in CLUB_SLUGS:
            url = f"https://www.nfl.com/teams/{slug}/roster/"
            result = fetch(url)
            path = os.path.join(out, "rosters", f"{slug}.html")
            if result.ok:
                write_text(path, result.text())
            else:
                write_text(path, "")
            record("roster", url, result, path, f"club={slug}")
        print(f"rosters: {len(CLUB_SLUGS)} club roster pages captured")

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

    # 5. A bounded structural diagnostic. It exists so the parser can be written
    #    and tested against the real text layout of the PDF without anyone
    #    having to eyeball a fifty-page document. It is a short extract of one
    #    document, not a redistribution of the league's file.
    if args.diagnostic:
        write_text(args.diagnostic, build_diagnostic(out))
        print(f"diagnostic: {args.diagnostic}")
    return 0


MARKERS = (
    "Lineups", "Substitutions", "Did Not Play", "Not Active",
    "Field Goals", "Scoring Plays", "Paid Attendance", "Final Individual",
)


def build_diagnostic(out: str, *, head_lines: int = 130) -> str:
    """Return a bounded extract of one captured Game Book's text."""
    parts: list[str] = []

    # (a) How the schedule page encodes its game links.
    sched_dir = os.path.join(out, "schedule")
    if os.path.isdir(sched_dir):
        for name in sorted(os.listdir(sched_dir)):
            path = os.path.join(sched_dir, name)
            if not name.endswith(".html"):
                continue
            with open(path, encoding="utf-8") as fh:
                html = fh.read()
            parts.append(f"# SCHEDULE PAGE SAMPLE: {name} ({len(html)} bytes)")
            hits = [m.start() for m in re.finditer(r"/games/", html)]
            parts.append(f"# occurrences of '/games/': {len(hits)}")
            for pos in hits[:6]:
                snippet = html[max(0, pos - 160): pos + 160].replace("\n", " ")
                parts.append(f"#   ...{snippet}...")
            parts.append("")

    # (b) The text layout of one captured Game Book.
    book_dir = os.path.join(out, "gamebooks")
    names = []
    if os.path.isdir(book_dir):
        names = sorted(n for n in os.listdir(book_dir) if n.endswith(".txt"))
    if not names:
        parts.append("no game books captured")
        return "\n".join(parts) + "\n"
    path = os.path.join(book_dir, names[0])
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    keep = list(range(min(head_lines, len(lines))))
    for idx, line in enumerate(lines):
        if any(marker in line for marker in MARKERS) and idx not in keep:
            keep.append(idx)
    keep = sorted(set(keep))
    parts.append(f"# GAME BOOK SAMPLE: {names[0]}")
    parts.append(f"# lines shown: {len(keep)} of {len(lines)}")
    parts.append("")
    for idx in keep:
        parts.append(f"{idx:05d}| {lines[idx]}")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
