# Design: BrewSpec v0.5

**Feature:** brewspec-v0.5
**Author:** architect
**Created:** 2026-02-28
**Input:** specs/products/brewspec-v0.5.md
**Baseline:** specs/designs/brewspec-v0.4.md
**Status:** Ready for Dev

---

## Overview

This document specifies every schema, model, test, and file change required to produce BrewSpec v0.5. v0.5 makes four categories of change:

1. **Breaking** — `coffee.origin` (string array) is removed and replaced by `coffee.origins` (structured object array). Any v0.4 file using `coffee.origin` will fail v0.5 validation. This is the second intentional breaking change across BrewSpec versions.
2. **Additive: brew level** — `brew_ratio` is added as an optional float at the brew level, representing water-to-coffee ratio (grams water per gram coffee).
3. **Additive: equipment** — `equipment.grinder_setting` and `equipment.notes` are added as optional strings.
4. **Carry-forward fixes** — The `rating_out_of_range.yaml` invalid example comment is corrected, and the README invalid examples inventory is completed.

The `brewspec_version` const advances from `"0.4"` to `"0.5"`. All other v0.4 fields are unchanged.

The dev should follow the TDD order in Section 9 (write failing tests first, then implement schema changes, then update examples and models).

---

## 1. JSON Schema Diff (v0.4 → v0.5)

This section specifies every change to `brewspec.schema.json`. The full target schema is in Section 2.

### 1.1 Root-Level Changes

| Location | v0.4 Value | v0.5 Value | AC |
|----------|-----------|-----------|-----|
| `title` | `"BrewSpec v0.4"` | `"BrewSpec v0.5"` | AC-1 |
| `properties.brewspec_version.const` | `"0.4"` | `"0.5"` | AC-1 |
| `properties.brewspec_version.description` | `"The BrewSpec version. Must be \"0.4\"."` | `"The BrewSpec version. Must be \"0.5\"."` | AC-1 |

The `$schema` and `$id` values are unchanged.

### 1.2 `$defs.brew` Changes

**New field: `brew_ratio`**

Add the following property to `$defs.brew.properties`, positioned after `water_weight_g` and before `water_volume_ml`:

```json
"brew_ratio": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Water-to-coffee ratio expressed as a single float (grams of water per gram of coffee). e.g. 15.5 represents 15.5:1 or approximately 64g/L. Can be computed from water_weight_g / dose_g. When both are present, tools should validate consistency; mismatches should be surfaced as a warning, not a schema error."
}
```

This field is optional. It does not appear in the `required` array on `$defs.brew`. (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7)

All other `$defs.brew` properties are unchanged: `date`, `type`, `method`, `dose_g`, `water_weight_g`, `water_volume_ml`, `water_temp_c`, `coffee`, `water`, `equipment`, `grind`, `duration_s`, `notes`, `result`.

### 1.3 `$defs.equipment` Changes

**New fields: `grinder_setting` and `notes`**

Add the following two properties to `$defs.equipment.properties`, after the existing `brewer` property:

```json
"grinder_setting": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "Grinder dial position or click setting used for this brew. Freeform; grinder setting systems are incompatible across brands.",
  "examples": ["21", "21 clicks", "3.2.1", "setting 21"]
},
"notes": {
  "type": "string",
  "minLength": 1,
  "maxLength": 2000,
  "description": "Equipment state notes — observations about maintenance, calibration, filter type, or burr age. Distinct from brew-level notes, which record preparation observations.",
  "examples": ["Burrs replaced 2026-01", "Aeropress rubber seal replaced"]
}
```

Both fields are optional. The `equipment` object continues to enforce `additionalProperties: false`. After this change, the only accepted fields in `equipment` are: `grinder`, `brewer`, `grinder_setting`, `notes`. (AC-8 through AC-16)

### 1.4 `$defs.coffee` Changes

**Removed field: `origin`**

Remove the `origin` property from `$defs.coffee.properties` entirely:

```json
// REMOVE from $defs.coffee.properties:
"origin": {
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "string",
    "minLength": 1,
    "maxLength": 100
  },
  ...
}
```

Because `$defs.coffee` carries `additionalProperties: false`, any document with a `coffee.origin` key will automatically fail v0.5 validation — no additional schema keyword is needed. (AC-17)

**New field: `origins`**

Add the following property to `$defs.coffee.properties`, in the position previously occupied by `origin`:

```json
"origins": {
  "type": "array",
  "minItems": 1,
  "items": {
    "$ref": "#/$defs/origin"
  },
  "description": "Structured origin records. Array to support blends. Each entry is an origin object with all fields optional."
}
```

This field is optional on the `coffee` object. An omitted `origins` key is valid. (AC-18, AC-25)

### 1.5 New `$defs.origin` Definition

Add a new definition to `$defs`:

```json
"origin": {
  "type": "object",
  "additionalProperties": false,
  "description": "A single origin record within a coffee.origins array. All fields optional. Supports single-origin and blend records.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "Human-readable label for this origin entry.",
      "examples": ["Ethiopia Yirgacheffe Natural", "Brazil Fazenda Santa Ines"]
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
      "description": "Green coffee processing method at origin. Distinct from the brew-level coffee.process field.",
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
    }
  }
}
```

