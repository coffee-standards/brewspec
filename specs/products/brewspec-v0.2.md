# Product: BrewSpec v0.2

**Status:** Ready
**Priority:** P2 (Medium)
**Author:** product-manager
**Created:** 2026-02-18
**Last Updated:** 2026-02-18

---

## Problem Statement

BrewSpec v0.1 shipped a minimal, working brew data format — enough to validate the standard and begin building tooling against it. Real usage and review feedback surfaced several issues that must be corrected before adoption grows, and a small set of high-value additions that belong in the spec now while the cost of a breaking change is still low.

Three categories of work make up v0.2:

1. **Carry-forward fixes** from the v0.1 review: documentation correctness issues (encoding in code examples, parametrized test IDs, missing hybrid example, missing repository URL) that should have been in v0.1.

2. **Schema corrections**: the `duration_s` field incorrectly allows zero, which is not a valid brew time for any method. The `coffee` and `water` objects conflate ingredient identity with brew-specific quantities, producing a model that becomes increasingly incoherent as coffee metadata is added. Both are corrected in v0.2.

3. **Additive enhancements**: coffee metadata fields (what coffee was used), water mineral content (`ppm`), and a brew result field (`tds`) that tool builders and coffee professionals have asked for.

The structural change to `coffee` and `water` is a breaking change from v0.1. It is deliberately made in v0.2 while adoption is near-zero and the BrewLog CLI has not yet shipped. Deferring it would entrench a confusing data model and require a more costly fix later.

Target personas:
- **Tool builders** — need a correct, stable schema to build against; the restructured model is easier to implement correctly
- **Home brewers** — benefit from coffee metadata so they can record which bag they used
- **Coffee professionals** — benefit from `ppm` and `tds` for water profiling and extraction tracking

---

## User Stories

- As a **tool builder**, I want the `coffee` object to describe the coffee ingredient (origin, roast, variety) separately from how much coffee was used in a brew, so that my data model reflects the correct relationship between a coffee and its brews.
- As a **tool builder**, I want a valid hybrid brew example so that I can test my AeroPress and Clever Dripper implementations against a real spec example.
- As a **tool builder**, I want a repository URL in the spec and README so that I can link to the canonical source when building against it.
- As a **home brewer**, I want to record coffee metadata (roast date, origin, varietal, process, and whether it is a blend or single origin) in my brew files so that I can remember which coffee I used.
- As a **home brewer**, I want brew duration to require a positive value so that a recording error (duration of zero) is caught at validation rather than stored silently.
- As a **coffee professional**, I want to record water mineral content (`ppm`) alongside my brew so that I can track how water quality affects outcomes.
- As a **coffee professional**, I want to record the TDS reading (`tds`) of the finished brew so that I can track extraction results alongside my brew parameters.
- As a **home brewer**, I want the Python validation code examples in the spec to use `encoding='utf-8'` so that the examples work correctly on all platforms.

---

## Acceptance Criteria

### Carry-Forward Fixes

- **AC-1**: A valid hybrid brew example file exists at `examples/valid/hybrid.yaml` and passes schema validation. The example uses brew `type: "hybrid"` and includes a realistic AeroPress brew (e.g., dose, water weight, temp, duration, method, rating, notes).
- **AC-2**: All Python code examples in `brewspec-v0.2.md` that call `open()` include `encoding='utf-8'` (e.g., `open("brewspec.schema.json", encoding="utf-8")`).
- **AC-3**: Both `pytest.mark.parametrize` decorators in the test suite (for valid and invalid examples) include `ids=lambda f: f.name`, so that test output identifies failing files by filename rather than index.
- **AC-4**: `brewspec-v0.2.md` and `README.md` both include the BrewSpec GitHub repository URL (e.g., `https://github.com/coffee-standards/brewspec`) in a visible location (Contributing section or header).

### Schema Version Bump

- **AC-5**: The JSON Schema file is updated so that `brewspec_version` validates against `const: "0.2"`. Files declaring `brewspec_version: "0.1"` are rejected by the v0.2 schema.
- **AC-6**: The schema `$id` is updated to the GitHub raw URL: `https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json`.

