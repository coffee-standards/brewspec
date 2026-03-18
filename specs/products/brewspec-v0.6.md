# Product: BrewSpec v0.6

**Status:** Ready
**Priority:** P2 (Medium)
**Author:** product-manager
**Created:** 2026-03-03
**Last Updated:** 2026-03-04

---

## Problem Statement

BrewSpec v0.5 delivered structured origin data, brew ratio, grinder setting, and equipment notes. Real-world use against that release surfaced four schema-level issues that make v0.5 an incomplete foundation for tooling:

1. **`equipment.grinder_setting` is a freeform string, blocking numeric analytics.** v0.5 stores grinder setting as a string (e.g., `"21 clicks"`, `"21"`). The long-term goal is cross-grinder normalisation — mapping settings from one grinder to equivalent positions on another as part of dial-in support. A string field cannot be queried numerically, averaged, or compared. The field needs to be a number to be analytically useful. Different grinder designs use primary increments with sub-steps, which maps cleanly to a float with decimal tenths (e.g., Fellow Ode 2: 5 → 5.1 → 5.2 → 5.3 → 6).

2. **`coffee.process` and `coffee.varietal` are at the wrong level of the coffee object.** Both fields exist at the top-level `coffee` object, where they are semantically ambiguous for blends — it is unclear which component the process or varietal refers to. `coffee.origins[].process` was added in v0.5 alongside the top-level `coffee.process`, creating an explicit duplication. `coffee.varietal` has no corresponding field inside `coffee.origins[]` at all, despite varietal being an intrinsic property of a specific coffee's origin. Both fields must be removed from the top-level coffee object and `varietal` added inside each origin entry, where they unambiguously describe the specific component.

3. **`water_volume_ml` is a redundant field.** Water density at brewing temperatures is effectively 1g/ml, making `water_volume_ml` a near-duplicate of `water_weight_g`. In a precision brewing context — especially espresso — volume measurement is not meaningful. The field adds noise without precision value and should be removed.

4. **Five carry-forward fixes from the v0.5 review are unresolved.** Documentation, code, and example files have stale or incorrect references that accumulate technical debt and mislead users and developers.

This release is described as a stability release — not a release that avoids breaking changes, but one that is well-considered and complete enough to build tooling on top of without needing another schema revision soon.

Target personas:
- **Home brewers** — numeric grinder setting means their logs are query-ready for analytics. Process and varietal on the origin entry means single-origin logs are complete and unambiguous.
- **Coffee professionals** — removing top-level process and varietal eliminates the ambiguity that arises when logging blends, where per-component provenance is the correct model.
- **Tool builders** — a numeric `grinder_setting`, no redundant fields, and no competing representations for process/varietal means a clean, unambiguous data model to build against.

---

## User Stories

- As a **home brewer**, I want to record my grinder setting as a number (e.g., `21` or `5.2`) so that my brew logs can be queried and compared numerically without string parsing.
- As a **home brewer**, I want to record the varietal of my coffee (e.g., `"Heirloom"`, `"Gesha"`) alongside the origin it belongs to, so that the information is attached to the right component in a blend.
- As a **coffee professional**, I want process and varietal to live exclusively inside `coffee.origins[]` so that each component of a blend carries its own complete provenance record without ambiguity about which field takes precedence.
- As a **tool builder**, I want `grinder_setting` to be a numeric type so that I can perform range queries and averages across brew logs without parsing freeform strings.
- As a **tool builder**, I want the schema to have no redundant fields so that I can build a complete, unambiguous data model from the spec without having to handle field conflicts or choose between competing representations.
- As a **home brewer**, I want to record a name for my coffee (e.g., `"Ethiopia Yirgacheffe"` or `"Blue Bottle Hayes Valley Espresso"`) so that I can identify the coffee in my brew log without needing to know its full origin breakdown.
- As a **coffee professional**, I want to record a branded product name (e.g., `"Estate"`) at the coffee level so that the label I use with customers is preserved in the brew record alongside structured origin data.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema file is updated so that `brewspec_version` validates against `const: "0.6"`. Files declaring `brewspec_version: "0.5"` are rejected by the v0.6 schema.

### grinder_setting: string to number

