# BrewSpec v0.8

Status: Stable
Version: 0.8
Last Updated: 2026-03-19

---

## Overview

BrewSpec is an open source standard for describing coffee brews. BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

BrewSpec repository: https://github.com/coffee-standards/brewspec

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.8 defines:
- A JSON Schema for validation
- All brew-level fields are optional — tools may record only the fields they capture
- A `coffee.roaster` field for the company or person who roasted the coffee — new in v0.8
- A `coffee.roast_level` field with a three-value enum (`light`, `medium`, `dark`) — new in v0.8
- An `origin.elevation_masl` field for growing elevation in meters above sea level — new in v0.8
- A `water_temp_c` precision constraint (`multipleOf: 0.1`) — changed in v0.8
- A `result.yield_g` field for output weight (espresso and other yield-tracked brews)
- Structured coffee origin metadata (`origins` object array with ten optional fields per entry)
- An optional `coffee.name` field for branded product names or descriptive labels
- Water mineral content (`ppm`)
- A `result` object grouping brew outcome measurements and sensory evaluation (`tds`, `ey`, `brix`, `yield_g`, `tasting_notes`, `ratings`)
- A `ratings` object with 8 SCA-aligned sensory dimensions (integer 1-5 each)
- Equipment descriptor (`grinder`, `brewer`, `grinder_setting`, `notes`)
- `brew_ratio` as an optional float at the brew level
- `maxLength` constraints on all freeform string fields
- A strict 7-value enumeration for `grind`
- Dual-format `date`: full UTC datetime or date-only
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.8 still defers to future versions:
- Standardized enumeration for `method` (deferred pending further usage data)
- Pour schedules and step-by-step timing
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
- Extended equipment fields (kettle, scale)
- Expanded `roast_level` enum (e.g., medium-light, medium-dark) — deferred pending usage data

---

## Field Reference

Complete reference for all fields in v0.8. Every field in the JSON Schema appears here.

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Yes | const: `"0.8"` | Must be the literal string `"0.8"`. Rejected if missing or any other value. |
| `brews` | array | Yes | minItems: 1 | Array of brew objects. At least one brew required. |

### Brew Object Fields

