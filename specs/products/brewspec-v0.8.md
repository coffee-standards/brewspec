# Product: BrewSpec v0.8

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-19
**Last Updated:** 2026-03-19

---

## Problem Statement

BrewSpec v0.7 captures brew parameters and results but lacks three descriptors commonly printed on specialty coffee bags: who roasted the coffee, the roast level, and the growing elevation. These are among the first things a brewer reads when opening a bag, yet there is no standard place to record them in a BrewSpec document. Without these fields, brew logs lose context that directly affects grind, temperature, and extraction decisions.

Separately, the `water_temp_c` field currently accepts arbitrary decimal precision (e.g., `96.15`). No consumer-grade thermometer measures beyond 0.1 degrees Celsius. Allowing unbounded precision invites false precision in brew records and creates inconsistency across tools that round differently. A `multipleOf: 0.1` constraint aligns the schema with real-world measurement capability.

Target personas:
- **Home brewers** — want to record the roaster, roast level, and elevation printed on their bag so their brew log tells the full story of each coffee.
- **Coffee professionals** — track roaster and roast level to compare supplier consistency; elevation is a standard quality indicator in sourcing decisions.
- **Tool builders** — need unambiguous, constrained fields to build filters, comparisons, and analytics without guessing at precision or inventing ad-hoc roast taxonomies.

---

## User Stories

- As a **home brewer**, I want to record who roasted my coffee so that I can track and compare coffees across different roasters over time.
- As a **home brewer**, I want to record the roast level (light, medium, or dark) so that I can see how roast level affects my grind and brew parameters.
- As a **coffee professional**, I want to record the growing elevation of a coffee so that I can correlate altitude with cup quality and sourcing decisions.
- As a **tool builder**, I want `water_temp_c` constrained to 0.1-degree precision so that I can store and compare temperatures without handling arbitrary decimal places or rounding inconsistencies.
- As a **tool builder**, I want `coffee.roast_level` to be a controlled enum so that I can build filters and groupings without normalizing freeform strings.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema is updated so that `brewspec_version` validates against `const: "0.8"`. Files declaring `brewspec_version: "0.7"` are rejected by the v0.8 schema.

### coffee.roaster (additive, non-breaking)

- **AC-2**: The `coffee` object accepts an optional `roaster` field (`type: string`, `minLength: 1`, `maxLength: 100`). A brew document that omits `coffee.roaster` passes validation.
- **AC-3**: A brew with `coffee.roaster: "Onyx"` passes validation.
- **AC-4**: A brew with `coffee.roaster: ""` (empty string) fails validation (`minLength: 1`).

### coffee.roast_level (additive, non-breaking)

- **AC-5**: The `coffee` object accepts an optional `roast_level` field (`type: string`, `enum: ["light", "medium", "dark"]`). A brew document that omits `coffee.roast_level` passes validation.
- **AC-6**: A brew with `coffee.roast_level: "light"` passes validation.
- **AC-7**: A brew with `coffee.roast_level: "medium"` passes validation.
- **AC-8**: A brew with `coffee.roast_level: "dark"` passes validation.
- **AC-9**: A brew with `coffee.roast_level: "medium_light"` fails validation (not in enum).
- **AC-10**: A brew with `coffee.roast_level: "Light"` (capitalised) fails validation (enum is lowercase).

### origin.elevation_masl (additive, non-breaking)

- **AC-11**: Each item in `coffee.origins[]` accepts an optional `elevation_masl` field (`type: integer`, `exclusiveMinimum: 0`). A brew document that omits `elevation_masl` from an origin entry passes validation.
- **AC-12**: A brew with `coffee.origins: [{ country: "Ethiopia", elevation_masl: 1950 }]` passes validation.
- **AC-13**: A brew with `coffee.origins: [{ elevation_masl: 0 }]` fails validation (`exclusiveMinimum: 0`).
- **AC-14**: A brew with `coffee.origins: [{ elevation_masl: -100 }]` fails validation.
- **AC-15**: A brew with `coffee.origins: [{ elevation_masl: 1950.5 }]` fails validation (must be integer).

