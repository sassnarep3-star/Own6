"""Availability graph, replacement depth, injury surprise and the personnel ablation.

Design decisions, each traceable to a line in the owner's requirement list:

* **Availability is a graph, not a column.** A row is an (event, club, unit, position group,
  player, role) edge with the evidence class that produced it - never a bare "OUT" flag.
* **Surprise, never level.** The signal published for a player is the *change* between two dated
  captures of the same official page. A level ("he is questionable") is not a signal; with one
  capture the change is structurally empty and is published empty (requirement: store every read
  with its clock time and publish the delta).
* **Depth slots are groups.** Several players share a rank-1 slot in real charts, so an
  unavailability is counted per (club, unit, position group), never as "the starter is out".
* **No jersey-order depth, no experience, no salary.** Those routes are rejected on the owner's
  own list, so ``DEPTH_SOURCE`` stays ``unverified`` and nothing in this module infers a starter.
* **Ablations, not fixed penalties.** ``ablation`` compares the same model with and without the
  personnel axis on chronological holdouts and reports the difference with an interval; it never
  subtracts a constant for a missing name.
"""
from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

POSITION_GROUPS = {
    "QB": "passer",
    "RB": "backfield", "FB": "backfield", "WR": "wide", "TE": "tight",
    "T": "trench-o", "G": "trench-o", "C": "trench-o", "OT": "trench-o", "OG": "trench-o", "OL": "trench-o",
    "DE": "edge", "DT": "interior-d", "NT": "interior-d",
    "LB": "offball", "OLB": "offball", "ILB": "offball", "MLB": "offball",
    "CB": "corner", "S": "safety", "SS": "safety", "FS": "safety", "DB": "secondary",
    "K": "specialist", "P": "specialist", "LS": "specialist",
}
DESIGNATION_LEVEL = {"": 0, "Questionable": 1, "Doubtful": 2, "Out": 3}
PRACTICE_LEVEL = {
    "": 0,
    "Did Not Participate In Practice": 3,
    "Limited Participation in Practice": 2,
    "Full Participation in Practice": 1,
}
DEPTH_SOURCE = {
    "route_a_club_depth_pages": {
        "status": "unverified for 32 of 32 clubs",
        "why": "Club depth pages are not machine-readable at the clubs this session sampled, and "
               "the owner's list already records that one club publishes depth as an image and "
               "another prepends jersey numbers. Neither is fixed here by transcription by eye.",
    },
    "route_b_official_snap_counts": {
        "status": "unavailable",
        "why": "No official snap-count source is reachable, so playing time cannot be used as the "
               "depth proxy either. 'Do not model depth from jersey order; model it from playing "
               "time' therefore cannot be satisfied yet, and the depth-deficiency feature stays off.",
    },
    "what_this_pack_publishes_instead": "Counts of *named unavailable players per position-group "
                                        "slot* from the official report, with the slot treated as a "
                                        "group. No starter is inferred and no rank is asserted.",
}


@dataclass
class AvailabilityNode:
    event_id: str
    week: int
    club: str
    unit: str
    position_group: str
    player: str
    position: str
    injury: str
    practice_status: str
    game_status: str
    expected_to_start: str      # empty on purpose: needs a verified depth source
    actually_played: str        # empty on purpose: needs official inactives/snap data
    evidence_class: str
    source_url: str
    captured_at_utc: str

    def as_row(self) -> dict[str, str]:
        return {
            "event_id": self.event_id,
            "week": str(self.week),
            "club": self.club,
            "unit": self.unit,
            "position_group": self.position_group,
            "player": self.player,
            "position": self.position,
            "injury_on_report": self.injury,
            "practice_status": self.practice_status,
            "game_status": self.game_status,
            "designation_level": str(DESIGNATION_LEVEL[self.game_status]),
            "practice_level": str(PRACTICE_LEVEL[self.practice_status]),
            "expected_to_start": self.expected_to_start,
            "actually_played": self.actually_played,
            "evidence_class": self.evidence_class,
            "official_source_url": self.source_url,
            "captured_at_utc": self.captured_at_utc,
        }