### Schema Restructure (Breaking Change from v0.1)

- **AC-7**: The brew object no longer contains a `coffee` object with `dose_g` inside it. Instead, `dose_g` is a required top-level field on the brew object (`number`, `exclusiveMinimum: 0`).
- **AC-8**: The brew object no longer contains a `water` object with `weight_g`, `volume_ml`, and `temp_c` inside it. Instead:
  - `water_weight_g` is a required top-level field on the brew object (`number`, `exclusiveMinimum: 0`)
  - `water_volume_ml` is an optional top-level field on the brew object (`number`, `exclusiveMinimum: 0`)
  - `water_temp_c` is an optional top-level field on the brew object (`number`, `minimum: 0`, `maximum: 100`)
- **AC-9**: The `coffee` object is now an optional field on the brew object (not required). When present, it may contain any combination of the coffee metadata fields defined in AC-11. It may be omitted entirely for brews where the user does not record coffee details.
- **AC-10**: The `water` object is now an optional field on the brew object (not required). When present, it may contain only `ppm` as defined in AC-12. It may be omitted entirely.
- **AC-11**: The `coffee` object, when present, accepts the following optional fields and no others (`additionalProperties: false`):
  - `roast_date`: string matching pattern `^\d{4}-\d{2}-\d{2}$` (plain date, `YYYY-MM-DD`). No time component.
  - `type`: string enum `["single_origin", "blend"]`.
  - `origin`: array of strings, `minItems: 1`, each item `minLength: 1`. Supports multiple entries for blends.
  - `varietal`: string, `minLength: 1`. Freeform.
  - `process`: string, `minLength: 1`. Freeform (e.g., `"Washed"`, `"Natural"`, `"Honey"`).
- **AC-12**: The `water` object, when present, accepts only `ppm` (`number`, `minimum: 0`) and no other fields (`additionalProperties: false`).
- **AC-13**: A v0.1-format file (one that uses `coffee.dose_g` and `water.weight_g` as nested fields) fails validation against the v0.2 schema. An invalid example demonstrating this exists at `examples/invalid/v0.1_format.yaml`.

### duration_s Correction

- **AC-14**: The `duration_s` field constraint is changed from `minimum: 0` to `exclusiveMinimum: 0`. A file with `duration_s: 0` fails validation. A file with `duration_s: 1` passes.

### New Fields: tds

- **AC-15**: The brew object accepts an optional `tds` field (`number`, `exclusiveMinimum: 0`). When present, it represents the total dissolved solids percentage of the finished brew (e.g., `1.38` for filter coffee, `8.5` for espresso). No maximum constraint is imposed by the schema.

### Examples Updated for v0.2

- **AC-16**: All existing valid example files are updated to use `brewspec_version: "0.2"` and the v0.2 flat field structure (`dose_g` and `water_weight_g` at the brew level, `coffee` and `water` objects containing only their respective metadata and `ppm`).
- **AC-17**: At least one valid example includes the `coffee` object with multiple metadata fields populated (e.g., `pour_over.yaml` includes `roast_date`, `type`, `origin`, `varietal`, `process`).
- **AC-18**: At least one valid example includes a blend with multiple `origin` entries (e.g., `origin: ["Ethiopia", "Colombia"]`).
- **AC-19**: At least one valid example includes `water.ppm` and `tds`.
- **AC-20**: At least one valid example includes the `coffee` object omitted entirely (to demonstrate that it is optional).
- **AC-21**: The invalid examples directory includes `v0.1_format.yaml` per AC-13, plus an example demonstrating `duration_s: 0` rejection.

### Spec Document (brewspec-v0.2.md)

