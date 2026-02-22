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

### Install

```bash
cd brewlog
pip install -e .
```

### Usage

```bash
# Add a brew interactively
brewlog add

# List all logged brews
brewlog list

# Show details for brew #3
brewlog show 3

# Export brews to a BrewSpec YAML file
brewlog export my_brews.yaml

# Import brews from a BrewSpec file
brewlog import my_brews.yaml
```

BrewLog stores brews in a local SQLite database and validates all input against the BrewSpec schema.
See [`brewlog/`](./brewlog/) for the full source code and tests.

---

## Questions?

- Read the spec: [`brewspec-v0.4.md`](./brewspec-v0.4.md)
- Check the examples: [`examples/`](./examples/)
- Open an issue: https://github.com/coffee-standards/brewspec

---

**BrewSpec** — Making coffee data portable, one brew at a time.
