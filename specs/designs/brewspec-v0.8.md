# Design: BrewSpec v0.8

**Feature:** brewspec-v0.8
**Author:** architect
**Created:** 2026-03-19
**Input:** specs/products/brewspec-v0.8.md
**Baseline:** specs/designs/brewspec-v0.7.md
**Status:** Ready for Dev

---

## Overview

BrewSpec v0.8 adds three new optional fields — `coffee.roaster`, `coffee.roast_level`, and `coffee.origins[].elevation_masl` — and tightens the existing `water_temp_c` field with a `multipleOf: 0.1` precision constraint.

The three new fields are additive, non-breaking changes. They capture metadata commonly printed on specialty coffee bags: who roasted the coffee, the roast level category, and the growing elevation of the origin. All three are optional and follow established patterns in the schema.

The `multipleOf: 0.1` constraint on `water_temp_c` is a **breaking change**. A v0.7 document containing `water_temp_c: 96.15` becomes invalid under v0.8. The migration path is straightforward: round to one decimal place.

This design document covers the JSON Schema changes, a floating-point investigation for `multipleOf: 0.1`, test strategy, example files, the spec document, and migration notes. BrewLog CLI changes are out of scope for this design — they are a separate task that depends on the v0.8 schema.

---

## 1. Changes Required

### 1.1 JSON Schema: `brewspec_version` constant

Change the `const` value from `"0.7"` to `"0.8"` and update the `title` string.

Before:
```json
"title": "BrewSpec v0.7",
"brewspec_version": {
  "const": "0.7",
  "description": "The BrewSpec version. Must be \"0.7\"."
}
```

After:
```json
"title": "BrewSpec v0.8",
"brewspec_version": {
  "const": "0.8",
  "description": "The BrewSpec version. Must be \"0.8\"."
}
```

### 1.2 JSON Schema: Add `roaster` to `$defs/coffee`

Add one property to the `coffee` object definition. Insert after `name`, before `roast_date`:

```json
"roaster": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "The company or person who roasted the coffee. Applies to the coffee as a whole, not to individual origin components.",
  "examples": ["Onyx", "Tim Wendelboe", "George Howell"]
}
```

### 1.3 JSON Schema: Add `roast_level` to `$defs/coffee`

Add one property to the `coffee` object definition. Insert after `roaster`, before `roast_date`:

```json
"roast_level": {
  "type": "string",
  "enum": ["light", "medium", "dark"],
  "description": "Roast level category. Deliberately coarse — three values cover the labels on the majority of retail bags. For finer roast detail, use the brew-level notes field. New in v0.8."
}
```

### 1.4 JSON Schema: Add `elevation_masl` to `$defs/origin`

Add one property to the `origin` object definition. Insert after `varietal` (last current field):

```json
"elevation_masl": {
  "type": "integer",
  "exclusiveMinimum": 0,
  "description": "Growing elevation in meters above sea level. Unit is embedded in the field name, following the established convention (dose_g, water_weight_g, water_temp_c, duration_s, yield_g). New in v0.8.",
  "examples": [1950, 1200, 2100]
}
```

### 1.5 JSON Schema: Add `multipleOf: 0.1` to `water_temp_c`

Modify the existing `water_temp_c` property in the `$defs/brew` definition.

Before:
```json
"water_temp_c": {
  "type": "number",
  "minimum": 0,
  "maximum": 100,
  "description": "Water temperature in celsius. Optional. Range 0-100 inclusive."
}
```

After:
```json
"water_temp_c": {
  "type": "number",
  "minimum": 0,
  "maximum": 100,
  "multipleOf": 0.1,
  "description": "Water temperature in celsius. Optional. Range 0-100 inclusive. Constrained to 0.1-degree precision (multipleOf: 0.1). New constraint in v0.8."
}
```

### 1.6 Full updated `$defs/coffee` in context

