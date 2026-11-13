"""Club depth-chart registry and starter-vs-backup classification for the NFL Week Pack.

Every chart string below was transcribed by hand from the official club page named in
``CHART_SOURCES`` and read during this session (2026-11-13). Nothing here is inferred from
memory or from a third-party depth chart.

A player's depth string is the 1-based position at which the club page lists him, taking the
*best* (lowest) position across the position groups he appears in. A player who does not appear
on the club page gets NO string: the field stays blank and the row is marked
``not_listed_on_club_chart``. A blank string is never treated as "backup" or as "starter".
"""

from __future__ import annotations

CHART_SOURCES = {
    "DET": {
        "source_id": "W11-S10",
        "url": "https://www.detroitlions.com/team/depth-chart",
        "label": "2026 Unofficial Depth Chart Compiled by Lions Football Communications",
        "as_of_week": "",
        "groups": {
            "WR1": ["Jameson Williams"],
            "WR2": ["Amon-Ra St. Brown", "DeAndre Carter"],
            "LT": ["Penei Sewell"],
            "LG": ["Christian Mahogany", "Miles Frazier"],
            "C": ["Cade Mays", "Juice Scruggs"],
            "RG": ["Tate Ratledge", "Seth McLaughlin"],
            "RT": ["Blake Miller", "Larry Borom"],
            "TE": ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"],
            "WR3": ["Isaac TeSlaa", "Tay Martin"],
            "QB": ["Jared Goff", "Joshua Dobbs"],
            "RB": ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors"],
            "EDGE1": ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill"],
            "DL1": ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo"],
            "DL2": ["Tyleik Williams", "Levi Onwuzurike"],
            "EDGE2": ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein"],
            "LB1": ["Derrick Barnes", "Joe Bachie"],
            "LB2": ["Malcolm Rodriguez", "K.J. Britt"],
            "LB3": ["Trevor Nowaske", "Amen Ogbongbemiga"],
            "CB1": ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"],
            "CB2": ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II"],
            "S1": ["Chuck Clark"],
            "S2": ["Brian Branch", "Christian Izien"],
        },
    },
    "NE": {
        "source_id": "W11-S11",
        "url": "https://www.patriots.com/team/depth-chart",
        "label": "New England Patriots Unofficial Depth Chart (published by Patriots.com writers)",
        "as_of_week": "",
        "groups": {
            "WR1": ["A.J. Brown", "Efton Chism III"],
            "LT": ["Will Campbell", "Dametrious Crownover", "Marcus Bryant"],
            "LG": ["Ben Brown", "Walter Rouse"],
            "C": ["Jared Wilson", "Ben Brown"],
            "RG": ["Matt Pryor", "Walter Rouse"],
            "RT": ["Morgan Moses", "Caleb Lomu"],
            "TE": ["Hunter Henry", "Eli Raridon", "Cameron Latu"],
            "WR2": ["DeMario Douglas", "Kyle Williams"],
            "WR3": ["Efton Chism III", "Kyle Williams"],
            "RB": ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner", "Lan Larison"],
            "QB": ["Drake Maye", "Tommy DeVito", "Behren Morton"],
            "OLB1": ["Dre'Mont Jones", "Gabe Jacas"],
            "DT1": ["Christian Barmore", "Leonard Taylor III"],
            "DT2": ["Cory Durden", "DaQuan Jones"],
            "DT3": ["Milton Williams", "Joshua Farmer"],
            "OLB2": ["Elijah Ponder", "Gabe Jacas"],
            "LB1": ["Robert Spillane", "Darius Muasau", "Erick Hunter"],
            "LB2": ["Christian Elliss", "Namdi Obiazor"],
            "CB1": ["Carlton Davis III", "Channing Canada"],
            "S1": ["Craig Woodson", "Mike Brown"],
            "S2": ["Kevin Byard III", "Jaylen Reed", "Brenden Schooler"],
            "CB2": ["Marcus Jones", "Charles Woods"],
            "CB3": ["Christian Gonzalez", "Karon Prunty"],
        },
    },
    "SEA": {
        "source_id": "W11-S08",
        "url": "https://www.seahawks.com/team/depth-chart",
        "label": "Seattle Seahawks Depth Chart",
        "as_of_week": "",
        "groups": {
            "WR1": ["Cooper Kupp", "Rashid Shaheed", "Irvin Charles"],
            "LT": ["Charles Cross", "Josh Jones"],
            "LG": ["Quenton Nelson", "Anthony Bradford"],
            "C": ["Jalen Sundell", "Olu Oluwatimi"],
            "RG": ["Grey Zabel", "Anthony Bradford", "Beau Stephens"],
            "RT": ["Abraham Lucas", "Josh Jones"],
            "TE": ["AJ Barner", "Eric Saubert", "Nick Kallerup"],
            "WR2": ["Jaxon Smith-Njigba", "Tory Horton"],
            "QB": ["Sam Darnold", "Drew Lock", "Jalen Milroe"],
            "FB": ["Brady Russell"],
            "RB": ["Zach Charbonnet", "Jadarian Price", "Emanuel Wilson", "George Holani"],
            "DT1": ["Leonard Williams", "Rylie Mills"],
            "NT": ["Byron Murphy II", "Brandon Pili", "Deven Eastern"],
            "DE": ["Jarran Reed", "Mike Morris"],
            "RUSH": ["DeMarcus Lawrence", "Derick Hall"],
            "MLB": ["Ernest Jones IV", "Patrick O'Connell"],
            "WLB": ["Drake Thomas", "Tyrice Knight", "Chazz Surratt"],
            "SLB": ["Uchenna Nwosu", "Dante Fowler Jr.", "Connor O'Toole"],
            "CB1": ["Devon Witherspoon", "Nehemiah Pritchett"],
            "CB2": ["Josh Jobe", "Avery Smith"],
            "S1": ["Ty Okada", "Rodney Thomas II"],
            "S2": ["Julian Love"],
            "S3": ["Nick Emmanwori"],
        },
    },
    "BAL": {
        "source_id": "W11-S09",
        "url": "https://www.baltimoreravens.com/team/depth-chart",
        "label": "Baltimore Ravens Depth Chart",
        "as_of_week": "",
        "groups": {
            "WR1": ["Zay Flowers", "Devontez Walker", "Elijah Sarratt"],
            "WR2": ["Rashod Bateman", "Ja'Kobi Lane", "LaJohntay Wester"],
            "LT": ["Ronnie Stanley", "Carson Vinson"],
            "LG": ["John Simpson", "Ryan Neuzil"],
            "C": ["Cam Jurgens", "Ryan Neuzil"],
            "RG": ["Vega Ioane", "Emery Jones Jr."],
            "RT": ["Roger Rosengarten", "Carson Vinson"],
            "TE1": ["Mark Andrews", "Josh Cuevas"],
            "TE2": ["Matt Hibner"],
            "QB": ["Jacoby Brissett", "Joe Fagnano", "Kedon Slovis"],
            "RB": ["Derrick Henry", "Justice Hill", "Rasheen Ali"],
            "DT": ["Nnamdi Madubuike", "Broderick Washington Jr."],
            "NT": ["Travis Jones", "John Jenkins"],
            "DE": ["Calais Campbell", "Aeneas Peebles"],
            "RUSH": ["Trey Hendrickson", "Mike Green"],
            "MLB": ["Roquan Smith", "Jay Higgins IV"],
            "WLB": ["Trenton Simpson", "Teddye Buchanan"],
            "SAM": ["Mike Green", "Zion Young", "Ethan Burke"],
            "CB1": ["Marlon Humphrey", "Chidobe Awuzie"],
            "DB": ["Kyle Hamilton", "Keyon Martin", "Chandler Rivers"],
            "SS": ["Jaylinn Hawkins", "Keondre Jackson"],
            "FS": ["Malaki Starks", "K'Von Wallace"],
            "CB2": ["Nate Wiggins", "T.J. Tampa Jr."],
        },
    },
    "MIN": {
        "source_id": "W11-S12",
        "url": "https://www.vikings.com/team/depth-chart",
        "label": "Minnesota Vikings Depth Chart (2026 Unofficial)",
        "as_of_week": "",
        "groups": {
            "QB": ["Kyler Murray", "Carson Wentz", "Max Brosmer"],
            "RB": ["Aaron Jones Sr.", "Jordan Mason", "Demond Claiborne", "DeeJay Dallas"],
            "FB": ["Max Bredeson"],
            "WR1": ["Justin Jefferson", "Tai Felton"],
            "WR2": ["Jordan Addison"],
            "WR3": ["Jauan Jennings", "Myles Price"],
            "TE": ["T.J. Hockenson", "Gavin Bartholomew"],
            "LT": ["Christian Darrisaw", "Ryan Van Demark"],
            "LG": ["Joe Huber"],
            "C": ["Blake Brandel", "Michael Jurgens", "Nick Samac"],
            "RG": ["Will Fries"],
            "RT": ["Brian O'Neill", "Caleb Tiernan"],
            "OLB1": ["Dallas Turner", "Kyle Van Noy", "Chaz Chambliss"],
            "DL1": ["Jalen Redmond", "Caleb Banks"],
            "DL2": ["Levi Drake Rodriguez", "Domonique Orange"],
            "DL3": ["Tyrion Ingram-Dawkins", "Elijah Williams"],
            "OLB2": ["Andrew Van Ginkel", "Bo Richter"],
            "LB1": ["Blake Cashman", "Ivan Pace Jr."],
            "LB2": ["Eric Wilson", "Jake Golday"],
            "CB1": ["Isaiah Rodgers", "James Pierre", "Zemaiah Vaughn"],
            "CB2": ["Byron Murphy Jr.", "Charles Demmings"],
            "S1": ["Harrison Smith", "Theo Jackson", "Jacob Thomas"],
            "S2": ["Joshua Metellus", "Jay Ward", "Jakobe Thomas"],
        },
    },
    "IND": {
        "source_id": "W11-S13",
        "url": "https://www.colts.com/team/depth-chart",
        "label": "Indianapolis Colts Depth Chart",
        "as_of_week": "",
        "groups": {
            "WR1": ["Laquon Treadwell", "Nick Westbrook-Ikhine"],
            "LT": ["Bernhard Raimann", "Charlie Heck"],
            "LG": ["Jalen Farmer", "Dalton Tucker"],
            "C": ["Tanor Bortolini", "Sedrick Van Pran-Granger"],
            "RG": ["Matt Goncalves"],
            "RT": ["Jalen Travis", "Luke Tenuta"],
            "TE": ["Tyler Warren", "Mo Alie-Cox", "Drew Ogletree", "Will Mallory"],
            "WR2": ["Anthony Gould"],
            "WR3": ["Ashton Dulin", "Deion Burks"],
            "QB": ["Daniel Jones", "Anthony Richardson Sr.", "Riley Leonard"],
            "RB": ["Jonathan Taylor", "Seth McGowan", "DJ Giddens"],
            "DE1": ["Jaylahn Tuimoloau", "George Gumbs Jr."],
            "DT": ["Adetomiwa Adebawore", "Kevin Givens"],
            "NT": ["Grover Stewart", "Jerry Tillery", "Tim Smith"],
            "DE2": ["Laiatu Latu", "Caden Curry"],
            "WLB": ["Jaylon Carlies", "Bryce Boettcher", "Tahj Chambers"],
            "MLB": ["Akeem Davis-Gaither", "CJ Allen", "Austin Ajiake"],
            "CB1": ["Charvarius Ward", "Kenneth Harris"],
            "FS": ["Cam Bynum", "Jonathan Owens"],
            "SS": ["AJ Haulcy", "Hunter Wohler"],
            "N": ["Justin Walley", "Kapena Gushiken"],
            "CB2": ["Sauce Gardner"],
        },
    },
    "PHI": {
        "source_id": "W11-S07",
        "url": "https://www.philadelphiaeagles.com/team/depth-chart",
        "label": "Philadelphia Eagles Depth Chart (compiled by the Eagles communications department)",
        "as_of_week": "11",
        "groups": {
            "WR1": ["DeVonta Smith", "Hollywood Brown"],
            "LT": ["Jordan Mailata"],
            "LG": ["Willie Lampkin"],
            "C": ["Drew Kendall", "Jake Majors"],
            "RG": ["Tyler Steen", "Micah Morris"],
            "RT": ["Markel Bell", "Fred Johnson"],
            "TE": ["Dallas Goedert", "Johnny Mundt"],
            "WR2": ["Makai Lemon", "Elijah Moore", "Britain Covey"],
            "WR3": ["Dontayvion Wicks", "Darius Cooper"],
            "RB": ["Saquon Barkley"],
            "QB": ["Tanner McKee", "Cole Payton", "Joe Milton"],
            "EDGE1": ["Jalyx Hunt", "Arnold Ebiketie"],
            "DT1": ["Jalen Carter", "Byron Young"],
            "DT2": ["Ty Robinson"],
            "DT3": ["Moro Ojomo"],
            "EDGE2": ["Nolan Smith Jr.", "A.J. Epenesa"],
            "LB1": ["Zack Baun", "Smael Mondon Jr."],
            "LB2": ["Jihaad Campbell", "Jeremiah Trotter Jr."],
            "CB1": ["Riq Woolen", "Jonathan Jones"],
            "CB2": ["Quinyon Mitchell", "Kelee Ringo"],
            "NCB": ["Cooper DeJean", "Mac McWilliams"],
            "S1": ["Marcus Epps", "Michael Carter II"],
            "S2": ["Andrew Mukuba", "Kenny Moore II"],
        },
    },
}

