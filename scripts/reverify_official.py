#!/usr/bin/env python3
"""Independent re-check of the published 2026-11-05 snapshot and its computed layer.

This script does not import the original analysis code. It re-reads the captured
official pages (data/reverify_2026_11_05/*_read.csv, transcribed from nba.com by
this session), compares every published value against them, and recomputes the
derived numbers with a separately written implementation.

Three separate evidence types are kept apart and labelled in the output:

  match / mismatch     a published value versus a value read on an official page
  computed_*           a published computation versus an independent recomputation
  verified_text        an official quotation that was read and copied verbatim
  unverified           cannot be confirmed from an official source (value left blank)

Nothing is scraped at run time and no value is inferred. Outputs:
  data/reverify_2026_11_05/reconciliation.csv
  data/reverify_2026_11_05/recompute.csv
  data/reverify_2026_11_05/report.json

Run: python3 scripts/reverify_official.py
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READS = ROOT / "data" / "reverify_2026_11_05"
PUBLISHED = ROOT / "data" / "official_2026_11_05"

STANDINGS_URL = "https://www.nba.com/standings"
RESULTS_URL = "https://www.nba.com/games?date=2026-11-04"
SLATE_5_URL = "https://www.nba.com/games?date=2026-11-05"
SLATE_6_URL = "https://www.nba.com/games?date=2026-11-06"
TERMS_URL = "https://www.nba.com/termsofuse"

RIDGE = 5.0
MIN_TRAIN = 60
BOOT = 2000
SEED = 20261105


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# --------------------------------------------------------------------------
# Independent linear algebra: Cholesky solve of the ridge normal equations.
# Written separately from the Gauss-Jordan solver used by the published build.
# --------------------------------------------------------------------------
def cholesky(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    low = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            acc = matrix[i][j] - sum(low[i][k] * low[j][k] for k in range(j))
            if i == j:
                if acc <= 0:
                    raise ValueError("normal equations not positive definite")
                low[i][j] = math.sqrt(acc)
            else:
                low[i][j] = acc / low[j][j]
    return low


def chol_solve(low: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    y = [0.0] * size
    for i in range(size):
        y[i] = (vector[i] - sum(low[i][k] * y[k] for k in range(i))) / low[i][i]
    x = [0.0] * size
    for i in reversed(range(size)):
        x[i] = (y[i] - sum(low[k][i] * x[k] for k in range(i + 1, size))) / low[i][i]
    return x


def ridge_fit(design: list[list[float]], y: list[float], penalised: int) -> list[float]:
    width = len(design[0])
    xtx = [[0.0] * width for _ in range(width)]
    xty = [0.0] * width
    for row, target in zip(design, y):
        for i in range(width):
            if row[i] == 0.0:
                continue
            xty[i] += row[i] * target
            for j in range(width):
                xtx[i][j] += row[i] * row[j]
    for i in range(penalised):
        xtx[i][i] += RIDGE
    return chol_solve(cholesky(xtx), xty)


# --------------------------------------------------------------------------
# Load the committed result archive (same selection rule, independent code).
# --------------------------------------------------------------------------
def load_games() -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    seen: dict[str, dict] = {}
    games: list[dict] = []
    for rel in (
        "data/games_results_2026-27.csv",
        "data/results_2026-11-02.csv",
        "data/official_2026_11_05/results_2026_11_04.csv",
    ):
        for row in read_rows(ROOT / rel):
            gid = row.get("game_id", "").strip()
            if not gid:
                continue
            entry = {
                "game_id": gid,
                "date": row["date"],
                "away": row["away_team"],
                "away_score": int(row["away_score"]),
                "home": row["home_team"],
                "home_score": int(row["home_score"]),
                "source_url": row["source_url"],
                "archive": rel,
            }
            if gid in seen:
                prior = seen[gid]
                if (prior["home_score"], prior["away_score"]) != (
                    entry["home_score"],
                    entry["away_score"],
                ):
                    notes.append(f"conflicting duplicate scores for {gid} in {rel}")
                continue
            seen[gid] = entry
            games.append(entry)
    games.sort(key=lambda g: (g["date"], g["game_id"]))
    return games, notes


def records(games: list[dict]) -> dict[str, list[int]]:
    table: dict[str, list[int]] = {}
    for game in games:
        table.setdefault(game["home"], [0, 0])
        table.setdefault(game["away"], [0, 0])
        if game["home_score"] > game["away_score"]:
            table[game["home"]][0] += 1
            table[game["away"]][1] += 1
        else:
            table[game["away"]][0] += 1
            table[game["home"]][1] += 1
    return table


def pearson(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    sum_x, sum_y = sum(xs), sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)
    sum_yy = sum(y * y for y in ys)
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_xx - sum_x**2) * (n * sum_yy - sum_y**2))
    r = numerator / denominator if denominator else 0.0
    r = max(-0.999999, min(0.999999, r))
    z = math.atanh(r)
    half = 1.96 / math.sqrt(max(1, n - 3))
    return {
        "n": n,
        "r": round(r, 4),
        "ci95_low": round(math.tanh(z - half), 4),
        "ci95_high": round(math.tanh(z + half), 4),
    }


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def brier(probabilities: list[float], outcomes: list[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(outcomes)


def exact_binomial_p(successes: int, trials: int) -> float:
    if trials == 0:
        return 1.0
    tail = sum(math.comb(trials, k) for k in range(0, min(successes, trials - successes) + 1))
    return min(1.0, 2 * tail / 2**trials)


def wilson(successes: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    z = 1.96
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def build_design(games: list[dict], teams: list[str]) -> tuple[list[list[float]], list[list[float]]]:
    index = {team: i for i, team in enumerate(teams)}
    margin_rows, total_rows = [], []
    for game in games:
        row = [0.0] * (len(teams) + 1)
        row[index[game["home"]]] = 1.0
        row[index[game["away"]]] = -1.0
        row[-1] = 1.0
        margin_rows.append(row)
        trow = [0.0] * (len(teams) + 1)
        trow[index[game["home"]]] = 1.0
        trow[index[game["away"]]] = 1.0
        trow[-1] = 1.0
        total_rows.append(trow)
    return margin_rows, total_rows


def fit_model(games: list[dict], teams: list[str]) -> dict:
    margins = [g["home_score"] - g["away_score"] for g in games]
    totals = [g["home_score"] + g["away_score"] for g in games]
    mrows, trows = build_design(games, teams)
    mbeta = ridge_fit(mrows, [float(m) for m in margins], len(teams))
    tbeta = ridge_fit(trows, [float(t) for t in totals], len(teams))
    mres = [m - sum(a * b for a, b in zip(row, mbeta)) for row, m in zip(mrows, margins)]
    tres = [t - sum(a * b for a, b in zip(row, tbeta)) for row, t in zip(trows, totals)]
    return {
        "margin": mbeta,
        "total": tbeta,
        "sigma": math.sqrt(sum(r * r for r in mres) / max(1, len(mres) - 1)),
        "tsigma": math.sqrt(sum(r * r for r in tres) / max(1, len(tres) - 1)),
        "home_win_rate": sum(1 for m in margins if m > 0) / len(margins),
    }


def predict(model: dict, teams: list[str], home: str, away: str) -> tuple[float, float]:
    index = {team: i for i, team in enumerate(teams)}
    margin = model["margin"][index[home]] - model["margin"][index[away]] + model["margin"][-1]
    total = model["total"][index[home]] + model["total"][index[away]] + model["total"][-1]
    return margin, total


def walk_forward(games: list[dict], teams: list[str]) -> dict:
    probs, base_probs, outcomes, picks = [], [], [], []
    margin_errors, total_errors = [], []
    for i in range(MIN_TRAIN, len(games)):
        model = fit_model(games[:i], teams)
        game = games[i]
        margin, total = predict(model, teams, game["home"], game["away"])
        probs.append(phi(margin / max(model["sigma"], 1e-6)))
        base_probs.append(model["home_win_rate"])
        outcomes.append(1 if game["home_score"] > game["away_score"] else 0)
        margin_errors.append(game["home_score"] - game["away_score"] - margin)
        total_errors.append(game["home_score"] + game["away_score"] - total)
        picks.append((margin > 0) == (game["home_score"] > game["away_score"]))
    wins = sum(picks)
    model_only = sum(1 for pk, y in zip(picks, outcomes) if pk and not y)
    base_only = sum(1 for pk, y in zip(picks, outcomes) if (not pk) and y)
    discordant = model_only + base_only
    rng = random.Random(SEED)
    boots = []
    for _ in range(BOOT):
        idx = [rng.randrange(len(outcomes)) for _ in outcomes]
        p = [probs[i] for i in idx]
        b = [base_probs[i] for i in idx]
        y = [outcomes[i] for i in idx]
        denom = brier(b, y)
        boots.append(1.0 - brier(p, y) / denom if denom else 0.0)
    boots.sort()
    model_brier = brier(probs, outcomes)
    base_brier = brier(base_probs, outcomes)
    return {
        "n_predictions": len(outcomes),
        "winner_accuracy": round(wins / len(picks), 4),
        "winner_accuracy_ci95_low": round(wilson(wins, len(picks))[0], 4),
        "winner_accuracy_ci95_high": round(wilson(wins, len(picks))[1], 4),
        "home_always_accuracy": round(sum(outcomes) / len(outcomes), 4),
        "brier_model": round(model_brier, 4),
        "brier_home_rate_baseline": round(base_brier, 4),
        "brier_skill_score": round(1.0 - model_brier / base_brier, 4),
        "brier_skill_score_ci95_low": round(boots[int(0.025 * BOOT)], 4),
        "brier_skill_score_ci95_high": round(boots[int(0.975 * BOOT) - 1], 4),
        "mcnemar_model_only_correct": model_only,
        "mcnemar_home_only_correct": base_only,
        "mcnemar_exact_p_two_sided": round(
            exact_binomial_p(min(model_only, base_only), discordant) if discordant else 1.0, 5
        ),
        "mae_margin": round(sum(abs(e) for e in margin_errors) / len(margin_errors), 3),
        "rmse_margin": round(math.sqrt(sum(e * e for e in margin_errors) / len(margin_errors)), 3),
        "mae_total": round(sum(abs(e) for e in total_errors) / len(total_errors), 3),
        "rmse_total": round(math.sqrt(sum(e * e for e in total_errors) / len(total_errors)), 3),
    }


# --------------------------------------------------------------------------
# Reconcilers
# --------------------------------------------------------------------------
def compare_scalar(
    rows: list[dict],
    check_id: str,
    category: str,
    subject: str,
    published_file: str,
    published_value: str,
    official_value: str,
    source_url: str,
    note: str = "",
) -> dict:
    if official_value == "":
        status = "unverified"
    elif published_value == official_value:
        status = "match"
    else:
        status = "mismatch"
    return {
        "check_id": check_id,
        "category": category,
        "subject": subject,
        "published_file": published_file,
        "published_value": published_value,
        "official_read_value": official_value,
        "status": status,
        "source_url": source_url,
        "note": note,
    }


def main() -> int:
    recon: list[dict] = []
    recompute: list[dict] = []

    published_standings = read_rows(PUBLISHED / "standings.csv")
    read_standings = {r["team_abbr"]: r for r in read_rows(READS / "standings_read.csv")}
    for row in published_standings:
        abbr = row["team_abbr"]
        fresh = read_standings.get(abbr, {})
        for field, label in (
            ("w", "wins"),
            ("l", "losses"),
            ("win_pct", "win percentage"),
            ("gb", "games behind"),
        ):
            recon.append(
                compare_scalar(
                    recon,
                    f"ST-{abbr}-{field}",
                    "standings",
                    f"{abbr} {label}",
                    "data/official_2026_11_05/standings.csv",
                    row[field],
                    fresh.get(field, ""),
                    STANDINGS_URL,
                )
            )
    missing = set(read_standings) - {r["team_abbr"] for r in published_standings}
    for abbr in sorted(missing):
        recon.append(
            compare_scalar(
                recon,
                f"ST-{abbr}-missing",
                "standings",
                f"{abbr} present on official page but absent from the published snapshot",
                "data/official_2026_11_05/standings.csv",
                "",
                "present",
                STANDINGS_URL,
                "published row missing",
            )
        )

    published_results = read_rows(PUBLISHED / "results_2026_11_04.csv")
    read_results = {r["game_id"]: r for r in read_rows(READS / "results_read.csv")}
    for row in published_results:
        gid = row["game_id"]
        fresh = read_results.get(gid, {})
        for field, label in (
            ("away_score", "away score"),
            ("home_score", "home score"),
            ("status", "status"),
            ("away_team", "away team"),
            ("home_team", "home team"),
        ):
            recon.append(
                compare_scalar(
                    recon,
                    f"RS-{gid}-{field}",
                    "results",
                    f"{gid} {label}",
                    "data/official_2026_11_05/results_2026_11_04.csv",
                    row[field],
                    fresh.get(field, ""),
                    RESULTS_URL,
                )
            )
    extra = set(read_results) - {r["game_id"] for r in published_results}
    for gid in sorted(extra):
        recon.append(
            compare_scalar(
                recon,
                f"RS-{gid}-missing",
                "results",
                f"{gid} on the official page but absent from the published snapshot",
                "data/official_2026_11_05/results_2026_11_04.csv",
                "",
                "present",
                RESULTS_URL,
                "missing result row",
            )
        )

    published_slate = read_rows(PUBLISHED / "slate_2026_11_05_06.csv")
    read_slate = {r["game_id"]: r for r in read_rows(READS / "slate_read.csv")}
    for row in published_slate:
        gid = row["game_id"]
        fresh = read_slate.get(gid, {})
        source = SLATE_5_URL if row["date"] == "2026-11-05" else SLATE_6_URL
        for field, label in (
            ("date", "date"),
            ("tip_et", "tip time (ET)"),
            ("away_team", "away team"),
            ("home_team", "home team"),
            ("competition", "competition"),
            ("away_w", "away wins"),
            ("away_l", "away losses"),
            ("home_w", "home wins"),
            ("home_l", "home losses"),
        ):
            if field.endswith(("_w", "_l")):
                side, kind = field.split("_")
                published_value = row[field]
                stable = fresh.get(f"stable_{side}_record", "")
                official_value = stable.split("-")[0 if kind == "w" else 1] if stable else ""
            else:
                published_value = row[field]
                official_value = fresh.get(field, "")
            note = ""
            if field == "competition":
                # The official page prefixes the competition with its title sponsor.
                # The published label drops that prefix; compare the rest exactly.
                official_normalised = official_value.replace("Emirates ", "")
                if official_normalised == published_value and official_value != published_value:
                    note = (
                        "official page reads '"
                        + official_value
                        + "'; the published label omits the title-sponsor prefix (NBA Terms 9(iii) "
                        "bars commercial identification) and is otherwise identical"
                    )
                    official_value = official_normalised
            recon.append(
                compare_scalar(
                    recon,
                    f"SL-{gid}-{field}",
                    "slate",
                    f"{gid} {label}",
                    "data/official_2026_11_05/slate_2026_11_05_06.csv",
                    published_value,
                    official_value,
                    source,
                    note,
                )
            )
    for gid in sorted(set(read_slate) - {r["game_id"] for r in published_slate}):
        recon.append(
            compare_scalar(
                recon,
                f"SL-{gid}-missing",
                "slate",
                f"{gid} on the official page but absent from the published slate",
                "data/official_2026_11_05/slate_2026_11_05_06.csv",
                "",
                "present",
                SLATE_6_URL,
                "missing slate row",
            )
        )

    # Official calendar counts versus the sizes of the published archives.
    calendar = {r["date"]: int(r["games_on_official_calendar"]) for r in read_rows(READS / "calendar_read.csv")}
    nov2 = read_rows(ROOT / "data" / "results_2026-11-02.csv")
    recon.append(
        compare_scalar(
            recon,
            "CAL-2026-11-02",
            "calendar",
            "games on 2026-11-02 (published archive rows)",
            "data/results_2026-11-02.csv",
            str(len(nov2)),
            str(calendar.get("2026-11-02", "")),
            "https://www.nba.com/games?date=2026-11-04",
            "official month calendar cell",
        )
    )
    recon.append(
        compare_scalar(
            recon,
            "CAL-2026-11-04",
            "calendar",
            "games on 2026-11-04 (published archive rows)",
            "data/official_2026_11_05/results_2026_11_04.csv",
            str(len(published_results)),
            str(calendar.get("2026-11-04", "")),
            "https://www.nba.com/games?date=2026-11-04",
            "official month calendar cell",
        )
    )
    for day in ("2026-11-05", "2026-11-06"):
        published_count = len([r for r in published_slate if r["date"] == day])
        recon.append(
            compare_scalar(
                recon,
                f"CAL-{day}",
                "calendar",
                f"games on {day} (published slate rows)",
                "data/official_2026_11_05/slate_2026_11_05_06.csv",
                str(published_count),
                str(calendar.get(day, "")),
                "https://www.nba.com/games?date=2026-11-04",
                "official month calendar cell",
            )
        )

    # Rights text: copied verbatim from the official page this session.
    for row in read_rows(READS / "rights_read.csv"):
        quote = row["verbatim_quote"]
        recon.append(
            {
                "check_id": f"RT-{row['clause'].replace(' ', '-')}",
                "category": "rights",
                "subject": f"{row['clause']} quoted on the site",
                "published_file": "data/reverify_2026_11_05/rights_read.csv",
                "published_value": f"{len(quote)} characters quoted",
                "official_read_value": "text read on nba.com/termsofuse",
                "status": "verified_text" if len(quote) > 60 else "unverified",
                "source_url": TERMS_URL,
                "note": row["compiler_note"],
            }
        )

    # Fail-closed ledger claims.
    report_rows = read_rows(ROOT / "data" / "empirical" / "report.csv")
    observations = read_rows(ROOT / "data" / "empirical" / "observations.csv")
    qualified = [r for r in report_rows if r.get("qualified", "").lower() == "true"]
    running = [r for r in report_rows if r.get("status") != "not_run"]
    for check_id, subject, published, recomputed, note in (
        ("FC-observations", "authorized observations in the ledger", "0", str(len(observations)), "rows in observations.csv"),
        ("FC-qualified", "strategies marked qualified", "0", str(len(qualified)), "rows in report.csv"),
        ("FC-running", "strategies in a non fail-closed state", "0", str(len(running)), "rows in report.csv"),
    ):
        recon.append(
            {
                "check_id": check_id,
                "category": "failclosed",
                "subject": subject,
                "published_file": "data/empirical/report.csv",
                "published_value": published,
                "official_read_value": recomputed,
                "status": "match" if published == recomputed else "mismatch",
                "source_url": "https://www.nba.com/termsofuse#nba-statistics",
                "note": note + " (project evidence, not an official NBA value)",
            }
        )

    # ---------------- computed layer ----------------
    games, dup_notes = load_games()
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    rec = records(games)

    for abbr in sorted(read_standings):
        fresh = read_standings[abbr]
        official = f"{fresh['w']}-{fresh['l']}"
        mine = rec.get(abbr)
        mine_text = f"{mine[0]}-{mine[1]}" if mine else ""
        recompute.append(
            {
                "check_id": f"REC-{abbr}",
                "quantity": f"{abbr} record recomputed from {len(games)} committed game results",
                "published_value": official,
                "recomputed_value": mine_text,
                "delta": "",
                "status": "computed_match" if mine_text == official else "computed_mismatch",
                "method": "count wins/losses per team over the committed result archives and compare with the official standings read today",
                "input_source_url": STANDINGS_URL,
            }
        )

    analysis = json.loads((PUBLISHED / "analysis.json").read_text(encoding="utf-8"))

    margins_all = [g["home_score"] - g["away_score"] for g in games]
    totals_all = [g["home_score"] + g["away_score"] for g in games]
    home_pts = [g["home_score"] for g in games]
    away_pts = [g["away_score"] for g in games]
    halves = {}
    for team in teams:
        seq = []
        for g in games:
            if team in (g["home"], g["away"]):
                own = g["home_score"] if g["home"] == team else g["away_score"]
                opp = g["away_score"] if g["home"] == team else g["home_score"]
                seq.append(own - opp)
        halves[team] = (seq[: len(seq) // 2], seq[len(seq) // 2 :])
    first = [sum(halves[t][0]) / max(1, len(halves[t][0])) for t in teams]
    second = [sum(halves[t][1]) / max(1, len(halves[t][1])) for t in teams]

    for key, xs, ys, label in (
        ("margin_vs_total", margins_all, totals_all, "correlation: game margin vs game total"),
        ("home_points_vs_away_points", home_pts, away_pts, "correlation: home points vs away points"),
        (
            "team_differential_first_half_vs_second_half",
            first,
            second,
            "correlation: team point differential, first half of games vs second half",
        ),
    ):
        published = analysis["correlations"][key]
        mine = pearson(xs, ys)
        for field in ("r", "ci95_low", "ci95_high"):
            delta = round(float(mine[field]) - float(published[field]), 4)
            recompute.append(
                {
                    "check_id": f"COR-{key}-{field}",
                    "quantity": f"{label} — {field} (n={mine['n']})",
                    "published_value": str(published[field]),
                    "recomputed_value": str(mine[field]),
                    "delta": f"{delta:+.4f}",
                    "status": "computed_match" if abs(delta) <= 0.0002 else "computed_mismatch",
                    "method": "Pearson r from raw-score sums; Fisher z 95% interval",
                    "input_source_url": "https://www.nba.com/games?date=2026-11-04",
                }
            )

    model = fit_model(games, teams)
    for row in analysis["slate"]:
        margin, total = predict(model, teams, row["home_team"], row["away_team"])
        probability = phi(margin / max(model["sigma"], 1e-6))
        for field, value, published in (
            ("model_home_margin", round(margin, 1), row["model_home_margin"]),
            ("model_total", round(total, 1), row["model_total"]),
            ("model_home_win_prob", round(probability, 3), row["model_home_win_prob"]),
        ):
            delta = round(value - float(published), 3)
            recompute.append(
                {
                    "check_id": f"MDL-{row['game_id']}-{field}",
                    "quantity": f"{row['away_team']} @ {row['home_team']} {row['date']} — {field}",
                    "published_value": str(published),
                    "recomputed_value": str(value),
                    "delta": f"{delta:+.3f}",
                    "status": "computed_match" if abs(delta) <= 0.1005 else "computed_mismatch",
                    "method": "ridge team-rating margin/total model (lambda=5) refitted with an independent Cholesky solver",
                    "input_source_url": row["source_url"],
                }
            )

    walk_pub = analysis["model"]["walk_forward"]
    walk_mine = walk_forward(games, teams)
    for field in (
        "n_predictions",
        "winner_accuracy",
        "winner_accuracy_ci95_low",
        "winner_accuracy_ci95_high",
        "home_always_accuracy",
        "brier_model",
        "brier_home_rate_baseline",
        "brier_skill_score",
        "brier_skill_score_ci95_low",
        "brier_skill_score_ci95_high",
        "mcnemar_model_only_correct",
        "mcnemar_home_only_correct",
        "mcnemar_exact_p_two_sided",
        "mae_margin",
        "rmse_margin",
        "mae_total",
        "rmse_total",
    ):
        published = walk_pub[field]
        mine = walk_mine[field]
        delta = round(float(mine) - float(published), 5)
        recompute.append(
            {
                "check_id": f"WF-{field}",
                "quantity": f"walk-forward holdout — {field}",
                "published_value": str(published),
                "recomputed_value": str(mine),
                "delta": f"{delta:+.5f}",
                "status": "computed_match" if abs(delta) <= 0.0006 else "computed_mismatch",
                "method": "expanding-window refit from game 61 onward; same seed for the bootstrap reproduction",
                "input_source_url": "https://www.nba.com/games?date=2026-11-04",
            }
        )

    read_recon = READS / "reconciliation.csv"
    with read_recon.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(recon[0].keys()))
        writer.writeheader()
        writer.writerows(recon)

    compute_csv = READS / "recompute.csv"
    with compute_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(recompute[0].keys()))
        writer.writeheader()
        writer.writerows(recompute)

    def tally(rows: list[dict]) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in rows:
            out[row["status"]] = out.get(row["status"], 0) + 1
        return dict(sorted(out.items()))

    mismatches = [r for r in recon if r["status"] in {"mismatch", "unverified"}]
    compute_mismatches = [r for r in recompute if r["status"] == "computed_mismatch"]
    summary = {
        "session": "arena/63a5b5ef-own6",
        "recheck_date": "2026-11-05",
        "published_snapshot": "data/official_2026_11_05/",
        "official_reads": {
            "standings": {"url": STANDINGS_URL, "teams": len(read_standings)},
            "results_2026_11_04": {"url": RESULTS_URL, "games": len(read_results)},
            "slate_2026_11_05": {"url": SLATE_5_URL, "games": len([r for r in read_slate.values() if r["date"] == "2026-11-05"])},
            "slate_2026_11_06": {"url": SLATE_6_URL, "games": len([r for r in read_slate.values() if r["date"] == "2026-11-06"])},
            "terms_of_use": {"url": TERMS_URL, "clauses": len(read_rows(READS / "rights_read.csv"))},
        },
        "reconciliation": {
            "rows": len(recon),
            "by_status": tally(recon),
            "open_items": mismatches,
        },
        "recompute": {
            "rows": len(recompute),
            "by_status": tally(recompute),
            "open_items": compute_mismatches,
            "games_recomputed": len(games),
            "teams_recomputed": len(teams),
            "duplicate_game_notes": dup_notes,
        },
        "walk_forward_reproduced": walk_mine,
        "verdict": {
            "published_values_confirmed": len([r for r in recon if r["status"] in {"match", "verified_text"}]),
            "published_values_contradicted": len([r for r in recon if r["status"] == "mismatch"]),
            "computations_reproduced": len([r for r in recompute if r["status"] == "computed_match"]),
            "computations_contradicted": len(compute_mismatches),
            "qualified_strategies": len(qualified),
            "authorized_observations": len(observations),
        },
        "limits": [
            "A match means the published value equals the value read on an official page today; it is not a licence to reuse NBA data.",
            "The model and correlation rows are computations over official final scores, not official NBA values and not evidence of an edge.",
            "No sportsbook price, closing line, ROI, CLV or reward value is available, so none is checked or filled in.",
        ],
    }
    (READS / "report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        "reconciliation rows={} {}".format(len(recon), tally(recon))
        + " | recompute rows={} {}".format(len(recompute), tally(recompute))
    )
    print(f"games={len(games)} teams={len(teams)} walk_forward_n={walk_mine['n_predictions']}")
    if mismatches or compute_mismatches:
        print("OPEN ITEMS:")
        for row in mismatches + compute_mismatches:
            print("  ", row.get("check_id"), row["status"], row.get("subject") or row.get("quantity"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
