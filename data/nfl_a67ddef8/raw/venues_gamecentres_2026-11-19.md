# RAW TRANSCRIPTION — 13 Week-11 NFL Game Centre venue fields + DEN@PIT Week-12 sample
# Source: nfl.com game centre pages (one fetch per game, chunk 0), 2026-11-19.
# Fields as rendered in the "Location" / "Stadium" labels.

1. /games/colts-at-texans-2026-reg-11 — Location: HOUSTON, TX — Stadium: RELIANT STADIUM
   (Thursday, November 19th; away IND 3-7, home HOU 3-6; IND injury report 11 rows / HOU 15 rows listed)
2. /games/dolphins-at-bills-2026-reg-11 — Location: ORCHARD PARK, NY — Stadium: HIGHMARK STADIUM
   (Sunday, November 22nd; away MIA 1-8, home BUF 8-1)
3. /games/ravens-at-panthers-2026-reg-11 — Location: CHARLOTTE, NC — Stadium: BANK OF AMERICA STADIUM
   (Sunday, November 22nd; away BAL 4-6, home CAR 4-5)
4. /games/saints-at-bears-2026-reg-11 — Location: CHICAGO, IL — Stadium: SOLDIER FIELD
   (Sunday, November 22nd; away NO 3-6, home CHI 7-2)
5. /games/titans-at-cowboys-2026-reg-11 — Location: ARLINGTON, TX — Stadium: AT&T STADIUM
   (Sunday, November 22nd; away TEN 1-8, home DAL 4-6)
6. /games/buccaneers-at-lions-2026-reg-11 — Location: DETROIT, MI — Stadium: FORD FIELD
   (Sunday, November 22nd; away TB 3-6, home DET 7-2)
7. /games/cardinals-at-chiefs-2026-reg-11 — Location: KANSAS CITY, MO — Stadium: ARROWHEAD STADIUM
   (Sunday, November 22nd; away AZ 3-7, home KC 7-2)
8. /games/steelers-at-eagles-2026-reg-11 — Location: PHILADELPHIA, PA — Stadium: LINCOLN FINANCIAL FIELD
   (Sunday, November 22nd; away PIT 6-3, home PHI 2-7)
9. /games/jets-at-chargers-2026-reg-11 — Location: INGLEWOOD, CA — Stadium: SOFI STADIUM
   (Sunday, November 22nd; away NYJ 2-8, home LAC 1-8)
10. /games/jaguars-at-giants-2026-reg-11 — Location: EAST RUTHERFORD, NJ — Stadium: METLIFE STADIUM
    (Sunday, November 22nd; away JAX 7-2, home NYG 5-3-1)
11. /games/raiders-at-broncos-2026-reg-11 — Location: DENVER, CO — Stadium: EMPOWER FIELD AT MILE HIGH
    (Sunday, November 22nd; away LV 4-6, home DEN 7-2)
12. /games/vikings-at-49ers-2026-reg-11 — Location: MEXICO CITY — Stadium: ESTADIO BANORTE
    (Sunday, November 22nd; away MIN 7-2, home SF 8-1 — international fixture, badge "Mexico City" on schedule card)
13. /games/bengals-at-commanders-2026-reg-11 — Location: LANDOVER, MD — Stadium: NORTHWEST STADIUM
    (Monday, November 23rd; away CIN 7-2, home WAS 3-5-1; panels: "Bengals have no active injuries at this time",
     "Commanders have no active injuries at this time")

## Week-12 venue sample (one game centre)
14. /games/broncos-at-steelers-2026-reg-12 — Location: PITTSBURGH, PA — Stadium: ACRISURE STADIUM
    (Friday, November 27th; away DEN 7-2, home PIT 6-3; injury panels both read
     "Broncos' Injury Report is not available at this time" /
     "Steelers' Injury Report is not available at this time" — week-12 report not yet published)

## Cross-check vs prior pack 0d4da02c week11_schedule.csv venue strings (hotel-affiliate params)
IND@HOU: game centre RELIANT STADIUM  vs hotel "NRG Stadium"           → MISMATCH (stale hotel name; venue renamed NRG 2013)
CIN@WAS: game centre NORTHWEST STADIUM vs hotel "FedEx Field"           → MISMATCH (stale hotel name; venue renamed 2025)
MIN@SF:  game centre ESTADIO BANORTE (+ MEXICO CITY) vs hotel "Mexico City" → stadium name now first-class; city matches
AZ@KC:   game centre ARROWHEAD STADIUM vs hotel "GEHA Field at Arrowhead Stadium" → naming variance (sponsor prefix), same venue
DEN@PIT: game centre ACRISURE STADIUM vs week-12 schedule hotel "Heinz Field Stadium" → MISMATCH (stale hotel name; renamed 2022)
Other 9 Week-11 games: exact case-insensitive matches (HIGHMARK, BANK OF AMERICA, SOLDIER, AT&T, FORD, LINCOLN FINANCIAL, SOFI, METLIFE, EMPOWER FIELD AT MILE HIGH)
