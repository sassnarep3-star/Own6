"""Flagged irregularities for pack nfl_0d4da02c.

Two kinds of row, kept apart by ``flag_scope``:

  pack      something this session found in its own evidence or in the repo
  inherited a defect recorded by a prior pack and not re-verified here

Nothing here blocks the merge. Every row carries the source a reviewer can open.
A row whose ``value_if_known`` is empty means: the honest value is unknown, and
the table cell it belongs to is blank.

Run:  python3 -m src.nfl_0d4da02c.flags
"""
from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl_0d4da02c")

INJ = "https://www.nfl.com/injuries/"
SCHED = "https://www.nfl.com/schedules/2026/REG11/"
REPO = "https://github.com/sassnarep3-star/Own6"

# (id, scope, severity, area, item, what_we_found, value_if_known, source_url, req_ids)
FLAGS: list[tuple[str, ...]] = [
    ("F-01", "pack", "high", "Availability",
     "Week 11 injury report not published at read time",
     "A request for /injuries/league/2026/REG11/ resolved to the canonical Week 10 URL with the "
     "Week 10 heading. No Week 11 availability evidence exists yet.",
     "", INJ, "R-21, R-54, R-55"),
    ("F-02", "pack", "high", "Fixtures",
     "Twelve of thirteen Week 11 venues come from a hotel affiliate link",
     "The only venue-bearing text on the official schedule page for those games is the "
     "destination parameter of the page's own Hotel affiliate link. That text is on the official "
     "page, but it is not a venue field.",
     "", SCHED, "R-23"),
    ("F-03", "pack", "medium", "Fixtures",
     "Stadium name for the Mexico City game is unknown",
     "The page badges the game 'Mexico City' with the Mexico City 2026 logo but does not name a "
     "stadium in the text read this session.",
     "", SCHED, "R-23"),
    ("F-04", "pack", "medium", "Availability",
     "Four clubs have no Week 10 injury section",
     "CHI, DEN, PHI and TB are absent from the Week 10 report. That is a bye-week presentation, "
     "not a clean bill of health, and it is published as absence with that reason.",
     "", INJ, "R-49, R-64"),
    ("F-05", "pack", "medium", "Engineering",
     "The read is stamped with a session window, not a clock time",
     "The owner asked for every injury-hub read to carry its clock time. This session can prove "
     "the read happened on 2026-11-18, not the instant it happened.",
     "", INJ, "R-21, R-55"),
    ("F-06", "pack", "medium", "Availability",
     "Two official headlines give different recovery windows for one player",
     "One dated official headline says Lamar Jackson is out 6-9 weeks; another dated 2026-11-13 "
     "says the Ravens confirmed 6-10 weeks. Both are quoted; neither is reconciled.",
     "", INJ, "R-34, R-46"),
    ("F-07", "pack", "low", "Availability",
     "A conditional report is not a fact",
     "The official headline says Drake Maye 'could miss' the rest of the season. The Week 10 "
     "injury report lists him Full Participation with no game status.",
     "", INJ, "R-42"),
    ("F-08", "pack", "low", "Availability",
     "An expected starter is not a declared starter",
     "The official headline says Kyle McCord is 'in line for first start' after Willis went to "
     "injured reserve. The injury report lists no Miami quarterback with an injury.",
     "", INJ, "R-42"),
    ("F-09", "pack", "medium", "Availability",
     "No dated starter announcement found for Brissett",
     "The owner named Brissett alongside Lock and McCord. No dated official announcement for him "
     "appeared in the news rail read on 2026-11-18. The cell is left blank rather than filled.",
     "", INJ, "R-42"),
    ("F-10", "pack", "high", "Prices",
     "No official market-price source exists",
     "Every price column in this pack and in the repository is blank. No residual, no closing "
     "line value and no vig decomposition can be published.",
     "", "", "R-01, R-04, R-18, R-59, R-60, R-73"),
    ("F-11", "pack", "medium", "Results",
     "The results feed was not re-read this session",
     "Prior packs publish a 136-150 game corpus. This session inherited it as a repo claim and "
     "did not re-read it, so no row carries this session's read date.",
     "", "", "R-02, R-19, R-26"),
    ("F-12", "pack", "high", "Repo",
     "Data files with no source-like column",
     "A scan of 415 committed CSV files found data files whose header contains no source, "
     "official, evidence, reference or url column, which is contrary to the requirement that "
     "every table row carry a source link.",
     "", REPO, "P-05"),
    ("F-13", "pack", "high", "Repo",
     "Published pages contain interactive controls",
     "The brief says there should be no manual input. A scan found page(s) under docs/ containing "
     "<input>, <select>, <textarea> or <button> elements.",
     "", REPO, "P-01"),
    ("F-14", "pack", "medium", "Repo",
     "One broken internal link in the existing site",
     "docs/dashboard.html links to 'lab/', and docs/lab/ has no index.html.",
     "", REPO, "P-04"),
    ("F-15", "pack", "medium", "Repo",
     "Parallel packs duplicate the same registers",
     "The repository holds 18 NFL data packs and 18 matching site directories, with up to 23 "
     "separate files registering the same concept under different column vocabularies.",
     "", REPO, "P-03"),
    ("F-16", "pack", "low", "Repo",
     "Committed files larger than 1 MB",
     "Five committed files exceed 1 MB, including an 11 MB coverage table and a 9.8 MB audit page.",
     "", REPO, "P-03"),
    ("F-17", "pack", "low", "Method",
     "The stored hash is a hash of our transcript, not of the page",
     "official_reads.csv records SHA-256 of the exact text this session transcribed. It is a "
     "tamper check on the committed data and is labelled as such; it is not a fingerprint of the "
     "page's bytes.",
     "", INJ, "R-21, R-30"),
    ("F-18", "pack", "low", "Repo",
     "Placeholder markers in committed scripts",
     "TODO, FIXME and XXX markers were found in committed verification scripts.",
     "", REPO, "P-03"),
    ("F-19", "pack", "medium", "Availability",
     "One read cannot produce a delta",
     "The owner wants the injury signal as a delta, not a level. This session has one dated read, "
     "so the injury table is necessarily published as levels until a second read exists.",
     "", INJ, "R-12, R-21, R-55"),
    ("F-20", "pack", "high", "Statistics",
     "Designation counts have no outcome leg",
     "90 Questionable, 70 Out and 11 Doubtful rows are counted from official text, but whether "
     "those players played is unknown without the official inactive list.",
     "", INJ, "R-44, R-53"),
    ("F-21", "inherited", "medium", "Availability",
     "Texans depth published as an image",
     "Recorded by prior packs and not re-read this session.",
     "", "", "R-32, R-52"),
    ("F-22", "inherited", "medium", "Availability",
     "Packers depth rows prepend jersey numbers",
     "Recorded by prior packs and not re-read this session.",
     "", "", "R-32"),
    ("F-23", "inherited", "medium", "Availability",
     "Stale depth rows versus the official transactions log",
     "Prior packs report Baltimore still publishing Lamar Jackson and Tyler Huntley at quarterback "
     "after both went on injured reserve. Not re-verified this session.",
     "", "", "R-46"),
    ("F-24", "inherited", "medium", "Availability",
     "Game Book host unreachable",
     "Prior sessions report the host could not be reached. Not attempted this session.",
     "", "", "R-10, R-25"),
    ("F-25", "inherited", "medium", "Availability",
     "No official snap-count source",
     "No session has read an official snap-count source.",
     "", "", "R-11, R-56"),
    ("F-26", "inherited", "medium", "Governance",
     "Terms of use reported to restrict automated capture",
     "Prior sessions record that section 1.3 restricts automated capture. Not re-read this session.",
     "", "", "R-20, R-29, R-30, R-39"),
]


def main() -> int:
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "flagged.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["flag_id", "flag_scope", "severity", "area", "item",
                    "what_we_found", "value_if_known", "source_url", "req_ids",
                    "reviewer_note"])
        for f in FLAGS:
            w.writerow(list(f) + [""])
    print(f"wrote flagged.csv: {len(FLAGS)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
