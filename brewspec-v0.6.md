# BrewSpec v0.6

Status: Stable
Version: 0.6
Last Updated: 2026-03-05

---

## Overview

BrewSpec is an open source standard for describing coffee brews. BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

BrewSpec repository: https://github.com/coffee-standards/brewspec

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.6 defines:
- A JSON Schema for validation
- Required and optional fields for describing a brew
- Structured coffee origin metadata (`origins` object array with nine optional fields per entry, including `varietal` — new in v0.6)
- An optional `coffee.name` field for branded product names or descriptive labels (new in v0.6)
- Water mineral content (`ppm`)
- A `result` object grouping brew outcome measurements and sensory evaluation (`tds`, `ey`, `brix`, `tasting_notes`, `ratings`)
- A `ratings` object with 8 SCA-aligned sensory dimensions (integer 1–5 each)
- Equipment descriptor (`grinder`, `brewer`, `grinder_setting`, `notes`) — `grinder_setting` is now a positive number (changed from string in v0.5)
- `brew_ratio` as an optional float at the brew level
- `maxLength` constraints on all freeform string fields
- A strict 7-value enumeration for `grind`
- Dual-format `date`: full UTC datetime or date-only
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.6 still defers to future versions:
- Standardized enumeration for `method` (deferred pending further usage data)
- Pour schedules and step-by-step timing
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
- Extended equipment fields (kettle, scale)

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Required | Must be `"0.6"` | The BrewSpec version. Rejected if missing or any other value. |
| `brews` | array | Required | Minimum 1 element | Array of brew objects. At least one brew required. |

### Brew Object

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Required | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Brew date or datetime (UTC) | `"2026-02-21"`, `"2026-02-15T08:30:00Z"` |
| `type` | string | Required | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Required | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Required | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `brew_ratio` | number | Optional | > 0 (exclusive) | Water-to-coffee ratio as a float (grams water per gram coffee). e.g. `15.5` represents 15.5:1. Tools should prefer this stored value when present. Consistency with `dose_g`/`water_weight_g` is not schema-enforced; tools should surface mismatches as a warning. | `15.5`, `15.56` |
| `method` | string | Optional | minLength 1, maxLength 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
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
| `name` | string | Optional | minLength 1, maxLength 150 | A branded product name or human-readable descriptive label for the coffee. New in v0.6. | `"Ethiopia Yirgacheffe"`, `"Blue Bottle Hayes Valley Espresso"` |
| `roast_date` | string | Optional | `YYYY-MM-DD` | Roast date. Plain date; no time component. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Whether the coffee is a single origin or a blend. | `"single_origin"` |
| `origins` | array | Optional | minItems 1; each item is an Origin Object | Structured origin records. Omit entirely to record no origin data (present but empty is invalid). | |

### Origin Object (all fields optional; `additionalProperties: false`)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `name` | string | Optional | minLength 1, maxLength 100 | Descriptive name for this origin component. Plays the same role at the component level as coffee.name does at the coffee level. For single-origin coffees it will typically match coffee.name; for blends it is the name of this specific component (e.g. 'Brazil Natural', 'Colombia Washed'). | `"Ethiopia Yirgacheffe Natural"` |
| `country` | string | Optional | minLength 1, maxLength 100 | Country of production. | `"Ethiopia"`, `"Colombia"` |
| `region` | string | Optional | minLength 1, maxLength 100 | State, province, or named growing region. | `"Yirgacheffe"`, `"Huila"` |
| `subregion` | string | Optional | minLength 1, maxLength 100 | District, zone, or sub-area within the region. | `"Kochere"` |
| `producer` | string | Optional | minLength 1, maxLength 100 | Farm, cooperative, or washing station name. | `"Daye Bensa Washing Station"` |
| `process` | string | Optional | minLength 1, maxLength 100 | Green coffee processing method at origin. | `"Washed"`, `"Natural"`, `"Honey"` |
| `lot` | string | Optional | minLength 1, maxLength 100 | Lot or batch identifier from the producer. | `"Lot 42"`, `"Export Grade 1"` |
| `harvest_year` | integer | Optional | minimum 1900, maximum 2100 | Year the crop was harvested. | `2025` |
| `varietal` | string | Optional | minLength 1, maxLength 100 | Coffee varietal for this origin entry. Records the coffee variety or cultivar specific to this component. New in v0.6. | `"Heirloom"`, `"Gesha"`, `"Bourbon"` |

### Water Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

