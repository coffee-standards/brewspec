# Design: BrewSpec v0.1

**Feature:** brewspec-v0.1
**Author:** architect
**Created:** 2026-02-15
**Input:** specs/products/brewspec.md

---

## 1. JSON Schema

Draft 2020-12. Complete schema for `brewspec/spec/brewspec.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://brewspec.org/schema/v0.1/brewspec.schema.json",
  "title": "BrewSpec v0.1",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.1",
      "description": "The BrewSpec spec version. Must be \"0.1\"."
    },
    "brews": {
      "type": "array",
      "description": "Array of brew records. At least one brew is required.",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/brew"
      }
    }
  },
  "$defs": {
    "brew": {
      "type": "object",
      "required": ["date", "type", "coffee", "water"],
      "additionalProperties": false,
      "properties": {
        "date": {
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
          "description": "Brew timestamp in ISO 8601 UTC format.",
          "examples": ["2026-02-15T08:30:00Z"]
        },
        "type": {
          "type": "string",
          "enum": ["immersion", "pour_over", "espresso", "hybrid"],
          "description": "Brew method category."
        },
        "method": {
          "type": "string",
          "minLength": 1,
          "description": "Freeform brewer description.",
          "examples": ["Hario V60", "French press", "AeroPress inverted"]
        },
        "coffee": {
          "$ref": "#/$defs/coffee"
        },
        "water": {
          "$ref": "#/$defs/water"
        },
        "grind": {
          "type": "string",
          "minLength": 1,
          "description": "Freeform grind description.",
          "examples": ["medium-fine", "setting 15 on Comandante"]
        },
        "duration_s": {
          "type": "number",
          "minimum": 0,
          "description": "Brew duration in seconds. Zero is valid for instant methods."
        },
        "rating": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Brew rating. 1 = poor, 5 = excellent."
        },
        "notes": {
          "type": "string",
          "minLength": 1,
          "description": "Freeform tasting or session notes."
        }
      }
    },
    "coffee": {
      "type": "object",
      "required": ["dose_g"],
      "additionalProperties": false,
      "properties": {
        "dose_g": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Coffee dose in grams. Must be > 0."
        }
      }
    },
    "water": {
      "type": "object",
      "required": ["weight_g"],
      "additionalProperties": false,
      "properties": {
        "weight_g": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Water weight in grams. Must be > 0."
        },
        "volume_ml": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Water volume in milliliters. Must be > 0."
        },
        "temp_c": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Water temperature in celsius. Range 0-100."
        }
      }
    }
  }
}
```

### Schema Design Decisions

| Decision | Rationale | Traces to |
|----------|-----------|-----------|
| `const: "0.1"` for version | Exact match prevents cross-version confusion | AC-2 |
| `exclusiveMinimum: 0` for weights | Dose and water must be positive (zero is meaningless) | AC-4, AC-7 |
| `minimum: 0` for duration | Zero valid for instant methods | AC-5 |
| `minimum: 0, maximum: 100` for temp | Physical range for liquid water at standard pressure | AC-5 |
| `integer` for rating | Star ratings are whole numbers | AC-6 |
| `additionalProperties: false` everywhere | Rejects unknown fields, catches typos, enforces spec | Scope discipline |
| `minLength: 1` for freeform strings | Prevents empty strings while keeping freeform | AC-5 |
| ISO 8601 regex pattern for date | Enforces `YYYY-MM-DDTHH:MM:SSZ` format | AC-4 |
| `$defs` for brew, coffee, water | Clean separation, reusable in future versions | Extensibility |

---

## 2. Directory Layout

```
brewspec/spec/
  brewspec.schema.json              # JSON Schema (canonical, machine-readable spec)
  brewspec-v0.1.md                  # Human-readable spec document
  README.md                         # Project overview, validation guide, contribution guidelines
  examples/
    valid/
      pour_over.yaml                # Pour over, all optional fields populated
      immersion_minimal.yaml        # French press, required fields only
      espresso.yaml                 # Espresso with rating and notes
      multi_brew.yaml               # 3 brews in one file
    invalid/
      missing_version.yaml          # Missing brewspec_version
      missing_required_field.yaml   # Brew missing required date field
      invalid_type_enum.yaml        # type: "drip" (not in enum)
      rating_out_of_range.yaml      # rating: 6
      negative_weight.yaml          # dose_g: -10
      empty_brews_array.yaml        # brews: []
tests/
  test_brewspec_schema.py           # Schema validation test suite
```

---

## 3. Example Files

### Valid Examples

**`brewspec/spec/examples/valid/pour_over.yaml`** — All fields populated (AC-4, AC-5)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
      volume_ml: 320
      temp_c: 96
    grind: "medium-fine"
    duration_s: 180
    rating: 4
    notes: "Bright acidity, slightly under-extracted"
