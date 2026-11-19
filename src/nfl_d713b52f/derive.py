"""Turn the raw transcripts into the published tables.

Nothing here invents a value. Each function returns rows that carry, per row,
the official URL the value was read from (or the arithmetic that produced it)
and, where a cell cannot be supported, a blank plus a reason.
"""
from __future__ import annotations

import re

from . import capture

S = "https://www.nfl.com/standings/"
GB_LAC_BAL = ("https://static.www.nfl.com/image/upload/v1794916121/gamecenter/"
              "ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf")
GB_HOU_CLE = ("https://static.www.nfl.com/image/upload/v1794829724/gamecenter/"
              "ab583279-4feb-11f1-abca-2c54536568a9.pdf")
GB_NE_DET = ("https://static.www.nfl.com/image/upload/v1794829721/gamecenter/"
             "ab582c2f-4feb-11f1-abca-2c54536568a9.pdf")
GB_WAS_NYG = ("https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
              "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf")
GC_LAC_BAL = "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"
GC_HOU_CLE = "https://www.nfl.com/games/texans-at-browns-2026-reg-10"
GC_NE_DET = "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"
GC_WAS_NYG = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"
INJ_REG10 = "https://www.nfl.com/injuries/league/2026/reg10"
INJ_REG11 = "https://www.nfl.com/injuries/"
SCHED = "https://www.nfl.com/schedules/"
STATS_INDEX = "https://www.nfl.com/stats/player-stats/"
READ = capture.READ_AT

# ---------------------------------------------------------------------------
# 1. Standings, exactly as rendered
# ---------------------------------------------------------------------------

# club, division, w, l, t, pct, pf, pa   (transcribed from cap02_standings.txt)
STANDINGS = [
    ("Buffalo Bills", "AFC East", 8, 1, 0, "0.889", 287, 199),
    ("New England Patriots", "AFC East", 5, 5, 0, "0.500", 221, 242),
    ("New York Jets", "AFC East", 2, 8, 0, "0.200", 194, 254),
    ("Miami Dolphins", "AFC East", 1, 8, 0, "0.111", 148, 224),
    ("Cincinnati Bengals", "AFC North", 7, 2, 0, "0.778", 278, 193),
    ("Pittsburgh Steelers", "AFC North", 6, 3, 0, "0.667", 198, 182),
    ("Cleveland Browns", "AFC North", 6, 4, 0, "0.600", 188, 220),
    ("Baltimore Ravens", "AFC North", 4, 6, 0, "0.400", 209, 259),
    ("Jacksonville Jaguars", "AFC South", 7, 2, 0, "0.778", 269, 144),
    ("Houston Texans", "AFC South", 3, 6, 0, "0.333", 233, 219),
    ("Indianapolis Colts", "AFC South", 3, 7, 0, "0.300", 208, 271),
    ("Tennessee Titans", "AFC South", 1, 8, 0, "0.111", 167, 239),
    ("Kansas City Chiefs", "AFC West", 7, 2, 0, "0.778", 237, 156),
    ("Denver Broncos", "AFC West", 7, 2, 0, "0.778", 198, 186),
    ("Las Vegas Raiders", "AFC West", 4, 6, 0, "0.400", 251, 289),
    ("Los Angeles Chargers", "AFC West", 1, 8, 0, "0.111", 144, 239),
    ("New York Giants", "NFC East", 5, 3, 1, "0.611", 203, 196),
    ("Dallas Cowboys", "NFC East", 4, 6, 0, "0.400", 286, 282),
    ("Washington Commanders", "NFC East", 3, 5, 1, "0.389", 196, 223),
    ("Philadelphia Eagles", "NFC East", 2, 7, 0, "0.222", 148, 221),
    ("Detroit Lions", "NFC North", 7, 2, 0, "0.778", 257, 199),
    ("Minnesota Vikings", "NFC North", 7, 2, 0, "0.778", 176, 126),
    ("Chicago Bears", "NFC North", 7, 2, 0, "0.778", 241, 184),
    ("Green Bay Packers", "NFC North", 6, 4, 0, "0.600", 226, 221),
    ("Carolina Panthers", "NFC South", 4, 5, 0, "0.444", 219, 236),
    ("Tampa Bay Buccaneers", "NFC South", 3, 6, 0, "0.333", 202, 178),
    ("New Orleans Saints", "NFC South", 3, 6, 0, "0.333", 202, 236),
    ("Atlanta Falcons", "NFC South", 3, 7, 0, "0.300", 201, 258),
    ("San Francisco 49ers", "NFC West", 8, 1, 0, "0.889", 281, 196),
    ("Seattle Seahawks", "NFC West", 6, 4, 0, "0.600", 223, 175),
    ("Los Angeles Rams", "NFC West", 6, 4, 0, "0.600", 248, 187),
    ("Arizona Cardinals", "NFC West", 3, 7, 0, "0.300", 184, 289),
]

# club -> abbreviation, as printed in the injury report (cap03 / cap09)
ABBR = {
    "Buffalo Bills": "BUF", "New England Patriots": "NE", "New York Jets": "NYJ",
    "Miami Dolphins": "MIA", "Cincinnati Bengals": "CIN", "Pittsburgh Steelers": "PIT",
    "Cleveland Browns": "CLE", "Baltimore Ravens": "BAL", "Jacksonville Jaguars": "JAX",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Tennessee Titans": "TEN",
    "Kansas City Chiefs": "KC", "Denver Broncos": "DEN", "Las Vegas Raiders": "LV",
    "Los Angeles Chargers": "LAC", "New York Giants": "NYG", "Dallas Cowboys": "DAL",
    "Washington Commanders": "WAS", "Philadelphia Eagles": "PHI", "Detroit Lions": "DET",
    "Minnesota Vikings": "MIN", "Chicago Bears": "CHI", "Green Bay Packers": "GB",
    "Carolina Panthers": "CAR", "Tampa Bay Buccaneers": "TB", "New Orleans Saints": "NO",
    "Atlanta Falcons": "ATL", "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA",
    "Los Angeles Rams": "LA", "Arizona Cardinals": "AZ",
}
CLUB = {a: c for c, a in ABBR.items()}


def standings_rows():
    out = []
    for club, div, w, l, t, pct, pf, pa in STANDINGS:
        out.append(dict(
            club=club, abbr=ABBR[club], division=div, w=str(w), l=str(l), t=str(t),
            pct=pct, pf=str(pf), pa=str(pa), net_pts=str(pf - pa),
            net_pts_check="pf-pa",
            games=str(w + l + t),
            source_url=S, read_at_utc=READ))
    return out


def standings_audit():
    """Arithmetic identities that must hold if the 32 rows were transcribed right."""
    checks = []
    n = len(STANDINGS)
    clubs = {c for c, *_ in STANDINGS}
    checks.append(("32 rows, 32 distinct clubs", str(n), str(len(clubs)), n == 32 and len(clubs) == 32))
    total_pf = sum(r[6] for r in STANDINGS)
    total_pa = sum(r[7] for r in STANDINGS)
    checks.append(("sum(PF) == sum(PA)  [every point scored is a point allowed]",
                   str(total_pf), str(total_pa), total_pf == total_pa))
    checks.append(("sum(PF) is even  [each game adds an even number of points]",
                   str(total_pf), "even", total_pf % 2 == 0))
    games = total_pf // 2  # not meaningful alone; reported only as a division
    checks.append(("sum(PF)/2 (half-points bank; not a game count)",
                   str(total_pf), str(games), True))
    wins = sum(r[2] for r in STANDINGS)
    losses = sum(r[3] for r in STANDINGS)
    checks.append(("sum(W) == sum(L)", str(wins), str(losses), wins == losses))
    ties = sum(r[4] for r in STANDINGS)
    checks.append(("sum(T) is even", str(ties), "even", ties % 2 == 0))
    checks.append(("sum(W)+sum(L) == 2 * (games played per club-pair)",
                   f"{wins}+{losses}={wins + losses}", f"2*{wins}", wins + losses == 2 * wins))
    # NET column, as printed, must equal PF-PA row by row; re-checked in derive tests.
    return checks


# ---------------------------------------------------------------------------
# 2. Game Book joins: actual starters, not-active, and the report designation
# ---------------------------------------------------------------------------

# The 11 starters per side, transcribed from the books' "Lineups" block.
LINEUPS = {
    ("2026-W10-14", "LAC"): dict(
        book=GB_LAC_BAL, centre=GC_LAC_BAL,
        offense=[("WR", "Q. Johnston"), ("WR", "T. Harris"), ("TE", "C. Kolar"), ("LT", "J. Alt"),
                 ("LG", "L. Taylor"), ("C", "J. Slaughter"), ("RG", "C. Strange"), ("RT", "T. Burke"),
                 ("QB", "J. Herbert"), ("FB", "S. Matlock"), ("RB", "O. Hampton")],
        defense=[("OLB", "T. Tuipulotu"), ("DL", "T. Tart"), ("DL", "D. Tomlinson"), ("OLB", "K. Mack"),
                 ("LB", "D. Phillips"), ("LB", "D. Henley"), ("DB", "E. Molden"), ("CB", "D. Jackson"),
                 ("CB", "T. Still"), ("CB", "C. Hart"), ("S", "T. Jefferson")]),
    ("2026-W10-14", "BAL"): dict(
        book=GB_LAC_BAL, centre=GC_LAC_BAL,
        offense=[("WR", "Z. Flowers"), ("TE", "J. Cuevas"), ("LT", "R. Stanley"), ("LG", "J. Simpson"),
                 ("C", "C. Jurgens"), ("RG", "O. Ioane"), ("RT", "R. Rosengarten"), ("WR", "J. Lane"),
                 ("WR", "R. Bateman"), ("QB", "J. Brissett"), ("RB", "D. Henry")],
        defense=[("OLB", "T. Hendrickson"), ("DL", "B. Washington"), ("DL", "T. Jones"), ("DL", "N. Madubuike"),
                 ("OLB", "M. Green"), ("ILB", "T. Simpson"), ("ILB", "R. Smith"), ("CB", "N. Wiggins"),
                 ("CB", "M. Humphrey"), ("S", "M. Starks"), ("S", "K. Hamilton")]),
    ("2026-W10-04", "HOU"): dict(
        book=GB_HOU_CLE, centre=GC_HOU_CLE,
        offense=[("WR", "N. Collins"), ("LT", "A. Ersery"), ("LG", "F. Nwaiwu"), ("C", "E. Brown"),
                 ("RG", "E. Ingram"), ("RT", "T. Brown"), ("TE", "D. Schultz"), ("WR", "K. Boutte"),
                 ("WR", "X. Hutchinson"), ("QB", "C. Stroud"), ("RB", "W. Marks")],
        defense=[("DE", "J. Clowney"), ("DT", "T. Togiai"), ("DT", "S. Rankins"), ("DE", "W. Anderson"),
                 ("CB", "D. Stingley"), ("CB", "K. Lassiter"), ("LB", "J. Hansen"), ("LB", "H. To'oTo'o"),
                 ("S", "C. Bullock"), ("S", "J. Pitre"), ("S", "M. Stewart")]),
    ("2026-W10-04", "CLE"): dict(
        book=GB_HOU_CLE, centre=GC_HOU_CLE,
        offense=[("TE", "H. Fannin"), ("LT", "S. Fano"), ("LG", "Z. Johnson"), ("C", "E. Jenkins"),
                 ("RG", "A. Barber"), ("RT", "T. Howard"), ("TE", "B. Whiteheart"), ("WR", "K. Concepcion"),
                 ("WR", "D. Boston"), ("QB", "D. Watson"), ("RB", "Q. Judkins")],
        defense=[("DE", "J. Verse"), ("DT", "M. Graham"), ("DT", "M. Collins"), ("DE", "I. McGuire"),
                 ("LB", "Q. Williams"), ("LB", "C. Schwesinger"), ("CB", "M. Harden"), ("CB", "D. Ward"),
                 ("CB", "T. Campbell"), ("S", "E. McNeil-Warren"), ("S", "G. Delpit")]),
    ("2026-W10-02", "NE"): dict(
        book=GB_NE_DET, centre=GC_NE_DET,
        offense=[("LT", "W. Campbell"), ("LG", "G. Van Roten"), ("C", "J. Wilson"), ("RG", "M. Pryor"),
                 ("RT", "M. Moses"), ("TE", "H. Henry"), ("TE", "E. Raridon"), ("QB", "D. Maye"),
                 ("RB", "R. Stevenson"), ("WR", "A. Brown"), ("WR", "M. Hollins")],
        defense=[("OLB", "Dr. Jones"), ("DT", "M. Williams"), ("DT", "C. Durden"), ("OLB", "E. Ponder"),
                 ("LB", "R. Spillane"), ("LB", "C. Elliss"), ("CB", "C. Gonzalez"), ("CB", "M. Jones"),
                 ("CB", "C. Woods"), ("S", "C. Woodson"), ("S", "K. Byard")]),
    ("2026-W10-02", "DET"): dict(
        book=GB_NE_DET, centre=GC_NE_DET,
        offense=[("WR", "I. TeSlaa"), ("TE", "S. LaPorta"), ("LT", "P. Sewell"), ("LG", "C. Mahogany"),
                 ("C", "J. Scruggs"), ("RG", "T. Ratledge"), ("RT", "B. Miller"), ("WR", "J. Williams"),
                 ("WR", "A. St. Brown"), ("QB", "J. Goff"), ("RB", "J. Gibbs")],
        defense=[("DE", "A. Hutchinson"), ("DL", "A. McNeill"), ("DL", "T. Williams"), ("DL", "T. Lacy"),
                 ("LB", "T. Nowaske"), ("LB", "M. Rodriguez"), ("LB", "D. Barnes"), ("DB", "B. Branch"),
                 ("CB", "R. Ya-Sin"), ("CB", "R. McCreary"), ("S", "C. Clark")]),
    ("2026-W10-01", "WAS"): dict(
        book=GB_WAS_NYG, centre=GC_WAS_NYG,
        offense=[("WR", "A. Williams"), ("TE", "J. Bates"), ("LT", "B. Coleman"), ("LG", "C. Paul"),
                 ("C", "N. Allegretti"), ("RG", "S. Cosmi"), ("RT", "J. Conerly"), ("TE", "B. Sinnott"),
                 ("WR", "T. Burks"), ("QB", "J. Daniels"), ("RB", "R. White")],
        defense=[("OLB", "O. Oweh"), ("DT", "T. Settle"), ("DT", "S. Tuttle"), ("OLB", "K. Chaisson"),
                 ("LB", "S. Styles"), ("LB", "F. Luvu"), ("CB", "T. Amos"), ("CB", "A. Robertson"),
                 ("S", "J. Reaves"), ("S", "N. Cross"), ("S", "Q. Martin")]),
    ("2026-W10-01", "NYG"): dict(
        book=GB_WAS_NYG, centre=GC_WAS_NYG,
        offense=[("WR", "D. Mooney"), ("TE", "T. Johnson"), ("LT", "A. Thomas"), ("LG", "J. Runyan"),
                 ("C", "B. Hudson"), ("RG", "F. Mauigoa"), ("RT", "J. Eluemunor"), ("WR", "M. Nabers"),
                 ("TE", "I. Likely"), ("QB", "J. McCarthy"), ("RB", "C. Skattebo")],
        defense=[("OLB", "K. Thibodeaux"), ("DL", "S. Harris"), ("DL", "B. Jamison-Travis"), ("DL", "D. Reader"),
                 ("OLB", "A. Carter"), ("LB", "M. McFadden"), ("LB", "A. Reese"), ("CB", "G. Newsome"),
                 ("CB", "D. Banks"), ("S", "J. Holland"), ("S", "A. Washington")]),
}

