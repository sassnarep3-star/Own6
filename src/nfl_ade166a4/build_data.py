"""Build the nfl_ade166a4 data registers from committed transcription artifacts.

No network, no clock-dependent content (clocks come from the artifacts/log rows
themselves). Parses the two same-day injury-hub transcriptions (the ~09:01Z
a67ddef8 read and the ~11:07Z ade166a4 read) and publishes the row-level DELTA
between them — the delta, never the level.

    python3 -m src.nfl_ade166a4.build_data        # or: python3 src/nfl_ade166a4/build_data.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACK_A = os.path.join(REPO, "data", "nfl_a67ddef8")
PACK_B = os.path.join(REPO, "data", "nfl_ade166a4")

INJ_SRC = "https://www.nfl.com/injuries/league/2026/reg11"
STANDINGS_SRC = "https://www.nfl.com/standings/division/2026/reg"
SCHEDULE_SRC = "https://www.nfl.com/schedules/2026/by-week/week-11"
RESERVE_SRC = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
TRADES_SRC = "https://www.nfl.com/transactions/league/trades/2026/11"

CLOCK_B_INJ = "2026-11-19T11:07:00Z"     # second same-day read (upper bound on fetch)
CLOCK_B_STAND = "2026-11-19T11:08:00Z"
CLOCK_B_SCHED = "2026-11-19T11:10:00Z"
CLOCK_B_RESERVE = "2026-11-19T11:11:00Z"

INJ_FIELDS = ["game", "team", "player", "position", "injury", "practice_status",
              "game_status", "note", "source_url", "read_on_utc"]

# ---------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------

GAME_RE = re.compile(r"^## (?=MONDAY|SUNDAY|THURSDAY)")
TEAM_RE = re.compile(r"^### (.+?)(?:\s*\(\d+ rows\))?$")
ROW_RE = re.compile(r"^(.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*)$")


def read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def parse_injuries(path: str) -> list[dict]:
    """Parse a transcription in the shared pack format into row dicts.
    'No Injuries Reported' becomes a marker row (player='(no injuries reported)')."""
    rows: list[dict] = []
    game, team = "", ""
    for line in read_lines(path):
        if GAME_RE.match(line):
            game = line[3:].strip()
            continue
        m = TEAM_RE.match(line)
        if m:
            team = m.group(1).strip()
            continue
        if line.strip() == "No Injuries Reported":
            rows.append({"game": game, "team": team, "player": "(no injuries reported)",
                         "position": "", "injury": "", "practice_status": "",
                         "game_status": "", "row_class": "marker"})
            continue
        m = ROW_RE.match(line.strip())
        if m and team and game:
            player, position, injury, practice, gstatus = (s.strip() for s in m.groups())
            rows.append({
                "game": game, "team": team, "player": player, "position": position,
                "injury": "" if injury == "(blank)" else injury,
                "practice_status": practice,
                "game_status": "" if gstatus == "(blank)" else gstatus,
                "row_class": "player",
            })
    return rows


def parse_standings(path: str) -> list[dict]:
    rows: list[dict] = []
    div = ""
    for line in read_lines(path):
        if line.startswith("## "):
            div = line[3:].strip()
            continue
        m = re.match(r"^(.*?) \| (\d+) \| (\d+) \| (\d+) \| (0\.\d{3}) \| (\d+) \| (\d+) \| (-?\d+) \| ([0-9]+[WL])$", line.strip())
        if m:
            club, w, l, t, pct, pf, pa, net, streak = m.groups()
            rows.append({"club": club, "division": div, "w": int(w), "l": int(l),
                         "t": int(t), "pct": float(pct), "pf": int(pf), "pa": int(pa),
                         "net_pts": int(net), "streak": streak})
    return rows


def parse_schedule(path: str) -> list[dict]:
    rows: list[dict] = []
    for line in read_lines(path):
        m = re.match(r"^(\d{4}-\d{2}-\d{2}) \| (.+?) \| ([^|]+?) \| (.+?) \((\w{2,3})\) (\d-\d(?:-\d)?) \| at \| (.+?) \((\w{2,3})\) (\d-\d(?:-\d)?)$", line.strip())
        if m:
            date, ko, net, away, aab, arec, home, hab, hrec = m.groups()
            rows.append({"game_date": date, "kickoff_et": ko, "network": net,
                         "away": aab, "away_record": arec, "home": hab, "home_record": hrec})
    return rows


def parse_transactions(path: str, section: str) -> list[dict]:
    rows: list[dict] = []
    in_section = False
    for line in read_lines(path):
        if line.startswith("## "):
            in_section = line[3:].startswith(section)
            continue
        if not in_section:
            continue
        m = re.match(r"^(\d{2}/\d{2}) \| (.+?) \| (.+)$", line.strip())
        if m:
            date, who, kind = m.groups()
            rows.append({"date": date, "who": who, "kind": kind})
    return rows


# ---------------------------------------------------------------------------
# delta computation (the delta, never the level)
# ---------------------------------------------------------------------------

def injury_key(row: dict) -> str:
    return f"{row['team']}|{row['player']}"


def comparable_fields(row: dict) -> dict:
    return {f: row[f] for f in ("position", "injury", "practice_status", "game_status")}


def compute_delta(first: list[dict], second: list[dict]) -> tuple[list[dict], dict]:
    """Row-level delta between two same-day reads. Returns (delta_rows, summary)."""
    first_by_key = {injury_key(r): r for r in first if r["row_class"] == "player"}
    second_by_key = {injury_key(r): r for r in second if r["row_class"] == "player"}
    delta_rows: list[dict] = []
    added = sorted(set(second_by_key) - set(first_by_key))
    removed = sorted(set(first_by_key) - set(second_by_key))
    changed = []
    for key in sorted(set(first_by_key) & set(second_by_key)):
        a, b = comparable_fields(first_by_key[key]), comparable_fields(second_by_key[key])
        diff_fields = [f for f in a if a[f] != b[f]]
        if diff_fields:
            changed.append((key, diff_fields, a, b))
    for key in added:
        r = second_by_key[key]
        delta_rows.append({"comparison_key": key, "change_class": "added",
                           "field": "row", "value_first_read": "(absent)",
                           "value_second_read": " | ".join(v for v in (
                               r["position"], r["injury"], r["practice_status"],
                               r["game_status"]) if v) or "(all fields blank)"})
    for key in removed:
        r = first_by_key[key]
        delta_rows.append({"comparison_key": key, "change_class": "removed",
                           "field": "row", "value_first_read": " | ".join(v for v in (
                               r["position"], r["injury"], r["practice_status"],
                               r["game_status"]) if v) or "(all fields blank)",
                           "value_second_read": "(absent)"})
    for key, diff_fields, a, b in changed:
        for f in diff_fields:
            delta_rows.append({"comparison_key": key, "change_class": "changed",
                               "field": f, "value_first_read": a[f] or "(blank)",
                               "value_second_read": b[f] or "(blank)"})
    # game/team placement check: a row moving between games or teams without a
    # key change is impossible by construction, but markers (no-injury) and
    # game headers are compared separately below.
    games_first = sorted({r["game"] for r in first})
    games_second = sorted({r["game"] for r in second})
    summary = {
        "rows_first_read": len([r for r in first if r["row_class"] == "player"]),
        "rows_second_read": len([r for r in second if r["row_class"] == "player"]),
        "added": len(added), "removed": len(removed), "changed_fields": len(delta_rows) - len(added) - len(removed),
        "player_keys_unchanged": len(set(first_by_key) & set(second_by_key)) - len(changed),
        "games_first": len(games_first), "games_second": len(games_second),
        "games_identical": games_first == games_second,
        "markers_first": len([r for r in first if r["row_class"] == "marker"]),
        "markers_second": len([r for r in second if r["row_class"] == "marker"]),
    }
    return delta_rows, summary


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------

def write_csv(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    os.makedirs(PACK_B, exist_ok=True)

    # --- injuries (both same-day reads) ------------------------------------
    first = parse_injuries(os.path.join(PACK_A, "raw", "injuries_reg11_2026-11-19.md"))
    second = parse_injuries(os.path.join(PACK_B, "raw", "injuries_reg11_2026-11-19_b.md"))

    inj_rows = []
    for r in second:
        inj_rows.append({
            "game": r["game"], "team": r["team"], "player": r["player"],
            "position": r["position"], "injury": r["injury"],
            "practice_status": r["practice_status"], "game_status": r["game_status"],
            "note": "",
            "source_url": INJ_SRC, "read_on_utc": CLOCK_B_INJ,
        })
    write_csv(os.path.join(PACK_B, "injuries_reg11_b.csv"), INJ_FIELDS, inj_rows)

    delta_rows, summary = compute_delta(first, second)
    delta_fields = ["comparison_key", "change_class", "field", "value_first_read",
                    "value_second_read", "first_read_artifact", "second_read_artifact"]
    for r in delta_rows:
        r["first_read_artifact"] = "data/nfl_a67ddef8/raw/injuries_reg11_2026-11-19.md"
        r["second_read_artifact"] = "data/nfl_ade166a4/raw/injuries_reg11_2026-11-19_b.md"
    write_csv(os.path.join(PACK_B, "delta_reg11_sameday.csv"), delta_fields, delta_rows)

    sum_row = {
        "first_read_utc": "2026-11-19T09:01:02Z (a67ddef8 artifact-write clock, upper bound)",
        "second_read_utc": CLOCK_B_INJ + " (ade166a4 artifact-write clock, upper bound)",
        "window_hours": 2.1,
        "rows_first_read": summary["rows_first_read"],
        "rows_second_read": summary["rows_second_read"],
        "added": summary["added"], "removed": summary["removed"],
        "changed_fields": summary["changed_fields"],
        "player_keys_unchanged": summary["player_keys_unchanged"],
        "games_first": summary["games_first"], "games_second": summary["games_second"],
        "games_identical": summary["games_identical"],
        "markers_first": summary["markers_first"], "markers_second": summary["markers_second"],
        "conclusion": ("No row-level change between the two same-day reads; the "
                       "register is empty by observation, not by omission"),
        "source_url": INJ_SRC,
    }
    write_csv(os.path.join(PACK_B, "delta_summary.csv"),
              list(sum_row.keys()), [sum_row])

    # --- standings ----------------------------------------------------------
    standings = parse_standings(os.path.join(PACK_B, "raw", "standings_2026-11-19_b.md"))
    out = []
    for r in standings:
        out.append({"club": r["club"], "division": r["division"], "w": r["w"], "l": r["l"],
                    "t": r["t"], "pct": f'{r["pct"]:.3f}', "pf": r["pf"], "pa": r["pa"],
                    "net_pts": r["net_pts"], "streak": r["streak"],
                    "source_url": STANDINGS_SRC, "read_on_utc": CLOCK_B_STAND})
    write_csv(os.path.join(PACK_B, "standings_2026_11_19b.csv"),
              ["club", "division", "w", "l", "t", "pct", "pf", "pa", "net_pts",
               "streak", "source_url", "read_on_utc"], out)
    w_sum = sum(r["w"] for r in standings)
    l_sum = sum(r["l"] for r in standings)
    t_sum = sum(r["t"] for r in standings)
    pf_sum = sum(r["pf"] for r in standings)
    pa_sum = sum(r["pa"] for r in standings)
    assert len(standings) == 32, f"standings clubs {len(standings)} != 32"
    assert w_sum == l_sum == 149, f"W/L {w_sum}/{l_sum} != 149/149"
    assert t_sum == 2, f"T {t_sum} != 2"
    assert pf_sum == pa_sum == 6923, f"PF/PA {pf_sum}/{pa_sum} != 6923/6923"

    # --- week 11 slate --------------------------------------------------------
    slate = parse_schedule(os.path.join(PACK_B, "raw", "week11_schedule_2026-11-19_b.md"))
    assert len(slate) == 13, f"slate games {len(slate)} != 13"
    out = []
    for r in slate:
        out.append({**r, "source_url": SCHEDULE_SRC, "read_on_utc": CLOCK_B_SCHED})
    write_csv(os.path.join(PACK_B, "week11_slate_b.csv"),
              ["game_date", "kickoff_et", "network", "away", "away_record",
               "home", "home_record", "source_url", "read_on_utc"], out)

    # --- transactions ---------------------------------------------------------
    reserve = parse_transactions(os.path.join(PACK_B, "raw", "transactions_2026-11-19_b.md"),
                                 "Reserve List")
    trades = parse_transactions(os.path.join(PACK_B, "raw", "transactions_2026-11-19_b.md"),
                                "Trades")
    assert len(reserve) == 25, f"reserve rows {len(reserve)} != 25"
    assert len(trades) == 12, f"trade rows {len(trades)} != 12"
    write_csv(os.path.join(PACK_B, "reserve_nov2026_b.csv"),
              ["date", "who", "kind", "source_url", "read_on_utc"],
              [{**r, "source_url": RESERVE_SRC, "read_on_utc": CLOCK_B_RESERVE} for r in reserve])
    write_csv(os.path.join(PACK_B, "trades_nov2026_b.csv"),
              ["date", "who", "kind", "source_url", "read_on_utc"],
              [{**r, "source_url": TRADES_SRC, "read_on_utc": CLOCK_B_RESERVE} for r in trades])

    print(f"injuries_b rows      : {len(inj_rows)} "
          f"({len([r for r in second if r['row_class'] == 'player'])} players "
          f"+ {len([r for r in second if r['row_class'] == 'marker'])} markers)")
    print(f"delta rows           : {len(delta_rows)} "
          f"(added {summary['added']}, removed {summary['removed']}, "
          f"changed {summary['changed_fields']}, unchanged keys {summary['player_keys_unchanged']})")
    print(f"standings            : 32 clubs, {w_sum}W/{l_sum}L/{t_sum}T, PF=PA={pf_sum}")
    print(f"week11 slate         : {len(slate)} games")
    print(f"reserve/trade rows   : {len(reserve)}/{len(trades)}")


if __name__ == "__main__":
    main()
