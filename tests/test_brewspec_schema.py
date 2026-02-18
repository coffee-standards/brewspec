"""
Test suite for BrewSpec v0.1

This test suite validates the BrewSpec JSON Schema against example files.
Tests are organized by acceptance criteria from specs/products/brewspec.md
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


@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def validator(schema):
    """Create a Draft 2020-12 validator for the BrewSpec schema."""
    return Draft202012Validator(schema)


# Meta-validation
# AC-1: JSON Schema file exists and is valid

def test_schema_is_valid_draft_2020_12(schema):
    """AC-1: Verify the schema itself is valid JSON Schema Draft 2020-12."""
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


# Required field tests
# AC-2: brewspec_version must be "0.1"

def test_version_must_be_0_1(validator):
    """AC-2: brewspec_version is required and must be exactly '0.1'."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                      "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
        })

    # Wrong version
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                      "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
        })

    # Correct version
    validator.validate({
        "brewspec_version": "0.1",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                  "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
    })


# AC-3: brews must be a non-empty array

def test_brews_must_be_nonempty_array(validator):
    """AC-3: brews is required and must be an array with minimum 1 element."""
    # Missing brews
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.1"})

    # Empty array
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.1",
            "brews": []
        })

    # Valid single-element array
    validator.validate({
        "brewspec_version": "0.1",
        "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                  "coffee": {"dose_g": 20}, "water": {"weight_g": 320}}]
    })


# AC-4: Required brew fields

def test_required_brew_fields(validator):
    """AC-4: Each brew must have date, type, coffee, water."""
    base = {"brewspec_version": "0.1"}

    # Missing date
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "type": "pour_over",
                "coffee": {"dose_g": 20},
                "water": {"weight_g": 320}
            }]
        })

    # Missing type
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "coffee": {"dose_g": 20},
                "water": {"weight_g": 320}
            }]
        })

    # Missing coffee
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "water": {"weight_g": 320}
            }]
        })

    # Missing water
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "coffee": {"dose_g": 20}
            }]
        })

    # All required fields present
    validator.validate({
        **base,
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    })


def test_required_coffee_fields(validator):
    """AC-4: coffee.dose_g is required and must be > 0."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "water": {"weight_g": 320}
        }]
    }

    # Missing dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "coffee": {}
            }]
        })


def test_required_water_fields(validator):
    """AC-4: water.weight_g is required and must be > 0."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20}
        }]
    }

    # Missing weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {}
            }]
        })


def test_date_format_iso8601(validator):
    """AC-4: date must be ISO 8601 format YYYY-MM-DDTHH:MM:SSZ."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

    # Invalid formats
    invalid_dates = [
        "2026-02-15",  # Date only
        "2026-02-15T08:30:00",  # Missing Z
        "2026-02-15T08:30:00+00:00",  # Timezone offset instead of Z
        "15-02-2026T08:30:00Z",  # Wrong order
        "not-a-date",  # Random string
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


# AC-5: Optional fields

def test_optional_fields_accepted(validator):
    """AC-5: All optional fields should be accepted when valid."""
    validator.validate({
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "method": "Hario V60",
            "coffee": {"dose_g": 20},
            "water": {
                "weight_g": 320,
                "volume_ml": 320,
                "temp_c": 96
            },
            "grind": "medium-fine",
            "duration_s": 180,
            "rating": 4,
            "notes": "Bright acidity, slightly under-extracted"
        }]
    })


def test_minimal_brew_passes(validator):
    """AC-5: Brew with only required fields should pass."""
    validator.validate({
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "immersion",
            "coffee": {"dose_g": 30},
            "water": {"weight_g": 500}
        }]
    })


# AC-6: Rating constraints

def test_rating_range_1_to_5(validator):
    """AC-6: rating must be an integer between 1 and 5 inclusive."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

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
    """AC-7: Negative values for dose_g, weight_g, volume_ml, duration_s must be rejected."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

    # Negative dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "coffee": {"dose_g": -10}
            }]
        })

    # Negative weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": -320}
            }]
        })

    # Negative volume_ml
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": 320, "volume_ml": -100}
            }]
        })

    # Negative duration_s
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{**base["brews"][0], "duration_s": -30}]
        })


def test_zero_weight_rejected(validator):
    """AC-7: Zero values for dose_g and weight_g must be rejected (exclusive minimum)."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

    # Zero dose_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "coffee": {"dose_g": 0}
            }]
        })

    # Zero weight_g
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": 0}
            }]
        })


def test_zero_duration_accepted(validator):
    """AC-7: duration_s can be 0 (valid for instant methods)."""
    validator.validate({
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "espresso",
            "coffee": {"dose_g": 18},
            "water": {"weight_g": 36},
            "duration_s": 0
        }]
    })


def test_temperature_range(validator):
    """AC-5: temp_c must be between 0 and 100."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

    # Below range
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": 320, "temp_c": -1}
            }]
        })

    # Above range
    with pytest.raises(ValidationError):
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": 320, "temp_c": 101}
            }]
        })

    # Valid boundary values
    for temp in [0, 50, 100]:
        validator.validate({
            **base,
            "brews": [{
                **base["brews"][0],
                "water": {"weight_g": 320, "temp_c": temp}
            }]
        })


# AC-8: Type enumeration

def test_type_enum_validation(validator):
    """AC-8: type must be one of: immersion, pour_over, espresso, hybrid."""
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
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


# AC-9, AC-10, AC-11: Example file validation

def load_example_file(filepath):
    """Load a YAML or JSON example file."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text())
    else:  # .yaml or .yml
        return yaml.safe_load(filepath.read_text())


@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")))
def test_valid_examples_pass(validator, example_file):
    """AC-9, AC-11: All valid example files must pass schema validation."""
    data = load_example_file(example_file)
    validator.validate(data)  # Raises ValidationError if invalid


@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")))
def test_invalid_examples_fail(validator, example_file):
    """AC-10, AC-11: All invalid example files must fail schema validation."""
    data = load_example_file(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# AC-15: Format-agnostic validation (JSON and YAML)

def test_json_format_supported(validator):
    """AC-15: Schema must support both YAML and JSON formats."""
    # Create a valid brew as a Python dict
    brew_data = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
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
    base = {
        "brewspec_version": "0.1",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "coffee": {"dose_g": 20},
            "water": {"weight_g": 320}
        }]
    }

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
            "brewspec_version": "0.1",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "coffee": {"dose_g": 20},
                "water": {"weight_g": 320},
                "unknown_field": "should fail"
            }]
        })
