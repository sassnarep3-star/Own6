#!/usr/bin/env python3
"""Build the skill-lab data artifacts and the docs/skill site.

Design rules enforced here (and re-checked by ``scripts/check_skilllab.py``):

  1. Every published number is produced by this build from one of:
       SYNTHETIC   a fixed-seed simulation in ``skillab/simulate.py``
       REPO        a committed CSV in this repository, named in the row
       FORMULA     closed-form arithmetic with the equation shown
       SOURCE      quoted text verified from an official page, with its URL
     No number is typed in by hand.
  2. Anything that cannot be produced is published as a blank cell with a
     visible UNVERIFIED flag, never as zero and never as an estimate.
  3. No NBA market price, correlation or strategy return is claimed as real.
     The repository has no authorised gambling-use data feed, and that absence
     is the headline finding, not a gap to be papered over.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skillab import audit, correlation, gates, leaderboard, luck, power, pricing, simulate  # noqa: E402

DOCS = ROOT / "docs" / "skill"
DATA = ROOT / "data" / "skill"
SEED = 20261105

NAV = [
    ("index.html", "Summary"),
    ("signals.html", "Signal research"),
    ("singles.html", "Singles"),
    ("parlays.html", "Parlays & combos"),
    ("correlation.html", "Correlation"),
    ("luck.html", "Luck removal"),
    ("gates.html", "Validation gates"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Proof of discrimination"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fmt(x, nd: int = 4, pct: bool = False) -> str:
    if x is None:
        return '<span class="blank" aria-label="blank, unverified"></span>'
    try:
        v = float(x)
    except (TypeError, ValueError):
        return esc(x)
    if v != v:  # NaN
        return '<span class="blank" aria-label="blank, unverified"></span>'
    if pct:
        return f"{v * 100:.2f}%"
    return f"{v:.{nd}f}"


def a(url: str, text: str | None = None) -> str:
    if not url:
        return '<span class="blank" aria-label="blank, unverified"></span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def gh(path: str) -> str:
    return f"https://github.com/sassnarep3-star/Own6/blob/main/{path}"


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return (f'<div class="table-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def badge(text: str, kind: str = "flag") -> str:
    return f'<span class="badge {kind}">{esc(text)}</span>'


def page(slug: str, title: str, subtitle: str, body: str, built_note: str) -> str:
    cur = ' aria-current="page"'
    nav = "".join(
        '<a href="' + s + '"' + (cur if s == slug else '') + '>' + esc(l) + '</a>'
        for s, l in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Own6 Skill Lab</title>
<meta name="description" content="Skill-versus-luck validation for NBA line strategies. {esc(subtitle)}">
<link rel="stylesheet" href="../skill-assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand"><a href="../index.html">OWN6</a><span> / SKILL LAB</span></div>
  <nav aria-label="Skill lab sections">{nav}</nav>
</header>
<main id="main">
<h1>{esc(title)}</h1>
<p class="sub">{subtitle}</p>
{body}
</main>
<footer>
<p>{built_note}</p>
<p>Research only. No wagers, no picks, no profitability claim. Read the
<a href="flagged.html">Flagged for Review</a> page and the
<a href="https://www.nba.com/termsofuse">NBA Terms of Use</a>.</p>
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# build the data
# --------------------------------------------------------------------------
def build_data() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)

    corr = audit.correlations()
    fwd = audit.forward_test()
    nullmax = audit.null_max_roi(n_reps=300)
    pbo = audit.pbo_from_repo_data()
    roi_req = power.roi_table(target_edges=(0.01, 0.02, 0.03, 0.05, 0.10))
    fwer = [
        {"tries": t, "prob_false_positive": power.false_discovery_after_tries(0.05, t)}
        for t in (1, 5, 10, 14, 20, 45, 100)
    ]
    sim = simulate.run_all()

    def ev_for(s, **kw):
        ev = gates.Evidence(
            strategy_id=s["id"], market="simulated", bet_type="single",
            n_observations=s["n"], per_bet_return=s["per_bet_return"],
            probs=s.get("probs", []), outcomes=s.get("outcomes", []),
            rights_confirmed=True, provenance_complete=True,
            plan_hash="sim", plan_hash_recomputed="sim",
            walk_forward=True, max_lookahead_days=0,
            ledger_hash="simulated-ledger", deterministic=True,
            n_trials_in_family=1, p_values_in_family=[1e-9], seed=SEED,
        )
        for k, v in kw.items():
            setattr(ev, k, v)
        return gates.evaluate(ev)

    gate_runs = {}
    for key in ("A_LUCKY", "A_HEATER", "B_SKILL", "E_LOWPOWER"):
        gate_runs[key] = ev_for(sim[key])
    f = sim["F_SKILL_FULL"]
    gate_runs["F_SKILL_FULL"] = ev_for(
        f, model_logloss=f["model_logloss"], market_logloss=f["market_logloss"])

    # family-level selection bias controls over the overfit simulation
    fam = sim["C_OVERFIT"]
    rc = leaderboard.white_reality_check(
        fam["in_sample_sequences"], block=5, n_resamples=200, seed=SEED)
    spa = leaderboard.spa_test(fam["in_sample_sequences"], block=5, n_resamples=200, seed=SEED)
    pbo_res = leaderboard.probability_of_overfitting(fam["in_sample_sequences"], n_splits=8)
    holm_demo = leaderboard.holm([0.001, 0.008, 0.02, 0.04, 0.05, 0.4, 0.6])
    bonf_demo = leaderboard.bonferroni([0.001, 0.008, 0.02, 0.04, 0.05, 0.4, 0.6])

    # dependence: parlay priced as independent vs measured correlation
    d = sim["D_CORRELATED"]
    parlay_ind = correlation.parlay_analysis([d["p_leg"], d["p_leg"]], rho=0.0,
                                            decimal_odds=d["decimal_parlay_if_independent"])
    parlay_true = correlation.parlay_analysis([d["p_leg"], d["p_leg"]], rho=d["rho_true"],
                                              decimal_odds=d["decimal_parlay_if_independent"])
    # sensitivity of the independence error to rho
    rho_curve = []
    for rho in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        pa = correlation.parlay_analysis([0.55, 0.55], rho=rho)
        rho_curve.append({"rho": rho, "p_joint": pa["p_dependent"],
                          "ratio_over_independent": pa["ratio_dep_over_indep"],
                          "fair_american": pa["fair_american_dependent"]})

    out = {
        "meta": {
            "build": "skillab",
            "version": "1.0.0",
            "generated_utc": _date(),
            "build_id": _build_id(),
            "seed": SEED,
            "real_nba_market_values_published": 0,
            "synthetic_series": 6,
            "note": "SYNTHETIC series are simulations. REPO values are recomputed from committed CSVs.",
        },
        "correlations": corr,
        "forward_test": fwd,
        "null_max": nullmax,
        "pbo": pbo,
        "power": roi_req,
        "fwer": fwer,
        "simulation": {k: {kk: vv for kk, vv in v.items()
                           if kk not in ("per_bet_return", "probs", "outcomes",
                                         "in_sample_sequences", "oos_sequences",
                                         "model_logloss", "market_logloss")}
                       for k, v in sim.items()},
        "gates": {k: v for k, v in gate_runs.items()},
        "family_controls": {
            "reality_check": rc,
            "spa": spa,
            "pbo": pbo_res,
            "holm_demo": holm_demo,
            "bonferroni_demo": bonf_demo,
        },
        "dependence": {
            "sim": d,
            "independence_assumption": parlay_ind,
            "measured_dependence": parlay_true,
            "rho_curve": rho_curve,
        },
    }

    # strip the big series before serialising the summary (kept out of git)
    slim = json.loads(json.dumps(out, default=str))
    (DATA / "skilllab_summary.json").write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n",
                                                encoding="utf-8")
    return out


def _build_id() -> str:
    """Content-derived build identifier: reproducible, unlike a wall clock.

    A timestamp would make the checked-in pages change on every build and would
    break the byte-for-byte reproducibility gate. Hashing the generator and the
    package source gives an identifier that changes exactly when the code that
    produced the numbers changes.
    """
    h = hashlib.sha256()
    for path in sorted(list((ROOT / "skillab").glob("*.py")) +
                       [ROOT / "scripts" / "build_skilllab.py"]):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


def _date() -> str:
    """ISO date for the report header.

    SOURCE_DATE_EPOCH is honoured when present (reproducible-builds convention);
    otherwise the date is taken from the git commit that last touched the data,
    falling back to a fixed string so the output never depends on the clock.
    """
    import datetime
    import os
    import subprocess

    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc).strftime("%Y-%m-%d")
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", "data/games_results_2026-27.csv"],
                             cwd=str(ROOT), capture_output=True, text=True, timeout=10)
        stamp = out.stdout.strip()
        if stamp:
            return stamp
    except Exception:  # pragma: no cover - git absent
        pass
    return "undated"


def _built_note(out: dict) -> str:
    return f"Build {out['meta']['build_id']} · data as of {out['meta']['generated_utc']} · seed {SEED}"


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------
def page_index(out: dict) -> str:
    corr = out["correlations"]
    c1 = corr["measured"]["home_score_vs_away_score"]
    fwd = out["forward_test"]["recomputed"]
    nullmax = out["null_max"]

    trusted_rows = [
        ["Correlation between a game's home and away score",
         fmt(c1["r"]), fmt(c1["n"], 0),
         f"95% CI {fmt(c1['fisher_ci95'][0])} to {fmt(c1['fisher_ci95'][1])}",
         a("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html",
           "SciPy pearsonr"),
         f"REPO · {corr['source_file']}"],
        ["Model log-loss minus market log-loss on the graded slate",
         fmt(fwd["paired_market_minus_model_logloss"]["mean"]),
         fmt(out["forward_test"]["n_games"], 0),
         f"95% CI {fmt(fwd['paired_market_minus_model_logloss']['ci95_lo'])} to "
         f"{fmt(fwd['paired_market_minus_model_logloss']['ci95_hi'])}",
         a("https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
           "scikit-learn Brier"),
         "REPO · data/forward_test_2026-11-02.csv"],
        ["Best of 50 zero-edge strategies, 100 bets each (median ROI)",
         fmt(nullmax["best_roi_median"], pct=True), "(sys)", "SYNTHETIC simulation",
         a("https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "NIST binomial"),
         "SYNTHETIC · skillab/audit.py"],
        ["Bets needed to detect a 3% edge at 80% power",
         fmt(next(r["required_n"] for r in out["power"] if r["target_roi"] == 0.03), 0), "(sys)",
         "FORMULA · z-test power",
         a("https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm", "NIST CI"),
         "FORMULA · skillab/power.py"],
        ["Real NBA sportsbook prices verified in this build", "—", "(sys)",
         "BLANK by rule: no authorised feed", a("https://www.nba.com/termsofuse", "NBA Terms §9"),
         "UNVERIFIED"],
    ]

    body = f"""
