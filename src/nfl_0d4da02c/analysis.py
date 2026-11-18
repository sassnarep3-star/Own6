"""Numbers computed only from this session's official reads.

Discipline: every number emitted here is a COUNT or a RATIO of rows that were
read from an official page on 2026-11-18. No number is a model output, no
number is a forecast, and no number is a claim about profit. Where a ratio has
a denominator of zero the cell is left blank. Where a quantity the owner asked
for needs an outcome (did the player actually play?) it is NOT computed here:
that needs the inactive list, which is registered as an information gap.

Run:  python3 -m src.nfl_0d4da02c.analysis
"""
from __future__ import annotations

import csv
import os
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl_0d4da02c")

INJ_URL = "https://www.nfl.com/injuries/"
READ_DATE = "2026-11-18"
POSITION_GROUPS = [
    ("QB", ("QB",)),
    ("Skill (RB/FB/WR/TE)", ("RB", "FB", "WR", "TE")),
    ("Offensive line (T/G/C)", ("T", "G", "C", "LS")),
    ("Defensive line (DE/DT)", ("DE", "DT")),
    ("Linebacker", ("LB",)),
    ("Secondary (CB/S)", ("CB", "S")),
    ("Specialists (K/P)", ("K", "P")),
]


def _read(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write(name: str, header: list[str], rows: list[list]) -> None:
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


def _pct(a: int, b: int) -> str:
    """Ratio of two official counts, rounded to 1dp. Blank if undefined."""
    if not b:
        return ""
    return f"{100.0 * a / b:.1f}"


def main() -> int:
    inj = _read("injury_report_2026_11_18.csv")
    n = len(inj)

    # ---- 1. headline counts ------------------------------------------------
    gs = Counter(r["game_status"] or "(blank)" for r in inj)
    ps = Counter(r["practice_status"] for r in inj)
    _write("designation_counts.csv",
           ["read_date", "dimension", "value", "n", "pct_of_rows", "source_url"],
           [["2026-11-18", "game_status", k, gs[k], _pct(gs[k], n), INJ_URL]
            for k in sorted(gs, key=lambda k: -gs[k])]
           + [["2026-11-18", "practice_status", k, ps[k], _pct(ps[k], n), INJ_URL]
              for k in sorted(ps, key=lambda k: -ps[k])]
           + [["2026-11-18", "rows_total", "", n, "100.0", INJ_URL]])

    # ---- 2. game status x practice status cross-tab ------------------------
    order_gs = ["Out", "Doubtful", "Questionable", "(blank)"]
    order_ps = ["Did Not Participate In Practice", "Limited Participation in Practice",
                "Full Participation in Practice"]
    cross = Counter((r["game_status"] or "(blank)", r["practice_status"]) for r in inj)
    rows = []
    for g in order_gs:
        for p in order_ps:
            c = cross.get((g, p), 0)
            dn = gs.get(g, 0)
            rows.append(["2026-11-18", g, p, c, dn, _pct(c, dn), INJ_URL])
    _write("designation_xtab.csv",
           ["read_date", "game_status", "practice_status", "n_cells",
            "n_with_that_game_status", "pct_of_game_status", "source_url"], rows)

    # ---- 3. per club -------------------------------------------------------
    clubs: "OrderedDict[str, Counter]" = OrderedDict()
    for r in inj:
        clubs.setdefault(r["club"], Counter())["rows"] += 1
        if r["game_status"]:
            clubs[r["club"]][r["game_status"]] += 1
        clubs[r["club"]]["DNP_" + r["practice_status"].split()[0]] = \
            clubs[r["club"]].get("DNP_" + r["practice_status"].split()[0], 0)
    prows = []
    for club, c in clubs.items():
        prows.append(["2026-11-18", "10", club, c.get("rows", 0), c.get("Out", 0),
                      c.get("Doubtful", 0), c.get("Questionable", 0),
                      c.get("rows", 0) - c.get("Out", 0) - c.get("Doubtful", 0)
                      - c.get("Questionable", 0), INJ_URL])
    for r in _read("week10_absent_clubs.csv"):
        prows.append(["2026-11-18", "10", r["club"], "", "", "", "", "",
                      INJ_URL])
    _write("club_injury_counts.csv",
           ["read_date", "nfl_week", "club", "n_rows", "n_out", "n_doubtful",
            "n_questionable", "n_blank_game_status", "source_url"], prows)

    # ---- 4. position groups ------------------------------------------------
    grows = []
    for label, codes in POSITION_GROUPS:
        sub = [r for r in inj if r["position"] in codes]
        g = Counter(r["game_status"] or "(blank)" for r in sub)
        grows.append(["2026-11-18", label, ", ".join(codes), len(sub),
                      g.get("Out", 0), g.get("Doubtful", 0), g.get("Questionable", 0),
                      g.get("(blank)", 0), _pct(g.get("Out", 0), len(sub)), INJ_URL])
    _write("position_group_counts.csv",
           ["read_date", "position_group", "positions_included", "n_rows", "n_out",
            "n_doubtful", "n_questionable", "n_blank_game_status", "pct_out",
            "source_url"], grows)

    # ---- 5. what the table CANNOT say --------------------------------------
    _write("designation_calibration_status.csv",
           ["question", "numerator_available", "denominator_available",
            "n_numerator", "n_denominator", "status", "what_is_missing", "source_url"],
           [["Of players listed Questionable, what share actually played?",
             "yes", "no", gs.get("Questionable", 0), 0, "not computable",
             "the official inactive list for the same games (gate G-INACT)", INJ_URL],
            ["Of players listed Doubtful, what share actually played?",
             "yes", "no", gs.get("Doubtful", 0), 0, "not computable",
             "the official inactive list for the same games (gate G-INACT)", INJ_URL],
            ["Of players who did not practise, what share were ruled Out?",
             "yes", "yes", ps.get("Did Not Participate In Practice", 0), n,
             "computable - see designation_xtab.csv", "", INJ_URL]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
