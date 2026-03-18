# Design: BrewSpec v0.2

**Feature:** brewspec-v0.2
**Author:** architect
**Created:** 2026-02-18
**Input:** specs/products/brewspec-v0.2.md
**Status:** Ready for Dev

---

## 1. JSON Schema Diff (v0.1 → v0.2)

This section specifies every change to `brewspec.schema.json`. The dev applies these changes to produce the v0.2 schema. Each change is labelled with the AC it satisfies.

### 1.1 Root-Level Changes

| Location | v0.1 Value | v0.2 Value | AC |
|----------|-----------|-----------|-----|
| `$id` | `"https://brewspec.org/schema/v0.1/brewspec.schema.json"` | `"https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json"` | AC-6 |
| `title` | `"BrewSpec v0.1"` | `"BrewSpec v0.2"` | AC-5 |
| `properties.brewspec_version.const` | `"0.1"` | `"0.2"` | AC-5 |
| `properties.brewspec_version.description` | `"The BrewSpec version. Must be \"0.1\"."` | `"The BrewSpec version. Must be \"0.2\"."` | AC-5 |

### 1.2 `$defs.brew` Changes

**`required` array — replace entirely:**

```
v0.1: ["date", "type", "coffee", "water"]
v0.2: ["date", "type", "dose_g", "water_weight_g"]
```

Rationale: `coffee` and `water` become optional objects (AC-9, AC-10). `dose_g` and `water_weight_g` are now required top-level brew fields (AC-7, AC-8).

**Properties added to `$defs.brew`:**

| Property | Type | Constraint | AC |
|----------|------|------------|-----|
| `dose_g` | number | `exclusiveMinimum: 0` | AC-7 |
| `water_weight_g` | number | `exclusiveMinimum: 0` | AC-8 |
| `water_volume_ml` | number | `exclusiveMinimum: 0` | AC-8 |
| `water_temp_c` | number | `minimum: 0, maximum: 100` | AC-8 |
| `tds` | number | `exclusiveMinimum: 0` | AC-15 |

**Properties unchanged in `$defs.brew`:** `date`, `type`, `method`, `grind`, `rating`, `notes`

**`duration_s` constraint change:**

```
v0.1: "minimum": 0,  "description": "Brew duration in seconds. Zero is valid for instant methods."
v0.2: "exclusiveMinimum": 0,  "description": "Brew duration in seconds. Must be > 0."
```

AC-14.

**`coffee` property in brew — unchanged reference:** still `"$ref": "#/$defs/coffee"`. The brew `coffee` property continues to point to the `coffee` $def, but that $def is restructured (see 1.3).

**`water` property in brew — unchanged reference:** still `"$ref": "#/$defs/water"`. The brew `water` property continues to point to the `water` $def, but that $def is restructured (see 1.4).

### 1.3 `$defs.coffee` Changes — Full Replacement

The entire `coffee` $def is replaced. In v0.1 it contained `dose_g` as a required field. In v0.2 it is an optional ingredient descriptor with no required fields.

```
v0.1 coffee $def:
  required: ["dose_g"]
  additionalProperties: false
  properties:
    dose_g: {type: number, exclusiveMinimum: 0}

v0.2 coffee $def:
  (no required array — all fields optional)
  additionalProperties: false
  properties:
    roast_date: {type: string, pattern: "^\d{4}-\d{2}-\d{2}$"}
    type: {type: string, enum: ["single_origin", "blend"]}
    origin: {type: array, minItems: 1, items: {type: string, minLength: 1}}
    varietal: {type: string, minLength: 1}
    process: {type: string, minLength: 1}
```

AC-9, AC-11.

### 1.4 `$defs.water` Changes — Full Replacement

The entire `water` $def is replaced. In v0.1 it contained `weight_g`, `volume_ml`, `temp_c`. In v0.2 those fields move to the brew level and the `water` object becomes an optional ingredient descriptor containing only `ppm`.

```
v0.1 water $def:
  required: ["weight_g"]
  additionalProperties: false
  properties:
    weight_g: {type: number, exclusiveMinimum: 0}
    volume_ml: {type: number, exclusiveMinimum: 0}
    temp_c: {type: number, minimum: 0, maximum: 100}

v0.2 water $def:
  (no required array — all fields optional)
  additionalProperties: false
  properties:
    ppm: {type: number, minimum: 0}
```

AC-10, AC-12.

---

## 2. Full Annotated v0.2 Schema

