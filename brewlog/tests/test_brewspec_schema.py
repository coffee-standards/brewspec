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
SCHEMA_PATH = REPO_ROOT / "brewspec" / "spec" / "brewspec.schema.json"
VALID_DIR = REPO_ROOT / "brewspec" / "spec" / "examples" / "valid"
INVALID_DIR = REPO_ROOT / "brewspec" / "spec" / "examples" / "invalid"


@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def validator(schema):
    """Create a Draft 2020-12 validator for the BrewSpec schema."""
    return Draft202012Validator(schema)


# ---------------------------------------------------------------------------
# Minimal valid v0.3 brew dict reused across tests
# ---------------------------------------------------------------------------

VALID_BREW_V03 = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC_V03 = {"brewspec_version": "0.3", "brews": [VALID_BREW_V03]}


# ---------------------------------------------------------------------------
# Meta-validation: schema is itself valid
# ---------------------------------------------------------------------------

def test_schema_is_valid_draft_2020_12(schema):
    """Verify the schema itself is valid JSON Schema Draft 2020-12."""
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


# ---------------------------------------------------------------------------
# AC-5 / AC-6: Version const
# ---------------------------------------------------------------------------

def test_version_must_be_0_3(validator):
    """brewspec_version is required and must be exactly '0.3'. Other values rejected."""
    # Missing version
    with pytest.raises(ValidationError):
        validator.validate({
            "brews": [VALID_BREW_V03]
        })

    # Wrong version
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "1.0",
            "brews": [VALID_BREW_V03]
        })

    # Correct version
    validator.validate(VALID_DOC_V03)


def test_version_const_rejects_v0_2(validator):
    """brewspec_version: '0.2' is rejected by the v0.3 schema (const: '0.3')."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.2",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320
            }]
        })


# ---------------------------------------------------------------------------
# brews array constraint
# ---------------------------------------------------------------------------

def test_brews_must_be_nonempty_array(validator):
    """brews is required and must be an array with minimum 1 element."""
    # Missing brews
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.3"})

    # Empty array
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": []
        })

    # Valid single-element array
    validator.validate(VALID_DOC_V03)


# ---------------------------------------------------------------------------
# Required brew fields (v0.3: date, type, dose_g, water_weight_g)
# ---------------------------------------------------------------------------

def test_required_brew_fields(validator):
    """Each brew must have date, type, dose_g, water_weight_g."""
    base = {"brewspec_version": "0.3"}

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


# ---------------------------------------------------------------------------
# AC-1 (carry-forward docstring fix): date format
# ---------------------------------------------------------------------------

def test_date_format_iso8601(validator):
    """date must be ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ. Tests valid and invalid date strings."""
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
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


# ---------------------------------------------------------------------------
# AC-2 (carry-forward docstring fix): optional fields
# ---------------------------------------------------------------------------

def test_optional_fields_accepted(validator):
    """Optional brew fields are accepted when valid: method, grind, duration_s, rating, notes, water_temp_c, water_volume_ml."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "method": "Hario V60",
            "water_volume_ml": 320,
            "water_temp_c": 96,
            "grind": "medium-fine",
            "duration_s": 180,
            "rating": 4,
            "notes": "Bright acidity, slightly under-extracted"
        }]
    })


def test_minimal_brew_passes(validator):
    """Brew with only required fields should pass."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "immersion",
            "dose_g": 30,
            "water_weight_g": 500
        }]
    })


# ---------------------------------------------------------------------------
# AC-4 (carry-forward docstring fix): rating constraints
# ---------------------------------------------------------------------------

def test_rating_range_1_to_5(validator):
    """rating must be an integer between 1 and 5 inclusive. Values 0, 6, -1, and 3.5 are rejected."""
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
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


# ---------------------------------------------------------------------------
# Numeric constraints
# ---------------------------------------------------------------------------

def test_negative_values_rejected(validator):
    """Negative values for dose_g, water_weight_g, water_volume_ml, duration_s must be rejected."""
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

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
    """Zero values for dose_g and water_weight_g must be rejected (exclusive minimum)."""
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

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


def test_temperature_range(validator):
    """water_temp_c must be between 0 and 100 inclusive."""
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    }

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


# ---------------------------------------------------------------------------
# Type enumeration
# ---------------------------------------------------------------------------

def test_type_enum_validation(validator):
    """type must be one of: immersion, pour_over, espresso, hybrid."""
    base = {
        "brewspec_version": "0.3",
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


# ---------------------------------------------------------------------------
# Example file validation
# ---------------------------------------------------------------------------

def load_example_file(filepath):
    """Load a YAML or JSON example file."""
    if filepath.suffix == ".json":
        return json.loads(filepath.read_text())
    else:  # .yaml or .yml
        return yaml.safe_load(filepath.read_text())


@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")))
def test_valid_examples_pass(validator, example_file):
    """All valid example files must pass schema validation."""
    data = load_example_file(example_file)
    validator.validate(data)  # Raises ValidationError if invalid


@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")))
def test_invalid_examples_fail(validator, example_file):
    """All invalid example files must fail schema validation."""
    data = load_example_file(example_file)
    with pytest.raises(ValidationError):
        validator.validate(data)


# ---------------------------------------------------------------------------
# AC-3 (carry-forward docstring fix): format-agnostic validation
# ---------------------------------------------------------------------------

def test_json_format_supported(validator):
    """Schema validation is format-agnostic: the same constraints apply whether the source was YAML or JSON."""
    # Create a valid brew as a Python dict (simulating JSON-parsed data)
    brew_data = {
        "brewspec_version": "0.3",
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
    base = {
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
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
            "brewspec_version": "0.3",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "unknown_field": "should fail"
            }]
        })


# ---------------------------------------------------------------------------
# AC-7, AC-8, AC-9, AC-10: equipment object tests
# ---------------------------------------------------------------------------

def test_equipment_both_fields_accepted(validator):
    """equipment object with both grinder and brewer passes validation."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "equipment": {
                "grinder": "Comandante C40 MK4",
                "brewer": "Hario V60 02"
            }
        }]
    })


