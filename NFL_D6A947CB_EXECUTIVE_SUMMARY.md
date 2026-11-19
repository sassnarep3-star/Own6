# Executive summary: NFL Decision Desk (session d6a947cb, 2026-11-19)

## Bottom line

- **No betting edge is shown and no profit claim is made.** No official NFL page read this session prints a price, so every price, residual and ROI cell stays blank by policy. No strategy qualifies for the leaderboard.
- **The repo already tracks every owner bullet, but in ten ledgers that disagree.** Those ledgers use 35 different status words. This session consolidates them into one register of 96 owner rows (88 unique bullets). Each row shows its gate and the number that would clear it.
- **Today's official re-reads found three contradictions, two unreadable sources and one partial read.** Details are in the verification table below.
- **The most important open risk is rights, not modelling.** NFL.com Terms section 1.3 prohibits systematic retrieval of data to compile a database without express written consent. Archive and price work depends on that answer, and counsel has not given one.

Site: https://sassnarep3-star.github.io/Own6/docs/nfl-d6a947cb/ (live after the merge recorded on the coordination board). Registers: `data/nfl_d6a947cb/`.

## What was verified today (2026-11-19, UTC 12:08 to 12:11)

| Check | Official source | Result |
|---|---|---|
| Week 11 injury hub title and Thursday block | https://www.nfl.com/injuries/ | match (chunk 0 of 7 only) |
| Blank Game Status for Carlies and Al-Shaair | https://www.nfl.com/injuries/ | match; their IR status was not checked |
| Lions Week 10 designations: Joseph, Mays, Reed | https://www.nfl.com/injuries/league/2026/reg10 | match: all three "Out" (the earlier blank cell does not reproduce) |
| Week 10 page title versus heading | https://www.nfl.com/injuries/league/2026/reg10 | **mismatch**: title says Week 11, heading says WEEK 10 |
| Colts at Texans venue | https://www.nfl.com/games/colts-at-texans-2026-reg-11 | match for this game: HOUSTON, TX; RELIANT STADIUM |
| Same game's stadium name on the schedule page | https://www.nfl.com/schedules/ | **conflict**: the hotel link says NRG Stadium |
| Schedule listing for the Thursday game | https://www.nfl.com/schedules/ | match |
| Schedule source cited by an earlier ledger | https://operations.nfl.com/gameday/nfl-schedule/ | **404** |
| Injury-report policy PDF cited by 50 repo files | https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf | **unreadable**: no text returned |
| Terms section 1.3 (systematic retrieval) | https://www.nfl.com/legal/terms/ | **contradicts** the carried "met" basis for the price-data policy |
| Week 11 game count | https://www.nfl.com/schedules/ | partial: 5 Sunday entries seen; the repo's slate has 13 games |

Result counts: 5 match, 1 match for one fixture only, 3 mismatch or conflict, 2 unreadable, 1 partial.

## Requirement status after re-checks (96 rows)

- 42 met, 24 partially met, 19 blocked by a named gate, 5 rejected in the brief, 4 not yet run, 1 needs review (price policy), 1 needs a decision (R29 depth-parser failures).
- Seven rows were re-checked; two changed status. Price-data policy (R20) moved from met to needs review. The depth-parser row (R29) moved from out of scope to needs a decision, because the brief asks for the fix. Venue (R23) and the Week 10 Lions row (R45) keep their states, and R45 is confirmed today. The R01 and R63 bases now cite the terms re-read.
- The landing table is on this pack's landing page. The earlier table sat on a sub-page, not the root landing.

## Blocked items and what clears them

| Blocked item | Gate | Number that would clear it |
|---|---|---|
| Price store, origination residuals, ROI (R01, R18, R57) | No official price source; terms s.1.3 unresolved | One licensed feed whose terms permit archiving; 100% of originated markets at T-24h and T-1h |
| Injury and depth capture over time (R51, R63, R95) | Terms s.1.3 unresolved (Q02) | Written consent or counsel's view; then daily fixed-time captures |
| Depth model for 32 clubs (R06, R11, R13, R40, R42) | Verified structured depth pages for 32 clubs (Q05) | 32 of 32 clubs with a readable official depth page |
| Actual starters and game-day status (R25, R28, R53) | No Game Book or snap-count source read (Q03, Q04) | One Game Book read and one snap-count table verified, then a parser |
| Venues for every fixture (R23) | 1 of 13 Week 11 venues read; name conflict open | 13 of 13 game-centre reads, conflict resolved |
| Game count (R02, R19, R26) | Three counts (121, 136, 150) never reconciled (Q07) | One table of weekly finals matching the standings totals |

## Irregularities for your review (not blocking)

Full list with links: Flagged for Review page. The most material:

1. **Amendment A1 to the pre-registration** (commit 3dd2913, eight minutes after the freeze at 56cc9b5) adds candidate S06 after the owner had seen a negative realised home margin (−0.53 points over 150 games). It is disclosed and kept off the leaderboard, but it changes the prospective family from 7 to 8. The owner should rule on it before week 11 kickoff.
2. **NFL.com Terms section 1.3** (see above). Legal review is needed before any further capture.
3. **Broken or unreadable sources.** One schedule link returns 404 (9 repo files cite it). The injury-policy PDF returns no text (50 repo files cite it).
4. **Official page integrity.** The Week 10 page is titled Week 11.
5. **Ten ledgers, 35 status words.** One of them (data/nfl, 18 rows) marks every row done.
6. **Two landing pages.** The Pages root is the root index.html; docs/index.html is an older NBA dashboard.

## Decisions I need from you (all in the Suggestions page; nothing implemented)

- **S-01** Which page is the public landing: replace the root page with this one, or keep both (current).
- **S-04 and S-05** Counsel review of Terms section 1.3, and reading the remaining eight chunks of the Terms.
- **S-09** Ruling on pre-registration amendment A1.
- **S-08** Whether to fix the Packers depth-parser prefix now (no outside source needed).
- **S-02** Which ledger becomes canonical.

## Method and limits (what this session did not do)

- Read only the chunks named in the verification table. Of the official pages, the schedule was read to chunk 0 of 3, the Week 11 injury hub to chunk 0 of 7, the Week 10 page to chunk 0 of 8, and the Terms to chunk 0 of 9.
- Re-checked 7 requirement rows against official text. The other 89 rows keep their carried state from earlier packs and show "not re-read this session".
- Repo counts were taken from git at the base commit e9185b3. The clone was shallow at claim time; it was unshallowed (539 commits) before history was read (RF-20).
- No parallel session's work was edited. Other sessions' packs are listed as irregularities only.
- The pack is a snapshot of base commit e9185b3. A later ledger (data/nfl_cdf86c07, PR #141) landed on main during the session and is recorded as RF-21, not reconciled here.
- No hallucinated values. Any field the official text did not show is blank or marked unverified.
