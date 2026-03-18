# Design: BrewSpec v0.4

**Feature:** brewspec-v0.4
**Author:** architect
**Created:** 2026-02-22
**Input:** specs/products/brewspec-v0.4.md
**Baseline:** specs/designs/brewspec-v0.3.md
**Status:** Ready for Dev

---

## Overview

This document specifies every schema, model, test, and file change required to produce BrewSpec v0.4. v0.4 is a larger and more breaking iteration than v0.3. Three fields are removed from the flat brew level (`tds`, `ey`, `rating`), grouped into a new `result` object alongside new fields (`brix`, `tasting_notes`, `ratings`). The `grind` field changes from a freeform string to a strict 7-value enum. The `date` field gains a date-only format alternative. The `brewspec_version` const advances to `"0.4"`.

The dev should follow the TDD order in Section 9 (write failing tests first, then implement schema changes, then update examples and models).

---

## 1. JSON Schema Diff (v0.3 → v0.4)

This section specifies every change to `brewspec.schema.json`. The full target schema is in Section 2.

### 1.1 Root-Level Changes

| Location | v0.3 Value | v0.4 Value | AC |
|----------|-----------|-----------|-----|
| `title` | `"BrewSpec v0.3"` | `"BrewSpec v0.4"` | AC-1 |
| `properties.brewspec_version.const` | `"0.3"` | `"0.4"` | AC-1 |
| `properties.brewspec_version.description` | `"The BrewSpec version. Must be \"0.3\"."` | `"The BrewSpec version. Must be \"0.4\"."` | AC-1 |

The `$schema` and `$id` values are unchanged.

### 1.2 `$defs.brew` Changes

**`date` field — dual-format pattern:**

The v0.3 `date` field uses a single pattern: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`

Replace with `oneOf` accepting two alternative patterns:

```json
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
}
```

See Section 3 for the design decision rationale on `oneOf` vs. a combined pattern.

**`grind` field — changed from freeform string to strict enum:**

Replace the freeform string definition with an enum:

```json
"grind": {
  "type": "string",
  "enum": ["turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"],
  "description": "Grind size. Standard vocabulary from finest to coarsest: turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse."
}
```

The `minLength` and `maxLength` constraints from v0.3 are removed; they are not meaningful for an enum.

**Fields removed from `$defs.brew`:**

The following properties are removed from `$defs.brew.properties`. Because `$defs.brew` uses `additionalProperties: false`, any document with these fields at the brew level will now fail validation.

| Property Removed | v0.3 Definition | Reason |
|-----------------|-----------------|--------|
| `tds` | `{type: number, exclusiveMinimum: 0}` | Moved to `result` object |
| `ey` | `{type: number, exclusiveMinimum: 0}` | Moved to `result` object |
| `rating` | `{type: integer, minimum: 1, maximum: 5}` | Removed; replaced by `result.ratings` object |

**New field added to `$defs.brew`:**

```json
"result": {
  "$ref": "#/$defs/result"
}
```

**`notes` description updated (no schema constraint change):**

Change the `notes` description string from:

`"Freeform tasting or session notes."`

to:

`"Brew-process notes — operational observations about the preparation (e.g. 'washed filter paper', 'water from Brita filter', 'grinder re-calibrated'). For sensory description, use result.tasting_notes."`

All other fields in `$defs.brew` are unchanged: `type`, `method`, `dose_g`, `water_weight_g`, `water_volume_ml`, `water_temp_c`, `coffee`, `water`, `equipment`, `duration_s`.

### 1.3 New `$defs.result`

Add a new definition to `$defs`:

```json
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
}
```

### 1.4 New `$defs.ratings`

Add a new definition to `$defs`:

```json
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
```

---

## 2. Full Annotated v0.4 Schema

This is the complete target `brewspec.schema.json`. The dev writes this verbatim to `brewspec.schema.json` in the public repo (and to `src/brewlog/brewspec.schema.json` in the CLI package, which must stay in sync).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json",
  "title": "BrewSpec v0.4",
  "description": "An open standard for describing coffee brews.",
  "type": "object",
  "required": ["brewspec_version", "brews"],
  "additionalProperties": false,
  "properties": {
    "brewspec_version": {
      "const": "0.4",
      "description": "The BrewSpec version. Must be \"0.4\"."
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

### 3.1 `date` Dual-Format: `oneOf` vs. Combined Regex Pattern

**Decision: Use `oneOf` with two sub-schemas, each containing a `pattern` keyword.**

**Alternatives considered:**

**Option A — Single pattern with regex alternation (`|`):**

```json
"pattern": "^(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z|\\d{4}-\\d{2}-\\d{2})$"
```

This works mechanically, but has two problems:
1. The error message from validators like `jsonschema` reports the full combined pattern, giving users no signal about which of the two expected formats they failed to match.
2. A date string like `"2026-02-21T08:30:00"` (missing the Z) would produce an error pointing at the combined regex rather than explaining that UTC suffix is required. Debugging is harder.

**Option B — `oneOf` with two sub-schemas (chosen):**

```json
"oneOf": [
  {"pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$"},
  {"pattern": "^\\d{4}-\\d{2}-\\d{2}$"}
]
```

Tradeoffs:
- Pro: Each sub-schema carries its own `description` and `pattern`, making error context more readable. The validator can report which alternative was attempted.
- Pro: Extensible — a third format alternative can be added as a third sub-schema without rewriting a combined regex.
- Con: A `type: string` constraint must remain on the parent property (not inside the `oneOf` sub-schemas) to keep the schema clean, as `oneOf` evaluates both sub-schemas and requires exactly one to match. A bare string satisfies both sub-schemas if neither pattern is present, but once `pattern` is added to both, only one can match for any given string. For the date-only string `"2026-02-21"`, it matches the date-only pattern and fails the datetime pattern — exactly one matches. For the datetime string `"2026-02-21T08:30:00Z"`, it fails the date-only pattern and matches the datetime pattern — exactly one matches.

**Implementation note on `type: string` placement:**

The `type: string` keyword is placed at the property level (parent of `oneOf`), not inside the sub-schemas. This prevents the two sub-schemas from each re-asserting type, which would produce redundant failures. The full definition:

```json
"date": {
  "type": "string",
  "oneOf": [
    {"pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$", "description": "..."},
    {"pattern": "^\\d{4}-\\d{2}-\\d{2}$", "description": "..."}
  ],
  "description": "...",
  "examples": [...]
}
```

**Why Z is required for the datetime format:**

The `Z` suffix enforces UTC. Permitting offsets like `+10:00` would allow two files representing the same moment to be recorded differently, breaking time-based comparison in analytics. Date-only format solves the primary UX problem (users who do not want to record a time). Full datetime with timezone offsets is excluded intentionally — see the product spec Design Notes.

**Calendar validation:**

The patterns enforce format only, not calendar correctness. `"2026-13-01"` (month 13) passes schema validation per AC-7. Calendar-correct validation is an application-layer responsibility.

### 3.2 `grind` Enum: 7 Values, Strict, No Freeform Fallback

**Decision: Replace freeform string with a closed 7-value enum. No fallback accepted.**

The values in coarseness order (finest to coarsest):
`turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`

`turkish` and `espresso` are named-standard grinds, not generic descriptors. A barista knows what "espresso" grind means. "extra_fine" requires interpretation. Named standards anchor the vocabulary to practice.

A freeform fallback (`oneOf` enum + arbitrary string) would defeat the standardization goal: tools could continue sending arbitrary values, making cross-brew and cross-user comparison impossible. Users who want to record a specific setting number (e.g., "setting 15 on Comandante") should use the `notes` field.

### 3.3 `result` Object: Optional, `additionalProperties: false`, No Required Fields Inside

**Decision: `result` follows the same pattern as `coffee`, `water`, and `equipment`.**

All fields inside `result` are optional. `additionalProperties: false` prevents unexpected data. An empty `result: {}` is valid — this is consistent with how `equipment: {}` is valid in v0.3. Tools should treat `result: {}` identically to no `result` key.

**Why `brix` uses `minimum: 0` and not `exclusiveMinimum: 0`:**

0 °Brix is a physically valid reading (distilled water). `tds` and `ey` use `exclusiveMinimum: 0` because a brew TDS or extraction yield of exactly 0 is meaningless (it means no extraction occurred, i.e., not a brew). 0 °Brix can arise from a clean refractometer baseline and is a legitimate measurement.

**Why `ratings` is a separate `$defs` entry:**

Consistent with `equipment`, `coffee`, `water`, and `result`, which are all defined in `$defs` and referenced via `$ref`. This keeps `$defs.result` readable and makes `$defs.ratings` independently referenceable if other objects ever need it.

### 3.4 Breaking Changes: `additionalProperties: false` Enforcement

`$defs.brew` already carries `additionalProperties: false` from v0.3. Removing `tds`, `ey`, and `rating` from `$defs.brew.properties` means they are automatically rejected at the brew level without any additional schema keyword — `additionalProperties: false` handles it.

This is the cleanest possible enforcement: it requires zero new schema constructs. The properties list shrinks; the constraint was already there.

### 3.5 `notes` vs. `result.tasting_notes`

No schema change to `notes`. The constraint (`type: string`, `minLength: 1`, `maxLength: 2000`) is unchanged. The distinction is a documentation and UX concern, not a schema enforcement concern. The description string in the schema is updated to make the distinction clear. Tool authors are expected to surface this distinction in their UIs (e.g., BrewLog CLI can label the prompts differently).

---

## 4. Pydantic Model Changes (`src/brewlog/models.py`)

The Pydantic models must be updated to match the v0.4 schema. The schema (`validate_document()` in `schema.py`) is the authoritative validation gate; the Pydantic models are the CLI input layer. Both must be consistent.

### 4.1 New Constants

Add to the constants section:

```python
GRIND_ENUM = frozenset({
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse"
})

