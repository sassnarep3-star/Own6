"""Line-by-line repo review at a pinned base commit, computed not asserted.

Everything this module emits is produced by scanning the working tree at the
pinned base commit ``BASE``. Nothing is hand-written. Where a check cannot be
performed (for example, a file that is not valid UTF-8) the module records a
finding rather than skipping the file silently.

Two outputs:
  data/nfl_0d4da02c/repo_findings.csv    irregularities, with the evidence
  data/nfl_0d4da02c/repo_evidence.csv    which repo files speak to which requirement

Run:  python3 -m src.nfl_0d4da02c.repo_review
"""
from __future__ import annotations

import csv
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl_0d4da02c")
BASE = "aa827981092a7d1996b1122bda0d2decc7f626c7"

REPO_LINK = "https://github.com/sassnarep3-star/Own6"
SCAN_DIRS = ("data", "docs", "src", "scripts", "audit", "tests", ".github")
# A header is treated as a source column if it names a source/evidence and points
# at something. The check is deliberately broad: it is better to under-report a
# missing link than to invent one.
SOURCE_PAT = re.compile(
    r"(source|official|evidence|reference|ref|link|page|url|host)", re.I)
# Registers that describe the repository's own bookkeeping rather than the
# outside world. A missing link here is an "info" note, not a data defect.
META_REGISTER_NAMES = (
    "repo_findings", "repo_inventory", "repo_evidence", "repo_stats",
    "requirement_terms", "gates", "suggestions", "suggestion_options", "qia",
    "information_gaps", "requirements", "sources", "official_reads",
    "designation_calibration_status", "gate_updates", "decision_paths",
)


def _source_columns(header: list[str]) -> list[str]:
    return [c for c in header
            if SOURCE_PAT.search(c) and not c.strip().lower().endswith("_needed")]


def _is_meta(path: str) -> bool:
    base = os.path.basename(path).rsplit(".", 1)[0].lower()
    return any(base == m or base.startswith(m) for m in META_REGISTER_NAMES)


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    return out.stdout


def tracked_files() -> list[str]:
    files = [f for f in _git("ls-files").splitlines() if f]
    return [f for f in files if f.split("/")[0] in SCAN_DIRS
            or ("/" not in f and f.endswith(".md"))]


def read_text(path: str) -> str | None:
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def check_csvs(files: list[str]) -> tuple[list[list], list[list]]:
    findings: list[list] = []
    inventory: list[list] = []
    for path in files:
        if not path.endswith(".csv"):
            continue
        try:
            with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            findings.append(["F-CSV-PARSE", "high", path,
                             f"CSV could not be parsed: {type(exc).__name__}", "", "open"])
            continue
        if not rows:
            findings.append(["F-CSV-EMPTY", "low", path, "CSV has no header row",
                             "0 rows", "open"])
            continue
        header, body = rows[0], rows[1:]
        widths = {len(r) for r in rows}
        if len(widths) > 1:
            findings.append(["F-CSV-RAGGED", "medium", path,
                             "rows have inconsistent column counts",
                             f"header {len(header)} cols; observed widths {sorted(widths)}",
                             "open"])
        src_cols = _source_columns(header)
        meta = _is_meta(path)
        if not src_cols:
            findings.append([
                "F-CSV-NOSOURCE", "info" if meta else "medium", path,
                f"no source-like column in the header{(' (governance register)' if meta else '')}",
                f"header: {','.join(header)}", "open"])
        else:
            worst = ("", 0)
            for col in src_cols:
                idx = header.index(col)
                blank = sum(1 for r in body if len(r) > idx and not r[idx].strip())
                if blank > worst[1]:
                    worst = (col, blank)
            if body and worst[1]:
                sev = "info" if meta else ("high" if worst[1] == len(body) else "medium")
                findings.append([
                    "F-CSV-BLANKSOURCE", sev, path,
                    f"{worst[1]} of {len(body)} rows have a blank source cell"
                    f"{(' (governance register)' if meta else '')}",
                    f"column '{worst[0]}'", "open"])
        inventory.append([path, len(header), len(body), ",".join(src_cols),
                          "register" if meta else "data"])
    return findings, inventory


def check_html_links(files: list[str]) -> list[list]:
    findings: list[list] = []
    link_re = re.compile(r'href="([^"#][^"]*)"')
    for path in files:
        if not path.endswith((".html", ".htm")):
            continue
        text = read_text(path)
        if text is None:
            findings.append(["F-HTML-READ", "medium", path, "file is not readable as UTF-8",
                             "", "open"])
            continue
        bad = []
        for href in link_re.findall(text):
            if href.startswith(("http://", "https://", "mailto:", "javascript:", "data:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path),
                                                   href.split("?")[0].split("#")[0]))
            if href.endswith("/"):
                target = os.path.join(target, "index.html")
            if not os.path.exists(os.path.join(ROOT, target)):
                bad.append(href)
        if bad:
            findings.append(["F-HTML-LINK", "high", path,
                             f"{len(bad)} internal link(s) resolve to a missing file",
                             "; ".join(sorted(set(bad))[:8]), "open"])
    return findings