def test_equipment_grinder_only_accepted(validator):
    """equipment object with only grinder passes validation (brewer is optional)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "espresso",
            "dose_g": 18,
            "water_weight_g": 36,
            "equipment": {"grinder": "Niche Zero"}
        }]
    })


def test_equipment_brewer_only_accepted(validator):
    """equipment object with only brewer passes validation (grinder is optional)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "immersion",
            "dose_g": 30,
            "water_weight_g": 500,
            "equipment": {"brewer": "French Press"}
        }]
    })


def test_equipment_empty_object_accepted(validator):
    """equipment: {} (empty object) passes validation (no fields required inside equipment)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "equipment": {}
        }]
    })


def test_equipment_omitted_accepted(validator):
    """Brew omitting equipment entirely passes validation (equipment is optional)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320
        }]
    })


def test_equipment_unknown_field_rejected(validator):
    """equipment with an unrecognised field is rejected (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "equipment": {"kettle": "Fellow Stagg EKG"}
            }]
        })


# ---------------------------------------------------------------------------
# AC-11, AC-12, AC-13: ey (extraction yield) field tests
# ---------------------------------------------------------------------------

def test_ey_valid_value_accepted(validator):
    """ey: 20.1 passes validation (exclusiveMinimum: 0)."""
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{
            "date": "2026-02-15T08:30:00Z",
            "type": "pour_over",
            "dose_g": 20,
            "water_weight_g": 320,
            "ey": 20.1
        }]
    })


def test_ey_zero_rejected(validator):
    """ey: 0 fails validation (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "ey": 0
            }]
        })


def test_ey_negative_rejected(validator):
    """ey: -1 fails validation (exclusiveMinimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{
                "date": "2026-02-15T08:30:00Z",
                "type": "pour_over",
                "dose_g": 20,
                "water_weight_g": 320,
                "ey": -1
            }]
        })


# ---------------------------------------------------------------------------
# AC-14, AC-15, AC-16: maxLength on brew-level freeform string fields
# ---------------------------------------------------------------------------

def test_method_maxlength_boundary(validator):
    """method: 100 chars passes; 101 chars fails (maxLength: 100)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    # Exactly 100 characters — passes
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "method": "x" * 100}]
    })
    # 101 characters — fails
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "method": "x" * 101}]
        })


def test_grind_maxlength_boundary(validator):
    """grind: 100 chars passes; 101 chars fails (maxLength: 100)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "grind": "x" * 100}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "grind": "x" * 101}]
        })


def test_notes_maxlength_boundary(validator):
    """notes: 2000 chars passes; 2001 chars fails (maxLength: 2000)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "notes": "x" * 2000}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "notes": "x" * 2001}]
        })


# ---------------------------------------------------------------------------
# AC-17, AC-18, AC-19: maxLength on coffee sub-object fields
# ---------------------------------------------------------------------------

def test_coffee_varietal_maxlength_boundary(validator):
    """coffee.varietal: 100 chars passes; 101 chars fails (maxLength: 100)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "coffee": {"varietal": "x" * 100}}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "coffee": {"varietal": "x" * 101}}]
        })


def test_coffee_process_maxlength_boundary(validator):
    """coffee.process: 100 chars passes; 101 chars fails (maxLength: 100)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "coffee": {"process": "x" * 100}}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "coffee": {"process": "x" * 101}}]
        })


def test_coffee_origin_item_maxlength_boundary(validator):
    """coffee.origin items: 100 char item passes; 101 char item fails (maxLength: 100)."""
    base_brew = {
        "date": "2026-02-15T08:30:00Z",
        "type": "pour_over",
        "dose_g": 20,
        "water_weight_g": 320
    }
    validator.validate({
        "brewspec_version": "0.3",
        "brews": [{**base_brew, "coffee": {"origin": ["x" * 100]}}]
    })
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.3",
            "brews": [{**base_brew, "coffee": {"origin": ["x" * 101]}}]
        })
