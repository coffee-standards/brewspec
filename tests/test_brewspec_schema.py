"""
Test suite for BrewSpec v1.0

This test suite validates the BrewSpec JSON Schema against example files.
Tests are organized by acceptance criteria from the brewspec-v1.0 product spec.
"""

import decimal
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

# Minimal valid v1.0 brew dict used across tests.
# In v1.0 all brew fields are optional, but we keep a typical set of fields
# here as they represent a typical valid brew document.
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_g": 320
}
VALID_DOC = {"brewspec_version": "1.0", "brews": [VALID_BREW]}

# All eight CVA rating field names (used in parametrized tests)
RATING_FIELDS = [
    "overall",
    "fragrance",
    "aroma",
    "flavour",
    "aftertaste",
    "acidity",
    "sweetness",
    "mouthfeel",
]


def _to_decimal(data):
    """Convert a Python dict to use Decimal floats for jsonschema multipleOf checks."""
    return json.loads(json.dumps(data), parse_float=decimal.Decimal)


def _load_yaml_example(path):
    """Load a YAML example file with Decimal float parsing for multipleOf accuracy."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(json.dumps(raw), parse_float=decimal.Decimal)


def _load_example_file(filepath):
    """Load a YAML or JSON example file with Decimal float parsing."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text(encoding="utf-8"), parse_float=decimal.Decimal)
    return _load_yaml_example(filepath)


@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema with Decimal parsing for multipleOf accuracy."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"), parse_float=decimal.Decimal)


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
# AC-1 (legacy): Version — const "1.0", title "BrewSpec v1.0"
# ---------------------------------------------------------------------------

def test_schema_title_is_v1_0(schema):
    """Schema title must be 'BrewSpec v1.0'."""
    assert schema["title"] == "BrewSpec v1.0"


def test_version_must_be_1_0(validator):
    """brewspec_version is required and must be exactly '1.0'."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({"brews": [VALID_BREW]})

    # Wrong version (old 0.9)
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.9", "brews": [VALID_BREW]})

    # Correct version
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_8(validator):
    """brewspec_version '0.8' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.8",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_7(validator):
    """brewspec_version '0.7' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.7",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_6(validator):
    """brewspec_version '0.6' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.6",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_5(validator):
    """brewspec_version '0.5' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.5",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_4(validator):
    """brewspec_version '0.4' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_3(validator):
    """brewspec_version '0.3' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_2(validator):
    """brewspec_version '0.2' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [VALID_BREW]
        })


def test_version_const_rejects_v0_1(validator):
    """brewspec_version '0.1' is rejected by the v1.0 schema."""
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
        validator.validate({"brewspec_version": "1.0"})

    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "1.0", "brews": []})


    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Brew fields are optional (required constraint removed in v0.7)
# ---------------------------------------------------------------------------

def test_brew_fields_all_optional_empty_brew(validator):
    """Empty brew object {} passes validation — all four fields are optional."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{}]
    })


def test_brew_fields_omit_date_passes(validator):
    """Brew without date passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"type": "pour_over", "dose_g": 20, "water_g": 320}]
    })


def test_brew_fields_omit_type_passes(validator):
    """Brew without type passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "dose_g": 20, "water_g": 320}]
    })


def test_brew_fields_omit_dose_g_passes(validator):
    """Brew without dose_g passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "water_g": 320}]
    })


def test_brew_fields_omit_water_g_passes(validator):
    """Brew without water_g passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "dose_g": 20}]
    })


def test_brew_fields_omit_all_four_with_other_field(validator):
    """Brew with only method (no date/type/dose_g/water_g) passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"method": "Hario V60"}]
    })


def test_minimal_document_empty_brew(validator):
    """Minimal document {brewspec_version, brews: [{}]} passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{}]
    })


def test_v09_valid_doc_passes_with_version_bump(validator):
    """A v0.9-style document with all four typical fields passes under v1.0 (using water_g)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_g": 320
        }]
    })


def test_schema_brew_def_has_no_required(schema):
    """$defs/brew must not contain a 'required' key."""
    assert "required" not in schema["$defs"]["brew"]


def test_schema_top_level_required_unchanged(schema):
    """Top-level required array is still ['brewspec_version', 'brews']."""
    assert schema["required"] == ["brewspec_version", "brews"]


# ---------------------------------------------------------------------------
# Date format — dual-format
# ---------------------------------------------------------------------------

def test_date_only_format_accepted(validator):
    """date: YYYY-MM-DD (date-only) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "date": "2026-02-21"}]
    })


def test_date_full_datetime_accepted(validator):
    """date: YYYY-MM-DDTHH:MM:SSZ (full datetime) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00Z"}]
    })


def test_date_no_z_rejected(validator):
    """date: datetime without Z suffix fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00"}]
        })


def test_date_wrong_order_rejected(validator):
    """date: DD-MM-YYYY order fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "date": "21-02-2026"}]
        })


def test_date_month_13_passes_schema(validator):
    """date: month 13 passes schema validation. Calendar validation is application-layer."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "date": "2026-13-01"}]
    })


def test_date_format_invalid_other(validator):
    """Plainly invalid date strings are rejected."""
    base = {"brewspec_version": "1.0", "brews": [{"type": "pour_over", "dose_g": 20, "water_g": 320}]}

    invalid_dates = [
        "2026-02-15T08:30:00+00:00",
        "15-02-2026T08:30:00Z",
        "not-a-date",
    ]
    for d in invalid_dates:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "date": d}]})


# ---------------------------------------------------------------------------
# grind field — strict enum
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"
])
def test_grind_enum_all_values_accepted(validator, grind_value):
    """Each of the 7 grind enum values passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "grind": grind_value}]
    })


def test_grind_freeform_rejected(validator):
    """grind: freeform string not in the enum fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "grind": "setting 15"}]
        })


def test_grind_wrong_case_rejected(validator):
    """grind: 'Medium' (wrong case) fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "grind": "Medium"}]
        })


