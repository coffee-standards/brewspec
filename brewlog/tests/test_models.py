"""
Unit tests for Pydantic models in brewlog.models.
Tests map to input validation requirements for BrewSpec v0.4.
"""

import pytest
from pydantic import ValidationError

from brewlog.models import BrewInput, CoffeeInput, EquipmentInput, WaterInput


# ---------------------------------------------------------------------------
# BrewInput — valid cases
# ---------------------------------------------------------------------------

def test_brew_input_valid_minimal():
    """Required-only fields accepted."""
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
    """All optional fields accepted (v0.4: result replaces tds/ey/rating)."""
    from brewlog.models import ResultInput, RatingsInput

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
        notes="Smooth and balanced",
        coffee=CoffeeInput(
            roast_date="2026-01-15",
            type="blend",
            origin=["Ethiopia", "Colombia"],
            varietal="Bourbon",
            process="Natural",
        ),
        water=WaterInput(ppm=120.0),
        result=ResultInput(
            tds=1.5,
            ey=20.1,
            brix=1.2,
            tasting_notes="Smooth and balanced",
            ratings=RatingsInput(overall=3, acidity=4),
        ),
    )
    assert brew.method == "French Press"
    assert brew.water_volume_ml == 300.0
    assert brew.water_temp_c == 95.0
    assert brew.grind == "coarse"
    assert brew.duration_s == 240
    assert brew.notes == "Smooth and balanced"
    assert brew.coffee is not None
    assert brew.coffee.origin == ["Ethiopia", "Colombia"]
    assert brew.water is not None
    assert brew.water.ppm == 120.0
    assert brew.result is not None
    assert brew.result.tds == 1.5
    assert brew.result.ratings.overall == 3


# ---------------------------------------------------------------------------
# BrewInput — date validation (v0.4: dual-format)
# ---------------------------------------------------------------------------

def test_brew_input_date_only_accepted():
    """AC v0.4: date: YYYY-MM-DD (date-only) is accepted."""
    brew = BrewInput(
        date="2026-02-21",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.date == "2026-02-21"


def test_brew_input_date_full_datetime_accepted():
    """AC v0.4: date: YYYY-MM-DDTHH:MM:SSZ (full datetime) is still accepted."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.date == "2026-02-21T08:30:00Z"


def test_brew_input_invalid_date_format():
    """date: string matching neither accepted format is rejected."""
    with pytest.raises(ValidationError, match="date"):
        BrewInput(
            date="not-a-date",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_invalid_date_missing_z():
    """AC v0.4: Date without trailing Z (and with time component) rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_invalid_date_impossible():
    """AC v0.4: Impossible datetime (month 13) rejected for full datetime."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-13-01T00:00:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_invalid_date_wrong_order():
    """date in DD-MM-YYYY order is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="21-02-2026",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )


# ---------------------------------------------------------------------------
# BrewInput — type enum validation
# ---------------------------------------------------------------------------

def test_brew_input_invalid_type_enum():
    """Unknown type string rejected."""
    with pytest.raises(ValidationError, match="type"):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="drip",
            dose_g=18.0,
            water_weight_g=280.0,
        )


def test_brew_input_valid_all_types():
    """All valid brew types accepted."""
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
    """dose_g=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=0,
            water_weight_g=280.0,
        )


def test_brew_input_dose_negative():
    """dose_g=-1 rejected."""
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
    """water_weight_g=0 rejected."""
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
    """water_temp_c=0 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        water_temp_c=0,
    )
    assert brew.water_temp_c == 0


def test_brew_input_temp_boundary_high():
    """water_temp_c=100 accepted."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        water_temp_c=100,
    )
    assert brew.water_temp_c == 100


def test_brew_input_temp_out_of_range():
    """water_temp_c=101 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            water_temp_c=101,
        )


def test_brew_input_temp_below_zero():
    """water_temp_c=-1 rejected."""
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
    """duration_s=0 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            duration_s=0,
        )


def test_brew_input_duration_negative():
    """duration_s=-1 rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            duration_s=-1,
        )


# ---------------------------------------------------------------------------
# BrewInput — grind enum validation (v0.4)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"
])
def test_brew_input_grind_enum_all_values_accepted(grind_value):
    """AC v0.4: Each of the 7 grind enum values is accepted."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        grind=grind_value,
    )
    assert brew.grind == grind_value


def test_brew_input_grind_freeform_rejected():
    """AC v0.4: grind: freeform string not in the enum is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-21T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="setting 15",
        )


def test_brew_input_grind_wrong_case_rejected():
    """AC v0.4: grind: 'Medium' (wrong case) is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-21T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="Medium",
        )


def test_brew_input_grind_empty_string_rejected():
    """grind='' is rejected (not in enum)."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="",
        )


