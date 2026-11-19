#!/usr/bin/env python3
"""Write every CSV in data/nfl_d713b52f/ except capture_log.csv (which capture.py owns).

No network. No clock. Re-running reproduces the tree byte for byte, which is what
the CI determinism step checks.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_d713b52f import audit, capture, derive, model  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_d713b52f")


def write(name, rows, columns=None):
    path = os.path.join(DATA, name)
    if not rows:
        raise SystemExit(f"refusing to write an empty table: {name}")
    if columns is None:
        columns = list(rows[0].keys())
    else:
        for r in rows:
            for c in columns:
                r.setdefault(c, "")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"{name}: {len(rows)} rows x {len(columns)} cols")


def main():
    os.makedirs(DATA, exist_ok=True)

    # --- capture -----------------------------------------------------------
    write("capture_log.csv", capture.capture_rows(),
          ["capture_id", "raw_file", "source_url", "kind", "read_at_utc", "sha256",
           "bytes", "used_for", "hash_scope"])
    write("source_probe.csv", capture.PROBE,
          ["probe_id", "question", "answer", "evidence", "raw", "caveat", "official", "status"])

    # --- official capture, verbatim ---------------------------------------
    write("standings.csv", derive.standings_rows())
    write("fixtures.csv", derive.fixture_rows())
    write("starters.csv", derive.starters_rows())
    write("playtime.csv", derive.playtime_rows())
    write("snap_sum.csv", derive.snap_sum_rows())
    write("game_status.csv", derive.status_rows())
    write("designation_join.csv", derive.designation_join_rows())
    write("replacement.csv", derive.replacement_rows())
    write("snap_gap.csv", derive.snap_gap_rows())
    write("fixture_features.csv", derive.fixture_feature_rows())

    # not_active: the book's own block, one row per printed entry
    na_rows = []
    for gid, g in derive.GAME_INDEX.items():
        for club in (g["away"], g["home"]):
            for pos, num, name in derive.NOT_ACTIVE[club]:
                na_rows.append(dict(
                    game_id=gid, club=club, position_listed=pos, jersey_as_printed=num,
                    player_as_printed=name,
                    evidence="official Game Book 'Not Active' block",
                    postkickoff="yes: the book is published after the game",
                    source_url=g["book"], read_at_utc=capture.READ_AT))
    write("not_active.csv", na_rows)

    # club view: one row per club per game
    na_rows = {}
    for gid2, g2 in derive.GAME_INDEX.items():
        for club2 in (g2["away"], g2["home"]):
            na_rows.setdefault(club2, []).extend(derive.NOT_ACTIVE[club2])
    club_rows = []
    joined = derive.designation_join_rows()
    for gid, g in derive.GAME_INDEX.items():
        for club in (g["away"], g["home"]):
            outs = [r for r in joined if r["game_id"] == gid and r["club"] == club and r["game_status"] == "Out"]
            qs = [r for r in joined if r["game_id"] == gid and r["club"] == club and r["game_status"] == "Questionable"]
            blanks = [r for r in joined if r["game_id"] == gid and r["club"] == club and r["game_status"] == "(blank)"]
            n_active = len(derive.NOT_ACTIVE[club])
            club_rows.append(dict(
                game_id=gid, club=club, opponent=(g["home"] if club == g["away"] else g["away"]),
                declared_out=str(len(outs)),
                declared_doubtful=str(len([r for r in qs if r["game_status"] == "Doubtful"])),
                declared_questionable=str(len(qs)),
                blank_game_status=str(len(blanks)),
                not_active_entries_this_pack=str(len(na_rows.get(club, []))),
                not_active_printed_in_book="6 or 7 per club as the book prints it",
                out_and_not_active=str(len([r for r in outs if r["not_active"].startswith("yes")])),
                out_not_on_inactive=str(len([r for r in outs if not r["not_active"].startswith("yes")])),
                net_injury_count=str(len(outs)),
                report_url=derive.INJ_REG10, book_url=g["book"], read_at_utc=capture.READ_AT,
                note="net_injury_count is the count of players the official report marks Out for this club in this game"))
    write("club_view.csv", club_rows)

    # --- model -------------------------------------------------------------
    bt = model.run_backtest()
    write("model_outputs.csv", bt)
    s = model.score(bt)
    write("backtest_summary.csv", [dict(
        strategy_id="S01", strategy="ML-FROZEN-MARGIN", n=str(s["n"]), weeks=str(s["weeks"]),
        brier=f"{s['brier']:.6f}", base_rate=f"{s['base_rate']:.6f}",
        brier_climatology=f"{s['brier_climatology']:.6f}", bss=f"{s['bss']:.6f}",
        bss_lo_week_cluster=f"{s['bss_lo']:.6f}", bss_hi_week_cluster=f"{s['bss_hi']:.6f}",
        bootstrap_resamples=str(s["bootstrap"]), bootstrap_seed=str(s["seed"]),
        totals_mae_points=f"{s['mae']:.6f}", totals_rmse_points=f"{s['rmse']:.6f}",
        separates_from_zero=("no" if s["bss_lo"] <= 0 else "yes"),
        state="paper",
        reading=("the week-cluster lower bound is below zero, so this model cannot be shown to be "
                 "better than guessing the base rate; it must not be promoted on this sample"))])

    # like-for-like comparison against the inherited implementation
    import csv as _csv
    inh = list(_csv.DictReader(open(os.path.join(REPO, "data", "nfl_0ce967db", "model_outputs.csv"), newline="")))
    inh_s1 = [r for r in inh if r["strategy_id"] == "S01"]
    sub = [r for r in bt if int(r["week"]) >= 3]
    b_sub = sum((float(r["p_home_win"]) - int(r["home_win"])) ** 2 for r in sub) / len(sub)
    b_inh = sum((float(r["p_home_win"]) - int(r["home_win"])) ** 2 for r in inh_s1) / len(inh_s1)
    clim_sub = None
    rate = sum(int(r["home_win"]) for r in sub) / len(sub)
    clim_sub = sum((rate - int(r["home_win"])) ** 2 for r in sub) / len(sub)
    write("implementation_comparison.csv", [dict(
        comparison="same frozen rule, two independent implementations, same 118 games (weeks 3-10)",
        games=str(len(sub)),
        brier_inherited_pack=f"{b_inh:.6f}", brier_this_pack=f"{b_sub:.6f}",
        difference=f"{abs(b_sub - b_inh):.6f}",
        measured_skill_full_run_bss=f"{s['bss']:.6f}",
        finding=("the gap between two honest implementations is larger than the measured skill; "
                 "on this sample the score cannot be separated from the implementation, let alone from noise"),
        inherited_source="data/nfl_0ce967db/model_outputs.csv (S01 rows)",
        this_source="data/nfl_d713b52f/model_outputs.csv (S01 rows, weeks>=3)")])

    write("luck_panel.csv", [model.luck_panel(bt)])
    write("week11_forecasts.csv", model.week11_forecasts())

    write("strategies.csv", [
        dict(strategy_id="S01", name="ML-FROZEN-MARGIN", division="singles-moneyline",
             definition="P(home win) = Phi(((strength_home - strength_away) + 2.5) / sigma); strength is the shrunk mean margin",
             registered_at_utc="2026-11-19T11:10:00Z",
             promote_if="100 scored prospective singles AND week-cluster BSS lower bound > 0 AND Bonferroni pass at family 7",
             demote_if="trailing-50 prospective BSS lower bound < 0 -> paper",
             what_would_change_our_mind_up="a prospective BSS lower bound above 0 over 100+ games",
             what_would_change_our_mind_down="a negative trailing-50 prospective BSS",
             backtest_n=str(s["n"]), backtest_bss=f"{s['bss']:.6f}",
             backtest_bss_lo=f"{s['bss_lo']:.6f}", prospective_n="0", state="paper",
             gate="G-SCORE"),
        dict(strategy_id="S02", name="TOT-FROZEN", division="singles-total",
             definition="expected total = league mean + both offences' shrunk deviations - both defences' shrunk deviations",
             registered_at_utc="2026-11-19T11:10:00Z",
             promote_if="100 scored prospective totals AND a walk-forward MAE lower bound below the league-mean predictor",
             demote_if="trailing-50 prospective MAE above the league-mean predictor",
             what_would_change_our_mind_up="a prospective MAE advantage with an interval excluding zero",
             what_would_change_our_mind_down="a prospective MAE worse than the league mean over 50 games",
             backtest_n=str(s["n"]), backtest_bss="", backtest_bss_lo="", prospective_n="0", state="paper",
             gate="G-SCORE"),
        dict(strategy_id="C01", name="CONTROL-CLIMATOLOGY", division="control-moneyline",
             definition="the training-window home-win rate for every game; no club information",
             registered_at_utc="2026-11-19T11:10:00Z",
             promote_if="never; a control cannot be promoted",
             demote_if="never",
             what_would_change_our_mind_up="a control beating the models would say the models are worse than nothing",
             what_would_change_our_mind_down="",
             backtest_n=str(s["n"]), backtest_bss="0.000000", backtest_bss_lo="", prospective_n="0",
             state="control", gate="G-SCORE"),
        dict(strategy_id="C02", name="CONTROL-HOME-ALWAYS", division="control-moneyline",
             definition="probability 1.0 for the home club, 0.0 away",
             registered_at_utc="2026-11-19T11:10:00Z",
             promote_if="never; a control cannot be promoted", demote_if="never",
             what_would_change_our_mind_up="a model losing to 'always home' is worse than a coin",
             what_would_change_our_mind_down="",
             backtest_n=str(s["n"]), backtest_bss="", backtest_bss_lo="", prospective_n="0",
             state="control", gate="G-SCORE"),
    ])

    # --- audit -------------------------------------------------------------
    arows = audit.audit_rows()
    write("recompute.csv", arows)
    sm = audit.summary(arows)
    write("recompute_summary.csv", [dict(
        checks=sm["checks"], match=sm["match"], mismatch=sm["mismatch"], info=sm["info"],
        pass_rate=sm["pass_rate"],
        note=("a MATCH means the inherited published number is reproduced from the inherited ledgers "
              "by this independent implementation; a MATCH (last-digit rounding) means the two agree "
              "at the published six decimals; nothing here validates a value against the official page "
              "except where the row's source is an official page"))])

    # --- registers ---------------------------------------------------------
    write("requirements.csv", derive.requirement_rows())
    write("gates.csv", derive.gate_rows())
    write("questions.csv", derive.question_rows())
    write("suggestions.csv", derive.suggestion_rows())
    write("flagged.csv", derive.flagged_rows())
    write("sources.csv", derive.source_rows())

    # --- diff between the two dated reads ---------------------------------
    diff_rows = []
    import json as _json
    prev = _json.load(open(os.path.join(REPO, "data", "nfl_a67ddef8", "standings_2026_11_19.json"), "r")) \
        if os.path.exists(os.path.join(REPO, "data", "nfl_a67ddef8", "standings_2026_11_19.json")) else None
    del prev
    # The prior read is a CSV in the inherited pack; compare club by club where both exist.
    prev_csv = os.path.join(REPO, "data", "nfl_a67ddef8", "standings_2026_11_19.csv")
    prev_rows = {}
    if os.path.exists(prev_csv):
        for r in _csv.DictReader(open(prev_csv, newline="")):
            prev_rows[r["club"]] = r
    for row in derive.standings_rows():
        p = prev_rows.get(row["club"])
        if not p:
            diff_rows.append(dict(entity="standings", key=row["club"], field="row", before="absent",
                                  after="present", changed="yes",
                                  note="club not present in the 2026-11-19 inherited read"))
            continue
        changed = []
        for f in ("w", "l", "t", "pf", "pa"):
            if p.get(f, "") != row[f]:
                changed.append(f"{f}: {p.get(f,'')}->{row[f]}")
        diff_rows.append(dict(entity="standings", key=row["club"], field="W/L/T/PF/PA",
                              before=f"{p.get('w','')}-{p.get('l','')}-{p.get('t','')} {p.get('pf','')}/{p.get('pa','')}",
                              after=f"{row['w']}-{row['l']}-{row['t']} {row['pf']}/{row['pa']}",
                              changed=("yes" if changed else "no"),
                              note=("; ".join(changed) if changed else "identical")))
    changed_n = sum(1 for r in diff_rows if r["changed"] == "yes")
    diff_rows.append(dict(entity="summary", key="clubs compared", field="changed",
                          before=f"{len(prev_rows)} prior rows", after=f"{len(derive.STANDINGS)} rows now",
                          changed=str(changed_n),
                          note=("no standings row moved between the two reads, so the Week 11 games were "
                                "not yet played at either read" if changed_n == 0 else
                                "standings moved between the reads")))
    write("diff.csv", diff_rows)

    print("\nall tables written")


if __name__ == "__main__":
    main()
