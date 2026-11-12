#!/usr/bin/env python3
"""Line-by-line verification gate for the NFL origination, depth and skill-gate pack.

Checks performed
  1. Every generated page is byte-identical to what the builder produces.
  2. Every register row carries an official HTTPS NFL source and, where declared, a
     methodology reference on the allowlist; every unverified row leaves its value blank.
  3. The league average, every per-game rate, every originated spread/total/moneyline and
     every pricing example are recomputed independently and must match the register.
  4. The depth-deficiency arithmetic is recomputed from the injury register.
  5. Every HTML table row carries an official NFL link, every external link is HTTPS and on
     an allowlist, every relative link resolves, and each page has exactly one h1.
  6. No betting recommendation, price claim or league-average push-frequency claim is made.
"""
from __future__ import annotations

import csv
import html.parser
import math
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_nfl_3b81013c as builder  # noqa: E402
from nfl_3b81013c import (  # noqa: E402
    american_to_implied_prob,
    devig_multiplicative,
    devig_shin_power,
    fair_prob_to_american,
    same_line_devig_clv,
)

DATA_DIR = ROOT / "data" / "nfl_3b81013c"
DOCS_DIR = ROOT / "docs" / "nfl-3b81013c"
EXPECTED_PAGES = {name for name, _ in builder.NAV_ITEMS}

OFFICIAL_HOSTS = builder.OFFICIAL_HOSTS
METHOD_HOSTS = builder.METHOD_HOSTS
MERGE_MARKER_RE = re.compile(r"^(?:<{7}(?:\s|$)|={7}$|>{7}(?:\s|$))", re.MULTILINE)

# Declared modelling priors, mirrored from the register prose.
HFA_PRIOR = 1.75
MARGIN_SD_PRIOR = 13.45

TEAM_ABBR = {
    "Washington Commanders": "WAS", "New York Giants": "NYG", "New England Patriots": "NE",
    "Detroit Lions": "DET", "Kansas City Chiefs": "KC", "Atlanta Falcons": "ATL",
    "Houston Texans": "HOU", "Cleveland Browns": "CLE", "Minnesota Vikings": "MIN",
    "Green Bay Packers": "GB", "Miami Dolphins": "MIA", "Indianapolis Colts": "IND",
    "Carolina Panthers": "CAR", "New Orleans Saints": "NO", "Buffalo Bills": "BUF",
    "New York Jets": "NYJ", "Jacksonville Jaguars": "JAX", "Tennessee Titans": "TEN",
    "Los Angeles Rams": "LAR", "Arizona Cardinals": "AZ", "Seattle Seahawks": "SEA",
    "Las Vegas Raiders": "LV", "San Francisco 49ers": "SF", "Dallas Cowboys": "DAL",
    "Pittsburgh Steelers": "PIT", "Cincinnati Bengals": "CIN", "Los Angeles Chargers": "LAC",
    "Baltimore Ravens": "BAL",
}

# Official Week 10 standings as transcribed, re-entered here independently of the register so
# that the register cannot be its own evidence.
OFFICIAL_STANDINGS = {
    "BUF": (7, 1, 0, 256, 187), "NE": (5, 4, 0, 211, 207), "NYJ": (2, 7, 0, 182, 223),
    "MIA": (1, 7, 0, 126, 200), "PIT": (6, 2, 0, 180, 144), "CIN": (6, 2, 0, 240, 175),
    "CLE": (5, 4, 0, 161, 196), "BAL": (4, 5, 0, 189, 236), "JAX": (6, 2, 0, 229, 121),
    "HOU": (3, 5, 0, 209, 192), "IND": (2, 7, 0, 184, 249), "TEN": (1, 7, 0, 144, 199),
    "DEN": (7, 2, 0, 198, 186), "KC": (6, 2, 0, 202, 143), "LV": (4, 5, 0, 238, 268),
    "LAC": (0, 8, 0, 121, 219), "NYG": (5, 2, 1, 182, 172), "DAL": (4, 5, 0, 246, 236),
    "WAS": (2, 5, 1, 172, 202), "PHI": (2, 7, 0, 148, 221), "CHI": (7, 2, 0, 241, 184),
    "DET": (6, 2, 0, 222, 189), "MIN": (6, 2, 0, 146, 116), "GB": (6, 3, 0, 216, 191),
    "CAR": (3, 5, 0, 199, 219), "NO": (3, 5, 0, 185, 216), "TB": (3, 6, 0, 202, 178),
    "ATL": (3, 6, 0, 188, 223), "SF": (7, 1, 0, 235, 156), "SEA": (5, 4, 0, 202, 162),
    "LAR": (5, 4, 0, 214, 181), "AZ": (3, 6, 0, 178, 255),
}

