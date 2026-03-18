# Product: BrewSpec v0.3

**Status:** Ready
**Priority:** P2 (Medium)
**Author:** product-manager
**Created:** 2026-02-19
**Last Updated:** 2026-02-19

---

## Problem Statement

BrewSpec v0.2 shipped a structurally sound brew data format with coffee metadata, water mineral content, and TDS. Three categories of improvement are ready for v0.3, none of which require real-world CLI usage data to justify:

1. **Carry-forward fixes** from the v0.2 review: four test docstring errors where AC numbers in inline comments no longer match the renumbered v0.2 ACs. The test logic and schema are correct; only the documentation inside the test functions is wrong. These must be fixed before the v0.3 review runs.

2. **Equipment fields**: grinder model and brewer model are factual identifiers — not perceptual or equipment-relative like grind size or method naming. They are important for the commercial product's prediction engine (grind recommendations across users require knowing which grinder was used) and are straightforward to add as a new optional `equipment` object. Unlike method/grind enumerations, equipment identity is objective and does not require usage data to standardize as freeform strings.

3. **Additive field tightening and extraction yield**: freeform string fields currently have no `maxLength` constraint, which the v0.2 review flagged twice as a low-concern security issue. Now that BrewLog CLI is being built against this schema, that gap needs to close in the spec rather than being patched individually by every implementing tool. Additionally, extraction yield (`ey`) — the percentage of the coffee's soluble mass that ended up in the cup — is the metric specialty coffee professionals rely on alongside TDS. It belongs in the spec as a flat optional field, parallel to `tds`.

Target personas:
- **Tool builders** — benefit from `equipment` fields and `maxLength` constraints that make parsers simpler to harden
- **Home brewers** — can now record which grinder and brewer they used alongside a brew
- **Coffee professionals** — can record extraction yield alongside TDS for full extraction analysis

---

## User Stories

- As a **home brewer**, I want to record which grinder and brewer I used for a brew so that I can correlate equipment with outcomes when I review my brew history.
- As a **coffee professional**, I want to record extraction yield (`ey`) alongside TDS so that I have a complete picture of extraction quality in a single brew file.
- As a **tool builder**, I want `maxLength` constraints on all freeform string fields so that I don't have to implement string length guards separately in every tool that imports BrewSpec files.
- As a **tool builder**, I want accurate AC references in the test suite docstrings so that when a test fails I can immediately locate the requirement it covers.

---

## Acceptance Criteria

### Carry-Forward Fixes from v0.2 Review

- **AC-1**: The `test_date_format_iso8601` test docstring is updated to remove the reference to "AC-3". The date field constraint is part of the original brew object structure inherited from v0.1 and is not a numbered v0.2 AC. The docstring should describe the test's purpose without citing a specific AC number.
- **AC-2**: The `test_optional_fields_accepted` test docstring is updated to remove the reference to "AC-5". In v0.2, AC-5 is the `brewspec_version` const. The docstring should reference optional brew fields generally (e.g., "optional brew fields: method, grind, duration_s, rating, notes, water_temp_c, water_volume_ml") rather than citing a specific AC number.
- **AC-3**: The `test_json_format_supported` test docstring is updated to remove the reference to "AC-15". In v0.2, AC-15 is the `tds` field. The docstring should describe format-agnostic validation without citing a specific AC number.
- **AC-4**: The `test_rating_range_1_to_5` test docstring is updated to remove the reference to "AC-6". In v0.2, AC-6 is the schema `$id`. Rating constraints were unchanged from v0.1 and are not a numbered v0.2 AC. The docstring should describe the rating constraint (integer 1–5) without citing an AC number.

### Schema Version Bump

- **AC-5**: The JSON Schema file is updated so that `brewspec_version` validates against `const: "0.2"`. Files declaring `brewspec_version: "0.2"` are rejected by the v0.3 schema.
- **AC-6**: The schema `const` for `brewspec_version` is updated to `"0.3"`. The schema title and description are updated to reflect v0.3.

### New Object: `equipment`

