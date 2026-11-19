# NFL decision desk — session `d713b52f`

**Read window:** all official pages were read on **2026-11-19** between 09:40 and 11:10 UTC.
Live site: <https://sassnarep3-star.github.io/Own6/docs/nfl-d713b52f/index.html>

## The one-line answer to "can we bet this yet"

**No — and the pack now says exactly how far away that is.** Three separate walls stand in the way,
and for the first time all three are measured rather than described.

1. **No price exists on any official page.** Not one of the four Game Books, the injury report, the
   schedule or the standings publishes an opening or closing number. Every market, residual, ROI and
   CLV column in this pack is therefore blank **by written policy**, and the policy is printed on the
   page rather than hidden in a file.
2. **The model cannot be distinguished from guessing the base rate.** A frozen, pre-registered margin
   model was scored on every game it could honestly forecast. Its Brier skill is **+0.013**, and a
   2,000-resample week-cluster interval runs from **−0.175 to +0.152**. That interval contains zero. On
   this sample the model is not evidence of skill; it is evidence of a well-built pipeline that has not
   yet earned a promotion.
3. **Nothing is live.** Every strategy row is `paper`, every prospective sample is 0, and the state is
   checked by a test that fails the build if anyone flips one of those values without a real sample.

## The one-line answer to "can we measure replacement depth yet"

**Partly — and further than any prior pack in this repo.** Every earlier pack recorded the official
Game Book PDF as blocked. From this session the route is reachable, and four books were read end to end:

| What the books give | Count | Status |
|---|---|---|
| Named offensive and defensive starters | 176 | transcribed, 11 per unit confirmed |
| Not Active entries | 50 | transcribed with jersey numbers as printed |
| Playtime (snap) rows on offence | 121 | transcribed, **labelled Unofficial** because the NFL does |
| Clubs whose player-snaps fit inside snaps × 11 | 8 of 8 | capacity check passes for every club |
| Week-10 designations joined to inactive lists | 79 | 12 of 16 `Out` confirmed inactive |
| Rows the join cannot resolve | 4 | **published as unresolved, not guessed** |

The single most consequential finding of the pack is a labelling one. The NFL's own playtime table is
captioned **"(Unofficial)"** on the page that publishes it. Every row in `playtime.csv` therefore
carries `publisher_label = Unofficial`, and a 20-rule verifier fails the build if any row claims
otherwise. A snap count from that table can support a starter-versus-backup argument; it cannot be
called a certified count, and this pack never does.

## What the model actually did

The rule was frozen in code before the first scoring run and is additive:

```
expected_margin = (home_strength − away_strength) + H
p_home_win       = Φ(expected_margin / σ)
```

with `H` a registered home field, `σ` floored and capped, and club strength built **only** from games
that had already finished. That last clause is where the interesting defect was found, by the pack's
own verifier rather than by a person.

> **A club's first game cannot be forecast honestly.** To score it, the model would have to borrow a
> number from a game played earlier in the same week — same-week information at kickoff. The pack
> therefore **refuses** those games instead of scoring them and quietly calling the result a forecast.
> 150-game corpus = **134 scored + 16 refused**, with each refusal's reason printed on the model page.

This is the difference between a 150-game claim and a 150-game result. The earlier inherited pack scored
those games; that is a large part of why its number looks better, and the comparison table says so.

| Quantity | Value |
|---|---|
| Games scored | 134 (of 150; 16 refused, reasons published) |
| Brier score | 0.244756 |
| Climatology Brier | 0.249088 |
| **Brier skill score** | **+0.013059** |
| **Week-cluster 95% interval** | **−0.175423 to +0.152370** (contains zero) |
| Totals MAE / RMSE | 12.02 / 15.18 points |
| Reliability / resolution / uncertainty | 0.0145 / 0.0183 / 0.2480 |
| Within-bin term (exact identity) | 0.2297 |
| Murphy identity residual | 5.6e-17 (closes) |
| Reliability as a share of the score | 5.9% — almost none of it is recoverable by recalibration |
| State | `paper` — nothing promoted |

The **implementation gap** is the honest footnote. Two independent implementations of the *same frozen
rule*, scored on the 118 games both could score, differ by **0.009213 Brier — 71% of the measured skill**.
An outside reader should conclude that this sample cannot tell a good model from a good implementation,
let alone from noise. The pack publishes that ratio rather than the flattering comparison.

**Week 11, published as paper forecasts** (registered 2026-11-19T11:20Z, before kickoff):

| Game | Home win prob. | Expected margin | Expected total |
|---|---|---|---|
| IND @ HOU | 0.752 | +9.63 | 41.83 |
| MIA @ BUF | 0.910 | +18.90 | 47.35 |
| BAL @ CAR | 0.648 | +5.35 | 39.91 |

σ = 14.1167. Market and residual columns blank by policy.

## Independent recompute: 38 checks, 0 mismatches

