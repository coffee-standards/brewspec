# Product: BrewSpec v0.1

**Status:** Draft
**Priority:** P0 (Critical)
**Author:** product-manager
**Created:** 2026-02-15
**Last Updated:** 2026-02-15

---

## Problem Statement

The coffee industry lacks what the beer industry has with BeerXML: an open, interoperable format for describing coffee brews. Every coffee app, spreadsheet template, and roaster portal invents its own schema, resulting in:

- **Tool builders** reinvent brew data schemas for each project with no standard to build against
- **Coffee professionals** (roasters, baristas, cafe owners) cannot export data from one system and import it into another — vendor lock-in is the default
- **Home brewers** who want to track their brews cannot easily migrate between tools or share recipes in a standard format

This feature defines the BrewSpec v0.1: a minimal, open source standard for describing coffee brews. It provides the foundational data format that any tool can adopt, making brew data portable and interoperable.

## User Stories

- As a **tool builder**, I want a published JSON Schema for coffee brews so that I can validate brew data against a standard instead of inventing my own format.
- As a **tool builder**, I want working example files (valid and invalid) so that I can test my parser implementation without writing test fixtures from scratch.
- As a **coffee professional**, I want a standard brew format so that I can export data from one tool and import it into another without manual reformatting.
- As a **home brewer**, I want a simple, human-readable format so that I can understand and edit my brew logs in a text editor if needed.
- As a **tool builder**, I want a spec document that defines each field, its type, constraints, and purpose so that I can implement the standard correctly.

## Acceptance Criteria

- **AC-1**: A JSON Schema file (`brewspec/spec/brewspec.schema.json`) defines the BrewSpec v0.1 format with all required and optional fields, types, constraints, and enumerations per the scope below.
- **AC-2**: The schema validates that `brewspec_version` is required and must be the string `"0.1"`.
- **AC-3**: The schema validates that `brews` is required and must be an array (minimum 1 element).
- **AC-4**: The schema validates that each brew has required fields: `date` (ISO 8601 string), `type` (enum: `immersion`, `pour_over`, `espresso`, `hybrid`), `coffee.dose_g` (number > 0), `water.weight_g` (number > 0).
- **AC-5**: The schema validates that each brew can have optional fields: `method` (string), `water.volume_ml` (number > 0), `water.temp_c` (number 0-100), `grind` (string), `duration_s` (number >= 0), `rating` (integer 1-5), `notes` (string).
- **AC-6**: The schema rejects brews with `rating` outside the 1-5 integer range.
- **AC-7**: The schema rejects brews with negative values for `coffee.dose_g`, `water.weight_g`, `water.volume_ml`, or `duration_s`.
- **AC-8**: The schema rejects brews with `type` values not in the enumeration (`immersion`, `pour_over`, `espresso`, `hybrid`).
- **AC-9**: At least 3 valid example files exist in `brewspec/spec/examples/valid/` covering different brew types (e.g., `pour_over.yaml`, `immersion.yaml`, `espresso.yaml`).
- **AC-10**: At least 3 invalid example files exist in `brewspec/spec/examples/invalid/` demonstrating common validation failures (e.g., `missing_required_field.yaml`, `invalid_type_enum.yaml`, `rating_out_of_range.yaml`).
- **AC-11**: A test suite validates the JSON Schema against all example files: valid examples pass, invalid examples fail with expected error messages.
- **AC-12**: A spec document (`brewspec/spec/brewspec-v0.1.md`) defines each field with its name, type, constraints, purpose, and examples.
- **AC-13**: The spec document includes a section explaining the v0.1 design decisions: freeform method/grind, array-only format, metric units, ISO 8601 timestamps, lowercase snake_case.
- **AC-14**: A README (`brewspec/spec/README.md`) describes the BrewSpec project, how to validate files against the schema, and how to contribute.
- **AC-15**: The JSON Schema supports both YAML and JSON file formats (validation is format-agnostic once parsed).

## Scope

### In Scope

