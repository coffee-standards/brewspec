"""
Test suite for the BrewSpec schema bundled inside the brewlog package.

The bundled schema is at src/brewlog/brewspec.schema.json and must be v0.4.
Tests validate that the bundled schema correctly accepts valid v0.4 documents
and rejects invalid ones.
"""

import json
import yaml
import pytest
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.validators import validator_for

# Paths
BREWLOG_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = BREWLOG_ROOT / "src" / "brewlog" / "brewspec.schema.json"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_EXAMPLES = sorted(FIXTURES_DIR.glob("valid_*.yaml")) + sorted(FIXTURES_DIR.glob("valid_*.json"))
INVALID_EXAMPLES = sorted(FIXTURES_DIR.glob("invalid_*.yaml"))


@pytest.fixture
def schema():
    """Load the bundled BrewSpec JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def validator(schema):
    """Create a Draft 2020-12 validator for the bundled schema."""
    return Draft202012Validator(schema)


# ---------------------------------------------------------------------------
# Minimal valid v0.4 brew dict reused across tests
# ---------------------------------------------------------------------------

VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.4", "brews": [VALID_BREW]}


# ---------------------------------------------------------------------------
# Meta-validation: schema is itself valid
# ---------------------------------------------------------------------------

def test_schema_is_valid_draft_2020_12(schema):
    """Verify the bundled schema is valid JSON Schema Draft 2020-12."""
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_bundled_schema_is_v0_4(schema):
    """Bundled schema must declare version 0.4."""
    assert schema["title"] == "BrewSpec v0.4"


# ---------------------------------------------------------------------------
# Version const
# ---------------------------------------------------------------------------

def test_version_must_be_0_4(validator):
    """brewspec_version is required and must be exactly '0.4'. Other values rejected."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({"brews": [VALID_BREW]})

    # Wrong version — 0.3 is now rejected
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.3", "brews": [VALID_BREW]})

    # Wrong version — 1.0
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "1.0", "brews": [VALID_BREW]})

    # Correct version
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_3(validator):
    """brewspec_version '0.3' is rejected by the v0.4 schema (const: '0.4')."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.3", "brews": [VALID_BREW]})


def test_version_const_rejects_v0_2(validator):
    """brewspec_version '0.2' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.2", "brews": [VALID_BREW]})


# ---------------------------------------------------------------------------
# brews array constraint
# ---------------------------------------------------------------------------

def test_brews_must_be_nonempty_array(validator):
    """brews is required and must be an array with minimum 1 element."""
    # Missing brews
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.4"})

    # Empty array
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.4", "brews": []})

    # Valid single-element array
    validator.validate(VALID_DOC)


# ---------------------------------------------------------------------------
# Required brew fields
# ---------------------------------------------------------------------------

def test_required_brew_fields(validator):
    """Each brew must have date, type, dose_g, water_weight_g."""
    base = {"brewspec_version": "0.4"}

    # Missing date
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{"type": "pour_over", "dose_g": 20, "water_weight_g": 320}]
        })

    # Missing type
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{"date": "2026-02-15T08:30:00Z", "dose_g": 20, "water_weight_g": 320}]
        })

    # Missing dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "water_weight_g": 320}]
        })

    # Missing water_weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over", "dose_g": 20}]
        })

    # All required fields present
    validator.validate({**base, "brews": [VALID_BREW]})


# ---------------------------------------------------------------------------
# Date format: dual-format (datetime or date-only)
# ---------------------------------------------------------------------------

def test_date_full_datetime_accepted(validator):
    """Full UTC datetime YYYY-MM-DDTHH:MM:SSZ is accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-15T08:30:00Z"}]
    })


def test_date_only_accepted(validator):
    """Date-only YYYY-MM-DD is accepted in v0.4."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-15"}]
    })


def test_date_invalid_formats_rejected(validator):
    """Invalid date strings are rejected."""
    invalid_dates = [
        "2026-02-15T08:30:00",        # missing Z
        "2026-02-15T08:30:00+00:00",  # timezone offset instead of Z
        "15-02-2026T08:30:00Z",       # wrong order
        "not-a-date",                 # random string
        "2026/02/15",                 # wrong separator
    ]
    for invalid_date in invalid_dates:
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, "date": invalid_date}]
            })


# ---------------------------------------------------------------------------
# Grind: enum values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse",
])
def test_grind_enum_values_accepted(validator, grind_value):
    """All 7 grind enum values are accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "grind": grind_value}]
    })


def test_grind_freeform_rejected(validator):
    """Freeform grind value rejected — grind is enum in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "setting 15"}]
        })


