"""
Test suite for BrewSpec v0.4

This test suite validates the BrewSpec JSON Schema against example files.
Tests are organized by acceptance criteria from specs/products/brewspec-v0.4.md
"""

import json
import yaml
import pytest
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.validators import validator_for

# Paths
REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "brewspec.schema.json"
VALID_DIR = REPO_ROOT / "examples" / "valid"
INVALID_DIR = REPO_ROOT / "examples" / "invalid"

# Minimal valid v0.4 brew dict used across tests
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.4", "brews": [VALID_BREW]}


@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def validator(schema):
    """Create a Draft 2020-12 validator for the BrewSpec schema."""
    return Draft202012Validator(schema)


# ---------------------------------------------------------------------------
# Meta-validation: schema is itself valid Draft 2020-12
# ---------------------------------------------------------------------------

def test_schema_is_valid_draft_2020_12(schema):
    """Verify the schema itself is valid JSON Schema Draft 2020-12."""
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


# ---------------------------------------------------------------------------
# AC-1: Version const must be "0.4"
# ---------------------------------------------------------------------------

def test_version_must_be_0_4(validator):
    """AC-1: brewspec_version is required and must be exactly '0.4'."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({"brews": [VALID_BREW]})

    # Wrong version
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "1.0", "brews": [VALID_BREW]})

    # Correct version
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_3(validator):
    """AC-1/AC-9 (from AC list): brewspec_version '0.3' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_2(validator):
    """brewspec_version '0.2' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_1(validator):
    """brewspec_version '0.1' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.1",
            "brews": [VALID_BREW]
        })


# ---------------------------------------------------------------------------
# brews array: required, non-empty
# ---------------------------------------------------------------------------

def test_brews_must_be_nonempty_array(validator):
    """brews is required and must be an array with minimum 1 element."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.4"})

    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.4", "brews": []})

    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Required brew fields
# ---------------------------------------------------------------------------

def test_required_brew_fields(validator):
    """Each brew must have date, type, dose_g, water_weight_g."""
    base = {"brewspec_version": "0.4"}

    for missing in ("date", "type", "dose_g", "water_weight_g"):
        fields = dict(VALID_BREW)
        del fields[missing]
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [fields]})

    # All required fields present
    validator.validate({**base, "brews": [dict(VALID_BREW)]})


def test_dose_g_required_at_brew_level(validator):
    """dose_g is required at the brew level."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "water_weight_g": 320}]
        })


def test_water_weight_g_required_at_brew_level(validator):
    """water_weight_g is required at the brew level."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "dose_g": 20}]
        })


# ---------------------------------------------------------------------------
# AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8: Date format — dual-format
# ---------------------------------------------------------------------------

def test_date_only_format_accepted(validator):
    """AC-3: date: YYYY-MM-DD (date-only) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-21"}]
    })


def test_date_full_datetime_accepted(validator):
    """AC-4: date: YYYY-MM-DDTHH:MM:SSZ (full datetime) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00Z"}]
    })


def test_date_no_z_rejected(validator):
    """AC-5: date: datetime without Z suffix fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00"}]
        })


def test_date_wrong_order_rejected(validator):
    """AC-6: date: DD-MM-YYYY order fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "date": "21-02-2026"}]
        })


def test_date_month_13_passes_schema(validator):
    """AC-7: date: month 13 passes schema validation. Calendar validation is application-layer."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-13-01"}]
    })


def test_date_format_invalid_other(validator):
    """Plainly invalid date strings are rejected."""
    base = {"brewspec_version": "0.4", "brews": [{"type": "pour_over", "dose_g": 20, "water_weight_g": 320}]}

    invalid_dates = [
        "2026-02-15T08:30:00+00:00",
        "15-02-2026T08:30:00Z",
        "not-a-date",
    ]
    for d in invalid_dates:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "date": d}]})


# ---------------------------------------------------------------------------
# AC-9, AC-10, AC-11, AC-12, AC-13, AC-14: grind field — strict enum
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"
])
def test_grind_enum_all_values_accepted(validator, grind_value):
    """AC-10/AC-11: Each of the 7 grind enum values passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "grind": grind_value}]
    })


def test_grind_freeform_rejected(validator):
    """AC-12: grind: freeform string not in the enum fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "setting 15"}]
        })


