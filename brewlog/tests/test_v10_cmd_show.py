"""
CLI integration tests for `brewlog show` — v1.0 renamed and new fields.

Tests cover acceptance criteria:
AC-33: process_notes (not notes) displayed when present
AC-34: brew-level yield_g displayed as "Target yield (g)"
AC-35: result_water_g displayed as "Actual water (g)"
AC-36: coffee.cupping_notes displayed in coffee section
AC-37: origin.cupping_notes displayed per-origin
AC-38: equipment.pressure_bar and flow_rate_ml_s displayed in equipment section

TDD: tests written before implementation.
"""

from __future__ import annotations


import pytest
from click.testing import CliRunner

from brewlog import db as db_module
from brewlog.cli import cli
from brewlog.models import (
    BrewInput, CoffeeInput, OriginInput, EquipmentInput, ResultInput
)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def runner(db_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return CliRunner()


def _add_brew_and_get_id(db_path, brew: BrewInput) -> int:
    conn = db_module.get_connection(db_path=db_path)
    try:
        return db_module.insert_brew(brew, conn)
    finally:
        conn.close()


def _show(runner, brew_id: int):
    return runner.invoke(cli, ["show", str(brew_id)])


# ---------------------------------------------------------------------------
# AC-33: process_notes displayed
# ---------------------------------------------------------------------------

class TestShowProcessNotes:
    """AC-33: process_notes displayed when present."""

    def test_show_displays_process_notes(self, runner, db_path):
        """process_notes value shown in output."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            process_notes="Pre-infused 5s at 3 bar",
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Pre-infused 5s at 3 bar" in result.output

    def test_show_process_notes_label(self, runner, db_path):
        """Process Notes label appears when process_notes set."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            process_notes="Rinsed filter",
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Process Notes:" in result.output

    def test_show_no_notes_key_used(self, runner, db_path):
        """Old 'Notes:' label must not appear (only 'Process Notes:')."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            process_notes="Some notes",
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        # "Process Notes:" is fine; standalone "Notes:" should not appear
        lines = result.output.split("\n")
        for line in lines:
            stripped = line.strip()
            # Must not have a line that is exactly "Notes: ..." (old label)
            assert not stripped.startswith("Notes:"), f"Old 'Notes:' label found: {stripped!r}"


# ---------------------------------------------------------------------------
# AC-34: brew-level yield_g displayed as "Target yield (g)"
# ---------------------------------------------------------------------------

class TestShowTargetYieldG:
    """AC-34: brew-level yield_g shown as 'Target yield (g)'."""

    def test_show_target_yield(self, runner, db_path):
        """'Target yield (g):' label and value appear in output."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            yield_g=36.0,
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Target yield (g):" in result.output
        assert "36.0" in result.output

    def test_show_target_yield_absent_when_null(self, runner, db_path):
        """'Target yield (g):' absent when yield_g is NULL."""
        brew = BrewInput(date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0)
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Target yield (g):" not in result.output


# ---------------------------------------------------------------------------
# AC-35: result_water_g displayed as "Actual water (g)"
# ---------------------------------------------------------------------------

class TestShowResultWaterG:
    """AC-35: result_water_g shown as 'Actual water (g)'."""

    def test_show_actual_water(self, runner, db_path):
        """'Actual water (g):' label and value appear in output."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            result=ResultInput(water_g=35.5),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Actual water (g):" in result.output
        assert "35.5" in result.output

    def test_show_actual_water_absent_when_null(self, runner, db_path):
        """'Actual water (g):' absent when result_water_g is NULL."""
        brew = BrewInput(date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0)
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Actual water (g):" not in result.output


# ---------------------------------------------------------------------------
# AC-36: coffee.cupping_notes displayed
# ---------------------------------------------------------------------------

class TestShowCoffeeCuppingNotes:
    """AC-36: coffee.cupping_notes shown in coffee section."""

    def test_show_coffee_cupping_notes(self, runner, db_path):
        """Coffee cupping notes shown when present."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            coffee=CoffeeInput(
                name="Colombia Huila",
                cupping_notes="Dark chocolate, citrus",
            ),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Dark chocolate, citrus" in result.output

    def test_show_coffee_cupping_notes_absent_when_null(self, runner, db_path):
        """Coffee cupping notes absent when not set."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            coffee=CoffeeInput(name="Colombia"),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        # Should not have a cupping notes line for the coffee section
        # (origins section may not exist either)
        assert "Cupping Notes:" not in result.output


# ---------------------------------------------------------------------------
# AC-37: origin.cupping_notes displayed per-origin
# ---------------------------------------------------------------------------

class TestShowOriginCuppingNotes:
    """AC-37: origin.cupping_notes shown per-origin."""

    def test_show_origin_cupping_notes(self, runner, db_path):
        """Origin cupping notes shown in origin section."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            coffee=CoffeeInput(
                origins=[OriginInput(country="Colombia", cupping_notes="Bright malic acidity")],
            ),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Bright malic acidity" in result.output

    def test_show_origin_cupping_notes_absent_when_null(self, runner, db_path):
        """Origin cupping notes absent when not set."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            coffee=CoffeeInput(origins=[OriginInput(country="Colombia")]),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        # Colombia is shown but "Cupping Notes:" should not appear
        assert "Colombia" in result.output
        assert "Cupping Notes:" not in result.output


# ---------------------------------------------------------------------------
# AC-38: equipment.pressure_bar and flow_rate_ml_s displayed
# ---------------------------------------------------------------------------

class TestShowEquipmentFields:
    """AC-38: equipment.pressure_bar and flow_rate_ml_s shown in equipment section."""

    def test_show_pressure_bar(self, runner, db_path):
        """'Pressure (bar):' shown when equipment_pressure_bar set."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            equipment=EquipmentInput(grinder="Niche Zero", pressure_bar=9.0),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Pressure (bar):" in result.output
        assert "9.0" in result.output

    def test_show_flow_rate(self, runner, db_path):
        """'Flow Rate (ml/s):' shown when equipment_flow_rate_ml_s set."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            equipment=EquipmentInput(grinder="Niche Zero", flow_rate_ml_s=1.3),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Flow Rate (ml/s):" in result.output
        assert "1.3" in result.output

    def test_show_pressure_bar_absent_when_null(self, runner, db_path):
        """'Pressure (bar):' absent when equipment_pressure_bar is NULL."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            equipment=EquipmentInput(grinder="Niche Zero"),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Pressure (bar):" not in result.output

    def test_show_flow_rate_absent_when_null(self, runner, db_path):
        """'Flow Rate (ml/s):' absent when equipment_flow_rate_ml_s is NULL."""
        brew = BrewInput(
            date="2026-03-30", type="espresso", dose_g=18.0, water_g=36.0,
            equipment=EquipmentInput(grinder="Niche Zero"),
        )
        _add_brew_and_get_id(db_path, brew)
        result = _show(runner, 1)
        assert result.exit_code == 0
        assert "Flow Rate (ml/s):" not in result.output