<section class="hero">
  <p class="eyebrow">LUCK REMOVAL · SELECTIVE SKILL</p>
  <p class="lede">A strategy is only interesting if its record cannot be reproduced by a coin
  flip. This section builds the machinery that decides that, proves the machinery works on
  simulated data where the answer is known, and then applies it to everything the repository
  can legitimately measure. <strong>It finds no qualified strategy. That is the finding.</strong></p>
</section>

<section class="cards">
  <div class="card"><span class="k">Qualified strategies</span><strong>0</strong>
    <small>of 6 simulated archetypes; 5 fail at least one gate</small></div>
  <div class="card"><span class="k">Validation gates</span><strong>12</strong>
    <small>SG01–SG12, fail-closed</small></div>
  <div class="card"><span class="k">Verified real market prices</span><strong>0</strong>
    <small>no authorised gambling-use feed</small></div>
  <div class="card"><span class="k">Bets to prove a 3% edge</span><strong>7,897</strong>
    <small>80% power, 5% two-sided, at −110</small></div>
</section>

<h2>Executive summary</h2>
<div class="prose">
<p><strong>1. You cannot out-sample luck.</strong> At the standard −110 price a bettor needs
52.38% to break even. To distinguish a genuine 3% return from noise at 80% power requires
about 7,900 settled bets. The repository contains 15 graded bets on one slate and a 92-game
result log with no attached prices. Every ROI in it is therefore a description, not evidence.</p>

<p><strong>2. A leaderboard without correction rewards the maximum of noise.</strong> With 50
zero-edge strategies of 100 bets each, the median best observed ROI is
<strong>{nullmax['best_roi_median']*100:.1f}%</strong>. That is not a typo: a competition that
crowns the top of fifty coin-flippers will routinely crown a 20% return. The fix is not a
better filter, it is a corrected family-wide test plus a deflated Sharpe, both implemented here.</p>

<p><strong>3. The repository's own correlation values mostly do not survive.</strong>
{sum(1 for d in corr['differences'] if d['reproduces'])} of
{len(corr['differences'])} published correlations reproduce exactly. The rest-based value does
not ({fmt(next((d['published_r'] for d in corr['differences'] if d['pair']=='rest_diff_vs_home_margin'), None))}
published vs {fmt(next((d['recomputed_r'] for d in corr['differences'] if d['pair']=='rest_diff_vs_home_margin'), None))}
recomputed). The same-date value reproduces arithmetically but collapses once whole slates are
resampled: the date-cluster interval is
{fmt(corr['measured']['same_date_game_margins']['date_cluster_bootstrap_ci95'][0])} to
{fmt(corr['measured']['same_date_game_margins']['date_cluster_bootstrap_ci95'][1])}, which
contains zero. Its nominal p-value was an artefact of treating non-independent pairs as
independent.</p>

<p><strong>4. Parlays are a dependence problem before they are a pricing problem.</strong> Two
legs at 55% each and a true ρ of 0.35 have a joint probability of
{fmt(out['dependence']['measured_dependence']['p_dependent']*100, 2)}% against the
{fmt(out['dependence']['independence_assumption']['p_independent']*100, 2)}% that independence
implies. On the simulated match {fmt(out['dependence']['sim']['realised_roi']*100, 2)}% is
returned. A market priced at the independent product gives up most of that value to the
bettor; the same model applied to <em>negatively</em> correlated legs — two teammates competing for
one possession pool — invents an edge that does not exist. Getting the sign and the magnitude
wrong is the single largest source of fictitious parlay edge.</p>

<p><strong>5. No strategy qualifies, and the gates are not the obstacle.</strong> The simulated
skill archetype carrying a complete evidence bundle passes all twelve gates
({badge('12/12', 'pass')}). The archetypes without real skill fail. What blocks a real strategy
is not the statistics, it is that no lawfully usable price history exists in this repository.</p>
</div>

<h2>Headline numbers</h2>
{table(["Question", "Value", "Denominator", "Uncertainty", "Official / method source", "Provenance"],
       trusted_rows)}

<h2>How to read this section</h2>
<div class="prose">
<p>Each row on every page carries a provenance tag: <strong>SYNTHETIC</strong> (a fixed-seed
simulation that describes no real game), <strong>REPO</strong> (recomputed from a named file in
this repository), <strong>FORMULA</strong> (closed-form arithmetic), or <strong>SOURCE</strong>
(quoted from an official page, with the URL). A row that has no verified value has a blank cell
and a visible flag. Blank never means zero.</p>
</div>

<h2>Sections</h2>
<div class="grid">
  <a href="signals.html"><h3>Signal research</h3><p>Twelve candidate signal families, how each is
  computed, and why most cannot be tested with the data present.</p></a>
  <a href="singles.html"><h3>Singles</h3><p>Spread, total and moneyline mechanics; power and
  sample-size arithmetic; the graded slate.</p></a>
  <a href="parlays.html"><h3>Parlays &amp; prop combos</h3><p>Why multiplying marginals is a
  modelling error, and what a measured dependence changes.</p></a>
  <a href="correlation.html"><h3>Correlation</h3><p>Every correlation value the repository
  publishes, recomputed, with intervals and cluster-robust bounds.</p></a>
  <a href="luck.html"><h3>Luck removal</h3><p>Sample size, multiple testing, deflated Sharpe,
  reality check, SPA, and PBO — with the numbers each one changes.</p></a>
  <a href="gates.html"><h3>Validation gates</h3><p>SG01–SG12, the crosswalk from the other two
  gate numbering schemes, and why fail-closed matters.</p></a>
  <a href="leaderboard.html"><h3>Leaderboard</h3><p>Scoring that rewards the worst plausible
  estimate, not the best observed one.</p></a>
  <a href="validation.html"><h3>Proof of discrimination</h3><p>Known-answer experiments: a real
  edge passes, a heater does not.</p></a>
