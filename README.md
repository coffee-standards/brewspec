# BrewSpec

**An open source standard for describing coffee brews.**

BrewSpec repository: https://github.com/coffee-standards/brewspec

BrewSpec is a common data format that makes brew data portable and interoperable across tools. Track your brews in one app, export the data, and import it into another — no vendor lock-in, no proprietary formats.

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

Create a YAML file describing your brew. Every field inside a brew is optional, so record what you measure:

```yaml
# my_brew.yaml
brewspec_version: "1.2"
brews:
  - date: "2026-10-14"
    brewed_at: "2026-10-14T07:30:00+11:00"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 20
    water_g: 320
    water_temp_c: 96
    grind: "medium_fine"
    duration_s: 180
    process_notes: "Rinsed filter paper before brewing"
    coffee:
      name: "Ethiopia Yirgacheffe"
      roaster: "Onyx"
      roast_date: "2026-10-01"
      roast_level: "light"
      caffeine_level: "regular"
      type: "single_origin"
      origins:
        - country: "Ethiopia"
          varietal: "Heirloom"
    water:
      ppm: 150
    result:
      tds: 1.38
      ey: 21.5
      tasting_notes: "Bright acidity, jasmine, slightly under-extracted"
      ratings:
        overall: 7
```

### 2. Validate against the schema

The schema is published at `https://brewspec.coffee/schema/v1.2.json`, and the same file is [`brewspec.schema.json`](./brewspec.schema.json) in this repository.

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

`water_temp_c` uses `multipleOf: 0.1`, which binary floats get wrong. Parse numbers as `Decimal` before validating; the spec's *Validation* section shows how.

**JavaScript/Node.js:**
```bash
npm install ajv yaml
```

```javascript
const Ajv2020 = require("ajv/dist/2020");
const YAML = require("yaml");
const fs = require("fs");

const ajv = new Ajv2020();
const schema = JSON.parse(fs.readFileSync("brewspec.schema.json", "utf8"));
const validate = ajv.compile(schema);

const data = YAML.parse(fs.readFileSync("my_brew.yaml", "utf8"));
if (validate(data)) {
  console.log("Valid!");
} else {
  console.error(validate.errors);
}
```

The schema is JSON Schema Draft 2020-12, so use Ajv's 2020 build. The default `Ajv` class targets draft-07 and cannot compile it.

**Command-line (ajv-cli):**
```bash
npm install -g ajv-cli
ajv validate --spec=draft2020 -s brewspec.schema.json -d my_brew.yaml
```

### 3. Read the spec

See [`brewspec-v1.2.md`](./brewspec-v1.2.md) for the full field reference, constraints, and design decisions.

---

## What's new in v1.2

BrewSpec 1.2 is an additive release. A valid 1.0 or 1.1 document is valid under 1.2 once `brewspec_version` is changed to `"1.2"`.

- **`brew.brewed_at`**: the instant the brew was made, as an ISO 8601 date-time that must state its offset (`Z` or `±HH:MM`). When it is present, `date` is the brewer's local calendar day.
- **`brew.servings`**: how many times the recipe was made, an integer of at least 1. Absent means 1. `dose_g`, `water_g` and `yield_g` describe one serving.
- **`coffee.caffeine_level`**: `regular`, `decaf`, `half_caf` or `extra`. Absent means not recorded.
- **`coffee.cupping_notes` and `equipment.notes`** no longer have a maximum length.

The spec's *What Changed in v1.2* section explains each change and why.

---

## Repository Structure

```
├── brewspec.schema.json     # JSON Schema: the canonical, machine-readable spec
├── brewspec-v1.2.md         # Human-readable spec document (current)
├── README.md                # This file
├── LICENSE                  # Apache 2.0
├── NOTICE                   # Copyright attribution
├── examples/
│   ├── valid/               # Documents that pass validation (YAML and JSON)
│   └── invalid/             # Documents that fail it, for testing validators
├── versions/                # Archived spec documents for earlier versions
├── tests/                   # Schema and example tests (pytest)
├── site/                    # brewspec.coffee: docs site and published schemas
│   └── public/schema/       # Every published schema, v0.7 to v1.2
└── brewlog/                 # BrewLog CLI (reference implementation)
    ├── pyproject.toml
    ├── src/brewlog/         # Python package, with a bundled copy of the schema
    └── tests/               # Test suite
```

---

## Schema

BrewSpec v1.2 uses **JSON Schema Draft 2020-12**.

- **Schema file:** [`brewspec.schema.json`](./brewspec.schema.json)
- **Published at:** `https://brewspec.coffee/schema/v1.2.json`. Earlier versions stay at `https://brewspec.coffee/schema/v<version>.json`.
- **Version:** 1.2 (stable)
- **Format:** YAML or JSON (both validate against the same schema)

---

## Examples

[`examples/valid/`](./examples/valid/) holds documents that pass validation, and [`examples/invalid/`](./examples/invalid/) holds documents that fail it, which are useful for testing a parser or validator. A few starting points:

