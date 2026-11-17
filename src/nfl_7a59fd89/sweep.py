"""32-club roster sweep integrity for pack nfl_7a59fd89.

`roster_reserve.csv` is the per-row register (verbatim truth: every non-ACT row
read from an official club roster page). `roster_sweep.csv` holds per-club blocks.
This module re-derives every sweep aggregate from the register and fails loudly
on any inconsistency — sweep tallies are never trusted over row-level truth.
"""
from __future__ import annotations
import csv
import sys
from collections import Counter
from pathlib import Path

REGISTER_DEFAULT = "data/nfl_7a59fd89/roster_reserve.csv"
SWEEP_DEFAULT = "data/nfl_7a59fd89/roster_sweep.csv"
GROUP_COLS = ("res_rows", "pup_rows", "cut_rows", "dev_rows")
OTHER_COL = "trd_rows"  # lumped non-RES/PUP/CUT/DEV codes (TRC/TRD/TRT/RSR/RSN/RLS/EXE)
ALL_CLUBS = ("AZ ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LAC "
             "LAR LV MIA MIN NE NO NYG NYJ PHI PIT SF SEA TB TEN WAS").split()


def load_register(path: str = REGISTER_DEFAULT) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_sweep(path: str = SWEEP_DEFAULT) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def counts_by_club(register: list[dict]) -> dict[str, Counter]:
    out: dict[str, Counter] = {}
    for r in register:
        out.setdefault(r["club"], Counter())[r["status_code"]] += 1
    return out


def verify(register: list[dict], sweep: list[dict], act_by_club: dict[str, int] | None = None) -> list[str]:
    errs: list[str] = []
    cnt = counts_by_club(register)
    if sorted(cnt) != sorted(ALL_CLUBS):
        errs.append(f"register clubs {sorted(cnt)} != all 32")
    if len({b["club"] for b in sweep}) != len(sweep):
        errs.append("duplicate sweep blocks")
    if sorted(b["club"] for b in sweep) != sorted(ALL_CLUBS):
        errs.append("sweep blocks != all 32 clubs")
    act = act_by_club or {}
    for b in sweep:
        c = b["club"]
        nonact = sum(cnt.get(c, Counter()).values())
        grp = sum(int(b[k]) for k in GROUP_COLS)
        other = int(b[OTHER_COL])
        if grp + other != nonact:
            errs.append(f"{c}: grouped({grp})+other({other}) != register non-ACT({nonact})")
        for k, code in (("res_rows", "RES"), ("pup_rows", "PUP"), ("cut_rows", "CUT"), ("dev_rows", "DEV")):
            if int(b[k]) != cnt.get(c, Counter()).get(code, 0):
                errs.append(f"{c}: {k}({b[k]}) != register {code}({cnt.get(c, Counter()).get(code, 0)})")
        if act and c in act and int(b["act_rows"]) != act[c]:
            errs.append(f"{c}: act_rows({b['act_rows']}) != confirmed({act[c]})")
        if int(b["total_rows_read"]) != int(b["act_rows"]) + nonact:
            errs.append(f"{c}: total({b['total_rows_read']}) != act+nonact({int(b['act_rows']) + nonact})")
    return errs


def main(argv: list[str]) -> int:
    reg = load_register(argv[1] if len(argv) > 1 else REGISTER_DEFAULT)
    swp = load_sweep(argv[2] if len(argv) > 2 else SWEEP_DEFAULT)
    errs = verify(reg, swp)
    total_codes = Counter(r["status_code"] for r in reg)
    print(f"register rows: {len(reg)} | sweep blocks: {len(swp)}")
    print("league status-code totals:", dict(sorted(total_codes.items())))
    if errs:
        print("INCONSISTENT:")
        for e in errs:
            print("  -", e)
        return 1
    print("sweep blocks fully consistent with register.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