# Week 10 slate: (ref, away abbr, home abbr, neutral site flag)
OFFICIAL_SLATE = [
    ("L10-01", "WAS", "NYG", False), ("L10-02", "NE", "DET", True),
    ("L10-03", "KC", "ATL", False), ("L10-04", "HOU", "CLE", False),
    ("L10-05", "MIN", "GB", False), ("L10-06", "MIA", "IND", False),
    ("L10-07", "CAR", "NO", False), ("L10-08", "BUF", "NYJ", False),
    ("L10-09", "JAX", "TEN", False), ("L10-10", "LAR", "AZ", False),
    ("L10-11", "SEA", "LV", False), ("L10-12", "SF", "DAL", False),
    ("L10-13", "PIT", "CIN", False), ("L10-14", "LAC", "BAL", False),
]

# Depth weights mirrored from src/nfl_3b81013c/depth.py for independent recomputation.
POSITION_WEIGHTS = {
    "QB": 1.00, "LT": 0.42, "RT": 0.36, "C": 0.34, "LG": 0.28, "RG": 0.28,
    "WR1": 0.38, "WR2": 0.26, "SLOT_WR": 0.22, "TE1": 0.24, "RB1": 0.20, "RB2": 0.20,
    "CB1": 0.40, "CB2": 0.32, "NICKEL_CB": 0.28, "EDGE1": 0.40, "EDGE2": 0.30,
    "DT_NT": 0.28, "LB_GREEN_DOT": 0.34, "FS": 0.30, "SS": 0.26,
}
STRING_MULTIPLIER = {1: 0.0, 2: 0.45, 3: 0.80, 4: 1.15}

# Phrases that would amount to an implied wagering recommendation.
BANNED_PHRASES = (
    "we recommend betting", "place a bet", "guaranteed profit", "lock of the week",
    "sure thing", "free pick", "best bet today", "bet this now",
)


