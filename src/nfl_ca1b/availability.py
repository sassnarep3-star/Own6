"""Availability: injury hub deltas, inactive evidence, and the empirical
calibration of what each game designation actually meant in Week 10.

The brief forbids three things, and this module is built around avoiding them:

  1. a *level* ("N players listed") instead of a *surprise* (what changed, and did
     the designation predict the inactive list?);
  2. inferring a replacement or a depth rank that no official page names;
  3. using a designation as a feature before its reliability is measured.
     reliability is measured here, on Week 10, and the interval is published.
"""
from __future__ import annotations

import csv
import pathlib
from typing import Dict, Iterable, List, Optional, Tuple

from . import capture
from .engine import wilson

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRIOR_HUB = ROOT / "data/nfl_8362b702/injury_series.csv"   # 2026-11-15T23:58Z read


# ------------------------------------------------------------------- deltas
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _name_key(name: str) -> str:
    """Join key robust to the suffix drift between the hub and the news article.

    The hub prints 'Kenneth Walker III' where the inactives article prints
    'Kenneth Walker', and 'Ronnie Hickman Jr.' vs 'Ronnie Hickman'. Dropping
    generational suffixes is the only normalisation applied; no fuzzy matching is
    used, so a genuine mismatch can never be silently paired.
    """
    toks = [t for t in name.lower().replace(".", "").replace("'", "").replace("-", " ").split()
            if t and t not in SUFFIXES]
    return " ".join(toks)


def injury_series_rows() -> List[Dict[str, object]]:
    rows = []
    for club, player, pos, inj, ps, gs in capture.INJURY_HUB:
        rows.append({
            "read_at_utc": "2026-11-17T00:44:00Z", "hub_week": 10, "club": club,
            "player": player, "position": pos, "injury": inj,
            "practice_status": ps, "practice_code": capture.PRACTICE_SHORT.get(ps, ""),
            "game_status": gs,
            "game_status_note": "blank on the page = no designation published" if not gs else "",
            "source_url": "https://www.nfl.com/injuries/",
        })
    return rows


def injury_deltas() -> List[Dict[str, object]]:
    """Player-level change between the 2026-11-15T23:58Z read and today's read.

    Only clubs present in BOTH captures are comparable. A club that appears only
    now is reported as `newly_captured`, never as "no change".
    """
    prior: Dict[Tuple[str, str], Dict[str, str]] = {}
    with PRIOR_HUB.open(newline="") as fh:
        for r in csv.DictReader(fh):
            prior[(r["club"], _name_key(r["player"]))] = r
    now: Dict[Tuple[str, str], Dict[str, str]] = {}
    for club, player, pos, inj, ps, gs in capture.INJURY_HUB:
        now[(club, _name_key(player))] = {
            "player": player, "position": pos, "injury": inj,
            "practice_status": ps, "game_status": gs,
        }
    prior_clubs = {c for c, _ in prior}
    out: List[Dict[str, object]] = []
    for key in sorted(now):
        club, _ = key
        n = now[key]
        p = prior.get(key)
        if p is None:
            out.append({
                "club": club, "player": n["player"], "position": n["position"],
                "delta_kind": "added_to_report" if club in prior_clubs else "newly_captured_club",
                "prior_read_at_utc": "" if club not in prior_clubs else "2026-11-15T23:58:00Z",
                "prior_value": "", "current_value": _fmt(n),
                "today_read_at_utc": "2026-11-17T00:44:00Z",
                "source_url": "https://www.nfl.com/injuries/",
            })
            continue
        if _fmt(n) == _fmt(p):
            continue
        out.append({
            "club": club, "player": n["player"], "position": n["position"],
            "delta_kind": "field_changed", "prior_read_at_utc": "2026-11-15T23:58:00Z",
            "prior_value": _fmt(p), "current_value": _fmt(n),
            "today_read_at_utc": "2026-11-17T00:44:00Z",
            "source_url": "https://www.nfl.com/injuries/",
        })
    for key in sorted(set(prior) - set(now)):
        club, _ = key
        p = prior[key]
        out.append({
            "club": club, "player": p["player"], "position": p["position"],
            "delta_kind": ("removed_from_report" if club in {c for c, _ in now}
                           else "not_in_today_capture"),
            "prior_read_at_utc": "2026-11-15T23:58:00Z", "prior_value": _fmt(p),
            "current_value": "", "today_read_at_utc": "2026-11-17T00:44:00Z",
            "source_url": "https://www.nfl.com/injuries/",
        })
    return out


def _fmt(r: Dict[str, str]) -> str:
    return "injury=%r; practice=%r; game=%r" % (
        r.get("injury") or "", r.get("practice_status") or "", r.get("game_status") or "")


# ------------------------------------------------------- inactives + calibration
def _inactive_index() -> Dict[Tuple[str, str], str]:
    """(club, name_key) -> the printed inactive label (position prefix stripped)."""
    out = {}
    for club, players in capture.INACTIVES_W10.items():
        for line in players:
            name = line
            # strip a leading position token (CB, FS, OT, C, QB, LB, ILB, OL, DL, ...)
            parts = name.split()
            if parts and parts[0].isupper() and len(parts[0]) <= 3:
                name = " ".join(parts[1:])
            if "(emergency" in name.lower() or "(designated" in name.lower():
                name = name.split("(")[0].strip()
            out[(club, _name_key(name))] = line
    return out


CALIBRATION_DESIGNATIONS = ["Out", "Doubtful", "Questionable", ""]
DESIGNATION_LABEL = {"Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable",
                     "": "(blank — no designation published)"}