def test_grind_omitted_accepted(validator):
    """grind omitted entirely passes validation (field remains optional)."""
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
        "brewspec_version": "1.0",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "method": "Hario V60",
            "dose_g": 20,
            "water_g": 320,
            "brew_ratio": 16.0,
            "water_temp_c": 96,
            "coffee": {
                "name": "Ethiopia Yirgacheffe",
                "roaster": "Onyx",
                "roast_level": "light",
                "roast_date": "2026-01-20",
                "type": "single_origin",
                "origins": [{"country": "Ethiopia", "process": "Washed", "varietal": "Heirloom", "elevation_masl": 1950}],
                "cupping_notes": "Blueberry, jasmine"
            },
            "water": {"ppm": 150},
            "equipment": {
                "grinder": "Comandante C40 MK4",
                "brewer": "Hario V60 02",
                "grinder_setting": 21,
                "notes": "Burrs replaced 2026-01",
                "pressure_bar": 9.0,
                "flow_rate_ml_s": 2.5
            },
            "grind": "medium_fine",
            "duration_s": 180,
            "process_notes": "Bright acidity, slightly under-extracted",
            "result": {
                "tds": 1.38,
                "ey": 20.5,
                "brix": 1.5,
                "water_g": 318,
                "tasting_notes": "Citrus and caramel",
                "ratings": {
                    "overall": 4,
                    "acidity": 5
                }
            }
        }]
    })


def test_minimal_brew_passes(validator):
    """Brew with typical fields passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "immersion", "dose_g": 30, "water_g": 500}]
    })


# ---------------------------------------------------------------------------
# water_volume_ml removed
# ---------------------------------------------------------------------------

def test_water_volume_ml_present_rejected(validator):
    """water_volume_ml present in brew fails validation
    (additionalProperties: false, field removed)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "water_volume_ml": 320}]
        })


def test_water_volume_ml_omitted_passes(validator):
    """brew without water_volume_ml passes validation."""
    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Numeric constraints
# ---------------------------------------------------------------------------

def test_negative_values_rejected(validator):
    """Negative values for dose_g, water_g, duration_s are rejected."""
    base = {"brewspec_version": "1.0", "brews": [dict(VALID_BREW)]}

    for field, value in [("dose_g", -10), ("water_g", -320), ("duration_s", -30)]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: value}]})


def test_zero_weight_rejected(validator):
    """Zero values for dose_g and water_g are rejected (exclusiveMinimum: 0)."""
    base = {"brewspec_version": "1.0", "brews": [dict(VALID_BREW)]}

    for field in ("dose_g", "water_g"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: 0}]})


def test_zero_duration_rejected(validator):
    """duration_s: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                       "dose_g": 18, "water_g": 36, "duration_s": 0}]
        })


def test_positive_duration_accepted(validator):
    """duration_s: 1 is accepted (exclusiveMinimum: 0)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                   "dose_g": 18, "water_g": 36, "duration_s": 1}]
    })


def test_temperature_range(validator):
    """water_temp_c must be between 0 and 100."""
    base = {"brewspec_version": "1.0", "brews": [dict(VALID_BREW)]}

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
    base = {"brewspec_version": "1.0", "brews": [{"date": "2026-02-15T08:30:00Z", "dose_g": 20, "water_g": 320}]}

    for invalid_type in ["drip", "aeropress", "cold_brew"]:
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], "type": invalid_type}]})

    for valid_type in ["immersion", "pour_over", "espresso", "hybrid"]:
        validator.validate({**base, "brews": [{**base["brews"][0], "type": valid_type}]})


# ---------------------------------------------------------------------------
# equipment.grinder_setting
# ---------------------------------------------------------------------------

def test_grinder_setting_integer_accepted(validator):
    """equipment.grinder_setting: 21 (integer) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {"grinder": "Comandante C40", "grinder_setting": 21}}]
    })


def test_grinder_setting_float_accepted(validator):
    """equipment.grinder_setting: 5.2 (float) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {"grinder_setting": 5.2}}]
    })


def test_grinder_setting_zero_rejected(validator):
    """equipment.grinder_setting: 0 fails validation (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"grinder_setting": 0}}]
        })


def test_grinder_setting_negative_rejected(validator):
    """equipment.grinder_setting: -1 fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"grinder_setting": -1}}]
        })


def test_grinder_setting_string_rejected(validator):
    """equipment.grinder_setting: '21' (string) fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"grinder_setting": "21"}}]
        })


def test_grinder_setting_string_clicks_rejected(validator):
    """equipment.grinder_setting: '21 clicks' (string) fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"grinder_setting": "21 clicks"}}]
        })


def test_grinder_setting_omitted_passes(validator):
    """equipment.grinder_setting omitted passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {}}]
    })


# ---------------------------------------------------------------------------
# coffee.process and coffee.varietal removed from top level
# ---------------------------------------------------------------------------

def test_coffee_process_top_level_rejected(validator):
    """coffee.process at top-level coffee object fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"process": "Washed"}}]
        })


def test_coffee_varietal_top_level_rejected(validator):
    """coffee.varietal at top-level coffee object fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"varietal": "Heirloom"}}]
        })


def test_coffee_process_in_origin_accepted(validator):
    """coffee.origins[0].process: 'Washed' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"origins": [{"process": "Washed"}]}}]
    })


def test_coffee_without_process_passes(validator):
    """A brew with coffee but no process field passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"type": "single_origin"}}]
    })


def test_coffee_without_varietal_passes(validator):
    """A brew with coffee but no varietal field passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"type": "single_origin"}}]
    })


# ---------------------------------------------------------------------------
# coffee.origins[].varietal
# ---------------------------------------------------------------------------

def test_origin_varietal_accepted(validator):
    """coffee.origins[0].varietal: 'Heirloom' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{"country": "Ethiopia", "varietal": "Heirloom"}]
        }}]
    })


def test_origin_varietal_empty_string_rejected(validator):
    """coffee.origins[0].varietal: '' fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {
                "origins": [{"varietal": ""}]
            }}]
        })


def test_origin_varietal_omitted_passes(validator):
    """origin entry without varietal passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{"country": "Ethiopia"}]
        }}]
    })


def test_origin_unknown_field_rejected(validator):
    """origin entry with unrecognised field fails validation
    (additionalProperties: false unchanged)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {
                "origins": [{"varietal": "Heirloom", "unknown": "bad"}]
            }}]
        })