```json
"coffee": {
  "type": "object",
  "additionalProperties": false,
  "description": "Optional coffee ingredient descriptor. All fields optional.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 150,
      "description": "A branded product name or human-readable descriptive label for the coffee (e.g. 'Ethiopia Yirgacheffe', 'Blue Bottle Hayes Valley Espresso', 'Estate'). Optional. Not required even when origins[] is populated. New in v0.6.",
      "examples": ["Ethiopia Yirgacheffe", "Blue Bottle Hayes Valley Espresso", "Estate"]
    },
    "roaster": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "The company or person who roasted the coffee. Applies to the coffee as a whole, not to individual origin components.",
      "examples": ["Onyx", "Tim Wendelboe", "George Howell"]
    },
    "roast_level": {
      "type": "string",
      "enum": ["light", "medium", "dark"],
      "description": "Roast level category. Deliberately coarse — three values cover the labels on the majority of retail bags. For finer roast detail, use the brew-level notes field. New in v0.8."
    },
    "roast_date": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
      "description": "Roast date in YYYY-MM-DD format. Plain date; no time component.",
      "examples": ["2026-01-20"]
    },
    "type": {
      "type": "string",
      "enum": ["single_origin", "blend"],
      "description": "Whether the coffee is a single origin or a blend."
    },
    "origins": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/origin"
      },
      "description": "Structured origin records. Array to support blends. Each entry is an origin object with all fields optional. minItems: 1 — omit the field entirely to record no origin data."
    }
  }
}
```

### 1.7 Full updated `$defs/origin` in context (showing only the new field addition)

Add `elevation_masl` to the existing `origin` properties object, after `varietal`:

```json
"varietal": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Coffee varietal for this origin entry. Freeform. Records the coffee variety or cultivar specific to this component (e.g. Heirloom, Gesha, Bourbon). New in v0.6.",
  "examples": ["Heirloom", "Gesha", "Bourbon", "Catuai", "SL28"]
},
"elevation_masl": {
  "type": "integer",
  "exclusiveMinimum": 0,
  "description": "Growing elevation in meters above sea level. Unit is embedded in the field name, following the established convention (dose_g, water_weight_g, water_temp_c, duration_s, yield_g). New in v0.8.",
  "examples": [1950, 1200, 2100]
}
```

---

## 2. Floating-Point Investigation: `multipleOf: 0.1`

### 2.1 Problem

IEEE 754 binary floating point cannot represent many decimal fractions exactly. For example, `0.1` in binary float is `0.1000000000000000055511151231257827021181583404541015625`. This causes `multipleOf` checks using the modulo operator (`%`) to produce unexpected results — values like `96.1` and `93.3` are falsely rejected because `96.1 % 0.1` is not exactly zero in binary floating point.

### 2.2 Investigation Results

Tested with Python `jsonschema` v4.25.1 (Draft 2020-12 validator). Results using **native float** parsing:

| Value | Expected | Actual | Correct? |
|-------|----------|--------|----------|
| 96.1 | PASS | **FAIL** | No |
| 96.5 | PASS | PASS | Yes |
| 93.0 | PASS | PASS | Yes |
| 93.3 | PASS | **FAIL** | No |
| 0.1 | PASS | PASS | Yes |
| 99.9 | PASS | PASS | Yes |
| 0.3 | PASS | **FAIL** | No |
| 0.7 | PASS | **FAIL** | No |
| 96.15 | FAIL | FAIL | Yes |
| 96.123 | FAIL | FAIL | Yes |

**6 out of 10 values behave correctly with native floats. 4 valid values are falsely rejected.** This is a showstopper — the schema cannot be used with plain `float` parsing.

### 2.3 Workaround: `Decimal` Parsing

The `jsonschema` library performs the `multipleOf` check using Python's `%` operator. When both the schema's `multipleOf` value and the instance value are `decimal.Decimal` objects, the modulo operation uses decimal arithmetic, which is exact for base-10 fractions.

**Approach:** Load both the schema JSON and the instance data using `json.loads(..., parse_float=decimal.Decimal)`. For YAML-sourced data, round-trip through JSON serialization first: `json.loads(json.dumps(data), parse_float=decimal.Decimal)`.