### Equipment Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | minLength 1, maxLength 100 | Grinder model. Freeform. | `"Comandante C40 MK4"` |
| `brewer` | string | Optional | minLength 1, maxLength 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"` |
| `grinder_setting` | number | Optional | > 0 (exclusive) | Grinder dial position or click setting for this brew. Must be a positive number. Integer for primary increment grinders (e.g. `21` on a Comandante C40); decimal tenths for grinders with sub-steps (e.g. `5.2` on a Fellow Ode Gen 2 means primary position 5, second sub-step). Changed from string in v0.5. | `21`, `5.2`, `30` |
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

## What Changed in v0.6

### New Fields

- **`coffee.name`** (`string`, optional, maxLength 150) — A branded product name or human-readable descriptive label for the coffee as a whole (e.g. `"Ethiopia Yirgacheffe"`, `"Blue Bottle Hayes Valley Espresso"`). Useful for blend names and for labelling single-origin coffees with their retail or marketing name. Lives on the top-level `coffee` object.

- **`coffee.origins[].varietal`** (`string`, optional, maxLength 100) — Coffee varietal for a specific origin entry. Records the coffee variety or cultivar specific to that component (e.g. `"Heirloom"`, `"Gesha"`, `"Bourbon"`). Placed at the origin level so blends can record per-component varietals accurately.

### Breaking Changes

- **`equipment.grinder_setting` changed from `string` to `number`** — The `grinder_setting` field now requires a positive number (`exclusiveMinimum: 0`). Freeform strings like `"21 clicks"` or `"3.2.1"` are no longer valid. Use the numeric position only: `21`, `5.2`. Migration: strip non-numeric suffixes and convert to a number. If your grinder uses a non-numeric system, omit the field.

- **`water_volume_ml` removed from brew object** — The field is removed. `water_weight_g` is the retained measurement (water density at brewing temperatures is effectively 1 g/ml, making volume a near-duplicate). Documents that include `water_volume_ml` will fail v0.6 validation.

- **`coffee.process` removed from top-level coffee object** — Process is semantically ambiguous at the top level for blends. Use `coffee.origins[].process` to record process per origin component. Documents that include `coffee.process` at the top level will fail v0.6 validation.

- **`coffee.varietal` removed from top-level coffee object** — Varietal is an intrinsic property of a specific origin, not of the top-level coffee descriptor. Use the new `coffee.origins[].varietal` field instead. Documents that include `coffee.varietal` at the top level will fail v0.6 validation.

### Non-Breaking Changes

None in v0.6. All additive changes (`coffee.name`, `coffee.origins[].varietal`) are optional new fields.

---

## Validation

### Validate at Storage Time

Tools implementing BrewSpec should validate a brew document at storage time — before writing to any database or file — not only at display or read time. Validating only at read time allows invalid data to enter the store, where it may cause failures much later and in contexts far removed from the original data entry. Validate early; reject invalid data at the point of entry.

The expected validation pipeline is:

1. **Safe parse** — Parse the YAML or JSON input using a safe parser (e.g., `yaml.safe_load` in Python, not `yaml.load`). Reject malformed input before any processing.
2. **Schema validation** — Validate the parsed data against the BrewSpec JSON Schema using a compliant validator (e.g., `jsonschema.Draft202012Validator` in Python, `ajv` in JavaScript). Reject documents that fail validation with a clear error message.
3. **Application logic** — Only after both steps succeed should the application store or process the data.

Never pass unvalidated input directly to a database query or downstream system.

When `brew_ratio`, `dose_g`, and `water_weight_g` are all present, tools should check that `brew_ratio ≈ water_weight_g / dose_g` and surface any significant mismatch as a warning. A mismatch is not a schema error — both values are stored as supplied.

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

### Documents from v0.5

v0.6 introduces four breaking changes from v0.5. v0.5 documents will fail validation under v0.6 if they contain any of the following.

**Change 1: `equipment.grinder_setting` type changed from string to number**

```yaml
# v0.5 format (string — no longer valid in v0.6)
equipment:
  grinder: "Comandante C40 MK4"
  grinder_setting: "21 clicks"

# v0.6 equivalent (number)
equipment:
  grinder: "Comandante C40 MK4"
  grinder_setting: 21
```

Migration: Strip non-numeric suffixes and convert to a number. If your grinder uses a non-numeric setting system, omit the field.

**Change 2: `water_volume_ml` removed**

```yaml
# v0.5 format (field present — no longer valid in v0.6)
date: "2026-02-21"
type: "pour_over"
dose_g: 18.0
water_weight_g: 288.0
water_volume_ml: 288.0   # remove this line

# v0.6 equivalent
date: "2026-02-21"
type: "pour_over"
dose_g: 18.0
water_weight_g: 288.0
```

Migration: Remove the `water_volume_ml` key. Use `water_weight_g` for water measurement.

