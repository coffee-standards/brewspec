"""
Pydantic model tests for BrewLog CLI v1.0.

Tests cover acceptance criteria:
AC-9:  BrewInput.water_g (renamed from water_weight_g)
AC-10: BrewInput.process_notes (renamed from notes)
AC-11: BrewInput.yield_g added
AC-12: ResultInput.water_g added
AC-13: CoffeeInput.cupping_notes added
AC-14: OriginInput.cupping_notes added
AC-15: EquipmentInput.pressure_bar added
AC-16: EquipmentInput.flow_rate_ml_s added
AC-17: CoffeeInput.name maxLength tightened from 150 to 100
AC-18: BrewInput docstring references BrewSpec v1.0

TDD: tests written before implementation.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from brewlog.models import (
    BrewInput,
    CoffeeInput,
    OriginInput,
    EquipmentInput,
    ResultInput,
)


# ---------------------------------------------------------------------------
# AC-9: BrewInput.water_g (renamed from water_weight_g)
# ---------------------------------------------------------------------------

class TestBrewInputWaterG:
    """AC-9: water_g field replaces water_weight_g."""

    def test_water_g_accepted(self):
        """water_g field accepted."""
        brew = BrewInput(date="2026-03-30", type="pour_over", dose_g=18.0, water_g=280.0)
        assert brew.water_g == 280.0

    def test_water_g_zero_rejected(self):
        """water_g=0 raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(date="2026-03-30", type="pour_over", dose_g=18.0, water_g=0.0)

    def test_water_g_negative_rejected(self):
        """water_g < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(date="2026-03-30", type="pour_over", dose_g=18.0, water_g=-1.0)

    def test_water_weight_g_not_a_field(self):
        """water_weight_g is no longer a valid field (should not be silently accepted)."""
        # In Pydantic v2, extra fields are ignored by default.
        # We verify water_g is None when only water_weight_g is passed.
        brew = BrewInput(date="2026-03-30", type="pour_over", dose_g=18.0, water_weight_g=280.0)
        assert brew.water_g is None  # water_weight_g is not mapped to water_g


# ---------------------------------------------------------------------------
# AC-10: BrewInput.process_notes (renamed from notes)
# ---------------------------------------------------------------------------

class TestBrewInputProcessNotes:
    """AC-10: process_notes field replaces notes."""

    def test_process_notes_accepted(self):
        """process_notes field accepted."""
        brew = BrewInput(process_notes="Pre-infused 5s at 3 bar")
        assert brew.process_notes == "Pre-infused 5s at 3 bar"

    def test_process_notes_empty_rejected(self):
        """Empty process_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(process_notes="")

    def test_process_notes_whitespace_rejected(self):
        """Whitespace-only process_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(process_notes="   ")

    def test_process_notes_max_length_accepted(self):
        """process_notes of exactly 2000 characters is accepted."""
        brew = BrewInput(process_notes="a" * 2000)
        assert len(brew.process_notes) == 2000

    def test_process_notes_too_long_rejected(self):
        """process_notes exceeding 2000 characters is rejected."""
        with pytest.raises(ValidationError):
            BrewInput(process_notes="a" * 2001)

    def test_notes_field_no_longer_exists(self):
        """notes field is no longer present on BrewInput."""
        brew = BrewInput(notes="old field value")
        assert not hasattr(brew, "notes") or brew.notes is None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# AC-11: BrewInput.yield_g added (brew-level recipe target)
# ---------------------------------------------------------------------------

class TestBrewInputYieldG:
    """AC-11: yield_g field added to BrewInput."""

    def test_yield_g_accepted(self):
        """yield_g positive value accepted."""
        brew = BrewInput(yield_g=36.0)
        assert brew.yield_g == 36.0

    def test_yield_g_none_by_default(self):
        """yield_g defaults to None."""
        brew = BrewInput()
        assert brew.yield_g is None

    def test_yield_g_zero_rejected(self):
        """yield_g=0 raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(yield_g=0.0)

    def test_yield_g_negative_rejected(self):
        """yield_g negative raises ValidationError."""
        with pytest.raises(ValidationError):
            BrewInput(yield_g=-5.0)


# ---------------------------------------------------------------------------
# AC-12: ResultInput.water_g added
# ---------------------------------------------------------------------------

class TestResultInputWaterG:
    """AC-12: water_g field added to ResultInput."""

    def test_result_water_g_accepted(self):
        """water_g positive value accepted."""
        result = ResultInput(water_g=35.5)
        assert result.water_g == 35.5

    def test_result_water_g_none_by_default(self):
        """water_g defaults to None."""
        result = ResultInput()
        assert result.water_g is None

    def test_result_water_g_zero_rejected(self):
        """water_g=0 raises ValidationError."""
        with pytest.raises(ValidationError):
            ResultInput(water_g=0.0)

    def test_result_water_g_negative_rejected(self):
        """water_g negative raises ValidationError."""
        with pytest.raises(ValidationError):
            ResultInput(water_g=-1.0)


# ---------------------------------------------------------------------------
# AC-13: CoffeeInput.cupping_notes added
# ---------------------------------------------------------------------------

