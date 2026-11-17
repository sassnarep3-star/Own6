"""Cross-read injury-hub delta for pack nfl_7a59fd89.

Joins two dated reads of the official injury hub (https://www.nfl.com/injuries/)
row-for-row and emits only deltas — never levels (R-12/R-21/R-53 discipline).

Join protocol (record-order independent):
  1. exact key (club, player)
  2. within a club, unmatched rows are paired 1:1 on position when both sides
     have exactly one leftover for that position (name variants, e.g.
     "Kam Curl" vs "Kamren Curl") — the pair is emitted as a NAME_VARIANT row
     with both names shown and never silently merged.

Field mapping: prior read column `injury` corresponds to current `injuries`
(same page element, renamed between captures).
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

PRIOR_DEFAULT = "data/nfl_48217a55/injury_report_2026_11_15.csv"
CURRENT_DEFAULT = "data/nfl_7a59fd89/injury_hub_2026_11_17.csv"
OUT_DEFAULT = "data/nfl_7a59fd89/injury_delta.csv"

COMPARE_FIELDS = (("practice_status", "practice_status"), ("game_status", "game_status"),
                  ("injury", "injuries"))


def _norm(name: str) -> str:
    return " ".join((name or "").strip().lower().split())


def delta_rows(prior: list[dict], current: list[dict]) -> list[dict]:
    prior_by_key = {(_norm(r["club"]), _norm(r["player"])): r for r in prior}
    cur_by_key = {(_norm(r["club"]), _norm(r["player"])): r for r in current}
    out: list[dict] = []

    def emit(p, c, kind, field=None):
        out.append({
            "club": (p or c)["club"],
            "player_prior": (p or {}).get("player", ""),
            "player_current": (c or {}).get("player", ""),
            "position": (p or c).get("position", ""),
            "field": field or "",
            "value_prior": (p or {}).get(field.split("->")[0], "") if field else "",
            "value_current": (c or {}).get(field.split("->")[1], "") if field else "",
            "delta_kind": kind,
        })

    matched_prior, matched_cur = set(), set()
    for key, c in cur_by_key.items():
        p = prior_by_key.get(key)
        if p is not None:
            matched_prior.add(key); matched_cur.add(key)
            for pf, cf in COMPARE_FIELDS:
                pv, cv = (p.get(pf) or "").strip(), (c.get(cf) or "").strip()
                if pv != cv:
                    emit(p, c, "FIELD_DIFF", f"{pf}->{cf}")

    # name-variant pairing: per club+position, exactly one leftover on each side
    left_p: dict[tuple, list] = {}
    left_c: dict[tuple, list] = {}
    for r in prior:
        k = (_norm(r["club"]), _norm(r["player"]))
        if k not in matched_prior:
            left_p.setdefault((_norm(r["club"]), _norm(r["position"])), []).append(r)
    for r in current:
        k = (_norm(r["club"]), _norm(r["player"]))
        if k not in matched_cur:
            left_c.setdefault((_norm(r["club"]), _norm(r["position"])), []).append(r)
    for key in sorted(set(left_p) & set(left_c)):
        ps, cs = left_p[key], left_c[key]
        if len(ps) == 1 and len(cs) == 1:
            p, c = ps[0], cs[0]
            emit(p, c, "NAME_VARIANT")
            for pf, cf in COMPARE_FIELDS:
                pv, cv = (p.get(pf) or "").strip(), (c.get(cf) or "").strip()
                if pv != cv:
                    emit(p, c, "FIELD_DIFF", f"{pf}->{cf}")
            matched_prior.add((_norm(p["club"]), _norm(p["player"])))
            matched_cur.add((_norm(c["club"]), _norm(c["player"])))
        else:
            for r in ps:
                emit(r, None, "ONLY_IN_PRIOR_UNPAIRED")
            for r in cs:
                emit(r, None, "ONLY_IN_CURRENT_UNPAIRED")

    # rows left over after both passes are genuine appearance changes
    for key, p in prior_by_key.items():
        if key not in matched_prior:
            emit(p, None, "ONLY_IN_PRIOR")
    for key, c in cur_by_key.items():
        if key not in matched_cur:
            emit(c, None, "ONLY_IN_CURRENT")
    return out


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(rows: list[dict], path: str) -> None:
    fields = ["club", "player_prior", "player_current", "position", "field",
              "value_prior", "value_current", "delta_kind"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str]) -> int:
    prior_p = argv[1] if len(argv) > 1 else PRIOR_DEFAULT
    cur_p = argv[2] if len(argv) > 2 else CURRENT_DEFAULT
    out_p = argv[3] if len(argv) > 3 else OUT_DEFAULT
    rows = delta_rows(load(prior_p), load(cur_p))
    write(rows, out_p)
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["delta_kind"]] = kinds.get(r["delta_kind"], 0) + 1
    print(f"delta rows: {len(rows)} -> {out_p}")
    for k in sorted(kinds):
        print(f"  {k}: {kinds[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