### water_temp_c multipleOf: 0.1 (breaking change — schema tightening)

- **AC-16**: `water_temp_c` adds a `multipleOf: 0.1` constraint. A brew with `water_temp_c: 96.0` passes validation.
- **AC-17**: A brew with `water_temp_c: 96.5` passes validation.
- **AC-18**: A brew with `water_temp_c: 93` (integer) passes validation (integers are multiples of 0.1).
- **AC-19**: A brew with `water_temp_c: 96.15` fails validation (`multipleOf: 0.1`).
- **AC-20**: A brew with `water_temp_c: 96.123` fails validation.
- **AC-21**: The spec document identifies this as a **breaking change** — a v0.7 document containing `water_temp_c: 96.15` becomes invalid under v0.8 — and provides a migration note (round to one decimal place).

### Examples

- **AC-22**: A valid example file `examples/valid/light_roast_ethiopian.yaml` is added demonstrating `coffee.roaster`, `coffee.roast_level`, and `coffee.origins[].elevation_masl` populated together.
- **AC-23**: An invalid example file `examples/invalid/invalid_roast_level.yaml` is added demonstrating that an out-of-enum value for `coffee.roast_level` is rejected.
- **AC-24**: An invalid example file `examples/invalid/invalid_water_temp_precision.yaml` is added demonstrating that `water_temp_c: 96.15` is rejected.
- **AC-25**: All existing valid example files are updated to `brewspec_version: "0.8"`. Any existing valid example with `water_temp_c` values that violate `multipleOf: 0.1` is corrected (rounded to one decimal place).

### Spec Document

- **AC-26**: `brewspec-v0.8.md` exists as the canonical spec document for v0.8. It contains a complete, updated field reference covering all current fields including the three new fields.
- **AC-27**: `brewspec-v0.8.md` contains a "What Changed in v0.8" section documenting: version bump; three additive fields (`coffee.roaster`, `coffee.roast_level`, `origin.elevation_masl`); one breaking change (`water_temp_c` precision constraint). The additive and breaking changes are clearly separated.
- **AC-28**: `brewspec-v0.8.md` contains a "Backward Compatibility" section documenting: the three additive fields require no migration; `water_temp_c` values with more than one decimal place must be rounded to one decimal place.

### Test Suite

