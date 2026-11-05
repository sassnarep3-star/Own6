#!/usr/bin/env python3
"""Offline, reproducible current-tree audit; never certifies a link as a fact.

Scans every line of every non-generated tracked text file, parses Python/JSON/CSV,
inventories checksums, and reviews every legacy data record. Direct external-source
review is a separate, manually recorded register in data/assurance/sources.csv.
No network collection, NBA statistics import, or synthetic performance is performed.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "assurance"
BASE = "86eca0f"
REPO = "https://github.com/sassnarep3-star/Own6"
BRANCH = "arena/74d27b5d-own6"
TERMS = "https://www.nba.com/termsofuse#nba-statistics"
GENERATED = {"data/assurance/inventory.csv", "data/assurance/row_audit.csv", "data/assurance/findings.csv", "data/assurance/summary.json"}
# The assurance dashboard renders the inventory; inventorying its own generated HTML
# would create a self-referential checksum loop. It is verified by check_assurance.py.
GENERATED_PREFIXES = ("docs/assurance/", "docs/coverage/", "data/source_coverage/")
OFFICIAL_SUFFIXES = (
    "nba.com", "github.com", "github.io", "docs.github.com", "scikit-learn.org",
    "scipy.org", "nist.gov", "statsmodels.org", "python.org", "law.go.kr", "draftkings.com",
)
URL = re.compile(r"https?://[^\s\"'<>]+")
MARKER = re.compile(r"^(<<<<<<<(?: .*)?|=======|>>>>>>>(?: .*)?)$")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def official(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def files() -> list[Path]:
    names = set(git("ls-files", "-z").split("\0"))
    names.update(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    return sorted(ROOT / n for n in names if n and (ROOT / n).is_file() and n not in GENERATED and not n.startswith(GENERATED_PREFIXES))


def record_source(row: dict) -> str:
    for key in ("source_url", "url", "official_source_url", "source_market", "contract_url", "feature_source_url"):
        value = str(row.get(key) or "").strip()
        if value.startswith("https://"):
            return value.rstrip(".,);")
    return ""


def row_review(path: Path, number: int, row: dict, category: str) -> dict:
    url = record_source(row)
    has_official = official(url)
    if category == "source_registry":
        status, note = "registry_record", "Source metadata only; direct-read status is not confirmation of any NBA numeric value."
    elif category == "review_ledger":
        status, note = "review_record", "An audit/review statement, not an empirical observation. Original evidence must be checked separately."
    elif category == "project_design":
        status, note = "project_design", "Compiler specification. Official references define vocabulary or constraints, not an edge or measured result."
    elif category == "empty_contract":
        status, note = "not_run", "No authorized observation or residual is present."
    elif has_official:
        status, note = "unverified", "An official reference is present, but this record was not independently matched to an authorized, immutable source snapshot. Values are not certified."
    else:
        status, note = "unverified", "No official value-level source is established. Secondary, local or missing provenance cannot verify the record; do not infer a value."
    if path.name in {"market_lines_2026-11-02.csv", "player_props_2026-11-02.csv", "our_lines_2026-11-02.csv"}:
        note += " ESPN is not the official NBA or the named sportsbook; quotes are historical and lack an executable-price audit."
    if path.name == "correlation_findings.csv":
        note += " No paired residual ledger, uncertainty interval or authorized training-only provenance accompanies this estimate."
    if path.name == "team_ratings_2026-27.csv":
        note += " A mutable season-filtered stats URL does not identify the historical snapshot."
    return {
        "file": path.relative_to(ROOT).as_posix(), "row": number, "category": category,
        "record_id": str(row.get("id") or row.get("game_id") or row.get("event_id") or row.get("team_abbr") or row.get("pair") or row.get("article") or number),
        "source_url": url, "official_source_present": has_official, "value_verification": status,
        "review_note": note, "official_scope_reference": TERMS,
        "record_url": f"{REPO}/blob/{BASE}/{path.relative_to(ROOT).as_posix()}",
    }


def audit_data(path: Path) -> list[dict]:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("data/assurance/"):
        return []
    if path.suffix == ".csv":
        text = path.read_text(encoding="utf-8")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"invalid CSV header: {rel}")
        if path.name in {"sources.csv", "verification_log.csv"}:
            category = "source_registry"
        elif path.name in {"flags.csv", "flagged_items.csv", "repo_findings.csv", "source_audit.csv", "repo_inventory.csv"}:
            category = "review_ledger"
        elif rel in {"data/empirical/report.csv", "data/methodology.json"}:
            category = "project_design"
        elif rel in {"data/empirical/observations.csv", "data/empirical/residuals.csv", "data/empirical/closing_probabilities.csv"}:
            category = "empty_contract"
        else:
            category = "legacy_data"
        return [row_review(path, i, row, category) for i, row in enumerate(reader, 2)]
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            rows = data["rows"]
        elif isinstance(data, dict) and isinstance(data.get("gates"), list):
            rows = data["gates"]
        elif rel == "data/empirical/report.json":
            rows = data.get("strategies", []) + data.get("correlations", [])
        else:
            rows = [data] if isinstance(data, dict) else data
        category = "source_registry" if path.name == "sources.json" else "review_ledger" if path.name == "flags.json" else "project_design" if path.name in {"methodology.json", "licenses.json", "evidence.json", "report.json"} else "legacy_data"
        return [row_review(path, i, row, category) for i, row in enumerate(rows, 1) if isinstance(row, dict)]
    return []


# Findings refer to immutable upstream code, not to the repaired working tree.
# Each tuple: id, severity, path, lines, title, detail, action, source id, status, evidence.
REVIEWS = [
    ("A-F01", "high", "docs/index.html", "1,4,6", "Committed merge markers", "Three conflict-marker lines were present at initial checkout 92cae24.", "Resolved by concurrent PR #26; release gate now rejects marker regressions.", "A-S16", "resolved_upstream", "<<<<<<< HEAD"),
    ("A-F02", "high", "scripts/model.py", "197-203", "Incorrect American-odds conversion", "Legacy imp() uses 100/positive_odds and -negative_odds/100. Official formulas use odds+100 in the denominator. At -110/+110 it yields 0.5475 rather than 0.5238 for the normalized favorite.", "Quarantine legacy model probabilities/edges. Use the tested strict conversion in nba_lab.pricing; do not repair historical outputs by guessing.", "A-S17", "open", "return 100.0 / ml if ml > 0 else -ml / 100.0"),
    ("A-F03", "high", "nba_lab/experiments.py", "24-31", "Audit gates accept self-asserted booleans", "Any truthy JSON value can satisfy external evidence keys; no audit artifact, reviewer, digest or scope is checked.", "Require structured evidence records bound to source/config digests; missing evidence stays blocked.", "A-S10", "resolved_in_session", 'evidence[key] = bool(data.get(key, False))'),
    ("A-F04", "high", "nba_lab/experiments.py", "54-94", "Correlation parser discards valid zeros", "The truthiness filter removes zero residuals, truncates unequal arrays, ignores split and event IDs, and can label an unverified estimate computed.", "Use a strict one-row-per-event training-only contract; retain zeros, reject missing values, and cluster the interval.", "A-S14", "resolved_in_session", "if x and y"),
    ("A-F05", "high", "nba_lab/gates.py", "120-125", "Declared dependence and ledger checks are weak", "A dependence string and global booleans do not establish a joint model, paired sample, immutable preregistration or audited ledger.", "Bind combo gates to actual training residuals and gate G10 to a versioned registration and audit manifest.", "A-S14", "resolved_in_session", 'o.dependence_evidence == "verified"'),
    ("A-F06", "high", "nba_lab/gates.py", "88-97", "Luck correction does not control the ranking test", "The Poisson-binomial win-count diagnostic assumes independent trials; padding its p-value with ones does not adjust clustered ROI or proper-score tests.", "Use a common slate-cluster bootstrap family and adjust the actual qualification p-values; retain the win-count test only as a labeled diagnostic.", "A-S12", "resolved_in_session", "[raw_p] + [1.0] * (family_size - 1)"),
    ("A-F07", "medium", "nba_lab/contracts.py", "132-145", "Raw-price CLV and line handling confound comparisons", "Raw offered/closing prices include changing margin. Forcing equal lines rejects moved-line observations instead of recording unavailable comparable CLV.", "Compare de-vigged same-side probabilities at identical lines; leave moved-line CLV blank and block its gate.", "A-S17", "resolved_in_session", "math.log(self.decimal_odds / self.closing_decimal_odds)"),
    ("A-F08", "high", "nba_lab/registry.py", "19-32", "Sample floor is not a power analysis", "The 200-event floor is a policy choice, not a demonstrated power guarantee. Documentation alternates between game and slate clustering.", "Use slate clusters for cross-game dependence, disclose the policy floor, and require a training-only power/precision analysis before qualification.", "A-S11", "resolved_in_session", '"min_events": 200'),
    ("A-F09", "high", "nba_lab/contracts.py", "121-164", "Selection and market contracts are not bound to the strategy", "Rows can use the wrong market, omit the declared edge/EV thresholds, or reuse one event with inconsistent start times.", "Enforce strategy-market identity, frozen selection thresholds and consistent event timestamps across the entire ledger.", "A-S10", "resolved_in_session", 'if market not in MARKETS:'),
    ("A-F10", "medium", "nba_lab/models.py", "69-85", "Prop history excludes zero-minute games", "Rejecting all zero-minute observations can condition the fit on playing and bias minutes/scoring upward. DNP settlement is a separate provider rule.", "Retain authorized prior zero-minute participation observations in the rate fit; require explicit DNP settlement before selecting a prop.", "A-S05", "resolved_in_session", "np.any(m <= 0)"),
    ("A-F11", "high", "scripts/verify_data.py", "1-9,31-53", "Internal consistency is labeled source verification", "The script checks URL presence and agreement among local tables, not whether values match official sources.", "Label all 213 checks as internal recomputation/structure; they do not certify the underlying scores, ratings or odds.", "A-S02", "open", "Line-by-line verification of collected NBA data."),
    ("A-F12", "high", "data/correlation_findings.csv", "2-5", "Legacy correlations lack qualification evidence", "Estimates include a six-game player pair and pooled same-date pairs without a paired residual ledger, clustered intervals or multiplicity control.", "Leave current correlation estimates blank in the assurance view; preserve historical claims only as flagged archive records.", "A-S14", "open", "teammate_PTS_Mitchell_Allen"),
    ("A-F13", "medium", "README.md", "9,23-32", "Conflicting data-availability statements", "The README says no historical data or quotes are included while also linking 92 results and historical ESPN/DraftKings rows.", "Distinguish the empty authorized empirical ledger from unverified legacy archives.", "A-S16", "open", "No historical data or sportsbook quotes are included here"),
    ("A-F14", "medium", "data/legal_kr.json", "all rows", "Statute article body not independently reproduced", "The official version header is readable, but the article body remains dynamic. Korean-law rows are not independently recertified.", "Keep article-level claims flagged; do not infer applicability from the user's location or the repository's language.", "A-S21", "open", '"article"'),
    ("A-F15", "low", "LICENSE", "missing", "Code license not specified", "No root LICENSE file exists. Public visibility is not a code or data license.", "Owner must choose code licensing separately from third-party data rights; no license is inferred.", "A-S16", "open", ""),
    ("A-F16", "medium", "scripts/check_lab.py", "baseline before PR #24", "Lab checker did not inspect table contents", "The earlier checker missed generator-object table rendering. Concurrent PR #24 added structural table checks.", "Preserve the upstream repair and add assurance-specific source/status checks without duplicating its scope.", "A-S16", "resolved_upstream", "def check_site():"),
    ("A-F17", "medium", "nba_lab/pricing.py", "49-53", "Fair American price invented a margin", "The earlier fair-price helper subtracted an arbitrary 10 from the negative-odds conversion, mapping even money to -110 rather than a fair +100.", "Use the inverse official American conversion with no added vig; even money is +100.", "A-S17", "resolved_in_session", "- 10) if p >= 0.5"),
]


def findings() -> list[dict]:
    sources = {r["id"]: r["url"] for r in csv.DictReader((OUT / "sources.csv").open(newline="", encoding="utf-8"))}
    rows = []
    for ident, severity, path, lines, title, detail, action, source, status, evidence in REVIEWS:
        if evidence and status == "open":
            original = git("show", f"{BASE}:{path}")
            if evidence not in original:
                raise ValueError(f"finding evidence no longer matches baseline: {ident}")
            current_path = ROOT / path
            if current_path.exists() and evidence not in current_path.read_text(encoding="utf-8"):
                status = "resolved_upstream"
        if status == "resolved_upstream" and path.endswith("index.html"):
            current = (ROOT / path).read_text(encoding="utf-8")
            if any(MARKER.fullmatch(line) for line in current.splitlines()):
                raise ValueError(f"unresolved marker: {path}")
        rows.append({"id": ident, "severity": severity, "file": path, "lines": lines, "finding": title,
                     "detail": detail, "action": action, "source_url": sources[source], "status": status,
                     "code_url": f"{REPO}/blob/{BASE}/{path}", "reviewed_on": "2026-11-03"})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory, records, anomalies = [], [], []
    lines_scanned = 0
    for path in files():
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines()
        lines_scanned += len(lines)
        kind = {".py": "python", ".json": "json", ".csv": "data", ".html": "html", ".md": "documentation", ".css": "stylesheet", ".js": "javascript", ".yml": "configuration"}.get(path.suffix, "text")
        for number, line in enumerate(lines, 1):
            if MARKER.fullmatch(line):
                anomalies.append({"file": rel, "line": number, "issue": "unresolved merge marker"})
        if path.suffix == ".py":
            ast.parse(text, filename=rel)
        if path.suffix == ".json":
            json.loads(text)
        records.extend(audit_data(path))
        try:
            unchanged = git("show", f"{BASE}:{rel}").encode("utf-8") == raw
        except subprocess.CalledProcessError:
            unchanged = False
        inventory.append({"path": rel, "lines": len(lines), "bytes": len(raw), "sha256": sha(raw),
                          "kind": kind, "review_scope": "every line structurally scanned; syntax/schema checked where applicable; not external fact certification",
                          "source_url": f"{REPO}/blob/{BASE if unchanged else BRANCH}/{rel}"})
    review = findings()
    write_csv("inventory.csv", list(inventory[0]), inventory)
    write_csv("row_audit.csv", ["file", "row", "category", "record_id", "source_url", "official_source_present", "value_verification", "review_note", "official_scope_reference", "record_url"], records)
    write_csv("findings.csv", list(review[0]), review)
    summary = {
        "reviewed_on": "2026-11-03", "baseline_commit": BASE, "files_inventoried": len(inventory),
        "lines_scanned": lines_scanned, "data_records_reviewed": len(records),
        "record_categories": dict(Counter(r["category"] for r in records)),
        "record_statuses": dict(Counter(r["value_verification"] for r in records)),
        "findings": len(review), "open_findings_at_baseline": sum(r["status"] == "open" for r in review),
        "resolved_in_session": sum(r["status"] == "resolved_in_session" for r in review),
        "resolved_upstream": sum(r["status"] == "resolved_upstream" for r in review),
        "structural_anomalies": anomalies,
        "external_source_policy": "Direct source reads are recorded separately. A URL, checksum or internal consistency check does not verify an external fact or grant rights.",
        "rights_status": "No authorized gambling-use data feed or license is configured.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if anomalies:
        raise SystemExit(f"Structural anomalies: {anomalies}")
    print(f"AUDIT: {len(inventory)} files / {lines_scanned} lines scanned; {len(records)} data records reviewed; {len(review)} findings recorded.")
    print("External numeric claims remain unverified unless separately matched to an authorized official snapshot. No data were collected.")


if __name__ == "__main__":
    main()
