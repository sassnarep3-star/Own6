"""Depth of the replacement, not the fact of a replacement.

What the official NFL injury report actually gives a project is a *list*: club,
player, position, injury, practice participation, game designation. It does not
publish depth charts, snap counts or who replaces whom. So "a starter is out" is
the fact, and this module's job is to turn the list into a *depth* measure without
inventing an order nobody published.

Two numbers are therefore reported for every club-position group:

``tiers_dropped_lower_bound``
    how many players at that position the report rules Out or Doubtful. Each one
    has to be covered by somebody further down the list, so this is a hard lower
    bound on how deep the drop is. It is a bound, not an estimate, and it is
    labelled as one everywhere it appears.

``tiers_dropped_evidenced``
    where an official nfl.com news headline names the replacement (for example
    "Drew Lock expected to start again" after Sam Darnold was ruled out, or
    "Kyle McCord in line for first start" after Malik Willis went to injured
    reserve), the drop is no longer inferred from a count - it is stated. Those
    rows carry the headline and its URL.

``club_depth_deficit`` weights the bound by unit and adds the evidenced cases. The
weights are a declared proposal (``proposed_weight_not_observed``): the pack
publishes an *unweighted* count everywhere so a reviewer can re-weight it.
"""

from __future__ import annotations

from . import capture as C
from .cache import memo

GROUPS = ("QB", "RB", "WR", "TE", "T", "G", "C", "LB", "DE", "DT", "CB", "S", "K", "P", "LS", "FB")
UNAVAILABLE = {"Out", "Doubtful"}
PARTIAL = {"Questionable"}

# Declared deficit weights. Not measured, not official - see the module docstring.
WEIGHTS = {"unavailable": 1.0, "partial": 0.25, "evidenced_replacement": 0.5}

# Only these kinds state that a *backup* is taking the start, which is what a depth
# drop means. Injured-reserve moves, surgeries and "expected to play" notes are
# recorded as evidence rows but are not weighted into the deficit.
REPLACEMENT_KINDS = {"first_start_named", "backup_start_named"}