```

**`brewspec/spec/examples/valid/immersion_minimal.yaml`** — Required fields only (AC-4)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-14T07:00:00Z"
    type: "immersion"
    coffee:
      dose_g: 30
    water:
      weight_g: 500
```

**`brewspec/spec/examples/valid/espresso.yaml`** — Espresso with rating and notes (AC-4, AC-5, AC-6)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-13T06:45:00Z"
    type: "espresso"
    method: "Breville Barista Express"
    coffee:
      dose_g: 18
    water:
      weight_g: 36
      temp_c: 93
    grind: "fine, setting 5"
    duration_s: 28
    rating: 5
    notes: "Thick crema, balanced sweetness"
```

**`brewspec/spec/examples/valid/multi_brew.yaml`** — Multiple brews in one file (AC-3)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
      temp_c: 96
    rating: 4
  - date: "2026-02-14T07:00:00Z"
    type: "immersion"
    method: "French press"
    coffee:
      dose_g: 30
    water:
      weight_g: 500
    rating: 3
  - date: "2026-02-13T06:45:00Z"
    type: "espresso"
    coffee:
      dose_g: 18
    water:
      weight_g: 36
```

### Invalid Examples

**`brewspec/spec/examples/invalid/missing_version.yaml`** — Missing brewspec_version (AC-2)
```yaml
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
```
Expected error: `'brewspec_version' is a required property`

**`brewspec/spec/examples/invalid/missing_required_field.yaml`** — Brew missing date (AC-4)
```yaml
brewspec_version: "0.1"
brews:
  - type: "pour_over"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
```
Expected error: `'date' is a required property`

**`brewspec/spec/examples/invalid/invalid_type_enum.yaml`** — Invalid type value (AC-8)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "drip"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
```
Expected error: `'drip' is not one of ['immersion', 'pour_over', 'espresso', 'hybrid']`

**`brewspec/spec/examples/invalid/rating_out_of_range.yaml`** — Rating exceeds max (AC-6)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
    rating: 6
```
Expected error: `6 is greater than the maximum of 5`

**`brewspec/spec/examples/invalid/negative_weight.yaml`** — Negative dose (AC-7)
```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: -10
    water:
      weight_g: 320
```
Expected error: `-10 is less than or equal to the minimum of 0`

**`brewspec/spec/examples/invalid/empty_brews_array.yaml`** — Empty array (AC-3)
```yaml
brewspec_version: "0.1"
brews: []
```
Expected error: `[] should be non-empty`

---

## 4. Validation Strategy

### Library
Python `jsonschema` package with `Draft202012Validator`.

### Flow
```
file (YAML or JSON)
  → safe parse (yaml.safe_load or json.load)
  → validate(data, schema) using Draft202012Validator
  → pass or raise ValidationError with field path + reason
```

### Safe Parsing Rules
- **YAML**: Always `yaml.safe_load()`. NEVER `yaml.load()` (allows arbitrary code execution).
- **JSON**: `json.load()` (safe by default).
- **File detection**: By extension (`.yaml`/`.yml` → YAML parser, `.json` → JSON parser).

### Error Reporting
`jsonschema.ValidationError` provides:
- `message`: Human-readable description
- `json_path`: Field path (e.g., `$.brews[0].rating`)
- `validator`: Which constraint failed (e.g., `maximum`)

---

## 5. Test Strategy

### Structure
Single test file: `tests/test_brewspec_schema.py`

### Test Map (Acceptance Criteria → Tests)

| AC | Test | What it verifies |
|----|------|-----------------|
| AC-1 | `test_schema_is_valid_draft_2020_12` | Schema itself passes meta-validation |
| AC-2 | `test_version_must_be_0_1` | Rejects missing version, wrong version |
| AC-3 | `test_brews_must_be_nonempty_array` | Rejects empty array, missing brews |
| AC-4 | `test_required_brew_fields` | Rejects missing date, type, coffee, water |
| AC-4 | `test_required_coffee_fields` | Rejects missing dose_g |
| AC-4 | `test_required_water_fields` | Rejects missing weight_g |
| AC-4 | `test_date_format_iso8601` | Rejects malformed dates |
| AC-5 | `test_optional_fields_accepted` | Valid file with all optional fields passes |
| AC-5 | `test_minimal_brew_passes` | Valid file with only required fields passes |
| AC-6 | `test_rating_range_1_to_5` | Rejects 0, 6, -1, 3.5; accepts 1, 5 |
| AC-7 | `test_negative_values_rejected` | Rejects negative dose_g, weight_g, volume_ml |
| AC-7 | `test_zero_weight_rejected` | Rejects dose_g: 0, weight_g: 0 |
| AC-7 | `test_zero_duration_accepted` | duration_s: 0 is valid |
| AC-8 | `test_type_enum_validation` | Rejects "drip", "aeropress"; accepts all 4 valid types |
| AC-9 | `test_valid_examples_pass` | Parametrized: all files in brewspec/spec/examples/valid/ pass |
| AC-10 | `test_invalid_examples_fail` | Parametrized: all files in brewspec/spec/examples/invalid/ fail |
| AC-11 | (covered by AC-9 + AC-10 tests) | Test suite validates schema against all examples |
| AC-15 | `test_json_format_supported` | Parse a valid JSON file and validate it passes |

