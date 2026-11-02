#!/usr/bin/env python3
"""Reproduce the row-level upstream audit without editing another session's files.

This is an offline audit of a frozen upstream tree plus explicitly recorded manual
source review. It does not fetch or republish NBA statistics and does not turn a
search snippet into a verified measurement. Run from any working directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "empirical"
BASE = "77a28cccea34e0764f6d45ff3316d3aa8f6b90b7"
REPO = "https://github.com/sassnarep3-star/Own6"
NBA = "https://www.nba.com"
LAW = "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95"
NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"
OFFICIAL_HOSTS = {"www.nba.com", "official.nba.com", "ak-static.cms.nba.com", "www.law.go.kr", "www.itl.nist.gov", "scikit-learn.org", "docs.scipy.org", "docs.github.com", "github.com", "api.github.com"}


def blob(path: str, lines: str = "") -> str:
    return f"{REPO}/blob/{BASE}/{path}{lines}"


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_audit() -> list[dict]:
    rows = []

    def add(file: str, key: str, status: str, note: str, url: str) -> None:
        rows.append({"file": file, "row": key, "verification": status, "review_note": note, "source_url": url, "reviewed_on": "2026-11-02"})

    games = load("data/games.json")["rows"]
    expected_ids = {f"002260{i:04d}" for i in range(158, 173)}
    if {r["game_id"] for r in games} != expected_ids or len(games) != 15:
        raise ValueError("Upstream schedule row identities changed; re-review required")
    for r in games:
        add("data/games.json", r["game_id"], "metadata_verified", "Matchup, ET start, venue and preview link checked against the official schedule; game 0022600169 also checked on its game page. The scheduled label is editorial. Scores and odds remain blank, not verified measurements.", f"{NBA}/schedule")
    for r in load("data/legal_kr.json")["rows"]:
        add("data/legal_kr.json", r["article"], "needs_review", "Official statute identity/version header was directly read. Article body was not returned by the dynamic page in this session; excerpt, translation and penalty were not independently re-verified. Not a finding that the upstream text is false.", LAW)
    for i, r in enumerate(load("data/nba_policy.json")["rows"], 1):
        if i == 1:
            add("data/nba_policy.json", str(i), "verified_direct", "Official October 26, 2026 release confirms the framework, Sportradar data distribution and existence of aligned restrictions; it does not enumerate the reported prop bans.", r["official_source_url"])
        elif i == 2:
            add("data/nba_policy.json", str(i), "verified_direct", "Official July 9, 2026 partner list read directly. Absence of a Korea entry is a statement about this list, not a legal conclusion.", r["official_source_url"])
        else:
            add("data/nba_policy.json", str(i), "unverified_correctly_blank", "Press-only claim. Official value and official source are blank in the upstream row; no official restriction text was confirmed.", f"{NBA}/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets")
    flag_review = {
        "F01": ("needs_review", "Statute header verified; legal applicability and article-body re-verification remain open.", LAW),
        "F02": ("unverified_secondary", "The linked newspaper is not an official legal source. Overseas enforcement was not verified.", f"{NBA}/termsofuse"),
        "F03": ("unverified_correctly_blank", "Specific prop restrictions are not enumerated in the official release.", f"{NBA}/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets"),
        "F04": ("gap_confirmed", "No licensed executable odds archive is present. Blank odds are appropriate.", f"{NBA}/termsofuse#nba-statistics"),
        "F05": ("scope_confirmed", "Upstream coverage is explicitly one day, not a historical backtest sample.", f"{NBA}/schedule"),
        "F06": ("gap_confirmed", "No historical player/team observations are present. NBA download and gambling-use restrictions are additional constraints.", f"{NBA}/stats/help/faq"),
        "F07": ("historical_confirmed", "Initial state and fixed Arena branch constraint are recorded on the shared board.", blob("COORDINATION.md")),
        "F08": ("historical_now_resolved", "The one-line README described the initial commit; the audited upstream README now contains project documentation.", blob("README.md")),
        "F09": ("partly_resolved", "Upstream now has .gitignore; a LICENSE file is still absent. The flag describes the initial tree.", blob(".gitignore")),
        "F10": ("historical_confirmed", "Commit metadata is publicly visible; no address is reproduced in this audit and no history was rewritten.", f"{REPO}/commit/c5d6e4c4b3b7ed486d48b0bf4d9d0cbce89ef49d"),
        "F11": ("configuration_confirmed", "GitHub Pages API reported legacy main-root publication. No competing publisher is introduced.", "https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site"),
        "F12": ("disclosure_confirmed", "Upstream explicitly labels English summaries as compiler translations, not official translations.", LAW),
    }
    for r in load("data/flags.json")["rows"]:
        status, note, url = flag_review[r["id"]]
        add("data/flags.json", r["id"], status, note, url)
    source_review = {
        "S1": ("needs_review", "Stats overview was not directly re-read in this session; indexed is not the same as verified.", f"{NBA}/stats/overview"),
        "S2": ("verified_direct", "Glossary definitions read directly; no performance claim is supported.", f"{NBA}/stats/help/glossary"),
        "S3": ("verified_canonical", "The FAQ was read at www.nba.com/stats/help/faq; the upstream CDN URL is a different locator for the reviewed FAQ content.", f"{NBA}/stats/help/faq"),
        "S4": ("needs_review", "The root official-site link does not by itself verify a specific scoring/timing rule. Exact rule text was not independently checked.", "https://official.nba.com/"),
        "S5": ("unverified_fetch_failed", "The dated injury-report PDF could not be fetched in this session. No injury values are used.", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-02_01_45PM.pdf"),
        "S6": ("verified_direct", "The November 4, 2021 official partnership release was read directly; use the newer list for current partners.", f"{NBA}/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners"),
        "S7": ("verified_direct", "Official scikit-learn calibration documentation read directly; Brier alone is not a calibration-only test.", "https://scikit-learn.org/stable/modules/calibration.html"),
        "S8": ("blank_confirmed", "No numeric ratings, odds or backtest results are supplied by this row.", f"{NBA}/termsofuse#nba-statistics"),
    }
    with (ROOT / "data/sources.csv").open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            status, note, url = source_review[r["id"]]
            add("data/sources.csv", r["id"], status, note, url)
    for r in load("data/methodology.json")["gates"]:
        url = LAW if r["id"] == "G1" else f"{NBA}/termsofuse#nba-statistics" if r["id"] in {"G2", "G3"} else NIST
        add("data/methodology.json", r["id"], "proposal_not_empirical_result", "Compiler-defined gate, not an official NBA rule or a passed test. The new lab evaluates its own expanded gates fail-closed; no real-data performance is asserted.", url)
    for name in ("data/strategies.json",):
        if load(name)["rows"]:
            raise ValueError("New upstream strategy rows require manual review")
    return rows


def inventory() -> list[dict]:
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True).splitlines()
    rows = []
    for path in paths:
        content = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        suffix = Path(path).suffix
        method = {
            ".py": "Source read; syntax and test execution checked separately",
            ".json": "Parsed; data rows reviewed in source_audit.csv where applicable",
            ".csv": "Parsed; each row reviewed in source_audit.csv",
            ".md": "Documentation read; external claims reviewed against cited primary sources",
            ".html": "Generated/static markup; structure and internal links checked",
            ".css": "Static stylesheet read; browser rendering checked separately",
            ".js": "Static client code read; no external data feed",
        }.get(suffix, "Deployment/configuration marker inspected")
        rows.append({"path": path, "lines": len(content.splitlines()), "sha256": hashlib.sha256(content).hexdigest(), "review_method": method, "source_url": blob(path), "base_commit": BASE})
    return rows


def findings() -> list[dict]:
    specs = [
        ("R01", "High", "EXECUTIVE_SUMMARY.md", "L24-L29", "Rights boundary incomplete", "The original summary discusses legal exposure but omits NBA Terms §9 gambling-use and §1 public-reuse restrictions. No authorized feed is present.", "Keep gambling-use and republication gates blocked; obtain appropriate rights and legal review.", f"{NBA}/termsofuse"),
        ("R02", "High", "src/own6/validation.py", "L28-L30", "Declared gates not enforced", "evaluate() omits log loss, correlation honesty (G7), and ledger integrity (G8), yet returns ALL from only six checks.", "Use nba_lab.gates, which requires every declared gate and fails closed on missing evidence.", blob("src/own6/validation.py", "#L28-L30")),
        ("R03", "High", "src/own6/leaderboard.py", "L3-L9", "Eligibility is sample size only", "skill_score() can mark a negative lower-bound strategy eligible and does not require validation gates, CLV, or independence.", "Rank only strategies passing all gates; use event-clustered uncertainty.", blob("src/own6/leaderboard.py", "#L3-L9")),
        ("R04", "High", "src/own6/validation.py", "L10-L13", "IID bootstrap for clustered bets", "Resampling individual bets breaks same-game and slate dependence and can understate uncertainty.", "Resample whole event clusters; disclose that temporal dependence may remain.", blob("src/own6/validation.py", "#L10-L13")),
        ("R05", "Medium", "src/own6/validation.py", "L7-L9", "Binomial assumptions and bounds", "The exact binomial test assumes independent constant-probability trials; bets/parlays can be clustered and heterogeneous. Inputs are not validated.", "Use as a diagnostic only; require cluster-robust ROI and market benchmarks.", blob("src/own6/validation.py", "#L7-L9")),
        ("R06", "Medium", "src/own6/parlay.py", "L4-L7", "Correlation input failure modes", "Empty inputs divide by zero, unequal lengths are silently zipped, and constant series return a measured-looking zero.", "Reject invalid pairs; return no estimate for undefined correlation.", blob("src/own6/parlay.py", "#L4-L7")),
        ("R07", "Medium", "src/own6/parlay.py", "L9-L22", "Copula input failure modes", "joint_prob does not validate matrix shape/PSD, probability bounds, or simulation count; invalid matrices can divide by zero or be silently clipped.", "Validate inputs; prefer directly estimated two-leg joint probabilities and disclose the dependence model.", blob("src/own6/parlay.py", "#L9-L22")),
        ("R08", "Medium", "src/own6/lines.py", "L31-L36", "Invalid odds/probabilities accepted", "American zero, probabilities outside (0,1), zero-sum de-vig and nonfinite values are not rejected.", "Use strict price/probability contracts in nba_lab.pricing.", blob("src/own6/lines.py", "#L31-L36")),
        ("R09", "Medium", "src/own6/lines.py", "L24-L29", "Small training samples", "fit_from_games divides by zero on an empty sample and returns NaN scale for one observation; fair_lines maps invalid scale to 0.5.", "Require adequate training data and reject nonfinite inputs.", blob("src/own6/lines.py", "#L24-L29")),
        ("R10", "Medium", "src/own6/props.py", "L4-L15", "Prop model input failure modes", "Negative shrinkage counts, zero denominators, invalid scales and nonfinite values are not consistently rejected; a zero SD becomes 0.5.", "Validate counts and scales; validate the count distribution rather than assuming normality.", blob("src/own6/props.py", "#L4-L15")),
        ("R11", "Medium", "src/own6/validation.py", "L5-L6", "Scoring function input failure modes", "zip silently truncates unequal arrays; empty arrays divide by zero; probability bounds are not checked.", "Use aligned, finite, in-range arrays and nonempty samples.", blob("src/own6/validation.py", "#L5-L6")),
        ("R12", "Medium", "src/own6/validation.py", "L14-L16", "Empty CLV sample", "clv_stats divides by zero for an empty sample and does not reject invalid observations.", "Return not_run for missing CLV and reject malformed evidence.", blob("src/own6/validation.py", "#L14-L16")),
        ("R13", "Medium", "data/sources.csv", "L2-L8", "Indexed evidence labeled verified", "Several rows say verified-indexed although the registry itself records search-index verification rather than direct primary-source review.", "Separate direct, partial, indexed and failed-fetch evidence in the new audit.", blob("data/sources.csv", "#L2-L8")),
        ("R14", "Medium", "data/legal_kr.json", "L10-L128", "Dynamic statute body not independently reproduced", "This session read the official version header but not the dynamic article body. Upstream excerpts and translations are not re-certified here.", "Publish the limitation and obtain official article text/counsel review before relying on it.", LAW),
        ("R15", "Low", "data/flags.json", "L79-L96", "Historical flags can look current", "F08/F09 describe the initial README/.gitignore state; upstream now has documentation and .gitignore, while LICENSE remains absent.", "Label these as historical/partly resolved in the new review ledger.", blob("data/flags.json", "#L73-L94")),
        ("R16", "Medium", "scripts/check_site.py", "L83-L108", "Incomplete combined-site link coverage", "The checker scans only docs/verified, not the original docs pages or the combined site; it does not validate fragments or require a source link in every table row.", "Add an isolated combined-site checker for all docs pages, fragments and lab table provenance.", blob("scripts/check_site.py", "#L83-L108")),
        ("R17", "Medium", "tests/test_engine.py", "L1-L16", "Shallow baseline and no active main CI", "The five baseline tests pass but do not cover the failure modes above; no active lab workflow exists on the audited main tree.", "Add adversarial tests and a non-publishing CI workflow before merge.", blob("tests/test_engine.py", "#L1-L16")),
        ("R18", "Low", "README.md", "L1-L20", "Repository license absent", "No LICENSE file exists in the audited tree. Code reuse rights are not specified; third-party data rights are separate.", "Do not infer a license. Repository owner must choose code licensing and data rights separately.", blob("README.md", "#L1-L20")),
        ("R19", "Medium", "data/games.json", "L12-L27", "Row-level verified flag is broader than evidence", "Schedule metadata was checked, but scheduled is an editorial status and scores/odds are blank. verified:true must not be read as a verified result or price.", "Use field-level evidence language in the audit and leave unavailable values blank.", f"{NBA}/schedule"),
        ("R20", "High", "EXECUTIVE_SUMMARY.md", "L5-L22", "No empirical qualification evidence", "The repository contains modeling utilities and hypotheses, not a licensed historical odds/results ledger. No strategy has demonstrated market-relative skill.", "Keep the leaderboard empty and all empirical metrics blank until the gates pass on authorized data.", f"{NBA}/termsofuse#nba-statistics"),
    ]
    return [{"id": i, "severity": severity, "file": path, "lines": lines, "finding": title, "detail": detail, "action": action, "source_url": url, "status": "needs_review"} for i, severity, path, lines, title, detail, action, url in specs]


def main() -> None:
    sources = load("data/empirical/sources.json")["rows"]
    for r in sources:
        if urlparse(r["url"]).hostname not in OFFICIAL_HOSTS:
            raise ValueError(f"Non-official source: {r['id']}")
    audit = source_audit()
    for r in audit:
        if urlparse(r["source_url"]).hostname not in OFFICIAL_HOSTS:
            raise ValueError(f"Non-official review link: {r['file']}:{r['row']}")
    fields = ["file", "row", "verification", "review_note", "source_url", "reviewed_on"]
    write_csv("source_audit.csv", fields, audit)
    write_csv("repo_inventory.csv", ["path", "lines", "sha256", "review_method", "source_url", "base_commit"], inventory())
    write_csv("repo_findings.csv", ["id", "severity", "file", "lines", "finding", "detail", "action", "source_url", "status"], findings())
    print(f"Audit complete: {len(audit)} upstream data rows, {len(inventory())} upstream files, {len(findings())} findings; {len(sources)} official-source records.")


if __name__ == "__main__":
    main()