(AC-19, AC-20, AC-21, AC-22, AC-23, AC-24)

---

## 2. Full Annotated v0.5 Schema

This is the complete target `brewspec.schema.json`. The dev writes this verbatim to `brewspec.schema.json` in the public repo and to `src/brewlog/brewspec.schema.json` in the CLI package (both copies must stay in sync).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json",
  "title": "BrewSpec v0.5",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.5",
      "description": "The BrewSpec version. Must be \"0.5\"."
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
          "description": "Processing method. Freeform. Records the green coffee processing method at the coffee object level. For per-origin process in blends, use origins[].process.",
          "examples": ["Washed", "Natural", "Honey"]
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
          "description": "Human-readable label for this origin entry.",
          "examples": ["Ethiopia Yirgacheffe Natural", "Brazil Fazenda Santa Ines"]
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
          "description": "Green coffee processing method at origin. Distinct from the brew-level coffee.process field.",
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
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "Grinder dial position or click setting used for this brew. Freeform; grinder setting systems are incompatible across brands.",
          "examples": ["21", "21 clicks", "3.2.1", "setting 21"]
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

## 3. Design Decisions

### 3.1 `coffee.origins[].process` Coexistence with `coffee.process`

**Context:** The `coffee` object has carried a top-level `process` field since v0.1 (e.g., `"Washed"`). In v0.5, each entry in `coffee.origins` also has a `process` field for the same concept. The two fields overlap semantically.

**Decision:** Both fields coexist in v0.5 with no precedence defined. Neither supersedes the other.

**Rationale:**

The two fields serve distinct but complementary intents:

- `coffee.process` — a single-value processing descriptor at the coffee object level. Written before `origins` existed. Works for single-origin coffees where the processing method is known and there is only one. A v0.4 file migrating to v0.5 retains this field unchanged; no migration of `coffee.process` is required.
- `origins[].process` — per-origin processing descriptor within a structured entry. Appropriate for blends where each component has a different processing method (e.g., one washed, one natural). A user populating the full `origins` structure for a single-origin coffee will likely populate `origins[0].process` and may leave `coffee.process` absent, or may populate both.

Defining a precedence rule in v0.5 would require enforcing it in validators. The schema does not enforce consistency between `coffee.process` and any `origins[].process` — this is an application-layer concern (consistent with how `brew_ratio` consistency with `dose_g`/`water_weight_g` is not schema-enforced).

**Forward path:** Recommend deprecating `coffee.process` in v0.6 in favour of `origins[].process`. By v0.6, tool builders will have adopted structured `origins` and `coffee.process` at the top level will be redundant for any brew that uses the `origins` field. The deprecation timeline gives BrewLog CLI v0.5 and any third-party tools one version cycle to migrate. A deprecation notice should appear in the v0.6 spec document.

**Consequences:** Tools in v0.5 should not attempt to infer a precedence order. If displaying a single processing method and both are present, prefer `origins[0].process` for structured data workflows, but do not treat this as a schema rule. Document this guidance in the spec doc.

### 3.2 `coffee.origin` Removal: Breaking Change is Intentional

**Decision:** `coffee.origin` (string array) is removed entirely from `$defs.coffee.properties`. There is no deprecation period or compatibility alias.

