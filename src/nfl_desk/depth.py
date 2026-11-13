"""Depth-deficiency scoring from the official weekly injury report.

The scoring weights are a stated policy, not an NFL number: they encode "how far
down the chart does this club have to reach". They are published in full so any
reader can re-run the arithmetic or substitute their own weights.
"""
from __future__ import annotations

WEIGHTS = {"Out": 3, "DNP": 2, "Limited": 1, "Full": 0}

UNIT_OF = {
    "QB": "OFFENCE_QB", "RB": "OFFENCE_SKILL", "FB": "OFFENCE_SKILL", "WR": "OFFENCE_SKILL",
    "TE": "OFFENCE_TE", "T": "OFFENCE_LINE", "G": "OFFENCE_LINE", "C": "OFFENCE_LINE",
    "DT": "DEFENCE_FRONT", "DE": "DEFENCE_PASS_RUSH", "LB": "DEFENCE_LINEBACKER",
    "CB": "DEFENCE_SECONDARY", "S": "DEFENCE_SECONDARY", "K": "SPECIAL_TEAMS",
    "P": "SPECIAL_TEAMS", "LS": "SPECIAL_TEAMS",
}

TIERS = (
    (0, 0, "no impairment listed"),
    (1, 1, "1 backup rep taken"),
    (2, 3, "2nd-string start in play"),
    (4, 6, "3rd-string involvement"),
    (7, 99, "4th-string / depleted"),
)

STARTER_DEPENDENT = {"OFFENCE_QB", "OFFENCE_LINE", "DEFENCE_PASS_RUSH", "DEFENCE_SECONDARY"}


def weight_of(row: dict) -> int:
    if row.get("game_status") == "Out":
        return WEIGHTS["Out"]
    prac = row.get("practice_status_abbrev", "")
    return WEIGHTS.get(prac, 0)


def tier_label(score: int) -> str:
    for lo, hi, label in TIERS:
        if lo <= score <= hi:
            return label
    return "unclassified"


def club_group_deficiency(rows: list[dict]) -> list[dict]:
    """Aggregate report rows into per-club, per-unit-group deficiency records."""
    buckets: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        unit = UNIT_OF.get(r["position"])
        if unit is None:
            raise ValueError(f"unmapped position {r['position']!r} for {r['player']!r}")
        buckets.setdefault((r["club"], unit), []).append(r)
    out = []
    for (club, unit), items in sorted(buckets.items()):
        for row in items:
            row["_w"] = weight_of(row)
        score = sum(r["_w"] for r in items)
        impaired = [r for r in items if r["_w"] >= 2]
        flagged = [r for r in items if r.get("game_status") == "Out"]
        out.append({
            "club": club,
            "unit_group": unit,
            "players_listed": len(items),
            "impaired_count": len(impaired),
            "out_count": len(flagged),
            "deficiency_score": score,
            "replacement_tier": tier_label(score),
            "cascading_cluster": "yes" if len(impaired) >= 2 else "no",
            "starter_dependent_unit": "yes" if unit in STARTER_DEPENDENT else "no",
            "affected_players": "; ".join(f"{r['player']} ({r['position']}, "
                                          f"{r.get('game_status') or r['practice_status_abbrev']})"
                                          for r in sorted(items, key=lambda x: -x["_w"])),
        })
        for row in items:
            row.pop("_w", None)
    return out


def matchup_deficiency(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Per-club summary used by the origination page (score and cluster counts)."""
    groups = club_group_deficiency(rows)
    summary: dict[str, dict[str, float]] = {}
    for g in groups:
        s = summary.setdefault(g["club"], {"score": 0.0, "clusters": 0.0, "worst": 0.0, "units": 0.0})
        s["score"] += g["deficiency_score"]
        s["clusters"] += 1 if g["cascading_cluster"] == "yes" else 0
        s["worst"] = max(s["worst"], g["deficiency_score"])
        s["units"] += 1
    return summary
