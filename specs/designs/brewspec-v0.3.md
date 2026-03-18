# Design: BrewSpec v0.3

**Feature:** brewspec-v0.3
**Author:** architect
**Created:** 2026-02-19
**Input:** specs/products/brewspec-v0.3.md
**Status:** Ready for Dev

---

## 1. JSON Schema Diff (v0.2 → v0.3)

This section specifies every change to `brewspec.schema.json`. The dev applies these changes to produce the v0.3 schema. Each change is labelled with the AC it satisfies. The source file is `src/brewlog/brewspec.schema.json`.

### 1.1 Root-Level Changes

| Location | v0.2 Value | v0.3 Value | AC |
|----------|-----------|-----------|-----|
| `title` | `"BrewSpec v0.2"` | `"BrewSpec v0.3"` | AC-6 |
| `properties.brewspec_version.const` | `"0.2"` | `"0.3"` | AC-5, AC-6 |
| `properties.brewspec_version.description` | `"The BrewSpec version. Must be \"0.2\"."` | `"The BrewSpec version. Must be \"0.3\"."` | AC-6 |

The `$schema` and `$id` values are unchanged.

### 1.2 `$defs.brew` Changes

**Properties with `maxLength` added:**

| Property | v0.2 Definition | v0.3 Change | AC |
|----------|----------------|-------------|-----|
| `method` | `{type: string, minLength: 1}` | Add `"maxLength": 100` | AC-14 |
| `grind` | `{type: string, minLength: 1}` | Add `"maxLength": 100` | AC-15 |
| `notes` | `{type: string, minLength: 1}` | Add `"maxLength": 2000` | AC-16 |

**New properties added to `$defs.brew`:**

| Property | Type | Constraints | AC |
|----------|------|-------------|-----|
| `equipment` | object | `"$ref": "#/$defs/equipment"` | AC-7 |
| `ey` | number | `exclusiveMinimum: 0` | AC-11, AC-12, AC-13 |

**Properties unchanged in `$defs.brew`:** `date`, `type`, `dose_g`, `water_weight_g`, `water_volume_ml`, `water_temp_c`, `coffee`, `water`, `duration_s`, `tds`, `rating`

The `required` array is unchanged: `["date", "type", "dose_g", "water_weight_g"]`.

### 1.3 `$defs.coffee` Changes

**Properties with `maxLength` added:**

| Property | v0.2 Definition | v0.3 Change | AC |
|----------|----------------|-------------|-----|
| `varietal` | `{type: string, minLength: 1}` | Add `"maxLength": 100` | AC-17 |
| `process` | `{type: string, minLength: 1}` | Add `"maxLength": 100` | AC-18 |
| `origin` items | `{type: string, minLength: 1}` | Add `"maxLength": 100` to the items schema | AC-19 |

**Properties unchanged in `$defs.coffee`:** `roast_date`, `type`

### 1.4 New `$defs.equipment`

A new definition is added to `$defs`:

```
$defs.equipment:
  type: object
  additionalProperties: false
  (no required array — all fields optional)
  properties:
    grinder: {type: string, minLength: 1, maxLength: 100}
    brewer:  {type: string, minLength: 1, maxLength: 100}
```

AC-7, AC-8, AC-9, AC-10.

Design note on `equipment` as an optional object with `additionalProperties: false`: this follows the same pattern as `coffee` and `water`. The object is optional entirely. When present it may be empty (`equipment: {}`). When present, only `grinder` and `brewer` are accepted; any unrecognised field causes a validation failure. This closes the door on tool builders placing arbitrary data in the equipment namespace.

---

## 2. Full Annotated v0.3 Schema