def test_origin_all_v0_9_fields_accepted(validator):
    """origin object with all 10 v0.9 fields passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{
                "name": "Ethiopia Yirgacheffe Natural",
                "country": "Ethiopia",
                "region": "Yirgacheffe",
                "subregion": "Kochere",
                "producer": "Daye Bensa Washing Station",
                "process": "Natural",
                "lot": "Lot 42 Export Grade 1",
                "harvest_year": 2025,
                "varietal": "Heirloom",
                "elevation_masl": 1950
            }]
        }}]
    })


# ---------------------------------------------------------------------------
# coffee.roaster
# ---------------------------------------------------------------------------

def test_roaster_valid_accepted(validator):
    """coffee.roaster: 'Onyx' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"roaster": "Onyx"}}]
    })


def test_roaster_omitted_passes(validator):
    """coffee.roaster omitted passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"name": "Test"}}]
    })


def test_roaster_empty_string_rejected(validator):
    """coffee.roaster: '' fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"roaster": ""}}]
        })


def test_roaster_maxlength_accepted(validator):
    """coffee.roaster: 100 chars (at maxLength boundary) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"roaster": "R" * 100}}]
    })


def test_roaster_maxlength_exceeded(validator):
    """coffee.roaster: 101 chars fails validation (maxLength: 100)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"roaster": "R" * 101}}]
        })


# ---------------------------------------------------------------------------
# coffee.roast_level
# ---------------------------------------------------------------------------

def test_roast_level_light_accepted(validator):
    """coffee.roast_level: 'light' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"roast_level": "light"}}]
    })


def test_roast_level_medium_accepted(validator):
    """coffee.roast_level: 'medium' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"roast_level": "medium"}}]
    })


def test_roast_level_dark_accepted(validator):
    """coffee.roast_level: 'dark' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"roast_level": "dark"}}]
    })


def test_roast_level_omitted_passes(validator):
    """coffee.roast_level omitted passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"name": "Test"}}]
    })


def test_roast_level_medium_light_rejected(validator):
    """coffee.roast_level: 'medium_light' fails validation (not in enum)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"roast_level": "medium_light"}}]
        })


def test_roast_level_capitalized_rejected(validator):
    """coffee.roast_level: 'Light' (capitalised) fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"roast_level": "Light"}}]
        })


# ---------------------------------------------------------------------------
# origin.elevation_masl
# ---------------------------------------------------------------------------

def test_elevation_masl_valid_accepted(validator):
    """elevation_masl: 1950 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{"country": "Ethiopia", "elevation_masl": 1950}]
        }}]
    })


def test_elevation_masl_omitted_passes(validator):
    """elevation_masl omitted passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{"country": "Ethiopia"}]
        }}]
    })


def test_elevation_masl_zero_rejected(validator):
    """elevation_masl: 0 fails validation (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {
                "origins": [{"elevation_masl": 0}]
            }}]
        })


def test_elevation_masl_negative_rejected(validator):
    """elevation_masl: -100 fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {
                "origins": [{"elevation_masl": -100}]
            }}]
        })


def test_elevation_masl_float_rejected(validator):
    """elevation_masl: 1950.5 fails validation (must be integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {
                "origins": [{"elevation_masl": 1950.5}]
            }}]
        })


# ---------------------------------------------------------------------------
# water_temp_c multipleOf: 0.1
# ---------------------------------------------------------------------------

def test_water_temp_c_96_0_passes(validator):
    """water_temp_c: 96.0 passes validation."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 96.0}]
    })
    validator.validate(doc)


def test_water_temp_c_96_5_passes(validator):
    """water_temp_c: 96.5 passes validation."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 96.5}]
    })
    validator.validate(doc)


def test_water_temp_c_integer_passes(validator):
    """water_temp_c: 93 (integer) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 93}]
    })


def test_water_temp_c_96_15_rejected(validator):
    """water_temp_c: 96.15 fails validation (multipleOf: 0.1)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 96.15}]
    })
    with pytest.raises(ValidationError):
        validator.validate(doc)


def test_water_temp_c_96_123_rejected(validator):
    """water_temp_c: 96.123 fails validation (multipleOf: 0.1)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 96.123}]
    })
    with pytest.raises(ValidationError):
        validator.validate(doc)


def test_water_temp_c_96_1_passes(validator):
    """water_temp_c: 96.1 passes validation (IEEE 754 edge case — needs Decimal)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 96.1}]
    })
    validator.validate(doc)


def test_water_temp_c_93_3_passes(validator):
    """water_temp_c: 93.3 passes validation (IEEE 754 edge case)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 93.3}]
    })
    validator.validate(doc)


def test_water_temp_c_0_1_passes(validator):
    """water_temp_c: 0.1 passes validation (boundary value)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 0.1}]
    })
    validator.validate(doc)


def test_water_temp_c_99_9_passes(validator):
    """water_temp_c: 99.9 passes validation (boundary value)."""
    doc = _to_decimal({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "water_temp_c": 99.9}]
    })
    validator.validate(doc)


# ---------------------------------------------------------------------------
# Schema structure verification
# ---------------------------------------------------------------------------

def test_schema_roaster_in_coffee_properties(schema):
    """roaster is present in $defs/coffee/properties with correct constraints."""
    roaster = schema["$defs"]["coffee"]["properties"]["roaster"]
    assert roaster["type"] == "string"
    assert roaster["minLength"] == 1
    assert roaster["maxLength"] == 100


def test_schema_roast_level_in_coffee_properties(schema):
    """roast_level is present in $defs/coffee/properties with correct enum."""
    roast_level = schema["$defs"]["coffee"]["properties"]["roast_level"]
    assert roast_level["type"] == "string"
    assert roast_level["enum"] == ["light", "medium", "dark"]


def test_schema_elevation_masl_in_origin_properties(schema):
    """elevation_masl is present in $defs/origin/properties with correct constraints."""
    elevation = schema["$defs"]["origin"]["properties"]["elevation_masl"]
    assert elevation["type"] == "integer"
    assert elevation["exclusiveMinimum"] == 0


def test_schema_water_temp_c_multiple_of(schema):
    """water_temp_c has multipleOf: 0.1."""
    water_temp = schema["$defs"]["brew"]["properties"]["water_temp_c"]
    assert water_temp["multipleOf"] == decimal.Decimal("0.1")


# ---------------------------------------------------------------------------
# coffee.name
# ---------------------------------------------------------------------------

def test_coffee_name_accepted(validator):
    """coffee.name: 'Estate' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"name": "Estate"}}]
    })


