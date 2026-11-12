# NFL Injury & Starter-vs-Backup (`1st`–`4th` String) Depth-Deficiency Methodology

**Implementation Module:** `src/nfl_origination/depth.py`  
**Verified Week 10 Dataset:** `data/nfl_origination/injury_and_depth_deficiency.csv` (`DEPTH-01`..`DEPTH-24`)  
**Primary Official Sources:** [`nfl.com/injuries/`](https://www.nfl.com/injuries/), [`operations.nfl.com/.../contract-language`](https://operations.nfl.com/calendar-events/nfl-free-agency/contract-language), [`Emergency 3rd QB FAQ`](https://www.nfl.com/news/nfl-emergency-third-quarterback-rule-questions-and-answers), and 8 official club depth charts (`NFL-S16`..`NFL-S23`).

---

## 1. Official 2026 NFL Roster, Elevation & Depth Rules Encoded in `depth.py`

Line origination models that treat NFL rosters as simple injury lists miss structural CBA/Bylaw discontinuities enforced by `validate_nfl_gameday_roster()`:

1. **48-Player Gameday Active Rule & 8-Offensive-Linemen Threshold (`NFL-S03`):**
   - A club may dress **48** active players on game day **if and only if at least 8 offensive linemen** (primary position Center, Guard, or Offensive Tackle) are active.
   - If injury clusters drop active offensive linemen below 8, maximum gameday active roster size drops to **47**, costing the team an active rotational defender or special-teamer while exposing out-of-position tackle/guard snaps if one more lineman is hurt mid-game.
2. **Practice Squad Standard Elevations (`54` / `55` Expanded Pool, `NFL-S03`):**
   - Up to **2** Practice Squad players may be elevated per week via the Saturday 4:00 p.m. ET transaction wire, reverting to the 16/17-man Practice Squad the next business day without passing through waivers.
   - Each individual player is capped at **3 regular-season elevations per League Year**; a 4th appearance requires signing the player to the 53-man Active/Inactive List (releasing/IR-ing another 53-man player).
3. **Emergency Third Quarterback Rule (`NFL-S04`, `NFL-S05`):**
   - Designated on the **90-minute pre-kickoff Gameday Administration Report**.
   - Must be a bona fide quarterback on the **53-man roster** (following the NFLPA veto, Practice Squad QBs **cannot** serve as the inactive Emergency 3rd QB—if elevated from the PS, a QB consumes one of the 47/48 active slots).
   - May enter **only** if both QB1 and QB2 are unable to play due to **injury or disqualification** (never for a coaching benching or equipment issue), cannot play Wildcat/non-QB snaps, and must leave immediately if QB1 or QB2 is medically cleared.
4. **Injured Reserve Return Horizon (`NFL-S06`, `NFL-S08`):**
   - Placement on IR or Reserve/PUP locks in a **minimum 4-game absence**; clubs hold **8** regular-season designated-for-return activations (**+2** in the postseason).

---

## 2. Four-String Replacement & Cascading Unit-Cluster Framework

`evaluate_unit_deficiency()` tracks every offensive and defensive unit across four explicit string tiers (`1 = Starter`, `2 = Primary Backup`, `3 = Third String`, `4 = Fourth String / Practice Squad`) and classifies unit health into six deterministic states:

- `NOMINAL_1ST_STRING_HEALTHY`: 1st-string starter active with full/normal participation.
- `WATCH_STARTER_LIMITED`: 1st-string starter expected active on `LIMITED` practice participation.
- `MODERATE_2ND_STRING_REPLACEMENT`: Single 1st-string starter out/DNP replaced by a healthy 2nd-string backup with intact 3rd-string depth behind them.
- `HIGH_2ND_STRING_THIN_BEHIND`: 2nd-string replacement forced into starting role while adjacent unit mates or the 3rd-string backup are simultaneously impaired (`cascading_cluster_alert = True`).
- `SEVERE_3RD_STRING_ELEVATION`: Both 1st- and 2nd-string players Out/IR/DNP, forcing a **3rd-string** player onto the field (`cascading_cluster_alert = True`).
- `CRITICAL_4TH_STRING_OR_DEPLETED`: 1st, 2nd, and 3rd strings unavailable or cross-listed injured, forcing **4th-string / emergency cross-positional** snaps (`cascading_cluster_alert = True`).

### Why Cascading Unit Clusters Are Non-Linear in Football
In football, offensive line protection and defensive pass coverage are **weak-link systems**:
- Losing `LG1` alone (`MODERATE_2ND_STRING_REPLACEMENT`) allows the Center and Left Tackle to slide help toward `LG2`. Losing `LG1 + LG2` (New England Week 10: `Ben Brown OUT + Walter Rouse DNP`) or `LG1 + C1` (Arizona Week 10: `Isaac Seumalo DNP + Hjalte Froholdt DNP`) destroys double-team communication and forces help away from edge rushers.
- Losing `CB1` (`Carlton Davis III OUT` for New England) shifts every coverage matchup down a rung (`CB2 -> WR1`, `CB3 -> WR2`, `4th CB -> slot`), allowing an opposing coordinator (e.g., Detroit with `Amon-Ra St. Brown` and `Jameson Williams`) to isolate the weakest replacement defender on high-leverage downs.

---

## 3. Four-Source Reconciliation Requirement (`Gate NFL-G10` & `NFL-F07`)

Our line-by-line Week 10 audit proved that static club depth-chart webpages (`*/team/depth-chart`) **must never be used as standalone model inputs**:
1. **Explicit PR Disclaimers:** `patriots.com` (*"published by the writers of Patriots.com"*), `detroitlions.com` (*"Unofficial Depth Chart Compiled by Lions Football Communications"*), `vikings.com`, and `packers.com` (*"Unofficial, Nov. 10, 2026"*) explicitly disclaim organizational binding authority.
2. **Trade-Deadline Lag:** `vikings.com` lists `QB1 Kyler Murray (DNP) -> QB2 Carson Wentz (Limited) -> QB3 Max Brosmer`, omitting newly acquired **QB Kirk Cousins** (`NFL-S10`).
3. **Injury-List Omissions:** `commanders.com` lists `C1 Nick Allegretti -> C2 Matt Gulbin`, omitting `C Lucas Patrick` (`OUT — Concussion` on `nfl.com/injuries/`); `giants.com` omits rotational `LB Malik Harrison` (`Questionable — Groin` on `nfl.com/injuries/`).

Therefore, `Gate NFL-G10` requires reconciling: **(1)** `nfl.com/injuries/` practice & game statuses, **(2)** club `1st–4th` string depth charts, **(3)** Saturday 4:00 p.m. ET Practice Squad elevations & trade wire, and **(4)** T-90m official Inactive Lists + post-game NFL Gamebook snap shares. Until licensed play-by-play EPA priors and Week 10 Gamebooks are ingested, `empirical_epa_dropoff` and `verified_week10_snap_share` remain strictly blank (`""`) in `injury_and_depth_deficiency.csv`.