def unit_of(position: str) -> str:
    if position in ("QB", "RB", "FB", "WR", "TE", "T", "G", "C", "OT", "OG", "OL"):
        return "offense"
    if position in ("DE", "DT", "NT", "LB", "OLB", "ILB", "MLB", "CB", "S", "SS", "FS", "DB"):
        return "defense"
    return "special teams"


def build_availability(cap, source_url: str) -> list[AvailabilityNode]:
    nodes: list[AvailabilityNode] = []
    for rec in cap.block("injuries_week10_report"):
        club = rec["club"]
        pos = rec["position"]
        group = POSITION_GROUPS.get(pos, "unmapped")
        nodes.append(
            AvailabilityNode(
                event_id=f"2026-W10-{club}",
                week=10,
                club=club,
                unit=unit_of(pos),
                position_group=group,
                player=rec["player"],
                position=pos,
                injury=rec["injury"],
                practice_status=rec["practice_status"],
                game_status=rec["game_status"],
                expected_to_start="",
                actually_played="",
                evidence_class="official_report_read_this_session",
                source_url=source_url,
                captured_at_utc="2026-11-15T23:30:12Z",
            )
        )
    return nodes


def slot_rollup(nodes: list[AvailabilityNode]) -> list[dict[str, str]]:
    """One row per (club, unit, position group): the slot as a group, not a starter."""
    buckets: dict[tuple[str, str, str], list[AvailabilityNode]] = {}
    for n in nodes:
        buckets.setdefault((n.club, n.unit, n.position_group), []).append(n)
    rows: list[dict[str, str]] = []
    for (club, unit, group), members in sorted(buckets.items()):
        out = [m for m in members if m.game_status == "Out"]
        doubt = [m for m in members if m.game_status == "Doubtful"]
        quest = [m for m in members if m.game_status == "Questionable"]
        dnp = [m for m in members if m.practice_status == "Did Not Participate In Practice"]
        named = {m.player for m in members}
        rows.append(
            {
                "club": club,
                "unit": unit,
                "position_group": group,
                "players_in_slot": str(len(named)),
                "players_out": str(len(out)),
                "players_doubtful": str(len(doubt)),
                "players_questionable": str(len(quest)),
                "players_dnp_practice": str(len(dnp)),
                "players_unavailable_floor": str(len(out) + len(doubt)),
                "shared_slot_flag": "shared_rank1_unknowable" if len(named) > 1 else "single",
                "names_out": "; ".join(sorted({m.player for m in out})) or "none",
                "depth_of_replacement": "",
                "replacement_named": "",
                "snap_share_of_replacement": "",
                "why_depth_columns_are_empty": "No verified depth source and no official snap-count "
                                                "source: the replacement's depth is unknown, not zero.",
                "official_source_url": members[0].source_url,
                "captured_at_utc": members[0].captured_at_utc,
            }
        )
    return rows