This is the complete target `brewspec.schema.json` as it must look after all changes. The dev writes this file verbatim to the public repo.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json",
  "title": "BrewSpec v0.2",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.2",
      "description": "The BrewSpec version. Must be \"0.2\"."
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
        "grind": {
          "type": "string",
          "minLength": 1,
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
            "minLength": 1
          },
          "description": "Origin country or region(s). Array supports blends with multiple origins.",
          "examples": [["Ethiopia"], ["Ethiopia", "Colombia"]]
        },
        "varietal": {
          "type": "string",
          "minLength": 1,
          "description": "Coffee variety or cultivar. Freeform.",
          "examples": ["Heirloom", "Gesha", "Bourbon"]
        },
        "process": {
          "type": "string",
          "minLength": 1,
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
    }
  }
}
```

### Schema Design Decisions (v0.2)

| Decision | Rationale | Traces to |
|----------|-----------|-----------|
| `dose_g` required at brew level, not inside `coffee` | Brew quantity is a parameter of the brew act, not a property of the coffee ingredient | AC-7, PM design notes |
| `water_weight_g` required at brew level; `water_volume_ml`, `water_temp_c` optional at brew level | Same separation: brew quantities are brew-level; `water` object describes the ingredient | AC-8, PM design notes |
| `water_` prefix on brew-level water fields | Retains semantic association with water without nesting; `dose_g` has no prefix because the brew context makes "dose" unambiguously a coffee dose | AC-8, PM design notes |
| `coffee` and `water` objects become optional, no required fields | Ingredient descriptor is optional detail; the brew can be recorded without knowing coffee metadata | AC-9, AC-10 |
| `coffee.origin` as array of strings, `minItems: 1` | Supports blends natively; single-origin is `["Ethiopia"]`; empty array is invalid | AC-11, PM design notes |
| `coffee.type` enum inside `coffee` object | Avoids collision with `brew.type`; the `coffee` namespace makes the field unambiguous | AC-11, PM design notes |
| `roast_date` as plain date string `YYYY-MM-DD` | Roasters label bags by day only; full datetime would imply precision that does not exist | AC-11, PM design notes |
| `ppm` under `water` object, `minimum: 0` | `ppm` of 0 is technically valid (pure water); `exclusiveMinimum` would be incorrect | AC-12 |
| `tds` at brew level, not nested in a `result` object | One field does not warrant a wrapping object; grouping deferred to v0.3+ if `ey` is added | AC-15, PM design notes |
| `duration_s` changed to `exclusiveMinimum: 0` | Zero duration is a data entry error; no valid brew method has zero contact time | AC-14 |
| `const: "0.2"` on `brewspec_version` | Exact match enforces versioning; v0.1 files are rejected by v0.2 schema, enabling clean per-version validation | AC-5 |

---

## 3. Spec Document Changes (brewspec-v0.1.md → brewspec-v0.2.md)

The dev produces `brewspec-v0.2.md` in the public repo by updating `brewspec-v0.1.md`. The following sections change. All other sections (File Format, Enumerations, Validation code examples, License) are preserved with edits noted below.

### 3.1 Header

```
v0.1:  # BrewSpec v0.1 / Status: Stable / Version: 0.1 / Last Updated: 2026-02-15
v0.2:  # BrewSpec v0.2 / Status: Stable / Version: 0.2 / Last Updated: 2026-02-18
```

### 3.2 Overview — Scope Section

Remove this paragraph from "What v0.1 defers":

> Coffee metadata (origin, roaster, roast date), Water chemistry (TDS, pH, minerals), Extraction metrics (TDS, extraction percentage)

Replace with: those items have been added in v0.2. Update the deferred list to reflect what v0.2 still defers (equipment fields, pour schedules, tasting dimensions, extraction yield, water chemistry beyond ppm).

### 3.3 File Format — Array-Only Example

Update the inline code example to v0.2 structure:

```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
```

### 3.4 Field Reference Tables — Full Replacement

Replace all three field reference tables with the v0.2 versions below.

**Top-Level Fields** (unchanged from v0.1):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.2"` | The BrewSpec version |
| `brews` | array | Required | Minimum 1 element | Array of brew objects |

**Brew Object:**

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Required | ISO 8601 UTC: `YYYY-MM-DDTHH:MM:SSZ` | Brew timestamp | `"2026-02-15T08:30:00Z"` |
| `type` | string | Required | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Required | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Required | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `method` | string | Optional | Min length 1 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `grind` | string | Optional | Min length 1 | Freeform grind description | `"medium-fine"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `rating` | integer | Optional | 1–5 inclusive | Brew rating. 1 = poor, 5 = excellent | `4` |
| `notes` | string | Optional | Min length 1 | Freeform tasting or session notes | `"Bright acidity"` |

**Coffee Object** (entire object is optional; all fields within are optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roast_date` | string | Optional | Pattern `YYYY-MM-DD` | Roast date. Plain date, no time. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Coffee classification | `"single_origin"` |
| `origin` | array of strings | Optional | Min 1 item; each item min length 1 | Origin(s). Multiple entries for blends. | `["Ethiopia"]`, `["Ethiopia", "Colombia"]` |
| `varietal` | string | Optional | Min length 1 | Coffee variety or cultivar. Freeform. | `"Heirloom"`, `"Gesha"` |
| `process` | string | Optional | Min length 1 | Processing method. Freeform. | `"Washed"`, `"Natural"` |