Results using **Decimal** parsing:

| Value | Expected | Actual | Correct? |
|-------|----------|--------|----------|
| 96.1 | PASS | PASS | Yes |
| 96.5 | PASS | PASS | Yes |
| 93.0 | PASS | PASS | Yes |
| 93.3 | PASS | PASS | Yes |
| 0.1 | PASS | PASS | Yes |
| 99.9 | PASS | PASS | Yes |
| 0.3 | PASS | PASS | Yes |
| 0.7 | PASS | PASS | Yes |
| 96.15 | FAIL | FAIL | Yes |
| 96.123 | FAIL | FAIL | Yes |

**10 out of 10 values behave correctly with Decimal parsing.**

### 2.4 Implementation Requirement

The test suite **must** use `decimal.Decimal` parsing for both schema and instance data when validating `multipleOf` constraints. The existing test fixtures load the schema with `json.loads(...)` — this must change to `json.loads(..., parse_float=decimal.Decimal)`.

For YAML-sourced data (example files loaded via `yaml.safe_load`), the data must be round-tripped through JSON with Decimal parsing:

```python
import decimal
import json
import yaml

def load_yaml_decimal(path):
    """Load a YAML file with Decimal float parsing for multipleOf accuracy."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(json.dumps(raw), parse_float=decimal.Decimal)
```

This roundtrip is safe because:
1. `yaml.safe_load` produces Python-native types (dict, list, str, int, float, bool, None)
2. `json.dumps` serializes these to JSON text (float values are serialized with enough precision to round-trip)
3. `json.loads(..., parse_float=decimal.Decimal)` parses the JSON text back, converting all float tokens to `Decimal`

**Important:** Both the schema and the instance must use `Decimal`. If the schema uses `Decimal` but the instance uses `float` (or vice versa), Python raises a `TypeError` on the `%` operation. The test fixtures must ensure consistency.

### 2.5 Impact on Existing Tests

The existing test suite loads the schema without `parse_float=decimal.Decimal`. Since v0.7 has no `multipleOf` constraints, this worked fine. Adding `parse_float=decimal.Decimal` to the schema fixture is backward-compatible — all existing tests continue to pass because `Decimal` values work correctly with all other JSON Schema keywords (`minimum`, `maximum`, `exclusiveMinimum`, `const`, `enum`, etc.).

The instance data path must also change. Currently, inline test dicts use Python `float` literals (e.g., `{"dose_g": 20}`). Integer literals are fine — Python `int % Decimal` works. But any test that constructs an inline dict with a float value for a field subject to `multipleOf` must use `Decimal`. In practice, only `water_temp_c` tests need this.

**Recommended approach for the test suite:**

1. Update the `schema` fixture to use `json.loads(..., parse_float=decimal.Decimal)`.
2. Add a helper function to convert instance dicts: `json.loads(json.dumps(data), parse_float=decimal.Decimal)`.
3. Use the helper for all inline test dicts that include `water_temp_c` values.
4. Use the helper for all YAML example file loads.
5. Test dicts that contain only integers and strings can skip the conversion (integers work with Decimal arithmetic).

### 2.6 Spec Document Note

The `brewspec-v0.8.md` spec document must include a validation note warning implementers about the IEEE 754 issue:

> **Implementer note:** The `multipleOf: 0.1` constraint on `water_temp_c` requires decimal-precise arithmetic in validators. In Python, load both the schema and the instance data using `json.loads(..., parse_float=decimal.Decimal)` to avoid false rejections from binary floating-point rounding. Other languages may need equivalent workarounds (e.g., using `BigDecimal` in Java, or a decimal-aware JSON Schema validator). Values like `96.1` and `93.3` are valid multiples of `0.1` in decimal arithmetic but produce non-zero remainders in binary float arithmetic.

---

## 3. Example Files

### 3.1 New valid example: `examples/valid/light_roast_ethiopian.yaml`

