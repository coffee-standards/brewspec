# Design: BrewSpec v0.6

**Feature:** brewspec-v0.6
**Author:** architect
**Created:** 2026-03-03
**Input:** specs/products/brewspec-v0.6.md
**Baseline:** specs/designs/brewspec-v0.5.md
**Status:** Ready for Dev

---

## Overview

This document specifies every schema, test, and file change required to produce BrewSpec v0.6. v0.6 is a stability release with four breaking schema changes, one additive schema change, and five carry-forward fixes from the v0.5 review.

Breaking changes:
1. `equipment.grinder_setting` type changes from `string` to `number` (`exclusiveMinimum: 0`), enabling numeric queries and cross-grinder normalisation tooling.
2. `water_volume_ml` is removed from the brew object — the field is redundant with `water_weight_g` and adds no precision value.
3. `coffee.process` is removed from the top-level coffee object — process is semantically correct only at the origin level for blends.
4. `coffee.varietal` is removed from the top-level coffee object.

Additive changes (non-breaking):
5. `coffee.origins[].varietal` is added as a new optional `string` field inside each origin entry, placing varietal where it belongs: attached to the specific origin it describes.
6. `coffee.name` is added as a new optional `string` field on the top-level `coffee` object. It serves as a branded product name or human-readable descriptive label (e.g., `"Ethiopia Yirgacheffe"`, `"Blue Bottle Hayes Valley Espresso"`). Resolves the previously deferred `blend_name` item.

Carry-forward fixes from v0.5 review: MED-1 (README stale references), MED-2 (`import_.py` version message + test), MED-4 (`export.py` docstring), MED-5 (`equipment.yaml` Yirgacheffe classification).

Note on `export.py` target version (open question from spec, AC-27): BrewLog v0.6 will adopt the v0.6 schema. The `export.py` module docstring must be updated to state `v0.6-compliant`. The `document = {"brewspec_version": "0.5", ...}` line in `export.py` must also be updated to `"0.6"`. The bundled schema copy at `src/brewlog/brewspec.schema.json` must be updated to v0.6 simultaneously so the post-serialisation validation passes.

The `brewspec_version` const advances from `"0.5"` to `"0.6"`.

The dev must follow the TDD order in Section 9: write failing tests first, then implement schema changes, then update examples and CLI code.

---

## 1. JSON Schema Diff (v0.5 to v0.6)

This section specifies every change to `brewspec.schema.json`. The full target schema is in Section 2. Apply changes in the order listed.

### 1.1 Root-Level Changes

| Location | v0.5 Value | v0.6 Value | AC |
|----------|-----------|-----------|-----|
| `title` | `"BrewSpec v0.5"` | `"BrewSpec v0.6"` | AC-1 |
| `properties.brewspec_version.const` | `"0.5"` | `"0.6"` | AC-1 |
| `properties.brewspec_version.description` | `"The BrewSpec version. Must be \"0.5\"."` | `"The BrewSpec version. Must be \"0.6\"."` | AC-1 |

The `$schema` and `$id` values are unchanged.

### 1.2 `$defs.brew` Changes

**Removed field: `water_volume_ml`**

Remove the following property from `$defs.brew.properties` entirely:

```json
// REMOVE from $defs.brew.properties:
"water_volume_ml": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Water volume in milliliters. Optional. Must be > 0 if present."
}
```

Because `$defs.brew` carries `additionalProperties: false`, any document with a `water_volume_ml` key at the brew level will automatically fail v0.6 validation. No additional schema keyword is needed. (AC-10, AC-11)

All other `$defs.brew` properties are unchanged: `date`, `type`, `method`, `dose_g`, `water_weight_g`, `brew_ratio`, `water_temp_c`, `coffee`, `water`, `equipment`, `grind`, `duration_s`, `notes`, `result`.

### 1.3 `$defs.equipment` Changes

**Changed field: `grinder_setting`**

Replace the current `grinder_setting` string definition with a number definition:

```json
// BEFORE (v0.5):
"grinder_setting": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Grinder dial position or click setting used for this brew. Freeform; grinder setting systems are incompatible across brands.",
  "examples": ["21", "21 clicks", "3.2.1", "setting 21"]
}

// AFTER (v0.6):
"grinder_setting": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Grinder dial position or click setting used for this brew. Must be a positive number. Encoding convention: integer for primary increment grinders (e.g. 21 on a Comandante C40); decimal tenths for grinders with sub-steps between primary positions (e.g. 5.2 on a Fellow Ode Gen 2 means primary position 5, second sub-step). The schema does not enforce decimal precision — this convention is guidance for consistent encoding, not a constraint."
}
```

The field remains optional. The `equipment` object continues to enforce `additionalProperties: false`. (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9)

### 1.4 `$defs.coffee` Changes

**Removed field: `process`**

Remove the following property from `$defs.coffee.properties` entirely:

```json
// REMOVE from $defs.coffee.properties:
"process": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Processing method. Freeform. ...",
  "examples": ["Washed", "Natural", "Honey"]
}
```

Because `$defs.coffee` carries `additionalProperties: false`, any document with a `coffee.process` key will automatically fail v0.6 validation. (AC-12, AC-15)

**Removed field: `varietal`**

Remove the following property from `$defs.coffee.properties` entirely:

```json
// REMOVE from $defs.coffee.properties:
"varietal": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Coffee variety or cultivar. Freeform.",
  "examples": ["Heirloom", "Gesha", "Bourbon"]
}
```

Because `$defs.coffee` carries `additionalProperties: false`, any document with a `coffee.varietal` key will automatically fail v0.6 validation. (AC-13)

**New field: `name`**

Add the following property to `$defs.coffee.properties`, before `roast_date`:

```json
"name": {
  "type": "string",
  "minLength": 1,
  "maxLength": 150,
  "description": "A branded product name or human-readable descriptive label for the coffee (e.g. 'Ethiopia Yirgacheffe', 'Blue Bottle Hayes Valley Espresso', 'Estate'). Optional. Not required even when origins[] is populated. New in v0.6.",
  "examples": ["Ethiopia Yirgacheffe", "Blue Bottle Hayes Valley Espresso", "Estate"]
}
```

The field is optional. The coffee object continues to enforce `additionalProperties: false`. (AC-40, AC-41, AC-42, AC-43)

