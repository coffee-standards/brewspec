# BrewSpec v0.3

**Status:** Stable
**Version:** 0.3
**Last Updated:** 2026-02-21

---

## Overview

BrewSpec is an open source standard for describing coffee brews. BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

BrewSpec repository: https://github.com/coffee-standards/brewspec

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.3 defines:
- A JSON Schema for validation
- Required and optional fields for describing a brew
- Coffee ingredient metadata (origin, roast date, varietal, process)
- Water mineral content (`ppm`)
- Brew result fields (`tds`, `ey`)
- Equipment descriptor (`grinder`, `brewer`)
- `maxLength` constraints on all freeform string fields
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.3 still defers to future versions:
- Standardized enumerations for `method` and `grind` (deferred pending usage data)
- Pour schedules and step-by-step timing
- Tasting dimensions (cupping scores, flavor notes taxonomy)
- Extended water chemistry (pH, bicarbonate, mineral breakdown)
- Date-only format for `date` field (requires schema change; tracked for v0.4)

---

## File Format

BrewSpec files use **YAML** or **JSON** format:
- UTF-8 encoding
- File extensions: `.yaml`, `.yml`, or `.json`
- Both formats validate against the same JSON Schema

### Array-Only Format

All BrewSpec files contain a `brews` array with minimum 1 element:

```yaml
brewspec_version: "0.3"
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
| `brewspec_version` | string | **Required** | Must be `"0.3"` | The BrewSpec version |
| `brews` | array | **Required** | Minimum 1 element | Array of brew objects |

### Brew Object

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | **Required** | ISO 8601 UTC: `YYYY-MM-DDTHH:MM:SSZ` | Brew timestamp | `"2026-02-15T08:30:00Z"` |
| `type` | string | **Required** | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | **Required** | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | **Required** | > 0 (exclusive) | Water weight in grams | `320`, `36` |
| `method` | string | Optional | Min length 1, max length 100 | Freeform brewer description | `"Hario V60"`, `"AeroPress inverted"` |
| `water_volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters | `320` |
| `water_temp_c` | number | Optional | 0–100 inclusive | Water temperature in celsius | `96`, `93` |
| `coffee` | object | Optional | See Coffee Object | Coffee ingredient descriptor | |
| `water` | object | Optional | See Water Object | Water ingredient descriptor | |
| `equipment` | object | Optional | See Equipment Object | Equipment descriptor | |
| `grind` | string | Optional | Min length 1, max length 100 | Freeform grind description | `"medium-fine"` |
| `duration_s` | number | Optional | > 0 (exclusive) | Brew duration in seconds | `180`, `28` |
| `tds` | number | Optional | > 0 (exclusive) | TDS percentage of finished brew | `1.38`, `8.5` |
| `ey` | number | Optional | > 0 (exclusive) | Extraction yield percentage | `20.5`, `21.3` |
| `rating` | integer | Optional | 1–5 inclusive | Brew rating. 1 = poor, 5 = excellent | `4` |
| `notes` | string | Optional | Min length 1, max length 2000 | Freeform tasting or session notes | `"Bright acidity"` |

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

---

## Validation

BrewSpec files are validated against the JSON Schema: [`brewspec.schema.json`](./brewspec.schema.json)

### Using Python

```python
import json
import yaml
from jsonschema import Draft202012Validator

# Load schema
schema = json.load(open("brewspec.schema.json", encoding="utf-8"))
validator = Draft202012Validator(schema)

# Validate a YAML file
data = yaml.safe_load(open("my_brew.yaml", encoding="utf-8"))
validator.validate(data)  # Raises ValidationError if invalid
```

### Using JavaScript/TypeScript

