"""Compare the live Thursday IND@HOU read with the stored Week 11 transcription.

Recomputes match/mismatch per row. Blank cells are compared as blank.
Run: python3 data/nfl_c54d6bda/reverify_thu_ind_hou.py
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIVE = ROOT / "data/nfl_c54d6bda/raw/thu_ind_hou_live_2026-11-19.txt"
STORED = ROOT / "data/nfl_51698d74/raw/injuries_reg11_2026-11-19.md"
OUT = ROOT / "data/nfl_c54d6bda/reverification_thu_ind_hou.csv"


def read_live():
    rows = []
    for line in LIVE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("## "):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts += [""] * (5 - len(parts))
        rows.append(tuple(parts[:5]))
    return rows


def read_stored():
    rows, on = [], False
    for line in STORED.read_text(encoding="utf-8").splitlines():
        if line.startswith("## THURSDAY"):
            on = True
            continue
        if line.startswith("## ") and on:
            break
        if on and "|" in line and not line.startswith("#"):
            parts = [p.strip() for p in line.split("|")]
            if parts[0] in ("", "Player"):
                continue
            parts = [("" if p == "(blank)" else p) for p in parts]
            parts += [""] * (5 - len(parts))
            rows.append(tuple(parts[:5]))
    return rows


def main():
    live, stored = read_live(), read_stored()
    stored_set = set(stored)
    out = []
    for r in live:
        status = "MATCH" if r in stored_set else "MISMATCH"
        out.append({"player": r[0], "position": r[1], "injury": r[2],
                    "practice": r[3], "game_status": r[4], "result": status})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    m = sum(o["result"] == "MATCH" for o in out)
    print(f"live rows={len(live)} stored rows(Thu)={len(stored)} match={m} mismatch={len(out)-m}")


if __name__ == "__main__":
    main()
