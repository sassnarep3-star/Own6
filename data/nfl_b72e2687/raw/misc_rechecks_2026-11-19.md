# Miscellaneous official re-reads for flag re-tests — 2026-11-19 (UTC)
Each section records what was read this session from the official page named. These reads support
the `flag_recheck.csv` rows; the standings, Week-12 schedule and injury-report sections live in their
own raw artifacts.

## A. Game centre: Colts at Texans 2026 REG 11
URL: https://www.nfl.com/games/colts-at-texans-2026-reg-11 (?tab=overview)
Read: 2026-11-19, 3 chunks, title as read: "Indianapolis Colts at Houston Texans 2026 REG 11 - Game Center"
- Game Info block reads verbatim: "Location LOCATION HOUSTON, TX" and "Stadium STADIUM RELIANT STADIUM".
  The official game centre carries the legacy stadium name (supports A67-F01/F02).
- Injury panels (overview): Colts — W. Mallory (TE #86, Hamstring, Did not participate), B. Raimann
  (OL #79, Concussion, Did not participate), J. Tillery (DL #94, Calf, Did not participate),
  J. Travis (OL #75, Knee, Did not participate); Texans — M. Harrison (WR, Hamstring, Did not
  participate), D. Hunter (DL #55, Hamstring, Did not participate), B. Jordan (TE #9, Illness,
  Did not participate), W. Marks (RB #4, Concussion, Did not participate). Panel shows "See All".
- Team leaders on the card: Colts D. Jones 1830 YDS / 59.6% / 7TD / 12INT; Texans C. Stroud 2462 YDS
  / 62.8% / 19TD / 3INT; rushing J. Taylor 739 YDS vs J. Marks 391 YDS; receiving T. Warren 276/40 vs
  N. Collins 478/37.
- Matches the standings records read this session: IND 3-7, HOU 3-6.

## B. Reserve list — November 2026
URL: https://www.nfl.com/transactions/league/reserve-list/2026/11
Read: 2026-11-19, 2 chunks, title as read: "2026 NFL reserve-list by month | NFL.com"
- 25 rows, all "Reserve/Injured". Dated: 11/18 McCormick (PIT), Wiley (KC), Hutchinson (DET),
  Richter (MIN); 11/17 Al-Shaair (HOU), Biggers (MIA), J. Phillips (MIA), Wingard (AZ), Burch (AZ),
  Reed-Adams (BUF), Carlies (IND), W.D. Robinson (TEN); 11/16 McMahon (LA), Taylor (LAC);
  11/14 Miller (NO), Henderson (NE), Burton (CLE), Alie-Cox (IND), Davis-Gaither (IND), Skoronski
  (TEN), Townsend (TEN), Goodson (DAL), Whyle (GB); 11/12 Nacua (LA); 11/10 Whittington (LA).
- Render window starts 11/10; nothing dated earlier in November is visible (A67-F03 persists).
- Hutchinson's 11/18 row corroborates the news-rail headline read this session ("Lions' Aidan
  Hutchinson feared to have suffered significant knee injury").
- Position column is blank on every row as rendered.

## C. Packers depth chart
URL: https://www.packers.com/team/depth-chart
Read: 2026-11-19, 1 chunk, title as read: "Packers Depth Chart | Green Bay Packers – packers.com"
- Cells render with jersey prefixes: "9 Christian Watson", "0 Matthew Golden", "77 Jordan Morgan",
  "65 Aaron Banks", etc. Footer reads verbatim: "Unofficial, Nov. 10, 2026" (9 days stale at read).
- Structure observed: OFFENSE (WR x3 incl. empty 3rd string on WR1 row; LT/LG/C/RG/RT; TE with 3
  names; WR slot; QB; RB with 3 names + an unlabelled 4th row "26 Kaleb Johnson"), DEFENSE
  (DT x2, EDGE x2, LB x2, CB x2, S x2, NB), SPECIAL TEAMS (K/P/H/PR/KR/LS). The unlabelled RB row
  and the empty 3rd-string cells are examples of shared/empty slots that a ranked-list model would
  flatten (VQ-08 class of issue).
- Deepest-rank count check: no position lists more than 3 names; PR row has an empty rank-1.

## D. Texans depth chart
URL: https://www.houstontexans.com/team/depth-chart
Read: 2026-11-19, 1 chunk, title as read: "Depth Chart | Houston Texans - HoustonTexans.com"
- Renders heading "Unofficial Depth Chart" plus a single image element (static.clubs.nfl.com
  image/upload/texans/g3gkhdyah3rj1knd6dnz) and headline links. Zero table text rows: no depth row
  is machine-readable from the club page (A67-F06 persists).
- The page's own "How To Watch: Week 11 vs Colts" banner reads "at Reliant Stadium on November 19" —
  the club site itself uses the legacy venue name, second official host for A67-F02.
- Related club links read on the page: "Houston Texans Transactions (11-17-2026)" and
  "Week 11 Injury Report | Texans vs Colts" (both club-domain links, not read this session).

## E. Game centre: Broncos at Steelers 2026 REG 12
URL: https://www.nfl.com/games/broncos-at-steelers-2026-reg-12 (?tab=overview)
Read: 2026-11-19, 2 chunks, title as read: "Denver Broncos at Pittsburgh Steelers 2026 REG 12 - Game Center"
- Game Info: Location PITTSBURGH, PA; Stadium ACRISURE STADIUM (current name on the game centre).
- Injury panels on the overview: "Broncos' Injury Report is not available at this time." and
  "Steelers' Injury Report is not available at this time." (A67-F09 persists; expected for a
  Friday 11/27 fixture read on Wednesday 11/19).
- Records on card match the standings read this session: DEN 7-2, PIT 6-3.
- Previous result shown on the page: Broncos won Week 9 at Carolina 26-21.