- **AC-7**: The brew object accepts an optional `equipment` field. When present, it is an object with `additionalProperties: false`.
- **AC-8**: The `equipment` object, when present, accepts the following optional fields and no others:
  - `grinder`: string, `minLength: 1`, `maxLength: 100`. Freeform. Records the grinder model used (e.g., `"Comandante C40"`, `"Baratza Encore"`).
  - `brewer`: string, `minLength: 1`, `maxLength: 100`. Freeform. Records the brewer or brewing vessel used (e.g., `"Hario V60 02"`, `"Aeropress"`, `"Moka Pot"`).
- **AC-9**: A brew that omits the `equipment` object entirely passes validation. A brew that includes `equipment: {}` (empty object) passes validation (no fields are required inside `equipment`).
- **AC-10**: A brew that includes an unrecognised field inside `equipment` (e.g., `equipment: { kettle: "Fellow Stagg" }`) fails validation due to `additionalProperties: false`.

### New Field: `ey`

- **AC-11**: The brew object accepts an optional `ey` field (`number`, `exclusiveMinimum: 0`). When present, it represents the extraction yield as a percentage (e.g., `20.1` for 20.1% extraction yield). No maximum constraint is imposed by the schema.
- **AC-12**: A file with `ey: 0` fails validation. A file with `ey: -1` fails validation. A file with `ey: 20.1` passes validation.
- **AC-13**: `ey` is a flat optional field on the brew object, at the same level as `tds` and `rating`. It is not nested inside any object.

### maxLength Constraints on Freeform String Fields

- **AC-14**: The `method` field on the brew object gains a `maxLength: 100` constraint. A `method` value of exactly 100 characters passes. A value of 101 characters fails.
- **AC-15**: The `grind` field on the brew object gains a `maxLength: 100` constraint. A `grind` value of exactly 100 characters passes. A value of 101 characters fails.
- **AC-16**: The `notes` field on the brew object gains a `maxLength: 2000` constraint. A `notes` value of exactly 2000 characters passes. A value of 2001 characters fails.
- **AC-17**: The `coffee.varietal` field gains a `maxLength: 100` constraint. A value of exactly 100 characters passes. A value of 101 characters fails.
- **AC-18**: The `coffee.process` field gains a `maxLength: 100` constraint. A value of exactly 100 characters passes. A value of 101 characters fails.
- **AC-19**: Each string item in the `coffee.origin` array gains a `maxLength: 100` constraint. An item of exactly 100 characters passes. An item of 101 characters fails. Existing `minLength: 1` constraint is unchanged.

### Examples Updated for v0.3

- **AC-20**: All existing valid example files are updated to use `brewspec_version: "0.3"`. No structural field changes are required (the v0.3 changes are additive and non-breaking except for the version bump).
- **AC-21**: At least one valid example includes the `equipment` object with both `grinder` and `brewer` fields populated (e.g., add to `pour_over.yaml`).
- **AC-22**: At least one valid example includes the `ey` field alongside `tds` (e.g., add to `pour_over.yaml` or `espresso.yaml`).
- **AC-23**: At least one valid example demonstrates `equipment` with only one of the two fields (either `grinder` only or `brewer` only), confirming both fields are independently optional.
- **AC-24**: The invalid examples directory includes a new file `invalid_equipment_field.yaml` that demonstrates rejection of an unrecognised field inside `equipment` (per AC-10).
- **AC-25**: The invalid examples directory includes a new file `ey_zero.yaml` that demonstrates rejection of `ey: 0` (per AC-12).

### Spec Document (brewspec-v0.3.md)

- **AC-26**: `brewspec-v0.3.md` exists as the canonical spec document for v0.3. It contains a complete, updated field reference covering all brew-level fields, the `coffee` object, the `water` object, and the new `equipment` object, in their v0.3 structure.
- **AC-27**: `brewspec-v0.3.md` contains a "What Changed in v0.3" section that documents: the four docstring carry-forward fixes, the addition of the `equipment` object and its fields, the addition of `ey`, the `maxLength` constraints added to all affected freeform string fields, and the version bump.
- **AC-28**: `brewspec-v0.3.md` contains a "Design Decisions" section that documents the rationale for: `equipment` as a separate object (not flat fields), freeform strings for `grinder` and `brewer` (not enums), `ey` as a flat field parallel to `tds` (not inside a `result` object), and the chosen `maxLength` values (100 for most freeform fields, 2000 for `notes`).
- **AC-29**: `brewspec-v0.3.md` contains a "Backward Compatibility" section that explains: v0.3 is a non-breaking additive change except for the version const; v0.2 files are valid against the v0.2 schema only; tools should check `brewspec_version` to select the appropriate schema; migrating from v0.2 requires only updating `brewspec_version` to `"0.3"` and (optionally) trimming any freeform string values that exceed the new `maxLength` limits.