- **AC-2**: `equipment.grinder_setting` changes type from `string` to `number` with `exclusiveMinimum: 0`. The field remains optional.
- **AC-3**: A brew with `equipment.grinder_setting: 21` passes validation.
- **AC-4**: A brew with `equipment.grinder_setting: 5.2` passes validation.
- **AC-5**: A brew with `equipment.grinder_setting: 0` fails validation (exclusiveMinimum: 0).
- **AC-6**: A brew with `equipment.grinder_setting: -1` fails validation.
- **AC-7**: A brew with `equipment.grinder_setting: "21"` (string value) fails validation.
- **AC-8**: A brew that omits `grinder_setting` entirely passes validation.
- **AC-9**: The spec document includes a guidance note on encoding convention: primary grinder increments are recorded as integers; sub-steps between primary increments are recorded as decimal tenths. Reference example: Fellow Ode 2 positions 5, 5.1, 5.2, 5.3, 6 represent primary position 5 with three sub-steps before position 6. The schema does not enforce decimal precision — the convention is guidance, not a constraint.

### Remove water_volume_ml

- **AC-10**: `water_volume_ml` is removed from the brew object schema. A v0.6 brew record that includes `water_volume_ml` fails validation due to `additionalProperties: false` on the brew object.
- **AC-11**: A brew that omits `water_volume_ml` passes validation. The field must not appear in any example files or spec documentation as a current field.

### Remove coffee.process and coffee.varietal from top-level coffee object

- **AC-12**: `coffee.process` is removed from the top-level `coffee` object schema. A v0.6 brew record that includes `coffee.process` at the top level fails validation.
- **AC-13**: `coffee.varietal` is removed from the top-level `coffee` object schema. A v0.6 brew record that includes `coffee.varietal` at the top level fails validation.
- **AC-14**: A brew that includes `coffee.origins[0].process: "Washed"` passes validation (process is valid at the origin level).
- **AC-15**: A brew that includes only `coffee.process: "Washed"` at the top level — with no `coffee.origins` — fails validation.

### Add varietal to coffee.origins[]

- **AC-16**: Each item in `coffee.origins[]` accepts an optional `varietal` field (`type: string`, `minLength: 1`, `maxLength: 100`). It records the coffee varietal for that origin component (e.g., `"Heirloom"`, `"Gesha"`, `"Bourbon"`).
- **AC-17**: A brew with `coffee.origins: [{ country: "Ethiopia", varietal: "Heirloom" }]` passes validation.
- **AC-18**: A brew with `coffee.origins: [{ varietal: "" }]` fails validation (minLength: 1).
- **AC-19**: A brew that omits `varietal` from an origin entry passes validation.
- **AC-20**: An origin object with an unrecognised field continues to fail validation (`additionalProperties: false` is unchanged). The complete valid field list for a `coffee.origins[]` entry after v0.6 is: `name`, `country`, `region`, `subregion`, `producer`, `process`, `lot`, `harvest_year`, `varietal`.

### Add coffee.name to top-level coffee object

- **AC-40**: The top-level `coffee` object accepts an optional `name` field (`type: string`, `minLength: 1`, `maxLength: 150`). Not required — a brew that omits `coffee.name` passes validation.
- **AC-41**: A brew with `coffee.name: "Estate"` passes validation.
- **AC-42**: A brew with `coffee.name: ""` (empty string) fails validation (`minLength: 1`).
- **AC-43**: A brew with `coffee.name: "Ethiopia Yirgacheffe"` alongside `coffee.origins[0].country: "Ethiopia"` passes validation — both fields coexist without conflict.
- **AC-44**: The spec document description for `coffee.origins[].name` is updated to clarify it plays the same role at the component level as `coffee.name` does at the coffee level: for single-origin coffees it will typically match `coffee.name`; for blends it is the descriptive name of that specific component (e.g., `"Brazil Natural"`, `"Colombia Washed"`).
- **AC-45**: At least one valid example demonstrates `coffee.name` populated alongside `coffee.origins[]`.

### Carry-Forward: MED-1 — README stale v0.4 references

- **AC-21**: `README.md` Quick Start section is updated to remove any reference to `coffee.origin` and replace with `coffee.origins` in the correct v0.6 structured format.
- **AC-22**: All version references in `README.md` are updated to accurately reflect the current version (v0.6 where current, historical version numbers left accurate where contextually appropriate).
- **AC-23**: The BrewLog CLI section of `README.md` is reviewed and updated to accurately reflect the current CLI version and its BrewSpec target version.
- **AC-24**: The archived file listing in `README.md` is updated to include all spec versions that have been archived to `versions/` but are missing from the listing (including `brewspec-v0.5.md` and any others).

### Carry-Forward: MED-2 — import_.py version message

