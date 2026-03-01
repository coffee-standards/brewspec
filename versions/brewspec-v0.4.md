# BrewSpec v0.4

**Status:** Stable
**Version:** 0.4
**Last Updated:** 2026-02-22

---

## Overview

BrewSpec is an open source standard for describing coffee brews. BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

BrewSpec repository: https://github.com/coffee-standards/brewspec

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.4 defines:
- A JSON Schema for validation
- Required and optional fields for describing a brew
- Coffee ingredient metadata (origin, roast date, varietal, process)
- Water mineral content (`ppm`)
- A `result` object grouping brew outcome measurements and sensory evaluation (`tds`, `ey`, `brix`, `tasting_notes`, `ratings`)
- A `ratings` object with 8 SCA-aligned sensory dimensions (integer 1–5 each)
- Equipment descriptor (`grinder`, `brewer`)
- `maxLength` constraints on all freeform string fields
- A strict 7-value enumeration for `grind`
- Dual-format `date`: full UTC datetime or date-only
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.4 still defers to future versions:
- Standardized enumeration for `method` (deferred pending further usage data)
- Pour schedules and step-by-step timing
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
- Extended equipment fields (kettle, scale)

---

## What Changed in v0.4

v0.4 is a breaking change from v0.3. Files with `brewspec_version: "0.3"` will not validate against the v0.4 schema.

### Summary of Changes

| Change | Type | Description |
|--------|------|-------------|
| `brewspec_version` | Breaking | Const updated from `"0.3"` to `"0.4"` |
| `date` dual-format | Additive / Breaking | Now accepts both `YYYY-MM-DDTHH:MM:SSZ` and `YYYY-MM-DD`; previous datetime-only format still accepted |
| `grind` enum | Breaking | Changed from freeform string to 7-value enum; arbitrary strings are now rejected |
| `result` object | Additive | New optional object grouping brew outcome fields |
| `result.tds` | Additive | TDS moved from flat brew level into `result` |
| `result.ey` | Additive | EY moved from flat brew level into `result` |
| `result.brix` | Additive | New field: dissolved sugar content in degrees Brix |
| `result.tasting_notes` | Additive | New field: freeform sensory description |
| `result.ratings` | Additive | New object: 8 SCA-aligned sensory rating dimensions |
| Flat `tds` removed | Breaking | `tds` at the brew level is no longer valid |
| Flat `ey` removed | Breaking | `ey` at the brew level is no longer valid |
| Flat `rating` removed | Breaking | The `rating` integer field is removed; use `result.ratings.overall` |
| `notes` description | Non-breaking | Description clarified to distinguish process notes from sensory notes |

### Detail: `date` Dual-Format

v0.3 required full UTC datetime: `YYYY-MM-DDTHH:MM:SSZ`

v0.4 accepts both:
- `YYYY-MM-DDTHH:MM:SSZ` — Full UTC datetime (existing format, still accepted)
- `YYYY-MM-DD` — Date-only, for users who do not want to record a time of day

A date-only string like `"2026-02-22"` is now a valid `date` value. Tools that stored full datetime strings are unaffected.

### Detail: `grind` Enum

v0.3 accepted any string for `grind` (freeform, maxLength 100).

v0.4 requires one of these 7 values (finest to coarsest):

| Value | Position |
|-------|----------|
| `turkish` | Finest |
| `espresso` | |
| `fine` | |
| `medium_fine` | |
| `medium` | |
| `medium_coarse` | |
| `coarse` | Coarsest |

Any other string (including previously valid values like `"medium-fine"` with a hyphen) will fail v0.4 validation.

### Detail: `result` Object

Three v0.3 flat fields (`tds`, `ey`, `rating`) are removed from the brew level and replaced by a `result` object:

```yaml
# v0.3 (no longer valid at brew level)
tds: 1.38
ey: 20.5
rating: 4

# v0.4 (correct structure)
result:
  tds: 1.38
  ey: 20.5
  ratings:
    overall: 4
```

All `result` fields are optional. The `result` object itself is optional. An empty `result: {}` is valid.

### Detail: `notes` vs. `result.tasting_notes`

The `notes` field is now explicitly scoped to **brew-process observations** — operational notes about the preparation (e.g., "washed filter paper", "water from Brita filter", "grinder re-calibrated").

For **sensory description** of the brew (e.g., "Bright citrus acidity, caramel sweetness, clean finish"), use `result.tasting_notes`.