### Test Suite

- **AC-30**: The test suite is updated to validate all v0.3 example files. New parametrized tests cover:
  - `equipment` object with both fields passes validation
  - `equipment` object with only `grinder` passes validation
  - `equipment` object with only `brewer` passes validation
  - `equipment: {}` (empty object) passes validation
  - Brew omitting `equipment` entirely passes validation
  - `equipment` with an unknown field (e.g., `kettle`) fails validation
  - `ey: 20.1` passes validation
  - `ey: 0` fails validation
  - `ey: -1` fails validation
  - `method` value of 101 characters fails validation
  - `grind` value of 101 characters fails validation
  - `notes` value of 2001 characters fails validation
  - `coffee.varietal` value of 101 characters fails validation
  - `coffee.process` value of 101 characters fails validation
  - `coffee.origin` item of 101 characters fails validation
  - `brewspec_version: "0.2"` is rejected by v0.3 schema

---

## Scope

### In Scope

- Carry-forward docstring fixes: four test docstring AC reference corrections (AC-1 through AC-4)
- Schema version bump: `brewspec_version` const to `"0.3"`
- New optional `equipment` object with `grinder` and `brewer` fields (both freeform strings, `minLength: 1`, `maxLength: 100`, `additionalProperties: false`)
- New optional `ey` field (flat on brew object, `number`, `exclusiveMinimum: 0`)
- `maxLength` constraints added to: `method` (100), `grind` (100), `notes` (2000), `coffee.varietal` (100), `coffee.process` (100), `coffee.origin` items (100)
- All existing valid examples updated to `brewspec_version: "0.3"`
- New valid examples demonstrating `equipment` (both fields, one field) and `ey`
- New invalid examples: `invalid_equipment_field.yaml`, `ey_zero.yaml`
- Updated spec document: `brewspec-v0.3.md` with complete field reference, What Changed, Design Decisions, and Backward Compatibility sections
- Test suite updated with new assertions covering `equipment`, `ey`, and `maxLength` boundaries

### Out of Scope

- **Standardized enumerations for `method` or `grind`** — deferred to v0.4; requires real-world usage data from BrewLog CLI to justify any specific enum values
- **Equipment enumerations** (standardized list of grinder or brewer models) — freeform strings are correct for v0.3; a product database is a different scope entirely
- **`result` object grouping `tds` and `ey`** — deferred; `ey` is added as a flat field parallel to `tds` in v0.3, consistent with how `tds` was added in v0.2. A `result` object may be warranted in v0.4+ if more result fields emerge.
- **Pour schedule / step-by-step timing** — significant complexity; deferred
- **Tasting dimensions / SCA cupping scores** — no user demand signal; deferred
- **Water chemistry beyond `ppm`** (pH, mineral breakdown, bicarbonate) — deferred
- **`maxLength` on `coffee.origin` array itself** — no `maxItems` constraint is added; an array of 1000 origins is technically valid. This is an extreme edge case that the application layer can address; the schema enforces `minItems: 1` and per-item `maxLength: 100` which covers realistic inputs.
- **Calendar validation for `roast_date`** — the `^\d{4}-\d{2}-\d{2}$` pattern remains unchanged; month 13 would still pass the regex. Calendar-correct validation is an application-layer concern. Deferred.
- **`maxLength` on `coffee.roast_date`** — the pattern constraint already enforces exactly 10 characters (`YYYY-MM-DD`); an explicit `maxLength` is redundant.
- **BrewLog CLI** — a separate task that depends on this spec, not vice versa

---

## Design Notes

### v0.3 is Non-Breaking (Except the Version Const)