```yaml
brewspec_version: "0.8"
brews:
  - date: "2026-03-19"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 18.0
    water_weight_g: 280.0
    brew_ratio: 15.56
    water_temp_c: 96.0
    grind: "medium_fine"
    duration_s: 195
    coffee:
      name: "Ethiopia Yirgacheffe"
      roaster: "Onyx"
      roast_level: "light"
      roast_date: "2026-03-10"
      type: "single_origin"
      origins:
        - name: "Yirgacheffe Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa"
          process: "Natural"
          varietal: "Heirloom"
          elevation_masl: 1950
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
      grinder_setting: 24
    result:
      tds: 1.38
      ey: 20.1
      yield_g: 260.0
      tasting_notes: "Bright blueberry, jasmine, honey sweetness"
      ratings:
        overall: 5
        fragrance: 4
        aroma: 5
        flavour: 5
        acidity: 5
        sweetness: 4
        mouthfeel: 4
```

This example demonstrates all three new v0.8 fields (`roaster`, `roast_level`, `elevation_masl`) populated together in a realistic brew record.

### 3.2 New invalid example: `examples/invalid/invalid_roast_level.yaml`

```yaml
brewspec_version: "0.8"
brews:
  - coffee:
      roast_level: "medium_light"
```

Fails validation because `"medium_light"` is not in the enum `["light", "medium", "dark"]`. The brew has no other fields — all brew fields are optional in v0.7+, so the only failure point is the invalid enum value.

### 3.3 New invalid example: `examples/invalid/invalid_water_temp_precision.yaml`

```yaml
brewspec_version: "0.8"
brews:
  - water_temp_c: 96.15
```

Fails validation because `96.15` is not a multiple of `0.1`. Demonstrates the new precision constraint.

### 3.4 Existing valid example updates

All files in `examples/valid/` must have `brewspec_version` bumped from `"0.7"` to `"0.8"`. The JSON example (`pour_over.json`) must also be bumped.

**Files requiring version bump (16 YAML files + 1 JSON file):**

| File | `water_temp_c` value | Needs rounding? |
|------|---------------------|-----------------|
| `pour_over.yaml` | 96 (integer) | No |
| `espresso.yaml` | 93 (integer) | No |
| `espresso_with_yield.yaml` | (none) | N/A |
| `minimal_no_required_fields.yaml` | (none) | N/A |
| `immersion_minimal.yaml` | (none) | N/A |
| `equipment.yaml` | 96 (integer) | No |
| `hybrid.yaml` | 85 (integer) | No |
| `multi_brew.yaml` | 96 (integer) | No |
| `pour_over_date_only.yaml` | 96 (integer) | No |
| `valid_brew_ratio.yaml` | (none) | N/A |
| `valid_grinder_setting.yaml` | (none) | N/A |
| `valid_equipment_notes.yaml` | (none) | N/A |
| `valid_single_origin_full.yaml` | (none) | N/A |
| `valid_single_origin_with_varietal.yaml` | 96 (integer) | No |
| `valid_blend_with_per_origin_varietal.yaml` | 94 (integer) | No |
| `valid_blend_origin.yaml` | (none) | N/A |
| `pour_over.json` | 96 (integer) | No |

**Result: No existing valid examples have `water_temp_c` values that violate `multipleOf: 0.1`.** All values are integers, which are exact multiples of `0.1`. Only the version bump is needed.

### 3.5 Existing invalid example updates

All invalid examples that currently have `brewspec_version: "0.7"` and test a non-version-related failure should be bumped to `"0.8"` so the test remains focused on its intended violation. Review each file:

- Files testing structural errors (extra fields, wrong types, out-of-range values, bad enums) should be bumped to `"0.8"`.
- Files testing old version formats (`v0.1_format.yaml`, `v0.2_format.yaml`) should be left as-is — their intended failure is the version mismatch.
- `missing_version.yaml` — leave as-is (no version field to bump).

---

## 4. Test Strategy