- [`examples/valid/pour_over.yaml`](./examples/valid/pour_over.yaml): pour over with full coffee metadata, water ppm and a result object
- [`examples/valid/espresso_full_symmetry.yaml`](./examples/valid/espresso_full_symmetry.yaml): espresso recording both the recipe target and the actual measurement for dose, water, yield and duration
- [`examples/valid/valid_brewed_at.yaml`](./examples/valid/valid_brewed_at.yaml): `brewed_at` with `Z`, positive and negative offsets
- [`examples/valid/valid_servings.yaml`](./examples/valid/valid_servings.yaml): a two-serving brew with per-serving recipe fields
- [`examples/invalid/invalid_brewed_at_no_offset.yaml`](./examples/invalid/invalid_brewed_at_no_offset.yaml): an instant without an offset

The spec's *Examples* section describes every example file.

---

## Spec Document

The human-readable spec is [`brewspec-v1.2.md`](./brewspec-v1.2.md). It includes:
- Field reference tables (types, constraints, descriptions, examples)
- Enumeration definitions (brew types, coffee types, grind sizes, roast levels, water types, caffeine levels)
- What changed in each version since v1.0, with design notes
- Validation guidance, including storage-time validation and decimal parsing
- Backward compatibility and migration steps
- The CVA hedonic scale used by the 1–9 ratings

Archived specs for earlier versions are in [`versions/`](./versions/). The previous version is [`versions/brewspec-v1.1.md`](./versions/brewspec-v1.1.md).

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

If you modify the schema or add examples, run both test suites. The schema is copied in three places (`brewspec.schema.json`, `site/public/schema/v<version>.json` and `brewlog/src/brewlog/brewspec.schema.json`), and the root suite checks that the copies match.

```bash
# Schema and examples
pip install -r requirements.txt
pytest tests/

# BrewLog CLI
pip install -e brewlog
cd brewlog && pytest
```

All tests must pass before changes are accepted.

---

## License

BrewSpec is licensed under the [Apache License 2.0](./LICENSE).

Copyright 2026 Scott Luengen. See [NOTICE](./NOTICE) for details.

---

## BrewLog CLI

**BrewLog** is the reference CLI implementation for BrewSpec — a local command-line tool for logging and tracking coffee brews using the BrewSpec format.

Current version: **1.0.0** (reads and writes BrewSpec v1.2)

### Install

```bash
cd brewlog
pip install -e .
```

### Commands

| Command | Does |
|---|---|
| `brewlog add` | Log a new brew. Prompts for date, type, dose and water if they are not given as flags. |
| `brewlog list` | List recent brews, filtered by type, date range or overall rating. |
| `brewlog show <id>` | Show every stored field for one brew. |
| `brewlog update [<id>]` | Update optional fields on a brew; without an ID, the latest brew. |
| `brewlog delete <id>` | Delete a brew, after confirmation unless `--force` is given. |
| `brewlog search <query>` | Search notes, tasting notes, coffee name and origin data. |
| `brewlog stats` | Print a summary of brew history. |
| `brewlog export <path>` | Export brews to a BrewSpec v1.2 YAML or JSON file, or to CSV. |
| `brewlog import <path>` | Import brews from a BrewSpec v1.2 YAML or JSON file. |

Every command documents its flags under `--help`, for example `brewlog add --help`. Ratings use the 1–9 CVA scale.

```bash
# Log a brew with result fields
brewlog add --date 2026-10-14 --type pour_over --dose 20 --water 320 \
  --method "V60" --grind medium_fine --temp 95 --duration 180 \
  --tds 1.38 --ey 21.5 --tasting-notes "Bright acidity, floral" \
  --rating-overall 7

# Filter the list
brewlog list --since 2026-10-01 --type espresso --rating-min 6

# Round-trip through BrewSpec
brewlog export my_brews.yaml
brewlog import my_brews.yaml
```

`import` accepts only BrewSpec v1.2. A file of any other version is rejected with the steps to migrate it; a v1.0 or v1.1 file needs only its `brewspec_version` changed.

### Storage

BrewLog stores brews in a local SQLite database (`~/.brewlog/brews.db`; `--db` selects another). `add` and `update` validate input before writing. `import` validates the whole file against the bundled BrewSpec v1.2 schema before writing anything, and stores the fields BrewLog tracks. Fields it does not track are dropped on import, among them `brewed_at`, `servings`, `caffeine_level`, `water.type` and `equipment.burr_set`. `export` validates its own output against the same schema before writing the file.

See [`brewlog/`](./brewlog/) for the full source code and tests.

---

## Questions?

- Read the spec: [`brewspec-v1.2.md`](./brewspec-v1.2.md)
- Check the examples: [`examples/`](./examples/)
- Open an issue: https://github.com/coffee-standards/brewspec
- Email us: hello@brewspec.coffee

---

**BrewSpec** — Making coffee data portable, one brew at a time.
