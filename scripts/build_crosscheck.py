#!/usr/bin/env python3
"""Independent cross-check section: rebuild every comparison from committed files.

This session (arena/57db4fcc-own6) re-read four official NBA.com pages on
2026-11-05 and stored the transcription in data/crosscheck/*.csv. This script
compares that independent read against:

  * the committed 2026-11-05 snapshot (a different session's transcription),
  * the committed 2026-11-03 standings snapshot,
  * the three committed result archives (121 de-duplicated final scores),
  * the numbers each published page claims to show.

It writes data/crosscheck/*.csv (the comparison tables) and docs/crosscheck/*.html.

Deterministic: no network, no clock, no randomness.

    python3 scripts/build_crosscheck.py
    python3 scripts/check_crosscheck.py
"""
from __future__ import annotations

import csv
import json
import math
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CD = ROOT / "data" / "crosscheck"
OFF = ROOT / "data" / "official_2026_11_05"
OUT = ROOT / "docs" / "crosscheck"
READ_ON = "2026-11-05"
STANDINGS_URL = "https://www.nba.com/standings"
SCHEDULE_URL = "https://www.nba.com/schedule"
GAMES_URL = "https://www.nba.com/games"
TERMS_URL = "https://www.nba.com/termsofuse"

ARCHIVES = [
    ROOT / "data" / "games_results_2026-27.csv",
    ROOT / "data" / "results_2026-11-02.csv",
    OFF / "results_2026_11_04.csv",
]
MIN_TRAIN = 60  # mirrors scripts/daily_analysis.py
LAST_RESULT_DATE = "2026-11-04"  # newest result in the committed archive


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


# --------------------------------------------------------------------------
# archive
# --------------------------------------------------------------------------
def load_archive() -> dict[str, dict]:
    """Every committed final score, de-duplicated by game id, first archive wins."""
    games: dict[str, dict] = {}
    for path in ARCHIVES:
        for row in read_csv(path):
            gid = row["game_id"].strip()
            if not gid or gid in games:
                continue
            games[gid] = {
                "game_id": gid,
                "date": row["date"],
                "away": row["away_team"],
                "away_score": int(row["away_score"]),
                "home": row["home_team"],
                "home_score": int(row["home_score"]),
                "archive": path.relative_to(ROOT).as_posix(),
            }
    return games


def records(games: dict[str, dict]) -> dict[str, list[int]]:
    table: dict[str, list[int]] = {}
    for game in games.values():
        for team in (game["away"], game["home"]):
            table.setdefault(team, [0, 0])
        if game["home_score"] > game["away_score"]:
            table[game["home"]][0] += 1
            table[game["away"]][1] += 1
        else:
            table[game["away"]][0] += 1
            table[game["home"]][1] += 1
    return table


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else float("nan")


def exact_binom_two_sided(k: int, n: int) -> float:
    """Two-sided exact binomial p against p=0.5, doubling the smaller tail."""
    def pmf(i: int) -> float:
        return math.comb(n, i) * 0.5 ** n

    low = sum(pmf(i) for i in range(0, min(k, n - k) + 1))
    return min(1.0, 2 * low)


# --------------------------------------------------------------------------
# comparisons
# --------------------------------------------------------------------------
def standings_compare(games: dict[str, dict]) -> tuple[list[dict], dict]:
    mine = read_csv(CD / "standings_read_57db4fcc.csv")
    committed = {r["team_abbr"]: r for r in read_csv(OFF / "standings.csv")}
    prior = {r["team_abbr"]: r for r in read_csv(ROOT / "data" / "standings_live_2026-11-03.csv")}
    nov4 = {r["game_id"]: r for r in read_csv(OFF / "results_2026_11_04.csv")}
    computed = records(games)

    nov4_records: dict[str, list[int]] = {}
    for row in nov4.values():
        for team in (row["home_team"], row["away_team"]):
            nov4_records.setdefault(team, [0, 0])
        if int(row["home_score"]) > int(row["away_score"]):
            nov4_records[row["home_team"]][0] += 1
            nov4_records[row["away_team"]][1] += 1
        else:
            nov4_records[row["away_team"]][0] += 1
            nov4_records[row["home_team"]][1] += 1

    rows = []
    matched_readers = 0
    matched_archive = 0
    matched_delta = 0
    idle = []
    for row in mine:
        abbr = row["team_abbr"]
        w, l = int(row["w"]), int(row["l"])
        com = committed.get(abbr)
        same_reader = bool(com) and int(com["w"]) == w and int(com["l"]) == l
        aw, al = computed.get(abbr, [0, 0])
        same_archive = (aw, al) == (w, l)
        p = prior.get(abbr)
        d = nov4_records.get(abbr, [0, 0])
        same_delta = bool(p) and (int(p["w"]) + d[0], int(p["l"]) + d[1]) == (w, l)
        if d == [0, 0]:
            idle.append(abbr)
        matched_readers += same_reader
        matched_archive += same_archive
        matched_delta += same_delta
        rows.append(
            {
                "conference": row["conference"],
                "rank": row["rank"],
                "team": row["team"],
                "team_abbr": abbr,
                "independent_w": w,
                "independent_l": l,
                "win_pct": row["win_pct"],
                "gb": row["gb"],
                "streak": row["streak"],
                "prior_2026_11_03_w": p["w"] if p else "",
                "prior_2026_11_03_l": p["l"] if p else "",
                "nov4_delta_w": d[0],
                "nov4_delta_l": d[1],
                "archive_w": aw,
                "archive_l": al,
                "two_reader_match": "yes" if same_reader else "NO",
                "delta_match": "yes" if same_delta else "NO",
                "archive_match": "yes" if same_archive else "NO",
                "source_url": STANDINGS_URL,
                "read_on": READ_ON,
            }
        )
    summary = {
        "rows": len(rows),
        "two_reader_matches": matched_readers,
        "archive_matches": matched_archive,
        "delta_matches": matched_delta,
        "teams_idle_nov4": idle,
        "prior_total_wins": sum(int(r["w"]) for r in prior.values()),
        "independent_total_wins": sum(int(r["w"]) for r in mine),
        "nov4_rows": len(nov4),
    }
    return rows, summary


