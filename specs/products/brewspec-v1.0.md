# Product: BrewSpec v1.0

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-29
**Last Updated:** 2026-03-29

---

## Problem Statement

BrewSpec v0.9 has four outstanding gaps that have accumulated across prior versions. They are addressed together in v1.0 because they are all breaking changes — bundling them into a single major version minimises the disruption to downstream tools.

**Gap 1: Water and yield field inconsistency.**
The current schema has `brew.water_weight_g` (the `_weight` suffix is redundant — grams already denotes weight). The result level has `result.yield_g` for actual output weight, but there is no recipe-level counterpart for intended output weight, and no result-level field for actual water used. This asymmetry means espresso-focused brewers cannot record their intended yield as a recipe target, and users who deviate from their recipe water amount have no way to record what they actually used.

**Gap 2: Inconsistent name field maxLength.**
`coffee.name` has `maxLength: 150` while `origin.name` has `maxLength: 100`. There is no reason for this discrepancy — both are freeform label fields playing the same role at different levels of the data model. The inconsistency creates unnecessary cognitive overhead for tool builders who must handle two different constraints for the same semantic type of field.

**Gap 3: Conflated notes fields.**
The single `brew.notes` field currently serves two different purposes that users want to record separately: process observations about preparation ("pre-infused 30s", "filter rinsed") and sensory notes about the coffee itself before brewing ("bag notes: jasmine and citrus"). The current model forces users to mix these concerns or omit one. Coffee professionals cupping a coffee before brewing have no standard place to record those observations in BrewSpec format.

**Gap 4: Missing espresso-specific equipment fields.**
`equipment` has no fields for line pressure or flow rate. These are primary variables in espresso dialling — espresso machine pressure (typically 6–9 bar) and volumetric flow rate (ml/s) are values that experienced home brewers and professionals record as part of their recipe. Without these fields, BrewSpec cannot represent a complete espresso recipe.

Target personas:
- **Home brewers** — benefit from yield targets for espresso dialling, and from a dedicated cupping notes field when they record bag notes before brewing.
- **Coffee professionals** — need to record cupping notes per coffee and per origin component, and need pressure and flow rate fields to represent espresso recipes in full.
- **Tool builders** — need consistent name field constraints and a cleaner notes model to build reliable UI and export tooling without handling inconsistencies.

---

## User Stories

- As a **home brewer** dialling in espresso, I want to record my intended output weight (`brew.yield_g`) as a recipe target so that I can track how close my actual yield (`result.yield_g`) was to my intent.
- As a **home brewer**, I want to record the actual water I used (`result.water_g`) so that when I deviate from my recipe target, I can log what I actually did.
- As a **coffee professional**, I want to record cupping notes at the coffee level (`coffee.cupping_notes`) and per origin component (`origin.cupping_notes`) so that my pre-brew or bag-description sensory notes are stored alongside the brew record, not mixed in with preparation observations.
- As a **home brewer**, I want my preparation notes (`brew.process_notes`) and my coffee's sensory notes (`coffee.cupping_notes`) to be separate fields so that I can record both without them conflating.
- As a **tool builder**, I want `coffee.name` and `origin.name` to have the same `maxLength` constraint so that I can apply uniform validation logic to all name fields in the schema.
- As a **coffee professional** using an espresso machine, I want to record line or lever pressure (`equipment.pressure_bar`) and volumetric flow rate (`equipment.flow_rate_ml_s`) so that my BrewSpec records capture the full recipe I am dialling.
- As a **tool builder** building an espresso recipe manager, I want structured pressure and flow rate fields so that I do not need to parse freeform `equipment.notes` to extract these values.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema `brewspec_version` const is updated to `"1.0"`. Documents declaring any other version string are rejected by the v1.0 schema.

### Change 1 — Water/Yield Field Symmetry

