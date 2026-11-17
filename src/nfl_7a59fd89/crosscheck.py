"""Availability cross-checks for pack nfl_7a59fd89 (W6).

Produces data/nfl_7a59fd89/availability_conflicts.csv with five conflict kinds:

  K1 RESERVE_CODE_VS_HUB_STATUS  - mechanically derived: player carries a
      reserve-family code (RES/PUP/RSR/RSN) on the club roster page yet appears
      on the league injury hub with a game status (or as listed with none).
  K2 ACT_VS_HUB_OUT              - mechanically checked against recorded ACT
      evidence: player is ACT on the club roster page but the hub prints Out.
      The register holds non-ACT rows only, so the ACT side is a recorded
      page-read constant re-verified by full page re-reads on 2026-11-17
      (DET, SEA, NE).
  K3 NEWS_VS_TABLE               - hub news text contradicts hub table/roster
      for the same player (recorded evidence).
  K4 HUB_ABSENT                  - club absent from the hub page at read:
      "not listed" never means "available" (flagged, never inferred).
  K5 SAME_SLUG_MULTI_PAGE        - identical player slug carries different
      status codes on different clubs' roster pages (recorded evidence from
      the 32-club sweep; ledger also in roster_sweep.csv notes).

Conflicts are flagged, never resolved by inference. Disposition is always
"flagged".
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

from .sweep import load_register, REGISTER_DEFAULT
from .injury import load, CURRENT_DEFAULT as HUB_DEFAULT

OUT_DEFAULT = "data/nfl_7a59fd89/availability_conflicts.csv"
HUB_URL = "https://www.nfl.com/injuries/"

# ACT-side evidence for K2: (club, player, position) verified ACT on the club
# roster page; re-verified by full page re-read 2026-11-17.
ACT_EVIDENCE = {
    ("DET", "Cade Mays"): "https://www.nfl.com/teams/detroit-lions/roster/",
    ("DET", "D.J. Reed"): "https://www.nfl.com/teams/detroit-lions/roster/",
    ("SEA", "Quenton Nelson"): "https://www.nfl.com/teams/seattle-seahawks/roster/",
}

# K3 recorded evidence (all sides read 2026-11-17: NE roster page + hub page).
NEWS_VS_TABLE = [
    {
        "club": "NE", "player": "Drake Maye", "position": "QB",
        "roster_page_status": "ACT",
        "hub_table": "practice Full Participation in Practice; game_status blank",
        "hub_news": "hub news item: Drake Maye possibly out rest of season",
        "source_urls": "https://www.nfl.com/teams/new-england-patriots/roster/ ; " + HUB_URL,
    },
]

# K4: clubs absent from the hub page at the 2026-11-17T00:45:48Z read.
HUB_ABSENT_CLUBS = ["CHI", "DEN", "PHI", "TB"]

# K5 ledger: identical slug, different status codes across club roster pages.
# Every listed side was read 2026-11-17 (32-club sweep; AZ/BAL/DET/SEA/NE sides
# re-verified by full page re-read). "other_side_unpersisted" marks a side whose
# verbatim row was not persisted and is flagged for re-verification.
SLUG_LEDGER = [
    ("Natrone Brooks", "TRC/MIN; TRC/DET; DEV/IND", ""),
    ("Kirk Cousins", "ACT/MIN; TRC/LV", ""),
    ("Odell Beckham Jr.", "TRD/NYG; DEV/MIN", ""),
    ("Jihad Ward", "TRD/NYG; DEV/MIN", ""),
    ("Darian Kinnard", "TRC/NYG; CUT/LV", ""),
    ("J.J. McCarthy", "ACT/NYG; TRD/MIN", ""),
    ("Davon Godchaux", "TRC/NO; ACT/JAX", ""),
    ("Scott Daly", "TRD/NO; TRT/GB", ""),
    ("David Long", "TRD/NO; DEV/LAR", ""),
    ("Audric Estime", "ACT/NO; TRD/MIN", ""),
    ("Blake Freeland", "ACT/NYJ; TRD/CIN", ""),
    ("Blake Grupe", "RES/LAR; TRC/NYJ", ""),
    ("John Saunders Jr.", "DEV/JAX; TRC/NYJ", ""),
    ("Xavier Newman-Johnson", "DEV/NE; TRT/NYJ", ""),
    ("Jordan Davis", "TRC/PHI; ACT/JAX", ""),
    ("Maximus Pulley", "TRD/PHI; ACT/LAR", ""),
    ("Evan Neal", "TRC/LV; DEV/PHI", ""),
    ("Christian Braswell", "TRC/JAX; DEV/PHI", ""),
    ("Marquez Valdes-Scantling", "DEV/PIT; TRD/LAC", ""),
    ("Keenan Allen", "ACT/SF; TRC/IND", ""),
    ("DeForest Buckner", "ACT/SF; TRC/IND", ""),
    ("Kevin Givens", "TRC/SF; ACT/IND", ""),
    ("Naquan Jones", "ACT/HOU; TRC/NO; TRC/SF", ""),
    ("Xavier Smith", "TRT/SF; ACT/LAR", ""),
    ("Rob Beal Jr.", "TRC/MIA; DEV/SF", ""),
    ("Quenton Nelson", "ACT/SEA; TRC/IND", ""),
    ("Jamie Sheriff", "TRT/LAR; DEV/SEA", ""),
    ("Cordell Volson", "TRD/GB; DEV/SEA", ""),
    ("Josiah Deguara", "TRD/PHI; CUT/SEA", ""),
    ("Josh Ross", "DEV/MIN; TRD/SEA", ""),
    ("Christian Haynes", "ACT/MIA; TRC/SEA", ""),
    ("Evan Beerntsen", "DEV/PHI; TRD/SEA", ""),
    ("Sean Murphy-Bunting", "TRC/TB; ACT/PIT", ""),
    ("Trevor Keegan", "ACT/TB; TRD/MIN", ""),
    ("Jonah Laulu", "TRD/LV; ACT/TEN", ""),
    ("Jimmy Ciarlo", "TRC/SEA; DEV/TEN", ""),
    ("Jakob Robinson", "TRC/SF; DEV/TEN", ""),
    ("Shemar Bartholomew", "DEV/IND; TRT/TEN", ""),
    ("Kaytron Allen", "ACT/MIA; TRC/WAS", ""),
    ("Darius Rush", "DEV/PIT; TRC/WAS", ""),
    ("Terell Smith", "CUT/PIT; TRC/WAS", ""),
    ("DJ Johnson", "DEV/GB; TRD/WAS", ""),
    ("Jeffrey M'ba", "DEV/DET; TRD/WAS", ""),
    ("Tyler Goodson", "TRD/ATL; RES/DAL", ""),
    ("Jacoby Brissett", "TRC/AZ; ACT/BAL", ""),
    ("Marvin Harrison Jr.", "TRC/AZ; ACT/HOU", ""),
    ("Matt Pryor", "TRC/AZ; ACT/NE", ""),
    ("D'Shawn Jamison", "TRC/AZ; CUT/NE", ""),
    ("Kedon Slovis", "ACT/BAL; TRC/GB", ""),
    ("Harrison Mevis", "DEV/BAL; TRC/LAR", "other-side status read this session, not persisted verbatim; flagged for re-verification"),
    ("Rayshawn Jenkins", "DEV/BAL; TRT/PIT", "other-side status read this session, not persisted verbatim; flagged for re-verification"),
]

# K6 display-name vs slug mismatches observed on roster pages (same read).
DISPLAY_SLUG_MISMATCH = [
    ("GB", "Zach Bako-Bewele", "zach-tom"),
    ("PHI", "Riq Woolen", "tariq-woolen"),
    ("SEA", "Malick Meiga", "hassane-meiga"),
    ("WAS", "Quan Martin", "jartavius-martin"),
    ("LAR", "Kam Curl", "kamren-curl"),
]

RESERVE_CODES = ("RES", "PUP", "RSR", "RSN")


def club_roster_url(club: str) -> str:
    slugs = {"ARI": "arizona-cardinals"}
    mapping = {
        "AZ": "arizona-cardinals", "ATL": "atlanta-falcons", "BAL": "baltimore-ravens",
        "BUF": "buffalo-bills", "CAR": "carolina-panthers", "CHI": "chicago-bears",
        "CIN": "cincinnati-bengals", "CLE": "cleveland-browns", "DAL": "dallas-cowboys",
        "DEN": "denver-broncos", "DET": "detroit-lions", "GB": "green-bay-packers",
        "HOU": "houston-texans", "IND": "indianapolis-colts", "JAX": "jacksonville-jaguars",
        "KC": "kansas-city-chiefs", "LAC": "los-angeles-chargers", "LAR": "los-angeles-rams",
        "LV": "las-vegas-raiders", "MIA": "miami-dolphins", "MIN": "minnesota-vikings",
        "NE": "new-england-patriots", "NO": "new-orleans-saints", "NYG": "new-york-giants",
        "NYJ": "new-york-jets", "PHI": "philadelphia-eagles", "PIT": "pittsburgh-steelers",
        "SF": "san-francisco-49ers", "SEA": "seattle-seahawks", "TB": "tampa-bay-buccaneers",
        "TEN": "tennessee-titans", "WAS": "washington-commanders",
    }
    return f"https://www.nfl.com/teams/{mapping[club]}/roster/"


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def conflicts(register: list[dict], hub: list[dict]) -> list[dict]:
    out: list[dict] = []
    regmap = {(r["club"], _norm(r["player"])): r for r in register}
    cid = 0

    def add(kind, club, player, position, roster_status, roster_src, detail, sources):
        nonlocal cid
        cid += 1
        out.append({
            "conflict_id": f"X-{cid:02d}",
            "conflict_kind": kind,
            "club": club,
            "player": player,
            "position": position,
            "roster_page_status": roster_status,
            "roster_status_source": roster_src,
            "hub_status_or_other_side": detail,
            "source_urls": sources,
            "disposition": "flagged; never resolved by inference",
        })

    # K1 mechanical
    for h in hub:
        r = regmap.get((h["club"], _norm(h["player"])))
        if not r:
            continue
        if r["status_code"] in RESERVE_CODES:
            gs = (h["game_status"] or "").strip()
            detail = f"hub game_status={gs or '(blank — listed without status)'}; practice={(h['practice_status'] or '').strip()}"
            add("RESERVE_CODE_VS_HUB_STATUS", h["club"], r["player"], r["position"],
                r["status_code"], club_roster_url(r["club"]), detail,
                club_roster_url(r["club"]) + " ; " + HUB_URL)

    # K2 recorded ACT evidence vs hub Out
    for h in hub:
        key = (h["club"], h["player"])
        if key in ACT_EVIDENCE and (h["game_status"] or "").strip().lower() == "out":
            add("ACT_VS_HUB_OUT", h["club"], h["player"], h["position"], "ACT",
                ACT_EVIDENCE[key], "hub game_status=Out",
                ACT_EVIDENCE[key] + " ; " + HUB_URL)

    # K3 news vs table
    for n in NEWS_VS_TABLE:
        add("NEWS_VS_TABLE", n["club"], n["player"], n["position"], n["roster_page_status"],
            club_roster_url(n["club"]),
            f"hub table: {n['hub_table']} | hub news: {n['hub_news']}", n["source_urls"])

    # K4 hub-absent clubs
    for club in HUB_ABSENT_CLUBS:
        n = sum(1 for r in register if r["club"] == club)
        add("HUB_ABSENT", club, "", "", "", club_roster_url(club),
            f"club not listed on hub page at read; roster page read with {n} non-ACT rows; no availability status published for its players; 'not listed' != available",
            club_roster_url(club) + " ; " + HUB_URL)

    # K5 slug ledger
    for player, pairs, note in SLUG_LEDGER:
        detail = "same player slug carries different status codes on club roster pages: " + pairs
        detail += " | ledger also recorded in roster_sweep.csv notes (32-club sweep 2026-11-17)"
        if note:
            detail += " | " + note
        add("SAME_SLUG_MULTI_PAGE", "", player, "", "", "https://www.nfl.com/teams/", detail,
            "https://www.nfl.com/teams/")

    # K6 display vs slug mismatch
    for club, display, slug in DISPLAY_SLUG_MISMATCH:
        add("DISPLAY_SLUG_MISMATCH", club, display, "", "", club_roster_url(club),
            f"page row displays '{display}' but player slug is '{slug}' (recorded verbatim, not 'fixed')",
            club_roster_url(club))

    return out


def main(argv: list[str]) -> int:
    reg_p = argv[1] if len(argv) > 1 else REGISTER_DEFAULT
    hub_p = argv[2] if len(argv) > 2 else HUB_DEFAULT
    out_p = argv[3] if len(argv) > 3 else OUT_DEFAULT
    rows = conflicts(load_register(reg_p), load(hub_p))
    Path(out_p).parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["conflict_kind"]] = kinds.get(r["conflict_kind"], 0) + 1
    print(f"conflict rows: {len(rows)} -> {out_p}")
    for k in sorted(kinds):
        print(f"  {k}: {kinds[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