This is a documentation clarification only — no schema constraint changes to the `notes` field itself.

---

## File Format

BrewSpec files use **YAML** or **JSON** format:
- UTF-8 encoding
- File extensions: `.yaml`, `.yml`, or `.json`
- Both formats validate against the same JSON Schema

### Array-Only Format

All BrewSpec files contain a `brews` array with minimum 1 element:

```yaml
brewspec_version: "0.4"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    dose_g: 20
    water_weight_g: 320
```

Even a single brew is represented as an array with one element. This simplifies parsers and eliminates branching logic.

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | **Required** | Must be `"0.4"` | The BrewSpec version |
| `brews` | array | **Required** | Minimum 1 element | Array of brew objects |

### Brew Object

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | **Required** | `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD` | Brew date or timestamp | `"2026-02-15T08:30:00Z"`, `"2026-02-15"` |
| `type` | string | **Required** | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | **Required** | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | **Required** | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `method` | string | Optional | Min length 1, max length 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `equipment` | object | Optional | See Equipment Object | Equipment descriptor | |
| `grind` | string | Optional | Enum: 7 values (see Grind Enum) | Standardised grind size | `"medium_fine"`, `"coarse"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `notes` | string | Optional | Min length 1, max length 2000 | Brew-process notes (operational observations). For sensory description, use `result.tasting_notes`. | `"Washed filter paper"` |
| `result` | object | Optional | See Result Object | Brew outcome descriptor | |

### Coffee Object

The entire `coffee` object is optional. When present, all fields within are also optional. No fields are required.

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `roast_date` | string | Optional | Pattern `YYYY-MM-DD` | Roast date. Plain date, no time. | `"2026-01-20"` |
| `type` | string | Optional | Enum: `single_origin`, `blend` | Coffee classification | `"single_origin"` |
| `origin` | array of strings | Optional | Min 1 item; each item min length 1, max length 100 | Origin(s). Multiple entries for blends. | `["Ethiopia"]`, `["Ethiopia", "Colombia"]` |
| `varietal` | string | Optional | Min length 1, max length 100 | Coffee variety or cultivar. Freeform. | `"Heirloom"`, `"Gesha"` |
| `process` | string | Optional | Min length 1, max length 100 | Processing method. Freeform. | `"Washed"`, `"Natural"` |

### Water Object

The entire `water` object is optional. When present, all fields within are also optional.

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `ppm` | number | Optional | >= 0 | Total dissolved solids in parts per million | `150`, `75`, `0` |

### Equipment Object

The entire `equipment` object is optional. When present, all fields within are also optional. No fields are required inside the object; `equipment: {}` is valid.

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `grinder` | string | Optional | Min length 1, max length 100 | Grinder model. Freeform. | `"Comandante C40 MK4"`, `"Baratza Encore ESP"` |
| `brewer` | string | Optional | Min length 1, max length 100 | Brewer or brewing vessel. Freeform. | `"Hario V60 02"`, `"AeroPress Original"` |

### Result Object

The entire `result` object is optional. When present, all fields within are also optional. No fields are required inside the object; `result: {}` is valid.

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield as a percentage | `20.5`, `21.3` |
| `brix` | number | Optional | >= 0 | Dissolved sugar content in degrees Brix. 0 is valid (distilled water baseline). | `4.2`, `0` |
| `tasting_notes` | string | Optional | Min length 1, max length 2000 | Sensory description of the brew. For brew-process notes, use the top-level `notes` field. | `"Bright citrus acidity, caramel sweetness"` |
| `ratings` | object | Optional | See Ratings Object | Multi-dimensional sensory ratings | |

### Ratings Object

The entire `ratings` object is optional. When present, all fields within are also optional. All values are integers 1–5 inclusive.

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

## Enumerations

### Brew Type

The `type` field categorizes the brew method:

| Value | Definition | Examples |
|-------|------------|----------|
| `immersion` | Coffee and water steep together for the full duration | French press, cupping, cold brew |
| `pour_over` | Water flows through coffee grounds via gravity | Hario V60, Chemex, Kalita Wave, Melitta |
| `espresso` | High-pressure extraction | Espresso machine, moka pot |
| `hybrid` | Combination of immersion and percolation | AeroPress (inverted or standard), Clever Dripper |

### Coffee Type

The `coffee.type` field classifies the coffee as a single origin or a blend:

| Value | Definition |
|-------|------------|
| `single_origin` | Coffee sourced from a single origin country or region |
| `blend` | Coffee sourced from multiple origins |

Note: `coffee.type` (values: `single_origin`, `blend`) is distinct from `brew.type` (values: `immersion`, `pour_over`, `espresso`, `hybrid`). They are different fields with different semantics, disambiguated by their position in the object hierarchy.

### Grind Enum

The `grind` field accepts exactly one of these 7 values. Values are ordered from finest to coarsest:

| Value | Description |
|-------|-------------|
| `turkish` | Finest grind; finer than espresso. Used for Turkish coffee. |
| `espresso` | Fine grind for high-pressure extraction. |
| `fine` | Finer than medium; suitable for moka pot or some pour over. |
| `medium_fine` | Between fine and medium; common for V60 and Aeropress. |
| `medium` | Standard grind; suitable for drip, Chemex, and flat-bed drippers. |
| `medium_coarse` | Coarser than medium; suits Clever Dripper and some immersion methods. |
| `coarse` | Coarsest grind; suitable for French press, cold brew, and cupping. |

Any value not in this list — including hyphenated variants like `"medium-fine"` — will fail validation. Users who want to record a specific grinder setting number should use the `notes` field.

---

## Validation

### Validate at Storage Time

Tools implementing BrewSpec should validate a brew document **at storage time** — before writing to any database or file — not only at display or read time. Validating only at read time allows invalid data to enter the store, where it may cause failures much later and in contexts far removed from the original data entry. Validate early; reject invalid data at the point of entry.

The expected validation pipeline is:

1. **Safe parse** — Parse the YAML or JSON input using a safe parser (e.g., `yaml.safe_load` in Python, not `yaml.load`). Reject malformed input before any processing.
2. **Schema validation** — Validate the parsed data against the BrewSpec JSON Schema using a compliant validator (e.g., `jsonschema.Draft202012Validator` in Python, `ajv` in JavaScript). Reject documents that fail validation with a clear error message.
3. **Application logic** — Only after both steps succeed should the application store or process the data.

Never pass unvalidated input directly to a database query or downstream system.

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

### Using JavaScript/TypeScript

```javascript
const Ajv = require("ajv");
const YAML = require("yaml");
const fs = require("fs");