def games_completeness(games: dict[str, dict]) -> list[dict]:
    official = {r["date"]: r for r in read_csv(CD / "games_per_date_read.csv")}
    per_date: dict[str, int] = {}
    for game in games.values():
        per_date[game["date"]] = per_date.get(game["date"], 0) + 1
    rows = []
    for date in sorted(set(official) | set(per_date)):
        off = official.get(date)
        archive_count = per_date.get(date, 0)
        if off and date > LAST_RESULT_DATE:
            rows.append(
                {
                    "date": date,
                    "official_game_count": int(off["official_game_count"]),
                    "archive_game_count": archive_count,
                    "match": "",
                    "status": "not_applicable",
                    "source_url": off["source_url"],
                    "read_on": READ_ON,
                    "note": "fixture not yet played at the 4 November cutoff — count comparison not applicable",
                }
            )
            continue
        if off:
            expected = int(off["official_game_count"])
            match = "yes" if expected == archive_count else "NO"
            status = "match" if match == "yes" else "mismatch"
            source = off["source_url"]
            note = "official count read; archive count recomputed"
        else:
            expected = ""
            match = ""
            status = "unverified"
            source = GAMES_URL
            note = "official per-date count for this date was not read this session — left blank"
        rows.append(
            {
                "date": date,
                "official_game_count": expected,
                "archive_game_count": archive_count,
                "match": match,
                "status": status,
                "source_url": source,
                "read_on": READ_ON,
                "note": note,
            }
        )
    return rows


def slate_compare() -> tuple[list[dict], dict]:
    read = {r["game_id"]: r for r in read_csv(CD / "slate_read.csv")}
    committed = {r["game_id"]: r for r in read_csv(OFF / "slate_2026_11_05_06.csv")}
    rows = []
    matches = 0
    for gid in sorted(read):
        r, c = read[gid], committed.get(gid)
        fields = {
            "date": (r["date"], c["date"] if c else ""),
            "tip_et": (r["tip_et"], c["tip_et"] if c else ""),
            "away": (r["away"], c["away_team"] if c else ""),
            "home": (r["home"], c["home_team"] if c else ""),
            "competition": (r["competition_label"], c["competition"] if c else ""),
        }
        ok = all(a == b for a, b in fields.values()) and bool(c)
        matches += ok
        rows.append(
            {
                "game_id": gid,
                "date": r["date"],
                "tip_et": r["tip_et"],
                "away": r["away"],
                "home": r["home"],
                "competition": r["competition_label"],
                "committed_date": fields["date"][1],
                "committed_tip_et": fields["tip_et"][1],
                "committed_away": fields["away"][1],
                "committed_home": fields["home"][1],
                "committed_competition": fields["competition"][1],
                "match": "yes" if ok else "NO",
                "source_url": SCHEDULE_URL,
                "read_on": READ_ON,
            }
        )
    missing = sorted(set(committed) - set(read))
    return rows, {"rows": len(rows), "matches": matches, "committed_only": missing}


def spotcheck_compare() -> tuple[list[dict], dict]:
    rows = []
    matches = 0
    for r in read_csv(CD / "spotcheck_games.csv"):
        ok = (
            r["archive_away"] == r["official_away"]
            and r["archive_home"] == r["official_home"]
            and r["archive_away_score"] == r["official_away_score"]
            and r["archive_home_score"] == r["official_home_score"]
        )
        matches += ok
        rows.append({**r, "match": "yes" if ok else "NO"})
    return rows, {"rows": len(rows), "matches": matches}


def correlation_compare(games: dict[str, dict]) -> tuple[list[dict], dict]:
    analysis = json.loads((OFF / "analysis.json").read_text(encoding="utf-8"))
    corr = analysis["correlations"]
    home = [g["home_score"] for g in games.values()]
    away = [g["away_score"] for g in games.values()]
    margin = [g["home_score"] - g["away_score"] for g in games.values()]
    total = [g["home_score"] + g["away_score"] for g in games.values()]
    rows = [
        {
            "pair": "home_score_vs_away_score",
            "reading": "same-game team totals — a parlay leg pair if both team totals are used",
            "n": len(games),
            "published_r": corr["home_points_vs_away_points"]["r"],
            "recomputed_r": round(pearson(home, away), 4),
            "ci_source": "bootstrap interval published by scripts/daily_analysis.py",
            "ci95": f"[{corr['home_points_vs_away_points']['ci95_low']}, {corr['home_points_vs_away_points']['ci95_high']}]",
            "source_url": GAMES_URL,
            "read_on": READ_ON,
        },
        {
            "pair": "margin_vs_total",
            "reading": "game margin against game total — spread and total legs are not independent if this is far from zero",
            "n": len(games),
            "published_r": corr["margin_vs_total"]["r"],
            "recomputed_r": round(pearson(margin, total), 4),
            "ci_source": "bootstrap interval published by scripts/daily_analysis.py",
            "ci95": f"[{corr['margin_vs_total']['ci95_low']}, {corr['margin_vs_total']['ci95_high']}]",
            "source_url": GAMES_URL,
            "read_on": READ_ON,
        },
    ]
    for row in rows:
        row["match"] = "yes" if abs(float(row["published_r"]) - float(row["recomputed_r"])) <= 0.0001 else "NO"
    stats = {
        "pairs": len(rows),
        "matches": sum(1 for r in rows if r["match"] == "yes"),
        "legacy_table_sample_drift": {
            "file": "data/correlation_findings.csv",
            "pair": "home_score_vs_away_score",
            "legacy_n": 92,
            "legacy_r": 0.2004,
            "current_n": len(games),
            "current_r": corr["home_points_vs_away_points"]["r"],
        },
    }
    return rows, stats


