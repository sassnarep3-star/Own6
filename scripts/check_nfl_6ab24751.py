#!/usr/bin/env python3
"""Line-by-line verifier for the consolidated decision-readiness pack (6ab24751).

Checks:
  * the data pack validates (readiness / gates / sources / flagged consistency);
  * every readiness row carries an official https source link present in sources.csv;
  * every blocking_gate resolves to a gate in gates.csv or is a "none" marker;
  * the generated dashboard pages exist and every <tr> carries an https source link;
  * the landing-page table injected into index.html matches the emitted fragment;
  * no <input> elements exist in any generated page;
  * internal relative links resolve to existing files.

Exit code 0 means all checks pass.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from nfl_6ab24751.readiness import PackPaths, load_pack, validate  # noqa: E402

DATA_DIR = os.path.join(ROOT, "data", "nfl_6ab24751")
DOCS_DIR = os.path.join(ROOT, "docs", "nfl-6ab24751")
ROOT_INDEX = os.path.join(ROOT, "index.html")

PAGES = ["index.html", "gates.html", "sources.html", "flagged.html",
         "executive-summary.html"]

BEGIN = "<!-- BEGIN DECISION-READINESS TABLE (session 6ab24751) -->"
END = "<!-- END DECISION-READINESS TABLE (session 6ab24751) -->"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main() -> int:
    failures: list[str] = []
    checks = 0

    paths = PackPaths.for_repo(ROOT)
    pack = load_pack(paths)

    # 1. data validation
    errors = validate(pack)
    checks += 1
    if errors:
        failures.extend(f"validate: {e}" for e in errors)

    # 2. readiness rows carry an https source present in sources.csv
    source_urls = {s["url"] for s in pack.sources}
    for r in pack.rows:
        checks += 1
        url = r.get("official_source_url", "")
        if not url.startswith("https://"):
            failures.append(f"{r['req_id']}: source not https: {url!r}")
        elif url not in source_urls:
            failures.append(f"{r['req_id']}: source {url!r} not in sources.csv")

    # 3. blocking gates resolve
    gate_ids = pack.gate_ids
    for r in pack.rows:
        gate = r.get("blocking_gate", "")
        checks += 1
        if gate and not gate.startswith("none"):
            if not any(g in gate for g in gate_ids):
                failures.append(f"{r['req_id']}: gate {gate!r} unresolved in gates.csv")

    # 4. generated pages exist; every <tr> has an https source link; no <input>
    for name in PAGES:
        path = os.path.join(DOCS_DIR, name)
        checks += 1
        if not os.path.exists(path):
            failures.append(f"missing page {name}")
            continue
        content = read(path)
        if "<input" in content.lower():
            failures.append(f"{name}: contains an <input> element")
        # only body rows need a source link; skip the thead header row
        bodies = re.findall(r"<tbody[^>]*>(.*?)</tbody>", content, flags=re.S | re.I)
        rows = []
        for b in bodies:
            rows.extend(re.findall(r"<tr[^>]*>(.*?)</tr>", b, flags=re.S | re.I))
        for i, row in enumerate(rows):
            checks += 1
            if "https://" not in row:
                failures.append(f"{name}: table row {i} has no https source link")

    # 5. landing fragment matches what is injected into index.html
    fragment_path = os.path.join(DOCS_DIR, "landing-table.fragment.html")
    checks += 1
    if not os.path.exists(fragment_path):
        failures.append("missing landing-table.fragment.html")
    else:
        fragment = read(fragment_path)
        checks += 1
        if not os.path.exists(ROOT_INDEX):
            failures.append("root index.html missing")
        else:
            idx = read(ROOT_INDEX)
            if BEGIN not in idx or END not in idx:
                failures.append("root index.html: readiness markers missing")
            else:
                seg = idx[idx.index(BEGIN): idx.index(END)]
                checks += 1
                if fragment not in seg:
                    failures.append("root index.html: injected table does not match fragment")

    # 6. internal relative links resolve in generated pages
    for name in PAGES:
        path = os.path.join(DOCS_DIR, name)
        if not os.path.exists(path):
            continue
        content = read(path)
        base = os.path.dirname(path)
        for href in re.findall(r'href="([^"#]+)"', content):
            if href.startswith("http") or href.startswith("mailto:") or href.startswith("#"):
                continue
            checks += 1
            target = os.path.normpath(os.path.join(base, href.split("#")[0]))
            if not os.path.exists(target):
                failures.append(f"{name}: broken internal link {href!r}")

    print(f"check_nfl_6ab24751: {checks} checks run, {len(failures)} failures")
    for f in failures:
        print(" -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