**Water Object** (entire object is optional; all fields within are optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

### 3.5 Validation Section — Code Examples

Update both Python `open()` calls to include `encoding='utf-8'` (AC-2). The v0.1 spec already has this in the published version. Confirm the examples remain correct after the schema file path is unchanged.

### 3.6 Design Decisions Section

Add the following new entries. Existing entries are preserved (array-only, freeform text, metric units, ISO 8601, snake_case, 1-5 rating, weight over volume). Remove the "Why minimum duration is 0, not > 0?" entry and replace with the correction entry.

**New entry: Why are brew quantities at the brew level, not inside ingredient objects?**

Decision: `dose_g`, `water_weight_g`, `water_volume_ml`, and `water_temp_c` are direct properties of the brew object. The `coffee` and `water` objects describe the ingredient, not the brew parameters.

Rationale: A coffee dose is a parameter of the brew act — you dose differently for a V60 and an espresso even when using the same coffee. `origin`, `roast_date`, and `varietal` describe the coffee itself — they are the same regardless of brew method. Mixing ingredient identity with brew-specific quantities (as v0.1 did) produces a model that becomes increasingly incoherent as coffee metadata is added. v0.2 corrects this while adoption is near-zero.

Changed from v0.1: This is a breaking change. v0.1 files require migration (see Backward Compatibility).

**New entry: Why `water_` prefix on brew-level water fields?**

Decision: Brew-level water quantity fields are named `water_weight_g`, `water_volume_ml`, `water_temp_c` — prefixed with `water_`.

Rationale: The prefix retains semantic association with water without nesting the fields in an object. `dose_g` carries no prefix because the brew context makes "dose" unambiguously a coffee dose — no other ingredient in the spec is measured by dose.

**New entry: Why is `coffee.origin` an array?**

Decision: `coffee.origin` is an array of strings (`minItems: 1`), not a plain string.

Rationale: This supports blends where multiple origins are known (`["Ethiopia", "Colombia"]`) without requiring a separate field. For single-origin coffees, the array has one entry. An empty array is not valid. This is forward-compatible with blend metadata without a schema change.

**New entry: Why is `roast_date` a plain date (not a datetime)?**

Decision: `roast_date` uses format `YYYY-MM-DD`, not the full ISO 8601 datetime used by `date`.

Rationale: Roasters label bags by day only. A full datetime (`2026-01-20T00:00:00Z`) would imply time-of-day precision that does not exist in practice and would make manual entry unnecessarily verbose. The spec uses two date formats intentionally: `date` (brew timestamp, needs UTC precision for sorting and deduplication) and `roast_date` (ingredient label, day precision is sufficient). The field name and table notes make this distinction explicit.

**New entry: Why is `tds` a flat brew-level field, not nested in a `result` object?**

Decision: `tds` is placed at the same level as `rating` and `notes`, not inside a `result: {}` wrapper.

Rationale: A single field does not warrant a wrapping object. A `result` object would add structural complexity without adding clarity at this stage. If v0.3 adds extraction yield (`ey`) or other result fields, grouping can be introduced then. Adding a wrapper object for a single field in v0.2 would produce premature structure.

**New entry: Why was `duration_s: 0` corrected to require `> 0`?**

Decision: `duration_s` uses `exclusiveMinimum: 0`. Zero is no longer valid.

Rationale: v0.1 set `minimum: 0` with the rationale that instant methods might have zero brew time. That rationale does not hold — even the fastest espresso shot has a non-zero contact time, and a recorded duration of zero is almost certainly a data entry error. `exclusiveMinimum: 0` is consistent with all other positive-value fields in the schema. This is a breaking change from v0.1 only for files that recorded `duration_s: 0`.

**New entry: Why does `coffee.type` not conflict with `brew.type`?**

Decision: The `coffee.type` field (values: `single_origin`, `blend`) lives inside the `coffee` object. The `brew.type` field (values: `immersion`, `pour_over`, `espresso`, `hybrid`) lives at the brew level. They are distinct fields with distinct semantics.

Rationale: The namespacing is handled naturally by JSON/YAML object nesting. Tool builders should access `brew.type` and `brew.coffee.type` — or in code, `brew["type"]` and `brew["coffee"]["type"]` — which are unambiguous. The spec document and field reference tables make this clear by documenting them in separate sections.

**Remove and replace:** "Why minimum duration is 0, not > 0?" entry is replaced by the correction entry above.

### 3.7 Backward Compatibility Section (New)

Add as a new section after "Design Decisions" and before "Future Versions":

```
## Backward Compatibility

v0.2 is a breaking change from v0.1. v0.1 files are valid against the v0.1 schema
only and will fail validation against the v0.2 schema.

### What changed

| v0.1 field | v0.2 field | Notes |
|---|---|---|
| `coffee.dose_g` (inside coffee object) | `dose_g` (brew level) | Required; moved out of `coffee` object |
| `water.weight_g` (inside water object) | `water_weight_g` (brew level) | Required; renamed and moved |
| `water.volume_ml` (inside water object) | `water_volume_ml` (brew level) | Optional; renamed and moved |
| `water.temp_c` (inside water object) | `water_temp_c` (brew level) | Optional; renamed and moved |
| `brewspec_version: "0.1"` | `brewspec_version: "0.2"` | Must be updated |
| `duration_s: 0` | Not valid in v0.2 | Must be corrected or removed |

### Why this change was made now

The v0.1 data model conflated ingredient identity with brew-specific quantities.
This becomes increasingly incoherent as coffee metadata grows. The fix is made in
v0.2 while adoption is near-zero and no production tooling has been built against v0.1.
Deferring this correction would entrench a confusing model and require a more
costly migration later.

### Migrating v0.1 files

Tools should validate `brewspec_version` before selecting a schema and must not
attempt to validate v0.1 files against the v0.2 schema.

To migrate a v0.1 file:

1. Change `brewspec_version` from `"0.1"` to `"0.2"`
2. Move `coffee.dose_g` to `dose_g` at the brew level; remove the `coffee` key if it has no other fields
3. Move `water.weight_g` to `water_weight_g` at the brew level
4. Move `water.volume_ml` (if present) to `water_volume_ml` at the brew level
5. Move `water.temp_c` (if present) to `water_temp_c` at the brew level
6. Remove the `water` key if it has no other fields (or retain it if you are adding `ppm`)
7. If any brew has `duration_s: 0`, remove or correct the value
```

### 3.8 Contributing Section — Add Repository URL

Add the repository URL in the Contributing section (AC-4):

```
BrewSpec repository: https://github.com/coffee-standards/brewspec
```

### 3.9 Future Versions Section

Update to reflect what v0.2 has shipped and what remains deferred:

Remove from the "v0.2 candidates" list: coffee metadata, water chemistry (TDS). Update to:

```
v0.3 candidates:
- Standardized enumerations for method/grind (based on v0.2 usage data)
- Equipment fields (grinder model, numeric grind setting)
- Pour schedules and step-by-step timing
- Tasting dimensions (SCA-style cupping scores)
- Extraction yield (ey field), likely alongside a result object grouping with tds
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
```

---

## 4. Example File Plan

### 4.1 Existing Valid Examples — Changes Required

All existing valid examples change in the same two ways: (1) `brewspec_version` updated from `"0.1"` to `"0.2"`, and (2) brew structure updated to v0.2 flat field layout.

**`examples/valid/pour_over.yaml`** — Update to v0.2 structure; add full `coffee` object (all 5 metadata fields), `water.ppm`, `tds`. Demonstrates: required fields, all coffee metadata, ppm, tds, all 5 coffee metadata fields populated. (AC-16, AC-17, AC-19)

Target content:
```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 20
    water_weight_g: 320
    water_volume_ml: 320
    water_temp_c: 96
    coffee:
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    water:
      ppm: 150
    grind: "medium-fine"
    duration_s: 180
    tds: 1.38
    rating: 4
    notes: "Bright acidity, slightly under-extracted"
```

**`examples/valid/pour_over.json`** — Same brew as `pour_over.yaml` in JSON format. Updated to v0.2 structure with identical field values. (AC-16)

Target content:
```json
{
  "brewspec_version": "0.2",
  "brews": [
    {
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
    }
  ]
}
```

**`examples/valid/immersion_minimal.yaml`** — Required fields only. No `coffee` object, no `water` object. Demonstrates: minimum valid v0.2 file; `coffee` object omitted entirely is valid. (AC-16, AC-20)

Target content:
```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-14T07:00:00Z"
    type: "immersion"
    dose_g: 30
    water_weight_g: 500
```

**`examples/valid/espresso.yaml`** — Espresso with `rating`, `notes`, `tds`. No `coffee` object (demonstrates optional). (AC-16, AC-19)

Target content:
```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-13T06:45:00Z"
    type: "espresso"
    method: "Breville Barista Express"
    dose_g: 18
    water_weight_g: 36
    water_temp_c: 93
    grind: "fine, setting 5"
    duration_s: 28
    tds: 8.5
    rating: 5
    notes: "Thick crema, balanced sweetness"
```

**`examples/valid/multi_brew.yaml`** — 3 brews. Mix of with/without `coffee` object; brew 1 has `coffee` (single origin), brew 2 has `coffee` with a blend (2 origins), brew 3 has no `coffee` object. Demonstrates: multi-brew, blend with multiple origins, optional `coffee` object. (AC-16, AC-18)

Target content:
```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 20
    water_weight_g: 320
    water_temp_c: 96
    coffee:
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
    rating: 4
  - date: "2026-02-14T07:00:00Z"
    type: "immersion"
    method: "French press"
    dose_g: 30
    water_weight_g: 500
    coffee:
      type: "blend"
      origin: ["Ethiopia", "Colombia"]
    rating: 3
  - date: "2026-02-13T06:45:00Z"
    type: "espresso"
    dose_g: 18
    water_weight_g: 36
```

### 4.2 New Valid Example

**`examples/valid/hybrid.yaml`** — New file. AeroPress brew (`type: "hybrid"`). Includes `coffee` object with a blend (`type: "blend"`, two origins), `water.ppm`, `tds`, `rating`, `notes`. Demonstrates: hybrid brew type, blend with multiple origins, water ppm, tds. (AC-1, AC-16, AC-18, AC-19)

Target content:
```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-18T07:15:00Z"
    type: "hybrid"
    method: "AeroPress inverted"
    dose_g: 15
    water_weight_g: 200
    water_temp_c: 85
    coffee:
      roast_date: "2026-02-01"
      type: "blend"
      origin: ["Ethiopia", "Colombia"]
      varietal: "Mixed"
      process: "Natural"
    water:
      ppm: 75
    grind: "medium"
    duration_s: 120
    tds: 1.55
    rating: 4
    notes: "Smooth and sweet, slightly fruity from the Ethiopian component"
```

### 4.3 New Invalid Examples

**`examples/invalid/v0.1_format.yaml`** — v0.1 structure with `coffee.dose_g` nested inside `coffee` object and `water.weight_g` nested inside `water` object. The file declares `brewspec_version: "0.2"` to make clear it is attempting v0.2 validation. Fails because `dose_g` is not a recognized property of the v0.2 `coffee` $def (`additionalProperties: false`), and `weight_g` is not a recognized property of the v0.2 `water` $def, and the brew object is missing the required `dose_g` and `water_weight_g` fields. (AC-13, AC-21)

Target content:
```yaml
# This file demonstrates the v0.1 data structure, which is invalid against the v0.2 schema.
# dose_g nested inside coffee and weight_g inside water are not valid in v0.2.
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
```

Expected validation errors: `dose_g` is not a valid property of `coffee` (additionalProperties false); `weight_g` is not a valid property of `water` (additionalProperties false); `dose_g` is a required property of `brew` (missing); `water_weight_g` is a required property of `brew` (missing).

**`examples/invalid/zero_duration.yaml`** — `duration_s: 0`. Fails `exclusiveMinimum: 0` constraint. (AC-21)

Target content:
```yaml
# duration_s: 0 is invalid in v0.2. Use exclusiveMinimum: 0 — duration must be > 0.
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "espresso"
    dose_g: 18
    water_weight_g: 36
    duration_s: 0
```

Expected validation error: `0 is less than or equal to the exclusive minimum of 0`

### 4.4 Existing Invalid Examples — Updates Required

The existing invalid examples in `examples/invalid/` use the v0.1 structure (`coffee.dose_g`, `water.weight_g`). They must be updated to use the v0.2 structure for all fields except the one being tested, and `brewspec_version` must be updated to `"0.2"`. Each file's single invalid condition is preserved; only the valid surrounding fields are migrated.

| File | What the file tests | Required update |
|------|--------------------|----|
| `missing_version.yaml` | Missing `brewspec_version` | Update brew structure: remove `coffee.dose_g`, add `dose_g`; remove `water.weight_g`, add `water_weight_g`. Do not add `brewspec_version`. |
| `missing_required_field.yaml` | Brew missing `date` | Update brew structure; keep `date` missing. |
| `invalid_type_enum.yaml` | `type: "drip"` | Update brew structure; keep invalid `type`. |
| `rating_out_of_range.yaml` | `rating: 6` | Update brew structure; keep `rating: 6`. |
| `negative_weight.yaml` | Negative dose value | Update to `dose_g: -10` at brew level (tests negative `dose_g`); `water_weight_g: 320` at brew level. Update `brewspec_version` to `"0.2"`. |
| `empty_brews_array.yaml` | `brews: []` | Update `brewspec_version` to `"0.2"`. No brew structure to change. |

---

## 5. Test Strategy

### 5.1 Test File Structure

Single file: `tests/test_brewspec_schema.py`

The dev updates this file by: (1) adding `ids=lambda f: f.name` to both parametrize decorators; (2) updating all inline brew dicts in existing tests to v0.2 structure; (3) removing tests that specifically validated v0.1 structure that no longer applies; (4) adding all new test functions listed below.

### 5.2 Parametrize Fix (AC-3)

Both parametrized decorators must add `ids=lambda f: f.name`:

```python
# Before (v0.1):
@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")))

# After (v0.2):
@pytest.mark.parametrize("example_file", sorted(VALID_DIR.glob("*.yaml")) + sorted(VALID_DIR.glob("*.json")), ids=lambda f: f.name)
```

```python
# Before (v0.1):
@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")))

# After (v0.2):
@pytest.mark.parametrize("example_file", sorted(INVALID_DIR.glob("*.yaml")), ids=lambda f: f.name)
```

### 5.3 Existing Tests — Required Updates

All existing test functions that construct inline brew dicts must be updated to v0.2 field structure. The minimal valid v0.2 brew dict used across tests is:

```python
# v0.2 minimal valid brew
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.2", "brews": [VALID_BREW]}
```

The following tests must replace all inline `"coffee": {"dose_g": 20}, "water": {"weight_g": 320}` patterns with `"dose_g": 20, "water_weight_g": 320`:

- `test_version_must_be_0_2` (rename from `test_version_must_be_0_1`; update const value asserted from `"0.1"` to `"0.2"`)
- `test_brews_must_be_nonempty_array`
- `test_required_brew_fields` — update the "all required fields present" case; the "missing coffee" and "missing water" cases are removed (coffee and water are no longer required); replace with "missing dose_g" and "missing water_weight_g" assertions
- `test_required_coffee_fields` — remove entirely (coffee is no longer required; `dose_g` has moved)
- `test_required_water_fields` — remove entirely (water is no longer required; `water_weight_g` has moved)
- `test_date_format_iso8601` — update brew dict to v0.2
- `test_optional_fields_accepted` — update to v0.2 structure; `coffee` and `water` objects updated to v0.2 fields
- `test_minimal_brew_passes` — update to v0.2 (remove `coffee` and `water` objects entirely)
- `test_rating_range_1_to_5` — update brew dict to v0.2
- `test_negative_values_rejected` — update to test `dose_g: -10` at brew level, `water_weight_g: -320` at brew level; test negative `water_volume_ml` at brew level; remove references to nested `coffee`/`water` dicts
- `test_zero_weight_rejected` — update to test `dose_g: 0` at brew level, `water_weight_g: 0` at brew level
- `test_zero_duration_accepted` — REMOVE this test entirely; replace with `test_zero_duration_rejected` (see 5.4)
- `test_temperature_range` — update to test `water_temp_c` at brew level (not inside `water` dict)
- `test_type_enum_validation` — update brew dict to v0.2
- `test_json_format_supported` — update inline brew dict to v0.2
- `test_freeform_text_fields_not_empty` — update brew dict to v0.2
- `test_additional_properties_rejected` — update brew dict to v0.2

### 5.4 New Test Functions

Add all of the following new tests to `tests/test_brewspec_schema.py`:

```python
def test_version_const_rejects_v0_1(validator):
    """AC-5: brewspec_version '0.1' is rejected by the v0.2 schema."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.1",
            "brews": [{"date": "2026-02-15T08:30:00Z", "type": "pour_over",
                       "dose_g": 20, "water_weight_g": 320}]
        })
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

```python
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
```

### 5.5 Test Coverage Map (AC → Tests)

| AC | Test function(s) | What is verified |
|----|-----------------|-----------------|
| AC-1 (hybrid example) | `test_valid_examples_pass[hybrid.yaml]` (parametrized) | `hybrid.yaml` passes schema validation |
| AC-2 (encoding) | Spec document review only; no schema test | Code examples use `encoding='utf-8'` |
| AC-3 (parametrize ids) | All parametrized tests | Test output shows file names, not indexes |
| AC-4 (repo URL) | Spec document review only; no schema test | URL visible in spec and README |
| AC-5 (version const) | `test_version_must_be_0_2`, `test_version_const_rejects_v0_1` | `"0.2"` accepted; `"0.1"` and others rejected |
| AC-6 ($id) | `test_schema_is_valid_draft_2020_12` (checks `$schema`); $id is a schema property | $id present in schema JSON |
| AC-7 (dose_g at brew level) | `test_dose_g_required_at_brew_level`, `test_zero_weight_rejected`, `test_negative_values_rejected` | `dose_g` required, > 0 |
| AC-8 (water fields at brew level) | `test_water_weight_g_required_at_brew_level`, `test_temperature_range`, `test_negative_values_rejected` | `water_weight_g` required; optional fields work |
| AC-9 (coffee optional) | `test_coffee_object_optional` | Brew without `coffee` passes |
| AC-10 (water optional) | `test_water_object_optional` | Brew without `water` passes |
| AC-11 (coffee metadata fields) | `test_coffee_origin_multi_entry_accepted`, `test_coffee_origin_empty_array_rejected`, `test_coffee_type_enum_valid`, `test_coffee_type_enum_invalid`, `test_roast_date_plain_date_accepted`, `test_roast_date_datetime_rejected` | All coffee metadata constraints |
| AC-12 (water.ppm) | `test_water_ppm_zero_accepted`, `test_water_ppm_negative_rejected` | ppm >= 0 |
| AC-13 (v0.1 format rejected) | `test_v0_1_format_rejected`, `test_invalid_examples_fail[v0.1_format.yaml]` | Nested v0.1 structure fails |
| AC-14 (duration_s correction) | `test_zero_duration_rejected`, `test_positive_duration_accepted` | 0 rejected; 1 accepted |
| AC-15 (tds field) | `test_tds_valid_value_accepted`, `test_tds_zero_rejected`, `test_tds_negative_rejected` | tds > 0 |
| AC-16–AC-21 (examples) | `test_valid_examples_pass` (parametrized), `test_invalid_examples_fail` (parametrized) | All example files pass/fail as expected |
| AC-22–AC-24 (spec document) | Spec document review only | Human-readable spec content |
| AC-25 (test suite) | All new tests above | Full v0.2 constraint coverage |

---

## 6. Migration Notes

### What breaks between v0.1 and v0.2

v0.2 is a breaking change. Any v0.1 file will fail validation against the v0.2 schema. The following changes are incompatible:

**1. Structural restructure (breaking for all v0.1 files)**

Every v0.1 brew record has `coffee.dose_g` nested inside a `coffee` object and `water.weight_g` nested inside a `water` object. In v0.2:

- `dose_g` is a required property of the brew object itself. It no longer exists inside `coffee`.
- `water_weight_g` is a required property of the brew object itself. It no longer exists inside `water`.
- `water_volume_ml` (if present) moves from `water.volume_ml` to `water_volume_ml` at brew level.
- `water_temp_c` (if present) moves from `water.temp_c` to `water_temp_c` at brew level.
- The `coffee` object in v0.2 does not accept `dose_g` (`additionalProperties: false`); passing a v0.1 `coffee: {dose_g: 20}` block will produce two errors: an additionalProperties error on `coffee.dose_g` and a required-property error for the missing `dose_g` at the brew level.
- The `water` object in v0.2 does not accept `weight_g`, `volume_ml`, or `temp_c`; passing these will produce additionalProperties errors.

**2. Version constant (breaking)**

`brewspec_version: "0.1"` fails the `const: "0.2"` constraint. Every v0.1 file must update this field.

**3. duration_s: 0 (breaking for affected files only)**

Files with `duration_s: 0` fail the `exclusiveMinimum: 0` constraint. Only files that recorded a zero duration are affected.

### Why this is acceptable at this stage

- BrewSpec v0.1 shipped on 2026-02-17. No production tooling has been built against it.
- The BrewLog CLI has not shipped. There are no user-generated v0.1 files in production.
- The v0.1 data model conflation of ingredient identity and brew quantities would require a more costly migration later if left uncorrected.
- All six v0.1 example files are migrated in this release, providing a complete reference for the migration pattern.
- The Backward Compatibility section in `brewspec-v0.2.md` documents the exact field-by-field migration steps.

### Tools that need to handle both versions

Tools that may encounter both v0.1 and v0.2 files should:

1. Parse the file (YAML or JSON) with a safe parser
2. Read `brewspec_version` before selecting a schema
3. If `brewspec_version == "0.1"`, validate against the v0.1 schema
4. If `brewspec_version == "0.2"`, validate against the v0.2 schema
5. Do not attempt to validate a v0.1 file against the v0.2 schema or vice versa

The BrewLog CLI (when built) should detect the version and either migrate files automatically or prompt the user to migrate.

---

## 7. Security Considerations

### Input Validation

All validation rules are specified at the schema level. No data should reach application logic without passing `Draft202012Validator.validate()`.

| Field | Risk | Schema Mitigation | Application-Layer Note |
|-------|------|------------------|-----------------------|
| `coffee.origin` (array of strings) | Pathologically long strings; unexpected array contents | Each item: `type: string, minLength: 1`; no `maxLength` | Enforce reasonable length limit (e.g., 255 chars) at application layer before display or storage |
| `coffee.varietal`, `coffee.process`, `notes`, `method`, `grind` | HTML injection if displayed in a web UI | Schema enforces string type and `minLength: 1`; no execution possible | HTML-escape before rendering in any web context |
| `roast_date` pattern | Month 13, day 32 pass the regex pattern `^\d{4}-\d{2}-\d{2}$` | Schema enforces structure only | Validate calendar correctness at application layer if needed |
| `tds`, `ppm` | No maximum; `tds: 9999` is schema-valid | Schema enforces `exclusiveMinimum: 0` (tds) and `minimum: 0` (ppm) | Apply display sanity limits (e.g., flag `tds > 20` as unusual) at application layer |
| `water_temp_c` | Already bounded 0-100 by schema | `minimum: 0, maximum: 100` enforced | No additional application layer check needed |

### Safe Parsing

`yaml.safe_load()` must be used for all YAML parsing. `yaml.load()` enables arbitrary Python object instantiation and must never be used. This rule is unchanged from v0.1 and must be verified in the updated test suite's `load_example_file()` function.

### File I/O Safety (unchanged from v0.1)

- Validate file paths before open/read. Reject paths with `..` traversal.
- Set file size limit before parsing (recommended: 10MB) to prevent memory exhaustion from oversized arrays.
- Handle encoding errors gracefully; expect UTF-8.
- Open files with `encoding='utf-8'` explicitly (this is the correction in AC-2).

### Trust Boundary

```
User-supplied file (YAML or JSON)
  → Path validation (reject ../traversal, check extension)
  → File size check (reject > limit)
  → Safe parser: yaml.safe_load() or json.load()
  → Schema validation: Draft202012Validator.validate()
  → Application logic (read fields, store, display)
```

No user data reaches application logic without passing all four gates. This is unchanged from v0.1.

### No Sensitive Data

No PII, API keys, credentials, or authentication in any example file. Example values (`"Ethiopia"`, `"Colombia"`, `"Heirloom"`) are public geographic names and standard coffee industry terms. `tds` and `ppm` are numeric measurements with no privacy implication.

---

## 8. Implementation Checklist for backend-dev

TDD order: tests first, then implementation. Do not write schema or example files until the tests exist and are failing.

1. Update `tests/test_brewspec_schema.py`:
   - Add `ids=lambda f: f.name` to both parametrize decorators
   - Update all inline brew dicts to v0.2 structure (replace `coffee.dose_g`/`water.weight_g` with flat fields)
   - Remove `test_zero_duration_accepted`
   - Remove `test_required_coffee_fields` and `test_required_water_fields`
   - Rename `test_version_must_be_0_1` to `test_version_must_be_0_2`; update assertion
   - Update `test_required_brew_fields` to test missing `dose_g` and `water_weight_g` instead of missing `coffee`/`water`
   - Add all new test functions from Section 5.4
   - Run tests — they should fail (schema not yet updated)

2. Update `brewspec.schema.json` using the complete v0.2 schema from Section 2 verbatim.
   - Run tests — meta-validation and inline-dict tests should now pass; example-file tests will still fail (files not yet updated)

3. Update existing valid example files (`pour_over.yaml`, `pour_over.json`, `immersion_minimal.yaml`, `espresso.yaml`, `multi_brew.yaml`) to v0.2 structure using content from Section 4.1.

4. Create new valid example file `examples/valid/hybrid.yaml` using content from Section 4.2.

5. Update existing invalid example files to v0.2 surrounding structure per Section 4.4.

6. Create new invalid example files (`examples/invalid/v0.1_format.yaml`, `examples/invalid/zero_duration.yaml`) using content from Section 4.3.
   - Run tests — all should pass

7. Update spec document: rename `brewspec-v0.1.md` → `brewspec-v0.2.md`; apply all changes from Section 3. Update `README.md` to add repository URL.

---

## 9. Acceptance Criteria Verification

| AC | Addressed in | Design location |
|----|-------------|-----------------|
| AC-1 (hybrid example) | Section 4.2 — `hybrid.yaml` target content | Example file plan |
| AC-2 (encoding='utf-8') | Section 3.5 — Validation code examples note | Spec document changes |
| AC-3 (ids=lambda f: f.name) | Section 5.2 — parametrize fix | Test strategy |
| AC-4 (repo URL in spec) | Section 3.8 — Contributing section | Spec document changes |
| AC-5 (version const "0.2") | Sections 1.1, 2 — root-level changes, full schema | Schema diff, annotated schema |
| AC-6 ($id GitHub raw URL) | Sections 1.1, 2 — root-level changes, full schema | Schema diff, annotated schema |
| AC-7 (dose_g at brew level, required) | Sections 1.2, 2 — brew $def changes | Schema diff, annotated schema |
| AC-8 (water_weight_g required; water_volume_ml, water_temp_c optional at brew level) | Sections 1.2, 2 — brew $def changes | Schema diff, annotated schema |
| AC-9 (coffee optional) | Sections 1.2, 2 — required array change | Schema diff, annotated schema |
| AC-10 (water optional) | Sections 1.2, 2 — required array change | Schema diff, annotated schema |
| AC-11 (coffee metadata fields) | Sections 1.3, 2 — coffee $def replacement | Schema diff, annotated schema |
| AC-12 (water.ppm) | Sections 1.4, 2 — water $def replacement | Schema diff, annotated schema |
| AC-13 (v0.1 format rejected) | Sections 4.3, 5.4 — invalid example + test | Example plan, test strategy |
| AC-14 (duration_s exclusiveMinimum) | Sections 1.2, 2 — brew $def changes | Schema diff, annotated schema |
| AC-15 (tds field) | Sections 1.2, 2 — tds property in brew $def | Schema diff, annotated schema |
| AC-16 (existing examples updated) | Section 4.1 — all 5 existing valid examples | Example file plan |
| AC-17 (coffee object with multiple metadata fields) | Section 4.1 — `pour_over.yaml` target content | Example file plan |
| AC-18 (blend with multiple origins) | Sections 4.1, 4.2 — `multi_brew.yaml`, `hybrid.yaml` | Example file plan |
| AC-19 (water.ppm and tds in an example) | Sections 4.1, 4.2 — `pour_over.yaml`, `hybrid.yaml` | Example file plan |
| AC-20 (coffee omitted entirely) | Section 4.1 — `immersion_minimal.yaml` | Example file plan |
| AC-21 (invalid examples: v0.1_format, zero_duration) | Section 4.3 | Example file plan |
| AC-22 (brewspec-v0.2.md as canonical spec) | Section 3 — full spec document changes | Spec document changes |
| AC-23 (backward compatibility section) | Section 3.7 | Spec document changes |
| AC-24 (design decisions section) | Section 3.6 | Spec document changes |
| AC-25 (test suite) | Sections 5.2, 5.3, 5.4 | Test strategy |