- **AC-29**: The test suite is updated to cover all new and changed ACs. New and updated tests include at minimum:
  - `coffee.roaster: "Onyx"` passes validation
  - `coffee.roaster: ""` fails validation
  - `coffee.roaster` omitted passes validation
  - `coffee.roast_level: "light"` passes validation
  - `coffee.roast_level: "medium"` passes validation
  - `coffee.roast_level: "dark"` passes validation
  - `coffee.roast_level: "medium_light"` fails validation
  - `coffee.roast_level: "Light"` fails validation
  - `coffee.roast_level` omitted passes validation
  - `coffee.origins[].elevation_masl: 1950` passes validation
  - `coffee.origins[].elevation_masl: 0` fails validation
  - `coffee.origins[].elevation_masl: -100` fails validation
  - `coffee.origins[].elevation_masl: 1950.5` fails validation (not integer)
  - `elevation_masl` omitted passes validation
  - `water_temp_c: 96.0` passes validation
  - `water_temp_c: 96.5` passes validation
  - `water_temp_c: 93` passes validation
  - `water_temp_c: 96.15` fails validation
  - `brewspec_version: "0.7"` is rejected by the v0.8 schema

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"0.8"`
- `coffee.roaster` added as optional string field (`minLength: 1`, `maxLength: 100`) — additive, non-breaking
- `coffee.roast_level` added as optional enum field (`light`, `medium`, `dark`) — additive, non-breaking
- `coffee.origins[].elevation_masl` added as optional integer field (`exclusiveMinimum: 0`) — additive, non-breaking
- `water_temp_c` adds `multipleOf: 0.1` constraint — **breaking change** from v0.7
- Updated spec document (`brewspec-v0.8.md`) with field reference, changelog, and backward compatibility sections
- New valid example: `examples/valid/light_roast_ethiopian.yaml`
- New invalid examples: `examples/invalid/invalid_roast_level.yaml`, `examples/invalid/invalid_water_temp_precision.yaml`
- All existing valid examples updated to `brewspec_version: "0.8"` with `water_temp_c` values corrected if needed
- Test suite updated to cover all new and changed ACs
- Update BrewLog CLI schema version reference to accept v0.8 documents

### Out of Scope

- **Expanded roast_level enum** (e.g., medium-light, medium-dark, city, full city) — intentionally deferred. The three-value enum follows the "earn complexity" principle: light/medium/dark covers the vast majority of bag labelling. Finer gradations can be added in a future version if real usage demonstrates the need, but adding them now invites bikeshedding over boundaries without data to guide the decision.
- **Roast profile data** (time/temperature curve, first crack time) — application-level concern for roasting software, not a brew log field.
- **origin.elevation as a range** (e.g., 1800-2100 masl) — a single integer is sufficient for bag-label data. Range support adds complexity without clear demand.
- **Water chemistry fields** (`ph`, bicarbonate, mineral breakdown) — deferred since v0.5.
- **Pour schedule / step-by-step timing** — deferred from prior versions.
- **`method` field enumeration** — remains freeform. Unchanged.
- **BrewLog CLI v0.8** — separate task depending on this spec.
- **Floating-point edge case investigation for `multipleOf: 0.1`** — the architect must verify how JSON Schema validators handle IEEE 754 floating-point representation for the `multipleOf` constraint (e.g., whether `96.1` is reliably recognised as a multiple of `0.1`). This is a design/implementation concern, not a product spec concern.

---

## Design Notes

### coffee.roaster placement

`roaster` belongs on the top-level `coffee` object, not inside `coffee.origins[]`. The roaster is the company that roasted the final product — it applies to the coffee as a whole, not to individual origin components. A blend roasted by Onyx has one roaster regardless of how many origins it contains.

### coffee.roast_level — why three values

The three-value enum (`light`, `medium`, `dark`) is deliberately coarse. Rationale:

1. **Earn complexity.** The principles state: "Every feature starts as the simplest version that's useful." Three values cover the labels printed on the overwhelming majority of retail bags.
2. **Boundary ambiguity.** Finer gradations (medium-light, medium-dark, city, full city) have no industry-standard boundaries. Different roasters define "medium-light" differently. A freeform string would be more honest than a false-precision enum.
3. **Expandable.** JSON Schema enums can be extended in future versions without breaking existing documents (adding values is additive). If usage data shows that three values are insufficient, the enum can grow.

If a brewer needs to record finer roast detail, the `notes` field is available for freeform annotation.

### origin.elevation_masl — unit in field name

The field is named `elevation_masl` (meters above sea level) rather than `elevation` with a separate unit field. This follows the established convention in the schema: `dose_g`, `water_weight_g`, `water_temp_c`, `duration_s`, `yield_g` all embed units in field names. Embedding the unit eliminates ambiguity (feet vs. meters) without requiring a unit enum.

### water_temp_c multipleOf: 0.1 — breaking change

This is the only breaking change in v0.8. A v0.7 document containing `water_temp_c: 96.15` becomes invalid under v0.8. The migration path is straightforward: round to one decimal place.

The architect should verify floating-point behaviour in target validators (Python `jsonschema`, and any other validators in the test matrix). IEEE 754 representation of decimal fractions can cause `multipleOf` checks to behave unexpectedly — e.g., `0.1 + 0.1 + 0.1 != 0.3` in binary floating point. The architect must confirm that values like `96.1`, `96.5`, and `93.0` reliably pass the constraint in practice, and document any workaround if they do not.

### Full v0.8 Data Structure (for Architect)

Changes from v0.7 are marked.

```yaml
brewspec_version: "0.8"          # required, const "0.8"
brews:
  - date: "2026-03-19"           # optional (unchanged)
    type: "pour_over"            # optional (unchanged)
    dose_g: 18.0                 # optional (unchanged)
    water_weight_g: 280.0        # optional (unchanged)
    brew_ratio: 15.56            # optional (unchanged)
    method: "Hario V60"          # optional (unchanged)
    water_temp_c: 96.0           # optional — NOW multipleOf: 0.1 (CHANGED in v0.8)
    grind: "medium_fine"         # optional (unchanged)
    duration_s: 180              # optional (unchanged)
    notes: "Washed filter paper" # optional (unchanged)
    coffee:                      # optional object
      name: "Ethiopia Yirgacheffe"  # optional (unchanged)
      roaster: "Onyx"              # optional — NEW in v0.8
      roast_level: "light"         # optional — NEW in v0.8 (enum: light, medium, dark)
      roast_date: "2026-03-01"     # optional (unchanged)
      type: "single_origin"        # optional (unchanged)
      origins:                     # optional array
        - name: "Yirgacheffe Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa"
          process: "Natural"
          lot: "Lot 42"
          harvest_year: 2025
          varietal: "Heirloom"
          elevation_masl: 1950     # NEW in v0.8 — integer, > 0
    water:                         # optional (unchanged)
      ppm: 150
    equipment:                     # optional (unchanged)
      grinder: "Comandante C40"
      brewer: "Hario V60 02"
      grinder_setting: 21
      notes: "Burrs 3 months old"
    result:                        # optional (unchanged)
      tds: 1.38
      ey: 20.1
      brix: 1.5
      yield_g: 260.0
      tasting_notes: "Bright citrus, caramel finish"
      ratings:
        overall: 4
        fragrance: 3
        aroma: 4
        flavour: 5
        aftertaste: 4
        acidity: 5
        sweetness: 3
        mouthfeel: 4