All fields in the brew object are optional. Tools may record only the fields they capture.

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | No | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Brew date or datetime (UTC). | `"2026-02-21"`, `"2026-02-15T08:30:00Z"` |
| `type` | string | No | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category. | `"pour_over"` |
| `dose_g` | number | No | > 0 (exclusive) | Coffee dose in grams. | `20`, `18` |
| `water_weight_g` | number | No | > 0 (exclusive) | Water weight in grams. | `320`, `36` |
| `brew_ratio` | number | No | > 0 (exclusive) | Water-to-coffee ratio as a float (grams water per gram coffee). e.g. `15.5` represents 15.5:1. Tools should prefer this stored value when present. Consistency with `dose_g`/`water_weight_g` is not schema-enforced; tools should surface mismatches as a warning. | `15.5`, `15.56` |
| `method` | string | No | minLength 1, maxLength 100 | Freeform brewer description. | `"Hario V60"`, `"AeroPress inverted"` |
| `water_temp_c` | number | No | 0-100 inclusive, multipleOf 0.1 | Water temperature in celsius. Constrained to 0.1-degree precision. Changed in v0.8. | `96.0`, `93.5` |
| `coffee` | object | No | See Coffee Object | Coffee ingredient descriptor. | |
| `water` | object | No | See Water Object | Water ingredient descriptor. | |
| `equipment` | object | No | See Equipment Object | Equipment descriptor. | |
| `grind` | string | No | Enum: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse` | Grind size (finest to coarsest). | `"medium_fine"` |
| `duration_s` | number | No | > 0 (exclusive) | Brew duration in seconds. | `180`, `28` |
| `notes` | string | No | minLength 1, maxLength 2000 | Brew-process notes — operational observations about the preparation. For sensory description, use `result.tasting_notes`. | `"Washed filter paper"` |
| `result` | object | No | See Result Object | Brew outcome measurements and sensory evaluation. | |

### Coffee Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `name` | string | No | minLength 1, maxLength 150 | A branded product name or human-readable descriptive label for the coffee. | `"Ethiopia Yirgacheffe"`, `"Blue Bottle Hayes Valley Espresso"` |
| `roaster` | string | No | minLength 1, maxLength 100 | The company or person who roasted the coffee. Applies to the whole coffee, not individual origins. New in v0.8. | `"Onyx"`, `"Tim Wendelboe"` |
| `roast_level` | string | No | Enum: `light`, `medium`, `dark` | Roast level category. Three values covering the majority of retail bag labels. For finer detail, use the brew-level `notes` field. New in v0.8. | `"light"` |
| `roast_date` | string | No | `YYYY-MM-DD` | Roast date. Plain date; no time component. | `"2026-01-20"` |
| `type` | string | No | Enum: `single_origin`, `blend` | Whether the coffee is a single origin or a blend. | `"single_origin"` |
| `origins` | array | No | minItems 1; each item is an Origin Object | Structured origin records. Omit entirely to record no origin data (present but empty is invalid). | |

### Origin Object (all fields optional; `additionalProperties: false`)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `name` | string | No | minLength 1, maxLength 100 | Descriptive name for this origin component. | `"Ethiopia Yirgacheffe Natural"` |
| `country` | string | No | minLength 1, maxLength 100 | Country of production. | `"Ethiopia"`, `"Colombia"` |
| `region` | string | No | minLength 1, maxLength 100 | State, province, or named growing region. | `"Yirgacheffe"`, `"Huila"` |
| `subregion` | string | No | minLength 1, maxLength 100 | District, zone, or sub-area within the region. | `"Kochere"` |
| `producer` | string | No | minLength 1, maxLength 100 | Farm, cooperative, or washing station name. | `"Daye Bensa Washing Station"` |
| `process` | string | No | minLength 1, maxLength 100 | Green coffee processing method at origin. | `"Washed"`, `"Natural"`, `"Honey"` |
| `lot` | string | No | minLength 1, maxLength 100 | Lot or batch identifier from the producer. | `"Lot 42"`, `"Export Grade 1"` |
| `harvest_year` | integer | No | minimum 1900, maximum 2100 | Year the crop was harvested. | `2025` |
| `varietal` | string | No | minLength 1, maxLength 100 | Coffee varietal for this origin entry. Records the coffee variety or cultivar specific to this component. | `"Heirloom"`, `"Gesha"`, `"Bourbon"` |
| `elevation_masl` | integer | No | > 0 (exclusive) | Growing elevation in meters above sea level. Unit embedded in field name per schema convention. New in v0.8. | `1950`, `1200` |

### Water Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | No | >= 0 | Total dissolved solids in parts per million. | `150`, `75`, `0` |

### Equipment Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | No | minLength 1, maxLength 100 | Grinder model. Freeform. | `"Comandante C40 MK4"` |
| `brewer` | string | No | minLength 1, maxLength 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"` |
| `grinder_setting` | number | No | > 0 (exclusive) | Grinder dial position or click setting for this brew. Must be a positive number. Integer for primary increment grinders (e.g. `21` on a Comandante C40); decimal tenths for grinders with sub-steps (e.g. `5.2` on a Fellow Ode Gen 2 means primary position 5, second sub-step). | `21`, `5.2`, `30` |
| `notes` | string | No | minLength 1, maxLength 2000 | Equipment state observations — burr age, maintenance, filter type, calibration state. | `"Burrs replaced 2026-01"` |

### Result Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `tds` | number | No | > 0 (exclusive) | TDS percentage of finished brew. | `1.38`, `8.5` |
| `ey` | number | No | > 0 (exclusive) | Extraction yield as a percentage. | `20.5`, `21.3` |
| `brix` | number | No | >= 0 | Dissolved sugar content in degrees Brix. 0 is valid. | `4.2`, `0` |
| `yield_g` | number | No | > 0 (exclusive) | Output weight of the brew in grams. For espresso, this is the liquid weight in the cup; for filter coffee, it is the total output weight. **Espresso dual-role note:** `yield_g` can function as both a recipe target (the output weight you are aiming for on the process card) and a measured result (the weight you actually pulled). BrewSpec represents it solely as a result field -- it records what was measured. Consuming tools may choose to store a target yield separately as an application-level concern outside BrewSpec's scope. | `36.5`, `42.0` |
| `tasting_notes` | string | No | minLength 1, maxLength 2000 | Sensory description of the brew. For brew-process notes, use the top-level `notes` field. | `"Bright citrus acidity, caramel sweetness"` |
| `ratings` | object | No | See Ratings Object | Multi-dimensional sensory ratings. | |

