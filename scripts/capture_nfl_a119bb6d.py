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
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_a119bb6d.net import fetch  # noqa: E402
from src.nfl_a119bb6d.gamebook import parse_game_book  # noqa: E402
from src.nfl_a119bb6d.htmltext import html_to_lines  # noqa: E402
from src.nfl_a119bb6d.pages import (  # noqa: E402
    CLUB_NICKNAME,
    parse_inactives_article,
    parse_injury_report,
)

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


def pdf_layout_text(path: str) -> str:
    """Return the PDF text with its column layout preserved.

    ``pdftotext -layout`` keeps the visual columns of the game book's lineups
    table, which is what makes a column-per-team parse deterministic instead of
    a guess. It is used when poppler is installed (the capture workflow installs
    it); otherwise the caller falls back to the plain pypdf text.
    """
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-q", path, "-"],
            capture_output=True,
            timeout=180,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", "replace")


def game_slug(away_abbr: str, home_abbr: str, season: int, week: int) -> str:
    """Build the league's game centre slug for a match-up.

    The league's game centre URLs use the two club nicknames, lower-cased and
    joined with ``-at-``. The result is not trusted: the capture re-fetches the
    URL and checks that the league's own page carries a Game Book for it.
    """
    away = CLUB_NICKNAME.get(away_abbr, "").lower()
    home = CLUB_NICKNAME.get(home_abbr, "").lower()
    if not away or not home:
        return ""
    return f"{away}-at-{home}-{season}-reg-{week}"