def test_coffee_name_empty_string_rejected(validator):
    """coffee.name: '' (empty string) fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"name": ""}}]
        })


def test_coffee_name_omitted_passes(validator):
    """brew with coffee object but no name field passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"type": "single_origin"}}]
    })


def test_coffee_name_coexists_with_origins(validator):
    """coffee.name alongside coffee.origins[0].country passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "name": "Ethiopia Yirgacheffe",
            "origins": [{"country": "Ethiopia"}]
        }}]
    })


def test_coffee_name_max_length_accepted(validator):
    """coffee.name: 100 chars (at maxLength boundary) passes validation (maxLength reduced to 100 in v1.0)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"name": "A" * 100}}]
    })


def test_coffee_name_over_max_length_rejected(validator):
    """coffee.name: 101 chars fails validation (maxLength: 100 in v1.0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"name": "A" * 101}}]
        })


# ---------------------------------------------------------------------------
# Coffee metadata fields
# ---------------------------------------------------------------------------

def test_coffee_origins_multi_entry_accepted(validator):
    """coffee.origins with multiple entries (blend) is valid."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "hybrid", "dose_g": 15,
                   "water_g": 200, "coffee": {"type": "blend",
                   "origins": [{"country": "Ethiopia"}, {"country": "Colombia"}]}}]
    })


def test_coffee_origin_old_format_rejected(validator):
    """coffee.origin string array is rejected by schema (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "hybrid", "dose_g": 15,
                       "water_g": 200, "coffee": {"origin": ["Ethiopia", "Colombia"]}}]
        })


def test_coffee_origins_empty_array_rejected(validator):
    """coffee.origins: [] (empty array) is rejected (minItems: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "coffee": {"origins": []}}]
        })


def test_coffee_type_enum_valid(validator):
    """coffee.type accepts 'single_origin' and 'blend'."""
    for coffee_type in ["single_origin", "blend"]:
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "coffee": {"type": coffee_type}}]
        })


def test_coffee_type_enum_invalid(validator):
    """coffee.type: 'roast' is rejected (not in enum)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "coffee": {"type": "roast"}}]
        })


def test_roast_date_plain_date_accepted(validator):
    """roast_date in YYYY-MM-DD format is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320, "coffee": {"roast_date": "2026-01-20"}}]
    })


def test_roast_date_datetime_rejected(validator):
    """roast_date with time component is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320,
                       "coffee": {"roast_date": "2026-01-20T00:00:00Z"}}]
        })


# ---------------------------------------------------------------------------
# water.ppm
# ---------------------------------------------------------------------------

def test_water_ppm_zero_accepted(validator):
    """water.ppm: 0 is accepted (minimum: 0, not exclusive)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320, "water": {"ppm": 0}}]
    })


def test_water_ppm_negative_rejected(validator):
    """water.ppm: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "water": {"ppm": -1}}]
        })


# ---------------------------------------------------------------------------
# v0.1 and v0.2 format rejection
# ---------------------------------------------------------------------------

def test_v0_2_format_rejected(validator):
    """brewspec_version '0.2' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.2", "brews": [VALID_BREW]})


def test_v0_1_format_rejected(validator):
    """v0.1-format file (nested coffee.dose_g, water.weight_g) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
        })


# ---------------------------------------------------------------------------
# tds and ey removed from brew level, now in result
# ---------------------------------------------------------------------------

def test_tds_at_brew_level_rejected(validator):
    """tds at flat brew level fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "tds": 1.38}]
        })


def test_ey_at_brew_level_rejected(validator):
    """ey at flat brew level fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "ey": 20.1}]
        })


# ---------------------------------------------------------------------------
# rating removed from brew level
# ---------------------------------------------------------------------------

def test_rating_at_brew_level_rejected(validator):
    """rating at flat brew level fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "rating": 4}]
        })


# ---------------------------------------------------------------------------
# result object
# ---------------------------------------------------------------------------

def test_result_omitted_accepted(validator):
    """Brew without result passes validation."""
    validator.validate(VALID_DOC)


def test_result_empty_object_accepted(validator):
    """result: {} (empty object) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {}}]
    })


def test_result_tds_ey_accepted(validator):
    """result with tds and ey passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"tds": 1.38, "ey": 20.1}}]
    })


def test_result_unknown_field_rejected(validator):
    """result with an unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"score": 95}}]
        })


# ---------------------------------------------------------------------------
# result.brix
# ---------------------------------------------------------------------------

def test_result_brix_valid_accepted(validator):
    """result.brix: 1.5 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"brix": 1.5}}]
    })


def test_result_brix_zero_accepted(validator):
    """result.brix: 0 passes validation (minimum: 0, not exclusive)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"brix": 0}}]
    })


def test_result_brix_negative_rejected(validator):
    """result.brix: -1 fails validation (minimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"brix": -1}}]
        })


# ---------------------------------------------------------------------------
# result.ratings — AC-2 through AC-10
# ---------------------------------------------------------------------------

def test_ratings_partial_accepted(validator):
    """AC-10: result.ratings with only some dimensions passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 4, "acidity": 3}}}]
    })


def test_ratings_empty_object_accepted(validator):
    """AC-10: result.ratings: {} (empty object) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {}}}]
    })


def test_ratings_omitted_accepted(validator):
    """AC-9: Document with no ratings object passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {}}]
    })


def test_ratings_overall_minimum_accepted(validator):
    """AC-3: result.ratings.overall: 1 passes validation (at minimum)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 1}}}]
    })


