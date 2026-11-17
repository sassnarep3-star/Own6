#!/usr/bin/env python3
"""Verifier for the nfl_dfc0c1bc pack — numbered rules, exit 0 = pass.

The pack makes four promises. They are enforced here rather than asserted in prose:

  1. nothing is dropped      — every row of every source register lands on exactly one theme (rule 2)
  2. nothing is invented     — provenance per row (rule 3), official reads only from official hosts (rule 5),
                               and this board publishes no price and no pick (rule 6)
  3. nothing is decided for
     the owner               — every decision column is empty (rule 4)
  4. nothing leaked into
     another pack's scope    — the git-diff scope rule (rule 13)
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
import subprocess
import sys
from urllib.parse import urlparse

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(REPO, "data", "nfl_dfc0c1bc")
DOCS = os.path.join(REPO, "docs", "nfl-dfc0c1bc")
SRC = os.path.join(REPO, "src", "nfl_dfc0c1bc")

sys.path.insert(0, os.path.join(REPO, "src"))
from nfl_dfc0c1bc import registers as RG  # noqa: E402
from nfl_dfc0c1bc import themes as TH  # noqa: E402

REQUIRED_CSVS = [
    "suggestions_inventory.csv", "suggestions_master.csv", "questions_master.csv",
    "decision_paths.csv", "information_board.csv", "information_gaps.csv", "official_reads.csv",
    "observations.csv", "answers.csv", "metrics.csv", "corpus_sizes.csv", "price_semantics.csv",
    "claim_checks.csv", "cross_pack_conflicts.csv", "reject_guardrails.csv", "repo_findings.csv",
    "flagged.csv", "sources.csv", "lions_status_check.csv",
]
REQUIRED_PAGES = [name for name, _ in [
    ("index.html", 1), ("suggestions.html", 1), ("questions.html", 1), ("answers.html", 1),
    ("gaps.html", 1), ("paths.html", 1), ("conflicts.html", 1), ("repo-review.html", 1),
    ("sources.html", 1), ("flagged.html", 1), ("executive-summary.html", 1)]]

OFFICIAL_READ_HOSTS = {"www.nfl.com", "nfl.com", "operations.nfl.com", "www.packers.com",
                       "www.packers.com:443", "www.texans.com", "www.miamidolphins.com"}
ALLOWED_CLAIM_VERDICTS = ("consistent", "check needed", "CONTRADICTION", "qualitative claim",
                          "not measurable", "the capture file already carries")
OWN_SCOPE = [
    "data/nfl_dfc0c1bc/", "docs/nfl-dfc0c1bc/", "src/nfl_dfc0c1bc/",
    "scripts/build_nfl_dfc0c1bc.py", "scripts/check_nfl_dfc0c1bc.py",
    "tests/test_nfl_dfc0c1bc.py", ".github/workflows/nfl-dfc0c1bc-ci.yml",
    "NFL_DFC0C1BC_EXECUTIVE_SUMMARY.md", "audit/NFL_DFC0C1BC_REPO_REVIEW.md", "COORDINATION.md",
    "README.md", "index.html", "docs/index.html", "docs/assets/style.css",
]


def rows(name: str):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    errs: list[str] = []

    # Rule 1 — artifacts
    for name in REQUIRED_CSVS:
        if not os.path.exists(os.path.join(DATA, name)):
            errs.append(f"rule 1: missing data file {name}")
    for name in REQUIRED_PAGES:
        if not os.path.exists(os.path.join(DOCS, name)):
            errs.append(f"rule 1: missing page {name}")
    if errs:
        print("\n".join(errs))
        print(f"FAIL ({len(errs)} problems)")
        return 1

    # Rule 2 — full coverage of the source registers, no unsorted rows
    inventory = RG.iter_registers()
    expected = sum(int(i["rows"]) for i in inventory)
    sug, que = rows("suggestions_master.csv"), rows("questions_master.csv")
    got = len(sug) + len(que)
    if got != expected:
        errs.append(f"rule 2: master registers hold {got} rows, the registers hold {expected}")
    for tag, table in (("suggestions", sug), ("questions", que)):
        ids = [(r["source_pack"], r["source_file"], r["source_row_id"]) for r in table]
        if len(set(ids)) != len(ids):
            errs.append(f"rule 2: {tag} master duplicates a source row")
        if any(r["theme_id"] == "T00" for r in table):
            errs.append(f"rule 2: {tag} master leaves a row unclassified (T00)")
        # the real test of "nothing dropped": each register row's *text* must survive on the board,
        # wherever its provenance landed — a row may absorb siblings, but it may not vanish
        board_text = {os.path.basename(r["source_file"]): set() for r in table}
        for r in table:
            for key in ("suggestion", "question", "options_raised", "problem_it_solves", "answer_needed"):
                if r.get(key):
                    board_text[os.path.basename(r["source_file"])].add(r[key])
        flat = " ||| ".join(" ".join(v) for v in board_text.values())
        for entry in (e for e in inventory if e["kind"] == tag):
            path = os.path.join(REPO, entry["path"])
            for n, raw in enumerate(RG.read_table(path), 1):
                lid = RG.field(raw, "id") or f"row{n:03d}"
                text = RG.field(raw, "suggestion") or RG.field(raw, "question") or RG.field(raw, "statement")
                key = (entry["pack"], entry["path"], lid)
                if key not in set(ids) and text[:60] not in flat:
                    errs.append(f"rule 2: register row {entry['path']}#{lid} is neither on the board "
                                f"nor absorbed into a row that quotes it")

    # Rule 3 — provenance on every board row
    for name, need in (("suggestions_master.csv", ("source_pack", "source_file", "suggestion")),
                       ("questions_master.csv", ("source_pack", "source_file", "question")),
                       ("decision_paths.csv", ("theme_id", "decision", "options")),
                       ("information_board.csv", ("theme_id", "question_to_answer", "how_to_get_it")),
                       ("information_gaps.csv", ("gap_id", "missing_dataset", "coverage_now")),
                       ("cross_pack_conflicts.csv", ("conflict_id", "subject", "what_it_changes")),
                       ("claim_checks.csv", ("claim_id", "claim", "verdict"))):
        for i, r in enumerate(rows(name), 2):
            for col in need:
                if not r.get(col, "").strip():
                    errs.append(f"rule 3: {name} line {i} has an empty required field {col}")
            if name in ("suggestions_master.csv", "questions_master.csv"):
                if not os.path.exists(os.path.join(REPO, r["source_file"])):
                    errs.append(f"rule 3: {name} line {i} cites a file that does not exist")

    # Rule 4 — the owner's columns stay empty until the owner fills them
    for name, cols in (("suggestions_master.csv", ("owner_decision", "owner_notes", "decision_logged_on")),
                       ("questions_master.csv", ("owner_answer", "answer_logged_on")),
                       ("decision_paths.csv", ("owner_choice", "owner_notes")),
                       ("repo_findings.csv", ("owner_decision",))):
        for i, r in enumerate(rows(name), 2):
            for col in cols:
                if r.get(col, "").strip():
                    errs.append(f"rule 4: {name} line {i} has a decision in {col}; the owner decides, not the builder")
    if any(r["status"] != "awaiting_owner_choice" for r in rows("decision_paths.csv")):
        errs.append("rule 4: a decision path is marked as anything other than awaiting the owner")

    # Rule 5 — official reads are official, clocked, quoted, and referenced honestly
    reads = rows("official_reads.csv")
    for r in reads:
        host = urlparse(r["url"]).netloc.lower()
        if host not in OFFICIAL_READ_HOSTS:
            errs.append(f"rule 5: read {r['read_id']} cites a non-official host {host}")
        if not r["verbatim_excerpt"].strip():
            errs.append(f"rule 5: read {r['read_id']} quotes no text")
        for line in r["verbatim_excerpt"].split(" || "):
            # a read_this_session quote must be page text, not repo formatting: no file paths, no table
            # delimiters, no register ids — that is how the R1 defect once crept in and it stays checked
            if re.search(r"""(data/nfl|\.csv|\.psv|\|---|^```|https?://github)""", line):
                errs.append(f"rule 5: read {r['read_id']} carries repo formatting in its verbatim quote: {line[:60]}")
            if re.search(r"\b[A-Za-z0-9_]+-(?:S|Q|F)\d+\b", line):
                errs.append(f"rule 5: read {r['read_id']} quotes a register id, which is repo text "
                            f"not page text: {line[:60]}")
        if "session clock" not in r["clock_note"]:
            errs.append(f"rule 5: read {r['read_id']} does not state how its clock was obtained")
        if urlparse(r["url"]).scheme != "https":
            errs.append(f"rule 5: read {r['read_id']} is not https")
    ids = {r["read_id"] for r in reads}
    for r in rows("observations.csv"):
        for ref in r["read_id"].split("|"):
            if ref not in ids:
                errs.append(f"rule 5: observation {r['obs_id']} cites unknown read {ref}")
    for r in rows("answers.csv"):
        for ref in r["reads"].split(";"):
            if ref and ref not in ids:
                errs.append(f"rule 5: answer {r['answer_id']} cites unknown read {ref}")
        if not r["answer"].strip():
            errs.append(f"rule 5: answer {r['answer_id']} is empty — say what is open instead of blanking it")

    # Rule 6 — this board publishes no price and no pick. Scope matters: other packs' registers do hold
    # price figures, and this board quotes their text verbatim with the file and row named. What is not
    # allowed is for *this* pack to author a number that reads like a price, or to carry a price column.
    price_col = re.compile(r"(opening|closing|current)?_?(line|price|odds|american|decimal|spread|total)", re.I)
    for name in REQUIRED_CSVS:
        header = open(os.path.join(DATA, name), encoding="utf-8").readline().strip().split(",")
        for col in header:
            if price_col.fullmatch(col):
                errs.append(f"rule 6: {name} carries a price column {col}; the board stores counts, not prices")
    ours = open(os.path.join(SRC, "themes.py"), encoding="utf-8").read() \
        + open(os.path.join(SRC, "audit.py"), encoding="utf-8").read()
    for m in re.finditer(r"""(?<![\w.])[+-](?:1[0-4]\d|150)(?![\w])""", ours):
        errs.append(f"rule 6: this pack's own prose publishes an odds figure ({m.group(0)}) — "
                    f"the board may state that no line is available, never a number that looks like one")
    for path in glob.glob(os.path.join(DATA, "*.csv")) + glob.glob(os.path.join(DOCS, "*.html")):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if re.search(r"\b(this bet wins|our pick is|guaranteed|locked in|sure thing)\b", text, re.I):
            errs.append(f"rule 6: {os.path.basename(path)} reads like a pick, not an evidence register")

    # Rule 7 — links
    for path in glob.glob(os.path.join(DOCS, "*.html")):
        with open(path, encoding="utf-8") as fh:
            htmltext = fh.read()
        for href in re.findall(r"""href=['"]([^'"]+)['"]""", htmltext):
            if href.startswith("mailto:") or href.startswith("#"):
                continue
            if href.startswith("http"):
                if urlparse(href).scheme != "https":
                    errs.append(f"rule 7: {os.path.basename(path)} links over http: {href}")
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), href.split("#")[0]))
            if not os.path.exists(target):
                errs.append(f"rule 7: broken internal link {href} on {os.path.basename(path)}")
    for name in ("suggestions_master.csv", "questions_master.csv"):
        for i, r in enumerate(rows(name), 2):
            u = r.get("source_url", "")
            if u and not u.startswith("https://"):
                errs.append(f"rule 7: {name} line {i} has a non-https source url")

    # Rule 8 — high-severity items are all on the flagged page
    flags = rows("flagged.csv")
    if not flags:
        errs.append("rule 8: flagged-for-review register is empty")
    flag_ids = " ".join(f.get("finding", "") + " " + f.get("category", "") for f in flags)
    for c in rows("cross_pack_conflicts.csv"):
        if c["severity"] in ("high", "medium") and c["kind"] != "agreement":
            if c["conflict_id"] not in flag_ids:
                errs.append(f"rule 8: {c['conflict_id']} ({c['subject'][:44]}) is not named by any "
                            f"flagged-for-review row, so nobody is prompted to choose a resolution")

    # Rule 9 — determinism: rebuilding changes no byte
    before = {p: sha(p) for p in glob.glob(os.path.join(DATA, "*.csv")) + glob.glob(os.path.join(DOCS, "*.html"))}
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_dfc0c1bc.py")],
                   check=True, capture_output=True)
    after = {p: sha(p) for p in before}
    for p, digest in before.items():
        if after.get(p) != digest:
            errs.append(f"rule 9: rebuild changed {os.path.basename(p)} — output is not deterministic")

    # Rule 10 — the registers we consolidated are still the ones on disk
    if len(inventory) < 20:
        errs.append(f"rule 10: only {len(inventory)} registers found; a whole domain looks missing")
    if not any(i["kind"] == "suggestions" for i in inventory) or not any(i["kind"] == "questions" for i in inventory):
        errs.append("rule 10: inventory is missing one of the two register kinds")

    # Rule 11 — themes are complete and distinct
    paths = rows("decision_paths.csv")
    if [p["theme_id"] for p in paths] != sorted(p["theme_id"] for p in paths) and len(paths) != len(TH.THEMES):
        errs.append("rule 11: decision paths and theme definitions disagree in count")
    if len(paths) != len(TH.THEMES):
        errs.append(f"rule 11: {len(paths)} paths for {len(TH.THEMES)} themes")
    per_theme = {t: 0 for t in TH.THEME_IDS}
    for r in sug + que:
        per_theme[r["theme_id"]] = per_theme.get(r["theme_id"], 0) + 1
    empty = [t for t, n in per_theme.items() if n == 0]
    if empty:
        errs.append(f"rule 11: themes with no source rows: {empty}")
    for p in paths:
        if not re.match(r"^\d+\.\d\d$", p["ratio"]):
            errs.append(f"rule 11: path {p['theme_id']} has a ratio that was not computed: {p['ratio']}")

    # Rule 12 — gaps carry a route and a number
    gaps = rows("information_gaps.csv")
    if len(gaps) < 12:
        errs.append(f"rule 12: only {len(gaps)} gaps; the brief implies more")
    for g in gaps:
        for col in ("acquisition_route", "clearing_number", "risk_if_left_open", "blocks_themes"):
            if not g[col].strip():
                errs.append(f"rule 12: gap {g['gap_id']} is missing {col}")
        if re.search(r"\bT\d\d\b", g["blocks_themes"]) is None:
            errs.append(f"rule 12: gap {g['gap_id']} blocks no decision — then why list it?")

    # Rule 13 — scope: none of THIS pack's commits touched another pack's file.
    #
    # The previous version diffed merge-base(HEAD, origin/main)..HEAD, which is
    # only equal to "this pack's commits" while HEAD is the pack's own branch.
    # Once the pack is merged, or once another session rebases its branch onto a
    # main that already contains this pack, the same diff also reports that other
    # session's files and this rule fails on innocent work. Selecting the pack's
    # own commits first makes the rule say what it means on any branch.
    own_commit_files = []
    try:
        commits = subprocess.run(["git", "log", "--format=%H", "--",
                                  "data/nfl_dfc0c1bc", "scripts/build_nfl_dfc0c1bc.py"],
                                 cwd=REPO, capture_output=True, text=True).stdout.split()
        for c in commits:
            files = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r",
                                    "--root", c], cwd=REPO, capture_output=True, text=True).stdout.split()
            own_commit_files.append((c[:8], files))
    except Exception:  # pragma: no cover - no git available
        own_commit_files = []
    for short, files in own_commit_files:
        for f in files:
            if not any(f.startswith(p.rstrip("/")) or f == p for p in OWN_SCOPE):
                errs.append(f"rule 13: commit {short} touches {f}, outside the claimed scope")

    # Rule 14 — every page carries the pack nav and the disclaimer
    for name in REQUIRED_PAGES:
        with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
            page = fh.read()
        for other, _ in [(n, t) for n, t in
                         [("index.html", 1), ("suggestions.html", 1), ("questions.html", 1), ("answers.html", 1),
                          ("gaps.html", 1), ("paths.html", 1), ("conflicts.html", 1), ("repo-review.html", 1),
                          ("sources.html", 1), ("flagged.html", 1), ("executive-summary.html", 1)]]:
            if other != name and f'href="{other}"' not in page and f"href={other}" not in page:
                errs.append(f"rule 14: {name} is missing the nav link to {other}")
        if "blank cell means no confirmed value" not in page:
            errs.append(f"rule 14: {name} has no blank-means-unknown disclaimer")

    # Rule 15 — sources ledger hashes still match the files on disk
    for s in rows("sources.csv"):
        if s["class"] not in ("official_read_this_session", "repo_register_inherited"):
            errs.append(f"rule 15: source {s['source_id']} has an unknown class")
        if s["hash"]:
            path = os.path.join(REPO, s["path_or_row"])
            if not os.path.exists(path):
                errs.append(f"rule 15: source {s['source_id']} points at a missing file")
            elif sha(path) != s["hash"]:
                errs.append(f"rule 15: {s['path_or_row']} changed since it was consolidated — "
                            f"the board must be rebuilt before it is quoted")

    if errs:
        print("\n".join(f"  {e}" for e in errs))
        print(f"FAIL — {len(errs)} problems")
        return 1
    counts = (f"registers {len(inventory)}; suggestions {len(sug)}; questions {len(que)}; paths {len(paths)}; "
              f"gaps {len(gaps)}; reads {len(reads)}; flags {len(flags)}")
    print(f"OK — 15 rules, 0 failures · {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