const ajv = new Ajv();
const schema = JSON.parse(fs.readFileSync("brewspec.schema.json"));
const validate = ajv.compile(schema);

// Step 1: Safe parse
const data = YAML.parse(fs.readFileSync("my_brew.yaml", "utf8"));

// Step 2: Schema validation
const valid = validate(data);
if (!valid) {
  console.error(validate.errors);
  process.exit(1);
}

// Step 3: Application logic — data is valid, proceed
```

### Command-Line (using `ajv-cli`)

```bash
npm install -g ajv-cli
ajv validate -s brewspec.schema.json -d my_brew.yaml
```

---

## Design Decisions

### Why array-only format?

**Decision:** All files contain `brews: [...]` (array), never a single bare object.

**Rationale:** One format means simpler parsers, simpler tests, fewer edge cases. No branching logic for "is this a single brew or a list?" The slight verbosity for single-brew files is worth the consistency.

### Why `date` accepts two formats?

**Decision:** v0.4 accepts both `YYYY-MM-DDTHH:MM:SSZ` (full UTC datetime) and `YYYY-MM-DD` (date-only).

**Rationale:** Users of a manual logging tool often do not know or care about the exact time of day. Requiring a full timestamp creates friction. Date-only format solves the primary UX problem while preserving the existing format for tools that already use it.

**Why Z is required for the datetime format:** The `Z` suffix enforces UTC. Permitting offsets like `+10:00` would allow two files representing the same moment to be recorded differently, breaking time-based comparison. Full datetime with timezone offsets is excluded intentionally.

**Calendar validation:** The patterns enforce format only, not calendar correctness. `"2026-13-01"` (month 13) passes schema validation. Calendar-correct validation is an application-layer responsibility.

### Why is `grind` now an enum?

**Decision:** `grind` changes from a freeform string to a closed 7-value enum.

**Rationale:** Freeform grind strings have produced inconsistent values across files (`"medium-fine"`, `"medium fine"`, `"med fine"`, etc.) that cannot be compared or aggregated. Standardizing on 7 named values makes cross-brew analysis possible. A freeform fallback would defeat the standardization goal. Users who want to record a specific grinder setting number should use the `notes` field.

### Why metric units only?

**Decision:** Coffee and water weight in grams, volume in milliliters, temperature in celsius, duration in seconds.

**Rationale:** Metric is the global standard in specialty coffee. Modern brewing practice measures water by weight (grams), not volume. US customary units can be converted by tools if needed, but the spec is metric-native.

### Why is `result` optional with no required fields?

**Decision:** `result` follows the same pattern as `coffee`, `water`, and `equipment` — entirely optional, with all internal fields also optional. `additionalProperties: false` prevents unexpected data. An empty `result: {}` is valid.

**Why `brix` uses `minimum: 0` and not `exclusiveMinimum: 0`:** 0 °Brix is a physically valid reading (distilled water). `tds` and `ey` use `exclusiveMinimum: 0` because a brew TDS or extraction yield of exactly 0 is meaningless (it means no extraction occurred). 0 °Brix can arise from a clean refractometer baseline and is a legitimate measurement.

### Why are `ratings` dimensions 1–5?

**Decision:** Integer scale, 1 = poor, 5 = excellent. The 8 dimensions align with SCA cupping protocol.

**Rationale:** Simple, familiar, reduces decision paralysis. Finer granularity (0-100 as in the SCA cupping form) adds cognitive load without clear benefit for everyday logging. All dimensions are optional — users can provide only the dimensions they care about.

### Why snake_case?

**Decision:** All field names use lowercase snake_case: `dose_g`, `water_weight_g`, `duration_s`.

**Rationale:** Consistent with Python conventions (BrewSpec reference implementation is Python-first). Easier to read than camelCase in YAML. JSON Schema standard uses snake_case for keywords.

### Why is `coffee.origin` an array?

**Decision:** `coffee.origin` is an array of strings (`minItems: 1`), not a plain string.

**Rationale:** This supports blends where multiple origins are known (`["Ethiopia", "Colombia"]`) without requiring a separate field. For single-origin coffees, the array has one entry. An empty array is not valid. This is forward-compatible with blend metadata without a schema change.

### Why is `roast_date` a plain date?

**Decision:** `roast_date` uses format `YYYY-MM-DD`, not the full ISO 8601 datetime used by `date`.

**Rationale:** Roasters label bags by day only. A full datetime would imply time-of-day precision that does not exist in practice. The spec uses two date formats intentionally: `date` (brew timestamp) and `roast_date` (ingredient label, day precision is sufficient).

---

## Backward Compatibility

### v0.3 to v0.4 — Breaking Changes

v0.4 introduces breaking changes. v0.3 files will not pass v0.4 schema validation without migration. The version const must be updated and structural changes applied.

**Fields removed or moved:**

| v0.3 Field | v0.4 Replacement | Migration Action |
|------------|-----------------|-----------------|
| `tds` (flat on brew) | `result.tds` | Move to `result` object |
| `ey` (flat on brew) | `result.ey` | Move to `result` object |
| `rating` (flat on brew) | `result.ratings.overall` | Move to `result.ratings` object |

**Breaking changes to existing fields:**

| Field | v0.3 | v0.4 | Migration Action |
|-------|------|------|-----------------|
| `brewspec_version` | `"0.3"` | `"0.4"` | Update version string |
| `grind` | Freeform string (any value) | Enum (7 values only) | Map to nearest enum value or remove |

**Additive changes (no migration required):**

| Feature | Notes |
|---------|-------|
| `date` date-only format | Existing datetime strings still valid |
| `result.brix` | New optional field |
| `result.tasting_notes` | New optional field |
| `result.ratings` | New optional object (replaces `rating`) |

### Step-by-Step Migration Guide: v0.3 to v0.4

Given a v0.3 file, apply these steps in order:

**Step 1: Update the version**

```yaml
# Before
brewspec_version: "0.3"