def test_ratings_overall_midrange_accepted(validator):
    """AC-4: result.ratings.overall: 5 passes validation (backward compatibility)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 5}}}]
    })


def test_ratings_new_maximum_accepted(validator):
    """AC-5: result.ratings.overall: 9 passes validation (new maximum)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 9}}}]
    })


def test_ratings_below_minimum_rejected(validator):
    """AC-6: result.ratings.overall: 0 fails validation (minimum: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 0}}}]
        })


def test_ratings_above_new_maximum_rejected(validator):
    """AC-7: result.ratings.overall: 10 fails validation (maximum: 9)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 10}}}]
        })


def test_ratings_value_6_accepted(validator):
    """AC-8: result.ratings.overall: 6 passes validation (was invalid on 1-5 scale)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 6}}}]
    })


def test_ratings_value_7_accepted(validator):
    """AC-8: result.ratings.overall: 7 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 7}}}]
    })


def test_ratings_value_8_accepted(validator):
    """AC-8: result.ratings.overall: 8 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 8}}}]
    })


def test_ratings_float_rejected(validator):
    """result.ratings.overall: 3.5 fails validation (must be integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 3.5}}}]
        })


def test_ratings_unknown_field_rejected(validator):
    """result.ratings with an unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {"balance": 4}}}]
        })


# ---------------------------------------------------------------------------
# AC-3: Parametrized — each of 8 rating fields accepts value 1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", RATING_FIELDS)
def test_ratings_all_fields_accept_minimum(validator, field):
    """AC-3: Each of the 8 rating fields accepts value 1 (minimum)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {field: 1}}}]
    })


# ---------------------------------------------------------------------------
# AC-4: Parametrized — each of 8 rating fields accepts value 5 (backward compat)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", RATING_FIELDS)
def test_ratings_all_fields_accept_5(validator, field):
    """AC-4: Each of the 8 rating fields accepts value 5 (backward compatibility)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {field: 5}}}]
    })


# ---------------------------------------------------------------------------
# AC-5: Parametrized — each of 8 rating fields accepts value 9
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", RATING_FIELDS)
def test_ratings_all_fields_accept_maximum(validator, field):
    """AC-5: Each of the 8 rating fields accepts value 9 (new maximum)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"ratings": {field: 9}}}]
    })


# ---------------------------------------------------------------------------
# AC-6: Parametrized — each of 8 rating fields rejects value 0
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", RATING_FIELDS)
def test_ratings_all_fields_reject_below_min(validator, field):
    """AC-6: Each of the 8 rating fields rejects value 0 (below minimum of 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {field: 0}}}]
        })


# ---------------------------------------------------------------------------
# AC-7: Parametrized — each of 8 rating fields rejects value 10
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", RATING_FIELDS)
def test_ratings_all_fields_reject_above_max(validator, field):
    """AC-7: Each of the 8 rating fields rejects value 10 (above maximum of 9)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"ratings": {field: 10}}}]
        })


# ---------------------------------------------------------------------------
# AC-1: v0.8 version const rejection (dedicated ratings test)
# ---------------------------------------------------------------------------

def test_ratings_version_0_8_rejected(validator):
    """AC-1: A document with brewspec_version '0.8' is rejected by the v0.9 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.8",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 4}}}]
        })


# ---------------------------------------------------------------------------
# result.tasting_notes
# ---------------------------------------------------------------------------

def test_result_tasting_notes_accepted(validator):
    """result.tasting_notes: non-empty string passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "Bright citrus"}}]
    })


def test_result_tasting_notes_maxlength_accepted(validator):
    """result.tasting_notes: exactly 2000 chars passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2000}}]
    })


def test_result_tasting_notes_maxlength_exceeded(validator):
    """result.tasting_notes: 2001 chars fails validation (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2001}}]
        })


def test_result_tasting_notes_empty_rejected(validator):
    """result.tasting_notes: empty string fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": ""}}]
        })


# ---------------------------------------------------------------------------
# maxLength constraints
# ---------------------------------------------------------------------------

def test_method_maxlength_accepted(validator):
    """method up to 100 chars is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320, "method": "H" * 100}]
    })


def test_method_maxlength_exceeded(validator):
    """method over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "method": "H" * 101}]
        })


def test_process_notes_maxlength_accepted(validator):
    """process_notes up to 2000 chars is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320, "process_notes": "N" * 2000}]
    })


def test_process_notes_maxlength_exceeded(validator):
    """process_notes over 2000 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "process_notes": "N" * 2001}]
        })


def test_coffee_origins_country_maxlength_exceeded(validator):
    """coffee.origins[].country over 100 chars is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320,
                       "coffee": {"origins": [{"country": "O" * 101}]}}]
        })


# ---------------------------------------------------------------------------
# Freeform string minimum length
# ---------------------------------------------------------------------------

def test_freeform_text_fields_not_empty(validator):
    """Optional string fields (method, process_notes) must not be empty strings."""
    base = {"brewspec_version": "1.0", "brews": [dict(VALID_BREW)]}

    for field in ("method", "process_notes"):
        with pytest.raises(ValidationError):
            validator.validate({**base, "brews": [{**base["brews"][0], field: ""}]})


# ---------------------------------------------------------------------------
# additionalProperties: false
# ---------------------------------------------------------------------------

def test_additional_properties_rejected(validator):
    """Schema rejects unknown fields (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320, "unknown_field": "should fail"}]
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
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320, "equipment": {}}]
    })


def test_equipment_grinder_accepted(validator):
    """equipment.grinder is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4"}}]
    })


def test_equipment_brewer_accepted(validator):
    """equipment.brewer is accepted as a freeform string."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320,
                   "equipment": {"brewer": "Hario V60 02"}}]
    })


def test_equipment_both_fields_accepted(validator):
    """equipment with both grinder and brewer passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_g": 320,
                   "equipment": {"grinder": "Comandante C40 MK4", "brewer": "Hario V60 02"}}]
    })


def test_equipment_unknown_field_rejected(validator):
    """equipment with an unrecognised field is rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320,
                       "equipment": {"kettle": "Fellow Stagg EKG"}}]
        })


def test_equipment_grinder_empty_string_rejected(validator):
    """equipment.grinder: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_g": 320,
                       "equipment": {"grinder": ""}}]
        })


