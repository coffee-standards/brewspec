# BrewSpec

**An open source standard for describing coffee brews.**

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
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    method: "Hario V60"
    coffee:
      dose_g: 20
    water:
      weight_g: 320
      temp_c: 96
    grind: "medium-fine"
    duration_s: 180
    rating: 4
    notes: "Bright acidity, slightly under-extracted"
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

See [`brewspec-v0.1.md`](./brewspec-v0.1.md) for the full field reference, constraints, and design decisions.

---

## Repository Structure

```
├── brewspec.schema.json     # JSON Schema (canonical spec)
├── brewspec-v0.1.md         # Human-readable spec document
├── README.md                # This file
├── LICENSE                  # Apache 2.0
├── NOTICE                   # Copyright attribution
├── examples/
│   ├── valid/               # Valid example files (YAML + JSON)
│   │   ├── pour_over.yaml
│   │   ├── pour_over.json
│   │   ├── immersion_minimal.yaml
│   │   ├── espresso.yaml
│   │   └── multi_brew.yaml
│   └── invalid/             # Invalid examples (for testing)
│       ├── missing_version.yaml
│       ├── missing_required_field.yaml
│       ├── invalid_type_enum.yaml
│       ├── rating_out_of_range.yaml
│       ├── negative_weight.yaml
│       └── empty_brews_array.yaml
└── tests/
    └── test_brewspec_schema.py
```

---

## Schema

BrewSpec v0.1 uses **JSON Schema Draft 2020-12**.

- **Schema file:** [`brewspec.schema.json`](./brewspec.schema.json)
- **Version:** 0.1 (stable)
- **Format:** YAML or JSON (both validate against the same schema)

---

## Examples

**Valid examples** demonstrate correct usage:
- [`examples/valid/pour_over.yaml`](./examples/valid/pour_over.yaml) — Pour over with all optional fields
- [`examples/valid/pour_over.json`](./examples/valid/pour_over.json) — Same brew in JSON format
- [`examples/valid/immersion_minimal.yaml`](./examples/valid/immersion_minimal.yaml) — Minimal brew (required fields only)
- [`examples/valid/espresso.yaml`](./examples/valid/espresso.yaml) — Espresso with rating and notes
- [`examples/valid/multi_brew.yaml`](./examples/valid/multi_brew.yaml) — Multiple brews in one file

**Invalid examples** demonstrate common validation failures (useful for testing parsers):
- [`examples/invalid/missing_version.yaml`](./examples/invalid/missing_version.yaml)
- [`examples/invalid/missing_required_field.yaml`](./examples/invalid/missing_required_field.yaml)
- [`examples/invalid/invalid_type_enum.yaml`](./examples/invalid/invalid_type_enum.yaml)
- [`examples/invalid/rating_out_of_range.yaml`](./examples/invalid/rating_out_of_range.yaml)
- [`examples/invalid/negative_weight.yaml`](./examples/invalid/negative_weight.yaml)
- [`examples/invalid/empty_brews_array.yaml`](./examples/invalid/empty_brews_array.yaml)

---

## Spec Document

The human-readable spec is in [`brewspec-v0.1.md`](./brewspec-v0.1.md). It includes:
- Field reference table (types, constraints, descriptions, examples)
- Enumeration definitions (brew types)
- Validation instructions (Python, JavaScript, CLI)
- Design decisions (why array-only format, why freeform method/grind, etc.)
- Future version roadmap

---

## Contributing

BrewSpec is an open standard. We welcome contributions!

### How to contribute

1. **Propose changes** — Open an issue or pull request in the BrewSpec repository describing your proposal
2. **Report problems** — File an issue if you find ambiguities, errors, or missing information in the spec
3. **Share usage data** — Help us understand how people use the spec to inform v0.2 design

### Contribution guidelines

- **Backward compatibility matters** — v0.2+ must support v0.1 files. Breaking changes require a major version bump.
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

## Related Projects

- **BrewLog CLI** — A local command-line tool for tracking brews using the BrewSpec format (coming soon)

---

## Questions?

- Read the spec: [`brewspec-v0.1.md`](./brewspec-v0.1.md)
- Check the examples: [`examples/`](./examples/)
- Open an issue in the BrewSpec repository

---

**BrewSpec** — Making coffee data portable, one brew at a time.
