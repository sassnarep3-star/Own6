"""Regression coverage for the static lab table renderer."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("build_lab", Path(__file__).resolve().parents[2] / "scripts/build_lab.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_table_renders_cells_not_generator_repr():
    result = module.table(["Name", "Source"], [[module.esc("A & B"), module.link("https://www.nba.com/", "NBA")]])
    assert '<td>A &amp; B</td>' in result
    assert '<td><a href="https://www.nba.com/"' in result
    assert "generator object" not in result
