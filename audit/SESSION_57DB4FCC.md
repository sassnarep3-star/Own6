# Session arena/57db4fcc-own6 — independent cross-check record (2026-11-05)

Branch fixed by Arena to `arena/57db4fcc-own6`. Base at claim: `origin/main` = `aea6a5a`
(PR #49). Scope: **new files only** plus an append-only section in `COORDINATION.md`:
`data/crosscheck/**`, `docs/crosscheck/**`, `scripts/build_crosscheck.py`,
`scripts/check_crosscheck.py`, `tests/test_crosscheck.py`,
`.github/workflows/crosscheck-ci.yml`, this file.

Purpose: a second, independent read of the official pages behind the 5 November snapshot, plus a
recomputation of every published headline number from the committed data. Nothing in this session
changes another section's values; anything that disagrees is published on
`docs/crosscheck/flagged.html` instead of being silently edited.

## What was read, and where it is written down

| ID | Official page (read 2026-11-05) | What was taken from it | Stored in |
|---|---|---|---|
| S1 | https://www.nba.com/standings | 30 team rows: W, L, win%, games behind, streak | `data/crosscheck/standings_read_57db4fcc.csv` |
| S2 | https://www.nba.com/schedule | 5–6 November fixtures: date, tip (ET), away/home, NBA Cup group | `data/crosscheck/slate_read.csv` |
| S3 | https://www.nba.com/games | games-per-date counts for all 30 November dates | `data/crosscheck/games_per_date_read.csv` |
| S4 | https://www.nba.com/game/okc-vs-cle-0022600158 | OKC 117 – CLE 112, Mon 2 Nov 2026 | `data/crosscheck/spotcheck_games.csv` |
| S5 | https://www.nba.com/game/bos-vs-det-0022600001 | BOS 113 – DET 121, Tue 20 Oct 2026 | `data/crosscheck/spotcheck_games.csv` |
| S6 | https://www.nba.com/game/atl-vs-was-0022600174 | ATL 120 – WAS 105, Wed 4 Nov 2026 | `data/crosscheck/spotcheck_games.csv` |
| S7 | https://www.nba.com/termsofuse | §1 reuse/linking restriction; §9 gambling-use restriction | `data/crosscheck/sources.csv` |
| S8 | https://api.github.com/repos/sassnarep3-star/Own6/pages | publishing source `main:/`, build status `built` | `COORDINATION.md` R4 |

Every transcription row carries its own `source_url` and `read_on`. A value that was not read is
blank; nothing was inferred, averaged, or back-filled.

## Line-by-line verification performed

1. **Two-reader transcription.** My 30 standings rows were compared with the previously committed
   snapshot produced by a different session. Result: 30/30 records agree, including the
   games-behind placeholders and the streak column. This does not prove either read correct; it
   proves two independent reads of the same page agree.
2. **Archive recomputation.** W-L was recomputed for all 30 teams from the 121 de-duplicated
   committed final scores and compared with the table read today: 30/30 match. Total wins balance
   at 121 on both sides.
3. **Delta reconciliation.** The 2026-11-03 snapshot plus the 14 games of 4 November reproduces
   today's table for 30/30 teams; the only idle teams are ORL and GSW, which is what the 4 November
   result file implies. Wins rise from 107 to 121 — exactly 14.
4. **Completeness by date.** The official games page prints a count for every date. On every
   November date already played the archive count equals the official count (4/4); 3 November shows
   `0 GAMES` and the archive has no 3 November fixture. 26 future dates are marked not applicable.
   12 October dates stay blank because their official counts were not read.
5. **Slate line by line.** 11/11 fixtures match the official schedule on date, tip time, both teams
   and competition label. Six Friday games carry NBA Cup group labels; the two Thursday games do not.
6. **Game-card spot checks.** 3/3 game cards agree with the archive score at three different dates.
7. **Claim recomputation.** 16 published headline numbers were traced to their page and recomputed
   from committed data: 14 match, 1 drifts, 1 is not recomputable. Details in
   `data/crosscheck/claims.csv` and `docs/crosscheck/claims.html`.
8. **Correlations recomputed.** Both published coefficients reproduce with an independent Pearson
   implementation: home-vs-away points r = 0.1994 (n = 121), margin-vs-total r = 0.018 (n = 121).
9. **Gate counts.** `data/methodology.json` defines G1–G8; the lab page prints G01–G10 and the
   landing page advertises 10 gates per candidate. Recorded as drift C13 / flag X-01.

## Irregularities (published on the site's Flagged for Review page)

| ID | Severity | One-line finding |
|---|---|---|
| X-01 | high | Two different validation-gate sets published (G1–G8 in data, G01–G10 on pages) |
| X-02 | medium | Same correlation pair published twice on different samples (n = 92 vs n = 121) |
| X-03 | high | A standings file labelled "live" is the 3 November snapshot |
| X-04 | high | No official market-price source, so edge / ROI / CLV / reward rank stay blank |
| X-05 | low | README has an empty `## Evidence state` heading |
| X-06 | low | README names an earlier session's branch as current |
| X-07 | medium | Ten separate Flagged-for-Review pages across the site |
| X-08 | medium | Root redirect and `docs/index.html` are two competing entry points |
| X-09 | medium | October per-date completeness unverified |
| X-10 | medium | Per-game verification covers 3 of 121 finals |
| X-11 | medium | Legacy market and player-prop data are third-party (ESPN), not official |
| X-12 | low | Games-behind placeholders for three Western teams transcribed verbatim |
| X-13 | medium | No licence file, so reuse terms are unstated |
| X-14 | medium | The six strategy candidates are prose, not a registry |
| X-15 | high | NBA rights for gambling-related reuse unresolved (§1, §9) |

None of these blocks publication: the site claims no edge, and a blank column cannot mislead the
way a filled one can. X-01, X-02 and X-14 are the three that would matter most to a reader trying to
score a strategy, because together they mean the gate set and the candidate family are not currently
machine-auditable.

## What this session did not do

- It did not re-fit or independently reimplement the ridge rating model; it verified the published
  Brier skill score arithmetically from its published components and confirmed the pipeline
  reproduces byte-identical output when re-run.
- It did not verify the 118 finals it did not open individually.
- It did not obtain any market price, and it made no profit, edge, ROI, CLV or reward claim.
- It did not edit another section's data or pages; disagreements are published, not patched.

## Reproduce

```sh
python3 scripts/build_crosscheck.py     # writes data/crosscheck + docs/crosscheck
python3 scripts/check_crosscheck.py     # publication rules, counts, links, blanks
python3 -m unittest tests.test_crosscheck -v
```
