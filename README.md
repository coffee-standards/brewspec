# BrewSpec

**An open source standard for describing coffee brews.**

BrewSpec repository: https://github.com/coffee-standards/brewspec

BrewSpec is to coffee what BeerXML is to beer: a common data format that makes brew data portable and interoperable across tools. Track your brews in one app, export the data, and import it into another — no vendor lock-in, no proprietary formats.

---

## Why BrewSpec?

The coffee industry lacks an open standard for brew data. Every app, spreadsheet template, and roaster portal invents its own schema, resulting in:
- **Tool builders** reinventing brew data schemas for each project
- **Coffee professionals** unable to migrate data between systems
- **Home brewers** locked into whichever tool they start with

BrewSpec solves this by providing a published JSON Schema and standard file format (YAML/JSON) that any tool can adopt.

---

## Quick Start

### 1. Write a brew file

Create a YAML file describing your brew:

```yaml
# my_brew.yaml
brewspec_version: "0.4"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 20
    water_weight_g: 320
    water_temp_c: 96
    coffee:
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    water:
      ppm: 150
    grind: "medium_fine"
    duration_s: 180
    notes: "Washed filter paper before brewing"
    result:
      tds: 1.38
      tasting_notes: "Bright acidity, slightly under-extracted"
      ratings:
        overall: 4
```

### 2. Validate against the schema

**Python:**
```bash
pip install jsonschema pyyaml
```

```python
import json
import yaml
from jsonschema import Draft202012Validator

schema = json.load(open("brewspec.schema.json", encoding="utf-8"))
validator = Draft202012Validator(schema)

data = yaml.safe_load(open("my_brew.yaml", encoding="utf-8"))
validator.validate(data)
print("Valid!")
```

**JavaScript/Node.js:**
```bash
npm install ajv yaml
```

```javascript
const Ajv = require("ajv");
const YAML = require("yaml");
const fs = require("fs");

const ajv = new Ajv();
const schema = JSON.parse(fs.readFileSync("brewspec.schema.json"));
const validate = ajv.compile(schema);

const data = YAML.parse(fs.readFileSync("my_brew.yaml", "utf8"));
if (validate(data)) {
  console.log("Valid!");
} else {
  console.error(validate.errors);
}
```

**Command-line (ajv-cli):**
```bash
npm install -g ajv-cli
ajv validate -s brewspec.schema.json -d my_brew.yaml
```

### 3. Read the spec

See [`brewspec-v0.4.md`](./brewspec-v0.4.md) for the full field reference, constraints, and design decisions.

---

## Repository Structure

```
├── brewspec.schema.json     # JSON Schema (canonical spec)
├── brewspec-v0.4.md         # Human-readable spec document (current)
├── README.md                # This file
├── LICENSE                  # Apache 2.0
├── NOTICE                   # Copyright attribution
├── examples/
│   ├── valid/               # Valid example files (YAML + JSON)
│   │   ├── pour_over.yaml
│   │   ├── pour_over.json
│   │   ├── immersion_minimal.yaml
│   │   ├── espresso.yaml
│   │   ├── multi_brew.yaml
│   │   ├── hybrid.yaml
│   │   └── equipment.yaml
│   └── invalid/             # Invalid examples (for testing)
│       ├── missing_version.yaml
│       ├── missing_required_field.yaml
│       ├── invalid_type_enum.yaml
│       ├── negative_weight.yaml
│       ├── empty_brews_array.yaml
│       ├── v0.1_format.yaml
│       └── zero_duration.yaml
├── versions/
│   ├── v0.1.md              # Archived spec (v0.1)
│   ├── brewspec-v0.2.md     # Archived spec (v0.2)
│   └── brewspec-v0.3.md     # Archived spec (v0.3)
├── tests/
│   └── test_brewspec_schema.py
└── brewlog/                 # BrewLog CLI (reference implementation)
    ├── pyproject.toml
    ├── src/brewlog/         # Python package
    └── tests/               # Test suite
```

---

## Schema

BrewSpec v0.4 uses **JSON Schema Draft 2020-12**.

- **Schema file:** [`brewspec.schema.json`](./brewspec.schema.json)
- **Version:** 0.4 (stable)
- **Format:** YAML or JSON (both validate against the same schema)

---

## Examples

**Valid examples** demonstrate correct usage:
- [`examples/valid/pour_over.yaml`](./examples/valid/pour_over.yaml) — Pour over with full coffee metadata, water ppm, result object
- [`examples/valid/pour_over.json`](./examples/valid/pour_over.json) — Same brew in JSON format
- [`examples/valid/immersion_minimal.yaml`](./examples/valid/immersion_minimal.yaml) — Minimal brew (required fields only)
- [`examples/valid/espresso.yaml`](./examples/valid/espresso.yaml) — Espresso with result.ratings and tasting_notes
- [`examples/valid/multi_brew.yaml`](./examples/valid/multi_brew.yaml) — Multiple brews; includes blend with multiple origins
- [`examples/valid/hybrid.yaml`](./examples/valid/hybrid.yaml) — AeroPress hybrid brew with blend coffee and water ppm
- [`examples/valid/equipment.yaml`](./examples/valid/equipment.yaml) — Full brew with equipment and all v0.4 result fields