- JSON Schema defining the BrewSpec v0.1 format
- Required fields: `brewspec_version`, `brews[].date`, `brews[].type`, `brews[].coffee.dose_g`, `brews[].water.weight_g`
- Optional fields: `method`, `water.volume_ml`, `water.temp_c`, `grind`, `duration_s`, `rating`, `notes`
- Enumeration for `type`: `immersion`, `pour_over`, `espresso`, `hybrid`
- Freeform text for `method` and `grind` (no standardized enumerations in v0.1)
- Integer rating scale 1-5
- Validation constraints: positive numbers for weights/volumes, 0-100 for temperature, non-negative for duration, 1-5 for rating
- Array-only format: all brew files contain `brews: [...]` with minimum 1 element
- Metric units: grams for coffee/water weight, milliliters for volume, celsius for temperature, seconds for duration
- ISO 8601 timestamps in UTC for `date`
- Lowercase snake_case for field names
- Valid and invalid example files for testing
- Test suite that validates schema against examples
- Spec document with field definitions
- README with validation instructions and contribution guidelines

### Out of Scope

v0.1 intentionally defers the following to v0.2 or later based on real usage data:

- **Coffee metadata** (origin, roaster, roast date, variety, processing method) — deferred to v0.2 to keep v0.1 minimal and focused on brew variables
- **Equipment details** (grinder model, grind setting as a number, brewer model) — deferred to v0.2 to avoid premature standardization
- **Standardized method/grind enumerations** — v0.1 uses freeform text; v0.2 will analyze real usage to propose enumerations if patterns emerge
- **Water chemistry** (TDS, pH, mineral content) — advanced users only; deferred to v0.2+
- **Pour schedule / step-by-step timing** (e.g., bloom 30s, pour 1 100g, pour 2 120g) — complex feature; deferred to v0.2+
- **Tasting dimensions / cupping scores** (SCA-style acidity, sweetness, body, etc.) — deferred to v0.2 pending user demand
- **Multi-brew sessions / flight comparisons** (linking multiple brews for side-by-side tasting) — deferred to v0.2+
- **Brew extraction metrics** (TDS, extraction percentage, strength) — advanced; deferred to v0.2+
- **Validation beyond schema** (e.g., warning if water temp is unusually low, or dose is outside typical ranges) — deferred; schema only enforces hard constraints
- **Versioning strategy for v0.2+** — deferred; v0.1 establishes the baseline

## Design Notes

### File Format Decisions

**Why array-only format?**
- A file always contains `brews: [...]` (array), never a single bare object
- A single brew is represented as an array with one element: `brews: [{ date: ..., type: ... }]`
- Rationale: One format means simpler parsers, simpler tests, fewer edge cases for tool builders. No branching logic for "is this a single brew or a list?"
- Trade-off: Slightly more verbose for single-brew files, but consistency is worth it

**Why freeform text for method and grind?**
- Users describe their equipment and grind in their own words: "Hario V60", "v60", "French press", "setting 15 on Comandante", "medium-fine", "slightly coarser than table salt"
- Rationale: Grind perception is relative to equipment. Method naming is inconsistent across brands. Standardizing prematurely adds false precision and frustrates users who don't fit the categories.
- v0.2 plan: Analyze real v0.1 usage data. If clear patterns emerge (e.g., 80% of users write "V60" or "Hario V60"), propose optional enumerations with freeform fallback.

**Why metric units only?**
- Coffee and water weight in grams (canonical), water volume in milliliters (optional), temperature in celsius, duration in seconds
- Rationale: Metric is the global standard in specialty coffee. Modern brewing practice measures water by weight (grams), not volume. US customary units (ounces, fahrenheit) can be converted by tools if needed, but the spec is metric-native.

**Why ISO 8601 timestamps in UTC?**
- `date` field uses ISO 8601 format: `2026-02-15T08:30:00Z`
- Rationale: Unambiguous, sortable, machine-parseable, universally supported. Tools can display in local timezone, but storage is UTC.