def test_equipment_all_four_fields_accepted(validator):
    """equipment with all four fields (grinder, brewer, grinder_setting, notes) passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {
            "grinder": "Comandante C40 MK4",
            "brewer": "Hario V60 02",
            "grinder_setting": 21,
            "notes": "Burrs replaced 2026-01"
        }}]
    })


def test_equipment_unrecognised_field_rejected(validator):
    """equipment with unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"grinder_setting": 21, "colour": "red"}}]
        })


def test_equipment_notes_accepted(validator):
    """equipment.notes: 'Burrs replaced 2026-01' passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {"notes": "Burrs replaced 2026-01"}}]
    })


def test_equipment_notes_empty_string_rejected(validator):
    """equipment.notes: '' fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"notes": ""}}]
        })


def test_equipment_notes_omitted_accepted(validator):
    """equipment.notes omitted passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {"grinder": "Comandante C40"}}]
    })


def test_equipment_notes_maxlength_accepted(validator):
    """equipment.notes: exactly 2000 chars passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "equipment": {"notes": "x" * 2000}}]
    })


def test_equipment_notes_maxlength_exceeded(validator):
    """equipment.notes: 2001 chars fails validation (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "equipment": {"notes": "x" * 2001}}]
        })


# ---------------------------------------------------------------------------
# coffee.origins structured array
# ---------------------------------------------------------------------------

def test_coffee_origin_string_array_rejected(validator):
    """coffee.origin string array is rejected by schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origin": ["Ethiopia"]}}]
        })


def test_coffee_origins_single_entry_accepted(validator):
    """coffee.origins with a single entry passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{
                "country": "Ethiopia",
                "region": "Yirgacheffe",
                "producer": "Daye Bensa",
                "process": "Washed",
                "harvest_year": 2025
            }]
        }}]
    })


def test_coffee_origins_full_ten_fields_accepted(validator):
    """origin object with all ten v0.9 fields passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [{
                "name": "Ethiopia Yirgacheffe Natural",
                "country": "Ethiopia",
                "region": "Yirgacheffe",
                "subregion": "Kochere",
                "producer": "Daye Bensa Washing Station",
                "process": "Natural",
                "lot": "Lot 42 Export Grade 1",
                "harvest_year": 2025,
                "varietal": "Heirloom",
                "elevation_masl": 1950
            }]
        }}]
    })


def test_coffee_origins_blend_two_entries_accepted(validator):
    """coffee.origins with two entries (blend) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {
            "origins": [
                {"name": "Ethiopia component", "country": "Ethiopia", "region": "Yirgacheffe",
                 "process": "Washed", "varietal": "Heirloom"},
                {"name": "Colombia component", "country": "Colombia", "region": "Huila",
                 "process": "Natural", "varietal": "Gesha"}
            ]
        }}]
    })


def test_coffee_origins_empty_object_entry_accepted(validator):
    """origin object with no fields (empty object {}) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"origins": [{}]}}]
    })


def test_coffee_origins_empty_array_rejected_with_valid_brew_base(validator):
    """coffee.origins: [] (empty array) fails validation (minItems: 1) when using VALID_BREW base."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": []}}]
        })


def test_coffee_origins_unrecognised_field_rejected(validator):
    """origin entry with unrecognised field fails (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": [{"altitude": 1800}]}}]
        })


def test_coffee_origins_omitted_accepted(validator):
    """coffee.origins omitted entirely passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"type": "single_origin"}}]
    })


def test_coffee_origins_harvest_year_valid_accepted(validator):
    """harvest_year: 2025 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 2025}]}}]
    })


def test_coffee_origins_harvest_year_min_boundary_accepted(validator):
    """harvest_year: 1900 (minimum boundary) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 1900}]}}]
    })


def test_coffee_origins_harvest_year_max_boundary_accepted(validator):
    """harvest_year: 2100 (maximum boundary) passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 2100}]}}]
    })


def test_coffee_origins_harvest_year_below_min_rejected(validator):
    """harvest_year: 1899 fails validation (minimum: 1900)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 1899}]}}]
        })


def test_coffee_origins_harvest_year_above_max_rejected(validator):
    """harvest_year: 2101 fails validation (maximum: 2100)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 2101}]}}]
        })


def test_coffee_origins_harvest_year_float_rejected(validator):
    """harvest_year: 2025.5 fails validation (type: integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": 2025.5}]}}]
        })


def test_coffee_origins_harvest_year_string_rejected(validator):
    """harvest_year: '2025' (string) fails validation (type: integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "coffee": {"origins": [{"harvest_year": "2025"}]}}]
        })


# ---------------------------------------------------------------------------
# brew_ratio field
# ---------------------------------------------------------------------------

def test_brew_ratio_positive_float_accepted(validator):
    """brew_ratio: 15.5 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "brew_ratio": 15.5}]
    })


def test_brew_ratio_zero_rejected(validator):
    """brew_ratio: 0 fails validation (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "brew_ratio": 0}]
        })


def test_brew_ratio_negative_rejected(validator):
    """brew_ratio: -1 fails validation."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "brew_ratio": -1}]
        })


def test_brew_ratio_string_rejected(validator):
    """brew_ratio: '15.5' (string) fails validation (type: number)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{**VALID_BREW, "brew_ratio": "15.5"}]
        })


# ---------------------------------------------------------------------------
# Example file validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "example_file",
    sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")),
    ids=lambda f: f.name,
)
def test_valid_examples_pass(validator, example_file):
    """AC-14/AC-15/AC-16: All valid example files must pass schema validation.
    Note: light_roast_ethiopian.yaml contains aftertaste: 7 (demonstrates 6-9 range, AC-16)."""
    data = _load_example_file(example_file)
    validator.validate(data)