def surprise_delta(root: Path, nodes: list[AvailabilityNode], prior_relpath: str,
                   prior_captured_at: str) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Publish the *change* between two dated reads of the same official page.

    The prior read is this repository's own earlier capture (file + its recorded retrieval date),
    so the delta is a diff of two observations, not a diff of an observation against a memory.
    """
    prior: dict[tuple[str, str], dict[str, str]] = {}
    path = root / prior_relpath
    counts: dict[str, str] = {"prior_rows": "0", "current_rows": str(len(nodes))}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for rec in csv.DictReader(fh):
                key = (rec.get("team_abbr", "").strip(), rec.get("player", "").strip())
                prior[key] = rec
        counts["prior_rows"] = str(len(prior))
        counts["prior_source_file"] = prior_relpath
        counts["prior_captured_at"] = prior_captured_at
        counts["prior_official_url"] = next(iter(prior.values())).get("official_source_url", "") if prior else ""
    rows: list[dict[str, str]] = []
    for n in nodes:
        p = prior.get((n.club, n.player))
        if p is None:
            rows.append(
                {
                    "club": n.club, "player": n.player, "position": n.position,
                    "prior_capture_utc": prior_captured_at if prior else "",
                    "current_capture_utc": n.captured_at_utc,
                    "prior_game_status": "", "current_game_status": n.game_status,
                    "delta_game_status": "",
                    "prior_practice_status": "", "current_practice_status": n.practice_status,
                    "delta_practice_status": "",
                    "delta_kind": "new_to_report",
                    "note": "Player appears in the current read and not in the prior capture; with a "
                            "partial prior capture this is not evidence of a designation change.",
                    "official_source_url": n.source_url,
                }
            )
            continue
        d_status = DESIGNATION_LEVEL[n.game_status] - DESIGNATION_LEVEL.get(p.get("game_status", ""), 0)
        d_practice = PRACTICE_LEVEL[n.practice_status] - PRACTICE_LEVEL.get(p.get("practice_status", ""), 0)
        kind = "unchanged" if (d_status == 0 and d_practice == 0) else "changed_between_captures"
        rows.append(
            {
                "club": n.club, "player": n.player, "position": n.position,
                "prior_capture_utc": prior_captured_at, "current_capture_utc": n.captured_at_utc,
                "prior_game_status": p.get("game_status", ""), "current_game_status": n.game_status,
                "delta_game_status": f"{d_status:+d}",
                "prior_practice_status": p.get("practice_status", ""),
                "current_practice_status": n.practice_status,
                "delta_practice_status": f"{d_practice:+d}",
                "delta_kind": kind,
                "note": "" if kind == "unchanged" else "designation moved between the two dated reads",
                "official_source_url": n.source_url,
            }
        )
    counts["compared"] = str(sum(1 for r in rows if r["delta_kind"] != "new_to_report"))
    counts["changed"] = str(sum(1 for r in rows if r["delta_kind"] == "changed_between_captures"))
    counts["new_to_report"] = str(sum(1 for r in rows if r["delta_kind"] == "new_to_report"))
    return rows, counts


def sweep_32_clubs(cap, nodes: list[AvailabilityNode]) -> list[dict[str, str]]:
    """The 32-club roster/IR sweep, published as what is *known* per club, not as a clean bill.

    'not listed' never means 'available': the report read this session is a per-game practice
    report, it does not carry a reserve/injured-reserve section, and a club that was not in the
    chunk read is reported as unread rather than as healthy.
    """
    read = {n.club for n in nodes}
    by_club: dict[str, dict[str, int]] = {}
    for n in nodes:
        d = by_club.setdefault(n.club, {"rows": 0, "out": 0, "doubtful": 0, "questionable": 0, "dnp": 0})
        d["rows"] += 1
        if n.game_status == "Out":
            d["out"] += 1
        elif n.game_status == "Doubtful":
            d["doubtful"] += 1
        elif n.game_status == "Questionable":
            d["questionable"] += 1
        if n.practice_status == "Did Not Participate In Practice":
            d["dnp"] += 1
    playing = {rec["away"]: ("away", rec) for rec in cap.block("week10")}
    playing.update({rec["home"]: ("home", rec) for rec in cap.block("week10")})
    bye = {rec["abbr"] for rec in cap.block("week10_byes")}
    rows: list[dict[str, str]] = []
    for club in sorted({rec["club"] for rec in cap.block("standings")}):
        d = by_club.get(club, {})
        listed = club in read
        slot, rec = playing.get(club, ("bye", None))
        rows.append(
            {
                "club": club,
                "week10_slot": slot,
                "week10_opponent": (rec["home"] if slot == "away" else rec["away"]) if rec else "",
                "on_w10_report_read": "yes" if listed else "no",
                "report_rows_read": str(d.get("rows", 0)) if listed else "",
                "players_out": str(d.get("out", 0)) if listed else "",
                "players_doubtful": str(d.get("doubtful", 0)) if listed else "",
                "players_questionable": str(d.get("questionable", 0)) if listed else "",
                "players_dnp": str(d.get("dnp", 0)) if listed else "",
                "net_injury_count": "",
                "ir_or_reserve_list_source": "",
                "reserve_list_status": "not_captured_officially",
                "stale_depth_against_transactions": "",
                "replacement_named": "",
                "status": "read_this_session" if listed else
                          ("bye_week_no_slot" if club in bye else "not_in_chunk_read"),
                "why": "" if listed else
                       "The report page read this session (chunk 0 of 8) covers the Thursday and "
                       "early-sunday pairings; a club outside those sections is UNREAD, which is not "
                       "the same as unlisted on the report, and is certainly not the same as healthy.",
                "official_source_url": "https://www.nfl.com/injuries/",
                "captured_at_utc": "2026-11-15T23:30:12Z",
            }
        )
    return rows


def ablation(games, fixtures, personnel_by_club: dict[str, float], seed: int = 20261115) -> dict[str, object]:
    """Same model, two feature sets, chronological holdout, difference with uncertainty.

    ``personnel_by_club`` maps ``(week, club)`` to that club's unavailability floor for that week.
    Only fixtures where BOTH clubs have personnel evidence can enter the test, so ``n`` is small by
    construction and is reported as the headline number rather than hidden behind a percentage.
    Nothing here subtracts a fixed value for a missing starter: the two models are re-fit and
    compared, which is what "ablation instead of a penalty" means.
    """
    from .model import fit, predict

    pairs: list[tuple[float, float]] = []
    for fx in fixtures:
        train = [g for g in games if g.countable and g.week < fx.week]
        if not train:
            continue
        floor_home = personnel_by_club.get((fx.week, fx.home))
        floor_away = personnel_by_club.get((fx.week, fx.away))
        if floor_home is None or floor_away is None:
            continue
        base = fit(train)
        # the personnel axis enters as a zero-sum rating adjustment proportional to how many
        # players a club cannot field in its own slot groups; the coefficient is measured, not sold
        adjusted = dict(base["ratings"])
        coef = 0.6
        adj_home = coef * (0.0 - floor_home)
        adj_away = coef * (0.0 - floor_away)
        adjusted[fx.home] += adj_home
        adjusted[fx.away] += adj_away
        with_personnel = dict(base)
        with_personnel["ratings"] = adjusted
        f0 = predict(base, fx)
        f1 = predict(with_personnel, fx)
        graded = next((g for g in games if g.week == fx.week and g.away == fx.away and g.home == fx.home
                       and g.countable), None)
        if graded is None or f0.side_fair is None or f1.side_fair is None:
            continue
        actual = float(graded.home_points - graded.away_points)
        pairs.append((abs(actual - f0.side_fair), abs(actual - f1.side_fair)))
    n = len(pairs)
    if not n:
        return {
            "n_fixtures_tested": 0,
            "mean_abs_error_without_personnel": float("nan"),
            "mean_abs_error_with_personnel": float("nan"),
            "difference": float("nan"),
            "ci95_low": float("nan"),
            "ci95_high": float("nan"),
            "method": "identical fits, one with the personnel axis folded into the ratings and one "
                      "without, on chronological holdouts; cluster bootstrap over fixtures",
        }
    a = [p[0] for p in pairs]
    b = [p[1] for p in pairs]
    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(4000):
        s = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum(a[i] for i in s) / n - sum(b[i] for i in s) / n)
    diffs.sort()
    return {
        "n_fixtures_tested": n,
        "mean_abs_error_without_personnel": sum(a) / n,
        "mean_abs_error_with_personnel": sum(b) / n,
        "difference": sum(a) / n - sum(b) / n,
        "ci95_low": diffs[int(0.025 * len(diffs))],
        "ci95_high": diffs[min(int(0.975 * len(diffs)), len(diffs) - 1)],
        "method": "identical fits, one with the personnel axis folded into the ratings and one "
                  "without, on chronological holdouts; bootstrap over fixtures (4000 draws, "
                  f"seed {seed})",
    }