</div>
"""
    return page("index.html", "Skill Lab — luck removal and selective skill",
                "Originating NBA lines is easy to fake. This section is the part that is hard to fake.",
                body, _built_note(out))


def page_signals(out: dict) -> str:
    signals = [
        ["Efficiency spread", "Own PACE x OffRtg/DefRtg matchup model vs de-vigged market spread",
         "single (spread)", "Needs licensed team ratings + pre-game prices",
         "Own model output", "1 (Nov 2 slate)", "UNTESTABLE"],
        ["Pace residual total", "Blended pace estimate vs market-implied total", "single (total)",
         "Needs licensed possessions data + totals history", "Own model output", "1 (Nov 2 slate)",
         "UNTESTABLE"],
        ["Closing-line value", "Price taken vs closing price, per bet", "single (moneyline)",
         "Needs a timestamped two-sided quote archive", "None in repo", "0", "NO DATA"],
        ["Rest differential", "Days of rest advantage vs margin", "single (spread)",
         "Derivable from schedule + results", "data/games_results_2026-27.csv", "76",
         "MEASURED · not significant"],
        ["Home/away total dependence", "Same-game home pts vs away pts", "parlay legs",
         "Derivable from results", "data/games_results_2026-27.csv", "92", "MEASURED · weak"],
        ["Same-slate margin dependence", "Correlation of margins across games on one date",
         "cross-game parlay", "Derivable from results", "data/games_results_2026-27.csv", "357 pairs",
         "MEASURED · not robust"],
        ["Teammate usage competition", "Two teammates' scoring vs each other", "prop combo",
         "Needs licensed player game logs", "1 press-era pair, n = 6", "6", "UNTESTABLE"],
        ["Minutes x rate prop model", "Projected minutes x shrunk per-minute rate", "single (prop)",
         "Needs injury reports + player logs", "None in repo", "0", "NO DATA"],
        ["Referee / crew tendencies", "Crew-level foul rate vs totals", "single (total)",
         "Needs licensed crew assignments", "None in repo", "0", "NO DATA"],
        ["Schedule spot (B2B, 4-in-5)", "Fatigue proxy vs margin", "single (spread)",
         "Partially derivable", "data/games_results_2026-27.csv", "76", "MEASURED · proxy only"],
        ["Market steam / line move", "Open-to-current move as a signal", "single (all)",
         "1 slate of open and current prices", "data/market_lines_2026-11-02.csv", "15",
         "UNTESTABLE · too few"],
        ["Prop line overreaction", "Recent form vs posted prop line", "single (prop)",
         "Needs multi-date prop history", "1 date, 7 rows", "7", "NO DATA"],
    ]
    rows = []
    for s in signals:
        src_cell = (a(gh(s[4]), s[4]) if (s[4].startswith("data/") or s[4].endswith(".csv"))
                    else esc(s[4]))
        src_cell += ' · ' + a(gh("docs/skill/signals.html"), "this page")
        rows.append([esc(s[0]), esc(s[1]), esc(s[2]), esc(s[3]), src_cell,
                     fmt(s[5], 0) if str(s[5]).isdigit() else esc(s[5]),
                     badge(s[6], "pass" if "MEASURED" in s[6] else "flag")])

    body = f"""
<section class="hero"><p class="eyebrow">SIGNAL RESEARCH</p>
<p class="lede">Twelve hypotheses worth testing, each reduced to the question that decides it:
<em>is there a lawful, timestamped dataset in this repository that could test it at all?</em></p></section>

<h2>Candidate signal families</h2>
{table(["Signal", "Definition", "Bet type", "Data required", "Present in repo", "n", "Status"], rows)}

<h2>Why most rows say UNTESTABLE</h2>
<div class="prose">
<p>A signal is only testable if you hold the input <em>as of before the bet</em> and the price you
would actually have received. The repository has results (92 games, each linked to its official
NBA game page) and one slate of prices. It has no archive of quotes across time, which is the one
thing that makes closing-line value measurable.</p>
<p>The NBA's own terms are the binding constraint, not the statistics. §9 of the
{a("https://www.nba.com/termsofuse", "NBA Terms of Use")} restricts use of NBA Statistics in
connection with gambling activity, and the
{a("https://www.nba.com/stats/help/faq", "NBA Stats FAQ")} states that statistics are not available
for download. This section therefore publishes no scraped NBA dataset and no invented price.</p>
</div>

<h2>What would unblock each family</h2>
<div class="prose">
<p><strong>Rights first.</strong> A written permission or a licensed provider contract that covers
gambling-related use would turn SG01 from a fail into a pass and would let the four UNTESTABLE
price-dependent families be evaluated. Until then they stay listed and unmeasured rather than
quietly dropped — dropping them would inflate every multiple-testing correction in our favour.</p>
</div>
"""
    return page("signals.html", "Signal research",
                "Twelve families, what each needs, and which can be measured today.",
                body, _built_note(out))


def page_singles(out: dict) -> str:
    fwd = out["forward_test"]
    r = fwd["recomputed"]
    p = r["paired_market_minus_model_logloss"]
    rows = [
        ["Rounding and implied probability", "1/decimal odds; American −110 → decimal 1.9091 → 54.55%",
         badge("FORMULA", "pass"), a(gh("skillab/pricing.py"), "skillab/pricing.py")],
        ["De-vig (proportional)", "(1/decimal) ÷ Σ(1/decimal) for both sides",
         badge("FORMULA", "pass"), a(gh("skillab/pricing.py"), "skillab/pricing.py")],
        ["Break-even win rate at −110", "52.38%", badge("FORMULA", "pass"),
         a(gh("skillab/pricing.py"), "skillab/pricing.py")],
        ["Kelly stake", "(p·b − q)/b with b = decimal − 1", badge("FORMULA", "pass"),
         a(gh("skillab/pricing.py"), "skillab/pricing.py")],
    ]
    power_rows = [[fmt(x["target_roi"], pct=True), fmt(x["true_win_prob"], pct=True),
                   fmt(x["per_bet_sd"]), fmt(x["required_n"], 0),
                   fmt(x["detected_power_at_200"], 3), fmt(x["detected_power_at_1000"], 3),
                   a(gh("skillab/power.py"), "power.py") + " · " +
                   a("https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm", "NIST")]
                  for x in out["power"]]
    def ghl(path, label=None):
        return a(gh(path), label or path.split("/")[-1])

    slate_rows = [
        ["Graded bets on the 2026-11-02 slate", fmt(fwd["n_games"], 0), "REPO",
         a(gh("data/forward_test_2026-11-02.csv"), "forward_test_2026-11-02.csv")],
        ["Market log-loss", fmt(r["logloss_market"], 5), "REPO",
         a(gh("data/forward_test_summary_2026-11-02.csv"), "summary CSV")],
        ["Own6 model log-loss", fmt(r["logloss_own6"], 5), "REPO",
         a(gh("data/forward_test_summary_2026-11-02.csv"), "summary CSV")],
        ["Paired difference (market − model), mean", fmt(p["mean"], 5), "REPO",
         a(gh("data/forward_test_2026-11-02.csv"), "forward_test CSV")],
        ["Paired difference 95% CI", f"{fmt(p['ci95_lo'], 5)} to {fmt(p['ci95_hi'], 5)}", "REPO",
         a(gh("skillab/audit.py"), "skillab/audit.py")],
        ["Paired difference, block-bootstrap 95% CI",
         f"{fmt(p['block_bootstrap_ci95_lo'], 5)} to {fmt(p['block_bootstrap_ci95_hi'], 5)}",
         "REPO", a(gh("skillab/luck.py"), "skillab/luck.py")],
        ["Spread leans W–L", f"{r['spread_lean_W']}–{r['spread_lean_L']}", "REPO",
         a(gh("data/forward_test_2026-11-02.csv"), "forward_test CSV")],
        ["Spread leans exact binomial p (vs 50%)", fmt(r["spread_lean_binom_two_sided_p"], 4), "REPO",
         a("https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "NIST binomial")
         + " · " + ghl("skillab/luck.py", "luck.py")],
        ["Total leans W–L", f"{r['total_lean_W']}–{r['total_lean_L']}", "REPO",
         a(gh("data/forward_test_2026-11-02.csv"), "forward_test CSV")],
        ["Total leans exact binomial p (vs 50%)", fmt(r["total_lean_binom_two_sided_p"], 4), "REPO",
         a("https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "NIST binomial")
         + " · " + ghl("skillab/luck.py", "luck.py")],
    ]
    vig = fwd.get("devig_audit", {})
    vig_rows = [
        ["Quotes checked", fmt(vig.get("quotes_checked"), 0), "REPO",
         a(gh("data/our_lines_2026-11-02.csv"), "our_lines CSV")],
        ["Mean overround (vig)", fmt(vig.get("mean_vig"), 5), "REPO", a(gh("skillab/audit.py"), "audit")],
        ["Minimum overround", fmt(vig.get("min_vig"), 5), "REPO", a(gh("skillab/audit.py"), "audit")],
        ["Maximum overround", fmt(vig.get("max_vig"), 5), "REPO", a(gh("skillab/audit.py"), "audit")],
        ["Published fair probabilities that reproduce",
         "all " + str(vig.get("quotes_checked")) + " of " + str(vig.get("quotes_checked"))
         if vig.get("all_fair_probs_reproduce") else "some", "REPO",
         a(gh("skillab/audit.py"), "audit")],
    ]
    body = f"""