### Fixtures

```python
import pytest
import json
import yaml
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("brewspec/spec/brewspec.schema.json")
VALID_DIR = Path("brewspec/spec/examples/valid")
INVALID_DIR = Path("brewspec/spec/examples/invalid")

@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())

@pytest.fixture
def validator(schema):
    return Draft202012Validator(schema)
```

### Parametrized Example Tests

```python
@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")))
def test_valid_examples_pass(validator, example_file):
    data = yaml.safe_load(example_file.read_text())
    validator.validate(data)  # raises on failure

@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")))
def test_invalid_examples_fail(validator, example_file):
    data = yaml.safe_load(example_file.read_text())
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(data)
```

---

## 6. Security Considerations

### Schema as Defense Layer
The JSON Schema is the first validation gate. All input must pass schema validation before any application logic processes it. This rejects malformed, oversized, or unexpected data at the boundary.

### Safe YAML Parsing
- `yaml.safe_load()` only. Never `yaml.load()`.
- `yaml.load()` can instantiate arbitrary Python objects, enabling remote code execution.
- This is the single most important security rule for any tool reading BrewSpec files.

### Freeform Text Safety
- `method`, `grind`, and `notes` are freeform strings.
- Always treat as plain text. Never pass to `eval()`, `exec()`, SQL without parameterization, or shell commands.
- `minLength: 1` prevents empty strings but does not limit length. Tools should enforce max length at the application layer if needed.

### File I/O Safety
- Validate file paths before read/write. Reject paths containing `..` or absolute paths when relative is expected.
- Set a file size limit (recommend 10MB) before parsing to prevent memory exhaustion from huge arrays.
- Handle encoding errors gracefully (expect UTF-8).

### Trust Boundary
```
User input (file)
  → Path validation
  → Size check
  → Safe parser (yaml.safe_load / json.load)
  → Schema validation (Draft202012Validator)
  → Application logic
```

No user data reaches application logic without passing through all four gates.

---

## 7. Spec Document Outline (`brewspec/spec/brewspec-v0.1.md`)

1. **Overview** — What BrewSpec is, mission, version scope
2. **File Format** — YAML/JSON, array-only, UTF-8
3. **Field Reference** — Table: field name, type, required/optional, constraints, description, examples
4. **Enumerations** — `type` enum values with definitions
5. **Validation** — How to validate (JSON Schema, pointer to schema file)
6. **Design Decisions** — Rationale for each v0.1 choice (AC-13)
7. **Future Versions** — What v0.2 may add, backward compatibility promise
8. **Examples** — Pointer to example files

## 8. README Outline (`brewspec/spec/README.md`)

1. **What is BrewSpec** — One-paragraph description
2. **Quick Start** — Validate a brew file in 3 steps
3. **Schema** — Where to find it, what version of JSON Schema it uses
4. **Examples** — Valid and invalid, where to find them
5. **Spec Document** — Pointer to the human-readable spec
6. **Contributing** — How to propose changes, report issues
7. **License** — Open source license

---

## 9. Implementation Checklist for backend-dev

TDD order — tests first, then implementation:

1. Write `tests/test_brewspec_schema.py` with all tests (they will fail initially)
2. Create `brewspec/spec/brewspec.schema.json` (copy from Section 1 above)
3. Create valid example files in `brewspec/spec/examples/valid/`
4. Create invalid example files in `brewspec/spec/examples/invalid/`
5. Run tests — all should pass
6. Write `brewspec/spec/brewspec-v0.1.md` (spec document)
7. Write `brewspec/spec/README.md`

---

## 10. Acceptance Criteria Verification

| AC | Addressed in | Status |
|----|-------------|--------|
| AC-1 | Section 1 (complete JSON Schema) | Designed |
| AC-2 | Schema `const: "0.1"` | Designed |
| AC-3 | Schema `minItems: 1` | Designed |
| AC-4 | Schema required fields + types | Designed |
| AC-5 | Schema optional fields + constraints | Designed |
| AC-6 | Schema `minimum: 1, maximum: 5, type: integer` | Designed |
| AC-7 | Schema `exclusiveMinimum: 0` | Designed |
| AC-8 | Schema `enum` on type | Designed |
| AC-9 | Section 3 valid examples (4 files) | Designed |
| AC-10 | Section 3 invalid examples (6 files) | Designed |
| AC-11 | Section 5 test strategy | Designed |
| AC-12 | Section 7 spec document outline | Designed |
| AC-13 | Section 1 design decisions table + spec outline section 6 | Designed |
| AC-14 | Section 8 README outline | Designed |
| AC-15 | Section 4 format-agnostic validation | Designed |