- **AC-22**: `brewspec-v0.2.md` replaces `brewspec-v0.1.md` as the canonical spec document. It contains a complete, updated field reference covering all top-level brew fields, the `coffee` object, and the `water` object in their v0.2 structure.
- **AC-23**: `brewspec-v0.2.md` contains a "Backward Compatibility" section that explains: v0.2 is a breaking change from v0.1; v0.1 files are valid against the v0.1 schema only; tools should check `brewspec_version` to select the appropriate schema version; a migration guide shows the field renames (`coffee.dose_g` -> `dose_g`, `water.weight_g` -> `water_weight_g`, etc.).
- **AC-24**: `brewspec-v0.2.md` contains a "Design Decisions" section that documents the rationale for: the object model restructure (ingredient identity vs. brew quantity), the `water_*` prefixed naming convention, plain date format for `roast_date`, `tds` as a flat brew-level field (not nested in a `result` object), and the `duration_s` correction.

### Test Suite

- **AC-25**: The test suite is updated to validate all v0.2 example files. New parametrized tests cover:
  - `duration_s: 0` is rejected
  - `duration_s: 1` is accepted
  - `coffee.origin` with multiple entries is accepted
  - A file omitting the `coffee` object entirely is accepted
  - A file omitting the `water` object entirely is accepted
  - `tds` with a valid value (e.g., `1.38`) is accepted
  - A v0.1-format file (nested `coffee.dose_g`) is rejected by the v0.2 schema

---

## Scope

### In Scope

- Carry-forward fixes: hybrid example, encoding in code samples, parametrize test IDs, repository URL
- Schema version bump: `brewspec_version` const to `"0.2"`, `$id` to GitHub raw URL
- Schema restructure: `dose_g` to brew level; `water_weight_g`, `water_volume_ml`, `water_temp_c` to brew level as prefixed fields; `coffee` object becomes optional ingredient descriptor; `water` object becomes optional ingredient descriptor
- Coffee metadata fields (all optional under `coffee`): `roast_date`, `type`, `origin`, `varietal`, `process`
- Water ingredient field: `ppm` (optional under `water`)
- Brew result field: `tds` (optional, flat on brew object)
- `duration_s` minimum corrected to `exclusiveMinimum: 0`
- All existing valid examples updated to v0.2 format
- New valid example: `hybrid.yaml`
- New invalid examples: `v0.1_format.yaml`, `zero_duration.yaml`
- Updated spec document: `brewspec-v0.2.md`
- Backward compatibility section in spec document
- Test suite updated with new assertions and `ids=lambda f: f.name`

### Out of Scope

- **Standardized enumerations for `method` or `grind`** — no usage data to inform this; remains freeform
- **Equipment fields** (grinder model, brewer model) — deferred to v0.3+
- **Pour schedules / step-by-step timing** — significant complexity; deferred to v0.3+
- **Tasting dimensions / SCA cupping scores** — no user demand signal yet; deferred
- **Extraction yield** (`ey` field) — related to `tds` but requires yield calculation; deferred to v0.3+ alongside potential `result` object grouping
- **Water chemistry beyond `ppm`** (pH, mineral breakdown, bicarbonate) — deferred to v0.3+
- **BrewLog CLI** — a separate task that depends on this spec, not vice versa
- **brewspec.org landing page** — tracked separately as `brewspec-landing-page` in the manifest

---

## Design Notes

### Object Model Restructure

**v0.1 structure** (fields grouped by ingredient, brew quantities inside ingredient objects):

```yaml
brewspec_version: "0.1"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    coffee:
      dose_g: 20          # brew quantity inside coffee object
    water:
      weight_g: 320       # brew quantity inside water object
      volume_ml: 320
      temp_c: 96
```

**v0.2 structure** (brew quantities at brew level; ingredient objects describe the ingredient):

```yaml
brewspec_version: "0.2"
brews:
  - date: "2026-02-15T08:30:00Z"
    type: "pour_over"
    dose_g: 20              # brew quantity — how much coffee used
    water_weight_g: 320     # brew quantity — how much water used
    water_volume_ml: 320    # brew quantity — optional alias
    water_temp_c: 96        # brew quantity — temperature used
    coffee:                 # optional — describes the coffee itself
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    water:                  # optional — describes the water itself
      ppm: 150
    tds: 1.38               # brew result
```