**Rationale:** BrewSpec is in early development with no established third-party tool ecosystem. The structural improvement (from opaque string array to queryable structured object) is worth the break. A file declaring `brewspec_version: "0.5"` that includes `coffee.origin` fails validation automatically via `additionalProperties: false` on the `coffee` object — no additional schema machinery is needed. The migration from `origin` to `origins` is mechanical and takes under 2 minutes per file. This is the second intentional breaking change across BrewSpec versions (after v0.4's `result` restructure).

*Architecture principle: Validate at every system boundary. The schema enforces the current contract; old contract files must migrate rather than introducing dual-schema complexity.*

### 3.3 `brew_ratio` as Single Float, Not Structured Object

**Decision:** `brew_ratio` is stored as a single `number` (float) representing grams of water per gram of coffee.

**Rationale:** The water-to-coffee ratio is a single, universally understood scalar in specialty coffee practice. Storing it as `15.5` rather than `{water: 15.5, coffee: 1}` reduces verbosity and avoids introducing a denominator that is always 1. Display formatting choices (1:15.5, 15.5:1, 63.9 g/L) are tool decisions, not schema decisions. The `exclusiveMinimum: 0` constraint correctly rejects zero and negative values. A coffee-to-water inverse representation (coffee/water) was not chosen because water-to-coffee is the dominant convention in specialty coffee discourse.

### 3.4 `grinder_setting` as Freeform String

**Decision:** `grinder_setting` is `type: string`, not a numeric type, structured object, or enum.

**Rationale:** Grinder setting systems are incompatible across brands. Comandante uses click counts (`"21"`), Timemore uses a decimal dial (`"3.0"`), Weber EG-1 uses a multi-part position code (`"3.2.1"`), espresso grinders use brand-specific codes. No single numeric or structured format covers all grinders. Freeform string with `minLength: 1` / `maxLength: 100` — the same constraint pattern as `equipment.grinder` and `equipment.brewer` — is the correct choice at this stage.

### 3.5 `equipment.notes` maxLength: 2000 (Not 100)

**Decision:** `equipment.notes` uses `maxLength: 2000`, consistent with the brew-level `notes` and `result.tasting_notes`, rather than `maxLength: 100` used by other equipment string fields.

**Rationale:** Equipment notes capture maintenance history, calibration records, and filter details — content that can accumulate more substance than a model name. A 2000-character limit is the established convention for freeform observation fields in BrewSpec. The 100-character limit applies only to fields that identify a specific item (model name, setting code, lot number, country name) where brevity is expected.

---

## 4. Pydantic Model Changes (`src/brewlog/models.py`)

The Pydantic models must be updated to match the v0.5 schema. The schema (`validate_document()` in `schema.py`) is the authoritative validation gate; the Pydantic models are the CLI input layer. Both must be consistent.

### 4.1 New `OriginInput` Model

Add before `CoffeeInput`:

```python
class OriginInput(BaseModel):
    """A single origin record within a coffee.origins array. All fields optional."""

    name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    producer: Optional[str] = None
    process: Optional[str] = None
    lot: Optional[str] = None
    harvest_year: Optional[int] = None

    @field_validator("name", "country", "region", "subregion", "producer", "process", "lot")
    @classmethod
    def validate_origin_string(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v

    @field_validator("harvest_year")
    @classmethod
    def validate_harvest_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1900 <= v <= 2100):
            raise ValueError("harvest_year must be between 1900 and 2100 inclusive")
        return v
```

### 4.2 Updates to `CoffeeInput`

**Remove from `CoffeeInput`:**

```python
origin: Optional[List[str]] = None   # REMOVE — replaced by origins
```

**Add to `CoffeeInput`:**

```python
origins: Optional[List[OriginInput]] = None
```

**Add validator to `CoffeeInput`:**

```python
@field_validator("origins")
@classmethod
def validate_origins(cls, v: Optional[List[OriginInput]]) -> Optional[List[OriginInput]]:
    if v is not None and len(v) == 0:
        raise ValueError("origins must have at least one entry when present; omit the field to record no origin data")
    return v
```

**Remove validator from `CoffeeInput`** (if a validator currently enforces `origin` items):

The existing `validate_origin_item` or equivalent string-item validator on `origin` is removed. `OriginInput` handles its own field validation.

### 4.3 Updates to `EquipmentInput`

Add two fields after `brewer`:

```python
grinder_setting: Optional[str] = None
notes: Optional[str] = None
```

Add or extend validators. The existing equipment string validator (if present) should be extended to cover `grinder_setting`. The `notes` field uses `maxLength: 2000`:

```python
@field_validator("grinder", "brewer", "grinder_setting")
@classmethod
def validate_equipment_short_text(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        if len(v) > 100:
            raise ValueError("value must not exceed 100 characters")
    return v

@field_validator("notes")
@classmethod
def validate_equipment_notes(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("notes must not be empty when provided")
        if len(v) > 2000:
            raise ValueError("notes must not exceed 2000 characters")
    return v
```

### 4.4 Updates to `BrewInput`

Add `brew_ratio` after `water_weight_g`:

```python
brew_ratio: Optional[float] = None
```

Add validator:

```python
@field_validator("brew_ratio")
@classmethod
def validate_brew_ratio(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("brew_ratio must be greater than 0")
    return v
```

Update docstring:

```python
class BrewInput(BaseModel):
    """Primary model for a brew log entry. Validates all BrewSpec v0.5 constraints."""
```

### 4.5 Complete Updated `BrewInput` Field List (after v0.5 changes)

**Required fields:**
- `date: str`
- `type: str`
- `dose_g: float`
- `water_weight_g: float`

**Optional brew parameters:**
- `brew_ratio: Optional[float] = None`  ← new
- `method: Optional[str] = None`
- `water_volume_ml: Optional[float] = None`
- `water_temp_c: Optional[float] = None`
- `grind: Optional[str] = None`
- `duration_s: Optional[int] = None`
- `notes: Optional[str] = None`

**Optional nested objects:**
- `coffee: Optional[CoffeeInput] = None`
- `water: Optional[WaterInput] = None`
- `equipment: Optional[EquipmentInput] = None`
- `result: Optional[ResultInput] = None`

Fields removed from v0.4: none on `BrewInput` itself. `CoffeeInput.origin` removed.
Fields added in v0.5: `BrewInput.brew_ratio`, `EquipmentInput.grinder_setting`, `EquipmentInput.notes`, `CoffeeInput.origins` (via `OriginInput`).

---

## 5. Public Spec Document (`brewspec-v0.5.md` in the public repo)

Before writing `brewspec-v0.5.md`, archive the previous spec: copy `brewspec-v0.4.md` to `versions/brewspec-v0.4.md`, then overwrite at the repo root with `brewspec-v0.5.md`.

### 5.1 Structure

The spec document must contain these sections in order:

1. Overview
2. Field Reference
3. What Changed in v0.5
4. Validation
5. Backward Compatibility

### 5.2 Header

```
# BrewSpec v0.5
Status: Stable
Version: 0.5
Last Updated: [date of deployment]
```

### 5.3 Field Reference Tables

**Top-Level Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.5"` | The BrewSpec version |
| `brews` | array | Required | Minimum 1 element | Array of brew objects |

**Brew Object:**

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Required | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Brew date or datetime (UTC) | `"2026-02-21"`, `"2026-02-15T08:30:00Z"` |
| `type` | string | Required | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Required | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Required | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `brew_ratio` | number | Optional | > 0 (exclusive) | Water-to-coffee ratio as a float (grams water per gram coffee). e.g. `15.5` represents 15.5:1 or approximately 64g/L. Tools should prefer this stored value when present and fall back to computing from `water_weight_g / dose_g` when absent. Consistency with `dose_g`/`water_weight_g` is not schema-enforced; tools should surface mismatches as a warning. | `15.5`, `15.56` |
| `method` | string | Optional | minLength 1, maxLength 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `equipment` | object | Optional | See Equipment Object | Equipment descriptor | |
| `grind` | string | Optional | Enum: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse` | Grind size (finest to coarsest) | `"medium_fine"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `notes` | string | Optional | minLength 1, maxLength 2000 | Brew-process notes — operational observations about the preparation. For sensory description, use `result.tasting_notes`. | `"Washed filter paper"` |
| `result` | object | Optional | See Result Object | Brew outcome measurements and sensory evaluation | |

**Coffee Object** (entire object optional; all fields within optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roast_date` | string | Optional | `YYYY-MM-DD` | Roast date. Plain date; no time component. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Whether the coffee is a single origin or a blend. | `"single_origin"` |
| `origins` | array | Optional | minItems 1; each item is an Origin Object | Structured origin records. Replaces v0.4 `origin` string array. Omit entirely to record no origin data (present but empty is invalid). | |
| `varietal` | string | Optional | minLength 1, maxLength 100 | Coffee variety or cultivar. Freeform. | `"Heirloom"`, `"Gesha"` |
| `process` | string | Optional | minLength 1, maxLength 100 | Green coffee processing method at the coffee level. For per-origin process in blends, use `origins[].process`. Both fields coexist in v0.5 with no defined precedence. | `"Washed"`, `"Natural"` |

**Origin Object** (all fields optional; `additionalProperties: false`):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `name` | string | Optional | minLength 1, maxLength 100 | Human-readable label for this origin entry. | `"Ethiopia Yirgacheffe Natural"` |
| `country` | string | Optional | minLength 1, maxLength 100 | Country of production. | `"Ethiopia"`, `"Colombia"` |
| `region` | string | Optional | minLength 1, maxLength 100 | State, province, or named growing region. | `"Yirgacheffe"`, `"Huila"` |
| `subregion` | string | Optional | minLength 1, maxLength 100 | District, zone, or sub-area within the region. | `"Kochere"` |
| `producer` | string | Optional | minLength 1, maxLength 100 | Farm, cooperative, or washing station name. | `"Daye Bensa Washing Station"` |
| `process` | string | Optional | minLength 1, maxLength 100 | Green coffee processing method at origin. Distinct from `coffee.process`. | `"Washed"`, `"Natural"`, `"Honey"` |
| `lot` | string | Optional | minLength 1, maxLength 100 | Lot or batch identifier from the producer. | `"Lot 42"`, `"Export Grade 1"` |
| `harvest_year` | integer | Optional | minimum 1900, maximum 2100 | Year the crop was harvested. | `2025` |

**Water Object** (entire object optional; all fields within optional): unchanged from v0.4.

**Equipment Object** (entire object optional; all fields within optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | minLength 1, maxLength 100 | Grinder model. Freeform. | `"Comandante C40 MK4"` |
| `brewer` | string | Optional | minLength 1, maxLength 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"` |
| `grinder_setting` | string | Optional | minLength 1, maxLength 100 | Grinder dial position or click setting for this brew. Freeform. | `"21 clicks"`, `"3.2.1"` |
| `notes` | string | Optional | minLength 1, maxLength 2000 | Equipment state observations — burr age, maintenance, filter type, calibration state. | `"Burrs replaced 2026-01"` |

**Result Object** and **Ratings Object**: unchanged from v0.4.

### 5.4 "What Changed in v0.5" Section

The spec document must include this section verbatim (content, not presentation, is specified here):

```
## What Changed in v0.5

### Version bump
brewspec_version const updated from "0.4" to "0.5". Schema title updated to "BrewSpec v0.5".

### brew_ratio field added (brew level)
A new optional brew_ratio field accepts a positive number representing
water-to-coffee ratio (grams of water per gram of coffee). e.g. 15.5 means
15.5:1 ratio. Can be computed from water_weight_g / dose_g but may also be
stored explicitly. The schema does not enforce consistency between brew_ratio
and the constituent fields — tools should surface mismatches as a warning,
not a hard error.

### equipment.grinder_setting field added
A new optional grinder_setting field on the equipment object records the
specific dial position or click setting used for this brew. Freeform string
(minLength 1, maxLength 100). Different grinder brands use incompatible
setting systems, so no structured type is imposed.

### equipment.notes field added
A new optional notes field on the equipment object records observations about
equipment state: burr age, maintenance history, filter type, calibration.
Freeform string (minLength 1, maxLength 2000). Distinct from the brew-level
notes field, which records preparation observations.

### coffee.origin removed (breaking change)
The coffee.origin string array field is removed. Files declaring
brewspec_version: "0.5" that include a coffee.origin key will fail schema
validation. See Backward Compatibility for migration guidance.

### coffee.origins structured array added
A new optional coffee.origins field replaces coffee.origin. It is an array
of origin objects (minItems: 1 when present). Each origin object accepts up
to eight optional fields: name, country, region, subregion, producer,
process, lot, harvest_year. All fields on each entry are optional; an empty
object {} is valid. Unrecognised fields are rejected (additionalProperties:
false on each item).

### Carry-forward fixes
- examples/invalid/rating_out_of_range.yaml: comment corrected. The file now
  demonstrates result.ratings.overall: 6 (exceeds maximum of 5), and the
  comment states this clearly.
- README.md: invalid examples inventory updated to include
  invalid_date_no_z.yaml, invalid_grind_freeform.yaml, and
  invalid_tds_at_brew_level.yaml, each with a brief description.
```

### 5.5 "Backward Compatibility" Section

```
## Backward Compatibility

v0.5 introduces one breaking change from v0.4: coffee.origin is removed.

### Migration: coffee.origin → coffee.origins

v0.4 files using coffee.origin must be migrated before they will validate
against the v0.5 schema. The migration is mechanical:

Step 1 — Update the version field:
  brewspec_version: "0.4"  →  brewspec_version: "0.5"

Step 2 — Rename origin to origins and wrap each string in an object:

  # v0.4 format
  coffee:
    origin: ["Ethiopia", "Colombia"]

  # v0.5 equivalent
  coffee:
    origins:
      - country: "Ethiopia"
      - country: "Colombia"

Each string from the old origin array maps to the country field of a new
origins entry. No data is lost in this migration.

If your v0.4 files do not use coffee.origin (the field was optional), only
the version bump in Step 1 is required.

### New optional fields

brew_ratio, equipment.grinder_setting, and equipment.notes are new optional
fields. v0.4 files that do not include them remain valid after migration
(version bump only required). No action is needed for these fields unless
you wish to add them.
```

### 5.6 "Validation" Section

Preserve the v0.4 guidance unchanged: tools should validate at storage time, not just display time. Add the following note about `brew_ratio` consistency:

```
When brew_ratio, dose_g, and water_weight_g are all present, tools should
check that brew_ratio ≈ water_weight_g / dose_g and surface any significant
mismatch as a warning. A mismatch is not a schema error — both values are
stored as supplied.
```

---

## 6. Examples: Migration and New Files

### 6.1 Existing Valid Examples — Required Updates

All valid example files must be updated with:
1. `brewspec_version: "0.4"` → `brewspec_version: "0.5"`
2. Any `coffee.origin` key migrated to `coffee.origins` using the pattern: each string in the array becomes `{ country: "<string>" }` in the new array.

The migration preserves all existing field values. No other changes to existing valid examples are required.

### 6.2 New Valid Example Files

The dev must create the following new valid example files in `examples/valid/`:

**`valid_brew_ratio.yaml`**

Demonstrates `brew_ratio` at the brew level with a fractional value:

```yaml
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    brew_ratio: 15.56
    method: "Hario V60"
    grind: "medium_fine"
    notes: "brew_ratio computed from 280 / 18"
```

**`valid_grinder_setting.yaml`**

Demonstrates `equipment.grinder_setting`:

```yaml
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 300.0
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
      grinder_setting: "21 clicks"
```

**`valid_equipment_notes.yaml`**

Demonstrates `equipment.notes` alongside `equipment.grinder_setting` (covers AC-33 and shows the four-field equipment object):

```yaml
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 20.0
    water_weight_g: 300.0
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
      grinder_setting: "21 clicks"
      notes: "Burrs replaced 2026-01"
```

**`valid_single_origin_full.yaml`**

Demonstrates a full single-origin `coffee.origins` entry with all eight fields populated (AC-29):

```yaml
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    brew_ratio: 15.56
    method: "Hario V60"
    grind: "medium_fine"
    duration_s: 195
    coffee:
      type: "single_origin"
      origins:
        - name: "Ethiopia Yirgacheffe Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa Washing Station"
          process: "Natural"
          lot: "Lot 42 Export Grade 1"
          harvest_year: 2025
      varietal: "Heirloom"
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
      grinder_setting: "21 clicks"
      notes: "Burrs 3 months old"
    result:
      tds: 1.38
      ey: 20.1
      tasting_notes: "Bright citrus, blueberry jam, clean finish"
      ratings:
        overall: 5
        flavour: 5
        acidity: 4
```

**`valid_blend_origin.yaml`**

Demonstrates a blend with two `coffee.origins` entries (AC-30):

```yaml
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 270.0
    brew_ratio: 15.0
    method: "Hario V60"
    grind: "medium_fine"
    coffee:
      type: "blend"
      origins:
        - name: "Ethiopia component"
          country: "Ethiopia"
          region: "Yirgacheffe"
          process: "Washed"
        - name: "Colombia component"
          country: "Colombia"
          region: "Huila"
          process: "Natural"
          producer: "El Paraiso"
```

### 6.3 New Invalid Example File

**`examples/invalid/invalid_origin_string_array.yaml`**

Demonstrates that the old `coffee.origin` string array format is rejected by v0.5 (AC-34):

```yaml
# Invalid: coffee.origin string array format is not valid in BrewSpec v0.5.
# The coffee.origin field was removed in v0.5 and replaced by coffee.origins
# (structured object array). Because the coffee object enforces
# additionalProperties: false, any key not in the v0.5 coffee property list
# causes validation failure. To migrate, rename 'origin' to 'origins' and
# wrap each string in an object: { country: "Ethiopia" }.
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    coffee:
      origin:
        - "Ethiopia"
```

### 6.4 Carry-Forward Example Update

**`examples/invalid/rating_out_of_range.yaml`**

Replace the file contents with a corrected version that:
- Uses `brewspec_version: "0.5"`
- Contains `result.ratings.overall: 6` (value exceeds maximum of 5)
- Has a comment that accurately describes what causes the failure (AC-26)

```yaml
# Invalid: result.ratings.overall value of 6 exceeds the maximum of 5.
# All rating dimension fields (overall, fragrance, aroma, flavour, aftertaste,
# acidity, sweetness, mouthfeel) accept integers 1-5 inclusive only.
brewspec_version: "0.5"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    result:
      ratings:
        overall: 6
```

---

## 7. Test Strategy

All tests live in `tests/test_brewspec_schema.py` in the public brewspec repo. Tests validate against `brewspec.schema.json`. Group new tests by acceptance criterion. All existing passing tests must continue to pass after the schema update.

### AC-1: Version Const

| Test | Input | Expected |
|------|-------|----------|
| v0.5 const accepted | `brewspec_version: "0.5"` with a valid brew | passes |
| v0.4 const rejected | `brewspec_version: "0.4"` with otherwise valid v0.5 brew | fails |
| v0.3 const rejected | `brewspec_version: "0.3"` | fails |

### AC-2 to AC-7: `brew_ratio`

| Test | Input | Expected |
|------|-------|----------|
| Positive float accepted | `brew_ratio: 15.5` | passes |
| Fractional value accepted | `brew_ratio: 15.56` | passes |
| Integer value accepted | `brew_ratio: 15` | passes (JSON Schema `number` accepts integers) |
| Zero rejected | `brew_ratio: 0` | fails (exclusiveMinimum: 0) |
| Negative rejected | `brew_ratio: -1` | fails |
| Field omitted | no `brew_ratio` key | passes |
| String type rejected | `brew_ratio: "15.5"` | fails |

### AC-8 to AC-12: `equipment.grinder_setting`

| Test | Input | Expected |
|------|-------|----------|
| Click count accepted | `equipment: { grinder_setting: "21 clicks" }` | passes |
| Decimal setting accepted | `equipment: { grinder_setting: "3.0" }` | passes |
| Multi-part setting accepted | `equipment: { grinder_setting: "3.2.1" }` | passes |
| Empty string rejected | `equipment: { grinder_setting: "" }` | fails (minLength: 1) |
| Field omitted | no `grinder_setting` key | passes |
| All four equipment fields | `{ grinder, brewer, grinder_setting, notes }` all populated | passes |
| Unrecognised equipment field | `equipment: { grinder_setting: "21", colour: "red" }` | fails (additionalProperties) |

### AC-13 to AC-16: `equipment.notes`

| Test | Input | Expected |
|------|-------|----------|
| Notes string accepted | `equipment: { notes: "Burrs replaced 2026-01" }` | passes |
| Empty string rejected | `equipment: { notes: "" }` | fails (minLength: 1) |
| Field omitted | no `equipment.notes` key | passes |
| 2000-char string accepted | `equipment: { notes: "x" * 2000 }` | passes |
| 2001-char string rejected | `equipment: { notes: "x" * 2001 }` | fails (maxLength: 2000) |

### AC-17: `coffee.origin` Rejected

| Test | Input | Expected |
|------|-------|----------|
| Old string array rejected | `coffee: { origin: ["Ethiopia"] }` | fails (additionalProperties: false on coffee) |

### AC-18 to AC-25: `coffee.origins`

| Test | Input | Expected |
|------|-------|----------|
| Single entry accepted | `coffee: { origins: [{ country: "Ethiopia" }] }` | passes |
| Full eight-field entry accepted | all eight origin fields populated | passes |
| Two-entry blend accepted | `origins: [{...}, {...}]` | passes |
| Empty object entry accepted | `origins: [{}]` | passes (all fields optional) |
| Empty array rejected | `origins: []` | fails (minItems: 1) |
| Origins omitted entirely | no `origins` key on coffee | passes |
| Unrecognised origin field | `origins: [{ altitude: 1800 }]` | fails (additionalProperties: false on origin) |
| harvest_year: 2025 accepted | `harvest_year: 2025` | passes |
| harvest_year: 1899 rejected | `harvest_year: 1899` | fails (minimum: 1900) |
| harvest_year: 2101 rejected | `harvest_year: 2101` | fails (maximum: 2100) |
| harvest_year: 1900 accepted | `harvest_year: 1900` (boundary) | passes |
| harvest_year: 2100 accepted | `harvest_year: 2100` (boundary) | passes |
| harvest_year float rejected | `harvest_year: 2025.5` | fails (type: integer) |
| harvest_year string rejected | `harvest_year: "2025"` | fails (type: integer) |

### AC-26: Carry-Forward — `rating_out_of_range.yaml`

| Test | Input | Expected |
|------|-------|----------|
| `rating_out_of_range.yaml` fails validation | load and validate the file | fails with error on `result.ratings.overall` |

The test must assert that the file fails, not merely that it does not pass. Validate against v0.5 schema (version const `"0.5"` is in the file).

### AC-28 to AC-33: Examples Pass Validation

| Test | Input | Expected |
|------|-------|----------|
| All valid examples pass v0.5 schema | load each file in `examples/valid/` and validate | all pass |
| `valid_single_origin_full.yaml` passes | see Section 6.2 | passes |
| `valid_blend_origin.yaml` passes | see Section 6.2 | passes |
| `valid_brew_ratio.yaml` passes | `brew_ratio: 15.56` | passes |
| `valid_grinder_setting.yaml` passes | `grinder_setting: "21 clicks"` | passes |
| `valid_equipment_notes.yaml` passes | all four equipment fields | passes |

### AC-34: `invalid_origin_string_array.yaml` Fails Validation

| Test | Input | Expected |
|------|-------|----------|
| New invalid example fails | load `invalid_origin_string_array.yaml` | fails (additionalProperties on coffee) |

### AC-38: Minimum Required New Tests (checklist)

All of the following must exist as distinct test cases:

- `brew_ratio: 15.5` — passes
- `brew_ratio: 0` — fails
- `brew_ratio: -1` — fails
- `brew_ratio` omitted — passes
- `equipment.grinder_setting: "21 clicks"` — passes
- `equipment.grinder_setting: ""` — fails
- `equipment.grinder_setting` omitted — passes
- `equipment.notes: "Burrs replaced 2026-01"` — passes
- `equipment.notes: ""` — fails
- `equipment.notes` omitted — passes
- `equipment` with unrecognised field — fails
- `coffee.origins` with one full-detail entry — passes
- `coffee.origins` with two entries (blend) — passes
- `coffee.origins: []` (empty array) — fails
- `coffee.origins` entry with unrecognised field — fails
- `coffee.origin` (old string array) — fails
- `coffee.origins` omitted entirely — passes
- `brewspec_version: "0.4"` — rejected by v0.5 schema

---

## 8. Security Considerations

### Input Validation

**`brew_ratio`** — validated as `type: number` with `exclusiveMinimum: 0` at the JSON Schema level. The Pydantic `validate_brew_ratio` validator enforces the same constraint at the CLI input layer. Zero and negative values are rejected before reaching application logic. Type coercion (string-to-float) must not occur silently; the schema type constraint rejects non-numeric values.

**`coffee.origins` array** — each entry validated against `$defs.origin` with `additionalProperties: false`. Unrecognised fields are rejected before any data is written to storage. `harvest_year` is validated as `integer` within `1900–2100`; out-of-range and non-integer types (float, string) are rejected by the schema. An empty `origins: []` array is rejected by `minItems: 1` before processing.

**`equipment.grinder_setting`** — freeform string. `minLength: 1` rejects empty strings. `maxLength: 100` limits storage impact from adversarial or malformed input. The field must not be executed, evaluated, or interpolated by any tool. Stored and displayed as plain text only.

**`equipment.notes`** — freeform string. Same handling as `grinder_setting`. `maxLength: 2000` is the established ceiling for observation fields; limits storage impact.

All new string fields inherit the same safe-handling requirements as existing freeform fields: no SQL interpolation (use parameterised queries), no shell execution, stored and retrieved as opaque strings.

### Trust Boundaries

```
user input (CLI flags / YAML file)
  → Pydantic model validation (OriginInput, EquipmentInput, BrewInput)
    → JSON Schema validation (validate_document())
      → SQLite write (parameterised queries only)
        → display / export
```

No new trust boundaries are introduced. The existing pipeline — parse safely with `yaml.safe_load()`, validate with schema before writing — is unchanged.

### File I/O

`yaml.safe_load()` is required for all YAML parsing. No new file I/O patterns are introduced. Example files are plain YAML with no executable content.

### Data Integrity

Origin data (`coffee.origins`) fields contain coffee provenance information. No PII risk. `equipment.notes` is a personal observation field and may contain informal personal content (e.g., "bought second-hand from John"). This is consistent with the brew-level `notes` field treatment: local-only storage, not transmitted in v0.5, low sensitivity.

### Error Messages

Validation error messages from JSON Schema and Pydantic must not expose internal file paths, stack traces, or schema implementation details. Return the field name and the constraint violated. This is unchanged from v0.4.

---

## 9. File Manifest

Complete list of every file the dev must create or modify.

| File | Repo | Operation | Notes |
|------|------|-----------|-------|
| `brewspec.schema.json` | brewspec | Modify | Schema changes per Sections 1 and 2 |
| `src/brewlog/brewspec.schema.json` | brewspec | Modify | Keep in sync with root schema |
| `brewspec-v0.5.md` | brewspec | Create | Per Section 5 |
| `versions/brewspec-v0.4.md` | brewspec | Archive | Copy `brewspec-v0.4.md` to `versions/` before overwriting |
| `examples/valid/*.yaml` (all existing) | brewspec | Modify | Version bump `"0.4"` → `"0.5"`; migrate `coffee.origin` → `coffee.origins` |
| `examples/valid/valid_brew_ratio.yaml` | brewspec | Create | Per Section 6.2 |
| `examples/valid/valid_grinder_setting.yaml` | brewspec | Create | Per Section 6.2 |
| `examples/valid/valid_equipment_notes.yaml` | brewspec | Create | Per Section 6.2 |
| `examples/valid/valid_single_origin_full.yaml` | brewspec | Create | Per Section 6.2 |
| `examples/valid/valid_blend_origin.yaml` | brewspec | Create | Per Section 6.2 |
| `examples/invalid/invalid_origin_string_array.yaml` | brewspec | Create | Per Section 6.3 |
| `examples/invalid/rating_out_of_range.yaml` | brewspec | Modify | Per Section 6.4 — corrected comment, updated version, result.ratings.overall: 6 |
| `README.md` | brewspec | Modify | Add `invalid_date_no_z.yaml`, `invalid_grind_freeform.yaml`, `invalid_tds_at_brew_level.yaml` to invalid examples inventory with brief descriptions (AC-27) |
| `tests/test_brewspec_schema.py` | brewspec | Modify | Add test cases per Section 7 |
| `src/brewlog/models.py` | brewspec | Modify | Add `OriginInput`; update `CoffeeInput`, `EquipmentInput`, `BrewInput` per Section 4 |

---

## 10. TDD Implementation Order

Follow this sequence. Write failing tests before any implementation code at each step.

1. **Write failing tests for AC-1** (version const). Run — expect failure because schema still says `"0.4"`.
2. **Update `brewspec.schema.json` root-level** — bump `const` to `"0.5"` and update `title` and `description`. Run AC-1 tests — expect pass. Run full suite — all pre-existing tests should now fail on version const; note these are expected to fail until examples are migrated.
3. **Write failing tests for AC-2 through AC-7** (`brew_ratio`). Run — expect failure.
4. **Add `brew_ratio` to `$defs.brew`** in schema. Run AC-2–7 tests — expect pass.
5. **Write failing tests for AC-8 through AC-16** (`equipment.grinder_setting` and `equipment.notes`). Run — expect failure.
6. **Update `$defs.equipment`** in schema — add `grinder_setting` and `notes`. Run AC-8–16 tests — expect pass.
7. **Write failing tests for AC-17 through AC-25** (`coffee.origin` removal, `coffee.origins` addition). Run — expect failure.
8. **Update `$defs.coffee`** — remove `origin`, add `origins`. **Add `$defs.origin`** to schema. Run AC-17–25 tests — expect pass.
9. **Write failing test for AC-34** (`invalid_origin_string_array.yaml`). Create the file. Run — expect pass (file exists and fails validation as intended).
10. **Migrate all existing valid examples** — version bump and `coffee.origin` → `coffee.origins` migration. Run the full examples-pass test — expect pass.
11. **Create new valid example files** per Section 6.2. Write tests for AC-28 through AC-33. Run — expect pass.
12. **Update `rating_out_of_range.yaml`** per Section 6.4. Write AC-26 test. Run — expect pass.
13. **Update `README.md`** with invalid examples inventory (AC-27). No test required; verify manually.
14. **Update Pydantic models** (`models.py`) per Section 4. Verify model-level tests pass.
15. **Run full test suite** — expect 100% pass.
16. **Run `ruff check .`** — fix any lint errors before handoff.