This is the complete target `brewspec.schema.json` as it must look after all changes. The dev writes this file verbatim to `src/brewlog/brewspec.schema.json`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json",
  "title": "BrewSpec v0.3",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.3",
      "description": "The BrewSpec version. Must be \"0.3\"."
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
      "required": ["date", "type", "dose_g", "water_weight_g"],
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
          "maxLength": 100,
          "description": "Freeform brewer description.",
          "examples": ["Hario V60", "French press", "AeroPress inverted"]
        },
        "dose_g": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Coffee dose in grams. Must be > 0."
        },
        "water_weight_g": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Water weight in grams. Must be > 0."
        },
        "water_volume_ml": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Water volume in milliliters. Optional. Must be > 0 if present."
        },
        "water_temp_c": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Water temperature in celsius. Optional. Range 0-100 inclusive."
        },
        "coffee": {
          "$ref": "#/$defs/coffee"
        },
        "water": {
          "$ref": "#/$defs/water"
        },
        "equipment": {
          "$ref": "#/$defs/equipment"
        },
        "grind": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Freeform grind description.",
          "examples": ["medium-fine", "setting 15 on Comandante"]
        },
        "duration_s": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Brew duration in seconds. Must be > 0."
        },
        "tds": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Total dissolved solids percentage of the finished brew. Optional. Must be > 0 if present."
        },
        "ey": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Extraction yield as a percentage (e.g., 20.1 for 20.1%). Optional. Must be > 0 if present. No maximum enforced."
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
          "maxLength": 2000,
          "description": "Freeform tasting or session notes."
        }
      }
    },
    "coffee": {
      "type": "object",
      "additionalProperties": false,
      "description": "Optional coffee ingredient descriptor. All fields optional.",
      "properties": {
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
        "origin": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
          },
          "description": "Origin country or region(s). Array supports blends with multiple origins.",
          "examples": [["Ethiopia"], ["Ethiopia", "Colombia"]]
        },
        "varietal": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Coffee variety or cultivar. Freeform.",
          "examples": ["Heirloom", "Gesha", "Bourbon"]
        },
        "process": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Processing method. Freeform.",
          "examples": ["Washed", "Natural", "Honey"]
        }
      }
    },
    "water": {
      "type": "object",
      "additionalProperties": false,
      "description": "Optional water ingredient descriptor. All fields optional.",
      "properties": {
        "ppm": {
          "type": "number",
          "minimum": 0,
          "description": "Water total dissolved solids in parts per million. Must be >= 0 if present."
        }
      }
    },
    "equipment": {
      "type": "object",
      "additionalProperties": false,
      "description": "Optional equipment descriptor. All fields optional.",
      "properties": {
        "grinder": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Grinder model. Freeform.",
          "examples": ["Comandante C40 MK4", "Baratza Encore ESP"]
        },
        "brewer": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Brewer or brewing vessel. Freeform.",
          "examples": ["Hario V60 02", "AeroPress Original", "Moka Pot"]
        }
      }
    }
  }
}
```

### Schema Design Decisions (v0.3)

| Decision | Rationale | Traces to |
|----------|-----------|-----------|
| `equipment` as a new `$defs` entry referenced via `$ref` | Consistent with how `coffee` and `water` are defined; keeps `$defs.brew` readable | AC-7, PM design notes |
| `equipment` object optional entirely; empty `{}` is valid | Equipment is recorded metadata, not a required brew parameter. An empty object is preferable to forcing `null` | AC-7, AC-9 |
| `additionalProperties: false` on `equipment` | Consistent with all other objects (`coffee`, `water`, root). Prevents tool builders injecting arbitrary fields | AC-10 |
| `grinder` and `brewer` as freeform strings, not enums | Equipment names are inconsistent across regions and product generations; any enum would require constant maintenance or be too permissive | AC-8, PM design notes |
| `ey` at brew level, not in a `result` object | One field does not warrant a wrapper. If a third result-type field appears in v0.4+, the case for a `result` object can be made then | AC-13, PM design notes |
| `ey` with `exclusiveMinimum: 0`, no maximum | A value of 0 or negative is nonsensical. No upper bound is imposed — over-extracted brews or measurement edge cases could produce values outside the typical 18-22% range | AC-11, AC-12 |
| `maxLength: 100` for `method`, `grind`, `varietal`, `process`, `origin` items, `grinder`, `brewer` | These fields describe short phrases or product names; 100 characters is generous in practice and gives tools a safe upper bound | AC-14–AC-19, PM design notes |
| `maxLength: 2000` for `notes` | Notes may be a paragraph; 2000 characters accommodates detailed tasting notes without being unbounded | AC-16, PM design notes |
| `const: "0.3"` on `brewspec_version` | Exact-match version enforcement; v0.2 files are rejected by the v0.3 schema, enabling clean per-version validation | AC-5, AC-6 |

---

## 3. Carry-Forward Test Docstring Fixes

The four carry-forward items from the v0.2 review are docstring corrections only. The test logic and schema are correct. These changes are made to `tests/test_brewspec_schema.py` (the private repo test file, which currently still reflects v0.1 inline dicts — see Section 6 for the full picture of test file state).

The corrections below specify the exact docstring replacement for each function:

### 3.1 `test_date_format_iso8601` (AC-1)

```python
# Before (incorrect):
"""AC-4: date must be ISO 8601 format YYYY-MM-DDTHH:MM:SSZ."""

# Note: the existing docstring references "AC-4" with a description that
# happens to be accurate, but the broader pattern of citing numbered ACs
# in docstrings causes confusion when ACs are renumbered. Remove the AC
# citation and describe the test purpose directly.

# After (correct):
"""date must be ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ. Tests valid and invalid date strings."""
```

### 3.2 `test_optional_fields_accepted` (AC-2)

```python
# Before (incorrect):
"""AC-5: All optional fields should be accepted when valid."""

# After (correct):
"""Optional brew fields are accepted when valid: method, grind, duration_s, rating, notes, water_temp_c, water_volume_ml."""
```

### 3.3 `test_json_format_supported` (AC-3)

```python
# Before (incorrect):
"""AC-15: Schema must support both YAML and JSON formats."""

# After (correct):
"""Schema validation is format-agnostic: the same constraints apply whether the source was YAML or JSON."""
```

### 3.4 `test_rating_range_1_to_5` (AC-4)

```python
# Before (incorrect):
"""AC-6: rating must be an integer between 1 and 5 inclusive."""

# After (correct):
"""rating must be an integer between 1 and 5 inclusive. Values 0, 6, -1, and 3.5 are rejected."""
```

---

## 4. Spec Document Changes (brewspec-v0.2.md → brewspec-v0.3.md)

The dev produces `brewspec-v0.3.md` in the public repo by updating `brewspec-v0.2.md`. The following sections change. All other sections are preserved with edits noted below.

### 4.1 Header

```
v0.2:  # BrewSpec v0.2 / Status: Stable / Version: 0.2 / Last Updated: 2026-02-18
v0.3:  # BrewSpec v0.3 / Status: Stable / Version: 0.3 / Last Updated: 2026-02-19
```

### 4.2 Field Reference Tables — Full Replacement (AC-26)

Replace all field reference tables with the v0.3 versions below.

**Top-Level Fields** (unchanged from v0.2):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.3"` | The BrewSpec version |
| `brews` | array | Required | Minimum 1 element | Array of brew objects |