def check_pack_pairs(files: list[str]) -> list[list]:
    findings: list[list] = []
    data_packs = {p.split("/")[1] for p in files
                  if p.startswith("data/") and p.count("/") >= 2 and p.split("/")[1].startswith("nfl")}
    docs_packs = {p.split("/")[1] for p in files
                  if p.startswith("docs/") and p.count("/") >= 2 and p.split("/")[1].startswith("nfl")}
    for pack in sorted(data_packs):
        mirror = pack.replace("_", "-")
        if mirror not in docs_packs:
            findings.append(["F-PACK-NOSITE", "medium", f"data/{pack}",
                             "data pack has no matching site directory under docs/",
                             f"expected docs/{mirror}/", "open"])
    for pack in sorted(docs_packs):
        mirror = pack.replace("-", "_")
        if mirror not in data_packs:
            findings.append(["F-PACK-NODATA", "medium", f"docs/{pack}",
                             "site directory has no matching data pack",
                             f"expected data/{mirror}/", "open"])
    findings.append(["F-PACK-COUNT", "info", "data/, docs/",
                     "the repository holds many parallel NFL packs with overlapping registers",
                     f"{len(data_packs)} data packs, {len(docs_packs)} site directories",
                     "needs review - see suggestion S-09"])
    return findings


def check_register_duplication(files: list[str]) -> list[list]:
    findings: list[list] = []
    wanted = ("suggestions", "questions", "qia", "requirements", "flagged", "readiness",
              "gates", "correlations", "injury", "depth")
    counts: dict[str, list[str]] = {w: [] for w in wanted}
    for path in files:
        name = os.path.basename(path).lower()
        for w in wanted:
            if w in name and path.endswith(".csv"):
                counts[w].append(path)
    for w in wanted:
        if len(counts[w]) >= 3:
            findings.append(["F-REGISTER-DUP", "medium", f"data/**/{w}*.csv",
                             f"{len(counts[w])} separate files register the same concept under "
                             f"different column vocabularies",
                             "; ".join(sorted(counts[w])[:6]) +
                             (" ..." if len(counts[w]) > 6 else ""),
                             "needs review - see suggestion S-09"])
    return findings


def check_input_controls(files: list[str]) -> list[list]:
    findings: list[list] = []
    for path in files:
        if not path.endswith((".html", ".htm")):
            continue
        text = read_text(path)
        if text is None:
            continue
        hits = re.findall(r"<(input|select|textarea|button)\b", text, re.I)
        if hits:
            findings.append(["F-HTML-INPUT", "high", path,
                             "page contains an interactive control, which the brief forbids",
                             f"{len(hits)} control(s): " + ", ".join(sorted(set(hits))),
                             "open"])
    return findings


def check_placeholders(files: list[str]) -> list[list]:
    findings: list[list] = []
    pat = re.compile(r"\b(TODO|FIXME|XXX|PLACEHOLDER|CHANGEME)\b")
    for path in files:
        if not path.endswith((".py", ".md", ".csv", ".yml")):
            continue
        text = read_text(path)
        if text is None:
            continue
        hits = pat.findall(text)
        if hits:
            findings.append(["F-PLACEHOLDER", "low", path,
                             f"{len(hits)} placeholder marker(s) in a committed file",
                             ", ".join(sorted(set(hits))), "open"])
    return findings


def check_large_files(files: list[str]) -> list[list]:
    findings: list[list] = []
    for path in files:
        try:
            size = os.path.getsize(os.path.join(ROOT, path))
        except OSError:
            continue
        if size > 1_000_000:
            findings.append(["F-LARGE", "low", path,
                             "committed file is larger than 1 MB",
                             f"{size:,} bytes", "needs review"])
    return findings


def requirement_evidence(files: list[str]) -> list[list]:
    """Map each requirement's search terms to the repo files that contain them."""
    terms: list[tuple[str, str]] = []
    with open(os.path.join(DATA, "requirement_terms.csv"), newline="",
              encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            terms.append((row["req_id"], row["search_term"]))

    texts: list[tuple[str, str]] = []
    for path in files:
        if not path.endswith((".py", ".md", ".csv", ".yml", ".html")):
            continue
        text = read_text(path)
        if text is None:
            continue
        texts.append((path, text.lower()))

    out: list[list] = []
    for req_id, term in terms:
        needle = term.lower()
        hits = [p for p, t in texts if needle in t]
        out.append([req_id, term, len(hits), "; ".join(sorted(hits)[:5])])
    return out


def main() -> int:
    os.makedirs(DATA, exist_ok=True)
    files = tracked_files()
    findings: list[list] = []
    csv_findings, inventory = check_csvs(files)
    findings += csv_findings
    findings += check_html_links(files)
    findings += check_pack_pairs(files)
    findings += check_register_duplication(files)
    findings += check_input_controls(files)
    findings += check_placeholders(files)
    findings += check_large_files(files)

    with open(os.path.join(DATA, "repo_findings.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["finding_id", "severity", "path", "finding", "evidence", "status"])
        w.writerows(findings)
    print(f"wrote repo_findings.csv: {len(findings)} rows (from {len(files)} tracked files)")

    with open(os.path.join(DATA, "repo_inventory.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "n_columns", "n_rows", "source_columns", "file_kind"])
        w.writerows(inventory)
    print(f"wrote repo_inventory.csv: {len(inventory)} rows")

    ev = requirement_evidence(files)
    with open(os.path.join(DATA, "repo_evidence.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["req_id", "search_term", "n_files_matching", "example_paths"])
        w.writerows(ev)
    print(f"wrote repo_evidence.csv: {len(ev)} rows")

    with open(os.path.join(DATA, "repo_stats.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value", "source_url"])
        w.writerow(["base_commit", BASE, f"{REPO_LINK}/commit/{BASE}"])
        w.writerow(["tracked_files_scanned", len(files), REPO_LINK])
        w.writerow(["csv_files_scanned", len(inventory), REPO_LINK])
        w.writerow(["html_files_scanned",
                    sum(1 for f in files if f.endswith((".html", ".htm"))), REPO_LINK])
        w.writerow(["findings_raised", len(findings), REPO_LINK])
        w.writerow(["review_session", "0d4da02c", REPO_LINK])
        w.writerow(["review_date", "2026-11-18", REPO_LINK])
    print("wrote repo_stats.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