# After
brewspec_version: "0.4"
```

**Step 2: Move `tds` into `result`**

If your brew has a `tds` field at the brew level, move it inside a `result` object:

```yaml
# Before (v0.3)
tds: 1.38

# After (v0.4)
result:
  tds: 1.38
```

**Step 3: Move `ey` into `result`**

If your brew has an `ey` field at the brew level, move it inside `result`:

```yaml
# Before (v0.3)
ey: 20.5

# After (v0.4)
result:
  ey: 20.5
```

If you have both `tds` and `ey`, group them in a single `result` object:

```yaml
result:
  tds: 1.38
  ey: 20.5
```

**Step 4: Move `rating` into `result.ratings.overall`**

If your brew has a `rating` integer, move it to `result.ratings.overall`:

```yaml
# Before (v0.3)
rating: 4

# After (v0.4)
result:
  ratings:
    overall: 4
```

**Step 5: Migrate `grind` values**

If your brew has a `grind` field, ensure the value is one of the 7 allowed enum values. Map freeform v0.3 values to the nearest v0.4 enum value:

| Typical v0.3 value | v0.4 enum value |
|--------------------|-----------------|
| `"turkish"` | `turkish` |
| `"espresso"` | `espresso` |
| `"fine"` | `fine` |
| `"medium-fine"`, `"medium fine"` | `medium_fine` |
| `"medium"` | `medium` |
| `"medium-coarse"`, `"medium coarse"` | `medium_coarse` |
| `"coarse"` | `coarse` |

If the v0.3 value does not map clearly to any enum value, remove the `grind` field and record the original value in `notes` instead.

**Step 6: Validate**

After applying all steps, validate the migrated file against the v0.4 schema:

```bash
# Python
python -c "
import json, yaml
from jsonschema import Draft202012Validator
schema = json.load(open('brewspec.schema.json'))
data = yaml.safe_load(open('my_brew.yaml'))
Draft202012Validator(schema).validate(data)
print('Valid')
"
```

### v0.4 from v0.1 or v0.2

v0.1 and v0.2 files require the structural migration described in the archived spec documents, plus the v0.3 → v0.4 steps above. See the archived specs in `versions/`:
- [`versions/v0.1.md`](./versions/v0.1.md) — v0.1 archived spec
- [`versions/brewspec-v0.2.md`](./versions/brewspec-v0.2.md) — v0.2 archived spec
- [`versions/brewspec-v0.3.md`](./versions/brewspec-v0.3.md) — v0.3 archived spec

---

## Examples

See [`examples/`](./examples/) directory:

**Valid examples:**
- [`valid/pour_over.yaml`](./examples/valid/pour_over.yaml) — Pour over with full coffee metadata, water ppm, and result object
- [`valid/pour_over.json`](./examples/valid/pour_over.json) — Same brew in JSON format
- [`valid/immersion_minimal.yaml`](./examples/valid/immersion_minimal.yaml) — Minimal brew (required fields only)
- [`valid/espresso.yaml`](./examples/valid/espresso.yaml) — Espresso with result.ratings and tasting_notes
- [`valid/multi_brew.yaml`](./examples/valid/multi_brew.yaml) — Multiple brews; demonstrates blend with multiple origins
- [`valid/hybrid.yaml`](./examples/valid/hybrid.yaml) — AeroPress hybrid brew with blend coffee metadata
- [`valid/equipment.yaml`](./examples/valid/equipment.yaml) — Full brew with equipment and all v0.4 result fields

**Invalid examples (for testing):**
- [`invalid/missing_version.yaml`](./examples/invalid/missing_version.yaml) — Missing `brewspec_version`
- [`invalid/missing_required_field.yaml`](./examples/invalid/missing_required_field.yaml) — Brew missing `date`
- [`invalid/invalid_type_enum.yaml`](./examples/invalid/invalid_type_enum.yaml) — Invalid `type` value
- [`invalid/negative_weight.yaml`](./examples/invalid/negative_weight.yaml) — Negative `dose_g`
- [`invalid/empty_brews_array.yaml`](./examples/invalid/empty_brews_array.yaml) — Empty `brews` array
- [`invalid/v0.1_format.yaml`](./examples/invalid/v0.1_format.yaml) — v0.1 structure with nested `coffee.dose_g`
- [`invalid/zero_duration.yaml`](./examples/invalid/zero_duration.yaml) — `duration_s: 0`

---

## License

BrewSpec is open source. The spec and examples are released under the Apache License 2.0. See the project repository for full license terms.

---

## Contributing

BrewSpec is an open standard. Contributions are welcome.

BrewSpec repository: https://github.com/coffee-standards/brewspec

- **Propose changes:** Open an issue or pull request in the BrewSpec repository
- **Report problems:** File an issue describing the ambiguity or error in the spec
- **Share usage data:** Help us understand how people use the spec to inform future design

See [`README.md`](./README.md) for contribution guidelines.