**Brew Object:**

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Required | ISO 8601 UTC: `YYYY-MM-DDTHH:MM:SSZ` | Brew timestamp | `"2026-02-15T08:30:00Z"` |
| `type` | string | Required | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Required | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Required | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `method` | string | Optional | Min length 1, max length 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `equipment` | object | Optional | See Equipment Object | Equipment descriptor | |
| `grind` | string | Optional | Min length 1, max length 100 | Freeform grind description | `"medium-fine"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield as a percentage | `20.1`, `19.8` |
| `rating` | integer | Optional | 1–5 inclusive | Brew rating. 1 = poor, 5 = excellent | `4` |
| `notes` | string | Optional | Min length 1, max length 2000 | Freeform tasting or session notes | `"Bright acidity"` |

**Coffee Object** (entire object is optional; all fields within are optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roast_date` | string | Optional | Pattern `YYYY-MM-DD` | Roast date. Plain date, no time. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Coffee classification | `"single_origin"` |
| `origin` | array of strings | Optional | Min 1 item; each item min length 1, max length 100 | Origin(s). Multiple entries for blends. | `["Ethiopia"]`, `["Ethiopia", "Colombia"]` |
| `varietal` | string | Optional | Min length 1, max length 100 | Coffee variety or cultivar. Freeform. | `"Heirloom"`, `"Gesha"` |
| `process` | string | Optional | Min length 1, max length 100 | Processing method. Freeform. | `"Washed"`, `"Natural"` |

