"""
Test suite for BrewSpec v0.3

This test suite validates the BrewSpec JSON Schema against example files.
Tests are organized by acceptance criteria from specs/products/brewspec-v0.3.md
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

# Minimal valid v0.3 brew dict used across tests
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.3", "brews": [VALID_BREW]}


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
# AC-5 / AC-6: Version const must be "0.3"
# ---------------------------------------------------------------------------

def test_version_must_be_0_3(validator):
    """AC-5 / AC-6: brewspec_version is required and must be exactly '0.3'."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({"brews": [VALID_BREW]})

    # Wrong version
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "1.0", "brews": [VALID_BREW]})

    # Correct version
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_2(validator):
    """AC-5: brewspec_version '0.2' is rejected by the v0.3 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_1(validator):
    """AC-5: brewspec_version '0.1' is rejected by the v0.3 schema."""
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
        validator.validate({"brewspec_version": "0.3"})

    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.3", "brews": []})

    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Required brew fields
# ---------------------------------------------------------------------------

def test_required_brew_fields(validator):
    """Each brew must have date, type, dose_g, water_weight_g."""
    base = {"brewspec_version": "0.3"}

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
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "water_weight_g": 320}]
        })


def test_water_weight_g_required_at_brew_level(validator):
    """water_weight_g is required at the brew level."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "dose_g": 20}]
        })


# ---------------------------------------------------------------------------
# Date format
# ---------------------------------------------------------------------------

def test_date_format_iso8601(validator):
    """date must be ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ."""
    base = {"brewspec_version": "0.3", "brews": [{"type": "pour_over", "dose_g": 20, "water_weight_g": 320}]}

    invalid_dates = [
        "2026-02-15",
        "2026-02-15T08:30:00",
        "2026-02-15T08:30:00+00:00",
        "15-02-2026T08:30:00Z",
        "not-a-date",
    ]
    for d in invalid_dates:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "date": d}]})

    validator.validate({**base, "brews": [{**base["brews"][0], "date": "2026-02-15T08:30:00Z"}]})


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
        "brewspec_version": "0.3",
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
            "grind": "medium-fine",
            "duration_s": 180,
            "tds": 1.38,
            "ey": 20.5,
            "rating": 4,
            "notes": "Bright acidity, slightly under-extracted"
        }]
    })


def test_minimal_brew_passes(validator):
    """Brew with only required fields passes."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "immersion", "dose_g": 30, "water_weight_g": 500}]
    })


# ---------------------------------------------------------------------------
# Rating constraints
# ---------------------------------------------------------------------------

def test_rating_range_1_to_5(validator):
    """rating must be an integer between 1 and 5 inclusive."""
    base = {"brewspec_version": "0.3", "brews": [dict(VALID_BREW)]}

    for invalid_rating in [0, 6, -1, 3.5]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "rating": invalid_rating}]})

    for valid_rating in [1, 2, 3, 4, 5]:
        validator.validate({**base, "brews": [{**base["brews"][0], "rating": valid_rating}]})


# ---------------------------------------------------------------------------
# Numeric constraints
# ---------------------------------------------------------------------------

def test_negative_values_rejected(validator):
    """Negative values for dose_g, water_weight_g, water_volume_ml, duration_s are rejected."""
    base = {"brewspec_version": "0.3", "brews": [dict(VALID_BREW)]}

    for field, value in [("dose_g", -10), ("water_weight_g", -320),
                         ("water_volume_ml", -100), ("duration_s", -30)]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: value}]})


def test_zero_weight_rejected(validator):
    """Zero values for dose_g and water_weight_g are rejected (exclusiveMinimum: 0)."""
    base = {"brewspec_version": "0.3", "brews": [dict(VALID_BREW)]}

    for field in ("dose_g", "water_weight_g"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: 0}]})


def test_zero_duration_rejected(validator):
    """duration_s: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                       "dose_g": 18, "water_weight_g": 36, "duration_s": 0}]
        })


def test_positive_duration_accepted(validator):
    """duration_s: 1 is accepted (exclusiveMinimum: 0)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                   "dose_g": 18, "water_weight_g": 36, "duration_s": 1}]
    })


def test_temperature_range(validator):
    """water_temp_c must be between 0 and 100."""
    base = {"brewspec_version": "0.3", "brews": [dict(VALID_BREW)]}

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
    base = {"brewspec_version": "0.3", "brews": [{"date": "2026-02-15T08:30:00Z", "dose_g": 20, "water_weight_g": 320}]}

    for invalid_type in ["drip", "aeropress", "cold_brew", "turkish"]:
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
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "hybrid", "dose_g": 15,
                   "water_weight_g": 200, "coffee": {"type": "blend", "origin": ["Ethiopia", "Colombia"]}}]
    })


def test_coffee_origin_empty_array_rejected(validator):
    """coffee.origin: [] (empty array) is rejected (minItems: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"origin": []}}]
        })


def test_coffee_type_enum_valid(validator):
    """coffee.type accepts 'single_origin' and 'blend'."""
    for coffee_type in ["single_origin", "blend"]:
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"type": coffee_type}}]
        })


def test_coffee_type_enum_invalid(validator):
    """coffee.type: 'roast' is rejected (not in enum)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "coffee": {"type": "roast"}}]
        })


def test_roast_date_plain_date_accepted(validator):
    """roast_date in YYYY-MM-DD format is accepted."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "coffee": {"roast_date": "2026-01-20"}}]
    })