def test_brew_input_grind_omitted_accepted():
    """grind omitted is valid (optional field)."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.grind is None


# ---------------------------------------------------------------------------
# BrewInput — freeform text field validation
# ---------------------------------------------------------------------------

def test_brew_input_method_empty_string():
    """method="" rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="",
        )


def test_brew_input_notes_empty_string():
    """notes="" rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            notes="",
        )


def test_brew_input_method_whitespace_only():
    """method with only whitespace rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-19T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            method="   ",
        )


# ---------------------------------------------------------------------------
# BrewInput — result field (v0.4)
# ---------------------------------------------------------------------------

def test_brew_input_with_result_tds_ey():
    """BrewInput with result containing tds and ey is valid."""
    from brewlog.models import ResultInput

    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        result=ResultInput(tds=1.38, ey=20.1),
    )
    assert brew.result is not None
    assert brew.result.tds == 1.38
    assert brew.result.ey == 20.1


def test_brew_input_result_omitted():
    """BrewInput with result omitted is valid."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.result is None


def test_brew_input_with_full_result():
    """BrewInput with fully populated result is valid (including date-only format)."""
    from brewlog.models import ResultInput, RatingsInput

    brew = BrewInput(
        date="2026-02-21",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
        result=ResultInput(
            tds=1.38,
            ey=20.1,
            brix=1.5,
            tasting_notes="Bright citrus, caramel finish",
            ratings=RatingsInput(overall=4, acidity=5, mouthfeel=3),
        ),
    )
    assert brew.result.brix == 1.5
    assert brew.result.tasting_notes == "Bright citrus, caramel finish"
    assert brew.result.ratings.overall == 4


# ---------------------------------------------------------------------------
# WaterInput — ppm validation
# ---------------------------------------------------------------------------

def test_brew_input_water_ppm_zero():
    """ppm=0 accepted (>= 0 is valid)."""
    water = WaterInput(ppm=0)
    assert water.ppm == 0


def test_brew_input_water_ppm_negative():
    """ppm=-1 rejected."""
    with pytest.raises(ValidationError):
        WaterInput(ppm=-1)


# ---------------------------------------------------------------------------
# CoffeeInput — roast_date validation
# ---------------------------------------------------------------------------

def test_coffee_input_roast_date_valid():
    """roast_date='2026-01-20' accepted."""
    coffee = CoffeeInput(roast_date="2026-01-20")
    assert coffee.roast_date == "2026-01-20"


def test_coffee_input_roast_date_invalid_format():
    """roast_date='01-20-2026' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_date="01-20-2026")


def test_coffee_input_roast_date_invalid_no_dashes():
    """roast_date='20260120' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(roast_date="20260120")


# ---------------------------------------------------------------------------
# CoffeeInput — type enum validation
# ---------------------------------------------------------------------------

def test_coffee_input_type_valid_single_origin():
    """type='single_origin' accepted."""
    coffee = CoffeeInput(type="single_origin")
    assert coffee.type == "single_origin"


def test_coffee_input_type_valid_blend():
    """type='blend' accepted."""
    coffee = CoffeeInput(type="blend")
    assert coffee.type == "blend"


def test_coffee_input_type_invalid():
    """type='unknown' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(type="unknown")


# ---------------------------------------------------------------------------
# CoffeeInput — origin validation
# ---------------------------------------------------------------------------

def test_coffee_input_origin_empty_list():
    """origin=[] rejected (minItems 1)."""
    with pytest.raises(ValidationError):
        CoffeeInput(origin=[])


def test_coffee_input_origin_empty_item():
    """origin=[''] rejected (each item must be non-empty string)."""
    with pytest.raises(ValidationError):
        CoffeeInput(origin=[""])


def test_coffee_input_origin_multiple():
    """origin=['Ethiopia', 'Colombia'] accepted."""
    coffee = CoffeeInput(origin=["Ethiopia", "Colombia"])
    assert coffee.origin == ["Ethiopia", "Colombia"]


def test_coffee_input_origin_single():
    """origin=['Ethiopia'] accepted."""
    coffee = CoffeeInput(origin=["Ethiopia"])
    assert coffee.origin == ["Ethiopia"]


# ---------------------------------------------------------------------------
# CoffeeInput — freeform text fields
# ---------------------------------------------------------------------------