**Water Object** (entire object is optional; all fields within are optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

**Equipment Object** (entire object is optional; all fields within are optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | Min length 1, max length 100 | Grinder model. Freeform. | `"Comandante C40 MK4"`, `"Baratza Encore ESP"` |
| `brewer` | string | Optional | Min length 1, max length 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"`, `"AeroPress Original"` |

### 4.3 "What Changed in v0.3" Section (AC-27)

Add a new section immediately after the header or overview:

```
## What Changed in v0.3

### Carry-forward test docstring fixes (no schema change)
Four test docstrings in the v0.2 test suite cited AC numbers that no longer
matched after v0.2 renumbering. The docstrings in test_date_format_iso8601,
test_optional_fields_accepted, test_json_format_supported, and
test_rating_range_1_to_5 were updated to describe each test's purpose without
citing specific AC numbers.

### New optional `equipment` object
A new optional `equipment` object is added to the brew record with two optional
freeform string fields:
- `grinder` (string, minLength: 1, maxLength: 100) — grinder model used
- `brewer` (string, minLength: 1, maxLength: 100) — brewer or brewing vessel used

The object follows the same pattern as `coffee` and `water`: optional, all
fields within it optional, `additionalProperties: false`.

### New optional `ey` field
`ey` (extraction yield) is added as an optional flat field on the brew object
at the same level as `tds`. It represents extraction yield as a percentage
(e.g., 20.1 for 20.1%). Constraint: `exclusiveMinimum: 0`. No maximum enforced.

### maxLength constraints on freeform string fields
The following freeform string fields gained `maxLength` constraints:
- `method`: maxLength 100
- `grind`: maxLength 100
- `notes`: maxLength 2000
- `coffee.varietal`: maxLength 100
- `coffee.process`: maxLength 100
- `coffee.origin` items: maxLength 100
- `equipment.grinder`: maxLength 100 (new field, constraint included at creation)
- `equipment.brewer`: maxLength 100 (new field, constraint included at creation)

### Version bump
`brewspec_version` const updated from `"0.2"` to `"0.3"`. The schema title
updated to "BrewSpec v0.3".
```

### 4.4 "Design Decisions" Section (AC-28)

Add the following entries to the existing "Design Decisions" section:

**New entry: Why is `equipment` a separate object rather than flat brew-level fields?**

Decision: `grinder` and `brewer` are placed inside an `equipment` object rather than added as `grinder` and `brewer` directly on the brew record.

Rationale: Equipment identity is a property of the instrument, not the brew act. A user brews with the same grinder for months. Grouping equipment fields under a dedicated namespace keeps the brew-level fields focused on brew parameters (dose, water weight, temperature, duration) and leaves room for future equipment fields (e.g., `kettle`, `scale`) without cluttering the top-level namespace. This is the same design principle that separates `coffee` metadata and `water` chemistry from the brew quantities.

**New entry: Why are `grinder` and `brewer` freeform strings, not enumerations?**

Decision: `grinder` and `brewer` use `type: string` with `minLength: 1` and `maxLength: 100`. No enum.

Rationale: Equipment naming is inconsistent across regions, retailers, and product generations. "Hario V60", "V60", and "Hario V60 02 Plastic" all refer to the same or similar brewers. A fixed enum would either be too restrictive (rejecting valid names) or too permissive (so many variants that standardisation provides no value). The commercial prediction engine will need to normalise equipment names regardless of what the spec does — an enum does not eliminate that problem, it moves it. Freeform strings are correct until a companion equipment registry is warranted at adoption scale.

**New entry: Why is `ey` a flat field parallel to `tds`, not inside a `result` object?**

Decision: `ey` is placed at the brew level alongside `tds`, `rating`, and `notes`. No `result: {}` wrapper is introduced in v0.3.

Rationale: A `result` object would add structural complexity without adding clarity at this stage. The v0.2 design note on `tds` anticipated this: a `result` object may be warranted when additional result-type fields emerge. With two fields (`tds` and `ey`), the argument for grouping is stronger than it was with one, but the principle of earning complexity applies: introduce a wrapper only when it provides value that outweighs the migration cost. v0.4 is the natural reassessment point if a third result-type field appears.

**New entry: Why are `maxLength` values set at 100 for most freeform fields and 2000 for `notes`?**

Decision: All freeform string fields except `notes` use `maxLength: 100`. `notes` uses `maxLength: 2000`.

Rationale: The purpose of these constraints is to give tools a safe, predictable upper bound for memory allocation and display logic, not to restrict what users write. 100 characters comfortably accommodates the longest realistic brew method name, grind description, coffee varietal, processing method, origin, grinder model, or brewer model. 2000 characters accommodates a paragraph of detailed tasting notes without being unbounded. These limits are generous in practice — they close a security gap without imposing any real constraint on legitimate use.

### 4.5 "Backward Compatibility" Section (AC-29)

Add as a new section after "Design Decisions":

```
## Backward Compatibility

v0.3 is a non-breaking additive change from v0.2, with one exception: the
`brewspec_version` const.

### What changed

| Change | Scope | Impact |
|--------|-------|--------|
| `brewspec_version` const updated to `"0.3"` | All files | v0.2 files fail the v0.3 schema |
| `equipment` object added | New field | Additive; v0.2 files without `equipment` are structurally valid |
| `ey` field added | New field | Additive; v0.2 files without `ey` are structurally valid |
| `maxLength` added to `method`, `grind`, `notes`, `coffee.varietal`, `coffee.process`, `coffee.origin` items | Existing fields | v0.2 files with values within these limits are unaffected |

### Which v0.2 files are affected by maxLength

A v0.2 file whose freeform string values exceed the new limits would fail
v0.3 validation. In practice this is extremely unlikely — the limits are
generous (100 characters for short phrases, 2000 for notes).

### Tools and version selection

Tools should read `brewspec_version` before selecting a schema. A file declaring
`brewspec_version: "0.2"` should be validated against the v0.2 schema only.
Do not validate a v0.2 file against the v0.3 schema.

### Migrating a v0.2 file to v0.3

1. Update `brewspec_version` from `"0.2"` to `"0.3"`.
2. (Optional) Trim any freeform string values that exceed the new maxLength limits
   (unlikely in practice).
3. Validate against the v0.3 schema.

No structural field changes are required. All v0.3 additions (`equipment`, `ey`)
are optional.
```

---

## 5. Example File Plan

### 5.1 Location Note

The test suite (`tests/test_brewspec_schema.py`) loads examples from the path `REPO_ROOT / "brewspec" / "spec" / "examples"`. However, the actual schema is at `src/brewlog/brewspec.schema.json` and the examples are at a path in the public repo structure. The dev must verify the actual example file locations by checking the path constants in the test file before updating or creating example files. The paths below describe the files by name; the dev determines the actual directory.

### 5.2 Existing Valid Examples — Version Bump and Additions Required

**`pour_over.yaml`** — Update `brewspec_version` to `"0.3"`. Add `equipment: { grinder: "Comandante C40 MK4", brewer: "Hario V60 02" }` and `ey: 20.5`. (AC-20, AC-21, AC-22)

Target additions to existing brew object:
```yaml
equipment:
  grinder: "Comandante C40 MK4"
  brewer: "Hario V60 02"
ey: 20.5
```

**`pour_over.json`** — Update `brewspec_version` to `"0.3"`. Add `equipment` and `ey` to match the YAML. (AC-20, AC-21, AC-22)

Target additions:
```json
"equipment": {
  "grinder": "Comandante C40 MK4",
  "brewer": "Hario V60 02"
},
"ey": 20.5
```

**`espresso.yaml`** — Update `brewspec_version` to `"0.3"`. Add `ey: 19.8` and `equipment: { grinder: "Niche Zero" }` (grinder only, no brewer). (AC-20, AC-22, AC-23)

Target additions:
```yaml
equipment:
  grinder: "Niche Zero"
ey: 19.8
```

**`multi_brew.yaml`** — Update `brewspec_version` to `"0.3"`. Add `equipment` to at least one brew (e.g., the first brew: `equipment: { grinder: "Comandante C40", brewer: "Hario V60" }`). (AC-20, AC-21)

**`immersion_minimal.yaml`** — Update `brewspec_version` to `"0.3"`. No other changes (demonstrates that `equipment` and `ey` omission is valid). (AC-20)

**`hybrid.yaml`** — Update `brewspec_version` to `"0.3"`. No other field changes required. (AC-20)

### 5.3 New Invalid Examples

**`invalid_equipment_field.yaml`** — New file. Brew with `equipment: { kettle: "Fellow Stagg EKG" }`. Fails `additionalProperties: false` on the `equipment` object. (AC-10, AC-24)

Target content:
```yaml
# This file demonstrates that unrecognised fields inside equipment are rejected.
# equipment only accepts: grinder, brewer. 'kettle' is not a valid field.
brewspec_version: "0.3"
brews:
  - date: "2026-02-19T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    equipment:
      kettle: "Fellow Stagg EKG"
```

Expected validation error: `Additional properties are not allowed ('kettle' was unexpected)`

**`ey_zero.yaml`** — New file. Brew with `ey: 0`. Fails `exclusiveMinimum: 0`. (AC-12, AC-25)

Target content:
```yaml
# This file demonstrates that ey: 0 is rejected (exclusiveMinimum: 0).
# Extraction yield must be a positive number.
brewspec_version: "0.3"
brews:
  - date: "2026-02-19T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    ey: 0
```

Expected validation error: `0 is less than or equal to the exclusive minimum of 0`

---

## 6. Test Strategy

### 6.1 Test File Overview

There are two relevant test files:

1. `tests/test_brewspec_schema.py` in the private monorepo — currently reflects v0.1 inline dicts throughout. This file must be updated comprehensively as part of v0.3.

2. The test file in the public `brewspec` repo (at the path referenced by `SCHEMA_PATH`, `VALID_DIR`, `INVALID_DIR` constants) — this is the file described in the v0.2 design. The v0.3 changes to the public repo test file follow the same patterns.

The v0.2 design specified changes to the public repo test file. The private repo test file (`tests/test_brewspec_schema.py`) was not updated during v0.2. For v0.3, the dev must update the private repo test file to reflect v0.2 structure first (as the v0.2 design specified), then apply the v0.3 additions. The Section 6.2 baseline establishes v0.2-correct inline dicts; Section 6.3 specifies carry-forward docstring fixes; Section 6.4 adds the new v0.3 tests.

### 6.2 Baseline Inline Dict Pattern

All existing tests that construct inline brew dicts must use v0.2 structure. The minimal valid brew dict for all tests is:

```python
VALID_BREW_V03 = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC_V03 = {"brewspec_version": "0.3", "brews": [VALID_BREW_V03]}
```

Every test that uses `"brewspec_version": "0.1"` with `"coffee": {"dose_g": 20}, "water": {"weight_g": 320}` must be updated to use `"brewspec_version": "0.3"` with `"dose_g": 20, "water_weight_g": 320` at the brew level.

The following existing tests require this update (version string and inline dict):
- `test_version_must_be_0_1` — rename to `test_version_must_be_0_3`; update const assertion to `"0.3"`; update inline brews to v0.3 structure
- `test_brews_must_be_nonempty_array` — update inline brews to v0.3 structure
- `test_required_brew_fields` — update inline brews to v0.3 structure; replace missing-coffee/missing-water assertions with missing-dose_g/missing-water_weight_g assertions; remove the `test_required_coffee_fields` and `test_required_water_fields` functions entirely
- `test_date_format_iso8601` — update inline brews to v0.3 structure; fix docstring (AC-1)
- `test_optional_fields_accepted` — update to v0.3 structure; fix docstring (AC-2)
- `test_minimal_brew_passes` — update to v0.3 structure
- `test_rating_range_1_to_5` — update inline brews to v0.3 structure; fix docstring (AC-4)
- `test_negative_values_rejected` — update to test `dose_g: -10` and `water_weight_g: -320` at brew level; remove nested coffee/water dict patterns
- `test_zero_weight_rejected` — update to test `dose_g: 0` and `water_weight_g: 0` at brew level
- `test_zero_duration_accepted` — REMOVE this test entirely (duration_s: 0 is invalid in v0.2+)
- `test_temperature_range` — update to test `water_temp_c` at brew level (not inside `water` dict)
- `test_type_enum_validation` — update inline brews to v0.3 structure
- `test_json_format_supported` — update inline brew dict to v0.3 structure; fix docstring (AC-3)
- `test_freeform_text_fields_not_empty` — update inline brews to v0.3 structure
- `test_additional_properties_rejected` — update inline brews to v0.3 structure

### 6.3 Carry-Forward Docstring Fixes (AC-1 through AC-4)

Apply the exact docstring text from Section 3. These are the only changes to those four functions; their test logic is correct.

### 6.4 New Test Functions (AC-30 and version check)

All new tests use the v0.3 minimal valid brew dict pattern. Add all of the following to `tests/test_brewspec_schema.py`:

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

### 6.5 Test Coverage Map (AC → Tests)

| AC | Test function(s) | What is verified |
|----|-----------------|-----------------|
| AC-1 (docstring fix: date) | `test_date_format_iso8601` — docstring updated | Docstring no longer cites AC number |
| AC-2 (docstring fix: optional fields) | `test_optional_fields_accepted` — docstring updated | Docstring no longer cites AC number |
| AC-3 (docstring fix: json format) | `test_json_format_supported` — docstring updated | Docstring no longer cites AC number |
| AC-4 (docstring fix: rating) | `test_rating_range_1_to_5` — docstring updated | Docstring no longer cites AC number |
| AC-5 (version const "0.2" rejected) | `test_version_const_rejects_v0_2` | `"0.2"` rejected by v0.3 schema |
| AC-6 (version const "0.3") | `test_version_must_be_0_3` (renamed) | `"0.3"` required; other values rejected |
| AC-7 (equipment object accepted) | `test_equipment_both_fields_accepted`, `test_equipment_empty_object_accepted`, `test_equipment_omitted_accepted` | Optional object; present or absent is valid |
| AC-8 (equipment fields) | `test_equipment_both_fields_accepted`, `test_equipment_grinder_only_accepted`, `test_equipment_brewer_only_accepted` | grinder and brewer fields work independently |
| AC-9 (equipment omitted or empty passes) | `test_equipment_omitted_accepted`, `test_equipment_empty_object_accepted` | Both cases pass |
| AC-10 (unknown equipment field rejected) | `test_equipment_unknown_field_rejected`, `test_invalid_examples_fail[invalid_equipment_field.yaml]` | additionalProperties: false enforced |
| AC-11 (ey valid) | `test_ey_valid_value_accepted` | ey: 20.1 passes |
| AC-12 (ey: 0 and ey: -1 rejected) | `test_ey_zero_rejected`, `test_ey_negative_rejected`, `test_invalid_examples_fail[ey_zero.yaml]` | exclusiveMinimum: 0 enforced |
| AC-13 (ey flat on brew object) | `test_ey_valid_value_accepted` — ey at top level of brew dict | ey is not nested |
| AC-14 (method maxLength 100) | `test_method_maxlength_boundary` | 100 passes; 101 fails |
| AC-15 (grind maxLength 100) | `test_grind_maxlength_boundary` | 100 passes; 101 fails |
| AC-16 (notes maxLength 2000) | `test_notes_maxlength_boundary` | 2000 passes; 2001 fails |
| AC-17 (coffee.varietal maxLength 100) | `test_coffee_varietal_maxlength_boundary` | 100 passes; 101 fails |
| AC-18 (coffee.process maxLength 100) | `test_coffee_process_maxlength_boundary` | 100 passes; 101 fails |
| AC-19 (coffee.origin item maxLength 100) | `test_coffee_origin_item_maxlength_boundary` | 100 passes; 101 fails |
| AC-20 (existing examples updated to 0.3) | `test_valid_examples_pass` (parametrized) | All valid example files pass v0.3 schema |
| AC-21 (example with equipment both fields) | `test_valid_examples_pass[pour_over.yaml]` | pour_over.yaml includes grinder + brewer |
| AC-22 (example with ey) | `test_valid_examples_pass[pour_over.yaml]`, `test_valid_examples_pass[espresso.yaml]` | Examples include ey |
| AC-23 (example with one equipment field) | `test_valid_examples_pass[espresso.yaml]` | espresso.yaml has grinder only |
| AC-24 (invalid_equipment_field.yaml) | `test_invalid_examples_fail[invalid_equipment_field.yaml]` | File with kettle field fails |
| AC-25 (ey_zero.yaml) | `test_invalid_examples_fail[ey_zero.yaml]` | File with ey: 0 fails |
| AC-26 (brewspec-v0.3.md field reference) | Spec document review only | Human-readable spec content |
| AC-27 (What Changed section) | Spec document review only | What Changed section present |
| AC-28 (Design Decisions section) | Spec document review only | Design rationale present |
| AC-29 (Backward Compatibility section) | Spec document review only | Migration guidance present |
| AC-30 (test suite) | All new test functions in Section 6.4 | Full v0.3 constraint coverage |

---

## 7. Pydantic Model Changes (`src/brewlog/models.py`)

The BrewLog CLI Pydantic models (`src/brewlog/models.py`) must be updated to match the v0.3 schema. These changes ensure the CLI's input validation layer is consistent with the schema's constraints. The `validate_document()` function in `schema.py` is the primary validation gate; the Pydantic models are a secondary layer for CLI-specific input.

### 7.1 New `EquipmentInput` Model

Add after `WaterInput`:

```python
class EquipmentInput(BaseModel):
    """Optional equipment descriptor. All fields optional."""

    grinder: Optional[str] = None
    brewer: Optional[str] = None

    @field_validator("grinder", "brewer")
    @classmethod
    def validate_equipment_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v
```

### 7.2 Updates to Existing Models

**`CoffeeInput` — add maxLength validators:**

```python
@field_validator("varietal", "process")
@classmethod
def validate_min_length_1(cls, v: Optional[str]) -> Optional[str]:
    # Replace existing validator with one that also checks maxLength
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty")
        if len(v) > 100:
            raise ValueError("value must not exceed 100 characters")
    return v

@field_validator("origin")
@classmethod
def validate_origin(cls, v: Optional[list[str]]) -> Optional[list[str]]:
    if v is not None:
        if len(v) == 0:
            raise ValueError("origin must have at least one entry")
        for item in v:
            if not isinstance(item, str) or len(item.strip()) == 0:
                raise ValueError("each origin entry must be a non-empty string")
            if len(item) > 100:
                raise ValueError("each origin entry must not exceed 100 characters")
    return v
```

**`BrewInput` — add `ey` field and `equipment` field; update `method`/`grind`/`notes` validators to check maxLength:**

Add to the optional fields section:
```python
equipment: Optional[EquipmentInput] = None
ey: Optional[float] = None
```

Update the `validate_exclusive_positive` validator to include `ey`:
```python
@field_validator("water_volume_ml", "tds", "ey")
@classmethod
def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("value must be greater than 0")
    return v
```

Update the `validate_nonempty_text` validator to check maxLength:
```python
@field_validator("method", "grind", "notes")
@classmethod
def validate_nonempty_text(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        max_lengths = {"notes": 2000}
        # method and grind default to 100; notes is 2000
        # Pydantic does not pass field name to field_validator by default;
        # use a model_validator or separate validators per field for exact limits
    return v
```

Note to dev: the `validate_nonempty_text` validator does not receive the field name, so exact per-field maxLength checking requires either separate validators per field or a `model_validator`. The simplest approach is to split the validator:

```python
@field_validator("method", "grind")
@classmethod
def validate_short_text(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        if len(v) > 100:
            raise ValueError("value must not exceed 100 characters")
    return v

@field_validator("notes")
@classmethod
def validate_notes(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        if len(v) > 2000:
            raise ValueError("notes must not exceed 2000 characters")
    return v
```

The schema (`validate_document()`) is the authoritative validation gate; the Pydantic validators are the CLI input layer. Both must be consistent with v0.3 constraints.

---

## 8. File Layout: Files to Create or Modify

The developer should confirm exact paths by reading `tests/test_brewspec_schema.py` path constants and the public repo structure. The files below are identified by their role and name.

### 8.1 Files to Modify

| File | What Changes | AC(s) |
|------|-------------|-------|
| `src/brewlog/brewspec.schema.json` | Full v0.3 schema (Section 2 verbatim) | AC-5, AC-6, AC-7–AC-19 |
| `src/brewlog/models.py` | Add `EquipmentInput`; update `BrewInput` with `ey`, `equipment`, `maxLength` validators; update `CoffeeInput` with `maxLength` validators | v0.3 constraint parity |
| `tests/test_brewspec_schema.py` | Carry-forward docstring fixes; inline dict updates to v0.3; new test functions (Section 6.4) | AC-1–AC-4, AC-30 |
| `[public repo]/brewspec.schema.json` | Same as `src/brewlog/brewspec.schema.json` — kept in sync | AC-5, AC-6, AC-7–AC-19 |
| `[public repo]/examples/valid/pour_over.yaml` | Version bump; add `equipment` (both fields); add `ey` | AC-20, AC-21, AC-22 |
| `[public repo]/examples/valid/pour_over.json` | Version bump; add `equipment` and `ey` | AC-20, AC-21, AC-22 |
| `[public repo]/examples/valid/espresso.yaml` | Version bump; add `equipment` (grinder only); add `ey` | AC-20, AC-22, AC-23 |
| `[public repo]/examples/valid/multi_brew.yaml` | Version bump; add `equipment` to one brew | AC-20, AC-21 |
| `[public repo]/examples/valid/immersion_minimal.yaml` | Version bump only | AC-20 |
| `[public repo]/examples/valid/hybrid.yaml` | Version bump only | AC-20 |
| `[public repo]/brewspec-v0.2.md` | Produce as `brewspec-v0.3.md` with all changes from Section 4 | AC-26, AC-27, AC-28, AC-29 |
| `[public repo]/tests/test_brewspec_schema.py` | Same carry-forward, inline dict, and new test additions as private repo test file | AC-1–AC-4, AC-30 |

### 8.2 Files to Create

| File | What It Is | AC(s) |
|------|-----------|-------|
| `[public repo]/examples/invalid/invalid_equipment_field.yaml` | Invalid example: equipment with unknown field `kettle` | AC-10, AC-24 |
| `[public repo]/examples/invalid/ey_zero.yaml` | Invalid example: `ey: 0` | AC-12, AC-25 |
| `[public repo]/brewspec-v0.3.md` | New canonical spec document | AC-26, AC-27, AC-28, AC-29 |

### 8.3 TDD Order

1. Update `tests/test_brewspec_schema.py`: apply carry-forward docstring fixes; update all inline dicts to v0.3 structure; add all new test functions from Section 6.4. Run — tests that reference the schema version or new fields will fail.

2. Update `src/brewlog/brewspec.schema.json` with the full v0.3 schema from Section 2. Run — schema-level tests should now pass; example-file tests will fail until examples are updated.

3. Update existing valid example files (version bumps and additions as per Section 5.2).

4. Create new invalid example files (`invalid_equipment_field.yaml`, `ey_zero.yaml`) as per Section 5.3.

5. Run tests — all should pass.

6. Update `src/brewlog/models.py` with `EquipmentInput` and updated validators (Section 7). Run `tests/test_models.py` — model tests should pass.

7. Produce `brewspec-v0.3.md` (public repo spec document) with all changes from Section 4.

---

## 9. Edge Cases and Developer Notes

### 9.1 `ey` — Computed vs. Recorded Field

The spec does not designate `ey` as computed or recorded. Tools may calculate `ey` from `dose_g`, `water_weight_g`, and `tds` (using the standard formula), or users may enter a measured value directly. The schema treats `ey` as a plain optional number — it accepts any positive value regardless of whether it is mathematically consistent with `tds`, `dose_g`, and `water_weight_g`.

**The schema does not enforce consistency between `ey`, `tds`, `dose_g`, and `water_weight_g`.** A file where `ey: 99.9` with `tds: 0.5` is schema-valid even though it is physically implausible. Application-layer tools may optionally warn about implausible combinations, but the schema's role is format enforcement only, not physical plausibility.

### 9.2 `equipment` Empty Object

`equipment: {}` is valid per AC-9. An empty `equipment` object is structurally equivalent to omitting the `equipment` key entirely — both produce a brew record with no equipment information. Tools should treat both cases identically when reading brew records.

### 9.3 `maxLength` Interaction with `minLength`

All freeform string fields that gain `maxLength` already had `minLength: 1`. The v0.3 constraint is that valid strings are `[1, max_length]` characters inclusive. An empty string (`""`) fails `minLength: 1`. A string of exactly `max_length` characters passes. A string of `max_length + 1` characters fails.

Edge case: strings consisting entirely of whitespace pass the schema (e.g., `"   "` has length 3, satisfies `minLength: 1`). The Pydantic model layer uses `v.strip()` to catch whitespace-only values at the CLI input layer. The schema does not enforce this — consistent with v0.2 behaviour.

### 9.4 `additionalProperties: false` on `$defs.equipment`

If a tool is processing a v0.3 file that has `equipment: { grinder: "Comandante", kettle: "Fellow Stagg" }`, the entire document fails validation. The `kettle` field is not listed in the `$defs.equipment` properties, and `additionalProperties: false` means no unlisted properties are permitted. This is intentional and consistent with how `coffee` and `water` work. Tools should validate documents before processing them.

### 9.5 Version Const and BrewLog CLI Dependency

The manifest shows `brewlog-cli-v0.1` with `depends_on: [brewspec-v0.2]` and `artifacts.design: specs/designs/brewlog-cli-v0.1.md`. The CLI design was written against v0.2. When BrewLog CLI v0.1 is implemented, the developer should target the v0.3 schema (the current version) rather than v0.2, as the CLI is not yet in production. The `src/brewlog/brewspec.schema.json` file will be v0.3 after this task completes.

The Pydantic models in `src/brewlog/models.py` are part of the private monorepo and must be updated alongside the schema (Section 7). The public repo schema file and test file are separate — the dev applies equivalent changes to both.

---

## 10. Security Considerations

### 10.1 Input Validation Rules

All new v0.3 fields follow the same validation pattern as existing fields: schema validation via `Draft202012Validator.validate()` is the first gate; no data reaches application logic without passing the schema.

| Field | Risk | Schema Mitigation | Application-Layer Note |
|-------|------|------------------|-----------------------|
| `equipment.grinder` | Pathologically long string before v0.3; potential injection if interpolated into shell commands | `minLength: 1, maxLength: 100` | Must be stored and displayed as plain text only. Never interpolated into shell, SQL template strings, or HTML without escaping |
| `equipment.brewer` | Same as `grinder` | `minLength: 1, maxLength: 100` | Same as `grinder` |
| `ey` | Non-positive value; no physical meaning | `exclusiveMinimum: 0` | Application may optionally warn when `ey` is outside the typical 18–22% specialty range; do not reject schema-valid values at application layer |
| All freeform strings with new `maxLength` | Memory exhaustion from unbounded strings in imported files | `maxLength` now enforced at schema level | The v0.2 security note flagging "no maxLength" as a low-concern issue is resolved by v0.3 for all affected fields |

### 10.2 Trust Boundary

The trust boundary is unchanged from v0.2:

```
User-supplied file (YAML or JSON)
  → Path validation (reject ../traversal, check extension)
  → File size check (reject > limit; recommended: 10MB)
  → Safe parser: yaml.safe_load() or json.load()
  → Schema validation: Draft202012Validator.validate()
  → Application logic (read fields, store, display)
```

`yaml.safe_load()` must be used for all YAML parsing. This is unchanged from v0.2. The test suite must verify the `load_example_file()` helper continues to use `yaml.safe_load()`.

### 10.3 `additionalProperties: false` as a Security Control

The `additionalProperties: false` constraint on `$defs.equipment` (and on `$defs.coffee`, `$defs.water`, and the root object) is a defence-in-depth measure: it prevents unexpected data from entering the object graph through an unlisted field. This is not just a data quality concern — it prevents tool builders from accidentally processing an unvalidated field that was injected by a malicious file. The v0.3 schema maintains this property on every object.

### 10.4 No Sensitive Data

`equipment.grinder` and `equipment.brewer` are commercially available product names. No PII, API keys, credentials, or authentication tokens are introduced by v0.3. Example values ("Comandante C40 MK4", "Niche Zero", "Hario V60 02") are publicly available product names. `ey` is a numeric measurement with no privacy implication.

---

## 11. Acceptance Criteria Verification

| AC | Addressed in | Design location |
|----|-------------|-----------------|
| AC-1 (docstring: date) | Section 3.1 — exact replacement text | Carry-forward fixes |
| AC-2 (docstring: optional fields) | Section 3.2 — exact replacement text | Carry-forward fixes |
| AC-3 (docstring: json format) | Section 3.3 — exact replacement text | Carry-forward fixes |
| AC-4 (docstring: rating) | Section 3.4 — exact replacement text | Carry-forward fixes |
| AC-5 (version const rejects "0.2") | Sections 1.1, 2 — schema diff, full schema | Schema diff, annotated schema |
| AC-6 (version const "0.3", title updated) | Sections 1.1, 2 — root-level changes | Schema diff, annotated schema |
| AC-7 (equipment optional object) | Sections 1.2, 1.4, 2 — brew $def, equipment $def, full schema | Schema diff, annotated schema |
| AC-8 (equipment fields: grinder, brewer) | Sections 1.4, 2 — equipment $def | Schema diff, annotated schema |
| AC-9 (equipment omitted or empty passes) | Sections 1.4, 6.4 — equipment $def, test functions | Schema diff, test strategy |
| AC-10 (unknown equipment field rejected) | Sections 1.4, 5.3, 6.4 — additionalProperties: false, invalid example, test | Schema diff, examples, test strategy |
| AC-11 (ey valid) | Sections 1.2, 2, 6.4 — ey in brew $def, full schema, test | Schema diff, annotated schema, test strategy |
| AC-12 (ey: 0 and ey: -1 rejected) | Sections 1.2, 5.3, 6.4 — exclusiveMinimum: 0, invalid example, tests | Schema diff, examples, test strategy |
| AC-13 (ey flat on brew object) | Sections 1.2, 2 — ey at brew level in $defs.brew | Schema diff, annotated schema |
| AC-14 (method maxLength 100) | Sections 1.2, 2, 6.4 — brew $def, full schema, test | Schema diff, annotated schema, test strategy |
| AC-15 (grind maxLength 100) | Sections 1.2, 2, 6.4 | Schema diff, annotated schema, test strategy |
| AC-16 (notes maxLength 2000) | Sections 1.2, 2, 6.4 | Schema diff, annotated schema, test strategy |
| AC-17 (coffee.varietal maxLength 100) | Sections 1.3, 2, 6.4 | Schema diff, annotated schema, test strategy |
| AC-18 (coffee.process maxLength 100) | Sections 1.3, 2, 6.4 | Schema diff, annotated schema, test strategy |
| AC-19 (coffee.origin item maxLength 100) | Sections 1.3, 2, 6.4 | Schema diff, annotated schema, test strategy |
| AC-20 (existing examples updated) | Section 5.2 — all six valid example updates | Example file plan |
| AC-21 (example with equipment both fields) | Section 5.2 — pour_over.yaml additions | Example file plan |
| AC-22 (example with ey) | Section 5.2 — pour_over.yaml and espresso.yaml | Example file plan |
| AC-23 (example with one equipment field) | Section 5.2 — espresso.yaml (grinder only) | Example file plan |
| AC-24 (invalid_equipment_field.yaml) | Section 5.3 — new invalid example | Example file plan |
| AC-25 (ey_zero.yaml) | Section 5.3 — new invalid example | Example file plan |
| AC-26 (brewspec-v0.3.md field reference) | Section 4.2 — complete field reference tables | Spec document changes |
| AC-27 (What Changed section) | Section 4.3 — What Changed content | Spec document changes |
| AC-28 (Design Decisions section) | Section 4.4 — four new design decision entries | Spec document changes |
| AC-29 (Backward Compatibility section) | Section 4.5 — backward compatibility content | Spec document changes |
| AC-30 (test suite) | Section 6.4 — 16 new test functions; Section 6.3 — 4 docstring fixes | Test strategy |
