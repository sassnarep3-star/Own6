#!/usr/bin/env python3
"""Publication acceptance audit.

What this answers, and what it deliberately does not:

* It checks facts that can be established from a primary source reachable in
  this environment: the GitHub API (repository, pull requests, Pages builds)
  and the committed tree itself.
* It does **not** certify any NBA number, odds quote, statute article or
  empirical result.  Those sources were unreachable from this sandbox, so they
  are recorded as unverified rather than re-labelled.

Outputs (deterministic given the cached API snapshot):
  data/acceptance/github_state.json   cached API snapshot (input, refreshed with --refresh)
  data/acceptance/pr_ledger.csv       every PR referenced in COORDINATION.md, with API state
  data/acceptance/pages.csv           every published HTML page, provenance and reachability
  data/acceptance/claims.csv          claim-by-claim verification records
  data/acceptance/summary.json        counts used by the site page

Usage:
  python3 scripts/acceptance_audit.py --refresh   # fetch the API snapshot, then rebuild
  python3 scripts/acceptance_audit.py             # rebuild from the cached snapshot
  python3 scripts/acceptance_audit.py --check     # fail if committed outputs are stale
"""

from __future__ import annotations

import argparse
import csv
import html.parser
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "acceptance"
STATE = OUT / "github_state.json"
REPO = "sassnarep3-star/Own6"
API = f"https://api.github.com/repos/{REPO}"
HTML_REPO = f"https://github.com/{REPO}/blob/main/"

# Generated directories in docs/ and the script that owns them.  A page whose
# directory has no generator is listed as hand-maintained (a provenance gap to
# review, not a factual error).
GENERATORS = {
    "hub": "scripts/build_hub.py",
    "lab": "scripts/build_lab.py",
    "coverage": "scripts/source_coverage.py",
    "verified": "scripts/build_site.py",
    "own6": "scripts/build_site_own6.py",
    "review": "tools/build_review.py",
    "reverification": "scripts/build_reverification.py",
    "verify": "scripts/build_verify.py",
    "luck": "scripts/build_luck.py",
}

OFFICIAL_HOSTS = {
    "www.nba.com",
    "official.nba.com",
    "www.law.go.kr",
    "law.go.kr",
    "docs.github.com",
    "github.com",
    "www.itl.nist.gov",
    "docs.scipy.org",
    "numpy.org",
    "www.statsmodels.org",
    "scikit-learn.org",
    "www.python.org",
}

LEGACY_UNLINKED = {"dashboard.html"}  # intentionally not linked (see flag H01)


class Page(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.links: list[str] = []
        self.rows = 0
        self._in_title = False
        self._in_h1 = False
        self._in_tbody = False
        self._in_row = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == "title":
            self._in_title = True
        elif tag == "h1" and not self.h1:
            self._in_h1 = True
        elif tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._in_row = True
            self.rows += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "tbody":
            self._in_tbody = False
        elif tag == "tr":
            self._in_row = False

    def handle_data(self, data):
        text = " ".join(data.split())
        if self._in_title and text:
            self.title += (" " if self.title else "") + text
        if self._in_h1 and text and not self.h1:
            self.h1 = text


def gh_json(path: str) -> object:
    result = subprocess.run(
        ["gh", "api", "--paginate", f"{API}/{path}"], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "gh api failed")
    # --paginate concatenates arrays; join them defensively.
    chunks = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            chunks.append(line)
    payload = "\n".join(chunks)
    decoder = json.JSONDecoder()
    items = []
    index = 0
    while index < len(payload):
        while index < len(payload) and payload[index] in " \n\r\t":
            index += 1
        if index >= len(payload):
            break
        obj, end = decoder.raw_decode(payload, index)
        items.extend(obj if isinstance(obj, list) else [obj])
        index = end
    return items


def refresh() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone

    state = {
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoints": {},
        "pulls": [],
        "pages": {},
        "builds": [],
        "main_commit": {},
    }
    pulls = gh_json("pulls?state=all&per_page=100")
    state["endpoints"]["pulls"] = f"{API}/pulls?state=all&per_page=100"
    for pull in pulls:
        state["pulls"].append(
            {
                "number": pull["number"],
                "title": pull["title"],
                "state": pull["state"],
                "merged": bool(pull.get("merged_at")),
                "merged_at": pull.get("merged_at"),
                "merge_commit_sha": pull.get("merge_commit_sha"),
                "base": pull["base"]["ref"],
                "head": pull["head"]["ref"],
                "html_url": pull["html_url"],
            }
        )
    state["endpoints"]["pages"] = f"{API}/pages"
    pages = gh_json("pages")[0]
    state["pages"] = {
        "status": pages.get("status"),
        "html_url": pages.get("html_url"),
        "source_branch": pages.get("source", {}).get("branch"),
        "source_path": pages.get("source", {}).get("path"),
        "build_type": pages.get("build_type"),
        "https_enforced": pages.get("https_enforced"),
    }
    state["endpoints"]["builds"] = f"{API}/pages/builds?per_page=5"
    for build in gh_json("pages/builds?per_page=5"):
        state["builds"].append(
            {
                "status": build.get("status"),
                "commit": build.get("commit"),
                "created_at": build.get("created_at"),
                "updated_at": build.get("updated_at"),
                "error": (build.get("error") or {}).get("message"),
            }
        )
    state["endpoints"]["main_commit"] = f"{API}/commits/main"
    commit = gh_json("commits/main")[0]
    state["main_commit"] = {"sha": commit["sha"], "date": commit["commit"]["committer"]["date"]}
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"refreshed {STATE.relative_to(ROOT)} at {state['fetched_at_utc']}")


