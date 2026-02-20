"""
Unit tests for Pydantic models in brewlog.models.
Tests map to input validation requirements for BrewSpec v0.3.
"""

import pytest
from pydantic import ValidationError

from brewlog.models import BrewInput, CoffeeInput, EquipmentInput, WaterInput


# ---------------------------------------------------------------------------
# BrewInput — valid cases
# ---------------------------------------------------------------------------

def test_brew_input_valid_minimal():
    """AC-9: Required-only fields accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.date == "2026-02-19T08:30:00Z"
    assert brew.type == "pour_over"
    assert brew.dose_g == 18.0
    assert brew.water_weight_g == 280.0
    assert brew.method is None
    assert brew.coffee is None
    assert brew.water is None


def test_brew_input_valid_all_fields():
    """AC-8, AC-9: All optional fields accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="immersion",
        dose_g=20.0,
        water_weight_g=300.0,
        method="French Press",
        water_volume_ml=300.0,
        water_temp_c=95.0,
        grind="coarse",
        duration_s=240,
        tds=1.5,
        rating=3,
        notes="Smooth and balanced",
        coffee=CoffeeInput(
            roast_date="2026-01-15",
            type="blend",
            origin=["Ethiopia", "Colombia"],
            varietal="Bourbon",
            process="Natural",
        ),
        water=WaterInput(ppm=120.0),
    )
    assert brew.method == "French Press"
    assert brew.water_volume_ml == 300.0
    assert brew.water_temp_c == 95.0
    assert brew.grind == "coarse"
    assert brew.duration_s == 240
    assert brew.tds == 1.5
    assert brew.rating == 3
    assert brew.notes == "Smooth and balanced"
    assert brew.coffee is not None
    assert brew.coffee.origin == ["Ethiopia", "Colombia"]
    assert brew.water is not None
    assert brew.water.ppm == 120.0


# ---------------------------------------------------------------------------
# BrewInput — date validation
# ---------------------------------------------------------------------------

def test_brew_input_invalid_date_format():
    """AC-9: Non-ISO-8601 date rejected."""
    with pytest.raises(ValidationError, match="date"):
        BrewInput(
            date="2026-02-19",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_invalid_date_missing_z():
    """AC-9: Date without trailing Z rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_invalid_date_impossible():
    """AC-9: Impossible datetime (month 13) rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-13-01T00:00:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


# ---------------------------------------------------------------------------
# BrewInput — type enum validation
# ---------------------------------------------------------------------------

def test_brew_input_invalid_type_enum():
    """AC-9: Unknown type string rejected."""
    with pytest.raises(ValidationError, match="type"):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="drip",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_valid_all_types():
    """AC-9: All valid brew types accepted."""
    for brew_type in ("immersion", "pour_over", "espresso", "hybrid"):
        brew = BrewInput(
            date="2026-02-19T08:30:00Z",
            type=brew_type,
            dose_g=18.0,
            water_weight_g=280.0,
        )
        assert brew.type == brew_type


# ---------------------------------------------------------------------------
# BrewInput — dose_g validation
# ---------------------------------------------------------------------------

def test_brew_input_dose_zero():
    """AC-9: dose_g=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=0,
            water_weight_g=280.0,
        )


def test_brew_input_dose_negative():
    """AC-9: dose_g=-1 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=-1,
            water_weight_g=280.0,
        )


# ---------------------------------------------------------------------------
# BrewInput — water_weight_g validation
# ---------------------------------------------------------------------------

def test_brew_input_water_weight_zero():
    """AC-9: water_weight_g=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=0,
        )


# ---------------------------------------------------------------------------
# BrewInput — water_temp_c validation
# ---------------------------------------------------------------------------

def test_brew_input_temp_boundary_low():
    """AC-9: water_temp_c=0 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        water_temp_c=0,
    )
    assert brew.water_temp_c == 0


def test_brew_input_temp_boundary_high():
    """AC-9: water_temp_c=100 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        water_temp_c=100,
    )
    assert brew.water_temp_c == 100


def test_brew_input_temp_out_of_range():
    """AC-9: water_temp_c=101 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            water_temp_c=101,
        )


def test_brew_input_temp_below_zero():
    """AC-9: water_temp_c=-1 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            water_temp_c=-1,
        )


# ---------------------------------------------------------------------------
# BrewInput — duration_s validation
# ---------------------------------------------------------------------------

def test_brew_input_duration_zero():
    """AC-9: duration_s=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            duration_s=0,
        )


def test_brew_input_duration_negative():
    """AC-9: duration_s=-1 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            duration_s=-1,
        )


# ---------------------------------------------------------------------------
# BrewInput — rating validation
# ---------------------------------------------------------------------------

def test_brew_input_rating_low_boundary():
    """AC-9: rating=1 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        rating=1,
    )
    assert brew.rating == 1


