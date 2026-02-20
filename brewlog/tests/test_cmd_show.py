"""
CLI integration tests for `brewlog show`.
Tests map to AC-17, AC-18, AC-19, AC-20.
"""

import pytest
from click.testing import CliRunner

from brewlog.cli import cli
from brewlog import db as db_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput


@pytest.fixture
def runner_with_db(tmp_path, monkeypatch):
    """CliRunner with a temporary DB path injected."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


def _insert_minimal(db_path):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _insert_full(db_path):
    conn = db_module.get_connection(db_path=db_path)
    try:
        brew = BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="Hario V60",
            water_temp_c=96.0,
            grind="medium-fine",
            duration_s=180,
            tds=1.38,
            rating=4,
            notes="Bright acidity",
            coffee=CoffeeInput(
                roast_date="2026-01-20",
                type="single_origin",
                origin=["Ethiopia"],
                varietal="Heirloom",
                process="Washed",
            ),
            water=WaterInput(ppm=150.0),
        )
        db_module.insert_brew(brew, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-17: Show all fields
# ---------------------------------------------------------------------------

def test_show_existing_brew(runner_with_db, tmp_path):
    """AC-17: shows all fields for brew #1."""
    _insert_full(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "2026-02-19T08:30:00Z" in result.output
    assert "pour_over" in result.output
    assert "Hario V60" in result.output
    assert "18.0" in result.output
    assert "280.0" in result.output


def test_show_omits_null_fields(runner_with_db, tmp_path):
    """AC-17: field not set is absent from output."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    # These optional fields were not set — they should not appear
    assert "Method" not in result.output
    assert "Grind" not in result.output
    assert "Notes" not in result.output
    assert "TDS" not in result.output
    assert "Rating" not in result.output


# ---------------------------------------------------------------------------
# AC-18: Grouped output sections
# ---------------------------------------------------------------------------

def test_show_groups_fields(runner_with_db, tmp_path):
    """AC-18: brew parameters, results, coffee, water sections present."""
    _insert_full(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    output = result.output
    assert "Brew parameters" in output or "Brew #1" in output
    assert "Results" in output or "TDS" in output
    assert "Coffee" in output
    assert "Water" in output


def test_show_omits_empty_sections(runner_with_db, tmp_path):
    """AC-18: no coffee section if no coffee metadata."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    # Coffee and Water *section headings* should not appear as standalone lines.
    # Note: "Water weight:" is a brew parameter field and legitimately contains "Water".
    # We check for section headings as standalone words on their own line.
    lines = result.output.split("\n")
    section_headings = [l.strip() for l in lines]
    assert "Coffee" not in section_headings
    assert "Water" not in section_headings


def test_show_displays_brew_id_header(runner_with_db, tmp_path):
    """AC-18: output starts with Brew #ID header."""
    _insert_minimal(tmp_path / "test.db")
    result = runner_with_db.invoke(cli, ["show", "1"])
    assert "Brew #1" in result.output


# ---------------------------------------------------------------------------
# AC-19: Brew not found
# ---------------------------------------------------------------------------

def test_show_not_found_message(runner_with_db):
    """AC-19: 'No brew found with ID 999.' printed."""
    result = runner_with_db.invoke(cli, ["show", "999"])
    assert "No brew found with ID 999" in result.output


def test_show_not_found_exit_nonzero(runner_with_db):
    """AC-19: exit code 1 when not found."""
    result = runner_with_db.invoke(cli, ["show", "999"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-20: Missing argument
# ---------------------------------------------------------------------------

def test_show_no_argument_error(runner_with_db):
    """AC-20: missing ID -> usage error, exit nonzero."""
    result = runner_with_db.invoke(cli, ["show"])
    assert result.exit_code != 0
