#!/usr/bin/env python3
"""Integrity checker for the 2026-11-05 verified snapshot section.

Validates, without any network access:
  * the snapshot CSVs (row counts, arithmetic, unique IDs, official HTTPS links),
  * the reconciliation claims in analysis.json against a fresh recomputation,
  * the generated HTML (internal links, one official link per table row, blank
    market cells, no leaked None/NaN, deterministic rebuild).

Exit code 0 means the snapshot is internally consistent and every published row
is source-linked. It is NOT proof that a cited page says what we claim; that is
what `audit/SESSION_27fdbe09.md` records, page by page.
"""
from __future__ import annotations

import csv
import html.parser
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "official_2026_11_05"
DOCS = ROOT / "docs" / "daily"
OFFICIAL_HOSTS = {"www.nba.com", "official.nba.com"}
NAV_PAGES = [
    "index.html", "standings.html", "results.html", "slate.html", "signals.html",
    "correlations.html", "validation.html", "sources.html", "flagged.html",
]


class Rows(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.in_tbody = False
        self.in_row = False
        self.row_links: list[str] = []
        self.rows: list[list[str]] = []
        self.row_cells = 0
        self.empty_cells = 0
        self.cells: list[str] = []
        self._cell_depth = 0

    def handle_starttag(self, tag, attrs):
        attrmap = dict(attrs)
        for key in ("href", "src"):
            if attrmap.get(key):
                self.links.append(attrmap[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []
            self.row_cells = 0
            self.empty_cells = 0
        elif tag == "td" and self.in_row:
            self.row_cells += 1
            if "empty" in (attrmap.get("class") or ""):
                self.empty_cells += 1
        elif tag == "a" and self.in_row and attrmap.get("href"):
            self.row_links.append(attrmap["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append([str(self.row_cells), str(self.empty_cells), *self.row_links])
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def official(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS


def check_data() -> list[str]:
    issues: list[str] = []
    standings = read(DATA / "standings.csv")
    results = read(DATA / "results_2026_11_04.csv")
    slate = read(DATA / "slate_2026_11_05_06.csv")

    if len(standings) != 30:
        issues.append(f"standings.csv: expected 30 rows, found {len(standings)}")
    wins = sum(int(r["w"]) for r in standings)
    losses = sum(int(r["l"]) for r in standings)
    if wins != losses:
        issues.append(f"standings.csv: wins {wins} != losses {losses} (impossible records)")
    if len({r["team_abbr"] for r in standings}) != 30:
        issues.append("standings.csv: duplicate or missing team abbreviations")
    for row in standings:
        if not official(row["source_url"]):
            issues.append(f"standings.csv: {row['team_abbr']} has no official source link")
        if not row["w"].isdigit() or not row["l"].isdigit():
            issues.append(f"standings.csv: {row['team_abbr']} has a non-integer record")

    if len(results) != 14:
        issues.append(f"results_2026_11_04.csv: expected 14 rows, found {len(results)}")
    if len({r["game_id"] for r in results}) != len(results):
        issues.append("results_2026_11_04.csv: duplicate game IDs")
    for row in results:
        if not official(row["source_url"]):
            issues.append(f"results_2026_11_04.csv: {row['game_id']} has no official source link")
        if row["game_id"] not in row["source_url"]:
            issues.append(f"results_2026_11_04.csv: {row['game_id']} source URL does not contain the game ID")
        if row["away_score"] == row["home_score"]:
            issues.append(f"results_2026_11_04.csv: {row['game_id']} is a tie, which the NBA does not allow")

    if len(slate) != 11:
        issues.append(f"slate_2026_11_05_06.csv: expected 11 rows, found {len(slate)}")
    for row in slate:
        if not official(row["source_url"]):
            issues.append(f"slate: {row['game_id']} has no official source link")
        if row["game_id"] not in row["source_url"]:
            issues.append(f"slate: {row['game_id']} source URL does not contain the game ID")
        if not row["tip_et"].endswith("ET"):
            issues.append(f"slate: {row['game_id']} tip time is not labelled ET")
        for field in ("market_spread", "market_total", "market_price"):
            if row.get(field):
                issues.append(f"slate: {row['game_id']} carries a {field} value with no official source")
    return issues


def check_analysis() -> list[str]:
    issues: list[str] = []
    data = json.loads((DATA / "analysis.json").read_text(encoding="utf-8"))

    sys.path.insert(0, str(ROOT / "scripts"))
    import daily_analysis  # noqa: PLC0415  (local import keeps the checker standalone)

    games = daily_analysis.load_games()
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    today = read(DATA / "standings.csv")
    prior = read(ROOT / "data" / "standings_live_2026-11-03.csv")
    rec = daily_analysis.record(games)
    cutoff = [g for g in games if g["date"] <= "2026-11-02"]
    rec107 = daily_analysis.record(cutoff)

    def matches(table, snapshot):
        return sum(
            1 for row in snapshot
            if table.get(row["team_abbr"]) == [int(row["w"]), int(row["l"])]
        )

    cons = data["consistency"]
    checks = [
        ("games_total", cons["games_total"], len(games)),
        ("teams_total", cons["teams_total"], len(teams)),
        ("standings_2026_11_05_matches", cons["standings_2026_11_05_matches"], matches(rec, today)),
        ("standings_2026_11_03_matches", cons["standings_2026_11_03_matches"], matches(rec107, prior)),
        ("games_through_2026_11_02", cons["games_through_2026_11_02"], len(cutoff)),
    ]
    for name, published, recomputed in checks:
        if published != recomputed:
            issues.append(f"analysis.json: {name} is {published}, recomputation gives {recomputed}")
    if cons["standings_2026_11_05_matches"] != cons["standings_2026_11_05_total"]:
        issues.append("analysis.json: today's standings do not reconcile to the game archive")
    if cons["standings_2026_11_03_matches"] != cons["standings_2026_11_03_total"]:
        issues.append("analysis.json: the 2026-11-03 snapshot does not reconcile to the archive")

    walk = data["model"]["walk_forward"]
    if not 0.0 <= walk["winner_accuracy"] <= 1.0:
        issues.append("analysis.json: winner_accuracy is not a probability")
    if not (walk["brier_skill_score_ci95_low"] <= walk["brier_skill_score"] <= walk["brier_skill_score_ci95_high"]):
        issues.append("analysis.json: Brier skill point estimate is outside its own interval")
    if walk["n_predictions"] != len(games) - data["model"]["min_training_games"]:
        issues.append("analysis.json: walk-forward prediction count does not match the training cutoff")

    if len(data["slate"]) != 11:
        issues.append("analysis.json: slate forecast count is not 11")
    for row in data["slate"]:
        if not (0.0 < row["model_home_win_prob"] < 1.0):
            issues.append(f"analysis.json: {row['game_id']} home-win probability is not in (0,1)")
        if not (row["model_margin_low80"] <= row["model_home_margin"] <= row["model_margin_high80"]):
            issues.append(f"analysis.json: {row['game_id']} margin is outside its 80% band")

    props = data["correlations"]["prop_or_player_level"]
    if props is not None:
        issues.append("analysis.json: player-level correlation has a value but no licensed source exists")
    return issues


def check_html(rebuild: bool = True) -> list[str]:
    issues: list[str] = []
    for name in NAV_PAGES:
        path = DOCS / name
        if not path.is_file():
            issues.append(f"docs/daily/{name}: missing page")
            continue
        text = path.read_text(encoding="utf-8")
        if "<generator object" in text:
            issues.append(f"docs/daily/{name}: leaked Python repr")
        for bad in (">None<", ">nan<", ">NaN<", ">NaN</td>", "TODO", "???"):
            if bad in text:
                issues.append(f"docs/daily/{name}: contains placeholder token {bad!r}")
        parser = Rows()
        parser.feed(text)
        if not parser.rows:
            issues.append(f"docs/daily/{name}: no table rows found")
        for index, row in enumerate(parser.rows, start=1):
            cells, empty = int(row[0]), int(row[1])
            links = row[2:]
            if cells == 0:
                issues.append(f"docs/daily/{name}: row {index} has no cells")
            if not any(official(link) for link in links):
                issues.append(f"docs/daily/{name}: row {index} has no official HTTPS source link")
            if name == "slate.html" and empty < 2:
                issues.append(f"docs/daily/{name}: row {index} does not keep market cells blank")
        for link_url in parser.links:
            parsed = urlparse(link_url)
            if parsed.scheme in {"https", "mailto"}:
                continue
            if parsed.scheme:
                issues.append(f"docs/daily/{name}: insecure or unsupported link {link_url}")
                continue
            if not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                issues.append(f"docs/daily/{name}: broken internal link {link_url}")

    # Blank-unverified rule: no market number may appear on the slate page.
    slate_text = (DOCS / "slate.html").read_text(encoding="utf-8")
    if "Market spread</th>" not in slate_text or "Market total</th>" not in slate_text:
        issues.append("docs/daily/slate.html: market columns are missing from the table header")

    if not rebuild:
        return issues

    # Determinism: rebuilding must reproduce byte-identical pages.
    snapshot = {p.name: p.read_bytes() for p in DOCS.glob("*.html")}
    css_before = (DOCS / "assets" / "style.css").read_bytes()
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_daily  # noqa: PLC0415

    import contextlib
    import io

    with contextlib.redirect_stdout(io.StringIO()):
        build_daily.OUT = DOCS
        build_daily.main()
    for name, before in snapshot.items():
        after = (DOCS / name).read_bytes()
        if before != after:
            issues.append(f"docs/daily/{name}: rebuild is not deterministic")
    if (DOCS / "assets" / "style.css").read_bytes() != css_before:
        issues.append("docs/daily/assets/style.css: rebuild is not deterministic")
    return issues


def main() -> int:
    issues = check_data() + check_analysis() + check_html()
    for issue in issues:
        print("FAIL", issue)
    print(f"Daily snapshot check: {len(NAV_PAGES)} pages, "
          f"{len(issues)} issue(s). Source links and blanks only — not factual re-verification.")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
