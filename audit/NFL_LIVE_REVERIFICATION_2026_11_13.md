# NFL Live Re-Verification — 13 November 2026 (session `arena/4fc2fd57-own6`)

**Scope.** Re-read the official NFL pages used by the merged NFL Origination pack (`docs/nfl-origination/`, PR #73) on **13 Nov 2026**, reconciled every value this session could reach, corrected what the official pages contradict, and recorded what could not be confirmed. No betting lines, correlations, ROI or leaderboard results were produced. Nothing below is a profitability claim.

**Reading rule used.** A value is "official" only if it was read on an nfl.com (or other official NFL domain) page in this session. Headlines read in a page's news list are marked **headline only**. Anything found only in a press outlet is marked **press only** and is not treated as official.

## 1. Sources read in this session

| ID | Official source (read 2026-11-13) | What was read | Depth of read |
|---|---|---|---|
| L-01 | https://www.nfl.com/standings/division/2026/reg | All 32 clubs: W, L, T, PF, PA | Full (2 chunks) |
| L-02 | https://www.nfl.com/injuries/ | Week 10 injury report: every club, every listed player (player, position, injury, practice status, game status) | Full (8 chunks) |
| L-03 | https://www.nfl.com/schedules/2026/by-week/week-10 | Thursday final score (Commanders 24, Giants 21), Munich game and its time | Chunk 0 only (of 3). The 14 Week 10 matchups were cross-checked against the game headers of L-02, which were read in full |
| L-04 | https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13 | Friday 13 Nov news roundup: Jackson surgery and 6–10 week estimate, Froholdt, Gaines, Vaki, others | Chunk 0 only (of 3); every item used is in chunk 0 |
| L-05 | https://www.nfl.com/news/nfl-week-10-injury-report-2026-season | Linked from the report (not opened separately) | Link only |
| L-06 | Headline-only items listed in the injury page's news list: Darnold ruled out; Jackson out 6–9 weeks; Huntley out for season (labelled "Report"); Packers Jacobs finger surgery; Browns start Watson / Cardinals start Beck (11 Nov roundup); Ravens place Jackson on IR (5 Nov roundup) | Headlines only | Headline only — articles not opened |

## 2. Reconciliation results

- **Standings (32 clubs).** 30 clubs match the through-Week-9 snapshot exactly. **NYG** moves 5-2-1 → 5-3-1 and **WAS** moves 2-5-1 → 3-5-1 after the Thursday 12 Nov game (**Commanders 24, Giants 21, FINAL**, L-03). League totals become **136 W – 136 L – 2 T** and **6,291 PF = 6,291 PA** (previously 6,246). The change is exactly the 45 points of that game (21 + 24). File: `data/nfl_origination/standings_live_2026_11_13.csv`.
- **Depth and injury rows (`live_check_2026_11_13.csv`, 102 checks).**
  - 29 match the official report.
  - **17 contradicted by the official report** and corrected (e.g. Rhamondre Stevenson is Limited/Questionable, not DNP; Carson Wentz is Full, not Limited; Arizona's Seumalo, Sweat, Wilson and Baker are not DNP; Roy Lopez is Limited).
  - **3 superseded by the 13 Nov roundup** (Vaki, Froholdt, Gaines II).
  - **43 named backups not on the report**, so the "Active Expected" label was not supported and was removed.
  - **1 starter omitted** (Arizona's Carson Beck, headline only).
  - **1 press-only claim** (Brissett, below).
  - **1 unverified and not re-read** (the Seahawks 53-man QB3). The Kirk Cousins trade is now `NEWS_SUPPORTED` by an nfl.com article read on 13 Nov (LC-044; NFL-F23).
- **Lamar Jackson.** The repo said "minimum 4 games". The 13 Nov roundup reports coach Jesse Minter saying he is expected to miss **6–10 weeks** after surgery on a broken and dislocated right thumb. The repo now records the coach's statement.
- **Sam Darnold.** nfl.com's news headline says he was ruled out; the report table lists him as DNP with no game status. The two official items conflict, so the conflict is recorded (NFL-F20).

## 3. Press-only and manual-review links (not official; not used as verified values)

- Brissett acquisition from Arizona, 4–6 Nov 2026 (press only): https://www.yardbarker.com/nfl/articles/ravens_acquire_jacoby_brissett_after_lamar_jackson_thumb_injury/s1_17668_44517489 · https://www.baltimoresun.com/2026/11/06/ravens-announce-trade-for-veteran-qb-morning-after-blowout-loss-to-jaguars/ · https://www.wbal.com/ravens-turning-to-veteran-qb-jacoby-brissett-to-end-four-game-losing-streak · https://thesportsencounter.com/2026/11/06/jacoby-brissett-ravens-trade-cardinals-lamar-jackson-2026/
- Official Ravens roster page (manual check, **not read**): https://www.nfl.com/teams/baltimore-ravens/roster
- Official Vikings roster page (manual check, **not read**): https://www.nfl.com/teams/minnesota-vikings/roster
- The Week 8 nfl.com headline "Cardinals bench QB Jacoby Brissett" (headline only) is consistent with the press reports.

## 4. Irregularities flagged (all non-blocking, shown on the Flagged for Review page)

| Flag | Severity | Summary |
|---|---|---|
| NFL-F16 | high | Standings and the Week 10 slate were a pre-Thursday snapshot; the Thursday game is final. |
| NFL-F17 | high | 17 depth/injury statuses contradicted by the official report; corrected. |
| NFL-F18 | high | Club depth-chart order (1st–4th string) rests on club charts labelled "Unofficial"; not re-read here. |
| NFL-F19 | medium | Jackson return estimate: "min 4 games" superseded by the coach's 6–10 week statement. |
| NFL-F20 | medium | nfl.com's news headline and report table disagree on Darnold. |
| NFL-F21 | medium | Starting QB for Arizona (Carson Beck, headline only) missing from the depth table. |
| NFL-F22 | high | Brissett's Baltimore move is press-only; no official transaction page was read. |
| NFL-F23 | low | Kirk Cousins trade confirmed by an nfl.com article (13 Nov); exact date and depth slot not confirmed. |
| NFL-F24 | medium | W10-G02, G05, G12 broadcast cells (NFL-V1) and W10-G02 venue wording not supported by the nfl.com pages read; not edited here. |
| NFL-F25 | low | The featured-rules link resolves, but its content is the 2025 rules page (10 citations in the pack). |

## 4a. Post-rebase checks (13 Nov, after `origin/main` 05f93ac)

- **Schedule page, all three chunks read.** The 14 Week 10 games match the repo. The "Teams on Bye" block lists CHI 7-2, DEN 7-2, PHI 2-7, and TB 3-6, which matches `W10-BYE`. NFL-V1's open item on CHI and TB is resolved. The malformed packing of four clubs into one row is a format issue and remains open.
- **Broadcasts.** The schedule page shows FOX for MIN@GB and SF@DAL, and FOX "+1" for NE@DET and SF@DAL. The nfl.com "How to watch" article says the Munich game is on NFL Network. Neither page names "FOX One". NFL-F24 records the conflict, and the cells are left for their owner to correct.
- **Rules citations.** `operations.nfl.com/rules-officiating/featured-rules` resolves, but it shows the 2025 rules changes (NFL-F25). The 2026 rulebook link is separate.
- **Emergency 3rd QB and contract-language pages** resolve. Used only for rule definitions; the contract page's pay amounts are for 2025 and are not used in the pack.
- **Cousins.** The nfl.com "How to watch" article says the Vikings acquired QB Kirk Cousins from the Raiders at the trade deadline and that he is "in line to start" (LC-044, NFL-F23).

## 5. What was not verified in this session (carried forward honestly)

- The NFL rulebook and operations rules cited in the pack (Rule 6 touchback spot, Rule 16 overtime, 48-vs-47 active-list rule, practice-squad elevation limits, Emergency 3rd QB) were **not re-read** here. They remain as stated by the earlier pack and are not re-verified by this audit.
- Club depth-chart ordering (NFL-F18).
- Sportsbook lines, closing prices, correlations and any empirical result. None exist in the repository and none were produced.
- The Week 10 games themselves (Nov 15–16) have not been played; no results exist.

## 6. Reproduction

- `python3 tools/run_tests.py` → 53/53 (includes `test_nfl_live_recheck_2026_11_13_*`).
- `python3 scripts/build_nfl_origination.py --check` → up to date.
- `python3 scripts/check_nfl_origination.py` → 11 pages, 0 `<input>`, 15 CSV datasets, live 136/136/2 and 6,291 identity passes.
- `python3 tools/release_gate.py` → 0 issues.