def test_grind_wrong_case_rejected(validator):
    """AC-13: grind: 'Medium' (wrong case) fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "Medium"}]
        })


def test_grind_omitted_accepted(validator):
    """AC-14: grind omitted entirely passes validation (field remains optional)."""
    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Optional objects: coffee and water
# ---------------------------------------------------------------------------

def test_coffee_object_optional(validator):
    """A brew with no coffee object passes validation."""
    validator.validate(VALID_DOC)


def test_water_object_optional(validator):
    """A brew with no water object passes validation."""
    validator.validate(VALID_DOC)


def test_optional_fields_accepted(validator):
    """All optional brew fields are accepted when valid."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "method": "Hario V60",
            "dose_g": 20,
            "water_weight_g": 320,
            "water_volume_ml": 320,
            "water_temp_c": 96,
            "coffee": {
                "roast_date": "2026-01-20",
                "type": "single_origin",
                "origin": ["Ethiopia"],
                "varietal": "Heirloom",
                "process": "Washed"
            },
            "water": {"ppm": 150},
            "equipment": {
                "grinder": "Comandante C40 MK4",
                "brewer": "Hario V60 02"
            },
            "grind": "medium_fine",
            "duration_s": 180,
            "notes": "Bright acidity, slightly under-extracted",
            "result": {
                "tds": 1.38,
                "ey": 20.5,
                "brix": 1.5,
                "tasting_notes": "Citrus and caramel",
                "ratings": {
                    "overall": 4,
                    "acidity": 5
                }
            }
        }]
    })


def test_minimal_brew_passes(validator):
    """Brew with only required fields passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "immersion", "dose_g": 30, "water_weight_g": 500}]
    })


# ---------------------------------------------------------------------------
# Numeric constraints
# ---------------------------------------------------------------------------

def test_negative_values_rejected(validator):
    """Negative values for dose_g, water_weight_g, water_volume_ml, duration_s are rejected."""
    base = {"brewspec_version": "0.4", "brews": [dict(VALID_BREW)]}

    for field, value in [("dose_g", -10), ("water_weight_g", -320),
                         ("water_volume_ml", -100), ("duration_s", -30)]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: value}]})


def test_zero_weight_rejected(validator):
    """Zero values for dose_g and water_weight_g are rejected (exclusiveMinimum: 0)."""
    base = {"brewspec_version": "0.4", "brews": [dict(VALID_BREW)]}

    for field in ("dose_g", "water_weight_g"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: 0}]})


def test_zero_duration_rejected(validator):
    """duration_s: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                       "dose_g": 18, "water_weight_g": 36, "duration_s": 0}]
        })


def test_positive_duration_accepted(validator):
    """duration_s: 1 is accepted (exclusiveMinimum: 0)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                   "dose_g": 18, "water_weight_g": 36, "duration_s": 1}]
    })


def test_temperature_range(validator):
    """water_temp_c must be between 0 and 100."""
    base = {"brewspec_version": "0.4", "brews": [dict(VALID_BREW)]}

    with pytest.raises(ValidationError):
        validator.validate({**base, "brews": [{**base["brews"][0], "water_temp_c": -1}]})
    with pytest.raises(ValidationError):
        validator.validate({**base, "brews": [{**base["brews"][0], "water_temp_c": 101}]})

    for temp in [0, 50, 100]:
        validator.validate({**base, "brews": [{**base["brews"][0], "water_temp_c": temp}]})


# ---------------------------------------------------------------------------
# Type enumeration
# ---------------------------------------------------------------------------

def test_type_enum_validation(validator):
    """type must be one of: immersion, pour_over, espresso, hybrid."""
    base = {"brewspec_version": "0.4", "brews": [{"date": "2026-02-15T08:30:00Z", "dose_g": 20, "water_weight_g": 320}]}

    for invalid_type in ["drip", "aeropress", "cold_brew"]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "type": invalid_type}]})

    for valid_type in ["immersion", "pour_over", "espresso", "hybrid"]:
        validator.validate({**base, "brews": [{**base["brews"][0], "type": valid_type}]})


# ---------------------------------------------------------------------------
# Coffee metadata fields
# ---------------------------------------------------------------------------

def test_coffee_origin_multi_entry_accepted(validator):
    """coffee.origin with multiple entries is valid."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "hybrid", "dose_g": 15,
                   "water_weight_g": 200, "coffee": {"type": "blend", "origin": ["Ethiopia", "Colombia"]}}]
    })