All field additions (`equipment`, `ey`) are optional. All `maxLength` additions tighten existing freeform string fields but do not change required fields or remove anything. The only change that makes v0.2 files invalid against the v0.3 schema is the `brewspec_version` const update from `"0.2"` to `"0.3"`. Migrating a v0.2 file to v0.3 requires updating the version string and ensuring no freeform string values exceed the new `maxLength` limits (unlikely in practice — the limits are generous).

### `equipment` as a Separate Object

`grinder` and `brewer` are placed in an `equipment` object rather than as flat brew-level fields for the same reason `coffee` metadata was placed in its own object: equipment identity is a property of the instrument, not the brew act. A user brews with the same grinder repeatedly. Grouping equipment fields under a dedicated namespace keeps the brew-level fields focused on brew parameters and leaves room for future equipment fields (e.g., `kettle`, `scale`) without cluttering the top-level namespace.

The object follows the same pattern as `coffee` and `water`: optional, `additionalProperties: false`, all contained fields optional.

### Freeform Strings for `grinder` and `brewer`

The decision to use freeform strings rather than enumerations is deliberate. Equipment naming is inconsistent across regions, retailers, and generations of a product (e.g., "Hario V60", "V60", "Hario V60 02 Plastic" all refer to the same or similar brewers). Forcing an enum would either be too strict (rejecting valid names) or too permissive (accepting so many variants it provides no standardisation value). The commercial product's prediction engine will need to normalise equipment names anyway — standardising the spec prematurely does not eliminate that problem, it just moves it.

If equipment name normalisation becomes a real problem at adoption scale, a companion "equipment registry" document or enumeration can be added to the spec in a future version. That is a different scope from the data format itself.

### `ey` Placement

`ey` (extraction yield) is a flat optional field on the brew object, at the same level as `tds`. It is a measurement or calculation derived from the brew result, parallel in nature to TDS. The v0.2 design note on `tds` anticipated this: "a `result` object may be warranted in v0.3+ if additional result fields are added." The decision in v0.3 is to add `ey` flat rather than introduce a `result` object, consistent with the principle of earning complexity. If a third result-type field emerges in v0.4, the case for a `result` object becomes stronger.

`ey` is expressed as a percentage (e.g., `20.1` for 20.1%). No maximum is enforced by the schema — over-extracted brews can theoretically exceed typical ranges, and the schema should not impose brewing orthodoxy. The typical specialty coffee target range is approximately 18–22% for filter and 18–22% for espresso, but this is a guide, not a constraint.

### `maxLength` Rationale

The `maxLength` values reflect what these fields actually contain in practice:

| Field | maxLength | Rationale |
|-------|-----------|-----------|
| `method` | 100 | A brew method description is a short phrase: "Hario V60 02", "AeroPress inverted". 100 characters is generous. |
| `grind` | 100 | A grind description is a short phrase: "medium-fine", "setting 15 on Comandante". 100 characters is generous. |
| `coffee.varietal` | 100 | A varietal name is a word or short phrase: "Heirloom", "Gesha", "Bourbon". 100 characters is generous. |
| `coffee.process` | 100 | A processing method is a word or short phrase: "Washed", "Natural", "Honey". 100 characters is generous. |
| `coffee.origin` items | 100 | A country or region name: "Ethiopia", "Yirgacheffe, Ethiopia". 100 characters is generous. |
| `notes` | 2000 | Notes can be a paragraph of tasting impressions. 2000 characters accommodates detailed notes without being unbounded. |
| `equipment.grinder` | 100 | A grinder model name: "Comandante C40 MK4", "Baratza Encore ESP". 100 characters is generous. |
| `equipment.brewer` | 100 | A brewer model name: "Hario V60 02", "AeroPress Original". 100 characters is generous. |

These constraints are not restrictive in practice. Their purpose is to give tools a safe upper bound for memory allocation and display without requiring each tool to define its own limits.

### Full v0.3 Data Structure for Architect

