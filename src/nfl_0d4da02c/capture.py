"""Raw as-read capture for pack nfl_0d4da02c (session 0d4da02c, read 2026-11-18).

Every string in this file was transcribed from the official page named in
``SOURCES`` during the capture window recorded in ``READS``. Nothing is
inferred, nothing is filled in. A field that was blank on the page is written
as an empty string, and the downstream builder is required to render it as a
blank cell and flag it.

The three practice-status shorthands used below expand to the exact official
page text (the mapping is asserted in ``tests/test_nfl_0d4da02c.py``):

    FP  -> "Full Participation in Practice"
    LP  -> "Limited Participation in Practice"
    DNP -> "Did Not Participate In Practice"

Run:  python3 -m src.nfl_0d4da02c.capture
Out:  data/nfl_0d4da02c/*.csv
"""
from __future__ import annotations

import csv
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl_0d4da02c")

READ_DATE = "2026-11-18"
READ_WINDOW = "2026-11-18 (session 0d4da02c; single manual read per page)"

INJ_URL = "https://www.nfl.com/injuries/"
INJ_CANON = "https://www.nfl.com/injuries/league/2026/reg10"
SCHED_URL = "https://www.nfl.com/schedules/2026/REG11/"
SCHED_CANON = "https://www.nfl.com/schedules/2026/by-week/week-11"

PRACTICE = {
    "FP": "Full Participation in Practice",
    "LP": "Limited Participation in Practice",
    "DNP": "Did Not Participate In Practice",
}

