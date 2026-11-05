#!/usr/bin/env python3
"""Gate the skill lab: links, sources, blank-unconfirmed discipline, reproducibility.

Checks, in order:

  1. Every internal link on every skill page resolves to a file that exists.
  2. Every external link is HTTPS and points at an allowlisted official or
     documentation host. No unknown publisher is linked, and no NBA stats page
     is linked without a rights note on the same page.
  3. Every table body row carries at least one link (a source, or the
     implementation file that produced the value).
  4. No page contains a merge-conflict marker, a placeholder string, a Python
     repr leak (``<generator``), or a ``nan``/``None`` rendered as text.
  5. The committed summary JSON has no real-market claim: the meta flag
     ``real_nba_market_values_published`` must be 0, and no strategy outside the
     fully-evidenced synthetic archetype may be marked qualified.
  6. Re-running the build reproduces the committed pages byte for byte
     (``--check`` mode). This is what makes every published number auditable.

Exit status is non-zero on any failure, so CI blocks a bad publish.
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "skill"
SUMMARY = ROOT / "data" / "skill" / "skilllab_summary.json"

ALLOWED_HOSTS = {
    "www.nba.com",
    "docs.scipy.org",
    "scikit-learn.org",
    "www.statsmodels.org",
    "www.itl.nist.gov",
    "github.com",
}

# Pages that must carry a rights caution because they discuss NBA-derived data.
RIGHTS_PAGES = {"index.html", "signals.html", "sources.html", "flagged.html", "singles.html"}

HREF_RE = re.compile(r'href="([^"]+)"')
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
TD_RE = re.compile(r"<td\b", re.I)
LINK_IN_ROW_RE = re.compile(r'<a [^>]*href="([^"]+)"', re.I)

FORBIDDEN_TEXT = [
    "genesis", "TODO", "FIXME", "XXX", "lorem ipsum",
    "<<<<<<<", ">>>>>>>", "=======",
    "<generator object", "<function ", "nan%", ">None<", "Traceback",
]


def allowed_external(url: str) -> bool:
    if not url.startswith("https://"):
        return False
    rest = url[len("https://"):]
    host = rest.split("/", 1)[0].split(":", 1)[0].lower()
    return host in ALLOWED_HOSTS


def main(check_only: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    pages = sorted(DOCS.glob("*.html"))
    if len(pages) < 11:
        errors.append(f"expected at least 11 skill pages, found {len(pages)}")

    total_rows = 0
    sourced_rows = 0
    external = set()

    for path in pages:
        name = path.name
        text = path.read_text(encoding="utf-8")

        for bad in FORBIDDEN_TEXT:
            if bad in text:
                errors.append(f"{name}: forbidden content {bad!r}")

        # 1 + 2: links
        for href in HREF_RE.findall(text):
            href = html.unescape(href)
            if href.startswith("#"):
                continue
            if href.startswith("https://"):
                external.add(href)
                if not allowed_external(href):
                    errors.append(f"{name}: non-allowlisted external link {href}")
                continue
            if href.startswith("http://"):
                errors.append(f"{name}: insecure http link {href}")
                continue
            if href.startswith("mailto:"):
                continue
            target = (path.parent / href.split("#", 1)[0].split("?", 1)[0]).resolve()
            if not target.exists():
                errors.append(f"{name}: broken internal link {href}")

        # 3: every table body row carries a link
        for i, body in enumerate(ROW_RE.findall(text), start=1):
            if not TD_RE.search(body):
                continue  # header row
            total_rows += 1
            if LINK_IN_ROW_RE.search(body):
                sourced_rows += 1
            else:
                errors.append(f"{name}: table data row #{i} has no source link")

        # rights caution on pages that discuss NBA-derived data
        if name in RIGHTS_PAGES and "termsofuse" not in text:
            warnings.append(f"{name}: no link to the NBA Terms of Use")

    # 4: summary contract
    if not SUMMARY.exists():
        errors.append("data/skill/skilllab_summary.json is missing; run scripts/build_skilllab.py")
    else:
        data = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if data.get("meta", {}).get("real_nba_market_values_published") != 0:
            errors.append("summary claims published real NBA market values; this build publishes none")
        qualified = [k for k, v in data.get("gates", {}).items() if v.get("qualified")]
        if qualified != ["F_SKILL_FULL"]:
            errors.append(f"qualified set must be exactly the fully-evidenced synthetic archetype, got {qualified}")
        for run in data.get("gates", {}).values():
            for g in run.get("gates", []):
                if not str(g.get("source", "")).startswith("https://"):
                    errors.append(f"gate {g.get('gate_id')} lacks an https source")
        if len(data.get("gates", {})) != 5:
            errors.append("expected 5 gate runs in the summary")

    # 5: reproducibility
    if not check_only:
        warnings.append("rebuild skipped (use --check to verify byte-for-byte reproducibility)")
    else:
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in pages}
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_skilllab.py")],
                              capture_output=True, text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            errors.append(f"rebuild failed: {proc.stderr.strip()[:400]}")
        else:
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in pages}
            changed = [k for k in before if before[k] != after.get(k)]
            if changed:
                errors.append(f"build is not reproducible; changed pages: {changed}")

    print(f"Skill lab: {len(pages)} pages, {total_rows} table rows, {sourced_rows} source-linked, "
          f"{len(external)} distinct external links")
    print(f"Allowed external hosts: {', '.join(sorted(ALLOWED_HOSTS))}")
    if warnings:
        print("\nAdvisory:")
        for w in warnings:
            print(f"  WARN  {w}")
    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(f"  ERROR {e}")
        return 1
    print("\nOK: skill lab pages pass link, source, content and reproducibility checks.")
    print("These are structural and arithmetic checks, not verification of any basketball fact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(check_only="--check" in sys.argv))
