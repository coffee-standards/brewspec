# BrewSpec v0.5

Status: Stable
Version: 0.5
Last Updated: 2026-03-01

---

## Overview

BrewSpec is an open source standard for describing coffee brews. BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

BrewSpec repository: https://github.com/coffee-standards/brewspec

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.5 defines:
- A JSON Schema for validation
- Required and optional fields for describing a brew
- Structured coffee origin metadata (`origins` object array with eight optional fields per entry)
- Water mineral content (`ppm`)
- A `result` object grouping brew outcome measurements and sensory evaluation (`tds`, `ey`, `brix`, `tasting_notes`, `ratings`)
- A `ratings` object with 8 SCA-aligned sensory dimensions (integer 1–5 each)
- Equipment descriptor (`grinder`, `brewer`, `grinder_setting`, `notes`)
- `brew_ratio` as an optional float at the brew level
- `maxLength` constraints on all freeform string fields
- A strict 7-value enumeration for `grind`
- Dual-format `date`: full UTC datetime or date-only
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.5 still defers to future versions:
- Standardized enumeration for `method` (deferred pending further usage data)
- Pour schedules and step-by-step timing
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
- Extended equipment fields (kettle, scale)

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.5"` | The BrewSpec version |
| `brews` | array | Required | Minimum 1 element | Array of brew objects |

### Brew Object

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

### Coffee Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roast_date` | string | Optional | `YYYY-MM-DD` | Roast date. Plain date; no time component. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Whether the coffee is a single origin or a blend. | `"single_origin"` |
| `origins` | array | Optional | minItems 1; each item is an Origin Object | Structured origin records. Replaces v0.4 `origin` string array. Omit entirely to record no origin data (present but empty is invalid). | |
| `varietal` | string | Optional | minLength 1, maxLength 100 | Coffee variety or cultivar. Freeform. | `"Heirloom"`, `"Gesha"` |
| `process` | string | Optional | minLength 1, maxLength 100 | Green coffee processing method at the coffee level. For per-origin process in blends, use `origins[].process`. Both fields coexist in v0.5 with no defined precedence. | `"Washed"`, `"Natural"` |

### Origin Object (all fields optional; `additionalProperties: false`)

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

### Water Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

### Equipment Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | minLength 1, maxLength 100 | Grinder model. Freeform. | `"Comandante C40 MK4"` |
| `brewer` | string | Optional | minLength 1, maxLength 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"` |
| `grinder_setting` | string | Optional | minLength 1, maxLength 100 | Grinder dial position or click setting for this brew. Freeform. | `"21 clicks"`, `"3.2.1"` |
| `notes` | string | Optional | minLength 1, maxLength 2000 | Equipment state observations — burr age, maintenance, filter type, calibration state. | `"Burrs replaced 2026-01"` |

### Result Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield as a percentage | `20.5`, `21.3` |
| `brix` | number | Optional | >= 0 | Dissolved sugar content in degrees Brix. 0 is valid. | `4.2`, `0` |
| `tasting_notes` | string | Optional | minLength 1, maxLength 2000 | Sensory description of the brew. For brew-process notes, use the top-level `notes` field. | `"Bright citrus acidity, caramel sweetness"` |
| `ratings` | object | Optional | See Ratings Object | Multi-dimensional sensory ratings | |

### Ratings Object (entire object optional; all fields within optional; integers 1–5)

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `overall` | integer | Optional | 1–5 inclusive | Holistic impression. 1 = poor, 5 = excellent. |
| `fragrance` | integer | Optional | 1–5 inclusive | Dry grounds aroma before water is added. |
| `aroma` | integer | Optional | 1–5 inclusive | Wet aroma after water is added. |
| `flavour` | integer | Optional | 1–5 inclusive | Taste and aroma experienced during drinking. |
| `aftertaste` | integer | Optional | 1–5 inclusive | Length and quality of positive flavour attributes after swallowing. |
| `acidity` | integer | Optional | 1–5 inclusive | Quality (not quantity) of acidity; brightness. |
| `sweetness` | integer | Optional | 1–5 inclusive | Perceived sweetness. |
| `mouthfeel` | integer | Optional | 1–5 inclusive | Tactile sensation; body and texture. |

---

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

---

## Validation

### Validate at Storage Time

Tools implementing BrewSpec should validate a brew document at storage time — before writing to any database or file — not only at display or read time. Validating only at read time allows invalid data to enter the store, where it may cause failures much later and in contexts far removed from the original data entry. Validate early; reject invalid data at the point of entry.

The expected validation pipeline is:

1. **Safe parse** — Parse the YAML or JSON input using a safe parser (e.g., `yaml.safe_load` in Python, not `yaml.load`). Reject malformed input before any processing.
2. **Schema validation** — Validate the parsed data against the BrewSpec JSON Schema using a compliant validator (e.g., `jsonschema.Draft202012Validator` in Python, `ajv` in JavaScript). Reject documents that fail validation with a clear error message.
3. **Application logic** — Only after both steps succeed should the application store or process the data.

Never pass unvalidated input directly to a database query or downstream system.

When brew_ratio, dose_g, and water_weight_g are all present, tools should
check that brew_ratio ≈ water_weight_g / dose_g and surface any significant
mismatch as a warning. A mismatch is not a schema error — both values are
stored as supplied.

### Using Python

```python
import json
import yaml
from jsonschema import Draft202012Validator

# Load schema
schema = json.load(open("brewspec.schema.json", encoding="utf-8"))
validator = Draft202012Validator(schema)

# Step 1: Safe parse
data = yaml.safe_load(open("my_brew.yaml", encoding="utf-8"))

# Step 2: Schema validation (raises ValidationError if invalid)
validator.validate(data)

# Step 3: Application logic — data is valid, proceed
```

---

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

### Archived specs

- [`versions/brewspec-v0.4.md`](./versions/brewspec-v0.4.md) — v0.4 archived spec
- [`versions/brewspec-v0.3.md`](./versions/brewspec-v0.3.md) — v0.3 archived spec
- [`versions/brewspec-v0.2.md`](./versions/brewspec-v0.2.md) — v0.2 archived spec
- [`versions/brewspec-v0.1.md`](./versions/brewspec-v0.1.md) — v0.1 archived spec