- **AC-2**: `brew.water_weight_g` is removed. `brew.water_g` is added: `type: number`, `exclusiveMinimum: 0`, description states "Recipe target water in grams. Must be > 0.".
- **AC-3**: `brew.yield_g` is added: `type: number`, `exclusiveMinimum: 0`, description states "Recipe target output weight in grams. Primarily used in espresso dialling to record intended yield before brewing. Must be > 0.".
- **AC-4**: `result.water_g` is added: `type: number`, `exclusiveMinimum: 0`, description states "Actual water used in grams. Records the measured input water when it deviates from the recipe target (brew.water_g). Must be > 0.".
- **AC-5**: `result.yield_g` is unchanged. No modification to its definition.
- **AC-6**: A brew using `brew.water_g: 280` passes validation.
- **AC-7**: A brew using `brew.water_weight_g: 280` fails validation (field removed).
- **AC-8**: A brew using `brew.yield_g: 36` passes validation.
- **AC-9**: A brew using `brew.yield_g: 0` fails validation (exclusiveMinimum: 0).
- **AC-10**: A brew using `result.water_g: 285` passes validation.
- **AC-11**: A brew using `result.water_g: 0` fails validation (exclusiveMinimum: 0).
- **AC-12**: A brew omitting all three new/renamed fields (`brew.water_g`, `brew.yield_g`, `result.water_g`) passes validation (all fields optional).

### Change 2 — Standardise name maxLength

- **AC-13**: `coffee.name` `maxLength` is changed from `150` to `100`.
- **AC-14**: A brew with `coffee.name` of exactly 100 characters passes validation.
- **AC-15**: A brew with `coffee.name` of 101 characters fails validation.
- **AC-16**: `origin.name` `maxLength` remains `100`. No change.

### Change 3 — Differentiate Notes Fields

- **AC-17**: `brew.notes` is removed. `brew.process_notes` is added: `type: string`, `minLength: 1`, `maxLength: 2000`, description states "Operational observations about the preparation (e.g. 'washed filter paper', 'pre-infused 30s', 'water from Brita filter'). For sensory description of the coffee, use coffee.cupping_notes or result.tasting_notes.".
- **AC-18**: `coffee.cupping_notes` is added: `type: string`, `minLength: 1`, `maxLength: 2000`, description states "Sensory notes on the coffee as a whole — from a bag description, pre-brew cupping, or any evaluation not tied to a specific brew result. For a single-origin coffee, this serves as the cupping note for the coffee. For blends, this describes the blend as a whole; individual components carry origin.cupping_notes.".
- **AC-19**: `origin.cupping_notes` is added: `type: string`, `minLength: 1`, `maxLength: 2000`, description states "Sensory notes specific to this origin component. For a single-origin coffee, this may duplicate coffee.cupping_notes. For blends, each component carries its own cupping note here.".
- **AC-20**: A brew using `brew.process_notes: "Rinsed filter, let bloom 30s"` passes validation.
- **AC-21**: A brew using `brew.notes: "Rinsed filter"` fails validation (field removed).
- **AC-22**: A brew with `coffee.cupping_notes: "Jasmine, peach, light honey"` passes validation.
- **AC-23**: A brew with `origin.cupping_notes: "Berry jam, floral"` passes validation.
- **AC-24**: A brew with `brew.process_notes: ""` (empty string) fails validation (minLength: 1).
- **AC-25**: A brew omitting all three notes fields (`brew.process_notes`, `coffee.cupping_notes`, `origin.cupping_notes`) passes validation (all fields optional).

### Change 4 — Equipment Pressure and Flow Rate

- **AC-26**: `equipment.pressure_bar` is added: `type: number`, `exclusiveMinimum: 0`, description states "Line or lever pressure in bars. Primarily relevant for espresso. Must be > 0 if present.".
- **AC-27**: `equipment.flow_rate_ml_s` is added: `type: number`, `exclusiveMinimum: 0`, description states "Volumetric flow rate in millilitres per second. Useful for espresso profiling and controlled pour-over. Must be > 0 if present.".
- **AC-28**: A brew with `equipment.pressure_bar: 9` passes validation.
- **AC-29**: A brew with `equipment.pressure_bar: 0` fails validation (exclusiveMinimum: 0).
- **AC-30**: A brew with `equipment.flow_rate_ml_s: 1.5` passes validation.
- **AC-31**: A brew with `equipment.flow_rate_ml_s: 0` fails validation (exclusiveMinimum: 0).
- **AC-32**: A brew omitting both `equipment.pressure_bar` and `equipment.flow_rate_ml_s` passes validation (both optional).

### Examples — Valid