@pytest.mark.parametrize(
    "example_file",
    sorted(INVALID_DIR.glob("*.yaml")),
    ids=lambda f: f.name,
)
def test_invalid_examples_fail(validator, example_file):
    """All invalid example files must fail schema validation."""
    data = _load_example_file(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# ---------------------------------------------------------------------------
# Specific example file validation
# ---------------------------------------------------------------------------

def test_light_roast_ethiopian_example_passes(validator):
    """AC-16: light_roast_ethiopian.yaml passes validation (contains aftertaste: 7)."""
    path = VALID_DIR / "light_roast_ethiopian.yaml"
    data = _load_yaml_example(path)
    validator.validate(data)


def test_rating_out_of_range_example_fails(validator):
    """AC-13: rating_out_of_range.yaml (value 10) fails validation."""
    path = INVALID_DIR / "rating_out_of_range.yaml"
    data = _load_yaml_example(path)
    with pytest.raises(ValidationError):
        validator.validate(data)


def test_invalid_roast_level_example_fails(validator):
    """invalid_roast_level.yaml fails validation."""
    path = INVALID_DIR / "invalid_roast_level.yaml"
    data = _load_yaml_example(path)
    with pytest.raises(ValidationError):
        validator.validate(data)


def test_invalid_water_temp_precision_example_fails(validator):
    """invalid_water_temp_precision.yaml fails validation."""
    path = INVALID_DIR / "invalid_water_temp_precision.yaml"
    data = _load_yaml_example(path)
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
        json_data = _load_example_file(json_files[0])
        validator.validate(json_data)


# ---------------------------------------------------------------------------
# result.yield_g — valid cases
# ---------------------------------------------------------------------------

def test_result_yield_g_typical_espresso(validator):
    """result.yield_g: 36.5 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"yield_g": 36.5}}]
    })


def test_result_yield_g_minimum_viable(validator):
    """result.yield_g: 0.1 passes validation."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{**VALID_BREW, "result": {"yield_g": 0.1}}]
    })


# ===========================================================================
# BrewSpec v1.0 Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# AC-1: Version bump — const "1.0", title "BrewSpec v1.0"
# ---------------------------------------------------------------------------

def test_schema_title_is_v1_0(schema):
    """AC-1: Schema title must be 'BrewSpec v1.0'."""
    assert schema["title"] == "BrewSpec v1.0"


def test_version_must_be_1_0(validator):
    """AC-1: brewspec_version '1.0' is required and accepted."""
    BREW_V1 = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_g": 320
    }
    validator.validate({"brewspec_version": "1.0", "brews": [BREW_V1]})


def test_version_1_0_rejects_0_9(validator):
    """AC-1: brewspec_version '0.9' is rejected by the v1.0 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.9", "brews": [{"type": "pour_over"}]})


# ---------------------------------------------------------------------------
# AC-2: brew.water_weight_g removed, brew.water_g and brew.yield_g added
# ---------------------------------------------------------------------------

def test_brew_water_g_accepted(validator):
    """AC-2: brew.water_g is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"water_g": 320}]
    })


def test_brew_water_g_zero_rejected(validator):
    """AC-2: brew.water_g: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"water_g": 0}]
        })


def test_brew_water_g_negative_rejected(validator):
    """AC-2: brew.water_g: -10 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"water_g": -10}]
        })


def test_brew_water_weight_g_rejected(validator):
    """AC-2: brew.water_weight_g is rejected (removed field, additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"water_weight_g": 320}]
        })


def test_brew_yield_g_accepted(validator):
    """AC-2: brew.yield_g is accepted (recipe target yield)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"yield_g": 40}]
    })


def test_brew_yield_g_zero_rejected(validator):
    """AC-2: brew.yield_g: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"yield_g": 0}]
        })


def test_brew_yield_g_negative_rejected(validator):
    """AC-2: brew.yield_g: -5 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"yield_g": -5}]
        })


def test_result_water_g_accepted(validator):
    """AC-2: result.water_g is accepted (actual water used)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"result": {"water_g": 318}}]
    })


def test_result_water_g_zero_rejected(validator):
    """AC-2: result.water_g: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"result": {"water_g": 0}}]
        })


def test_schema_brew_has_water_g(schema):
    """AC-2: $defs/brew/properties must contain water_g."""
    assert "water_g" in schema["$defs"]["brew"]["properties"]


def test_schema_brew_has_yield_g(schema):
    """AC-2: $defs/brew/properties must contain yield_g."""
    assert "yield_g" in schema["$defs"]["brew"]["properties"]


def test_schema_brew_lacks_water_weight_g(schema):
    """AC-2: $defs/brew/properties must NOT contain water_weight_g."""
    assert "water_weight_g" not in schema["$defs"]["brew"]["properties"]


def test_schema_result_has_water_g(schema):
    """AC-2: $defs/result/properties must contain water_g."""
    assert "water_g" in schema["$defs"]["result"]["properties"]


# ---------------------------------------------------------------------------
# AC-3: coffee.name maxLength reduced from 150 to 100
# ---------------------------------------------------------------------------

def test_coffee_name_100_chars_accepted(validator):
    """AC-3: coffee.name: 100 chars passes validation (new maxLength boundary)."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"coffee": {"name": "A" * 100}}]
    })


def test_coffee_name_101_chars_rejected(validator):
    """AC-3: coffee.name: 101 chars fails validation (maxLength now 100)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"coffee": {"name": "A" * 101}}]
        })


def test_coffee_name_150_chars_rejected_v1(validator):
    """AC-3: coffee.name: 150 chars fails under v1.0 (maxLength 150 -> 100, breaking change)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"coffee": {"name": "A" * 150}}]
        })


def test_schema_coffee_name_maxlength_is_100(schema):
    """AC-3: coffee.name maxLength must be 100 in the schema."""
    name = schema["$defs"]["coffee"]["properties"]["name"]
    assert name["maxLength"] == 100


# ---------------------------------------------------------------------------
# AC-4: brew.notes removed, brew.process_notes added
# ---------------------------------------------------------------------------

def test_brew_process_notes_accepted(validator):
    """AC-4: brew.process_notes is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"process_notes": "Washed filter paper first"}]
    })


def test_brew_process_notes_empty_rejected(validator):
    """AC-4: brew.process_notes: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"process_notes": ""}]
        })


def test_brew_process_notes_maxlength_accepted(validator):
    """AC-4: brew.process_notes: 2000 chars passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"process_notes": "x" * 2000}]
    })