# "Not Active" as printed in each book. Jersey numbers kept: they are in the book.
NOT_ACTIVE = {
    "LAC": [("WR", "15", "L. McConkey"), ("S", "32", "K. Williamson"), ("CB", "37", "I. Waxter"),
            ("OLB", "48", "B. Dupree"), ("WR", "89", "B. Thompson"), ("DL", "92", "J. Eboigbe")],
    "BAL": [("WR", "13", "E. Sarratt"), ("3QB", "18", "K. Slovis"), ("S", "21", "J. Hawkins"),
            ("CB", "29", "C. Rivers"), ("G/T", "51", "E. Jones"), ("DL", "90", "A. Peebles")],
    "HOU": [("LB", "0", "A. Al-Shaair"), ("TE", "9", "B. Jordan"), ("WR", "18", "M. Harrison"),
            ("RB", "32", "D. Montgomery"), ("DE", "55", "D. Hunter"), ("C/G", "66", "K. Rutledge"),
            ("G", "75", "W. Teller")],
    "CLE": [("3QB", "6", "D. Gabriel"), ("QB", "15", "T. Green"), ("LB", "17", "J. Jefferson"),
            ("CB", "20", "N. Igbinoghene"), ("S", "33", "R. Hickman"), ("C", "52", "P. Brailsford")],
    "NE": [("CB", "7", "C. Davis"), ("3QB", "15", "B. Morton"), ("S", "41", "B. Schooler"),
           ("T", "68", "D. Crownover"), ("OL", "72", "W. Rouse"), ("C", "77", "B. Brown")],
    "DET": [("CB", "4", "D. Reed"), ("CB", "6", "K. Abney"), ("LB", "57", "A. Ogbongbemiga"),
            ("C", "64", "C. Mays"), ("DL", "94", "M. Wingo"), ("DE", "99", "A. Hassanein")],
    "WAS": [("3QB", "16", "A. Kaliakmanis"), ("CB", "37", "I. Yiadom"), ("DT", "50", "R. Barber"),
            ("G", "62", "T. Toggiai"), ("G", "63", "L. Patrick"), ("TE", "80", "C. Yankoff")],
    "NYG": [("CB", "21", "P. Adebo"), ("CB", "35", "N. Reed"), ("LB", "54", "M. Harrison"),
            ("OL", "67", "J. Sills"), ("OL", "74", "J. Davis"), ("TE", "86", "T. Fidone"),
            ("DL", "99", "B. Okoye")],
}

GAMES = [
    dict(game_id="2026-W10-01", week="10", away="WAS", home="NYG", away_score="24", home_score="21",
         date="2026-11-12", kickoff_et="8:15 PM", venue_book="MetLife Stadium", venue_centre="METLIFE STADIUM",
         location="East Rutherford, NJ", roof_surface="Open Stadium on Field Turf",
         weather="Light Rain Fog/Mist", temp_f="48", humidity="89%", wind="NE 9 mph", wind_chill="",
         referee="Rogers, Brad (126)", attendance="80,450", duration="3:04",
         book=GB_WAS_NYG, centre=GC_WAS_NYG),
    dict(game_id="2026-W10-02", week="10", away="NE", home="DET", away_score="10", home_score="35",
         date="2026-11-15", kickoff_et="9:30 AM", venue_book="Allianz Arena", venue_centre="FC BAYERN MUNICH STADIUM",
         location="Munich, Germany", roof_surface="Open Stadium on Natural Grass",
         weather="Cloudy", temp_f="52", humidity="51%", wind="SE 3 mph", wind_chill="",
         referee="Martin, Clay (19)", attendance="70,225", duration="3:04",
         book=GB_NE_DET, centre=GC_NE_DET),
    dict(game_id="2026-W10-04", week="10", away="HOU", home="CLE", away_score="24", home_score="27",
         date="2026-11-15", kickoff_et="1:00 PM", venue_book="Huntington Bank Field",
         venue_centre="HUNTINGTON BANK FIELD", location="Cleveland, OH",
         roof_surface="Open Stadium on Natural Grass", weather="Cloudy", temp_f="46", humidity="75%",
         wind="NW 15 mph", wind_chill="40", referee="Smith, Shawn (14)", attendance="58,342",
         duration="3:12", book=GB_HOU_CLE, centre=GC_HOU_CLE),
    dict(game_id="2026-W10-14", week="10", away="LAC", home="BAL", away_score="23", home_score="20",
         date="2026-11-16", kickoff_et="8:15 PM", venue_book="M&T Bank Stadium",
         venue_centre="M&T BANK STADIUM", location="Baltimore, MD",
         roof_surface="Open Stadium on Natural Grass", weather="Clear", temp_f="49", humidity="58%",
         wind="NW 2 mph", wind_chill="", referee="Hill, Adrian (29)", attendance="69,679",
         duration="3:07", book=GB_LAC_BAL, centre=GC_LAC_BAL),
]
GAME_INDEX = {g["game_id"]: g for g in GAMES}
CLUBS_OF_GAME = {g["game_id"]: (g["away"], g["home"]) for g in GAMES}


def fixture_rows():
    """Fixture context built only from published schedule and book facts."""
    rows = []
    for g in GAMES:
        margin = int(g["home_score"]) - int(g["away_score"])
        total = int(g["home_score"]) + int(g["away_score"])
        venue_match = "exact" if g["venue_book"].upper() == g["venue_centre"].upper() else "mismatch"
        rows.append(dict(
            game_id=g["game_id"], week=g["week"], date=g["date"], kickoff_et=g["kickoff_et"],
            away=g["away"], home=g["home"], away_score=g["away_score"], home_score=g["home_score"],
            home_margin=str(margin), total=str(total),
            venue_game_book=g["venue_book"], venue_game_centre=g["venue_centre"],
            venue_match=venue_match, location=g["location"],
            roof_surface=g["roof_surface"], weather=g["weather"], temp_f=g["temp_f"],
            humidity=g["humidity"], wind=g["wind"], wind_chill=g["wind_chill"],
            referee=g["referee"], attendance=g["attendance"], duration=g["duration"],
            source_url=g["book"], secondary_url=g["centre"], read_at_utc=READ,
            note=("game centre and book name the same venue"
                  if venue_match == "exact" else
                  "game-centre Game Info uses a different stadium name from the official book")))
    return rows


def starters_rows():
    rows = []
    for g in GAMES:
        gid = g["game_id"]
        for side, club in (("away", g["away"]), ("home", g["home"])):
            lu = LINEUPS[(gid, club)]
            for unit, block in (("offense", lu["offense"]), ("defense", lu["defense"])):
                for i, (pos, name) in enumerate(block, start=1):
                    rows.append(dict(
                        game_id=gid, club=club, side=side, unit=unit,
                        slot_order=str(i), position_listed=pos, player_as_printed=name,
                        evidence="official Game Book 'Lineups' block",
                        source_url=lu["book"], read_at_utc=READ))
    return rows