def test_roast_date_datetime_rejected(validator):
    """roast_date with time component is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
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
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "water": {"ppm": 0}}]
    })


def test_water_ppm_negative_rejected(validator):
    """water.ppm: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "water": {"ppm": -1}}]
        })


# ---------------------------------------------------------------------------
# v0.1 and v0.2 format rejection
# ---------------------------------------------------------------------------

def test_v0_2_format_rejected(validator):
    """brewspec_version '0.2' is rejected by the v0.3 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.2", "brews": [VALID_BREW]})


def test_v0_1_format_rejected(validator):
    """v0.1-format file (nested coffee.dose_g, water.weight_g) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
        })


# ---------------------------------------------------------------------------
# tds field
# ---------------------------------------------------------------------------

def test_tds_valid_value_accepted(validator):
    """tds: 1.38 is accepted."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "tds": 1.38}]
    })


def test_tds_zero_rejected(validator):
    """tds: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "tds": 0}]
        })


def test_tds_negative_rejected(validator):
    """tds: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "tds": -1}]
        })


# ---------------------------------------------------------------------------
# AC-11 / AC-12 / AC-13: ey (extraction yield)
# ---------------------------------------------------------------------------

def test_ey_valid_value_accepted(validator):
    """AC-11/AC-13: ey: 20.5 is accepted (flat on brew, > 0)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "ey": 20.5}]
    })


def test_ey_zero_rejected(validator):
    """AC-12: ey: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "ey": 0}]
        })


def test_ey_negative_rejected(validator):
    """AC-12: ey: -5 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "ey": -5}]
        })


def test_ey_optional(validator):
    """AC-11: ey is optional — brew without ey passes."""
    validator.validate(VALID_DOC)


def test_ey_and_tds_together(validator):
    """AC-13: ey and tds can both be present on the same brew."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "tds": 1.38, "ey": 20.5}]
    })


# ---------------------------------------------------------------------------
# AC-7 / AC-8 / AC-9 / AC-10: equipment object
# ---------------------------------------------------------------------------

def test_equipment_object_optional(validator):
    """AC-9: brew without equipment object passes."""
    validator.validate(VALID_DOC)


def test_equipment_empty_object_accepted(validator):
    """AC-9: equipment: {} (empty object) passes validation."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "equipment": {}}]
    })


def test_equipment_grinder_accepted(validator):
    """AC-8: equipment.grinder is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4"}}]
    })


def test_equipment_brewer_accepted(validator):
    """AC-8: equipment.brewer is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"brewer": "Hario V60 02"}}]
    })


def test_equipment_both_fields_accepted(validator):
    """AC-8: equipment with both grinder and brewer passes."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4", "brewer": "Hario V60 02"}}]
    })


def test_equipment_unknown_field_rejected(validator):
    """AC-10: equipment with an unrecognised field is rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "equipment": {"kettle": "Fellow Stagg EKG"}}]
        })


def test_equipment_grinder_empty_string_rejected(validator):
    """AC-8: equipment.grinder: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "equipment": {"grinder": ""}}]
        })


# ---------------------------------------------------------------------------
# AC-14 through AC-19: maxLength constraints
# ---------------------------------------------------------------------------

def test_method_maxlength_accepted(validator):
    """AC-14: method up to 100 chars is accepted."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "method": "H" * 100}]
    })


def test_method_maxlength_exceeded(validator):
    """AC-14: method over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "method": "H" * 101}]
        })


def test_grind_maxlength_accepted(validator):
    """AC-15: grind up to 100 chars is accepted."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "grind": "G" * 100}]
    })


def test_grind_maxlength_exceeded(validator):
    """AC-15: grind over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "grind": "G" * 101}]
        })


def test_notes_maxlength_accepted(validator):
    """AC-16: notes up to 2000 chars is accepted."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320, "notes": "N" * 2000}]
    })


def test_notes_maxlength_exceeded(validator):
    """AC-16: notes over 2000 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "notes": "N" * 2001}]
        })


def test_coffee_varietal_maxlength_exceeded(validator):
    """AC-17: coffee.varietal over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"varietal": "V" * 101}}]
        })


def test_coffee_process_maxlength_exceeded(validator):
    """AC-18: coffee.process over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"process": "P" * 101}}]
        })


def test_coffee_origin_item_maxlength_exceeded(validator):
    """AC-19: coffee.origin item over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320,
                       "coffee": {"origin": ["O" * 101]}}]
        })


# ---------------------------------------------------------------------------
# Freeform string minimum length
# ---------------------------------------------------------------------------

def test_freeform_text_fields_not_empty(validator):
    """Optional string fields (method, grind, notes) must not be empty strings."""
    base = {"brewspec_version": "0.3", "brews": [dict(VALID_BREW)]}

    for field in ("method", "grind", "notes"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: ""}]})


# ---------------------------------------------------------------------------
# additionalProperties: false
# ---------------------------------------------------------------------------

def test_additional_properties_rejected(validator):
    """Schema rejects unknown fields (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320, "unknown_field": "should fail"}]
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
    """All valid example files must pass schema validation."""
    data = load_example_file(example_file)
    validator.validate(data)


@pytest.mark.parametrize(
    "example_file",
    sorted(INVALID_DIR.glob("*.yaml")),
    ids=lambda f: f.name,
)
def test_invalid_examples_fail(validator, example_file):
    """All invalid example files must fail schema validation."""
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