**Rationale**: `dose_g` is a parameter of the brew act (you dose differently for V60 vs espresso using the same coffee). `origin`, `roast_date`, and `varietal` describe the coffee ingredient — the same values apply regardless of brew method. Keeping them in separate namespaces produces an accurate, extensible model. The v0.1 structure conflated these concerns and would become increasingly confusing as coffee metadata grew.

### Field Naming Convention

Brew-level water quantities use a `water_` prefix (`water_weight_g`, `water_volume_ml`, `water_temp_c`) to retain their association with water without nesting them in an object. `dose_g` carries no prefix because the brew context makes it unambiguously a coffee dose — there is no other ingredient that is measured by dose in this spec.

### coffee.type Field Name Collision

The brew object already has a `type` field (brew method category: `pour_over`, `espresso`, etc.). The coffee metadata field that distinguishes single origin from blend is named `coffee.type` — it lives inside the `coffee` object, so there is no collision in the schema. However, tool builders should be aware that `brew.type` and `brew.coffee.type` are distinct fields with distinct semantics. The spec document and field reference tables must make this unambiguous.

### roast_date Format

Plain date string `YYYY-MM-DD` (e.g., `"2026-01-20"`). Rationale: roasters label bags by day only. A full ISO 8601 datetime would imply time-of-day precision that does not exist in practice and would make manual entry unnecessarily verbose. The JSON Schema pattern constraint is `^\d{4}-\d{2}-\d{2}$`. Note that this format is intentionally different from the `date` field (which uses full ISO 8601 UTC datetime) — the spec document must explain why both formats exist.

### origin as an Array

`coffee.origin` is defined as an array of strings (`minItems: 1`) rather than a plain string. This supports blends where multiple origins are known (`["Ethiopia", "Colombia"]`) without requiring a separate field. For single-origin coffees, the array has one entry (`["Ethiopia"]`). An empty array is not valid (`minItems: 1`). Each string must have `minLength: 1`.

### tds Placement

`tds` is a flat optional field on the brew object, at the same level as `rating` and `notes`. It is a measurement taken after the brew completes, but it does not require a separate `result` object in v0.2. That grouping is deferred to v0.3+ if additional result fields (e.g., extraction yield) are added. Introducing a `result` object for a single field would add structure without adding clarity.

### duration_s Correction

v0.1 set `minimum: 0` with the rationale that "some methods have effectively zero brew time." That rationale does not hold — even instant coffee requires some contact time, and a recorded duration of zero is almost certainly a data entry error. The constraint is corrected to `exclusiveMinimum: 0`. This is consistent with all other positive-value fields in the schema (`dose_g`, `water_weight_g`, `water_volume_ml`). The v0.2 spec document removes the "zero is valid for instant methods" design decision and replaces it with a note that this was corrected from v0.1.

### Backward Compatibility

v0.2 is a breaking change. The following field-level migrations are required for any v0.1 file to be valid against the v0.2 schema:

| v0.1 field | v0.2 field | Notes |
|---|---|---|
| `coffee.dose_g` | `dose_g` (brew level) | Required; moves out of `coffee` object |
| `water.weight_g` | `water_weight_g` (brew level) | Required; renamed and moved |
| `water.volume_ml` | `water_volume_ml` (brew level) | Optional; renamed and moved |
| `water.temp_c` | `water_temp_c` (brew level) | Optional; renamed and moved |
| `brewspec_version: "0.1"` | `brewspec_version: "0.2"` | Must be updated |
| `duration_s: 0` | Not valid in v0.2 | Must be corrected or removed |

Tools should validate `brewspec_version` before selecting a schema and should not attempt to validate v0.1 files against the v0.2 schema.

### JSON Schema Strategy for Architect

- `dose_g`, `water_weight_g`, `water_volume_ml`, `water_temp_c` move to the `brew` `$def` as direct properties
- `dose_g` and `water_weight_g` move to the brew `required` array; `coffee` and `water` are removed from `required`
- `coffee` `$def` is restructured: `required` is removed entirely (all fields are optional); `dose_g` is removed; metadata fields are added
- `water` `$def` is restructured: `required` is removed entirely; `weight_g`, `volume_ml`, `temp_c` are removed; `ppm` is added
- `tds` is added as a property of the `brew` `$def`
- `duration_s` constraint changes from `"minimum": 0` to `"exclusiveMinimum": 0`
- `brewspec_version` const changes from `"0.1"` to `"0.2"`
- `$id` changes to `https://raw.githubusercontent.com/coffee-standards/brewspec/main/brewspec.schema.json`