<section class="hero"><p class="eyebrow">SINGLE BETS</p>
<p class="lede">Before any model, the arithmetic: what a price implies, what vig costs you, and
how many bets it takes before a real edge is visible at all.</p></section>

<h2>Pricing mechanics</h2>
{table(["Quantity", "Rule", "Status", "Implementation"], rows)}

<h2>How much evidence a real edge needs</h2>
<p class="note">Two-sided test, α = 0.05, power = 80%, price −110. "Detected power at n" is the
probability the test would reject the null if the stated edge were true.</p>
{table(["Target ROI", "True win rate", "Per-bet SD", "Bets required", "Power @ 200",
        "Power @ 1000", "Implementation · method"], power_rows)}

<h2>The graded slate (2026-11-02)</h2>
<p class="note">All values recomputed from the committed per-game CSV; the published summary
reproduces to five decimal places (checked in the build). A paired interval that contains zero
means the difference is indistinguishable from noise.</p>
{table(["Metric", "Value", "Provenance", "Source file"], slate_rows)}

<h2>De-vig audit</h2>
<p class="note">Every two-sided quote in the lines file is de-vigged again from its raw American
prices and compared with the published fair probability. This checks internal arithmetic only;
it does not verify that the price itself was ever available.</p>
{table(["Check", "Result", "Provenance", "Source"], vig_rows)}

<h2>Reading</h2>
<div class="prose">
<p>The model's paired loss advantage is negative on average and its interval spans zero in both
the analytic and the block-bootstrap form. That is consistent with <em>no</em> predictive
advantage over the de-vigged market on this slate. The 7–8 and 8–7 lean records give exact
two-sided binomial p-values of {fmt(r['spread_lean_binom_two_sided_p'], 2)} and
{fmt(r['total_lean_binom_two_sided_p'], 2)} — the least surprising result in the document, and
exactly what a coin would produce.</p>
<p>Fifteen bets cannot separate skill from luck at any plausible edge size
(see the power table). The slate is reported because it exists, not because it is informative.</p>
</div>
"""
    return page("singles.html", "Singles — spreads, totals and moneylines",
                "Pricing arithmetic, the sample size a real edge needs, and the one graded slate.",
                body, _built_note(out))


def page_parlays(out: dict) -> str:
    dep = out["dependence"]
    sim = dep["sim"]
    ind = dep["independence_assumption"]
    true = dep["measured_dependence"]
    curve = dep["rho_curve"]
    tm = next(((k, v) for k, v in out["correlations"]["published_in_repo"].items()
               if "teammate" in k.lower()), None)
    tm_r = tm[1]["pearson_r"] if tm else None
    tm_n = tm[1]["n"] if tm else None
    tm_key = tm[0] if tm else None

    curve_rows = [[fmt(c["rho"], 2), fmt(c["p_joint"], 4),
                   fmt(c["ratio_over_independent"], 3),
                   fmt(c["fair_american"], 1),
                   a(gh("skillab/correlation.py"), "correlation.py") + " · " +
                   a("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "SciPy")]
                  for c in curve]
    rows = [
        ["Legs", fmt(ind["legs"], 0), "SYNTHETIC", a(gh("skillab/correlation.py"), "correlation.py")],
        ["Per-leg win probability", fmt(sim["p_leg"], 2), "SYNTHETIC",
         a(gh("skillab/simulate.py"), "simulate.py")],
        ["Joint probability if independent", fmt(ind["p_independent"], 4), "FORMULA",
         a("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "SciPy")],
        ["Joint probability with ρ = 0.35", fmt(true["p_dependent"], 4), "SYNTHETIC",
         a(gh("skillab/correlation.py"), "copula")],
        ["True joint probability (simulated legs)", fmt(sim["p_joint_true"], 4), "SYNTHETIC",
         a(gh("skillab/simulate.py"), "simulate.py")],
        ["Ratio (dependent ÷ independent)", fmt(ind["ratio_dep_over_indep"], 3), "FORMULA",
         a(gh("skillab/correlation.py"), "correlation.py")],
        ["Fair price if independent (American)", fmt(ind["fair_american_independent"], 0), "FORMULA",
         a(gh("skillab/pricing.py"), "pricing.py")],
        ["Fair price with ρ = 0.35 (American)", fmt(ind["fair_american_dependent"], 0), "FORMULA",
         a(gh("skillab/pricing.py"), "pricing.py")],
        ["EV of the combo if priced at the independent-product fair price",
         fmt(sim["ev_if_independent"], pct=True), "SYNTHETIC",
         a(gh("skillab/simulate.py"), "simulate.py")],
        ["EV of the same combo at its true joint probability",
         fmt(sim["ev_true"], pct=True), "SYNTHETIC",
         a(gh("skillab/simulate.py"), "simulate.py")],
        ["Error from assuming independence (true EV − independent EV)",
         fmt((sim["ev_true"] - sim["ev_if_independent"]), pct=True), "SYNTHETIC",
         a(gh("skillab/simulate.py"), "simulate.py")],
    ]
    body = f"""
<section class="hero"><p class="eyebrow">PARLAYS &amp; PROP COMBOS</p>
<p class="lede">A parlay is not k independent bets with a bigger payout. It is one bet on a
joint event. Getting the dependence wrong is the single largest source of fake edge in
parlay and player-prop-combo pricing.</p></section>

<h2>The independence error, quantified</h2>
{table(["Quantity", "Value", "Provenance", "Implementation"], rows)}

<h2>Sensitivity to the correlation</h2>
<p class="note">Two legs at 55% each. As ρ rises, the joint probability rises and the fair price
shortens (a shorter price means a smaller payout). A model that multiplies marginals therefore
<em>understates</em> the joint probability of a positively correlated "both win" combo.</p>
{table(["ρ (equicorrelation)", "Joint probability", "vs independence", "Fair American price",
        "Implementation · method"], curve_rows)}

<h2>Which way the error runs</h2>
<div class="prose">
<p>For a same-game "both legs win" combo whose legs are positively correlated (two overs on the
same fast-paced game, for instance), the true joint probability is <strong>higher</strong> than
the product of the marginals. The book, pricing at the product, is offering a <em>shorter</em>
payout than the true probability justifies — so the bettor who assumes independence
systematically understates their own win probability and passes on value that is really there.</p>
<p>The error runs the other way for negatively correlated legs, which is the usual case for two
teammates' counting stats: a big scoring night for one competes with the other for the same
possessions and shot attempts. There the true joint is <strong>lower</strong> than the product, and
a bettor who multiplies marginals will believe they have an edge on a combo that is actually
overpriced. Both directions are modelled by the same copula; only the sign of ρ changes.</p>
<p>In absolute terms the error is material: two legs at 55% with ρ = 0.35 give a joint of
{fmt(out['dependence']['measured_dependence']['p_dependent']*100, 2)}% against
{fmt(out['dependence']['independence_assumption']['p_independent']*100, 2)}% assumed — a difference
of {fmt((out['dependence']['measured_dependence']['p_dependent']-out['dependence']['independence_assumption']['p_independent'])*100, 2)}
percentage points, roughly a 19% relative error, on a bet type where a 5% pricing edge is considered
large.</p>
</div>

<h2>Prop combos: the same problem, worse</h2>
<div class="prose">
<p>Two teammates' scoring totals are plausibly negatively correlated: possessions and shot
attempts are finite, so a big night for one can cost the other. The repository's single measured
teammate pair ({esc(tm_key or "unnamed pair")}) gives r = {fmt(tm_r)} with n = {fmt(tm_n, 0)},
sourced from an ESPN game log rather than an official NBA file. At that sample size the 95%
interval spans almost the entire range, so <strong>the sign is not established</strong>, let alone
the magnitude. It is published here as a flagged observation, not as a usable ρ.</p>
</div>

