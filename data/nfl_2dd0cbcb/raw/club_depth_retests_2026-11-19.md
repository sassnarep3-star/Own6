# Club depth-chart re-tests — session 2dd0cbcb, read 2026-11-19 (UTC)

Transcription of three club depth-chart pages re-read this session to re-test open flags
(a67ddef8 Q-03/A67-F07 Texans; a67ddef8 A67-F07/F-09 Packers; a67ddef8 S-08 / inherited
B-05 Arizona QB). TRANSCRIPTION only; see capture_log.csv.

## Section A — Arizona Cardinals, https://www.azcardinals.com/team/depth-chart

Page title as read: "Arizona Cardinals Official Depth Chart" (browser tab title renders
"Arizona Cardinals Team"). Tables render as Position | P1 | P2 | P3 (empty cells where fewer
strings are listed). NO publication date or "unofficial" footer appeared anywhere on the page.

Offense rows as read (QB row quoted in full):
- QB: "Carson Beck" | "Josh Johnson" | "Joey Aguilar" | (empty)
- WR: Reggie Virgil | Harrison Wallace III
- WR: Simi Fehoko | Devin Duvernay
- LT: Jayden Williams | Jedrick Wills; LG: Isaac Seumalo | Hayden Conner; C: Hjalte Froholdt
  | Kingsley Eguakun; RG: Isaiah Adams | Jon Gaines II; RT: Elijah Wilkinson | Josh Fryar
- TE: Trey McBride | Hunter Long; TE: Elijah Higgins | Teagan Quitoriano
- RB: Tyler Allgeier | Bam Knight | Evan Hull

Defense rows as read:
- DT: Dante Stills | Darius Robinson | Jared Harrison-Hunte; NT: Roy Lopez | Andrew Billings
- DT: Walter Nolen III | L.J. Collier; OLB: Josh Sweat | Eku Leota
- ILB: Jack Gibbens | Karson Sharar; ILB: Mack Wilson Sr. | Cody Simon
- OLB: "Zaven Collins" and "Baron Browning" in the SAME first cell, remaining cells empty
  (a shared slot, printed exactly as the club publishes it)
- CB: Denzel Burke | Starling Thomas V; CB: Kei'Trel Clark | Max Melton
- CB: Kalen King | Garrett Williams; S: Wydett Williams Jr. | Kitan Crawford
- S: Budda Baker | Dadrion Taylor-Demerson

Special teams: K Chad Ryland; P Blake Gillikin; LS Casey Kreiter; H Blake Gillikin;
KR Devin Duvernay | Max Melton | Harrison Wallace III; PR Devin Duvernay | Harrison Wallace III.

Findings:
1. QB group is Beck / Johnson / Aguilar. Jacoby Brissett does NOT appear anywhere on the page.
   This answers the presence test a67ddef8 S-08 asked for (inherited flag B-05): the club's
   depth page names Carson Beck at QB1 and no Brissett row exists.
2. Kyler Murray and Gardner Minshew also do not appear on the depth page. The WAS@AZ game
   centre (read this session) shows the Cardinals season passing leader as "G. Minshew
   354 YDS" — the leader panel and the depth chart disagree about who is on the roster.
   No transaction covering Minshew or Murray was read this session, so their status is left
   blank+flagged, NOT inferred.
3. The OLB shared cell (Collins+Browning) is the same "two players in one slot" representation
   the brief asks to preserve (shared slots); it must not be silently split into rank-1/rank-2.
4. Row counts: Offense 11, Defense 12, Special Teams 6 = 29 printed rows.

## Section B — Green Bay Packers, https://www.packers.com/team/depth-chart

Title as read: "Green Bay Packers Depth Chart". Every player cell is prefixed by the jersey
number. Footer stamp as read (verbatim): "Unofficial, Nov. 10, 2026".