DATE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z|\d{4}-\d{2}-\d{2})$"
)
```

The `DATE_PATTERN` constant is updated from the v0.3 datetime-only pattern to accept both formats. A combined regex is appropriate here (Python-level validation, not user-facing JSON Schema errors). The Pydantic `validate_date` method will use this pattern and then apply format-specific secondary validation.

### 4.2 New `RatingsInput` Model

Add before `BrewInput`:

```python
class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-5."""

    overall: Optional[int] = None
    fragrance: Optional[int] = None
    aroma: Optional[int] = None
    flavour: Optional[int] = None
    aftertaste: Optional[int] = None
    acidity: Optional[int] = None
    sweetness: Optional[int] = None
    mouthfeel: Optional[int] = None

    @field_validator(
        "overall", "fragrance", "aroma", "flavour",
        "aftertaste", "acidity", "sweetness", "mouthfeel"
    )
    @classmethod
    def validate_rating_dimension(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating dimension must be between 1 and 5 inclusive")
        return v
```

### 4.3 New `ResultInput` Model

Add after `RatingsInput`:

```python
class ResultInput(BaseModel):
    """Optional brew outcome descriptor. All fields optional."""

    tds: Optional[float] = None
    ey: Optional[float] = None
    brix: Optional[float] = None
    tasting_notes: Optional[str] = None
    ratings: Optional[RatingsInput] = None

    @field_validator("tds", "ey")
    @classmethod
    def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    @field_validator("brix")
    @classmethod
    def validate_brix(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("brix must be >= 0")
        return v

    @field_validator("tasting_notes")
    @classmethod
    def validate_tasting_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("tasting_notes must not be empty when provided")
            if len(v) > 2000:
                raise ValueError("tasting_notes must not exceed 2000 characters")
        return v
```

### 4.4 Updates to `BrewInput`

**Fields to remove from `BrewInput`:**

Remove these three fields from the optional brew parameters section:

```python
tds: Optional[float] = None      # REMOVE — moved to ResultInput
ey: Optional[float] = None       # REMOVE — moved to ResultInput
rating: Optional[int] = None     # REMOVE — replaced by result.ratings
```

**Fields to add to `BrewInput`:**

Add to the optional nested objects section:

```python
result: Optional[ResultInput] = None
```

**Validators to remove from `BrewInput`:**

Remove the `validate_exclusive_positive` validator that covered `tds` and `ey` (they no longer live on `BrewInput`):

```python
@field_validator("water_volume_ml", "tds", "ey")   # REMOVE
@classmethod
def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
    ...
```

Replace with a validator covering only `water_volume_ml`:

```python
@field_validator("water_volume_ml")
@classmethod
def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("value must be greater than 0")
    return v
```

Remove the `validate_rating` validator entirely (the `rating` field no longer exists on `BrewInput`):

```python
@field_validator("rating")         # REMOVE
@classmethod
def validate_rating(cls, v: Optional[int]) -> Optional[int]:
    ...
```

**`grind` validator update:**

The `validate_short_text` validator currently accepts any non-empty string up to 100 characters for `grind`. Replace with an enum check:

```python
@field_validator("grind")
@classmethod
def validate_grind(cls, v: Optional[str]) -> Optional[str]:
    if v is not None and v not in GRIND_ENUM:
        raise ValueError(
            f"grind must be one of: {sorted(GRIND_ENUM)}"
        )
    return v
```

The `method` field retains the existing `validate_short_text` logic (freeform string, maxLength 100). Since `grind` now has its own validator, `validate_short_text` should only apply to `method`:

```python
@field_validator("method")
@classmethod
def validate_short_text(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        if len(v) > 100:
            raise ValueError("value must not exceed 100 characters")
    return v
```

**`date` validator update:**

Update `validate_date` to accept both formats. The secondary parse check applies format-specific logic:

```python
@field_validator("date")
@classmethod
def validate_date(cls, v: str) -> str:
    if not DATE_PATTERN.match(v):
        raise ValueError(
            "date must be YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ"
        )
    # Format-specific secondary validation
    if "T" in v:
        # Full datetime — verify it parses as a real datetime
        try:
            datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("date is not a valid datetime")
    # Date-only format: the pattern ^\\d{4}-\\d{2}-\\d{2}$ enforces format.
    # Calendar correctness (e.g., month 13) is NOT checked here per AC-7.
    return v
```

**Updated docstring for `BrewInput`:**

```python
class BrewInput(BaseModel):
    """Primary model for a brew log entry. Validates all BrewSpec v0.4 constraints."""
```

### 4.5 Complete Updated `BrewInput` Field List

After the changes, `BrewInput` contains:

**Required fields:**
- `date: str`
- `type: str`
- `dose_g: float`
- `water_weight_g: float`

**Optional brew parameters:**
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

Fields removed: `tds`, `ey`, `rating`.

---

## 5. Spec Document Changes (`brewspec-v0.4.md` in the public repo)

The dev produces `brewspec-v0.4.md` in the public repo. The following sections must be present or updated. All other sections from `brewspec-v0.3.md` are preserved with version references updated.

### 5.1 Header

```
# BrewSpec v0.4
Status: Stable
Version: 0.4
Last Updated: [date of deployment]
```

### 5.2 Complete Field Reference Tables

**Top-Level Fields** (unchanged from v0.3):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.4"` | The BrewSpec version |
| `brews` | array | Required | Minimum 1 element | Array of brew objects |

**Brew Object:**

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Required | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Brew date or datetime (UTC) | `"2026-02-21"`, `"2026-02-15T08:30:00Z"` |
| `type` | string | Required | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Required | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Required | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `method` | string | Optional | Min length 1, max length 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `equipment` | object | Optional | See Equipment Object | Equipment descriptor | |
| `grind` | string | Optional | Enum: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse` | Grind size | `"medium_fine"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `notes` | string | Optional | Min length 1, max length 2000 | Brew-process notes — operational observations about the preparation. For sensory description, use `result.tasting_notes`. | `"Washed filter paper, water from Brita filter"` |
| `result` | object | Optional | See Result Object | Brew outcome measurements and sensory evaluation | |

**Coffee Object** (entire object optional; all fields within optional): unchanged from v0.3.

**Water Object** (entire object optional; all fields within optional): unchanged from v0.3.

**Equipment Object** (entire object optional; all fields within optional): unchanged from v0.3.

**Result Object** (entire object optional; all fields within optional):

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `tds` | number | Optional | > 0 (exclusive) | Total dissolved solids percentage | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield as a percentage | `20.1`, `19.8` |
| `brix` | number | Optional | >= 0 | Dissolved sugar content in degrees Brix. 0 is valid. | `1.5`, `0` |
| `tasting_notes` | string | Optional | Min length 1, max length 2000 | Sensory description of the brew | `"Bright citrus, caramel finish"` |
| `ratings` | object | Optional | See Ratings Object | Multi-dimensional sensory ratings | |

**Ratings Object** (entire object optional; all fields within optional integers 1–5):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `overall` | integer | Optional | 1–5 inclusive | Holistic impression |
| `fragrance` | integer | Optional | 1–5 inclusive | Dry grounds aroma before water is added |
| `aroma` | integer | Optional | 1–5 inclusive | Wet aroma after water is added |
| `flavour` | integer | Optional | 1–5 inclusive | Taste and aroma experienced during drinking |
| `aftertaste` | integer | Optional | 1–5 inclusive | Length and quality of positive flavour attributes |
| `acidity` | integer | Optional | 1–5 inclusive | Quality (not quantity) of acidity; brightness |
| `sweetness` | integer | Optional | 1–5 inclusive | Perceived sweetness |
| `mouthfeel` | integer | Optional | 1–5 inclusive | Tactile sensation; body and texture |

### 5.3 "What Changed in v0.4" Section

The spec document must include this section:

```
## What Changed in v0.4

### Version bump
brewspec_version const updated from "0.3" to "0.4". Schema title updated to "BrewSpec v0.4".

### Date field: dual-format accepted
The date field now accepts two formats:
- YYYY-MM-DD (date-only) — new in v0.4
- YYYY-MM-DDTHH:MM:SSZ (full UTC datetime) — previously the only accepted format

Both are valid ISO 8601 formats. The Z suffix is still required for full datetime.
Date-only format does not include a time component; tools should treat it as a
calendar date without assuming any specific time of day.

### grind field: strict enum
The grind field changes from a freeform string to a strict 7-value enum.
Accepted values (finest to coarsest): turkish, espresso, fine, medium_fine,
medium, medium_coarse, coarse.
Freeform values (e.g. "setting 15", "medium-fine") are rejected. v0.3 files
using freeform grind values must update to the nearest enum value or remove
the field before validating against v0.4.

### New result object
A new optional result object groups all brew outcome data:
- tds — moved from brew level (breaking change from v0.3)
- ey — moved from brew level (breaking change from v0.3)
- brix — new field; dissolved sugar content in degrees Brix (>= 0)
- tasting_notes — new field; sensory description string (maxLength 2000)
- ratings — new object; 8 optional integer dimensions 1-5, SCA-aligned

### Brew-level fields removed (breaking changes)
Three fields are removed from the flat brew level:
- tds — rejected at brew level; must be placed inside result
- ey — rejected at brew level; must be placed inside result
- rating — removed entirely; use result.ratings.overall for the equivalent value

### notes field clarification (no schema change)
The notes field description is updated to clarify it is for brew-process and
operational observations, not sensory description. Use result.tasting_notes
for sensory impressions. No schema constraint change; this is documentation only.
```

### 5.4 "Validation" Section

The spec document must include this section (addresses review carry-forward Q3 from v0.3):

```
## Validation

Tools implementing BrewSpec should validate a brew document at storage time —
before writing to any database or file — not only at display or read time.

The expected pipeline is:
1. Safe parse — load YAML with yaml.safe_load() or JSON with json.load().
   Never eval() user input.
2. Schema validation — validate the parsed document against the versioned
   brewspec.schema.json using a Draft 2020-12 validator. Reject the document
   if validation fails.
3. Application logic — only after validation passes, write the document to
   persistent storage and proceed with application behaviour.

A document that has not passed schema validation must never be written to
storage. Validating only at read or display time allows corrupt or malformed
documents to accumulate in storage and surface as errors later.

Tools should read brewspec_version from the document first and select the
matching schema version for validation. Do not validate a v0.3 document
against the v0.4 schema.
```

### 5.5 "Backward Compatibility" Section

The spec document must include this section:

```
## Backward Compatibility

v0.4 introduces breaking changes beyond the version const. v0.3 files that
use tds, ey, or rating at the brew level, or that use a freeform grind value,
will fail v0.4 schema validation.

### Breaking changes

| Change | v0.3 Behaviour | v0.4 Behaviour |
|--------|----------------|----------------|
| Flat tds | Optional number on brew object | Removed; rejected at brew level; valid only inside result |
| Flat ey | Optional number on brew object | Removed; rejected at brew level; valid only inside result |
| Flat rating | Optional integer 1-5 on brew object | Removed; no direct replacement; map to result.ratings.overall |
| grind values | Any freeform string | Strict 7-value enum; freeform values rejected |

### Additive changes (no action required for v0.3 files)

These changes add new fields or format options. v0.3 files that do not use
these fields are not affected by these additions once the version const is
updated.

| Change | Action required |
|--------|-----------------|
| date dual-format | None; existing datetime strings still valid |
| brix field | None; new optional field |
| tasting_notes field | None; new optional field |
| ratings object | None; new optional object |
| result object (if not used) | None; new optional object |

### Migrating a v0.3 file to v0.4

1. Update brewspec_version from "0.3" to "0.4".
2. If tds is present at the brew level: move it to result.tds.
3. If ey is present at the brew level: move it to result.ey.
4. If rating is present at the brew level: move its value to
   result.ratings.overall. The 1-5 scale is unchanged.
5. If grind is present: replace the freeform value with the nearest enum value
   (turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse).
   If no enum value is a reasonable match, remove the grind field.
6. Validate against the v0.4 schema.

### Tools and version selection

Tools should read brewspec_version before selecting a schema. A file declaring
brewspec_version: "0.3" should be validated against the v0.3 schema only.
Do not validate a v0.3 file against the v0.4 schema — it will fail on the
version const alone even if no other fields changed.
```

---

## 6. Example File Plan

### 6.1 Path Note

The test file in the public repo loads examples from paths rooted at the repo root. The dev must verify paths by reading the `SCHEMA_PATH`, `VALID_DIR`, and `INVALID_DIR` constants in `tests/test_brewspec_schema.py`. Files below are identified by name; the dev resolves the actual directory.

### 6.2 Existing Valid Examples — Version Bump and Migration Required

All valid example files must be updated to `brewspec_version: "0.4"`. Where `tds`, `ey`, or `rating` appear at the brew level, migrate them into the `result` object. Where `grind` appears as a freeform string, update it to the nearest enum value.

**`pour_over.yaml`** (AC-29, AC-31, AC-32, AC-33, AC-35)

Update `brewspec_version` to `"0.4"`. Keep the existing full datetime `date` field — this example continues to use `YYYY-MM-DDTHH:MM:SSZ` format. Move existing `tds` and `ey` into `result`. Update `grind` from whatever freeform value is currently present to `"medium_fine"`. Add `result.tasting_notes`. Add `result.ratings` with at least `overall` and one other dimension.

Target `result` addition:
```yaml
result:
  tds: 1.38
  ey: 20.5
  tasting_notes: "Bright citrus acidity, caramel sweetness, clean finish"
  ratings:
    overall: 4
    aroma: 4
    acidity: 5
```

**`pour_over.json`** (AC-29, AC-31)

Same changes as `pour_over.yaml` in JSON format.

**`espresso.yaml`** (AC-29, AC-32, AC-34, AC-35)

Update `brewspec_version` to `"0.4"`. Move existing `ey` to `result`. Update `grind` to `"espresso"`. Add `result.brix`:

```yaml
grind: "espresso"
result:
  ey: 19.8
  brix: 1.5
  ratings:
    overall: 4
    mouthfeel: 5
```

**`multi_brew.yaml`** (AC-29, AC-30)

Update `brewspec_version` to `"0.4"`. On the brew that has `tds`/`ey`, migrate to `result`. Use date-only format (`YYYY-MM-DD`) on at least one brew — this example satisfies AC-30.

Target first brew date field:
```yaml
date: "2026-02-21"
```

**`immersion_minimal.yaml`** (AC-29)

Update `brewspec_version` to `"0.4"`. No other changes (this is the minimal example, demonstrates that omitting `result` is valid).

**`hybrid.yaml`** (AC-29)

Update `brewspec_version` to `"0.4"`. No other field changes required.

### 6.3 New Valid Example (AC-30, AC-32, AC-33, AC-34, AC-35)

**`pour_over_date_only.yaml`** — New file. A complete pour-over brew using date-only format, demonstrating all new `result` fields.

```yaml
# Valid example: date-only format and full result object.
# Demonstrates YYYY-MM-DD date, grind enum, result with all fields.
brewspec_version: "0.4"
brews:
  - date: "2026-02-21"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    grind: "medium_fine"
    water_temp_c: 96
    duration_s: 210
    method: "Hario V60 02"
    notes: "Washed filter paper, water from Brita filter"
    coffee:
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "Hario V60 02"
    result:
      tds: 1.38
      ey: 20.1
      brix: 1.5
      tasting_notes: "Bright citrus acidity, caramel sweetness, clean finish"
      ratings:
        overall: 4
        fragrance: 3
        aroma: 4
        flavour: 5
        aftertaste: 4
        acidity: 5
        sweetness: 3
        mouthfeel: 4
```

### 6.4 New Invalid Examples

**`invalid_date_no_z.yaml`** (AC-36)

```yaml
# This file demonstrates that a datetime string without the Z suffix is rejected.
# date must be YYYY-MM-DDTHH:MM:SSZ (Z is required) or YYYY-MM-DD (date-only).
brewspec_version: "0.4"
brews:
  - date: "2026-02-21T09:00:00"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
```

Expected validation error: The string matches neither accepted pattern.

**`invalid_grind_freeform.yaml`** (AC-37)

```yaml
# This file demonstrates that a freeform grind value is rejected.
# grind accepts only: turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse
brewspec_version: "0.4"
brews:
  - date: "2026-02-21"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    grind: "setting 15"
```

Expected validation error: `"setting 15"` is not in the enum.

**`invalid_tds_at_brew_level.yaml`** (AC-38)

```yaml
# This file demonstrates that tds at the flat brew level is now rejected.
# tds was moved to the result object in v0.4.
# Use result.tds instead.
brewspec_version: "0.4"
brews:
  - date: "2026-02-21"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    tds: 1.38
```

Expected validation error: Additional properties not allowed (`tds` was unexpected at the brew level).

---

## 7. Test Strategy

### 7.1 Test File Locations

The dev updates two test files:

1. `tests/test_brewspec_schema.py` in the **public repo** — schema and example file tests.
2. `brewlog/tests/test_models.py` in the **public repo** (inside the `brewlog/` subdirectory) — Pydantic model tests.

### 7.2 Schema Test Updates

**Baseline dict update:**

Change the `VALID_BREW` and `VALID_DOC` constants at the top of the test file:

```python
VALID_BREW = {
    "date": "2026-02-15T08:30:00Z",
    "type": "pour_over",
    "dose_g": 20,
    "water_weight_g": 320
}
VALID_DOC = {"brewspec_version": "0.4", "brews": [VALID_BREW]}
```

**Version const test update:**

Rename `test_version_must_be_0_3` to `test_version_must_be_0_4`. Update the assertion to test `"0.4"`. Add a test that `"0.3"` is rejected:

```python
def test_version_must_be_0_4(validator):
    """brewspec_version is required and must be exactly '0.4'."""
    with pytest.raises(ValidationError):
        validator.validate({"brews": [VALID_BREW]})
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "1.0", "brews": [VALID_BREW]})
    validator.validate(VALID_DOC)


def test_version_const_rejects_v0_3(validator):
    """brewspec_version '0.3' is rejected by the v0.4 schema."""
    with pytest.raises(ValidationError):
        validator.validate({"brewspec_version": "0.3", "brews": [VALID_BREW]})
```

### 7.3 New Schema Test Functions

All new tests use `VALID_BREW` and `VALID_DOC` as defined above. Add all of the following to `tests/test_brewspec_schema.py`:

```python
# --- Date format ---

def test_date_only_format_accepted(validator):
    """date: YYYY-MM-DD (date-only) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-21"}]
    })


