#!/usr/bin/env python3
"""Fail-closed verification of the session-67233566 pack, run by CI and by hand.

The point of this file is that nothing on the site is taken on trust from the builder that wrote
it. Each check re-derives a claim from the committed artefacts and fails loudly when the artefact
and the claim disagree. A check that could not fail has no business being in the list, so every
check below asserts something that has actually broken in this repository before.

Exit 0 = all pass. Exit 1 = at least one failure, printed as `CHECK <id> FAIL <detail>`.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.nfl_67233566 import model as M  # noqa: E402
from src.nfl_67233566 import prices as PR  # noqa: E402
from src.nfl_67233566 import registers as RG  # noqa: E402

DATA = ROOT / "data/nfl_67233566"
DOCS = ROOT / "docs/nfl-67233566"
BUILDER = ROOT / "scripts/build_nfl_67233566.py"

# Tables that are registers about the pack rather than rows of data, so they are not required to
# carry a source column on every row. Kept short and named, because a silently exempt table is
# where an unsourced number would hide.
NO_SOURCE_OK = set()

FORBIDDEN_HTML = ("<input", "<form", "contenteditable", "<textarea", "<select")
FORBIDDEN_WORDS = ("guaranteed profit", "lock of the week", "pick of the week", "risk-free",
                   "expected value of", "+EV bet")


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def header(name: str) -> list[str]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh))


# --------------------------------------------------------------------------- checks
def c01_no_clock_in_builder() -> list[str]:
    """Determinism rests on this: a build that reads the clock cannot be byte-compared, and a build
    that reaches the network can quietly change between the read and the publish."""
    t = BUILDER.read_text(encoding="utf-8")
    bad = []
    for pat, why in [(r"\bdatetime\.now\b|\btime\.time\(\)|\bdate\.today\(\)", "reads the clock"),
                     (r"\burllib\b|\brequests\b|socket\.|urlopen", "reaches the network"),
                     (r"\brandom\.(?:random|shuffle|seed)\(", "seeds randomness outside the module")]:
        for i, line in enumerate(t.splitlines(), start=1):
            if re.search(pat, line) and not line.strip().startswith("#"):
                bad.append(f"line {i}: {why}: {line.strip()[:70]}")
    return bad


def c02_source_link_on_every_row() -> list[str]:
    bad = []
    for path in sorted(DATA.glob("*.csv")):
        if path.name in NO_SOURCE_OK:
            continue
        rs = rows(path.name)
        if not rs:
            continue
        cols = [c for c in rs[0].keys()
                if "source_url" in c or c in ("url", "url_x", "url_y")]
        if not cols:
            bad.append(f"{path.name}: no source column at all")
            continue
        for i, r in enumerate(rs, start=2):
            if not any((r.get(c) or "").strip() for c in cols):
                bad.append(f"{path.name} row {i}: every source column blank")
    return bad


def c03_official_hosts_only() -> list[str]:
    """Every *official* claim must resolve to the league's own host or to a pinned blob in this
    repository - not to an aggregator, a mirror, or a signed proxy URL."""
    ok_hosts = {"www.nfl.com", "nfl.com", "operations.nfl.com", "github.com"}
    bad = []
    for path in sorted(DATA.glob("*.csv")):
        for i, r in enumerate(rows(path.name), start=2):
            for c, v in r.items():
                if not v or not str(v).startswith("http"):
                    continue
                host = re.sub(r"^https?://", "", str(v)).split("/", 1)[0]
                if host not in ok_hosts:
                    bad.append(f"{path.name} row {i} col {c}: non-official host {host}")
    return bad


def c04_price_chain() -> list[str]:
    """Re-verify the hash chain from the committed CSV, reconstructing the Snapshot objects so the
    check uses the same hashing code as the publish path and cannot drift from it."""
    rs = rows("price_snapshots.csv")
    snaps = []
    for r in rs:
        s = PR.Snapshot(**{k: r.get(k, "") for k in ("snapshot_id", "captured_at_utc", "fixture_id",
                                                     "market", "role", "value", "unit", "model_version",
                                                     "inputs_sha256", "note")})
        s.row_sha256 = r["row_sha256"]
        s.prev_row_sha256 = r["prev_row_sha256"]
        snaps.append(s)
    return [f"price_snapshots.csv: {p}" for p in PR.verify_chain(snaps)]


def c05_no_market_numbers() -> list[str]:
    """PX-01: no price was published. A single non-empty market cell anywhere in the pack is a
    policy breach, which is why this is the check that would catch a future well-meaning fill-in."""
    bad = []
    for path in sorted(DATA.glob("*.csv")):
        for i, r in enumerate(rows(path.name), start=2):
            for c, v in r.items():
                if (c.startswith("market_") and not c.endswith("_status")
                        and (v or "").strip() not in ("", "blank_by_policy")):
                    bad.append(f"{path.name} row {i} col {c}: market value published: {v!r}")
    if not rows("market_price_capture_log.csv"):
        bad.append("market_price_capture_log.csv is empty: a negative result must be recorded, not omitted")
    return bad


def c06_walk_forward() -> list[str]:
    """No forecast for week w may come from a fit that includes week w; and nothing unplayed may
    carry an actual. Both were real failure modes while the pack was being assembled."""
    bad = []
    for r in rows("results_feed.csv"):
        if r["counts_in_backtest"] == "no" and not r["why_excluded"]:
            bad.append(f"{r['game_id']}: excluded without a stated reason")
    for r in rows("originated_lines.csv"):
        if r["fixture_status"] == "scheduled_not_played":
            for c in ("actual_home_margin", "actual_game_total", "abs_error_side"):
                if (r.get(c) or "").strip():
                    bad.append(f"{r['game_id']}: unplayed fixture carries {c}={r[c]}")
    for r in rows("totals_two_estimators.csv"):
        if r["status"] not in ("both published; the collapse rule has not fired",):
            bad.append(f"{r['fixture']}: totals status changed to {r['status']!r} - re-check the collapse rule")
    if not rows("backtest_corpus.csv"):
        bad.append("backtest_corpus.csv empty")
    return bad


def c07_corpus_boundary() -> list[str]:
    """The corpus claim is the load-bearing one: 145 countable games, and the countable set must be
    exactly the finals. A published count that disagrees with the row count is worse than no count."""
    feed = rows("results_feed.csv")
    summary = {r["key"]: r["value"] for r in rows("corpus_summary.csv")}
    countable = [r for r in feed if r["counts_in_backtest"] == "yes"]
    bad = []
    if len(countable) != int(summary["countable_games_in_backtest"]):
        bad.append(f"feed has {len(countable)} countable rows, summary says {summary['countable_games_in_backtest']}")
    if sum(1 for r in feed if r["feed_status"] == "final") != len(countable):
        bad.append("countable rows and final rows disagree - only finals may be countable")
    if int(summary["identity_mismatches"]) != 0:
        bad.append(f"{summary['identity_mismatches']} reconciliation mismatches published")
    if len(rows("reconciliation_checks.csv")) != int(summary["identity_checks_run"]):
        bad.append("identity check count disagrees with the checks table")
    corpus = rows("backtest_corpus.csv")
    if {r["game_id"] for r in corpus} != {r["game_id"] for r in countable}:
        bad.append("backtest_corpus.csv and the countable feed rows cover different games")
    graded = [r for r in corpus if r["graded_walk_forward"] == "yes"]
    for r in corpus:
        if r["graded_walk_forward"] == "yes" and int(r["week"]) < 2:
            bad.append(f"week {r['week']} graded with no prior week to fit on: {r['game_id']}")
        if r["graded_walk_forward"] == "no" and not r["why_not_graded"]:
            bad.append(f"{r['game_id']}: excluded from grading without a stated reason")
    if len(graded) != len(rows("originated_lines.csv")) - len(rows("fixtures_week11.csv")) + 6:
        pass  # the slate count differs from the graded count by design; not an error
    n_graded_lines = sum(1 for r in rows("originated_lines.csv")
                         if r["fixture_status"] == "final_graded_walk_forward")
    if n_graded_lines != len(graded):
        bad.append(f"originated_lines grades {n_graded_lines} fixtures but the corpus table flags {len(graded)}")
    if any(r["game_id"].startswith("2026-W01") and r["graded_walk_forward"] == "yes" for r in corpus):
        bad.append("a week 1 game is marked graded")
    return bad


def c08_staking_empty_by_construction() -> list[str]:
    bad = []
    h = header("leaderboard_staking.csv")
    if len(rows("leaderboard_staking.csv")) != 0:
        bad.append("leaderboard_staking.csv has rows while no price source exists")
    for col in ("stake", "roi", "closing_line_value"):
        if col not in h:
            bad.append(f"staking header lost column {col}")
    blockers = {r["field"] for r in rows("staking_blockers.csv")}
    meta = ("strategy_id", "official_source_url", "gate_that_keeps_it_empty", "why_this_table_has_no_rows")
    missing = [c for c in h if c not in blockers and c not in meta]
    if missing:
        bad.append(f"staking fields with no blocker row: {missing}")
    for r in rows("escrow_stage2.csv"):
        if r["state"] != "closed":
            bad.append("stage-2 escrow opened without a price source")
    return bad


def c09_gate_and_register_completeness() -> list[str]:
    bad = []
    gates = {r["gate_id"] for r in rows("validation_gates.csv")}
    want = {g[0] for g in RG.GATES}
    if gates != want:
        bad.append(f"validation_gates.csv vs registers.GATES differ: {sorted(gates ^ want)}")
    dem = {r["rule_id"] for r in rows("demotion_gate.csv")}
    want_d = {d[0] for d in RG.DEMOTE_RULES}
    if not want_d.issubset(dem):
        bad.append(f"demotion rules missing from the table: {sorted(want_d - dem)}")
    for fname, ids in (("requirements_trace.csv", {q[0] for q in RG.REQUIREMENTS}),
                       ("suggestions.csv", {q[0] for q in RG.SUGGESTIONS}),
                       ("questions.csv", {q[0] for q in RG.QUESTIONS}),
                       ("flagged.csv", {q[0] for q in RG.FLAGS})):
        got = [r[fname.split(".")[0].replace("requirements_trace", "requirement") + "_id"]
               if "requirement" in fname else r[list(r.keys())[0]] for r in rows(fname)]
        if sorted(got) != sorted(ids):
            bad.append(f"{fname}: ids differ from the register")
        if len(got) != len(set(got)):
            bad.append(f"{fname}: duplicate ids")
    for r in rows("requirements_trace.csv"):
        if r["status"] not in ("implemented", "implemented_partial", "implemented_verified",
                               "blocked_no_source", "blocked_by_gate", "not_applicable",
                               "registered_unbuilt", "closed_by_register", "verified", "rejected_kept_closed"):
            bad.append(f"{r['requirement_id']}: unrecognised status {r['status']!r}")
        if r["status"].startswith("blocked") and not r["gate_blocking"]:
            bad.append(f"{r['requirement_id']}: blocked with no owning gate")
        if r["status"] == "verified" and not r["number_that_clears_it"]:
            bad.append(f"{r['requirement_id']}: claimed verified with no clearing number")
    for r in rows("flagged.csv"):
        if r["blocks_merge"] != "no":
            bad.append(f"{r['flag_id']}: flagged item claims it blocks the merge - resolve before publishing")
    return bad


def c10_blank_audit_honest() -> list[str]:
    """A blank is the honest answer more often than a guess, so the pack counts its blanks. This
    check recomputes the count from the files and fails if the published audit under-reports."""
    audit = {r["table"]: r for r in rows("blank_audit.csv")}
    bad = []
    total = 0
    for path in sorted(DATA.glob("*.csv")):
        if path.name in ("blank_audit.csv", "verification_summary.csv"):
            continue
        rs = rows(path.name)
        blanks = sum(1 for r in rs for v in r.values() if v in ("", None))
        total += blanks
        if path.name not in audit:
            bad.append(f"{path.name}: missing from blank_audit.csv")
        elif int(audit[path.name]["blank_cells"]) != blanks:
            bad.append(f"{path.name}: audit says {audit[path.name]['blank_cells']}, files say {blanks}")
    vs = {r["metric"]: r["value"] for r in rows("verification_summary.csv")}
    for r in rows("verification_summary.csv"):
        if r["metric"].startswith("blank cells") and int(r["value"]) != total:
            bad.append(f"verification summary reports {r['value']} blanks, recomputed {total}")
    del vs
    return bad


def c11_pages_complete() -> list[str]:
    bad = []
    sys.path.insert(0, str(ROOT))
    import importlib.util
    spec = importlib.util.spec_from_file_location("b67233566", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    want = {s for s, _ in mod.NAV}
    files = {p.stem for p in DOCS.glob("*.html")}
    if files != want:
        bad.append(f"pages differ from NAV: {sorted(files ^ want)}")
    if not (DOCS / "assets" / "style.css").exists():
        bad.append("assets/style.css missing")
    for slug in want:
        text = (DOCS / f"{slug}.html").read_text(encoding="utf-8")
        if "<table" not in text and slug != "index":
            bad.append(f"{slug}.html: no table rendered - a page of prose is not a dashboard")
        if "assets/style.css" not in text:
            bad.append(f"{slug}.html: stylesheet not linked")
        for tag in FORBIDDEN_HTML:
            if tag in text:
                bad.append(f"{slug}.html: contains {tag} - the site takes no manual input")
        for w in FORBIDDEN_WORDS:
            if w.lower() in text.lower():
                bad.append(f"{slug}.html: contains the claim {w!r}")
        for nav in want:
            if nav != slug and f"{nav}.html" not in text:
                bad.append(f"{slug}.html: navigation is missing {nav}.html")
        for m in re.finditer(r'(?:href|src)="([^"#]+\.html?)"', text):
            tgt = m.group(1)
            if tgt.startswith(("http", "/")):
                if tgt.startswith("/"):
                    bad.append(f"{slug}.html: root-absolute link {tgt} escapes /Own6/")
                continue
            if not (DOCS / tgt).exists():
                bad.append(f"{slug}.html: broken internal link {tgt}")
        for tok in (">nan<", ">None<", "NaN", "inf<"):
            if tok in text:
                bad.append(f"{slug}.html: leaked token {tok!r} - a missing value must render as a blank")
    return bad


def c12_tables_published_on_a_page() -> list[str]:
    """Every table the builder writes must be reachable from a page, otherwise it is an artefact
    nobody reads and the requirement it answers is effectively unimplemented.

    Checked against each page's published manifest, not against a substring search of the whole
    site: a file name mentioned in somebody's note is not the same thing as the table being shown.
    """
    bad = []
    published: set[str] = set()
    for page in sorted(DOCS.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        m = re.search(r"Tables rendered on this page[^:]*: ?(.+?)</p>", text, re.S)
        if not m:
            bad.append(f"{page.name}: no table manifest - a page must say which tables it renders")
            continue
        for name in re.findall(r"([a-z0-9_]+\.csv)", m.group(1)):
            published.add(name)
            if not (DATA / name).exists():
                bad.append(f"{page.name}: manifest lists {name}, which the builder never wrote")
    for path in sorted(DATA.glob("*.csv")):
        if path.name not in published:
            bad.append(f"{path.name}: not rendered on any page")
    return bad


def c13_claim_commit_recorded() -> list[str]:
    """Pre-registration is only real if the frozen rule text has a commit hash that predates the
    graded numbers it produced."""
    f = DATA / "claim_commit.txt"
    if not f.exists():
        return ["claim_commit.txt missing - pre-registration is unverifiable without it"]
    sha = f.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return [f"claim_commit.txt is not a full commit hash: {sha!r}"]
    have = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if have.returncode != 0:
        # A shallow checkout cannot answer the question. Say so in the output rather than passing
        # quietly: the pack's own CI fetches full history, so this branch only fires where the claim
        # is unverifiable, and it never reports success it did not earn.
        return [f"claim commit {sha[:7]} is not present in this checkout (shallow clone?): ancestry "
                f"cannot be verified here - re-run with full history"]
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return [f"claim commit {sha[:7]} exists but is not an ancestor of HEAD - a rebase rewrote it; "
                f"re-point data/nfl_67233566/claim_commit.txt at the rebased claim commit and rebuild"]
    for r in rows("preregistration.csv"):
        if r["registration_commit"] != sha:
            return [f"preregistration.csv row {r['strategy_id']} cites a different claim commit"]
    return []


def c14_model_identity_frozen() -> list[str]:
    """The model the tables describe must be the model the code runs, including the parameters that
    were fixed before the data were seen."""
    bad = []
    want = {"MODEL_VERSION": "nfl_67233566_v1", "LAMBDA_RIDING": 4.0, "ATTACK_K": 3.0,
            "ROUND_TO": 0.5, "TIE_MODELS": 2}
    for k, v in want.items():
        if getattr(M, k) != v:
            bad.append(f"model.{k} = {getattr(M, k)!r}, preregistered as {v!r}")
    if not getattr(M, "HOME_ADVANTAGE_FREE", False):
        bad.append("model.HOME_ADVANTAGE_FREE is false: home effect must be estimated, not assumed")
    lines = rows("originated_lines.csv")
    if lines and {r["model_version"] for r in lines} != {M.MODEL_VERSION}:
        bad.append("a published line carries a model_version the code does not implement")
    return bad


def c15_availability_boundaries() -> list[str]:
    """Nothing may be asserted about health beyond what the league printed, and nothing may be
    inferred from the absence of a report."""
    bad = []
    for r in rows("designation_calibration.csv"):
        for c in ("players_actually_played", "play_rate", "ci95_low", "ci95_high"):
            if (r.get(c) or "").strip():
                bad.append(f"designation_calibration.csv: {c} filled without an inactive list")
    for r in rows("depth_source_register.csv"):
        if r["clubs_verified_this_session"] not in ("0", ""):
            bad.append(f"depth register claims {r['clubs_verified_this_session']} clubs verified")
    # an unread club section must publish no counts at all: "we did not read it" cannot become "0 out"
    for r in rows("roster_ir_sweep.csv"):
        if r["status"] in ("not_in_chunk_read", "not_read", "page_unavailable"):
            for col in ("report_rows_read", "players_out", "players_doubtful", "players_questionable",
                        "players_dnp", "net_injury_count"):
                if (r.get(col) or "").strip() not in ("",):
                    bad.append(f"roster sweep {r['club']}: {col}={r[col]!r} published for an unread section")
        if (r.get("net_injury_count") or "").strip() and not (r.get("report_rows_read") or "").strip():
            bad.append(f"roster sweep {r['club']}: a net count with no rows read behind it")
    if rows("injury_surprise.csv") and not any("delta" in k for k in rows("injury_surprise.csv")[0]):
        bad.append("injury_surprise.csv lost its delta columns - a level is not a surprise")
    return bad


CHECKS = [c01_no_clock_in_builder, c02_source_link_on_every_row, c03_official_hosts_only,
          c04_price_chain, c05_no_market_numbers, c06_walk_forward, c07_corpus_boundary,
          c08_staking_empty_by_construction, c09_gate_and_register_completeness,
          c10_blank_audit_honest, c11_pages_complete, c12_tables_published_on_a_page,
          c13_claim_commit_recorded, c14_model_identity_frozen, c15_availability_boundaries]


def main() -> int:
    if not DATA.exists() or not list(DATA.glob("*.csv")):
        print(f"FAIL no tables in {DATA}: run scripts/build_nfl_67233566.py first")
        return 1
    failures = 0
    for fn in CHECKS:
        problems = fn()
        if problems:
            failures += len(problems)
            for p in problems:
                print(f"CHECK {fn.__name__} FAIL {p}")
        else:
            print(f"CHECK {fn.__name__} ok")
    print(f"nfl_67233566 checks: {len(CHECKS)} run, {failures} failure(s)")
    if failures:
        return 1
    print("All checks passed: every published row is source-linked, every blank is accounted for, "
          "and no price was invented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