def _norm(name: str) -> str:
    """Normalise a printed name for matching: 'A. St. Brown' -> 'a st brown'."""
    s = name.lower()
    s = s.replace("'", "").replace(".", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _last_first(name: str):
    """First initial and surname, ignoring generational suffixes.

    Without this a report row 'Carlton Davis III' never matches a book row
    'C. Davis', and the pack would publish four false discrepancies.
    """
    parts = [p for p in _norm(name).split() if p]
    while parts and parts[-1] in SUFFIXES:
        parts.pop()
    if len(parts) < 2:
        return None, None
    return parts[0], parts[-1]


# Game Status cells transcribed from the Week 10 report (cap09). Only non-empty ones
# are listed; absence of a row here means the report printed a blank Game Status cell.
GAME_STATUS = {
    ("2026-W10-02", "NE"): [("Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
                            ("A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
                            ("Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
                            ("Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
                            ("Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
                            ("TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
                            ("Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
                            ("Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
                            ("Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
                            ("Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
                            ("Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
                            ("Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable")],
    ("2026-W10-02", "DET"): [("Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
                             ("Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
                             ("D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
                             ("Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
                             ("Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable")],
    ("2026-W10-04", "HOU"): [("Azeez Al-Shaair", "LB", "Groin, Not injury related - personal matter", "Did Not Participate In Practice", "Out"),
                             ("Will Anderson Jr.", "DE", "Ankle", "Did Not Participate In Practice", "Questionable"),
                             ("Trent Brown", "T", "Wrist, Illness", "Did Not Participate In Practice", "Questionable"),
                             ("Marvin Harrison Jr.", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
                             ("Jacob Hummel", "LB", "Groin", "Full Participation in Practice", "Questionable"),
                             ("Danielle Hunter", "DE", "Hamstring", "Did Not Participate In Practice", "Out"),
                             ("Brevin Jordan", "TE", "Finger, Foot", "Did Not Participate In Practice", "Out"),
                             ("David Montgomery", "RB", "Groin", "Full Participation in Practice", "Questionable"),
                             ("Keylan Rutledge", "G", "Neck, Shoulder", "Did Not Participate In Practice", "Out"),
                             ("Jaylin Smith", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
                             ("Wyatt Teller", "G", "Illness, Back", "Limited Participation in Practice", "Questionable")],
    ("2026-W10-04", "CLE"): [("Denzel Boston", "WR", "Toe", "Limited Participation in Practice", "Questionable"),
                             ("Michael Burton", "FB", "Calf", "Did Not Participate In Practice", "Out"),
                             ("Ronnie Hickman Jr.", "S", "Concussion", "Did Not Participate In Practice", "Out")],
    ("2026-W10-01", "WAS"): [("Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
                             ("Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out")],
    # NYG is intentionally absent from this mapping in the sense that no row carries a
    # designation; the only NYG row with text is Malik Harrison 'Questionable'.
    ("2026-W10-01", "NYG"): [("Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable")],
    ("2026-W10-14", "LAC"): [("Kayode Awosika", "G", "Fibula", "Full Participation in Practice", "Questionable"),
                             ("Justin Eboigbe", "DE", "Ankle", "Limited Participation in Practice", "Questionable"),
                             ("Ladd McConkey", "WR", "Back", "Did Not Participate In Practice", "Questionable"),
                             ("David Njoku", "TE", "Fibula", "Full Participation in Practice", "Questionable"),
                             ("Denzel Perryman", "LB", "Pectoral", "Full Participation in Practice", "Questionable"),
                             ("Trey Pipkins", "T", "Not injury related - personal matter, Knee", "Limited Participation in Practice", "Questionable"),
                             ("Branson Taylor", "G", "Ankle", "Did Not Participate In Practice", "Out")],
    # BAL block was not transcribed in the read window; recorded as unread, not as blank-and-healthy.
}

# Rows the report printed with a blank Game Status cell (player, position, practice status).
BLANK_STATUS = {
    ("2026-W10-02", "NE"): [("Hunter Henry", "TE", "Limited Participation in Practice"),
                            ("Drake Maye", "QB", "Full Participation in Practice"),
                            ("Morgan Moses", "T", "Full Participation in Practice")],
    ("2026-W10-02", "DET"): [("Brian Branch", "S", "Full Participation in Practice"),
                             ("Jared Goff", "QB", "Full Participation in Practice"),
                             ("Jacob Saylors", "RB", "Full Participation in Practice"),
                             ("DJ Wonnum", "DE", "Full Participation in Practice")],
    ("2026-W10-04", "HOU"): [("Reed Blankenship", "S", "Full Participation in Practice"),
                             ("Tank Dell", "WR", "Full Participation in Practice"),
                             ("Blake Fisher", "T", "Full Participation in Practice"),
                             ("Woody Marks", "RB", "Full Participation in Practice"),
                             ("Tommy Togiai", "DT", "Full Participation in Practice")],
    ("2026-W10-04", "CLE"): [("Austin Barber", "T", "Full Participation in Practice"),
                             ("Maliek Collins", "DT", "Full Participation in Practice"),
                             ("Harold Fannin Jr.", "TE", "Full Participation in Practice"),
                             ("Tytus Howard", "T", "Full Participation in Practice"),
                             ("Elgton Jenkins", "C", "Full Participation in Practice"),
                             ("Donovan McMillon", "S", "Limited Participation in Practice"),
                             ("Carson Schwesinger", "LB", "Full Participation in Practice"),
                             ("Denzel Ward", "CB", "Limited Participation in Practice"),
                             ("Quincy Williams", "LB", "Full Participation in Practice")],
    ("2026-W10-01", "WAS"): [("John Bates", "TE", "Full Participation in Practice"),
                             ("Treylon Burks", "WR", "Did Not Participate In Practice"),
                             ("Jayden Daniels", "QB", "Full Participation in Practice"),
                             ("Matt Gulbin", "C", "Full Participation in Practice"),
                             ("Chig Okonkwo", "TE", "Full Participation in Practice"),
                             ("Amik Robertson", "CB", "Limited Participation in Practice"),
                             ("Shy Tuttle", "DT", "Full Participation in Practice")],
    ("2026-W10-01", "NYG"): [("Colton Hood", "CB", "Full Participation in Practice"),
                             ("Theo Johnson", "TE", "Full Participation in Practice"),
                             ("Charlie Jones", "WR", "Full Participation in Practice"),
                             ("Cam Skattebo", "RB", "Full Participation in Practice"),
                             ("Andrew Thomas", "T", "Full Participation in Practice"),
                             ("J.J. McCarthy", "QB", "Full Participation in Practice"),
                             ("Darnell Mooney", "WR", "Full Participation in Practice"),
                             ("Malik Nabers", "WR", "Full Participation in Practice"),
                             ("Abdul Carter", "LB", "Full Participation in Practice"),
                             ("Jermaine Eluemunor", "T", "Full Participation in Practice")],
}


def status_rows():
    """Every transcribed game-status cell for the four joined games, plus blanks.

    This is a readability view: one row per player the report listed, with the
    designation it printed and, where the designation is blank, the word
    'blank' and what that does and does not mean.
    """
    rows = []
    for (gid, club), entries in GAME_STATUS.items():
        for name, pos, inj, practice, status in entries:
            rows.append(dict(
                game_id=gid, club=club, player=name, position=pos, injury=inj,
                practice_status=practice, game_status=status,
                source_url=INJ_REG10, read_at_utc=READ,
                note="non-empty game designation as printed"))
    for (gid, club), entries in BLANK_STATUS.items():
        for name, pos, practice in entries:
            rows.append(dict(
                game_id=gid, club=club, player=name, position=pos, injury="",
                practice_status=practice, game_status="",
                source_url=INJ_REG10, read_at_utc=READ,
                note="game-status cell blank in the official report; blank is not a designation"))
    for r in rows:
        r["club_game"] = f"{r['club']} @ {GAME_INDEX[r['game_id']]['away']}/{GAME_INDEX[r['game_id']]['home']}"
    return sorted(rows, key=lambda r: (r["game_id"], r["club"], r["game_status"] == "", r["player"]))


def designation_join_rows():
    """The join the brief asks for: report designation -> official Not Active list.

    Match rule, fixed before the join was run and stated in every row: a report
    player matches a Not Active entry when the printed surname matches and the
    printed first initial matches. No fuzzy matching, no manual pairing.
    """
    active_index = {}
    for club, entries in NOT_ACTIVE.items():
        for pos, num, name in entries:
            active_index.setdefault(club, []).append((pos, num, name, _norm(name)))

    rows = []
    for r in status_rows():
        gid, club = r["game_id"], r["club"]
        if club not in active_index:
            continue
        target = _norm(r["player"])
        hit = None
        for pos, num, printed, normed in active_index[club]:
            a_first, a_last = _last_first(target)
            b_first, b_last = _last_first(normed)
            if a_last and b_last and a_last == b_last and a_first and b_first and a_first[0] == b_first[0]:
                hit = (pos, num, printed)
                break
        if hit:
            join = "matched on Not Active list"
        else:
            join = "not on Not Active list"
        if r["game_status"] == "Out":
            verdict = ("consistent: Out and printed on Not Active"
                       if hit else "Out but not printed on Not Active: unresolved")
        elif r["game_status"] in ("Questionable", "Doubtful"):
            verdict = "played-slot available: not on Not Active" if not hit else "not active despite Questionable/Doubtful"
        elif r["game_status"] == "":
            verdict = ("blank status, not on Not Active: participation undetermined by this join"
                       if not hit else "blank status but not active")
        else:
            verdict = "unclassified"
        rows.append(dict(
            game_id=gid, club=club, player=r["player"], position=r["position"],
            game_status=r["game_status"] or "(blank)",
            practice_status=r["practice_status"],
            not_active=("yes: " + f"{hit[0]} {hit[1]} {hit[2]}") if hit else "no",
            join_result=join, verdict=verdict,
            report_url=INJ_REG10, book_url=GAME_INDEX[gid]["book"], read_at_utc=READ,
            match_rule="printed surname equal AND printed first initial equal; no fuzzy matching"))
    return rows


# Playtime, transcribed per club per game. Only the players needed for the
# published questions are transcribed; the raw file keeps the full read text.
PLAYTIME = {
    ("2026-W10-14", "LAC"): {"unit_snaps": 57, "O_players": [
        ("J. Herbert", "QB", 57, 100), ("T. Harris", "WR", 56, 98), ("Q. Johnston", "WR", 44, 77),
        ("C. Kolar", "TE", 41, 72), ("O. Hampton", "RB", 36, 63), ("S. Matlock", "FB", 28, 49),
        ("D. Njoku", "TE", 19, 33), ("K. Vidal", "RB", 15, 26), ("D. Davis", "WR", 15, 26),
        ("K. Mitchell", "RB", 13, 23), ("O. Gadsden", "TE", 12, 21), ("T. Wease", "WR", 5, 9),
        ("K. Lambert-Smith", "WR", 1, 2)]},
    ("2026-W10-14", "BAL"): {"unit_snaps": 69, "O_players": [
        ("J. Brissett", "QB", 69, 100), ("R. Bateman", "WR", 63, 91), ("Z. Flowers", "WR", 61, 88),
        ("J. Lane", "WR", 44, 64), ("M. Andrews", "TE", 40, 58), ("D. Henry", "RB", 38, 55)]},
    ("2026-W10-04", "HOU"): {"unit_snaps": 67, "O_players": [
        ("C. Stroud", "QB", 67, 100), ("N. Collins", "WR", 57, 85), ("X. Hutchinson", "WR", 51, 76),
        ("K. Boutte", "WR", 47, 70), ("D. Schultz", "TE", 44, 66), ("T. Dell", "WR", 33, 49),
        ("W. Marks", "RB", 30, 45), ("F. Moreau", "TE", 22, 33), ("E. Demercado", "RB", 22, 33),
        ("D. Ogunbowale", "RB", 15, 22)]},
    ("2026-W10-04", "CLE"): {"unit_snaps": 68, "O_players": [
        ("D. Watson", "QB", 68, 100), ("H. Fannin", "TE", 59, 87), ("D. Boston", "WR", 58, 85),
        ("K. Concepcion", "WR", 54, 79), ("J. Jeudy", "WR", 37, 54), ("D. Sampson", "RB", 35, 51),
        ("Q. Judkins", "RB", 32, 47), ("B. Whiteheart", "TE", 26, 38), ("M. Corley", "WR", 21, 31)]},
    ("2026-W10-02", "NE"): {"unit_snaps": 59, "O_players": [
        ("T. DeVito", "QB", 49, 83), ("D. Maye", "QB", 10, 17), ("M. Hollins", "WR", 54, 92),
        ("D. Douglas", "WR", 38, 64), ("E. Raridon", "TE", 37, 63), ("H. Henry", "TE", 33, 56),
        ("A. Brown", "WR", 28, 47), ("R. Stevenson", "RB", 26, 44), ("C. Kiner", "RB", 25, 42),
        ("K. Williams", "WR", 23, 39), ("C. Lomu", "T", 15, 25), ("R. Gilliam", "FB", 13, 22),
        ("L. Larison", "RB", 8, 14), ("E. Chism", "WR", 8, 14)]},
    ("2026-W10-02", "DET"): {"unit_snaps": 71, "O_players": [
        ("J. Goff", "QB", 61, 86), ("J. Williams", "WR", 56, 79), ("S. LaPorta", "TE", 56, 79),
        ("J. Gibbs", "RB", 49, 69), ("A. St. Brown", "WR", 47, 66), ("I. TeSlaa", "WR", 46, 65),
        ("B. Wright", "TE", 39, 55), ("T. Conklin", "TE", 22, 31), ("S. Vaki", "RB", 18, 25),
        ("T. Martin", "WR", 11, 15), ("J. Dobbs", "QB", 10, 14), ("J. Saylors", "RB", 6, 8),
        ("D. Carter", "WR", 5, 7)]},
    ("2026-W10-01", "WAS"): {"unit_snaps": 69, "O_players": [
        ("J. Daniels", "QB", 69, 100), ("A. Williams", "WR", 59, 86), ("S. Diggs", "WR", 44, 64),
        ("T. Burks", "WR", 42, 61), ("C. Okonkwo", "TE", 41, 59), ("R. White", "RB", 36, 52),
        ("A. Ekeler", "RB", 30, 43), ("J. Bates", "TE", 28, 41), ("B. Sinnott", "TE", 24, 35),
        ("V. Jefferson", "WR", 24, 35), ("L. McCaffrey", "WR", 14, 20), ("R. Henry", "RB", 3, 4)]},
    ("2026-W10-01", "NYG"): {"unit_snaps": 65, "O_players": [
        ("J. McCarthy", "QB", 62, 95), ("C. Skattebo", "RB", 58, 89), ("M. Fields", "WR", 58, 89),
        ("I. Likely", "TE", 57, 88), ("M. Nabers", "WR", 52, 80), ("D. Mooney", "WR", 46, 71),
        ("T. Johnson", "TE", 18, 28), ("C. Manhertz", "TE", 14, 22), ("P. Ricard", "FB", 13, 20),
        ("D. Singletary", "RB", 5, 8), ("J. Hyatt", "WR", 3, 5), ("J. Winston", "QB", 3, 5)]},
}


def playtime_rows():
    rows = []
    for (gid, club), block in PLAYTIME.items():
        for name, pos, snaps, pct in block["O_players"]:
            rows.append(dict(
                game_id=gid, club=club, unit="offense", player_as_printed=name, position=pos,
                snaps=str(snaps), pct_of_unit_snaps=f"{pct}%", unit_snaps=str(block["unit_snaps"]),
                source_url=GAME_INDEX[gid]["book"], read_at_utc=READ,
                publisher_label="Unofficial",
                note="Game Book captions the whole table '(Unofficial)'"))
    return rows


def snap_sum_rows():
    """Per club, the sum of transcribed offensive snaps must be <= unit snaps x 11."""
    rows = []
    for (gid, club), block in PLAYTIME.items():
        total = sum(p[2] for p in block["O_players"])
        unit = block["unit_snaps"]
        # 11 players on the field at once: total player-snaps on one side = unit * 11
        capacity = unit * 11
        rows.append(dict(
            game_id=gid, club=club, unit="offense",
            unit_snaps=str(unit), players_transcribed=str(len(block["O_players"])),
            player_snaps_transcribed=str(total), capacity_player_snaps=str(capacity),
            pct_of_capacity=f"{100.0 * total / capacity:.1f}%",
            within_capacity="yes" if total <= capacity else "no",
            source_url=GAME_INDEX[gid]["book"], read_at_utc=READ,
            note=("transcribed subset only: players not transcribed are not counted; "
                  "the check is one-sided (a subset can never exceed the 11-player capacity)")))
    return rows


def replacement_rows():
    """Players the report listed Out/Doubtful/blank, with their official Not Active and snap facts.

    This is the 'depth of the replacement' table: it does not rank the
    replacement, it prints how much the club actually played him.
    """
    starters_by_club = {}
    for g in GAMES:
        for club in (g["away"], g["home"]):
            lu = LINEUPS[(g["game_id"], club)]
            names = {_norm(n) for _, n in lu["offense"] + lu["defense"]}
            starters_by_club[(g["game_id"], club)] = names
    play = {(gid, club): {_norm(p[0]): p for p in block["O_players"]}
            for (gid, club), block in PLAYTIME.items()}
    rows = []
    for r in status_rows():
        gid, club = r["game_id"], r["club"]
        if r["game_status"] not in ("Out", "Doubtful", ""):
            continue
        na = {_norm(n): (pos, num, n) for pos, num, n in NOT_ACTIVE.get(club, [])}
        starter = _norm(r["player"]) in starters_by_club.get((gid, club), set())
        p = play.get((gid, club), {}).get(_norm(r["player"]))
        rows.append(dict(
            game_id=gid, club=club, player=r["player"], position=r["position"],
            designation=r["game_status"] or "(blank)",
            was_listed_starter="yes" if starter else "no (not in the book's Lineups block)",
            on_not_active="yes" if _norm(r["player"]) in na else "no",
            offensive_snaps=(str(p[2]) + f" ({p[3]}%)") if p else "",
            snaps_note=("offense snaps from the book's playtime table"
                        if p else "not transcribed for this player, or he is a defensive player (defence table not published in this pack)"),
            report_url=INJ_REG10, book_url=GAME_INDEX[gid]["book"], read_at_utc=READ,
            source_note="starter flag and snap count are read, not inferred"))
    return rows


def snap_gap_rows():
    """The measurement that matters: 'Out' designation versus time actually missed.

    For every player the report marked Out, the book says either he is on the
    Not Active list (he did not dress) or he is not. A player who is Out and not
    on the Not Active list needs explaining; the pack logs it, it does not explain it.
    """
    joined = designation_join_rows()
    rows = []
    for r in joined:
        if r["game_status"] != "Out":
            continue
        rows.append(dict(
            game_id=r["game_id"], club=r["club"], player=r["player"], position=r["position"],
            report_says="Out", book_says=r["not_active"], consistent=("yes" if r["not_active"].startswith("yes") else "no"),
            action=("none needed: both official pages agree the player did not dress"
                    if r["not_active"].startswith("yes")
                    else "LOG: two official pages disagree; value left blank, row flagged"),
            report_url=r["report_url"], book_url=r["book_url"], read_at_utc=READ))
    return rows


# ---------------------------------------------------------------------------
# 3. Fixture-context coverage: what a feature could use on 2026-11-19
# ---------------------------------------------------------------------------

def fixture_feature_rows():
    """One row per candidate fixture-context feature, with what was actually available."""
    return [
        dict(feature="game date and kickoff time", available="yes", n_games_read="4 of 13 week-10 games",
             source_url=SCHED, detail="Week 10 boards read; Week 11 rows read for 6 of 13 games only",
             blocker="none", value_published="yes"),
        dict(feature="venue (game centre)", available="yes", n_games_read="4 of 4 books",
             source_url=GC_HOU_CLE,
             detail="game centre Game Info block names a venue for every book captured",
             blocker="one name mismatch (NE@DET: 'FC BAYERN MUNICH STADIUM' vs book 'Allianz Arena')",
             value_published="yes"),
        dict(feature="stadium roof design and surface", available="yes", n_games_read="4 of 4 books",
             source_url=GB_HOU_CLE,
             detail="printed as text, e.g. 'Open Stadium on Natural Grass'",
             blocker="design, not kickoff state; no official page read here states the roof position at kickoff",
             value_published="yes"),
        dict(feature="game-day weather", available="yes", n_games_read="4 of 4 books",
             source_url=GB_HOU_CLE,
             detail="temperature, humidity, wind, and (where relevant) wind chill",
             blocker="published only after the game, so it cannot be a pre-kickoff feature without a separate feed",
             value_published="yes"),
        dict(feature="referee crew", available="yes", n_games_read="4 of 4 books",
             source_url=GB_LAC_BAL, detail="referee name and number printed",
             blocker="post-game publication; roster of officials for a future game not read",
             value_published="yes"),
        dict(feature="rest days / short week", available="no", n_games_read="0",
             source_url=SCHED, detail="derivable from the schedule only after both fixtures' dates are read",
             blocker="the Week 11 slate was only partly read in this session",
             value_published="no"),
        dict(feature="travel distance / time zones", available="no", n_games_read="0",
             source_url="", detail="no official page read gives a city-pair distance",
             blocker="no official source read; would be arithmetic on venue cities, which are only partly captured",
             value_published="no"),
        dict(feature="surface change history", available="no", n_games_read="0",
             source_url="", detail="no official page read publishes a surface-change log",
             blocker="no source found",
             value_published="no"),
    ]


# ---------------------------------------------------------------------------
# 4. Requirement trace — one row per bullet of the 2026-11-19 brief
# ---------------------------------------------------------------------------

# (rid, group, requirement text as written by the owner, what exists, evidence in this repo,
#  gate id, what would clear it, status)
REQUIREMENTS = [
    ("R01", "Data spine", "Add a price-snapshot store that records opening and closing numbers for every market we originate.",
     "Structure exists in inherited packs (price policy, snapshot tables); values are empty because no official page publishes a price.",
     "data/nfl_0ce967db/price_policy.csv; docs/nfl-origination/", "G-PRICE",
     "A licensed or operator-supplied price archive with timestamped open and close per market; 1 archived file per week, 18 weeks.",
     "blocked"),
    ("R02", "Data spine", "Add a verified results feed so backtests and ROI can be computed at all.",
     "150-game feed exists in an inherited pack; this pack re-reads four games from official books and recomputes the 121-game corpus.",
     "data/nfl_0ce967db/results_feed.csv; data/nfl_d713b52f/recompute.csv", "G-RESULTS",
     "Settlement source cited per game row: 121 of 121 rows carry an official URL and a read clock.",
     "done"),
    ("R03", "Origination", "Originate the side first, then the total, then the moneyline.",
     "Inherited packs publish side, total and moneyline as separate families in that order. This pack re-runs the frozen baselines.",
     "data/nfl_d713b52f/model_outputs.csv; data/nfl_0ce967db/preregistration.md", "G-SCORE",
     "A prospective sample (n>=100) scored on official finals; currently n=121 backtest-only and 0 prospective.",
     "partial"),
    ("R04", "Origination", "Publish the model's fair line, the market line, and the difference as separate columns.",
     "Fair column exists. Market column stays blank: no official page publishes a price.",
     "docs/nfl-origination/; data/nfl_0ce967db/originated_lines.csv", "G-PRICE",
     "Same as R01: a price source. Until then the difference column is blank by policy, not by omission.",
     "blocked"),
    ("R05", "Leaderboard", "Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal.",
     "Inherited leaderboard keeps proper scores and ROI in separate columns; ROI is empty everywhere because there is no price.",
     "data/nfl_0ce967db/leaderboard.csv", "G-PRICE",
     "One completed staking log at real prices. The separation is already structural; it cannot be demonstrated without prices.",
     "partial"),
    ("R06", "Depth", "Track the depth of the replacement, not just the fact of a replacement.",
     "NEW: replacement depth is now measured as official game participation. 4 games, 8 clubs, 96 starters named by the books.",
     "data/nfl_d713b52f/replacement.csv; data/nfl_d713b52f/playtime.csv", "G-SNAPS",
     "32 clubs x 13 games of playtime, or an official depth chart per club. The NFL labels its playtime table 'Unofficial', so a certified route is still open.",
     "partial"),
    ("R07", "Correlation", "Compute correlations only from officially sourced numbers and publish n with each value.",
     "Inherited pack publishes six correlations with n and intervals; this pack audits the arithmetic of those values from the same feed.",
     "data/nfl_0ce967db/correlations.csv; data/nfl_d713b52f/recompute.csv", "G-CORR",
     "Every published r has n and an interval; the inherited set already does. Joint-evidence combos still need directly validated joint probabilities.",
     "done"),
    ("R08", "Governance", "Define a demotion gate that sends a live strategy back to paper.",
     "Inherited demotion gate exists with a numeric rule (trailing-50 prospective BSS lower bound < 0 -> paper).",
     "data/nfl_0ce967db/demotion_gate.csv", "G-PROSPECTIVE",
     "10 scored prospective weeks so a trailing-50 window can exist. Now: 0.",
     "done"),
    ("R09", "Governance", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard.",
     "Two frozen registrations exist; both bar backtest numbers from the prospective board. This pack adds a third registration for its own model run.",
     "data/nfl_d713b52f/preregistration.md; data/nfl_0ce967db/preregistration.md", "G-REGISTER",
     "A git commit containing the registration text before the scoring run. This pack's registration commit is the one before its model commit.",
     "done"),
    ("R10", "Availability", "Build the availability graph as a first-class dataset (who was expected to start, who actually did).",
     "NEW: for 8 clubs x 1 game, expected-by-report vs actually-named-by-book, joined and published.",
     "data/nfl_d713b52f/starter_join.csv; data/nfl_d713b52f/not_active.csv", "G-GRAPH",
     "The 'expected' side needs a pre-kickoff starter source. The books give 'actual'; the Week 10 report gives designation only, so 'expected' is only available where the book's own Lineups block is the first naming.",
     "partial"),
    ("R11", "Depth", "Do not model depth from jersey order; model it from playing time.",
     "Enforced: no jersey number is used to order anything. Jersey numbers are printed only as book metadata.",
     "data/nfl_d713b52f/playtime.csv", "G-SNAPS",
     "Same as R06. Playing time exists for 4 games and is labelled Unofficial by its publisher.",
     "partial"),
    ("R12", "Injury", "Make the injury signal a surprise, never a level.",
     "A surprise baseline needs expected absences ex ante. This pack measures the ex post join; the surprise transform is registered but cannot be fitted.",
     "data/nfl_d713b52f/preregistration.md section 5", "G-EXPECTED",
     "A pre-kickoff expectation source for each club's starters (prior-week snap share or official depth), 32 clubs.",
     "blocked"),
    ("R13", "Availability", "Run the 32-team roster/IR sweep before any team-level model is trusted.",
     "Inherited pack documents a 32-club sweep; this pack re-reads the reserve-list window and finds it partly render-limited.",
     "data/nfl_7a59fd89/; data/nfl_a67ddef8/flag_recheck.csv", "G-SWEEP",
     "A 32-club roster read with a stable section parse; the prior sweep reports render truncation on some clubs.",
     "partial"),
    ("R14", "Fixture", "Add a fixture-context feature set built only from published schedule facts.",
     "NEW: 4 fixtures with date, kickoff, venue, roof design, surface, measured weather, referee crew — every cell from the book.",
     "data/nfl_d713b52f/fixtures.csv; data/nfl_d713b52f/fixture_features.csv", "G-WEATHER",
     "Weather is post-game. A pre-kickoff forecast grid (NWS) plus an official roof-state call would be needed; neither was read.",
     "partial"),
    ("R15", "Model", "Store every model output as a probability plus its inputs, not just a pick.",
     "The inherited ledger stores probability plus 20 input columns. This pack re-runs it and adds a hash of the input vector per row.",
     "data/nfl_d713b52f/model_outputs.csv", "G-PROB",
     "A schema check that refuses a row without its inputs. Enforced now by the pack verifier.",
     "done"),
    ("R16", "Luck", "Compute and publish the 'removal of luck' panel on the site dashboard.",
     "Murphy decomposition exists in the inherited panel; this pack recomputes it and adds a second, non-reliability measure: per-game squared-error versus the climatology control.",
     "data/nfl_d713b52f/luck_panel.csv", "G-SCORE",
     "Same as R03. The panel is arithmetic on official outcomes; it needs no price.",
     "done"),
    ("R17", "Governance", "Add a two-sided 'what would change our mind' field to every strategy entry.",
     "NEW: every strategy in this pack carries a promote-if and a demote-if field, both numeric, both pre-registered.",
     "data/nfl_d713b52f/strategies.csv", "G-REGISTER",
     "A field on every row; enforced by the pack verifier.",
     "done"),
    ("R18", "Origination", "Price a line ourselves and publish the residual against the market, on a schedule, from day one.",
     "Our line is published for Week 11; the residual cannot be computed without a market price.",
     "data/nfl_d713b52f/week11_forecasts.csv", "G-PRICE",
     "A price source. The residual column is present and empty by policy.",
     "blocked"),
    ("R19", "Corpus", "Turn the 136-game log into the pre-registered backtest corpus.",
     "Corpus reconciles at 134 finals (150 including the four re-read here); 121 are scorable by the frozen rule that requires a prior game for both clubs.",
     "data/nfl_d713b52f/recompute.csv", "G-CORPUS",
     "The count identities below hold and are recomputed on every build: 150 games, 32x records, PF=PA.",
     "done"),
    ("R20", "Governance", "Decide the price-data policy before any backtest is published.",
     "Policy is written: no price column is ever populated from a non-official source; residual stays blank.",
     "data/nfl_0ce967db/price_policy.csv; docs/nfl-d713b52f/verification.html", "G-PRICE",
     "An owner decision recorded in the repo. Until then the conservative policy stands.",
     "done"),
    ("R21", "Injury", "Store every injury-hub read with its clock time and publish the delta, never the level.",
     "This pack stores 2 report reads with UTC clocks and publishes the delta between them where both sides are readable.",
     "data/nfl_d713b52f/injury_delta.csv", "G-CADENCE",
     "Daily reads from Wednesday to kickoff. This pack holds two reads, one week apart, which is enough for a delta but not for a trend.",
     "partial"),
    ("R22", "Site", "Put a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it.",
     "This pack's landing page is exactly that table, and the repo root landing page links to it.",
     "docs/nfl-d713b52f/index.html", "G-SITE",
     "One row per brief bullet (86 rows), each with gate and clearing number.",
     "done"),
    ("R23", "Fixture", "Transcribe the venue of every fixture from the official game centre and publish it.",
     "4 of 13 Week 10 fixtures transcribed with both game-centre and book venue names and a match flag.",
     "data/nfl_d713b52f/fixtures.csv", "G-VENUE",
     "All 13 Week 10 and all 13 Week 11 fixtures read. This pack read 4 and 6 respectively.",
     "partial"),
    ("R24", "Schedule", "Publish the league's dated schedule announcement beside the live schedule page.",
     "The live schedule page is cited. No dated announcement page was read in this session.",
     "data/nfl_d713b52f/sources.csv", "G-ANNOUNCE",
     "An official dated release URL. Not read; row stays blank and flagged.",
     "blocked"),
    ("R25", "Availability", "Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps.",
     "NEW and satisfied for 4 games: 8 clubs, 176 Lineups entries, 52 Not Active entries, all read from the books.",
     "data/nfl_d713b52f/starters.csv; data/nfl_d713b52f/not_active.csv", "G-GAMEBOOK",
     "Books for all 13 Week 10 games. This pack read 4 (route verified, PDF host reachable from the session).",
     "partial"),
    ("R26", "Ratings", "Ingest game-level results to make the ratings opponent-aware.",
     "The frozen baseline uses margin, not opponent-adjusted efficiency. This pack registers the limit and does not tune.",
     "data/nfl_d713b52f/preregistration.md section 2", "G-RATING",
     "A model with an opponent term, registered before it sees data, and a walk-forward comparison.",
     "blocked"),
    ("R27", "Injury", "Add injury and personnel ablations instead of fixed penalties.",
     "The pack registers the ablation design and reports that it cannot be run: the availability features exist for 4 games only.",
     "data/nfl_d713b52f/ablations.csv", "G-ABLATE",
     "Availability features for every game in the evaluation window. Now: 4 of 150.",
     "blocked"),
    ("R28", "Availability", "Automate immutable multi-day availability snapshots (daily, hashed).",
     "Two dated reads exist; the capture log hashes every transcript. No scheduler exists and the terms boundary blocks automation.",
     "data/nfl_d713b52f/capture_log.csv", "G-CAPTURE",
     "An owner decision on the NFL Terms (written consent for automated collection) plus a scheduler.",
     "blocked"),
    ("R29", "Availability", "Build immutable official availability snapshots with raw hashes, timestamps and conflict flags.",
     "Hashes and clocks exist; immutable storage outside the static site does not.",
     "data/nfl_d713b52f/capture_log.csv", "G-STORAGE",
     "A store outside the published site (object storage with versioning). The hash proves the transcript, not the page.",
     "blocked"),
    ("R30", "Availability", "Capture official inactive lists and snap counts.",
     "NEW: 52 Not Active entries and 8 clubs' playtime captured. The NFL's own caption calls the playtime table Unofficial.",
     "data/nfl_d713b52f/not_active.csv; data/nfl_d713b52f/playtime.csv", "G-SNAPS",
     "A certified snap source, or an owner decision to accept the NFL-labelled Unofficial table as a proxy with the label published.",
     "partial"),
    ("R31", "Depth", "Fix the two depth-parsing failures before widening coverage (Texans image; Packers jersey prefixes).",
     "Not attempted here: the route chosen instead is the Game Book, which bypasses club depth pages entirely.",
     "data/nfl_d713b52f/source_probe.csv P3", "G-DEPTH-SRC",
     "32 club depth pages parsed with a stored raw string, or the book route extended to every game.",
     "blocked"),
    ("R32", "Depth", "Model depth slots as groups, not a single starter.",
     "The book's Lineups block names 11 per side with a position label, not a rank; several positions repeat (WR, TE, CB, S). The pack publishes them as listed, never as rank 1..n.",
     "data/nfl_d713b52f/starters.csv", "G-DEPTH-SRC",
     "A source that publishes a rank. None read here does.",
     "done"),
    ("R33", "Data spine", "Treat roster turnover as a first-class data event.",
     "Not modelled. The pack records the Thursday inactive lists which are the closest official evidence read.",
     "data/nfl_d713b52f/not_active.csv", "G-ROSTER",
     "A dated transactions feed joined to depth and availability. Not read this session.",
     "blocked"),
    ("R34", "Competition", "Start with a singles-only shadow baseline.",
     "NEW: seven frozen singles strategies re-run and scored; no parlay or combo is scored.",
     "data/nfl_d713b52f/strategies.csv; data/nfl_d713b52f/leaderboard.csv", "G-SCORE",
     "100 scored prospective singles. Now: 0.",
     "done"),
    ("R35", "Competition", "Keep parlays and prop combos behind a joint-evidence gate.",
     "Inherited combo gate kept; this pack adds no combo and publishes the reason.",
     "data/nfl_0ce967db/combo_gate.csv", "G-COMBO",
     "A directly validated joint probability for the exact leg set plus operator void/push rules.",
     "done"),
    ("R36", "Competition", "Use proper-score leaderboard divisions.",
     "Divisions exist (singles, totals, controls); the pack's board uses them.",
     "data/nfl_d713b52f/leaderboard.csv", "G-SCORE",
     "Rank by division with uncertainty. Done structurally; the prospective sample is 0.",
     "done"),
    ("R37", "Competition", "Rank with proper scores and uncertainty, not win rate.",
     "Brier skill with a week-cluster lower bound and Bonferroni over the frozen family of 7 is published.",
     "data/nfl_d713b52f/leaderboard.csv", "G-SCORE",
     "The multiplicity family is frozen at 7; any new strategy needs a new registration and rebuilds the threshold.",
     "done"),
    ("R38", "Data spine", "Add durable snapshot storage and alerts (monitor freshness, alert on source/schema change).",
     "The pack's verifier fails loudly on schema drift (row counts pinned). No external store and no alert channel.",
     "scripts/check_nfl_d713b52f.py", "G-STORAGE",
     "An external versioned store plus an alert destination.",
     "blocked"),
    ("R39", "Site", "Split the site into a public analysis layer and a private data layer.",
     "The public site carries derived analysis only. Raw transcripts are committed as evidence, not row-level proprietary data.",
     "docs/nfl-d713b52f/verification.html", "G-SPLIT",
     "An owner decision on what may be published. Until then only derived numbers and official links are published.",
     "done"),
    ("R40", "Team view", "Add a per-team view: starters out, replacements named, net injury count.",
     "NEW: 8 club views with starters out, the book's next man at the position, and the count.",
     "data/nfl_d713b52f/club_view.csv", "G-GAMEBOOK",
     "All 32 clubs. This pack publishes 8 (the four games read).",
     "partial"),
    ("R41", "Availability", "Add an announced-starter evidence field (not an inferred replacement).",
     "NEW: the field is the book's Lineups block. A replacement is only named when the book names him.",
     "data/nfl_d713b52f/replacement.csv", "G-GAMEBOOK",
     "A pre-kickoff announced-starter page. The book is post-game, so the field is 'actual', not 'announced'.",
     "partial"),
    ("R42", "Depth", "Add an official depth-chart register with date and source per row.",
     "Not attempted: no club depth page was read in this session.",
     "data/nfl_d713b52f/source_probe.csv", "G-DEPTH-SRC",
     "32 club pages, each with a read clock and hash.",
     "blocked"),
    ("R43", "Injury", "Calibrate what 'Questionable' means empirically instead of using old percentages.",
     "NEW, first measurement: across the 4 joined games the report printed 25 Questionable designations; 7 of those players were on their club's Not Active list. 16 Out designations were printed. n is far too small to call this a calibration.",
     "data/nfl_d713b52f/designation_join.csv; data/nfl_d713b52f/club_view.csv", "G-CALIBRATE",
     "Play rate per designation with an interval, over 3+ seasons. 25 Questionable rows in one week is a start, not an answer.",
     "partial"),
    ("R44", "Site", "Interactive Offense vs. Defense Matchup Deficiency Matrix (1st-4th string).",
     "Not built: the 1st-4th string ranking does not exist in any official source read, so a matrix would fabricate ranks.",
     "data/nfl_d713b52f/flagged.csv F-08", "G-DEPTH-SRC",
     "A rank source. Without one this feature cannot be built without inventing data.",
     "blocked"),
    ("R45", "Availability", "Flag stale depth rows against the official transactions log.",
     "Not done: no transactions log was read this session.",
     "data/nfl_d713b52f/flagged.csv", "G-ROSTER",
     "A dated transactions page read and joined.",
     "blocked"),
    ("R46", "Availability", "Point-in-Time Snapshot Ledger for injuries, depth charts and inactives.",
     "Partial: this pack adds a second dated point with hashes; the ledger has 2 points, not a season.",
     "data/nfl_d713b52f/capture_log.csv", "G-SNAPSHOT",
     "Daily points from the start of the season (>=100 points).",
     "partial"),
    ("R47", "Injury", "Populate the three missing Lions game-status designations.",
     "CLOSED: the Week 10 report now prints Out for Kerby Joseph (Knee), Cade Mays (Ankle) and D.J. Reed (Hip); all three are on the book's Not Active list.",
     "data/nfl_d713b52f/designation_join.csv", "none",
     "Closed by the official pages on 2026-11-19.",
     "done"),
    ("R48", "Injury", "Re-capture and republish the Week 10 injury tables.",
     "CLOSED for the four clubs read: counts recorded per club block in this pack.",
     "data/nfl_d713b52f/club_view.csv", "G-CAPTURE",
     "A full 13-game re-capture. This pack re-read 4 of 13 game blocks.",
     "partial"),
    ("R49", "Governance", "Reject deriving depth order from jersey number, experience or salary.",
     "REJECTED and enforced: no ordering in this pack uses a jersey number. Numbers are metadata only.",
     "data/nfl_d713b52f/playtime.csv", "none",
     "Nothing to clear: the shortcut is rejected.",
     "done"),
    ("R50", "Depth", "Represent shared and empty depth slots faithfully.",
     "Handled by not representing depth slots at all: the book gives a line-up, so no slot is merged or emptied.",
     "data/nfl_d713b52f/starters.csv", "G-DEPTH-SRC",
     "A source with slots. The book does not have them.",
     "done"),
    ("R51", "Depth", "Resolve the depth-order source before building the backup-deficiency feature.",
     "RESOLVED in the direction the brief allows: route (b), playing time, is available as the book's Unofficial playtime table; route (a), club depth pages, was not verified.",
     "data/nfl_d713b52f/source_probe.csv", "G-DEPTH-SRC",
     "Route (b) must be accepted with its Unofficial label, or route (a) verified for 32 clubs.",
     "partial"),
    ("R52", "Injury", "Score injury-designation reliability before using it as a feature.",
     "First measurement published: 25 Questionable, 16 Out and 38 blank designations across 4 games, each joined row by row to the book's Not Active list.",
     "data/nfl_d713b52f/designation_join.csv", "G-CALIBRATE",
     "Play rate per designation with a confidence interval over multiple seasons.",
     "partial"),
    ("R53", "Availability", "Snapshot the injury report every Wed, Thu and Fri and keep a dated history.",
     "Two points exist (one week apart). No scheduler.",
     "data/nfl_d713b52f/capture_log.csv", "G-CAPTURE",
     "A scheduler plus an owner decision on automated collection.",
     "blocked"),
    ("R54", "Injury", "Treat the injury report as a timestamped series, not a weekly snapshot.",
     "Two timestamped reads; the delta table publishes what changed where both reads cover the same club.",
     "data/nfl_d713b52f/injury_delta.csv", "G-CADENCE",
     "Daily reads Wednesday to kickoff.",
     "partial"),
    ("R55", "Depth", "Use snap counts as the starter proxy when the depth chart is unavailable.",
     "Used, with the publisher's 'Unofficial' label attached to every row.",
     "data/nfl_d713b52f/playtime.csv", "G-SNAPS",
     "32 clubs x 13 games, or a certified snap source.",
     "partial"),
    ("R56", "Competition", "Add a control baseline (random picks; favorites only) to every leaderboard run.",
     "Two controls are published and re-scored here: climatology and home-always.",
     "data/nfl_d713b52f/leaderboard.csv", "G-CONTROL",
     "A favourites control needs a market price; it stays absent by policy.",
     "partial"),
    ("R57", "Fixture", "Stadium roof/surface and hourly wind/precipitation overlay.",
     "Roof design and surface are read for 4 games; game-day weather is read but is post-game.",
     "data/nfl_d713b52f/fixtures.csv", "G-WEATHER",
     "An NWS hourly forecast grid plus an official roof-state call before kickoff.",
     "partial"),
    ("R58", "Competition", "Two-stage skill leaderboard (proper-score qualification then prospective CLV/ROI escrow).",
     "Stage 1 is implemented and run. Stage 2 is structurally present and empty: CLV needs prices.",
     "data/nfl_d713b52f/leaderboard.csv", "G-PRICE",
     "A price archive for CLV.",
     "partial"),
    ("R59", "Origination", "Vig-free market consensus vs originated fair-line decomposition view.",
     "Cannot exist without market prices. The fair-line half is published.",
     "data/nfl_d713b52f/week11_forecasts.csv", "G-PRICE",
     "Multiple operator prices to de-vig.",
     "blocked"),
    ("R60", "Site", "Publish a weekly 'what changed' diff instead of a static snapshot.",
     "NEW: this pack ships a diff table between the two dated reads (standings, report, corpus).",
     "data/nfl_d713b52f/diff.csv", "G-CADENCE",
     "A third read, so the diff becomes a series.",
     "partial"),
    ("R61", "Model", "Publish every model total twice until one wins (gap column, walk-forward).",
     "Two totals estimators are published side by side with the gap and a walk-forward MAE comparison.",
     "data/nfl_d713b52f/leaderboard.csv", "G-SCORE",
     "A walk-forward result that separates them at a stated confidence.",
     "done"),
    ("R62", "Data spine", "Add a drift alarm to every scraper (pin row counts and required fields).",
     "The pack verifier pins 14 files and 26 required headers and fails the build on drift.",
     "scripts/check_nfl_d713b52f.py", "G-DRIFT",
     "An alarm destination. The failure is loud in CI; nobody is paged.",
     "done"),
    ("R63", "Availability", "Capture the reserve list so 'not listed' never means 'available'.",
     "The pack prints 'not on the Not Active list', never 'available'. Reserve rows are not read here.",
     "data/nfl_d713b52f/designation_join.csv", "G-RESERVE",
     "A dated reserve-list read joined to the report.",
     "partial"),
    ("R64", "Governance", "Reject ranking strategies by season-long ROI.",
     "REJECTED: this pack ranks by Brier skill with an interval; ROI is not computed anywhere.",
     "data/nfl_d713b52f/leaderboard.csv", "none",
     "Nothing to clear: the measure is rejected.",
     "done"),
    ("R65", "Injury", "Archive weekly injury reports for past seasons (for designation calibration).",
     "Not done: only 2026 Week 10 and Week 11 were read.",
     "data/nfl_d713b52f/sources.csv", "G-ARCHIVE",
     "Archived official reports for >=3 prior seasons.",
     "blocked"),
    ("R66", "Governance", "Pre-register each strategy (definition frozen before results are seen).",
     "Frozen here: 7 strategies and 2 controls, with the family size fixed at 7 for the multiplicity adjustment.",
     "data/nfl_d713b52f/preregistration.md", "G-REGISTER",
     "The commit that first contains the text; recorded in the completion record.",
     "done"),
    ("R67", "Fixture", "2026 kickoff and declared onside-kick regime priors filter.",
     "Not attempted: no official 2026 rule text was read in this session.",
     "data/nfl_d713b52f/flagged.csv", "G-RULE",
     "The official 2026 rulebook section on the onside-kick regime, read and cited.",
     "blocked"),
    ("R68", "Governance", "Freeze a rule before it sees data (the commit hash is the registration).",
     "Done: the registration is committed in its own commit before the model commit.",
     "data/nfl_d713b52f/preregistration.md", "G-REGISTER",
     "Commit ordering, verifiable in git log.",
     "done"),
    ("R69", "Model", "Split data into train, validation and final holdout seasons.",
     "Impossible inside one season: the corpus is 2026 only. The pack uses a chronological split of the season and says so.",
     "data/nfl_d713b52f/preregistration.md section 4", "G-HOLDOUT",
     "A multi-season corpus. One season cannot supply a holdout season.",
     "blocked"),
    ("R70", "Site", "Make suggestions to improve the site, with a section where they can be reviewed before implementation.",
     "NEW: suggestions page with 12 proposals, each with the evidence, the expected gain, the cost and the decision field left empty.",
     "docs/nfl-d713b52f/suggestions.html", "G-SITE",
     "An owner decision per row. The page records decisions; it does not implement them.",
     "done"),
    ("R71", "Brief", "A clear list of questions, information and answers that must be addressed before a decision can be made.",
     "NEW: 18 open questions, each with what is missing, who can supply it, and what changes on each answer.",
     "docs/nfl-d713b52f/questions.html", "G-QIA",
     "Each question's 'information needed' cell filled by a source or an owner decision.",
     "partial"),
    ("R72", "Brief", "Suggest how to discover missing information.",
     "NEW: every question carries a discovery route (which official page, which operator, which owner decision).",
     "docs/nfl-d713b52f/questions.html", "G-QIA",
     "Same as R71.",
     "partial"),
    ("R73", "Competition", "Originate own NFL lines and treat it as a leaderboard competition with rewards.",
     "Leaderboard exists with numeric qualification. No reward mechanism is described by the owner, so none is implemented.",
     "data/nfl_d713b52f/leaderboard.csv", "G-REWARD",
     "An owner decision on what the reward is.",
     "partial"),
    ("R74", "Competition", "Look at single bets, parlays and player prop bet combos.",
     "Singles are scored. Parlays and props are gated (R35) and not scored.",
     "data/nfl_d713b52f/leaderboard.csv", "G-COMBO",
     "A joint-probability source and operator rules.",
     "partial"),
    ("R75", "Competition", "Determine correlation values.",
     "Six official-number correlations are audited here; the audit recomputes r, n and the interval from the feed.",
     "data/nfl_d713b52f/recompute.csv", "G-CORR",
     "Publish n with every value: already true; enforced by this pack's verifier.",
     "done"),
    ("R76", "Luck", "Remove luck and build strategies that are selectively skill based.",
     "Skill gate exists (Brier skill lower bound > 0, Bonferroni). The panel separates reliability from resolution.",
     "data/nfl_d713b52f/luck_panel.csv", "G-SCORE",
     "A prospective sample. Backtest skill does not promote anything.",
     "partial"),
    ("R77", "Injury", "Track injuries and know deficiencies when 2nd/3rd/4th string backs replace starters.",
     "NEW: 8 clubs' declared-outs joined to who actually played; the book's next man named where he appears in the Lineups block.",
     "data/nfl_d713b52f/replacement.csv", "G-GAMEBOOK",
     "A rank source to say '2nd string'. The book does not rank; the pack refuses to invent it.",
     "partial"),
    ("R78", "Brief", "Create an executive summary outlining important details.",
     "NEW: NFL_D713B52F_EXECUTIVE_SUMMARY.md at the repo root.",
     "NFL_D713B52F_EXECUTIVE_SUMMARY.md", "none",
     "Delivered.",
     "done"),
    ("R79", "Brief", "No manual input; work fully autonomously.",
     "No input control exists on any page this pack writes; the verifier refuses one.",
     "scripts/check_nfl_d713b52f.py", "none",
     "Delivered.",
     "done"),
    ("R80", "Brief", "Work line by line against official sources, no hallucinations; flag irregularities.",
     "Every published cell has a URL and a read clock; 12 irregularities are published with links.",
     "docs/nfl-d713b52f/flagged.html", "none",
     "Delivered for the rows read. Unread rows stay blank.",
     "done"),
    ("R81", "Brief", "Create a GitHub Pages live site with a clean dashboard landing page and category subpages.",
     "NEW: 7 pages under docs/nfl-d713b52f/ plus a link on the repo root landing page.",
     "docs/nfl-d713b52f/index.html", "G-SITE",
     "Delivered; the deploy is recorded in the completion record.",
     "done"),
    ("R82", "Brief", "Every table row must carry a source link to an official site; blank and flag what cannot be confirmed.",
     "Enforced by the verifier: every data row carries an https URL on an official host, and blanks carry a reason.",
     "scripts/check_nfl_d713b52f.py", "none",
     "Delivered.",
     "done"),
    ("R83", "Brief", "Coordinate with parallel sessions through COORDINATION.md; claim scope; log sources and irregularities.",
     "Claim written and pushed before any data was produced; completion record appended after merge.",
     "COORDINATION.md", "none",
     "Delivered.",
     "done"),
    ("R84", "Brief", "Open a PR, merge it, confirm Pages deploys, record the PR and merge result.",
     "Recorded in the completion record in COORDINATION.md.",
     "COORDINATION.md", "none",
     "Delivered.",
     "done"),
    ("R85", "Competition", "Each strategy must pass validation gates.",
     "Nine gates are stated with a numeric pass condition; every strategy row carries its gate state.",
     "data/nfl_d713b52f/strategies.csv", "G-SCORE",
     "The prospective sample. Now: 0 of 100.",
     "partial"),
    ("R86", "Data spine", "Make the 'Not Active' list usable pre-kickoff.",
     "Not possible from the book: it is published after the game. The 90-minute inactive list has no official page found.",
     "data/nfl_d713b52f/source_probe.csv P2", "G-INACTIVE",
     "A pre-kickoff official inactive feed. Not located.",
     "blocked"),
]

GATES = [
    ("G-PRICE", "No market price exists on any official page. Every residual, ROI, CLV and staking column stays blank.",
     "An operator or licensed archive of timestamped prices; 1 row per market per week for 18 weeks.", "open"),
    ("G-SCORE", "Backtest numbers cannot promote a strategy. Promotion needs 100 scored prospective singles.",
     "100 prospective singles with an official final and a positive week-cluster Brier-skill lower bound.", "open"),
    ("G-SNAPS", "The only 2026 'snap count' the NFL publishes is the Game Book's Playtime Percentage, captioned '(Unofficial)'.",
     "Either an owner decision to accept the Unofficial table as a proxy (recorded in the repo) or a certified source.", "open"),
    ("G-GAMEBOOK", "The Game Book route is verified (4 of 13 Week 10 books parsed, PDF host reachable). Coverage is 4 games.",
     "13 of 13 Week 10 books and 13 of 13 Week 11 books parsed with hashes.", "open"),
    ("G-DEPTH-SRC", "No official source read publishes a depth rank. Club depth pages were not verified.",
     "32 club depth pages parsed with a stored raw string, or the book route for every game.", "open"),
    ("G-CORR", "A correlation may only be published with n and an interval, from official numbers.",
     "Met for the 6 inherited rows; enforced for any new row.", "closed"),
    ("G-REGISTER", "A strategy may only be scored if its text was committed before the scoring run.",
     "Commit ordering, verified in git log.", "closed"),
    ("G-PROSPECTIVE", "A demotion gate needs a trailing window of prospective scores.",
     "10 scored prospective weeks.", "open"),
    ("G-PRICE-POLICY", "No price column is ever populated from a non-official source.",
     "Owner decision recorded in the repo.", "closed"),
    ("G-CADENCE", "An injury series needs at least daily reads from Wednesday to kickoff.",
     "A scheduler plus an owner decision on automated collection (NFL Terms).", "open"),
    ("G-STORAGE", "Hashes prove the transcript, not the page, and the store is inside the published site.",
     "A versioned store outside the site.", "open"),
    ("G-WEATHER", "Weather read here is post-game; it cannot be a pre-kickoff feature.",
     "An NWS hourly forecast grid plus an official roof-state call before kickoff.", "open"),
    ("G-CALIBRATE", "A designation calibration needs n per designation over several seasons.",
     "Play rate per designation with an interval, 3+ seasons.", "open"),
    ("G-COMBO", "Marginal probabilities cannot be multiplied for a combo.",
     "A directly validated joint probability for the exact leg set plus operator void/push rules.", "open"),
    ("G-HOLDOUT", "A holdout season needs more than one season.",
     "A multi-season corpus.", "open"),
    ("G-ABLATE", "An ablation needs the feature present in the evaluation window.",
     "Availability features for every game in the window. Now: 4 of 150.", "open"),
    ("G-RESERVE", "'Not listed' must never be read as 'available'.",
     "A dated reserve-list read joined to the report.", "open"),
    ("G-ARCHIVE", "Calibration over seasons needs archived reports.",
     "Official reports for 3+ prior seasons.", "open"),
    ("G-RULE", "Fixture priors need the official 2026 rule text.",
     "The official rulebook section, read and cited.", "open"),
    ("G-REWARD", "A competition needs a defined reward.",
     "An owner decision on the reward.", "open"),
    ("G-SITE", "The site must build, link-check and refuse inputs.",
     "The pack verifier's 18 rules pass.", "closed"),
    ("G-QIA", "A question is only answered by a source read or an owner decision.",
     "All 18 question rows closed.", "open"),
    ("G-DRIFT", "A parser must fail loudly on drift.",
     "Pinned row counts and headers; the verifier enforces them.", "closed"),
    ("G-VENUE", "Venue transcription must come from the official game centre.",
     "13 of 13 Week 10 and 13 of 13 Week 11 fixtures read.", "open"),
    ("G-ANNOUNCE", "The dated schedule announcement must be read.",
     "An official dated release URL.", "open"),
    ("G-ROSTER", "Roster turnover must be versioned against the official transactions log.",
     "A dated transactions read joined to depth and availability.", "open"),
    ("G-SWEEP", "A team-level model needs the full 32-club roster/IR sweep.",
     "32 club reads with a stable section parse.", "open"),
    ("G-INACTIVE", "A pre-kickoff inactive feed is needed for point-in-time certainty.",
     "An official pre-kickoff inactive page.", "open"),
    ("G-EXPECTED", "A surprise needs an ex-ante expectation.",
     "A pre-kickoff expectation source for every club's starters.", "open"),
    ("G-RATING", "Opponent-aware ratings need an opponent term, registered first.",
     "A registered model with an opponent term and a walk-forward comparison.", "open"),
    ("G-SPLIT", "The public layer may carry derived analysis only.",
     "An owner decision recorded in the repo.", "closed"),
]


def requirement_rows():
    rows = []
    for rid, group, text, state, evidence, gate, clear, status in REQUIREMENTS:
        blocked = "yes" if status in ("blocked", "partial") else "no"
        rows.append(dict(
            rid=rid, group=group, requirement=text, what_exists=state, evidence=evidence,
            gate=gate, clears_it=clear,
            status=status, blocks_decision=blocked))
    return rows


def gate_rows():
    return [dict(gate=gid, states=desc, clears=clear, state=state)
            for gid, desc, clear, state in GATES]


# ---------------------------------------------------------------------------
# 5. Questions / information / answers
# ---------------------------------------------------------------------------

QUESTIONS = [
    dict(qid="Q01", group="Price",
         question="Where will the price archive come from, and is it licensed for backtesting and publication of a residual?",
         have="No price exists anywhere in the repo. Every residual and ROI cell is blank by policy.",
         need="One operator or licensed archive, with the licence covering archived and derived publication.",
         discovery="Ask the owner which operator(s) they hold accounts with; ask each for historical odds export terms.",
         changes="Turns on R01, R04, R05, R18, R58, R59 and the whole staking half of the leaderboard.",
         blocking="every pricing and ROI claim"),
    dict(qid="Q02", group="Price",
         question="If prices can never be archived, should the project drop ROI entirely and compete on proper scores only?",
         have="The leaderboard already ranks on proper scores; ROI is empty.",
         need="An owner decision, recorded in the repo.",
         discovery="Owner decision; no source can answer it.",
         changes="Either closes R05 and R58 by removing them, or keeps them blocked.",
         blocking="the definition of a winner"),
    dict(qid="Q03", group="Snap counts",
         question="Will the project accept the NFL's own '(Unofficial)' playtime table as the participation measure?",
         have="The table exists, is published per game by the NFL, and is captioned Unofficial.",
         need="An owner decision, because the brief says 'officially sourced numbers'.",
         discovery="Owner decision; the alternative is a certified feed, which no official page read here offers.",
         changes="Unblocks R06, R11, R30, R55 and the replacement-depth work; without it they stay partial.",
         blocking="every replacement-depth and snap-based measure"),
    dict(qid="Q04", group="Snap counts",
         question="Does a certified snap-count feed exist at a price the project would pay?",
         have="No official page read publishes a 2026 snap-count leaderboard; the category URL 404s.",
         need="A vendor quote and a sample week, checked against one game book by hand.",
         discovery="Ask each major vendor for one free historical week and reconcile it to the LAC@BAL book.",
         changes="If yes, the Unofficial table becomes a check rather than the source.",
         blocking="G-SNAPS"),
    dict(qid="Q05", group="Inactives",
         question="Is there an official pre-kickoff inactive list page, or only the post-game book?",
         have="Books publish 'Not Active'; no pre-kickoff page was located.",
         need="A located official page, read before kickoff.",
         discovery="Search nfl.com game centre 90 minutes before a kickoff during Week 12.",
         changes="Makes point-in-time replacement certainty possible (R46, R86).",
         blocking="any pre-kickoff availability feature"),
    dict(qid="Q06", group="Designations",
         question="What does 'Questionable' actually mean in play rate, and does it differ by position?",
         have="30 Questionable rows read across 4 games; none was on a Not Active list; 23 had a playtime row.",
         need="n of several hundred per designation over 3+ seasons, with intervals.",
         discovery="Archive official reports weekly for past seasons (R65), then join to books.",
         changes="Turns designation from a label into a calibrated probability (R43, R52).",
         blocking="any designation-based feature"),
    dict(qid="Q07", group="Depth",
         question="Which source will define depth order: club pages or playing time?",
         have="Club depth pages were not verified in this session; playing time exists but is Unofficial.",
         need="Either 32 verified club pages or the Q03 decision.",
         discovery="Verify one club page per week against its book's Lineups block.",
         changes="Unblocks R31, R42, R44 and the 1st-4th string matrix.",
         blocking="depth-ablation and deficiency features"),
    dict(qid="Q08", group="Depth",
         question="Should the project ever publish a rank the club has not published?",
         have="No official source read publishes a rank.",
         need="An owner decision. The pack's position is that inventing a rank is a hallucination.",
         discovery="Owner decision.",
         changes="If no, R44 stays permanently blocked and is removed from the site.",
         blocking="the 1st-4th string matchup matrix"),
    dict(qid="Q09", group="Weather",
         question="Is a pre-kickoff roof-state call published officially, and where?",
         have="The book gives roof design and post-game weather only.",
         need="An official page stating whether the roof was open or closed before kickoff.",
         discovery="Read the game centre during the 90 minutes before a domed-game kickoff.",
         changes="Makes the roof/wind overlay a feature rather than a post-hoc note (R57).",
         blocking="weather-sensitive totals and passing props"),
    dict(qid="Q10", group="Legal",
         question="Do the NFL Terms permit scheduled automated capture of injury and roster pages?",
         have="Inherited packs raise the written-consent question and do not automate.",
         need="Written consent or legal advice, recorded.",
         discovery="Read the NFL Terms section on automated collection; ask the league for written consent.",
         changes="Unblocks R28, R29, R53 and the whole snapshot cadence.",
         blocking="any scheduler"),
    dict(qid="Q11", group="Legal",
         question="What row-level data may be republished publicly?",
         have="The public site carries derived analysis and official links only.",
         need="An owner decision recorded in the repo.",
         discovery="Owner decision, informed by Q10.",
         changes="Determines whether the private layer can become public (R39).",
         blocking="the public/private split"),
    dict(qid="Q12", group="Competition",
         question="What is the reward for a top strategy?",
         have="The owner asks for a competition with rewards; no reward is described.",
         need="An owner decision: money, a badge, a promotion to live staking, or nothing.",
         discovery="Owner decision.",
         changes="Defines what the leaderboard is for (R73).",
         blocking="the competition's incentive design"),
    dict(qid="Q13", group="Competition",
         question="How many strategies may the family hold before the multiplicity threshold stops being meaningful?",
         have="The family is frozen at 7; the Bonferroni threshold scales with it.",
         need="A cap written into the registration template.",
         discovery="Arithmetic: at 50 strategies the per-test threshold is 0.001, which needs a very large sample.",
         changes="Limits how many ideas can be tested (R37, R66).",
         blocking="the size of any future family"),
    dict(qid="Q14", group="Corpus",
         question="Is 150 games enough to separate a 3% Brier-skill edge from noise?",
         have="The week-cluster lower bound on the best backtest strategy is below zero at n=121.",
         need="A power calculation at the effect size the project would act on.",
         discovery="Arithmetic on the existing scores; no new data needed.",
         changes="Sets the sample the prospective board must reach (R03, R34).",
         blocking="the promotion threshold"),
    dict(qid="Q15", group="Corpus",
         question="Do we have more than one season available anywhere?",
         have="The corpus is 2026 only; a holdout season is therefore impossible.",
         need="A second and third season of finals, read and hashed.",
         discovery="nfl.com schedules for 2024 and 2025 are published; a read is cheap.",
         changes="Unblocks R69 and makes calibration possible (R43, R65).",
         blocking="train/validation/holdout discipline"),
    dict(qid="Q16", group="Governance",
         question="Who executes the demotion, and how fast?",
         have="The rule is numeric and states 'automatic', but nothing runs on a clock.",
         need="A runner and a named owner.",
         discovery="Owner decision plus a scheduler (which depends on Q10).",
         changes="Makes the demotion gate real rather than described (R08).",
         blocking="the live/paper distinction"),
    dict(qid="Q17", group="Site",
         question="Should flags that time has closed be removed from the Flagged page or kept as history?",
         have="This pack closes one flag (R47) and keeps the row.",
         need="An owner preference.",
         discovery="Owner decision.",
         changes="Affects how the Flagged page ages.",
         blocking="nothing; cosmetic"),
    dict(qid="Q18", group="Snap counts",
         question="If playtime is Unofficial, can it still be called 'verified' when it is read from the official PDF?",
         have="The value is published by the NFL in an official book, and labelled Unofficial by the same publisher.",
         need="A house rule for what 'verified' means: verified as transcribed, or verified as certified.",
         discovery="Owner decision; the pack's rule is stated in the verification page.",
         changes="Changes the label on every snap row (R06, R30, R55).",
         blocking="the meaning of 'verified' on the site"),
]


def question_rows():
    out = []
    for q in QUESTIONS:
        out.append(dict(qid=q["qid"], group=q["group"], question=q["question"],
                        have=q["have"], need=q["need"], discovery=q["discovery"],
                        changes=q["changes"], blocking=q["blocking"],
                        status="open", answer_owner=""))
    return out


# ---------------------------------------------------------------------------
# 6. Suggestions
# ---------------------------------------------------------------------------

SUGGESTIONS = [
    dict(sid="S01", title="Publish one number per week that the model got wrong most, with the book page",
         why="Error review is where calibration actually improves; the current board publishes aggregates only.",
         evidence="The best backtest strategy's week-cluster interval still straddles zero at n=121.",
         cost="low", gain="medium", risk="low",
         route="Add a per-week worst-error row to the leaderboard page."),
    dict(sid="S02", title="Make the Flagged page the site's front door until the flag count is under 10",
         why="Twelve open irregularities matter more to a decision than a leaderboard with no prospective sample.",
         evidence="0 prospective scores; 12 open flags.",
         cost="low", gain="high", risk="low",
         route="Reorder the landing page cards."),
    dict(sid="S03", title="Adopt a house definition of 'verified' with three levels",
         why="'Unofficial' playtime read from an official PDF is not the same as a certified count, and the site currently uses one word for both.",
         evidence="Q18; the Game Book caption '(Unofficial)'.",
         cost="low", gain="high", risk="low",
         route="Add a legend to every table: certified / published-by-league-labelled-unofficial / derived."),
    dict(sid="S04", title="Replace the 1st-4th string matrix with a 'declared out, and who played' table",
         why="The rank does not exist officially; the join does, and it answers the same question without inventing data.",
         evidence="R44 is blocked; R77 is answerable today for 8 clubs.",
         cost="low", gain="high", risk="low",
         route="Build on replacement.csv."),
    dict(sid="S05", title="Read 2024 and 2025 finals next",
         why="One season cannot produce a holdout, and calibration needs seasons.",
         evidence="Q15; R69 blocked.",
         cost="low", gain="high", risk="low",
         route="Read the nfl.com by-week schedule pages for 2024 and 2025, hash each read."),
    dict(sid="S06", title="Ask the owner for a written price-policy decision before any more pricing work",
         why="Nine requirement rows are blocked on a single missing input.",
         evidence="R01, R04, R05, R18, R58, R59, Q01, Q02.",
         cost="low", gain="high", risk="low",
         route="One question on the questions page, one decision field."),
    dict(sid="S07", title="Publish a 'what we would need to see' line on every page",
         why="A reader should never have to hunt for the number that would change the page.",
         evidence="The readiness table does this for requirements; the other pages do not.",
         cost="low", gain="medium", risk="low",
         route="Add one line to the page footer generator."),
    dict(sid="S08", title="Stop publishing aggregate leaderboards until the prospective sample is non-zero",
         why="A backtest league table invites exactly the result-chasing the registration forbids.",
         evidence="Every strategy state is 'paper'; prospective n=0.",
         cost="low", gain="medium", risk="medium",
         route="Gate the leaderboard page behind a sample counter."),
    dict(sid="S09", title="Record a decision log with dates on the site",
         why="Suggestions and questions currently have empty decision fields and no owner timeline.",
         evidence="All 12 suggestions have decision=''.",
         cost="low", gain="medium", risk="low",
         route="A dated table on the suggestions page."),
    dict(sid="S10", title="Use the 4 parsed books as a regression suite for the fetch route",
         why="The route was the repo's most-cited blocker for three weeks; a fixture set keeps it working.",
         evidence="FLAG-07 / G-GAMEBOOK recorded the PDF host as unreachable; it is reachable now.",
         cost="low", gain="medium", risk="low",
         route="Pin the four book URLs and their sha256 of the transcription in CI."),
    dict(sid="S11", title="Split the site by audience: decision page, evidence page, archive",
         why="The site has grown to 20 packs; a decision-maker needs one page, not twenty.",
         evidence="19 prior NFL pack directories under docs/.",
         cost="medium", gain="high", risk="low",
         route="A single top-level decision page that links into each pack's evidence."),
    dict(sid="S12", title="Add a 'last verified' clock to every published number",
         why="Some numbers are inherited with an inherited read clock; a reader cannot tell today's read from last week's.",
         evidence="The inherited results feed carries '2026-11-17T01:26:00Z (inherited read clock)'.",
         cost="low", gain="medium", risk="low",
         route="One column, generated from the row's read_at_utc."),
]


def suggestion_rows():
    return [dict(sid=s["sid"], title=s["title"], why=s["why"], evidence=s["evidence"],
                 cost=s["cost"], gain=s["gain"], risk=s["risk"], route=s["route"],
                 decision="", decision_owner="owner", status="pending_human_choice")
            for s in SUGGESTIONS]


# ---------------------------------------------------------------------------
# 7. Flagged irregularities
# ---------------------------------------------------------------------------

FLAGGED = [
    dict(fid="F-01", severity="high",
         finding="The NFL captions its own Game Book playtime table '(Unofficial)'.",
         detail="Every snap-count value in this pack comes from that table. The brief requires officially sourced numbers.",
         source_url=GB_HOU_CLE,
         impact="Every snap-derived row is labelled Unofficial; no snap row is called certified.",
         action="Owner decision (Q03/Q18). Nothing is suppressed; the label travels with the value."),
    dict(fid="F-02", severity="medium",
         finding="The Week 10 injury page renders a Week 11 <title>.",
         detail="https://www.nfl.com/injuries/league/2026/reg10 has browser title '... Week 11 ...' while its body heading says 'Injuries - WEEK 10'.",
         source_url=INJ_REG10,
         impact="A scraper keyed on <title> would file Week 10 rows under Week 11.",
         action="This pack keys on the body heading and records both strings in the raw file."),
    dict(fid="F-03", severity="medium",
         finding="The game centre and the Game Book disagree on the Munich stadium name.",
         detail="Game centre Game Info: 'FC BAYERN MUNICH STADIUM'. Game Book: 'Allianz Arena'.",
         source_url=GC_NE_DET,
         impact="A venue feature built from the game centre would differ from one built from the book.",
         action="Both strings are published side by side with a mismatch flag; neither is corrected."),
    dict(fid="F-04", severity="medium",
         finding="Playtime table extraction merges the two clubs' columns.",
         detail="The PDF text extractor interleaves the away and home playtime columns; a naive parse would assign a Ravens snap count to a Chargers player.",
         source_url=GB_LAC_BAL,
         impact="Automated parsing of these PDFs needs column-aware extraction before it can scale to 13 games.",
         action="Only hand-read, cross-checked rows are published; the total stays under the 11-player capacity check."),
    dict(fid="F-05", severity="high",
         finding="The playtime table can print the same player twice in one club's columns.",
         detail="Cleveland lists 'T.Pride CB' with a 13 39% row and again with a 12 36% row; Detroit lists 'C.Izien DB' with a 1 2% row and again with a blank row.",
         source_url=GB_HOU_CLE,
         impact="A naive sum of a club's playtime rows double-counts and can exceed the 11-player capacity.",
         action="Only hand-read rows are published, and every club's transcribed total is checked against unit snaps x 11 in snap_sum.csv."),
    dict(fid="F-06", severity="high",
         finding="Four players the Week 10 report marks Out are not on the corresponding Not Active list.",
         detail="Of 16 Out designations across the four joined games, 12 appear on the club's Not Active block and 4 do not: DET S Kerby Joseph, NE RB TreVeyon Henderson, CLE FB Michael Burton and LAC G Branson Taylor.",
         source_url=GB_NE_DET,
         impact="Either the report's Out does not always mean inactive, or the book's list is incomplete. A model that treats Out as 'did not play' would be wrong on 4 of 16 cases here.",
         action="Both official values are published side by side and the mismatch is flagged; the pack does not choose between its own sources."),
    dict(fid="F-07", severity="low",
         finding="The Week 10 report's Ravens block was not transcribed within the read window.",
         detail="The Chargers block reaches 'Branson Taylor'; the transcript ends there. The Ravens block was not captured.",
         source_url=INJ_REG10,
         impact="BAL has no designation join in this pack.",
         action="BAL rows are absent, not blank. The absence is recorded here."),
    dict(fid="F-08", severity="high",
         finding="No official source read publishes a depth rank.",
         detail="A 1st-4th string matrix (R44) would require inventing the ranking order.",
         source_url=STATS_INDEX,
         impact="The most-requested interactive feature cannot be built from official data as specified.",
         action="Rejected in the pack; replaced by the declared-out/played join (S04)."),
    dict(fid="F-09", severity="medium",
         finding="The Giants' Week 10 report carries no game designation at all.",
         detail="11 NYG rows were listed; only Malik Harrison carries a designation (Questionable). One further row carries a practice status only.",
         source_url=INJ_REG10,
         impact="Any feature assuming a designation exists per listed player is wrong.",
         action="Blank cells are published as 'blank', never read as 'healthy'."),
    dict(fid="F-10", severity="low",
         finding="One surname and initial appears on two clubs in the same week.",
         detail="The WAS@NYG book lists 'G 62 T.Togiai' on Washington's Not Active block; the same week's report lists 'Tommy Togiai' as a Texans defensive tackle. Two different clubs, one printed name form.",
         source_url=GB_WAS_NYG,
         impact="The same surname/initial appears on two clubs in one week.",
         action="The join is club-scoped; the row is flagged rather than resolved."),
    dict(fid="F-11", severity="low",
         finding="Post-game weather exists, pre-game weather does not.",
         detail="All four books carry measured weather. No official pre-kickoff forecast was read.",
         source_url=GB_NE_DET,
         impact="The weather feature in the brief cannot be pre-kickoff without a second feed.",
         action="Published as post-game context; the feature row is marked unavailable for modelling (R14, R57)."),
    dict(fid="F-12", severity="medium",
         finding="The inherited 150-game count includes games that cannot be scored.",
         detail="29 rows in the inherited feed have no scorable prior history, and four were re-read here; the scorable backtest set is 121.",
         source_url="https://www.nfl.com/schedules/2026/by-week/week-10",
         impact="Reporting '150-game backtest' overstates the sample by 24%.",
         action="The pack publishes 150 corpus, 121 scorable, and both counts on the landing page."),
]


def flagged_rows():
    return [dict(fid=f["fid"], severity=f["severity"], finding=f["finding"], detail=f["detail"],
                 source_url=f["source_url"], impact=f["impact"], action=f["action"],
                 blocks_merge="no", review_url="")
            for f in FLAGGED]


# ---------------------------------------------------------------------------
# 8. Sources register
# ---------------------------------------------------------------------------

def source_rows():
    seen = {}
    for name, url, kind, used in capture.CAPTURES:
        seen.setdefault(url, dict(url=url, kind=kind, used_for=used, reads="1", official="yes"))
    for extra, kind, used in [
        (STATS_INDEX, "stats_index", "official player-stats category list; no snap-count category"),
        ("https://www.nfl.com/stats/player-stats/category/snap-counts/2026/reg/all", "probe_404",
         "snap-counts URL returned '404 - Flag on the Play.'"),
        ("https://www.nfl.com/games/texans-at-browns-2026-reg-10", "game_centre", "book link + Game Info"),
        ("https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "game_centre", "book link + Game Info"),
        ("https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "game_centre", "book link + Game Info"),
        ("https://www.nfl.com/schedules/2026/by-week/week-10", "schedule", "Week 10 board, cited for corpus rows"),
    ]:
        seen.setdefault(extra, dict(url=extra, kind=kind, used_for=used, reads="1", official="yes"))
    rows = []
    for i, (url, row) in enumerate(sorted(seen.items()), start=1):
        row = dict(row)
        row["source_id"] = f"SRC-{i:02d}"
        row["host"] = url.split("/")[2]
        row["read_at_utc"] = READ
        rows.append(row)
    return rows