def test_date_full_datetime_accepted(validator):
    """date: YYYY-MM-DDTHH:MM:SSZ (full datetime) passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00Z"}]
    })


def test_date_no_z_rejected(validator):
    """date: datetime without Z suffix fails validation (AC-5)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "date": "2026-02-21T09:00:00"}]
        })


def test_date_wrong_order_rejected(validator):
    """date: DD-MM-YYYY order fails validation (AC-6)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "date": "21-02-2026"}]
        })


def test_date_month_13_passes_schema(validator):
    """date: month 13 passes schema validation (AC-7). Calendar validation is application-layer."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "date": "2026-13-01"}]
    })


# --- grind enum ---

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"
])
def test_grind_enum_all_values_accepted(validator, grind_value):
    """Each of the 7 grind enum values passes validation (AC-10, AC-11)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "grind": grind_value}]
    })


def test_grind_freeform_rejected(validator):
    """grind: freeform string not in the enum fails validation (AC-12)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "setting 15"}]
        })


def test_grind_wrong_case_rejected(validator):
    """grind: 'Medium' (wrong case) fails validation (AC-13)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "grind": "Medium"}]
        })


def test_grind_omitted_accepted(validator):
    """grind omitted entirely passes validation (field remains optional, AC-14)."""
    validator.validate(VALID_DOC)


# --- result object ---

def test_result_omitted_accepted(validator):
    """Brew without result passes validation (AC-17)."""
    validator.validate(VALID_DOC)


def test_result_empty_object_accepted(validator):
    """result: {} (empty object) passes validation (AC-18)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {}}]
    })