- **AC-33**: All existing valid example files are updated to `brewspec_version: "1.0"`.
- **AC-34**: All occurrences of `water_weight_g` in valid example files are renamed to `water_g`.
- **AC-35**: All occurrences of `notes:` at the brew level in valid example files are renamed to `process_notes:`.
- **AC-36**: At least one valid example demonstrates `brew.yield_g` (recipe target) alongside `result.yield_g` (actual output) to show the symmetry.
- **AC-37**: At least one valid example demonstrates `result.water_g`.
- **AC-38**: At least one valid example demonstrates `coffee.cupping_notes` and `origin.cupping_notes`.
- **AC-39**: At least one valid example demonstrates `equipment.pressure_bar` and `equipment.flow_rate_ml_s`.

### Examples — Invalid

- **AC-40**: An invalid example `examples/invalid/invalid_water_weight_g.yaml` exists that uses the removed field `brew.water_weight_g` and fails v1.0 validation. (This replaces the pre-v1.0 pattern of `water_weight_g` being a valid field — it is now invalid under `additionalProperties: false`.)
- **AC-41**: An invalid example `examples/invalid/invalid_brew_notes.yaml` exists that uses the removed field `brew.notes` and fails v1.0 validation.
- **AC-42**: All existing invalid examples that use `water_weight_g` at the brew level are updated or replaced so they continue to exercise their intended failure case under v1.0.
- **AC-43**: All existing invalid examples are updated to `brewspec_version: "1.0"` unless the file is specifically testing a version string rejection.

### Spec Document

- **AC-44**: `brewspec-v1.0.md` exists as the canonical spec document for v1.0. It contains a complete field reference covering all fields in the schema.
- **AC-45**: `brewspec-v1.0.md` contains a "What Changed in v1.0" section documenting all four changes, identifying each breaking change explicitly.
- **AC-46**: `brewspec-v1.0.md` contains a "Backward Compatibility" section explaining what v0.9 documents must change to migrate to v1.0: rename `brew.water_weight_g` → `brew.water_g`, rename `brew.notes` → `brew.process_notes`, bump version to `1.0`, and ensure `coffee.name` does not exceed 100 characters.

### Test Suite

