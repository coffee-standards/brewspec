"""
CLI integration tests for `brewlog add` — v1.0 new and renamed flags.

Tests cover acceptance criteria:
AC-19: --water internal name is water_g; prompt text "Water in grams"
AC-20: --process-notes replaces --notes
AC-21: --target-yield flag for brew.yield_g
AC-22: --actual-water flag for result.water_g
AC-23: --coffee-cupping-notes flag
AC-24: --origin-cupping-notes flag
AC-25: --pressure-bar flag
AC-26: --flow-rate flag
AC-27: validation errors for --target-yield, --actual-water, --pressure-bar, --flow-rate
AC-28: validation errors for empty --coffee-cupping-notes and --origin-cupping-notes
AC-61: each new flag writes correct value to DB
AC-65: validation error tests for zero and negative values
AC-66: coffee-name of 101 chars produces error

TDD: tests written before implementation.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    return CliRunner()


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner_with_path(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner(), db_path


def _add_minimal(runner, **extra_flags):
    """Invoke add with minimal required flags plus any extras."""
    flags = [
        "add",
        "--date", "2026-03-30",
        "--type", "espresso",
        "--dose", "18.0",
        "--water", "36.0",
    ]
    for k, v in extra_flags.items():
        flags.extend([k, v])
    return runner.invoke(cli, flags)


def _get_row(db_path, brew_id=1):
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.get_brew(brew_id, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-19: --water internal name is water_g
# ---------------------------------------------------------------------------

class TestAddWaterG:
    """AC-19: --water flag uses internal name water_g."""

    def test_water_flag_stores_water_g(self, runner_with_path):
        runner, db_path = runner_with_path
        result = _add_minimal(runner)
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["water_g"] == 36.0

    def test_water_flag_zero_rejected(self, runner):
        """--water 0 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "0",
        ])
        assert result.exit_code == 1

    def test_water_flag_negative_rejected(self, runner):
        """--water -1 is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "-1",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-20: --process-notes replaces --notes
# ---------------------------------------------------------------------------

class TestAddProcessNotes:
    """AC-20: --process-notes flag replaces --notes."""

    def test_process_notes_stored(self, runner_with_path):
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--process-notes": "Pre-infused 5s"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["process_notes"] == "Pre-infused 5s"

    def test_process_notes_empty_rejected(self, runner):
        """--process-notes with empty string is rejected."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--process-notes", "",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-21: --target-yield flag (brew.yield_g)
# ---------------------------------------------------------------------------

class TestAddTargetYield:
    """AC-21: --target-yield stores brew-level yield_g."""

    def test_add_target_yield(self, runner_with_path):
        """AC-61: --target-yield 36.0 writes to yield_g DB column."""
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--target-yield": "36.0"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["yield_g"] == 36.0

    def test_target_yield_zero_rejected(self, runner):
        """AC-27, AC-65: --target-yield 0 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--target-yield", "0",
        ])
        assert result.exit_code == 1
        assert "target-yield" in result.output.lower() or "target-yield" in (result.output + "").lower()

    def test_target_yield_negative_rejected(self, runner):
        """AC-27, AC-65: --target-yield -1 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--target-yield", "-1",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-22: --actual-water flag (result.water_g)
# ---------------------------------------------------------------------------

class TestAddActualWater:
    """AC-22: --actual-water stores result_water_g."""

    def test_add_actual_water(self, runner_with_path):
        """AC-61: --actual-water 35.5 writes to result_water_g DB column."""
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--actual-water": "35.5"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["result_water_g"] == 35.5

    def test_actual_water_zero_rejected(self, runner):
        """AC-27, AC-65: --actual-water 0 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-water", "0",
        ])
        assert result.exit_code == 1

    def test_actual_water_negative_rejected(self, runner):
        """AC-27, AC-65: --actual-water -5 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--actual-water", "-5",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-23: --coffee-cupping-notes flag
# ---------------------------------------------------------------------------

