"""
Test suite for BrewSpec v0.2

This test suite validates the BrewSpec JSON Schema against example files.
Tests are organized by acceptance criteria from specs/products/brewspec-v0.2.md
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

# Minimal valid v0.2 brew dict used across tests
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.2", "brews": [VALID_BREW]}


@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def validator(schema):
    """Create a Draft 2020-12 validator for the BrewSpec schema."""
    return Draft202012Validator(schema)


# Meta-validation
# AC-6: JSON Schema file exists and is valid Draft 2020-12

def test_schema_is_valid_draft_2020_12(schema):
    """AC-6: Verify the schema itself is valid JSON Schema Draft 2020-12."""
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


# AC-5: brewspec_version must be "0.2"

def test_version_must_be_0_2(validator):
    """AC-5: brewspec_version is required and must be exactly '0.2'."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({
            "brews": [VALID_BREW]
        })

    # Wrong version
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [VALID_BREW]
        })

    # Correct version
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_1(validator):
    """AC-5: brewspec_version '0.1' is rejected by the v0.2 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.1",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320}]
        })


# AC-3: brews must be a non-empty array

def test_brews_must_be_nonempty_array(validator):
    """AC-3: brews is required and must be an array with minimum 1 element."""
    # Missing brews
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.2"})

    # Empty array
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": []
        })

    # Valid single-element array
    validator.validate(VALID_DOC)


# Required brew fields

def test_required_brew_fields(validator):
    """AC-7, AC-8: Each brew must have date, type, dose_g, water_weight_g."""
    base = {"brewspec_version": "0.2"}

    # Missing date
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320
            }]
        })

    # Missing type
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "dose_g": 20,
                "water_weight_g": 320
            }]
        })

    # Missing dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "water_weight_g": 320
            }]
        })

    # Missing water_weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20
            }]
        })

    # All required fields present
    validator.validate({
        **base,
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    })


def test_dose_g_required_at_brew_level(validator):
    """AC-7: dose_g is required at the brew level."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "water_weight_g": 320
            }]
        })


def test_water_weight_g_required_at_brew_level(validator):
    """AC-8: water_weight_g is required at the brew level."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20
            }]
        })


def test_date_format_iso8601(validator):
    """AC-3: date must be ISO 8601 format YYYY-MM-DDTHH:MM:SSZ."""
    base = {
        "brewspec_version": "0.2",
        "brews": [{
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

    # Invalid formats
    invalid_dates = [
        "2026-02-15",           # Date only
        "2026-02-15T08:30:00",  # Missing Z
        "2026-02-15T08:30:00+00:00",  # Timezone offset instead of Z
        "15-02-2026T08:30:00Z", # Wrong order
        "not-a-date",           # Random string
    ]

    for invalid_date in invalid_dates:
        with pytest.raises(ValidationError):
            validator.validate({
                **base,
                "brews": [{**base["brews"][0], "date": invalid_date}]
            })

    # Valid format
    validator.validate({
        **base,
        "brews": [{**base["brews"][0], "date": "2026-02-15T08:30:00Z"}]
    })


# AC-9, AC-10: coffee and water objects are optional

def test_coffee_object_optional(validator):
    """AC-9: A brew with no coffee object passes validation."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320}]
    })


def test_water_object_optional(validator):
    """AC-10: A brew with no water object passes validation."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                   "dose_g": 20, "water_weight_g": 320}]
    })


# AC-5: Optional fields

def test_optional_fields_accepted(validator):
    """AC-5: All optional fields should be accepted when valid."""
    validator.validate({
        "brewspec_version": "0.2",
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
            "water": {
                "ppm": 150
            },
            "grind": "medium-fine",
            "duration_s": 180,
            "tds": 1.38,
            "rating": 4,
            "notes": "Bright acidity, slightly under-extracted"
        }]
    })


def test_minimal_brew_passes(validator):
    """AC-5: Brew with only required fields should pass."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "immersion",
            "dose_g": 30,
            "water_weight_g": 500
        }]
    })


# AC-6: Rating constraints

def test_rating_range_1_to_5(validator):
    """AC-6: rating must be an integer between 1 and 5 inclusive."""
    base = {"brewspec_version": "0.2", "brews": [dict(VALID_BREW)]}

    # Invalid ratings
    invalid_ratings = [0, 6, -1, 3.5]
    for invalid_rating in invalid_ratings:
        with pytest.raises(ValidationError):
            validator.validate({
                **base,
                "brews": [{**base["brews"][0], "rating": invalid_rating}]
            })

    # Valid ratings
    for valid_rating in [1, 2, 3, 4, 5]:
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "rating": valid_rating}]
        })


# AC-7: Numeric constraints

def test_negative_values_rejected(validator):
    """AC-7, AC-8: Negative values for dose_g, water_weight_g, water_volume_ml, duration_s must be rejected."""
    base = {"brewspec_version": "0.2", "brews": [dict(VALID_BREW)]}

    # Negative dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "dose_g": -10}]
        })

    # Negative water_weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_weight_g": -320}]
        })

    # Negative water_volume_ml
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_volume_ml": -100}]
        })

    # Negative duration_s
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "duration_s": -30}]
        })


def test_zero_weight_rejected(validator):
    """AC-7, AC-8: Zero values for dose_g and water_weight_g must be rejected (exclusive minimum)."""
    base = {"brewspec_version": "0.2", "brews": [dict(VALID_BREW)]}

    # Zero dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "dose_g": 0}]
        })

    # Zero water_weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_weight_g": 0}]
        })


# AC-14: duration_s correction — exclusiveMinimum: 0