**Full v0.2 data structure for architect reference:**

```yaml
brewspec_version: "0.2"          # required, const "0.2"
brews:                            # required, array, minItems: 1
  - date: "2026-02-15T08:30:00Z" # required, ISO 8601 UTC datetime
    type: "pour_over"             # required, enum: immersion | pour_over | espresso | hybrid
    method: "Hario V60"           # optional, freeform string, minLength: 1
    dose_g: 20                    # required, number, exclusiveMinimum: 0
    water_weight_g: 320           # required, number, exclusiveMinimum: 0
    water_volume_ml: 320          # optional, number, exclusiveMinimum: 0
    water_temp_c: 96              # optional, number, minimum: 0, maximum: 100
    coffee:                       # optional object
      roast_date: "2026-01-20"   # optional, string, pattern: ^\d{4}-\d{2}-\d{2}$
      type: "single_origin"       # optional, enum: single_origin | blend
      origin: ["Ethiopia"]        # optional, array of strings, minItems: 1, each minLength: 1
      varietal: "Heirloom"        # optional, freeform string, minLength: 1
      process: "Washed"           # optional, freeform string, minLength: 1
    water:                        # optional object
      ppm: 150                    # optional, number, minimum: 0
    grind: "medium-fine"          # optional, freeform string, minLength: 1
    duration_s: 180               # optional, number, exclusiveMinimum: 0
    tds: 1.38                     # optional, number, exclusiveMinimum: 0
    rating: 4                     # optional, integer, minimum: 1, maximum: 5
    notes: "Bright acidity"       # optional, freeform string, minLength: 1
```

### Example Files for Architect

**Valid examples to update (v0.2 field structure + `brewspec_version: "0.2"`):**
- `examples/valid/pour_over.yaml` — include full `coffee` object (all 5 metadata fields), `water.ppm`, `tds`
- `examples/valid/pour_over.json` — same brew in JSON format, updated to v0.2
- `examples/valid/immersion_minimal.yaml` — required fields only, no `coffee` object, no `water` object
- `examples/valid/espresso.yaml` — espresso with `rating`, `notes`, `tds`
- `examples/valid/multi_brew.yaml` — 3 brews, mix of with/without `coffee` object

**Valid examples to add:**
- `examples/valid/hybrid.yaml` — AeroPress brew (`type: "hybrid"`), include `coffee` object with a blend (`type: "blend"`, `origin: ["Ethiopia", "Colombia"]`), `water.ppm`, `tds`, `rating`, `notes`

**Invalid examples to add:**
- `examples/invalid/v0.1_format.yaml` — v0.1 structure with `coffee.dose_g` nested; demonstrates breaking change
- `examples/invalid/zero_duration.yaml` — `duration_s: 0`; demonstrates corrected constraint

### Test Suite Requirements for Architect

New test assertions required (in addition to updating all existing tests for v0.2 field names):
- `duration_s: 0` is rejected
- `duration_s: 1` is accepted
- Brew with no `coffee` object passes validation
- Brew with no `water` object passes validation
- `coffee.origin: ["Ethiopia", "Colombia"]` (multi-entry array) passes validation
- `coffee.origin: []` (empty array) fails validation
- `coffee.type: "blend"` passes; `coffee.type: "roast"` fails
- `tds: 1.38` passes; `tds: 0` fails; `tds: -1` fails
- `water.ppm: 0` passes; `water.ppm: -1` fails
- `v0.1_format.yaml` (nested `coffee.dose_g`) fails v0.2 schema validation
- `roast_date: "2026-01-20"` passes; `roast_date: "2026-01-20T00:00:00Z"` fails

---

## Security Requirements