```

Fields added in v0.8: `coffee.roaster`, `coffee.roast_level`, `coffee.origins[].elevation_masl`.
Fields changed in v0.8: `water_temp_c` (added `multipleOf: 0.1`).

---

## Security Requirements

- **Data sensitivity:** `coffee.roaster` is a business name (e.g., "Onyx", "Tim Wendelboe"). Not PII. `coffee.roast_level` is a categorical descriptor. `elevation_masl` is geographic data about a farm, not a person. No new PII-bearing fields. Overall sensitivity profile is unchanged.
- **Input validation:** All three new fields are validated at schema level before storage. `roaster` is a bounded freeform string (`minLength: 1`, `maxLength: 100`) — must not be executed, evaluated, or interpolated. `roast_level` is a closed enum — only three values accepted. `elevation_masl` is a positive integer — no string-injection risk. The `multipleOf` constraint on `water_temp_c` tightens validation, reducing the range of accepted values.
- **Safe parsing:** No change to the existing safe-parse requirement (`yaml.safe_load()`, JSON parse before schema validation). The new fields do not alter the validation pipeline.
- **File I/O:** New example files follow the same pattern as existing examples: plain YAML, no executable content.
- **No secrets in spec:** No credentials, API keys, or PII in any example file. Roaster names in examples are well-known specialty coffee companies.

---

## Dependencies

- **Depends on:** `brewspec-v0.7` (done) — this version builds on the v0.7 schema
- **Blocks:** BrewLog CLI v0.8 (must adopt v0.8 schema); Calibrate Coffee (roaster and roast level fields needed for coffee card model)

---

## Success Metrics

- The JSON Schema v0.8 passes meta-validation (is itself a valid JSON Schema)
- All existing valid examples pass v0.8 validation after version bump and any `water_temp_c` corrections
- All existing invalid examples continue to fail v0.8 validation
- New valid example (`light_roast_ethiopian.yaml`) passes validation
- New invalid examples (`invalid_roast_level.yaml`, `invalid_water_temp_precision.yaml`) fail validation
- Test suite passes with ruff clean
- The three additive fields do not break any v0.7 document (confirmed by updating existing examples with only a version bump)
- The `multipleOf: 0.1` constraint is the only change that can invalidate a previously valid document

---

## Open Questions

None. All four changes are fully specified. The floating-point behaviour of `multipleOf: 0.1` is flagged as an architect/implementation concern in the Design Notes and Out of Scope sections — the product spec defers that investigation to the architect.