def test_coffee_input_varietal_empty_rejected():
    """varietal='' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(varietal="")


def test_coffee_input_process_empty_rejected():
    """process='' rejected."""
    with pytest.raises(ValidationError):
        CoffeeInput(process="")


def test_coffee_input_all_none_valid():
    """CoffeeInput with all None fields is valid."""
    coffee = CoffeeInput()
    assert coffee.roast_date is None
    assert coffee.type is None
    assert coffee.origin is None


# ---------------------------------------------------------------------------
# CoffeeInput — maxLength validators
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
# EquipmentInput — basic validation
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
# BrewInput — method maxLength
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


# ---------------------------------------------------------------------------
# BrewInput — notes maxLength
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


# ---------------------------------------------------------------------------
# BrewInput — with equipment field
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
# RatingsInput — v0.4
# ---------------------------------------------------------------------------

def test_ratings_input_partial():
    """RatingsInput with only some dimensions is valid."""
    from brewlog.models import RatingsInput

    ratings = RatingsInput(overall=4, acidity=3)
    assert ratings.overall == 4
    assert ratings.acidity == 3
    assert ratings.fragrance is None


def test_ratings_input_all_dimensions():
    """RatingsInput with all 8 dimensions is valid."""
    from brewlog.models import RatingsInput

    ratings = RatingsInput(
        overall=4, fragrance=3, aroma=4, flavour=5,
        aftertaste=4, acidity=5, sweetness=3, mouthfeel=4
    )
    assert ratings.mouthfeel == 4


def test_ratings_input_boundary_minimum():
    """Each dimension: 1 is accepted (minimum boundary)."""
    from brewlog.models import RatingsInput

    ratings = RatingsInput(overall=1)
    assert ratings.overall == 1


def test_ratings_input_boundary_maximum():
    """Each dimension: 5 is accepted (maximum boundary)."""
    from brewlog.models import RatingsInput

    ratings = RatingsInput(overall=5)
    assert ratings.overall == 5


def test_ratings_input_below_minimum_rejected():
    """rating dimension: 0 is rejected (minimum: 1)."""
    from brewlog.models import RatingsInput

    with pytest.raises(ValidationError):
        RatingsInput(overall=0)


def test_ratings_input_above_maximum_rejected():
    """rating dimension: 6 is rejected (maximum: 5)."""
    from brewlog.models import RatingsInput

    with pytest.raises(ValidationError):
        RatingsInput(overall=6)


def test_ratings_input_empty():
    """RatingsInput with no fields is valid (all optional)."""
    from brewlog.models import RatingsInput

    ratings = RatingsInput()
    assert ratings.overall is None
    assert ratings.fragrance is None


# ---------------------------------------------------------------------------
# ResultInput — v0.4
# ---------------------------------------------------------------------------

def test_result_input_brix_zero_accepted():
    """ResultInput.brix: 0 is accepted (minimum: 0, not exclusive)."""
    from brewlog.models import ResultInput

    result = ResultInput(brix=0)
    assert result.brix == 0


def test_result_input_brix_positive_accepted():
    """ResultInput.brix: 1.5 is accepted."""
    from brewlog.models import ResultInput

    result = ResultInput(brix=1.5)
    assert result.brix == 1.5


def test_result_input_brix_negative_rejected():
    """ResultInput.brix: -1 is rejected."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(brix=-1)


def test_result_input_tds_zero_rejected():
    """ResultInput.tds: 0 is rejected (exclusiveMinimum: 0)."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(tds=0)


def test_result_input_tds_positive_accepted():
    """ResultInput.tds: 1.38 is accepted."""
    from brewlog.models import ResultInput

    result = ResultInput(tds=1.38)
    assert result.tds == 1.38


def test_result_input_ey_negative_rejected():
    """ResultInput.ey: -1 is rejected."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(ey=-1)


def test_result_input_ey_zero_rejected():
    """ResultInput.ey: 0 is rejected (exclusiveMinimum: 0)."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(ey=0)


def test_result_input_tasting_notes_empty_rejected():
    """ResultInput.tasting_notes: empty string is rejected."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(tasting_notes="")


def test_result_input_tasting_notes_valid():
    """ResultInput.tasting_notes: non-empty string is accepted."""
    from brewlog.models import ResultInput

    result = ResultInput(tasting_notes="Bright citrus")
    assert result.tasting_notes == "Bright citrus"


def test_result_input_tasting_notes_maxlength_accepted():
    """ResultInput.tasting_notes: 2000 chars is accepted."""
    from brewlog.models import ResultInput

    result = ResultInput(tasting_notes="x" * 2000)
    assert len(result.tasting_notes) == 2000


def test_result_input_tasting_notes_maxlength_exceeded():
    """ResultInput.tasting_notes: 2001 chars is rejected."""
    from brewlog.models import ResultInput

    with pytest.raises(ValidationError):
        ResultInput(tasting_notes="x" * 2001)


def test_result_input_empty():
    """ResultInput with no fields is valid (all optional)."""
    from brewlog.models import ResultInput

    result = ResultInput()
    assert result.tds is None
    assert result.ey is None
    assert result.brix is None
    assert result.tasting_notes is None
    assert result.ratings is None