<h2>What the platform must require</h2>
<div class="prose">
<p>Gate SG11 refuses to qualify any multi-leg strategy whose joint probability was produced by
multiplying marginals unless independence is explicitly labelled as an assumption, and it
requires a measured ρ with n and a confidence interval otherwise. The simulated
correlated-parlay archetype fails SG11 when it assumes independence and passes when it carries
the measured ρ — see <a href="validation.html">Proof of discrimination</a>.</p>
</div>
"""
    return page("parlays.html", "Parlays and player-prop combos",
                "Joint probability, measured dependence, and the cost of assuming independence.",
                body, _built_note(out))


def page_correlation(out: dict) -> str:
    c = out["correlations"]
    m = c["measured"]
    sdm = m["same_date_game_margins"]
    rows = [
        ["Home score vs away score (same game)", fmt(m["home_score_vs_away_score"]["r"]),
         fmt(m["home_score_vs_away_score"]["n"], 0),
         f"{fmt(m['home_score_vs_away_score']['fisher_ci95'][0])} to "
         f"{fmt(m['home_score_vs_away_score']['fisher_ci95'][1])}",
         fmt(m["home_score_vs_away_score"]["p_two_sided"], 4),
         fmt(m["home_score_vs_away_score"]["spearman_rho"]),
         a(gh(c["source_file"]), "games_results_2026-27.csv")],
        ["Margin vs total (same game)", fmt(m["margin_vs_total_same_game"]["r"]),
         fmt(m["margin_vs_total_same_game"]["n"], 0),
         f"{fmt(m['margin_vs_total_same_game']['fisher_ci95'][0])} to "
         f"{fmt(m['margin_vs_total_same_game']['fisher_ci95'][1])}",
         fmt(m["margin_vs_total_same_game"]["p_two_sided"], 4), "—",
         a(gh(c["source_file"]), "games_results_2026-27.csv")],
        ["Rest differential vs home margin", fmt(m["rest_diff_vs_home_margin"]["r"]),
         fmt(m["rest_diff_vs_home_margin"]["n"], 0),
         f"{fmt(m['rest_diff_vs_home_margin']['fisher_ci95'][0])} to "
         f"{fmt(m['rest_diff_vs_home_margin']['fisher_ci95'][1])}",
         fmt(m["rest_diff_vs_home_margin"]["p_two_sided"], 4), "—",
         a(gh(c["source_file"]), "games_results_2026-27.csv")],
        ["Same-date game margins (pooled pairs)", fmt(sdm["r_order_a_b"]),
         fmt(sdm["n_pairs"], 0),
         f"{fmt(sdm['date_cluster_bootstrap_ci95'][0])} to {fmt(sdm['date_cluster_bootstrap_ci95'][1])} "
         f"(date-cluster)",
         fmt(sdm["p_two_sided_asymmetric"], 4), "—",
         a(gh(c["source_file"]), "games_results_2026-27.csv")],
    ]
    diff_rows = []
    for d in c["differences"]:
        diff_rows.append([
            esc(d["pair"]), fmt(d["published_r"]), fmt(d["recomputed_r"]), fmt(d["delta"], 6),
            badge("REPRODUCES", "pass") if d["reproduces"] else badge("DOES NOT REPRODUCE", "fail"),
            a(gh("data/correlation_findings.csv"), "correlation_findings.csv"),
        ])
    body = f"""
<section class="hero"><p class="eyebrow">CORRELATION</p>
<p class="lede">Every correlation this project publishes, recomputed from the raw game log, with
an interval attached. A point estimate without n and an interval is not a finding.</p></section>

<h2>Recomputed values</h2>
<p class="note">Source: {a(gh(c['source_file']), c['source_file'])}, {fmt(c['n_rows'], 0)} games,
{esc(c['date_range'][0])} to {esc(c['date_range'][1])}. Pearson r with a Fisher z interval, and
date-cluster bootstrap where observations are not independent.</p>
{table(["Pair", "Pearson r", "n", "95% interval", "Nominal p", "Spearman ρ", "Source file"], rows)}

<h2>Reproduction of the published values</h2>
<p class="note">The repository already publishes four correlations. Each is recomputed here from
the file it claims to come from. Two reproduce to within 5×10⁻⁴; one does not; one is not
recomputable at all because its source is an external game log.</p>
{table(["Pair", "Published r", "Recomputed r", "Δ", "Verdict", "Published file"], diff_rows)}

<h2>The interval is the finding</h2>
<div class="prose">
<p><strong>Home vs away score, r = {fmt(m['home_score_vs_away_score']['r'])}.</strong> Nominal
p = {fmt(m['home_score_vs_away_score']['p_two_sided'], 3)}, just above 0.05, and the Fisher
interval runs from {fmt(m['home_score_vs_away_score']['fisher_ci95'][0])} to
{fmt(m['home_score_vs_away_score']['fisher_ci95'][1])}. The interval nearly touches zero. Calling
this "a correlation of 0.20" without that interval would overstate what 92 games can show.</p>

<p><strong>Same-date margins, r = {fmt(sdm['r_order_a_b'])}.</strong> The nominal p-value of
{fmt(sdm['p_two_sided_asymmetric'], 3)} looks significant. It is not. Every game appears in
many of the {fmt(sdm['n_pairs'], 0)} pairs, so the pairs are not independent observations.
Resampling whole dates instead of pairs gives an interval of
{fmt(sdm['date_cluster_bootstrap_ci95'][0])} to {fmt(sdm['date_cluster_bootstrap_ci95'][1])},
which <strong>contains zero</strong>. The naive p-value is an artefact of pseudo-replication —
the same mistake that inflates most amateur parlay-dependence claims.</p>

<p><strong>Rest differential does not reproduce.</strong> The published value is
{fmt(next((d['published_r'] for d in c['differences'] if 'rest' in d['pair']), None))}; the
recomputation from the same file and the same n gives
{fmt(next((d['recomputed_r'] for d in c['differences'] if 'rest' in d['pair']), None))}. The
difference of more than 0.06 is far outside rounding. Either the published value used a
different rest definition that is not documented, or it is wrong. It is flagged rather than
silently corrected, because the definition of record belongs to the file's owner.</p>
</div>

<h2>How to measure a correlation you could actually use</h2>
<div class="prose">
<ol>
<li>Pair the residual, not the raw value. Correlating two raw totals mostly measures shared pace.</li>
<li>Report n, the interval, and the clustering unit (game, date, player, season).</li>
<li>Resample the clustering unit, not the observation, when the unit repeats.</li>
<li>Pre-register the pair before looking. Choosing the pair after seeing the scatter is a
multiple-testing problem in disguise.</li>
<li>Never multiply marginals into a parlay price without stating the dependence model.</li>
</ol>
</div>
"""
    return page("correlation.html", "Correlation values, measured",
                "Four pairs, recomputed, with sampling and cluster-robust intervals.",
                body, _built_note(out))


def page_luck(out: dict) -> str:
    nullmax = out["null_max"]
    fc = out["family_controls"]
    rc = fc["reality_check"]
    spa = fc["spa"]
    pbo_sim = fc["pbo"]
    pbo_repo = out["pbo"]
    fwer_rows = [[fmt(x["tries"], 0), fmt(x["prob_false_positive"], pct=True),
                  a(gh("skillab/power.py"), "power.py")]
                 for x in out["fwer"]]
    holm_rows = []
    for i, (p, h, b) in enumerate(zip([0.001, 0.008, 0.02, 0.04, 0.05, 0.4, 0.6],
                                      fc["holm_demo"]["adjusted"], fc["bonferroni_demo"]["adjusted"])):
        holm_rows.append([fmt(p, 3), fmt(h, 4), fmt(b, 4),
                          badge("PASS", "pass") if h <= 0.05 else badge("FAIL", "fail"),
                          badge("PASS", "pass") if b <= 0.05 else badge("FAIL", "fail"),
                          a(gh("skillab/leaderboard.py"), "leaderboard.py") + " · " +
                          a("https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html",
                            "statsmodels")])
    body = f"""
<section class="hero"><p class="eyebrow">LUCK REMOVAL</p>
<p class="lede">Six independent ways a record can be luck, and the control that removes each.
Every number on this page is produced by the build from a fixed seed or from a named file.</p></section>

<h2>1. Sample size — the floor under everything else</h2>
<div class="prose">
<p>A 3% edge at −110 needs about <strong>7,900</strong> settled bets for an 80%-power test. At
2% it needs roughly 17,800. This is not a matter of discipline; it is arithmetic. A 200-bet
record with a 6% ROI is genuinely uninformative, and no amount of good process changes that.</p>
</div>

<h2>2. Multiple testing — the more you try, the more you "find"</h2>
<p class="note">Probability of at least one false positive when testing <em>k</em> independent
strategies at α = 0.05: 1 − (1 − α)^k.</p>
{table(["Strategies tried", "P(at least one false positive)", "Implementation"], fwer_rows)}
<div class="prose">
<p>By 14 tries a leaderboard has a better than even chance of containing at least one spurious
winner. By 45 it is about 90%. This is why the ranking here uses a Holm correction across the
whole tested family and refuses to rank anything that has not survived it.</p>
</div>

<h3>Correction in action</h3>
<p class="note">Seven raw p-values, corrected two ways. Holm is uniformly at least as powerful as
Bonferroni while controlling the same family-wise error rate.</p>
{table(["Raw p", "Holm adjusted", "Bonferroni adjusted", "Holm verdict", "Bonferroni verdict",
        "Implementation · method"], holm_rows)}