- **AC-25**: `import_.py` `_V05_REQUIRED_MSG` constant (or equivalent) is updated so that the error message references the correct BrewSpec and BrewLog versions — specifically, reflecting that BrewLog v0.5 requires BrewSpec v0.5 and documenting the correct v0.4-to-v0.5 migration instructions (rename `origin` to `origins`, wrap country strings in objects).
- **AC-26**: The test asserting the exact text of the version error message is updated to match the corrected message text.

### Carry-Forward: MED-4 — export.py docstring

- **AC-27**: The `export.py` module docstring is updated to accurately state the current BrewSpec target version. If export is updated to target v0.6 in this release, the docstring should state v0.6-compliant; if it targets v0.5, it should state v0.5-compliant. The architect should confirm which version export targets in v0.6.

### Carry-Forward: MED-5 — equipment.yaml Yirgacheffe classification

- **AC-28**: The example file that contains the misclassified origin entry is corrected so that the Yirgacheffe entry reads `{ country: "Ethiopia", region: "Yirgacheffe" }` rather than `country: "Yirgacheffe"`. The corrected entry must also pass v0.6 schema validation (i.e. `coffee.process` and `coffee.varietal` must not appear at the top-level coffee object in that file).

### Examples Updated for v0.6

- **AC-29**: All existing valid example files are updated to `brewspec_version: "0.6"`. Any example using `coffee.process`, `coffee.varietal`, or `water_volume_ml` at the brew or coffee top level is migrated to the v0.6 structure.
- **AC-30**: Any example using `equipment.grinder_setting` as a string value is updated to use a numeric value.
- **AC-31**: At least one valid example demonstrates `coffee.origins[]` with `varietal` populated.
- **AC-32**: At least one valid example demonstrates a blend where each origin entry carries its own `process` and `varietal`.
- **AC-33**: The invalid examples directory includes a new file `invalid_grinder_setting_string.yaml` demonstrating that a string value for `grinder_setting` is rejected by the v0.6 schema.
- **AC-34**: The invalid examples directory includes a new file `invalid_coffee_process_top_level.yaml` demonstrating that `coffee.process` at the top-level coffee object is rejected.
- **AC-35**: The invalid examples directory includes a new file `invalid_water_volume_ml.yaml` demonstrating that `water_volume_ml` is rejected by the v0.6 schema.

### Spec Document (brewspec-v0.6.md)

- **AC-36**: `brewspec-v0.6.md` exists as the canonical spec document for v0.6. It contains a complete, updated field reference covering all current fields.
- **AC-37**: `brewspec-v0.6.md` contains a "What Changed in v0.6" section documenting: version bump; `grinder_setting` type change (string to number) with encoding guidance; `water_volume_ml` removal; `coffee.process` removal from top-level coffee object; `coffee.varietal` removal from top-level coffee object; `coffee.origins[].varietal` addition; carry-forward fixes MED-1 through MED-5.
- **AC-38**: `brewspec-v0.6.md` contains a "Backward Compatibility" section documenting the migration path from v0.5 to v0.6, covering all four breaking changes with concrete before/after YAML examples.

### Test Suite