def test_result_tds_ey_accepted(validator):
    """result with tds and ey passes validation (AC-20)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tds": 1.38, "ey": 20.1}}]
    })


def test_result_unknown_field_rejected(validator):
    """result with an unrecognised field fails validation (AC-19)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"score": 95}}]
        })


# --- tds and ey removed from brew level ---

def test_tds_at_brew_level_rejected(validator):
    """tds at flat brew level fails validation in v0.4 (AC-20)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "tds": 1.38}]
        })


def test_ey_at_brew_level_rejected(validator):
    """ey at flat brew level fails validation in v0.4 (AC-20)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "ey": 20.1}]
        })


def test_rating_at_brew_level_rejected(validator):
    """rating at flat brew level fails validation in v0.4 (AC-27)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "rating": 4}]
        })


# --- result.brix ---

def test_result_brix_valid_accepted(validator):
    """result.brix: 1.5 passes validation (AC-21)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 1.5}}]
    })


def test_result_brix_zero_accepted(validator):
    """result.brix: 0 passes validation (AC-21, minimum: 0 not exclusive)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"brix": 0}}]
    })


def test_result_brix_negative_rejected(validator):
    """result.brix: -1 fails validation (AC-21, minimum: 0)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"brix": -1}}]
        })


# --- result.ratings ---