def load_state() -> dict:
    if not STATE.exists():
        raise SystemExit("data/acceptance/github_state.json missing; run with --refresh")
    return json.loads(STATE.read_text(encoding="utf-8"))


def page_inventory() -> list[dict[str, object]]:
    docs = ROOT / "docs"
    pages: dict[str, Page] = {}
    for path in sorted(docs.rglob("*.html")):
        parser = Page()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        pages[path.relative_to(docs).as_posix()] = parser

    inbound: dict[str, set[str]] = {name: set() for name in pages}
    for name, parser in pages.items():
        base = (docs / name).parent
        for link in parser.links:
            if link.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            target = (base / link.split("#")[0].split("?")[0]).resolve()
            try:
                rel = target.relative_to(docs).as_posix()
            except ValueError:
                continue
            if target.is_dir() or rel == ".":
                rel = (Path(rel) / "index.html").as_posix().lstrip("./")
            for candidate in (rel, rel.rstrip("/") + "/index.html"):
                if candidate in pages and candidate != name:
                    inbound[candidate].add(name)

    rows = []
    for name, parser in pages.items():
        section = name.split("/")[0] if "/" in name else "(root)"
        generator = GENERATORS.get(section, "")
        if section == "(root)" and name != "index.html":
            generator = "hand-maintained (legacy root page)"
        elif name == "index.html":
            generator = "hand-maintained landing page (integration sessions)"
        official = 0
        external = 0
        for link in parser.links:
            host = urlparse(link).hostname
            if not host:
                continue
            external += 1
            if host in OFFICIAL_HOSTS:
                official += 1
        rows.append(
            {
                "page": f"docs/{name}",
                "title": parser.title,
                "heading": parser.h1,
                "section": section,
                "generator": generator,
                "generator_exists": "yes"
                if generator and (ROOT / generator).exists()
                else ("n/a" if generator.startswith("hand") else "NO"),
                "table_rows": parser.rows,
                "external_links": external,
                "official_links": official,
                "inbound_links": len(inbound[name]),
                "orphan": "yes" if not inbound[name] and name != "index.html" else "no",
                "intentional_orphan": "yes" if name in LEGACY_UNLINKED else "no",
                "evidence_url": f"{HTML_REPO}docs/{name}",
            }
        )
    return rows


def internal_link_issues(pages: list[dict[str, object]]) -> int:
    """Count local hrefs/srcs that do not resolve to a file under docs/."""
    docs = ROOT / "docs"
    issues = 0
    for path in docs.rglob("*.html"):
        parser = Page()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        for link in parser.links:
            if link.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
                continue
            target = (path.parent / link.split("#")[0].split("?")[0]).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                issues += 1
    return issues