- **AC-47**: The test suite is updated to cover all new and changed ACs. New tests include at minimum:
  - `brew.water_g` accepts a positive number
  - `brew.water_g: 0` fails validation
  - `brew.water_weight_g` fails validation (removed field)
  - `brew.yield_g` accepts a positive number
  - `brew.yield_g: 0` fails validation
  - `result.water_g` accepts a positive number
  - `result.water_g: 0` fails validation
  - `coffee.name` of 100 chars passes
  - `coffee.name` of 101 chars fails
  - `brew.process_notes` accepts a non-empty string
  - `brew.process_notes: ""` fails (minLength: 1)
  - `brew.notes` fails validation (removed field)
  - `coffee.cupping_notes` accepts a non-empty string
  - `origin.cupping_notes` accepts a non-empty string
  - `equipment.pressure_bar` accepts a positive number
  - `equipment.pressure_bar: 0` fails
  - `equipment.flow_rate_ml_s` accepts a positive number
  - `equipment.flow_rate_ml_s: 0` fails
  - `brewspec_version: "0.9"` is rejected by the v1.0 schema

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"1.0"`
- **Breaking rename**: `brew.water_weight_g` → `brew.water_g`
- **New field**: `brew.yield_g` (recipe target output weight)
- **New field**: `result.water_g` (actual water used)
- **Breaking constraint tightening**: `coffee.name` `maxLength` 150 → 100
- **Breaking rename**: `brew.notes` → `brew.process_notes`
- **New field**: `coffee.cupping_notes`
- **New field**: `origin.cupping_notes`
- **New field**: `equipment.pressure_bar`
- **New field**: `equipment.flow_rate_ml_s`
- Spec document `brewspec-v1.0.md` written with complete field reference, changelog, and backward compatibility sections
- All valid example files updated: `brewspec_version` bumped, `water_weight_g` renamed, `brew.notes` renamed
- New valid examples demonstrating each new field
- New invalid examples for removed fields (`water_weight_g`, `brew.notes`)
- Test suite updated to cover all ACs above

### Out of Scope

- **BrewLog CLI changes** — the CLI must adopt v1.0 schema changes (field renames, new fields, DB migration), but that work is tracked under `brewlog-cli-v1.0`. No CLI code changes in this task.
- **BrewSpec site update** — tracked under `brewspec-site-v1.0`.
- **Additional equipment fields** — other espresso variables (pre-infusion time, temperature profiling) are not included. Add only when there is demonstrated demand.
- **Brew ratio field changes** — `brew_ratio` is unchanged. Its description references `water_weight_g`; the architect should update the description to reference `brew.water_g` during the design pass.
- **New brew type values** — the `type` enum (`immersion`, `pour_over`, `espresso`, `hybrid`) is unchanged.
- **New ratings dimensions** — no change to the `ratings` object.

---

## Design Notes

### Breaking change summary

All four changes contain at least one breaking element. Documents valid under v0.9 may fail v1.0 validation if they use:
- `brew.water_weight_g` (removed — must rename to `brew.water_g`)
- `brew.notes` (removed — must rename to `brew.process_notes`)
- `coffee.name` longer than 100 characters (was valid at 101-150 chars under v0.9)

Documents that do not use these fields or do not exceed the length limit are valid under v1.0 with only a version bump.

### Field naming conventions

The schema uses the pattern `field_unit` for measurement fields (e.g. `dose_g`, `water_temp_c`, `duration_s`, `elevation_masl`). The v1.0 changes follow this convention:

| Field | Unit suffix | Rationale |
|---|---|---|
| `brew.water_g` | `_g` | Weight in grams; drops redundant `_weight` |
| `brew.yield_g` | `_g` | Weight in grams; mirrors `result.yield_g` |
| `result.water_g` | `_g` | Weight in grams; mirrors `brew.water_g` |
| `equipment.pressure_bar` | `_bar` | Pressure in bar |
| `equipment.flow_rate_ml_s` | `_ml_s` | Flow rate in ml per second |

### Recipe vs result symmetry

The distinction between brew-level fields (recipe intent) and result-level fields (actual measurements) is central to v1.0:

| Intent (recipe) | Actual (result) |
|---|---|
| `brew.water_g` | `result.water_g` |
| `brew.yield_g` | `result.yield_g` |

Brew-level fields are what you plan to do. Result-level fields are what you measured. Both are optional — a minimal log needs neither.

### Cupping notes coexistence rule

For a **single-origin coffee**: `origin.cupping_notes` serves as the cupping note for the single component. `coffee.cupping_notes` may also be present (e.g. copied from the bag). Both are optional; neither is required when the other is present.

For a **blend**: each component in `coffee.origins[]` may carry its own `origin.cupping_notes`. `coffee.cupping_notes` describes the blend as a whole (e.g. "Balanced, chocolate and citrus"). This mirrors the existing pattern where `origin.name` describes a component and `coffee.name` describes the blend.

### Full v1.0 schema changes for the architect

Changes from v0.9 are marked. Unchanged fields are not listed.

**brew object:**
```yaml
# REMOVED: water_weight_g
water_g:           number, exclusiveMinimum: 0          # RENAMED from water_weight_g
yield_g:           number, exclusiveMinimum: 0          # NEW: recipe target output weight
# REMOVED: notes
process_notes:     string, minLength: 1, maxLength: 2000  # RENAMED from notes
```

**coffee object:**
```yaml
name:              string, minLength: 1, maxLength: 100  # CHANGED: was maxLength: 150
cupping_notes:     string, minLength: 1, maxLength: 2000  # NEW
```

**origin object:**
```yaml
cupping_notes:     string, minLength: 1, maxLength: 2000  # NEW
```

**equipment object:**
```yaml
pressure_bar:      number, exclusiveMinimum: 0          # NEW
flow_rate_ml_s:    number, exclusiveMinimum: 0          # NEW
```

**result object:**
```yaml
water_g:           number, exclusiveMinimum: 0          # NEW: actual water used
# yield_g unchanged
```

### Example YAML — demonstrating new fields

**Espresso with full recipe/result symmetry:**
```yaml
brewspec_version: "1.0"
brews:
  - date: "2026-03-29"
    type: "espresso"
    method: "La Marzocco Linea Mini"
    dose_g: 18.0
    water_g: 36.0           # recipe target water
    yield_g: 36.0           # recipe target output weight
    grind: "espresso"
    duration_s: 27
    process_notes: "Pre-infused 5s at 3 bar, then ramped to 9 bar"
    coffee:
      name: "Colombia Huila Washed"
      roaster: "Tim Wendelboe"
      roast_level: "light"
      cupping_notes: "Dark chocolate, citrus zest, dried fruit"
      type: "single_origin"
      origins:
        - name: "Huila Washed"
          country: "Colombia"
          region: "Huila"
          process: "Washed"
          cupping_notes: "Bright malic acidity, brown sugar sweetness"
    equipment:
      grinder: "Niche Zero"
      brewer: "La Marzocco Linea Mini"
      grinder_setting: 14
      pressure_bar: 9.0
      flow_rate_ml_s: 1.3
    result:
      water_g: 35.5          # actual water used (deviated slightly from target)
      yield_g: 36.5          # actual output weight
      tds: 9.1
      ey: 19.6
      tasting_notes: "Caramel sweetness, low bright acidity, clean finish"
      ratings:
        overall: 8
        flavour: 8
        acidity: 7
        mouthfeel: 7