def test_grind_old_hyphenated_rejected(validator):
    """Old hyphenated value 'medium-fine' is rejected in v0.4 (enum uses underscores)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "medium-fine"}]
        })


def test_grind_wrong_case_rejected(validator):
    """Uppercase grind value rejected (enum is lowercase)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "MEDIUM"}]
        })


# ---------------------------------------------------------------------------
# result object
# ---------------------------------------------------------------------------

def test_result_object_accepted(validator):
    """result object with valid fields is accepted."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{
            **VALID_BREW,
            "result": {"tds": 1.38, "ey": 20.5, "brix": 1.5}
        }]
    })


def test_result_tds_valid(validator):
    """result.tds with positive value passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tds": 1.38}}]
    })


def test_result_tds_zero_rejected(validator):
    """result.tds: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tds": 0}}]
        })


def test_result_tds_negative_rejected(validator):
    """result.tds: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tds": -1}}]
        })


def test_result_ey_valid(validator):
    """result.ey with positive value passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ey": 20.1}}]
    })


def test_result_ey_zero_rejected(validator):
    """result.ey: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ey": 0}}]
        })


def test_result_ey_negative_rejected(validator):
    """result.ey: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ey": -1}}]
        })


def test_result_brix_valid(validator):
    """result.brix with non-negative value passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 0}}]
    })
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 1.5}}]
    })


def test_result_brix_negative_rejected(validator):
    """result.brix: -1 is rejected (minimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"brix": -1}}]
        })


def test_result_tasting_notes_valid(validator):
    """result.tasting_notes non-empty string passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "Dark chocolate"}}]
    })


def test_result_tasting_notes_empty_rejected(validator):
    """result.tasting_notes empty string rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": ""}}]
        })


def test_result_unknown_field_rejected(validator):
    """result with unknown field rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"unknown": "bad"}}]
        })


# ---------------------------------------------------------------------------
# ratings object (inside result)
# ---------------------------------------------------------------------------

def test_ratings_all_dimensions_accepted(validator):
    """ratings object with all 8 SCA dimensions passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{
            **VALID_BREW,
            "result": {
                "ratings": {
                    "overall": 4,
                    "fragrance": 3,
                    "aroma": 4,
                    "flavour": 5,
                    "aftertaste": 3,
                    "acidity": 4,
                    "sweetness": 5,
                    "mouthfeel": 4,
                }
            }
        }]
    })


@pytest.mark.parametrize("dim", [
    "overall", "fragrance", "aroma", "flavour",
    "aftertaste", "acidity", "sweetness", "mouthfeel",
])
def test_ratings_dimension_range_1_to_5(validator, dim):
    """Each ratings dimension accepts 1-5; rejects 0 and 6."""
    for valid_val in [1, 2, 3, 4, 5]:
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {dim: valid_val}}}]
        })
    for invalid_val in [0, 6, -1]:
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, "result": {"ratings": {dim: invalid_val}}}]
            })


def test_ratings_unknown_field_rejected(validator):
    """ratings with unknown field rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"style": 4}}}]
        })


# ---------------------------------------------------------------------------
# Flat tds/ey/rating at brew level rejected in v0.4
# ---------------------------------------------------------------------------

def test_flat_tds_at_brew_level_rejected(validator):
    """tds directly on brew (not inside result) is rejected in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "tds": 1.38}]
        })


def test_flat_ey_at_brew_level_rejected(validator):
    """ey directly on brew (not inside result) is rejected in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "ey": 20.5}]
        })


def test_flat_rating_at_brew_level_rejected(validator):
    """rating directly on brew (not inside result.ratings) is rejected in v0.4."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "rating": 4}]
        })


# ---------------------------------------------------------------------------
# Optional fields accepted
# ---------------------------------------------------------------------------

def test_optional_brew_fields_accepted(validator):
    """Optional brew-level fields are accepted when valid."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{
            **VALID_BREW,
            "method": "Hario V60",
            "water_volume_ml": 320,
            "water_temp_c": 96,
            "grind": "medium_fine",
            "duration_s": 180,
            "notes": "Bright acidity, slightly under-extracted",
        }]
    })