The test suite is in `tests/test_brewspec_schema.py`. All tests use the `validator` fixture. The fixture must be updated to use `Decimal` parsing (see Section 2.4).

### Test Fixture Changes

```python
import decimal

@pytest.fixture
def schema():
    """Load the BrewSpec JSON Schema with Decimal parsing for multipleOf accuracy."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"), parse_float=decimal.Decimal)


def _to_decimal(data):
    """Convert a Python dict to use Decimal floats for jsonschema multipleOf checks."""
    return json.loads(json.dumps(data), parse_float=decimal.Decimal)
```

Update `VALID_DOC` and `VALID_BREW` to use version `"0.8"`:

```python
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.8", "brews": [VALID_BREW]}
```

For YAML example file loads, update the loading pattern:

```python
def _load_yaml_example(path):
    """Load a YAML example file with Decimal float parsing."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(json.dumps(raw), parse_float=decimal.Decimal)
```

### AC-1: Version bump

| Test | Input | Expected | AC |
|------|-------|----------|----|
| Version const is "0.8" | Schema JSON | `const: "0.8"` | AC-1 |
| Schema title is "BrewSpec v0.8" | Schema JSON | `title == "BrewSpec v0.8"` | AC-1 |
| `brewspec_version: "0.7"` rejected | `{"brewspec_version": "0.7", "brews": [VALID_BREW]}` | fails validation | AC-1 |
| `brewspec_version: "0.8"` accepted | `VALID_DOC` | passes validation | AC-1 |

### AC-2, AC-3, AC-4: `coffee.roaster`

| Test | Input | Expected | AC |
|------|-------|----------|----|
| `roaster: "Onyx"` passes | `{..., "coffee": {"roaster": "Onyx"}}` | passes | AC-3 |
| `roaster` omitted passes | `{..., "coffee": {"name": "Test"}}` | passes | AC-2 |
| `roaster: ""` fails | `{..., "coffee": {"roaster": ""}}` | fails — minLength 1 | AC-4 |

### AC-5 through AC-10: `coffee.roast_level`

| Test | Input | Expected | AC |
|------|-------|----------|----|
| `roast_level: "light"` passes | `{..., "coffee": {"roast_level": "light"}}` | passes | AC-6 |
| `roast_level: "medium"` passes | `{..., "coffee": {"roast_level": "medium"}}` | passes | AC-7 |
| `roast_level: "dark"` passes | `{..., "coffee": {"roast_level": "dark"}}` | passes | AC-8 |
| `roast_level` omitted passes | `{..., "coffee": {"name": "Test"}}` | passes | AC-5 |
| `roast_level: "medium_light"` fails | `{..., "coffee": {"roast_level": "medium_light"}}` | fails — not in enum | AC-9 |
| `roast_level: "Light"` fails | `{..., "coffee": {"roast_level": "Light"}}` | fails — not in enum | AC-10 |

### AC-11 through AC-15: `origin.elevation_masl`

| Test | Input | Expected | AC |
|------|-------|----------|----|
| `elevation_masl: 1950` passes | `{..., "coffee": {"origins": [{"country": "Ethiopia", "elevation_masl": 1950}]}}` | passes | AC-12 |
| `elevation_masl` omitted passes | `{..., "coffee": {"origins": [{"country": "Ethiopia"}]}}` | passes | AC-11 |
| `elevation_masl: 0` fails | `{..., "coffee": {"origins": [{"elevation_masl": 0}]}}` | fails — exclusiveMinimum 0 | AC-13 |
| `elevation_masl: -100` fails | `{..., "coffee": {"origins": [{"elevation_masl": -100}]}}` | fails — exclusiveMinimum 0 | AC-14 |
| `elevation_masl: 1950.5` fails | `{..., "coffee": {"origins": [{"elevation_masl": 1950.5}]}}` | fails — not integer | AC-15 |

### AC-16 through AC-20: `water_temp_c` multipleOf

**These tests require Decimal conversion** via the `_to_decimal()` helper.