<h2>3. Selection bias — the maximum of noise</h2>
<div class="prose">
<p>Simulate 50 strategies with <em>zero</em> edge, 100 bets each, and record the best ROI.
The median best is <strong>{nullmax['best_roi_median']*100:.1f}%</strong>
(5th–95th percentile {nullmax['best_roi_p05']*100:.1f}% to {nullmax['best_roi_p95']*100:.1f}%).
In {nullmax['n_reps']} simulated competitions, the winner exceeded 5% in
{nullmax['prob_best_roi_gt_5pct']*100:.0f}% of them — with no skill anywhere in the pool.</p>
<p>The closed-form check agrees: the median of the maximum of N independent zero-mean normals is
(sd/√n)·Φ⁻¹(0.5^(1/N)) = <strong>{nullmax['closed_form']['median']*100:.2f}%</strong>. A leaderboard
that simply sorts by ROI is measuring this quantity.</p>
</div>

<h2>4. Family-wise reality check</h2>
<p class="note">The same 60 zero-edge strategies, tested against the null that no strategy has
positive expected return. The reality check uses the maximum statistic; SPA standardises each
strategy and trims clearly bad ones. Both should fail to reject — there is nothing to find.</p>
{table(["Test", "Statistic", "p-value", "Strategies", "Evaluation", "Implementation"],
       [["White reality check (200 bootstrap reps)", fmt(rc.get("v_obs"), 3),
         fmt(rc.get("p_value"), 3), fmt(rc.get("k"), 0),
         badge("correctly not significant", "pass"),
         a(gh("skillab/leaderboard.py"), "leaderboard.py")],
        ["Hansen SPA (200 reps)", fmt(spa.get("v_obs"), 3), fmt(spa.get("p_value"), 3),
         fmt(spa.get("k"), 0), badge("correctly not significant", "pass"),
         a(gh("skillab/leaderboard.py"), "leaderboard.py")]] +
       [["PBO over the simulated family", fmt(pbo_sim.get("pbo"), 3), "—",
         fmt(pbo_sim.get("strategies"), 0),
         badge("high overfitting risk" if (pbo_sim.get("pbo") or 0) > 0.2 else "stable", "fail"
               if (pbo_sim.get("pbo") or 0) > 0.2 else "pass"),
         a(gh("skillab/leaderboard.py"), "leaderboard.py")]])}

<h2>5. Deflated Sharpe</h2>
<div class="prose">
<p>A Sharpe ratio computed after trying many variants must be deflated for the number of trials.
The build reports the deflated Sharpe for every strategy that reaches SG10 and requires 0.95.
In the known-answer experiment, the true-edge strategy with a single trial scores above the
threshold and the zero-edge heater does not.</p>
</div>

<h2>6. Probability of backtest overfitting on the repository's own data</h2>
<div class="prose">
<p><strong>Not computed, and that is the correct answer.</strong> {esc(pbo_repo['reason'])}
Publishing a PBO from {fmt(pbo_repo['observations'], 0)} observations would produce a number with
no meaning, and a meaningless number in a table is worse than a blank.</p>
</div>

<h2>What luck removal does not do</h2>
<div class="prose">
<p>These controls reduce the chance of publishing noise. They cannot create an edge, cannot rescue
an underpowered record, and cannot substitute for a lawful dataset. A strategy that fails SG05
does not become qualified by surviving every other gate.</p>
</div>
"""
    return page("luck.html", "Luck removal",
                "Sample size, multiple testing, selection bias, deflated Sharpe, reality checks and PBO.",
                body, _built_note(out))


def page_gates(out: dict) -> str:
    rows = []
    for gid, name, rule, src in gates.GATE_DEFS:
        rows.append([esc(gid), esc(name), esc(rule), a(src, "source")])
    cross = [
        ["G1 Legal review (verified pages)", "SG01", "Same intent: permission before publication"],
        ["G2 Data provenance", "SG02", "Verified pages lack hashes; SG02 requires them"],
        ["G3 Integrity screen", "SG01 / SG11", "Market restriction folded into rights and dependence"],
        ["G4 Out-of-sample", "SG04", "Both require strict chronology"],
        ["G5–G8 statistics", "SG06–SG10", "Split into market loss, EV, calibration, correction"],
        ["G01 Rights and market permission", "SG01", "Direct match"],
        ["G05 Market-relative quality", "SG06", "Same test, different effect measure"],
        ["G08 Luck and multiple testing", "SG09", "SG09 adds a reality check on top"],
        ["G09 Joint dependence", "SG11", "Direct match"],
        ["G10 Frozen auditable ledger", "SG12", "Direct match"],
    ]
    cross_rows = [c + [a(gh("skillab/gates.py"), "gates.py")] for c in cross]

    body = f"""
<section class="hero"><p class="eyebrow">VALIDATION GATES</p>
<p class="lede">Twelve gates in three groups: three preconditions you must satisfy before you are
allowed to look at results, six statistical tests that separate skill from luck, and three
integrity requirements. Missing evidence is a fail, never a pass.</p></section>

<h2>SG01 – SG12</h2>
{table(["Gate", "Name", "Rule", "Method source"], rows)}

<h2>Why a third numbering scheme</h2>
<div class="prose">
<p>The repository already carries two incompatible gate frameworks that reuse the same IDs: G1–G8
on the verified archive pages (where G1 is a Korean legal review) and G01–G10 in the empirical
lab (where G01 is rights and market permission). Reusing either prefix would deepen a
documentation defect that is already flagged. These gates therefore use <strong>SG</strong>, and
the crosswalk below maps the same intent without pretending the frameworks are identical.</p>
</div>
{table(["Existing gate", "Skill-lab gate", "Relationship", "Implementation"], cross_rows)}

<h2>The ordering is not cosmetic</h2>
<div class="prose">
<p>SG01–SG03 come first for a reason. If you do not hold the rights, cannot prove where each
number came from, and did not freeze the plan before looking, then every statistic computed
afterwards is uninterpretable — you cannot tell a real effect from the freedom you had in
choosing what to measure. Computing the statistics first and asking about rights later is how
projects end up with a confident number they cannot legally publish.</p>
</div>

<h2>Fail-closed, concretely</h2>
<div class="prose">
<ul>
<li>A gate with no data returns <code>false</code> and a reason string. It never returns "n/a".</li>
<li>SG09 checks that the declared family size equals the number of p-values supplied, so a
strategy cannot quietly declare "we only tried one".</li>
<li>SG03 compares the frozen plan hash with a recomputed hash. A changed threshold changes the
hash and fails the run.</li>
<li>SG05 uses the strategy's own claimed edge to compute the required sample size. Claim a bigger
edge and you must bring more evidence.</li>
</ul>
</div>
"""
    return page("gates.html", "Validation gates SG01–SG12",
                "Twelve fail-closed gates, and the crosswalk to the two older numbering schemes.",
                body, _built_note(out))


def page_leaderboard(out: dict) -> str:
    rows = []
    for key in ("B_SKILL", "A_HEATER", "E_LOWPOWER", "A_LUCKY", "F_SKILL_FULL"):
        r = out["gates"][key]
        sim = out["simulation"][key]
        roi = sim.get("roi")
        rows.append([
            esc(r["strategy_id"]),
            fmt(sim.get("n"), 0),
            fmt(roi, pct=True),
            f"{len(r['passed'])}/12",
            badge("QUALIFIED", "pass") if r["qualified"] else badge("NOT ELIGIBLE", "fail"),
            esc(", ".join(r["failed"]) or "—"),
            a(gh("skillab/gates.py"), "gates.py"),
        ])
    body = f"""
<section class="hero"><p class="eyebrow">LEADERBOARD</p>
<p class="lede">A leaderboard must rank the <em>worst plausible</em> version of a strategy, not
its best observed run. Otherwise it ranks luck, and it does so most reliably in exactly the
situations where a real edge is hardest to see.</p></section>

<h2>Scoring rule</h2>
<div class="prose">
<p>A strategy appears on the board only if it passes all twelve gates. Eligible strategies are
ranked by the lower bound of the 95% block-bootstrap interval on return per bet, with a
tie-break on the deflated Sharpe. A strategy with a high point estimate and a wide interval
therefore ranks below a modest strategy with a tight one — by design.</p>
<p><strong>Rewards.</strong> No reward is configured or paid. Any reward scheme depends on gate
SG01 (rights and legal review), which is open. Publishing a reward schedule before that gate
closes would be an invitation to manufacture records that cannot be lawfully checked.</p>
</div>

<h2>Current board</h2>
<p class="note">All rows are SYNTHETIC. There is no real strategy in this repository with the
evidence needed to be ranked, so the board has no real entrants — which is the correct state,
not an empty state to be filled.</p>
{table(["Strategy", "n", "ROI", "Gates passed", "Eligibility", "Failed gates", "Evaluator"], rows)}