**Invalid examples** demonstrate common validation failures (useful for testing parsers):
- [`examples/invalid/missing_version.yaml`](./examples/invalid/missing_version.yaml)
- [`examples/invalid/missing_required_field.yaml`](./examples/invalid/missing_required_field.yaml)
- [`examples/invalid/invalid_type_enum.yaml`](./examples/invalid/invalid_type_enum.yaml)
- [`examples/invalid/negative_weight.yaml`](./examples/invalid/negative_weight.yaml)
- [`examples/invalid/empty_brews_array.yaml`](./examples/invalid/empty_brews_array.yaml)
- [`examples/invalid/v0.1_format.yaml`](./examples/invalid/v0.1_format.yaml) — v0.1 structure with nested dose_g
- [`examples/invalid/zero_duration.yaml`](./examples/invalid/zero_duration.yaml) — duration_s: 0

---

## Spec Document

The human-readable spec is in [`brewspec-v0.4.md`](./brewspec-v0.4.md). It includes:
- Field reference tables (types, constraints, descriptions, examples)
- Enumeration definitions (brew types, coffee types, grind sizes)
- Validation instructions (Python, JavaScript, CLI) with storage-time guidance
- Design decisions (result object, grind enum, dual-format date, etc.)
- Backward compatibility guide (v0.3 to v0.4 migration, step-by-step)
- Archived specs: [`versions/brewspec-v0.3.md`](./versions/brewspec-v0.3.md), [`versions/brewspec-v0.2.md`](./versions/brewspec-v0.2.md), [`versions/v0.1.md`](./versions/v0.1.md)

---

## Contributing

BrewSpec is an open standard. We welcome contributions!

### How to contribute

1. **Propose changes** — Open an issue or pull request in the BrewSpec repository describing your proposal
2. **Report problems** — File an issue if you find ambiguities, errors, or missing information in the spec
3. **Share usage data** — Help us understand how people use the spec to inform future design

### Contribution guidelines

- **Backward compatibility matters** — Breaking changes require a version bump and a migration guide.
- **Simplicity first** — New fields must justify their existence. Complexity is earned, not assumed.
- **Real usage drives design** — Propose enumerations or new fields only when real usage data shows a clear pattern.
- **Tests prove the spec** — All changes must include test cases (valid and invalid examples).

### Testing your changes

If you modify the schema or add examples, run the test suite:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_brewspec_schema.py -v
```

All tests must pass before changes are accepted.

---

## License

BrewSpec is licensed under the [Apache License 2.0](./LICENSE).

Copyright 2026 Scott Luengen. See [NOTICE](./NOTICE) for details.

---

## BrewLog CLI

**BrewLog** is the reference CLI implementation for BrewSpec — a local command-line tool for logging and tracking coffee brews using the BrewSpec format.

Current version: **0.3.0** (targets BrewSpec v0.4)

### Install

```bash
cd brewlog
pip install -e .
```

### Commands

#### `brewlog add` — Log a new brew

Required fields (date, type, dose, water) are prompted interactively if not supplied as flags. All optional fields can be supplied as flags.

```bash
# Fully interactive
brewlog add

# Non-interactive with flags
brewlog add --date 2026-02-23 --type pour_over --dose 20 --water 320

# With result fields
brewlog add --date 2026-02-23 --type pour_over --dose 20 --water 320 \
  --method "V60" --grind medium_fine --temp 95 --duration 180 \
  --tds 1.38 --ey 21.5 --brix 1.4 \
  --tasting-notes "Bright acidity, floral" \
  --rating-overall 4 --rating-aroma 4 --rating-flavour 5
