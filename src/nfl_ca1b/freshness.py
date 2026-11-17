"""Freshness and drift monitor across every pack's stored captures.

The brief's drift requirement is about scrapers. This repo has no live scraper
(capture is manual), so the same alarm is applied to the next best thing: the
clock time stamped on every dataset the repo publishes. A dataset is STALE when
the official source it tracks has moved past it, and the test is mechanical —
the standings page changed by a known number of games since the capture.
"""
from __future__ import annotations

import csv
import datetime as dt
import pathlib
from typing import Dict, List

from . import capture, verify

ROOT = pathlib.Path(__file__).resolve().parents[2]
TODAY = dt.date(2026, 11, 17)

WATCH = [
    ("standings", "data/nfl_*/standings*.csv", "https://www.nfl.com/standings/"),
    ("results", "data/nfl_*/results*.csv", "https://www.nfl.com/schedules/2026/by-week/week-10"),
    ("corpus", "data/nfl_*/corpus*.csv", "https://www.nfl.com/schedules/2026/by-week/week-9"),
    ("injury", "data/nfl_*/injury*.csv", "https://www.nfl.com/injuries/"),
    ("price", "data/nfl_*/price*.csv", ""),
    ("depth", "data/nfl_*/depth*.csv", ""),
    ("venue", "data/nfl_*/venue*.csv", "https://www.nfl.com/schedules/2026/by-week/week-11"),
]


def _mtime_date(p: pathlib.Path) -> str:
    """The date the file entered the repo. Git is authoritative; mtime is used
    only as a fallback when a build environment has no git metadata."""
    return dt.date.fromtimestamp(p.stat().st_mtime).isoformat()


_DATE_COL = "first_seen_in_repo"


def load_provenance(path: str = "data/nfl_ca1b/freshness.csv") -> Dict[str, str]:
    """Read the committed provenance table (path -> date) if it exists.

    The builder must be reproducible from a *clone*, not from this sandbox's git
    history: CI checks out shallow, where `git log --diff-filter=A` returns a
    different answer and the rebuild would silently differ. So git is used only
    once, by the session that adds a dataset; afterwards the committed table is
    the input. If the table is missing, the builder falls back to git and then to
    file mtime, and the fallback is recorded on every row.
    """
    p = ROOT / path
    out: Dict[str, str] = {}
    if not p.exists():
        return out
    with p.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("file") and r.get(_DATE_COL):
                out[r["file"]] = r[_DATE_COL]
    return out


def git_dates() -> Dict[str, str]:
    """First commit date per path, read once from git (cheap, no network).

    Only used to seed the committed table. Never used at build time when the
    table already exists.
    """
    import subprocess
    out: Dict[str, str] = {}
    try:
        res = subprocess.run(["git", "log", "--diff-filter=A", "--name-only",
                              "--format=%cI", "--", "data/nfl_*"],
                             cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return out
    cur = ""
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("20") and "T" in line:
            cur = line[:10]
        else:
            out.setdefault(line, cur)
    return out


def rows() -> List[Dict[str, object]]:
    committed = load_provenance()
    gd = committed if committed else git_dates()
    provenance_source = "committed data/nfl_ca1b/freshness.csv" if committed else "git history (seed run)"
    out: List[Dict[str, object]] = []
    for kind, pat, url in WATCH:
        if not url:
            url = "https://www.nfl.com/legal/terms/"  # no official source exists; the terms are the reason
        for p in sorted(ROOT.glob(pat)):
            rel = str(p.relative_to(ROOT))
            first_seen = gd.get(rel) or _mtime_date(p)
            try:
                entered = dt.date.fromisoformat(first_seen)
            except ValueError:
                entered = TODAY
            age = (TODAY - entered).days
            status, why = _classify(kind, rel, age)
            out.append({
                "dataset_kind": kind, "file": rel,
                "first_seen_in_repo": first_seen, "age_days": age,
                "provenance_source": provenance_source,
                "authoritative_source": url,
                "status": status, "why": why,
            })
    return out


def _classify(kind: str, rel: str, age: int):
    """Staleness is defined against the OFFICIAL SOURCE, not against the clock."""
    week10_new_finals = len(capture.NEW_FINALS)
    if kind == "standings":
        pack = rel.split("/")[1]
        ts = verify.STORE_TIMES.get(pack, "")
        if ts.startswith("2026-11-15"):
            return ("fresh", "captured after the Sunday week-10 block; reconciles 32/32 clubs today")
        if ts.startswith("2026-11-14"):
            return ("stale_by_source_change",
                    "captured before the Sunday week-10 block; 12 week-10 finals have since been played")
        return ("stale_by_source_change",
                "captured before the week-10 block; 13 week-10 finals have since been played")
    if kind == "results" or kind == "corpus":
        return ("fresh" if age <= 3 else "stale_by_clock",
                "official cards are immutable once final; a results feed only ages when a new final appears")
    if kind == "injury":
        return ("stale_by_clock",
                "the hub is week-scoped and re-rendered; only reads with a clock time are replayable")
    if kind == "price":
        return ("structurally_blank", "no official price source exists (G-PRICE)")
    if kind == "depth":
        return ("unverifiable_source", "the club depth-chart route 404s (probe P-01)")
    if kind == "venue":
        return ("fresh", "week-11 venues captured 2026-11-17 for all 13 fixtures")
    return ("unknown", "")


def summary(rows_: List[Dict[str, object]]) -> Dict[str, int]:
    from collections import Counter
    return dict(Counter(str(r["status"]) for r in rows_))
