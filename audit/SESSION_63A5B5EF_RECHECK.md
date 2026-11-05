# Independent recheck — 5 November 2026 (session arena/63a5b5ef-own6)

Scope: re-verify the repository's published 2026-11-05 numerical snapshot line by line against
official pages read **in this session**, then recompute the derived layer with separately written
code. Nothing from earlier sessions' reports was accepted as evidence.

Product: `data/reverify_2026_11_05/`, `scripts/reverify_official.py`, `scripts/build_reverify.py`,
`scripts/check_reverify.py`, `docs/reverify/` (8 pages), `tests/test_reverify.py`.

## Official pages read (all on 2026-11-05, via direct page fetch)

| Page | Used for | Result |
|---|---|---|
| https://www.nba.com/standings | 30 team records, conference/division records, streaks | Read in full (both chunks). 30 teams. |
| https://www.nba.com/games?date=2026-11-04 | 14 final scores, overtime flags, month calendar cells | Read in full (all chunks). |
| https://www.nba.com/games?date=2026-11-05 | 2 games, tip times, records | Read in full. |
| https://www.nba.com/games?date=2026-11-06 | 9 games, tip times, Cup group labels and group records | Read in full (both chunks). |
| https://www.nba.com/termsofuse | §1 and §9(i)–(vii) verbatim | Read (§1 and §9 fully quoted into `rights_read.csv`). |

The official month calendar shows 15 games on 2 November, 0 on 3 November, 14 on 4 November,
2 on 5 November and 9 on 6 November. The committed archives contain 15, 14, 11 (2 + 9) rows
respectively, which matches.

## Result of the line-by-line reconciliation

| Family | Rows checked | Match | Mismatch | Unverified |
|---|---|---|---|---|
| Standings (wins, losses, win%, games behind) | 120 | 120 | 0 | 0 |
| 4 November results (scores, status, teams) | 70 | 70 | 0 | 0 |
| 5–6 November slate (date, tip, matchup, competition, both records) | 99 | 99 | 0 | 0 |
| Calendar game counts | 4 | 4 | 0 | 0 |
| Rights clauses | 9 | 9 (text verified verbatim) | 0 | 0 |
| Fail-closed ledger counts | 3 | 3 | 0 | 0 |
| **Total** | **305** | **305** | **0** | **0** |

Derived layer, recomputed with independent code (Cholesky solve instead of Gauss-Jordan;
raw-score-sum Pearson instead of centred means): 30 rebuilt team records, 9 correlation values
(3 coefficients + 3 intervals), 33 model line values for the 11-game slate, and 17 holdout
statistics — **89 of 89 reproduced**, maximum absolute difference within rounding.

Key recomputed values: holdout winner accuracy 0.6721 (Wilson 95% 0.5472–0.7767) against an
always-home baseline of 0.5082; McNemar exact two-sided p = 0.06391; Brier skill score 0.1299 with
a bootstrap interval of −0.0385 to 0.2961, **which includes zero**.

## Irregularities and notes for review

1. **Competition label prefix (low).** The official games page prints "Emirates NBA Cup East
   Group C" (and so on). The published slate file stores "NBA Cup East Group C". The group and
   tier are identical; the title-sponsor prefix is dropped, which is consistent with NBA Terms
   §9(iii) (no commercial identification). Recorded on each row rather than "corrected".
2. **Cup group records omitted from the published slate (informational).** The official pages
   print in-season tournament group records (e.g. WAS 1-0, ATL 0-0) that the published slate file
   does not carry. They are captured in `data/reverify_2026_11_05/slate_read.csv` and shown on the
   site as newly verified readings; they are not used by the model.
3. **No market prices anywhere (high, unchanged).** No authorized odds source exists; §9(iv)
   prohibits gambling use of NBA Statistics. Line value, edge, ROI and CLV remain blank.
4. **Skill not established (high, unchanged).** 61 holdout games cannot separate skill from luck;
   the interval for the Brier skill score includes zero, and the McNemar test does not reach
   p < 0.05. No strategy is promoted and no reward is paid.
5. **Unequal games played.** Team records range from 6 to 9 games, so rating precision is uneven;
   line intervals, not point estimates, are the honest output.
6. **Korean statute not re-read this session (medium).** `data/legal_kr.json` is carried forward
   from an earlier session and is listed on the recheck Flagged page as unverified here.

## Reproduction

```sh
python3 scripts/reverify_official.py   # rebuild reconciliation.csv, recompute.csv, report.json
python3 scripts/build_reverify.py      # rebuild docs/reverify/
python3 scripts/check_reverify.py      # source-link, link and fail-closed checks
python3 -m pytest -q tests/test_reverify.py
```

No value is inferred. A row that cannot be tied to an official page is published blank and listed
on `docs/reverify/flagged.html`.