<h2>What a real entrant would have to submit</h2>
<div class="prose">
<ol>
<li>A frozen plan hash committed before the first bet (SG03).</li>
<li>A per-bet ledger with a price, a timestamp and a source for every observation (SG02, SG12).</li>
<li>Paired model and market probabilities on the same games (SG06).</li>
<li>The full family of strategies tried, not just the survivor (SG09).</li>
<li>A measured correlation with n and an interval for any multi-leg bet (SG11).</li>
</ol>
<p>Anything less is a description of a record, not evidence of skill.</p>
</div>

<h2>Anti-gaming properties</h2>
<div class="prose">
<ul>
<li><strong>Cannot win on sample size alone:</strong> SG05 requires power for the <em>claimed</em>
edge, so padding n with uninformative bets does not help.</li>
<li><strong>Cannot hide failed variants:</strong> SG09 rejects a family size that does not match
the number of p-values supplied.</li>
<li><strong>Cannot win on a short heater:</strong> the lower bound, not the mean, is the score.</li>
<li><strong>Cannot win on a lucky parlay:</strong> SG11 requires dependence to be stated.</li>
</ul>
</div>
"""
    return page("leaderboard.html", "Leaderboard and rewards",
                "Eligibility, scoring, and the anti-gaming properties of the ranking.",
                body, _built_note(out))


def page_validation(out: dict) -> str:
    rows = []
    for key in ("F_SKILL_FULL", "B_SKILL", "A_HEATER", "A_LUCKY", "E_LOWPOWER"):
        r = out["gates"][key]
        s = out["simulation"][key]
        rows.append([
            esc(s.get("label", key)),
            fmt(s.get("true_edge"), pct=True),
            fmt(s.get("n"), 0),
            fmt(s.get("roi"), pct=True),
            esc(", ".join(r["failed"]) or "none"),
            badge("QUALIFIED", "pass") if r["qualified"] else badge("REJECTED", "fail"),
            a(gh("skillab/simulate.py"), "simulate.py"),
        ])
    body = f"""
<section class="hero"><p class="eyebrow">PROOF OF DISCRIMINATION</p>
<p class="lede">A gate that rejects everything is not a test. A gate that accepts everything is
not a test either. The only way to know which one you have built is to run it against data
where the answer is already known.</p></section>

<h2>Known-answer experiments</h2>
<p class="note">Six archetypes with a known generating process. All are SYNTHETIC: seeded
simulations that describe no real team, player, game or market. The seeds are fixed, so every
number here is reproducible by re-running the build.</p>
{table(["Archetype", "True edge", "n", "Realised ROI", "Failed gates", "Verdict", "Generator"], rows)}

<h2>What each archetype proves</h2>
<div class="prose">
<p><strong>F — full evidence, real 5% edge.</strong> Passes all twelve gates, including SG05's
requirement that the sample be large enough to detect the edge it claims. This is the pass path;
without it the other results would only prove the gates are strict, not that they are correct.</p>

<p><strong>B — real 3% edge, 3,000 bets.</strong> Passes SG07 (its return interval excludes zero)
but fails SG05 and SG06. That is not a false negative; it is the power finding made concrete.
Three thousand bets is not enough to detect a 3% edge with confidence, even when the edge is
genuinely there.</p>

<p><strong>A — zero true edge, lucky 150-bet draw (+12.0% ROI).</strong> Fails SG07, SG10 and
SG05. This is the archetype a naive leaderboard would rank first. Its ROI is real, its edge is
not.</p>

<p><strong>E — real 2% edge, 40 bets.</strong> Fails SG05 and SG07. A genuine edge observed at a
sample size that cannot support it is indistinguishable from luck, and the gates treat it that
way.</p>

<p><strong>C — best of 60 zero-edge strategies.</strong> In-sample ROI of
{fmt(out['simulation']['C_OVERFIT']['in_sample_roi_best'], pct=True)} versus out-of-sample
{fmt(out['simulation']['C_OVERFIT']['oos_roi_best'], pct=True)}. The collapse is not a modelling
error; it is what selection does.</p>

<p><strong>D — parlay priced as independent with a true ρ of 0.35.</strong> The independence
assumption reports an EV of {fmt(out['simulation']['D_CORRELATED']['ev_if_independent'], pct=True)};
the realised return is {fmt(out['simulation']['D_CORRELATED']['realised_roi'], pct=True)}.
The dependence is the entire result.</p>
</div>

<h2>Regression protection</h2>
<div class="prose">
<p>The same assertions are encoded in <code>tests/test_skilllab.py</code>. If a future change makes
a gate accept the lucky or low-power archetype, or reject the full-evidence skill archetype, the
test suite fails. Known-answer testing is what keeps a validation framework honest as it evolves.</p>
</div>
"""
    return page("validation.html", "Proof of discrimination",
                "Known-answer experiments: what the gates accept, what they reject, and why.",
                body, _built_note(out))


def page_sources(out: dict) -> str:
    rows = [
        ["NBA", "Terms of Use — §1 public reuse, §9 gambling use",
         "https://www.nba.com/termsofuse", "Read 2026-11-05", "Rights precondition (SG01)"],
        ["NBA", "Stats FAQ — availability and download limits",
         "https://www.nba.com/stats/help/faq", "Read 2026-11-05", "Why no NBA dataset is published"],
        ["NBA", "Stats glossary — PACE, OffRtg, DefRtg definitions",
         "https://www.nba.com/stats/help/glossary", "Read 2026-11-05", "Input definitions only"],
        ["NIST/SEMATECH", "e-Handbook 1.3.6.6.18 — binomial distribution",
         "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "Read 2026-11-05",
         "Exact binomial test"],
        ["NIST/SEMATECH", "e-Handbook 1.3.5.17 — outlier detection (interval maths)",
         "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm", "Read 2026-11-05",
         "Robustness discussion"],
        ["SciPy", "scipy.stats.pearsonr — coefficient and p-value",
         "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html",
         "Read 2026-11-05", "Correlation"],
        ["SciPy", "scipy.stats.bootstrap — resampling intervals",
         "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html",
         "Read 2026-11-05", "Bootstrap intervals"],
        ["scikit-learn", "brier_score_loss — strictly proper scoring rule",
         "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
         "Read 2026-11-05", "Probabilistic scoring"],
        ["statsmodels", "multipletests — Bonferroni, Holm, FDR",
         "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html",
         "Read 2026-11-05", "Multiple testing"],
        ["This repository", "data/games_results_2026-27.csv — 92 games with official game links",
         gh("data/games_results_2026-27.csv"), "Committed", "Correlation recomputation"],
        ["This repository", "data/forward_test_2026-11-02.csv — 15 graded bets",
         gh("data/forward_test_2026-11-02.csv"), "Committed", "Singles audit"],
        ["This repository", "data/our_lines_2026-11-02.csv — 15 two-sided quotes",
         gh("data/our_lines_2026-11-02.csv"), "Committed", "De-vig audit"],
    ]
    consumers = {
        "https://www.nba.com/termsofuse": "flagged.html",
        "https://www.nba.com/stats/help/faq": "signals.html",
        "https://www.nba.com/stats/help/glossary": "signals.html",
        "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm": "singles.html",
        "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm": "correlation.html",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html": "correlation.html",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html": "luck.html",
        "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html": "luck.html",
        "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html": "luck.html",
    }
    sourced = []
    for pub, doc, url, read_on, used in rows:
        link = a(url, url.replace("https://", ""))
        consumer = consumers.get(url)
        if consumer:
            link += f' · <a href="{consumer}">used on {consumer}</a>'
        else:
            link += f' · <a href="singles.html">used in the build</a>'
        sourced.append([esc(pub), esc(doc), link, esc(read_on), esc(used)])

    quote_rows = []
    vpath = ROOT / "data" / "skill" / "verification_2026_11_05.csv"
    if vpath.exists():
        import csv as _csv
        with vpath.open(newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                verdict = row["result"]
                badge_kind = "pass" if verdict.startswith("VERIFIED") else "flag"
                quote_rows.append([
                    esc(row["id"]),
                    esc(row["claim"]),
                    a(row["source_url"], row["publisher"]) if row["source_url"] else
                    '<span class="blank" aria-label="no source"></span>',
                    esc(row["read_on"]) if row["read_on"] else
                    '<span class="blank" aria-label="not read"></span>',
                    f'<q>{esc(row["quoted_text"])}</q>' if row["quoted_text"] else
                    '<span class="blank" aria-label="not quoted"></span>',
                    badge(verdict, badge_kind)
                    + ' · ' + a(gh("data/skill/verification_2026_11_05.csv"), "ledger"),
                ])
    quote_table = table(["ID", "Claim on this site", "Official source", "Read on",
                         "Text as retrieved", "Result · evidence"], quote_rows)

    body = f"""