- **AC-39**: The test suite is updated to cover all new and changed ACs. New and updated tests include at minimum:
  - `grinder_setting: 21` (integer) passes validation
  - `grinder_setting: 5.2` (float with one decimal place) passes validation
  - `grinder_setting: 0` fails validation (exclusiveMinimum: 0)
  - `grinder_setting: -1` fails validation
  - `grinder_setting: "21"` (string) fails validation
  - `grinder_setting` omitted passes validation
  - `water_volume_ml` present fails validation
  - `water_volume_ml` omitted passes validation
  - `coffee.process` at top level fails validation
  - `coffee.varietal` at top level fails validation
  - `coffee.origins[0].process: "Washed"` passes validation
  - `coffee.origins[0].varietal: "Heirloom"` passes validation
  - `coffee.origins[0].varietal: ""` fails validation (minLength: 1)
  - `coffee.origins` entry with `varietal` and an unrecognised field fails validation
  - `brewspec_version: "0.5"` is rejected by the v0.6 schema
  - `coffee.name: "Estate"` passes validation
  - `coffee.name: ""` (empty string) fails validation (`minLength: 1`)
  - `coffee.name` omitted passes validation
  - `coffee.name: "Ethiopia Yirgacheffe"` alongside `coffee.origins[0].country: "Ethiopia"` passes validation

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"0.6"`
- `equipment.grinder_setting` type change: string to number (`exclusiveMinimum: 0`) — breaking change from v0.5
- `water_volume_ml` removed from brew object — breaking change from v0.5
- `coffee.process` removed from top-level coffee object — breaking change from v0.5
- `coffee.varietal` removed from top-level coffee object — breaking change from v0.5
- `coffee.origins[].varietal` added as new optional string field inside each origin entry (`minLength: 1`, `maxLength: 100`) — additive, no breaking change
- `coffee.name` added as new optional string field on the top-level `coffee` object (`minLength: 1`, `maxLength: 150`) — serves as a branded product name or human-readable descriptive label; additive, no breaking change
- Carry-forward MED-1: README stale v0.4 references corrected
- Carry-forward MED-2: `import_.py` version error message and corresponding test updated
- Carry-forward MED-4: `export.py` module docstring updated to correct version
- Carry-forward MED-5: `equipment.yaml` Yirgacheffe origin entry corrected to `{country: Ethiopia, region: Yirgacheffe}`
- All valid examples updated to `brewspec_version: "0.6"`; top-level `coffee.process`, `coffee.varietal`, `water_volume_ml` migrated or removed; string `grinder_setting` values converted to numeric
- New valid examples: at least one demonstrating `coffee.origins[].varietal`; at least one demonstrating a blend with per-origin `process` and `varietal`
- New invalid examples: `invalid_grinder_setting_string.yaml`, `invalid_coffee_process_top_level.yaml`, `invalid_water_volume_ml.yaml`
- Updated spec document: `brewspec-v0.6.md` with complete field reference, What Changed, Backward Compatibility sections, grinder setting encoding guidance note
- Test suite updated to cover all new and changed ACs

### Out of Scope

- **MED-3 (BrewLog CLI show command gaps)** — `show` command missing `brew_ratio`, `grinder_setting`, `equipment.notes` display; `has_equipment` gate incomplete. Handled in BrewLog CLI v0.5.
- **grinder_setting decimal precision enforcement** — the schema does not constrain decimal places. The encoding convention (one decimal place for sub-steps) is documented as guidance, not enforced as a constraint.
- **Cross-grinder normalisation** — mapping equivalent settings across grinder models is an application-layer concern, not a schema concern. Deferred.
- **`coffee.origins[].altitude`** — deferred from v0.5. Vocabulary still unclear.
- **`grind` enum expansion** — insufficient usage data. Unchanged.
- **`method` field enumeration** — remains freeform. Unchanged.
- **`brew_ratio` computed validation** — schema does not enforce consistency between `brew_ratio`, `dose_g`, and `water_weight_g`. Application concern.
- **`source`/`provenance` field** — deferred from prior versions.
- **Water chemistry beyond `ppm`** — deferred from prior versions.
- **Pour schedule / step-by-step timing** — deferred from prior versions.
- **BrewLog CLI v0.6** — separate task depending on this spec.

---

## Design Notes

### Breaking Changes Summary

| Field | Change | Migration path |
|---|---|---|
| `equipment.grinder_setting` | Type: string to number (`exclusiveMinimum: 0`) | Replace string values with numeric equivalents. Simple strings like `"21"` or `"21 clicks"` become `21`. Compound strings like `"5.2"` become `5.2`. |
| `water_volume_ml` | Removed from brew object | Remove the field from any v0.5 files. No data equivalent exists in v0.6; if precision distinction between volume and weight was needed, `water_weight_g` is the retained field. |
| `coffee.process` | Removed from top-level coffee object | Move value to `coffee.origins[].process` on each relevant origin entry. |
| `coffee.varietal` | Removed from top-level coffee object | Move value to `coffee.origins[].varietal` on each relevant origin entry. |

**Additive changes (not breaking):**

| Field | Change | Migration path |
|---|---|---|
| `coffee.name` | New optional string field on top-level `coffee` object (`minLength: 1`, `maxLength: 150`) | No migration required — field is optional. Existing v0.5 files that omit it remain valid. |
| `coffee.origins[].varietal` | New optional string field on each origin entry (`minLength: 1`, `maxLength: 100`) | No migration required — field is optional. Existing entries without it remain valid. |

### grinder_setting Encoding Convention

`grinder_setting` is stored as a positive number. The intended encoding convention:

- **Integer** = primary increment position (e.g., `21` for 21 clicks on a Comandante C40)
- **Float with one decimal place** = primary increment with sub-step (e.g., `5.2` on a Fellow Ode 2 means primary position 5, second sub-step)

The convention maps to grinders that use primary steps with discrete sub-steps between each. The schema enforces only that the value is a positive number; the decimal convention is guidance for consistent encoding across grinder types.

```yaml
# Comandante C40 — click-count grinder, integer
equipment:
  grinder: "Comandante C40"
  grinder_setting: 21