```

**Pour-over with cupping notes:**
```yaml
brewspec_version: "1.0"
brews:
  - date: "2026-03-29"
    type: "pour_over"
    method: "Hario V60"
    dose_g: 18.0
    water_g: 280.0
    water_temp_c: 96.0
    grind: "medium_fine"
    duration_s: 195
    process_notes: "Rinsed filter, 30s bloom with 50g water"
    coffee:
      name: "Ethiopia Yirgacheffe"
      roaster: "Onyx"
      roast_level: "light"
      cupping_notes: "Jasmine, bergamot, peach tea"
      type: "single_origin"
      origins:
        - name: "Yirgacheffe Natural"
          country: "Ethiopia"
          region: "Yirgacheffe"
          process: "Natural"
          varietal: "Heirloom"
          cupping_notes: "Blueberry, floral, honey sweetness"
    result:
      yield_g: 260.0
      tds: 1.38
      tasting_notes: "Bright blueberry, jasmine, clean finish"
```

---

## Security Requirements

- **Data sensitivity**: All fields in this change are brew recipe parameters or freeform text notes. They are personal preferences and process records, not PII. Sensitivity profile is the same as the rest of BrewSpec — personal but not identifying. No change to the existing security posture.
- **Input validation**: All new string fields (`brew.process_notes`, `coffee.cupping_notes`, `origin.cupping_notes`, `equipment.notes`) have `minLength: 1` and `maxLength: 2000`, consistent with existing string fields in the schema. JSON Schema validation is the enforcement mechanism. The schema's `additionalProperties: false` on all objects ensures removed fields (`water_weight_g`, `brew.notes`) are rejected rather than silently accepted.
- **Removed field handling**: The `additionalProperties: false` constraint on the brew object means documents containing `brew.water_weight_g` or `brew.notes` will fail schema validation. This is the correct behaviour — it prevents silently dropping data from documents that haven't been migrated.
- **Number field injection**: New number fields (`pressure_bar`, `flow_rate_ml_s`, `water_g`, `yield_g`, `result.water_g`) all use JSON Schema number constraints with `exclusiveMinimum: 0`. Type enforcement is handled by the schema validator; no string injection is possible via these fields.
- **File I/O**: No change to the file I/O pattern. YAML is parsed with `yaml.safe_load()` before schema validation. Example files are plain YAML with no executable content.
- **No secrets in examples**: All new example YAML files contain only brew recipe data. No credentials, API keys, or PII.

---

## Dependencies

- **Depends on**: `brewspec-v0.9` (done) — v1.0 builds on the v0.9 schema
- **Blocks**: `brewlog-cli-v1.0` (CLI must adopt all field renames and new fields, update DB schema, update Pydantic models); `brewspec-site-v1.0` (landing page update)
- **Downstream impact**: Any tool storing or validating BrewSpec documents must handle the three breaking renames/removals (`water_weight_g`, `brew.notes`, `coffee.name` length) when adopting v1.0. Tools that do not use these fields need only a version bump.

---

## Success Metrics

- The JSON Schema v1.0 passes meta-validation (is itself a valid JSON Schema Draft 2020-12 document)
- All valid example files pass v1.0 validation after updates
- All invalid example files fail v1.0 validation as intended
- `brew.water_weight_g` and `brew.notes` in any document are rejected by the v1.0 schema
- `coffee.name` of 101 characters is rejected by the v1.0 schema
- New fields (`brew.yield_g`, `result.water_g`, `coffee.cupping_notes`, `origin.cupping_notes`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s`) each appear in at least one valid example that passes validation
- Test suite passes with ruff clean (schema tests only — no CLI code in this task)
- The four described changes are the only schema changes in v1.0 — no other fields are affected

---

## Open Questions

None. All four changes are fully described in the manifest and confirmed by the task description. Field names, types, constraints, and rationale are specified above.
