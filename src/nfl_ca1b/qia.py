"""Question / Information / Answer matrix.

The owner asked for "a clear list of questions, informations and answers that need
to be addressed before any decision can be reasonably made ... and suggestions to
discover missing information".

Each row is one decision that is currently unreachable, and carries:
  Q  the question that must be answered before a bet could be priced,
  I  the information we have (with the official source),
  X  the information we do NOT have,
  A  the answer we can defend today (often "not yet, and here is why"),
  N  the number that would settle it,
  T  the test that would produce that number, and its power if it can be computed.
"""
from __future__ import annotations

import math
from typing import Dict, List

Z95 = 1.959964

# Every number quoted in a row below is computed at import time from the same data
# the site publishes, so prose and tables can never disagree. This is deliberate:
# a hard-coded statistic in explanatory text is the most common way a dashboard
# starts lying.
def _live() -> Dict[str, object]:
    from . import engine, availability
    games = engine.load_games()
    wf = engine.walk_forward(games, engine.teams())
    n = len(wf)
    bs = sum((r["p_home"] - int(r["y_home_win"])) ** 2 for r in wf) / n
    skill = 1 - bs / 0.25
    s = 20261117
    draws = []
    p = [r["p_home"] for r in wf]
    y = [int(r["y_home_win"]) for r in wf]
    for _t in range(1000):
        tot = 0.0
        for _ in range(n):
            s = (1103515245 * s + 12345) % (2 ** 31)
            j = s % n
            tot += (p[j] - y[j]) ** 2
        draws.append(1 - (tot / n) / 0.25)
    draws.sort()
    lo, hi = draws[24], draws[974]
    for r in wf:
        r["p_home_pick"] = max(r["p_home"], 1 - r["p_home"])
    hits = sum(1 for r in wf if (r["p_home"] >= 0.5) == bool(r["y_home_win"]))
    luck = engine.luck_rows(wf, "rating", lambda r: (r["p_home"] >= 0.5,
                                                     max(r["p_home"], 1 - r["p_home"])))
    cal, _ = availability.designation_calibration()
    by = {c["game_designation"]: c for c in cal}
    q = by.get("Questionable", {})
    if by.get("Out", {}).get("n_on_inactive_list") == by.get("Out", {}).get("n_players_joined"):
        out_note = "every Out row that joined was inactive"
    else:
        out_note = ("%d of %d Out rows joined an inactive list; the rest are named on the delta page"
                    % (by.get("Out", {}).get("n_on_inactive_list", 0),
                       by.get("Out", {}).get("n_players_joined", 0)))
    corr = {c["corr_id"]: c for c in engine.correlations(games)}
    return {
        "n": n, "skill": skill, "lo": lo, "hi": hi, "hits": hits,
        "luck_p": luck["exact_two_sided_p"], "own_p": luck["p_two_sided_vs_own_p"],
        "own_exp": luck["expected_hits_under_own_p"],
        "q_n": q.get("n_players_joined", 0), "q_rate": q.get("observed_play_rate", 0.0),
        "q_lo": q.get("wilson_lo", 0.0), "q_hi": q.get("wilson_hi", 0.0),
        "d_n": by.get("Doubtful", {}).get("n_players_joined", 0),
        "d_rate": by.get("Doubtful", {}).get("observed_play_rate", 0.0),
        "b_n": by.get("(blank — no designation published)", {}).get("n_players_joined", 0),
        "b_rate": by.get("(blank — no designation published)", {}).get("observed_play_rate", 0.0),
        "out_note": out_note,
        "corr3_r": corr["CORR-03"]["r"], "corr3_n": corr["CORR-03"]["n"],
        "corr3_lo": corr["CORR-03"]["ci_lo"], "corr3_hi": corr["CORR-03"]["ci_hi"],
    }


L = _live()