```yaml
brewspec_version: "0.3"          # required, const "0.3"
brews:                            # required, array, minItems: 1
  - date: "2026-02-19T08:30:00Z" # required, ISO 8601 UTC datetime
    type: "pour_over"             # required, enum: immersion | pour_over | espresso | hybrid
    method: "Hario V60"          # optional, freeform string, minLength: 1, maxLength: 100
    dose_g: 18                   # required, number, exclusiveMinimum: 0
    water_weight_g: 280          # required, number, exclusiveMinimum: 0
    water_volume_ml: 280         # optional, number, exclusiveMinimum: 0
    water_temp_c: 96             # optional, number, minimum: 0, maximum: 100
    coffee:                      # optional object
      roast_date: "2026-01-20"  # optional, string, pattern: ^\d{4}-\d{2}-\d{2}$
      type: "single_origin"      # optional, enum: single_origin | blend
      origin: ["Ethiopia"]       # optional, array of strings, minItems: 1, each minLength: 1, maxLength: 100
      varietal: "Heirloom"       # optional, freeform string, minLength: 1, maxLength: 100
      process: "Washed"          # optional, freeform string, minLength: 1, maxLength: 100
    water:                       # optional object
      ppm: 150                   # optional, number, minimum: 0
    equipment:                   # optional object  ← NEW in v0.3
      grinder: "Comandante C40"  # optional, freeform string, minLength: 1, maxLength: 100
      brewer: "Hario V60 02"     # optional, freeform string, minLength: 1, maxLength: 100
    grind: "medium-fine"         # optional, freeform string, minLength: 1, maxLength: 100
    duration_s: 180              # optional, number, exclusiveMinimum: 0
    tds: 1.38                    # optional, number, exclusiveMinimum: 0
    ey: 20.1                     # optional, number, exclusiveMinimum: 0  ← NEW in v0.3
    rating: 4                    # optional, integer, minimum: 1, maximum: 5
    notes: "Bright acidity"      # optional, freeform string, minLength: 1, maxLength: 2000
```

### JSON Schema Changes for Architect

The following changes are required to `brewspec.schema.json` relative to v0.2:

- `brewspec_version` const: change from `"0.2"` to `"0.3"`
- Add `$defs.equipment` definition:
  ```json
  "equipment": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "grinder": { "type": "string", "minLength": 1, "maxLength": 100 },
      "brewer":  { "type": "string", "minLength": 1, "maxLength": 100 }
    }
  }
  ```
- Add `equipment` as an optional property of `$defs.brew` referencing `$defs.equipment`
- Add `ey` as an optional property of `$defs.brew`: `{ "type": "number", "exclusiveMinimum": 0 }`
- Add `maxLength` to existing string properties in `$defs.brew`:
  - `method`: add `"maxLength": 100`
  - `grind`: add `"maxLength": 100`
  - `notes`: add `"maxLength": 2000`
- Add `maxLength` to existing string properties in `$defs.coffee`:
  - `varietal`: add `"maxLength": 100`
  - `process`: add `"maxLength": 100`
  - `origin` items: add `"maxLength": 100` to the items schema

### Example Files for Architect

**Valid examples to update (`brewspec_version: "0.3"`, all other fields unchanged):**
- `examples/valid/pour_over.yaml` — add `equipment: { grinder: "Comandante C40 MK4", brewer: "Hario V60 02" }` and `ey: 20.5`
- `examples/valid/pour_over.json` — update to v0.3, add `equipment` and `ey` to match YAML
- `examples/valid/immersion_minimal.yaml` — version bump only (no optional fields to add)
- `examples/valid/espresso.yaml` — version bump; add `ey: 19.8` and `equipment: { grinder: "Niche Zero" }`
- `examples/valid/multi_brew.yaml` — version bump; add `equipment` to at least one brew
- `examples/valid/hybrid.yaml` — version bump only

**Valid examples to add:**
- No new standalone valid example file is required — the `equipment` single-field demonstration (AC-23) can be satisfied within `espresso.yaml` (grinder only, no brewer).

**Invalid examples to add:**
- `examples/invalid/invalid_equipment_field.yaml` — brew with `equipment: { kettle: "Fellow Stagg EKG" }`; rejected by `additionalProperties: false`
- `examples/invalid/ey_zero.yaml` — brew with `ey: 0`; rejected by `exclusiveMinimum: 0`

### Test Suite Requirements for Architect

New test assertions required (in addition to updating all existing tests for the version const):

