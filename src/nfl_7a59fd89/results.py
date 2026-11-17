"""Week-10 finals settlement for pack nfl_7a59fd89.

Extends the 8362b702 verified-results corpus (weeks 1-9, 136 rows) with the
week-10 finals read from the official scores page
(https://www.nfl.com/scores/, read 2026-11-17). Only FINAL rows carry scores;
games whose page state conflicts between reads stay blank + flagged
(never inferred). The extension preserves the corpus schema and keeps
margin_home / total as derived columns with the derivation shown in code.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

CORPUS_DEFAULT = "data/nfl_8362b702/corpus_136.csv"
FINALS_DEFAULT = "data/nfl_7a59fd89/week10_finals.csv"
OUT_DEFAULT = "data/nfl_7a59fd89/corpus_150.csv"


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def finals_to_corpus_rows(finals: list[dict], start_seq: int = 1) -> list[dict]:
    rows = []
    seq = start_seq
    for r in finals:
        week = "10"
        aw, hm = r.get("away_score", ""), r.get("home_score", "")
        if aw and hm:
            margin = str(int(hm) - int(aw))
            total = str(int(hm) + int(aw))
        else:
            margin = ""  # derivation impossible without both scores — stays blank
            total = ""
        rows.append({
            "game_id": f"2026-W10-{seq:02d}",
            "week": week,
            "date_on_card": r.get("kickoff_et", ""),
            "away": r["away_team"],
            "home": r["home_team"],
            "away_score": aw,
            "home_score": hm,
            "margin_home": margin,
            "total": total,
            "event_mark_on_card": r.get("notes", ""),
            "game_page_url": f"https://www.nfl.com/games/{r['game_id']}",
            "week_page_url": r.get("source_url", ""),
        })
        seq += 1
    return rows


def extend(corpus: list[dict], finals: list[dict]) -> list[dict]:
    return list(corpus) + finals_to_corpus_rows(finals)


def main(argv: list[str]) -> int:
    corpus_p = argv[1] if len(argv) > 1 else CORPUS_DEFAULT
    finals_p = argv[2] if len(argv) > 2 else FINALS_DEFAULT
    out_p = argv[3] if len(argv) > 3 else OUT_DEFAULT
    corpus = load(corpus_p)
    finals = load(finals_p)
    rows = extend(corpus, finals)
    Path(out_p).parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    blank = [r for r in rows if r["week"] == "10" and not r["away_score"]]
    print(f"corpus: {len(corpus)} prior + {len(finals)} week-10 rows = {len(rows)} -> {out_p}")
    print(f"week-10 rows with blank scores (flagged, not inferred): {len(blank)}"
          + (f" {[r['away']+'@'+r['home'] for r in blank]}" if blank else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