Rows as read (jersey prefixes preserved; number-stripped names in the data CSV):
- WR: 9 Christian Watson | 16 Bo Melton
- WR: 0 Matthew Golden | 87 J. Michael Sturdivant
- WR: 83 Savion Williams (alone)
- LT: 77 Jordan Morgan | 73 John Williams
- LG: 65 Aaron Banks | 79 Travis Glover | 67 Donovan Jennings
- C: 75 Sean Rhyan | 52 Jager Burton; RG: 72 Laken Tomlinson | 70 Kevin Zeitler
- RT: 71 Anthony Belton | 74 Mekhi Becton Sr.
- TE: 85 Tucker Kraft | 18 Jonnu Smith | 86 Mark Redman
- QB: 10 Jordan Love | 6 Tyrod Taylor
- RB: 8 Josh Jacobs | 32 MarShawn Lloyd | 22 Pierre Strong Jr.
- (blank position cell row): 26 Kaleb Johnson
- DT: 94 Karl Brooks | 97 Jordon Riley | 93 Anthony Campbell
- DT: 95 Devonte Wyatt | 55 Chris McClellan
- EDGE: 90 Lukas Van Ness | 57 Brenton Cox Jr; EDGE: 99 Barryn Sorrell | 51 Dani Dennis-Sutton
- LB: 44 Zaire Franklin | 59 Ty'Ron Hopper | 54 Kristian Welch
- LB: 58 Isaiah McDuffie | 31 Nick Niemann
- CB: 25 Keisean Nixon | 24 Carrington Valentine
- CB: 2 Brandon Cisse | 21 Benjamin St-Juste
- S: 29 Xavier McKinney | 27 Kitan Oladapo
- S: 33 Evan Williams | 27 Kitan Oladapo   ← same player printed in BOTH safety rows
- NB: 7 Javon Bullard | 36 Kamal Hadden
- ST: K 28 Trey Smack; P/H 19 Daniel Whelan; PR 0 Matthew Golden; KR 16 Bo Melton; LS 42 Matt Orzech

Findings:
1. The jersey-prefix parsing failure a67ddef8 re-tested (inherited 48217a55 flag) is confirmed
   still present; the fix the brief prescribes (strip number, KEEP the raw string) is exercised
   by this pack: the CSV stores both raw cell and stripped name.
2. The footer date "Unofficial, Nov. 10, 2026" is unchanged from the 09:01Z read by a67ddef8 —
   nine days stale at this read and still self-labelled "Unofficial". Row counts:
   Offense 12 (one with blank position), Defense 11, ST 6 = 29 printed rows.
3. Kaleb Johnson's row has a blank position cell and Matthew Golden appears under PR with no
   other cell — "empty slot" representations that must survive into the register.
4. Kitan Oladapo printed in both S rows means the safety "group" cannot be read as a strict
   two-deep ranking.

## Section C — Houston Texans, https://www.houstontexans.com/team/depth-chart

Page heading as read: "Depth Chart | Houston Texans - HoustonTexans.com"; body shows
"## Unofficial Depth Chart" followed by a single image element
(static.clubs.nfl.com/image/upload/texans/g3gkhdyah3rj1knd6dnz) and NO text table rows.
The page also renders a gameday banner: "How To Watch: Week 11 vs Colts — All the ways you
can watch, stream, and tune-in to Week 11 between the Texans and the Indianapolis Colts at
Reliant Stadium on November 19." and links including "Week 11 Injury Report | Texans vs
Colts" and "Houston Texans Transactions (11-17-2026)".

Findings:
1. Image-only rendering persists at this read (third session confirming). The Texans depth
   blocker (a67ddef8 Q-03) stays OPEN; no transcription by eye is performed here.
2. New corroboration for A67-F02: the CLUB's own banner uses the legacy stadium name "Reliant
   Stadium" for tonight's game, while the schedule hotel param says NRG Stadium and the
   BAL@HOU game centre also says RELIANT STADIUM. Three surfaces now read:
   club banner = RELIANT, game centre = RELIANT, hotel param = NRG.