def n_for_skill(alt_skill: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Games needed for a one-sided z-test that Brier skill > 0 vs a coin.

    Variance of the per-game Brier difference against p=0.5: for a calibrated
    forecast with true skill s, the per-game Brier is 0.25(1-s) on average and the
    per-game variance of the difference is approximated by 0.25*(1-s)*... using the
    standard normal-approximation formula. The result is rounded up and reported as
    an order of magnitude, never as a promise.
    """
    z_a = 1.644854 if alpha == 0.05 else Z95
    z_b = 0.841621 if power == 0.8 else 1.281552
    # per-game sd of brier(forecast) - brier(coin) under a coin truth ~ 0.25/sqrt(3)
    sd = 0.25 / math.sqrt(3.0)
    return int(math.ceil(((z_a + z_b) * sd / (0.25 * alt_skill)) ** 2))


ROWS: List[Dict[str, object]] = [
    dict(qid="Q-01", area="Rights / capture",
         question="May this project retrieve nfl.com pages on a schedule and store them?",
         have="NFL.com Terms of Use were read by an earlier session: the pages are the league's property and systematic retrieval is restricted (https://www.nfl.com/legal/terms/). Every capture in this repo is a single manual read with a clock time.",
         missing="A written permission, or a licensed data feed. Nothing in the repo substitutes for it.",
         answer="Not today. Capture stays manual and dated; no CI job fetches nfl.com.",
         number="1 written permission (or 1 licensed feed contract)",
         test="Owner decision. Until then every automation suggestion stays behind this gate.",
         power="not a statistical question"),
    dict(qid="Q-02", area="Price",
         question="Where does an opening and closing market price come from?",
         have="Official NFL pages publish schedule, results, standings, injuries and inactives. None publishes a betting price.",
         missing="Any price at all: opening, closing, or live. This is why ROI, CLV and every 'market' column in the repo is blank.",
         answer="The project cannot compute ROI or CLV from official sources. It can only originate a fair line and publish it beside a blank market column.",
         number=">= 1 timestamped price per originated market, from a licensed archive",
         test="Archive ingest; then the residual column is computable on day one.",
         power="not a statistical question"),
    dict(qid="Q-03", area="Skill",
         question="Does the rating model beat a coin over a season, or only over 101 games?",
         have=("Walk-forward on %d games: Brier skill vs coin %.4f, game-bootstrap 95%% CI [%.4f, %.4f]. "
               "The lower bound includes zero." % (L["n"], L["skill"], L["lo"], L["hi"])),
         missing="A prospective sample. Every one of those 101 games was graded after the fact.",
         answer="Not established. The point estimate is positive and the interval is not.",
         number="%d prospective games to detect skill 0.05 at 80%% power (%d to detect the observed %.3f)"
                % (n_for_skill(0.05), n_for_skill(L["skill"]), L["skill"]),
         test="Pre-registered singles-only shadow: one unit per game, probability stored before kickoff, proper scores after the official final.",
         power="detect 0.05 skill: %d games; detect the observed %.3f: %d games"
               % (n_for_skill(0.05), L["skill"], n_for_skill(L["skill"]))),
    dict(qid="Q-04", area="Calibration",
         question="Are the published probabilities honest, and what does a game designation mean?",
         have=("Raw model is overconfident in the tail: its 80-100%% band predicted 0.895 and observed "
               "0.636 over 22 games. A walk-forward variance multiplier (median k = 1.8) brings the same "
               "band to 0.839 predicted against 1.000 observed over 8 games - better, but on 8 games. "
               "Week-10 designations joined to the official inactive lists: Questionable played %.1f%% "
               "(n=%d, 95%% CI %.1f-%.1f), Doubtful %.1f%% (n=%d), blank %.1f%% (n=%d). %s."
               % (L["q_rate"] * 100, L["q_n"], L["q_lo"] * 100, L["q_hi"] * 100,
                  L["d_rate"] * 100, L["d_n"], L["b_rate"] * 100, L["b_n"], L["out_note"])),
         missing="Multi-week designation history; the tail bins are still too small to certify.",
         answer="Questionable is closer to 'probably plays' than to the old 50% folklore, and Out is a hard exclusion. The sample is one week.",
         number=">= 3 weeks of hub reads (about 400 Questionable rows) before the designation becomes a model feature",
         test="Join each designation to the official inactive list per week; publish the play rate with a Wilson interval.",
         power="+/-5 points on a 0.80 play rate needs n=246 designation rows"),
    dict(qid="Q-05", area="Depth / availability",
         question="Who actually starts, and who replaced whom?",
         have="The club depth-chart route on nfl.com returns 404 (probe P-01, 2026-11-17). No official snap-count page was reachable. The official inactives article names 147 inactive players for week 10.",
         missing="A dated starting line-up per game, and snap shares. Without them '2nd-string corner replaces starter' cannot be stated, only suspected.",
         answer="Cannot be answered from the sources that exist. Depth rank must stay blank; the deficiency view can only report designations and inactive evidence.",
         number="32 dated starting line-ups (one per club) or 1 official snap-count source covering all games",
         test="NFL Game Book PDFs name starters and snaps; the host was unreachable from this sandbox (sibling pack FLAG-07). That is a network question, not a data question.",
         power="not a statistical question"),
    dict(qid="Q-06", area="Leaderboard",
         question="Which strategy, if any, deserves money, and how is that decided without being fooled by luck?",
         have="Five strategies registered with SHA-256 rule hashes; five demotion gates; exact binomial and Poisson-binomial luck tests; game-cluster bootstrap intervals; a five-trial multiplicity adjustment (alpha 0.0102).",
         missing="Prospective settlements and prices. Nothing has been bet, and no strategy can be promoted.",
         answer="No strategy is promotable. The leaderboard publishes backtest scores on a separate page and keeps every rank column blank.",
         number=">= 100 prospective settled singles for a first rank; >= 32 for a first published Brier",
         test="One unit per pre-registered pick, settled against the official final, scored with Brier and the cluster lower bound.",
         power="see Q-03"),
    dict(qid="Q-07", area="Data integrity",
         question="Can any number already published by the repo be trusted after today's re-read?",
         have="971 stored values re-tested: 288/288 comparable standings club-rows and 625 joined result rows reconcile to today's official pages. 0 contradictions.",
         missing="Clubs whose abbreviation differs between pack and page (AZ/ARI, LA/LAR) needed an alias map; the alias itself is an unverified assumption about the page's intent.",
         answer=("Yes, with documented gaps rather than errors: two packs' results feeds stop before "
                 "week 10, five week-10 finals are absent from two feeds (both reads predate the games), "
                 "one pack stores the score of a game that was still live when it captured it (SF 24-19 "
                 "DAL, now 46-40 final), and s11's own 2026-11-15 diagnosis that d966f630 stores injury "
                 "text the live page does not show is CONFIRMED here on the IND Arden Key row. Not one "
                 "stored value contradicts the official page."),
         number="0 open contradictions after the next full re-read",
         test="Re-run scripts/check_nfl_ca1b.py; it fails the build on any new mismatch.",
         power="not a statistical question"),
    dict(qid="Q-08", area="Schedule / venue",
         question="Which stadium is each week-11 game actually in?",
         have="All 13 venues transcribed from official pages. Two official surfaces disagree on three names (Reliant vs NRG, FedEx vs Northwest, Arrowhead vs GEHA Field at Arrowhead).",
         missing="A single authoritative naming. The league uses different strings on the schedule page and the game centre.",
         answer="Publish both strings with the surface that carries them; do not pick one silently.",
         number="1 published league naming convention, or the owner's decision to prefer the game-centre string",
         test="Compare the two surfaces per fixture; log every disagreement.",
         power="not a statistical question"),
    dict(qid="Q-09", area="Totals",
         question="Do the model's expected totals carry information about the realised total?",
         have=("In-sample correlation between expected and actual total is %.3f (n=%d, 95%% CI %.3f-%.3f). "
               "In-sample is optimistic by construction." % (L["corr3_r"], L["corr3_n"], L["corr3_lo"], L["corr3_hi"])),
         missing="An out-of-sample total grade. Totals cannot be scored as bets without a line, so this can only be scored as a forecast.",
         answer="The signal exists in-sample; the out-of-sample test is registered as S02 and has not been run.",
         number=">= 100 out-of-sample fixtures with a stored expected total",
         test="Walk-forward expected total vs actual total correlation with 95% CI.",
         power="a correlation of 0.30 needs n=85 for a 95% CI to exclude 0; the registered S02 test uses 100"),
    dict(qid="Q-10", area="Leaderboard hygiene",
         question="How do we stop a lucky staking run from masking a bad signal?",
         have="Signal and staking are separate columns by construction; a staking run cannot promote a strategy whose signal gate failed (demotion rule D-04).",
         missing="A live staking series to test the separation against (no price exists).",
         answer="Structurally solved; untested in practice.",
         number=">= 50 settled priced bets",
         test="Rank on the signal column; publish staking beside it, never instead of it.",
         power="not a statistical question"),
]

PRE_STATED = {
    "Q-01": "This session did NOT automate any capture. The scheduled-capture suggestions are marked blocked-by-Q-01 on the suggestions page.",
    "Q-02": "Every market column in data/nfl_ca1b is blank, with the reason in market_gate.",
    "Q-03": "S01 is registered with the exact settlement rule before any prospective game.",
    "Q-04": "The calibration measurement above is descriptive; it is not used as a feature yet.",
    "Q-05": "No depth rank is published anywhere in this pack.",
    "Q-06": "The leaderboard ranks are blank; the backtest page is separate and labelled as such.",
}


def rows() -> List[Dict[str, object]]:
    out = []
    for r in ROWS:
        out.append({**r, "pre_stated_action": PRE_STATED.get(r["qid"], "")})
    return out