```javascript
const Ajv = require("ajv");
const YAML = require("yaml");
const fs = require("fs");

const ajv = new Ajv();
const schema = JSON.parse(fs.readFileSync("brewspec.schema.json"));
const validate = ajv.compile(schema);

const data = YAML.parse(fs.readFileSync("my_brew.yaml", "utf8"));
const valid = validate(data);
if (!valid) console.error(validate.errors);
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

### Why freeform text for method and grind?

**Decision:** `method` and `grind` are freeform strings, not enumerations.

**Rationale:**
- Grind perception is relative to equipment. What's "medium" on one grinder is "medium-fine" on another.
- Method naming is inconsistent across brands (e.g., "V60", "Hario V60", "pour over cone").
- Standardizing prematurely adds false precision and frustrates users who don't fit the categories.

**v0.4 candidate:** Analyze real v0.3 usage data from BrewLog CLI. If clear patterns emerge, propose optional enumerations with freeform fallback.

### Why metric units only?

**Decision:** Coffee and water weight in grams, volume in milliliters, temperature in celsius, duration in seconds.

**Rationale:** Metric is the global standard in specialty coffee. Modern brewing practice measures water by weight (grams), not volume. US customary units can be converted by tools if needed, but the spec is metric-native.

### Why ISO 8601 timestamps in UTC?

**Decision:** `date` field uses strict format `YYYY-MM-DDTHH:MM:SSZ` (UTC only).

**Rationale:** Unambiguous, sortable, machine-parseable, universally supported. Tools can display in local timezone, but storage is UTC.

**Known friction:** Users report the full datetime format is onerous for a manual logging tool. A date-only format (`YYYY-MM-DD`) would be more natural but requires a schema change and corresponding tool updates. This is tracked as a candidate for v0.4.

### Why snake_case?

**Decision:** All field names use lowercase snake_case: `dose_g`, `water_weight_g`, `duration_s`.

**Rationale:**
- Consistent with Python conventions (BrewSpec reference implementation is Python-first)
- Easier to read than camelCase in YAML
- JSON Schema standard uses snake_case for keywords

### Why rating 1-5 instead of 0-10 or 0-100?

**Decision:** Integer scale, 1 = poor, 5 = excellent.

**Rationale:** Simple, familiar (5-star rating), reduces decision paralysis. Finer granularity (0-100) adds cognitive load without clear benefit for home brewers. Rating is optional — power users can omit it or use `notes` for detailed tasting feedback.

### Why are brew quantities at the brew level, not inside ingredient objects?

**Decision:** `dose_g`, `water_weight_g`, `water_volume_ml`, and `water_temp_c` are direct properties of the brew object. The `coffee` and `water` objects describe the ingredient, not the brew parameters.

**Rationale:** A coffee dose is a parameter of the brew act — you dose differently for a V60 and an espresso even when using the same coffee. `origin`, `roast_date`, and `varietal` describe the coffee itself — they are the same regardless of brew method. Mixing ingredient identity with brew-specific quantities (as v0.1 did) produces a model that becomes increasingly incoherent as coffee metadata is added. v0.2 corrected this while adoption was near-zero.

### Why is `ey` flat on the brew object, not grouped with `tds` in a `result` object?

**Decision:** `ey` is placed at the same level as `tds`, `rating`, and `notes` — not inside a `result: {}` wrapper.

**Rationale:** Two fields do not warrant a wrapping object at this stage. A `result` object would add structural complexity without adding clarity. If a third result-type field emerges in a future version, grouping can be introduced then with a stronger motivation. Premature grouping locks in a structural decision before the data model is stable.

### Why is `equipment` a separate object, not flat fields?

**Decision:** `grinder` and `brewer` live inside an `equipment: {}` object rather than as top-level brew fields.

**Rationale:** Equipment fields describe the physical setup used, not the brew parameters or the ingredients. Grouping them in a named object keeps the brew level semantically clean, follows the same pattern as `coffee` and `water`, and provides a natural extension point for future equipment fields (e.g., `kettle`, `scale`) without polluting the top-level namespace.

### Why freeform strings for equipment fields?

**Decision:** `equipment.grinder` and `equipment.brewer` are freeform strings with no enumeration.

**Rationale:** Equipment identity is objective (a grinder model is a grinder model), but standardizing names requires a curated registry that does not exist yet. Freeform strings let users record what they actually use without waiting for an enumeration. A tool-maintained registry or fuzzy matching layer can normalize values at the application level without a schema constraint.

### Why `maxLength` constraints in v0.3?

**Decision:** All freeform string fields now have explicit `maxLength` — 100 for most fields, 2000 for `notes`.

**Rationale:** The v0.2 review flagged the absence of length limits as a low-concern security issue: without `maxLength`, a malicious or buggy file could contain arbitrarily large strings that crash naive parsers or cause DB column overflow. Now that implementing tools are being built against the spec, closing this gap in the spec is preferable to patching it in each tool independently. The limits are generous — 100 characters covers any realistic grinder name, brew method, or varietal; 2000 characters covers detailed tasting notes.

### Why is `coffee.origin` an array?

**Decision:** `coffee.origin` is an array of strings (`minItems: 1`), not a plain string.

**Rationale:** This supports blends where multiple origins are known (`["Ethiopia", "Colombia"]`) without requiring a separate field. For single-origin coffees, the array has one entry. An empty array is not valid. This is forward-compatible with blend metadata without a schema change.

### Why is `roast_date` a plain date (not a datetime)?

**Decision:** `roast_date` uses format `YYYY-MM-DD`, not the full ISO 8601 datetime used by `date`.

**Rationale:** Roasters label bags by day only. A full datetime (`2026-01-20T00:00:00Z`) would imply time-of-day precision that does not exist in practice and would make manual entry unnecessarily verbose. The spec uses two date formats intentionally: `date` (brew timestamp, needs UTC precision for sorting and deduplication) and `roast_date` (ingredient label, day precision is sufficient).

### Why is `tds` a flat brew-level field?

**Decision:** `tds` is at the brew level alongside `rating` and `notes`, not inside a `result: {}` wrapper.

**Rationale:** This was established in v0.2 and is consistent with the v0.3 decision to keep `ey` flat as well. Grouping in a `result` object is deferred until a stronger motivation (a third result-type field) emerges.

### Why does `coffee.type` not conflict with `brew.type`?

**Decision:** The `coffee.type` field (values: `single_origin`, `blend`) lives inside the `coffee` object. The `brew.type` field (values: `immersion`, `pour_over`, `espresso`, `hybrid`) lives at the brew level. They are distinct fields with distinct semantics.

**Rationale:** The namespacing is handled naturally by JSON/YAML object nesting. Tool builders access `brew["type"]` and `brew["coffee"]["type"]` — unambiguous in any language. The field reference tables document them in separate sections.

---

## Backward Compatibility

### v0.3 from v0.2 — Additive only, no migration required

v0.3 is fully additive relative to v0.2. The only breaking change is the `brewspec_version` const (`"0.2"` → `"0.3"`). All field additions are optional.

**What changed:**

| Change | Type | Notes |
|--------|------|-------|
| `brewspec_version` const | Breaking | Must be updated from `"0.2"` to `"0.3"` |
| `equipment` object | Addition | Optional; does not affect existing brews |
| `ey` field | Addition | Optional; does not affect existing brews |
| `maxLength` on freeform strings | Tightening | Only breaks files with abnormally long strings (> 100 chars for most fields, > 2000 for `notes`) — unlikely in practice |

**To upgrade a v0.2 file to v0.3:**

1. Change `brewspec_version` from `"0.2"` to `"0.3"`
2. Optionally add `equipment`, `ey`, or any other new fields
3. Validate against the v0.3 schema

No field removals, renames, or structural changes. The upgrade is a version bump plus optional field additions.

### v0.3 from v0.1

v0.1 files require the same migration as v0.2 (structural changes to brew quantities), plus the version bump to `"0.3"`. See the [archived v0.2 spec](./versions/brewspec-v0.2.md) for the full v0.1 → v0.2 migration guide, then apply the v0.2 → v0.3 steps above.

---

## Future Versions

BrewSpec v0.3 is intentionally scoped. Future versions may add:

- **v0.4 candidates:**
  - Date-only `date` format (`YYYY-MM-DD`) — more natural for manual logging; requires coordinated schema + tool update
  - Standardized enumerations for `method` and `grind` (pending real-world usage data from BrewLog CLI)
  - Pour schedules and step-by-step timing
  - Tasting dimensions (SCA-style cupping scores)
  - Extended water chemistry (pH, bicarbonate, mineral breakdown)
  - A `result` object grouping `tds` and `ey` if a third result-type field emerges

---

## Examples

See [`examples/`](./examples/) directory:

**Valid examples:**
- [`valid/pour_over.yaml`](./examples/valid/pour_over.yaml) — Pour over with all optional fields including full coffee metadata, water ppm, tds
- [`valid/pour_over.json`](./examples/valid/pour_over.json) — Same brew in JSON format
- [`valid/immersion_minimal.yaml`](./examples/valid/immersion_minimal.yaml) — Minimal brew (required fields only)
- [`valid/espresso.yaml`](./examples/valid/espresso.yaml) — Espresso with rating, notes, and tds
- [`valid/multi_brew.yaml`](./examples/valid/multi_brew.yaml) — Multiple brews; demonstrates blend with multiple origins
- [`valid/hybrid.yaml`](./examples/valid/hybrid.yaml) — AeroPress hybrid brew with blend coffee metadata
- [`valid/equipment.yaml`](./examples/valid/equipment.yaml) — Full brew with equipment, ey, and all v0.3 fields

**Invalid examples (for testing):**
- [`invalid/missing_version.yaml`](./examples/invalid/missing_version.yaml) — Missing `brewspec_version`
- [`invalid/missing_required_field.yaml`](./examples/invalid/missing_required_field.yaml) — Brew missing `date`
- [`invalid/invalid_type_enum.yaml`](./examples/invalid/invalid_type_enum.yaml) — Invalid `type` value
- [`invalid/rating_out_of_range.yaml`](./examples/invalid/rating_out_of_range.yaml) — Rating > 5
- [`invalid/negative_weight.yaml`](./examples/invalid/negative_weight.yaml) — Negative `dose_g`
- [`invalid/empty_brews_array.yaml`](./examples/invalid/empty_brews_array.yaml) — Empty `brews` array
- [`invalid/v0.1_format.yaml`](./examples/invalid/v0.1_format.yaml) — v0.1 structure with nested `coffee.dose_g`
- [`invalid/v0.2_format.yaml`](./examples/invalid/v0.2_format.yaml) — `brewspec_version: "0.2"` rejected by v0.3 schema
- [`invalid/zero_duration.yaml`](./examples/invalid/zero_duration.yaml) — `duration_s: 0`

---

## License

BrewSpec is open source. The spec and examples are released under the MIT License. See the project repository for full license terms.

---

## Contributing

BrewSpec is an open standard. Contributions are welcome!

BrewSpec repository: https://github.com/coffee-standards/brewspec

- **Propose changes:** Open an issue or pull request in the BrewSpec repository
- **Report problems:** File an issue describing the ambiguity or error in the spec
- **Share usage data:** Help us understand how people use the spec to inform v0.4 design

See [`README.md`](./README.md) for contribution guidelines.
