"""
CLI integration tests for `brewlog update` — v1.0 new and renamed flags.

Tests cover acceptance criteria:
AC-29: --process-notes replaces --notes on update
AC-30: --target-yield, --actual-water, --coffee-cupping-notes, --origin-cupping-notes,
       --pressure-bar, --flow-rate flags on update
AC-31: validation for all new flags mirrors add command
AC-32: water_g removed from UPDATABLE_COLUMNS (not updatable)
AC-62: each new update flag writes correct value to DB

TDD: tests written before implementation.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew(db_path):
    """Insert a minimal brew and return its ID."""
    conn = db_module.get_connection(db_path=db_path)
    try:
        from brewlog.models import BrewInput
        brew = BrewInput(date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0)
        return db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _get_row(db_path, brew_id=1):
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.get_brew(brew_id, conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AC-29: --process-notes replaces --notes on update
# ---------------------------------------------------------------------------

class TestUpdateProcessNotes:
    """AC-29: --process-notes flag replaces --notes on update."""

    def test_update_process_notes(self, runner, db_path):
        """AC-62: --process-notes updates process_notes column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--process-notes", "Updated notes"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["process_notes"] == "Updated notes"

    def test_update_process_notes_empty_rejected(self, runner, db_path):
        """AC-31: empty --process-notes -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--process-notes", ""])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --target-yield flag on update
# ---------------------------------------------------------------------------

class TestUpdateTargetYield:
    """AC-30: --target-yield updates yield_g column."""

    def test_update_target_yield(self, runner, db_path):
        """AC-62: --target-yield 36.0 updates yield_g column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--target-yield", "36.0"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["yield_g"] == 36.0

    def test_update_target_yield_zero_rejected(self, runner, db_path):
        """AC-31: --target-yield 0 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--target-yield", "0"])
        assert result.exit_code == 1

    def test_update_target_yield_negative_rejected(self, runner, db_path):
        """AC-31: --target-yield -1 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--target-yield", "-1"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --actual-water flag on update
# ---------------------------------------------------------------------------

class TestUpdateActualWater:
    """AC-30: --actual-water updates result_water_g column."""

    def test_update_actual_water(self, runner, db_path):
        """AC-62: --actual-water 35.5 updates result_water_g column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--actual-water", "35.5"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["result_water_g"] == 35.5

    def test_update_actual_water_zero_rejected(self, runner, db_path):
        """AC-31: --actual-water 0 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--actual-water", "0"])
        assert result.exit_code == 1

    def test_update_actual_water_negative_rejected(self, runner, db_path):
        """AC-31: --actual-water -5 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--actual-water", "-5"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --coffee-cupping-notes flag on update
# ---------------------------------------------------------------------------

class TestUpdateCoffeeCuppingNotes:
    """AC-30: --coffee-cupping-notes updates coffee_cupping_notes column."""

    def test_update_coffee_cupping_notes(self, runner, db_path):
        """AC-62: --coffee-cupping-notes updates coffee_cupping_notes column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--coffee-cupping-notes", "Bright citrus"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["coffee_cupping_notes"] == "Bright citrus"

    def test_update_coffee_cupping_notes_empty_rejected(self, runner, db_path):
        """AC-31: empty --coffee-cupping-notes -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--coffee-cupping-notes", ""])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --origin-cupping-notes on update
# ---------------------------------------------------------------------------

class TestUpdateOriginCuppingNotes:
    """AC-30: --origin-cupping-notes updates coffee_origins JSON."""

    def test_update_origin_cupping_notes_with_structured_origins(self, runner, db_path):
        """AC-62: --origin-cupping-notes with structured origin flags patches first origin."""
        _add_brew(db_path)
        result = runner.invoke(cli, [
            "update", "1",
            "--origin-country", "Colombia",
            "--origin-cupping-notes", "floral jasmine",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        origins = json.loads(row["coffee_origins"])
        assert origins[0]["cupping_notes"] == "floral jasmine"
        assert origins[0]["country"] == "Colombia"

    def test_update_origin_cupping_notes_without_structured_origins(self, runner, db_path):
        """AC-62: --origin-cupping-notes alone reads existing origins and patches first entry."""
        # First add a brew with an origin
        conn = db_module.get_connection(db_path=db_path)
        try:
            from brewlog.models import BrewInput, CoffeeInput, OriginInput
            brew = BrewInput(
                date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
                coffee=CoffeeInput(origins=[OriginInput(country="Ethiopia")]),
            )
            db_module.insert_brew(brew, conn)
        finally:
            conn.close()

        result = runner.invoke(cli, [
            "update", "1", "--origin-cupping-notes", "berry notes",
        ])
        assert result.exit_code == 0
        row = _get_row(db_path)
        origins = json.loads(row["coffee_origins"])
        assert origins[0]["cupping_notes"] == "berry notes"
        assert origins[0]["country"] == "Ethiopia"

    def test_update_origin_cupping_notes_empty_rejected(self, runner, db_path):
        """AC-31: empty --origin-cupping-notes -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--origin-cupping-notes", ""])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --pressure-bar flag on update
# ---------------------------------------------------------------------------

class TestUpdatePressureBar:
    """AC-30: --pressure-bar updates equipment_pressure_bar column."""

    def test_update_pressure_bar(self, runner, db_path):
        """AC-62: --pressure-bar 9.0 updates equipment_pressure_bar column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--pressure-bar", "9.0"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["equipment_pressure_bar"] == 9.0

    def test_update_pressure_bar_zero_rejected(self, runner, db_path):
        """AC-31: --pressure-bar 0 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--pressure-bar", "0"])
        assert result.exit_code == 1

    def test_update_pressure_bar_negative_rejected(self, runner, db_path):
        """AC-31: --pressure-bar -1 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--pressure-bar", "-1"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# AC-30: --flow-rate flag on update
# ---------------------------------------------------------------------------

class TestUpdateFlowRate:
    """AC-30: --flow-rate updates equipment_flow_rate_ml_s column."""

    def test_update_flow_rate(self, runner, db_path):
        """AC-62: --flow-rate 1.3 updates equipment_flow_rate_ml_s column."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--flow-rate", "1.3"])
        assert result.exit_code == 0
        row = _get_row(db_path)
        assert row["equipment_flow_rate_ml_s"] == 1.3

    def test_update_flow_rate_zero_rejected(self, runner, db_path):
        """AC-31: --flow-rate 0 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--flow-rate", "0"])
        assert result.exit_code == 1

    def test_update_flow_rate_negative_rejected(self, runner, db_path):
        """AC-31: --flow-rate -1 -> exit code 1."""
        _add_brew(db_path)
        result = runner.invoke(cli, ["update", "1", "--flow-rate", "-1"])
        assert result.exit_code == 1