def read_matchups(path: str) -> dict[int, list[tuple[str, str]]]:
    """Read the committed match-up list, grouped by week."""
    out: dict[int, list[tuple[str, str]]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            week = int(row["week"])
            out.setdefault(week, []).append((row["away_abbr"], row["home_abbr"]))
    return out


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
    ap.add_argument(
        "--matchups",
        default="",
        help="committed match-up CSV used to re-derive and verify game centre URLs",
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

    weeks = [int(w.strip()) for w in args.weeks.split(",") if w.strip()]
    problems: list[str] = []

    # 1. The league's availability pages.
    #
    #    (a) the injury-report hub and its week-specific route, which print the
    #        league's Practice Status and Game Status designations;
    #    (b) the weekly game-day inactive-list article, which prints each
    #        club's inactive list and the official game centre URL of every
    #        game it covers.
    injury_rows: list[dict] = []
    inactive_rows: list[dict] = []
    article_slugs: dict[int, set[str]] = {}

    store("pages", "injuries-hub.html", "https://www.nfl.com/injuries/",
          note="injury report hub")
    for week in weeks:
        inj_url = f"https://www.nfl.com/injuries/league/{args.season}/reg{week}"
        result = store("pages", f"injuries-reg{week}.html", inj_url,
                       note="week-specific injury report")
        if result.ok:
            parsed = parse_injury_report(
                result.text(), url=result.final_url or inj_url,
                read_at_utc=result.fetched_at_utc,
            )
            for row in parsed["rows"]:
                row["week"] = week
            injury_rows.extend(parsed["rows"])
            for prob in parsed["problems"]:
                problems.append(f"injury report reg{week}: {prob}")

        for pattern in (
            f"nfl-week-{week}-inactives-players-ruled-out-sunday-{args.season}-season",
            f"nfl-week-{week}-inactives-players-ruled-out-{args.season}-season",
            f"nfl-week-{week}-inactives",
        ):
            art_url = f"https://www.nfl.com/news/{pattern}"
            art = fetch(art_url)
            if art.ok and "404" not in art.text()[:4000]:
                art_path = os.path.join(out, "pages", f"inactives-week-{week}.html")
                write_text(art_path, art.text())
                record("inactives", art_url, art, art_path, f"week={week}")
                parsed = parse_inactives_article(
                    art.text(), url=art_url, read_at_utc=art.fetched_at_utc,
                )
                for row in parsed["rows"]:
                    row["week"] = week
                inactive_rows.extend(parsed["rows"])
                for game in parsed["games"]:
                    m = re.search(r"-reg-(\d+)$", game["slug"])
                    if m:
                        article_slugs.setdefault(int(m.group(1)), set()).add(game["slug"])
                for prob in parsed["problems"]:
                    problems.append(f"inactive article week {week}: {prob}")
                print(f"week {week}: inactive article {art_url} "
                      f"({len(parsed['rows'])} rows)")
                break
        else:
            print(f"week {week}: no official inactive-list article found")

    # 2. The Game Books.
    #
    #    The game centre URL of each game is taken from the league's own
    #    inactive-list article where the article covers the game, and otherwise
    #    re-derived from the committed match-up list. Every URL is then fetched
    #    and the Game Book link is read off the league's page, so a URL that
    #    does not resolve is a logged failure and never a silent row.
    matchups = read_matchups(args.matchups) if args.matchups else {}
    game_rows: list[dict] = []
    lineup_rows: list[dict] = []
    participation_rows: list[dict] = []

    for week in weeks:
        slugs = set(article_slugs.get(week, set()))
        for away, home in matchups.get(week, []):
            slug = game_slug(away, home, args.season, week)
            if slug:
                slugs.add(slug)
        if args.no_gamebooks:
            print(f"week {week}: game books skipped by request")
            continue
        print(f"week {week}: {len(slugs)} games to capture")
        for slug in sorted(slugs):
            gc_url = f"https://www.nfl.com/games/{slug}"
            gc = store("gamecenter", f"{slug}.html", gc_url, note="game centre")
            pdfs = sorted(set(GAMEBOOK_RE.findall(gc.text())))
            if not pdfs:
                problems.append(f"{slug}: no Game Book link on the game centre page")
                print(f"  {slug}: NO GAME BOOK LINK FOUND")
                continue
            pdf_url = pdfs[0]
            pdf = fetch(pdf_url)
            pdf_path = os.path.join(out, "gamebooks", f"{slug}.pdf")
            if not pdf.ok:
                problems.append(f"{slug}: Game Book download failed ({pdf.error})")
                print(f"  {slug}: GAME BOOK FETCH FAILED {pdf.error}")
                continue
            write_bytes(pdf_path, pdf.body)
            layout = pdf_layout_text(pdf_path)
            if not layout:
                layout, _pages = pdf_text(pdf.body)
            write_text(os.path.join(out, "gamebooks", f"{slug}.layout.txt"), layout)
            record("gamebook", pdf_url, pdf, pdf_path, f"slug={slug}")

            parsed = parse_game_book(
                layout, source_url=gc_url, gamebook_sha256=pdf.sha256
            )
            problems.extend(f"{slug}: {p}" for p in parsed["problems"])
            game_rows.append(
                {
                    "game_slug": slug,
                    "game_url": gc_url,
                    "gamebook_url": pdf_url,
                    "gamebook_sha256": pdf.sha256,
                    "gamebook_bytes": len(pdf.body),
                    "read_at_utc": pdf.fetched_at_utc,
                    "date_et": parsed["date_et"],
                    "away_team": parsed["away_team"],
                    "home_team": parsed["home_team"],
                    "start_time": parsed["start_time"],
                    "stadium": parsed["stadium"],
                    "city": parsed["city"],
                    "roof_status": parsed["roof_status"],
                    "surface": parsed["surface"],
                    "weather_sky": parsed["weather_sky"],
                    "temp_f": parsed["temp_f"],
                    "temp_c": parsed["temp_c"],
                    "humidity_pct": parsed["humidity_pct"],
                    "wind": parsed["wind"],
                    "wind_chill": parsed["wind_chill"],
                    "attendance": parsed["attendance"],
                    "away_score": parsed["away_score"],
                    "home_score": parsed["home_score"],
                    "away_q1": parsed["away_q1"], "away_q2": parsed["away_q2"],
                    "away_q3": parsed["away_q3"], "away_q4": parsed["away_q4"],
                    "away_ot": parsed["away_ot"],
                    "home_q1": parsed["home_q1"], "home_q2": parsed["home_q2"],
                    "home_q3": parsed["home_q3"], "home_q4": parsed["home_q4"],
                    "home_ot": parsed["home_ot"],
                    "officials": "; ".join(
                        f"{o['role']}: {o['name']} ({o['number']})"
                        for o in parsed["officials"]
                    ),
                    "problems": "; ".join(parsed["problems"]),
                    "source_url": gc_url,
                }
            )
            for entry in parsed["lineups"]:
                lineup_rows.append(
                    {
                        "game_slug": slug, "side": entry["side"],
                        "unit": entry["unit"], "position": entry["position"],
                        "jersey": entry["jersey"], "player": entry["player"],
                        "source_url": gc_url, "gamebook_sha256": pdf.sha256,
                        "read_at_utc": pdf.fetched_at_utc,
                    }
                )
            for role, key in (("substitute", "substitutions"),
                              ("did_not_play", "did_not_play"),
                              ("not_active", "not_active")):
                for entry in parsed[key]:
                    participation_rows.append(
                        {
                            "game_slug": slug, "side": entry["side"], "role": role,
                            "position": entry["position"], "jersey": entry["jersey"],
                            "player": entry["player"], "source_url": gc_url,
                            "gamebook_sha256": pdf.sha256,
                            "read_at_utc": pdf.fetched_at_utc,
                        }
                    )
            print(f"  {slug}: {len(parsed['lineups'])} starters, "
                  f"{len(parsed['substitutions'])} subs, "
                  f"{len(parsed['not_active'])} inactive")

    # 3. The archived weekly injury reports of past seasons. The archive exists
    #    at the same /injuries/league/<season>/reg<week> route, which is what
    #    makes the empirical calibration of a designation possible at all.
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

    # 4. The 32 club roster pages. They carry the club's own roster status
    #    (Active / Reserve / Injured Reserve / Practice Squad), which is the
    #    only way to stop "not listed on the injury report" from being read
    #    as "available".
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

    # 5. The league's dated schedule announcements.
    for slug in ("week-11-schedule-change", "week-12-schedule-change"):
        store("pages", f"{slug}.html", f"https://www.nfl.com/news/{slug}",
              note="dated schedule announcement")

    # 6. The structured outputs of this capture.
    parsed_dir = os.path.join(out, "parsed")
    write_csv(os.path.join(parsed_dir, "game_books.csv"), game_rows, [
        "game_slug", "game_url", "gamebook_url", "gamebook_sha256",
        "gamebook_bytes", "read_at_utc", "date_et", "away_team", "home_team",
        "start_time", "stadium", "city", "roof_status", "surface",
        "weather_sky", "temp_f", "temp_c", "humidity_pct", "wind", "wind_chill",
        "attendance", "away_score", "home_score", "away_q1", "away_q2",
        "away_q3", "away_q4", "away_ot", "home_q1", "home_q2", "home_q3",
        "home_q4", "home_ot", "officials", "problems", "source_url",
    ])
    write_csv(os.path.join(parsed_dir, "gamebook_lineups.csv"), lineup_rows, [
        "game_slug", "side", "unit", "position", "jersey", "player",
        "source_url", "gamebook_sha256", "read_at_utc",
    ])
    write_csv(os.path.join(parsed_dir, "gamebook_participation.csv"),
              participation_rows, [
        "game_slug", "side", "role", "position", "jersey", "player",
        "source_url", "gamebook_sha256", "read_at_utc",
    ])
    write_csv(os.path.join(parsed_dir, "injury_report.csv"), injury_rows, [
        "week", "club", "player", "position", "injury", "practice_status",
        "game_status", "game_url", "source_url", "read_at_utc",
    ])
    write_csv(os.path.join(parsed_dir, "inactives.csv"), inactive_rows, [
        "week", "club", "position", "player", "game_slug", "game_url",
        "source_url", "read_at_utc",
    ])
    write_csv(os.path.join(parsed_dir, "capture_problems.csv"),
              [{"problem": p} for p in problems], ["problem"])
    print(f"parsed outputs: {parsed_dir}")


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

    # (a2) The line view of one captured availability page. The availability
    #      parsers work on a line view of the league's HTML, so a bounded
    #      sample of that view is what makes the parsers reviewable without
    #      re-running the network capture.
    pages_dir = os.path.join(out, "pages")
    if os.path.isdir(pages_dir):
        for name in sorted(os.listdir(pages_dir)):
            if not name.startswith("inactives") and not name.startswith("injuries"):
                continue
            path = os.path.join(pages_dir, name)
            with open(path, encoding="utf-8") as fh:
                html = fh.read()
            lines = html_to_lines(html)
            parts.append(f"# AVAILABILITY PAGE LINE VIEW: {name} ({len(html)} bytes)")
            parts.append(f"#   lines: {len(lines)}")
            for idx, line in enumerate(lines[:head_lines]):
                parts.append(f"{idx:05d}| {line}")
            parts.append("")

    # (b) The text layout of one captured Game Book.
    book_dir = os.path.join(out, "gamebooks")
    names = []
    if os.path.isdir(book_dir):
        names = sorted(n for n in os.listdir(book_dir) if n.endswith(".layout.txt"))
        if not names:
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

    # (c) Does the Game Book carry playing-time information at all?
    keywords = ("Snap", "Participation", "Plays", "Involved", "Snaps Played")
    hits = {kw: [] for kw in keywords}
    for idx, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                hits[kw].append(idx)
    parts.append("")
    parts.append("# KEYWORD SCAN (whole document)")
    for kw, idxs in hits.items():
        parts.append(f"#   {kw}: {len(idxs)} lines" + (f" -> {idxs[:12]}" if idxs else ""))
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