def test_coffee_origin_empty_array_rejected(validator):
    """coffee.origin: [] (empty array) is rejected (minItems: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"origin": []}}]
        })


def test_coffee_type_enum_valid(validator):
    """coffee.type accepts 'single_origin' and 'blend'."""
    for coffee_type in ["single_origin", "blend"]:
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"type": coffee_type}}]
        })


def test_coffee_type_enum_invalid(validator):
    """coffee.type: 'roast' is rejected (not in enum)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"type": "roast"}}]
        })


def test_roast_date_plain_date_accepted(validator):
    """roast_date in YYYY-MM-DD format is accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "coffee": {"roast_date": "2026-01-20"}}]
    })


def test_roast_date_datetime_rejected(validator):
    """roast_date with time component is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"roast_date": "2026-01-20T00:00:00Z"}}]
        })


# ---------------------------------------------------------------------------
# water.ppm
# ---------------------------------------------------------------------------

def test_water_ppm_zero_accepted(validator):
    """water.ppm: 0 is accepted (minimum: 0, not exclusive)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "water": {"ppm": 0}}]
    })


def test_water_ppm_negative_rejected(validator):
    """water.ppm: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "water": {"ppm": -1}}]
        })


# ---------------------------------------------------------------------------
# v0.1 and v0.2 format rejection
# ---------------------------------------------------------------------------

def test_v0_2_format_rejected(validator):
    """brewspec_version '0.2' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.2", "brews": [VALID_BREW]})


def test_v0_1_format_rejected(validator):
    """v0.1-format file (nested coffee.dose_g, water.weight_g) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
        })


# ---------------------------------------------------------------------------
# AC-20: tds and ey removed from brew level, now in result
# ---------------------------------------------------------------------------

def test_tds_at_brew_level_rejected(validator):
    """AC-20: tds at flat brew level fails validation in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "tds": 1.38}]
        })


def test_ey_at_brew_level_rejected(validator):
    """AC-20: ey at flat brew level fails validation in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "ey": 20.1}]
        })


# ---------------------------------------------------------------------------
# AC-27: rating removed from brew level
# ---------------------------------------------------------------------------

def test_rating_at_brew_level_rejected(validator):
    """AC-27: rating at flat brew level fails validation in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "rating": 4}]
        })


# ---------------------------------------------------------------------------
# AC-15, AC-16, AC-17, AC-18, AC-19: result object
# ---------------------------------------------------------------------------

def test_result_omitted_accepted(validator):
    """AC-17: Brew without result passes validation."""
    validator.validate(VALID_DOC)


def test_result_empty_object_accepted(validator):
    """AC-18: result: {} (empty object) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {}}]
    })


def test_result_tds_ey_accepted(validator):
    """AC-20: result with tds and ey passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tds": 1.38, "ey": 20.1}}]
    })


def test_result_unknown_field_rejected(validator):
    """AC-19: result with an unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"score": 95}}]
        })


# ---------------------------------------------------------------------------
# AC-21: result.brix
# ---------------------------------------------------------------------------

def test_result_brix_valid_accepted(validator):
    """AC-21: result.brix: 1.5 passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 1.5}}]
    })


def test_result_brix_zero_accepted(validator):
    """AC-21: result.brix: 0 passes validation (minimum: 0, not exclusive)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 0}}]
    })


def test_result_brix_negative_rejected(validator):
    """AC-21: result.brix: -1 fails validation (minimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"brix": -1}}]
        })


# ---------------------------------------------------------------------------
# AC-22, AC-23, AC-24, AC-25: result.ratings
# ---------------------------------------------------------------------------

def test_ratings_partial_accepted(validator):
    """AC-24: result.ratings with only some dimensions passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 4, "acidity": 3}}}]
    })


def test_ratings_overall_maximum_accepted(validator):
    """AC-25: result.ratings.overall: 5 passes validation (at maximum)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 5}}}]
    })


def test_ratings_overall_minimum_accepted(validator):
    """AC-25: result.ratings.overall: 1 passes validation (at minimum)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 1}}}]
    })


def test_ratings_below_minimum_rejected(validator):
    """AC-25: result.ratings.overall: 0 fails validation (minimum: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 0}}}]
        })


def test_ratings_above_maximum_rejected(validator):
    """AC-25: result.ratings.overall: 6 fails validation (maximum: 5)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 6}}}]
        })


def test_ratings_float_rejected(validator):
    """AC-25: result.ratings.overall: 3.5 fails validation (must be integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 3.5}}}]
        })


def test_ratings_unknown_field_rejected(validator):
    """result.ratings with an unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"balance": 4}}}]
        })


# ---------------------------------------------------------------------------
# AC-26: result.tasting_notes
# ---------------------------------------------------------------------------

