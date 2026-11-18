# Repository review — session `0d4da02c`

**Base commit:** `aa827981092a7d1996b1122bda0d2decc7f626c7` · **Reviewed:** 2026-11-18
**Method:** every finding below is produced by `src/nfl_0d4da02c/repo_review.py`, which scans the
tracked files at the base commit. Nothing in this document is hand-written. Where a check could not
be performed (a file that is not valid UTF-8, a CSV that will not parse) the script raises a finding
rather than skipping the file silently.

## Scope

| Metric | Value |
|---|---|
| tracked files scanned | 1166 |
| CSV files parsed | 415 |
| HTML files parsed | 365 |
| findings raised | 113 |

## Findings by severity

| Severity | Count |
|---|---|
| medium | 73 |
| high | 21 |
| info | 11 |
| low | 8 |

## Findings by check

| Check | Count |
|---|---|
| `F-CSV-BLANKSOURCE` | 47 |
| `F-CSV-NOSOURCE` | 34 |
| `F-HTML-INPUT` | 13 |
| `F-REGISTER-DUP` | 9 |
| `F-LARGE` | 5 |
| `F-PLACEHOLDER` | 3 |
| `F-HTML-LINK` | 1 |
| `F-PACK-COUNT` | 1 |

## Headline irregularities

1. **27 committed data CSVs have no source-like column at all.** A header is treated as
   source-bearing if it names a source, official, evidence, reference, link, page or url. The
   requirement (P-05) is that every table row carries a source link to an official site. Governance
   registers of this pack are excluded from this count and marked `info` rather than `medium`.

2. **44 data CSVs have rows with a blank source cell.** A blank source cell renders as a
   blank link on the page, which is the visible symptom.

3. **18 parallel NFL data packs and 18 matching site directories**, with up to 23 separate files
   registering the same concept under different column vocabularies: 23 `depth*`, 18 `flagged*`,
   15 `suggestions*`, 15 `injury*`, 13 `gates*`, 11 `correlations*`, 10 `questions*`,
   6 `requirements*`, 3 `readiness*`. No reviewer can compare two of them.

4. **13 published pages contain interactive controls** (`<input>`, `<select>`, `<textarea>` or
   `<button>`), which the brief forbids ("there should be no manual input on my part").

5. **One broken internal link**: `docs/dashboard.html` links to `lab/`, and `docs/lab/` has no
   `index.html`.

6. **Five committed files exceed 1 MB**, the largest being `data/source_coverage/rows.csv`
   (11,274,771 bytes) and `docs/assurance/repo-audit.html` (9,788,464 bytes).

7. **Three committed scripts contain placeholder markers** (`TODO`, `FIXME`, `XXX`).

## What the review could not do

- It did **not** re-read any official page. Every official value in this pack comes from the four
  dated reads logged in `data/nfl_0d4da02c/official_reads.csv`; everything else is a repo claim.
- It did **not** verify the arithmetic inside other packs' registers. It checked that each CSV
  parses, that its columns are consistent, and that a source column exists and is populated.
- It did **not** re-run other packs' verifiers. That is their CI's job.
- The keyword scan in `repo_evidence.csv` shows which files *mention* a requirement. It does not
  show that those files *satisfy* it. That distinction is printed on the requirements page.

## Finding register

The full register is `data/nfl_0d4da02c/repo_findings.csv` (113 rows) and is rendered on
`docs/nfl-0d4da02c/repo-review.html`. The first 113 rows are reproduced below.

