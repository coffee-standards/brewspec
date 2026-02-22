# BrewSpec v0.1

**Status:** Stable
**Version:** 0.1
**Last Updated:** 2026-02-15

---

## Overview

BrewSpec is an open source standard for describing coffee brews. Like BeerXML for beer, BrewSpec provides a common data format that any tool can adopt, making brew data portable and interoperable across applications.

Version 0.1 is the minimal viable spec: it captures the essential brew variables (coffee dose, water weight, brew method, timing) with maximum flexibility and minimum complexity.

### Mission

Make the coffee supply chain more sustainable for everyone by enabling open, interoperable brew data.

### Scope

BrewSpec v0.1 defines:
- A JSON Schema for validation
- Required and optional fields for describing a brew
- Constraints on field types and values
- A standard file format (YAML or JSON)

What v0.1 defers to future versions:
- Coffee metadata (origin, roaster, roast date)
- Equipment details (grinder model, numeric grind settings)
- Water chemistry (TDS, pH, minerals)
- Pour schedules and step-by-step timing
- Tasting dimensions (cupping scores, flavor notes taxonomy)
- Extraction metrics (TDS, extraction percentage)

---

## File Format

BrewSpec files use **YAML** or **JSON** format:
- UTF-8 encoding
- File extensions: `.yaml`, `.yml`, or `.json`
- Both formats validate against the same JSON Schema

### Array-Only Format

All BrewSpec files contain a `brews` array with minimum 1 element:

```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
```

Even a single brew is represented as an array with one element. This simplifies parsers and eliminates branching logic.

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | **Required** | Must be `"0.1"` | The BrewSpec version |
| `brews` | array | **Required** | Minimum 1 element | Array of brew objects |

### Brew Object

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | **Required** | ISO 8601 UTC: `YYYY-MM-DDTHH:MM:SSZ` | Brew timestamp | `"2026-02-15T08:30:00Z"` |
| `type` | string | **Required** | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `method` | string | Optional | Min length 1 | Freeform brewer description | `"Hario V60"`, `"French press"`, `"AeroPress inverted"` |
| `coffee` | object | **Required** | See Coffee Object | Coffee parameters | |
| `water` | object | **Required** | See Water Object | Water parameters | |
| `grind` | string | Optional | Min length 1 | Freeform grind description | `"medium-fine"`, `"setting 15 on Comandante"`, `"slightly coarser than table salt"` |
| `duration_s` | number | Optional | >= 0 | Brew duration in seconds. Zero is valid for instant methods. | `180`, `28`, `0` |
| `rating` | integer | Optional | 1-5 inclusive | Brew rating. 1 = poor, 5 = excellent. | `4` |
| `notes` | string | Optional | Min length 1 | Freeform tasting or session notes | `"Bright acidity, slightly under-extracted"` |

### Coffee Object

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `dose_g` | number | **Required** | > 0 (exclusive) | Coffee dose in grams |

### Water Object

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `weight_g` | number | **Required** | > 0 (exclusive) | Water weight in grams |
| `volume_ml` | number | Optional | > 0 (exclusive) | Water volume in milliliters |
| `temp_c` | number | Optional | 0-100 inclusive | Water temperature in celsius |

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

**v0.2 plan:** Analyze real v0.1 usage data. If clear patterns emerge (e.g., 80% of users write "V60" or "Hario V60"), propose optional enumerations with freeform fallback.

### Why metric units only?

**Decision:** Coffee and water weight in grams, volume in milliliters, temperature in celsius, duration in seconds.

**Rationale:** Metric is the global standard in specialty coffee. Modern brewing practice measures water by weight (grams), not volume. US customary units can be converted by tools if needed, but the spec is metric-native.

### Why ISO 8601 timestamps in UTC?

**Decision:** `date` field uses strict format `YYYY-MM-DDTHH:MM:SSZ` (UTC only).

**Rationale:** Unambiguous, sortable, machine-parseable, universally supported. Tools can display in local timezone, but storage is UTC.

### Why snake_case?

**Decision:** All field names use lowercase snake_case: `dose_g`, `water.weight_g`, `duration_s`.

**Rationale:**
- Consistent with Python conventions (BrewSpec reference implementation is Python-first)
- Easier to read than camelCase in YAML
- JSON Schema standard uses snake_case for keywords

### Why rating 1-5 instead of 0-10 or 0-100?

**Decision:** Integer scale, 1 = poor, 5 = excellent.

**Rationale:** Simple, familiar (5-star rating), reduces decision paralysis. Finer granularity (0-100) adds cognitive load without clear benefit for home brewers. Rating is optional — power users can omit it or use `notes` for detailed tasting feedback.

### Why require water weight but not volume?

**Decision:** `water.weight_g` is required. `water.volume_ml` is optional.

**Rationale:** Modern brewing practice uses weight as the canonical measurement (scales are more accurate than volumetric measures). Volume can be derived or recorded optionally.

### Why minimum duration is 0, not > 0?

**Decision:** `duration_s` can be 0.

**Rationale:** Some methods (instant coffee) may have effectively zero brew time. Let users decide.

---

## Future Versions

BrewSpec v0.1 is intentionally minimal. Future versions may add:

- **v0.2 candidates:**
  - Coffee metadata (origin, roaster, roast date, variety, processing method)
  - Optional standardized enumerations for method/grind (based on v0.1 usage patterns)
  - Equipment details (grinder model, grind setting as number)
  - Water chemistry (TDS, pH)
  - Pour schedules (step-by-step timing)
  - Tasting dimensions (SCA-style cupping scores)
  - Extraction metrics (TDS, extraction percentage)

**Backward compatibility promise:** v0.2+ will support v0.1 files. Parsers should validate `brewspec_version` and handle each version appropriately.

---

## Examples

See [`examples/`](./examples/) directory:

**Valid examples:**
- [`valid/pour_over.yaml`](./examples/valid/pour_over.yaml) — Pour over with all optional fields
- [`valid/pour_over.json`](./examples/valid/pour_over.json) — Same brew in JSON format
- [`valid/immersion_minimal.yaml`](./examples/valid/immersion_minimal.yaml) — Minimal brew (required fields only)
- [`valid/espresso.yaml`](./examples/valid/espresso.yaml) — Espresso with rating and notes
- [`valid/multi_brew.yaml`](./examples/valid/multi_brew.yaml) — Multiple brews in one file

**Invalid examples (for testing):**
- [`invalid/missing_version.yaml`](./examples/invalid/missing_version.yaml) — Missing `brewspec_version`
- [`invalid/missing_required_field.yaml`](./examples/invalid/missing_required_field.yaml) — Brew missing `date`
- [`invalid/invalid_type_enum.yaml`](./examples/invalid/invalid_type_enum.yaml) — Invalid `type` value
- [`invalid/rating_out_of_range.yaml`](./examples/invalid/rating_out_of_range.yaml) — Rating > 5
- [`invalid/negative_weight.yaml`](./examples/invalid/negative_weight.yaml) — Negative `dose_g`
- [`invalid/empty_brews_array.yaml`](./examples/invalid/empty_brews_array.yaml) — Empty `brews` array

---

## License

BrewSpec is open source. The spec and examples are released under the MIT License. See the project repository for full license terms.

---

## Contributing

BrewSpec is an open standard. Contributions are welcome!

- **Propose changes:** Open an issue or pull request in the BrewSpec repository
- **Report problems:** File an issue describing the ambiguity or error in the spec
- **Share usage data:** Help us understand how people use the spec to inform v0.2 design

See [`README.md`](./README.md) for contribution guidelines.
