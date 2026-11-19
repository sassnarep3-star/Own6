# Pre-registration — session `d713b52f`

**Registration rule.** The constants in §3 were fixed in `src/nfl_d713b52f/model.py` before the
first scoring run, and the code is the binding artefact. This file, the first scoring artifacts
and that code entered git together in commit `7d213bf`. That is the true chronology: the
*definitions* predate the *numbers*, but this text was not itself committed ahead of the run, and
this note corrects an earlier draft that said it was. Nothing below may be edited after `7d213bf`
except by a new, dated, separately headed amendment naming what it supersedes.

**Registered:** 2026-11-19 (UTC). **Session:** `d713b52f`. **Branch:** `arena/d713b52f-own6`.

This registration exists so that a fresh reader can check the pack's own numbers were fixed
before they were seen, and it says precisely how strong that guarantee is: the definitions were
written first, and the repository history is printed above rather than asserted.

The earlier registration in `data/nfl_0ce967db/preregistration.md` still governs the seven-strategy family; this file registers what *this* pack adds and
changes nothing about that family's multiplicity count.

## 1. What is being registered here

| Item | Frozen definition |
|---|---|
| `S01` `ML-FROZEN-MARGIN` | A single probability forecaster, re-implemented from the `0ce967db` rule text without reading their code. `P(home win) = Phi((strength_home − strength_away + 2.5) / sigma)`. `strength` is the club's shrunk mean scoring margin, shrink `n/(n+1)`. `sigma` is the sample standard deviation of *already scored* (actual − expected) margins, floored at 7.0 and capped at 25.0. |
| `S02` `TOT-FROZEN` | `expected total = league mean total + (off_home + off_away) − (def_home + def_away)`, each club deviation shrunk by the same `n/(n+1)` rule. |
| `C01` `CONTROL-CLIMATOLOGY` | The training-window home-win rate applied to every game. No club information. |
| `C02` `CONTROL-HOME-ALWAYS` | Probability 1.0 for the home club. |
| `W11-01/02/03` | Three Week 11 forecasts, named in §5, published before kickoff. |

Family size for this pack's own multiplicity note: **2 models**. Controls do not count.

## 2. Data the forecaster may see

Only final scores from `data/nfl_0ce967db/results_feed.csv`, which is itself derived from the
official nfl.com by-week schedule pages. No market price. No injury data. No personnel. No
weather. No earlier season. **The availability work in this pack is deliberately kept out of
the model** so that its ablation (below) has a clean baseline to compare against.

**Chronology.** A game in week *w* uses only weeks strictly below *w*. The code asserts this by
walking the feed in chronological order and updating club state only after a row is scored.

## 3. Fixed constants (not tuned)

`H = 2.5`. `SHRINK_K = 1`. `SIGMA_FLOOR = 7.0`. `SIGMA_CAP = 25.0`.
Bootstrap for the interval: 2,000 week-cluster resamples, seed `20261119`.

## 4. Evaluation protocol

1. **Primary score**: Brier score and Brier skill against `C01` over every scored game.
2. **Uncertainty**: a week-cluster bootstrap lower bound at 95%, because games inside a week
   share a common league environment and are not independent.
3. **Promotion rule** (nothing is promoted by this pack): 100 scored prospective singles **and**
   a week-cluster lower bound above zero **and** a Bonferroni pass at family size 2.
   The backtest can never promote anything; it can only fail to block.
4. **What counts as a failure to report as a failure**: if the lower bound is at or below zero,
   the pack publishes that sentence on the landing page in the same type size as any success
   would have had.

## 5. The three Week 11 forecasts

Registered **before kickoff**: IND at HOU (2026-11-19 20:15 ET), MIA at BUF and BAL at CAR
(2026-11-22 13:00 ET). Only these three are published because only these three fixtures were
read from the official schedule in this session; the other ten are not invented.

Settlement rule: the official final score as published on nfl.com. A tie is a loss for both
sides of the moneyline. No game is dropped after the fact.

## 6. The availability ablation — registered, not run

The brief asks for injury and personnel ablations rather than fixed penalties. The design is
fixed here:

* Base model: `S01` exactly as above, which *cannot* see availability.
* Treatment: the same model with one added feature, the number of the club's declared-Out
  players who were on the previous game's `Not Active` list, at the club's last game.
* Report: the change in Brier skill with a week-cluster interval, on identical games.
* **Why it is not run**: the availability join exists for 4 games and 8 clubs. Running it would
  produce a number over 4 games that could not be told apart from noise, and publishing it
  would be worse than publishing nothing. The ablation stays registered and blocked on
  coverage (`G-ABLATE`), and no fixed penalty is used anywhere in this pack.

## 7. What this registration forbids

* Editing this file after the registration commit.
* Publishing a backtest number in a column that claims to be prospective.
* Any rank, depth order, or snap count that is not read from an official page.
* Reporting a score without its n.
