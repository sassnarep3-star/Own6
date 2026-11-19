# Repo review, session d6a947cb (2026-11-19)

Scope: the repository at base commit `e9185b3` (origin/main at claim time). Method: counts taken from git at that commit (`git ls-tree`, `git grep`, `git show`), not from the working tree. Official-page checks are in `data/nfl_d6a947cb/official_reads_2026_11_19.csv`. Each finding in `data/nfl_d6a947cb/repo_findings.csv` gives the command that reproduces it.

## Counts at base e9185b3

| Measure | Count | Command |
|---|---|---|
| Tracked files | 1,581 | `git ls-tree -r --name-only e9185b3 \| wc -l` |
| Root executive-summary files | 25 (23 NFL-named) | `git ls-tree --name-only e9185b3 \| grep -c EXECUTIVE_SUMMARY` |
| Audit files | 38 | `git ls-tree --name-only e9185b3 audit/ \| wc -l` |
| docs/ directories | 44 (26 NFL-named) | `git ls-tree -d --name-only e9185b3 docs/` |
| Workflow files | 34 | `git ls-tree --name-only e9185b3 .github/workflows/` |
| Requirement ledgers (requirements.csv) at base | 10, status words 35 (11 on main now; see RF-21) | `data/nfl_d6a947cb/ledger_comparison.csv` |
| COORDINATION.md | 4,234 lines, 486,966 bytes | `git show e9185b3:COORDINATION.md \| wc -lc` |
| Files citing the 404 schedule URL | 9 | `git grep -l operations.nfl.com/gameday/nfl-schedule e9185b3` |
| Files citing the unreadable 2017 policy PDF | 50 | `git grep -l 2017-nfl-injury-report-policy e9185b3` |
| Root index.html | 64,739 bytes, 47 links | `git show e9185b3:index.html` |
| docs/index.html | 26,344 characters, 1 table tag | `git show e9185b3:docs/index.html` |
| Open pull requests (other sessions) | 15 at claim time | `gh pr list --state open` |

## Line-by-line checks performed

1. Every row of the 96-row owner ledger (data/nfl_0ce967db/requirements.csv) was copied by script into this pack, with its carried state, gate and clearing number. Its source link is listed in `requirements.csv`.
2. Each source link was tested against the list of official URLs read this session. 42 rows cite a URL read today (partial reads: chunk 0 of the page). 54 rows cite URLs not re-read.
3. Seven rows were re-checked against official text (R01, R20, R22, R23, R29, R45, R63). Two changed status (R20, R29).
4. The 12 official checks were re-read with a UTC clock. Results: 5 match, 1 match for one fixture only, 3 mismatch or conflict, 2 unreadable, 1 partial.
5. Sha256 hashes were computed for all seven raw excerpt files (`data/nfl_d6a947cb/capture_log.csv`). The hash covers the excerpt file, not the live page.
6. The pre-registration history was read after unshallowing the clone (539 commits). The first commit is 56cc9b5; amendment A1 is 3dd2913.

## Irregularities (21 findings; none blocks the merge)

The full list with source links is in `data/nfl_d6a947cb/repo_findings.csv` and on the site's Flagged for Review page. In summary:

- RF-01 Ten requirement ledgers use 35 status words. data/nfl (18 rows) marks all rows done.
- RF-02 The Week 10 official page is titled Week 11.
- RF-03 A schedule source cited in 9 files returns 404.
- RF-04 A policy PDF cited in 50 files returns no text.
- RF-05 The earlier blank-cell defect for the Lions does not reproduce; the three players show Out.
- RF-06 NFL.com Terms section 1.3 restricts systematic retrieval absent written consent. This conflicts with the carried "met" price-policy basis. Counsel review needed.
- RF-07 Colts at Texans: RELIANT STADIUM (game centre) versus NRG Stadium (schedule hotel link). 12 of 13 venues unread.
- RF-08 R29 (depth-parser failures) marked out of scope although the brief asks for the fix.
- RF-09 Two IR-listed players on the hub show blank game status (reproduced today).
- RF-10 Two landing pages with different content; the Pages root is the root index.html.
- RF-11 Game counts 121, 136 and 150 are never reconciled.
- RF-12 The decision-readiness table sits on a sub-page, not the root landing.
- RF-13 COORDINATION.md is an append-only log of 486,966 bytes.
- RF-14 Pack sprawl: 25 root summaries, 38 audit files, 44 docs directories.
- RF-15 Several rows cite a source that cannot support their claim (404, unreadable PDF, privacy page, rulebook).
- RF-16 The official injury page gives no publication time; Wed/Thu/Fri timing cannot be verified from it.
- RF-17 15 pull requests from other sessions were open at claim time.
- RF-18 Pages publishes from main path /; no build step runs on it.
- RF-19 Pre-registration amendment A1 (3dd2913), made after the owner had seen the data, changes the prospective family from 7 to 8. It is disclosed.
- RF-20 The clone was shallow at claim time; history-based audits must unshallow first.
- RF-21 A later requirement ledger (data/nfl_cdf86c07, 82 rows, PR #141) landed on main after the base. It is not in this snapshot; the pack pins the ten ledgers at e9185b3.

## Not done in this session (stated, not hidden)

- Full reads of multi-chunk official pages. Only the chunks named in the verification table were read.
- Parallel sessions' packs were not edited. Their issues are logged above, not fixed.
- No new model, price, correlation, or leaderboard value was computed. The site does not add any.
- Rows keep their carried states unless a re-read in this session says otherwise.
