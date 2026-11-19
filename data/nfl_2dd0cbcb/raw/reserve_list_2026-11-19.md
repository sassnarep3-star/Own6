# November reserve list — render-window probe — session 2dd0cbcb, read 2026-11-19 (UTC)

Transcription of https://www.nfl.com/transactions/league/reserve-list/2026/11 (2 chunks, full
page) as rendered at read time. Purpose: the probe a67ddef8 S-03 asked for — record first/last
date and row count on every read, so the window can be tracked instead of theorized.
TRANSCRIPTION only; see capture_log.csv.

Tab links rendered beside "Reserve List": Trades / Signings / Reserve List / Waivers /
Terminations / Other (all /2026/11). Year selector: 1965…2026. Month selector:
January…November (November selected). No intra-month pagination control was observed.

Fields: `RES|<date>|<name>|<club>|<transaction>` (club from the From/To logo+name cell; both
cells show the same club on every row)

RES|11/18|Mason McCormick|PIT|Reserve/Injured
RES|11/18|Jared Wiley|KC|Reserve/Injured
RES|11/18|Aidan Hutchinson|DET|Reserve/Injured
RES|11/18|Bo Richter|MIN|Reserve/Injured
RES|11/17|Azeez Al-Shaair|HOU|Reserve/Injured
RES|11/17|Zeek Biggers|MIA|Reserve/Injured
RES|11/17|Jordan Phillips|MIA|Reserve/Injured
RES|11/17|Andrew Wingard|AZ|Reserve/Injured
RES|11/17|Jordan Burch|AZ|Reserve/Injured
RES|11/17|Ar'maj Reed-Adams|BUF|Reserve/Injured
RES|11/17|Jaylon Carlies|IND|Reserve/Injured
RES|11/17|Wan'Dale Robinson|TEN|Reserve/Injured
RES|11/16|Dylan McMahon|LA|Reserve/Injured
RES|11/16|Branson Taylor|LAC|Reserve/Injured
RES|11/14|Christen Miller|NO|Reserve/Injured
RES|11/14|TreVeyon Henderson|NE|Reserve/Injured
RES|11/14|Michael Burton|CLE|Reserve/Injured
RES|11/14|Mo Alie-Cox|IND|Reserve/Injured
RES|11/14|Akeem Davis-Gaither|IND|Reserve/Injured
RES|11/14|Peter Skoronski|TEN|Reserve/Injured
RES|11/14|Tommy Townsend|TEN|Reserve/Injured
RES|11/14|Tyler Goodson|DAL|Reserve/Injured
RES|11/14|Josh Whyle|GB|Reserve/Injured
RES|11/12|Puka Nacua|LA|Reserve/Injured
RES|11/10|Jordan Whittington|LA|Reserve/Injured

## Probe record

| field | value |
|---|---|
| row_count_on_page | 25 |
| window_first_date_rendered | 11/10 |
| window_last_date_rendered | 11/18 |
| intra-month pagination control | none observed |
| position column | blank on all 25 rows (as rendered) |
| read clock | 2026-11-19 (UTC), second read of the day on this URL |

Comparison with the same page read by session a67ddef8 at 2026-11-19T09:01:02Z: identical
25 rows and identical 11/10–11/18 window at both clocks. The "render window" explanation
(a rolling or capped window that hides earlier November moves) is NOT distinguishable from a
static omission at these two clocks; only the intra-month row set changing on a later day
would separate the two. Q-01 from a67ddef8 therefore remains open; this probe is the
instrumentation S-03 asked for.

Material roster facts visible in this window (each links the player to a game-status question):
- Puka Nacua (LA WR) placed on Reserve/Injured 11/12 — Rams play GB Wednesday 11/25; the
  GB@LA game centre still lists "P. Nacua 715 YDS" as the Rams receiving leader (season
  leaders do not exclude IR players; noted so no one reads the leader panel as availability).
- Azeez Al-Shaair (HOU) 11/17 and Jaylon Carlies (IND) 11/17 — both appear on tonight's
  Week-11 Thursday report with a blank game-status cell (see injuries probe file, Section C).
- Aidan Hutchinson (DET) 11/18 — Bears at Lions Thursday 11/26; no Detroit depth re-read was
  in this session's scope, so Hutchinson's effect on DET depth is recorded as an open
  availability question, not modelled.
