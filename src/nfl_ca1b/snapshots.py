"""Point-in-time snapshot ledger: one immutable entry per capture, hash-chained.

The ledger is what makes a backtest honest. Each entry records (a) the exact URL,
(b) the clock time, (c) a SHA-256 over the canonical form of everything captured,
and (d) the previous entry's hash. Any later edit to a captured value breaks the
chain, which the verifier re-computes on every build.

This cannot replace scheduled daily capture (that needs the owner's decision on
the retrieval-terms question, Q-01). It does mean every capture this repo already
holds becomes replayable as of a stated clock time instead of being undated.
"""
from __future__ import annotations

import hashlib
import csv
import pathlib
from typing import Dict, List

from . import capture

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _canon(rows: List[Dict[str, object]], keys: List[str]) -> str:
    return "\n".join("|".join(str(r.get(k, "")) for k in keys) for r in rows)


def chain() -> List[Dict[str, object]]:
    """The ledger, oldest state first. Hashes are computed from the frozen data."""
    entries: List[Dict[str, object]] = []

    # 1. the prior pack's capture, as recorded by that pack (not re-read today)
    prior_hub = list(csv.DictReader((ROOT / "data/nfl_8362b702/injury_series.csv").open(newline="")))
    entries.append({
        "entry_id": "SNP-0001",
        "read_at_utc": "2026-11-15T23:58:00Z",
        "dataset": "injury_hub_week10",
        "source_url": "https://www.nfl.com/injuries/",
        "n_rows": len(prior_hub),
        "content_hash": _h(_canon(prior_hub, ["club", "player", "injury_text", "practice_status", "game_status"])),
        "captured_by": "session 8362b702 (frozen in data/nfl_8362b702/injury_series.csv)",
        "replay_note": "two reads exist, so designations can be replayed as they were known",
    })
    # 2. today's fresh read
    today = [{"club": c, "player": p, "injury": i, "practice": ps, "game": gs}
             for c, p, _pos, i, ps, gs in capture.INJURY_HUB]
    entries.append({
        "entry_id": "SNP-0002",
        "read_at_utc": "2026-11-17T00:44:00Z",
        "dataset": "injury_hub_week10",
        "source_url": "https://www.nfl.com/injuries/",
        "n_rows": len(today),
        "content_hash": _h(_canon(today, ["club", "player", "injury", "practice", "game"])),
        "captured_by": "session ca1b3769 (this read)",
        "replay_note": "second dated read of the same page; delta published in injury_deltas.csv",
    })
    # 3. week-10 inactives (game-day evidence, published once per game)
    inact = [{"club": c, "line": line} for c, players in capture.INACTIVES_W10.items() for line in players]
    entries.append({
        "entry_id": "SNP-0003",
        "read_at_utc": "2026-11-17T00:45:00Z",
        "dataset": "week10_inactives",
        "source_url": "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
        "n_rows": len(inact),
        "content_hash": _h(_canon(inact, ["club", "line"])),
        "captured_by": "session ca1b3769",
        "replay_note": "the article is immutable once published, so this is a true point-in-time record",
    })
    # 4. week-10 results as of today
    res = [{"gid": g, "away": a, "home": h, "as": s1, "hs": s2, "status": st}
           for g, _d, a, h, s1, s2, st in capture.WEEK10]
    entries.append({
        "entry_id": "SNP-0004",
        "read_at_utc": "2026-11-17T00:41:00Z",
        "dataset": "week10_results",
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "n_rows": len(res),
        "content_hash": _h(_canon(res, ["gid", "away", "home", "as", "hs", "status"])),
        "captured_by": "session ca1b3769",
        "replay_note": "supersedes the 2026-11-15T23:35Z read, which saw 9 finals; that read is kept in pack 8362b702",
    })
    # 5. week-11 fixtures
    fx = [{"gid": g, "date": d, "time": t, "net": n, "away": a, "home": h, "venue": v}
          for g, _day, d, t, n, a, h, v, _m in capture.WEEK11]
    entries.append({
        "entry_id": "SNP-0005",
        "read_at_utc": "2026-11-17T00:39:00Z",
        "dataset": "week11_fixtures",
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "n_rows": len(fx),
        "content_hash": _h(_canon(fx, ["gid", "date", "time", "net", "away", "home", "venue"])),
        "captured_by": "session ca1b3769",
        "replay_note": "13 fixtures + 6 byes; venue text taken from each card's hotel deep-link",
    })
    # chain them
    prev = ""
    for e in entries:
        e["prev_hash"] = prev
        e["chain_hash"] = _h(prev + e["content_hash"])
        prev = e["chain_hash"]
    return entries


def verify_chain(entries: List[Dict[str, object]]) -> List[str]:
    """Re-compute the chain; return a list of failures (empty means intact)."""
    problems = []
    prev = ""
    for e in entries:
        if e["prev_hash"] != prev:
            problems.append("%s: prev_hash mismatch" % e["entry_id"])
        want = _h(prev + e["content_hash"])
        if e["chain_hash"] != want:
            problems.append("%s: chain_hash mismatch" % e["entry_id"])
        prev = e["chain_hash"]
    return problems


def coverage() -> Dict[str, object]:
    """What the ledger can and cannot replay."""
    return {
        "dated_reads_of_injury_hub_in_repo": 2,
        "datasets_with_a_dated_capture": 5,
        "reads_needed_for_a_designation_replay_backtest": 40,
        "gap": ("2 dated reads is not a series. A Questionable->Out replay needs a read on "
                "each of Wed/Thu/Fri/Sat for many weeks; that is scheduled capture and is "
                "blocked on the retrieval-terms question Q-01."),
    }
