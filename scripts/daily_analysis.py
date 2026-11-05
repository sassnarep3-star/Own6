#!/usr/bin/env python3
"""Deterministic, dependency-free analysis for the 2026-11-05 verified snapshot.

Everything here is computed from committed CSVs whose values were read from
official NBA.com pages. The script does three separate jobs:

1. Consistency checks that tie the three committed result archives to the two
   dated official standings snapshots (2026-11-03 and 2026-11-05).
2. A walk-forward margin/total rating model with honest out-of-sample scoring
   (Brier skill against a home-team base rate, bootstrap interval, exact
   binomial test). There is no market comparison, so no edge or ROI is claimed.
3. Descriptive correlation estimates from official final scores only.

Nothing is scraped. Re-run with: python3 scripts/daily_analysis.py
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "official_2026_11_05" / "analysis.json"

RIDGE = 5.0
MIN_TRAIN = 60
BOOT = 2000
SEED = 20261105


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_games() -> list[dict]:
    """Chronological, de-duplicated game list from the three result archives."""
    games: list[dict] = []
    seen: set[str] = set()
    sources = [
        ROOT / "data" / "games_results_2026-27.csv",
        ROOT / "data" / "results_2026-11-02.csv",
        ROOT / "data" / "official_2026_11_05" / "results_2026_11_04.csv",
    ]
    for path in sources:
        for row in read_rows(path):
            gid = row.get("game_id", "").strip()
            if not gid or gid in seen:
                continue
            seen.add(gid)
            games.append(
                {
                    "game_id": gid,
                    "date": row["date"],
                    "away": row["away_team"],
                    "away_score": int(row["away_score"]),
                    "home": row["home_team"],
                    "home_score": int(row["home_score"]),
                    "source_url": row["source_url"],
                    "archive": path.relative_to(ROOT).as_posix(),
                }
            )
    games.sort(key=lambda g: (g["date"], g["game_id"]))
    return games


def record(games: list[dict]) -> dict[str, list[int]]:
    table: dict[str, list[int]] = {}
    for game in games:
        for team in (game["away"], game["home"]):
            table.setdefault(team, [0, 0])
        home_won = game["home_score"] > game["away_score"]
        table[game["home"]][0 if home_won else 1] += 1
        table[game["away"]][1 if home_won else 0] += 1
    return table


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gauss-Jordan with partial pivoting."""
    size = len(vector)
    aug = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular normal equations")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        lead = aug[col][col]
        aug[col] = [value / lead for value in aug[col]]
        for row in range(size):
            if row == col:
                continue
            factor = aug[row][col]
            if factor:
                aug[row] = [a - factor * b for a, b in zip(aug[row], aug[col])]
    return [aug[i][size] for i in range(size)]


def ridge(features: list[list[float]], target: list[float], penalise: list[bool]) -> list[float]:
    width = len(features[0])
    xtx = [[0.0] * width for _ in range(width)]
    xty = [0.0] * width
    for row, y in zip(features, target):
        for i, a in enumerate(row):
            if a == 0.0:
                continue
            xty[i] += a * y
            for j, b in enumerate(row):
                if b:
                    xtx[i][j] += a * b
    for i in range(width):
        if penalise[i]:
            xtx[i][i] += RIDGE
    return solve(xtx, xty)


def design(games: list[dict], teams: list[str]) -> tuple[list[list[float]], list[list[float]]]:
    index = {team: i for i, team in enumerate(teams)}
    margin_rows: list[list[float]] = []
    total_rows: list[list[float]] = []
    for game in games:
        row = [0.0] * (len(teams) + 1)
        row[index[game["home"]]] = 1.0
        row[index[game["away"]]] = -1.0
        row[-1] = 1.0  # home advantage, unpenalised
        margin_rows.append(row)
        trow = [0.0] * (len(teams) + 1)
        trow[index[game["home"]]] = 1.0
        trow[index[game["away"]]] = 1.0
        trow[-1] = 1.0  # intercept, unpenalised
        total_rows.append(trow)
    return margin_rows, total_rows