class TestCoffeeInputCuppingNotes:
    """AC-13: cupping_notes field added to CoffeeInput."""

    def test_cupping_notes_accepted(self):
        """cupping_notes string accepted."""
        coffee = CoffeeInput(cupping_notes="Dark chocolate, citrus")
        assert coffee.cupping_notes == "Dark chocolate, citrus"

    def test_cupping_notes_none_by_default(self):
        """cupping_notes defaults to None."""
        coffee = CoffeeInput()
        assert coffee.cupping_notes is None

    def test_cupping_notes_empty_rejected(self):
        """Empty cupping_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            CoffeeInput(cupping_notes="")

    def test_cupping_notes_whitespace_rejected(self):
        """Whitespace-only cupping_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            CoffeeInput(cupping_notes="   ")

    def test_cupping_notes_max_length_accepted(self):
        """cupping_notes of exactly 2000 characters is accepted."""
        coffee = CoffeeInput(cupping_notes="a" * 2000)
        assert len(coffee.cupping_notes) == 2000

    def test_cupping_notes_too_long_rejected(self):
        """cupping_notes exceeding 2000 characters is rejected."""
        with pytest.raises(ValidationError):
            CoffeeInput(cupping_notes="a" * 2001)


# ---------------------------------------------------------------------------
# AC-14: OriginInput.cupping_notes added
# ---------------------------------------------------------------------------

class TestOriginInputCuppingNotes:
    """AC-14: cupping_notes field added to OriginInput."""

    def test_cupping_notes_accepted(self):
        """cupping_notes string accepted."""
        origin = OriginInput(cupping_notes="Bright malic acidity")
        assert origin.cupping_notes == "Bright malic acidity"

    def test_cupping_notes_none_by_default(self):
        """cupping_notes defaults to None."""
        origin = OriginInput()
        assert origin.cupping_notes is None

    def test_cupping_notes_empty_rejected(self):
        """Empty cupping_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            OriginInput(cupping_notes="")

    def test_cupping_notes_whitespace_rejected(self):
        """Whitespace-only cupping_notes raises ValidationError."""
        with pytest.raises(ValidationError):
            OriginInput(cupping_notes="   ")

    def test_cupping_notes_max_length_accepted(self):
        """cupping_notes of exactly 2000 characters is accepted."""
        origin = OriginInput(cupping_notes="a" * 2000)
        assert len(origin.cupping_notes) == 2000

    def test_cupping_notes_too_long_rejected(self):
        """cupping_notes exceeding 2000 characters is rejected."""
        with pytest.raises(ValidationError):
            OriginInput(cupping_notes="a" * 2001)


# ---------------------------------------------------------------------------
# AC-15: EquipmentInput.pressure_bar added
# ---------------------------------------------------------------------------

class TestEquipmentInputPressureBar:
    """AC-15: pressure_bar field added to EquipmentInput."""

    def test_pressure_bar_accepted(self):
        """pressure_bar positive value accepted."""
        eq = EquipmentInput(pressure_bar=9.0)
        assert eq.pressure_bar == 9.0

    def test_pressure_bar_none_by_default(self):
        """pressure_bar defaults to None."""
        eq = EquipmentInput()
        assert eq.pressure_bar is None

    def test_pressure_bar_zero_rejected(self):
        """pressure_bar=0 raises ValidationError."""
        with pytest.raises(ValidationError):
            EquipmentInput(pressure_bar=0.0)

    def test_pressure_bar_negative_rejected(self):
        """pressure_bar negative raises ValidationError."""
        with pytest.raises(ValidationError):
            EquipmentInput(pressure_bar=-1.0)


# ---------------------------------------------------------------------------
# AC-16: EquipmentInput.flow_rate_ml_s added
# ---------------------------------------------------------------------------

class TestEquipmentInputFlowRateMlS:
    """AC-16: flow_rate_ml_s field added to EquipmentInput."""

    def test_flow_rate_accepted(self):
        """flow_rate_ml_s positive value accepted."""
        eq = EquipmentInput(flow_rate_ml_s=1.3)
        assert eq.flow_rate_ml_s == 1.3

    def test_flow_rate_none_by_default(self):
        """flow_rate_ml_s defaults to None."""
        eq = EquipmentInput()
        assert eq.flow_rate_ml_s is None

    def test_flow_rate_zero_rejected(self):
        """flow_rate_ml_s=0 raises ValidationError."""
        with pytest.raises(ValidationError):
            EquipmentInput(flow_rate_ml_s=0.0)

    def test_flow_rate_negative_rejected(self):
        """flow_rate_ml_s negative raises ValidationError."""
        with pytest.raises(ValidationError):
            EquipmentInput(flow_rate_ml_s=-0.5)


# ---------------------------------------------------------------------------
# AC-17: CoffeeInput.name maxLength tightened from 150 to 100
# ---------------------------------------------------------------------------

class TestCoffeeInputNameMaxLength:
    """AC-17: coffee name maxLength tightened to 100."""

    def test_name_100_chars_accepted(self):
        """Name of exactly 100 characters is accepted."""
        coffee = CoffeeInput(name="a" * 100)
        assert len(coffee.name) == 100

    def test_name_101_chars_rejected(self):
        """Name of 101 characters is rejected (maxLength=100)."""
        with pytest.raises(ValidationError):
            CoffeeInput(name="a" * 101)

    def test_name_150_chars_rejected(self):
        """Name of 150 characters (old limit) is now rejected."""
        with pytest.raises(ValidationError):
            CoffeeInput(name="a" * 150)


# ---------------------------------------------------------------------------
# AC-18: BrewInput docstring references BrewSpec v1.0
# ---------------------------------------------------------------------------

class TestBrewInputDocstring:
    """AC-18: BrewInput docstring references BrewSpec v1.0."""

    def test_brew_input_docstring_references_v10(self):
        """BrewInput docstring must mention v1.0."""
        assert "1.0" in BrewInput.__doc__