def test_ratings_partial_accepted(validator):
    """result.ratings with only some dimensions passes validation (AC-24)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 4, "acidity": 3}}}]
    })


def test_ratings_overall_maximum_accepted(validator):
    """result.ratings.overall: 5 passes validation (AC-25, at maximum)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 5}}}]
    })


def test_ratings_overall_minimum_accepted(validator):
    """result.ratings.overall: 1 passes validation (at minimum)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 1}}}]
    })


def test_ratings_below_minimum_rejected(validator):
    """result.ratings.overall: 0 fails validation (AC-25, minimum: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 0}}}]
        })


def test_ratings_above_maximum_rejected(validator):
    """result.ratings.overall: 6 fails validation (AC-25, maximum: 5)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 6}}}]
        })


def test_ratings_float_rejected(validator):
    """result.ratings.overall: 3.5 fails validation (AC-25, must be integer)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"overall": 3.5}}}]
        })


def test_ratings_unknown_field_rejected(validator):
    """result.ratings with an unrecognised field fails validation (additionalProperties: false)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"ratings": {"balance": 4}}}]
        })


# --- result.tasting_notes ---

def test_result_tasting_notes_accepted(validator):
    """result.tasting_notes: non-empty string passes validation (AC-26)."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "Bright citrus"}}]
    })


def test_result_tasting_notes_maxlength_accepted(validator):
    """result.tasting_notes: exactly 2000 chars passes validation."""
    validator.validate({
        "brewspec_version": "0.4",
        "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2000}}]
    })


def test_result_tasting_notes_maxlength_exceeded(validator):
    """result.tasting_notes: 2001 chars fails validation (maxLength: 2000)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": "x" * 2001}}]
        })


def test_result_tasting_notes_empty_rejected(validator):
    """result.tasting_notes: empty string fails validation (minLength: 1)."""
    with pytest.raises(ValidationError):
        validator.validate({
            "brewspec_version": "0.4",
            "brews": [{**VALID_BREW, "result": {"tasting_notes": ""}}]
        })
```

### 7.4 Model Test Updates (`brewlog/tests/test_models.py`)

**Tests to remove:**

- `test_brew_input_valid_all_fields` — references `tds`, `ey`, `rating` on `BrewInput`. Replace with an updated version that uses `result=ResultInput(...)`.
- `test_brew_input_invalid_date_format` — the test currently expects `"2026-02-19"` (date-only) to be rejected. In v0.4, date-only is valid. Remove this test. The relevant rejection case is non-pattern strings.
- `test_brew_input_rating_low_boundary`, `test_brew_input_rating_high_boundary`, `test_brew_input_rating_below_min`, `test_brew_input_rating_above_max` — `rating` field removed from `BrewInput`. Remove all four.
- `test_brew_input_tds_zero` — `tds` removed from `BrewInput`. Remove.
- `test_brew_input_ey_valid`, `test_brew_input_ey_zero_rejected`, `test_brew_input_ey_negative_rejected`, `test_brew_input_ey_omitted` — `ey` removed from `BrewInput`. Remove.
- `test_brew_input_grind_maxlength_accepted`, `test_brew_input_grind_maxlength_exceeded` — `grind` is now enum-validated, not length-validated. Remove.

**Tests to update:**

- `test_brew_input_invalid_date_format` → replace with `test_brew_input_invalid_date_format` that uses a genuinely invalid string (neither datetime nor date-only pattern):

```python
def test_brew_input_invalid_date_format():
    """date: string matching neither accepted format is rejected."""
    with pytest.raises(ValidationError, match="date"):
        BrewInput(
            date="not-a-date",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )
```

**New model tests to add:**

```python
# --- date dual-format ---

def test_brew_input_date_only_accepted():
    """date: YYYY-MM-DD (date-only) is accepted in v0.4."""
    brew = BrewInput(
        date="2026-02-21",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.date == "2026-02-21"


def test_brew_input_date_full_datetime_accepted():
    """date: YYYY-MM-DDTHH:MM:SSZ (full datetime) is still accepted."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.date == "2026-02-21T08:30:00Z"


# --- grind enum ---

@pytest.mark.parametrize("grind_value", [
    "turkish", "espresso", "fine", "medium_fine", "medium", "medium_coarse", "coarse"
])
def test_brew_input_grind_enum_all_values_accepted(grind_value):
    """Each of the 7 grind enum values is accepted."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        grind=grind_value,
    )
    assert brew.grind == grind_value


def test_brew_input_grind_freeform_rejected():
    """grind: freeform string not in the enum is rejected."""
    with pytest.raises(ValidationError):
        BrewInput(
            date="2026-02-21T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
            grind="setting 15",
        )


def test_brew_input_grind_omitted_accepted():
    """grind omitted is valid (optional field)."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.grind is None


# --- result object ---

def test_brew_input_with_result_tds_ey():
    """BrewInput with result containing tds and ey is valid."""
    from brewlog.models import ResultInput
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        result=ResultInput(tds=1.38, ey=20.1),
    )
    assert brew.result is not None
    assert brew.result.tds == 1.38
    assert brew.result.ey == 20.1