def test_brew_input_rating_high_boundary():
    """AC-9: rating=5 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        rating=5,
    )
    assert brew.rating == 5


def test_brew_input_rating_below_min():
    """AC-9: rating=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            rating=0,
        )


def test_brew_input_rating_above_max():
    """AC-9: rating=6 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            rating=6,
        )


# ---------------------------------------------------------------------------
# BrewInput — tds validation
# ---------------------------------------------------------------------------

def test_brew_input_tds_zero():
    """AC-9: tds=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            tds=0,
        )


# ---------------------------------------------------------------------------
# BrewInput — freeform text field validation
# ---------------------------------------------------------------------------

def test_brew_input_method_empty_string():
    """AC-9: method="" rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="",
        )


def test_brew_input_grind_empty_string():
    """AC-9: grind="" rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="",
        )


def test_brew_input_notes_empty_string():
    """AC-9: notes="" rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            notes="",
        )


def test_brew_input_method_whitespace_only():
    """AC-9: method with only whitespace rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="   ",
        )


# ---------------------------------------------------------------------------
# WaterInput — ppm validation
# ---------------------------------------------------------------------------

def test_brew_input_water_ppm_zero():
    """AC-9: ppm=0 accepted (>= 0 is valid)."""
    water = WaterInput(ppm=0)
    assert water.ppm == 0


def test_brew_input_water_ppm_negative():
    """AC-9: ppm=-1 rejected."""
    with pytest.raises(ValidationError):
        WaterInput(ppm=-1)


# ---------------------------------------------------------------------------
# CoffeeInput — roast_date validation
# ---------------------------------------------------------------------------

def test_coffee_input_roast_date_valid():
    """AC-9: roast_date='2026-01-20' accepted."""
    coffee = CoffeeInput(roast_date="2026-01-20")
    assert coffee.roast_date == "2026-01-20"


def test_coffee_input_roast_date_invalid_format():
    """AC-9: roast_date='01-20-2026' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_date="01-20-2026")


def test_coffee_input_roast_date_invalid_no_dashes():
    """AC-9: roast_date='20260120' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_date="20260120")


# ---------------------------------------------------------------------------
# CoffeeInput — type enum validation
# ---------------------------------------------------------------------------

def test_coffee_input_type_valid_single_origin():
    """AC-9: type='single_origin' accepted."""
    coffee = CoffeeInput(type="single_origin")
    assert coffee.type == "single_origin"


def test_coffee_input_type_valid_blend():
    """AC-9: type='blend' accepted."""
    coffee = CoffeeInput(type="blend")
    assert coffee.type == "blend"


def test_coffee_input_type_invalid():
    """AC-9: type='unknown' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(type="unknown")


# ---------------------------------------------------------------------------
# CoffeeInput — origin validation
# ---------------------------------------------------------------------------

def test_coffee_input_origin_empty_list():
    """AC-9: origin=[] rejected (minItems 1)."""
    with pytest.raises(ValidationError):
        CoffeeInput(origin=[])


def test_coffee_input_origin_empty_item():
    """AC-9: origin=[''] rejected (each item must be non-empty string)."""
    with pytest.raises(ValidationError):
        CoffeeInput(origin=[""])


def test_coffee_input_origin_multiple():
    """AC-8: origin=['Ethiopia', 'Colombia'] accepted."""
    coffee = CoffeeInput(origin=["Ethiopia", "Colombia"])
    assert coffee.origin == ["Ethiopia", "Colombia"]


def test_coffee_input_origin_single():
    """AC-9: origin=['Ethiopia'] accepted."""
    coffee = CoffeeInput(origin=["Ethiopia"])
    assert coffee.origin == ["Ethiopia"]


# ---------------------------------------------------------------------------
# CoffeeInput — freeform text fields
# ---------------------------------------------------------------------------

def test_coffee_input_varietal_empty_rejected():
    """AC-9: varietal='' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(varietal="")


def test_coffee_input_process_empty_rejected():
    """AC-9: process='' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(process="")


def test_coffee_input_all_none_valid():
    """CoffeeInput with all None fields is valid."""
    coffee = CoffeeInput()
    assert coffee.roast_date is None
    assert coffee.type is None
    assert coffee.origin is None


# ---------------------------------------------------------------------------
# CoffeeInput — maxLength validators (v0.3)
# ---------------------------------------------------------------------------

def test_coffee_input_varietal_maxlength_accepted():
    """varietal of exactly 100 chars is accepted."""
    coffee = CoffeeInput(varietal="x" * 100)
    assert len(coffee.varietal) == 100


def test_coffee_input_varietal_maxlength_exceeded():
    """varietal of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(varietal="x" * 101)


def test_coffee_input_process_maxlength_accepted():
    """process of exactly 100 chars is accepted."""
    coffee = CoffeeInput(process="x" * 100)
    assert len(coffee.process) == 100