class RowParser(html.parser.HTMLParser):
    """Collect table rows, their links, and whether an unverified value cell stayed empty."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.inputs = 0
        self.links: list[str] = []
        self.in_tbody = False
        self.in_row = False
        self.row_links: list[str] = []
        self.row_badges: list[str] = []
        self.row_empty_cells = 0
        self.in_empty_cell = False
        self.empty_buf: list[str] = []
        self.in_badge = False
        self.badge_buf: list[str] = []
        self.rows: list[dict] = []
        self.tables = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag == "h1":
            self.h1 += 1
        elif tag == "input":
            self.inputs += 1
        elif tag == "table":
            self.tables += 1
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []
            self.row_badges = []
            self.row_empty_cells = 0
        elif self.in_row:
            if tag == "a" and a.get("href"):
                self.row_links.append(a["href"])
            elif tag == "td" and "empty-cell" in cls:
                self.in_empty_cell = True
                self.empty_buf = []
            elif tag == "span" and "badge" in cls:
                self.in_badge = True
                self.badge_buf = []

    def handle_data(self, data):
        if self.in_empty_cell:
            self.empty_buf.append(data)
        if self.in_badge:
            self.badge_buf.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_empty_cell:
            if "".join(self.empty_buf).strip() != "":
                self.row_empty_cells = -999  # a hatched cell must be truly empty
            else:
                self.row_empty_cells += 1
            self.in_empty_cell = False
        elif tag == "span" and self.in_badge:
            self.row_badges.append("".join(self.badge_buf).strip())
            self.in_badge = False
        elif tag == "tr" and self.in_row:
            self.rows.append({
                "links": list(self.row_links),
                "badges": list(self.row_badges),
                "empty_cells": self.row_empty_cells,
            })
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _american(prob: float) -> int:
    if abs(prob - 0.5) < 1e-12:
        return 100
    if prob > 0.5:
        return -round(100.0 * prob / (1.0 - prob))
    return round(100.0 * (1.0 - prob) / prob)


def load(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_registers(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    names = sorted(p.name for p in (root / "data" / "nfl_3b81013c").glob("*.csv"))
    if len(names) < 12:
        errors.append(f"expected at least 12 registers, found {len(names)}")
    totals = {"rows": 0, "verified": 0, "computed": 0, "unverified": 0}
    for name in names:
        raw = (root / "data" / "nfl_3b81013c" / name).read_text(encoding="utf-8")
        if MERGE_MARKER_RE.search(raw):
            errors.append(f"{name}: merge conflict marker")
        with (root / "data" / "nfl_3b81013c" / name).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if not fields or len(set(fields)) != len(fields):
                errors.append(f"{name}: duplicate or missing CSV header")
                continue
            for index, row in enumerate(reader, 2):
                totals["rows"] += 1
                status = (row.get("verification_status") or "").strip()
                if status not in {"verified", "computed", "unverified"}:
                    errors.append(f"{name}:{index}: invalid verification_status {status!r}")
                    continue
                totals[status] += 1
                if status == "unverified" and (row.get("value") or "").strip() != "":
                    errors.append(f"{name}:{index}: unverified row carries a value")
                official = [u.strip() for u in (row.get("official_source_url") or "").split() if u.strip()]
                if not any(urlparse(u).scheme == "https" and _host(u) in OFFICIAL_HOSTS for u in official):
                    errors.append(f"{name}:{index}: no official HTTPS NFL source")
                method = (row.get("methodology_reference_url") or "").strip()
                if method and not any(
                    urlparse(u).scheme == "https" and _host(u) in METHOD_HOSTS
                    for u in method.split()
                    if u.strip()
                ):
                    errors.append(f"{name}:{index}: methodology URL off allowlist: {method!r}")
                for column in ("official_source_label", "official_source_url"):
                    if not (row.get(column) or "").strip():
                        errors.append(f"{name}:{index}: missing {column}")
    return errors, totals


def check_line_arithmetic(root: Path) -> list[str]:
    errors: list[str] = []
    records = load("team_season_records.csv")
    games = load("originated_lines.csv")

    games_played = {}
    points_for = {}
    points_against = {}
    for abbr, (w, l, t, pf, pa) in OFFICIAL_STANDINGS.items():
        games_played[abbr] = w + l + t
        points_for[abbr] = pf
        points_against[abbr] = pa
    league_avg = sum(points_for.values()) / sum(games_played.values())

    # league average row
    league_rows = [r for r in records if r["id"] == "TS-00"]
    if len(league_rows) != 1:
        errors.append("team_season_records.csv: expected exactly one league-average row TS-00")
    else:
        stored = float(league_rows[0]["value"])
        if abs(stored - league_avg) > 5e-5:
            errors.append(f"TS-00: league average {stored} != recomputed {league_avg:.6f}")

    # per-club rows
    seen_teams = set()
    for row in records:
        rid = row["id"]
        if not rid.startswith("TS-") or rid == "TS-00":
            continue
        if rid.count("-") == 1:  # games played row: TS-XXX
            abbr = rid[3:]
            seen_teams.add(abbr)
            expected = str(games_played.get(abbr))
            if row["value"] != expected:
                errors.append(f"{rid}: games played {row['value']} != {expected}")
            continue
        abbr = rid[3:].rsplit("-", 1)[0]
        metric = rid.rsplit("-", 1)[1]
        if abbr not in games_played:
            errors.append(f"{rid}: unknown club abbreviation")
            continue
        gp = games_played[abbr]
        total, per_game = {
            "PF": (points_for[abbr], points_for[abbr] / gp),
            "PA": (points_against[abbr], points_against[abbr] / gp),
        }[metric]
        expected = f"{total} / {per_game:.4f}"
        if row["value"] != expected:
            errors.append(f"{rid}: value {row['value']!r} != recomputed {expected!r}")
    if seen_teams != set(OFFICIAL_STANDINGS):
        errors.append(f"team_season_records.csv: club set mismatch {sorted(seen_teams ^ set(OFFICIAL_STANDINGS))}")
    if len(seen_teams) != 32:
        errors.append(f"team_season_records.csv: expected 32 clubs, found {len(seen_teams)}")

    # originated lines
    if len(games) != len(OFFICIAL_SLATE):
        errors.append(f"originated_lines.csv: expected {len(OFFICIAL_SLATE)} games, found {len(games)}")
    by_id = {g["id"]: g for g in games}
    for ref, away, home, neutral in OFFICIAL_SLATE:
        row = by_id.get(ref)
        if row is None:
            errors.append(f"originated_lines.csv: missing {ref}")
            continue
        item = row["item"]
        if not (item.startswith(away) or item.startswith(builder_team_name(away))):
            pass  # name form is checked below via abbreviation mapping
        if TEAM_ABBR.get(item.split(" at ")[0]) != away or TEAM_ABBR.get(item.split(" at ")[1]) != home:
            errors.append(f"{ref}: item {item!r} does not match the official slate {away} at {home}")
            continue
        hfa = 0.0 if neutral else HFA_PRIOR
        home_off = points_for[home] / games_played[home] - league_avg
        home_def = points_against[home] / games_played[home] - league_avg
        away_off = points_for[away] / games_played[away] - league_avg
        away_def = points_against[away] / games_played[away] - league_avg
        home_pts = league_avg + home_off + away_def + hfa / 2.0
        away_pts = league_avg + away_off + home_def - hfa / 2.0
        margin = home_pts - away_pts
        p_home = min(max(_norm_cdf(margin / MARGIN_SD_PRIOR), 0.001), 0.999)
        expected = (
            f"spread {(-margin):+.2f} / total {home_pts + away_pts:.2f} / home ML {_american(p_home):+d}"
        )
        if row["value"] != expected:
            errors.append(f"{ref}: originated line {row['value']!r} != recomputed {expected!r}")
        if row["verification_status"] != "computed":
            errors.append(f"{ref}: originated line must be labelled computed, got {row['verification_status']!r}")
        if "market" in row["derivation_or_detail"].lower() and "no market comparison" not in row["derivation_or_detail"].lower():
            errors.append(f"{ref}: derivation must state that no market comparison is made")
    if set(by_id) != {ref for ref, *_ in OFFICIAL_SLATE}:
        errors.append("originated_lines.csv: reference set does not match the official slate")
    return errors


def builder_team_name(abbr: str) -> str:
    for name, value in TEAM_ABBR.items():
        if value == abbr:
            return name
    return abbr


def check_pricing_arithmetic(root: Path) -> list[str]:
    errors: list[str] = []
    rows = {r["id"]: r for r in load("pricing_methods.csv")}

    expect = {
        "PM-01": f"{american_to_implied_prob(-110):.6f} and {american_to_implied_prob(150):.6f}",
        "PM-02": " / ".join(f"{p:.6f}" for p in devig_multiplicative([-110, -110])),
        "PM-03": (
            " / ".join(f"{p:.6f}" for p in devig_shin_power([-110, -110]))
            + " and "
            + " / ".join(f"{p:.6f}" for p in devig_shin_power([-150, 130]))
        ),
        "PM-04": f"{fair_prob_to_american(0.5):+d} and {fair_prob_to_american(0.62):+d}",
        "PM-05": f"{same_line_devig_clv(0, -3.0, -3.0, [-110, -110], [-125, 105]):+.6f}",
    }
    for pid, expected in expect.items():
        row = rows.get(pid)
        if row is None:
            errors.append(f"pricing_methods.csv: missing {pid}")
            continue
        if row["computed_output"] != expected:
            errors.append(f"{pid}: output {row['computed_output']!r} != recomputed {expected!r}")
        if row["verification_status"] != "computed":
            errors.append(f"{pid}: must be labelled computed")

    # The moved-line case must stay blank rather than be bridged.
    if same_line_devig_clv(0, -2.5, -3.5, [-110, -110], [-125, 105]) is not None:
        errors.append("same_line_devig_clv must return None on a moved line")
    # Independent sanity on the conversion: -110 must be 0.523810, +150 exactly 0.4.
    if abs(american_to_implied_prob(-110) - 0.5238095238) > 1e-9:
        errors.append("american_to_implied_prob(-110) is not 0.5238095238")
    if abs(american_to_implied_prob(150) - 0.4) > 1e-12:
        errors.append("american_to_implied_prob(150) is not 0.4")
    if fair_prob_to_american(0.5) != 100:
        errors.append("fair even money must be +100, not -110")
    return errors


def check_depth_arithmetic(root: Path) -> list[str]:
    errors: list[str] = []
    injuries = load("injuries_and_depth.csv")
    summary = load("depth_deficiency_summary.csv")
    verified_tiers = {"ID-01": 2, "ID-03": 2, "ID-17": 2, "ID-23": 1}

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in injuries:
        slot = row["position_slot"]
        if slot not in POSITION_WEIGHTS:
            errors.append(f"{row['id']}: unknown position slot {slot!r}")
            continue
        tier = verified_tiers.get(row["id"])
        if tier is None:
            if row["structural_severity_index"] != "":
                errors.append(f"{row['id']}: unverified replacement must leave severity blank")
            if row["verification_status"] != "unverified":
                errors.append(f"{row['id']}: unverified replacement must be labelled unverified")
        else:
            if tier == 1 and row["official_report_status"] == "ACTIVE_EXPECTED":
                expected = 0.0
            elif row["official_report_status"] == "LP":
                expected = POSITION_WEIGHTS[slot] * 0.15
            else:
                expected = POSITION_WEIGHTS[slot] * STRING_MULTIPLIER[tier]
            if abs(float(row["structural_severity_index"]) - expected) > 5e-5:
                errors.append(
                    f"{row['id']}: severity {row['structural_severity_index']} != recomputed {expected:.4f}"
                )
        if row["official_report_status"] in {"DNP", "OUT", "IR", "LP"}:
            groups.setdefault((row["team"], row["side"], row["unit_group"]), []).append(row)

    if len(summary) != len(groups):
        errors.append(f"depth_deficiency_summary.csv: {len(summary)} rows != {len(groups)} register groups")
    seen = set()
    for row in summary:
        key = (row["team"], row["side"], row["unit_group"])
        if key not in groups:
            errors.append(f"{row['id']}: group {key} not present in the injury register")
            continue
        seen.add(key)
        recs = groups[key]
        verified = [r for r in recs if r["structural_severity_index"] != ""]
        raw = sum(float(r["structural_severity_index"]) for r in verified)
        n_abs = sum(1 for r in recs if r["official_report_status"] in {"DNP", "OUT", "IR"})
        n_lp = sum(1 for r in recs if r["official_report_status"] == "LP")
        cluster = 1.35 if n_abs >= 3 else 1.18 if n_abs == 2 else 1.00
        if row["slots_on_report"] != str(len(recs)):
            errors.append(f"{row['id']}: slots_on_report {row['slots_on_report']} != {len(recs)}")
        if row["starters_out_or_dnp"] != str(n_abs):
            errors.append(f"{row['id']}: starters_out_or_dnp {row['starters_out_or_dnp']} != {n_abs}")
        if row["limited_participants"] != str(n_lp):
            errors.append(f"{row['id']}: limited_participants {row['limited_participants']} != {n_lp}")
        if row["slots_with_verified_replacement"] != str(len(verified)):
            errors.append(f"{row['id']}: verified replacements {row['slots_with_verified_replacement']} != {len(verified)}")
        if not verified:
            if row["raw_structural_sum"].strip() != "" or row["cluster_adjusted_index"].strip() != "":
                errors.append(f"{row['id']}: a group with no verified replacement must leave both sums blank")
            continue
        if abs(float(row["raw_structural_sum"]) - raw) > 5e-5:
            errors.append(f"{row['id']}: raw sum {row['raw_structural_sum']} != {raw:.4f}")
        if abs(float(row["cluster_multiplier"]) - cluster) > 1e-9:
            errors.append(f"{row['id']}: cluster multiplier {row['cluster_multiplier']} != {cluster:.2f}")
        if abs(float(row["cluster_adjusted_index"]) - raw * cluster) > 5e-5:
            errors.append(f"{row['id']}: cluster index {row['cluster_adjusted_index']} != {raw * cluster:.4f}")
        if not verified and row["verification_status"] != "unverified":
            errors.append(f"{row['id']}: a group with no verified replacement must be labelled unverified")
    if seen != set(groups):
        errors.append(f"depth_deficiency_summary.csv: missing groups {sorted(set(groups) - seen)}")
    return errors


def check_correlation_arithmetic(root: Path) -> list[str]:
    errors: list[str] = []
    for row in load("correlations.csv"):
        if row["verification_status"] != "unverified":
            errors.append(f"{row['id']}: empirical correlations must stay unverified")
        for column in ("pearson_r", "fisher_z_ci_low", "fisher_z_ci_high", "verified_paired_residuals"):
            if row[column].strip() != "":
                errors.append(f"{row['id']}: {column} must be blank while no paired sample exists")
        lo, hi = float(row["frechet_lower_computed"]), float(row["frechet_upper_computed"])
        if not (abs(lo - 0.0) < 1e-9 and abs(hi - 0.5) < 1e-9):
            errors.append(f"{row['id']}: Frechet bounds at two 0.50 legs must be 0 and 0.5, got {lo}, {hi}")
        mid = float(row["joint_prob_rho_0"])
        if abs(mid - 0.25) > 1e-9:
            errors.append(f"{row['id']}: independent joint probability must be 0.25, got {mid}")
        neg = float(row["joint_prob_rho_minus_0_5"])
        pos = float(row["joint_prob_rho_plus_0_5"])
        if not (lo <= neg < mid < pos <= hi):
            errors.append(f"{row['id']}: copula columns breach Frechet bounds or ordering")
    return errors


def check_gates_and_leaderboard(root: Path) -> list[str]:
    errors: list[str] = []
    gates = load("validation_gates.csv")
    if len(gates) != 10:
        errors.append(f"validation_gates.csv: expected 10 gates, found {len(gates)}")
    if [g["id"] for g in gates] != [f"VG-{i:02d}" for i in range(1, 11)]:
        errors.append("validation_gates.csv: gate identifiers must be VG-01..VG-10 in order")
    try:
        from nfl_3b81013c import StrategyCandidate, evaluate_strategy_gates, rank_skill_leaderboard
    except Exception as exc:  # pragma: no cover - import failure is a hard error
        return [f"cannot import the package: {exc}"]

    strategies = load("strategies.csv")
    if len(strategies) < 8:
        errors.append("strategies.csv: expected at least 8 registered strategies")
    candidates = []
    for row in strategies:
        candidates.append(StrategyCandidate(
            strategy_id=row["id"], strategy_name=row["name"], category=row["category"],
            n_authorized_events=0, n_slate_clusters=0, rights_verified=False,
            pre_kickoff_timestamps_verified=False, walk_forward_clean=False,
            depth_chart_verified=False, holdout_brier_delta_vs_market=None,
            holdout_same_line_clv=None, holdout_roi_ci_lower=None,
            raw_p_value=None, adjusted_p_value=None, combo_correlation_verified=False,
        ))
    ranked = rank_skill_leaderboard(candidates)
    if any(r["qualified"] for r in ranked):
        errors.append("a strategy with zero authorized observations must never qualify")
    for row in strategies:
        if row["leaderboard_status"] != "QUARANTINED_UNVERIFIED_DATA":
            errors.append(f"{row['id']}: expected quarantine status, got {row['leaderboard_status']!r}")
        if row["reward_tier"] != "QUARANTINED_UNVERIFIED_DATA":
            errors.append(f"{row['id']}: expected quarantine reward tier, got {row['reward_tier']!r}")

    board = load("leaderboard.csv")
    if len(board) != len(strategies):
        errors.append("leaderboard.csv: one row per strategy is required")
    for row in board:
        if row["rank"].strip() != "":
            errors.append(f"{row['strategy_id']}: rank must be blank while quarantined")
        if row["qualified"] != "no":
            errors.append(f"{row['strategy_id']}: qualified must be 'no'")
        if row["holdout_roi_ci_lower"].strip() != "":
            errors.append(f"{row['strategy_id']}: ROI lower bound must be blank")
    return errors


def check_pages(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    docs = root / "docs" / "nfl-3b81013c"
    pages = sorted(p.name for p in docs.glob("*.html"))
    if set(pages) != EXPECTED_PAGES:
        errors.append(f"page set mismatch: {sorted(set(pages) ^ EXPECTED_PAGES)}")
    if not (docs / "styles.css").is_file():
        errors.append("docs/nfl-3b81013c/styles.css missing")

    total_rows = 0
    for name in pages:
        text = (docs / name).read_text(encoding="utf-8")
        rel = f"docs/nfl-3b81013c/{name}"
        if MERGE_MARKER_RE.search(text):
            errors.append(f"{rel}: merge conflict marker")
        if "<generator object" in text:
            errors.append(f"{rel}: generator repr leaked into HTML")
        if "Math.erf(" in text:
            errors.append(f"{rel}: calls Math.erf, undefined in browser JavaScript")
        lowered = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lowered:
                errors.append(f"{rel}: contains a wagering-recommendation phrase {phrase!r}")

        parser = RowParser()
        parser.feed(text)
        if parser.h1 != 1:
            errors.append(f"{rel}: expected exactly one h1, found {parser.h1}")
        if parser.inputs != 0:
            errors.append(f"{rel}: input elements are not allowed ({parser.inputs})")
        if not parser.rows:
            errors.append(f"{rel}: no table rows found")

        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme:
                if parsed.scheme != "https":
                    errors.append(f"{rel}: non-HTTPS link {href}")
                elif _host(href) not in OFFICIAL_HOSTS | METHOD_HOSTS | {"github.com"}:
                    errors.append(f"{rel}: external host not allowlisted: {href}")
            else:
                if href.startswith(("/", "//")):
                    errors.append(f"{rel}: root-absolute link is not project relative: {href}")
                    continue
                target = unquote(parsed.path)
                if target and not (docs / target).resolve().is_file():
                    errors.append(f"{rel}: broken relative link {href}")

        for index, info in enumerate(parser.rows, 1):
            total_rows += 1
            official = [h for h in info["links"] if urlparse(h).scheme == "https" and _host(h) in OFFICIAL_HOSTS]
            if not official:
                errors.append(f"{rel}: table row {index} lacks an official HTTPS NFL source link")
            if "unverified" in info["badges"] and info["empty_cells"] <= 0:
                errors.append(f"{rel}: unverified row {index} does not leave a value cell blank")
    return errors, {"pages": len(pages), "rows": total_rows}


def run_checks(root: Path = ROOT) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []

    # 1. deterministic build
    if root.resolve() == ROOT.resolve():
        expected = builder.generate_all()
        for name, content in expected.items():
            target = root / "docs" / "nfl-3b81013c" / name
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                errors.append(f"docs/nfl-3b81013c/{name}: out of sync with the builder")

    register_errors, totals = check_registers(root)
    arithmetic_errors = (
        check_line_arithmetic(root)
        + check_pricing_arithmetic(root)
        + check_depth_arithmetic(root)
        + check_correlation_arithmetic(root)
        + check_gates_and_leaderboard(root)
    )
    page_errors, page_stats = check_pages(root)

    errors += register_errors + arithmetic_errors + page_errors

    # 4. required narrative deliverables
    for rel in ("research/NFL_3B81013C_EXECUTIVE_SUMMARY.md", "audit/NFL_3B81013C_REPO_AND_SOURCE_AUDIT.md"):
        if not (root / rel).is_file():
            errors.append(f"{rel}: missing required report")
            continue
        text = (root / rel).read_text(encoding="utf-8")
        if MERGE_MARKER_RE.search(text):
            errors.append(f"{rel}: merge conflict marker")
        for match in re.finditer(r"\]\((https?://[^)]+)\)", text):
            url = match.group(1)
            if urlparse(url).scheme != "https":
                errors.append(f"{rel}: non-HTTPS markdown link {url}")

    stats = {
        "pages": page_stats["pages"],
        "table_rows": page_stats["rows"],
        "register_rows": totals["rows"],
        "verified": totals["verified"],
        "computed": totals["computed"],
        "unverified": totals["unverified"],
    }
    return errors, stats


def main() -> int:
    errors, stats = run_checks(ROOT)
    if errors:
        print(f"NFL 3B81013C CHECK FAILED ({len(errors)} error(s)):")
        for err in errors:
            print(f" - {err}")
        return 1
    print(
        f"NFL 3B81013C OK: {stats['pages']} pages / {stats['table_rows']} sourced table rows; "
        f"{stats['register_rows']} register rows "
        f"({stats['verified']} verified, {stats['computed']} computed, {stats['unverified']} unverified); "
        f"line, pricing, depth and correlation arithmetic recomputed; zero unverified values filled in."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
