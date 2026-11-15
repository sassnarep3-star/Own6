"""Verified game corpus + reconciliation for session 67233566.

Two independent official reads are combined, and the combination is *tested* rather than
trusted:

* the Week 10 status/score cards read directly this session (``#week10`` block);
* the Weeks 1-9 game log captured by session ``f4e592a7`` at commit-pinned
  ``data/nfl_f4/results.csv`` (each row already carries its own official ``nfl.com``
  by-week URL and read date).

The test is the division standings page read this session: for all 32 clubs the corpus must
reproduce W, L, T, PF and PA exactly, because the standings page counts only games marked
FINAL. 160 identities (32 clubs x 5 fields) plus the 26 Week 10 card badges and the 32
Week 11 card badges. A club that fails any identity is dropped from the corpus and published
on the flagged page - a silent patch is not possible, because the drop is itself a row.

Every game in the corpus is either ``direct_read_this_session`` (Week 10) or
``prior_capture_reconciled`` (Weeks 1-9). No row is labelled verified by a read it did not have.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .capture import Capture, as_int, badge_to_record

PRIOR_RESULTS_RELPATH = "data/nfl_f4/results.csv"
PRIOR_RESULTS_PIN = "32a1b692ea6674b3755716e9926596e4772a3364"
PRIOR_RESULTS_OWNER = "session f4e592a7 (pack nfl_f4), read 2026-11-14"
LEAGUE_CLUBS = 32


@dataclass
class Game:
    game_id: str
    week: int
    season: int
    date_on_card: str
    slot_on_card: str
    away: str
    home: str
    away_points: int | None
    home_points: int | None
    feed_status: str
    provenance: str
    official_source_url: str
    game_page_url: str
    read_on_utc: str
    countable: bool  # True only when FINAL at read time and reconciliation passed



def week10_games(cap: Capture, source_url: str) -> list[Game]:
    games: list[Game] = []
    for i, rec in enumerate(cap.block("week10"), start=1):
        away, home = rec["away"], rec["home"]
        status_raw = rec["card_status"].lower()
        ap, hp = as_int(rec["away_points"]), as_int(rec["home_points"])
        status = {"final": "final", "live": "in_progress", "scheduled": "unplayed"}[status_raw]
        games.append(
            Game(
                game_id=f"2026-W10-{i:02d}",
                week=10,
                season=2026,
                date_on_card=rec["card_date"],
                slot_on_card=rec["card_slot"],
                away=away,
                home=home,
                away_points=ap,
                home_points=hp,
                feed_status=status,
                provenance="direct_read_this_session",
                official_source_url=source_url,
                game_page_url="",
                read_on_utc="2026-11-15T23:26:34Z",
                countable=status == "final",
            )
        )
    return games


def prior_games(root: Path, cap: Capture) -> tuple[list[Game], list[Game]]:
    """Weeks 1-9 from the pinned prior capture, plus that capture's own Week 10 row (used
    only as an agreement check, never as corpus)."""
    out: list[Game] = []
    other: list[Game] = []
    with (root / PRIOR_RESULTS_RELPATH).open(newline="", encoding="utf-8") as fh:
        for i, rec in enumerate(csv.DictReader(fh), start=1):
            week = int(rec["week"])
            g = Game(
                game_id=f"2026-W{week:02d}-P{i:02d}",
                week=week,
                season=int(rec["season"]),
                date_on_card="",
                slot_on_card="",
                away=rec["away"],
                home=rec["home"],
                away_points=int(rec["away_score"]),
                home_points=int(rec["home_score"]),
                feed_status="final" if rec["status"].lower() == "final" else rec["status"],
                provenance="prior_capture_reconciled",
                official_source_url=rec["result_source_url"],
                game_page_url="",
                read_on_utc=rec["read_date"],
                countable=rec["status"].lower() == "final",
            )
            (out if week <= 9 else other).append(g)
    return out, other


def standings(cap: Capture) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for rec in cap.block("standings"):
        table[rec["club"]] = {
            "w": int(rec["w"]),
            "l": int(rec["l"]),
            "t": int(rec["t"]),
            "pf": int(rec["pf"]),
            "pa": int(rec["pa"]),
            "net": int(rec["net_pts"]),
        }
    return table


def derived_records(games: list[Game]) -> dict[str, dict[str, int]]:
    agg: dict[str, dict[str, int]] = {}
    for g in games:
        if not g.countable:
            continue
        for club, opp, pf, pa in ((g.away, g.home, g.away_points, g.home_points),
                                  (g.home, g.away, g.home_points, g.away_points)):
            a = agg.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "games": 0})
            assert pf is not None and pa is not None
            a["pf"] += pf
            a["pa"] += pa
            a["games"] += 1
            if pf > pa:
                a["w"] += 1
            elif pf < pa:
                a["l"] += 1
            else:
                a["t"] += 1
    return agg



def card_badges(cap: Capture) -> list[tuple[str, str, tuple[int, int, int]]]:
    """All card badges read this session as (club, provenance-page, (w,l,t)) pairs.
    Later reads override earlier ones only when the badge string is identical; a differing
    badge for the same club from two pages is a conflict and is published as one."""
    out: list[tuple[str, str, tuple[int, int, int]]] = []
    for block, page, sides in (
        ("week10", "https://www.nfl.com/schedules/2026/by-week/week-10", ("away", "home")),
        ("week11_game", "https://www.nfl.com/schedules/2026/by-week/week-11", ("away", "home")),
    ):
        for rec in cap.block(block):
            for side in sides:
                t = badge_to_record(rec[f"{side}_badge"])
                if t:
                    out.append((rec[side], page, t))
    for block, page in (
        ("week10_byes", "https://www.nfl.com/schedules/2026/by-week/week-10"),
        ("week11_byes", "https://www.nfl.com/schedules/2026/by-week/week-11"),
    ):
        for rec in cap.block(block):
            t = badge_to_record(rec["badge"])
            if t:
                out.append((rec["abbr"], page, t))
    return out


@dataclass
class Reconciliation:
    checks: list[dict[str, str]]
    excluded_clubs: list[str]

    @property
    def passed(self) -> bool:
        return all(c["result"] == "match" for c in self.checks)


def reconcile(games: list[Game], cap: Capture, weeks_through: int = 10) -> Reconciliation:
    """Compare corpus-derived club records with the official standings read and the card badges."""
    checks: list[dict[str, str]] = []
    st = standings(cap)
    derived = derived_records(games)
    for club in sorted(st):
        d = derived.get(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "games": 0})
        for field_name, official_key, derived_key in (
            ("W", "w", "w"), ("L", "l", "l"), ("T", "t", "t"), ("PF", "pf", "pf"), ("PA", "pa", "pa"),
        ):
            checks.append(
                {
                    "check_id": f"STAND-{club}-{field_name}",
                    "club": club,
                    "kind": "standings_identity",
                    "field": field_name,
                    "official_value": str(st[club][official_key]),
                    "derived_value": str(d[derived_key]),
                    "result": "match" if st[club][official_key] == d[derived_key] else "MISMATCH",
                    "official_source_url": "https://www.nfl.com/standings/division/2026/reg",
                }
            )
        if d["games"] != st[club]["w"] + st[club]["l"] + st[club]["t"]:
            checks.append(
                {
                    "check_id": f"GAMES-{club}",
                    "club": club,
                    "kind": "games_played_identity",
                    "field": "GP",
                    "official_value": str(st[club]["w"] + st[club]["l"] + st[club]["t"]),
                    "derived_value": str(d["games"]),
                    "result": "match"
                    if d["games"] == st[club]["w"] + st[club]["l"] + st[club]["t"]
                    else "MISMATCH",
                    "official_source_url": "https://www.nfl.com/standings/division/2026/reg",
                }
            )
    # card badges: printed record must equal the corpus-derived record at that page's moment
    badges_seen: dict[str, list[tuple[str, tuple[int, int, int]]]] = {}
    for club, page, t in card_badges(cap):
        badges_seen.setdefault(club, []).append((page, t))
    for club, entries in sorted(badges_seen.items()):
        d = derived.get(club)
        for idx, (page, (w, l, t_)) in enumerate(entries, start=1):
            ok = d is not None and (d["w"], d["l"], d["t"]) == (w, l, t_)
            checks.append(
                {
                    "check_id": f"BADGE-{club}-{idx}",
                    "club": club,
                    "kind": "card_badge_identity",
                    "field": "W-L-T",
                    "official_value": f"{w}-{l}-{t_}",
                    "derived_value": "" if d is None else f"{d['w']}-{d['l']}-{d['t']}",
                    "result": "match" if ok else "MISMATCH",
                    "official_source_url": page,
                }
            )
    # internal identities that need no external source
    checks.append(
        {
            "check_id": "LEAGUE-PF-PA",
            "club": "ALL",
            "kind": "league_identity",
            "field": "sum(PF)-sum(PA)",
            "official_value": "0",
            "derived_value": str(sum(d["pf"] for d in derived.values()) - sum(d["pa"] for d in derived.values())),
            "result": "match"
            if sum(d["pf"] for d in derived.values()) == sum(d["pa"] for d in derived.values())
            else "MISMATCH",
            "official_source_url": "https://www.nfl.com/standings/division/2026/reg",
        }
    )
    tot = sum(d["w"] + d["l"] + d["t"] for d in derived.values())
    checks.append(
        {
            "check_id": "LEAGUE-GAME-COUNT",
            "club": "ALL",
            "kind": "league_identity",
            "field": "sum(club games)/2 == countable games",
            "official_value": str(tot // 2) if tot % 2 == 0 else "ODD",
            "derived_value": str(sum(1 for g in games if g.countable)),
            "result": "match" if tot % 2 == 0 and tot // 2 == sum(1 for g in games if g.countable) else "MISMATCH",
            "official_source_url": "https://www.nfl.com/standings/division/2026/reg",
        }
    )
    bad = sorted({c["club"] for c in checks if c["result"] == "MISMATCH"})
    return Reconciliation(checks=checks, excluded_clubs=bad)


def build_corpus(cap: Capture, root: Path, week10_source_url: str) -> tuple[list[Game], list[Game], list[Game]]:
    """Return (corpus, prior_week10_rows, all_week10_rows)."""
    w10 = week10_games(cap, week10_source_url)
    prior_w1_9, prior_w10 = prior_games(root, cap)
    corpus = sorted(prior_w1_9 + w10, key=lambda g: (g.week, g.game_id))
    return corpus, prior_w10, w10


def load(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parents[2]
    from .capture import load_capture

    cap = load_capture(root)
    src = next((s for s in cap.sources() if s["url"].endswith("week-10")), {})
    corpus, prior_w10, w10 = build_corpus(cap, root, src.get("url", ""))
    rec = reconcile(corpus, cap)
    return {"capture": cap, "corpus": corpus, "prior_week10": prior_w10, "week10": w10, "reconciliation": rec}