**Why snake_case?**
- All field names use lowercase snake_case: `dose_g`, `water.weight_g`, `duration_s`
- Rationale: Consistent with Python conventions (project is Python-first). Easier to read than camelCase in YAML. JSON Schema standard uses snake_case for keywords.

**Why rating 1-5 instead of 0-10 or 0-100?**
- Integer scale, 1 = poor, 5 = excellent
- Rationale: Simple, familiar (5-star rating), reduces decision paralysis. Finer granularity (0-100) adds cognitive load without clear benefit for home brewers. Rating is optional — power users can omit it or use `notes` for detailed tasting notes.

### Data Structure for Architect

```yaml
brewspec_version: "0.1"  # required, string literal "0.1"
brews:  # required, array, min 1 element
  - date: "2026-02-15T08:30:00Z"  # required, ISO 8601 string
    type: "pour_over"  # required, enum: immersion | pour_over | espresso | hybrid
    method: "Hario V60"  # optional, freeform string
    coffee:  # required object
      dose_g: 20  # required, number > 0
    water:  # required object
      weight_g: 320  # required, number > 0
      volume_ml: 320  # optional, number > 0
      temp_c: 96  # optional, number 0-100
    grind: "medium-fine"  # optional, freeform string
    duration_s: 180  # optional, number >= 0
    rating: 4  # optional, integer 1-5
    notes: "Bright acidity, slightly under-extracted"  # optional, string
```

### JSON Schema Validation Strategy for Architect

- Use JSON Schema Draft 2020-12 or later (widely supported, stable)
- Define `brewspec_version` as `const: "0.1"` (enforces exact string match)
- Define `type` as `enum: ["immersion", "pour_over", "espresso", "hybrid"]`
- Use `required: ["date", "type", "coffee", "water"]` at brew level
- Use `required: ["dose_g"]` for `coffee` object
- Use `required: ["weight_g"]` for `water` object
- Use `minimum: 0.001` (exclusive of zero) for positive number fields (dose, weight, volume)
- Use `minimum: 0, maximum: 100` for temperature
- Use `minimum: 0` for duration (zero is valid for instant methods)
- Use `minimum: 1, maximum: 5, type: "integer"` for rating
- Use `minItems: 1` for `brews` array (at least one brew required)
- Include descriptive error messages in schema where possible (JSON Schema supports `description` and `examples`)

### Test Suite Requirements for Architect

- Python test using `jsonschema` library (or equivalent)
- Test discovers all files in `brewspec/spec/examples/valid/` and `brewspec/spec/examples/invalid/`
- For each valid example: assert schema validation passes
- For each invalid example: assert schema validation fails
- Test should output which file failed and why (helpful for debugging)
- Test should support both YAML and JSON files (parse with `pyyaml` and `json`, validate as dict)

### Example Files to Include

**Valid examples:**
- `brewspec/spec/examples/valid/pour_over.yaml` — pour over with all optional fields
- `brewspec/spec/examples/valid/immersion_minimal.yaml` — French press with only required fields
- `brewspec/spec/examples/valid/espresso.yaml` — espresso with rating and notes
- `brewspec/spec/examples/valid/multi_brew.yaml` — file with 3 brews in the array

**Invalid examples:**
- `brewspec/spec/examples/invalid/missing_brewspec_version.yaml` — missing top-level `brewspec_version`
- `brewspec/spec/examples/invalid/missing_required_brew_field.yaml` — brew missing `date` or `type`
- `brewspec/spec/examples/invalid/invalid_type_enum.yaml` — `type: "drip"` (not in enum)
- `brewspec/spec/examples/invalid/rating_out_of_range.yaml` — `rating: 6` (exceeds max 5)
- `brewspec/spec/examples/invalid/negative_dose.yaml` — `dose_g: -10`
- `brewspec/spec/examples/invalid/empty_brews_array.yaml` — `brews: []` (violates minItems: 1)

## Security Requirements

