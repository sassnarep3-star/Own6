"""Offensive and defensive starter-vs-backup (1st, 2nd, 3rd, 4th string) depth-deficiency model.

Models NFL roster rules (53-man active/inactive list, 48-man vs. 47-man gameday active list
requiring >=8 offensive linemen, max 2 practice squad elevations per week, 90-minute pre-kickoff
inactive report) and computes unit-level compounding penalties when multiple offensive line or
defensive secondary/front starters are replaced by 2nd, 3rd, or 4th string backups.
"""
from __future__ import annotations

from dataclasses import dataclass

VALID_SIDES = {"OFFENSE", "DEFENSE"}
VALID_PRACTICE_STATUSES = {"FP", "LP", "DNP", "IR", "OUT_ON_REPORT"}
VALID_GAME_STATUSES = {"ACTIVE_EXPECTED", "QUESTIONABLE", "DOUBTFUL", "OUT", "IR"}

# Structural prior weights (uncalibrated structural severity index on [0, 1] scale;
# empirical point drop-offs require authorized play-by-play calibration).
POSITION_IMPORTANCE_WEIGHTS: dict[str, float] = {
    "QB": 1.00,
    "LT": 0.42,
    "RT": 0.36,
    "C": 0.34,
    "LG": 0.28,
    "RG": 0.28,
    "WR1": 0.38,
    "WR2": 0.26,
    "SLOT_WR": 0.22,
    "TE1": 0.24,
    "RB1": 0.20,
    "RB2": 0.20,
    "CB1": 0.40,
    "CB2": 0.32,
    "NICKEL_CB": 0.28,
    "EDGE1": 0.40,
    "EDGE2": 0.30,
    "DT_NT": 0.28,
    "LB_GREEN_DOT": 0.34,
    "FS": 0.30,
    "SS": 0.26,
}

# Replacement string severity multiplier relative to 1st-string starter (string 1 = 0.0 deficiency)
STRING_REPLACEMENT_MULTIPLIER: dict[int, float] = {
    1: 0.00,  # 1st-string starter active at full capacity
    2: 0.45,  # 2nd-string primary backup
    3: 0.80,  # 3rd-string reserve / emergency 3rd QB
    4: 1.15,  # 4th-string practice squad elevation / emergency cross-positional fill-in
}


@dataclass(frozen=True)
class DepthSlotStatus:
    team: str
    side: str  # "OFFENSE" or "DEFENSE"
    unit_group: str  # "QB", "OL", "SKILL", "DL_EDGE", "LB", "SECONDARY"
    position_slot: str
    starter_name: str
    active_replacement_name: str
    active_string_tier: int  # 1, 2, 3, or 4
    practice_status: str  # "FP", "LP", "DNP", "IR"
    game_status: str  # "ACTIVE_EXPECTED", "QUESTIONABLE", "DOUBTFUL", "OUT", "IR"


@dataclass(frozen=True)
class UnitDeficiencyReport:
    team: str
    side: str
    slots_evaluated: int
    starters_replaced: int
    second_string_count: int
    third_string_count: int
    fourth_string_count: int
    cluster_penalty_multiplier: float
    structural_deficiency_index: float


def check_gameday_active_limit(
    active_roster_count: int,
    active_offensive_linemen: int,
    practice_squad_elevations: int = 0,
) -> tuple[bool, int, str]:
    """Validate NFL CBA gameday active roster limits (operations.nfl.com).

    - Maximum gameday active players is 48 if >= 8 offensive linemen (C, G, T) are active;
      otherwise maximum drops to 47.
    - Practice squad standard elevations are capped at 2 players per game week (expanding
      the 53-man Active/Inactive List to 54 or 55).
    """
    if practice_squad_elevations < 0 or practice_squad_elevations > 2:
        return (
            False,
            48 if active_offensive_linemen >= 8 else 47,
            f"Practice squad elevations ({practice_squad_elevations}) violate CBA max of 2 per week.",
        )
    max_active = 48 if active_offensive_linemen >= 8 else 47
    if active_roster_count > max_active:
        return (
            False,
            max_active,
            f"Active gameday count ({active_roster_count}) exceeds limit ({max_active}) for {active_offensive_linemen} active OL.",
        )
    return (True, max_active, "Compliant with NFL CBA gameday active roster rule.")


def evaluate_unit_deficiency(slots: list[DepthSlotStatus]) -> UnitDeficiencyReport:
    """Compute structural depth-deficiency index for an NFL offensive or defensive unit.

    Accounts for:
      1. Positional weight & active replacement string (1st vs 2nd vs 3rd vs 4th string)
      2. Limited-participation / Questionable starter degradation
      3. Non-linear cluster interaction when >=2 starters in a cohesive unit (OL or Secondary
         or DL/LB) are simultaneously replaced by backups.
    """
    if not slots:
        raise ValueError("slots list cannot be empty.")
    team = slots[0].team
    side = slots[0].side
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side {side!r}; must be in {VALID_SIDES}.")

    starters_replaced = 0
    s2 = s3 = s4 = 0
    raw_score = 0.0
    unit_replacements: dict[str, int] = {}

    for slot in slots:
        if slot.team != team or slot.side != side:
            raise ValueError("All slots in evaluate_unit_deficiency must belong to the same team and side.")
        if slot.active_string_tier not in STRING_REPLACEMENT_MULTIPLIER:
            raise ValueError(f"Invalid string tier {slot.active_string_tier}; must be 1, 2, 3, or 4.")
        weight = POSITION_IMPORTANCE_WEIGHTS.get(slot.position_slot, 0.25)
        tier_mult = STRING_REPLACEMENT_MULTIPLIER[slot.active_string_tier]

        if slot.active_string_tier > 1:
            starters_replaced += 1
            unit_replacements[slot.unit_group] = unit_replacements.get(slot.unit_group, 0) + 1
            if slot.active_string_tier == 2:
                s2 += 1
            elif slot.active_string_tier == 3:
                s3 += 1
            elif slot.active_string_tier == 4:
                s4 += 1
            raw_score += weight * tier_mult
        elif slot.practice_status in {"LP", "DNP"} or slot.game_status in {"QUESTIONABLE", "DOUBTFUL"}:
            # Starter expected to play through injury or game-time decision carries partial degradation
            raw_score += weight * (0.15 if slot.practice_status == "LP" else 0.28)

    # Non-linear cluster penalty when >= 2 starters in the same cohesive unit (e.g., OL or Secondary) are out
    max_cluster_in_group = max(unit_replacements.values(), default=0)
    if max_cluster_in_group >= 3:
        cluster_mult = 1.35
    elif max_cluster_in_group == 2:
        cluster_mult = 1.18
    else:
        cluster_mult = 1.00

    return UnitDeficiencyReport(
        team=team,
        side=side,
        slots_evaluated=len(slots),
        starters_replaced=starters_replaced,
        second_string_count=s2,
        third_string_count=s3,
        fourth_string_count=s4,
        cluster_penalty_multiplier=cluster_mult,
        structural_deficiency_index=round(raw_score * cluster_mult, 4),
    )