def merge_markers() -> int:
    count = 0
    for path in list((ROOT / "docs").rglob("*.html")) + list(ROOT.glob("*.md")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(("<<<<<<<", "=======")) or re.match(r"^>{7}(\s|$)", line):
                if line.startswith("=======") and len(line) > 7:
                    continue
                count += 1
    return count


def plain_http_external() -> int:
    docs = ROOT / "docs"
    count = 0
    for path in docs.rglob("*.html"):
        parser = Page()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        count += sum(1 for link in parser.links if link.startswith("http://"))
    return count


def pr_references() -> list[int]:
    text = (ROOT / "COORDINATION.md").read_text(encoding="utf-8")
    numbers = set(int(n) for n in re.findall(rf"https://github\.com/{REPO}/pull/(\d+)", text))
    numbers |= set(int(n) for n in re.findall(r"PR\s*\*\*#(\d+)\*\*", text))
    numbers |= set(int(n) for n in re.findall(r"PR\s+#(\d+)", text))
    return sorted(numbers)


def build() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict]:
    state = load_state()
    pages = page_inventory()
    pulls_by_number = {pull["number"]: pull for pull in state["pulls"]}

    ledger: list[dict[str, object]] = []
    for number in pr_references():
        pull = pulls_by_number.get(number)
        if pull is None:
            ledger.append(
                {
                    "pr": number,
                    "title": "",
                    "state": "not_found_in_api_snapshot",
                    "merged": "unknown",
                    "merged_at": "",
                    "merge_commit_sha": "",
                    "head": "",
                    "evidence_url": f"https://github.com/{REPO}/pull/{number}",
                }
            )
            continue
        ledger.append(
            {
                "pr": number,
                "title": pull["title"],
                "state": pull["state"],
                "merged": "yes" if pull["merged"] else "no",
                "merged_at": pull["merged_at"] or "",
                "merge_commit_sha": pull["merge_commit_sha"] or "",
                "head": pull["head"],
                "evidence_url": pull["html_url"],
            }
        )

    claims: list[dict[str, object]] = []

    def add(claim_id, category, claim, observed, verdict, method, source_url, action=""):
        claims.append(
            {
                "id": claim_id,
                "category": category,
                "claim": claim,
                "observed": observed,
                "verdict": verdict,
                "method": method,
                "source_url": source_url,
                "action": action,
            }
        )

    pages_api = state["pages"]
    add(
        "A01",
        "Publication",
        "GitHub Pages serves this project from the main branch root (`main:/`).",
        f"source={pages_api.get('source_branch')}:{pages_api.get('source_path')}; status={pages_api.get('status')}; build_type={pages_api.get('build_type')}",
        "verified" if pages_api.get("source_branch") == "main" and pages_api.get("source_path") == "/" else "mismatch",
        "GitHub Pages API read in this session",
        state["endpoints"].get("pages", f"{API}/pages"),
    )
    latest = (state["builds"] or [{}])[0]
    add(
        "A02",
        "Publication",
        "The most recent Pages build completed without error.",
        f"status={latest.get('status')}; commit={latest.get('commit')}; updated={latest.get('updated_at')}; error={latest.get('error') or 'none'}",
        "verified" if latest.get("status") == "built" and not latest.get("error") else "mismatch",
        "GitHub Pages builds API read in this session",
        state["endpoints"].get("builds", f"{API}/pages/builds"),
    )
    main_sha = state["main_commit"].get("sha", "")
    add(
        "A03",
        "Publication",
        "The deployed build corresponds to the current main commit.",
        f"latest_build_commit={latest.get('commit')}; main={main_sha}",
        "verified"
        if latest.get("commit") == main_sha
        else "mismatch",
        "Pages builds API vs commits/main API vs local git HEAD",
        state["endpoints"].get("main_commit", f"{API}/commits/main"),
    )
    add(
        "A04",
        "Repository",
        f"Every pull request referenced in COORDINATION.md resolves on GitHub ({len(ledger)} references).",
        "resolved="
        + str(sum(1 for row in ledger if row["state"] != "not_found_in_api_snapshot"))
        + f"/{len(ledger)}; merged={sum(1 for row in ledger if row['merged'] == 'yes')}; "
        + f"open_or_unmerged={sum(1 for row in ledger if row['merged'] != 'yes')}",
        "verified" if all(row["state"] != "not_found_in_api_snapshot" for row in ledger) else "mismatch",
        "GitHub pulls API for every referenced number",
        state["endpoints"].get("pulls", f"{API}/pulls"),
    )
    unmerged = [row["pr"] for row in ledger if row["merged"] != "yes"]
    add(
        "A05",
        "Repository",
        "No PR referenced in the coordination board is left unmerged without a recorded status.",
        "unmerged references: " + (", ".join(f"#{n}" for n in unmerged) if unmerged else "none"),
        "needs review" if unmerged else "verified",
        "GitHub pulls API, joined against the board's own prose",
        f"https://github.com/{REPO}/pulls",
        "Confirm each unmerged PR is intentionally open; this session merged none of them."
        if unmerged
        else "",
    )
    add(
        "A06",
        "Repository",
        "Commit SHAs quoted as merge commits in COORDINATION.md are reachable in the clone.",
        "not assessable: the clone used for this audit was shallow (two commits), so a cited historical SHA can be neither confirmed nor refuted locally; absence is not evidence",
        "not assessable",
        "clone-depth inspection in the auditing session (recorded here as static text so the snapshot is reproducible on any checkout)",
        f"https://github.com/{REPO}/commits/main",
        "Re-check from a full clone before treating any quoted SHA as wrong.",
    )

    scripts_missing = []
    workflow_rows = []
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        referenced = sorted(set(re.findall(r"python3?\s+([A-Za-z0-9_./-]+\.py)", text)))
        missing = [rel for rel in referenced if not (ROOT / rel).exists()]
        scripts_missing.extend(missing)
        workflow_rows.append(
            {
                "workflow": f".github/workflows/{workflow.name}",
                "scripts": "; ".join(referenced),
                "missing": "; ".join(missing),
            }
        )
    add(
        "A07",
        "CI",
        f"Every script invoked by the {len(workflow_rows)} CI workflows exists in the tree.",
        f"workflows={len(workflow_rows)}; missing_scripts={len(scripts_missing)}"
        + (f" ({', '.join(sorted(set(scripts_missing)))})" if scripts_missing else ""),
        "verified" if not scripts_missing else "mismatch",
        "static parse of .github/workflows/*.yml against the file tree",
        f"{HTML_REPO}.github/workflows",
    )

    link_issues = internal_link_issues(pages)
    add(
        "A08",
        "Site integrity",
        "Every internal link on every published page resolves to a published file.",
        f"pages={len(pages)}; broken_local_links={link_issues}",
        "verified" if link_issues == 0 else "mismatch",
        "independent HTML parse + filesystem resolution in this session",
        f"{HTML_REPO}docs",
    )
    orphans = [row["page"] for row in pages if row["orphan"] == "yes"]
    unexpected = [page for page in orphans if Path(page).name not in LEGACY_UNLINKED]
    add(
        "A09",
        "Site integrity",
        "Every published page is reachable from at least one other published page, except the intentionally unlinked legacy calculator.",
        f"orphans={len(orphans)} ({', '.join(orphans) if orphans else 'none'})",
        "verified" if not unexpected else "needs review",
        "inbound-link graph over docs/**/*.html",
        f"{HTML_REPO}docs/index.html",
        "Link the unreachable pages from the landing page or retire them."
        if unexpected
        else "",
    )
    markers = merge_markers()
    add(
        "A10",
        "Site integrity",
        "No published page or tracked Markdown file contains git merge-conflict markers.",
        f"markers={markers}",
        "verified" if markers == 0 else "mismatch",
        "line scan of docs/**/*.html and *.md",
        f"{HTML_REPO}docs",
    )
    insecure = plain_http_external()
    add(
        "A11",
        "Site integrity",
        "Every external link uses https.",
        f"http_links={insecure}",
        "verified" if insecure == 0 else "mismatch",
        "anchor scan of docs/**/*.html",
        f"{HTML_REPO}docs",
    )
    provenance_gaps = [row["page"] for row in pages if row["generator_exists"] == "NO"]
    hand_written = [row["page"] for row in pages if str(row["generator"]).startswith("hand")]
    add(
        "A12",
        "Provenance",
        "Every generated page has an existing generator script in the tree.",
        f"pages={len(pages)}; missing_generator={len(provenance_gaps)}; hand_maintained={len(hand_written)}",
        "verified" if not provenance_gaps else "needs review",
        "page inventory joined to the documented generator map",
        f"{HTML_REPO}docs",
        "Record the generator (or the hand-maintained status) for each page without one."
        if provenance_gaps
        else "",
    )
    add(
        "A13",
        "Source reading",
        "Official NBA / Korean statute / press pages cited by this project were re-read and re-confirmed in this session.",
        "not performed: direct requests to www.nba.com, www.law.go.kr and www.espn.com returned no response (HTTP 000) from this sandbox",
        "verification blocked",
        "curl HTTP status probe of the cited hosts before starting the audit",
        "https://www.nba.com/termsofuse",
        "Re-read every cited official page from an environment with egress before calling any inherited row verified.",
    )
    add(
        "A14",
        "Publication",
        "The live site responds at its public URL.",
        "not performed: sassnarep3-star.github.io is not reachable from this sandbox (HTTP 000)",
        "verification blocked",
        "HTTP probe; the GitHub Pages API is the only reachable deployment evidence",
        pages_api.get("html_url") or f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/",
        "Open the Pages URL in a browser, or re-check via the API build status (A02).",
    )

    summary = {
        "generated_for": "2026-11-05",
        "snapshot_fetched_at_utc": state.get("fetched_at_utc"),
        "pages": len(pages),
        "table_rows": sum(int(row["table_rows"]) for row in pages),
        "official_links": sum(int(row["official_links"]) for row in pages),
        "prs_referenced": len(ledger),
        "prs_merged": sum(1 for row in ledger if row["merged"] == "yes"),
        "prs_unmerged": len(unmerged),
        "orphans": len(orphans),
        "claims": len(claims),
        "claims_verified": sum(1 for row in claims if row["verdict"] == "verified"),
        "claims_needs_review": sum(1 for row in claims if row["verdict"] == "needs review"),
        "claims_mismatch": sum(1 for row in claims if row["verdict"] == "mismatch"),
        "claims_blocked": sum(1 for row in claims if row["verdict"] == "verification blocked"),
        "claims_not_assessable": sum(1 for row in claims if row["verdict"] == "not assessable"),
        "workflows": workflow_rows,
    }
    return ledger, pages, claims, summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def outputs() -> dict[Path, str]:
    ledger, pages, claims, summary = build()
    files: dict[Path, str] = {}
    for name, rows in (("pr_ledger.csv", ledger), ("pages.csv", pages), ("claims.csv", claims)):
        buffer = []
        buffer.append(",".join(rows[0].keys()))
        for row in rows:
            buffer.append(",".join(_csv_cell(value) for value in row.values()))
        files[OUT / name] = "\n".join(buffer) + "\n"
    files[OUT / "summary.json"] = json.dumps(summary, indent=2) + "\n"
    return files


def _csv_cell(value: object) -> str:
    text = str(value)
    if any(character in text for character in ',"\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refresh the GitHub API snapshot")
    parser.add_argument("--check", action="store_true", help="fail if committed outputs are stale")
    args = parser.parse_args(argv)
    if args.refresh:
        refresh()
    files = outputs()
    if args.check:
        stale = []
        for path, content in files.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        for name in stale:
            print(f"FAIL stale {name}")
        if stale:
            return 1
        print(f"OK: acceptance audit outputs are up to date ({len(files)} files)")
        return 0
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    ledger, pages, claims, summary = build()
    print(
        f"wrote {len(ledger)} PR rows, {len(pages)} page rows, {len(claims)} claims; "
        f"verified={summary['claims_verified']} needs_review={summary['claims_needs_review']} "
        f"blocked={summary['claims_blocked']} mismatch={summary['claims_mismatch']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
