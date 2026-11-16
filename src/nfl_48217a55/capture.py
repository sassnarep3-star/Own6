"""Official values read during session 48217a55.

This module is the pack's only hand-written content. Every tuple below was transcribed
from a page fetched during this session; ``SOURCES`` maps each source id to its URL, the
UTC clock time the page was requested, the number of chunks the page was served in, and
the chunk indices actually read. Nothing is inferred, imputed or estimated.

Where the official page left a cell blank (no injury listed, no game status yet) the
value is the empty string, and it stays empty all the way to the published table.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# capture metadata
# ---------------------------------------------------------------------------

CAPTURE_DATE_UTC = "2026-11-15"
CAPTURE_CLOCK_UTC = "2026-11-15T18:40Z"

#: The 2026 season week whose injury report was live at capture time.
WEEK = 10
SEASON = 2026

SOURCES = [
    # id, url, read_at_utc, chunks_total, chunks_read, what_it_supports
    (
        "S1",
        "https://www.nfl.com/injuries/",
        "2026-11-15T18:32Z",
        8,
        "0-7",
        "Official Week 10 injury report: every club/player/position/injury/practice/game-status row; "
        "kickoff time, network and club record badge per fixture.",
    ),
    (
        "S2",
        "https://www.nfl.com/schedules/2026/by-week/week-10",
        "2026-11-15T18:34Z",
        2,
        "0-1",
        "Week 10 slate: 14 fixtures, kickoff date/time, network, FINAL/LIVE/scheduled status and "
        "final scores for the games that had completed; the four bye clubs; the Week 16-18 "
        "flexible-scheduling note.",
    ),
    (
        "S3",
        "https://www.nfl.com/standings/division/2026/reg",
        "2026-11-15T18:36Z",
        2,
        "0-1",
        "All 32 clubs: W, L, T, PCT, PF, PA, NET PTS, HOME, ROAD, DIV, CONF, STRK as rendered at "
        "capture time.",
    ),
    (
        "S4",
        "https://www.nfl.com/news/week-10-injuries-sunday-pregame-2026-nfl-season",
        "2026-11-15T18:37Z",
        1,
        "0",
        "Sunday-pregame active/inactive confirmations for Week 10, each with the club record the "
        "page printed before kickoff.",
    ),
    (
        "S5",
        "https://www.nfl.com/news/nfl-week-9-inactives-players-ruled-out-sunday-2026-season",
        "2026-11-15T18:38Z",
        2,
        "0-1",
        "Official Week 9 inactive lists for all 13 Sunday games, with the venue and kickoff of "
        "each fixture.",
    ),
    (
        "S6",
        "https://www.nfl.com/transactions/",
        "2026-11-15T18:39Z",
        1,
        "0",
        "League trades for November 2026 (from/to club, date, player, transaction type) and the "
        "existence of the Reserve List, Signings, Waivers, Terminations and Other sub-routes.",
    ),
    (
        "S7",
        "https://www.nfl.com/transactions/league/reserve-list/2026/11",
        "2026-11-15T18:39Z",
        2,
        "0-1",
        "November 2026 Reserve/Injured entries: club, date and player for every player moved to a "
        "reserve list.",
    ),
    (
        "S8",
        "https://www.nfl.com/teams/kansas-city-chiefs/roster",
        "2026-11-15T18:40Z",
        3,
        "0-2",
        "Official club roster route: jersey number, position, roster status (ACT/RES/DEV/CUT/PUP/"
        "TRD), height, weight, experience, college; and the club-hosted DEPTH CHART link.",
    ),
    (
        "S9",
        "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
        "2026-11-15T18:40Z",
        1,
        "0",
        "Route probe only: the per-club /depth-chart path on nfl.com returns HTTP 404 "
        "('404 - Flag on the Play.'). No depth data is published from it.",
    ),
]

SOURCE_URL = {sid: url for sid, url, *_ in SOURCES}

# ---------------------------------------------------------------------------
# S1 — official Week 10 injury report
# ---------------------------------------------------------------------------
# (club, player, position, injury, practice_status, game_status)
# Injury and game status are '' exactly where the official table printed nothing.

INJURY_REPORT = [
    # --- Thursday, November 12 -------------------------------------------
    ("WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
    ("WAS", "Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
    ("WAS", "Matt Gulbin", "C", "", "Full Participation in Practice", ""),
    ("WAS", "Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("WAS", "Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
    ("WAS", "Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
    ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    ("NYG", "Abdul Carter", "LB", "", "Full Participation in Practice", ""),
    ("NYG", "Jermaine Eluemunor", "T", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable"),
    ("NYG", "Colton Hood", "CB", "", "Full Participation in Practice", ""),
    ("NYG", "Theo Johnson", "TE", "", "Full Participation in Practice", ""),
    ("NYG", "Charlie Jones", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "J.J. McCarthy", "QB", "", "Full Participation in Practice", ""),
    ("NYG", "Darnell Mooney", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Nabers", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Cam Skattebo", "RB", "", "Full Participation in Practice", ""),
    ("NYG", "Andrew Thomas", "T", "", "Full Participation in Practice", ""),
    # --- Sunday, November 15 — 9:30 AM (Munich) ---------------------------
    ("NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
    ("NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
    ("NE", "Hunter Henry", "TE", "", "Limited Participation in Practice", ""),
    ("NE", "Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
    ("NE", "Drake Maye", "QB", "", "Full Participation in Practice", ""),
    ("NE", "Morgan Moses", "T", "", "Full Participation in Practice", ""),
    ("NE", "Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("NE", "Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("NE", "Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("NE", "Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("DET", "Brian Branch", "S", "", "Full Participation in Practice", ""),
    ("DET", "Jared Goff", "QB", "", "Full Participation in Practice", ""),
    ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
    ("DET", "Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
    ("DET", "Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
    ("DET", "Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("DET", "DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
    # --- Sunday, November 15 — 1:00 PM ------------------------------------
    ("KC", "Jeffrey Bassa", "LB", "", "Full Participation in Practice", ""),
    ("KC", "Mansoor Delane", "CB", "Shoulder", "Full Participation in Practice", "Questionable"),
    ("KC", "Justin Fields", "QB", "", "Full Participation in Practice", ""),
    ("KC", "Jaden Hicks", "S", "", "Full Participation in Practice", ""),
    ("KC", "Travis Kelce", "TE", "", "Full Participation in Practice", ""),
    ("KC", "Patrick Mahomes", "QB", "", "Full Participation in Practice", ""),
    ("KC", "Jaylon Moore", "T", "Ankle", "Did Not Participate In Practice", "Out"),
    ("KC", "Omarr Norman-Lott", "DT", "Knee", "Limited Participation in Practice", "Out"),
    ("KC", "Jaydn Ott", "RB", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("KC", "Rashee Rice", "WR", "", "Full Participation in Practice", ""),
    ("KC", "Kenneth Walker III", "RB", "Groin", "Did Not Participate In Practice", "Questionable"),
    ("KC", "Peter Woods", "DT", "Neck", "Did Not Participate In Practice", "Out"),
    ("KC", "Xavier Worthy", "WR", "", "Full Participation in Practice", ""),
    ("ATL", "Zachariah Branch", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("ATL", "Kendal Daniels", "LB", "", "Full Participation in Practice", ""),
    ("ATL", "Divine Deablo", "LB", "Forearm", "Did Not Participate In Practice", "Doubtful"),
    ("ATL", "Gervon Dexter Sr.", "DT", "Illness", "Limited Participation in Practice", "Questionable"),
    ("ATL", "Jake Matthews", "T", "", "Limited Participation in Practice", ""),
    ("ATL", "Liam McCullough", "LS", "", "Did Not Participate In Practice", ""),
    ("ATL", "James Pearce Jr.", "DE", "Back", "Limited Participation in Practice", "Questionable"),
    ("ATL", "Za'Darius Smith", "DE", "", "Full Participation in Practice", ""),
    ("ATL", "Jawaan Taylor", "T", "", "Limited Participation in Practice", ""),
    ("ATL", "Cameron Thomas", "DE", "", "Full Participation in Practice", ""),
    ("ATL", "Josh Woods", "LB", "Ankle", "Full Participation in Practice", "Questionable"),
    ("MIN", "Jordan Addison", "WR", "Thumb", "Limited Participation in Practice", "Questionable"),
    ("MIN", "Blake Cashman", "LB", "Concussion", "Limited Participation in Practice", "Out"),
    ("MIN", "Christian Darrisaw", "T", "", "Did Not Participate In Practice", ""),
    ("MIN", "T.J. Hockenson", "TE", "Wrist, Chest", "Did Not Participate In Practice", "Out"),
    ("MIN", "Tyrion Ingram-Dawkins", "DT", "Ankle", "Did Not Participate In Practice", "Out"),
    ("MIN", "Theo Jackson", "S", "", "Full Participation in Practice", ""),
    ("MIN", "Jauan Jennings", "WR", "Calf", "Did Not Participate In Practice", "Out"),
    ("MIN", "Josh Metellus", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
    ("MIN", "Kyler Murray", "QB", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("MIN", "Harrison Smith", "S", "", "Limited Participation in Practice", ""),
    ("MIN", "Kyle Van Noy", "LB", "Calf", "Limited Participation in Practice", "Questionable"),
    ("MIN", "Jay Ward", "S", "", "Full Participation in Practice", ""),
    ("MIN", "Carson Wentz", "QB", "", "Full Participation in Practice", ""),
    ("GB", "Aaron Banks", "G", "", "Limited Participation in Practice", ""),
    ("GB", "Chris Brooks", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("GB", "Javon Bullard", "S", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("GB", "Zaire Franklin", "LB", "Shin", "Did Not Participate In Practice", "Doubtful"),
    ("GB", "Travis Glover", "G", "Knee", "Limited Participation in Practice", "Questionable"),
    ("GB", "Ty'Ron Hopper", "LB", "", "Full Participation in Practice", ""),
    ("GB", "Josh Jacobs", "RB", "Finger", "Did Not Participate In Practice", "Out"),
    ("GB", "Xavier McKinney", "S", "Foot", "Limited Participation in Practice", "Questionable"),
    ("GB", "Bo Melton", "WR", "", "Full Participation in Practice", ""),
    ("GB", "Skyy Moore", "WR", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("GB", "Micah Parsons", "LB", "Knee, Illness", "Limited Participation in Practice", "Out"),
    ("GB", "Sean Rhyan", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("GB", "Trey Smack", "K", "", "Full Participation in Practice", ""),
    ("GB", "Lukas Van Ness", "LB", "Back", "Limited Participation in Practice", "Questionable"),
    ("GB", "Josh Whyle", "TE", "Concussion", "Did Not Participate In Practice", "Out"),
    ("GB", "Savion Williams", "WR", "", "Limited Participation in Practice", ""),
    ("GB", "Kevin Zeitler", "G", "Ankle, Triceps", "Did Not Participate In Practice", "Questionable"),
    ("JAX", "Jessie Bates", "S", "Not injury related - resting player",
     "Limited Participation in Practice", "Out"),
    ("JAX", "Ezra Cleveland", "G", "", "Full Participation in Practice", ""),
    ("JAX", "Branson Combs", "LB", "", "Full Participation in Practice", ""),
    ("JAX", "Jordan Davis", "DT", "Not injury related - resting player",
     "Limited Participation in Practice", "Out"),
    ("JAX", "BJ Green II", "DE", "Forearm", "Full Participation in Practice", "Out"),
    ("JAX", "Robert Hainsey", "C", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("JAX", "Antonio Johnson", "S", "", "Limited Participation in Practice", ""),
    ("JAX", "Jakobi Meyers", "WR", "", "Limited Participation in Practice", ""),
    ("JAX", "Chris Rodriguez Jr.", "RB", "", "Limited Participation in Practice", ""),
    ("JAX", "Bhayshul Tuten", "RB", "", "Limited Participation in Practice", ""),
    ("JAX", "Travon Walker", "DE", "", "Limited Participation in Practice", ""),
    ("TEN", "Cody Barton", "LB", "Concussion", "Did Not Participate In Practice", "Out"),
    ("TEN", "John Franklin-Myers", "DE", "", "Full Participation in Practice", ""),
    ("TEN", "Marcus Harris", "CB", "", "Full Participation in Practice", ""),
    ("TEN", "Anthony Hill Jr.", "LB", "Neck", "Did Not Participate In Practice", "Out"),
    ("TEN", "Jaylon Jones", "CB", "", "Full Participation in Practice", ""),
    ("TEN", "JC Latham", "T", "", "Full Participation in Practice", ""),
    ("TEN", "Tony Pollard", "RB", "", "Full Participation in Practice", ""),
    ("TEN", "Peter Skoronski", "G", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("TEN", "Tyjae Spears", "RB", "Knee", "Full Participation in Practice", "Questionable"),
    ("TEN", "Carnell Tate", "WR", "Shoulder", "Did Not Participate In Practice", "Out"),
    ("TEN", "Tommy Townsend", "P", "Knee, Achilles", "Did Not Participate In Practice", "Out"),
    ("TEN", "Kevin Winston Jr.", "S", "", "Full Participation in Practice", ""),
    ("BUF", "Alec Anderson", "G", "", "Full Participation in Practice", ""),
    ("BUF", "Christian Benford", "CB", "Wrist", "Full Participation in Practice", "Questionable"),
    ("BUF", "Terrel Bernard", "LB", "", "Did Not Participate In Practice", ""),
    ("BUF", "Spencer Brown", "T", "Ankle", "Did Not Participate In Practice", "Doubtful"),
    ("BUF", "Dion Dawkins", "T", "", "Full Participation in Practice", ""),
    ("BUF", "Sam Franklin Jr.", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
    ("BUF", "Greg Gaines", "DT", "", "Full Participation in Practice", ""),
    ("BUF", "Jordan Hancock", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("BUF", "Dalton Kincaid", "TE", "", "Full Participation in Practice", ""),
    ("BUF", "Connor McGovern", "C", "", "Full Participation in Practice", ""),
    ("BUF", "Ed Oliver", "DE", "", "Did Not Participate In Practice", ""),
    ("BUF", "Ar'maj Reed-Adams", "G", "", "Full Participation in Practice", ""),
    ("BUF", "T.J. Sanders", "DE", "", "Full Participation in Practice", ""),
    ("BUF", "Tyrell Shavers", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Jarvis Brownlee Jr.", "CB", "Illness", "Limited Participation in Practice", "Questionable"),
    ("NYJ", "Omar Cooper Jr.", "WR", "Ankle", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Adonai Mitchell", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Joseph Ossai", "DE", "Ankle", "Full Participation in Practice", "Questionable"),
    ("NYJ", "VJ Payne", "S", "Knee", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Harrison Phillips", "DT", "Ankle", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Trevin Wallace", "LB", "Groin", "Did Not Participate In Practice", "Out"),
    ("NYJ", "Garrett Wilson", "WR", "Concussion", "Full Participation in Practice", "Questionable"),
    ("NYJ", "Nahshon Wright", "CB", "Back", "Full Participation in Practice", "Questionable"),
    ("MIA", "Tucker Addington", "LS", "", "Limited Participation in Practice", ""),
    ("MIA", "Kaytron Allen", "RB", "", "Full Participation in Practice", ""),
    ("MIA", "Darrell Baker Jr.", "CB", "Knee", "Full Participation in Practice", "Questionable"),
    ("MIA", "Chris Bell", "WR", "Knee", "Did Not Participate In Practice", "Doubtful"),
    ("MIA", "Aaron Brewer", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("MIA", "Malik Herring", "DE", "", "Full Participation in Practice", ""),
    ("MIA", "Will Kacmarek", "TE", "", "Full Participation in Practice", ""),
    ("MIA", "Michael Taaffe", "S", "", "Full Participation in Practice", ""),
    ("MIA", "Dante Trader Jr.", "S", "", "Full Participation in Practice", ""),
    ("MIA", "Jared Wayne", "WR", "Quadricep", "Did Not Participate In Practice", "Out"),
    ("MIA", "Jaylen Wright", "RB", "", "Full Participation in Practice", ""),
    ("IND", "Mo Alie-Cox", "TE", "Groin", "Did Not Participate In Practice", "Out"),
    ("IND", "CJ Allen", "LB", "", "Full Participation in Practice", ""),
    ("IND", "Jaylon Carlies", "LB", "Neck", "Did Not Participate In Practice", "Out"),
    ("IND", "Akeem Davis-Gaither", "LB", "Knee", "Did Not Participate In Practice", "Out"),
    ("IND", "A.J. Haulcy", "S", "", "Full Participation in Practice", ""),
    ("IND", "Arden Key", "DE", "", "Full Participation in Practice", ""),
    ("IND", "Will Mallory", "TE", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("IND", "Luke Rhodes", "LS", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("IND", "Grover Stewart", "DT", "", "Full Participation in Practice", ""),
    ("IND", "Jonathan Taylor", "RB", "", "Full Participation in Practice", ""),
    ("IND", "Jerry Tillery", "DT", "Calf", "Did Not Participate In Practice", "Out"),
    ("IND", "Jalen Travis", "T", "Knee", "Did Not Participate In Practice", "Out"),
    ("IND", "Justin Walley", "CB", "", "Full Participation in Practice", ""),
    ("IND", "Charvarius Ward", "CB", "", "Full Participation in Practice", ""),
    ("CAR", "Jonathon Brooks", "RB", "Groin", "Limited Participation in Practice", "Doubtful"),
    ("CAR", "Brady Christensen", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("CAR", "Trevor Etienne", "RB", "", "Full Participation in Practice", ""),
    ("CAR", "Chuba Hubbard", "RB", "", "Full Participation in Practice", ""),
    ("CAR", "Lee Hunter", "DT", "", "Full Participation in Practice", ""),
    ("CAR", "Mike Jackson", "CB", "Groin", "Limited Participation in Practice", "Doubtful"),
    ("CAR", "Will Lee III", "CB", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("CAR", "Xavier Legette", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ("CAR", "Damien Lewis", "G", "", "Full Participation in Practice", ""),
    ("CAR", "Bobby Okereke", "LB", "Foot", "Did Not Participate In Practice", "Out"),
    ("CAR", "Jaelan Phillips", "LB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("CAR", "Torricelli Simpkins III", "G", "", "Full Participation in Practice", ""),
    ("NO", "Kelvin Banks Jr.", "T", "", "Full Participation in Practice", ""),
    ("NO", "CJ Donaldson", "RB", "Shoulder", "Did Not Participate In Practice", "Out"),
    ("NO", "David Edwards", "G", "", "Full Participation in Practice", ""),
    ("NO", "Martin Emerson", "CB", "Shin", "Limited Participation in Practice", "Questionable"),
    ("NO", "Travis Etienne", "RB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("NO", "Noah Fant", "TE", "", "Full Participation in Practice", ""),
    ("NO", "Taliese Fuaga", "T", "Knee", "Did Not Participate In Practice", "Out"),
    ("NO", "Alvin Kamara", "RB", "", "Full Participation in Practice", ""),
    ("NO", "Erik McCoy", "C", "Biceps", "Did Not Participate In Practice", "Out"),
    ("NO", "Christen Miller", "DT", "Knee", "Did Not Participate In Practice", "Out"),
    ("NO", "Asim Richards", "T", "", "Full Participation in Practice", ""),
    ("NO", "Quincy Riley", "CB", "", "Full Participation in Practice", ""),
    ("HOU", "Azeez Al-Shaair", "LB", "Groin, Not injury related - personal matter",
     "Did Not Participate In Practice", "Out"),
    ("HOU", "Will Anderson Jr.", "DE", "Ankle", "Did Not Participate In Practice", "Questionable"),
    ("HOU", "Reed Blankenship", "S", "", "Full Participation in Practice", ""),
    ("HOU", "Trent Brown", "T", "Wrist, Illness", "Did Not Participate In Practice", "Questionable"),
    ("HOU", "Tank Dell", "WR", "", "Full Participation in Practice", ""),
    ("HOU", "Blake Fisher", "T", "", "Full Participation in Practice", ""),
    ("HOU", "Marvin Harrison Jr.", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("HOU", "Jacob Hummel", "LB", "Groin", "Full Participation in Practice", "Questionable"),
    ("HOU", "Danielle Hunter", "DE", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("HOU", "Brevin Jordan", "TE", "Finger, Foot", "Did Not Participate In Practice", "Out"),
    ("HOU", "Woody Marks", "RB", "", "Full Participation in Practice", ""),
    ("HOU", "David Montgomery", "RB", "Groin", "Full Participation in Practice", "Questionable"),
    ("HOU", "Keylan Rutledge", "G", "Neck, Shoulder", "Did Not Participate In Practice", "Out"),
    ("HOU", "Jaylin Smith", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("HOU", "Tommy Togiai", "DT", "", "Full Participation in Practice", ""),
    ("HOU", "Wyatt Teller", "G", "Illness, Back", "Limited Participation in Practice", "Questionable"),
    ("CLE", "Austin Barber", "T", "", "Full Participation in Practice", ""),
    ("CLE", "Denzel Boston", "WR", "Toe", "Limited Participation in Practice", "Questionable"),
    ("CLE", "Michael Burton", "FB", "Calf", "Did Not Participate In Practice", "Out"),
    ("CLE", "Maliek Collins", "DT", "", "Full Participation in Practice", ""),
    ("CLE", "Harold Fannin Jr.", "TE", "", "Full Participation in Practice", ""),
    ("CLE", "Ronnie Hickman Jr.", "S", "Concussion", "Did Not Participate In Practice", "Out"),
    ("CLE", "Tytus Howard", "T", "", "Full Participation in Practice", ""),
    ("CLE", "Elgton Jenkins", "C", "", "Full Participation in Practice", ""),
    ("CLE", "Donovan McMillon", "S", "", "Limited Participation in Practice", ""),
    ("CLE", "Carson Schwesinger", "LB", "", "Full Participation in Practice", ""),
    ("CLE", "Denzel Ward", "CB", "", "Limited Participation in Practice", ""),
    ("CLE", "Quincy Williams", "LB", "", "Full Participation in Practice", ""),
    # --- Sunday, November 15 — 4:05 PM ------------------------------------
    ("LAR", "Davis Allen", "TE", "Oblique", "Limited Participation in Practice", "Questionable"),
    ("LAR", "Steve Avila", "G", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("LAR", "Joe Cardona", "LS", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("LAR", "Kam Curl", "S", "Toe", "Limited Participation in Practice", "Questionable"),
    ("LAR", "Aaron Donald", "DT", "", "Did Not Participate In Practice", ""),
    ("LAR", "Terrance Ferguson", "TE", "Ankle, Hamstring", "Did Not Participate In Practice", "Out"),
    ("LAR", "Braden Fiske", "DT", "", "Did Not Participate In Practice", ""),
    ("LAR", "Myles Garrett", "LB", "Knee, Not injury related - resting player",
     "Did Not Participate In Practice", "Questionable"),
    ("LAR", "Tyler Higbee", "TE", "", "Limited Participation in Practice", ""),
    ("LAR", "Trent McDuffie", "CB", "Back", "Limited Participation in Practice", "Questionable"),
    ("LAR", "Puka Nacua", "WR", "", "Did Not Participate In Practice", ""),
    ("LAR", "Colby Parkinson", "TE", "", "Full Participation in Practice", ""),
    ("LAR", "Matthew Stafford", "QB", "", "Full Participation in Practice", ""),
    ("LAR", "Byron Young", "LB", "", "Did Not Participate In Practice", ""),
    ("AZ", "Budda Baker", "S", "", "Full Participation in Practice", ""),
    ("AZ", "Zachary Carter", "DT", "Knee", "Limited Participation in Practice", "Out"),
    ("AZ", "Hjalte Froholdt", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("AZ", "Jon Gaines II", "G", "Ankle", "Did Not Participate In Practice", "Out"),
    ("AZ", "Bam Knight", "RB", "", "Full Participation in Practice", ""),
    ("AZ", "Hunter Long", "TE", "Knee", "Limited Participation in Practice", "Questionable"),
    ("AZ", "Roy Lopez", "DT", "Toe, Ankle", "Limited Participation in Practice", "Questionable"),
    ("AZ", "Max Melton", "CB", "Knee, Hand", "Limited Participation in Practice", "Questionable"),
    ("AZ", "Darius Robinson", "DT", "Wrist", "Limited Participation in Practice", "Questionable"),
    ("AZ", "Isaac Seumalo", "G", "", "Full Participation in Practice", ""),
    ("AZ", "Dante Stills", "DT", "", "Full Participation in Practice", ""),
    ("AZ", "Josh Sweat", "LB", "", "Full Participation in Practice", ""),
    ("AZ", "Jayden Williams", "T", "Knee", "Limited Participation in Practice", "Questionable"),
    ("AZ", "Mack Wilson", "LB", "", "Full Participation in Practice", ""),
    ("AZ", "Andrew Wingard", "S", "Groin", "Did Not Participate In Practice", "Questionable"),
    ("SEA", "AJ Barner", "TE", "", "Full Participation in Practice", ""),
    ("SEA", "Anthony Bradford", "G", "", "Full Participation in Practice", ""),
    ("SEA", "Charles Cross", "T", "Ankle", "Did Not Participate In Practice", "Out"),
    ("SEA", "Sam Darnold", "QB", "Ribs, Quadricep", "Did Not Participate In Practice", "Out"),
    ("SEA", "Derick Hall", "LB", "", "Did Not Participate In Practice", ""),
    ("SEA", "Drew Lock", "QB", "", "Limited Participation in Practice", ""),
    ("SEA", "Quenton Nelson", "G", "Knee", "Did Not Participate In Practice", "Out"),
    ("SEA", "Uchenna Nwosu", "LB", "", "Full Participation in Practice", ""),
    ("SEA", "Patrick O'Connell", "LB", "", "Full Participation in Practice", ""),
    ("SEA", "Connor O'Toole", "LB", "", "Full Participation in Practice", ""),
    ("SEA", "Brandon Pili", "DT", "", "Full Participation in Practice", ""),
    ("SEA", "Jarran Reed", "DT", "", "Full Participation in Practice", ""),
    ("SEA", "Rashid Shaheed", "WR", "", "Full Participation in Practice", ""),
    ("SEA", "Jaxon Smith-Njigba", "WR", "", "Full Participation in Practice", ""),
    ("SEA", "Leonard Williams", "DT", "Stinger", "Did Not Participate In Practice", "Out"),
    ("LV", "Thomas Booker", "DT", "Ankle", "Full Participation in Practice", "Questionable"),
    ("LV", "Foley Fatukasi", "DT", "", "Full Participation in Practice", ""),
    ("LV", "Ian Thomas", "TE", "", "Full Participation in Practice", ""),
    ("LV", "Dont'e Thornton Jr.", "WR", "Back", "Did Not Participate In Practice", "Questionable"),
    ("LV", "Trey Zuhn III", "C", "", "Full Participation in Practice", ""),
    # --- Sunday, November 15 — 4:25 PM ------------------------------------
    ("SF", "Mike Evans", "WR", "Achilles", "Did Not Participate In Practice", "Out"),
    ("SF", "Renardo Green", "CB", "Back", "Limited Participation in Practice", "Questionable"),
    ("SF", "Dre Greenlaw", "LB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("SF", "Nate Hobbs", "CB", "Groin", "Full Participation in Practice", "Questionable"),
    ("SF", "Deommodore Lenoir", "CB", "Foot", "Limited Participation in Practice", "Questionable"),
    ("SF", "Christian McCaffrey", "RB", "", "Full Participation in Practice", ""),
    ("SF", "Siran Neal", "S", "", "Full Participation in Practice", ""),
    ("SF", "Demarcus Robinson", "WR", "", "Full Participation in Practice", ""),
    ("SF", "Deebo Samuel Sr.", "WR", "", "Full Participation in Practice", ""),
    ("SF", "Upton Stout", "CB", "Shoulder, Neck", "Limited Participation in Practice", "Questionable"),
    ("SF", "C.J. West", "DT", "Knee", "Full Participation in Practice", "Questionable"),
    ("SF", "Trent Williams", "T", "Shoulder", "Did Not Participate In Practice", "Questionable"),
    ("DAL", "DaRon Bland", "CB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("DAL", "Jonathan Bullard", "DT", "Calf", "Full Participation in Practice", "Questionable"),
    ("DAL", "Alijah Clark", "S", "Illness", "Did Not Participate In Practice", "Questionable"),
    ("DAL", "Donovan Ezeiruaku", "LB", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DAL", "Jake Ferguson", "TE", "Knee, Ankle", "Did Not Participate In Practice", "Out"),
    ("DAL", "Tyler Goodson", "RB", "Ankle, Knee", "Did Not Participate In Practice", "Out"),
    ("DAL", "Malik Hooker", "S", "", "Did Not Participate In Practice", ""),
    ("DAL", "Marist Liufau", "LB", "", "Full Participation in Practice", ""),
    ("DAL", "P.J. Locke", "S", "Concussion", "Did Not Participate In Practice", "Out"),
    ("DAL", "Von Miller", "LB", "", "Did Not Participate In Practice", ""),
    ("DAL", "Jonathan Mingo", "WR", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DAL", "Devin Moore", "CB", "Hip", "Full Participation in Practice", "Questionable"),
    ("DAL", "DeMarvion Overshown", "LB", "", "Full Participation in Practice", ""),
    ("DAL", "George Pickens", "WR", "", "Full Participation in Practice", ""),
    ("DAL", "Joey Porter Jr.", "CB", "Ankle, Foot", "Limited Participation in Practice", "Questionable"),
    ("DAL", "Luke Schoonmaker", "TE", "", "Full Participation in Practice", ""),
    ("DAL", "Brevyn Spann-Ford", "TE", "", "Full Participation in Practice", ""),
    ("DAL", "Juanyeh Thomas", "S", "Hamstring", "Did Not Participate In Practice", "Doubtful"),
    ("DAL", "KaVontae Turpin", "WR", "", "Full Participation in Practice", ""),
    # --- Sunday, November 15 — 8:20 PM ------------------------------------
    ("PIT", "Brandin Echols", "CB", "", "Full Participation in Practice", ""),
    ("PIT", "DeShon Elliott", "S", "", "Full Participation in Practice", ""),
    ("PIT", "Derrick Harmon", "DT", "Foot", "Full Participation in Practice", "Questionable"),
    ("PIT", "Cameron Heyward", "DT", "", "Full Participation in Practice", ""),
    ("PIT", "Ben Skowronek", "WR", "", "Full Participation in Practice", ""),
    ("PIT", "Doneiko Slaughter", "CB", "", "Full Participation in Practice", ""),
    ("PIT", "Darnell Washington", "TE", "", "Full Participation in Practice", ""),
    ("PIT", "T.J. Watt", "LB", "", "Full Participation in Practice", ""),
    ("CIN", "Jonathan Allen", "DT", "", "Limited Participation in Practice", ""),
    ("CIN", "Jalen Davis", "CB", "Hamstring", "Full Participation in Practice", "Doubtful"),
    ("CIN", "Kyle Dugger", "S", "Quadricep", "Did Not Participate In Practice", "Out"),
    ("CIN", "Dylan Fairchild", "G", "", "Full Participation in Practice", ""),
    ("CIN", "B.J. Hill", "DT", "", "Did Not Participate In Practice", ""),
    ("CIN", "Andrei Iosivas", "WR", "Thumb", "Full Participation in Practice", "Doubtful"),
    ("CIN", "Dexter Lawrence", "DT", "", "Did Not Participate In Practice", ""),
    ("CIN", "Brian Parker II", "G", "Knee", "Full Participation in Practice", "Doubtful"),
    ("CIN", "DJ Turner II", "CB", "", "Full Participation in Practice", ""),
    # --- Monday, November 16 ----------------------------------------------
    ("LAC", "Kayode Awosika", "G", "Fibula", "Full Participation in Practice", "Questionable"),
    ("LAC", "Bud Dupree", "DE", "", "Full Participation in Practice", ""),
    ("LAC", "Justin Eboigbe", "DE", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("LAC", "Alex Harkey", "G", "", "Full Participation in Practice", ""),
    ("LAC", "Tre Harris", "WR", "", "Full Participation in Practice", ""),
    ("LAC", "Cam Hart", "CB", "", "Full Participation in Practice", ""),
    ("LAC", "Daiyan Henley", "LB", "", "Full Participation in Practice", ""),
    ("LAC", "Deane Leonard", "CB", "", "Full Participation in Practice", ""),
    ("LAC", "Khalil Mack", "LB", "", "Full Participation in Practice", ""),
    ("LAC", "Ladd McConkey", "WR", "Back", "Did Not Participate In Practice", "Questionable"),
    ("LAC", "Keaton Mitchell", "RB", "", "Full Participation in Practice", ""),
    ("LAC", "David Njoku", "TE", "Fibula", "Full Participation in Practice", "Questionable"),
    ("LAC", "Denzel Perryman", "LB", "Pectoral", "Full Participation in Practice", "Questionable"),
    ("LAC", "Trey Pipkins", "T", "Not injury related - personal matter, Knee",
     "Limited Participation in Practice", "Questionable"),
    ("LAC", "Rodney Shelley", "CB", "", "Full Participation in Practice", ""),
    ("LAC", "Branson Taylor", "G", "Ankle", "Did Not Participate In Practice", "Out"),
    ("LAC", "Brenen Thompson", "WR", "Hamstring", "Did Not Participate In Practice", "Doubtful"),
    ("LAC", "Isas Waxter", "CB", "Ankle", "Did Not Participate In Practice", "Out"),
    ("LAC", "Kendall Williamson", "S", "Calf", "Did Not Participate In Practice", "Out"),
    ("BAL", "Rasheen Ali", "RB", "", "Full Participation in Practice", ""),
    ("BAL", "Rashod Bateman", "WR", "", "Full Participation in Practice", ""),
    ("BAL", "Calais Campbell", "DT", "", "Did Not Participate In Practice", ""),
    ("BAL", "Kyle Hamilton", "S", "", "Full Participation in Practice", ""),
    ("BAL", "Jaylinn Hawkins", "S", "Knee", "Limited Participation in Practice", "Out"),
    ("BAL", "Matthew Hibner", "TE", "", "Full Participation in Practice", ""),
    ("BAL", "Olaivavega Ioane", "G", "", "Full Participation in Practice", ""),
    ("BAL", "Adam Randall", "RB", "Neck, Hamstring", "Full Participation in Practice", "Questionable"),
    ("BAL", "Ronnie Stanley", "T", "", "Did Not Participate In Practice", ""),
    ("BAL", "Nate Wiggins", "CB", "", "Full Participation in Practice", ""),
]

#: Clubs on bye in Week 10 (S2). No injury section exists for them on S1, which is
#: correct and is *not* evidence that they are injury free.
BYE_CLUBS_WEEK10 = ["CHI", "DEN", "PHI", "TB"]

# ---------------------------------------------------------------------------
# S2 — Week 10 slate
# ---------------------------------------------------------------------------
# (game_slug, date, kickoff_et, away, home, away_pts, home_pts, status, network)
# status is one of FINAL / LIVE / SCHEDULED exactly as the page rendered it.
# away_pts and home_pts are '' unless status == FINAL.

WEEK10_SLATE = [
    ("commanders-at-giants-2026-reg-10", "2026-11-12", "8:15 PM", "WAS", "NYG", "24", "21",
     "FINAL", "Prime Video"),
    ("patriots-at-lions-2026-reg-10", "2026-11-15", "9:30 AM", "NE", "DET", "10", "35",
     "FINAL", "FOX, FOX DEPORTES"),
    ("chiefs-at-falcons-2026-reg-10", "2026-11-15", "1:00 PM", "KC", "ATL", "35", "13",
     "FINAL", "CBS"),
    ("texans-at-browns-2026-reg-10", "2026-11-15", "1:00 PM", "HOU", "CLE", "24", "27",
     "FINAL", "CBS"),
    ("vikings-at-packers-2026-reg-10", "2026-11-15", "1:00 PM", "MIN", "GB", "30", "10",
     "FINAL", "FOX"),
    ("dolphins-at-colts-2026-reg-10", "2026-11-15", "1:00 PM", "MIA", "IND", "22", "24",
     "FINAL", "CBS"),
    ("panthers-at-saints-2026-reg-10", "2026-11-15", "1:00 PM", "CAR", "NO", "20", "17",
     "FINAL", "FOX"),
    ("bills-at-jets-2026-reg-10", "2026-11-15", "1:00 PM", "BUF", "NYJ", "31", "12",
     "FINAL", "CBS"),
    ("jaguars-at-titans-2026-reg-10", "2026-11-15", "1:00 PM", "JAX", "TEN", "40", "23",
     "FINAL", "CBS"),
    ("rams-at-cardinals-2026-reg-10", "2026-11-15", "4:05 PM", "LAR", "AZ", "", "",
     "LIVE", "CBS"),
    ("seahawks-at-raiders-2026-reg-10", "2026-11-15", "4:05 PM", "SEA", "LV", "", "",
     "LIVE", "CBS"),
    ("49ers-at-cowboys-2026-reg-10", "2026-11-15", "4:25 PM", "SF", "DAL", "", "",
     "LIVE", "FOX, FOX DEPORTES"),
    ("steelers-at-bengals-2026-reg-10", "2026-11-15", "8:20 PM", "PIT", "CIN", "", "",
     "SCHEDULED", "NBC, UNIVERSO"),
    ("chargers-at-ravens-2026-reg-10", "2026-11-16", "8:15 PM", "LAC", "BAL", "", "",
     "SCHEDULED", "ESPN, ABC, ESPN2, ESPN DEPORTES"),
]

#: Scores shown on the LIVE cards at capture time. These are in-progress, NOT finals,
#: so they are published in their own table with an explicit in-progress marker and are
#: never allowed into the results feed.
WEEK10_LIVE_SCORES = [
    ("rams-at-cardinals-2026-reg-10", "LAR", "AZ", "34", "6", "Q4"),
    ("seahawks-at-raiders-2026-reg-10", "SEA", "LV", "21", "10", "Q4"),
    ("49ers-at-cowboys-2026-reg-10", "SF", "DAL", "24", "19", "Q3"),
]

# ---------------------------------------------------------------------------
# S3 — standings as rendered at capture time
# ---------------------------------------------------------------------------
# (club, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, CONF, STRK)
# IMPORTANT: this page renders live. At capture time it already included the nine
# completed Week 10 games, and excluded the three in progress. It is therefore an
# as-of-render table, NOT a "through Week 9" table.

STANDINGS_RENDER = [
    ("BUF", 8, 1, 0, "0.889", 287, 199, 88, "3-1-0", "5-0-0", "5-1-0", "3-0-0", "5W"),
    ("NE", 5, 5, 0, "0.500", 221, 242, -21, "3-1-0", "2-4-0", "5-1-0", "0-4-0", "2L"),
    ("NYJ", 2, 8, 0, "0.200", 194, 254, -60, "1-4-0", "1-4-0", "2-5-0", "0-3-0", "5L"),
    ("MIA", 1, 8, 0, "0.111", 148, 224, -76, "0-4-0", "1-4-0", "1-5-0", "0-3-0", "3L"),
    ("PIT", 6, 2, 0, "0.750", 180, 144, 36, "4-0-0", "2-2-0", "3-2-0", "3-0-0", "4W"),
    ("CIN", 6, 2, 0, "0.750", 240, 175, 65, "2-1-0", "4-1-0", "4-2-0", "2-0-0", "4W"),
    ("CLE", 6, 4, 0, "0.600", 188, 220, -32, "4-0-0", "2-4-0", "4-3-0", "2-1-0", "1W"),
    ("BAL", 4, 5, 0, "0.444", 189, 236, -47, "1-3-0", "3-2-0", "2-4-0", "2-1-0", "4L"),
    ("JAX", 7, 2, 0, "0.778", 269, 144, 125, "4-1-0", "3-1-0", "6-2-0", "1-0-0", "3W"),
    ("HOU", 3, 6, 0, "0.333", 233, 219, 14, "0-4-0", "3-2-0", "3-4-0", "0-2-0", "1L"),
    ("IND", 3, 7, 0, "0.300", 208, 271, -63, "2-3-0", "1-4-0", "2-5-0", "1-2-0", "1W"),
    ("TEN", 1, 8, 0, "0.111", 167, 239, -72, "0-5-0", "1-3-0", "1-6-0", "0-2-0", "3L"),
    ("KC", 7, 2, 0, "0.778", 237, 156, 81, "4-0-0", "3-2-0", "6-1-0", "1-1-0", "2W"),
    ("DEN", 7, 2, 0, "0.778", 198, 186, 12, "4-0-0", "3-2-0", "3-1-0", "4-1-0", "5W"),
    ("LV", 4, 5, 0, "0.444", 238, 268, -30, "1-3-0", "3-2-0", "3-3-0", "1-2-0", "1L"),
    ("LAC", 0, 8, 0, "0.000", 121, 219, -98, "0-4-0", "0-4-0", "0-5-0", "0-3-0", "8L"),
    ("NYG", 5, 3, 1, "0.611", 203, 196, 7, "3-2-0", "2-1-1", "3-3-1", "2-0-0", "1L"),
    ("DAL", 4, 5, 0, "0.444", 246, 236, 10, "1-3-0", "3-2-0", "2-4-0", "2-1-0", "1W"),
    ("WAS", 3, 5, 1, "0.389", 196, 223, -27, "2-2-1", "1-3-0", "3-4-1", "0-1-0", "1W"),
    ("PHI", 2, 7, 0, "0.222", 148, 221, -73, "1-4-0", "1-3-0", "1-6-0", "1-1-0", "7L"),
    ("DET", 7, 2, 0, "0.778", 257, 199, 58, "5-0-0", "2-2-0", "4-1-0", "3-1-0", "5W"),
    ("MIN", 7, 2, 0, "0.778", 176, 126, 50, "3-1-0", "4-1-0", "5-1-0", "2-1-0", "1W"),
    ("CHI", 7, 2, 0, "0.778", 241, 184, 57, "4-1-0", "3-1-0", "5-2-0", "2-0-0", "4W"),
    ("GB", 6, 4, 0, "0.600", 226, 221, 5, "3-2-0", "3-2-0", "4-4-0", "2-0-0", "1L"),
    ("CAR", 4, 5, 0, "0.444", 219, 236, -17, "1-3-0", "3-2-0", "4-3-0", "0-2-0", "1W"),
    ("TB", 3, 6, 0, "0.333", 202, 178, 24, "1-4-0", "2-2-0", "3-3-0", "0-3-0", "1L"),
    ("NO", 3, 6, 0, "0.333", 202, 236, -34, "1-5-0", "2-1-0", "1-4-0", "2-2-0", "1L"),
    ("ATL", 3, 7, 0, "0.300", 201, 258, -57, "1-5-0", "2-2-0", "3-3-0", "0-4-0", "3L"),
    ("SF", 7, 1, 0, "0.875", 235, 156, 79, "5-0-0", "2-1-0", "4-1-0", "3-0-0", "1W"),
    ("SEA", 5, 4, 0, "0.556", 202, 162, 40, "4-2-0", "1-2-0", "2-3-0", "3-1-0", "1W"),
    ("LAR", 5, 4, 0, "0.556", 214, 181, 33, "2-3-0", "3-1-0", "3-2-0", "2-2-0", "3W"),
    ("AZ", 3, 6, 0, "0.333", 178, 255, -77, "0-3-0", "3-3-0", "2-5-0", "1-1-0", "1L"),
]

# ---------------------------------------------------------------------------
# S4 — Sunday-pregame active/inactive confirmations, with the pre-kickoff record
# ---------------------------------------------------------------------------
# (club, record_before_kickoff, player, position, designation, resolution, note)

WEEK10_PREGAME = [
    ("CAR", "3-5", "Jaelan Phillips", "OLB", "Questionable", "active",
     "expected to play Sunday against New Orleans, NFL Network's Ian Rapoport reported; officially active"),
    ("CLE", "5-4", "Denzel Boston", "WR", "Questionable", "active",
     "expected to play Sunday against Houston, ESPN's Jeremy Fowler reported; officially active"),
    ("DAL", "4-5", "DaRon Bland", "CB", "Questionable", "trending toward playing",
     "trending toward playing against San Francisco, NFL Network's Ian Rapoport reported"),
    ("DAL", "4-5", "Joey Porter Jr.", "CB", "Questionable", "trending toward playing",
     "trending toward playing vs. the 49ers, per Rapoport"),
    ("DET", "6-2", "Amon-Ra St. Brown", "WR", "Questionable", "active",
     "active for Sunday's game against New England"),
    ("HOU", "3-5", "Will Anderson Jr.", "DE", "Questionable", "active",
     "expected to play Sunday against Cleveland, NFL Network's Ian Rapoport reported; officially active"),
    ("MIN", "6-2", "Jordan Addison", "WR", "Questionable", "inactive",
     "was a game-time decision for Sunday's game against Green Bay, per Rapoport"),
    ("NE", "5-4", "Rhamondre Stevenson", "RB", "Questionable", "active",
     "active for Sunday's game against Detroit"),
    ("NE", "5-4", "A.J. Brown", "WR", "Questionable", "active",
     "active vs. the Lions"),
    ("NYJ", "2-7", "Omar Cooper Jr.", "WR", "Questionable", "active",
     "expected to play Sunday against Buffalo, per Rapoport; active"),
    ("NYJ", "2-7", "Adonai Mitchell", "WR", "Questionable", "active",
     "expected to play vs. the Bills, per Rapoport; active"),
    ("NYJ", "2-7", "Garrett Wilson", "WR", "Questionable", "active",
     "cleared concussion protocol and will play against Buffalo, per Rapoport; active"),
    ("SF", "7-1", "Trent Williams", "LT", "Questionable", "expected to play",
     "expected to play Sunday against Dallas, ESPN's Adam Schefter reported"),
    ("TEN", "1-7", "Tyjae Spears", "RB", "Questionable", "active",
     "expected to play Sunday vs. the Jaguars, ESPN's Jeremy Fowler reported; active"),
]

# ---------------------------------------------------------------------------
# S5 — Week 9 official inactive lists + venues (13 Sunday games)
# ---------------------------------------------------------------------------
# (game_slug, away, home, kickoff_et, venue, away_inactives, home_inactives)

WEEK9_INACTIVES = [
    ("bengals-at-falcons-2026-reg-9", "CIN", "ATL", "9:30 a.m. ET",
     "Bernabeu Stadium (Madrid, Spain)",
     ["S Kyle Dugger", "C Connor Lew", "OT Myles Hinton", "DT Landon Robinson"],
     ["QB Andy Dalton (emergency third QB)", "QB Jack Strand", "WR Zachariah Branch",
      "DB Billy Bowman", "DB Robert Longerbeam", "DE Drake Jackson"]),
    ("broncos-at-panthers-2026-reg-9", "DEN", "CAR", "1:00 p.m. ET",
     "Bank of America Stadium (Charlotte, N.C.)",
     ["QB Sam Ehlinger (emergency third QB)", "WR Lil'Jordan Humphrey", "S Talanoa Hufanga",
      "S Brandon Jones", "CB Kris Abrams-Draine", "OL Kage Casey", "TE Dallen Bentley"],
     ["OLB Jaelan Phillips", "QB Haynes King (emergency third QB)", "CB Will Lee III",
      "RB AJ Dillon", "LB Bobby Okereke", "G Damien Lewis", "DT TeRah Edwards"]),
    ("cowboys-at-colts-2026-reg-9", "DAL", "IND", "1:00 p.m. ET",
     "Lucas Oil Stadium (Indianapolis)",
     ["LB DeMarvion Overshown", "WR George Pickens", "WR KaVontae Turpin", "CB Joey Porter Jr.",
      "LB Tyrus Wheat", "OL Ajani Cornelius", "TE Luke Schoonmaker"],
     ["TE Pharaoh Brown", "LB Akeem Davis-Gaither", "S A.J. Haulcy", "OT Charlie Heck",
      "QB Riley Leonard (emergency third QB)", "TE Will Mallory", "CB Justin Walley"]),
    ("jets-at-chiefs-2026-reg-9", "NYJ", "KC", "1:00 p.m. ET",
     "Arrowhead Stadium (Kansas City, Mo.)",
     ["OL Blake Freeland", "OL Kohl Levao", "Edge Joseph Ossai", "WR Tim Patrick",
      "LB Trevin Wallace", "WR Garrett Wilson", "CB Nahshon Wright"],
     ["CB Mansoor Delane", "QB Garrett Nussmeier", "FB Ben VanSumeren", "DE Jack Pyburn",
      "OT Diego Pounds", "DT Peter Woods"]),
    ("lions-at-dolphins-2026-reg-9", "DET", "MIA", "1:00 p.m. ET",
     "Hard Rock Stadium (Miami Gardens, Fla.)",
     ["CB D.J. Reed", "Edge DJ Wonnum", "C Cade Mays", "RB Jacob Saylors", "TE Jordan Meeks",
      "DL Mekhi Wingo", "Edge Ahmed Hassanein"],
     ["WR Jalen Tolbert", "RB Jaylen Wright", "CB Marcellas Dial Jr.", "CB Reese Taylor",
      "G Christian Haynes", "T Chukwuebuka Godrick", "TE Justin Joly"]),
    ("browns-at-saints-2026-reg-9", "CLE", "NO", "1:00 p.m. ET",
     "Caesars Superdome (New Orleans)",
     ["QB Deshaun Watson", "QB Taylen Green (emergency third QB)", "LB Justin Jefferson",
      "CB Noah Igbinoghene", "C Parker Brailsford", "DT Maliek Collins"],
     ["QB Zach Wilson (emergency third QB)", "S Mike Reid", "RB CJ Donaldson",
      "DL Christen Miller", "LB Jaylan Ford", "OT Mason Murphy", "DL John Ridgeway III"]),
    ("giants-at-eagles-2026-reg-9", "NYG", "PHI", "1:00 p.m. ET",
     "Lincoln Financial Field (Philadelphia)",
     ["TE Thomas Fidone II", "CB Colton Hood", "OT Marcus Mbow", "DL C.J. Okoye",
      "CB Nikko Reed", "OL Josh Sills", "RB Cam Skattebo"],
     ["WR Devonta Smith", "LB Jihaad Campbell", "WR Dontayvion Wicks", "CB Jonathan Jones",
      "CB Michael Carter II", "WR Britain Covey"]),
    ("rams-at-commanders-2026-reg-9", "LAR", "WAS", "1:00 p.m. ET",
     "Northwest Stadium (Landover, Md.)",
     ["QB Ty Simpson (emergency third QB)", "CB Trent McDuffie", "LS Joe Cardona",
      "OLB Darryl Peterson III", "OL Bill Murray", "OL Keagen Trost", "OLB Desjuan Johnson"],
     ["WR Treylon Burks", "QB Athan Kaliakmanis (emergency third QB)", "CB Fabian Moreau",
      "CB Isaac Yiadom", "G Tanoa Togiai"]),
    ("texans-at-chargers-2026-reg-9", "HOU", "LAC", "4:05 p.m. ET",
     "SoFi Stadium (Inglewood, Calif.)",
     ["S Reed Blankenship", "TE Cade Stover", "RB David Montgomery", "G Febechi Nwaiwu",
      "OT Braden Smith", "OT Nate Thomas"],
     ["S Kendall Williamson", "DB Deane Leonard", "G Kayode Awosika", "WR Theo Wease",
      "WR Brenen Thompson"]),
    ("raiders-at-49ers-2026-reg-9", "LV", "SF", "4:25 p.m. ET",
     "Levi's Stadium (Santa Clara, Calif.)",
     ["QB Aidan O'Connell (emergency third QB)", "WR Dont'e Thornton Jr.", "WR Malik Benson",
      "S Dalton Johnson", "G Bryce Cabeldue", "DT Thomas Booker IV"],
     ["QB Kurtis Rourke", "WR Mike Evans", "OL Enrique Cruz Jr.", "WR Deebo Samuel Sr.",
      "LB Tatum Bethune", "DL Khalid Kareem"]),
    ("packers-at-patriots-2026-reg-9", "GB", "NE", "4:25 p.m. ET",
     "Gillette Stadium (Foxborough, Mass.)",
     ["RB MarShawn Lloyd", "LB Zaire Franklin", "G Donovan Jennings", "G Sean Rhyan",
      "OT Travis Glover", "TE Josh Whyle"],
     ["WR A.J. Brown", "RB TreVeyon Henderson", "CB Charles Woods", "OT Dametrious Crownover",
      "QB Behren Morton"]),
    ("cardinals-at-seahawks-2026-reg-9", "AZ", "SEA", "4:25 p.m. ET",
     "Lumen Field (Seattle)",
     ["RB Bam Knight", "CB Starling Thomas V", "LB Eku Leota", "OL Jayden Williams",
      "OL Jon Gaines II", "OL Albert Reese IV"],
     ["LT Charles Cross", "QB Sam Darnold", "G Quenton Nelson", "LB Uchenna Nwosu",
      "NT Brandon Pili", "WR Rashid Shaheed", "DT Leonard Williams"]),
    ("buccaneers-at-bears-2026-reg-9", "TB", "CHI", "8:20 p.m. ET",
     "Soldier Field (Chicago)",
     ["OLB YaYa Diaby", "DL DeMonte Capehart", "G Billy Schrauth", "CB Ayden Garnes",
      "G Trevor Keegan"],
     ["QB Case Keenum (emergency third QB)", "DB Malik Muhammad", "RB Kyle Monangai",
      "LB Keyshaun Elliott", "DL Jayden Loving"]),
]

# ---------------------------------------------------------------------------
# S6 — November 2026 league trades
# ---------------------------------------------------------------------------
# (date, from_club, to_club, player, transaction)

TRADES_NOV_2026 = [
    ("11/10", "ATL", "JAX", "Jessie Bates", "Traded"),
    ("11/10", "PHI", "JAX", "Jordan Davis", "Traded"),
    ("11/10", "TEN", "BUF", "Amani Hooker", "Traded"),
    ("11/10", "IND", "SF", "Keenan Allen", "Traded"),
    ("11/10", "LV", "MIN", "Kirk Cousins", "Traded"),
    ("11/10", "LAC", "DEN", "Daiyan Henley", "Traded"),
    ("11/10", "IND", "KC", "Josh Downs", "Traded"),
    ("11/10", "ATL", "BAL", "Ryan Neuzil", "Traded"),
    ("11/10", "BAL", "ATL", "Andrew Vorhees", "Traded"),
    ("11/09", "NYJ", "DET", "Andre Cisco", "Traded"),
    ("11/09", "NO", "JAX", "Davon Godchaux", "Traded"),
    ("11/06", "AZ", "BAL", "Jacoby Brissett", "Traded"),
]

# ---------------------------------------------------------------------------
# S7 — November 2026 reserve list
# ---------------------------------------------------------------------------
# (date, club, player, transaction)

RESERVE_LIST_NOV_2026 = [
    ("11/14", "NO", "Christen Miller", "Reserve/Injured"),
    ("11/14", "NE", "TreVeyon Henderson", "Reserve/Injured"),
    ("11/14", "CLE", "Michael Burton", "Reserve/Injured"),
    ("11/14", "IND", "Mo Alie-Cox", "Reserve/Injured"),
    ("11/14", "IND", "Akeem Davis-Gaither", "Reserve/Injured"),
    ("11/14", "TEN", "Peter Skoronski", "Reserve/Injured"),
    ("11/14", "TEN", "Tommy Townsend", "Reserve/Injured"),
    ("11/14", "DAL", "Tyler Goodson", "Reserve/Injured"),
    ("11/14", "GB", "Josh Whyle", "Reserve/Injured"),
    ("11/12", "LA", "Puka Nacua", "Reserve/Injured"),
    ("11/10", "LA", "Jordan Whittington", "Reserve/Injured"),
    ("11/10", "MIA", "Zach Sieler", "Reserve/Injured"),
    ("11/10", "MIA", "Malik Willis", "Reserve/Injured"),
    ("11/10", "SF", "Gracen Halton", "Reserve/Injured"),
    ("11/10", "AZ", "Gardner Minshew", "Reserve/Injured"),
    ("11/10", "AZ", "Michael Wilson", "Reserve/Injured"),
    ("11/09", "TEN", "James Williams", "Reserve/Injured"),
    ("11/09", "MIN", "Demond Claiborne", "Reserve/Injured"),
    ("11/09", "BUF", "Josh Palmer", "Reserve/Injured"),
    ("11/07", "ATL", "Brian Robinson", "Reserve/Injured"),
    ("11/07", "LA", "Jaylen Watson", "Reserve/Injured"),
    ("11/07", "DEN", "Eyioma Uwazurike", "Reserve/Injured"),
    ("11/07", "DET", "Jack Campbell", "Reserve/Injured"),
    ("11/07", "DAL", "Malachi Lawrence", "Reserve/Injured"),
    ("11/07", "WAS", "Dyami Brown", "Reserve/Injured"),
]

# ---------------------------------------------------------------------------
# S8 / S9 — route probes for the depth-order question
# ---------------------------------------------------------------------------
# (route, url, http_result, depth_order_published, club_hosted_depth_link_found, notes)

DEPTH_ROUTE_PROBES = [
    ("nfl.com per-club depth chart", "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart",
     "HTTP 404 ('404 - Flag on the Play.')", "", "",
     "Route does not exist on nfl.com. No depth data can be published from it."),
    ("nfl.com per-club roster", "https://www.nfl.com/teams/kansas-city-chiefs/roster",
     "HTTP 200", "", "https://www.chiefs.com/team/depth-chart",
     "Publishes jersey number, position, roster status (ACT/RES/DEV/CUT/PUP/TRD), height, "
     "weight, experience and college. It publishes NO depth order. The page links a "
     "DEPTH CHART on the club's own site."),
]

#: Roster-status codes observed on S8 (no depth meaning is attached to any of them).
ROSTER_STATUS_CODES = ["ACT", "RES", "DEV", "CUT", "PUP", "TRD"]

#: One named fact verified from S8: the club the official injury report lists for a
#: player was checked against the official roster of that club.
# (player, club_in_injury_report, verified_on_official_roster, source)
CLUB_ATTRIBUTION_CHECKS = [
    ("Kenneth Walker III", "KC", "yes",
     "https://www.nfl.com/teams/kansas-city-chiefs/roster"),
]

# ---------------------------------------------------------------------------
# Official news items surfaced on S1's sidebar (headline + link only).
# These are dated official NFL.com stories; they are evidence that a fact is
# published, not a transcription of the fact itself unless noted.
# ---------------------------------------------------------------------------
# (date_in_story, headline, url)

OFFICIAL_NEWS_SURFACED = [
    ("2026-11-15",
     "Notable injuries, news from Sunday's Week 10 games: Jets QB Geno Smith suffers ankle injury vs. Bills",
     "https://www.nfl.com/news/notable-injuries-news-sunday-week-10-games-2026"),
    ("2026-11-15",
     "Patriots QB Drake Maye suffers ankle injury early in loss to Lions",
     "https://www.nfl.com/news/patriots-drake-maye-ankle-injury-lions"),
    ("2026-11-14",
     "NFL news roundup: Patriots place RB TreVeyon Henderson (illness) on injured reserve",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14"),
    ("2026-11-14",
     "Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
     "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    ("2026-11-13",
     "NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),
    ("2026-11-12",
     "NFL news roundup: Latest league updates from Thursday, Nov. 12",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-12"),
    ("2026-11-11",
     "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    ("2026-11-11",
     "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
     "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
    ("2026-11-10",
     "NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10"),
    ("2026-11-10",
     "Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL",
     "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl"),
    ("2026-11-10",
     "Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD",
     "https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week"),
    ("2026-11-10",
     "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again",
     "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"),
    ("2026-11-09",
     "NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-9"),
    ("2026-11-08",
     "NFL Week 9 inactives: Players ruled out for Sunday's 13 games",
     "https://www.nfl.com/news/nfl-week-9-inactives-players-ruled-out-sunday-2026-season"),
    ("2026-11-05",
     "NFL news roundup: Ravens officially place Lamar Jackson on injured reserve",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-5"),
]

#: Player-club identity map used only to normalise the club abbreviations. nfl.com
#: prints AZ on the injury/standings pages and ARI elsewhere (a known repo trap).
CLUB_ABBR_ALIASES = {
    "ARI": "AZ",
    "LA": "LAR",
}


# ---------------------------------------------------------------------------
# Price-capture attempts
# ---------------------------------------------------------------------------
# Every route considered for an operator price, and what reading it produced.
# (route, kind, result, what_the_page_actually_contains, conclusion)

PRICE_CAPTURE_ATTEMPTS = [
    ("https://www.nfl.com/injuries/", "official NFL page", "read, no price field",
     "player, position, injury, practice status, game status, kickoff, network, club record",
     "The official injury report carries no operator price for any market."),
    ("https://www.nfl.com/schedules/2026/by-week/week-10", "official NFL page",
     "read, no price field",
     "fixtures, kickoff date and time, network, final or live scores, bye panel",
     "The official schedule carries no spread, total or moneyline."),
    ("https://www.nfl.com/standings/division/2026/reg", "official NFL page",
     "read, no price field",
     "W, L, T, PCT, PF, PA, NET PTS, HOME, ROAD, DIV, CONF, STRK",
     "The official standings carry results, not prices."),
    ("operator sportsbook sites", "non-official commercial source", "not consulted",
     "",
     "Not an official source. Consulted prices would need a written data-use position "
     "first; without one the pack leaves every market cell blank (flag 48217-F01)."),
]


# ---------------------------------------------------------------------------
# Repository review findings
# ---------------------------------------------------------------------------
# (id, area, finding, how_it_was_checked, status, effect, source_url)
# status: verified-this-session | verified-in-repo | observed-needs-owner

REPO_FINDINGS = [
    ("RF-01", "Source routes",
     "nfl.com's per-club depth-chart route (nfl.com/teams/<club>/depth-chart) returns "
     "HTTP 404. The roster route on the same host returns 200 and links a depth chart on "
     "the club's own domain.",
     "Fetched both routes this session and read the responses.",
     "verified-this-session",
     "Any pack that plans to read depth from nfl.com cannot. The club-hosted route is "
     "unverified for the other 31 clubs.",
     "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart"),

    ("RF-02", "Source routes",
     "nfl.com/standings and nfl.com/injuries both render live. During a live week the "
     "standings already contain completed games, and the record badges beside each fixture "
     "on the injury page are post-game.",
     "Reconstructed the through-Week-9 table by subtraction and checked it 10/10 against "
     "the official pregame page; badges were then arithmetically confirmed as post-game.",
     "verified-this-session",
     "'Through week N' figures cannot be read straight off the page mid-week.",
     "https://www.nfl.com/standings/division/2026/reg"),

    ("RF-03", "Club identifiers",
     "The injury and standings pages print the club code AZ while the schedule page and the "
     "logo paths print ARI.",
     "Read both pages this session; the pack normalises with an alias map and asserts it in "
     "a test.",
     "verified-this-session",
     "Joins between availability data and schedule data silently drop Arizona.",
     "https://www.nfl.com/injuries/"),

    ("RF-04", "Source routes",
     "nfl.com/scores/2026/by-week/week-N returns 404; finals print on "
     "nfl.com/schedules/2026/by-week/week-N.",
     "This session used the /schedules/ route successfully for Week 10. The 404 was "
     "recorded by an earlier session in COORDINATION.md.",
     "verified-in-repo",
     "Scrapers pointed at /scores/ fail rather than returning an empty week.",
     "https://www.nfl.com/schedules/2026/by-week/week-10"),

    ("RF-05", "Official data quality",
     "The Week 10 injury report groups players under clubs that look wrong at first read "
     "(Kenneth Walker III under Kansas City). Checking the official roster confirmed the "
     "grouping: he is on the Kansas City roster.",
     "Read the Kansas City roster page end to end this session.",
     "verified-this-session",
     "The report's club attribution held on the one row checked. The other 346 rows are "
     "unchecked (flag 48217-F13).",
     "https://www.nfl.com/teams/kansas-city-chiefs/roster"),

    ("RF-06", "Official data quality",
     "The November 2026 reserve-list table's earliest row is dated 11/07, but an official "
     "NFL.com news story dated 2026-11-05 reports a Reserve/Injured move for Lamar "
     "Jackson that has no row in the table.",
     "Read the reserve-list route (both chunks) and the news list on the injury page.",
     "verified-this-session",
     "The reserve-list route may be truncated or paginated; a completeness check is needed "
     "before it is trusted as a full IR register (flag 48217-F15).",
     "https://www.nfl.com/transactions/league/reserve-list/2026/11"),

    ("RF-07", "Bye handling",
     "A club on bye has no section at all on the injury report. Four clubs are on bye in "
     "Week 10 (CHI, DEN, PHI, TB), so 28 clubs appear, not 32.",
     "Read the bye panel on the official schedule page and counted the sections on the "
     "injury page.",
     "verified-this-session",
     "An absence on the report must never be published as 'injury free'.",
     "https://www.nfl.com/schedules/2026/by-week/week-10"),

    ("RF-08", "Coverage gaps",
     "The by-week schedule page prints no venue. The official inactives page prints WHERE "
     "for every game it lists.",
     "Read both pages this session; 13 Week 9 venues were transcribed from the inactives "
     "page.",
     "verified-this-session",
     "Venue capture must use the inactives page or the game centre, not the schedule page.",
     "https://www.nfl.com/news/nfl-week-9-inactives-players-ruled-out-sunday-2026-season"),

    ("RF-09", "Cross-session consistency",
     "This session counted 347 rows on the Week 10 injury report. An earlier session "
     "(d966f630) independently recorded 347 rows for the same report.",
     "Compared counts recorded in COORDINATION.md against this session's transcription.",
     "verified-in-repo",
     "Two independent readings agree, which is a consistency signal for both.",
     "https://www.nfl.com/injuries/"),

    ("RF-10", "Repository structure",
     "Eight self-contained NFL packs now live under docs/, each with its own data, builder, "
     "checker and tests, covering overlapping requirements.",
     "Listed docs/ and data/ and read COORDINATION.md.",
     "observed-needs-owner",
     "A reader cannot tell which pack is authoritative. The decision-readiness register on "
     "the landing page is this pack's answer to that.",
     "https://github.com/sassnarep3-star/Own6"),

    ("RF-11", "Shared tooling",
     "scripts/source_coverage.py PUBLISHERS and tools/release_gate.py OFFICIAL_HOSTS both "
     "omit www.nfl.com, so rows citing official NFL pages are classified as secondary by "
     "the repo-wide tools even when the citation is correct.",
     "Read both files this session.",
     "observed-needs-owner",
     "Every NFL pack inherits the misclassification. Recorded as request R7; this pack "
     "enforces the NFL allowlist in its own checker instead of editing shared tooling.",
     "https://github.com/sassnarep3-star/Own6"),

    ("RF-12", "Shared tooling",
     "data/assurance/inventory.csv hashes every tracked text file including COORDINATION.md, "
     "and a test asserts those hashes, so any append to the coordination board turns the "
     "repo suite red until the generator is re-run.",
     "Recorded in COORDINATION.md by session d966f630; confirmed by reading the file list.",
     "verified-in-repo",
     "Bookkeeping edits break the build for every session. Logged as request R8.",
     "https://github.com/sassnarep3-star/Own6"),

    ("RF-13", "Season scope",
     "The reconstructed through-Week-9 table implies exactly 136 completed games, which "
     "matches the 136-game log the brief refers to.",
     "Summed team-games across the 32 reconstructed rows and halved; the points-for and "
     "points-against totals also balance.",
     "verified-this-session",
     "The brief's figure is confirmed arithmetically, so the corpus target is well defined.",
     "https://www.nfl.com/standings/division/2026/reg"),
]