def test_zero_duration_rejected(validator):
    """AC-14: duration_s: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                       "dose_g": 18, "water_weight_g": 36, "duration_s": 0}]
        })


def test_positive_duration_accepted(validator):
    """AC-14: duration_s: 1 is accepted (exclusiveMinimum: 0)."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "espresso",
                   "dose_g": 18, "water_weight_g": 36, "duration_s": 1}]
    })


# AC-8: water_temp_c range

def test_temperature_range(validator):
    """AC-8: water_temp_c must be between 0 and 100."""
    base = {"brewspec_version": "0.2", "brews": [dict(VALID_BREW)]}

    # Below range
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_temp_c": -1}]
        })

    # Above range
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_temp_c": 101}]
        })

    # Valid boundary values
    for temp in [0, 50, 100]:
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "water_temp_c": temp}]
        })


# AC-8: Type enumeration

def test_type_enum_validation(validator):
    """AC-8: type must be one of: immersion, pour_over, espresso, hybrid."""
    base = {
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

    # Invalid types
    invalid_types = ["drip", "aeropress", "cold_brew", "turkish"]
    for invalid_type in invalid_types:
        with pytest.raises(ValidationError):
            validator.validate({
                **base,
                "brews": [{**base["brews"][0], "type": invalid_type}]
            })

    # Valid types
    valid_types = ["immersion", "pour_over", "espresso", "hybrid"]
    for valid_type in valid_types:
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "type": valid_type}]
        })


# AC-11: Coffee metadata fields

def test_coffee_origin_multi_entry_accepted(validator):
    """AC-11, AC-25: coffee.origin with multiple entries is valid."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "hybrid",
            "dose_g": 15,
            "water_weight_g": 200,
            "coffee": {"type": "blend", "origin": ["Ethiopia", "Colombia"]}
        }]
    })


def test_coffee_origin_empty_array_rejected(validator):
    """AC-11, AC-25: coffee.origin: [] (empty array) is rejected (minItems: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "coffee": {"origin": []}
            }]
        })


def test_coffee_type_enum_valid(validator):
    """AC-11: coffee.type accepts 'single_origin' and 'blend'."""
    for valid_coffee_type in ["single_origin", "blend"]:
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "coffee": {"type": valid_coffee_type}
            }]
        })


def test_coffee_type_enum_invalid(validator):
    """AC-11, AC-25: coffee.type: 'roast' is rejected (not in enum)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "coffee": {"type": "roast"}
            }]
        })


def test_roast_date_plain_date_accepted(validator):
    """AC-11, AC-25: roast_date in YYYY-MM-DD format is accepted."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "coffee": {"roast_date": "2026-01-20"}
        }]
    })


def test_roast_date_datetime_rejected(validator):
    """AC-11, AC-25: roast_date with time component (ISO datetime) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "coffee": {"roast_date": "2026-01-20T00:00:00Z"}
            }]
        })


# AC-12: water.ppm

def test_water_ppm_zero_accepted(validator):
    """AC-12, AC-25: water.ppm: 0 is accepted (minimum: 0, not exclusive)."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "water": {"ppm": 0}
        }]
    })


def test_water_ppm_negative_rejected(validator):
    """AC-12, AC-25: water.ppm: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "water": {"ppm": -1}
            }]
        })


# AC-13: v0.1 format rejected

def test_v0_1_format_rejected(validator):
    """AC-13, AC-25: v0.1-format file (nested coffee.dose_g, water.weight_g) is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "coffee": {"dose_g": 20},
                "water": {"weight_g": 320}
            }]
        })


# AC-15: tds field

def test_tds_valid_value_accepted(validator):
    """AC-15, AC-25: tds: 1.38 is accepted."""
    validator.validate({
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "tds": 1.38
        }]
    })


def test_tds_zero_rejected(validator):
    """AC-15, AC-25: tds: 0 is rejected (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "tds": 0
            }]
        })


def test_tds_negative_rejected(validator):
    """AC-15, AC-25: tds: -1 is rejected."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "tds": -1
            }]
        })


# AC-9, AC-10, AC-11: Example file validation

def load_example_file(filepath):
    """Load a YAML or JSON example file."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text(encoding="utf-8"))
    else:  # .yaml or .yml
        return yaml.safe_load(filepath.read_text(encoding="utf-8"))


@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")), ids=lambda f: f.name)
def test_valid_examples_pass(validator, example_file):
    """AC-16: All valid example files must pass schema validation."""
    data = load_example_file(example_file)
    validator.validate(data)  # Raises ValidationError if invalid


@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")), ids=lambda f: f.name)
def test_invalid_examples_fail(validator, example_file):
    """AC-21: All invalid example files must fail schema validation."""
    data = load_example_file(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# AC-15: Format-agnostic validation (JSON and YAML)

def test_json_format_supported(validator):
    """AC-15: Schema must support both YAML and JSON formats."""
    # Create a valid brew as a Python dict
    brew_data = {
        "brewspec_version": "0.2",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

    # Validate directly (format-agnostic)
    validator.validate(brew_data)

    # Also verify we can load and validate a JSON file
    json_files = list(VALID_DIR.glob("*.json"))
    if json_files:
        json_data = load_example_file(json_files[0])
        validator.validate(json_data)


def test_freeform_text_fields_not_empty(validator):
    """Optional string fields (method, grind, notes) must not be empty strings."""
    base = {"brewspec_version": "0.2", "brews": [dict(VALID_BREW)]}

    # Empty method
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "method": ""}]
        })

    # Empty grind
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "grind": ""}]
        })

    # Empty notes
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "notes": ""}]
        })


def test_additional_properties_rejected(validator):
    """Schema should reject unknown fields (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "unknown_field": "should fail"
            }]
        })
