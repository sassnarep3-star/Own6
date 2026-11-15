#!/usr/bin/env python3
"""Verifier for the e5e38f9e NFL evidence pack. Exit 0 only if every check passes.

Checks
  1. Generated files (reconciliation, injury comparison, pages) match the builder output (drift alarm).
  2. Official reads: 14 Week 10 games; 9 Final at read; 44 injury rows for WAS, NYG, NE, DET; every official row has an nfl.com URL and a read date.
  3. Every brief-trace row has an allowed status, a unique id, and any URL points at nfl.com.
  4. Every flag id cited in brief_trace.csv exists in flagged.csv; every flag with an official URL uses https://www.nfl.com/.
  5. Every question and suggestion row is filled and carries an allowed answer or decision state.
  6. Every internal link in docs/nfl-e5e38f9e/*.html resolves; every external link is https and on an allowed host.
"""
from __future__ import annotations

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_nfl_e5e38f9e as b  # noqa: E402

ROOT = b.ROOT
ALLOWED_STATUS = set(b.STATUS_LABEL)
ALLOWED_HOSTS = {"www.nfl.com", "nfl.com", "github.com"}
ALLOWED_QUESTION_TYPES = {"owner_decision", "self_serveable", "owner_decision_and_self_serveable"}
ALLOWED_SUG_STATUS = {"awaiting_human_choice"}


def rows(name: str) -> list[dict]:
    return b.read_local(name)


def check_generated() -> list[str]:
    errs = []
    outs = b.build_outputs()
    for path, text in outs.items():
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if cur != text:
            errs.append(f"drift: {os.path.relpath(path, ROOT)} is stale; run scripts/build_nfl_e5e38f9e.py")
    return errs


def check_official() -> list[str]:
    errs = []
    finals = rows("official_w10_finals.csv")
    if len(finals) != 14:
        errs.append(f"official_w10_finals.csv: expected 14 Week 10 games, found {len(finals)}")
    n_final = sum(1 for r in finals if r["official_status_at_read"] == "Final")
    if n_final != 9:
        errs.append(f"official_w10_finals.csv: expected 9 Final at read, found {n_final}")
    for r in finals:
        src = r["official_game_page"] or r["official_schedule_page"]
        if not src.startswith("https://www.nfl.com/"):
            errs.append(f"{r['game_key']}: no official nfl.com source link")
        if not r["official_schedule_page"].startswith("https://www.nfl.com/"):
            errs.append(f"{r['game_key']}: schedule page not on nfl.com")
        if r["official_status_at_read"] == "Final" and not (r["away_score"].isdigit() and r["home_score"].isdigit()):
            errs.append(f"{r['game_key']}: Final game without integer scores")
        if not r["read_on_utc"]:
            errs.append(f"{r['game_key']}: no read date")

    inj = rows("official_injury_spotcheck.csv")
    if len(inj) != 44:
        errs.append(f"official_injury_spotcheck.csv: expected 44 rows, found {len(inj)}")
    clubs = {r["club"] for r in inj}
    if clubs != {"WAS", "NYG", "NE", "DET"}:
        errs.append(f"official_injury_spotcheck.csv: clubs {sorted(clubs)} != WAS NYG NE DET")
    for r in inj:
        if r["official_source_url"] != "https://www.nfl.com/injuries/":
            errs.append(f"{r['row_id']}: source is not the nfl.com injury report")
        if not r["read_on_utc"]:
            errs.append(f"{r['row_id']}: no read date")
    return errs


def check_trace() -> list[str]:
    errs = []
    trace = rows("brief_trace.csv")
    ids = [r["item_id"] for r in trace]
    if len(ids) != len(set(ids)):
        errs.append("brief_trace.csv: duplicate item_id")
    flags = {r["flag_id"] for r in rows("flagged.csv")}
    for r in trace:
        if r["status"] not in ALLOWED_STATUS:
            errs.append(f"{r['item_id']}: status {r['status']!r} not allowed")
        url = r["official_source_url"]
        if url and not url.startswith("https://www.nfl.com/"):
            errs.append(f"{r['item_id']}: URL is not an nfl.com page")
        for fid in filter(None, (x.strip() for x in r["flag_ids"].split(";"))):
            if fid not in flags:
                errs.append(f"{r['item_id']}: cites flag {fid} which is not in flagged.csv")
    return errs


def check_flags_and_registers() -> list[str]:
    errs = []
    for r in rows("flagged.csv"):
        url = r["official_source_url"]
        if url and not url.startswith("https://www.nfl.com/"):
            errs.append(f"{r['flag_id']}: flag URL not on nfl.com")
        if not r["title"] or not r["what_we_observed"]:
            errs.append(f"{r['flag_id']}: missing title or observation")
    for r in rows("questions.csv"):
        if r["answer_type"] not in ALLOWED_QUESTION_TYPES:
            errs.append(f"{r['question_id']}: answer_type {r['answer_type']!r} not allowed")
        if not r["how_to_answer"]:
            errs.append(f"{r['question_id']}: no route to an answer")
    for r in rows("suggestions.csv"):
        if r["status"] not in ALLOWED_SUG_STATUS:
            errs.append(f"{r['suggestion_id']}: status {r['status']!r} is not review-only")
        if not r["options_for_review"] or not r["recommended_path"]:
            errs.append(f"{r['suggestion_id']}: missing options or recommendation")
    return errs


class _LinkParser:
    HREF = re.compile(r'href="([^"]+)"')


def check_links() -> list[str]:
    errs = []
    d = b.DOCS
    for name in sorted(os.listdir(d)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(d, name), encoding="utf-8") as fh:
            text = fh.read()
        for href in _LinkParser.HREF.findall(text):
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            if href.startswith("https://"):
                host = href.split("/")[2]
                if host not in ALLOWED_HOSTS:
                    errs.append(f"{name}: external host not allowed: {host}")
                continue
            if href.startswith("http://") or href.startswith("javascript:"):
                errs.append(f"{name}: disallowed link {href}")
                continue
            target = os.path.normpath(os.path.join(d, href))
            if not os.path.exists(target):
                errs.append(f"{name}: broken internal link {href}")
    return errs


def run() -> list[str]:
    return (check_generated() + check_official() + check_trace()
            + check_flags_and_registers() + check_links())


def main() -> int:
    errs = run()
    trace = rows("brief_trace.csv")
    counts: dict[str, int] = {}
    for r in trace:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    if errs:
        print("FAILED")
        for e in errs:
            print("  -", e)
        return 1
    print(f"OK: {len(trace)} brief rows; statuses {dict(sorted(counts.items()))}; "
          f"{len(rows('flagged.csv'))} flags; {len(rows('questions.csv'))} questions; "
          f"{len(rows('suggestions.csv'))} suggestions; links and drift clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