def test_minimal_brew_passes(validator):
    """Brew with only required fields should pass."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "immersion",
                   "dose_g": 30, "water_weight_g": 500}]
    })


# ---------------------------------------------------------------------------
# Numeric constraints
# ---------------------------------------------------------------------------

def test_negative_values_rejected(validator):
    """Negative values for dose_g, water_weight_g, water_volume_ml, duration_s rejected."""
    for field, value in [
        ("dose_g", -10), ("water_weight_g", -320),
        ("water_volume_ml", -100), ("duration_s", -30),
    ]:
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, field: value}]
            })


def test_zero_weight_rejected(validator):
    """Zero values for dose_g and water_weight_g rejected (exclusive minimum)."""
    for field in ("dose_g", "water_weight_g"):
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, field: 0}]
            })


def test_temperature_range(validator):
    """water_temp_c must be between 0 and 100 inclusive."""
    for invalid_temp in [-1, 101]:
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, "water_temp_c": invalid_temp}]
            })
    for valid_temp in [0, 50, 100]:
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "water_temp_c": valid_temp}]
        })


# ---------------------------------------------------------------------------
# Type enumeration
# ---------------------------------------------------------------------------

def test_type_enum_validation(validator):
    """type must be one of: immersion, pour_over, espresso, hybrid."""
    for invalid_type in ["drip", "aeropress", "cold_brew"]:
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, "type": invalid_type}]
            })
    for valid_type in ["immersion", "pour_over", "espresso", "hybrid"]:
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "type": valid_type}]
        })


# ---------------------------------------------------------------------------
# Freeform text fields
# ---------------------------------------------------------------------------

def test_freeform_text_fields_not_empty(validator):
    """Optional string fields (method, notes) must not be empty strings."""
    for field in ("method", "notes"):
        with pytest.raises(ValidationError):
            validator.validate({
                "brewspec_version": "0.4",
                "brews": [{**VALID_BREW, field: ""}]
            })


def test_method_maxlength_boundary(validator):
    """method: 100 chars passes; 101 chars fails (maxLength: 100)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "method": "x" * 100}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "method": "x" * 101}]
        })


def test_notes_maxlength_boundary(validator):
    """notes: 2000 chars passes; 2001 chars fails (maxLength: 2000)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "notes": "x" * 2000}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "notes": "x" * 2001}]
        })


# ---------------------------------------------------------------------------
# additionalProperties enforcement
# ---------------------------------------------------------------------------

def test_additional_properties_rejected(validator):
    """Unknown fields at brew level rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "unknown_field": "should fail"}]
        })


# ---------------------------------------------------------------------------
# Equipment object
# ---------------------------------------------------------------------------

def test_equipment_both_fields_accepted(validator):
    """equipment with both grinder and brewer passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "equipment": {
            "grinder": "Comandante C40 MK4", "brewer": "Hario V60 02"
        }}]
    })


def test_equipment_grinder_only_accepted(validator):
    """equipment with only grinder passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "equipment": {"grinder": "Niche Zero"}}]
    })


def test_equipment_brewer_only_accepted(validator):
    """equipment with only brewer passes."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "equipment": {"brewer": "French Press"}}]
    })


def test_equipment_empty_object_accepted(validator):
    """equipment: {} (empty object) passes (no fields required inside)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "equipment": {}}]
    })


def test_equipment_unknown_field_rejected(validator):
    """equipment with unrecognised field rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "equipment": {"kettle": "Fellow Stagg EKG"}}]
        })


# ---------------------------------------------------------------------------
# Fixture file validation
# ---------------------------------------------------------------------------

def _load_example(filepath):
    """Load a YAML or JSON fixture file."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text())
    return yaml.safe_load(filepath.read_text())


@pytest.mark.parametrize("example_file", VALID_EXAMPLES)
def test_valid_fixtures_pass(validator, example_file):
    """All valid fixture files must pass schema validation."""
    data = _load_example(example_file)
    validator.validate(data)


@pytest.mark.parametrize("example_file", INVALID_EXAMPLES)
def test_invalid_fixtures_fail(validator, example_file):
    """All invalid fixture files must fail schema validation."""
    data = _load_example(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# ---------------------------------------------------------------------------
# Format-agnostic validation
# ---------------------------------------------------------------------------

def test_json_format_supported(validator):
    """Schema validation works on JSON-parsed data."""
    validator.validate(VALID_DOC)
    json_files = [f for f in VALID_EXAMPLES if f.suffix == ".json"]
    if json_files:
        json_data = _load_example(json_files[0])
        validator.validate(json_data)
