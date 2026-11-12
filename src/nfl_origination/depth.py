"""NFL Roster Rules & Starter-vs-Backup (1st/2nd/3rd/4th String) Depth-Deficiency Engine.

Implements official NFL Football Operations roster rules:
- 53-man Active/Inactive List (+ up to 2 Standard Practice Squad Elevations -> 54 or 55;
  each PS player capped at 3 regular-season elevations per League Year).
- 48-player Gameday Active List ONLY if >= 8 offensive linemen (C/G/T) are active;
  otherwise maximum drops to 47 active players.
- Emergency Third Quarterback (90-minute Gameday Administration Report): must be a bona fide
  QB on the 53-man roster (NOT a Practice Squad elevation), requires 2 active bona fide QBs on
  the 47/48 list, and may enter ONLY on injury/disqualification of both QB1 and QB2.
- Injured Reserve designated-for-return: minimum 4-game absence; max 8 regular-season
  designations (+2 in postseason).

Also evaluates Offensive and Defensive unit depth deficiencies when 1st-string starters
are replaced by 2nd-, 3rd-, or 4th-string backups, including cascading multi-player
unit cluster alerts. Never invents point/EPA weights when empirical drop-off calibration
is unverified (`dropoff_epa_by_string=None` -> `estimated_epa_delta=None`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

VALID_STRINGS = (1, 2, 3, 4)
VALID_SIDES = ("OFFENSE", "DEFENSE", "SPECIAL_TEAMS")
VALID_PRACTICE_STATUSES = ("FULL", "LIMITED", "DNP", "NOT_LISTED")
VALID_GAME_STATUSES = ("ACTIVE_EXPECTED", "QUESTIONABLE", "DOUBTFUL", "OUT", "IR", "INACTIVE")


@dataclass(frozen=True)
class GamedayRosterCheck:
    valid: bool
    max_gameday_active_allowed: int
    total_contract_pool: int
    violations: tuple[str, ...]


def validate_nfl_gameday_roster(
    roster_53_count: int,
    ps_standard_elevations: int,
    gameday_active_count: int,
    active_offensive_linemen: int,
    active_bona_fide_qbs: int,
    has_emergency_third_qb: bool,
    emergency_qb_is_ps_elevation: bool = False,
    player_season_ps_elevations: Sequence[int] = (),
    regular_season_ir_returns_used: int = 0,
) -> GamedayRosterCheck:
    """Validate an NFL club's gameday roster against official 2026 NFL Operations rules."""
    violations: list[str] = []
    if not (0 <= roster_53_count <= 53):
        violations.append(f"53-man roster count ({roster_53_count}) exceeds 53-player limit")
    if not (0 <= ps_standard_elevations <= 2):
        violations.append(f"Practice squad standard elevations ({ps_standard_elevations}) must be 0, 1, or 2")
    total_pool = roster_53_count + ps_standard_elevations
    if total_pool > 55:
        violations.append(f"Expanded active/inactive pool ({total_pool}) exceeds 55-player limit")

    max_active = 48 if active_offensive_linemen >= 8 else 47
    if gameday_active_count > max_active:
        violations.append(
            f"Gameday active count ({gameday_active_count}) exceeds {max_active} "
            f"(active offensive linemen={active_offensive_linemen}; >=8 required for 48 actives)"
        )
    if has_emergency_third_qb:
        if emergency_qb_is_ps_elevation:
            violations.append("Emergency 3rd QB must be on the 53-man roster, not a Practice Squad elevation")
        if active_bona_fide_qbs != 2:
            violations.append(
                f"Emergency 3rd QB requires exactly 2 bona fide QBs on 47/48 active list (got {active_bona_fide_qbs})"
            )
    for idx, elev_count in enumerate(player_season_ps_elevations, 1):
        if elev_count > 3:
            violations.append(f"Practice squad player #{idx} has {elev_count} regular-season elevations (max 3)")
    if regular_season_ir_returns_used > 8:
        violations.append(
            f"Regular-season IR designated-for-return count ({regular_season_ir_returns_used}) exceeds 8"
        )
    return GamedayRosterCheck(
        valid=len(violations) == 0,
        max_gameday_active_allowed=max_active,
        total_contract_pool=total_pool,
        violations=tuple(violations),
    )