**Data Sensitivity:**
- The `coffee.origin`, `coffee.varietal`, and `coffee.process` fields are not PII but are user-supplied strings. They must be treated as plain text — not executed, not interpreted.
- The `notes` field (existing) and all new freeform string fields must not be processed as code by any tool implementing the spec. Tool builders are responsible for sanitizing these fields before display (e.g., HTML escaping in a web UI).
- `tds` and `ppm` are numeric measurements with no PII risk.
- `coffee.origin` as an array of strings must be validated element-by-element — each string must pass `minLength: 1` individually. Tools should not assume array contents are safe.

**Input Validation:**
- All new fields must be validated against the JSON Schema before storage or processing. No field should be stored without schema validation passing.
- `roast_date` pattern constraint (`^\d{4}-\d{2}-\d{2}$`) enforces structure but does not validate calendar correctness (e.g., month 13 would pass the regex). Tools that need stricter date validation must implement it at the application layer.
- `ppm` and `tds` are unbounded above — the schema enforces `> 0` but not a maximum. Tools should apply reasonable display limits (e.g., a `tds` of 99 is clearly erroneous) at the application layer, not in the schema.
- `coffee.origin` array items have no `maxLength`. Tools importing user-provided files should enforce a reasonable string length limit at the application layer to prevent memory issues from pathologically long strings.

**File I/O:**
- The updated test suite and any tools implementing v0.2 must continue to use `yaml.safe_load()` (not `yaml.load()`) for all YAML parsing. This is unchanged from v0.1 but must be verified in the updated test suite.
- The v0.2 invalid example `v0.1_format.yaml` contains valid YAML that is invalid per the schema — parsers must validate after parsing, not during.
- No new file I/O attack surface is introduced by v0.2. All concerns are the same as v0.1.

**No Secrets in Spec:**
- No authentication, API keys, credentials, or PII in any example file. Example data uses fictional brew records.
- `coffee.origin` example values ("Ethiopia", "Colombia") are public geographic names, not PII.

---

## Dependencies

**Upstream:**
- `brewspec-v0.1` (done) — v0.2 is an iteration on the existing schema and spec document

**Downstream:**
- `brewlog-cli-v0.1` — depends on BrewSpec for its data format; must target v0.2 schema if spec is finalized before CLI implementation begins
- All future products and third-party tools building against BrewSpec

**External:**
- JSON Schema Draft 2020-12 — unchanged
- ISO 8601 standard — unchanged; `roast_date` uses the date-only subset
- GitHub raw content URL — used for `$id`; stable as long as the repo and filename are unchanged

---

## Success Metrics

- **Correctness**: JSON Schema v0.2 passes meta-validation (is itself a valid JSON Schema)
- **Completeness**: All acceptance criteria AC-1 through AC-25 met
- **Example coverage**: All 4 brew `type` enum values (`immersion`, `pour_over`, `espresso`, `hybrid`) have at least one valid example
- **Backward compatibility documentation**: A developer reading the spec can determine exactly which field names changed from v0.1 to v0.2 and migrate their files without guessing
- **Test suite**: All tests pass (100%); new tests cover every new field and constraint; parametrize output identifies files by name

---

## Open Questions

- [x] **Coffee metadata fields**: Confirmed — `roast_date`, `type`, `origin`, `varietal`, `process`. All optional.
- [x] **roast_date format**: Confirmed — plain date string `YYYY-MM-DD`.
- [x] **Manifest dependency**: Confirmed — remove `depends_on: brewlog-cli-v0.1` from `brewspec-v0.2`.
- [x] **Schema $id**: Confirmed — GitHub raw URL.
- [x] **duration_s correction**: Confirmed — `exclusiveMinimum: 0`.
- [x] **Schema restructure**: Confirmed — brew quantities to brew level; `coffee` and `water` become optional ingredient descriptors.
- [x] **Field naming convention**: Confirmed — `dose_g` (no prefix), `water_weight_g`, `water_volume_ml`, `water_temp_c` (prefixed).
- [x] **tds placement**: Confirmed — flat field on brew object, not nested in a `result` object.
- [x] **ppm placement**: Confirmed — optional field inside `water` object.