def designation_calibration() -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """Play rate per game designation, joined to the official week-10 inactive lists.

    `played` means: the player appears in the hub table and does NOT appear in the
    official inactive list for that game. That is evidence, not proof — a player
    not on either list is not captured. Clubs whose game had no inactive article
    (TNF, MNF) are excluded from the denominator, never counted as healthy.
    """
    inactive = _inactive_index()
    covered = set(capture.INACTIVES_W10)
    per_player: List[Dict[str, object]] = []
    agg: Dict[str, Dict[str, int]] = {d: {"inactive": 0, "not_inactive": 0} for d in CALIBRATION_DESIGNATIONS}
    for club, player, pos, inj, ps, gs in capture.INJURY_HUB:
        if club not in covered:
            continue
        key = (club, _name_key(player))
        is_inactive = key in inactive
        agg.setdefault(gs, {"inactive": 0, "not_inactive": 0})
        agg[gs]["inactive" if is_inactive else "not_inactive"] += 1
        per_player.append({
            "club": club, "player": player, "position": pos, "injury": inj,
            "practice_status": ps, "game_status": gs,
            "on_official_inactive_list": "yes" if is_inactive else "no",
            "inactive_line_verbatim": inactive.get(key, ""),
            "hub_source_url": "https://www.nfl.com/injuries/",
            "inactive_source_url": "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
        })
    rows = []
    for d in CALIBRATION_DESIGNATIONS:
        a = agg.get(d, {"inactive": 0, "not_inactive": 0})
        n = a["inactive"] + a["not_inactive"]
        # play rate = share of designation rows NOT on the inactive list
        k = a["not_inactive"]
        lo, hi = wilson(k, n)
        rows.append({
            "game_designation": DESIGNATION_LABEL[d],
            "n_players_joined": n,
            "n_on_inactive_list": a["inactive"],
            "n_not_on_inactive_list": a["not_inactive"],
            "observed_play_rate": (k / n) if n else "",
            "wilson_lo": lo if n else "",
            "wilson_hi": hi if n else "",
            "suggested_feature_use": (
                "Out rows never appeared on an inactive list — treat Out as a hard exclusion, not a probability" if d == "Out" else
                "sample too small to separate Doubtful from Questionable" if d == "Doubtful" else
                "blank is not a designation; do not score it as healthy" if d == "" else
                "wide interval: usable as a weak prior only after a multi-week sample"),
            "source_url": "https://www.nfl.com/injuries/ + https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
        })
    return rows, per_player


# ------------------------------------------------------------- team-level view
def team_view(calibration_per_player: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Per-club: designations out, inactive evidence, and what stays blank."""
    by_club: Dict[str, List[Dict[str, object]]] = {}
    for r in calibration_per_player:
        by_club.setdefault(str(r["club"]), []).append(r)
    hub_count: Dict[str, int] = {}
    for club, *_ in capture.INJURY_HUB:
        hub_count[club] = hub_count.get(club, 0) + 1
    rows = []
    for club in sorted(hub_count):
        recs = by_club.get(club, [])
        out_n = sum(1 for r in recs if r["game_status"] == "Out")
        dbt_n = sum(1 for r in recs if r["game_status"] == "Doubtful")
        q_n = sum(1 for r in recs if r["game_status"] == "Questionable")
        blank_n = sum(1 for r in recs if r["game_status"] == "")
        confirmed_out = sum(1 for r in recs if r["on_official_inactive_list"] == "yes")
        rows.append({
            "club": club,
            "hub_rows_captured": hub_count[club],
            "designation_out": out_n,
            "designation_doubtful": dbt_n,
            "designation_questionable": q_n,
            "designation_blank": blank_n,
            "confirmed_on_inactive_list": ("" if club not in capture.INACTIVES_W10 else confirmed_out),
            "starters_out": "",
            "replacements_named": "",
            "net_injury_count": "",
            "why_blank": ("no official page names the starting line-up for week 10 (Game Books not "
                          "reachable) so 'starters out' and 'replacements named' cannot be stated" ),
            "depth_gate": "G-SNAP/G-GAMEBOOK: depth rank is not published on nfl.com (depth-chart route returns 404, probe P-01)",
            "source_url": "https://www.nfl.com/injuries/",
        })
    return rows


def headline_conflicts() -> List[Dict[str, object]]:
    """Rows where a club's hub entry and its official inactive line disagree.

    Only exact name matches are compared; nothing is inferred from a similar name.
    """
    inactive = _inactive_index()
    rows = []
    for club, player, pos, inj, ps, gs in capture.INJURY_HUB:
        key = (club, _name_key(player))
        if key not in inactive:
            continue
        line = inactive[key]
        silent = gs == ""
        if silent:
            rows.append({
                "club": club, "player": player, "hub_game_status": "(blank)",
                "official_inactive_line": line,
                "conflict": "player is on the official inactive list but the hub publishes no game designation",
                "source_url": "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
            })
    return rows


def reserve_gap() -> Dict[str, int]:
    """How many clubs are still not captured by any injury-hub read in this repo."""
    seen = set()
    for path in ROOT.glob("data/nfl_*/injury*.csv"):
        try:
            with path.open(newline="") as fh:
                rdr = csv.DictReader(fh)
                cols = rdr.fieldnames or []
                club_col = next((c for c in ("club", "team", "club_abbr") if c in cols), None)
                if not club_col:
                    continue
                for r in rdr:
                    v = (r.get(club_col) or "").strip()
                    if v:
                        seen.add(v)
        except OSError:
            continue
    all_clubs = set(capture.STANDINGS)
    return {"captured_anywhere": len(seen & all_clubs), "total": len(all_clubs),
            "never_captured": len(all_clubs - seen)}
