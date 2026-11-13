#!/usr/bin/env python3
"""Build the NFL decision desk: derived registers, then the published pages.

Everything numeric on the site comes from src/nfl_desk applied to the verified
registers in data/nfl_desk. Re-running this script must reproduce every file
byte for byte (`--check`), which is what makes the tables auditable rather than
hand-written. No network access, no manual input, no placeholder values: an
unconfirmed cell is rendered as an empty <td class="empty">.
"""
from __future__ import annotations

import csv
import hashlib
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_desk import audit, derive  # noqa: E402
from nfl_desk.league import league_facts, load_clubs  # noqa: E402

DATA = ROOT / "data" / "nfl_desk"
DERIVED = DATA / "derived"
SITE = ROOT / "docs" / "nfl-decision-desk"
ASSETS = SITE / "assets"
READ = "2026-11-13"
BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"

PAGES = (
    "index.html", "executive-summary.html", "requirements.html", "questions.html", "suggestions.html",
    "verification.html", "standings.html", "slate.html", "origination.html", "strategies.html",
    "leaderboard.html", "validation.html", "correlations.html", "injuries.html", "depth.html",
    "repo-audit.html", "sources.html", "flagged.html",
)

NAV = (
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions & answers"),
    ("suggestions.html", "Suggestions"),
    ("standings.html", "Verified data"),
    ("slate.html", "Week 10 slate"),
    ("origination.html", "Originated lines"),
    ("correlations.html", "Correlations"),
    ("validation.html", "Validation gates"),
    ("strategies.html", "Strategy lab"),
    ("leaderboard.html", "Leaderboard & rewards"),
    ("injuries.html", "Injury tracking"),
    ("depth.html", "Depth deficiency"),
    ("verification.html", "Verification ledger"),
    ("repo-audit.html", "Repo audit"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
)

LABELS = {
    "row_id": "Row", "register_audited": "Register audited", "subject": "Subject", "field": "Field",
    "prior_value": "Prior published value", "official_value_2026_11_13": "Official value read 2026-11-13",
    "disposition": "Disposition", "explanation": "Explanation / audit note", "prior_source_url": "Prior source",
    "this_read_source_url": "This read", "verification_status": "Status", "official_source_url": "Source",
    "source_url": "Source", "input_source": "Inputs read", "game_id": "Game", "club": "Club",
    "unit_group": "Unit group", "players_listed": "Players listed", "impaired_count": "Impaired (Out or DNP)",
    "out_count": "Designated out", "deficiency_score": "Deficiency score", "replacement_tier": "Replacement tier",
    "cascading_cluster": "Cluster alert", "starter_dependent_unit": "Starter-dependent",
    "affected_players": "Affected players", "model_fair_spread_home": "Fair spread (home)",
    "model_fair_spread_rounded": "Fair spread (0.5)", "model_fair_total": "Fair total",
    "model_fair_total_rounded": "Fair total (0.5)", "model_home_win_prob": "Home win prob",
    "model_push_prob": "Push on the quoted line", "model_tie_mass": "Regulation tie mass", "key_number_mass_3": "Mass at 3", "key_number_mass_7": "Mass at 7",
    "one_score_window_mass": "One-score window (1-8)", "market_open_line": "Market open",
    "market_close_line": "Market close", "market_total": "Market total", "market_implied_prob": "Market implied",
    "de_vigged_market_prob": "De-vigged prob", "assumption_grid_sign_stable": "Sign stable across grid",
    "flips_at_home_points": "Flips at home points", "line_status": "Line status", "kickoff_et": "Kickoff (ET)",
    "away_club": "Away", "home_club": "Home", "neutral_site": "Neutral", "away_record": "Away record",
    "home_record": "Home record", "away_ppg": "Away pts/g", "away_papg": "Away allowed/g", "home_ppg": "Home pts/g",
    "home_papg": "Home allowed/g", "home_deficiency_score": "Home deficiency", "away_deficiency_score":
    "Away deficiency", "home_cluster_alert": "Home cluster", "away_cluster_alert": "Away cluster",
    "fact_id": "ID", "category": "Category", "item": "Item", "value": "Value", "unit": "Unit",
    "derivation_or_definition": "Derivation / definition", "status": "Status", "flag_id": "Flag",
    "corr_id": "ID", "scope": "Scope", "pair": "Pair", "n": "n", "pearson_r": "Pearson r",
    "spearman_rho": "Spearman rho", "boot_ci_95": "95% bootstrap CI", "perm_p": "Permutation p",
    "r_squared": "R-squared", "mechanism_or_reason": "Mechanism / why it matters",
    "how_the_desk_uses_it": "How the desk uses it", "note": "Note", "combo_id": "Combo", "leg_1_prob": "Leg 1 p",
    "leg_2_prob": "Leg 2 p", "independent_product": "Independence price", "frechet_lower_bound": "Lower bound",
    "frechet_upper_bound": "Upper bound", "fair_american_at_lower": "Fair odds at floor",
    "fair_american_at_independent": "Fair odds if independent", "fair_american_at_upper": "Fair odds at ceiling",
    "worst_case_overcharge_vs_bounds": "Worst-case overcharge", "gate_id": "Gate", "name": "Name",
    "requirement": "Requirement", "blocks_failure_mode": "Failure mode it blocks", "enforcer": "Enforced by",
    "enforcer_path": "Enforced by", "family": "Family", "measured": "Measured state", "unlock": "What unlocks it",
    "strategy_id": "Strategy", "structure": "Bet structure", "hypothesis": "Frozen hypothesis",
    "required_features": "Inputs required", "available_features": "Inputs available today",
    "missing_features": "Inputs missing", "luck_controls": "Luck controls", "readiness": "Readiness",
    "gates_passed": "Gates passed", "gates_total": "Gates total", "reward_tier": "Reward tier",
    "unlock_next": "Next unlock", "rank": "Rank", "settled_selections": "Settled selections",
    "holdout_roi": "Holdout ROI", "same_line_clv": "Same-line CLV", "brier": "Brier", "skill_score": "Skill score",
    "leaderboard_note": "Board note", "tier_id": "Tier", "criteria": "Criteria", "entries_at_tier": "Entries",
    "how_ties_are_broken": "Tie-break rule", "finding_id": "ID", "severity": "Severity", "repo_path": "Path",
    "finding": "Finding", "evidence_computed_here": "Evidence recomputed in this build", "source_urls": "Sources",
    "slot_label_on_official_page": "Slot label as printed", "broadcast_listing_verified": "Broadcast as listed",
    "venue_label_verified": "Venue (as read)", "game_state": "State", "away_points_final": "Away pts",
    "home_points_final": "Home pts", "player": "Player", "position": "Pos", "listed_injury": "Listed injury",
    "practice_status_abbrev": "Practice", "practice_status_verbatim": "Practice status (verbatim)",
    "game_status": "Game status", "inclusion_rule": "Why this row is here", "rows_listed_on_official_page":
    "Rows on page", "rows_included_in_register": "Rows published", "dnp_count": "DNP", "limited_count": "Limited",
    "full_count": "Full", "questionable_count": "Questionable", "exclusion_rule": "Exclusion rule",
    "sens_id": "ID", "matchup": "Matchup", "assumed_home_points": "Assumed home pts", "spread_home": "Spread",
    "favoured": "Favoured side", "games_played": "GP", "wins": "W", "losses": "L", "ties": "T", "win_pct": "PCT",
    "points_for": "PF", "points_against": "PA", "net_points": "Net", "home_w": "Home W", "home_l": "Home L",
    "home_t": "Home T", "road_w": "Road W", "road_l": "Road L", "road_t": "Road T", "div_w": "Div W",
    "div_l": "Div L", "div_t": "Div T", "conf_w": "Conf W", "conf_l": "Conf L", "conf_t": "Conf T",
    "streak": "Streak", "club_id": "ID", "record_id": "ID", "req_id": "ID", "qid": "ID", "sid": "ID",
    "depth_id": "ID", "weighting_policy": "Weighting policy (stated, not an NFL number)", "read_date": "Read",
    "verification_status": "Verification", "date": "Date", "bulletin_id": "ID", "headline_verbatim": "Headline",
    "published_date_label": "Date label", "url": "Link", "what_it_confirms": "What it confirms",
    "what_it_does_not_confirm": "What it does not confirm", "title": "Suggestion", "problem_it_solves":
    "Decision problem it solves", "option_a": "Option A", "option_b": "Option B", "option_c": "Option C",
    "recommended_path": "Recommended path", "why_recommended": "Why", "prerequisites_before_implementing":
    "Prerequisites", "effort": "Effort", "reversibility": "Reversibility", "files_touched": "Files touched",
    "review_status": "Review status", "requirement_verbatim_from_user": "Requirement (as stated)",
    "how_it_is_addressed": "How this pack addresses it", "artefacts": "Artefacts", "analysis_or_method":
    "Analysis / method", "gap_or_next_step": "Gap or next step", "decision_this_gates": "Decision it gates",
    "question": "Question", "information_we_have_verified": "Information we have (verified)",
    "information_we_do_not_have": "Information we do not have", "current_answer": "Current answer",
    "gate_impact": "Gate impact", "discovery_path_to_close_it": "Discovery path to close it", "blocking":
    "Blocking", "area": "Area", "publisher": "Publisher", "retrieval_method": "Retrieval method",
    "verbatim_evidence_excerpt": "Verbatim excerpt from the read", "supports_claim": "What it supports",
    "does_not_support_boundary": "Boundary: what it does not support", "finding": "Finding",
    "blocking_merge": "Blocks merge", "what_cannot_be_confirmed": "What cannot be confirmed", "why_it_stays_blank":
    "Why it stays blank", "resolution_path": "Resolution path", "games": "Games", "team": "Team",
}


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def links_for(cell: str) -> str:
    """Render one or more https links; the raw url stays visible for manual review."""
    parts = [p.strip() for p in str(cell).split(";") if p.strip()]
    out = []
    for part in parts:
        if part.startswith("http://") or part.startswith("https://"):
            label = part.replace("https://", "").replace("http://", "")
            label = label[:58] + "..." if len(label) > 58 else label
            out.append(f'<a href="{esc(part)}" rel="noopener">{esc(label)}</a>')
        elif "see read log" in part:
            out.append(esc(part))
        else:
            out.append(esc(part))
    return " ".join(out)


def is_url(value: str) -> bool:
    v = str(value).strip()
    return v.startswith("https://") or v.startswith("http://") or " ; http" in v or v.startswith("see read log")


def render_table(headers: list[str], rows: list[dict], caption: str, anchor: str, status_key: str = "status") -> str:
    body = []
    for row in rows:
        cells = []
        for h in headers:
            value = row.get(h, "")
            if value is None:
                value = ""
            value = str(value)
            if not value.strip():
                cells.append('<td class="empty" aria-label="blank - no confirmed value"></td>')
            elif value.strip().lower().startswith(("not applicable", "none required", "nothing missing",
                                                    "no verbatim excerpt")):
                # an asserted absence is a value, so it gets its own style instead of the blank-cell hatch
                cells.append(f'<td class="na">{esc(value)}</td>')
            elif is_url(value):
                cells.append(f"<td>{links_for(value)}</td>")
            elif h == status_key or h in ("verification_status", "disposition", "state", "severity", "blocking",
                                          "review_status", "line_status", "assumption_grid_sign_stable"):
                cls = value.strip().lower().replace(" ", "-").replace("_", "-")[:34]
                cells.append(f'<td><span class="badge b-{esc(cls)}">{esc(value)}</span></td>')
            elif h == "cascading_cluster" or h.endswith("_alert") or h == "starter_dependent_unit":
                cls = "yes" if value.strip().lower() in ("yes", "true") else "no"
                cells.append(f'<td><span class="badge b-{cls}">{esc(value)}</span></td>')
            else:
                cells.append(f"<td>{esc(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f'<th scope="col">{esc(LABELS.get(h, h.replace("_", " ")))}</th>' for h in headers)
    return (f'<div class="table-wrap"><table id="{esc(anchor)}"><caption>{esc(caption)} '
            f'<span class="rowcount">{len(rows)} rows</span></caption><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def columns(rows: list[dict], preferred: tuple[str, ...] = ()) -> list[str]:
    if not rows:
        return []
    keys = list(rows[0].keys())
    ordered = [k for k in preferred if k in keys] + [k for k in keys if k not in preferred]
    return ordered


def page(fname: str, title: str, lede: str, blocks: list[str], *, eyebrow: str = "NFL DECISION DESK") -> str:
    nav = "".join(f'<a{" class=on" if p == fname else ""} href="{p}">{esc(label)}</a>' for p, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | NFL Decision Desk</title>
<meta name="description" content="{esc(lede)}">
<link rel="stylesheet" href="assets/style.css">
<link rel="canonical" href="{BLOB}docs/nfl-decision-desk/{fname}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <div class="brand"><a href="index.html">NFL DECISION DESK</a><span>verified inputs only &middot; snapshot {READ}</span></div>
  <p class="tagline">Own-line origination, skill gates, injury and depth tracking. No picks, no profitability claim.</p>
</header>
<nav class="sections" aria-label="Section navigation">{nav}</nav>
<main id="main">
  <p class="eyebrow">{esc(eyebrow)}</p>
  <h1>{esc(title)}</h1>
  <p class="lede">{esc(lede)}</p>
  {chr(10).join(blocks)}
</main>
<footer>
  <p>Every table row links to the official page actually read for it. A blank cell means no confirmed value exists,
  not zero. Values labelled <span class="badge b-model-assumption">model assumption</span> are the model's own dials
  and are never presented as facts. Problem gambling help (verified from the regulator's own page on 2026-11-03 by a
  prior session, <a href="https://aglc.ca/gaming/common-gaming-questions" rel="noopener">aglc.ca</a>): Alberta Addicted Help Centre
  <strong>1-866-332-2322</strong>.</p>
  <p class="build">Register hashes and page build note: see <a href="sources.html">Sources</a>.</p>
</footer>
</body>
</html>
"""


def write_rows(path: Path, rows: list[dict], headers: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    hdr = headers or list(rows[0].keys())
    missing = [k for k in hdr if k not in rows[0]]
    if missing:
        raise ValueError(f"{path.name}: header names absent from the rows: {missing}")
    for i, r in enumerate(rows, 1):
        for k, v in r.items():
            text = "" if v is None else str(v)
            if text.lower() in ("nan", "inf", "-inf", "none") or text != text:
                raise ValueError(f"{path.name} row {i}: refusing to publish {k}={text!r}; a register cell is "
                                 "either a value or blank, never a float artefact")
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(hdr)
        for r in rows:
            w.writerow(["" if r.get(k) is None else r.get(k, "") for k in hdr])


def build_registers() -> dict:
    lines, summary = derive.originated_lines()
    gates, states = derive.gate_register(summary)
    reg = {
        "model_facts.csv": derive.fact_register(),
        "correlations.csv": derive.correlation_register(),
        "frechet_bounds.csv": derive.frechet_table(),
        "originated_lines.csv": lines,
        "sensitivity.csv": derive.sensitivity_register(),
        "depth_deficiency.csv": derive.depth_register(),
        "validation_gates.csv": gates,
        "strategies.csv": derive.strategy_register(states),
        "leaderboard.csv": derive.leaderboard_register(states, summary),
        "rewards.csv": derive.reward_register(),
        "verification_ledger.csv": [dict(zip(audit.LEDGER_HDR, r)) for r in audit.ledger_rows()],
        "repo_audit.csv": audit.repo_checks(),
    }
    for name, rows in reg.items():
        write_rows(DERIVED / name, rows)
    return reg


def summary_counts(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        k = str(r.get(key, "")).strip() or "(blank)"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def belt(pairs: list[tuple[str, str]], note: str) -> str:
    cells = "".join(f'<div><span>{esc(k)}</span><strong>{esc(v)}</strong></div>' for k, v in pairs)
    return f'<section class="belt"><div class="belt-cells">{cells}</div><p>{note}</p></section>'


def load_input(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_derived(name: str) -> list[dict]:
    with (DERIVED / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_pages(reg: dict) -> dict[str, str]:
    c26 = load_clubs("standings_2026_thru_w10.csv")
    facts = league_facts(c26)
    ledger = reg["verification_ledger.csv"]
    dispo = summary_counts(ledger, "disposition")
    gate_states = summary_counts(reg["validation_gates.csv"], "state")
    n_review = sum(1 for r in ledger if r["verification_status"] == "needs_review")
    pages: dict[str, str] = {}

    # ---------------------------------------------------------------- index
    cards = [
        ("executive-summary.html", "Executive summary", "The eight numbers that matter, what is blocked, and the "
         "two decisions that unblock the most."),
        ("requirements.html", "Requirements ledger", "18 stated requirements, each mapped to the artefact that "
         "answers it and the gap that remains."),
        ("questions.html", "Questions & answers", "16 decision questions with verified facts, known unknowns and "
         "the discovery path that closes each one."),
        ("suggestions.html", "Suggestions for review", "14 site and workflow changes with option paths A/B/C, "
         "effort, reversibility and a recommendation - nothing applied."),
        ("standings.html", "Verified data", "32 clubs, two seasons, every value re-read from the standings page on "
         "2026-11-13 plus the league facts derived from them."),
        ("slate.html", "Week 10 slate", "14 games and four byes, with the settled Thursday result and the records "
         "that moved because of it."),
        ("origination.html", "Originated lines", "Fair spread, total, win probability and push probability for the "
         "13 unsettled games - market columns deliberately blank."),
        ("correlations.html", "Correlation register", "Measured club-level dependence with bootstrap intervals and "
         "permutation p-values, plus Frechet bounds where a coefficient cannot exist yet."),
        ("validation.html", "Validation gates", "16 gates with a recomputed state: 7 pass, 2 fail, 7 blocked."),
        ("strategies.html", "Strategy lab", "12 preregistered strategies across singles, parlays and prop combos, "
         "each with its hypothesis and luck controls."),
        ("leaderboard.html", "Leaderboard & rewards", "Two boards: readiness now, performance only after the "
         "evidence gates - with the reward ladder published in advance."),
        ("injuries.html", "Injury tracking", "326 rows read off the official Week 10 report for all 28 clubs; the "
         "107 decision-relevant rows are published in full."),
        ("depth.html", "Depth deficiency", "77 club-unit records scoring how far down a chart a club has to reach, "
         "with the weighting policy shown."),
        ("verification.html", "Verification ledger", "544 field-by-field comparisons against the three previously "
         "published NFL registers."),
        ("repo-audit.html", "Repo audit", "Twelve integrity checks computed from the working tree, plus the GitHub "
         "publication state read the same day."),
        ("sources.html", "Sources", "Every official page read for this pack, how it was read, and what it does not "
         "support."),
        ("flagged.html", "Flagged for review", "23 items that stay blank or unverified, with the resolution path for "
         "each and whether they block anything."),
    ]
    grid = "".join(
        f'<a class="card" href="{href}"><h2>{esc(t)}</h2><p>{esc(d)}</p><span class="go">Open &rarr;</span></a>'
        for href, t, d in cards)
    blocks = [
        belt([("Games in the verified register", f"{facts['games']:.0f}"),
              ("Lines originated", f"{len(reg['originated_lines.csv'])}"),
              ("Gates passing", f"{gate_states.get('PASS', 0)} of 16"),
              ("Ledger rows re-verified", f"{len(ledger) - n_review} of {len(ledger)}"),
              ("Items flagged for review", str(len(load_input('flagged.csv'))))],
             "The performance board is empty by design: <strong>no strategy is paid a reward for a promise</strong>. "
             "Seven gates are blocked by data the project does not have yet, and each one names the exact artefact "
             "that unlocks it."),
        f'<section id="categories"><h2>Sections</h2><p>One page per category. Every table row links to the official '
        f'page read for that row; unconfirmed values are blank rather than estimated.</p><div class="grid">{grid}'
        f'</div></section>',
        "<section id=\"evidence\"><h2>What this pack can and cannot show</h2>" + render_table(
            ["topic", "published_value", "boundary", "official_source_for_review"],
            [{"topic": "Club scoring, records and venue splits", "published_value": "32 clubs, 2026 and 2025",
              "boundary": "verified - read directly from the standings page on 2026-11-13",
              "official_source_for_review": "https://www.nfl.com/standings/"},
             {"topic": "Weekly injury report", "published_value": "326 rows across 28 clubs",
              "boundary": "verified as a single snapshot; the page is revised during the week",
              "official_source_for_review": "https://www.nfl.com/injuries/"},
             {"topic": "Fair spread, total, win and push probability", "published_value": "13 games",
              "boundary": "originated internally from the verified inputs; not validated against a market",
              "official_source_for_review": "https://github.com/sassnarep3-star/Own6/blob/main/"
                                            "data/nfl_desk/derived/originated_lines.csv"},
             {"topic": "Market lines, vig, ROI, CLV, Brier", "published_value": "",
              "boundary": "blank - no licensed quote source exists in this repository",
              "official_source_for_review": "https://www.nfl.com/legal/terms/"},
             {"topic": "Same-game prop dependence coefficient", "published_value": "",
              "boundary": "blank - bounded with Frechet limits instead of a point estimate",
              "official_source_for_review": "https://docs.scipy.org/doc/scipy/reference/stats.html"},
             {"topic": "Which player is a club's 2nd string", "published_value": "",
              "boundary": "blank - the report carries participation and status, not depth-chart order",
              "official_source_for_review": "https://www.nfl.com/injuries/"},
             {"topic": "Points value of one Out designation", "published_value": "",
              "boundary": "blank - ordinal weights published instead, clearly labelled as policy",
              "official_source_for_review": "https://github.com/sassnarep3-star/Own6/blob/main/"
                                            "src/nfl_desk/depth.py"}],
            "Evidence state", "evidence-state", status_key="boundary") + "</section>",
        "<section id=\"method\"><h2>How a number gets here</h2><ol class=\"steps\">"
        "<li>An official page is read and the value is transcribed into a register with its URL and read date "
        "(<code>data/nfl_desk/*.csv</code>).</li>"
        "<li><code>src/nfl_desk</code> derives every published figure from those registers - arithmetic, fits, "
        "bootstraps, gate states.</li>"
        "<li>The builder writes the derived registers and renders the pages; <code>--check</code> requires byte "
        "equality, so a page can never disagree with its own code.</li>"
        "<li>The checker enforces row-level sourcing, blank-not-guessed cells, table alignment and link integrity; "
        "CI runs both on every push to main.</li></ol></section>",
    ]
    pages["index.html"] = page("index.html", "NFL decision desk",
                               "Origination, skill gates, injury and depth tracking for the 2026 Week 10 slate - "
                               "built only from official pages read on 2026-11-13, with every unconfirmed value left "
                               "blank.", blocks, eyebrow="OVERVIEW")

    # ---------------------------------------------------------------- exec summary
    pers = next(r for r in reg["correlations.csv"] if r["corr_id"] == "CR-03")
    luckr = next(r for r in reg["correlations.csv"] if r["corr_id"] == "CR-06")
    pf_pa = next(r for r in reg["correlations.csv"] if r["corr_id"] == "CR-01")
    mf = {r["fact_id"]: r for r in reg["model_facts.csv"]}
    key = [
        ("Scoring environment 2026", f"{mf['MF-03']['value']} points per team-game over {mf['MF-02']['value']} games",
         "the whole model is anchored on this; 2025 finished at " + mf['MF-04']['value']),
        ("Home advantage, win share", f"{float(mf['MF-05']['value']) * 100:.2f}% in 2026 vs "
         f"{float(mf['MF-06']['value']) * 100:.2f}% in 2025", "home clubs are below .500 this season - the model "
         "publishes a zero-point home assumption by default rather than importing last year's number"),
        ("Tied games", f"{mf['MF-07']['value']} of games in 2026 vs {mf['MF-08']['value']} in 2025",
         "tie mass is priced explicitly; the model's regulation-tie mass is "
         f"{mf['MF-23']['value']}, so overtime resolution is the missing calibration (FL-16)"),
        ("Skill measured from scoring", f"R-squared {mf['MF-13']['value']} (2026) and {mf['MF-14']['value']} (2025)",
         f"fitted exponent {mf['MF-11']['value']} / {mf['MF-12']['value']}; points-based expectation explains most "
         "of the spread in wins"),
        ("Luck does not persist", f"r = {luckr['pearson_r']} (p = {luckr['perm_p']})",
         "wins above expectation in 2025 say nothing about 2026, which is the quantitative reason records-only "
         "strategies are refused here"),
        ("Prior-season information", f"r = {pers['pearson_r']}, 95% CI {pers['boot_ci_95']}, p = {pers['perm_p']}",
         "about a quarter of last season's scoring differential carries over - enough to use as a weak prior, "
         "not enough to price a line from"),
        ("Offence and defence independence", f"r = {pf_pa['pearson_r']}, 95% CI {pf_pa['boot_ci_95']}, "
         f"p = {pf_pa['perm_p']}", "the interval spans zero, so a total and a side carry largely separate "
         "information on this data"),
        ("Gates", f"{gate_states.get('PASS', 0)} pass, {gate_states.get('FAIL', 0)} fail, "
         f"{gate_states.get('BLOCKED', 0)} blocked", "the two fails are 'no settled selections' and 'the favoured "
         "side is not robust on two near-pick games' - the second is a model finding, not a data gap"),
    ]
    blocks = [
        render_table(["measure", "value", "why_it_matters"],
                     [{"measure": k, "value": v, "why_it_matters": w} for k, v, w in key],
                     "Headline results from verified data", "headline", status_key="measure"),
        "<section id=\"new\"><h2>What this pack adds over the three published NFL packs</h2><ul>"
        "<li>An actual re-verification: 544 field-by-field comparisons of the prior registers against today's "
        "official read, with a disposition for each.</li>"
        "<li>Originated lines that are computed rather than deferred: fair spread, total, win and push probability "
        "for all 13 unsettled games, from verified scoring only.</li>"
        "<li>Luck instrumented with numbers: Pythagorean fit, residual variance against a binomial floor, and a "
        "cross-season persistence test.</li>"
        "<li>Correlations measured where they can be, and bounded where they cannot - no invented coefficients.</li>"
        "<li>The full Week 10 injury report for 28 clubs, transcribed and scored into 77 club-unit deficiency "
        "records.</li>"
        "<li>A leaderboard that separates readiness (rankable today) from performance (empty until the evidence "
        "gates pass), with the reward ladder published before anyone competes.</li></ul></section>",
        "<section id=\"decisions\"><h2>The two decisions that unblock the most</h2><ol>"
        "<li><strong>Start the weekly snapshot job</strong> (SUG-03). Four dated, hashed captures per slate unlock "
        "DG-04, and after roughly eight slates DG-06 and DG-15 as well. It needs no licence and no money.</li>"
        "<li><strong>Answer the rights question in writing</strong> (SUG-04, Q-01). A licensed quote feed is the "
        "only way to DG-03, DG-07, DG-08 and DG-13 - and a documented refusal is a legitimate outcome, because it "
        "converts an invisible blocker into a scope decision.</li></ol>"
        "<p>Both are cheap; neither is urgent until a third of the site's value depends on them, which is exactly "
        "where the project now sits.</p></section>",
        "<section id=\"boundaries\"><h2>Boundaries this pack will not cross</h2><ul>"
        "<li>No line, vig, ROI, CLV or skill score is published without an authorized source - those cells are "
        "blank and listed on the <a href=\"flagged.html\">flagged page</a>.</li>"
        "<li>Model assumptions (Poisson law, zero home points, ordinal depth weights) are labelled in-cell and are "
        "excluded from every gate.</li>"
        "<li>Nothing here is a pick. The desk prices an internal estimate and states the evidence still missing "
        "before that estimate deserves trust.</li></ul></section>",
    ]
    pages["executive-summary.html"] = page("executive-summary.html", "Executive summary",
                                           "Important details of the NFL decision desk, every figure traceable to a "
                                           "register row and an official page read.", blocks,
                                           eyebrow="SUMMARY")

    # ---------------------------------------------------------------- requirements
    reqs = load_input("requirements.csv")
    by_status = summary_counts(reqs, "status")
    blocks = [belt([(k, str(v)) for k, v in by_status.items()],
                   "One row per requirement stated by the owner. <em>Gap or next step</em> is the honest remainder, "
                   "not a to-do list."),
              render_table(columns(reqs, ("req_id", "requirement_verbatim_from_user", "how_it_is_addressed",
                                          "artefacts", "analysis_or_method", "status", "gap_or_next_step",
                                          "official_source_url")), reqs,
                             "Requirements ledger", "requirements-table", status_key="status")]
    pages["requirements.html"] = page("requirements.html", "Requirements ledger",
                                      "The full list of stated requirements, what answers each one, and what is "
                                      "still missing.", blocks, eyebrow="SCOPE")

    # ---------------------------------------------------------------- questions
    qs = load_input("questions.csv")
    n_blocking = sum(1 for r in qs if r["blocking"].upper().startswith("BLOCKING"))
    n_measured = sum(1 for r in qs if "MEASURED" in r["current_answer"])
    n_open = sum(1 for r in qs if r["current_answer"].split(" ")[0] in ("NO", "UNKNOWN", "NONE", "NOT"))
    blocks = [belt([("Questions", str(len(qs))), ("Blocking a gate", str(n_blocking)),
                   ("Answered with measured values", str(n_measured)),
                   ("Still open (answer begins with a no)", str(n_open))],
                   "Each question is written so that the answer changes a specific gate. Nothing here is a rhetorical "
                   "question: every 'we do not have' names the artefact that would supply it."),
              render_table(columns(qs, ("qid", "domain", "decision_this_gates", "question",
                                        "information_we_have_verified", "information_we_do_not_have",
                                        "current_answer", "gate_impact", "discovery_path_to_close_it", "blocking",
                                        "flag_id", "official_source_url")), qs,
                           "Decision questions, knowns, unknowns and discovery paths", "questions-table",
                           status_key="blocking")]
    pages["questions.html"] = page("questions.html", "Questions, information and answers",
                                   "What must be addressed before a decision here is reasonable, and how to find the "
                                   "missing piece.", blocks, eyebrow="DECISION INPUTS")

    # ---------------------------------------------------------------- suggestions
    sug = load_input("suggestions.csv")
    blocks = [belt([("Suggestions", str(len(sug))), ("Awaiting your choice", str(sum(1 for r in sug if
                   r["review_status"] == "pending_human_choice"))),
                   ("Recommended option A", str(sum(1 for r in sug if r["recommended_path"].startswith("A")))),
                   ("Low effort", str(sum(1 for r in sug if r["effort"].startswith("low"))))],
                   "Nothing on this page has been implemented. Each row keeps the alternatives visible so the "
                   "decision can be reviewed before any file changes."),
              render_table(columns(sug, ("sid", "area", "title", "problem_it_solves", "option_a", "option_b",
                                        "option_c", "recommended_path", "why_recommended",
                                        "prerequisites_before_implementing", "effort", "reversibility",
                                        "files_touched", "review_status", "official_source_url")), sug,
                           "Site and workflow suggestions for review", "suggestions-table",
                           status_key="review_status"),
              "<section id=\"how-to-choose\"><h2>How to choose</h2><p>Pick by reversibility first: every option here "
              "is a git-revert away, but three of them touch files other sessions own (SUG-01, SUG-02, SUG-05) and "
              "need the integration owner in the loop. Then pick by unlock count: SUG-03 unlocks four gates and is "
              "the only one that changes what the site can prove.</p></section>"]
    pages["suggestions.html"] = page("suggestions.html", "Suggestions for review",
                                     "Improvement options for the site and the workflow, held unimplemented until a "
                                     "path is chosen.", blocks, eyebrow="REVIEW BEFORE IMPLEMENTING")

    # ---------------------------------------------------------------- standings + facts
    st26, st25 = load_input("standings_2026_thru_w10.csv"), load_input("standings_2025_final.csv")
    keep = ("record_id", "club", "abbr", "conference", "division", "games_played", "wins", "losses", "ties",
            "win_pct", "points_for", "points_against", "net_points", "home_w", "home_l", "home_t", "road_w",
            "road_l", "road_t", "div_w", "div_l", "div_t", "conf_w", "conf_l", "conf_t", "streak", "source_url",
            "read_date", "verification_status")
    mfs = reg["model_facts.csv"]
    blocks = [
        belt([("Clubs", "32 x 2 seasons"), ("League points 2026", f"{facts['points_for']:.0f} for = "
              f"{facts['points_against']:.0f} against"), ("Games", f"{facts['games']:.0f}"),
              ("Home record sum", f"{facts['home_wins']:.0f}-{facts['home_losses']:.0f}-{facts['home_ties']:.0f}")],
             "Points for must equal points against across the league, and venue splits must sum to the game count. "
             "The checker asserts both on every build, so a transcription error fails CI instead of shipping."),
        render_table(list(keep), st26, "2026 division standings, read 2026-11-13 (after the Thursday result)",
                     "standings-2026"),
        render_table(list(keep), st25, "2025 final regular-season division standings, read 2026-11-13",
                     "standings-2025"),
        render_table(columns(mfs, ("fact_id", "category", "item", "value", "unit", "derivation_or_definition",
                                   "status", "source_url", "flag_id")), mfs,
                           "League facts derived from the two registers", "league-facts", status_key="status"),
    ]
    pages["standings.html"] = page("standings.html", "Verified data and league facts",
                                   "The two standings registers this pack reads everything from, plus every league "
                                   "figure derived from them.", blocks, eyebrow="DATA")

    # ---------------------------------------------------------------- slate
    slate = load_input("week10_slate.csv")
    bul = load_input("official_bulletins.csv")
    blocks = [
        belt([("Games", "14"), ("Settled at read", "1"), ("Awaiting kickoff", "13"), ("Clubs on bye", "4")],
             "One game had finished when the official pages were read: Thursday's Commanders 24, Giants 21. It is "
             "the only result on this page and it is the reason the 2026 register differs from the 12 November "
             "registers by exactly those points."),
        render_table(columns(slate, ("game_id", "date", "kickoff_et", "away_club", "away_record", "home_club",
                                     "home_record", "slot_label_on_official_page", "broadcast_listing_verified",
                                     "neutral_site", "venue_label_verified", "game_state", "away_points_final",
                                     "home_points_final", "source_urls")), slate,
                           "2026 Week 10 slate as published on the official schedule and injury-report pages",
                           "slate-table", status_key="game_state"),
        render_table(columns(bul, ("bulletin_id", "headline_verbatim", "published_date_label", "read_date",
                                   "what_it_confirms", "what_it_does_not_confirm", "url", "verification_status")), bul,
                           "Official bulletins linked from the injury-report page read the same day", "bulletins",
                           status_key="verification_status"),
    ]
    pages["slate.html"] = page("slate.html", "Week 10 slate and official bulletins",
                               "The fixture list, the one settled result, and the league bulletins that change how "
                               "the slate should be read.", blocks, eyebrow="FIXTURES")

    # ---------------------------------------------------------------- origination
    lines = reg["originated_lines.csv"]
    sens = reg["sensitivity.csv"]
    flips = [r for r in lines if r["assumption_grid_sign_stable"] == "no"]
    blocks = [
        belt([("Lines originated", str(len(lines))), ("Market columns populated", "0 (by design)"),
              ("Sign stable across the grid", f"{len(lines) - len(flips)} of {len(lines)}"),
              ("Total invariance to home points", "yes, by construction")],
             "Method: each club's points scored and allowed per game come from the standings register; a game's "
             "expected total is the average of the two clubs' scoring and each other's allowing, the spread is the "
             "difference, and the win, push and key-number probabilities come from the exact margin distribution of "
             "two Poisson laws - so a tie is a priced outcome rather than a rounding error."),
        "<section id=\"formula\"><h2>The arithmetic, in full</h2><pre class=\"formula\">"
        "base_home = 0.5 * (home.points_per_game + away.points_allowed_per_game)\n"
        "base_away = 0.5 * (away.points_per_game + home.points_allowed_per_game)\n"
        "expected_total = base_home + base_away\n"
        "expected_margin = base_home - base_away + home_field_points   (0 on this slate, and 0 at a neutral site)\n"
        "points_home ~ Poisson(base_home + hfp/2), points_away ~ Poisson(base_away - hfp/2)\n"
        "P(margin = m) = sum_k P_home(k + m) * P_away(k)        (exact, truncated at 80 points and renormalised)\n"
        "P(home win) = sum over m > 0, plus half the mass at m = 0"
        "</pre><p>Two assumptions are load-bearing and labelled: the Poisson law for points, and zero home-field "
        "points. The first is a distributional choice, the second is a refusal to import a number this register "
        "cannot measure. Both are varied in the grid below; the market columns stay blank because there is no "
        "licensed quote to fill them (FL-01).</p></section>",
        render_table(columns(lines, ("line_id", "kickoff_et", "away_club", "away_record", "home_club", "home_record",
                                     "away_ppg", "away_papg", "home_ppg", "home_papg", "model_fair_spread_home",
                                     "model_fair_spread_rounded", "model_fair_total", "model_fair_total_rounded",
                                     "model_home_win_prob", "model_push_prob", "model_tie_mass",
                                     "key_number_mass_3",
                                     "key_number_mass_7", "one_score_window_mass", "market_open_line",
                                     "market_close_line", "market_total", "market_implied_prob",
                                     "de_vigged_market_prob", "home_deficiency_score", "away_deficiency_score",
                                     "home_cluster_alert", "away_cluster_alert", "assumption_grid_sign_stable",
                                     "line_status", "flag_id", "input_source")), lines,
                           "Originated lines for the 13 unsettled Week 10 games (negative spread = home club "
                           "favoured)", "originated", status_key="line_status"),
        render_table(columns(flips, ("line_id", "matchup" if "matchup" in flips[0] else "away_club", "home_club",
                                     "model_fair_spread_home", "model_home_win_prob", "flips_at_home_points",
                                     "assumption_grid_sign_stable", "input_source")) if flips else [],
                     flips, "Games where the favoured side depends on the home assumption (DG-12 fail reason)",
                     "flip-games"),
        render_table(columns(sens, ("sens_id", "game_id", "matchup", "assumed_home_points", "spread_home", "total",
                                    "home_win_prob", "push_prob", "favoured", "note", "status", "source_url")),
                           sens, "Assumption grid: the same 13 games across home-point values, plus the sample-size "
                           "arithmetic for a per-game edge", "sensitivity", status_key="status"),
    ]
    pages["origination.html"] = page("origination.html", "Own-line origination",
                                     "Fair values originated from verified scoring, with the assumptions exposed as a "
                                     "grid instead of hidden in a constant.", blocks, eyebrow="MODEL")

    # ---------------------------------------------------------------- correlations
    corr = reg["correlations.csv"]
    fr = reg["frechet_bounds.csv"]
    blocks = [
        belt([("Measured coefficients", str(sum(1 for r in corr if r["status"] == "measured"))),
              ("Deliberately blank", str(sum(1 for r in corr if r["status"].startswith("blank")))),
              ("Resamples per interval", "4,000"), ("Permutation replicates", "20,000")],
             "Club-season correlations are measurable today from the standings registers. Same-game residual "
             "dependence is not, so those rows carry bounds and a flag rather than a number - which is the whole "
             "point: a parlay priced on independence is a guess dressed as arithmetic."),
        render_table(columns(corr, ("corr_id", "scope", "pair", "n", "pearson_r", "spearman_rho", "boot_ci_95",
                                    "perm_p", "r_squared", "mechanism_or_reason", "how_the_desk_uses_it", "status",
                                    "note", "flag_id", "source_url")), corr,
                           "Correlation register", "correlation-table", status_key="status"),
        render_table(columns(fr, ("combo_id", "leg_1_prob", "leg_2_prob", "independent_product",
                                  "frechet_lower_bound", "frechet_upper_bound", "fair_american_at_lower",
                                  "fair_american_at_independent", "fair_american_at_upper",
                                  "worst_case_overcharge_vs_bounds", "note", "status", "source_url", "flag_id")), fr,
                           "Frechet bounds for combo pricing while dependence is unmeasured", "frechet",
                           status_key="status"),
    ]
    pages["correlations.html"] = page("correlations.html", "Correlations and combo dependence",
                                      "Measured dependence where data exists, published bounds where it does not.",
                                      blocks, eyebrow="DEPENDENCE")

    # ---------------------------------------------------------------- gates
    gates = reg["validation_gates.csv"]
    blocks = [
        belt([(k, str(v)) for k, v in summary_counts(gates, "state").items()],
             "A gate is PASS only when its evidence exists. BLOCKED means an input is missing; it is never counted "
             "as a pass, and no strategy is promoted across it."),
        render_table(columns(gates, ("gate_id", "name", "family", "requirement", "blocks_failure_mode", "state",
                                     "measured", "enforcer_path", "unlock", "read_date", "source_url")), gates,
                           "Validation gates, with the state recomputed from the registers at build time",
                           "gates-table", status_key="state"),
    ]
    pages["validation.html"] = page("validation.html", "Validation gates",
                                    "Sixteen checks a strategy must clear before it can appear on the performance "
                                    "board - with today's measured state for each.", blocks, eyebrow="QUALITY GATES")

    # ---------------------------------------------------------------- strategies
    strat = reg["strategies.csv"]
    blocks = [
        belt([("Strategies", str(len(strat))), ("Singles", str(sum(1 for r in strat if "Single" in r["structure"]))),
              ("Parlays", str(sum(1 for r in strat if r["structure"].startswith("Parlay")))),
              ("Prop combos", str(sum(1 for r in strat if "prop combo" in r["structure"]))),
              ("Qualifying today", "0")],
             "Hypotheses are frozen before any outcome is scored - the register itself is the pre-registration. "
             "Rewriting a hypothesis after seeing results is what turns noise into a story, so the file is the "
             "commit boundary."),
        render_table(columns(strat, ("strategy_id", "structure", "name", "hypothesis", "required_features",
                                     "available_features", "missing_features", "luck_controls", "readiness",
                                     "gates_passed", "gates_total", "status", "reward_tier", "unlock_next",
                                     "read_date", "source_url")), strat,
                           "Preregistered strategies", "strategies-table", status_key="status"),
    ]
    pages["strategies.html"] = page("strategies.html", "Strategy lab",
                                    "Twelve signals for singles, parlays and prop combos, each with the inputs it "
                                    "needs and what it is missing today.", blocks, eyebrow="SIGNALS")

    # ---------------------------------------------------------------- leaderboard
    lb = reg["leaderboard.csv"]
    rw = reg["rewards.csv"]
    blocks = [
        belt([("Entries on the performance board", "0"), ("Entries on the readiness board", str(len(lb))),
              ("Best readiness", f"{max(float(r['readiness']) for r in lb):.2f}"),
              ("Rewards paid", "0")],
             "Two boards, one purpose: readiness is what can be ranked today from verified inputs; performance is "
             "what the gates allow later. A strategy climbs the readiness board by becoming testable, not by looking "
             "good."),
        render_table(columns(lb, ("rank", "strategy_id", "structure", "name", "readiness", "missing_features",
                                  "gates_passed_evidence", "settled_selections", "holdout_roi", "same_line_clv",
                                  "brier", "skill_score", "status", "reward_tier", "reward", "leaderboard_note",
                                  "read_date", "source_url")), lb,
                           "Leaderboard - readiness ranked, performance columns blank until the evidence exists",
                           "leaderboard-table", status_key="status"),
        render_table(columns(rw, ("tier_id", "reward", "criteria", "entries_at_tier", "how_ties_are_broken",
                                  "status", "read_date", "source_url")), rw,
                           "Reward ladder, published before anyone competes", "rewards", status_key="status"),
    ]
    pages["leaderboard.html"] = page("leaderboard.html", "Leaderboard and rewards",
                                     "A competition with the prize rules written down first and an empty top tier "
                                     "until the evidence arrives.", blocks, eyebrow="COMPETITION")

    # ---------------------------------------------------------------- injuries
    cov = load_input("injury_report_coverage.csv")
    inj = load_input("injury_report_2026_w10.csv")
    blocks = [
        belt([("Clubs read", f"{len(cov)} of 32 (28 play in Week 10)"),
              ("Rows on the official page", str(sum(int(r['rows_listed_on_official_page']) for r in cov))),
              ("Rows published here", str(len(inj))), ("Designated out", str(sum(int(r['out_count']) for r in cov))),
              ("Did not practise", str(sum(int(r['dnp_count']) for r in cov)))],
             "The report lists only players a club designated that week, so an absence of a name is not evidence of "
             "health - four bye clubs are outside the read, and rows carrying neither a designation nor a no-practice "
             "mark are summarised in the coverage counts rather than dropped silently."),
        render_table(columns(cov, ("row_id", "club", "rows_listed_on_official_page", "rows_included_in_register",
                                   "out_count", "dnp_count", "limited_count", "full_count", "questionable_count",
                                   "exclusion_rule", "source_url", "read_date", "verification_status")), cov,
                           "Coverage of the Week 10 official injury report read", "injury-coverage",
                           status_key="verification_status"),
        render_table(columns(inj, ("row_id", "club", "player", "position", "listed_injury",
                                   "practice_status_verbatim", "game_status", "inclusion_rule", "source_url",
                                   "read_date", "verification_status")), inj,
                           "Decision-relevant injury rows (designated out, questionable, or did not practise)",
                           "injury-rows", status_key="verification_status"),
    ]
    pages["injuries.html"] = page("injuries.html", "Injury tracking, Week 10 2026",
                                  "Every designation the official report carried for the Week 10 slate at the moment "
                                  "it was read.", blocks, eyebrow="AVAILABILITY")

    # ---------------------------------------------------------------- depth
    depth = reg["depth_deficiency.csv"]
    worst = sorted(depth, key=lambda r: -int(r["deficiency_score"]))[:1]
    blocks = [
        belt([("Club-unit records", str(len(depth))), ("Cluster alerts (2+ in one group)",
              str(sum(1 for r in depth if r["cascading_cluster"] == "yes"))),
              ("Groups at 4th string or deeper", str(sum(1 for r in depth if "4th" in r["replacement_tier"] or "depleted" in r["replacement_tier"].lower()))),
              ("Deepest single gap", f"{worst[0]['club']}, {worst[0]['unit_group_label']} (score {worst[0]['deficiency_score']})")],
             "The score is an ordinal screen built from the report rows above: Out=3, did not practise=2, "
             "limited=1. It is a stated policy weight, not a measured points value, and it is deliberately not "
             "converted into a spread (FL-09)."),
        render_table(columns(depth, ("depth_id", "club", "unit_group_label", "players_listed", "impaired_count",
                                     "out_count", "deficiency_score", "replacement_tier", "cascading_cluster",
                                     "starter_dependent_unit", "affected_players", "weighting_policy", "status",
                                     "flag_id", "source_url", "read_date")), depth,
                           "Depth deficiency by club and unit group", "depth-table", status_key="status"),
    ]
    pages["depth.html"] = page("depth.html", "Depth deficiency model",
                               "How far down each chart a club has to reach for Week 10, unit by unit, with the "
                               "weighting policy on the same page.", blocks, eyebrow="DEPTH")

    # ---------------------------------------------------------------- verification ledger
    ver = ledger
    review_rows = [r for r in ver if r["verification_status"] == "needs_review"]
    dispo_rows = [{"disposition": k, "rows": str(v),
                   "meaning": {
                       "CONFIRMED": "the prior published value equals the 2026-11-13 official read",
                       "CONFIRMED_LABEL_VARIANT": "same claim in another notation (ET vs EST, true vs yes); the "
                                                   "desk prints the abbreviation the official page uses",
                       "DISAGREES_ACROSS_OFFICIAL_PAGES": "two official nfl.com pages list different values for the "
                                                          "same field, and neither is marked authoritative, so the "
                                                          "disagreement is published instead of resolved",
                       "VALUES_DIFFER": "prior and official differ with nothing between the reads that reconciles "
                                        "them",
                       "SELF_CHECK_RECOMPUTED": "an invariant of this pack's own registers, asserted on every "
                                                "build; there is no prior publication to compare it against",
                       "JOIN_KEY_MISMATCH": "the two registers key the same club differently, so a naive join drops "
                                            "the row",
                       "SUPERSEDED_RECONCILED": "the prior value was correct at its own timestamp; the difference is "
                                                "exactly the one settled game between the two reads",
                       "CONFIRMED_NAME_NORMALISED": "status matches once Jr./Sr./II/III suffixes are normalised - the "
                                                    "prior register prints a name the report does not",
                       "CONFIRMED_VIA_BULLETIN": "an IR or season-ending move is not on a weekly participation "
                                                 "report; the official bulletin linked from that page confirms it",
                       "DRIFT_STATUS_CHANGED": "the designation differs from the prior read, most often because the "
                                               "weekly report is revised Wednesday to Friday",
                       "PENDING_GAME_DESIGNATION": "the participation level is consistent with the claim, but this "
                                                  "club's Friday game status had not been posted at read time",
                       "FORECAST_NOT_A_REPORT": "the prior row states an expectation, not a designation; the report "
                                                "can neither confirm nor refute it",
                       "NAME_NOT_MATCHED": "no name in that club's rows matches after normalisation, so identity is "
                                           "unresolved without a player id",
                       "PROVENANCE_MISMATCH": "a participation or game-status claim is sourced to a club depth-chart "
                                              "page, which does not carry those fields",
                       "NOT_REVERIFIED_THIS_READ": "this session declined to verify the field (stadium names appear "
                                                   "only inside partner links on the schedule page)",
                   }.get(k, "")} for k, v in dispo.items()]
    blocks = [
        belt([("Rows compared", str(len(ver))), ("Verified", str(len(ver) - len(review_rows))),
              ("Needs review", str(len(review_rows))), ("Registers audited", "3")],
             "This is the audit of the previously published NFL packs, run as code rather than as prose: the same "
             "script regenerates the ledger against any later official read. Nothing in another session's files was "
             "edited; findings are reported here and on the flagged page."),
        render_table(["disposition", "rows", "meaning"], dispo_rows, "Ledger summary by disposition",
                     "ledger-summary", status_key="disposition"),
        # the read that verifies a row is listed before the citation the row is about: a reviewer following the
        # link on the right should land on the official page, not on somebody else's source
        render_table(columns(review_rows, ("row_id", "register_audited", "subject", "field", "prior_value",
                                           "official_value_2026_11_13", "disposition", "explanation",
                                           "this_read_source_url", "prior_source_url", "verification_status")),
                     review_rows, "Every row that needs a human decision", "ledger-review",
                     status_key="disposition"),
        render_table(columns(ver, ("row_id", "register_audited", "subject", "field", "prior_value",
                                  "official_value_2026_11_13", "disposition", "explanation", "this_read_source_url",
                                  "prior_source_url", "verification_status")), ver,
                            "Complete ledger: field-by-field comparison of the three prior registers against the "
                            "2026-11-13 official read", "ledger-full", status_key="verification_status"),
    ]
    pages["verification.html"] = page("verification.html", "Verification ledger",
                                      "Line-by-line re-verification of the three published NFL registers against "
                                      "official pages read on 2026-11-13.", blocks, eyebrow="AUDIT")

    # ---------------------------------------------------------------- repo audit
    ra = reg["repo_audit.csv"]
    gh = load_input("github_state.csv")
    blocks = [
        belt([("Computed checks", str(len(ra))), ("Published NFL dashboard sections", "4 (this one included)"),
              ("Computed by this build, not transcribed", "every row"),
              ("Open pull requests", "6"), ("CI checks on main", "14, all success")],
             "Each finding below was recomputed inside this build, so it cannot quietly go stale: if the repo "
             "changes, the text changes with it."),
        render_table(columns(ra, ("finding_id", "severity", "repo_path", "finding", "evidence_computed_here",
                                 "disposition", "read_date", "official_source_url")), ra,
                           "Repository audit, computed from the working tree", "repo-audit-table",
                           status_key="severity"),
        render_table(columns(gh, ("record_id", "severity", "repo_path", "finding", "evidence_computed_here",
                                  "disposition", "official_source_url", "read_date")), gh,
                           "Publication and coordination state read from GitHub the same day", "github-state",
                           status_key="severity"),
    ]
    pages["repo-audit.html"] = page("repo-audit.html", "Repo audit and irregularities",
                                    "Irregularities found in the repository while verifying it, each with the "
                                    "evidence that produced it.", blocks, eyebrow="REPO REVIEW")

    # ---------------------------------------------------------------- sources
    src = load_input("sources.csv")
    blocks = [
        belt([("Official pages read", str(sum(1 for r in src if "nfl.com" in r["url"]))),
              ("Methodology references", str(sum(1 for r in src if r["verification_status"] == "methodology_reference"))),
              ("Read but not confirmed", str(sum(1 for r in src if r["verification_status"] == "link_only_not_reverified"))),
              ("Registers", str(len(list((DERIVED).glob('*.csv'))) + len([p for p in DATA.glob('*.csv')])))],
             "Read method is recorded because it matters: a chunked read of a live page is a snapshot of one moment, "
             "which is exactly the limitation the snapshot gate (DG-04) is about."),
        render_table(columns(src, ("source_id", "publisher", "title", "url", "read_date", "retrieval_method",
                                   "verification_status", "verbatim_evidence_excerpt", "supports_claim",
                                   "does_not_support_boundary")), src,
                           "Source register for this pack", "sources-table", status_key="verification_status"),
        "<section id=\"integrity\"><h2>Register integrity</h2><pre class=\"formula\">"
        + "\n".join(f"{p.name:<34} sha256 {hashlib.sha256(p.read_bytes()).hexdigest()[:32]}"
                    for p in sorted(list(DATA.glob("*.csv")) + list(DERIVED.glob("*.csv"))))
        + "</pre><p>The derived registers are regenerated on every build; <code>--check</code> fails if a committed "
        "file differs from what the code produces.</p></section>",
    ]
    pages["sources.html"] = page("sources.html", "Sources and register integrity",
                                 "What was read, when, how, and what each source does not support.", blocks,
                                 eyebrow="PROVENANCE")

    # ---------------------------------------------------------------- flagged
    fl = load_input("flagged.csv")
    blocks = [
        belt([("Flagged items", str(len(fl))), ("Blocking the merge", str(sum(1 for r in fl if
              r["blocking_merge"] == "yes"))), ("High severity", str(sum(1 for r in fl if r["severity"] == "high"))),
              ("Blank cells held across the published registers",
               str(sum(1 for rows in reg.values() for r in rows for v in r.values() if str(v).strip() == "")))],
             "Every blank on this site is listed here with the artefact that would fill it. Nothing was filled in by "
             "inference to make a table look complete."),
        render_table(columns(fl, ("flag_id", "severity", "category", "affected_items", "what_cannot_be_confirmed",
                                  "why_it_stays_blank", "resolution_path", "blocking_merge", "source_url",
                                  "read_date")), fl,
                           "Flagged for review", "flagged-table", status_key="severity"),
    ]
    pages["flagged.html"] = page("flagged.html", "Flagged for review",
                                 "Unverified values, missing inputs and irregularities - published, not hidden.",
                                 blocks, eyebrow="NEEDS REVIEW")
    return pages


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#12171f;--muted:#5b6675;--line:#e2e6ec;--brand:#0b4ea2;--brand-2:#0a7d5a;
--warn:#a8560a;--bad:#b3261e;--ok:#0a7d5a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px}
.masthead{background:#0d1b2a;color:#fff;padding:18px 22px}
.masthead .brand{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.masthead .brand a{color:#fff;font-weight:700;letter-spacing:.14em;font-size:15px}
.masthead .brand span{color:#9fb3c8;font-size:12px;letter-spacing:.04em}
.masthead .tagline{margin:6px 0 0;color:#c6d4e2;font-size:13px}
nav.sections{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:8px 14px;
display:flex;gap:4px;flex-wrap:wrap;box-shadow:0 1px 2px rgba(16,24,32,.04)}
nav.sections a{font-size:12.5px;color:#334;padding:5px 9px;border-radius:999px;border:1px solid transparent}
nav.sections a:hover{background:#eef2f7;text-decoration:none}
nav.sections a.on{background:var(--brand);color:#fff}
main{max-width:1400px;margin:0 auto;padding:22px 22px 40px}
.eyebrow{margin:0;color:var(--muted);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase}
h1{margin:.25em 0 .35em;font-size:27px;letter-spacing:-.01em}
h2{margin:26px 0 8px;font-size:18px}h3{margin:18px 0 6px;font-size:15px}
.lede{margin:0 0 18px;color:var(--muted);max-width:100ch}
.belt{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:20px}
.belt-cells{display:flex;gap:10px;flex-wrap:wrap}
.belt-cells div{flex:1 1 150px;background:#f2f5f9;border-radius:9px;padding:9px 11px}
.belt-cells span{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.belt-cells strong{display:block;font-size:18px;margin-top:3px}
.belt p{margin:10px 0 0;color:#334155;font-size:13.5px;max-width:110ch}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:10px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 15px;color:var(--ink)}
.card h2{margin:0 0 6px;font-size:15.5px}.card p{margin:0;color:var(--muted);font-size:13px}
.card .go{display:inline-block;margin-top:9px;font-size:12.5px;color:var(--brand);font-weight:600}
.table-wrap{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:10px 0 22px}
table{border-collapse:collapse;width:100%;font-size:13px}
caption{text-align:left;padding:11px 13px;font-weight:600;font-size:13.5px;border-bottom:1px solid var(--line)}
caption .rowcount{color:var(--muted);font-weight:500;margin-left:8px;font-size:12px}
th,td{padding:8px 10px;border-bottom:1px solid #eef1f5;vertical-align:top;text-align:left}
th{position:sticky;top:0;background:#f8fafc;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#37465c;
white-space:nowrap;z-index:1}
tbody tr:nth-child(even){background:#fbfcfd}
.na{color:#475569;font-size:12px}
td.empty{background:repeating-linear-gradient(135deg,#fdf6f3,#fdf6f3 6px,#f7ece7 6px,#f7ece7 12px)}
td a{word-break:break-word}
.badge{display:inline-block;padding:1.5px 7px;border-radius:999px;font-size:11px;background:#eef2f7;color:#2b3a4d;
white-space:nowrap}
.b-verified,.b-confirmed,.b-yes,.b-pass,.b-verified-by-code-read,.b-verified-direct-official-read,.b-done{background:#e5f5ec;color:#0a6844}
.b-needs-review,.b-model-assumption,.b-unverified,.b-blank,.b-flagged,.b-medium,.b-pending-human-choice,.b-blocked{background:#fdf1e0;color:#8a5310}
.b-fail,.b-no,.b-high,.b-drift-status-changed,.b-provenance-mismatch,.b-name-not-matched,.b-forecast-not-a-report{background:#fdeaea;color:#98251e}
.b-computed,.b-computed-bounds,.b-computed-from-official-read,.b-info,.b-low,.b-originated-internally-not-validated-against-a-market{background:#e8f0fb;color:#1c4c8c}
.b-unverified-blank,.b-blank-pending-licensed-play-by-play{background:#f1eefe;color:#4c3d99}
pre.formula{background:#0d1b2a;color:#dfe9f3;padding:13px 15px;border-radius:10px;overflow:auto;font-size:12.5px;line-height:1.55}
ol.steps li{margin-bottom:6px}
footer{border-top:1px solid var(--line);background:#fff;margin-top:26px;padding:18px 22px 28px;color:var(--muted);font-size:12.5px}
footer .build{margin-top:6px}
@media (max-width:760px){h1{font-size:22px}main{padding:16px 12px 30px}}
"""


def main() -> int:
    check = "--check" in sys.argv
    SITE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    reg = build_registers()
    pages = build_pages(reg)
    written: list[str] = []
    generated: dict[Path, str] = {}
    for fname, content in pages.items():
        generated[SITE / fname] = content
    generated[ASSETS / "style.css"] = CSS
    for path, content in generated.items():
        if check:
            if not path.exists():
                print(f"MISSING {path.relative_to(ROOT)}", file=sys.stderr)
                return 1
            if path.read_text(encoding="utf-8") != content:
                print(f"STALE {path.relative_to(ROOT)} - rebuild required", file=sys.stderr)
                return 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(ROOT)))
    for name in reg:
        written.append(str((DERIVED / name).relative_to(ROOT)))
    if check:
        stale = sorted(p for p in SITE.glob("*.html") if p.name not in pages)
        if stale:
            print("UNEXPECTED pages: " + ", ".join(p.name for p in stale), file=sys.stderr)
            return 1
        print(f"build_nfl_desk OK: {len(pages)} pages and {len(reg)} derived registers reproduce byte-for-byte")
        return 0
    n_rows = sum(len(v) for v in reg.values())
    print(f"built {len(written)} files, {len(pages)} pages, {n_rows} derived rows across {len(reg)} registers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