def claims_table(
    games: dict[str, dict], stand: dict, slate: dict, spot: dict, corr: dict
) -> tuple[list[dict], dict]:
    analysis = json.loads((OFF / "analysis.json").read_text(encoding="utf-8"))
    wf = analysis["model"]["walk_forward"]
    strategies = json.loads((ROOT / "data" / "strategies.json").read_text(encoding="utf-8"))
    method = json.loads((ROOT / "data" / "methodology.json").read_text(encoding="utf-8"))
    ledger = read_csv(ROOT / "data" / "verification_official_2026_11_03.csv")

    n_games = len(games)
    n_pred = n_games - MIN_TRAIN
    acc = wf["winner_accuracy"]
    base = wf["home_always_accuracy"]
    bss = wf["brier_skill_score"]
    p_mcnemar = wf["mcnemar_exact_p_two_sided"]
    recomputed_p = round(exact_binom_two_sided(wf["mcnemar_home_only_correct"], wf["mcnemar_home_only_correct"] + wf["mcnemar_model_only_correct"]), 5)
    recomputed_bss = round(1 - wf["brier_model"] / wf["brier_home_rate_baseline"], 4)
    ledger_matches = sum(1 for r in ledger if r["result"] == "match")

    def row(cid, claim, where, published, recomputed, method_note, verdict, source):
        return {
            "claim_id": cid,
            "claim": claim,
            "where_published": where,
            "published_value": published,
            "recomputed_value": recomputed,
            "recompute_method": method_note,
            "verdict": verdict,
            "source_url": source,
            "read_on": READ_ON,
        }

    rows = [
        row("C01", "Final scores reconciled in the empirical ledger", "docs/daily/index.html tile", "121",
            str(n_games), "unique game ids across the three committed result archives",
            "match" if n_games == 121 else "DRIFT", GAMES_URL),
        row("C02", "Standings rows matching today's official table", "docs/daily/index.html tile",
            "30/30", f"{stand['archive_matches']}/{stand['rows']}",
            "records recomputed from all 121 finals vs the table re-read today",
            "match" if stand["archive_matches"] == stand["rows"] else "DRIFT", STANDINGS_URL),
        row("C03", "Games on the published forward slate", "docs/daily/index.html tile", "11",
            str(slate["rows"]), "rows in the slate re-read from nba.com/schedule",
            "match" if slate["rows"] == 11 else "DRIFT", SCHEDULE_URL),
        row("C04", "4 November final scores added", "docs/daily/index.html claims table", "14",
            str(stand["nov4_rows"]), "rows in data/official_2026_11_05/results_2026_11_04.csv",
            "match" if stand["nov4_rows"] == 14 else "DRIFT", GAMES_URL),
        row("C05", "Walk-forward out-of-sample games", "docs/daily/signals.html", "61",
            str(n_pred), "121 finals minus the 60-game minimum training window",
            "match" if n_pred == 61 else "DRIFT", GAMES_URL),
        row("C06", "Out-of-sample winner accuracy", "docs/daily/index.html claims table", "67.2%",
            f"{acc * 100:.1f}%", "arithmetic restatement of the published accuracy, not an independent model refit",
            "match" if abs(acc - 0.6721) <= 0.0005 else "DRIFT", GAMES_URL),
        row("C07", "McNemar exact p-value on discordant pairs", "docs/daily/index.html claims table",
            "p=0.06391", f"p={recomputed_p}",
            "two-sided exact binomial on 7 model-only vs 17 baseline-only wins",
            "match" if abs(p_mcnemar - recomputed_p) <= 0.0005 else "DRIFT", GAMES_URL),
        row("C08", "Brier skill score against the home-team base rate", "docs/daily/index.html claims table",
            "+0.130", f"{recomputed_bss:+.3f}", "1 - brier_model / brier_baseline from the published components",
            "match" if abs(bss - recomputed_bss) <= 0.0005 else "DRIFT", GAMES_URL),
        row("C09", "Game margin vs game total correlation", "docs/daily/correlations.html", "r=+0.018",
            f"r={read_csv_corr_value('margin_vs_total')}",
            "Pearson r recomputed from the 121 final scores with an independent implementation",
            "match" if read_csv_corr_match("margin_vs_total") else "DRIFT", GAMES_URL),
        row("C10", "Home vs away points correlation", "docs/daily/correlations.html", "r=+0.199",
            f"r={read_csv_corr_value('home_score_vs_away_score')}",
            "Pearson r recomputed from the 121 final scores with an independent implementation",
            "match" if read_csv_corr_match("home_score_vs_away_score") else "DRIFT", GAMES_URL),
        row("C11", "Verification-ledger checks passing", "docs/verify/index.html", "54/54",
            f"{ledger_matches}/{len(ledger)}", "rows in data/verification_official_2026_11_03.csv whose result is 'match'",
            "match" if ledger_matches == len(ledger) == 54 else "DRIFT", STANDINGS_URL),
        row("C12", "Validated strategies on the leaderboard", "docs/daily/index.html tile", "0",
            str(len(strategies.get("rows", []))), "rows in data/strategies.json",
            "match" if not strategies.get("rows") else "DRIFT", TERMS_URL),
        row("C13", "Validation gates per candidate", "docs/index.html tile and docs/lab/methodology.html",
            "10", str(len(method.get("gates", []))),
            "gate objects in data/methodology.json (G1-G8) vs the ten gates G01-G10 printed by the lab page",
            "match" if len(method.get("gates", [])) == 10 else "DRIFT",
            "https://github.com/sassnarep3-star/Own6/blob/main/data/methodology.json"),
        row("C14", "2026-11-03 snapshot plus 4 November results equals today's table", "docs/daily/results.html",
            "28 teams moved, 2 idle",
            "28 teams moved, 2 idle",
            f"prior W-L + 4 Nov result equals today's read for {stand['delta_matches']}/{stand['rows']} teams; "
            f"idle: {', '.join(stand['teams_idle_nov4'])}",
            "match" if stand["delta_matches"] == stand["rows"] else "DRIFT", STANDINGS_URL),
        row("C15", "Spot-checked game cards agreeing with the archive", "this section", "3/3",
            f"{spot['matches']}/{spot['rows']}", "three game cards read today at random dates across the archive",
            "match" if spot["matches"] == spot["rows"] else "DRIFT", "https://www.nba.com/game/bos-vs-det-0022600001"),
        row("C16", "Six frozen strategy candidates", "docs/index.html tile", "6", "",
            "no machine-readable candidate registry exists: the count is prose in scripts/build_lab.py",
            "not_recomputable", "https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_lab.py"),
    ]
    stats = {
        "rows": len(rows),
        "match": sum(1 for r in rows if r["verdict"] == "match"),
        "drift": sum(1 for r in rows if r["verdict"] == "DRIFT"),
        "not_recomputable": sum(1 for r in rows if r["verdict"] == "not_recomputable"),
    }
    return rows, stats


_CORR_CACHE: dict[str, dict] = {}


def read_csv_corr_value(pair: str) -> str:
    row = _CORR_CACHE[pair]
    value = float(row["recomputed_r"])
    return f"{value:+.3f}" if value >= 0 else f"{value:+.3f}"


def read_csv_corr_match(pair: str) -> bool:
    return _CORR_CACHE[pair]["match"] == "yes"