**Data Sensitivity:**
- Brew logs are personal data (user preferences, habits, location-implied by timestamps)
- No PII is collected (names, emails, addresses) in the spec itself, but tools using the spec may link brews to user accounts
- Spec files may contain freeform `notes` field — users could write sensitive info (e.g., "brewed at [friend's address]")
- Tools should treat brew files as user-generated content and apply appropriate access controls

**Input Validation:**
- All fields must be validated against the JSON Schema before storage or processing
- Freeform text fields (`method`, `grind`, `notes`) must not be executed as code — treat as plain text only
- Numeric fields must be validated for type and range (schema enforces this)
- ISO 8601 date parsing must reject malformed dates
- File size limits should be enforced by tools (e.g., reject files > 10MB to prevent DoS via large arrays)

**File I/O Considerations:**
- Import feature (in future BrewLog CLI) will read user-provided YAML/JSON files — must validate before parsing to prevent injection attacks
- YAML parsing libraries can execute code if not configured safely (e.g., PyYAML's `yaml.load()` without `Loader=SafeLoader`)
- Architect must specify safe YAML parsing in design (use `yaml.safe_load()` in Python)
- Export feature writes files to user-specified paths — must validate paths to prevent directory traversal attacks (e.g., reject paths containing `..`)

**Schema Validation as Security Layer:**
- The JSON Schema is the first line of defense against malformed or malicious input
- Tools must reject files that fail schema validation before processing
- Schema must enforce hard constraints (type, range, required fields) but not business logic (e.g., "is this a reasonable dose for espresso?")

**No Secrets in Spec:**
- The spec itself contains no authentication, API keys, or credentials
- Tools that sync brew data to cloud services must handle auth separately (out of scope for v0.1)

## Dependencies

**Upstream:**
- None — this is the foundation feature for the entire BrewSpec ecosystem

**Downstream:**
- All other features depend on this spec:
  - BrewLog CLI (import, export, storage schema)
  - Future web UI (data model)
  - Third-party tools (interoperability)

**External:**
- JSON Schema specification (Draft 2020-12 or later) — the standard we're building against
- ISO 8601 standard for timestamps — referenced for date format
- YAML 1.2 and JSON standards — the file formats the spec supports

## Success Metrics

Tied to `specs/strategy.md` success metrics for BrewSpec:

- **Usability**: Someone outside the project can validate a brew file against the schema without prior knowledge (proven by documentation and examples)
- **Completeness**: At least 3 valid example files covering different brew methods (pour over, immersion, espresso)
- **Correctness**: JSON Schema passes validation against all valid examples and correctly rejects all invalid examples
- **Clarity**: Spec document is comprehensible to a developer with no coffee knowledge (field definitions are explicit)
- **Adoption readiness**: A tool builder can implement an BrewSpec parser/generator from the spec and examples alone (proven by the BrewLog CLI implementation in next feature)

**Pass criteria:**
- All acceptance criteria (AC-1 through AC-15) met
- Test suite runs without failures
- Reviewer confirms spec document is clear and complete
- JSON Schema validates as valid JSON Schema (meta-validation)

## Open Questions

- [x] **Q: Should `date` support timezone offsets or require UTC?**
  - Decision: Require UTC (ISO 8601 with `Z` suffix). Tools can convert from local time, but storage is UTC for consistency.
- [x] **Q: Should `grind` be an enum or freeform?**
  - Decision: Freeform for v0.1. Analyze usage data in v0.2 to propose standardized options if patterns emerge.
- [x] **Q: Should `method` be an enum or freeform?**
  - Decision: Freeform for v0.1. Same rationale as grind — too many variations, premature standardization hurts adoption.
- [x] **Q: Should rating be required or optional?**
  - Decision: Optional. Many users won't rate every brew. Requiring it adds friction.
- [x] **Q: Should water weight or volume be required?**
  - Decision: Weight (`water.weight_g`) is required. Volume (`water.volume_ml`) is optional. Modern practice uses weight as canonical.