# ---------------------------------------------------------------------------
# 1. Official NFL injury report, WEEK 10 of the 2026 season.
#    Read 2026-11-18 from https://www.nfl.com/injuries/ .
#    The page's own canonical URL is .../injuries/league/2026/reg10 and its
#    <h1> reads "Injuries - WEEK 10". A request for .../2026/REG11/ resolves
#    to the same Week 10 page (see READS note R-W11), i.e. the Week 11 report
#    was NOT published at read time.
#    Rows are (player, position, injuries, practice, game_status).
#    Clubs on a Week 10 bye are simply absent from the page: CHI, DEN, PHI, TB.
# ---------------------------------------------------------------------------
INJURY: dict[str, tuple[str, list[tuple[str, str, str, str, str]]]] = {
    # --- THURSDAY, NOVEMBER 12TH -------------------------------------------
    "WAS": ("WAS @ NYG, Thu Nov 12, 8:15 PM ET, Prime Video", [
        ("John Bates", "TE", "", "FP", ""),
        ("Treylon Burks", "WR", "", "DNP", ""),
        ("Jayden Daniels", "QB", "", "FP", ""),
        ("Matt Gulbin", "C", "", "FP", ""),
        ("Chig Okonkwo", "TE", "", "FP", ""),
        ("Lucas Patrick", "C", "Concussion", "DNP", "Out"),
        ("Amik Robertson", "CB", "", "LP", ""),
        ("Shy Tuttle", "DT", "", "FP", ""),
        ("Colson Yankoff", "TE", "Knee", "DNP", "Out"),
    ]),
    "NYG": ("WAS @ NYG, Thu Nov 12, 8:15 PM ET, Prime Video", [
        ("Abdul Carter", "LB", "", "FP", ""),
        ("Jermaine Eluemunor", "T", "", "FP", ""),
        ("Malik Harrison", "LB", "Groin", "LP", "Questionable"),
        ("Colton Hood", "CB", "", "FP", ""),
        ("Theo Johnson", "TE", "", "FP", ""),
        ("Charlie Jones", "WR", "", "FP", ""),
        ("J.J. McCarthy", "QB", "", "FP", ""),
        ("Darnell Mooney", "WR", "", "FP", ""),
        ("Malik Nabers", "WR", "", "FP", ""),
        ("Cam Skattebo", "RB", "", "FP", ""),
        ("Andrew Thomas", "T", "", "FP", ""),
    ]),
    # --- SUNDAY, NOVEMBER 15TH ---------------------------------------------
    "NE": ("NE @ DET, Sun Nov 15, 9:30 AM ET, FOX", [
        ("Ben Brown", "C", "Knee", "DNP", "Out"),
        ("A.J. Brown", "WR", "Ankle, Knee", "LP", "Questionable"),
        ("Kevin Byard", "S", "Chest", "FP", "Questionable"),
        ("Carlton Davis III", "CB", "Knee", "DNP", "Out"),
        ("Reggie Gilliam", "FB", "Knee", "LP", "Questionable"),
        ("TreVeyon Henderson", "RB", "Illness", "DNP", "Out"),
        ("Hunter Henry", "TE", "", "LP", ""),
        ("Cameron Latu", "TE", "Back", "LP", "Questionable"),
        ("Drake Maye", "QB", "", "FP", ""),
        ("Morgan Moses", "T", "", "FP", ""),
        ("Walter Rouse", "T", "Concussion", "LP", "Questionable"),
        ("Brenden Schooler", "S", "Hamstring", "LP", "Questionable"),
        ("Rhamondre Stevenson", "RB", "Knee", "LP", "Questionable"),
        ("Greg Van Roten", "G", "Hamstring", "FP", "Questionable"),
        ("Charles Woods", "CB", "Hamstring", "FP", "Questionable"),
    ]),
    "DET": ("NE @ DET, Sun Nov 15, 9:30 AM ET, FOX", [
        ("Brian Branch", "S", "", "FP", ""),
        ("Jared Goff", "QB", "", "FP", ""),
        ("Kerby Joseph", "S", "Knee", "DNP", "Out"),
        ("Cade Mays", "C", "Ankle", "DNP", "Out"),
        ("D.J. Reed", "CB", "Hip", "DNP", "Out"),
        ("Jacob Saylors", "RB", "", "FP", ""),
        ("Amon-Ra St. Brown", "WR", "Rib", "LP", "Questionable"),
        ("Sione Vaki", "RB", "Ankle", "LP", "Questionable"),
        ("DJ Wonnum", "DE", "", "FP", ""),
    ]),
    "KC": ("KC @ ATL, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Jeffrey Bassa", "LB", "", "FP", ""),
        ("Mansoor Delane", "CB", "Shoulder", "FP", "Questionable"),
        ("Justin Fields", "QB", "", "FP", ""),
        ("Jaden Hicks", "S", "", "FP", ""),
        ("Travis Kelce", "TE", "", "FP", ""),
        ("Patrick Mahomes", "QB", "", "FP", ""),
        ("Jaylon Moore", "T", "Ankle", "DNP", "Out"),
        ("Omarr Norman-Lott", "DT", "Knee", "LP", "Out"),
        ("Jaydn Ott", "RB", "Hamstring", "LP", "Questionable"),
        ("Rashee Rice", "WR", "", "FP", ""),
        ("Kenneth Walker III", "RB", "Groin", "DNP", "Questionable"),
        ("Peter Woods", "DT", "Neck", "DNP", "Out"),
        ("Xavier Worthy", "WR", "", "FP", ""),
    ]),
    "ATL": ("KC @ ATL, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Zachariah Branch", "WR", "Hamstring", "DNP", "Out"),
        ("Kendal Daniels", "LB", "", "FP", ""),
        ("Divine Deablo", "LB", "Forearm", "DNP", "Doubtful"),
        ("Gervon Dexter Sr.", "DT", "Illness", "LP", "Questionable"),
        ("Jake Matthews", "T", "", "LP", ""),
        ("Liam McCullough", "LS", "", "DNP", ""),
        ("James Pearce Jr.", "DE", "Back", "LP", "Questionable"),
        ("Za'Darius Smith", "DE", "", "FP", ""),
        ("Jawaan Taylor", "T", "", "LP", ""),
        ("Cameron Thomas", "DE", "", "FP", ""),
        ("Josh Woods", "LB", "Ankle", "FP", "Questionable"),
    ]),
    "MIN": ("MIN @ GB, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Jordan Addison", "WR", "Thumb", "LP", "Questionable"),
        ("Blake Cashman", "LB", "Concussion", "LP", "Out"),
        ("Christian Darrisaw", "T", "", "DNP", ""),
        ("T.J. Hockenson", "TE", "Wrist, Chest", "DNP", "Out"),
        ("Tyrion Ingram-Dawkins", "DT", "Ankle", "DNP", "Out"),
        ("Theo Jackson", "S", "", "FP", ""),
        ("Jauan Jennings", "WR", "Calf", "DNP", "Out"),
        ("Josh Metellus", "S", "Shoulder", "LP", "Questionable"),
        ("Kyler Murray", "QB", "Hamstring", "DNP", "Out"),
        ("Harrison Smith", "S", "", "LP", ""),
        ("Kyle Van Noy", "LB", "Calf", "LP", "Questionable"),
        ("Jay Ward", "S", "", "FP", ""),
        ("Carson Wentz", "QB", "", "FP", ""),
    ]),
    "GB": ("MIN @ GB, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Aaron Banks", "G", "", "LP", ""),
        ("Chris Brooks", "RB", "Ankle", "LP", "Questionable"),
        ("Javon Bullard", "S", "Ankle, Knee", "LP", "Questionable"),
        ("Zaire Franklin", "LB", "Shin", "DNP", "Doubtful"),
        ("Travis Glover", "G", "Knee", "LP", "Questionable"),
        ("Ty'Ron Hopper", "LB", "", "FP", ""),
        ("Josh Jacobs", "RB", "Finger", "DNP", "Out"),
        ("Xavier McKinney", "S", "Foot", "LP", "Questionable"),
        ("Bo Melton", "WR", "", "FP", ""),
        ("Skyy Moore", "WR", "Ankle", "LP", "Questionable"),
        ("Micah Parsons", "LB", "Knee, Illness", "LP", "Out"),
        ("Sean Rhyan", "C", "Ankle", "DNP", "Out"),
        ("Trey Smack", "K", "", "FP", ""),
        ("Lukas Van Ness", "LB", "Back", "LP", "Questionable"),
        ("Josh Whyle", "TE", "Concussion", "DNP", "Out"),
        ("Savion Williams", "WR", "", "LP", ""),
        ("Kevin Zeitler", "G", "Ankle, Triceps", "DNP", "Questionable"),
    ]),
    "JAX": ("JAX @ TEN, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Jessie Bates", "S", "Not injury related - resting player", "LP", "Out"),
        ("Ezra Cleveland", "G", "", "FP", ""),
        ("Branson Combs", "LB", "", "FP", ""),
        ("Jordan Davis", "DT", "Not injury related - resting player", "LP", "Out"),
        ("BJ Green II", "DE", "Forearm", "FP", "Out"),
        ("Robert Hainsey", "C", "Concussion", "LP", "Questionable"),
        ("Antonio Johnson", "S", "", "LP", ""),
        ("Jakobi Meyers", "WR", "", "LP", ""),
        ("Chris Rodriguez Jr.", "RB", "", "LP", ""),
        ("Bhayshul Tuten", "RB", "", "LP", ""),
        ("Travon Walker", "DE", "", "LP", ""),
    ]),
    "TEN": ("JAX @ TEN, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Cody Barton", "LB", "Concussion", "DNP", "Out"),
        ("John Franklin-Myers", "DE", "", "FP", ""),
        ("Marcus Harris", "CB", "", "FP", ""),
        ("Anthony Hill Jr.", "LB", "Neck", "DNP", "Out"),
        ("Jaylon Jones", "CB", "", "FP", ""),
        ("JC Latham", "T", "", "FP", ""),
        ("Tony Pollard", "RB", "", "FP", ""),
        ("Peter Skoronski", "G", "Hamstring", "DNP", "Out"),
        ("Tyjae Spears", "RB", "Knee", "FP", "Questionable"),
        ("Carnell Tate", "WR", "Shoulder", "DNP", "Out"),
        ("Tommy Townsend", "P", "Knee, Achilles", "DNP", "Out"),
        ("Kevin Winston Jr.", "S", "", "FP", ""),
    ]),
    "BUF": ("BUF @ NYJ, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Alec Anderson", "G", "", "FP", ""),
        ("Christian Benford", "CB", "Wrist", "FP", "Questionable"),
        ("Terrel Bernard", "LB", "", "DNP", ""),
        ("Spencer Brown", "T", "Ankle", "DNP", "Doubtful"),
        ("Dion Dawkins", "T", "", "FP", ""),
        ("Sam Franklin Jr.", "S", "Shoulder", "LP", "Questionable"),
        ("Greg Gaines", "DT", "", "FP", ""),
        ("Jordan Hancock", "CB", "Hamstring", "FP", "Questionable"),
        ("Dalton Kincaid", "TE", "", "FP", ""),
        ("Connor McGovern", "C", "", "FP", ""),
        ("Ed Oliver", "DE", "", "DNP", ""),
        ("Ar'maj Reed-Adams", "G", "", "FP", ""),
        ("T.J. Sanders", "DE", "", "FP", ""),
        ("Tyrell Shavers", "WR", "Knee", "FP", "Questionable"),
    ]),
    "NYJ": ("BUF @ NYJ, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Jarvis Brownlee Jr.", "CB", "Illness", "LP", "Questionable"),
        ("Omar Cooper Jr.", "WR", "Ankle", "FP", "Questionable"),
        ("Adonai Mitchell", "WR", "Knee", "FP", "Questionable"),
        ("Joseph Ossai", "DE", "Ankle", "FP", "Questionable"),
        ("VJ Payne", "S", "Knee", "FP", "Questionable"),
        ("Harrison Phillips", "DT", "Ankle", "FP", "Questionable"),
        ("Trevin Wallace", "LB", "Groin", "DNP", "Out"),
        ("Garrett Wilson", "WR", "Concussion", "FP", "Questionable"),
        ("Nahshon Wright", "CB", "Back", "FP", "Questionable"),
    ]),
    "MIA": ("MIA @ IND, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Tucker Addington", "LS", "", "LP", ""),
        ("Kaytron Allen", "RB", "", "FP", ""),
        ("Darrell Baker Jr.", "CB", "Knee", "FP", "Questionable"),
        ("Chris Bell", "WR", "Knee", "DNP", "Doubtful"),
        ("Aaron Brewer", "C", "Concussion", "DNP", "Out"),
        ("Malik Herring", "DE", "", "FP", ""),
        ("Will Kacmarek", "TE", "", "FP", ""),
        ("Michael Taaffe", "S", "", "FP", ""),
        ("Dante Trader Jr.", "S", "", "FP", ""),
        ("Jared Wayne", "WR", "Quadricep", "DNP", "Out"),
        ("Jaylen Wright", "RB", "", "FP", ""),
    ]),
    "IND": ("MIA @ IND, Sun Nov 15, 1:00 PM ET, CBS", [
        ("Mo Alie-Cox", "TE", "Groin", "DNP", "Out"),
        ("CJ Allen", "LB", "", "FP", ""),
        ("Jaylon Carlies", "LB", "Neck", "DNP", "Out"),
        ("Akeem Davis-Gaither", "LB", "Knee", "DNP", "Out"),
        ("A.J. Haulcy", "S", "", "FP", ""),
        ("Arden Key", "DE", "", "FP", ""),
        ("Will Mallory", "TE", "Hamstring", "LP", "Questionable"),
        ("Luke Rhodes", "LS", "Hamstring", "DNP", "Out"),
        ("Grover Stewart", "DT", "", "FP", ""),
        ("Jonathan Taylor", "RB", "", "FP", ""),
        ("Jerry Tillery", "DT", "Calf", "DNP", "Out"),
        ("Jalen Travis", "T", "Knee", "DNP", "Out"),
        ("Justin Walley", "CB", "", "FP", ""),
        ("Charvarius Ward", "CB", "", "FP", ""),
    ]),
    "CAR": ("CAR @ NO, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Jonathon Brooks", "RB", "Groin", "LP", "Doubtful"),
        ("Brady Christensen", "G", "Hamstring", "FP", "Questionable"),
        ("Trevor Etienne", "RB", "", "FP", ""),
        ("Chuba Hubbard", "RB", "", "FP", ""),
        ("Lee Hunter", "DT", "", "FP", ""),
        ("Mike Jackson", "CB", "Groin", "LP", "Doubtful"),
        ("Will Lee III", "CB", "Hamstring", "LP", "Questionable"),
        ("Xavier Legette", "WR", "Knee", "FP", "Questionable"),
        ("Damien Lewis", "G", "", "FP", ""),
        ("Bobby Okereke", "LB", "Foot", "DNP", "Out"),
        ("Jaelan Phillips", "LB", "Hamstring", "FP", "Questionable"),
        ("Torricelli Simpkins III", "G", "", "FP", ""),
    ]),
    "NO": ("CAR @ NO, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Kelvin Banks Jr.", "T", "", "FP", ""),
        ("CJ Donaldson", "RB", "Shoulder", "DNP", "Out"),
        ("David Edwards", "G", "", "FP", ""),
        ("Martin Emerson", "CB", "Shin", "LP", "Questionable"),
        ("Travis Etienne", "RB", "Hamstring", "FP", "Questionable"),
        ("Noah Fant", "TE", "", "FP", ""),
        ("Taliese Fuaga", "T", "Knee", "DNP", "Out"),
        ("Alvin Kamara", "RB", "", "FP", ""),
        ("Erik McCoy", "C", "Biceps", "DNP", "Out"),
        ("Christen Miller", "DT", "Knee", "DNP", "Out"),
        ("Asim Richards", "T", "", "FP", ""),
        ("Quincy Riley", "CB", "", "FP", ""),
    ]),
    "HOU": ("HOU @ CLE, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Azeez Al-Shaair", "LB", "Groin, Not injury related - personal matter", "DNP", "Out"),
        ("Will Anderson Jr.", "DE", "Ankle", "DNP", "Questionable"),
        ("Reed Blankenship", "S", "", "FP", ""),
        ("Trent Brown", "T", "Wrist, Illness", "DNP", "Questionable"),
        ("Tank Dell", "WR", "", "FP", ""),
        ("Blake Fisher", "T", "", "FP", ""),
        ("Marvin Harrison Jr.", "WR", "Hamstring", "DNP", "Out"),
        ("Jacob Hummel", "LB", "Groin", "FP", "Questionable"),
        ("Danielle Hunter", "DE", "Hamstring", "DNP", "Out"),
        ("Brevin Jordan", "TE", "Finger, Foot", "DNP", "Out"),
        ("Woody Marks", "RB", "", "FP", ""),
        ("David Montgomery", "RB", "Groin", "FP", "Questionable"),
        ("Keylan Rutledge", "G", "Neck, Shoulder", "DNP", "Out"),
        ("Jaylin Smith", "CB", "Hamstring", "FP", "Questionable"),
        ("Wyatt Teller", "G", "Illness, Back", "LP", "Questionable"),
        ("Tommy Togiai", "DT", "", "FP", ""),
    ]),
    "CLE": ("HOU @ CLE, Sun Nov 15, 1:00 PM ET, FOX", [
        ("Austin Barber", "T", "", "FP", ""),
        ("Denzel Boston", "WR", "Toe", "LP", "Questionable"),
        ("Michael Burton", "FB", "Calf", "DNP", "Out"),
        ("Maliek Collins", "DT", "", "FP", ""),
        ("Harold Fannin Jr.", "TE", "", "FP", ""),
        ("Ronnie Hickman Jr.", "S", "Concussion", "DNP", "Out"),
        ("Tytus Howard", "T", "", "FP", ""),
        ("Elgton Jenkins", "C", "", "FP", ""),
        ("Donovan McMillon", "S", "", "LP", ""),
        ("Carson Schwesinger", "LB", "", "FP", ""),
        ("Denzel Ward", "CB", "", "LP", ""),
        ("Quincy Williams", "LB", "", "FP", ""),
    ]),
    "LAR": ("LAR @ AZ, Sun Nov 15, 4:05 PM ET, CBS", [
        ("Davis Allen", "TE", "Oblique", "LP", "Questionable"),
        ("Steve Avila", "G", "Hamstring", "DNP", "Out"),
        ("Joe Cardona", "LS", "Ankle", "LP", "Questionable"),
        ("Kam Curl", "S", "Toe", "LP", "Questionable"),
        ("Aaron Donald", "DT", "", "DNP", ""),
        ("Terrance Ferguson", "TE", "Ankle, Hamstring", "DNP", "Out"),
        ("Braden Fiske", "DT", "", "DNP", ""),
        ("Myles Garrett", "LB", "Knee, Not injury related - resting player", "DNP", "Questionable"),
        ("Tyler Higbee", "TE", "", "LP", ""),
        ("Trent McDuffie", "CB", "Back", "LP", "Questionable"),
        ("Puka Nacua", "WR", "", "DNP", ""),
        ("Colby Parkinson", "TE", "", "FP", ""),
        ("Matthew Stafford", "QB", "", "FP", ""),
        ("Byron Young", "LB", "", "DNP", ""),
    ]),
    "AZ": ("LAR @ AZ, Sun Nov 15, 4:05 PM ET, CBS", [
        ("Budda Baker", "S", "", "FP", ""),
        ("Zachary Carter", "DT", "Knee", "LP", "Out"),
        ("Hjalte Froholdt", "C", "Concussion", "DNP", "Out"),
        ("Jon Gaines II", "G", "Ankle", "DNP", "Out"),
        ("Bam Knight", "RB", "", "FP", ""),
        ("Hunter Long", "TE", "Knee", "LP", "Questionable"),
        ("Roy Lopez", "DT", "Toe, Ankle", "LP", "Questionable"),
        ("Max Melton", "CB", "Knee, Hand", "LP", "Questionable"),
        ("Darius Robinson", "DT", "Wrist", "LP", "Questionable"),
        ("Isaac Seumalo", "G", "", "FP", ""),
        ("Dante Stills", "DT", "", "FP", ""),
        ("Josh Sweat", "LB", "", "FP", ""),
        ("Jayden Williams", "T", "Knee", "LP", "Questionable"),
        ("Mack Wilson", "LB", "", "FP", ""),
        ("Andrew Wingard", "S", "Groin", "DNP", "Questionable"),
    ]),
    "SEA": ("SEA @ LV, Sun Nov 15, 4:05 PM ET, CBS", [
        ("AJ Barner", "TE", "", "FP", ""),
        ("Anthony Bradford", "G", "", "FP", ""),
        ("Charles Cross", "T", "Ankle", "DNP", "Out"),
        ("Sam Darnold", "QB", "Ribs, Quadricep", "DNP", "Out"),
        ("Derick Hall", "LB", "", "DNP", ""),
        ("Drew Lock", "QB", "", "LP", ""),
        ("Quenton Nelson", "G", "Knee", "DNP", "Out"),
        ("Uchenna Nwosu", "LB", "", "FP", ""),
        ("Patrick O'Connell", "LB", "", "FP", ""),
        ("Connor O'Toole", "LB", "", "FP", ""),
        ("Brandon Pili", "DT", "", "FP", ""),
        ("Jarran Reed", "DT", "", "FP", ""),
        ("Rashid Shaheed", "WR", "", "FP", ""),
        ("Jaxon Smith-Njigba", "WR", "", "FP", ""),
        ("Leonard Williams", "DT", "Stinger", "DNP", "Out"),
    ]),
    "LV": ("SEA @ LV, Sun Nov 15, 4:05 PM ET, CBS", [
        ("Thomas Booker", "DT", "Ankle", "FP", "Questionable"),
        ("Foley Fatukasi", "DT", "", "FP", ""),
        ("Ian Thomas", "TE", "", "FP", ""),
        ("Dont'e Thornton Jr.", "WR", "Back", "DNP", "Questionable"),
        ("Trey Zuhn III", "C", "", "FP", ""),
    ]),
    "SF": ("SF @ DAL, Sun Nov 15, 4:25 PM ET, FOX, FOX DEPORTES", [
        ("Mike Evans", "WR", "Achilles", "DNP", "Out"),
        ("Renardo Green", "CB", "Back", "LP", "Questionable"),
        ("Dre Greenlaw", "LB", "Knee", "LP", "Questionable"),
        ("Nate Hobbs", "CB", "Groin", "FP", "Questionable"),
        ("Deommodore Lenoir", "CB", "Foot", "LP", "Questionable"),
        ("Christian McCaffrey", "RB", "", "FP", ""),
        ("Siran Neal", "S", "", "FP", ""),
        ("Demarcus Robinson", "WR", "", "FP", ""),
        ("Deebo Samuel Sr.", "WR", "", "FP", ""),
        ("Upton Stout", "CB", "Shoulder, Neck", "LP", "Questionable"),
        ("C.J. West", "DT", "Knee", "FP", "Questionable"),
        ("Trent Williams", "T", "Shoulder", "DNP", "Questionable"),
    ]),
    "DAL": ("SF @ DAL, Sun Nov 15, 4:25 PM ET, FOX, FOX DEPORTES", [
        ("DaRon Bland", "CB", "Ankle", "LP", "Questionable"),
        ("Jonathan Bullard", "DT", "Calf", "FP", "Questionable"),
        ("Alijah Clark", "S", "Illness", "DNP", "Questionable"),
        ("Donovan Ezeiruaku", "LB", "Ankle", "DNP", "Out"),
        ("Jake Ferguson", "TE", "Knee, Ankle", "DNP", "Out"),
        ("Tyler Goodson", "RB", "Ankle, Knee", "DNP", "Out"),
        ("Malik Hooker", "S", "", "DNP", ""),
        ("Marist Liufau", "LB", "", "FP", ""),
        ("P.J. Locke", "S", "Concussion", "DNP", "Out"),
        ("Von Miller", "LB", "", "DNP", ""),
        ("Jonathan Mingo", "WR", "Ankle", "DNP", "Out"),
        ("Devin Moore", "CB", "Hip", "FP", "Questionable"),
        ("DeMarvion Overshown", "LB", "", "FP", ""),
        ("George Pickens", "WR", "", "FP", ""),
        ("Joey Porter Jr.", "CB", "Ankle, Foot", "LP", "Questionable"),
        ("Luke Schoonmaker", "TE", "", "FP", ""),
        ("Brevyn Spann-Ford", "TE", "", "FP", ""),
        ("Juanyeh Thomas", "S", "Hamstring", "DNP", "Doubtful"),
        ("KaVontae Turpin", "WR", "", "FP", ""),
    ]),
    "PIT": ("PIT @ CIN, Sun Nov 15, 8:20 PM ET, NBC, UNIVERSO", [
        ("Brandin Echols", "CB", "", "FP", ""),
        ("DeShon Elliott", "S", "", "FP", ""),
        ("Derrick Harmon", "DT", "Foot", "FP", "Questionable"),
        ("Cameron Heyward", "DT", "", "FP", ""),
        ("Ben Skowronek", "WR", "", "FP", ""),
        ("Doneiko Slaughter", "CB", "", "FP", ""),
        ("Darnell Washington", "TE", "", "FP", ""),
        ("T.J. Watt", "LB", "", "FP", ""),
    ]),
    "CIN": ("PIT @ CIN, Sun Nov 15, 8:20 PM ET, NBC, UNIVERSO", [
        ("Jonathan Allen", "DT", "", "LP", ""),
        ("Jalen Davis", "CB", "Hamstring", "FP", "Doubtful"),
        ("Kyle Dugger", "S", "Quadricep", "DNP", "Out"),
        ("Dylan Fairchild", "G", "", "FP", ""),
        ("B.J. Hill", "DT", "", "DNP", ""),
        ("Andrei Iosivas", "WR", "Thumb", "FP", "Doubtful"),
        ("Dexter Lawrence", "DT", "", "DNP", ""),
        ("Brian Parker II", "G", "Knee", "FP", "Doubtful"),
        ("DJ Turner II", "CB", "", "FP", ""),
    ]),
    # --- MONDAY, NOVEMBER 16TH ----------------------------------------------
    "LAC": ("LAC @ BAL, Mon Nov 16, 8:15 PM ET, ESPN, ABC, ESPN2, ESPN DEPORTES", [
        ("Kayode Awosika", "G", "Fibula", "FP", "Questionable"),
        ("Bud Dupree", "DE", "", "FP", ""),
        ("Justin Eboigbe", "DE", "Ankle", "LP", "Questionable"),
        ("Alex Harkey", "G", "", "FP", ""),
        ("Tre Harris", "WR", "", "FP", ""),
        ("Cam Hart", "CB", "", "FP", ""),
        ("Daiyan Henley", "LB", "", "FP", ""),
        ("Deane Leonard", "CB", "", "FP", ""),
        ("Khalil Mack", "LB", "", "FP", ""),
        ("Ladd McConkey", "WR", "Back", "DNP", "Questionable"),
        ("Keaton Mitchell", "RB", "", "FP", ""),
        ("David Njoku", "TE", "Fibula", "FP", "Questionable"),
        ("Denzel Perryman", "LB", "Pectoral", "FP", "Questionable"),
        ("Trey Pipkins", "T", "Not injury related - personal matter, Knee", "LP", "Questionable"),
        ("Rodney Shelley", "CB", "", "FP", ""),
        ("Branson Taylor", "G", "Ankle", "DNP", "Out"),
        ("Brenen Thompson", "WR", "Hamstring", "DNP", "Doubtful"),
        ("Isas Waxter", "CB", "Ankle", "DNP", "Out"),
        ("Kendall Williamson", "S", "Calf", "DNP", "Out"),
    ]),
    "BAL": ("LAC @ BAL, Mon Nov 16, 8:15 PM ET, ESPN, ABC, ESPN2, ESPN DEPORTES", [
        ("Rasheen Ali", "RB", "", "FP", ""),
        ("Rashod Bateman", "WR", "", "FP", ""),
        ("Calais Campbell", "DT", "", "DNP", ""),
        ("Kyle Hamilton", "S", "", "FP", ""),
        ("Jaylinn Hawkins", "S", "Knee", "LP", "Out"),
        ("Matthew Hibner", "TE", "", "FP", ""),
        ("Olaivavega Ioane", "G", "", "FP", ""),
        ("Adam Randall", "RB", "Neck, Hamstring", "FP", "Questionable"),
        ("Ronnie Stanley", "T", "", "DNP", ""),
        ("Nate Wiggins", "CB", "", "FP", ""),
    ]),
}