class TestAddCoffeeCuppingNotes:
    """AC-23: --coffee-cupping-notes stores coffee_cupping_notes."""

    def test_add_coffee_cupping_notes(self, runner_with_path):
        """AC-61: --coffee-cupping-notes writes to coffee_cupping_notes DB column."""
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--coffee-cupping-notes": "chocolate"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["coffee_cupping_notes"] == "chocolate"

    def test_coffee_cupping_notes_empty_rejected(self, runner):
        """AC-28: empty --coffee-cupping-notes -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--coffee-cupping-notes", "",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-24: --origin-cupping-notes flag
# ---------------------------------------------------------------------------

class TestAddOriginCuppingNotes:
    """AC-24: --origin-cupping-notes stores cupping_notes in coffee_origins JSON."""

    def test_add_origin_cupping_notes_with_origin_country(self, runner_with_path):
        """AC-61: --origin-cupping-notes with --origin-country -> first origin has cupping_notes."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--origin-country", "Colombia",
            "--origin-cupping-notes", "citrus",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        origins = json.loads(row["coffee_origins"])
        assert origins[0]["cupping_notes"] == "citrus"
        assert origins[0]["country"] == "Colombia"

    def test_add_origin_cupping_notes_only(self, runner_with_path):
        """--origin-cupping-notes alone creates a single origin with cupping_notes."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--origin-cupping-notes", "floral",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        origins = json.loads(row["coffee_origins"])
        assert origins[0]["cupping_notes"] == "floral"

    def test_origin_cupping_notes_empty_rejected(self, runner):
        """AC-28: empty --origin-cupping-notes -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--origin-cupping-notes", "",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-25: --pressure-bar flag
# ---------------------------------------------------------------------------

class TestAddPressureBar:
    """AC-25: --pressure-bar stores equipment_pressure_bar."""

    def test_add_pressure_bar(self, runner_with_path):
        """AC-61: --pressure-bar 9.0 writes to equipment_pressure_bar DB column."""
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--pressure-bar": "9.0"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["equipment_pressure_bar"] == 9.0

    def test_pressure_bar_zero_rejected(self, runner):
        """AC-27, AC-65: --pressure-bar 0 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--pressure-bar", "0",
        ])
        assert result.exit_code == 1

    def test_pressure_bar_negative_rejected(self, runner):
        """AC-27, AC-65: --pressure-bar -1 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--pressure-bar", "-1",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-26: --flow-rate flag
# ---------------------------------------------------------------------------

class TestAddFlowRate:
    """AC-26: --flow-rate stores equipment_flow_rate_ml_s."""

    def test_add_flow_rate(self, runner_with_path):
        """AC-61: --flow-rate 1.3 writes to equipment_flow_rate_ml_s DB column."""
        runner, db_path = runner_with_path
        result = _add_minimal(runner, **{"--flow-rate": "1.3"})
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["equipment_flow_rate_ml_s"] == 1.3

    def test_flow_rate_zero_rejected(self, runner):
        """AC-27, AC-65: --flow-rate 0 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--flow-rate", "0",
        ])
        assert result.exit_code == 1

    def test_flow_rate_negative_rejected(self, runner):
        """AC-27, AC-65: --flow-rate -1 -> exit code 1."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--flow-rate", "-1",
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-66: coffee-name of 101 chars produces error
# ---------------------------------------------------------------------------

class TestAddCoffeeNameMaxLength:
    """AC-66: --coffee-name of 101 characters produces error."""

    def test_coffee_name_101_chars_rejected(self, runner):
        """101-character coffee name is rejected at add."""
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--coffee-name", "a" * 101,
        ])
        assert result.exit_code == 1

    def test_coffee_name_100_chars_accepted(self, runner_with_path):
        """100-character coffee name is accepted."""
        runner, db_path = runner_with_path
        result = runner.invoke(cli, [
            "add", "--date", "2026-03-30", "--type", "espresso",
            "--dose", "18.0", "--water", "36.0",
            "--coffee-name", "a" * 100,
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["coffee_name"] == "a" * 100