# Fellow Ode 2 — primary steps + 3 sub-steps, encoded as decimal tenths
equipment:
  grinder: "Fellow Ode Gen 2"
  grinder_setting: 5.2
```

Cross-grinder normalisation (mapping "21 on a Comandante" to an equivalent on a Fellow Ode) is an application-layer concern requiring a reference dataset. The schema records the raw setting; tools handle interpretation.

### coffee.origins[] — Full Field List for v0.6

After this version, `coffee.origins[]` entries accept the following optional fields with `additionalProperties: false`:

| Field | Type | Constraints | Description |
|---|---|---|---|
| `name` | string | minLength: 1, maxLength: 100 | Descriptive name for this origin component — plays the same role at the component level as `coffee.name` does at the coffee level. For single-origin coffees it will typically match `coffee.name`; for blends it is the name of this specific component (e.g., `"Brazil Natural"`, `"Colombia Washed"`). |
| `country` | string | minLength: 1, maxLength: 100 | Country of production |
| `region` | string | minLength: 1, maxLength: 100 | State, province, or named growing region |
| `subregion` | string | minLength: 1, maxLength: 100 | District, zone, or sub-area within the region |
| `producer` | string | minLength: 1, maxLength: 100 | Farm, estate, cooperative, or washing station |
| `process` | string | minLength: 1, maxLength: 100 | Green coffee processing method (e.g., Washed, Natural, Honey) |
| `lot` | string | minLength: 1, maxLength: 100 | Lot or batch identifier from the producer |
| `harvest_year` | integer | minimum: 1900, maximum: 2100 | Harvest year as a four-digit integer |
| `varietal` | string | minLength: 1, maxLength: 100 | Coffee varietal (e.g., Heirloom, Gesha, Bourbon) — new in v0.6 |

All fields are optional on each entry. A minimal entry with only `country: "Ethiopia"` is valid.

### Full v0.6 Data Structure (for Architect)

```yaml
brewspec_version: "0.6"          # required, const "0.6"
brews:
  - date: "2026-03-03"           # required — YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ (unchanged)
    type: "pour_over"            # required — enum: immersion | pour_over | espresso | hybrid (unchanged)
    dose_g: 18.0                 # required — number, > 0 (unchanged)
    water_weight_g: 280.0        # required — number, > 0 (unchanged)
    brew_ratio: 15.56            # optional — number, > 0 (unchanged from v0.5)
    method: "Hario V60"         # optional — freeform string (unchanged)
    water_temp_c: 96.0           # optional — number, 0–100 (unchanged)
    grind: "medium_fine"         # optional — enum, 7 values (unchanged)
    duration_s: 180              # optional — number, > 0 (unchanged)
    notes: "Washed filter paper" # optional — operational notes (unchanged)
    # water_volume_ml REMOVED in v0.6
    coffee:                      # optional object
      name: "Ethiopia Yirgacheffe" # optional — new in v0.6; branded or descriptive label for the coffee
      roast_date: "2026-01-20"   # optional — unchanged
      type: "single_origin"      # optional — enum (unchanged)
      # coffee.process REMOVED in v0.6
      # coffee.varietal REMOVED in v0.6
      origins:                   # optional — array of origin objects (unchanged from v0.5)
        - name: "Ethiopia Yirgacheffe" # same value as coffee.name for single-origin; per-component for blends
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa"
          process: "Washed"      # process now lives here only
          lot: "Lot 42"
          harvest_year: 2025
          varietal: "Heirloom"   # varietal added here in v0.6
    water:                       # optional object — unchanged
      ppm: 150
    equipment:                   # optional object
      grinder: "Comandante C40"  # optional — unchanged
      brewer: "Hario V60 02"     # optional — unchanged
      grinder_setting: 21        # optional — type changed to number in v0.6
      notes: "Burrs 3 months old"# optional — unchanged
    result:                      # optional object — unchanged from v0.5
      tds: 1.38
      ey: 20.1
      brix: 1.5
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

Fields removed from v0.5: `water_volume_ml`, `coffee.process`, `coffee.varietal`.
Fields changed in v0.6: `equipment.grinder_setting` (string to number).
Fields added in v0.6: `coffee.name`, `coffee.origins[].varietal`.

