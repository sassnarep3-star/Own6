# 48217A55 — Method notes

**Session:** `arena/48217a55-own6` · **Capture:** 2026-11-15 · **Scope:** nine official NFL pages
read once, on a game day, while Week 10 was still being played.

This note records *how* the pack was built, so a reader can judge the numbers without
re-deriving them. It is not a claim that the numbers are certified — only that they are
traceable.

---

## 1. The capture boundary

Everything in `src/nfl_48217a55/capture.py` was transcribed by hand from `fetch_page` output
during one session. There is no scraper: the sandbox has no outbound network for NFL.com, and
the pages are JavaScript-rendered, so the values were read off the returned text and typed in.

That has one consequence worth stating plainly: **a transcription is not a certification**.
The pack's own verifier checks internal consistency (row counts, arithmetic, flag
completeness, link integrity); it cannot re-read the page. Anyone wanting to re-verify a
value has to open the cited URL and compare.

## 2. Why the standings needed reconstruction

The official standings page is *live*. It was read mid-Sunday, so it already contained the
nine completed Week 10 games. The pack needed a **through-Week-9** table, because every
rating, correlation and luck calculation in it is pre-Week-10 by construction.

The reconstruction is subtraction, not estimation:

```
through_week9 = live_standings - week10_completed_games
```

Each of the nine completed games contributes its points to one club's `PF` and the other's
`PA`, and one W/L/T to each side. Subtracting them is exact, so no value is inferred.

The result was checked against an independent official page — the Week 10 pre-game injury
article, which prints each club's record *before* kickoff. **10 of 10 matched.** Two
structural checks also hold:

- league points for = league points against = 6,246 (they must: every point scored is
  conceded)
- wins = losses = 135, and 272 team-games implies **136 completed games** — the corpus size
  the brief refers to, confirmed arithmetically rather than assumed.

## 3. Why the injury report has 28 clubs, not 32

Four clubs were on bye in Week 10 (CHI, DEN, PHI, TB) and have no section on the report.
Their absence is published as a bye, never as health. This matters more than it looks: a
naive "count the Out rows per club" produces a misleadingly good score for a bye club, and
any depth-of-replacement metric built on it is wrong by construction.

## 4. The 176 blank game statuses

176 of the 347 injury rows carry no game status. The page prints a blank where there is no
designation. The pack publishes those as **empty cells**, not as "active".

This is the single most consequential editorial decision in the pack. It would be trivial to
map blank → active, and it would be wrong: a player is on the injury report *because* a club
listed him, and "listed but undesignated" is not the same statement as "cleared". Where the
pack needed an availability number, it used the reserve list and the pre-game article instead
of guessing.

## 5. Luck, and why it is measured before any skill claim

The luck panel computes the share of the win-percentage spread that a fair coin flip would
produce over the same number of games:

- observed variance of win percentage across the 32 clubs
- null variance = `0.25 / games` (a coin-flip team, same schedule length)
- skill variance = observed − null

Result: **0.518**. Slightly over half the spread in the standings is what randomness alone
would generate across 136 games.

The strategy-level luck number is deliberately blank. It needs 100 prospective graded
forecasts; there are zero. Estimating it would produce the exact artifact the brief asks to
avoid — a number that looks like evidence and is not.

## 6. Correlations: measured ones and refused ones

Six correlations were measured, each with n, unit, method, interval, p-value and one official
URL per axis. **Every interval either straddles zero or sits on a sample too small to decide
anything.** That is reported as the finding, not buried.

Five further candidates were *refused* and published as exclusions with the reason and the
number that would clear them. The discipline here is the point: a correlation computed from
the wrong unit (e.g. club-level aggregates when the question is about games, or a sample
drawn from the four clubs that happen to be on bye) produces a precise-looking number that
answers nothing.

## 7. Rejected inference patterns

Recorded here so they are not reintroduced later:

| Pattern | Why it is rejected |
|---|---|
| Blank game status → "active" | The report lists a player *because* a club listed him. Undesignated ≠ cleared. |
| Bye club → "healthy club" | The club has no section on the report at all. |
| Jersey number / experience / salary → depth order | Explicitly rejected by the brief. The roster page publishes these; they are not used. |
| One injury capture → a "surprise" signal | A surprise needs a delta; a delta needs two reads. One capture gives a level only. |
| A trade → a starter announcement | `roster_events.py` publishes the trades with `starter_announced` blank, with a note saying why. |
| Backtest ROI → the leaderboard | The leaderboard schema has no backtest column. All five divisions report 0 ranked. |

## 8. Reproducibility

```sh
python3 scripts/build_nfl_48217a55.py    # 36 CSVs, 18 pages, no network, no arguments
python3 scripts/check_nfl_48217a55.py    # 115 checks
python3 -m unittest discover -s tests -p "test_nfl_48217a55.py" -v   # 59 tests
```

A rebuild is byte-identical, and a test asserts the digest. That makes the published tables
auditable: they are exactly what the code computes from the captured values, with no manual
editing afterwards.