**Change 3: `coffee.process` removed from top-level coffee object**

```yaml
# v0.5 format (coffee.process at top level — no longer valid in v0.6)
coffee:
  type: "single_origin"
  process: "Washed"   # remove from here; move to origins[]
  origins:
    - country: "Ethiopia"

# v0.6 format (process moved to origins[])
coffee:
  type: "single_origin"
  origins:
    - country: "Ethiopia"
      process: "Washed"   # process lives here in v0.6
```

Migration: Move the `coffee.process` value to `coffee.origins[].process` on the relevant origin entry.

**Change 4: `coffee.varietal` removed from top-level coffee object; `coffee.origins[].varietal` added**

```yaml
# v0.5 format (coffee.varietal at top level — no longer valid in v0.6)
coffee:
  type: "single_origin"
  varietal: "Heirloom"   # remove this line; move to origins[]
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"

# v0.6 format (varietal moved to origins[])
coffee:
  type: "single_origin"
  origins:
    - country: "Ethiopia"
      region: "Yirgacheffe"
      varietal: "Heirloom"   # varietal lives here in v0.6
```

Migration: Move the `coffee.varietal` value to `coffee.origins[].varietal` on the relevant origin entry. For blends, add `varietal` to each origin entry that has a known varietal.

### Migration summary

To migrate a v0.5 document to v0.6:

1. Change `brewspec_version` from `"0.5"` to `"0.6"`
2. Change `equipment.grinder_setting` from a string to a positive number (if present)
3. Remove `water_volume_ml` from the brew object (if present)
4. Move `coffee.process` to `coffee.origins[].process` (if present at top level)
5. Move `coffee.varietal` to `coffee.origins[].varietal` (if present at top level)

Steps 2–5 are only required if the document uses the affected fields.

### Archived specs

- [`versions/brewspec-v0.5.md`](./versions/brewspec-v0.5.md) — v0.5 archived spec
- [`versions/brewspec-v0.4.md`](./versions/brewspec-v0.4.md) — v0.4 archived spec
- [`versions/brewspec-v0.3.md`](./versions/brewspec-v0.3.md) — v0.3 archived spec
- [`versions/brewspec-v0.2.md`](./versions/brewspec-v0.2.md) — v0.2 archived spec
- [`versions/brewspec-v0.1.md`](./versions/brewspec-v0.1.md) — v0.1 archived spec

---

## Examples

Valid examples in `examples/valid/`:
- `examples/valid/pour_over.yaml` — Single origin pour over with full brew parameters
- `examples/valid/espresso.yaml` — Espresso with dose and yield
- `examples/valid/immersion_minimal.yaml` — Minimal brew with required fields only
- `examples/valid/equipment.yaml` — Full equipment descriptor with numeric `grinder_setting`
- `examples/valid/hybrid.yaml` — Hybrid brew method with blend coffee
- `examples/valid/multi_brew.yaml` — Multiple brews in a single document
- `examples/valid/pour_over_date_only.yaml` — Date-only format (YYYY-MM-DD)
- `examples/valid/valid_brew_ratio.yaml` — Optional `brew_ratio` field
- `examples/valid/valid_grinder_setting.yaml` — Numeric `grinder_setting` (new v0.6 format)
- `examples/valid/valid_equipment_notes.yaml` — Equipment `notes` field
- `examples/valid/valid_single_origin_full.yaml` — Single origin with full origin metadata
- `examples/valid/valid_single_origin_with_varietal.yaml` — `coffee.name` and `origins[].varietal` (new v0.6 fields)
- `examples/valid/valid_blend_with_per_origin_varietal.yaml` — Blend with per-origin `process` and `varietal`
- `examples/valid/valid_blend_origin.yaml` — Multi-origin blend
- `examples/valid/valid_brew_ratio.yaml` — Brew ratio field

Invalid examples in `examples/invalid/` (for testing validators):
- `examples/invalid/invalid_grinder_setting_string.yaml` — `grinder_setting` as string (rejected in v0.6)
- `examples/invalid/invalid_coffee_process_top_level.yaml` — `coffee.process` at top level (rejected in v0.6)
- `examples/invalid/invalid_water_volume_ml.yaml` — `water_volume_ml` field (removed in v0.6)
- `examples/invalid/invalid_date_no_z.yaml` — Datetime without trailing Z
- `examples/invalid/invalid_grind_freeform.yaml` — Freeform grind value not in enum
- `examples/invalid/invalid_tds_at_brew_level.yaml` — TDS at brew level (must be inside `result`)
- `examples/invalid/rating_out_of_range.yaml` — Rating value 6 (exceeds maximum of 5)