After removing `process` and `varietal` and adding `name`, `$defs.coffee.properties` contains: `name`, `roast_date`, `type`, `origins`.

### 1.5 `$defs.origin` Changes

**New field: `varietal`**

Add the following property to `$defs.origin.properties`, after the existing `harvest_year` property:

```json
"varietal": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Coffee varietal for this origin entry. Freeform. Records the coffee variety or cultivar specific to this component (e.g. Heirloom, Gesha, Bourbon). New in v0.6.",
  "examples": ["Heirloom", "Gesha", "Bourbon", "Catuai", "SL28"]
}
```

The field is optional on each origin entry. The origin object continues to enforce `additionalProperties: false`. After this change, the only accepted fields in an origin entry are: `name`, `country`, `region`, `subregion`, `producer`, `process`, `lot`, `harvest_year`, `varietal`. (AC-16, AC-17, AC-18, AC-19, AC-20)

---

## 2. Full Annotated v0.6 Schema

This is the complete target `brewspec.schema.json`. The dev writes this verbatim to `brewspec.schema.json` in the public repo and to `src/brewlog/brewspec.schema.json` in the CLI package (both copies must stay in sync).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json",
  "title": "BrewSpec v0.6",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.6",
      "description": "The BrewSpec version. Must be \"0.6\"."
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
          "oneOf": [
            {
              "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
              "description": "Full ISO 8601 UTC datetime."
            },
            {
              "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
              "description": "Date-only in YYYY-MM-DD format."
            }
          ],
          "description": "Brew date. Accepts YYYY-MM-DD (date-only) or YYYY-MM-DDTHH:MM:SSZ (full UTC datetime).",
          "examples": ["2026-02-21", "2026-02-15T08:30:00Z"]
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
        "brew_ratio": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Water-to-coffee ratio expressed as a single float (grams of water per gram of coffee). e.g. 15.5 represents 15.5:1 or approximately 64g/L. Can be computed from water_weight_g / dose_g. When both are present, tools should validate consistency; mismatches should be surfaced as a warning, not a schema error."
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
          "enum": ["turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"],
          "description": "Grind size. Standard vocabulary from finest to coarsest: turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse."
        },
        "duration_s": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Brew duration in seconds. Must be > 0."
        },
        "notes": {
          "type": "string",
          "minLength": 1,
          "maxLength": 2000,
          "description": "Brew-process notes — operational observations about the preparation (e.g. 'washed filter paper', 'water from Brita filter', 'grinder re-calibrated'). For sensory description, use result.tasting_notes."
        },
        "result": {
          "$ref": "#/$defs/result"
        }
      }
    },
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
    },
    "origin": {
      "type": "object",
      "additionalProperties": false,
      "description": "A single origin record within a coffee.origins array. All fields optional. Supports single-origin and blend records.",
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Descriptive name for this origin component. Plays the same role at the component level as coffee.name does at the coffee level. For single-origin coffees it will typically match coffee.name; for blends it is the name of this specific component (e.g. 'Brazil Natural', 'Colombia Washed').",
          "examples": ["Ethiopia Yirgacheffe Natural", "Brazil Natural", "Colombia Washed"]
        },
        "country": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Country of production.",
          "examples": ["Ethiopia", "Colombia", "Brazil"]
        },
        "region": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "State, province, or named growing region within the country.",
          "examples": ["Yirgacheffe", "Huila", "Minas Gerais"]
        },
        "subregion": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "District, zone, or sub-area within the region.",
          "examples": ["Kochere", "Pitalito"]
        },
        "producer": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Farm, estate, cooperative, or washing station name.",
          "examples": ["Daye Bensa Washing Station", "Fazenda Santa Ines"]
        },
        "process": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Green coffee processing method at origin. Distinct from the removed brew-level coffee.process field.",
          "examples": ["Washed", "Natural", "Honey"]
        },
        "lot": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Lot or batch identifier from the producer.",
          "examples": ["Lot 42", "Export Grade 1"]
        },
        "harvest_year": {
          "type": "integer",
          "minimum": 1900,
          "maximum": 2100,
          "description": "Year the crop was harvested. Four-digit integer.",
          "examples": [2025, 2024]
        },
        "varietal": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Coffee varietal for this origin entry. Freeform. Records the coffee variety or cultivar specific to this component (e.g. Heirloom, Gesha, Bourbon). New in v0.6.",
          "examples": ["Heirloom", "Gesha", "Bourbon", "Catuai", "SL28"]
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
        },
        "grinder_setting": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Grinder dial position or click setting used for this brew. Must be a positive number. Encoding convention: integer for primary increment grinders (e.g. 21 on a Comandante C40); decimal tenths for grinders with sub-steps between primary positions (e.g. 5.2 on a Fellow Ode Gen 2 means primary position 5, second sub-step). The schema does not enforce decimal precision — this convention is guidance for consistent encoding, not a constraint."
        },
        "notes": {
          "type": "string",
          "minLength": 1,
          "maxLength": 2000,
          "description": "Equipment state notes — observations about maintenance, calibration, filter type, or burr age. Distinct from brew-level notes, which record preparation observations.",
          "examples": ["Burrs replaced 2026-01", "AeroPress rubber seal replaced"]
        }
      }
    },
    "result": {
      "type": "object",
      "additionalProperties": false,
      "description": "Optional brew outcome descriptor. Groups measurements and sensory evaluation. All fields optional.",
      "properties": {
        "tds": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Total dissolved solids percentage of the finished brew. Must be > 0 if present."
        },
        "ey": {
          "type": "number",
          "exclusiveMinimum": 0,
          "description": "Extraction yield as a percentage (e.g., 20.1 for 20.1%). Must be > 0 if present. No maximum enforced."
        },
        "brix": {
          "type": "number",
          "minimum": 0,
          "description": "Dissolved sugar content in degrees Brix. A value of 0 is valid (distilled water). Must be >= 0 if present."
        },
        "tasting_notes": {
          "type": "string",
          "minLength": 1,
          "maxLength": 2000,
          "description": "Sensory description of the brew (e.g. 'Bright citrus acidity, caramel sweetness, clean finish'). For brew-process notes, use the top-level notes field."
        },
        "ratings": {
          "$ref": "#/$defs/ratings"
        }
      }
    },
    "ratings": {
      "type": "object",
      "additionalProperties": false,
      "description": "Optional multi-dimensional sensory ratings. Dimensions align with SCA cupping protocol. All fields optional integers 1-5.",
      "properties": {
        "overall": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Holistic impression. 1 = poor, 5 = excellent."
        },
        "fragrance": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Dry grounds aroma before water is added."
        },
        "aroma": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Wet aroma after water is added."
        },
        "flavour": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Taste and aroma experienced during drinking."
        },
        "aftertaste": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Length and quality of positive flavour attributes after swallowing."
        },
        "acidity": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Quality (not quantity) of acidity; brightness."
        },
        "sweetness": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Perceived sweetness."
        },
        "mouthfeel": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "description": "Tactile sensation; body and texture."
        }
      }
    }
  }
}
```

---

## 3. Data Models

### 3.1 Pydantic Models

The Pydantic models in `models.py` are used by the BrewLog CLI for in-process validation. They must be updated to reflect the v0.6 schema changes.

**OriginInput** — add `varietal`, remove nothing (origins already had no `process` at coffee level):

```python
class OriginInput(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    producer: Optional[str] = None
    process: Optional[str] = None
    lot: Optional[str] = None
    harvest_year: Optional[int] = None
    varietal: Optional[str] = None  # new in v0.6

    model_config = ConfigDict(extra="forbid")
```

**CoffeeInput** — remove `process` and `varietal`; add `name`:

```python
class CoffeeInput(BaseModel):
    name: Optional[str] = None          # new in v0.6; branded or descriptive label
    roast_date: Optional[str] = None
    type: Optional[Literal["single_origin", "blend"]] = None
    origins: Optional[list[OriginInput]] = None
    # process: removed in v0.6
    # varietal: removed in v0.6

    model_config = ConfigDict(extra="forbid")
```

**EquipmentInput** — change `grinder_setting` from `Optional[str]` to `Optional[float]`:

```python
class EquipmentInput(BaseModel):
    grinder: Optional[str] = None
    brewer: Optional[str] = None
    grinder_setting: Optional[float] = None   # was Optional[str] in v0.5; float accepts both int and float inputs
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
```

**BrewInput** — remove `water_volume_ml`:

```python
class BrewInput(BaseModel):
    date: str
    type: Literal["immersion", "pour_over", "espresso", "hybrid"]
    dose_g: float
    water_weight_g: float
    brew_ratio: Optional[float] = None
    # water_volume_ml: removed in v0.6
    water_temp_c: Optional[float] = None
    coffee: Optional[CoffeeInput] = None
    water: Optional[WaterInput] = None
    equipment: Optional[EquipmentInput] = None
    grind: Optional[Literal["turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"]] = None
    duration_s: Optional[float] = None
    notes: Optional[str] = None
    result: Optional[ResultInput] = None
    method: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
```

The complete model file is not shown in full here — only changed models are specified. Fields and classes not listed above are unchanged from v0.5. The dev must update the models accordingly and confirm no other references to `water_volume_ml`, `coffee.process`, or `coffee.varietal` exist in the CLI code.

### 3.2 SQLite Schema

The BrewLog CLI SQLite schema does not have a separate column for `water_volume_ml`, `coffee.process`, or `coffee.varietal` as top-level fields — these are serialised into JSON columns. The schema change therefore has no DDL impact on the SQLite table definitions.

The `grinder_setting` column in the `brews` table stores the value as a TEXT column (the CLI serialises/deserialises it). In v0.6, when a user provides `grinder_setting` via the CLI, the value is a float. The TEXT column can store the numeric string representation without a DDL change. However, the dev should verify the `add` and `update` commands accept a numeric value for `--grinder-setting` (previously freeform string — the CLI option type should change from `str` to `float`). This is a CLI-layer concern, not a schema concern — but must be caught during dev review of the add/update command flags.

**No DDL changes are required.** State explicitly: SQLite schema is unchanged in v0.6.

---

## 4. Architecture Decision Records

No new ADRs are required for this release. All four breaking changes are schema-level refinements that follow the established pattern of using `additionalProperties: false` to enforce field removal (same pattern used for `coffee.origin` removal in v0.5). The decision to use `number` type with `exclusiveMinimum: 0` for grinder_setting is straightforward — no meaningful alternatives exist for a numeric-only field.

---

## 5. Public Spec Document

The dev must produce `brewspec-v0.6.md` in the public brewspec repo alongside the schema. Before writing the new spec doc, archive the previous version: copy `brewspec-v0.5.md` to `versions/brewspec-v0.5.md`, then overwrite `brewspec-v0.6.md` at the repo root.

### 5.1 Structure

The spec document must include these sections in order:

1. **Overview** — What BrewSpec is; one paragraph; version scope updated to v0.6
2. **Field Reference** — Table of all fields with type, required/optional, constraints, description. Updated tables for: Brew Object (no `water_volume_ml`), Coffee Object (no `process`, no `varietal`; add `name` — `type: string`, `minLength: 1`, `maxLength: 150`, optional), Origin Object (add `varietal`; update `name` description to reflect its relationship to `coffee.name`), Equipment Object (`grinder_setting` type changed to number)
3. **What Changed in v0.6** — See Section 5.2
4. **Validation** — Guidance unchanged from v0.5 (validate at storage time)
5. **Backward Compatibility** — See Section 5.3

### 5.2 "What Changed in v0.6" Section Content

The spec document's "What Changed" section must cover each of the following items:

**Version bump**
`brewspec_version` const updated from `"0.5"` to `"0.6"`. Schema title updated to `"BrewSpec v0.6"`. Files declaring `brewspec_version: "0.5"` are rejected by the v0.6 schema.

**`equipment.grinder_setting` type changed: string to number**
`grinder_setting` changes from a freeform string to a positive number (`exclusiveMinimum: 0`). This enables numeric queries, averages, and range filtering across brew logs without string parsing.

Encoding convention (guidance, not enforced by schema):
- Integer = primary increment position (e.g., `21` for 21 clicks on a Comandante C40)
- Float with one decimal place = primary increment with sub-step (e.g., `5.2` on a Fellow Ode Gen 2 means primary position 5, second sub-step — the Ode Gen 2 has three sub-steps between each primary position: 5.1, 5.2, 5.3)

Cross-grinder normalisation (mapping "21 on a Comandante" to an equivalent on a Fellow Ode) is an application-layer concern requiring a reference dataset. The schema records the raw setting; tools handle interpretation.

**`water_volume_ml` removed**
The `water_volume_ml` field is removed from the brew object. Water density at brewing temperatures is effectively 1g/ml, making the field a near-duplicate of `water_weight_g`. In a precision brewing context, volume measurement is not meaningful. `water_weight_g` is the retained field.

**`coffee.process` removed from top-level coffee object**
`coffee.process` is removed. Process is semantically ambiguous at the top-level coffee object for blends — it is unclear which component the process refers to. `coffee.origins[].process` remains valid and is the correct location for process data. Documents that include `coffee.process` at the top level will fail v0.6 validation.

**`coffee.varietal` removed from top-level coffee object**
`coffee.varietal` is removed. Varietal is an intrinsic property of a specific origin component, not of the top-level coffee descriptor. For blends, it is unclear which component the varietal refers to. The replacement is `coffee.origins[].varietal` (see next item).

**`coffee.origins[].varietal` added**
A new optional `varietal` field is added inside each origin entry (`type: string`, `minLength: 1`, `maxLength: 100`). It records the coffee varietal for that specific origin component (e.g., `"Heirloom"`, `"Gesha"`, `"Bourbon"`). The complete valid field list for a `coffee.origins[]` entry in v0.6 is: `name`, `country`, `region`, `subregion`, `producer`, `process`, `lot`, `harvest_year`, `varietal`.

**`coffee.name` added**
A new optional `name` field is added to the top-level `coffee` object (`type: string`, `minLength: 1`, `maxLength: 150`). It serves as a branded product name or human-readable descriptive label (e.g., `"Ethiopia Yirgacheffe"`, `"Estate"`). `coffee.origins[].name` plays the same role at the component level: for single-origin coffees it will typically match `coffee.name`; for blends it names the specific component (e.g., `"Brazil Natural"`, `"Colombia Washed"`). Resolves the previously deferred `blend_name` item. The field is entirely optional — brews that omit it remain valid.

**Carry-forward fixes**
- MED-1: README stale v0.4 references corrected (Quick Start updated to v0.6 format; version references updated; BrewLog CLI section updated; archived spec listing completed including `brewspec-v0.5.md`)
- MED-2: `import_.py` `_V05_REQUIRED_MSG` and corresponding test updated to correct versions
- MED-4: `export.py` module docstring updated to state v0.6-compliant
- MED-5: `equipment.yaml` example corrected: Yirgacheffe entry updated to `{ country: "Ethiopia", region: "Yirgacheffe" }`

### 5.3 "Backward Compatibility" Section Content

The spec document's "Backward Compatibility" section must cover all four breaking changes with concrete before/after YAML examples. The content below defines the required examples exactly.

**Change 1: `equipment.grinder_setting` type changed**

```yaml
# v0.5 format (string — no longer valid in v0.6)
equipment:
  grinder: "Comandante C40 MK4"
  grinder_setting: "21 clicks"

# v0.6 equivalent (number)
equipment:
  grinder: "Comandante C40 MK4"
  grinder_setting: 21

# v0.5 format (decimal string — no longer valid in v0.6)
equipment:
  grinder: "Fellow Ode Gen 2"
  grinder_setting: "5.2"

# v0.6 equivalent (number)
equipment:
  grinder: "Fellow Ode Gen 2"
  grinder_setting: 5.2
```

Migration: Replace string values with numeric equivalents. Simple click-count strings like `"21"` or `"21 clicks"` become `21`. Decimal strings like `"5.2"` become `5.2`. Compound strings with no clear numeric equivalent (e.g., `"3.2.1"`) should be converted to the best available numeric representation or removed.

**Change 2: `water_volume_ml` removed**

```yaml
# v0.5 format (field present — no longer valid in v0.6)
brewspec_version: "0.5"
brews:
  - date: "2026-01-15"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    water_volume_ml: 320    # remove this line

# v0.6 format (field removed)
brewspec_version: "0.6"
brews:
  - date: "2026-01-15"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
```

Migration: Remove `water_volume_ml` from every brew record. Use `water_weight_g` for water quantity. No data equivalent exists in v0.6.

**Change 3: `coffee.process` removed from top-level coffee object**

```yaml
# v0.5 format (coffee.process at top level — no longer valid in v0.6)
coffee:
  type: "single_origin"
  process: "Washed"         # remove this line; move to origins[]
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"

# v0.6 format (process moved to origins[])
coffee:
  type: "single_origin"
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"
      process: "Washed"     # process lives here in v0.6
```

Migration: Move the `coffee.process` value to `coffee.origins[].process` on the relevant origin entry. For blends, add `process` to each origin entry that has a known process method.

**Change 4: `coffee.varietal` removed from top-level coffee object; `coffee.origins[].varietal` added**

```yaml
# v0.5 format (coffee.varietal at top level — no longer valid in v0.6)
coffee:
  type: "single_origin"
  varietal: "Heirloom"      # remove this line; move to origins[]
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"

# v0.6 format (varietal moved to origins[])
coffee:
  type: "single_origin"
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"
      varietal: "Heirloom"  # varietal lives here in v0.6
```

Migration: Move the `coffee.varietal` value to `coffee.origins[].varietal` on the relevant origin entry. For blends, add `varietal` to each origin entry that has a known varietal.

---

## 6. File Manifest

Complete list of every file the dev must create or modify. Both repos are involved.

### brewspec repo (public: `github.com/coffee-standards/brewspec`)

| File | Operation | Notes |
|------|-----------|-------|
| `brewspec.schema.json` | Modify | Apply Section 1 diff: bump version const, remove `water_volume_ml`, change `grinder_setting` to number, remove `coffee.process` and `coffee.varietal`, add `coffee.name`, add `origin.varietal` |
| `brewspec-v0.6.md` | Create | New spec doc per Section 5. Archive `brewspec-v0.5.md` to `versions/` first |
| `versions/brewspec-v0.5.md` | Archive | Copy `brewspec-v0.5.md` to this path before overwriting root spec |
| `examples/valid/pour_over.yaml` | Modify | Remove `water_volume_ml`, `coffee.process`, `coffee.varietal`; move to `origins[].process`, `origins[].varietal`; bump version to `"0.6"` |
| `examples/valid/equipment.yaml` | Modify | Fix MED-5: replace `{ country: "Yirgacheffe" }` with `{ country: "Ethiopia", region: "Yirgacheffe" }`; remove `coffee.varietal` and `coffee.process`; change `grinder_setting` to number; bump version to `"0.6"` |
| `examples/valid/espresso.yaml` | Modify | Bump version to `"0.6"` only (no deprecated fields present) |
| `examples/valid/hybrid.yaml` | Modify | Remove `coffee.varietal` and `coffee.process`; bump version to `"0.6"` |
| `examples/valid/immersion_minimal.yaml` | Modify | Bump version to `"0.6"` only (no deprecated fields present) |
| `examples/valid/multi_brew.yaml` | Modify | Bump version to `"0.6"` only (no deprecated fields present; no `water_volume_ml`, `coffee.process`, or `coffee.varietal` in this file) |
| `examples/valid/pour_over_date_only.yaml` | Modify | Remove `coffee.varietal` and `coffee.process`; bump version to `"0.6"` |
| `examples/valid/valid_brew_ratio.yaml` | Modify | Bump version to `"0.6"` only (no deprecated fields present) |
| `examples/valid/valid_grinder_setting.yaml` | Modify | Change `grinder_setting` from string `"21 clicks"` to number `21`; bump version to `"0.6"` |
| `examples/valid/valid_equipment_notes.yaml` | Modify | Change `grinder_setting` from string `"21 clicks"` to number `21`; bump version to `"0.6"` |
| `examples/valid/valid_single_origin_full.yaml` | Modify | Move `coffee.varietal` to `origins[].varietal`; move `origins[0].process` (already at origin level — no change needed there); remove `coffee.varietal`; bump version to `"0.6"` |
| `examples/valid/valid_blend_origin.yaml` | Modify | Bump version to `"0.6"` only (no deprecated fields present — origins already have per-origin `process`; no top-level `varietal` in this file) |
| `examples/valid/valid_single_origin_with_varietal.yaml` | Create | New file. AC-31: demonstrates `coffee.origins[].varietal` in a realistic single-origin record. See Section 6.1 |
| `examples/valid/valid_blend_with_per_origin_varietal.yaml` | Create | New file. AC-32: demonstrates a blend where each origin entry carries its own `process` and `varietal`. See Section 6.1 |
| `examples/invalid/invalid_grinder_setting_string.yaml` | Create | AC-33. See Section 6.2 |
| `examples/invalid/invalid_coffee_process_top_level.yaml` | Create | AC-34. See Section 6.2 |
| `examples/invalid/invalid_water_volume_ml.yaml` | Create | AC-35. See Section 6.2 |
| `README.md` | Modify | MED-1: update Quick Start to v0.6 format (remove `coffee.origin`, use `coffee.origins`); update all version references to v0.6; update BrewLog CLI section; add `brewspec-v0.5.md` to archived spec listing |

### brewlog CLI repo (path: `brewspec/brewlog/`)

| File | Operation | Notes |
|------|-----------|-------|
| `src/brewlog/brewspec.schema.json` | Modify | Replace with v0.6 schema (same content as public repo schema) |
| `src/brewlog/models.py` | Modify | Per Section 3.1: remove `water_volume_ml` from `BrewInput`; remove `process` and `varietal` from `CoffeeInput`; add `name: Optional[str]` to `CoffeeInput`; change `grinder_setting` from `Optional[str]` to `Optional[float]` in `EquipmentInput`; add `varietal: Optional[str]` to `OriginInput` |
| `src/brewlog/commands/import_.py` | Modify | MED-2: update `_V05_REQUIRED_MSG` constant — see Section 6.3 |
| `src/brewlog/commands/export.py` | Modify | MED-4: update module docstring to `v0.6-compliant`; update `document = {"brewspec_version": "0.5", ...}` to `"0.6"` |
| `tests/test_brewspec_schema.py` | Modify | Update schema version references from `"0.5"` to `"0.6"`; update `VALID_DOC`; update `test_bundled_schema_is_v0_5` to `test_bundled_schema_is_v0_6`; update `test_version_must_be_0_5`; add new test cases per Section 7; remove `water_volume_ml` from `test_optional_brew_fields_accepted` |
| `tests/test_cmd_import.py` | Modify | MED-2: update `test_import_v03_exact_error_message` expected string — see Section 6.3 |
| `tests/fixtures/valid_brewspec.yaml` | Verify/Modify | Confirm no `water_volume_ml`, `coffee.process`, `coffee.varietal`, or string `grinder_setting`; if present, migrate and bump to v0.6 |
| `tests/fixtures/valid_brewspec_multi.yaml` | Verify/Modify | Same check as above |

### 6.1 New Valid Example File Content

**`examples/valid/valid_single_origin_with_varietal.yaml`** (AC-31, AC-45):

```yaml
# Valid example: single origin with varietal at origin level.
# Demonstrates coffee.name (new in v0.6) alongside coffee.origins[].varietal.
# For single-origin coffees, coffee.name and origins[].name typically match.
brewspec_version: "0.6"
brews:
  - date: "2026-03-01"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 288.0
    brew_ratio: 16.0
    method: "Hario V60 02"
    grind: "medium_fine"
    water_temp_c: 96
    duration_s: 210
    coffee:
      name: "Ethiopia Yirgacheffe Natural"
      type: "single_origin"
      roast_date: "2026-02-10"
      origins:
        - name: "Ethiopia Yirgacheffe Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa Washing Station"
          process: "Natural"
          harvest_year: 2025
          varietal: "Heirloom"
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
      grinder_setting: 22
      notes: "Burrs 4 months old"
    result:
      tds: 1.41
      ey: 21.2
      tasting_notes: "Blueberry jam, floral, clean finish"
      ratings:
        overall: 5
        flavour: 5
        acidity: 4
```

**`examples/valid/valid_blend_with_per_origin_varietal.yaml`** (AC-32, AC-45):

```yaml
# Valid example: blend where each origin carries its own process and varietal.
# Demonstrates coffee.name at coffee level and per-origin process and varietal —
# the correct v0.6 model for blends.
brewspec_version: "0.6"
brews:
  - date: "2026-03-02"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 300.0
    brew_ratio: 15.0
    method: "Hario V60"
    grind: "medium_fine"
    water_temp_c: 94
    coffee:
      name: "House Blend"
      type: "blend"
      origins:
        - name: "Ethiopia Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          process: "Washed"
          varietal: "Heirloom"
        - name: "Colombia Natural"
          country: "Colombia"
          region: "Huila"
          producer: "El Paraiso"
          process: "Natural"
          varietal: "Gesha"
    result:
      ratings:
        overall: 4
        flavour: 4
```

### 6.2 New Invalid Example File Content

**`examples/invalid/invalid_grinder_setting_string.yaml`** (AC-33):

```yaml
# Invalid: grinder_setting must be a number in v0.6; string is rejected.
brewspec_version: "0.6"
brews:
  - date: "2026-03-01"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 288.0
    equipment:
      grinder_setting: "21 clicks"
```

**`examples/invalid/invalid_coffee_process_top_level.yaml`** (AC-34):

```yaml
# Invalid: coffee.process at the top-level coffee object is removed in v0.6.
# Process must be recorded inside coffee.origins[].process.
brewspec_version: "0.6"
brews:
  - date: "2026-03-01"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 288.0
    coffee:
      process: "Washed"
```

**`examples/invalid/invalid_water_volume_ml.yaml`** (AC-35):

```yaml
# Invalid: water_volume_ml is removed in v0.6.
brewspec_version: "0.6"
brews:
  - date: "2026-03-01"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 288.0
    water_volume_ml: 288
```

### 6.3 MED-2: Corrected `_V05_REQUIRED_MSG` and Test

The `_V05_REQUIRED_MSG` constant in `import_.py` currently says "BrewLog v0.3 requires BrewSpec v0.4" and gives v0.3-to-v0.4 migration steps. This is wrong for a v0.6 CLI. The constant must be updated to describe v0.5-to-v0.6 migration, since that is the version gap users are most likely to encounter.

**New constant value (replace verbatim):**

```python
_V06_REQUIRED_MSG = """\
Error: This file uses BrewSpec v{version}, which is not supported by BrewLog v0.5.
BrewLog v0.5 requires BrewSpec v0.5.

To migrate your file from v0.4 to v0.5, make the following changes:
  1. Change 'brewspec_version' from "0.4" to "0.5"
  2. Replace 'coffee.origin' (string array) with 'coffee.origins' (object array):
     Before: coffee:
               origin: ["Ethiopia", "Colombia"]
     After:  coffee:
               origins:
                 - country: "Ethiopia"
                 - country: "Colombia"

Full migration guide: https://github.com/coffee-standards/brewspec"""
```

Note: The constant is renamed from `_V05_REQUIRED_MSG` to `_V06_REQUIRED_MSG` to reflect that the CLI now requires v0.6. The version check in `import_cmd` must also be updated from `if file_version != "0.5":` to `if file_version != "0.6":`. The constant's `{version}` placeholder is preserved.

The corresponding test `test_import_v03_exact_error_message` in `test_cmd_import.py` must be updated to assert the new verbatim message text. The test name should be updated to `test_import_v04_exact_error_message` (the fixture under test is a v0.4 file, which is now the relevant "wrong version" case).

**Updated test expected string:**

```python
def test_import_v04_exact_error_message(runner_with_db):
    """MED-2: v0.4 file rejection produces the exact verbatim error message."""
    fixture = str(FIXTURES_DIR / "invalid_v03_file.yaml")  # reuse existing fixture or create invalid_v04_file.yaml
    result = runner_with_db.invoke(cli, ["import", fixture])
    expected = (
        'Error: This file uses BrewSpec v0.3, which is not supported by BrewLog v0.5.\n'
        'BrewLog v0.5 requires BrewSpec v0.5.\n'
        '\n'
        'To migrate your file from v0.4 to v0.5, make the following changes:\n'
        '  1. Change \'brewspec_version\' from "0.4" to "0.5"\n'
        '  2. Replace \'coffee.origin\' (string array) with \'coffee.origins\' (object array):\n'
        '     Before: coffee:\n'
        '               origin: ["Ethiopia", "Colombia"]\n'
        '     After:  coffee:\n'
        '               origins:\n'
        '                 - country: "Ethiopia"\n'
        '                 - country: "Colombia"\n'
        '\n'
        'Full migration guide: https://github.com/coffee-standards/brewspec'
    )
    assert result.output.strip() == expected.strip()
```

Note: The existing `invalid_v03_file.yaml` fixture has `brewspec_version: "0.3"`, so `{version}` in the message renders as `0.3` — which is correct for the test. The test name changes to `test_import_v04_exact_error_message` to reflect the intent (testing the migration path for the most recent prior version), but the fixture file used can remain `invalid_v03_file.yaml` since it simply provides a non-v0.6 version string.

---

## 7. Test Strategy

All new tests belong in `tests/test_brewspec_schema.py` unless otherwise noted. The dev writes failing tests first, then implements schema changes to make them pass.

### AC-1: Version bump

| Test | Input | Expected |
|------|-------|----------|
| `test_bundled_schema_is_v0_6` | `schema["title"]` | `== "BrewSpec v0.6"` |
| `test_version_must_be_0_6` | `brewspec_version: "0.6"` | passes |
| `test_version_const_rejects_v0_5` | `brewspec_version: "0.5"` | `ValidationError` |
| `test_version_const_rejects_v0_4` | `brewspec_version: "0.4"` | `ValidationError` (already existed; update to use v0.6 `VALID_DOC`) |

Update `VALID_DOC` constant at the top of `test_brewspec_schema.py`:
```python
VALID_DOC = {"brewspec_version": "0.6", "brews": [VALID_BREW]}
```

### AC-2 through AC-9: `grinder_setting` type change

| Test | Input | Expected |
|------|-------|----------|
| `test_grinder_setting_integer_accepted` | `equipment: {grinder_setting: 21}` | passes — AC-3 |
| `test_grinder_setting_float_accepted` | `equipment: {grinder_setting: 5.2}` | passes — AC-4 |
| `test_grinder_setting_zero_rejected` | `equipment: {grinder_setting: 0}` | `ValidationError` — AC-5 |
| `test_grinder_setting_negative_rejected` | `equipment: {grinder_setting: -1}` | `ValidationError` — AC-6 |
| `test_grinder_setting_string_rejected` | `equipment: {grinder_setting: "21"}` | `ValidationError` — AC-7 |
| `test_grinder_setting_omitted_passes` | `equipment: {}` | passes — AC-8 |
| `test_grinder_setting_string_clicks_rejected` | `equipment: {grinder_setting: "21 clicks"}` | `ValidationError` — AC-7 variant |

### AC-10 and AC-11: `water_volume_ml` removal

| Test | Input | Expected |
|------|-------|----------|
| `test_water_volume_ml_present_rejected` | `{...VALID_BREW, water_volume_ml: 320}` | `ValidationError` — AC-10 |
| `test_water_volume_ml_omitted_passes` | `VALID_DOC` (no `water_volume_ml`) | passes — AC-11 |

Note: also update `test_optional_brew_fields_accepted` — remove `water_volume_ml` from the `extra_fields` dict in that test since it is no longer an accepted field.

Also update `test_negative_values_rejected` — remove `("water_volume_ml", -100)` from the parametrize list.

### AC-12 through AC-15: `coffee.process` removal from top-level coffee object

| Test | Input | Expected |
|------|-------|----------|
| `test_coffee_process_top_level_rejected` | `coffee: {process: "Washed"}` | `ValidationError` — AC-12, AC-15 |
| `test_coffee_process_in_origin_accepted` | `coffee: {origins: [{process: "Washed"}]}` | passes — AC-14 |
| `test_coffee_without_process_passes` | `coffee: {type: "single_origin"}` | passes |

### AC-13: `coffee.varietal` removal from top-level coffee object

| Test | Input | Expected |
|------|-------|----------|
| `test_coffee_varietal_top_level_rejected` | `coffee: {varietal: "Heirloom"}` | `ValidationError` — AC-13 |
| `test_coffee_without_varietal_passes` | `coffee: {type: "single_origin"}` | passes |

### AC-40 through AC-45: `coffee.name` addition

| Test | Input | Expected |
|------|-------|----------|
| `test_coffee_name_accepted` | `coffee: {name: "Estate"}` | passes — AC-41 |
| `test_coffee_name_empty_string_rejected` | `coffee: {name: ""}` | `ValidationError` (`minLength: 1`) — AC-42 |
| `test_coffee_name_omitted_passes` | `coffee: {type: "single_origin"}` | passes — AC-40 |
| `test_coffee_name_coexists_with_origins` | `coffee: {name: "Ethiopia Yirgacheffe", origins: [{country: "Ethiopia"}]}` | passes — AC-43 |
| `test_coffee_name_max_length_accepted` | `coffee: {name: "A" * 150}` | passes — AC-40 boundary |
| `test_coffee_name_over_max_length_rejected` | `coffee: {name: "A" * 151}` | `ValidationError` (`maxLength: 150`) |

For AC-44 (description update for `origins[].name`): verified by reading the schema description field in `test_bundled_schema_is_v0_6` or a dedicated test that asserts the `description` text of `$defs.origin.properties.name` contains the relationship to `coffee.name`. This is a documentation-level AC; the primary verification is the spec document text, not a runtime validation test.

For AC-45 (example demonstrating `coffee.name` alongside `origins[]`): satisfied by the two new valid example files in Section 6.1 (`valid_single_origin_with_varietal.yaml` and `valid_blend_with_per_origin_varietal.yaml`), which both include `coffee.name`. These are automatically validated by the parametrized `test_valid_fixtures_pass` test.

### AC-16 through AC-20: `coffee.origins[].varietal` addition

| Test | Input | Expected |
|------|-------|----------|
| `test_origin_varietal_accepted` | `origins: [{country: "Ethiopia", varietal: "Heirloom"}]` | passes — AC-17 |
| `test_origin_varietal_empty_string_rejected` | `origins: [{varietal: ""}]` | `ValidationError` — AC-18 |
| `test_origin_varietal_omitted_passes` | `origins: [{country: "Ethiopia"}]` | passes — AC-19 |
| `test_origin_unknown_field_rejected` | `origins: [{varietal: "Heirloom", unknown: "bad"}]` | `ValidationError` — AC-20 |
| `test_origin_all_v0_6_fields_accepted` | Origin with all 9 fields populated | passes |

### Fixture file tests (auto-run via parametrize)

The existing `test_valid_fixtures_pass` and `test_invalid_fixtures_fail` parametrize tests will automatically pick up new fixture files from the `fixtures/` directory. The dev must ensure the new valid and invalid fixture files follow the `valid_*.yaml` and `invalid_*.yaml` naming patterns and are placed in the correct fixtures subdirectory.

However, note that the schema test file uses `brewlog/tests/fixtures/` — this is the CLI's own fixtures directory, not `examples/`. The new invalid examples in `examples/invalid/` are validated by the schema tests that reference the `examples/` directory. The dev should verify that `VALID_EXAMPLES` and `INVALID_EXAMPLES` path globs in `test_brewspec_schema.py` point at the correct directories.

Looking at the existing test file:
```python
FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_EXAMPLES = sorted(FIXTURES_DIR.glob("valid_*.yaml")) + sorted(FIXTURES_DIR.glob("valid_*.json"))
INVALID_EXAMPLES = sorted(FIXTURES_DIR.glob("invalid_*.yaml"))
```

These glob the `brewlog/tests/fixtures/` directory, not `examples/`. The dev must add a separate test section that validates the `examples/valid/` and `examples/invalid/` files from the repo root, similar to what the v0.5 design specified. See the note in Section 9 TDD order.

### MED-2: Import version message test

In `tests/test_cmd_import.py`:
- Rename `test_import_v03_exact_error_message` to `test_import_v04_exact_error_message`
- Update the `expected` string to match the new `_V06_REQUIRED_MSG` constant (per Section 6.3)
- Update the version check in `import_cmd` from `!= "0.5"` to `!= "0.6"`

---

## 8. Security Considerations

**Principle alignment**: "Validate at every system boundary" — all four breaking changes tighten the schema, reducing the valid input surface area. This is a security improvement, not a regression.

### Input validation

| Field | v0.5 validation | v0.6 validation | Change |
|-------|----------------|----------------|--------|
| `equipment.grinder_setting` | `type: string`, `minLength: 1`, `maxLength: 100` | `type: number`, `exclusiveMinimum: 0` | Removes string injection surface. Numbers cannot contain escape sequences, SQL special characters, or HTML. The type change reduces attack surface relative to freeform string. |
| `water_volume_ml` | `type: number`, `exclusiveMinimum: 0` | Field removed | Removal reduces schema surface area with no user-facing risk. |
| `coffee.process` | `type: string`, `minLength: 1`, `maxLength: 100` (at top level) | Field removed from top level; remains valid at `origins[].process` | No change to per-origin process validation. |
| `coffee.varietal` | `type: string`, `minLength: 1`, `maxLength: 100` (at top level) | Field removed from top level | No change to per-origin varietal validation (new field inherits same constraints). |
| `coffee.name` | Field did not exist | `type: string`, `minLength: 1`, `maxLength: 150` | New freeform string on the top-level coffee object. Must not be executed, evaluated, or interpolated — stored and displayed as plain text only. `maxLength: 150` bounds storage impact. No PII risk — this is a coffee product name, not personal data. |
| `origins[].varietal` | Field did not exist | `type: string`, `minLength: 1`, `maxLength: 100` | New freeform string. Consistent constraints with all other origin string fields. Must not be executed, evaluated, or interpolated — stored and displayed as plain text only. |

### Trust boundaries

The validation pipeline is unchanged from v0.5:

```
User file / stdin
    → yaml.safe_load() or json.loads()       # Parse boundary — malformed input rejected here
    → Draft202012Validator.validate(doc)      # Schema boundary — type/constraint violations rejected here
    → db.insert_brew_dict(brew_dict, conn)    # Storage boundary — parameterised queries only
    → Output / display                        # Output boundary — plain text display, no interpolation
```

All new and changed fields pass through this pipeline unchanged. No new boundary crossings are introduced.

### File I/O

- `yaml.safe_load()` requirement is unchanged. The three new invalid example files are plain YAML with no executable content.
- New example files are read-only reference documents. No change to file write paths.

### Data integrity

- Removing `water_volume_ml` eliminates a source of inconsistency (volume vs. weight) from the stored record.
- Removing `coffee.process` and `coffee.varietal` from the top-level coffee object eliminates the dual-representation problem where a v0.5 tool reading a blend could read conflicting process/varietal values from two locations.
- Adding `origins[].varietal` at the origin level ensures varietal is unambiguously associated with a specific component.

### No sensitive data

- `coffee.name` is a product label or descriptive name. No PII.
- `origins[].varietal` is coffee provenance information. No PII.
- Producer names, varietals, lot identifiers, and coffee names in examples are fictitious or publicly known specialty coffee names.
- No credentials or API keys in any example file.

---

## 9. TDD Implementation Order

The dev must follow this sequence. Tests are written before the implementation they test.

1. **Write failing tests for AC-1 (version bump)**
   - Update `VALID_DOC` to `brewspec_version: "0.6"`
   - Update `test_bundled_schema_is_v0_5` → `test_bundled_schema_is_v0_6`
   - Update `test_version_must_be_0_5` → `test_version_must_be_0_6` with v0.5 rejection
   - Add `test_version_const_rejects_v0_5`
   - These will fail because schema still says `"0.5"`

2. **Implement: update `brewspec.schema.json` version const only** (title + const + description)
   - Run tests for AC-1 — confirm they pass
   - Other tests will now fail (schema is v0.6 but brew object still has `water_volume_ml`, etc.)

3. **Write failing tests for AC-10, AC-11 (`water_volume_ml` removal)**
   - `test_water_volume_ml_present_rejected`
   - `test_water_volume_ml_omitted_passes`
   - Update `test_optional_brew_fields_accepted` and `test_negative_values_rejected` to remove `water_volume_ml`

4. **Implement: remove `water_volume_ml` from `$defs.brew`**
   - Run AC-10 and AC-11 tests — confirm they pass

5. **Write failing tests for AC-2 through AC-9 (`grinder_setting` type change)**
   - All seven grinder_setting tests listed in Section 7

6. **Implement: change `grinder_setting` to `type: number` with `exclusiveMinimum: 0`**
   - Run AC-2–AC-9 tests — confirm they pass

7. **Write failing tests for AC-12, AC-13, AC-14, AC-15 (`coffee.process` and `coffee.varietal` removal)**
   - All tests listed in Section 7

8. **Implement: remove `process` and `varietal` from `$defs.coffee`**
   - Run AC-12–AC-15 tests — confirm they pass

9. **Write failing tests for AC-16 through AC-20 (`origins[].varietal` addition)**
   - All tests listed in Section 7

10. **Implement: add `varietal` to `$defs.origin`**
    - Run AC-16–AC-20 tests — confirm they pass

10a. **Write failing tests for AC-40 through AC-43 (`coffee.name` addition)**
    - All six `coffee.name` tests listed in Section 7
    - These will fail because `$defs.coffee` does not yet have `name`

10b. **Implement: add `name` to `$defs.coffee`**
    - Run AC-40–AC-43 tests — confirm they pass
    - AC-44 (description text) is satisfied by the schema description string written here
    - AC-45 (example with `coffee.name`) is satisfied in step 11

11. **Update and create example files** (Section 6)
    - Modify all existing valid examples (version bump + deprecated field removal)
    - Create two new valid examples
    - Create three new invalid examples
    - Run the parametrized fixture tests to confirm all pass/fail as expected

12. **Update Pydantic models in `models.py`** (Section 3.1)
    - Run `test_models.py` to confirm models match schema

13. **Update CLI code for carry-forward fixes**
    - MED-2: rename and update `_V05_REQUIRED_MSG` → `_V06_REQUIRED_MSG`; update version check in `import_cmd` from `!= "0.5"` to `!= "0.6"`
    - MED-4: update `export.py` module docstring; update `brewspec_version` in `document` dict to `"0.6"`
    - Update `test_import_v03_exact_error_message` → `test_import_v04_exact_error_message` with new expected text
    - Run `test_cmd_import.py` — confirm the renamed test passes

14. **Update `brewspec-v0.6.md` spec document and `README.md`**
    - Archive `brewspec-v0.5.md` to `versions/`
    - Write new `brewspec-v0.6.md` per Section 5
    - Update `README.md` per MED-1

15. **Run full test suite** — confirm all tests pass (100%)

16. **Run `ruff check .`** — fix any lint errors before handoff to reviewer