| Test | Input | Expected | AC |
|------|-------|----------|----|
| `water_temp_c: 96.0` passes | `_to_decimal({..., "water_temp_c": 96.0})` | passes | AC-16 |
| `water_temp_c: 96.5` passes | `_to_decimal({..., "water_temp_c": 96.5})` | passes | AC-17 |
| `water_temp_c: 93` passes | `{..., "water_temp_c": 93}` (integer, no Decimal needed) | passes | AC-18 |
| `water_temp_c: 96.15` fails | `_to_decimal({..., "water_temp_c": 96.15})` | fails — multipleOf 0.1 | AC-19 |
| `water_temp_c: 96.123` fails | `_to_decimal({..., "water_temp_c": 96.123})` | fails — multipleOf 0.1 | AC-20 |

Additional edge-case tests (to verify Decimal handling is correct):

| Test | Input | Expected | Notes |
|------|-------|----------|-------|
| `water_temp_c: 96.1` passes | `_to_decimal({..., "water_temp_c": 96.1})` | passes | IEEE 754 edge case — would fail without Decimal |
| `water_temp_c: 93.3` passes | `_to_decimal({..., "water_temp_c": 93.3})` | passes | IEEE 754 edge case |
| `water_temp_c: 0.1` passes | `_to_decimal({..., "water_temp_c": 0.1})` | passes | Boundary value |
| `water_temp_c: 99.9` passes | `_to_decimal({..., "water_temp_c": 99.9})` | passes | Boundary value |

### AC-22, AC-23, AC-24: Example file validation

| Test | File | Expected | AC |
|------|------|----------|----|
| `light_roast_ethiopian.yaml` passes | load with `_load_yaml_example` | passes validation | AC-22 |
| `invalid_roast_level.yaml` fails | load with `_load_yaml_example` | fails validation | AC-23 |
| `invalid_water_temp_precision.yaml` fails | load with `_load_yaml_example` | fails validation | AC-24 |

### AC-25: Existing example files pass after version bump

| Test | Condition | Expected | AC |
|------|-----------|----------|----|
| All valid examples pass | iterate `examples/valid/*.yaml` and `*.json`, load each, validate | all pass | AC-25 |
| All invalid examples fail | iterate `examples/invalid/*.yaml`, load each, validate | all fail | AC-25 |

The existing parametrized tests that iterate over example directories should continue to work — they just need the YAML/JSON loading path updated to use `_load_yaml_example` / Decimal-aware loading.

### AC-29: Schema structure verification

| Test | Check | Expected | AC |
|------|-------|----------|----|
| `roaster` in `$defs/coffee/properties` | inspect schema dict | present with `minLength: 1`, `maxLength: 100` | AC-29 |
| `roast_level` in `$defs/coffee/properties` | inspect schema dict | present with `enum: ["light", "medium", "dark"]` | AC-29 |
| `elevation_masl` in `$defs/origin/properties` | inspect schema dict | present with `type: "integer"`, `exclusiveMinimum: 0` | AC-29 |
| `multipleOf` on `water_temp_c` | inspect schema dict | `multipleOf: 0.1` (as Decimal) | AC-29 |

---

## 5. Spec Document: `brewspec-v0.8.md`

The dev must produce `brewspec-v0.8.md` in the brewspec repo root. Archive the existing `brewspec-v0.7.md` to `versions/brewspec-v0.7.md` first, then write `brewspec-v0.8.md`.

### 5.1 Structure

The spec document must include these sections in order:

1. **Overview** — What BrewSpec is; scope of v0.8
2. **Field Reference** — Updated tables for all objects, with the three new fields added and `water_temp_c` constraint updated
3. **What Changed in v0.8** — New fields and breaking changes clearly separated
4. **Validation** — Guidance including the Decimal/floating-point note for `multipleOf: 0.1`
5. **Backward Compatibility** — Migration from v0.7 (three additive fields need no migration; `water_temp_c` precision constraint is breaking)
6. **Examples** — Updated examples list including the three new v0.8 examples

### 5.2 Field Reference Updates