| Finding | Severity | Path | What was found | Evidence |
|---|---|---|---|---|
| F-CSV-BLANKSOURCE | medium | `data/assurance/row_audit.csv` | 2723 of 16067 rows have a blank source cell | column 'source_url' |
| F-CSV-BLANKSOURCE | medium | `data/line_reverification_2026-11-03.csv` | 1 of 40 rows have a blank source cell | column 'official_source_read_on' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_309921cc/depth_unlisted_designations.csv` | 3 of 4 rows have a blank source cell | column 'same_prefix_name_on_chart' |
| F-CSV-BLANKSOURCE | high | `data/nfl_48217a55/depth_of_replacement.csv` | 151 of 151 rows have a blank source cell | column 'replacement_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_48217a55/depth_route_probe.csv` | 1 of 2 rows have a blank source cell | column 'club_hosted_depth_link_found' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_48217a55/price_capture_attempts.csv` | 1 of 4 rows have a blank source cell | column 'what_the_page_actually_contains' |
| F-CSV-BLANKSOURCE | high | `data/nfl_48217a55/week10_slate.csv` | 14 of 14 rows have a blank source cell | column 'venue_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_67233566/fixtures_week11.csv` | 18 of 19 rows have a blank source cell | column 'venue_source' |
| F-CSV-BLANKSOURCE | high | `data/nfl_67233566/roster_ir_sweep.csv` | 32 of 32 rows have a blank source cell | column 'ir_or_reserve_list_source' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_67233566/validation_gates.csv` | 1 of 13 rows have a blank source cell | column 'evidence_in_this_pack' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_6ab24751/readiness.csv` | 39 of 81 rows have a blank source cell | column 'evidence_artifact' |
| F-CSV-BLANKSOURCE | high | `data/nfl_6cefc476/leaderboard.csv` | 6 of 6 rows have a blank source cell | column 'official_rank' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_6cefc476/replacement_depth.csv` | 56 of 72 rows have a blank source cell | column 'depth_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_6cefc476/results_feed.csv` | 1 of 16 rows have a blank source cell | column 'backtest_grade_ref' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_7a59fd89/availability_conflicts.csv` | 60 of 96 rows have a blank source cell | column 'roster_page_status' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_7a59fd89/week10_finals.csv` | 1 of 14 rows have a blank source cell | column 'score_source' |
| F-CSV-BLANKSOURCE | high | `data/nfl_8362b702/availability_edges.csv` | 79 of 79 rows have a blank source cell | column 'actual_start_evidence' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_8362b702/availability_sweep.csv` | 31 of 32 rows have a blank source cell | column 'roster_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_8362b702/reserve_register.csv` | 17 of 41 rows have a blank source cell | column 'jersey_on_page' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_8362b702/venues_week11.csv` | 11 of 13 rows have a blank source cell | column 'stadium_on_page' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_d966f630/depth_of_replacement.csv` | 212 of 213 rows have a blank source cell | column 'tiers_dropped_evidenced' |
| F-CSV-BLANKSOURCE | high | `data/nfl_d966f630/model_parameters.csv` | 8 of 8 rows have a blank source cell | column 'source_kind' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_d966f630/originated_lines.csv` | 13 of 14 rows have a blank source cell | column 'grade_official_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_d966f630/price_capture_attempts.csv` | 1 of 4 rows have a blank source cell | column 'source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_d966f630/results_reconciliation.csv` | 10 of 96 rows have a blank source cell | column 'official_card_badge_w_l_t' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_dfc0c1bc/flagged.csv` | 13 of 26 rows have a blank source cell | column 'source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_dfc0c1bc/information_board.csv` | 6 of 16 rows have a blank source cell | column 'information_added_by_official_reads' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_dfc0c1bc/metrics.csv` | 49 of 55 rows have a blank source cell | column 'rows_market_number_official_host' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_dfc0c1bc/questions_master.csv` | 66 of 176 rows have a blank source cell | column 'status_in_source' |
| F-CSV-BLANKSOURCE | info | `data/nfl_dfc0c1bc/suggestions_master.csv` | 79 of 159 rows have a blank source cell (governance register) | column 'priority_in_source' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_e5e38f9e/brief_trace.csv` | 61 of 76 rows have a blank source cell | column 'official_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_e5e38f9e/flagged.csv` | 6 of 16 rows have a blank source cell | column 'official_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_e5e38f9e/injury_pack_comparison.csv` | 24 of 44 rows have a blank source cell | column 'official_game' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_e5e38f9e/official_injury_spotcheck.csv` | 24 of 44 rows have a blank source cell | column 'game_status_official' |
| F-CSV-BLANKSOURCE | high | `data/nfl_e5e38f9e/official_w10_finals.csv` | 14 of 14 rows have a blank source cell | column 'official_game_page' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_e5e38f9e/questions.csv` | 5 of 14 rows have a blank source cell | column 'official_source_url' |
| F-CSV-BLANKSOURCE | info | `data/nfl_e5e38f9e/suggestions.csv` | 8 of 11 rows have a blank source cell (governance register) | column 'official_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_f4/correlations.csv` | 1 of 6 rows have a blank source cell | column 'source_x' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_f4/flagged.csv` | 10 of 20 rows have a blank source cell | column 'source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_f4/originated_markets.csv` | 39 of 42 rows have a blank source cell | column 'results_source_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_f4/repo_review.csv` | 3 of 12 rows have a blank source cell | column 'source_url' |
| F-CSV-BLANKSOURCE | info | `data/nfl_market/sources.csv` | 4 of 9 rows have a blank source cell (governance register) | column 'verbatim_evidence_excerpt' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_s11/injury_reconciliation_w10.csv` | 2 of 49 rows have a blank source cell | column 'page_value_transcribed' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_wk/depth_deficiency.csv` | 191 of 326 rows have a blank source cell | column 'depth_chart_url' |
| F-CSV-BLANKSOURCE | medium | `data/nfl_wk/depth_summary.csv` | 16 of 28 rows have a blank source cell | column 'depth_chart_url' |
| F-CSV-BLANKSOURCE | medium | `data/session_107fc87d_verification.csv` | 4 of 53 rows have a blank source cell | column 'official_value' |
| F-CSV-BLANKSOURCE | medium | `data/source_coverage/rows.csv` | 30401 of 31299 rows have a blank source cell | column 'other_https_urls' |
| F-CSV-NOSOURCE | medium | `data/empirical/closing_probabilities.csv` | no source-like column in the header | header: observation_id,closing_market_probability |
| F-CSV-NOSOURCE | medium | `data/forward_test_summary_2026-11-02.csv` | no source-like column in the header | header: metric,value |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/blank_audit.csv` | no source-like column in the header | header: table,rows,columns,cells,blank_cells,blank_pct,why_blank,flag_ids |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/integrity_checks.csv` | no source-like column in the header | header: check,value_a,value_b,result,note |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/luck_panel.csv` | no source-like column in the header | header: metric,value,derivation |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/standings_point_in_time.csv` | no source-like column in the header | header: club,club_name,through_week,w,l,t,games,win_pct,pf,pa,net_points,pf_per_game,pa_per_game,margin_per_game,week10_games_removed |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/standings_reconstruction.csv` | no source-like column in the header | header: club,rendered_record,rendered_pf,rendered_pa,week10_games_subtracted,subtracted_pf,subtracted_pa,reconstructed_record,reconstructed_pf,reconstructed_pa |
| F-CSV-NOSOURCE | info | `data/nfl_48217a55/suggestions.csv` | no source-like column in the header (governance register) | header: suggestion_id,title,category,what_it_changes,options,cost_of_doing_nothing,priority |
| F-CSV-NOSOURCE | medium | `data/nfl_48217a55/team_ratings_naive.csv` | no source-like column in the header | header: club,club_name,rating_ppg,win_pct,pf_per_game,pa_per_game,opponent_adjusted,blocking_gate,note |
| F-CSV-NOSOURCE | medium | `data/nfl_7a59fd89/injury_delta.csv` | no source-like column in the header | header: club,player_prior,player_current,position,field,value_prior,value_current,delta_kind |
| F-CSV-NOSOURCE | medium | `data/nfl_7a59fd89/schedule_announcement.csv` | no source-like column in the header | header: attempt_id,target,outcome,detail,read_at_utc |
| F-CSV-NOSOURCE | medium | `data/nfl_dfc0c1bc/answers.csv` | no source-like column in the header | header: answer_id,theme,question,answer,status,reads,still_open,note_on_repo |
| F-CSV-NOSOURCE | medium | `data/nfl_dfc0c1bc/claim_checks.csv` | no source-like column in the header | header: claim_id,metric,claim,where,test,measured_from_file,actual,verdict |
| F-CSV-NOSOURCE | medium | `data/nfl_dfc0c1bc/corpus_sizes.csv` | no source-like column in the header | header: metric_id,pack,file,rows,weeks,games_with_final_scores,rows_counted_in_backtest,status |
| F-CSV-NOSOURCE | medium | `data/nfl_dfc0c1bc/lions_status_check.csv` | no source-like column in the header | header: player,found_in_capture,club,practice_status_in_file,game_status_in_file,read_at_utc_in_file |
| F-CSV-NOSOURCE | medium | `data/nfl_dfc0c1bc/observations.csv` | no source-like column in the header | header: obs_id,read_id,observation,supports,theme |
| F-CSV-NOSOURCE | info | `data/nfl_dfc0c1bc/repo_findings.csv` | no source-like column in the header (governance register) | header: finding_id,finding,measured,why_it_matters_for_decisions,suggested_action,owner_decision |
| F-CSV-NOSOURCE | info | `data/nfl_dfc0c1bc/suggestions_inventory.csv` | no source-like column in the header (governance register) | header: kind,pack,path,rows,columns,sha256 |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/depth_unit_summary.csv` | no source-like column in the header | header: team,unit,slots_listed,starters_ruled_out,replacement_from_3rd_string_or_worse,deficiency_points_total,contingency_slots_3rd_string_or_worse,worst_case_ |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/fair_vs_market.csv` | no source-like column in the header | header: market_id,game_key,market,origination_order,model_fair_line,market_line,difference,difference_units,model_prob,market_prob,probability_difference,model_ |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/leaderboard.csv` | no source-like column in the header | header: rank,strategy_id,name,signal_score_per_bet,staking_score,signal_rank,staking_rank,rank_gap,certified,verdict |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/leaderboard_mask_test.csv` | no source-like column in the header | header: strategies_with_positive_staking_and_nonpositive_signal,board_can_mask,certified_strategies,max_settled_bets_on_any_strategy,verdict |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/leaderboard_strategies.csv` | no source-like column in the header | header: strategy_id,name,market,structure,origin_order,bets_defined,bets_settled,weeks_covered,signal_bets,signal_score_clv_points,signal_score_per_bet,staking_ |
| F-CSV-NOSOURCE | medium | `data/nfl_f4/strategy_state.csv` | no source-like column in the header | header: strategy_id,name,current_state,target_state,reason_code,reason_text,bets_settled,signal_score_per_bet,staking_score,sticky,re_entry_condition,effective_ |
| F-CSV-NOSOURCE | info | `data/nfl_f4/suggestions.csv` | no source-like column in the header (governance register) | header: s_id,suggestion,why,options,cost,risk,recommendation,state |
| F-CSV-NOSOURCE | medium | `data/nfl_market/demotion_gate.csv` | no source-like column in the header | header: strategy_id,trailing_window_n,trailing_hit_rate,trailing_p_vs_fair_coin,max_drawdown_units,triggers_fired,lifecycle_status,lifecycle_detail,threshold_D1 |
| F-CSV-NOSOURCE | medium | `data/nfl_market/leaderboard.csv` | no source-like column in the header | header: strategy_id,tier,tier_label,n,hit_rate,ci_low,ci_high,p_one_sided_fair_coin,signal_score,staking_roi,staking_score,profit_units,divergence_flag,live,rew |
| F-CSV-NOSOURCE | medium | `data/nfl_market/promotion_ladder.csv` | no source-like column in the header | header: strategy_id,n,hit_rate,gates_closed,rung,promotion_granted,why |
| F-CSV-NOSOURCE | info | `data/nfl_market/repo_findings.csv` | no source-like column in the header (governance register) | header: finding_id,area,severity,finding,why_it_matters |
| F-CSV-NOSOURCE | info | `data/nfl_market/suggestions.csv` | no source-like column in the header (governance register) | header: id,area,title,option_a,option_b,option_c,recommended,rationale,effort,reversible,status,decision_owner |
| F-CSV-NOSOURCE | medium | `data/nfl_wk/depth_cascade.csv` | no source-like column in the header | header: team,position_group,slot_1_player,slot_1_status,slot_2_player,slot_2_status,next_listed_player,next_listed_slot,next_listed_status,slots_listed_on_chart |
| F-CSV-NOSOURCE | medium | `data/nfl_wk/input_manifest.csv` | no source-like column in the header | header: file,sha256,bytes |
| F-CSV-NOSOURCE | medium | `data/nfl_wk/leaderboard.csv` | no source-like column in the header | header: rank,strategy_id,name,family,gates_passed,holdout_bets,roi,clv,brier_skill,eligibility,tier,research_units,reward_paid,status_note |
| F-CSV-NOSOURCE | info | `data/nfl_wk/requirements.csv` | no source-like column in the header (governance register) | header: id,requirement,deliverable,file,status,note |
| F-HTML-INPUT | high | `docs/dashboard.html` | page contains an interactive control, which the brief forbids | 10 control(s): button, input |
| F-HTML-INPUT | high | `docs/review/flagged.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/review/index.html` | page contains an interactive control, which the brief forbids | 2 control(s): input |
| F-HTML-INPUT | high | `docs/review/repo-review.html` | page contains an interactive control, which the brief forbids | 3 control(s): input |
| F-HTML-INPUT | high | `docs/review/summary.html` | page contains an interactive control, which the brief forbids | 3 control(s): input |
| F-HTML-INPUT | high | `docs/review/verification.html` | page contains an interactive control, which the brief forbids | 2 control(s): input |
| F-HTML-INPUT | high | `docs/verified/flagged.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/verified/games.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/verified/legal-kr.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/verified/methodology.html` | page contains an interactive control, which the brief forbids | 2 control(s): input |
| F-HTML-INPUT | high | `docs/verified/nba-policy.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/verified/sources.html` | page contains an interactive control, which the brief forbids | 1 control(s): input |
| F-HTML-INPUT | high | `docs/verified/strategies.html` | page contains an interactive control, which the brief forbids | 2 control(s): input |
| F-HTML-LINK | high | `docs/dashboard.html` | 1 internal link(s) resolve to a missing file | lab/ |
| F-LARGE | low | `data/assurance/row_audit.csv` | committed file is larger than 1 MB | 6,369,125 bytes |
| F-LARGE | low | `data/source_coverage/rows.csv` | committed file is larger than 1 MB | 11,274,771 bytes |
| F-LARGE | low | `docs/assurance/repo-audit.html` | committed file is larger than 1 MB | 9,788,464 bytes |
| F-LARGE | low | `docs/coverage/flagged.html` | committed file is larger than 1 MB | 1,096,178 bytes |
| F-LARGE | low | `docs/coverage/rows.html` | committed file is larger than 1 MB | 11,268,720 bytes |
| F-PACK-COUNT | info | `data/, docs/` | the repository holds many parallel NFL packs with overlapping registers | 18 data packs, 18 site directories |
| F-PLACEHOLDER | low | `scripts/check_daily.py` | 1 placeholder marker(s) in a committed file | TODO |
| F-PLACEHOLDER | low | `scripts/check_nfl_3b81013c.py` | 1 placeholder marker(s) in a committed file | XXX |
| F-PLACEHOLDER | low | `scripts/check_nfl_wk.py` | 3 placeholder marker(s) in a committed file | FIXME, TODO, XXX |
| F-REGISTER-DUP | medium | `data/**/correlations*.csv` | 11 separate files register the same concept under different column vocabularies | data/nfl/correlations.csv; data/nfl_309921cc/correlations.csv; data/nfl_3b81013c/correlations.csv; data/nfl_48217a55/correlations.csv; data/nfl_67233566/correla |
| F-REGISTER-DUP | medium | `data/**/depth*.csv` | 23 separate files register the same concept under different column vocabularies | data/nfl/depth_model.csv; data/nfl_309921cc/depth_charts.csv; data/nfl_309921cc/depth_deficiency.csv; data/nfl_309921cc/depth_unlisted_designations.csv; data/nf |
| F-REGISTER-DUP | medium | `data/**/flagged*.csv` | 18 separate files register the same concept under different column vocabularies | data/flagged_items.csv; data/nfl/flagged.csv; data/nfl_309921cc/flagged.csv; data/nfl_48217a55/flagged.csv; data/nfl_67233566/flagged.csv; data/nfl_6ab24751/fla |
| F-REGISTER-DUP | medium | `data/**/gates*.csv` | 13 separate files register the same concept under different column vocabularies | data/nfl/validation_gates.csv; data/nfl_309921cc/validation_gates.csv; data/nfl_3b81013c/validation_gates.csv; data/nfl_48217a55/validation_gates.csv; data/nfl_ |
| F-REGISTER-DUP | medium | `data/**/injury*.csv` | 15 separate files register the same concept under different column vocabularies | data/nfl/injury_tracking.csv; data/nfl_309921cc/week10_injury_load.csv; data/nfl_48217a55/injury_club_rollup.csv; data/nfl_48217a55/injury_report_2026_11_15.csv |
| F-REGISTER-DUP | medium | `data/**/questions*.csv` | 10 separate files register the same concept under different column vocabularies | data/nfl/decision_questions.csv; data/nfl_3b81013c/open_questions.csv; data/nfl_48217a55/questions.csv; data/nfl_67233566/questions.csv; data/nfl_6cefc476/decis |
| F-REGISTER-DUP | medium | `data/**/readiness*.csv` | 3 separate files register the same concept under different column vocabularies | data/nfl_48217a55/requirements_decision_readiness.csv; data/nfl_6ab24751/readiness.csv; data/nfl_8362b702/readiness.csv |
| F-REGISTER-DUP | medium | `data/**/requirements*.csv` | 6 separate files register the same concept under different column vocabularies | data/nfl/requirements.csv; data/nfl_48217a55/requirements_decision_readiness.csv; data/nfl_67233566/requirements_trace.csv; data/nfl_d966f630/requirements_trace |
| F-REGISTER-DUP | medium | `data/**/suggestions*.csv` | 15 separate files register the same concept under different column vocabularies | data/nfl/suggestions.csv; data/nfl_309921cc/suggestions.csv; data/nfl_3b81013c/site_suggestions.csv; data/nfl_48217a55/suggestions.csv; data/nfl_67233566/sugges |

---

Flagged irregularities and unverified items are published on the site's
[Flagged for Review](https://sassnarep3-star.github.io/Own6/docs/nfl-0d4da02c/flagged.html) page
and do not block the merge.
