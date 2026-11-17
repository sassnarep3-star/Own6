"""Settlement engine: grade every pre-kickoff week-10 forecast in the repo
against the official finals read this session.

Two things make this different from the sibling packs' grading:

1. **Point-in-time provenance.** Each forecast row is traced to the git commit
   that first added its file (``git log --diff-filter=A``). That commit time is
   compared with the fixture's kickoff. A row committed *after* its game kicked
   off is labelled ``post_kickoff`` and is excluded from every score. Without
   this check a "prospective" table can contain a forecast made after the result
   was public, which is lookahead leakage.

2. **Official result only.** The result comes from this session's capture of the
   nfl.com week-10 schedule page (``capture.W10_CARDS``). No result is taken from
   another pack's CSV, because a pack's CSV is not an official source.

Nothing here is a price. No row carries a stake, a payout or a return, so no ROI
or closing-line value can be computed and none is printed.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

from . import capture as C

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Kickoff instants in UTC for the week-10 fixtures. Derived from the schedule
# page's own ET clock (the page prints ET; November is standard time, UTC-5) and
# printed so the derivation can be checked: 11-12 8:15 PM ET = 11-13 01:15Z.
KICKOFF_UTC = {
    "W10-01": "2026-11-13T01:15:00Z",  # Thu Nov 12, 8:15 PM ET
    "W10-02": "2026-11-15T14:30:00Z",  # Sun Nov 15, 9:30 AM ET
    "W10-03": "2026-11-15T18:00:00Z",  # Sun Nov 15, 1:00 PM ET
    "W10-04": "2026-11-15T18:00:00Z",
    "W10-05": "2026-11-15T18:00:00Z",
    "W10-06": "2026-11-15T18:00:00Z",
    "W10-07": "2026-11-15T18:00:00Z",
    "W10-08": "2026-11-15T18:00:00Z",
    "W10-09": "2026-11-15T18:00:00Z",
    "W10-10": "2026-11-15T21:05:00Z",  # Sun Nov 15, 4:05 PM ET
    "W10-11": "2026-11-15T21:05:00Z",
    "W10-12": "2026-11-15T21:25:00Z",  # Sun Nov 15, 4:25 PM ET
    "W10-13": "2026-11-16T01:20:00Z",  # Sun Nov 15, 8:20 PM ET
    "W10-14": "2026-11-17T01:15:00Z",  # Mon Nov 16, 8:15 PM ET
}

# ---------------------------------------------------------------------------
# forecast sources. Each entry says where a probability lives, how to read it,
# and what its own file claims about when it was made.
# ---------------------------------------------------------------------------
SOURCE_SPECS = [
    {
        "pack": "a411fed0",
        "path": "data/nfl_a411fed0/origination_2026_w10.psv",
        "delim": "|",
        "encoding": "utf-8-sig",
        "game_key": "game_slug",
        "game_key_kind": "slug",
        "prob_col": "origination_step_3_p_home_win_empirical",
        "prob_col_alt": "origination_step_3_p_home_win_normal",
        "home_col": "home_abbr",
        "away_col": "away_abbr",
        "strategy": "A411-ML-EMPIRICAL",
        "strategy_alt": "A411-ML-NORMAL",
        "family": "moneyline_probability",
    },
    {
        "pack": "d966f630",
        "path": "data/nfl_d966f630/originated_lines.csv",
        "delim": ",",
        "encoding": "utf-8",
        "game_key": "game_id",
        "game_key_kind": "game_id",
        "prob_col": "moneyline_prob_home",
        "home_col": "home",
        "away_col": "away",
        "strategy": "D966-ML",
        "family": "moneyline_probability",
    },
    {
        "pack": "6cefc476",
        "path": "data/nfl_6cefc476/originated_lines.csv",
        "delim": ",",
        "encoding": "utf-8",
        "game_key": "matchup",
        "game_key_kind": "matchup",
        "prob_col": "model_win_prob_home",
        "home_col": "",
        "away_col": "",
        "strategy": "N6F-ML",
        "family": "moneyline_probability",
        "coverage_note": "file holds no W10-01 (WAS at NYG) moneyline row; the pack published it as a side market only",
        "filter_col": "market_type",
        "filter_val": "moneyline",
    },
    {
        "pack": "wk",
        "path": "data/nfl_wk/own_lines.csv",
        "delim": ",",
        "encoding": "utf-8",
        "game_key": "matchup",
        "game_key_kind": "matchup2",
        "prob_col": "own_win_prob_home",
        "home_col": "",
        "away_col": "",
        "strategy": "WK-ML",
        "family": "moneyline_probability",
        "coverage_note": "file holds 13 rows; W10-01 (WAS at NYG) is absent from the pack itself",
    },
]


# Provenance is *captured data*, not derived at build time.
#
# Each entry was read once, in this session, with
#     git log --diff-filter=A --format=%H -- <path>   (take the earliest)
#     git show -s --format=%cI <sha>
# and is frozen here. Deriving it inside the builder would make the published
# point-in-time labels depend on the commit graph the builder happens to see:
# on a GitHub pull-request merge ref the same files resolve to different commits,
# so the same CSV rebuilt in CI differed from the committed one. A frozen table
# is reproducible everywhere and is checkable by hand with the two commands above.
FIRST_ADD_COMMIT = {
    "data/nfl_a411fed0/origination_2026_w10.psv": (
        "2026-11-14T22:28:35+00:00", "e919855d",
        "e919855d0a3d6faa136165d6ec865a5c2aad30ef"),
    "data/nfl_d966f630/originated_lines.csv": (
        "2026-11-14T22:21:15+00:00", "f5c0790e",
        "f5c0790e2f183025549c8e6360198d1c8f4b34c2"),
    "data/nfl_6cefc476/originated_lines.csv": (
        "2026-11-14T22:14:54+00:00", "834555be",
        "834555bea41500ef112512ef5539ea196e8a9022"),
    "data/nfl_wk/own_lines.csv": (
        "2026-11-13T21:46:37+00:00", "1abbff43",
        "1abbff430ff30d36812ae112f1278404d2b914bc"),
}


def first_add_commit(path: str) -> tuple[str, str]:
    """(committed_iso_utc, short_sha) of the commit that first added ``path``."""
    entry = FIRST_ADD_COMMIT.get(path)
    if entry is None:
        return "", ""
    return entry[0], entry[1]


def parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def iso(d: datetime) -> str:
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# official finals, from this session's capture
# ---------------------------------------------------------------------------
def finals() -> dict[str, dict]:
    out = {}
    for gid, away, home, day, slot, status, asc, hsc, mark in C.W10_CARDS:
        if status != "FINAL":
            out[gid] = {
                "game_id": gid, "away": away, "home": home, "day": day, "slot": slot,
                "status": status, "away_score": "", "home_score": "",
                "margin_home": "", "total": "", "winner": "", "final": False,
                "event_mark": mark,
                "game_url": C.W10_GAME_URL.format(slug=C.W10_SLUGS[gid]),
            }
            continue
        margin = hsc - asc
        out[gid] = {
            "game_id": gid, "away": away, "home": home, "day": day, "slot": slot,
            "status": status, "away_score": asc, "home_score": hsc,
            "margin_home": margin, "total": asc + hsc,
            "winner": home if margin > 0 else (away if margin < 0 else "tie"),
            "final": True, "event_mark": mark,
            "game_url": C.W10_GAME_URL.format(slug=C.W10_SLUGS[gid]),
        }
    return out


SLUG_TO_GID = {v: k for k, v in C.W10_SLUGS.items()}
ABBR_TO_GID = {}
for _gid, _away, _home, *_rest in C.W10_CARDS:
    ABBR_TO_GID[(_away, _home)] = _gid

# the 6cefc476 / wk packs use their own internal ids; map by abbr pair instead
MATCHUP_ALIASES = {
    "LAR": "LA",
}


def norm_abbr(a: str) -> str:
    a = (a or "").strip().upper()
    return MATCHUP_ALIASES.get(a, a)


def resolve_game_id(row: dict, spec: dict) -> tuple[str, str]:
    """Return (game_id, how_resolved). Empty game_id means unresolved."""
    kind = spec["game_key_kind"]
    raw = (row.get(spec["game_key"]) or "").strip()
    if kind == "slug":
        for gid, slug in C.W10_SLUGS.items():
            if raw == f"{slug}-2026-reg-10":
                return gid, "slug"
        return "", "slug_unmatched"
    if kind == "game_id":
        # d966f630 prefixes the season: "2026-W10-01"
        if raw.startswith("2026-"):
            raw = raw[5:]
        return (raw, "game_id") if raw in C.W10_SLUGS else ("", "game_id_unmatched")
    # matchup forms: "NE at DET", "Patriots at Lions"
    if " at " not in raw:
        return "", "matchup_unparsed"
    left, right = raw.split(" at ", 1)
    left, right = norm_abbr(left.strip()), norm_abbr(right.strip())
    left, right = norm_abbr(left), norm_abbr(right)
    for (a, h), gid in ABBR_TO_GID.items():
        if (left, right) == (a, h):
            return gid, "matchup_abbr"
    # 6cefc476 prints club names; map by the official page's own club names
    NAME_TO_ABBR = {
        "patriots": "NE", "lions": "DET", "chiefs": "KC", "falcons": "ATL",
        "texans": "HOU", "browns": "CLE", "vikings": "MIN", "packers": "GB",
        "dolphins": "MIA", "colts": "IND", "panthers": "CAR", "saints": "NO",
        "bills": "BUF", "jets": "NYJ", "jaguars": "JAX", "titans": "TEN",
        "rams": "LA", "cardinals": "AZ", "seahawks": "SEA", "raiders": "LV",
        "49ers": "SF", "cowboys": "DAL", "steelers": "PIT", "bengals": "CIN",
        "chargers": "LAC", "ravens": "BAL", "commanders": "WAS", "giants": "NYG",
    }
    la = NAME_TO_ABBR.get(left.lower(), left)
    ra = NAME_TO_ABBR.get(right.lower(), right)
    for (a, h), gid in ABBR_TO_GID.items():
        if (la, ra) == (a, h):
            return gid, "matchup_name"
    return "", "matchup_unmatched"


def load_rows(spec: dict) -> list[dict]:
    path = os.path.join(REPO, spec["path"])
    with open(path, encoding=spec["encoding"], newline="") as fh:
        return list(csv.DictReader(fh, delimiter=spec["delim"]))


def build_register() -> list[dict]:
    """One row per (forecast source row) that names a week-10 fixture."""
    fin = finals()
    out = []

    def add(spec, row, gid, prob, strategy, family, note=""):
        add_iso, add_sha = first_add_commit(spec["path"])
        ko = parse_iso(KICKOFF_UTC[gid])
        made = parse_iso(add_iso)
        if made is None or ko is None:
            pit = "unknown"
        elif made < ko:
            pit = "pre_kickoff"
        else:
            pit = "post_kickoff"
        out.append({
            "forecast_id": f"{spec['pack']}:{gid}:{strategy}",
            "strategy_id": strategy,
            "family": family,
            "pack": spec["pack"],
            "source_path": spec["path"],
            "game_id": gid,
            "away": fin[gid]["away"],
            "home": fin[gid]["home"],
            "p_home_win": f"{prob:.6f}",
            "kickoff_utc": KICKOFF_UTC[gid],
            "value_committed_utc": add_iso,
            "commit": add_sha,
            "point_in_time": pit,
            "note": note,
            "source_url": C.URL_REPO + "/blob/main/" + spec["path"],
        })

    for spec in SOURCE_SPECS:
        for row in load_rows(spec):
            if spec.get("filter_col") and row.get(spec["filter_col"]) != spec["filter_val"]:
                continue
            gid, how = resolve_game_id(row, spec)
            if not gid:
                continue
            raw = (row.get(spec["prob_col"]) or "").strip()
            if not raw:
                continue
            try:
                prob = float(raw)
            except ValueError:
                continue
            if not 0.0 < prob < 1.0:
                continue
            add(spec, row, gid, prob, spec["strategy"], spec["family"], f"resolved_by={how}")
            alt = spec.get("prob_col_alt")
            if alt:
                raw_alt = (row.get(alt) or "").strip()
                if raw_alt:
                    try:
                        p2 = float(raw_alt)
                    except ValueError:
                        p2 = None
                    if p2 and 0.0 < p2 < 1.0:
                        add(spec, row, gid, p2, spec["strategy_alt"], spec["family"],
                            f"resolved_by={how}; second estimator published beside the first")
    return out


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def brier(p: float, outcome_home: int) -> float:
    return (p - outcome_home) ** 2


def log_loss(p: float, outcome_home: int) -> float:
    import math
    q = p if outcome_home == 1 else 1.0 - p
    return -math.log(max(q, 1e-12))


def settle_row(row: dict, fin: dict) -> dict:
    if not fin.get("final"):
        row.update({
            "settled": "no", "actual_winner": "", "outcome_home": "",
            "brier": "", "log_loss": "", "correct_pick": "",
            "settle_reason": "official page still shows the card as not final at this read",
        })
        return row
    margin = fin["margin_home"]
    if margin > 0:
        outcome_home, winner = 1, fin["home"]
    elif margin < 0:
        outcome_home, winner = 0, fin["away"]
    else:
        outcome_home, winner = None, "tie"
    p = float(row["p_home_win"])
    row["settled"] = "yes"
    row["actual_winner"] = winner
    row["actual_margin_home"] = margin
    row["actual_total"] = fin["total"]
    row["outcome_home"] = "" if outcome_home is None else outcome_home
    row["brier"] = "" if outcome_home is None else f"{brier(p, outcome_home):.6f}"
    row["log_loss"] = "" if outcome_home is None else f"{log_loss(p, outcome_home):.6f}"
    if outcome_home is None:
        row["correct_pick"] = ""
    else:
        pick_home = p >= 0.5
        row["correct_pick"] = "yes" if pick_home == bool(outcome_home) else "no"
    row["settle_reason"] = ""
    return row


def settle_all(register: list[dict]) -> list[dict]:
    fin = finals()
    return [settle_row(dict(r), fin[r["game_id"]]) for r in register]