@memo
def injury_rows() -> list[dict[str, str]]:
    """One row per listed player, exactly as the report prints it."""
    game_by_club = {row[4]: row[0] for row in C.WEEK10_SLATE}
    game_by_club.update({row[5]: row[0] for row in C.WEEK10_SLATE})
    rows: list[dict[str, str]] = []
    for i, line in enumerate(C.INJURY_REPORT_W10_RAW.strip().split("\n"), start=1):
        club, player, pos, injury, practice, status = (line.split("|") + [""] * 6)[:6]
        rows.append({
            "row_id": f"D966-INJ-{i:03d}",
            "season": "2026",
            "week": "10",
            "club": club,
            "game_id": game_by_club.get(club, ""),
            "player": player,
            "position": pos,
            "position_unit": C.POSITION_UNIT.get(pos, "unmapped"),
            "position_group": pos if pos in GROUPS else "other",
            "injury_text": injury,
            "practice_status": practice,
            "game_status": status,
            "availability": "unavailable" if status in UNAVAILABLE
                             else "questionable" if status in PARTIAL
                             else "listed_no_designation" if status == "" else "other",
            "counts_toward_lower_bound": "1" if status in UNAVAILABLE else "0",
            "official_source_url": C.link_for("INJURIES"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return rows


@memo
def group_depth() -> list[dict[str, str]]:
    """Depth-of-replacement rows per club and position group."""
    rows = injury_rows()
    by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in rows:
        by_key.setdefault((r["club"], r["position_group"]), []).append(r)
    out: list[dict[str, str]] = []
    evidence = _replacement_evidence()
    for (club, group), members in sorted(by_key.items()):
        n_out = sum(1 for m in members if m["game_status"] == "Out")
        n_doubtful = sum(1 for m in members if m["game_status"] == "Doubtful")
        n_quest = sum(1 for m in members if m["game_status"] == "Questionable")
        n_practice_only = sum(1 for m in members if m["game_status"] == "")
        ev = [e for e in evidence
              if e["club"] == club and e["position_group"] == group
              and e["evidence_kind"] in REPLACEMENT_KINDS]
        bound = n_out + n_doubtful
        out.append({
            "club": club,
            "unit": C.POSITION_UNIT.get(group, "unmapped"),
            "position_group": group,
            "players_listed": str(len(members)),
            "ruled_out": str(n_out),
            "doubtful": str(n_doubtful),
            "questionable": str(n_quest),
            "practice_report_only_no_designation": str(n_practice_only),
            "tiers_dropped_lower_bound": str(bound),
            "tiers_dropped_evidenced": "; ".join(e["replacement_tier"] for e in ev),
            "first_string_impacted": "yes" if bound else "no",
            "depth_bound_kind": "hard_lower_bound_from_official_designations",
            "club_depth_deficit": f"{WEIGHTS['unavailable'] * bound + WEIGHTS['partial'] * n_quest + WEIGHTS['evidenced_replacement'] * len(ev):.2f}",
            "deficit_score_kind": "proposed_weight_not_observed",
            "evidence_url": ev[0]["url"] if ev else "",
            "official_source_url": C.link_for("INJURIES"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


@memo
def club_rollup() -> list[dict[str, str]]:
    """Club-level view, joined to the fixture it affects and the model's line."""
    depth = group_depth()
    fixtures = {row[4]: row for row in C.WEEK10_SLATE}
    fixtures.update({row[5]: row for row in C.WEEK10_SLATE})
    out: list[dict[str, str]] = []
    for club in sorted({d["club"] for d in depth}):
        rows = [d for d in depth if d["club"] == club]
        fx = fixtures.get(club)
        sides = {}
        for unit in ("offence", "defence", "special"):
            sel = [d for d in rows if d["unit"] == unit]
            sides[unit] = {
                "bound": sum(int(d["tiers_dropped_lower_bound"]) for d in sel),
                "worst_group_bound": max([int(d["tiers_dropped_lower_bound"]) for d in sel], default=0),
                "worst_group": max(sel, key=lambda d: int(d["tiers_dropped_lower_bound"]))["position_group"] if sel else "",
                "deficit": sum(float(d["club_depth_deficit"]) for d in sel),
                "groups_listed": len(sel),
            }
        out.append({
            "club": club,
            "game_id": fx[0] if fx else "",
            "fixture": f"{fx[4]} at {fx[5]}" if fx else "",
            "groups_listed_total": str(len(rows)),
            "offence_tiers_dropped_lower_bound": str(sides["offence"]["bound"]),
            "offence_worst_group": sides["offence"]["worst_group"],
            "offence_worst_group_bound": str(sides["offence"]["worst_group_bound"]),
            "defence_tiers_dropped_lower_bound": str(sides["defence"]["bound"]),
            "defence_worst_group": sides["defence"]["worst_group"],
            "defence_worst_group_bound": str(sides["defence"]["worst_group_bound"]),
            "special_teams_tiers_dropped_lower_bound": str(sides["special"]["bound"]),
            "defence_groups_listed": str(sides["defence"]["groups_listed"]),
            "club_depth_deficit": f"{sides['offence']['deficit'] + sides['defence']['deficit'] + sides['special']['deficit']:.2f}",
            "deficit_score_kind": "proposed_weight_not_observed",
            "position_group_order_status": "unverified: the report does not rank players within a group",
            "official_source_url": C.link_for("INJURIES"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


@memo
def _replacement_evidence() -> list[dict[str, str]]:
    """Rows where an official headline states who the replacement is."""
    out: list[dict[str, str]] = []
    for i, (club, headline, url) in enumerate(C.OFFICIAL_HEADLINES, start=1):
        group, tier, kind = _classify_headline(club, headline)
        out.append({
            "evidence_id": f"D966-REP-{i:02d}",
            "club": club,
            "position_group": group,
            "replacement_tier": tier,
            "evidence_kind": kind,
            "credited_as_depth_replacement": "yes" if kind in REPLACEMENT_KINDS else "no",
            "headline_verbatim": headline,
            "url": url,
            "official_source_url": url,
            "read_on_utc": C.CAPTURE_DATE_UTC,
            "note": "headline text only; the linked article body was not read in this session",
        })
    return out


def _classify_headline(club: str, headline: str) -> tuple[str, str, str]:
    h = headline.lower()
    if "kyle mccord in line for first start" in h:
        return "QB", "QB2 or deeper, zero prior starts stated", "first_start_named"
    if "drew lock expected to start again" in h or "will start for seahawks" in h:
        return "QB", "QB2 named to start", "backup_start_named"
    if "browns to start qb deshaun watson" in h:
        return "QB", "starting QB named", "starter_named"
    if "cardinals' carson beck to start" in h:
        return "QB", "starting QB named", "starter_named"
    if "on injured reserve" in h and "rb treveyon henderson" in h:
        return "RB", "movement to IR stated; replacement not named", "injured_reserve"
    if "on injured reserve" in h and "puka nacua" in h:
        return "WR", "movement to IR stated; replacement not named", "injured_reserve"
    if "lamar jackson" in h:
        return "QB", "absence window stated; replacement not named", "absence_window_or_roundup"
    if "josh jacobs" in h:
        return "RB", "surgery stated; return timeline not stated", "surgery"
    if "kenneth walker questionable" in h:
        return "RB", "designation stated in headline", "designation"
    if "news roundup" in h:
        return "multi", "headline covers several clubs; nothing is credited to one group", "multi_club_roundup"
    if "jj mccarthy expected to play" in h or "j.j. mccarthy expected to play" in h:
        return "QB", "availability stated", "availability"
    if "ammani hooker" in h or "amani hooker" in h or "daiyan henley" in h:
        return "S" if "hooker" in h else "LB", "roster acquired via trade; not an injury replacement", "transaction"
    return "unmapped", "", "unclassified"


REPLACEMENT_EVIDENCE = _replacement_evidence
