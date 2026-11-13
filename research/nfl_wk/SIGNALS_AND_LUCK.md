# NFL signal generation, validation and luck removal — method notes

This file records the reasoning behind `src/nfl_wk/` so a reviewer can attack the method rather than guess at it. It is not a claim of skill; it is a description of what would have to be true for a claim of skill to be testable.

## 1. Where a signal could come from

A usable signal is a disagreement between our own number and a price, where the price is timestamped *after* the information we used and *before* kickoff. That ordering is the whole game, and it is why gate VG-02 exists.

| Candidate signal | What would have to move | Why the market might not have moved | Gate that must pass first |
|---|---|---|---|
| Own total vs market total | Team scoring rates, opponent adjustment | Slow adjustment to mid-week injury news | VG-02, VG-03, VG-04 |
| Own spread vs market spread | Margin distribution, home field | Home-field term mispriced for low-talent clubs | VG-02, VG-03, VG-14 |
| Verified first-string line loss | Offensive efficiency | Market prices the *name*, not the snap share | VG-02, VG-09, VG-10 |
| Secondary-cluster deficiency | Opposing passing game | Market prices sacks, not coverage depth | VG-02, VG-09, VG-10 |
| Quarterback cascade | Non-linear efficiency drop | Market's backup curve is often linear | VG-02, VG-09 |
| Prop combo dependence | Joint distribution | Books price combinations off marginals | VG-10, VG-11 |

The recurring theme: **information asymmetry about who is actually on the field.** That is precisely what the injury-plus-depth-chart join is for, and precisely why the pack refuses to guess a depth string it cannot read from a club page.

## 2. Why the own line is deliberately naive

The model uses only each club's points-for and points-against per game. It has:

- **no opponent adjustment** — a club's rate is not opponent-neutral;
- **no home-field term** — the official standings do not publish one;
- **no pace or efficiency decomposition** — that needs play-by-play, which is not licensed here.

Each omission is disclosed on the site. The consequence is a systematic bias: ignoring home field under-rates home clubs by roughly the league's true home advantage. That bias is large enough that a naive "our line vs the market" comparison would produce confident nonsense, which is exactly the failure the gates are designed to catch.

**A model that is knowingly biased cannot be used to declare a market wrong.** It can only be used as a transparent baseline after the bias is measured.

## 3. The luck problem, stated precisely

Suppose a strategy has true edge `e` per unit staked at price `-110`. Over `n` independent bets, the standard deviation of total profit is approximately `1.95·√n` and the mean is `e·n`. Skill becomes statistically distinguishable from luck roughly when `e·n ≫ 1.95·√n`, i.e. `n ≫ (1.95/e)²`.

- At `e = 0.02` (2% edge, which is excellent), `n` needs to be about **9,500 bets**.
- At `e = 0.05` (5% edge, which is rare), `n` needs to be about **1,500 bets**.

The 200-bet floor in VG-07 is therefore **far below** what a 2% edge requires. It is a policy floor for *listing*, not for *declaring skill*. This is stated here rather than buried because a 200-bet floor that is mistaken for proof would be actively misleading.

**This arithmetic is a derivation from the normal approximation, not a result from data.** It is the reason the pack treats CLV as the primary signal: CLV measures whether the price beat the close, which is far less noisy than win/loss over the same number of bets.

## 4. Why CLV is the better skill signal

A bet can win because of luck and lose despite a good price. Closing-line value asks a narrower, less noisy question: *did we get a better number than the market closed at?* If a model systematically beats the close, that is evidence of information; if it does not, a winning record is not evidence of skill.

CLV requires a timestamped close. We have none, so every CLV cell is blank and VG-03 blocks the whole path. That is the correct outcome, not an inconvenience.

## 5. Correlation and combos

For legs `A` and `B` with probabilities `p_A` and `p_B`:

- independence assumes `P(A∩B) = p_A·p_B`;
- the truth is `P(A∩B) = p_A·p_B + ρ·√(p_A(1-p_A)·p_B(1-p_B))` for a latent-normal copula, where `ρ` is the dependence parameter.

If `ρ > 0` the independent price under-states the joint and the book's parlay price is too generous to the bettor; if `ρ > 0` in a same-game parlay the book already prices it, so the naive product overstates the payout. Either way, **pricing a combo off marginals is a modelling error with a known sign**, which is why VG-10 requires the sign to be preregistered before measurement.

The register in `data/nfl_wk/correlations.csv` preregisters eight pairs and leaves every `ρ` blank.

## 6. What would change this pack from design to evidence

1. **A licence** naming analytics and database construction (Q-01).
2. **A timestamped closing-line archive** for spread, total, moneyline, team total and props (Q-03).
3. **Paired outcome history** at game and player-game level (Q-11).
4. **Dated depth charts or snap counts** so "starter" has a timestamp and a measured share (Q-07, Q-08).
5. **A pilot effect size** so the sample floor is derived instead of asserted (Q-12).

With those five, every gate becomes evaluable and the leaderboard stops being empty for a legitimate reason rather than a structural one.

## 7. What this pack will never do

- Publish a price it did not license.
- Publish a correlation it did not measure.
- Convert a lost starter into points without a fitted conversion.
- Award a rank to a strategy that has not passed every gate.
- Present a computed number as an official NFL figure.