def test_coffee_input_process_maxlength_exceeded():
    """process of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(process="x" * 101)


def test_coffee_input_origin_item_maxlength_accepted():
    """origin item of exactly 100 chars is accepted."""
    coffee = CoffeeInput(origin=["x" * 100])
    assert len(coffee.origin[0]) == 100


def test_coffee_input_origin_item_maxlength_exceeded():
    """origin item of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(origin=["x" * 101])


# ---------------------------------------------------------------------------
# EquipmentInput — basic validation (v0.3)
# ---------------------------------------------------------------------------

def test_equipment_input_both_fields():
    """EquipmentInput with grinder and brewer is valid."""
    equipment = EquipmentInput(grinder="Comandante C40 MK4", brewer="Hario V60 02")
    assert equipment.grinder == "Comandante C40 MK4"
    assert equipment.brewer == "Hario V60 02"


def test_equipment_input_grinder_only():
    """EquipmentInput with only grinder is valid."""
    equipment = EquipmentInput(grinder="Niche Zero")
    assert equipment.grinder == "Niche Zero"
    assert equipment.brewer is None


def test_equipment_input_brewer_only():
    """EquipmentInput with only brewer is valid."""
    equipment = EquipmentInput(brewer="French Press")
    assert equipment.brewer == "French Press"
    assert equipment.grinder is None


def test_equipment_input_empty():
    """EquipmentInput with no fields is valid (all optional)."""
    equipment = EquipmentInput()
    assert equipment.grinder is None
    assert equipment.brewer is None


def test_equipment_input_grinder_empty_string():
    """grinder='' is rejected."""
    with pytest.raises(ValidationError):
        EquipmentInput(grinder="")


def test_equipment_input_brewer_empty_string():
    """brewer='' is rejected."""
    with pytest.raises(ValidationError):
        EquipmentInput(brewer="")


def test_equipment_input_grinder_whitespace_only():
    """grinder with only whitespace is rejected."""
    with pytest.raises(ValidationError):
        EquipmentInput(grinder="   ")


def test_equipment_input_grinder_maxlength_accepted():
    """grinder of exactly 100 chars is accepted."""
    equipment = EquipmentInput(grinder="x" * 100)
    assert len(equipment.grinder) == 100


def test_equipment_input_grinder_maxlength_exceeded():
    """grinder of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        EquipmentInput(grinder="x" * 101)


def test_equipment_input_brewer_maxlength_accepted():
    """brewer of exactly 100 chars is accepted."""
    equipment = EquipmentInput(brewer="x" * 100)
    assert len(equipment.brewer) == 100


def test_equipment_input_brewer_maxlength_exceeded():
    """brewer of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        EquipmentInput(brewer="x" * 101)


# ---------------------------------------------------------------------------
# BrewInput — ey field (v0.3)
# ---------------------------------------------------------------------------

def test_brew_input_ey_valid():
    """ey=20.1 is accepted (exclusiveMinimum: 0)."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        ey=20.1,
    )
    assert brew.ey == 20.1


def test_brew_input_ey_zero_rejected():
    """ey=0 is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            ey=0,
        )


def test_brew_input_ey_negative_rejected():
    """ey=-1 is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            ey=-1,
        )


def test_brew_input_ey_omitted():
    """ey omitted is valid (optional field)."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.ey is None


# ---------------------------------------------------------------------------
# BrewInput — equipment field (v0.3)
# ---------------------------------------------------------------------------

def test_brew_input_with_equipment():
    """BrewInput with equipment object is valid."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        equipment=EquipmentInput(grinder="Comandante C40", brewer="Hario V60"),
    )
    assert brew.equipment is not None
    assert brew.equipment.grinder == "Comandante C40"
    assert brew.equipment.brewer == "Hario V60"


def test_brew_input_equipment_omitted():
    """BrewInput with equipment omitted is valid."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.equipment is None


# ---------------------------------------------------------------------------
# BrewInput — method and grind maxLength (v0.3)
# ---------------------------------------------------------------------------

def test_brew_input_method_maxlength_accepted():
    """method of exactly 100 chars is accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        method="x" * 100,
    )
    assert len(brew.method) == 100


def test_brew_input_method_maxlength_exceeded():
    """method of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="x" * 101,
        )


def test_brew_input_grind_maxlength_accepted():
    """grind of exactly 100 chars is accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        grind="x" * 100,
    )
    assert len(brew.grind) == 100


def test_brew_input_grind_maxlength_exceeded():
    """grind of 101 chars is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="x" * 101,
        )


# ---------------------------------------------------------------------------
# BrewInput — notes maxLength (v0.3)
# ---------------------------------------------------------------------------

def test_brew_input_notes_maxlength_accepted():
    """notes of exactly 2000 chars is accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        notes="x" * 2000,
    )
    assert len(brew.notes) == 2000


def test_brew_input_notes_maxlength_exceeded():
    """notes of 2001 chars is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            notes="x" * 2001,
        )