# Clubs with no injury section on the Week 10 page (Week 10 bye). Never
# treated as "healthy" — the page simply does not list them.
WEEK10_ABSENT_CLUBS = ["CHI", "DEN", "PHI", "TB"]

# ---------------------------------------------------------------------------
# 2. Week 11 schedule, read 2026-11-18 from https://www.nfl.com/schedules/2026/REG11/
#    Columns: date, time_et, network, away, away_record, home, home_record,
#             venue_text_on_page, game_url.
#    ``venue_text_on_page`` is the venue string as it appears on the official
#    schedule page. For twelve games the only venue-bearing text on the page is
#    the destination parameter of the page's own "Hotel" affiliate link; that
#    provenance is recorded in the ``venue_provenance`` column and every such
#    row is flagged for review (F-VENUE).
# ---------------------------------------------------------------------------
WEEK11_GAMES: list[tuple[str, ...]] = [
    ("2026-11-19", "8:15 PM", "PRIME", "IND", "3-7", "HOU", "3-6",
     "NRG Stadium", "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "MIA", "1-8", "BUF", "8-1",
     "Highmark Stadium", "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "BAL", "4-6", "CAR", "4-5",
     "Bank of America Stadium", "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "NO", "3-6", "CHI", "7-2",
     "Soldier Field", "https://www.nfl.com/games/saints-at-bears-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "TEN", "1-8", "DAL", "4-6",
     "AT&T Stadium", "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "FOX", "TB", "3-6", "DET", "7-2",
     "Ford Field", "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "AZ", "3-7", "KC", "7-2",
     "GEHA Field at Arrowhead Stadium", "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11"),
    ("2026-11-22", "1:00 PM", "CBS", "PIT", "6-3", "PHI", "2-7",
     "Lincoln Financial Field", "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11"),
    ("2026-11-22", "4:05 PM", "FOX", "NYJ", "2-8", "LAC", "1-8",
     "SoFi Stadium", "https://www.nfl.com/games/jets-at-chargers-2026-reg-11"),
    ("2026-11-22", "4:25 PM", "CBS", "JAX", "7-2", "NYG", "5-3-1",
     "MetLife Stadium", "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11"),
    ("2026-11-22", "4:25 PM", "CBS", "LV", "4-6", "DEN", "7-2",
     "Empower Field at Mile High", "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11"),
    ("2026-11-22", "8:20 PM", "NBC", "MIN", "7-2", "SF", "8-1",
     "Mexico City", "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
    ("2026-11-23", "8:15 PM", "ESPN", "CIN", "7-2", "WAS", "3-5-1",
     "FedEx Field", "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11"),
]

# Only the MIN @ SF row was labelled directly on the page (a "Mexico City"
# badge and the Mexico City 2026 logo); every other venue string comes from
# the destination parameter of the page's own "Hotel" affiliate link.
DIRECT_VENUE_LABEL = {"MIN@SF"}

WEEK11_BYES: list[tuple[str, str]] = [
    ("ATL", "3-7"), ("CLE", "6-4"), ("GB", "6-4"),
    ("LAR", "6-4"), ("NE", "5-5"), ("SEA", "6-4"),
]

# ---------------------------------------------------------------------------
# 3. The "2026 TBD Games" announcement block, verbatim from the same official
#    schedule page (read 2026-11-18). This is the league's dated statement
#    about which Week 16/17/18 kickoff times are not yet fixed.
# ---------------------------------------------------------------------------
TBD_TEXT = (
    "In Week 16, two of the four designated matchups will be played on Saturday at 4:30 PM ET "
    "and 8:00 PM ET on NFL Network, with the remainder to be played either on Thursday night "
    "(8:15 PM ET), Sunday afternoon (1:00 PM ET and 4:25 PM ET), Sunday night (8:20 PM ET), or "
    "Monday night (8:15 PM ET). Specific dates and start times for the designated Week 16 "
    "matchups will be determined and announced at a later date during the season, no later than "
    "immediately after Week 14.\n"
    "In Week 17, two of the four designated matchups will be played on Saturday at 4:30 PM ET on "
    "NBC and 8:00 PM ET on Peacock, with the remainder to be played either on Thursday night "
    "(8:15 PM ET), Sunday afternoon (1:00 PM ET and4:25 PM ET), Sunday night (8:20 PM ET), or "
    "Monday night (8:15 PM ET). Specific dates and start times for the designated Week 17 "
    "matchups will be determined and announced at a later date during the season, no later than "
    "immediately after Week 15.\n"
    "In Week 18, three games will be played on Saturday (1:00 PM ET on Netflix, 4:30 PM ET and "
    "8:00 PM ET on ESPN/ABC) with the remainder to be played on Sunday afternoon (1:00 PM ET and "
    "4:25 PM ET), or Sunday night (8:20 PM ET). Specific dates, start times, and networks for "
    "Week 18 matchups will be determined and announced following the conclusion of Week 17."
)
FLEX_URL = "https://www.nfl.com/legal/flexible-scheduling-procedures"

# ---------------------------------------------------------------------------
# 4. Dated starter / injury announcements surfaced by the official injury hub
#    page's own news rail (read 2026-11-18). These are the league's dated
#    statements about who STARTED — not an inferred replacement. Each entry is
#    (date_in_headline, club, player, headline_verbatim, url).
#    "date_in_headline" is the date nfl.com printed in the headline; where the
#    headline carries no date the cell is left blank and flagged.
# ---------------------------------------------------------------------------
ANNOUNCEMENTS: list[tuple[str, ...]] = [
    ("", "SEA", "Drew Lock",
     "Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
     "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    ("", "SEA", "Sam Darnold",
     "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again",
     "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"),
    ("", "MIA", "Kyle McCord",
     "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
     "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
    ("2026-11-11", "CLE", "Deshaun Watson",
     "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    ("2026-11-11", "AZ", "Carson Beck",
     "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    ("2026-11-17", "MIN", "Jordan Addison",
     "NFL news roundup: Vikings WR Jordan Addison needs thumb surgery, could go to IR; Buccaneers add QB",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-16"),
    ("2026-11-17", "TB", "Baker Mayfield",
     "NFL Network: Buccaneers QB Baker Mayfield dealing with lower leg injury ahead of Week 11",
     "https://www.nfl.com/news/buccaneers-qb-baker-mayfield-injury-week-11"),
    ("2026-11-17", "NE", "Drake Maye",
     "NFL Network: Patriots QB Drake Maye could miss rest of 2026 season",
     "https://www.nfl.com/news/nfl-network-patriots-qb-drake-maye-could-miss-rest-of-2026-season"),
    ("2026-11-17", "DET", "Aidan Hutchinson",
     "NFL Network: Lions' Aidan Hutchinson feared to have suffered significant knee injury on sack celebration",
     "https://www.nfl.com/news/lions-aidan-hutchinson-knee-injury-patriots"),
    ("2026-11-17", "LAR", "Puka Nacua",
     "Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL",
     "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl"),
    ("2026-11-14", "NE", "TreVeyon Henderson",
     "NFL news roundup: Patriots place RB TreVeyon Henderson (illness) on injured reserve",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14"),
    ("2026-11-13", "BAL", "Lamar Jackson",
     "NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"),
    ("2026-11-12", "GB", "Josh Jacobs",
     "Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD",
     "https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week"),
    ("2026-11-10", "BUF", "Amani Hooker",
     "NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10"),
    ("2026-11-10", "DEN", "Daiyan Henley",
     "NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10"),
    ("2026-11-09", "MIN", "J.J. McCarthy",
     "NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-9"),
    ("", "BAL", "Lamar Jackson",
     "NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season",
     "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season"),
    ("2026-11-07", "NO", "Kendre Miller",
     "NFL news roundup: Saints waive Kendre Miller; Cowboys place Malachi Lawrence on IR",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-7"),
    ("2026-11-06", "NYJ", "Garrett Wilson",
     "NFL news roundup: Jets' Garrett Wilson ruled out; Falcons RB Brian Robinson out for Madrid game",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-6"),
]

# ---------------------------------------------------------------------------
# 5. Read log. `sha256_transcript` is the SHA-256 of the exact UTF-8 text this
#    session transcribed from the page — a hash of OUR TRANSCRIPT, not of the
#    page's bytes. It is a tamper check on the committed data, nothing more.
# ---------------------------------------------------------------------------
READS_NOTE_W11 = (
    "A direct request for https://www.nfl.com/injuries/league/2026/REG11/ resolved to the "
    "canonical URL https://www.nfl.com/injuries/league/2026/reg10 with page title "
    "'Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season'. The Week 11 "
    "injury report was therefore not published at read time (2026-11-18)."
)

SOURCES = [
    ("S-01", INJ_URL, INJ_CANON,
     "Official NFL Injury Report for Players - Week 10 of the 2026 Season",
     "injury rows, practice status, game status", READ_DATE, ""),
    ("S-02", SCHED_URL, SCHED_CANON,
     "NFL Schedules: Games, Times, Matchups & Tickets (Week 11, 2026)",
     "Week 11 fixtures, kickoff times, networks, club records, byes, venue text, TBD announcement",
     READ_DATE, ""),
    ("S-03", "https://www.nfl.com/injuries/league/2026/REG11/", INJ_CANON,
     "Official NFL Injury Report (Week 11 attempt)",
     "absence check: does a Week 11 report exist", READ_DATE, READS_NOTE_W11),
    ("S-04", INJ_URL, INJ_URL,
     "Official NFL injury hub news rail (dated league announcements)",
     "dated starter / injury / transaction announcements", READ_DATE,
     "Headline and link only; the article body was not opened in this session, so no "
     "value beyond the headline text is claimed."),
]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(name: str, header: list[str], rows: list[list[str]]) -> None:
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


def transcript_injury() -> str:
    out: list[str] = []
    for club in INJURY:
        label = INJURY[club][0]
        for player, pos, inj, prac, game in INJURY[club][1]:
            out.append("|".join([club, label, player, pos, inj, prac, game]))
    return "\n".join(out)


def transcript_schedule() -> str:
    lines = ["|".join(g) for g in WEEK11_GAMES]
    lines += ["BYE|" + "|".join(b) for b in WEEK11_BYES]
    return "\n".join(lines)


def transcript_announcements() -> str:
    return "\n".join("|".join(a) for a in ANNOUNCEMENTS)


def main() -> int:
    os.makedirs(DATA, exist_ok=True)

    # injury rows -----------------------------------------------------------
    rows: list[list[str]] = []
    for club, (label, players) in INJURY.items():
        for player, pos, inj, prac, game in players:
            rows.append([READ_DATE, "10", club, label, player, pos, inj,
                         PRACTICE[prac], game, INJ_URL])
    _write("injury_report_2026_11_18.csv",
           ["read_date", "nfl_week", "club", "game_block", "player", "position",
            "injuries", "practice_status", "game_status", "source_url"], rows)

    _write("week10_absent_clubs.csv",
           ["read_date", "nfl_week", "club", "page_state", "interpretation", "source_url"],
           [[READ_DATE, "10", c, "no injury section on the Week 10 injury page",
             "blank by presentation, NOT verified healthy", INJ_URL]
            for c in WEEK10_ABSENT_CLUBS])

    # week 11 schedule ------------------------------------------------------
    srows: list[list[str]] = []
    for g in WEEK11_GAMES:
        date, time_et, net, away, arec, home, hrec, venue, url = g
        key = f"{away}@{home}"
        prov = ("page badge / logo text" if key in DIRECT_VENUE_LABEL
                else "destination parameter of the page's own Hotel affiliate link")
        srows.append([READ_DATE, "11", date, time_et, net, away, arec, home, hrec,
                      venue, prov, url])
    _write("week11_schedule.csv",
           ["read_date", "nfl_week", "game_date", "kickoff_et", "network",
            "away", "away_record", "home", "home_record", "venue_text_on_page",
            "venue_provenance", "game_url"], srows)

    _write("week11_byes.csv",
           ["read_date", "nfl_week", "club", "record_on_page", "source_url"],
           [[READ_DATE, "11", c, r, SCHED_URL] for c, r in WEEK11_BYES])

    _write("schedule_announcement.csv",
           ["read_date", "item", "text_verbatim", "source_url"],
           [[READ_DATE, "2026 TBD Games block (Week 11 schedule page)", TBD_TEXT, SCHED_URL],
            [READ_DATE, "flexible-scheduling-procedures link (as printed on the page)",
             "View Flexible Schedule Procedures: https://www.nfl.com/legal/flexible-scheduling-procedures",
             SCHED_URL]])

    _write("starter_announcements.csv",
           ["read_date", "date_in_headline", "club", "player", "headline_verbatim",
            "claim_scope", "source_url"],
           [[READ_DATE, d, c, p, h, "headline text only; article body not read", u]
            for d, c, p, h, u in ANNOUNCEMENTS])

    # sources + read log ----------------------------------------------------
    _write("sources.csv",
           ["source_id", "requested_url", "canonical_url", "page_title",
            "used_for", "read_date", "note"],
           [list(s) for s in SOURCES])

    reads = [
        ["R-01", "S-01", INJ_URL, INJ_CANON, READ_DATE, READ_WINDOW,
         _sha(transcript_injury()), len(rows),
         "SHA-256 of this session's transcript of the page (not of the page bytes)", ""],
        ["R-02", "S-02", SCHED_URL, SCHED_CANON, READ_DATE, READ_WINDOW,
         _sha(transcript_schedule()), len(WEEK11_GAMES) + len(WEEK11_BYES),
         "SHA-256 of this session's transcript of the page (not of the page bytes)", ""],
        ["R-03", "S-03", "https://www.nfl.com/injuries/league/2026/REG11/", INJ_CANON,
         READ_DATE, READ_WINDOW, "", 0, "no transcript: page resolved to the Week 10 report",
         READS_NOTE_W11],
        ["R-04", "S-04", INJ_URL, INJ_URL, READ_DATE, READ_WINDOW,
         _sha(transcript_announcements()), len(ANNOUNCEMENTS),
         "SHA-256 of this session's transcript of the news rail headlines",
         "Headlines only; no article body was opened."],
    ]
    _write("official_reads.csv",
           ["read_id", "source_id", "requested_url", "canonical_url", "read_date",
            "read_window", "sha256_transcript", "rows_transcribed", "hash_scope", "note"],
           reads)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