def test_brew_process_notes_maxlength_exceeded(validator):
    """AC-4: brew.process_notes: 2001 chars fails (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"process_notes": "x" * 2001}]
        })


def test_brew_notes_rejected_v1(validator):
    """AC-4: brew.notes is rejected in v1.0 (removed field, additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"notes": "Old field should fail"}]
        })


def test_coffee_cupping_notes_accepted(validator):
    """AC-4: coffee.cupping_notes is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"coffee": {"cupping_notes": "Blueberry, jasmine"}}]
    })


def test_coffee_cupping_notes_empty_rejected(validator):
    """AC-4: coffee.cupping_notes: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"coffee": {"cupping_notes": ""}}]
        })


def test_coffee_cupping_notes_maxlength_accepted(validator):
    """AC-4: coffee.cupping_notes: 2000 chars passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"coffee": {"cupping_notes": "x" * 2000}}]
    })


def test_coffee_cupping_notes_maxlength_exceeded(validator):
    """AC-4: coffee.cupping_notes: 2001 chars fails (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"coffee": {"cupping_notes": "x" * 2001}}]
        })


def test_origin_cupping_notes_accepted(validator):
    """AC-4: origin.cupping_notes is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"coffee": {"origins": [{"cupping_notes": "Citrus and honey"}]}}]
    })


def test_origin_cupping_notes_empty_rejected(validator):
    """AC-4: origin.cupping_notes: '' is rejected (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"coffee": {"origins": [{"cupping_notes": ""}]}}]
        })


def test_schema_brew_has_process_notes(schema):
    """AC-4: $defs/brew/properties must contain process_notes."""
    assert "process_notes" in schema["$defs"]["brew"]["properties"]


def test_schema_brew_lacks_notes(schema):
    """AC-4: $defs/brew/properties must NOT contain notes."""
    assert "notes" not in schema["$defs"]["brew"]["properties"]


def test_schema_coffee_has_cupping_notes(schema):
    """AC-4: $defs/coffee/properties must contain cupping_notes."""
    assert "cupping_notes" in schema["$defs"]["coffee"]["properties"]


def test_schema_origin_has_cupping_notes(schema):
    """AC-4: $defs/origin/properties must contain cupping_notes."""
    assert "cupping_notes" in schema["$defs"]["origin"]["properties"]


# ---------------------------------------------------------------------------
# AC-5: equipment.pressure_bar and equipment.flow_rate_ml_s added
# ---------------------------------------------------------------------------

def test_equipment_pressure_bar_accepted(validator):
    """AC-5: equipment.pressure_bar is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"equipment": {"pressure_bar": 9.0}}]
    })


def test_equipment_pressure_bar_zero_rejected(validator):
    """AC-5: equipment.pressure_bar: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"pressure_bar": 0}}]
        })


def test_equipment_pressure_bar_negative_rejected(validator):
    """AC-5: equipment.pressure_bar: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"pressure_bar": -1}}]
        })


def test_equipment_pressure_bar_string_rejected(validator):
    """AC-5: equipment.pressure_bar: '9' (string) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"pressure_bar": "9"}}]
        })


def test_equipment_flow_rate_ml_s_accepted(validator):
    """AC-5: equipment.flow_rate_ml_s is accepted."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"equipment": {"flow_rate_ml_s": 2.5}}]
    })


def test_equipment_flow_rate_ml_s_zero_rejected(validator):
    """AC-5: equipment.flow_rate_ml_s: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"flow_rate_ml_s": 0}}]
        })


def test_equipment_flow_rate_ml_s_negative_rejected(validator):
    """AC-5: equipment.flow_rate_ml_s: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"flow_rate_ml_s": -1}}]
        })


def test_equipment_flow_rate_ml_s_string_rejected(validator):
    """AC-5: equipment.flow_rate_ml_s: '2.5' (string) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"equipment": {"flow_rate_ml_s": "2.5"}}]
        })


def test_equipment_all_v1_fields_accepted(validator):
    """AC-5: equipment with all v1.0 fields (grinder, brewer, grinder_setting, notes, pressure_bar, flow_rate_ml_s) passes."""
    validator.validate({
        "brewspec_version": "1.0",
        "brews": [{"equipment": {
            "grinder": "Comandante C40 MK4",
            "brewer": "Hario V60 02",
            "grinder_setting": 21,
            "notes": "Burrs replaced 2026-01",
            "pressure_bar": 9.0,
            "flow_rate_ml_s": 2.5
        }}]
    })


def test_schema_equipment_has_pressure_bar(schema):
    """AC-5: $defs/equipment/properties must contain pressure_bar."""
    assert "pressure_bar" in schema["$defs"]["equipment"]["properties"]


def test_schema_equipment_has_flow_rate_ml_s(schema):
    """AC-5: $defs/equipment/properties must contain flow_rate_ml_s."""
    assert "flow_rate_ml_s" in schema["$defs"]["equipment"]["properties"]


# ---------------------------------------------------------------------------
# v1.0 Example file tests
# ---------------------------------------------------------------------------

def test_espresso_full_symmetry_example_passes(validator):
    """AC-36: examples/valid/espresso_full_symmetry.yaml passes validation."""
    path = VALID_DIR / "espresso_full_symmetry.yaml"
    data = _load_yaml_example(path)
    validator.validate(data)


def test_pour_over_cupping_notes_example_passes(validator):
    """AC-37: examples/valid/pour_over_cupping_notes.yaml passes validation."""
    path = VALID_DIR / "pour_over_cupping_notes.yaml"
    data = _load_yaml_example(path)
    validator.validate(data)


def test_invalid_water_weight_g_example_fails(validator):
    """AC-38: examples/invalid/invalid_water_weight_g.yaml fails validation."""
    path = INVALID_DIR / "invalid_water_weight_g.yaml"
    data = _load_yaml_example(path)
    with pytest.raises(ValidationError):
        validator.validate(data)


def test_invalid_brew_notes_example_fails(validator):
    """AC-39: examples/invalid/invalid_brew_notes.yaml fails validation."""
    path = INVALID_DIR / "invalid_brew_notes.yaml"
    data = _load_yaml_example(path)
    with pytest.raises(ValidationError):
        validator.validate(data)