### Ratings Object (entire object optional; all fields within optional; integers 1-5)

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `overall` | integer | No | 1-5 inclusive | Holistic impression. 1 = poor, 5 = excellent. |
| `fragrance` | integer | No | 1-5 inclusive | Dry grounds aroma before water is added. |
| `aroma` | integer | No | 1-5 inclusive | Wet aroma after water is added. |
| `flavour` | integer | No | 1-5 inclusive | Taste and aroma experienced during drinking. |
| `aftertaste` | integer | No | 1-5 inclusive | Length and quality of positive flavour attributes after swallowing. |
| `acidity` | integer | No | 1-5 inclusive | Quality (not quantity) of acidity; brightness. |
| `sweetness` | integer | No | 1-5 inclusive | Perceived sweetness. |
| `mouthfeel` | integer | No | 1-5 inclusive | Tactile sensation; body and texture. |

---

## What Changed in v0.8

### New Fields (additive, non-breaking)

- **`coffee.roaster`** (`string`, optional, `minLength: 1`, `maxLength: 100`) -- The company or person who roasted the coffee. Placed on the `coffee` object, not inside `origins[]`, because a roaster applies to the coffee as a whole.
- **`coffee.roast_level`** (`string`, optional, `enum: ["light", "medium", "dark"]`) -- Roast level category. Deliberately coarse three-value enum. Expandable in future versions if usage data demonstrates the need.
- **`coffee.origins[].elevation_masl`** (`integer`, optional, `exclusiveMinimum: 0`) -- Growing elevation in meters above sea level. Unit embedded in field name per schema convention.

### Breaking Changes

- **`water_temp_c` precision constraint** -- Added `multipleOf: 0.1`. A v0.7 document containing `water_temp_c: 96.15` (or any value with more than one decimal place) becomes invalid under v0.8. Migration: round to one decimal place.

---

## Validation

### Validate at Storage Time

Tools implementing BrewSpec should validate a brew document at storage time -- before writing to any database or file -- not only at display or read time. Validating only at read time allows invalid data to enter the store, where it may cause failures much later and in contexts far removed from the original data entry. Validate early; reject invalid data at the point of entry.

The expected validation pipeline is:

1. **Safe parse** -- Parse the YAML or JSON input using a safe parser (e.g., `yaml.safe_load` in Python, not `yaml.load`). Reject malformed input before any processing.
2. **Schema validation** -- Validate the parsed data against the BrewSpec JSON Schema using a compliant validator (e.g., `jsonschema.Draft202012Validator` in Python, `ajv` in JavaScript). Reject documents that fail validation with a clear error message.
3. **Application logic** -- Only after both steps succeed should the application store or process the data.

Never pass unvalidated input directly to a database query or downstream system.

When `brew_ratio`, `dose_g`, and `water_weight_g` are all present, tools should check that `brew_ratio ~ water_weight_g / dose_g` and surface any significant mismatch as a warning. A mismatch is not a schema error -- both values are stored as supplied.

### Floating-Point Note for `multipleOf: 0.1`

**Implementer note:** The `multipleOf: 0.1` constraint on `water_temp_c` requires decimal-precise arithmetic in validators. In Python, load both the schema and the instance data using `json.loads(..., parse_float=decimal.Decimal)` to avoid false rejections from binary floating-point rounding. Other languages may need equivalent workarounds (e.g., using `BigDecimal` in Java, or a decimal-aware JSON Schema validator). Values like `96.1` and `93.3` are valid multiples of `0.1` in decimal arithmetic but produce non-zero remainders in binary float arithmetic.

### Using Python

```python
import decimal
import json
import yaml
from jsonschema import Draft202012Validator

# Load schema with Decimal parsing for multipleOf accuracy
schema = json.loads(
    open("brewspec.schema.json", encoding="utf-8").read(),
    parse_float=decimal.Decimal,
)
validator = Draft202012Validator(schema)

# Step 1: Safe parse
raw = yaml.safe_load(open("my_brew.yaml", encoding="utf-8"))

# Step 2: Convert to Decimal for multipleOf accuracy
data = json.loads(json.dumps(raw), parse_float=decimal.Decimal)

# Step 3: Schema validation (raises ValidationError if invalid)
validator.validate(data)

# Step 4: Application logic -- data is valid, proceed
```

---

## Backward Compatibility

### Documents from v0.7

The three new fields (`coffee.roaster`, `coffee.roast_level`, `coffee.origins[].elevation_masl`) are additive and optional. Existing v0.7 documents that omit these fields remain valid under v0.8 with only a version bump.

The `water_temp_c` precision constraint is a breaking change. Any v0.7 document with a `water_temp_c` value that has more than one decimal place must be corrected before validating against v0.8.