def test_brew_input_result_omitted():
    """BrewInput with result omitted is valid."""
    brew = BrewInput(
        date="2026-02-21T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )
    assert brew.result is None


def test_brew_input_with_full_result():
    """BrewInput with fully populated result is valid."""
    from brewlog.models import ResultInput, RatingsInput
    brew = BrewInput(
        date="2026-02-21",
        type="pour_over",
        dose_g=20.0,
        water_weight_g=320.0,
        result=ResultInput(
            tds=1.38,
            ey=20.1,
            brix=1.5,
            tasting_notes="Bright citrus, caramel finish",
            ratings=RatingsInput(overall=4, acidity=5, mouthfeel=3),
        ),
    )
    assert brew.result.brix == 1.5
    assert brew.result.tasting_notes == "Bright citrus, caramel finish"
    assert brew.result.ratings.overall == 4


# --- RatingsInput ---

def test_ratings_input_partial():
    """RatingsInput with only some dimensions is valid."""
    from brewlog.models import RatingsInput
    ratings = RatingsInput(overall=4, acidity=3)
    assert ratings.overall == 4
    assert ratings.acidity == 3
    assert ratings.fragrance is None


def test_ratings_input_all_dimensions():
    """RatingsInput with all 8 dimensions is valid."""
    from brewlog.models import RatingsInput
    ratings = RatingsInput(
        overall=4, fragrance=3, aroma=4, flavour=5,
        aftertaste=4, acidity=5, sweetness=3, mouthfeel=4
    )
    assert ratings.mouthfeel == 4


def test_ratings_input_boundary_minimum():
    """Each dimension: 1 is accepted (minimum boundary)."""
    from brewlog.models import RatingsInput
    ratings = RatingsInput(overall=1)
    assert ratings.overall == 1


def test_ratings_input_boundary_maximum():
    """Each dimension: 5 is accepted (maximum boundary)."""
    from brewlog.models import RatingsInput
    ratings = RatingsInput(overall=5)
    assert ratings.overall == 5


def test_ratings_input_below_minimum_rejected():
    """rating dimension: 0 is rejected (minimum: 1)."""
    from brewlog.models import RatingsInput
    with pytest.raises(ValidationError):
        RatingsInput(overall=0)


def test_ratings_input_above_maximum_rejected():
    """rating dimension: 6 is rejected (maximum: 5)."""
    from brewlog.models import RatingsInput
    with pytest.raises(ValidationError):
        RatingsInput(overall=6)


# --- ResultInput ---

def test_result_input_brix_zero_accepted():
    """ResultInput.brix: 0 is accepted (minimum: 0, not exclusive)."""
    from brewlog.models import ResultInput
    result = ResultInput(brix=0)
    assert result.brix == 0


def test_result_input_brix_negative_rejected():
    """ResultInput.brix: -1 is rejected."""
    from brewlog.models import ResultInput
    with pytest.raises(ValidationError):
        ResultInput(brix=-1)


def test_result_input_tds_zero_rejected():
    """ResultInput.tds: 0 is rejected (exclusiveMinimum: 0)."""
    from brewlog.models import ResultInput
    with pytest.raises(ValidationError):
        ResultInput(tds=0)


def test_result_input_ey_negative_rejected():
    """ResultInput.ey: -1 is rejected."""
    from brewlog.models import ResultInput
    with pytest.raises(ValidationError):
        ResultInput(ey=-1)


def test_result_input_tasting_notes_empty_rejected():
    """ResultInput.tasting_notes: empty string is rejected."""
    from brewlog.models import ResultInput
    with pytest.raises(ValidationError):
        ResultInput(tasting_notes="")


def test_result_input_tasting_notes_maxlength_accepted():
    """ResultInput.tasting_notes: 2000 chars is accepted."""
    from brewlog.models import ResultInput
    result = ResultInput(tasting_notes="x" * 2000)
    assert len(result.tasting_notes) == 2000


def test_result_input_tasting_notes_maxlength_exceeded():
    """ResultInput.tasting_notes: 2001 chars is rejected."""
    from brewlog.models import ResultInput
    with pytest.raises(ValidationError):
        ResultInput(tasting_notes="x" * 2001)
```

### 7.5 Test Coverage Map (AC → Tests)

| AC | Test function(s) | What is verified |
|----|-----------------|-----------------|
| AC-1 (version const "0.4") | `test_version_must_be_0_4` | `"0.4"` required; other values rejected |
| AC-2 (date dual-format both accepted) | `test_date_only_format_accepted`, `test_date_full_datetime_accepted` | Both formats pass |
| AC-3 (date-only passes) | `test_date_only_format_accepted` | `"2026-02-21"` passes |
| AC-4 (datetime passes) | `test_date_full_datetime_accepted` | `"2026-02-21T09:00:00Z"` passes |
| AC-5 (datetime without Z fails) | `test_date_no_z_rejected`, `test_invalid_examples_fail[invalid_date_no_z.yaml]` | Pattern enforced |
| AC-6 (wrong order fails) | `test_date_wrong_order_rejected` | `"21-02-2026"` rejected |
| AC-7 (month 13 passes schema) | `test_date_month_13_passes_schema` | Calendar validation is application-layer |
| AC-8 (oneOf pattern) | `test_date_only_format_accepted`, `test_date_full_datetime_accepted`, `test_date_no_z_rejected` | Pattern enforcement |
| AC-9 (version rejects "0.3") | `test_version_const_rejects_v0_3` | `"0.3"` rejected by v0.4 schema |
| AC-10 (grind enum accepted) | `test_grind_enum_all_values_accepted[turkish]` ... `[coarse]` (7 parametrized) | All 7 values pass |
| AC-11 (grind specific values) | `test_grind_enum_all_values_accepted[medium]`, `[turkish]`, `[espresso]` | Subset coverage |
| AC-12 (freeform grind fails) | `test_grind_freeform_rejected`, `test_invalid_examples_fail[invalid_grind_freeform.yaml]` | Enum enforced |
| AC-13 (wrong case fails) | `test_grind_wrong_case_rejected` | Case-sensitive enum |
| AC-14 (grind omitted passes) | `test_grind_omitted_accepted` | Optional field |
| AC-15 (result optional) | `test_result_omitted_accepted` | No result passes |
| AC-16 (result accepted fields) | `test_result_tds_ey_accepted`, `test_result_brix_valid_accepted`, `test_ratings_partial_accepted`, `test_result_tasting_notes_accepted` | All five fields accepted |
| AC-17 (result omitted passes) | `test_result_omitted_accepted` | No result passes |
| AC-18 (result empty passes) | `test_result_empty_object_accepted` | `result: {}` passes |
| AC-19 (result unknown field fails) | `test_result_unknown_field_rejected` | `additionalProperties: false` enforced |
| AC-20 (tds/ey in result, rejected at brew level) | `test_result_tds_ey_accepted`, `test_tds_at_brew_level_rejected`, `test_ey_at_brew_level_rejected`, `test_invalid_examples_fail[invalid_tds_at_brew_level.yaml]` | Both directions tested |
| AC-21 (brix constraints) | `test_result_brix_valid_accepted`, `test_result_brix_zero_accepted`, `test_result_brix_negative_rejected` | 0 accepted, -1 rejected |
| AC-22 (ratings optional object) | `test_ratings_partial_accepted` | Optional, partial is valid |
| AC-23 (ratings dimensions) | `test_ratings_partial_accepted`, `test_ratings_overall_maximum_accepted`, `test_ratings_overall_minimum_accepted` | Dimension range |
| AC-24 (partial ratings pass) | `test_ratings_partial_accepted` | Not all dims required |
| AC-25 (ratings boundary failures) | `test_ratings_below_minimum_rejected`, `test_ratings_above_maximum_rejected`, `test_ratings_float_rejected` | 0, 6, 3.5 all fail |
| AC-26 (tasting_notes) | `test_result_tasting_notes_accepted`, `test_result_tasting_notes_maxlength_accepted`, `test_result_tasting_notes_maxlength_exceeded`, `test_result_tasting_notes_empty_rejected` | Full constraint coverage |
| AC-27 (rating at brew level fails) | `test_rating_at_brew_level_rejected` | `additionalProperties: false` enforced |
| AC-28 (notes field doc) | Spec document review only | Documentation content |
| AC-29–AC-38 (examples) | `test_valid_examples_pass`, `test_invalid_examples_fail` (parametrized) | Example files load and validate correctly |
| AC-39–AC-42 (spec document sections) | Spec document review only | Human-readable spec content |
| AC-43 (test suite) | All test functions in Section 7.3 and 7.4 | Full v0.4 constraint coverage |

---

## 8. File Layout: Files to Create or Modify

The dev should verify exact paths by reading the path constants in `tests/test_brewspec_schema.py` and the public repo structure before modifying files.

### 8.1 Files to Modify

| File | What Changes | AC(s) |
|------|-------------|-------|
| `brewspec.schema.json` (public repo root) | Full v0.4 schema (Section 2 verbatim) | AC-1 through AC-27 |
| `src/brewlog/brewspec.schema.json` (CLI package) | Same full v0.4 schema — must stay in sync with public repo | AC-1 through AC-27 |
| `src/brewlog/models.py` | Update constants; add `RatingsInput`, `ResultInput`; update `BrewInput` (remove `tds`, `ey`, `rating`; add `result`; update `grind`, `date` validators) | v0.4 model parity |
| `tests/test_brewspec_schema.py` (public repo) | Update `VALID_DOC` version; rename version test; add all new schema test functions from Section 7.3 | AC-43 |
| `brewlog/tests/test_models.py` | Remove obsolete tests; update affected tests; add all new model tests from Section 7.4 | AC-43 |
| `examples/valid/pour_over.yaml` | Version bump; migrate tds/ey to result; update grind; add tasting_notes, ratings | AC-29, AC-31, AC-32, AC-33, AC-35 |
| `examples/valid/pour_over.json` | Same changes in JSON format | AC-29, AC-31 |
| `examples/valid/espresso.yaml` | Version bump; migrate ey to result; update grind to "espresso"; add brix | AC-29, AC-32, AC-34, AC-35 |
| `examples/valid/multi_brew.yaml` | Version bump; migrate tds/ey; use date-only on at least one brew | AC-29, AC-30 |
| `examples/valid/immersion_minimal.yaml` | Version bump only | AC-29 |
| `examples/valid/hybrid.yaml` | Version bump only | AC-29 |
| `brewspec-v0.3.md` (public repo) | Archive existing spec doc to `versions/brewspec-v0.3.md` (deployment-manager task) | — |

### 8.2 Files to Create

| File | What It Is | AC(s) |
|------|-----------|-------|
| `examples/valid/pour_over_date_only.yaml` | Valid example: date-only format, full result object | AC-30, AC-32, AC-33, AC-34, AC-35 |
| `examples/invalid/invalid_date_no_z.yaml` | Invalid example: datetime without Z suffix | AC-36 |
| `examples/invalid/invalid_grind_freeform.yaml` | Invalid example: freeform grind value | AC-37 |
| `examples/invalid/invalid_tds_at_brew_level.yaml` | Invalid example: tds at flat brew level | AC-38 |
| `brewspec-v0.4.md` (public repo) | New canonical spec document | AC-39, AC-40, AC-41, AC-42 |

### 8.3 TDD Order

1. Update `tests/test_brewspec_schema.py`: update `VALID_DOC` to `"0.4"`; rename version test; add all new schema test functions from Section 7.3. Run — most will fail.

2. Update `brewspec.schema.json` and `src/brewlog/brewspec.schema.json` with the full v0.4 schema from Section 2. Run — schema-level tests should pass; example-file tests will fail until examples are updated.

3. Update existing valid example files per Section 6.2.

4. Create new valid example `pour_over_date_only.yaml` per Section 6.3.

5. Create new invalid example files per Section 6.4.

6. Run tests — all schema and example tests should pass.

7. Update `brewlog/tests/test_models.py`: remove obsolete tests; update affected tests; add new model tests from Section 7.4. Run — model tests will fail.

8. Update `src/brewlog/models.py` with all changes from Section 4. Run — model tests should pass.

9. Run `ruff check .` — code must be lint-clean before handoff.

10. Produce `brewspec-v0.4.md` in the public repo with all sections from Section 5.

---

## 9. Edge Cases and Developer Notes

### 9.1 `oneOf` and `type: string` on `date`

The `type: string` keyword is on the parent property, not inside the `oneOf` sub-schemas. This is the correct placement for Draft 2020-12: the `type` keyword in the parent schema is evaluated independently of `oneOf`. The `oneOf` sub-schemas each contain only a `pattern` keyword. A non-string value will fail on `type: string` and never reach `oneOf` evaluation.

A string that matches both patterns (e.g., if someone constructs a 10-character string matching both regexes — this is impossible given the patterns are structurally different lengths) would fail `oneOf`. But in practice, no well-formed string can match both `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` (20 characters) and `^\d{4}-\d{2}-\d{2}$` (10 characters) simultaneously, so `oneOf` behaves correctly.

### 9.2 `grind` Empty String

With the freeform string definition removed and replaced by an enum, an empty string `""` is automatically rejected (it is not a valid enum member). No `minLength` constraint is needed for enum fields — the enum list itself is exhaustive.

### 9.3 `result` Empty Object

`result: {}` is valid per AC-18. All fields inside `result` are optional. An empty `result` object is semantically equivalent to omitting the `result` key. Tools should treat both cases identically when reading brew records.

### 9.4 `ratings` Integer Enforcement

The `type: integer` constraint in JSON Schema Draft 2020-12 rejects float values. `3.5` fails `type: integer` even though it could satisfy `minimum: 1` and `maximum: 5` if treated as a number. This is correct behaviour per AC-25.

Note: JSON Schema `type: integer` means the value must be a JSON number with no fractional part. A value encoded in JSON as `4.0` is technically a valid integer in Draft 2020-12 (the fractional part is zero). The test for float rejection should use `3.5` (non-zero fractional part), not `4.0`.

### 9.5 `brix` vs. `tds` Minimum Semantics

Both `brix` and `tds` represent refractometer measurements, but they have different physical minimum semantics:
- `tds: 0` is meaningless (no dissolved solids = no extraction = not a brew). Use `exclusiveMinimum: 0`.
- `brix: 0` is a valid calibration baseline (distilled water reads 0 °Brix). Use `minimum: 0`.

The dev must not accidentally copy `exclusiveMinimum: 0` from `tds` onto `brix`.

### 9.6 Existing `test_brew_input_invalid_date_format` Update

The existing model test `test_brew_input_invalid_date_format` passes `date="2026-02-19"` (date-only) and expects it to be rejected. This test must be updated — date-only format is now valid in v0.4. The test should be renamed or its assertion changed to use a genuinely invalid string as described in Section 7.4.

### 9.7 `validate_exclusive_positive` Scope Reduction on `BrewInput`

The v0.3 `validate_exclusive_positive` validator covers `water_volume_ml`, `tds`, and `ey`. After removing `tds` and `ey` from `BrewInput`, this validator must be updated to cover only `water_volume_ml`. If the dev leaves `tds` and `ey` in the validator signature, Pydantic will not error (the fields are simply absent), but it is dead code that should be cleaned up per the `ruff check .` requirement.

---

## 10. Migration Path (v0.3 → v0.4)

This section documents how a v0.3 brew file is migrated to v0.4. It is also included in the spec document "Backward Compatibility" section.

### 10.1 Step-by-Step Migration

Given a v0.3 brew file, apply these steps in order:

**Step 1: Update the version const.**

```yaml
# Before
brewspec_version: "0.3"

# After
brewspec_version: "0.4"
```

**Step 2: Move `tds` from the brew level to `result.tds` (if present).**

```yaml
# Before (v0.3)
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    tds: 1.38

# After (v0.4)
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
    result:
      tds: 1.38
```

**Step 3: Move `ey` from the brew level to `result.ey` (if present).**

If both `tds` and `ey` are present, they merge into the same `result` object:

```yaml
# Before (v0.3)
    tds: 1.38
    ey: 20.1

# After (v0.4)
    result:
      tds: 1.38
      ey: 20.1
```

**Step 4: Move `rating` to `result.ratings.overall` (if present).**

The 1–5 scale is unchanged. A v0.3 `rating: 4` becomes `result.ratings.overall: 4`:

```yaml
# Before (v0.3)
    rating: 4

# After (v0.4)
    result:
      ratings:
        overall: 4
```

If `tds`, `ey`, and `rating` are all present, they all merge into the same `result` object:

```yaml
# After (v0.4) — all three fields merged
    result:
      tds: 1.38
      ey: 20.1
      ratings:
        overall: 4
```

**Step 5: Update `grind` value (if present).**

Replace freeform values with the nearest enum member. Use the following mapping as a guide:

| v0.3 freeform value | Nearest v0.4 enum value |
|---------------------|-------------------------|
| `"turkish"` / `"powder"` / `"super fine"` | `"turkish"` |
| `"espresso"` / `"extra fine"` / `"very fine"` | `"espresso"` |
| `"fine"` | `"fine"` |
| `"medium fine"` / `"medium-fine"` | `"medium_fine"` |
| `"medium"` / `"med"` | `"medium"` |
| `"medium coarse"` / `"medium-coarse"` | `"medium_coarse"` |
| `"coarse"` | `"coarse"` |
| `"setting 15"` / any setting number | Omit `grind` or infer from context |

If no enum value is a reasonable match (e.g., the value is a grinder-specific click number with no clear coarseness label), remove the `grind` field and optionally record the value in `notes`.

**Step 6: Validate against the v0.4 schema.**

Run the v0.4 JSON Schema validator. All errors must be resolved before the file is considered migrated.

### 10.2 Files Needing No Migration Steps

v0.3 files that do not use `tds`, `ey`, `rating`, or a freeform `grind` value only require the version const update in Step 1. All new v0.4 fields (`brix`, `tasting_notes`, `ratings`, `result`) are optional.

### 10.3 Tool Migration Guidance

Tools that store brew data in a database and export to BrewSpec format need to update their export logic:

- Remove `tds`, `ey`, `rating` from the flat export
- Add a `result` object when any of `tds`, `ey`, `brix`, `tasting_notes`, or `ratings` data is present
- Emit `grind` only if the stored value maps to a valid enum member; otherwise omit or emit in `notes`
- Update the `brewspec_version` const in the export output

The BrewLog CLI must update its DB schema and export/import logic as part of the BrewLog CLI v0.3 task, which depends on this BrewSpec v0.4 schema.

---

## 11. Security Considerations

### 11.1 Input Validation Rules

All new v0.4 fields follow the same validation pipeline as existing fields: schema validation via `Draft202012Validator.validate()` is the first gate; no data reaches application logic without passing the schema.

| Field | Risk | Schema Mitigation | Application-Layer Note |
|-------|------|------------------|------------------------|
| `result.tasting_notes` | Pathologically long string; injection if rendered in HTML or interpolated into queries | `minLength: 1, maxLength: 2000` | Must be stored and displayed as plain text only. Never interpolated into shell, SQL template strings, or HTML without escaping. Same principle as the existing `notes` field. |
| `result.brix` | Non-numeric or negative value | `type: number, minimum: 0` | Schema rejects strings and negative values. No PII risk. |
| `result.tds`, `result.ey` | Same constraints as v0.3 flat fields — non-positive values | `exclusiveMinimum: 0` | Unchanged from v0.3. |
| `result.ratings.*` | Out-of-range integer or float | `type: integer, minimum: 1, maximum: 5` | Schema rejects floats (type: integer) and values outside [1, 5]. |
| `grind` (enum) | The closed enum prevents injection of arbitrary strings at this field | Enum list enforces membership | No application-layer concern beyond enum enforcement. |
| `date` (dual-format) | The `oneOf` pattern approach ensures only two specific formats are accepted | `oneOf` with two anchored patterns | Neither pattern allows executable or injected content. |

### 11.2 Trust Boundary

The trust boundary is unchanged from v0.3:

```
User-supplied file (YAML or JSON)
  → Path validation (reject ../traversal, check extension)
  → File size check (reject > limit; recommended: 10 MB)
  → Safe parser: yaml.safe_load() or json.load()
  → Schema validation: Draft202012Validator.validate()
  → Application logic (read fields, store, display)
```

`yaml.safe_load()` must continue to be used for all YAML parsing. This is unchanged.

### 11.3 `additionalProperties: false` as a Security Control

The `additionalProperties: false` constraint is applied to all objects in the v0.4 schema: the root document, `$defs.brew`, `$defs.coffee`, `$defs.water`, `$defs.equipment`, `$defs.result`, and `$defs.ratings`. This prevents unexpected fields from entering the object graph regardless of where they are injected. The `result` and `ratings` objects are new in v0.4 and both carry this constraint.

### 11.4 Breaking Change and Data Integrity

The removal of `tds`, `ey`, and `rating` from `$defs.brew` is enforced by `additionalProperties: false` on the brew object. A v0.3 file that still has these fields at the brew level will fail schema validation cleanly (not silently drop the data). This is the correct data integrity behaviour: the file is rejected rather than processed with data silently discarded.

### 11.5 No Sensitive Data

`result.tasting_notes` contains personal sensory impressions. Low sensitivity — same category as the existing `notes` field. No PII, API keys, credentials, or authentication tokens are introduced by v0.4. Rating integers have no privacy implication. Date-only values (`YYYY-MM-DD`) carry slightly less temporal precision than full datetimes, which is a privacy improvement for users who prefer not to record an exact time.

---

## 12. Acceptance Criteria Verification

| AC | Addressed in | Design location |
|----|-------------|-----------------|
| AC-1 (version const "0.4", title updated) | Sections 1.1, 2 | Schema diff, full schema |
| AC-2 (date dual-format both accepted) | Sections 1.2, 3.1, 2 | Schema diff, design decision, full schema |
| AC-3 (date-only passes) | Sections 1.2, 7.3 | Schema diff, test functions |
| AC-4 (full datetime passes) | Sections 1.2, 7.3 | Schema diff, test functions |
| AC-5 (datetime without Z fails) | Sections 1.2, 6.4, 7.3 | Schema diff, invalid example, tests |
| AC-6 (wrong order fails) | Sections 1.2, 7.3 | Schema diff, tests |
| AC-7 (month 13 passes schema) | Sections 3.1, 7.3 | Design decision, tests |
| AC-8 (oneOf expression) | Sections 1.2, 2, 3.1 | Schema diff, full schema, design decision |
| AC-9 (version "0.3" rejected) | Sections 1.1, 7.3 | Schema diff, tests |
| AC-10 (grind enum accepted) | Sections 1.2, 2, 7.3 | Schema diff, full schema, tests |
| AC-11 (grind specific values) | Sections 1.2, 7.3 | Schema diff, parametrized tests |
| AC-12 (freeform grind fails) | Sections 1.2, 6.4, 7.3 | Schema diff, invalid example, tests |
| AC-13 (wrong case fails) | Sections 1.2, 7.3 | Schema diff, tests |
| AC-14 (grind omitted passes) | Sections 1.2, 7.3 | Schema diff, tests |
| AC-15 (result optional) | Sections 1.2, 1.3, 2, 7.3 | Schema diff, result def, full schema, tests |
| AC-16 (result accepted fields) | Sections 1.3, 2, 7.3 | Result def, full schema, tests |
| AC-17 (result omitted passes) | Sections 1.3, 7.3 | Result def, tests |
| AC-18 (result empty passes) | Sections 3.3, 7.3 | Design decision, tests |
| AC-19 (result unknown field fails) | Sections 1.3, 7.3 | `additionalProperties: false`, tests |
| AC-20 (tds/ey in result, brew level rejected) | Sections 1.2, 1.3, 2, 7.3 | Schema diff, result def, tests |
| AC-21 (brix constraints) | Sections 1.3, 2, 3.3, 7.3 | Result def, full schema, design decision, tests |
| AC-22 (ratings optional) | Sections 1.4, 2, 7.3 | Ratings def, full schema, tests |
| AC-23 (ratings 8 dimensions) | Sections 1.4, 2 | Ratings def, full schema |
| AC-24 (partial ratings pass) | Sections 1.4, 7.3 | Ratings def, tests |
| AC-25 (ratings boundary failures) | Sections 1.4, 7.3 | Ratings def, tests |
| AC-26 (tasting_notes) | Sections 1.3, 2, 7.3 | Result def, full schema, tests |
| AC-27 (brew-level rating rejected) | Sections 1.2, 3.4, 7.3 | Schema diff (field removed), design decision, tests |
| AC-28 (notes doc clarification) | Sections 1.2, 5.2, 5.3 | Schema diff (description updated), spec document |
| AC-29 (examples updated) | Section 6.2 | Example file plan |
| AC-30 (date-only example) | Sections 6.2, 6.3 | `multi_brew.yaml`, `pour_over_date_only.yaml` |
| AC-31 (datetime example) | Section 6.2 | `pour_over.yaml` |
| AC-32 (result with tds/ey/ratings) | Sections 6.2, 6.3 | `pour_over.yaml`, `pour_over_date_only.yaml` |
| AC-33 (tasting_notes example) | Sections 6.2, 6.3 | `pour_over.yaml`, `pour_over_date_only.yaml` |
| AC-34 (brix example) | Sections 6.2, 6.3 | `espresso.yaml`, `pour_over_date_only.yaml` |
| AC-35 (grind enum example) | Sections 6.2, 6.3 | Updated examples using enum values |
| AC-36 (`invalid_date_no_z.yaml`) | Section 6.4 | Invalid example file |
| AC-37 (`invalid_grind_freeform.yaml`) | Section 6.4 | Invalid example file |
| AC-38 (`invalid_tds_at_brew_level.yaml`) | Section 6.4 | Invalid example file |
| AC-39 (`brewspec-v0.4.md` exists) | Section 5 | Spec document plan |
| AC-40 ("What Changed in v0.4" section) | Section 5.3 | Spec document content |
| AC-41 ("Validation" section) | Section 5.4 | Spec document content |
| AC-42 ("Backward Compatibility" section) | Sections 5.5, 10 | Spec document content, migration path |
| AC-43 (test suite) | Sections 7.3, 7.4 | Schema and model test functions |