```
test_equipment_both_fields_accepted         # grinder + brewer present
test_equipment_grinder_only_accepted        # only grinder present
test_equipment_brewer_only_accepted         # only brewer present
test_equipment_empty_object_accepted        # equipment: {} passes
test_equipment_omitted_accepted             # no equipment key passes
test_equipment_unknown_field_rejected       # equipment: { kettle: "..." } fails
test_ey_valid_value_accepted                # ey: 20.1 passes
test_ey_zero_rejected                       # ey: 0 fails
test_ey_negative_rejected                   # ey: -1 fails
test_method_maxlength_boundary              # 100 chars passes, 101 fails
test_grind_maxlength_boundary               # 100 chars passes, 101 fails
test_notes_maxlength_boundary               # 2000 chars passes, 2001 fails
test_coffee_varietal_maxlength_boundary     # 100 chars passes, 101 fails
test_coffee_process_maxlength_boundary      # 100 chars passes, 101 fails
test_coffee_origin_item_maxlength_boundary  # 100 char item passes, 101 char item fails
test_version_const_rejects_v0_2             # brewspec_version: "0.2" fails v0.3 schema
```

---

## Security Requirements

**Data Sensitivity:**
- `equipment.grinder` and `equipment.brewer` are not PII. They are commercially available product names. No new sensitivity is introduced by this object.
- `ey` is a numeric measurement. No PII risk.
- The `maxLength` additions reduce — not increase — the attack surface for memory-based abuse via large string inputs.

**Input Validation:**
- `equipment.grinder` and `equipment.brewer` are freeform strings. They must not be executed, evaluated, or interpolated into shell commands. They are stored and displayed as plain text only.
- `ey` must be validated as a positive number before storage. Tools must reject `ey: 0` and `ey: -1` per the schema constraint.
- The new `maxLength` constraints are the schema's enforcement mechanism for string length limits. Tools must validate all freeform string fields against the schema before storage, not just at display time.
- `additionalProperties: false` on `$defs.equipment` prevents injection of unexpected fields into the equipment object. This is consistent with the same constraint on `coffee`, `water`, and the root object.

**File I/O:**
- No new file I/O concerns are introduced by v0.3. The `maxLength` constraints reduce the risk of memory issues from pathologically large strings in imported files, which was flagged as a low-concern item in both the v0.1 and v0.2 reviews.
- All YAML parsing must continue to use `yaml.safe_load()`. This is not changed by v0.3 but must be verified in the updated test suite.

**No Secrets in Spec:**
- No credentials, API keys, authentication tokens, or PII in any example file.
- Equipment names in examples ("Comandante C40 MK4", "Hario V60 02", "Niche Zero") are publicly available product names.

---

## Dependencies

**Upstream:**
- `brewspec-v0.2` (done) — v0.3 is an additive iteration on the v0.2 schema and spec document

**Downstream:**
- `brewlog-cli-v0.1` (ready_for_design) — targeting v0.2 schema; if v0.3 ships before CLI implementation begins, CLI should target v0.3. The architect should check which version is current before designing the CLI data model.
- All future products and third-party tools building against BrewSpec

**External:**
- JSON Schema Draft 2020-12 — unchanged
- ISO 8601 standard — unchanged
- GitHub raw content URL for `$id` — unchanged

---

## Success Metrics

- **Correctness**: JSON Schema v0.3 passes meta-validation (is itself a valid JSON Schema)
- **Completeness**: All acceptance criteria AC-1 through AC-30 met
- **Non-breaking**: Every valid v0.3 example file is also structurally valid v0.2 content (modulo the version const) — no field removals or renames
- **Test suite**: All tests pass (100%); new tests cover all new fields and `maxLength` boundary conditions; all four carry-forward docstrings are corrected
- **Backward compatibility documentation**: A developer can determine exactly what changed from v0.2 to v0.3 and migrate their files in under 5 minutes

---

## Open Questions

- [x] **`ey` field** — Confirmed: flat optional field on brew object, parallel to `tds`. No `result` object in v0.3.
- [x] **`maxLength` values** — Confirmed: `notes` 2000, all other freeform strings 100.
- [x] **`depends_on` gate** — Confirmed: remove `brewlog-cli-v0.1` dependency. v0.3 proceeds now. Method/grind enumerations (usage-data-dependent) move to v0.4.
