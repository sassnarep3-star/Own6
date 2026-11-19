"""Tests for the a119bb6d official-Game-Book pack.

The fixture is a bounded extract of one official NFL Game Book, read from the
league's own game centre on 2026-11-19. It is kept so that the parser can be
tested without a network, and so that a change in the parser shows up as a
failing test rather than as a silently empty table.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_a119bb6d.gamebook import parse_game_book  # noqa: E402
from src.nfl_a119bb6d.htmltext import html_to_lines  # noqa: E402
from src.nfl_a119bb6d.registers import (  # noqa: E402
    build_availability_graph,
    build_designation_calibration,
    club_of,
    wilson_interval,
)

FIXTURE = os.path.join(
    ROOT, "tests", "fixtures", "49ers-at-cowboys-2026-reg-10.layout.txt"
)


@pytest.fixture(scope="module")
def parsed():
    with open(FIXTURE, encoding="utf-8") as fh:
        return parse_game_book(fh.read())


def test_header_is_read(parsed):
    assert parsed["date_et"] == "Sunday, 11/15/2026"
    assert parsed["away_team"] == "San Francisco 49ers"
    assert parsed["home_team"] == "Dallas Cowboys"
    assert parsed["start_time"] == "3:25 PM CST"
    assert parsed["problems"] == []


def test_venue_and_roof_are_read(parsed):
    assert parsed["stadium"] == "AT&T Stadium"
    assert parsed["city"] == "Arlington, TX"
    assert parsed["roof_status"] == "Retractable Roof - Closed"
    assert parsed["surface"] == "Field Turf"


def test_game_day_weather_is_read(parsed):
    assert parsed["weather_sky"] == "Rainy"
    assert parsed["temp_f"] == "49"
    assert parsed["humidity_pct"] == "86"
    assert parsed["wind"] == "NE 3 mph"
    assert parsed["wind_chill"] == "49"


def test_score_and_attendance_are_read(parsed):
    assert parsed["away_score"] == "46"
    assert parsed["home_score"] == "40"
    assert parsed["attendance"] == "90763"


def test_officials_are_read(parsed):
    roles = {o["role"] for o in parsed["officials"]}
    assert "Referee" in roles and "Replay Official" in roles
    referee = [o for o in parsed["officials"] if o["role"] == "Referee"][0]
    assert referee["name"] == "Hussey, John"
    assert referee["number"] == "35"


def test_forty_four_starters_are_read(parsed):
    assert len(parsed["lineups"]) == 44
    away = [r for r in parsed["lineups"] if r["side"] == "away"]
    home = [r for r in parsed["lineups"] if r["side"] == "home"]
    assert len(away) == 22 and len(home) == 22
    for side in (away, home):
        assert len([r for r in side if r["unit"] == "offense"]) == 11
        assert len([r for r in side if r["unit"] == "defense"]) == 11


def test_starters_are_in_the_right_columns(parsed):
    def players(side, unit, position):
        return {
            r["player"]
            for r in parsed["lineups"]
            if r["side"] == side and r["unit"] == unit and r["position"] == position
        }

    assert players("away", "offense", "QB") == {"B.Purdy"}
    assert players("home", "offense", "QB") == {"D.Prescott"}
    assert "N.Bosa" in players("away", "defense", "DL")
    assert "V.Miller" in players("home", "defense", "OLB")
    assert players("away", "offense", "WR") == {"D.Samuel", "J.Watkins"}
    assert players("home", "offense", "WR") == {"C.Lamb", "R.Flournoy", "G.Pickens"}


def test_inactive_list_is_read_per_club(parsed):
    away = sorted(r["player"] for r in parsed["not_active"] if r["side"] == "away")
    home = sorted(r["player"] for r in parsed["not_active"] if r["side"] == "home")
    assert away == ["B.Cooks", "E.Cruz", "K.Rourke", "M.Evans", "T.Bethune"]
    assert home == [
        "A.Cornelius", "D.Ezeiruaku", "D.Kendrick", "J.Ferguson",
        "J.Mingo", "J.Thomas", "P.Locke",
    ]


def test_substitutes_are_read_per_club(parsed):
    away = [r["player"] for r in parsed["substitutions"] if r["side"] == "away"]
    home = [r["player"] for r in parsed["substitutions"] if r["side"] == "home"]
    assert "C.Waitman" in away   # the 49ers punter
    assert "B.Anger" in home     # the Cowboys punter
    assert "E.Pineiro" in away   # the 49ers kicker
    assert "B.Aubrey" in home    # the Cowboys kicker


def test_did_not_play_is_read_per_club(parsed):
    assert [(r["side"], r["player"]) for r in parsed["did_not_play"]] == [
        ("away", "M.Jones"),
        ("home", "S.Howell"),
    ]


def test_club_of():
    assert club_of("San Francisco 49ers") == "SF"
    assert club_of("Dallas Cowboys") == "DAL"
    assert club_of("Nowhere FC") == ""


def test_wilson_interval():
    low, high = wilson_interval(10, 10)
    assert low < 1.0 and high <= 1.0 and high > 0.99
    low, high = wilson_interval(0, 10)
    assert low == 0.0 and 0.0 < high < 0.5
    assert wilson_interval(0, 0) == (0.0, 0.0)


def _fake_games():
    return [
        {
            "game_slug": "b-at-a-2026-reg-1",
            "game_url": "https://www.nfl.com/games/b-at-a-2026-reg-1",
            "gamebook_url": "https://static.www.nfl.com/x.pdf",
            "away_team": "San Francisco 49ers",
            "home_team": "Dallas Cowboys",
            "read_at_utc": "2026-11-19T00:00:00Z",
        }
    ]


def test_availability_graph_counts_a_replacement():
    games = _fake_games()
    lineups = [
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "unit": "offense",
         "position": "QB", "jersey": "1", "player": "A.Qb"},
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "unit": "offense",
         "position": "WR", "jersey": "2", "player": "A.Wr"},
    ]
    rows, problems = build_availability_graph(games, lineups, [])
    assert not problems
    assert len(rows) == 2
    assert all(r["change_type"] == "no_prior_game_book" for r in rows)
    assert all(r["expected_starters"] == "" for r in rows)


def test_availability_graph_depth_lower_bound():
    games = [
        {
            "game_slug": "b-at-a-2026-reg-1", "game_url": "u1",
            "gamebook_url": "u1", "away_team": "San Francisco 49ers", "home_team": "Dallas Cowboys",
            "read_at_utc": "",
        },
        {
            "game_slug": "b-at-a-2026-reg-2", "game_url": "u2",
            "gamebook_url": "u2", "away_team": "San Francisco 49ers", "home_team": "Dallas Cowboys",
            "read_at_utc": "",
        },
    ]
    lineups = [
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "unit": "offense",
         "position": "QB", "jersey": "1", "player": "A.Qb"},
        {"game_slug": "b-at-a-2026-reg-2", "side": "away", "unit": "offense",
         "position": "QB", "jersey": "1", "player": "A.Qb2"},
    ]
    participation = [
        {"game_slug": "b-at-a-2026-reg-2", "side": "away", "role": "not_active",
         "position": "QB", "jersey": "1", "player": "A.Qb"},
    ]
    rows, _ = build_availability_graph(games, lineups, participation)
    qb = [r for r in rows if r["position"] == "QB" and r["week"] == 2][0]
    assert qb["change_type"] == "replaced"
    assert qb["expected_starters"] == "A.Qb"
    assert qb["actual_starters"] == "A.Qb2"
    assert qb["starters_out"] == "A.Qb"
    assert qb["starters_in"] == "A.Qb2"
    assert qb["unavailable_ahead"] == 1
    assert qb["replacement_string_lower_bound"] == 2


def test_designation_calibration_joins_to_game_book():
    games = [
        {
            "game_slug": "b-at-a-2026-reg-1", "game_url": "u1",
            "gamebook_url": "u1", "away_team": "San Francisco 49ers", "home_team": "Dallas Cowboys",
            "read_at_utc": "",
        }
    ]
    lineups = [
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "unit": "offense",
         "position": "QB", "jersey": "1", "player": "A.Qb"},
    ]
    participation = [
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "role": "substitute",
         "position": "WR", "jersey": "2", "player": "A.Wr"},
        {"game_slug": "b-at-a-2026-reg-1", "side": "away", "role": "not_active",
         "position": "WR", "jersey": "3", "player": "A.Wr2"},
    ]
    injuries = [
        {"week": "1", "club": "SF", "player": "A.Qb", "position": "QB",
         "injury": "", "practice_status": "", "game_status": "Questionable",
         "source_url": "https://www.nfl.com/injuries/"},
        {"week": "1", "club": "SF", "player": "A.Wr", "position": "WR",
         "injury": "", "practice_status": "", "game_status": "Questionable",
         "source_url": "https://www.nfl.com/injuries/"},
        {"week": "1", "club": "SF", "player": "A.Wr2", "position": "WR",
         "injury": "", "practice_status": "", "game_status": "Out",
         "source_url": "https://www.nfl.com/injuries/"},
    ]
    rows, _ = build_designation_calibration(injuries, games, lineups, participation)
    by_name = {r["designation"]: r for r in rows}
    assert by_name["Questionable"]["n"] == 2
    assert by_name["Questionable"]["n_started"] == 1
    assert by_name["Questionable"]["n_played_off_bench"] == 1
    assert by_name["Out"]["n_inactive"] == 1
    assert float(by_name["Out"]["play_rate"]) == 0.0


def test_html_to_lines_keeps_links_and_blocks():
    html = (
        "<div><h3>COWBOYS</h3><ul><li>CB X.Y</li><li>WR A.B</li></ul>"
        '<p>WHEN: <a href="https://www.nfl.com/games/a-at-b-2026-reg-1">1:00</a></p></div>'
    )
    lines = html_to_lines(html)
    assert "COWBOYS" in lines
    assert "CB X.Y" in lines
    assert any("https://www.nfl.com/games/a-at-b-2026-reg-1" in line for line in lines)


# ---- the availability-page parsers ---------------------------------------

INJURY_FIXTURE = os.path.join(
    ROOT, "tests", "fixtures", "injuries-report-2026-reg10.layout.html"
)


def test_injury_report_is_parsed_by_column():
    from src.nfl_a119bb6d.pages import parse_injury_report

    with open(INJURY_FIXTURE, encoding="utf-8") as fh:
        html = fh.read()
    parsed = parse_injury_report(
        html, url="https://www.nfl.com/injuries/league/2026/reg10",
        read_at_utc="2026-11-19T00:00:00Z",
    )
    assert parsed["problems"] == []
    assert parsed["week_line"] == "Injuries - WEEK 10"
    assert len(parsed["rows"]) == 5
    by_player = {r["player"]: r for r in parsed["rows"]}
    assert by_player["John Bates"]["club"] == "WAS"
    assert by_player["John Bates"]["position"] == "TE"
    assert by_player["John Bates"]["injury"] == ""
    assert by_player["John Bates"]["game_status"] == ""
    assert by_player["Lucas Patrick"]["injury"] == "Concussion"
    assert by_player["Lucas Patrick"]["game_status"] == "Out"
    assert by_player["Malik Harrison"]["game_status"] == "Questionable"
    assert by_player["Colson Yankoff"]["club"] == "NYG"


def test_injury_report_keeps_an_empty_injury_column_in_place():
    """An empty injury cell must not shift the status columns."""
    from src.nfl_a119bb6d.pages import parse_injury_report

    with open(INJURY_FIXTURE, encoding="utf-8") as fh:
        html = fh.read()
    parsed = parse_injury_report(
        html, url="https://www.nfl.com/injuries/league/2026/reg10",
        read_at_utc="",
    )
    for row in parsed["rows"]:
        assert row["practice_status"] in (
            "Full Participation in Practice",
            "Limited Participation in Practice",
            "Did Not Participate In Practice",
        )
        assert row["game_status"] in ("", "Out", "Doubtful", "Questionable")


def test_inactives_article_is_parsed():
    from src.nfl_a119bb6d.pages import parse_inactives_article

    html = (
        "<h2>NFL Inactives for Week 10</h2>"
        '<p>WHEN: Sunday, November 15th at 1:00 PM ET</p>'
        '<p>WHERE: Allegiant Stadium, Las Vegas, NV</p>'
        '<a href="https://www.nfl.com/games/raiders-at-49ers-2026-reg-10">1:00 PM ET</a>'
        "<h3>49ERS</h3><ul><li>S Kyle Diggs</li><li>LB Fred Warner Jr.</li></ul>"
        "<h3>RAIDERS</h3><ul><li>C Jakobi Meyers</li></ul>"
    )
    parsed = parse_inactives_article(
        html, url="https://www.nfl.com/news/nfl-week-10-inactives", read_at_utc=""
    )
    assert parsed["problems"] == []
    assert len(parsed["games"]) == 1
    assert parsed["games"][0]["slug"] == "raiders-at-49ers-2026-reg-10"
    clubs = {r["club"] for r in parsed["rows"]}
    assert clubs == {"SF", "LV"}
    assert len(parsed["rows"]) == 3


def test_split_table_row_keeps_empty_cells():
    from src.nfl_a119bb6d.htmltext import split_table_row

    assert split_table_row("| a | b | | d |") == ["a", "b", "", "d"]
    assert split_table_row("not a row") == []