def test_result_tasting_notes_accepted(validator):
    """AC-26: result.tasting_notes: non-empty string passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "Bright citrus"}}]
    })


def test_result_tasting_notes_maxlength_accepted(validator):
    """AC-26: result.tasting_notes: exactly 2000 chars passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2000}}]
    })


def test_result_tasting_notes_maxlength_exceeded(validator):
    """AC-26: result.tasting_notes: 2001 chars fails validation (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2001}}]
        })


def test_result_tasting_notes_empty_rejected(validator):
    """AC-26: result.tasting_notes: empty string fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": ""}}]
        })


# ---------------------------------------------------------------------------
# AC-14 through AC-19: maxLength constraints
# ---------------------------------------------------------------------------

def test_method_maxlength_accepted(validator):
    """method up to 100 chars is accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "method": "H" * 100}]
    })


def test_method_maxlength_exceeded(validator):
    """method over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "method": "H" * 101}]
        })


def test_notes_maxlength_accepted(validator):
    """notes up to 2000 chars is accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "notes": "N" * 2000}]
    })


def test_notes_maxlength_exceeded(validator):
    """notes over 2000 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "notes": "N" * 2001}]
        })


def test_coffee_varietal_maxlength_exceeded(validator):
    """coffee.varietal over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"varietal": "V" * 101}}]
        })


def test_coffee_process_maxlength_exceeded(validator):
    """coffee.process over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"process": "P" * 101}}]
        })


def test_coffee_origin_item_maxlength_exceeded(validator):
    """coffee.origin item over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"origin": ["O" * 101]}}]
        })


# ---------------------------------------------------------------------------
# Freeform string minimum length
# ---------------------------------------------------------------------------

def test_freeform_text_fields_not_empty(validator):
    """Optional string fields (method, notes) must not be empty strings.
    grind is now an enum so empty string is tested differently."""
    base = {"brewspec_version": "0.4", "brews": [dict(VALID_BREW)]}

    for field in ("method", "notes"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: ""}]})


# ---------------------------------------------------------------------------
# additionalProperties: false
# ---------------------------------------------------------------------------

def test_additional_properties_rejected(validator):
    """Schema rejects unknown fields (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "unknown_field": "should fail"}]
        })


# ---------------------------------------------------------------------------
# equipment object
# ---------------------------------------------------------------------------

def test_equipment_object_optional(validator):
    """brew without equipment object passes."""
    validator.validate(VALID_DOC)


def test_equipment_empty_object_accepted(validator):
    """equipment: {} (empty object) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "equipment": {}}]
    })


def test_equipment_grinder_accepted(validator):
    """equipment.grinder is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4"}}]
    })


def test_equipment_brewer_accepted(validator):
    """equipment.brewer is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"brewer": "Hario V60 02"}}]
    })


def test_equipment_both_fields_accepted(validator):
    """equipment with both grinder and brewer passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4", "brewer": "Hario V60 02"}}]
    })


def test_equipment_unknown_field_rejected(validator):
    """equipment with an unrecognised field is rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "equipment": {"kettle": "Fellow Stagg EKG"}}]
        })


def test_equipment_grinder_empty_string_rejected(validator):
    """equipment.grinder: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "equipment": {"grinder": ""}}]
        })


# ---------------------------------------------------------------------------
# Example file validation
# ---------------------------------------------------------------------------

def load_example_file(filepath):
    """Load a YAML or JSON example file."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text(encoding="utf-8"))
    return yaml.safe_load(filepath.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "example_file",
    sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")),
    ids=lambda f: f.name,
)
def test_valid_examples_pass(validator, example_file):
    """AC-29–AC-35: All valid example files must pass schema validation."""
    data = load_example_file(example_file)
    validator.validate(data)


@pytest.mark.parametrize(
    "example_file",
    sorted(INVALID_DIR.glob("*.yaml")),
    ids=lambda f: f.name,
)
def test_invalid_examples_fail(validator, example_file):
    """AC-36–AC-38: All invalid example files must fail schema validation."""
    data = load_example_file(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# ---------------------------------------------------------------------------
# Format-agnostic validation (JSON and YAML)
# ---------------------------------------------------------------------------

def test_json_format_supported(validator):
    """Schema supports both YAML and JSON formats."""
    validator.validate(VALID_DOC)

    json_files = list(VALID_DIR.glob("*.json"))
    if json_files:
        json_data = load_example_file(json_files[0])
        validator.validate(json_data)