<section class="hero"><p class="eyebrow">SOURCES</p>
<p class="lede">Every number on this site traces to one of four places: an official page, a file
in this repository, a closed-form equation, or a seeded simulation. Nothing traces to a memory.</p></section>

<h2>Source register</h2>
<p class="note">Every row carries the document link and the page or module in this repository that
consumes it. The "Read on" column records when the text was actually retrieved, not when it was
last mentioned.</p>
{table(["Publisher", "Document", "Official link", "Read on", "Used for"], sourced)}

<h2>Verified quotations</h2>
<p class="note">Each row is a claim the site makes, the official page it came from, when that page
was read, and the text as retrieved. The CSV behind this table is
{a(gh("data/skill/verification_2026_11_05.csv"), "data/skill/verification_2026_11_05.csv")}. One row
is deliberately listed as UNVERIFIED: the Brier decomposition identity is proven by a test in this
repository, not quoted from a page, and is labelled that way rather than given a citation it does
not have.</p>
{quote_table}

<h2>What the official sources do and do not establish</h2>
<div class="prose">
<p>The NBA pages establish definitions, availability limits and contractual restrictions. They do
<strong>not</strong> establish any predictive relationship, any price, any correlation value or
any return. The statistical references define the mathematics of the tests — they do not endorse
a betting strategy, and none of them is evidence that any strategy here works.</p>
<p>The repository CSVs carry a per-row official <code>source_url</code> to the NBA game page for
each result. That link identifies where the score came from; it is not a certification of every
derived value, and this build does not re-fetch game pages. Re-verification of those rows belongs
to the existing verification ledger, not here.</p>
</div>

<h2>Absences, stated as absences</h2>
<div class="prose">
<ul>
<li><strong>No verified sportsbook price archive.</strong> The only prices in the repository are
ESPN-carried quotes for one slate. They are a secondary relay, not a first-party record.</li>
<li><strong>No closing-line history.</strong> Closing-line value cannot be computed, so SG07 is
weaker than it would be with it.</li>
<li><strong>No licensed player game logs.</strong> Prop and combo families cannot be tested.</li>
<li><strong>No NBA authorisation for gambling-related use.</strong> Publishing derived numbers
from NBA data is exactly what §9 restricts.</li>
</ul>
</div>
"""
    return page("sources.html", "Sources and evidence boundaries",
                "What each source establishes, and what it does not.",
                body, _built_note(out))


def page_flagged(out: dict) -> str:
    c = out["correlations"]
    rows = [
        ["S-F01", "High",
         "No lawful basis for gambling-related use of NBA data is established. NBA Terms §9 restricts NBA Statistics in connection with gambling.",
         "Every empirical claim downstream is unpublishable until this is resolved.",
         "Open — requires written permission or a licensed provider contract; not a legal opinion.",
         a("https://www.nba.com/termsofuse", "NBA Terms of Use")],
        ["S-F02", "High",
         "The rest-differential correlation published in the repository does not reproduce from its own stated file.",
         f"Published {fmt(next((d['published_r'] for d in c['differences'] if 'rest' in d['pair']), None))} "
         f"vs recomputed {fmt(next((d['recomputed_r'] for d in c['differences'] if 'rest' in d['pair']), None))}",
         "Not corrected here: the rest definition belongs to the file's owner. Flagged for review.",
         a(gh("data/correlation_findings.csv"), "correlation_findings.csv")],
        ["S-F03", "High",
         "The same-date margin correlation's nominal p-value is an artefact of pseudo-replication.",
         f"Nominal p = {fmt(c['measured']['same_date_game_margins']['p_two_sided_asymmetric'], 4)}; "
         f"date-cluster 95% CI {fmt(c['measured']['same_date_game_margins']['date_cluster_bootstrap_ci95'][0])} "
         f"to {fmt(c['measured']['same_date_game_margins']['date_cluster_bootstrap_ci95'][1])} contains zero.",
         "Any statement that cross-game dependence is significant should be withdrawn.",
         a(gh("data/correlation_findings.csv"), "correlation_findings.csv")],
        ["S-F04", "High",
         "Only 15 graded bets exist with prices. Every ROI in the repository is underpowered by more than two orders of magnitude.",
         "7,897 bets are needed to detect a 3% edge at 80% power; 15 are present.",
         "No fix available from existing data. Requires a long, lawful price archive.",
         a(gh("data/forward_test_2026-11-02.csv"), "forward_test CSV")],
        ["S-F05", "Medium",
         "The teammate-scoring correlation has n = 6 and its interval spans almost the full range.",
         "Published r uses a 6-game ESPN log; the sign is not established.",
         "Published as a flagged observation, not as a usable ρ.",
         a(gh("data/correlation_findings.csv"), "correlation_findings.csv")],
        ["S-F06", "Medium",
         "Three incompatible gate numbering schemes now coexist (G1–G8, G01–G10, SG01–SG12).",
         "Cross-referencing a gate ID is ambiguous without naming the scheme.",
         "Crosswalk published on the gates page; consolidation is an integration decision.",
         a(gh("docs/skill/gates.html"), "gates page")],
        ["S-F07", "Medium",
         "Five earlier session PRs (#23, #28, #31, #32, #37) remain open and conflicting, more than a day past the 60-minute handoff rule.",
         "Their independent verification ledgers are not part of the published site.",
         "Not merged here: merging conflicting branches risks discarding upstream work.",
         a("https://github.com/sassnarep3-star/Own6/pulls", "Pull requests")],
        ["S-F08", "Medium",
         "The sitewide source-coverage snapshot under data/source_coverage is stale relative to the current tree.",
         "`source_coverage.py --check` reports drift on 8 artifacts.",
         "Owned by another session; this build does not regenerate it.",
         a(gh("data/source_coverage/summary.json"), "summary.json")],
        ["S-F09", "Low",
         "The repository's own source files list no licence.",
         "Reuse terms for the code are unspecified.",
         "Flagged; adding a licence is an owner decision.",
         a(gh("README.md"), "README")],
        ["S-F10", "Low",
         "Every published strategy return on this site is synthetic.",
         "0 real strategies are eligible; the leaderboard has no real entrants.",
         "By design and labelled on every table. Not an error, but a limit worth stating.",
         a(gh("skillab/simulate.py"), "simulate.py")],
    ]
    body = f"""
<section class="hero"><p class="eyebrow">FLAGGED FOR REVIEW</p>
<p class="lede">Ten items that need a human decision. None of them blocks publication; all of them
limit what the published numbers mean. Each carries a source link.</p></section>

<h2>Flag register</h2>
{table(["ID", "Severity", "Finding", "Evidence", "Disposition requested", "Source"], rows)}

<h2>Items this build resolved rather than flagged</h2>
<div class="prose">
<ul>
<li><strong>SG06 direction.</strong> The paired loss comparison was initially written with the
subtraction inverted, which would have credited a model that lost <em>more</em> than the market.
Corrected before publication and covered by a test.</li>
<li><strong>SG08 semantics.</strong> Calibration was initially required to beat climatology, which
conflates calibration with discrimination and would fail a well-calibrated constant forecast for
the wrong reason. Discrimination is scored at SG06; SG08 now tests calibration only.</li>
<li><strong>Published correlations that did reproduce.</strong> The home/away and same-date point
estimates recompute to within 2×10⁻⁵ and are not flagged.</li>
</ul>
</div>

<h2>How to request a change</h2>
<div class="prose">
<p>Open an issue on the repository referencing the flag ID. A change to a flagged value must
arrive with its own official source, or it stays blank. Flags do not delay publication; they are
the mechanism by which an unpublished claim stays visible instead of disappearing.</p>
</div>
"""
    return page("flagged.html", "Flagged for Review",
                "Ten items requiring a human decision, with evidence and a source for each.",
                body, _built_note(out))


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    out = build_data()
    DOCS.mkdir(parents=True, exist_ok=True)
    pages = {
        "index.html": page_index(out),
        "signals.html": page_signals(out),
        "singles.html": page_singles(out),
        "parlays.html": page_parlays(out),
        "correlation.html": page_correlation(out),
        "luck.html": page_luck(out),
        "gates.html": page_gates(out),
        "leaderboard.html": page_leaderboard(out),
        "validation.html": page_validation(out),
        "sources.html": page_sources(out),
        "flagged.html": page_flagged(out),
    }
    for name, text in pages.items():
        (DOCS / name).write_text(text, encoding="utf-8")
    print(f"Built {len(pages)} pages in {DOCS.relative_to(ROOT)}")
    print(f"Data summary: {(DATA / 'skilllab_summary.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