**Migration steps** for existing v0.7 documents:

1. Change `brewspec_version` from `"0.7"` to `"0.8"`
2. If any `water_temp_c` value has more than one decimal place, round it to one decimal place (e.g., `96.15` -> `96.2`)

### Archived specs

- [`versions/brewspec-v0.7.md`](./versions/brewspec-v0.7.md) -- v0.7 archived spec
- [`versions/brewspec-v0.6.md`](./versions/brewspec-v0.6.md) -- v0.6 archived spec
- [`versions/brewspec-v0.5.md`](./versions/brewspec-v0.5.md) -- v0.5 archived spec
- [`versions/brewspec-v0.4.md`](./versions/brewspec-v0.4.md) -- v0.4 archived spec
- [`versions/brewspec-v0.3.md`](./versions/brewspec-v0.3.md) -- v0.3 archived spec
- [`versions/brewspec-v0.2.md`](./versions/brewspec-v0.2.md) -- v0.2 archived spec
- [`versions/brewspec-v0.1.md`](./versions/brewspec-v0.1.md) -- v0.1 archived spec

---

## Examples

Valid examples in `examples/valid/`:
- `examples/valid/pour_over.yaml` -- Single origin pour over with full brew parameters
- `examples/valid/espresso.yaml` -- Espresso with dose and yield
- `examples/valid/espresso_with_yield.yaml` -- Espresso with `result.yield_g`
- `examples/valid/minimal_no_required_fields.yaml` -- Brew with no required fields
- `examples/valid/immersion_minimal.yaml` -- Minimal brew document
- `examples/valid/equipment.yaml` -- Full equipment descriptor with numeric `grinder_setting`
- `examples/valid/hybrid.yaml` -- Hybrid brew method with blend coffee
- `examples/valid/multi_brew.yaml` -- Multiple brews in a single document
- `examples/valid/pour_over_date_only.yaml` -- Date-only format (YYYY-MM-DD)
- `examples/valid/valid_brew_ratio.yaml` -- Optional `brew_ratio` field
- `examples/valid/valid_grinder_setting.yaml` -- Numeric `grinder_setting`
- `examples/valid/valid_equipment_notes.yaml` -- Equipment `notes` field
- `examples/valid/valid_single_origin_full.yaml` -- Single origin with full origin metadata
- `examples/valid/valid_single_origin_with_varietal.yaml` -- `coffee.name` and `origins[].varietal`
- `examples/valid/valid_blend_with_per_origin_varietal.yaml` -- Blend with per-origin `process` and `varietal`
- `examples/valid/valid_blend_origin.yaml` -- Multi-origin blend
- `examples/valid/light_roast_ethiopian.yaml` -- Light roast Ethiopian with `coffee.roaster`, `coffee.roast_level`, and `origins[].elevation_masl` (new v0.8 fields)

Invalid examples in `examples/invalid/` (for testing validators):
- `examples/invalid/invalid_roast_level.yaml` -- `coffee.roast_level: "medium_light"` (not in enum)
- `examples/invalid/invalid_water_temp_precision.yaml` -- `water_temp_c: 96.15` (violates `multipleOf: 0.1`)
- `examples/invalid/invalid_yield_zero.yaml` -- `result.yield_g: 0` (zero is rejected; must be > 0)
- `examples/invalid/invalid_grinder_setting_string.yaml` -- `grinder_setting` as string (must be a positive number)
- `examples/invalid/invalid_coffee_process_top_level.yaml` -- `coffee.process` at top level (must be inside `origins[]`)
- `examples/invalid/invalid_water_volume_ml.yaml` -- `water_volume_ml` field (removed in v0.6)
- `examples/invalid/invalid_date_no_z.yaml` -- Datetime without trailing Z
- `examples/invalid/invalid_grind_freeform.yaml` -- Freeform grind value not in enum
- `examples/invalid/invalid_tds_at_brew_level.yaml` -- TDS at brew level (must be inside `result`)
- `examples/invalid/rating_out_of_range.yaml` -- Rating value 6 (exceeds maximum of 5)
- `examples/invalid/invalid_origin_string_array.yaml` -- Origins as array of strings (must be array of objects)

---

## Open Questions

- **Expanded roast_level enum** -- The three-value enum (`light`, `medium`, `dark`) is deliberately coarse. If real usage data demonstrates the need for finer gradations (e.g., medium-light, medium-dark), the enum can be extended in a future version.