def fit(games: list[dict], teams: list[str]) -> dict:
    margins = [g["home_score"] - g["away_score"] for g in games]
    totals = [g["home_score"] + g["away_score"] for g in games]
    mrows, trows = design(games, teams)
    penal = [True] * len(teams) + [False]
    mbeta = ridge(mrows, margins, penal)
    tbeta = ridge(trows, [float(t) for t in totals], penal)
    residuals = [m - sum(a * b for a, b in zip(row, mbeta)) for row, m in zip(mrows, margins)]
    sigma = math.sqrt(sum(r * r for r in residuals) / max(1, len(residuals) - 1))
    tresiduals = [t - sum(a * b for a, b in zip(row, tbeta)) for row, t in zip(trows, totals)]
    tsigma = math.sqrt(sum(r * r for r in tresiduals) / max(1, len(tresiduals) - 1))
    return {
        "margin": mbeta,
        "total": tbeta,
        "sigma": sigma,
        "tsigma": tsigma,
        "home_win_rate": sum(1 for m in margins if m > 0) / len(margins),
        "games": len(games),
    }


def predict(model: dict, teams: list[str], home: str, away: str) -> tuple[float, float]:
    index = {team: i for i, team in enumerate(teams)}
    margin = model["margin"][index[home]] - model["margin"][index[away]] + model["margin"][-1]
    total = model["total"][index[home]] + model["total"][index[away]] + model["total"][-1]
    return margin, total


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def brier(probabilities: list[float], outcomes: list[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(outcomes)


def pearson(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    r = sxy / math.sqrt(sxx * syy) if sxx > 0 < syy else 0.0
    r = max(-0.999999, min(0.999999, r))
    z = math.atanh(r)
    half = 1.96 / math.sqrt(max(1, n - 3))
    return {
        "n": n,
        "r": round(r, 4),
        "ci95_low": round(math.tanh(z - half), 4),
        "ci95_high": round(math.tanh(z + half), 4),
    }


def exact_binomial_p(successes: int, trials: int) -> float:
    """Two-sided exact binomial test against p=0.5."""
    if trials == 0:
        return 1.0
    tail = sum(math.comb(trials, k) for k in range(0, min(successes, trials - successes) + 1))
    return min(1.0, 2 * tail / 2 ** trials)


def walk_forward(games: list[dict], teams: list[str]) -> dict:
    margins, totals, probs, base_probs, outcomes, picks, actual_totals = [], [], [], [], [], [], []
    for i in range(MIN_TRAIN, len(games)):
        train = games[:i]
        model = fit(train, teams)
        game = games[i]
        margin, total = predict(model, teams, game["home"], game["away"])
        p = phi(margin / max(model["sigma"], 1e-6))
        outcomes.append(1 if game["home_score"] > game["away_score"] else 0)
        probs.append(p)
        base_probs.append(model["home_win_rate"])
        margins.append(game["home_score"] - game["away_score"] - margin)
        totals.append(game["home_score"] + game["away_score"] - total)
        actual_totals.append(game["home_score"] + game["away_score"])
        picks.append((margin > 0) == (game["home_score"] > game["away_score"]))
    wins = sum(picks)
    home_wins = sum(outcomes)
    model_only = sum(1 for pk, y in zip(picks, outcomes) if pk and not y)
    base_only = sum(1 for pk, y in zip(picks, outcomes) if (not pk) and y)
    discordant = model_only + base_only
    mcnemar_p = exact_binomial_p(min(model_only, base_only), discordant) if discordant else 1.0
    bs = brier(probs, outcomes)
    bsb = brier(base_probs, outcomes)
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
    return {
        "first_predicted_game": games[MIN_TRAIN]["game_id"],
        "n_predictions": len(outcomes),
        "mae_margin": round(sum(abs(e) for e in margins) / len(margins), 3),
        "rmse_margin": round(math.sqrt(sum(e * e for e in margins) / len(margins)), 3),
        "mae_total": round(sum(abs(e) for e in totals) / len(totals), 3),
        "rmse_total": round(math.sqrt(sum(e * e for e in totals) / len(totals)), 3),
        "winner_accuracy": round(wins / len(picks), 4),
        "winner_accuracy_ci95_low": round(_wilson(wins, len(picks))[0], 4),
        "winner_accuracy_ci95_high": round(_wilson(wins, len(picks))[1], 4),
        "winner_accuracy_exact_p_two_sided": round(exact_binomial_p(wins, len(picks)), 5),
        "home_always_accuracy": round(home_wins / len(outcomes), 4),
        "accuracy_vs_home_always": round(wins / len(picks) - home_wins / len(outcomes), 4),
        "mcnemar_model_only_correct": model_only,
        "mcnemar_home_only_correct": base_only,
        "mcnemar_exact_p_two_sided": round(mcnemar_p, 5),
        "brier_model": round(bs, 4),
        "brier_home_rate_baseline": round(bsb, 4),
        "brier_skill_score": round(1.0 - bs / bsb, 4),
        "brier_skill_score_ci95_low": round(boots[int(0.025 * BOOT)], 4),
        "brier_skill_score_ci95_high": round(boots[int(0.975 * BOOT) - 1], 4),
        "mean_actual_total": round(sum(actual_totals) / len(actual_totals), 1),
        "note": "No market prices are used, so this cannot establish a betting edge or ROI.",
    }


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    z = 1.96
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def available(roster: list[str]) -> list[str]:
    return [t for t in roster if t not in ("ORL", "GSW")] if False else roster


def main() -> int:
    games = load_games()
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    today = read_rows(ROOT / "data" / "official_2026_11_05" / "standings.csv")
    prior = read_rows(ROOT / "data" / "standings_live_2026-11-03.csv")

    # --- consistency chain -------------------------------------------------
    nov2 = read_rows(ROOT / "data" / "results_2026-11-02.csv")
    nov4 = read_rows(ROOT / "data" / "official_2026_11_05" / "results_2026_11_04.csv")
    cutoff = [g for g in games if g["date"] <= "2026-11-02"]
    rec107 = record(cutoff)
    rec121 = record(games)

    def compare(table: dict[str, list[int]], snapshot: list[dict[str, str]]) -> list[dict]:
        rows = []
        for row in snapshot:
            abbr = row["team_abbr"]
            official = [int(row["w"]), int(row["l"])]
            local = table.get(abbr, [0, 0])
            rows.append(
                {
                    "team_abbr": abbr,
                    "official_w": official[0],
                    "official_l": official[1],
                    "recomputed_w": local[0],
                    "recomputed_l": local[1],
                    "match": local == official,
                    "source_url": row["source_url"],
                }
            )
        return rows

    cmp_today = compare(rec121, today)
    cmp_prior = compare(rec107, prior)

    # Nov-4 delta: every team that played moved by exactly one result, no team twice.
    played: dict[str, int] = {}
    for row in nov4:
        played[row["home_team"]] = played.get(row["home_team"], 0) + 1
        played[row["away_team"]] = played.get(row["away_team"], 0) + 1
    delta_rows = []
    for row in today:
        abbr = row["team_abbr"]
        before = rec107.get(abbr, [0, 0])
        after = [int(row["w"]), int(row["l"])]
        delta_rows.append(
            {
                "team_abbr": abbr,
                "w_before": before[0],
                "l_before": before[1],
                "w_after": after[0],
                "l_after": after[1],
                "delta_games": (after[0] + after[1]) - (before[0] + before[1]),
                "played_nov4": played.get(abbr, 0),
                "source_url": row["source_url"],
            }
        )

    # --- model -------------------------------------------------------------
    walk = walk_forward(games, teams)
    final = fit(games, teams)
    slate = read_rows(ROOT / "data" / "official_2026_11_05" / "slate_2026_11_05_06.csv")
    slate_rows = []
    for row in slate:
        margin, total = predict(final, teams, row["home_team"], row["away_team"])
        slate_rows.append(
            {
                "game_id": row["game_id"],
                "date": row["date"],
                "tip_et": row["tip_et"],
                "away_team": row["away_team"],
                "home_team": row["home_team"],
                "competition": row["competition"],
                "model_home_margin": round(margin, 1),
                "model_margin_low80": round(margin - 1.2816 * final["sigma"], 1),
                "model_margin_high80": round(margin + 1.2816 * final["sigma"], 1),
                "model_total": round(total, 1),
                "model_total_low80": round(total - 1.2816 * final["tsigma"], 1),
                "model_total_high80": round(total + 1.2816 * final["tsigma"], 1),
                "model_home_win_prob": round(phi(margin / max(final["sigma"], 1e-6)), 3),
                "source_url": row["source_url"],
            }
        )

    # --- descriptive correlations -----------------------------------------
    margins_all = [g["home_score"] - g["away_score"] for g in games]
    totals_all = [g["home_score"] + g["away_score"] for g in games]
    home_pts = [g["home_score"] for g in games]
    away_pts = [g["away_score"] for g in games]

    # split-half persistence of team point differential (luck vs skill probe)
    halves: dict[str, list[list[int]]] = {}
    for team in teams:
        seq = []
        for g in games:
            if team in (g["home"], g["away"]):
                own = g["home_score"] if g["home"] == team else g["away_score"]
                opp = g["away_score"] if g["home"] == team else g["home_score"]
                seq.append([own - opp])
        halves[team] = [seq[: len(seq) // 2], seq[len(seq) // 2:]]
    first = [sum(x[0] for x in halves[t][0]) / max(1, len(halves[t][0])) for t in teams]
    second = [sum(x[0] for x in halves[t][1]) / max(1, len(halves[t][1])) for t in teams]

    analysis = {
        "snapshot_date": "2026-11-05",
        "sources": {
            "standings": "https://www.nba.com/standings",
            "games_feed": "https://www.nba.com/games?date=2026-11-04",
            "slate": "https://www.nba.com/game/orl-vs-phx-0022600187",
        },
        "consistency": {
            "games_total": len(games),
            "teams_total": len(teams),
            "games_through_2026_11_02": len(cutoff),
            "rows_through_2026_11_02": len(nov2) + len([g for g in games if g["date"] < "2026-11-02"]),
            "nov4_rows": len(nov4),
            "standings_2026_11_05_matches": sum(1 for r in cmp_today if r["match"]),
            "standings_2026_11_05_total": len(cmp_today),
            "standings_2026_11_03_matches": sum(1 for r in cmp_prior if r["match"]),
            "standings_2026_11_03_total": len(cmp_prior),
            "teams_in_nov4_delta": sum(1 for r in delta_rows if r["delta_games"] == 1),
            "teams_idle_nov4": sorted(r["team_abbr"] for r in delta_rows if r["delta_games"] == 0),
            "compare_today": cmp_today,
            "compare_prior": cmp_prior,
        },
        "model": {
            "type": "ridge team-rating margin/total model with home advantage",
            "ridge_lambda": RIDGE,
            "min_training_games": MIN_TRAIN,
            "final_sigma_margin": round(final["sigma"], 3),
            "final_sigma_total": round(final["tsigma"], 3),
            "training_home_win_rate": round(final["home_win_rate"], 4),
            "ratings": {team: round(final["margin"][i], 2) for i, team in enumerate(teams)},
            "home_advantage_points": round(final["margin"][-1], 2),
            "total_effects": {team: round(final["total"][i], 2) for i, team in enumerate(teams)},
            "walk_forward": walk,
        },
        "correlations": {
            "margin_vs_total": pearson(margins_all, totals_all),
            "home_points_vs_away_points": pearson(home_pts, away_pts),
            "team_differential_first_half_vs_second_half": pearson(first, second),
            "prop_or_player_level": None,
            "prop_note": "No licensed player-level observation archive is configured; values left blank and flagged.",
        },
        "slate": slate_rows,
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(ROOT)} — games={len(games)} "
        f"standings {analysis['consistency']['standings_2026_11_05_matches']}/30 (today), "
        f"{analysis['consistency']['standings_2026_11_03_matches']}/30 (2026-11-03), "
        f"walk-forward n={walk['n_predictions']}, BSS={walk['brier_skill_score']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