---

## Security Requirements

**Data sensitivity:**
- `coffee.name` is a descriptive label (e.g., a product name or origin description). No PII risk.
- `coffee.origins[].varietal` is coffee provenance information. No PII risk.
- `equipment.grinder_setting` changes from string to number. Numeric fields carry no string-injection risk. The change reduces attack surface relative to the v0.5 string field.
- No new PII-bearing fields introduced in v0.6. The overall data sensitivity profile is unchanged: local-only storage, no cloud transmission.

**Input validation:**
- `equipment.grinder_setting`: must be validated as a number with `exclusiveMinimum: 0`. Zero and negative values are rejected by the schema. Applications must reject string inputs — the type change from string to number is a security improvement, not just a schema cleanup.
- `coffee.name`: freeform string. Must not be executed, evaluated, or interpolated. Stored and displayed as plain text only. `minLength: 1`, `maxLength: 150` constraints prevent empty values and bound storage impact.
- `coffee.origins[].varietal`: freeform string. Must not be executed, evaluated, or interpolated. Stored and displayed as plain text only. `minLength: 1`, `maxLength: 100` constraints are consistent with other origin string fields.
- All new string fields inherit the same safe-handling requirements as existing freeform fields: no SQL interpolation, no shell execution, stored and retrieved as plain strings.
- The validation pipeline is unchanged: safe parse → schema validation → application logic. All validation occurs before any write to persistent storage.

**File I/O:**
- Three new invalid example files follow the same pattern as existing invalid examples: plain YAML, no executable content.
- `yaml.safe_load()` requirement is unchanged.

**No secrets in spec:**
- No credentials, API keys, or PII in any example file.
- Producer names, varietals, and lot identifiers in examples are fictitious or publicly known specialty coffee names.

---

## Dependencies

**Upstream:**
- `brewspec-v0.5` (ready_for_deploy) — v0.6 builds on v0.5. All v0.5 fields not explicitly changed are unchanged.

**Downstream:**
- `brewlog-cli-v0.5` (ready_for_design) — depends on the v0.6 schema for BrewSpec adoption. The CLI spec should target v0.6 once this spec is stable. Note: MED-3 carry-forward items (show command display gaps) are assigned to brewlog-cli-v0.5.
- All future tools building against BrewSpec. The four breaking changes are migration costs for any tool targeting v0.5.

**External:**
- JSON Schema Draft 2020-12 — unchanged
- ISO 8601 standard — unchanged

---

## Success Metrics

- **Correctness**: JSON Schema v0.6 passes meta-validation (is itself a valid JSON Schema)
- **Completeness**: All acceptance criteria AC-1 through AC-45 met
- **No redundant fields**: The schema contains no fields that duplicate information already captured by another field at the same or lower level
- **Migration coverage**: The Backward Compatibility section gives a developer a complete v0.5 to v0.6 migration path. A v0.5 file can be migrated to v0.6 by following the documented steps in under 5 minutes.
- **Test suite**: All tests pass (100%); new and updated tests cover all four breaking changes and the new `varietal` field
- **Example coverage**: At least one valid example demonstrates all new and changed fields in a realistic brew record
- **Carry-forward resolved**: MED-1 through MED-5 all closed with no open items remaining

---

## Open Questions

- [ ] **export.py target version for MED-4** — AC-27 specifies the `export.py` docstring should be updated to the correct version, but whether export targets v0.5 or v0.6 in this release should be confirmed by the architect during design. The product spec defers this to the architect.
- [x] **`blend_name` at coffee level** — resolved: addressed by `coffee.name` in v0.6. `coffee.name` is a single optional field that serves as a branded product name (e.g., `"Estate"`) or a human-readable descriptive label (e.g., `"Ethiopia Yirgacheffe"`), depending on what the user knows. A separate `blend_name` field is not needed — `coffee.name` covers both use cases without requiring users to know whether their coffee is a blend.
- [x] **`coffee.process` and `coffee.varietal` placement** — resolved: both removed from top-level coffee object. `process` remains valid only inside `coffee.origins[]`. `varietal` added to `coffee.origins[]` and removed from top level.
- [x] **`grinder_setting` type** — resolved: changes from string to number (`exclusiveMinimum: 0`). Encoding convention documented in spec guidance note.
- [x] **`water_volume_ml` removal** — resolved: field removed. Rationale: redundant with `water_weight_g`; volume measurement not meaningful in precision brewing context.