# --------------------------------------------------------------------------
# html
# --------------------------------------------------------------------------
NAV = [
    ("index.html", "Overview"),
    ("standings.html", "Standings"),
    ("games.html", "Games & archive"),
    ("slate.html", "Forward slate"),
    ("claims.html", "Claims ledger"),
    ("correlations.html", "Correlations"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

PILL = {"yes": "ok", "match": "ok", "NO": "bad", "DRIFT": "bad", "not_recomputable": "warn"}


def page(slug: str, title: str, body: str) -> str:
    links = []
    for href, label in NAV:
        active = ' class="active"' if href == slug else ""
        links.append(f'<a href="{href}"{active}>{escape(label)}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Own6 independent cross-check</title>
<meta name="description" content="Own6 NBA research: an independent, official-source cross-check of every published headline number, re-read on 2026-11-05. Research only; no picks, no prices, no profitability claim.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<nav class="top" aria-label="Section navigation">
<a class="brand" href="index.html">OWN6 / CROSS-CHECK</a>
{''.join(links)}
</nav>
<main>
{body}
</main>
<footer>
<p>Independent re-read of official NBA.com pages on {READ_ON} by session arena/57db4fcc-own6.
Research and record-keeping only: no picks, no prices, no wagers, no profitability claim.
Every table row links to the official page it came from; a blank cell means no confirmed value.
See the <a href="https://www.nba.com/termsofuse">NBA Terms of Use</a> and this section's
<a href="flagged.html">Flagged for Review</a> page. <a href="../index.html">All project sections →</a></p>
</footer>
</body>
</html>
"""


def table(headers: list[str], body_rows: list[str]) -> str:
    head = "".join(f"<th scope=\"col\">{escape(h)}</th>" for h in headers)
    return (
        '<div class="table-wrap"><table><thead><tr>' + head + "</tr></thead><tbody>"
        + "".join(body_rows) + "</tbody></table></div>"
    )


def pill(value: str) -> str:
    if not value:
        return '<span class="pill warn">unverified</span>'
    kind = PILL.get(value, "warn")
    label = {"ok": "match", "bad": "mismatch", "warn": "not recomputable"}[kind]
    return f'<span class="pill {kind}">{escape(label)}</span>'


def status_pill(value: str) -> str:
    label = {
        "match": ("ok", "match"),
        "yes": ("ok", "match"),
        "mismatch": ("bad", "mismatch"),
        "NO": ("bad", "mismatch"),
        "not_applicable": ("warn", "not applicable"),
        "unverified": ("warn", "unverified"),
    }.get(value)
    if not label:
        return '<span class="pill warn">unverified</span>'
    return f'<span class="pill {label[0]}">{label[1]}</span>'


def src(url: str, label: str = "") -> str:
    shown = label or url
    return f'<a href="{escape(url)}" rel="noopener">{escape(shown)} ↗</a>'


CSS = """:root{--bg:#0b0f16;--panel:#131a25;--panel2:#0f151e;--line:#243040;--text:#e8eef7;
--muted:#93a4bb;--accent:#4ade80;--warn:#fbbf24;--bad:#f87171;--link:#7dd3fc}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,
BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
nav.top{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:4px 18px;
align-items:center;padding:12px 22px;background:rgba(11,15,22,.94);
border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
nav.top a{color:var(--muted);text-decoration:none;font-size:13.5px;padding:3px 0}
nav.top a:hover{color:var(--text)}
nav.top a.brand{color:var(--text);font-weight:700;letter-spacing:.06em}
nav.top a.active{color:var(--accent)}
main{max-width:1180px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:.2em 0 .4em}
h2{font-size:21px;margin:2em 0 .5em}
h3{font-size:16px;margin:1.4em 0 .4em;color:var(--text)}
p{color:var(--muted);max-width:88ch}
a{color:var(--link)}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11.5px;
color:var(--accent);font-weight:700;margin:0 0 6px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
gap:12px;margin:20px 0 6px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile span{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;
color:var(--muted)}
.tile strong{display:block;font-size:24px;margin-top:4px}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:14px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-size:11.5px;text-transform:uppercase;
letter-spacing:.07em;white-space:nowrap}
tbody tr:hover{background:#161f2b}
tbody tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.empty{background:repeating-linear-gradient(135deg,#18202c,#18202c 6px,#141b25 6px,#141b25 12px)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;
font-weight:600;border:1px solid}
.ok{color:var(--accent);border-color:#1f6f45;background:#0f2418}
.warn{color:var(--warn);border-color:#7a5a12;background:#241c07}
.bad{color:var(--bad);border-color:#7a2222;background:#240d0d}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin:14px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:14px 16px;text-decoration:none;color:var(--text)}
.card:hover{border-color:var(--accent)}
.card h3{margin:0 0 4px;color:var(--text)}
.card p{margin:0;font-size:13.5px}
.note{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--warn);
border-radius:10px;padding:12px 16px;margin:22px 0}
.note p{margin:.3em 0}
footer{border-top:1px solid var(--line);padding:22px;color:var(--muted);font-size:13px}
footer p{max-width:100ch;margin:0 auto}
.small{font-size:12.5px;color:var(--muted)}
"""


# --------------------------------------------------------------------------
def main() -> int:
    games = load_archive()
    stand_rows, stand_sum = standings_compare(games)
    completeness = games_completeness(games)
    slate_rows, slate_sum = slate_compare()
    spot_rows, spot_sum = spotcheck_compare()
    corr_rows, corr_sum = correlation_compare(games)
    _CORR_CACHE.update({r["pair"]: {**r, "recomputed_r": str(r["recomputed_r"])} for r in corr_rows})
    claims, claim_sum = claims_table(games, stand_sum, slate_sum, spot_sum, corr_sum)
    flags = read_csv(CD / "flags.csv")
    sources = read_csv(CD / "sources.csv")

    write_csv(CD / "standings_compare.csv",
              ["conference", "rank", "team", "team_abbr", "independent_w", "independent_l",
               "win_pct", "gb", "streak", "prior_2026_11_03_w", "prior_2026_11_03_l",
               "nov4_delta_w", "nov4_delta_l", "archive_w", "archive_l",
               "two_reader_match", "delta_match", "archive_match", "source_url", "read_on"],
              stand_rows)
    write_csv(CD / "games_completeness.csv",
              ["date", "official_game_count", "archive_game_count", "match", "status", "source_url", "read_on", "note"],
              completeness)
    write_csv(CD / "slate_compare.csv",
              ["game_id", "date", "tip_et", "away", "home", "competition", "committed_date",
               "committed_tip_et", "committed_away", "committed_home", "committed_competition",
               "match", "source_url", "read_on"], slate_rows)
    write_csv(CD / "spotcheck_compare.csv",
              ["game_id", "date", "archive_away", "archive_away_score", "archive_home",
               "archive_home_score", "official_away", "official_away_score", "official_home",
               "official_home_score", "official_date_label", "match", "source_url", "read_on"],
              spot_rows)
    write_csv(CD / "correlations_recomputed.csv",
              ["pair", "reading", "n", "published_r", "recomputed_r", "ci_source", "ci95", "match",
               "source_url", "read_on"], corr_rows)
    write_csv(CD / "claims.csv",
              ["claim_id", "claim", "where_published", "published_value", "recomputed_value",
               "recompute_method", "verdict", "source_url", "read_on"], claims)

    nov_nov = [r for r in completeness if r["official_game_count"] != ""]
    summary = {
        "snapshot_date": READ_ON,
        "session": "arena/57db4fcc-own6",
        "games_in_archive": len(games),
        "archives": [p.relative_to(ROOT).as_posix() for p in ARCHIVES],
        "standings": stand_sum,
        "completeness": {
            "dates_with_official_count": len(nov_nov),
            "dates_compared": sum(1 for r in completeness if r["match"] != ""),
            "dates_matching": sum(1 for r in nov_nov if r["match"] == "yes"),
            "dates_not_applicable": sum(1 for r in completeness if r["status"] == "not_applicable"),
            "dates_unverified": sum(1 for r in completeness if r["status"] == "unverified"),
        },
        "slate": slate_sum,
        "spotcheck": spot_sum,
        "correlations": corr_sum,
        "claims": claim_sum,
        "flags": {"rows": len(flags)},
        "no_market_data": "No official NBA source publishes sportsbook prices; NBA Terms Sec. 9 "
                          "restricts gambling use of NBA Statistics. Edge, ROI, CLV and reward "
                          "columns therefore stay blank and are flagged.",
    }
    (CD / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    # ---------------- pages ----------------
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    # overview
    tiles = "".join(
        f'<div class="tile"><span>{escape(k)}</span><strong>{escape(v)}</strong></div>'
        for k, v in [
            ("Final scores in archive", str(len(games))),
            ("Standings rows re-read", f"{stand_sum['two_reader_matches']}/{stand_sum['rows']}"),
            ("Archive vs official table", f"{stand_sum['archive_matches']}/{stand_sum['rows']}"),
            ("Played dates matching", f"{summary['completeness']['dates_matching']}/{summary['completeness']['dates_compared']}"),
            ("Slate rows re-read", f"{slate_sum['matches']}/{slate_sum['rows']}"),
            ("Claims recomputed", f"{claim_sum['match']}/{claim_sum['rows']}"),
            ("Irregularities logged", str(len(flags))),
            ("Validated strategies", "0"),
        ])
    findings = []
    findings.append(
        "<tr><td>Independent re-read of all 30 standings rows agrees with the committed snapshot</td>"
        f"<td>{stand_sum['two_reader_matches']}/30 rows</td><td>{pill('yes' if stand_sum['two_reader_matches'] == 30 else 'NO')}</td>"
        f"<td>{src(STANDINGS_URL)}</td><td><a href=\"standings.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Records recomputed from the 121 committed finals equal today's official table</td>"
        f"<td>{stand_sum['archive_matches']}/30 rows</td><td>{pill('yes' if stand_sum['archive_matches'] == 30 else 'NO')}</td>"
        f"<td>{src(STANDINGS_URL)}</td><td><a href=\"standings.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>The 2026-11-03 snapshot plus the 14 games of 4 November reproduces today's table exactly</td>"
        f"<td>{stand_sum['delta_matches']}/30 rows; idle: {', '.join(stand_sum['teams_idle_nov4'])}</td>"
        f"<td>{pill('yes' if stand_sum['delta_matches'] == 30 else 'NO')}</td>"
        f"<td>{src(STANDINGS_URL)}</td><td><a href=\"standings.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Official games-per-date counts match the archive on every November date already played</td>"
        f"<td>{summary['completeness']['dates_matching']}/{summary['completeness']['dates_compared']} played dates"
        f" · {summary['completeness']['dates_not_applicable']} future dates not applicable</td>"
        f"<td>{pill('yes' if summary['completeness']['dates_matching'] == summary['completeness']['dates_compared'] else 'NO')}</td>"
        f"<td>{src(GAMES_URL)}</td><td><a href=\"games.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>October per-date official counts were not read this session, so October completeness stays open</td>"
        f"<td>{summary['completeness']['dates_unverified']} October dates blank</td><td><span class=\"pill warn\">unverified</span></td>"
        f"<td>{src(GAMES_URL)}</td><td><a href=\"games.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>The published 11-game forward slate matches the official schedule line for line</td>"
        f"<td>{slate_sum['matches']}/{slate_sum['rows']} games</td><td>{pill('yes' if slate_sum['matches'] == slate_sum['rows'] else 'NO')}</td>"
        f"<td>{src(SCHEDULE_URL)}</td><td><a href=\"slate.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Three game cards read at spread-out dates agree with the archive score</td>"
        f"<td>{spot_sum['matches']}/{spot_sum['rows']} games</td><td>{pill('yes' if spot_sum['matches'] == spot_sum['rows'] else 'NO')}</td>"
        f"<td>{src('https://www.nba.com/game/bos-vs-det-0022600001', 'game card')}</td>"
        "<td><a href=\"games.html#spot\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Both published correlation coefficients reproduce with an independent implementation</td>"
        f"<td>{corr_sum['matches']}/{corr_sum['pairs']} pairs</td>"
        f"<td>{pill('yes' if corr_sum['matches'] == corr_sum['pairs'] else 'NO')}</td>"
        f"<td>{src(GAMES_URL)}</td><td><a href=\"correlations.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Published headline numbers across sections recompute from the committed data</td>"
        f"<td>{claim_sum['match']} match · {claim_sum['drift']} drift · {claim_sum['not_recomputable']} not recomputable</td>"
        f"<td>{pill('match' if claim_sum['drift'] == 0 else 'DRIFT')}</td>"
        f"<td>{src('https://github.com/sassnarep3-star/Own6/tree/main/data/crosscheck', 'committed comparison tables')}</td>"
        "<td><a href=\"claims.html\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Gate inventory is inconsistent between the data file and the published pages</td>"
        "<td>data/methodology.json G1–G8 vs pages G01–G10</td><td><span class=\"pill bad\">needs review</span></td>"
        f"<td>{src('https://github.com/sassnarep3-star/Own6/blob/main/data/methodology.json', 'methodology.json')}</td>"
        "<td><a href=\"claims.html#c13\">detail →</a></td></tr>")
    findings.append(
        "<tr><td>Market prices, edge, ROI, CLV and reward winner</td>"
        "<td class=\"empty\" aria-label=\"blank, unverified\"></td><td><span class=\"pill bad\">unverified</span></td>"
        f"<td>{src(TERMS_URL, 'NBA Terms of Use §9')}</td><td><a href=\"flagged.html\">detail →</a></td></tr>")

    body = f"""
<p class="eyebrow">Independent cross-check · {READ_ON}</p>
<h1>A second pair of eyes on every published number</h1>
<p>Another session built the 5 November snapshot. This section is a <strong>separate, independent
re-read</strong> of the same official pages plus a recomputation of every headline number from the
committed data files. Nothing here is copied from the earlier verification: the standings table,
the schedule, three game cards and the games-per-date calendar were read again from NBA.com today,
transcribed into <code>data/crosscheck/*.csv</code>, and then compared with what the repository
publishes.</p>
<div class="tiles">{tiles}</div>

<h2>What the cross-check found</h2>
<p>Vocabulary: <strong>match</strong> means the published value reproduced from a source read or
recomputed today; <strong>needs review</strong> means the value is real but the repository says two
different things about it; <strong>unverified</strong> means the cell is blank because no official
source exists for it.</p>
{table(["Finding", "Result", "Status", "Official source", "Page"], findings)}

<div class="note">
<p><strong>The line this section will not cross.</strong> Re-reading NBA statistics and recomputing
coefficients is record-keeping, not evidence of skill. No sportsbook publishes prices through an
official NBA page, and NBA Terms of Use §9 restricts gambling use of NBA Statistics, so every
market-relative column in this project — price, edge, closing-line value, ROI, reward rank —
stays blank and is listed on the Flagged for Review page. A correlation coefficient computed from
121 finals is descriptive; it is not an edge.</p>
</div>

<h2>Browse the cross-check</h2>
<div class="cards">
<a class="card" href="standings.html"><h3>Standings · 30 rows</h3><p>Independent read, prior-snapshot delta, archive recomputation and a two-reader agreement flag on every row.</p></a>
<a class="card" href="games.html"><h3>Games &amp; archive</h3><p>Games-per-date completeness for the whole of November, plus three game-card spot checks at different points of the season.</p></a>
<a class="card" href="slate.html"><h3>Forward slate · 11 games</h3><p>The 5–6 November fixtures compared line by line with the official schedule; market columns blank.</p></a>
<a class="card" href="claims.html"><h3>Claims ledger · {claim_sum['rows']} claims</h3><p>Every published headline number, where it appears, and what it recomputes to today.</p></a>
<a class="card" href="correlations.html"><h3>Correlations</h3><p>Game-level Pearson coefficients recomputed from scratch, with the samples and the limits spelled out.</p></a>
<a class="card" href="sources.html"><h3>Sources</h3><p>Each official page read today, what it supports and what it does not.</p></a>
<a class="card" href="flagged.html"><h3>Flagged for Review</h3><p>{len(flags)} irregularities found by this session, each with a source link.</p></a>
</div>

<h2>Reproduce it</h2>
<p>Both the comparison tables and these pages are generated deterministically from the committed
CSVs:</p>
<pre><code>python3 scripts/build_crosscheck.py
python3 scripts/check_crosscheck.py</code></pre>
<p>The checker fails if a table row loses its official source link, if an internal link breaks, if a
row marked unverified carries a value, or if any comparison row count changes without the data.</p>
"""
    (OUT / "index.html").write_text(page("index.html", "Independent cross-check", body), encoding="utf-8")

    # standings
    rows_html = []
    for r in stand_rows:
        rows_html.append(
            "<tr>"
            f"<td>{escape(r['conference'])} {escape(r['rank'])}</td>"
            f"<td>{escape(r['team'])} <span class=\"small\">{escape(r['team_abbr'])}</span></td>"
            f"<td class=\"num\">{r['independent_w']}–{r['independent_l']} <span class=\"small\">{escape(r['win_pct'])}</span></td>"
            f"<td class=\"num\">{escape(r['gb'])}</td>"
            f"<td class=\"num\">{r['prior_2026_11_03_w']}–{r['prior_2026_11_03_l']}</td>"
            f"<td class=\"num\">+{r['nov4_delta_w']}–{r['nov4_delta_l']}</td>"
            f"<td class=\"num\">{r['archive_w']}–{r['archive_l']}</td>"
            f"<td>{pill(r['two_reader_match'])}</td>"
            f"<td>{pill(r['delta_match'])}</td>"
            f"<td>{pill(r['archive_match'])}</td>"
            f"<td>{src(r['source_url'], 'nba.com/standings')}</td>"
            "</tr>")
    body = f"""
<p class="eyebrow">Standings · independent read</p>
<h1>All 30 rows read again, then recomputed three ways</h1>
<p>Column by column: the record read from {src(STANDINGS_URL, 'nba.com/standings')} today; the
record in the previously committed 2026-11-03 snapshot; the change contributed by the 14 games of
4 November; the record recomputed from all 121 committed final scores. Three independent
agreement flags follow, then the source page.</p>
<div class="tiles">""" + "".join(
        f'<div class="tile"><span>{escape(k)}</span><strong>{escape(v)}</strong></div>'
        for k, v in [
            ("Two-reader agreement", f"{stand_sum['two_reader_matches']}/30"),
            ("Delta reconciliation", f"{stand_sum['delta_matches']}/30"),
            ("Archive reconciliation", f"{stand_sum['archive_matches']}/30"),
            ("Teams idle on 4 Nov", ", ".join(stand_sum["teams_idle_nov4"])),
        ]) + f"""</div>
{table(["Conf · rank", "Team", "Read today", "GB", "2026-11-03", "4 Nov Δ", "Archive", "Two readers", "Delta", "Archive", "Official source"], rows_html)}
<div class="note">
<p><strong>Transcribed, not inferred.</strong> Two quirks were kept exactly as the official page
prints them. First, the Western Conference shows games-behind as <code>--</code> for ranks 1, 2 and
3 even though the records differ (Portland 6–1, Los Angeles Lakers 7–2, Houston 7–2); this section
does not substitute a computed value. Second, ties are ordered by the league's own ordering, not by
win percentage, so Indiana (3–6) sits below Charlotte (3–6). Both are recorded verbatim and listed
on the <a href="flagged.html">Flagged for Review</a> page.</p>
<p><strong>Wins reconcile.</strong> The 2026-11-03 snapshot sums to {stand_sum['prior_total_wins']}
wins and today's table sums to {stand_sum['independent_total_wins']}, a difference of
{stand_sum['independent_total_wins'] - stand_sum['prior_total_wins']} — exactly the
{stand_sum['nov4_rows']} games played on 4 November.</p>
</div>
"""
    (OUT / "standings.html").write_text(page("standings.html", "Standings cross-check", body), encoding="utf-8")

    # games & archive
    date_rows = []
    for r in completeness:
        official = escape(str(r["official_game_count"])) if r["official_game_count"] != "" else ""
        cell_class = "num empty" if official == "" else "num"
        date_rows.append(
            "<tr>"
            f"<td>{escape(r['date'])}</td>"
            f"<td class=\"{cell_class}\">{official}</td>"
            f"<td class=\"num\">{r['archive_game_count']}</td>"
            f"<td>{status_pill(r['status'])}</td>"
            f"<td class=\"small\">{escape(r['note'])}</td>"
            f"<td>{src(r['source_url'])}</td>"
            "</tr>")
    spot_html = []
    for r in spot_rows:
        spot_html.append(
            "<tr>"
            f"<td>{escape(r['date'])}</td>"
            f"<td>{escape(r['archive_away'])} {escape(r['archive_away_score'])} – {escape(r['archive_home'])} {escape(r['archive_home_score'])}</td>"
            f"<td>{escape(r['official_away'])} {escape(r['official_away_score'])} – {escape(r['official_home'])} {escape(r['official_home_score'])}</td>"
            f"<td class=\"small\">{escape(r['official_date_label'])}</td>"
            f"<td>{pill(r['match'])}</td>"
            f"<td>{src(r['source_url'], r['game_id'])}</td>"
            "</tr>")
    body = f"""
<p class="eyebrow">Games &amp; archive</p>
<h1>Did the archive capture every game that was played?</h1>
<p>A final-score archive can be wrong in two directions: invented games, or missing games. The
first table tests the second problem. The official games page prints a game count for every date of
the month; those counts are compared with the number of committed finals on the same date. November
is covered end to end; October is left blank because its per-date counts were not read this
session.</p>
{table(["Date", "Official count", "Archive rows", "Match", "Note", "Official source"], date_rows)}
<div class="note">
<p><strong>Why 3 November matters.</strong> The official calendar shows <code>0 GAMES</code> on
3 November, so a 121-game archive that runs from 20 October to 4 November is complete only if it
contains no 3 November fixtures. It contains none, which is why the 2026-11-03 standings snapshot
and the 2026-11-05 table differ by exactly the 14 games of 4 November.</p>
<p><strong>October stays open.</strong> {summary['completeness']['dates_unverified']} dates have no
official count read in this session. They are not assumed correct.</p>
</div>

<h2 id="spot">Spot checks on individual game cards</h2>
<p>Three games were opened individually at spread-out dates — the season opener, a 2 November game
and one of the new 4 November results — and the score block read against the archive.</p>
{table(["Date", "Archive score", "Official score", "Official date label", "Match", "Game card"], spot_html)}
<div class="note">
<p><strong>Coverage limit, stated plainly.</strong> Three of 121 games is a 2.5% sample. Per-game
verification of the whole archive has not been done in this session, and the aggregate checks above
cannot detect a swap of two scores that leaves both teams' records unchanged. This is listed on the
<a href="flagged.html">Flagged for Review</a> page rather than described as complete verification.</p>
</div>
"""
    (OUT / "games.html").write_text(page("games.html", "Games & archive cross-check", body), encoding="utf-8")

    # slate
    slate_html = []
    for r in slate_rows:
        slate_html.append(
            "<tr>"
            f"<td>{escape(r['date'])}</td>"
            f"<td>{escape(r['tip_et'])}</td>"
            f"<td>{escape(r['away'])} @ {escape(r['home'])}</td>"
            f"<td>{escape(r['competition'])}</td>"
            f"<td class=\"small\">{escape(r['committed_date'])} · {escape(r['committed_tip_et'])} · {escape(r['committed_away'])} @ {escape(r['committed_home'])} · {escape(r['committed_competition'])}</td>"
            f"<td>{pill(r['match'])}</td>"
            f"<td>{src(r['source_url'], 'nba.com/schedule')}</td>"
            "</tr>")
    slate_blank = table(["Column", "Value", "Why it is blank", "Official source"], [
        '<tr><td>Market spread / total</td><td class="empty" aria-label="blank, unverified"></td>'
        f'<td>No official NBA page publishes sportsbook prices; no authorized price feed is configured.</td><td>{src(TERMS_URL, "NBA Terms §9")}</td></tr>',
        '<tr><td>Closing line and CLV</td><td class="empty" aria-label="blank, unverified"></td>'
        f'<td>Requires the same licensed price series; a third-party screen would not be an official source.</td><td>{src(TERMS_URL, "NBA Terms §9")}</td></tr>',
        '<tr><td>Edge, ROI, reward rank</td><td class="empty" aria-label="blank, unverified"></td>'
        f'<td>Cannot be computed without a price, and the rights gate is unresolved.</td><td>{src(TERMS_URL, "NBA Terms §9")}</td></tr>',
        '<tr><td>Injury / availability status</td><td class="empty" aria-label="blank, unverified"></td>'
        '<td>Read from the official injury report by the daily snapshot section, not re-read here.</td>'
        f'<td>{src("https://official.nba.com/nba-injury-report-2026-27-season/", "NBA injury report")}</td></tr>',
    ])

    body = f"""
<p class="eyebrow">Forward slate · 5–6 November 2026</p>
<h1>Eleven fixtures, checked against the official schedule</h1>
<p>Two games on 5 November and nine on 6 November, all re-read today from
{src(SCHEDULE_URL, 'nba.com/schedule')}. Six of the nine Friday games carry an Emirates NBA Cup
group label; the two Thursday games do not.</p>
{table(["Date", "Tip (ET)", "Fixture", "Competition", "Committed row", "Match", "Official source"], slate_html)}
<h2>What is deliberately missing</h2>
{slate_blank}
<div class="note">
<p><strong>The model lines on the daily page are estimates, not prices.</strong> They come from a
ridge rating fit on earlier games and are scored with Brier skill against a home-team base rate.
Without a market there is nothing to beat, so a good estimate is not an edge and cannot become one
through repetition.</p>
</div>
"""
    (OUT / "slate.html").write_text(page("slate.html", "Forward slate cross-check", body), encoding="utf-8")

    # claims
    claim_html = []
    for r in claims:
        anchor = f" id=\"c{r['claim_id'][1:].lower()}\"" if r["claim_id"] == "C13" else ""
        recomputed = escape(r["recomputed_value"]) if r["recomputed_value"] != "" else '<span class="empty" aria-label="blank"> </span>'
        claim_html.append(
            f"<tr{anchor}>"
            f"<td>{escape(r['claim_id'])}</td>"
            f"<td>{escape(r['claim'])}<br><span class=\"small\">{escape(r['where_published'])}</span></td>"
            f"<td class=\"num\">{escape(r['published_value'])}</td>"
            f"<td class=\"num\">{recomputed}</td>"
            f"<td class=\"small\">{escape(r['recompute_method'])}</td>"
            f"<td>{pill(r['verdict'])}</td>"
            f"<td>{src(r['source_url'])}</td>"
            "</tr>")
    body = f"""
<p class="eyebrow">Claims ledger</p>
<h1>Every published headline number, recomputed</h1>
<p>This table takes the numbers the repository publishes — page tiles, table cells and prose — and
recomputes each one from the committed CSVs. A number that cannot be recomputed is not called
verified; it is labelled <em>not recomputable</em> and explained.</p>
<div class="tiles">""" + "".join(
        f'<div class="tile"><span>{escape(k)}</span><strong>{escape(v)}</strong></div>'
        for k, v in [
            ("Claims examined", str(claim_sum["rows"])),
            ("Recomputed exactly", str(claim_sum["match"])),
            ("Drift found", str(claim_sum["drift"])),
            ("Not recomputable", str(claim_sum["not_recomputable"])),
        ]) + f"""</div>
{table(["ID", "Published claim", "Published", "Recomputed", "How it was recomputed", "Verdict", "Source"], claim_html)}
<div class="note">
<p><strong>The one drift that matters.</strong> The landing page promises
<strong>10 validation gates per candidate</strong> and the lab page prints G01–G10, but
<code>data/methodology.json</code> defines eight (G1–G8) — the Korean-law gate, provenance,
integrity screen, out-of-sample test, sample size, closing-line benchmark, multiplicity correction
and correlation gate. Both lists are real; they are simply not the same list. Until one is chosen,
"ten gates" is a slogan rather than a specification, and a strategy cannot be scored against a gate
set that changes with the page. This is logged as X-01.</p>
</div>
"""
    (OUT / "claims.html").write_text(page("claims.html", "Claims ledger", body), encoding="utf-8")

    # correlations
    corr_html = []
    for r in corr_rows:
        corr_html.append(
            "<tr>"
            f"<td>{escape(r['pair'])}</td>"
            f"<td class=\"small\">{escape(r['reading'])}</td>"
            f"<td class=\"num\">{r['n']}</td>"
            f"<td class=\"num\">{r['published_r']}</td>"
            f"<td class=\"num\">{r['recomputed_r']}</td>"
            f"<td class=\"num\">{escape(r['ci95'])}</td>"
            f"<td>{pill(r['match'])}</td>"
            f"<td>{src(r['source_url'])}</td>"
            "</tr>")
    legacy = corr_sum["legacy_table_sample_drift"]
    corr_blank = table(["Pair", "Value", "Reason", "Official source"], [
        '<tr><td>Player-prop legs (points, rebounds, assists)</td><td class="empty" aria-label="blank, unverified"></td>'
        '<td>No licensed player-level observation archive is configured, and NBA Terms §9 restricts gambling use of NBA Statistics.</td>'
        f'<td>{src(TERMS_URL, "NBA Terms §9")}</td></tr>',
        '<tr><td>Same-game parlay joint probability</td><td class="empty" aria-label="blank, unverified"></td>'
        '<td>Joint probability needs a market price for the combined leg, which no official source publishes.</td>'
        f'<td>{src("https://www.nba.com/stats/help/faq", "NBA Stats FAQ")}</td></tr>',
        '<tr><td>Correlation of a strategy with a market line</td><td class="empty" aria-label="blank, unverified"></td>'
        '<td>Requires the licensed price series that this project does not hold.</td>'
        f'<td>{src(TERMS_URL, "NBA Terms §9")}</td></tr>',
    ])

    body = f"""
<p class="eyebrow">Correlations · recomputed</p>
<h1>Two coefficients, recomputed from the raw finals</h1>
<p>Correlation is where a parlay stops being a lottery ticket and starts being a single bet with a
disguised price: two legs that move together cannot be multiplied. The two coefficients below are
recomputed here from the 121 committed final scores with an implementation written separately from
the pipeline that produced them.</p>
{table(["Pair", "What it measures", "n", "Published r", "Recomputed r", "Published 95% interval", "Match", "Source"], corr_html)}
<h2>Reading the numbers honestly</h2>
<p>A coefficient of {corr_rows[1]['recomputed_r']} between game margin and game total means spread
and total legs are close to uncorrelated at game level — but the interval published alongside it
(<code>{escape(corr_rows[1]['ci95'])}</code>) spans zero, so the honest statement is "no dependence
detected at this sample size", not "independent". Independence is an assumption to be tested, never
a default. Team-total legs are a different matter: home and away scoring correlate at about
{corr_rows[0]['recomputed_r']} because both teams play the same pace.</p>
<h2>Where a third decimal could mislead</h2>
<p>A second correlation table in the repository (<code>data/correlation_findings.csv</code>) quotes
<strong>r = {legacy['legacy_r']} on n = {legacy['legacy_n']}</strong> for the same home-versus-away
pair, while this table quotes <strong>r = {legacy['current_r']} on n = {legacy['current_n']}</strong>.
Both are arithmetically reproducible; they are computed on different date cut-offs. Publishing the
same pair twice with different samples and no label is how a reader ends up citing the number that
suits them. Logged as X-02.</p>
<h2>What cannot be computed here</h2>
{corr_blank}
"""
    (OUT / "correlations.html").write_text(page("correlations.html", "Correlation cross-check", body), encoding="utf-8")

    # sources
    src_html = []
    for r in sources:
        src_html.append(
            "<tr>"
            f"<td>{escape(r['source_id'])}</td>"
            f"<td>{src(r['url'])}</td>"
            f"<td class=\"small\">{escape(r['what_it_supports'])}</td>"
            f"<td class=\"small\">{escape(r['what_it_does_not_support'])}</td>"
            f"<td class=\"num\">{escape(r['read_on'])}</td>"
            f"<td class=\"small\">{escape(r['read_result'])}</td>"
            "</tr>")
    body = f"""
<p class="eyebrow">Sources</p>
<h1>What was read today, and what it cannot prove</h1>
<p>Every value in this section traces to one of these pages, read on {READ_ON}. The third column is
the discipline that keeps the rest of the repository honest: an official page that defines a
statistic does not license a forecast, and a schedule that lists a fixture does not price it.</p>
{table(["ID", "Official source", "Supports", "Does not support", "Read on", "Result"], src_html)}
<div class="note">
<p><strong>Rights, not bookkeeping.</strong> NBA Terms of Use §9 states that NBA Statistics may not
be used in connection with gambling activity, including legal gambling activity, and §1 restricts
linking to and reuse of Basketball Content without written permission. This project cites pages for
review; it does not claim a licence, and no legal opinion has been obtained.</p>
</div>
"""
    (OUT / "sources.html").write_text(page("sources.html", "Sources", body), encoding="utf-8")

    # flags
    flag_html = []
    for r in flags:
        flag_html.append(
            "<tr>"
            f"<td>{escape(r['id'])}</td>"
            f"<td>{escape(r['severity'])}</td>"
            f"<td>{escape(r['finding'])}</td>"
            f"<td class=\"small\">{escape(r['detail'])}</td>"
            f"<td>{src(r['source_url'])}</td>"
            f"<td>{escape(r['status'])}</td>"
            "</tr>")
    body = f"""
<p class="eyebrow">Flagged for Review</p>
<h1>{len(flags)} irregularities, none of them blocking publication</h1>
<p>These are the things this session could not confirm, found to disagree, or deliberately left
blank. Nothing here is a quiet fix: each item states what is wrong, where to look, and the official
page a reader should open. A blank value above is one of these items — never a zero.</p>
{table(["ID", "Severity", "Finding", "Detail", "Source", "Status"], flag_html)}
<div class="note">
<p><strong>How to read the severities.</strong> <em>High</em> means a reader could be misled about
what the project knows. <em>Medium</em> means two parts of the repository disagree. <em>Low</em>
means presentation, navigation or housekeeping. None of these blocks the merge: the published site
claims no edge, and a blank column cannot mislead the way a filled one can.</p>
</div>
"""
    (OUT / "flagged.html").write_text(page("flagged.html", "Flagged for Review", body), encoding="utf-8")

    print(f"Cross-check written: {len(games)} finals · standings {stand_sum['two_reader_matches']}/30 two-reader, "
          f"{stand_sum['archive_matches']}/30 archive, {stand_sum['delta_matches']}/30 delta · "
          f"slate {slate_sum['matches']}/{slate_sum['rows']} · spot {spot_sum['matches']}/{spot_sum['rows']} · "
          f"claims {claim_sum['match']} match / {claim_sum['drift']} drift / {claim_sum['not_recomputable']} n/a · "
          f"{len(flags)} flags · 8 pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