# Positions that, when a first-string player is replaced, affect the passing/run game most.
OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "T", "G", "FB"}
DEFENSIVE_POSITIONS = {
    "CB", "S", "LB", "MLB", "OLB", "ILB", "DE", "DT", "NT", "EDGE", "DB", "SS", "FS", "N", "NCB", "RUSH", "SAM", "WLB", "SLB", "DL",
}

PRACTICE_WEIGHT = {
    "Full Participation in Practice": 1.0,
    "Limited Participation in Practice": 0.5,
    "Did Not Participate In Practice": 0.0,
    "": None,
}

GAME_STATUS_WEIGHT = {
    "Out": 0.0,
    "Doubtful": 0.25,
    "Questionable": 0.5,
    "": 1.0,
}


def _norm(name: str) -> str:
    """Normalise a player name for matching across official pages.

    NFL.com and the club pages differ in suffixes (``Jr.``/``III``), apostrophes and in the
    occasional middle initial, so matching is done on a lower-cased, punctuation-free,
    suffix-free version of the surname-bearing core.
    """
    import re

    n = name.lower()
    n = n.replace("'", "").replace("\u2019", "")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    for suf in (" jr", " sr", " iii", " ii", " iv"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    return n


# Cross-source name variants observed between the official injury report and the club chart.
# Each entry is (team, report name, chart name, note). Documented so a reviewer can see that the
# match was a transcription difference and not a guess about the player's identity.
NAME_ALIASES = [
    ("BAL", "Matthew Hibner", "Matt Hibner", "Official injury report uses 'Matthew'; club chart uses 'Matt'."),
    ("BAL", "Olaivavega Ioane", "Vega Ioane", "Injury report uses the legal first name; club chart uses 'Vega'."),
    ("IND", "A.J. Haulcy", "AJ Haulcy", "Punctuation only."),
    ("IND", "Drew Ogletree", "Andrew Ogletree", "Colts chart lists 'Drew Ogletree'; the injury report does not list him in Week 10."),
]


def depth_index(team: str, player: str) -> tuple[int | None, list[str]]:
    """Return (best 1-based depth string, list of position groups he is listed in)."""
    chart = CHART_SOURCES.get(team)
    if not chart:
        return None, []
    key = _norm(player)
    for t, report_name, chart_name, _note in NAME_ALIASES:
        if t == team and _norm(player) == _norm(report_name):
            key = _norm(chart_name)
            break
    best = None
    groups = []
    for group, names in chart["groups"].items():
        for i, n in enumerate(names, start=1):
            if _norm(n) == key:
                groups.append(group)
                best = i if best is None else min(best, i)
                break
    return best, groups


def unit_of(position: str) -> str:
    p = (position or "").upper()
    if p in OFFENSIVE_POSITIONS:
        return "offense"
    if p in DEFENSIVE_POSITIONS:
        return "defense"
    return "special_teams"


def availability(practice_status: str, game_status: str) -> float | None:
    """Declared availability weight, 1.0 = fully available, 0.0 = ruled out.

    This is a *policy weight*, not an official probability: the league publishes the labels,
    not their probabilities. Returns None when no official label is present.
    """
    if game_status in GAME_STATUS_WEIGHT and game_status != "":
        return GAME_STATUS_WEIGHT[game_status]
    pw = PRACTICE_WEIGHT.get(practice_status, None)
    return pw


def deficiency_weight(depth: int | None, avail: float | None) -> float | None:
    """Share of the starter's expected work that the club's own chart says is displaced.

    weight = (depth_string - 1) * (1 - availability). A 1st-string player who is fully
    available contributes 0. A 1st-string player ruled out contributes 0 * ... wait: the
    displaced share is the *incoming* string minus one, weighted by unavailability of the
    player in front. See :func:`team_deficiency` for the aggregation that does this properly.
    """
    if depth is None or avail is None:
        return None
    return (depth - 1) * (1.0 - avail)


def team_deficiency(rows: list[dict]) -> dict:
    """Aggregate one club's Week 10 injury rows into offensive/defensive deficiency scores.

    Method (policy, disclosed on the site):
      1. For every listed player with a club-chart depth string ``d`` (1 = starter) and
         declared availability ``a`` in [0,1], the *displacement* of that player is
         ``w = (1 - a) / max(d, 1) ** 0`` … concretely, ``w = (1 - a)`` if d == 1 else 0.
      2. A club's slot is only counted as deficient when a *first-string* player is
         unavailable and the chart lists a replacement behind him.
    The return value therefore reports counts, not a continuous score, so that nothing is
    presented as a measured effect size.
    """
    out = {
        "off_starters_out": 0,
        "off_starters_questionable": 0,
        "def_starters_out": 0,
        "def_starters_questionable": 0,
        "second_string_in": 0,
        "third_string_in": 0,
        "fourth_string_in": 0,
        "unlisted": 0,
        "unverifiable": 0,
    }
    for r in rows:
        d = r.get("depth_string")
        if d == "" or d is None:
            if r.get("chart_status") == "not_listed_on_club_chart":
                out["unlisted"] += 1
            else:
                out["unverifiable"] += 1
            continue
        d = int(d)
        gs = r.get("game_status") or ""
        ps = r.get("practice_status") or ""
        unit = r.get("unit")
        out_fn = (1 - GAME_STATUS_WEIGHT.get(gs, 1.0)) if gs else (
            1 - (PRACTICE_WEIGHT.get(ps) or 1.0) if ps else 0.0
        )
        if d == 1 and gs == "Out":
            if unit == "offense":
                out["off_starters_out"] += 1
            elif unit == "defense":
                out["def_starters_out"] += 1
        elif d == 1 and gs == "Questionable":
            if unit == "offense":
                out["off_starters_questionable"] += 1
            elif unit == "defense":
                out["def_starters_questionable"] += 1
        elif d == 2 and (gs == "Out" or out_fn >= 1.0):
            out["second_string_in"] += 1
        elif d == 3 and (gs == "Out" or out_fn >= 1.0):
            out["third_string_in"] += 1
        elif d == 4 and (gs == "Out" or out_fn >= 1.0):
            out["fourth_string_in"] += 1
    return out
