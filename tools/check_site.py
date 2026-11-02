#!/usr/bin/env python3
"""Strict verification gate for the Own6 GitHub Pages site.

Enforces the project rules:
  1. every external link on the maintained pages points at an official URL that
     appears in data/verification_log.csv with a verified-direct* status;
  2. every data table row (<tr> containing <td>) carries at least one such link;
  3. no internal link is broken (relative href/src must resolve inside the repo);
  4. Math.erf (undefined in standard JavaScript) is never used;
  5. every URL in data/sources.csv is present in the verification log.

Pages owned by other sessions (docs/verified/**) are checked for broken internal
links and for table-row source coverage, but those findings are reported as
warnings with a coordination request rather than edited by this session.

Writes audit/link_check_report.md and exits non-zero on any strict failure.
"""
from __future__ import annotations

import csv
import html
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LOG = ROOT / "data" / "verification_log.csv"
SOURCES = ROOT / "data" / "sources.csv"
REPORT = ROOT / "audit" / "link_check_report.md"

# The project's own GitHub repository is the official primary source for facts
# about the repository itself (V24 / V18 / V19 / V20 in the verification log).
OFFICIAL_PREFIXES = (
    "https://github.com/sassnarep3-star/Own6/",
    "https://api.github.com/repos/sassnarep3-star/Own6/",
)

HREF_RE = re.compile(r'(?:href|src)="([^"]+)"', re.I)
ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
TD_RE = re.compile(r"<td\b", re.I)
URL_RE = re.compile(r'href="(https?://[^"]+)"', re.I)


def norm(url: str) -> str:
    url = html.unescape(url.strip())
    url = url.split("#", 1)[0]
    return url.rstrip("/")


def load_verified() -> set[str]:
    verified: set[str] = set()
    with LOG.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["status"].startswith("verified-direct"):
                verified.add(norm(row["url"]))
    return verified


ADVISORY_DOMAINS = (
    "nba.com", "official.nba.com", "law.go.kr", "github.com", "docs.github.com",
    "api.github.com", "scikit-learn.org", "scipy.org", "docs.scipy.org",
    "python.org", "nist.gov", "statsmodels.org", "cftc.gov",
)


def is_official(url: str, verified: set[str]) -> bool:
    u = norm(url)
    return u in verified or any(u.startswith(p) for p in OFFICIAL_PREFIXES)


def is_official_advisory(url: str, verified: set[str]) -> bool:
    """For pages owned by other sessions: accept any link on an official domain.

    Those pages cite, for example, law.go.kr and per-game nba.com preview links
    that are official but are not part of this session's verification registry.
    """
    if is_official(url, verified):
        return True
    host = (urlparse(html.unescape(url)).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ADVISORY_DOMAINS)


def strict_pages() -> list[pathlib.Path]:
    return sorted(list(DOCS.glob("*.html")) + list((DOCS / "review").glob("*.html")))


def report_pages() -> list[pathlib.Path]:
    return sorted((DOCS / "verified").glob("*.html"))


def check_page(path: pathlib.Path, verified: set[str], strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()

    # 1. internal links resolve inside the repository (Pages source is main:/).
    for target in HREF_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        resolved = (path.parent / clean).resolve()
        if not resolved.exists() or not str(resolved).startswith(str(ROOT)):
            (errors if strict else warnings).append(f"{rel}: broken internal link '{target}'")

    # 2. external links on maintained pages must be directly verified official URLs.
    for url in URL_RE.findall(text):
        if strict and not is_official(html.unescape(url), verified):
            errors.append(f"{rel}: external link not in verified official registry: {url}")

    # 3. every data row carries an official source link.
    predicate = is_official if strict else is_official_advisory
    for idx, row in enumerate(ROW_RE.findall(text), 1):
        if not TD_RE.search(row):
            continue  # header row
        external = URL_RE.findall(row)
        if not any(predicate(u, verified) for u in external):
            msg = f"{rel}: table data row #{idx} has no official source link"
            (errors if strict else warnings).append(msg)

    # 4. no undefined JS math helper (prose mentions of the name are fine).
    if "Math.erf(" in text:
        errors.append(f"{rel}: calls Math.erf(), which is undefined in standard JavaScript")

    return errors, warnings


def check_assets(verified: set[str]) -> list[str]:
    errors: list[str] = []
    # Math.erf is checked everywhere; URL allowlisting applies only to assets
    # maintained by this integration session (other sessions own docs/verified/).
    maintained = [DOCS / "assets", DOCS / "review" / "assets"]
    for path in sorted(DOCS.rglob("*.js")):
        text = path.read_text(encoding="utf-8")
        if "Math.erf(" in text:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: calls Math.erf()")
        if not any(path.parent == d for d in maintained):
            continue
        for url in re.findall(r'https?://[^\s"\'<>]+', text):
            if not is_official(url.rstrip(".,);"), verified):
                errors.append(f"{path.relative_to(ROOT).as_posix()}: unverified JS URL {url}")
    return errors


def check_sources(verified: set[str]) -> list[str]:
    errors: list[str] = []
    if not SOURCES.exists():
        return ["data/sources.csv missing"]
    with SOURCES.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            url = (row.get("url") or "").strip()
            if not url:
                errors.append(f"data/sources.csv: {row.get('id')} has no official URL")
            elif not is_official(url, verified):
                errors.append(f"data/sources.csv: {row.get('id')} URL not directly verified: {url}")
    return errors


def main() -> int:
    verified = load_verified()
    errors: list[str] = []
    warnings: list[str] = []
    strict = strict_pages()
    external = report_pages()

    for path in strict:
        e, w = check_page(path, verified, strict=True)
        errors += e
        warnings += w
    for path in external:
        e, w = check_page(path, verified, strict=False)
        warnings += e + w

    errors += check_assets(verified)
    errors += check_sources(verified)

    lines = [
        "# Site verification gate report",
        "",
        f"- Strict pages checked: {len(strict)}",
        f"- Other-session pages checked (advisory): {len(external)}",
        f"- Directly verified official URLs in registry: {len(verified)}",
        f"- Strict errors: {len(errors)}",
        f"- Advisory warnings (other-session scope): {len(warnings)}",
        "",
        "## Strict errors",
        "",
    ]
    lines += [f"- {e}" for e in errors] or ["- none"]
    lines += ["", "## Advisory warnings / coordination requests", ""]
    lines += [f"- {w}" for w in warnings] or ["- none"]
    lines += [
        "",
        "Advisory findings are published on the Flagged for Review page and logged in",
        "COORDINATION.md; this session does not edit another session's files.",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    for e in errors:
        print("ERROR", e)
    for w in warnings:
        print("WARN ", w)
    print(f"STRICT PAGES: {len(strict)} | ERRORS: {len(errors)} | ADVISORY: {len(warnings)}")
    print(f"Report: {REPORT.relative_to(ROOT).as_posix()}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
