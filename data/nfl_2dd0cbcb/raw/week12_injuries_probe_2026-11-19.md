# Week-12 injury-panel probe + Week-11 Thursday game statuses — session 2dd0cbcb, 2026-11-19 (UTC)

Transcription of www.nfl.com pages read this session through the page-fetch tool.
TRANSCRIPTION only; sha256 in the capture log covers this file, not the live page.

## Section A — reg12 probe (cadence evidence)

- Requested URL: https://www.nfl.com/injuries/league/2026/reg12
- Returned page (as rendered): title "Official NFL Injury Report for Players - Week 11 of the
  2026 Season"; the fetch tool reports the effective URL as
  https://www.nfl.com/injuries/league/2026/reg11 — i.e. the reg12 path serves the Week 11 report.
- Week selector on the page lists WEEK 1 … WEEK 11 only. No WEEK 12 option was rendered.
- Read at 2026-11-19 (UTC), before the Thursday 4:00 PM ET weekly reporting cycle for
  Week 12 (Week 12 games begin Wednesday 2026-11-25 per the schedule page).
- Corroboration: every Week-12 game centre rendered "Injury Report is not available at
  this time" for both clubs (see week12_venues file observations).
- Finding: no Week-12 injury report existed at read time; the /regNN path falls back to the
  latest published week rather than 404-ing. Consumers must check the page's own week heading,
  not assume the requested week was served.

## Section B — Week 11 Thursday game (Indianapolis at Houston) game-day statuses as read

Header as read: "## THURSDAY, NOVEMBER 19TH", "8:15 PMEST", "Prime Video",
IND (3-7) at HOU (3-6). Rows below are the full printed tables for both clubs.

Fields: `THUR|<club>|<player>|<pos>|<injury>|<practice_status>|<game_status>`

THUR|IND|Jaylon Carlies|LB||Did Not Participate In Practice|
THUR|IND|Sauce Gardner|CB|Calf|Did Not Participate In Practice|Questionable
THUR|IND|Anthony Gould|WR|Toe|Full Participation in Practice|Questionable
THUR|IND|Charlie Heck|T|Not injury related - personal matter|Did Not Participate In Practice|Questionable
THUR|IND|Will Mallory|TE|Hamstring|Did Not Participate In Practice|Out
THUR|IND|Bernhard Raimann|T|Concussion|Did Not Participate In Practice|Out
THUR|IND|Luke Rhodes|LS|Hamstring|Limited Participation in Practice|Questionable
THUR|IND|Jerry Tillery|DT|Calf|Did Not Participate In Practice|Out
THUR|IND|Jalen Travis|T|Knee|Did Not Participate In Practice|Out
THUR|IND|Dalton Tucker|G||Full Participation in Practice|
THUR|IND|Charvarius Ward|CB|Knee|Did Not Participate In Practice|Out
THUR|HOU|Azeez Al-Shaair|LB||Did Not Participate In Practice|
THUR|HOU|Reed Blankenship|S||Full Participation in Practice|
THUR|HOU|Tank Dell|WR||Full Participation in Practice|
THUR|HOU|Blake Fisher|T||Full Participation in Practice|
THUR|HOU|Marvin Harrison Jr.|WR|Hamstring|Did Not Participate In Practice|Out
THUR|HOU|Jacob Hummel|LB|Groin|Full Participation in Practice|Questionable
THUR|HOU|Danielle Hunter|DE|Hamstring|Did Not Participate In Practice|Out
THUR|HOU|Brevin Jordan|TE|Foot, Illness|Did Not Participate In Practice|Out
THUR|HOU|Kamari Lassiter|CB||Full Participation in Practice|
THUR|HOU|Woody Marks|RB|Concussion|Did Not Participate In Practice|Out
THUR|HOU|David Montgomery|RB||Full Participation in Practice|
THUR|HOU|Febechi Nwaiwu|G||Full Participation in Practice|
THUR|HOU|Keylan Rutledge|G||Full Participation in Practice|
THUR|HOU|Jaylin Smith|CB|Hamstring|Full Participation in Practice|Questionable
THUR|HOU|Wyatt Teller|G|Back|Full Participation in Practice|Questionable

Counts: 26 player rows (IND 11, HOU 15). Game statuses: IND 9, HOU 7 → 16 — matching the
count a67ddef8 read on the same page at 2026-11-19T09:01:02Z (no designation change between
the two reads within the same day).

## Section C — blank-game-status players of note (as read)

- Jaylon Carlies (IND LB): blank game status; he appears on the November reserve list dated
  11/17 (Reserve/Injured) — the same pattern a67ddef8 flagged for Al-Shaair (A67-F04): a player
  on IR shows DNP practice with no game designation on the game-day report.
- Azeez Al-Shaair (HOU LB): blank game status; reserve list row 11/17 Reserve/Injured (re-read
  this session, same day, same table — see reserve_list file).
- Dalton Tucker (IND G): blank injury and blank game status with full practice participation.
- Blank game status cells carry no value in the source table; they are transcribed as empty and
  must not be read as "available" (brief: 'not listed' never means 'available').