Nothing inherited was taken on trust. 38 numbers from earlier packs were re-computed from the official
transcripts with the arithmetic shown on the page: standings identities (32 clubs, PF = PA = 6,923,
W = L = 149, 2 ties), the Week-10 finals, the corpus total, designation counts, snap capacity and every
published correlation. Result: **37 match, 0 mismatch, 1 informational** (the ledger's 118 scorable
games versus 109 where both clubs had a prior game — a definitional difference, not an error, and both
figures are published). Rounding is handled explicitly: a 6-decimal published value is compared at 5e-6
and labelled *"match (last-digit rounding)"*, so neither false mismatches nor hidden errors survive.

## Questions, suggestions, flags

* **18 questions** — each states what is missing, the route that would answer it, and what changes once
  it is answered. None is rhetorical; Q01 is the price-policy decision that blocks most of the brief.
* **12 suggestions** — each with cost, gain, risk and a route, and **every decision field empty**. The
  site is a review surface: nothing here is implemented pending the owner's choice.
* **12 flags** — every one linked to the official page that shows it, every one marked non-blocking, all
  published on the Flagged for Review page. The serious ones: the playtime table is self-labelled
  Unofficial; one venue is printed two different ways (F-03); an injury page titled "Week 11" carries a
  "WEEK 10" heading (F-08/F-09); four `Out` players never appear on an inactive list.

## Engineering, and what enforces it

* **29 data tables**, **1,066 pinned rows**, rebuilt from committed transcripts with **no network and no
  clock** other than the recorded read time.
* **20-rule verifier** (`scripts/check_nfl_d713b52f.py`): row counts pinned, every URL on an official
  host, capture hashes re-checked, no form control anywhere, no placeholder text, every internal link
  resolving, every playtime row carrying the Unofficial label, the corpus identity holding — and a
  determinism rule that rebuilds the data and the site and fails on a single byte of drift.
* **194 repo-wide tests pass**, including this pack's suite; **release gate: 0 issues**; **link check:
  13 pages, 0 errors**.
* **CI** (`.github/workflows/nfl-d713b52f-ci.yml`): rebuild → data diff → build → docs diff → verify → test.

## Bugs found and fixed inside this session

Recorded because a pack that publishes other sessions' irregularities must publish its own.

1. **Same-week leak in the model** — found by the verifier's "a scored game must have a prior game for
   both clubs" rule. 16 games were being scored with a same-week number. Fixed by refusing them and
   publishing a reconciliation; headline skill moved from +0.010 to +0.013 on a smaller, honest sample.
2. **Cross-pack register schema mismatch** — this pack's suggestion rows used `title`, but the
   repository-wide reader maps `title` into `statement` and the theme classifier saw only headlines.
   Two rows were silently unclassifiable. Fixed on my side of the boundary, not by editing the other
   session's code; the cross-pack classifier now resolves every row.
3. **Four false "missing inactive" discrepancies** — caused by generational suffixes (`Carlton Davis III`
   vs `C. Davis`). Fixed in the name matcher; this is why the pack reports 4 unresolved rows, all real.
4. **A meaningless parity assertion** — 6,923 is odd, so an "is it even" check could never pass. Replaced
   with a parity *report* that states the odd total and why a tie makes it odd.
5. **A degenerate luck panel** — the first decomposition keyed bins on exact forecast values, so every bin held
   one game and reliability came out *exactly equal* to the Brier score (0.2420 vs 0.2420). The numbers looked
   plausible and measured nothing. Rebuilt on five fixed probability bands, with the identity
   `brier_binned = reliability − resolution + uncertainty` asserted at 1e-9 inside the model. The corrected
   panel is far more interesting: reliability is only **5.9%** of the score, and the model is overconfident
   exactly where it should be humblest — 0.40–0.50 bands won 32% of the time, 0.50–0.60 bands 44%.
   **The same signature appears in the inherited `data/nfl_0ce967db/luck_panel.csv` S03 row** (brier exactly
   equals reliability, resolution exactly equals uncertainty); that pack's panel needs the same repair by its
   owner, and it is logged as a finding rather than edited here.

## What would change the answer

Written as a two-sided test, because a claim with no falsifier is marketing:

* **Upgrade the model if** a prospective or multi-season sample gives a week-cluster lower bound above 0,
  measured on games the model had not seen.
* **Retire it if** the point estimate falls below the climatology on a sample twice this size, or if the
  reliability term stays this close to the uncertainty term once sigma is calibrated per season.
* **Unblock pricing only if** a licensed price archive exists with its rights stated, or the owner
  formally drops ROI/CLV and competes on proper scores alone. That is Q01, and it is a decision, not a
  data pull.

**Decision readiness: 86 brief bullets — 33 done, 32 partial, 21 blocked.** Every row carries the gate
that blocks it and the number that clears it. Full detail on the landing page.