```

**Flags:**

| Flag | Type | Description |
|---|---|---|
| `--date` | string | Brew date: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` (defaults to today) |
| `--type` | enum | Brew type: `espresso`, `hybrid`, `immersion`, `pour_over` |
| `--dose` | float | Coffee dose in grams (> 0) |
| `--water` | float | Water weight in grams (> 0) |
| `--method` | string | Brewer description, e.g. `"Hario V60"` |
| `--grind` | enum | Grind size: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse` |
| `--temp` | float | Water temperature in Celsius (0–100) |
| `--duration` | int | Brew duration in seconds (> 0) |
| `--notes` | string | Brew process notes (up to 2000 chars) |
| `--tds` | float | TDS percentage (> 0) |
| `--ey` | float | Extraction yield percentage (> 0) |
| `--brix` | float | Degrees Brix (>= 0) |
| `--tasting-notes` | string | Sensory tasting notes — cup impressions (up to 2000 chars) |
| `--rating-overall` | int | Overall impression, 1–5 |
| `--rating-fragrance` | int | Fragrance rating, 1–5 |
| `--rating-aroma` | int | Aroma rating, 1–5 |
| `--rating-flavour` | int | Flavour rating, 1–5 |
| `--rating-aftertaste` | int | Aftertaste rating, 1–5 |
| `--rating-acidity` | int | Acidity rating, 1–5 |
| `--rating-sweetness` | int | Sweetness rating, 1–5 |
| `--rating-mouthfeel` | int | Mouthfeel rating, 1–5 |
| `--roast-date` | string | Coffee roast date (YYYY-MM-DD) |
| `--coffee-type` | enum | `single_origin` or `blend` |
| `--origin` | string | Coffee origin (repeatable: `--origin Ethiopia --origin Colombia`) |
| `--varietal` | string | Coffee varietal (freeform) |
| `--process` | string | Coffee processing method (freeform) |
| `--water-ppm` | float | Water mineral content in ppm (>= 0) |
| `--grinder` | string | Grinder name or description |
| `--brewer` | string | Brewer/dripper name or description |

#### `brewlog list` — List recent brews

Displays a table of recent brews ordered by date descending. Filters are combinable (logical AND) and the limit applies to the filtered result set.

```bash
brewlog list                              # last 20 brews
brewlog list --limit 50                   # last 50 brews
brewlog list --all                        # all brews
brewlog list --type pour_over             # filter by type
brewlog list --since 2026-01-01           # on or after date
brewlog list --until 2026-02-01           # on or before date
brewlog list --since 2026-01-01 --until 2026-02-01  # date range
brewlog list --rating-min 4               # overall rating >= 4
brewlog list --rating-max 3               # overall rating <= 3
brewlog list --rating-min 3 --rating-max 4 --type espresso  # combined
```

**Flags:**

| Flag | Type | Description |
|---|---|---|
| `--limit` | int | Number of brews to show (default: 20) |
| `--all` | flag | Show all brews (overrides `--limit`) |
| `--type` | enum | Filter by brew type: `espresso`, `hybrid`, `immersion`, `pour_over` |
| `--since` | string | Filter brews on or after this date (YYYY-MM-DD) |
| `--until` | string | Filter brews on or before this date (YYYY-MM-DD) |
| `--rating-min` | int | Filter brews with overall rating >= N (1–5) |
| `--rating-max` | int | Filter brews with overall rating <= N (1–5) |

#### `brewlog show` — Show brew details

Displays all stored fields for a brew by ID. Sections with no data (Results, Coffee, Water, Equipment) are omitted.

```bash
brewlog show 3
```

Output includes a Results section (TDS, EY, Brix, tasting notes, ratings dimensions) when result data is present.

#### `brewlog update` — Update an existing brew

Updates optional fields on an existing brew by ID. Omit the ID to update the most recently dated brew. At least one flag must be provided.

```bash
brewlog update 3 --rating-overall 4 --tasting-notes "Bright, floral"
brewlog update --tds 1.40 --ey 22.1   # updates the latest brew
```

Supports all optional flags from `brewlog add` except the required fields (date, type, dose, water).

#### `brewlog delete` — Delete a brew

Deletes a brew by ID with a confirmation prompt. The `--force` flag skips confirmation. ID is required (no default-to-latest behaviour).

```bash
brewlog delete 3           # prompts for confirmation
brewlog delete 3 --force   # skips confirmation
```

#### `brewlog export` — Export to BrewSpec file

Exports all brews to a BrewSpec v0.4 YAML or JSON file. File format is determined by extension (`.yaml`, `.yml`, or `.json`).

```bash
brewlog export my_brews.yaml
brewlog export my_brews.json
```

#### `brewlog import` — Import from BrewSpec file

Imports brews from a BrewSpec file. Requires BrewSpec v0.4 — v0.3 and earlier files are rejected with an actionable error message.

```bash
brewlog import my_brews.yaml
```

### Storage

BrewLog stores brews in a local SQLite database (`~/.brewlog/brews.db`). All input is validated against the BrewSpec v0.4 schema via Pydantic before writing.

See [`brewlog/`](./brewlog/) for the full source code and tests.

---

## Questions?

- Read the spec: [`brewspec-v0.4.md`](./brewspec-v0.4.md)
- Check the examples: [`examples/`](./examples/)
- Open an issue: https://github.com/coffee-standards/brewspec

---

**BrewSpec** — Making coffee data portable, one brew at a time.
