# BrewSpec v0.6

Status: Archived
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
| `name` | string | Optional | minLength 1, maxLength 100 | Descriptive name for this origin component. | `"Ethiopia Yirgacheffe Natural"` |
| `country` | string | Optional | minLength 1, maxLength 100 | Country of production. | `"Ethiopia"`, `"Colombia"` |
| `region` | string | Optional | minLength 1, maxLength 100 | State, province, or named growing region. | `"Yirgacheffe"`, `"Huila"` |
| `subregion` | string | Optional | minLength 1, maxLength 100 | District, zone, or sub-area within the region. | `"Kochere"` |
| `producer` | string | Optional | minLength 1, maxLength 100 | Farm, cooperative, or washing station name. | `"Daye Bensa Washing Station"` |
| `process` | string | Optional | minLength 1, maxLength 100 | Green coffee processing method at origin. | `"Washed"`, `"Natural"`, `"Honey"` |
| `lot` | string | Optional | minLength 1, maxLength 100 | Lot or batch identifier from the producer. | `"Lot 42"`, `"Export Grade 1"` |
| `harvest_year` | integer | Optional | minimum 1900, maximum 2100 | Year the crop was harvested. | `2025` |
| `varietal` | string | Optional | minLength 1, maxLength 100 | Coffee varietal for this origin entry. New in v0.6. | `"Heirloom"`, `"Gesha"`, `"Bourbon"` |

### Water Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

### Equipment Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | minLength 1, maxLength 100 | Grinder model. Freeform. | `"Comandante C40 MK4"` |
| `brewer` | string | Optional | minLength 1, maxLength 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"` |
| `grinder_setting` | number | Optional | > 0 (exclusive) | Grinder dial position or click setting for this brew. Must be a positive number. | `21`, `5.2`, `30` |
| `notes` | string | Optional | minLength 1, maxLength 2000 | Equipment state observations. | `"Burrs replaced 2026-01"` |

### Result Object (entire object optional; all fields within optional)

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield as a percentage | `20.5`, `21.3` |
| `brix` | number | Optional | >= 0 | Dissolved sugar content in degrees Brix. 0 is valid. | `4.2`, `0` |
| `tasting_notes` | string | Optional | minLength 1, maxLength 2000 | Sensory description of the brew. | `"Bright citrus acidity, caramel sweetness"` |
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

- **`coffee.name`** (`string`, optional, maxLength 150) — A branded product name or human-readable descriptive label for the coffee as a whole. Lives on the top-level `coffee` object.

- **`coffee.origins[].varietal`** (`string`, optional, maxLength 100) — Coffee varietal for a specific origin entry. Placed at the origin level so blends can record per-component varietals accurately.

### Breaking Changes

- **`equipment.grinder_setting` changed from `string` to `number`** — The `grinder_setting` field now requires a positive number. Freeform strings are no longer valid.

- **`water_volume_ml` removed from brew object** — The field is removed. `water_weight_g` is the retained measurement.

- **`coffee.process` removed from top-level coffee object** — Use `coffee.origins[].process` instead.

- **`coffee.varietal` removed from top-level coffee object** — Use the new `coffee.origins[].varietal` field instead.

---

## Validation

See `brewspec-v0.7.md` for current validation guidance.

---

## Archived specs

- [`versions/brewspec-v0.5.md`](./brewspec-v0.5.md) — v0.5 archived spec
- [`versions/brewspec-v0.4.md`](./brewspec-v0.4.md) — v0.4 archived spec
- [`versions/brewspec-v0.3.md`](./brewspec-v0.3.md) — v0.3 archived spec
- [`versions/brewspec-v0.2.md`](./brewspec-v0.2.md) — v0.2 archived spec
- [`versions/brewspec-v0.1.md`](./brewspec-v0.1.md) — v0.1 archived spec