@dataclass(frozen=True)
class DepthSlot:
    player_name: str
    position: str
    unit_group: str
    side: str
    string_rank: int  # 1 = starter, 2 = 2nd string, 3 = 3rd string, 4 = 4th string / PS
    practice_status: str  # FULL, LIMITED, DNP, NOT_LISTED
    game_status: str  # ACTIVE_EXPECTED, QUESTIONABLE, DOUBTFUL, OUT, IR, INACTIVE

    def __post_init__(self) -> None:
        if self.string_rank not in VALID_STRINGS:
            raise ValueError(f"string_rank must be in {VALID_STRINGS}; got {self.string_rank}")
        if self.side not in VALID_SIDES:
            raise ValueError(f"side must be in {VALID_SIDES}; got {self.side}")
        if self.practice_status not in VALID_PRACTICE_STATUSES:
            raise ValueError(f"invalid practice_status: {self.practice_status}")
        if self.game_status not in VALID_GAME_STATUSES:
            raise ValueError(f"invalid game_status: {self.game_status}")

    @property
    def is_ruled_unavailable(self) -> bool:
        return self.game_status in {"OUT", "IR", "INACTIVE"}

    @property
    def is_impaired_or_out(self) -> bool:
        return self.is_ruled_unavailable or self.game_status in {"DOUBTFUL", "QUESTIONABLE"} or self.practice_status == "DNP"


@dataclass(frozen=True)
class UnitDeficiencySummary:
    team: str
    side: str
    unit_group: str
    projected_active_Top_string: int | None
    projected_replacement_player: str | None
    starters_ruled_out: int
    starters_impaired_or_out: int
    backups_impaired_or_out: int
    cascading_cluster_alert: bool
    deficiency_tier: str
    estimated_epa_per_play_delta: float | None


def evaluate_unit_deficiency(
    team: str,
    side: str,
    unit_group: str,
    slots: Sequence[DepthSlot],
    calibrated_dropoff_epa_by_string: Mapping[int, float] | None = None,
    cluster_interaction_multiplier: float | None = None,
) -> UnitDeficiencySummary:
    """Evaluate starter-to-backup replacement depth (1st -> 2nd -> 3rd -> 4th string).

    If `calibrated_dropoff_epa_by_string` is None (unverified empirical drop-off),
    `estimated_epa_per_play_delta` stays strictly None rather than guessing a penalty.
    """
    if not slots:
        raise ValueError("slots must be non-empty")
    ordered = sorted(slots, key=lambda s: s.string_rank)
    available = [s for s in ordered if not s.is_ruled_unavailable and s.practice_status != "DNP"]
    # If all listed players are DNP/Out, fall back to lowest-rank player not explicitly ruled Out/IR
    not_out = [s for s in ordered if not s.is_ruled_unavailable]
    top_slot = available[0] if available else (not_out[0] if not_out else None)

    starters_out = sum(1 for s in ordered if s.string_rank == 1 and s.is_ruled_unavailable)
    starters_imp = sum(1 for s in ordered if s.string_rank == 1 and s.is_impaired_or_out)
    backups_imp = sum(1 for s in ordered if s.string_rank >= 2 and s.is_impaired_or_out)

    # Cascading cluster alert triggers when starter is impaired/out AND a backup is also impaired/out,
    # or when >=2 starters in the same unit group (e.g. OL or DB) are impaired/out, or forced to >=3rd string.
    top_string = top_slot.string_rank if top_slot is not None else None
    cascade = (
        (starters_imp >= 2)
        or (starters_imp >= 1 and backups_imp >= 1)
        or (top_string is not None and top_string >= 3)
        or (top_string is None)
    )

    if top_string is None or top_string == 4:
        tier = "CRITICAL_4TH_STRING_OR_DEPLETED"
    elif top_string == 3:
        tier = "SEVERE_3RD_STRING_ELEVATION"
    elif top_string == 2 and cascade:
        tier = "HIGH_2ND_STRING_THIN_BEHIND"
    elif top_string == 2:
        tier = "MODERATE_2ND_STRING_REPLACEMENT"
    elif starters_imp >= 1:
        tier = "WATCH_STARTER_LIMITED"
    else:
        tier = "NOMINAL_1ST_STRING_HEALTHY"

    epa_delta: float | None = None
    if calibrated_dropoff_epa_by_string is not None and top_string is not None:
        if top_string not in calibrated_dropoff_epa_by_string:
            raise ValueError(f"missing calibrated drop-off for string {top_string}")
        base_delta = float(calibrated_dropoff_epa_by_string[top_string])
        if cascade and cluster_interaction_multiplier is not None:
            epa_delta = base_delta * float(cluster_interaction_multiplier)
        else:
            epa_delta = base_delta

    return UnitDeficiencySummary(
        team=team,
        side=side,
        unit_group=unit_group,
        projected_active_Top_string=top_string,
        projected_replacement_player=top_slot.player_name if top_slot else None,
        starters_ruled_out=starters_out,
        starters_impaired_or_out=starters_imp,
        backups_impaired_or_out=backups_imp,
        cascading_cluster_alert=cascade,
        deficiency_tier=tier,
        estimated_epa_per_play_delta=epa_delta,
    )