**Coffee Object table** — add two rows:

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roaster` | string | No | minLength 1, maxLength 100 | The company or person who roasted the coffee. Applies to the whole coffee, not individual origins. New in v0.8. | `"Onyx"`, `"Tim Wendelboe"` |
| `roast_level` | string | No | Enum: `light`, `medium`, `dark` | Roast level category. Three values covering the majority of retail bag labels. For finer detail, use the brew-level `notes` field. New in v0.8. | `"light"` |

Insert `roaster` after `name` and `roast_level` after `roaster`, before `roast_date`.

**Origin Object table** — add one row:

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `elevation_masl` | integer | No | > 0 (exclusive) | Growing elevation in meters above sea level. Unit embedded in field name per schema convention. New in v0.8. | `1950`, `1200` |

Insert after `varietal`.

**Brew Object table** — update `water_temp_c`:

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `water_temp_c` | number | No | 0–100 inclusive, multipleOf 0.1 | Water temperature in celsius. Constrained to 0.1-degree precision. Changed in v0.8. | `96.0`, `93.5` |

### 5.3 What Changed in v0.8

**New Fields (additive, non-breaking)**

- **`coffee.roaster`** (`string`, optional, `minLength: 1`, `maxLength: 100`) — The company or person who roasted the coffee. Placed on the `coffee` object, not inside `origins[]`, because a roaster applies to the coffee as a whole.
- **`coffee.roast_level`** (`string`, optional, `enum: ["light", "medium", "dark"]`) — Roast level category. Deliberately coarse three-value enum. Expandable in future versions if usage data demonstrates the need.
- **`coffee.origins[].elevation_masl`** (`integer`, optional, `exclusiveMinimum: 0`) — Growing elevation in meters above sea level. Unit embedded in field name per schema convention.

**Breaking Changes**

- **`water_temp_c` precision constraint** — Added `multipleOf: 0.1`. A v0.7 document containing `water_temp_c: 96.15` (or any value with more than one decimal place) becomes invalid under v0.8. Migration: round to one decimal place.

### 5.4 Backward Compatibility Section

**Documents from v0.7**

The three new fields (`coffee.roaster`, `coffee.roast_level`, `coffee.origins[].elevation_masl`) are additive and optional. Existing v0.7 documents that omit these fields remain valid under v0.8 with only a version bump.

The `water_temp_c` precision constraint is a breaking change. Any v0.7 document with a `water_temp_c` value that has more than one decimal place must be corrected before validating against v0.8.

**Migration steps:**

1. Change `brewspec_version` from `"0.7"` to `"0.8"`
2. If any `water_temp_c` value has more than one decimal place, round it to one decimal place (e.g., `96.15` → `96.2`)

### 5.5 Validation Section Addition

Add the floating-point implementer note from Section 2.6 of this design to the Validation section of the spec document.

---

## 6. Architecture Decision Records

No new cross-cutting decisions. The four changes follow established patterns:

- Adding optional fields to `coffee` and `origin` follows the same pattern as `coffee.name` (v0.6) and `origins[].varietal` (v0.6).
- The three-value `roast_level` enum follows the "earn complexity" principle — start with the simplest version, expand if real usage demonstrates the need.
- `elevation_masl` embeds the unit in the field name, following the established convention (`dose_g`, `water_weight_g`, `water_temp_c`, `duration_s`, `yield_g`).
- Adding `multipleOf` to an existing field is a schema tightening — a known category of breaking change, versioned and documented per the architecture principle "additive changes are preferred over breaking changes; breaking changes must be versioned, documented, and carry migration guidance."

No ADR is required.

---

## 7. File Manifest

| File | Operation | Notes |
|------|-----------|-------|
| `brewspec.schema.json` | Modify | Version bump, add `roaster` + `roast_level` to coffee def, add `elevation_masl` to origin def, add `multipleOf: 0.1` to `water_temp_c` |
| `brewspec-v0.8.md` | Create | New root spec doc per Section 5 |
| `versions/brewspec-v0.7.md` | Archive | Copy `brewspec-v0.7.md` here before writing new root spec |
| `examples/valid/light_roast_ethiopian.yaml` | Create | New valid example per Section 3.1 |
| `examples/invalid/invalid_roast_level.yaml` | Create | New invalid example per Section 3.2 |
| `examples/invalid/invalid_water_temp_precision.yaml` | Create | New invalid example per Section 3.3 |
| `examples/valid/*.yaml` and `*.json` (all existing) | Modify | Bump `brewspec_version` from `"0.7"` to `"0.8"` |
| `examples/invalid/*.yaml` (non-version tests) | Modify | Bump `brewspec_version` from `"0.7"` to `"0.8"` where the intended failure is not version-related |
| `tests/test_brewspec_schema.py` | Modify | Update fixtures for Decimal parsing, update version references, add new test cases per Section 4 |

---

## 8. Security Considerations

**Input validation**

All three new fields are validated at schema level:
- `roaster` is a bounded freeform string (`minLength: 1`, `maxLength: 100`) — must not be executed, evaluated, or interpolated.
- `roast_level` is a closed enum — only three values accepted. No injection risk.
- `elevation_masl` is a positive integer — no string-injection risk.
- The `multipleOf` constraint tightens `water_temp_c` validation, reducing the range of accepted values.

**Safe parsing**

No change to the existing safe-parse requirement (`yaml.safe_load()`, JSON parse before schema validation). The Decimal roundtrip for `multipleOf` validation uses `json.dumps()` → `json.loads()`, which is safe — it only operates on already-parsed Python-native types.

**File I/O**

New example files follow the same pattern as existing examples: plain YAML, no executable content. No secrets, API keys, or PII in any example file.

---

## 9. TDD Implementation Order

1. **Update test fixtures.** Change the `schema` fixture to use `parse_float=decimal.Decimal`. Add `_to_decimal()` and `_load_yaml_example()` helpers. Update `VALID_DOC` and `VALID_BREW` to version `"0.8"`. Verify all existing tests still pass with the new fixtures (they should — Decimal is backward-compatible with all existing constraints).

2. **Write failing tests: version bump.** Test that `"0.7"` is rejected, `"0.8"` is accepted, schema title is `"BrewSpec v0.8"`.

3. **Update `brewspec.schema.json`: version.** Change `const` and `title`. Tests from step 2 pass.

4. **Write failing tests: `coffee.roaster`.** Valid (`"Onyx"`), omitted, invalid (empty string).

5. **Update `brewspec.schema.json`: add `roaster`.** Tests from step 4 pass.

6. **Write failing tests: `coffee.roast_level`.** All three valid enum values, omitted, two invalid values (`"medium_light"`, `"Light"`).

7. **Update `brewspec.schema.json`: add `roast_level`.** Tests from step 6 pass.

8. **Write failing tests: `origin.elevation_masl`.** Valid (1950), omitted, invalid (0, -100, 1950.5).

9. **Update `brewspec.schema.json`: add `elevation_masl`.** Tests from step 8 pass.

10. **Write failing tests: `water_temp_c` multipleOf.** Valid (96.0, 96.5, 93, 96.1, 93.3, 99.9), invalid (96.15, 96.123). Use `_to_decimal()` for float inputs.

11. **Update `brewspec.schema.json`: add `multipleOf: 0.1`.** Tests from step 10 pass.

12. **Create example files.** `light_roast_ethiopian.yaml`, `invalid_roast_level.yaml`, `invalid_water_temp_precision.yaml`. Write file validation tests.

13. **Bump version in all existing examples.** Change `"0.7"` to `"0.8"` in all valid and relevant invalid examples. Confirm full example suite passes.

14. **Archive and write spec document.** Copy `brewspec-v0.7.md` to `versions/brewspec-v0.7.md`. Write `brewspec-v0.8.md` per Section 5.

15. **Run full test suite.** `pytest tests/` — all pass.

16. **Run lint.** `ruff check .` — clean.
