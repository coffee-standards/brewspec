# Product: BrewSpec v0.5

**Status:** Ready
**Priority:** P2 (Medium)
**Author:** product-manager
**Created:** 2026-02-26
**Last Updated:** 2026-02-26

---

## Problem Statement

BrewSpec v0.4 delivered a clean structural foundation: the `result` object, SCA-aligned ratings, dual-format dates, and a standard `grind` enum. v0.5 adds the next layer of practical detail that real brew logging surfaces as gaps.

**Four problems this version solves:**

1. **Coffee origin is a single string, not structured data.** v0.4 stores `coffee.origin` as an array of strings (e.g., `["Ethiopia"]`). This captures country-level provenance but loses everything a specialty coffee enthusiast or professional actually wants to record: region, subregion, producer, processing station, lot, and harvest year. For blends, the model collapses multiple distinct origins into one array with no way to express what percentage comes from where or which details belong to which component. The current structure works for basic logging but cannot represent the provenance information that's standard on a specialty coffee bag.

2. **Brew ratio is not directly expressible.** The two required inputs — `dose_g` and `water_weight_g` — are present, so brew ratio can be computed, but it cannot be stored explicitly as a named field. BrewLog CLI v0.5 will auto-calculate and display ratio, but without a schema field it cannot be persisted or exchanged as a first-class data point. Brew ratio (water:coffee) is one of the most commonly discussed variables in recipe development.

3. **Grinder setting is not capturable.** `equipment.grinder` records the grinder model (e.g., "Comandante C40") but not the dial position or click setting used for this particular brew. Without the setting, the equipment record is only half useful — knowing you used a Comandante tells you nothing about how it was set. The grinder setting is brew-specific, not equipment-specific.

4. **Equipment has no notes field.** The `equipment` object (`grinder`, `brewer`) accepts freeform model names but has no place for observations about the equipment — maintenance notes, calibration state, filter type, age of burrs. These details are relevant to reproducibility and are currently shoehorned into the brew-level `notes` field, mixing equipment context with brew-process notes.

**Backward compatibility approach for origin:**

The origin restructure is the most significant decision in v0.5. v0.4 defines `coffee.origin` as an array of strings. Two clean options exist:

- **Option A (Replace):** Rename or replace `coffee.origin` with a new structured `coffee.origins` array of objects. Remove (or deprecate) the old `coffee.origin` string array. This is a breaking change — any v0.4 file using `coffee.origin` will fail v0.5 validation. Migration is straightforward but required.

- **Option B (Add alongside):** Keep `coffee.origin` as-is and add a new `coffee.origins` field with structure. Tools can use either. This avoids breaking changes but creates two competing fields that serve overlapping purposes, muddying the schema indefinitely.

**Decision: Option A — structured `coffee.origins` replaces `coffee.origin`.**

The old `coffee.origin` string array is removed from the v0.5 schema. Files declaring `brewspec_version: "0.5"` and using `coffee.origin` will fail validation. This is the second intentional breaking change across BrewSpec versions (after v0.4's `result` object). The rationale: BrewSpec is still in early development with no third-party tool ecosystem to protect. The structural improvement is worth the break. The migration path is simple and documented: rename `origin` to `origins` and wrap each string in an object with `country` populated.

Target personas:
- **Home brewers** — grinder setting and brew ratio fill in the practical details that make a brew reproducible. Equipment notes let them track burr age or maintenance.
- **Coffee professionals** — structured origin data aligns with how specialty coffee is described on bags, cupping sheets, and green coffee catalogues. Lot, producer, and harvest year are standard professional provenance fields.
- **Tool builders** — structured origin supports filtering and aggregation by region, producer, and process in a way that freeform strings cannot. Brew ratio as a stored field simplifies display and analysis.

---

## User Stories

- As a **home brewer**, I want to record my grinder's dial position (e.g., `"21 clicks"`) alongside the model so that I can reproduce a brew exactly.
- As a **home brewer**, I want to store an explicit `brew_ratio` value so that my recipe is complete without having to manually compute it from dose and water every time I read my logs.
- As a **home brewer**, I want to add notes to my equipment (e.g., "burrs replaced 2026-01") so that I can track equipment state alongside my brews.
- As a **coffee professional**, I want to record the country, region, producer, process, lot, and harvest year for a coffee origin so that my brew records carry the same provenance information as a specialty bag label.
- As a **coffee professional**, I want to record multiple distinct origins with their full details so that I can log and evaluate blends with the same precision as single-origins.
- As a **tool builder**, I want origin data to be structured (not a freeform string) so that I can filter and group brews by country, region, or producer without string parsing.
- As a **tool builder**, I want `brew_ratio` available as a named field so that I can display it without recomputing it from `dose_g` and `water_weight_g` on every read.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema file is updated so that `brewspec_version` validates against `const: "0.5"`. Files declaring `brewspec_version: "0.4"` are rejected by the v0.5 schema.

### Brew Ratio Field

- **AC-2**: The brew object accepts an optional `brew_ratio` field (`type: number`, `exclusiveMinimum: 0`). When present, it represents the water-to-coffee ratio (e.g., `15.5` means 15.5g water per 1g coffee).
- **AC-3**: A brew with `brew_ratio: 15.5` passes validation.
- **AC-4**: A brew with `brew_ratio: 0` fails validation (exclusiveMinimum: 0).
- **AC-5**: A brew with `brew_ratio: -1` fails validation.
- **AC-6**: A brew that omits `brew_ratio` entirely passes validation (field is optional).
- **AC-7**: The spec document defines `brew_ratio` as: "Water-to-coffee ratio expressed as a single float (grams of water per gram of coffee). e.g. `15.5` represents 15.5:1 or approximately 64g/L. Can be computed from `water_weight_g / dose_g`. When both are present, tools should validate consistency; mismatches should be surfaced as a warning, not a schema error."

### Grinder Setting Field

- **AC-8**: The `equipment` object accepts an optional `grinder_setting` field (`type: string`, `minLength: 1`, `maxLength: 100`). When present, it records the specific setting used on the grinder for this brew (e.g., `"21"`, `"21 clicks"`, `"3.2.1"`, `"setting 21"`).
- **AC-9**: A brew with `equipment: { grinder: "Comandante C40", grinder_setting: "21 clicks" }` passes validation.
- **AC-10**: A brew that omits `grinder_setting` entirely passes validation.
- **AC-11**: A brew with `equipment: { grinder_setting: "" }` fails validation (minLength: 1).
- **AC-12**: The `equipment` object continues to enforce `additionalProperties: false`. Only `grinder`, `brewer`, `grinder_setting`, and `notes` are accepted (see AC-13 for `notes`).

### Equipment Notes Field

- **AC-13**: The `equipment` object accepts an optional `notes` field (`type: string`, `minLength: 1`, `maxLength: 2000`). When present, it records observations about equipment state (e.g., burr age, maintenance, filter type).
- **AC-14**: A brew with `equipment: { grinder: "Comandante C40", notes: "Burrs replaced 2026-01" }` passes validation.
- **AC-15**: A brew that omits `equipment.notes` passes validation.
- **AC-16**: A brew with `equipment: { notes: "" }` fails validation (minLength: 1).

### Structured Origin: `coffee.origins` Replaces `coffee.origin`

- **AC-17**: The `coffee.origin` field (array of strings) is removed from the v0.5 schema. A v0.5 brew record that includes a `coffee.origin` key fails validation due to `additionalProperties: false` on the `coffee` object.
- **AC-18**: The `coffee` object accepts an optional `coffee.origins` field. When present, it is an array of origin objects with `minItems: 1`.
- **AC-19**: Each item in `coffee.origins` is an object with `additionalProperties: false` accepting the following optional fields and no others:
  - `name` — `type: string`, `minLength: 1`, `maxLength: 100`. A label for this origin (e.g., `"Ethiopia Yirgacheffe"`, `"Brazil Fazenda Santa Ines"`).
  - `country` — `type: string`, `minLength: 1`, `maxLength: 100`. Country of origin (e.g., `"Ethiopia"`, `"Colombia"`).
  - `region` — `type: string`, `minLength: 1`, `maxLength: 100`. Region or state within the country (e.g., `"Yirgacheffe"`, `"Huila"`).
  - `subregion` — `type: string`, `minLength: 1`, `maxLength: 100`. District, zone, or kebele within the region (e.g., `"Kochere"`, `"Pitalito"`).
  - `producer` — `type: string`, `minLength: 1`, `maxLength: 100`. Farm, cooperative, or washing station name (e.g., `"Daye Bensa"`, `"Fazenda Santa Ines"`).
  - `process` — `type: string`, `minLength: 1`, `maxLength: 100`. Processing method at origin (e.g., `"Washed"`, `"Natural"`, `"Honey"`). Distinct from the brew-level process; this is the green coffee processing.
  - `lot` — `type: string`, `minLength: 1`, `maxLength: 100`. Lot or batch identifier (e.g., `"Lot 42"`, `"Export Grade 1"`).
  - `harvest_year` — `type: integer`, `minimum: 1900`, `maximum: 2100`. Harvest year as a four-digit integer (e.g., `2025`).
- **AC-20**: An origin object with no fields (empty object `{}`) passes validation — all origin fields are optional. This supports minimal logging where a user wants to record that an origin array entry exists without filling in details.
- **AC-21**: A brew with a single-origin `coffee.origins` entry passes validation:
  ```yaml
  coffee:
    origins:
      - country: "Ethiopia"
        region: "Yirgacheffe"
        producer: "Daye Bensa"
        process: "Washed"
        harvest_year: 2025
  ```
- **AC-22**: A brew with multiple origin entries (blend) passes validation:
  ```yaml
  coffee:
    origins:
      - name: "Ethiopia component"
        country: "Ethiopia"
        region: "Yirgacheffe"
      - name: "Colombia component"
        country: "Colombia"
        region: "Huila"
  ```
- **AC-23**: A brew with `coffee.origins: []` (empty array) fails validation (minItems: 1). If a user intends to record no origin data, they omit the `origins` field entirely.
- **AC-24**: An origin object with an unrecognised field (e.g., `altitude: 1800`) fails validation due to `additionalProperties: false`.
- **AC-25**: A brew that omits `coffee.origins` entirely passes validation. The field is optional on the `coffee` object.

### Carry-Forward Fixes (from v0.4 review)

- **AC-26**: The `examples/invalid/rating_out_of_range.yaml` file is updated. The file comment is corrected to accurately describe what causes the validation failure in the v0.5 context. The file demonstrates `result.ratings.overall: 6` (value exceeds maximum of 5) and the comment states this clearly. The obsolete reference to a `rating` field at the brew level is removed.
- **AC-27**: `README.md` invalid examples inventory is updated to include all v0.4 invalid examples that were omitted: `invalid_date_no_z.yaml`, `invalid_grind_freeform.yaml`, `invalid_tds_at_brew_level.yaml`. Each is listed with a brief description of what it demonstrates.

### Examples Updated for v0.5

- **AC-28**: All existing valid example files are updated to `brewspec_version: "0.5"`. Any example using `coffee.origin` is migrated to `coffee.origins` with the string values placed in the `country` field of each origin object.
- **AC-29**: At least one valid example uses the full structured origin format with `country`, `region`, `producer`, `process`, and `harvest_year` populated.
- **AC-30**: At least one valid example demonstrates a blend using `coffee.origins` with two or more entries.
- **AC-31**: At least one valid example includes `brew_ratio`.
- **AC-32**: At least one valid example includes `equipment.grinder_setting`.
- **AC-33**: At least one valid example includes `equipment.notes`.
- **AC-34**: The invalid examples directory includes a new file `invalid_origin_string_array.yaml` demonstrating that the old `coffee.origin` string array format is rejected by the v0.5 schema.

### Spec Document (brewspec-v0.5.md)

- **AC-35**: `brewspec-v0.5.md` exists as the canonical spec document for v0.5. It contains a complete, updated field reference covering all fields.
- **AC-36**: `brewspec-v0.5.md` contains a "What Changed in v0.5" section documenting: version bump; `brew_ratio` addition; `equipment.grinder_setting` addition; `equipment.notes` addition; `coffee.origin` removal; `coffee.origins` structured array addition; carry-forward example and README fixes.
- **AC-37**: `brewspec-v0.5.md` contains a "Backward Compatibility" section documenting the migration path from v0.4 to v0.5, specifically: how to migrate `coffee.origin: ["Ethiopia"]` to `coffee.origins: [{ country: "Ethiopia" }]`, and the addition of the three new optional fields (`brew_ratio`, `equipment.grinder_setting`, `equipment.notes`).

### Test Suite

- **AC-38**: The test suite is updated to cover all new ACs. New tests include at minimum:
  - `brew_ratio: 15.5` passes validation
  - `brew_ratio: 0` fails validation
  - `brew_ratio: -1` fails validation
  - `brew_ratio` omitted passes validation
  - `equipment.grinder_setting: "21 clicks"` passes validation
  - `equipment.grinder_setting: ""` fails validation
  - `equipment.grinder_setting` omitted passes validation
  - `equipment.notes: "Burrs replaced 2026-01"` passes validation
  - `equipment.notes: ""` fails validation
  - `equipment.notes` omitted passes validation
  - `equipment` with unrecognised field fails validation
  - `coffee.origins` with one entry (full detail) passes validation
  - `coffee.origins` with two entries (blend) passes validation
  - `coffee.origins: []` (empty array) fails validation
  - `coffee.origins` entry with unrecognised field fails validation
  - `coffee.origin` (old string array format) fails v0.5 validation
  - `coffee.origins` omitted entirely passes validation
  - `brewspec_version: "0.4"` is rejected by v0.5 schema

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"0.5"`
- New `brew_ratio` field: optional number at brew level, `exclusiveMinimum: 0`
- New `equipment.grinder_setting` field: optional string, `minLength: 1`, `maxLength: 100`
- New `equipment.notes` field: optional string, `minLength: 1`, `maxLength: 2000`
- `coffee.origin` (string array) removed; `coffee.origins` (array of structured objects) added — breaking change from v0.4
- `coffee.origins` items: optional object with `additionalProperties: false`, fields: `name`, `country`, `region`, `subregion`, `producer`, `process`, `lot`, `harvest_year`
- Carry-forward: `rating_out_of_range.yaml` comment corrected (LOW-1 from v0.4 review)
- Carry-forward: `README.md` invalid examples inventory updated (LOW-2 from v0.4 review)
- All valid examples updated to `brewspec_version: "0.5"`, `coffee.origin` migrated to `coffee.origins`
- New valid examples for structured origin (single-origin), blend origin, `brew_ratio`, `grinder_setting`, `equipment.notes`
- New invalid example: `invalid_origin_string_array.yaml`
- Updated spec document: `brewspec-v0.5.md` with complete field reference, What Changed, Backward Compatibility sections
- Test suite updated to cover all new ACs

### Out of Scope

- **`coffee.origins` percentage/weight split for blends** — no `percentage` or `weight_g` field on blend entries. The schema records provenance, not blend composition ratios. Blend proportions are a commercial roaster concern, not a brew logger concern. Deferred indefinitely.
- **`brew_ratio` computed validation** — the schema does not enforce consistency between `brew_ratio` and `dose_g`/`water_weight_g`. If all three are present and the ratio doesn't match the computation, the file still passes schema validation. This is application-layer concern, not schema concern. The spec document recommends tools surface a warning, not a hard error.
- **`grind` enum expansion** — the 7-value grind enum is unchanged. No new values added. Usage data is still too thin to justify expansion.
- **`method` field enumeration** — `method` remains freeform. Same rationale as prior versions.
- **Equipment registry or normalization** — no companion document or controlled vocabulary for grinder/brewer model names.
- **`coffee.origins` altitude field** — altitude is a common detail on specialty bags but varies in meaning (farm altitude, growing zone altitude). Deferred until the vocabulary is clearer.
- **`coffee` object `blend_name` field** — a label for the overall blend at the coffee level. Could be useful but adds complexity; single-origin coffees already have `coffee.origins[0].name`. Deferred.
- **`source`/`provenance` field** — tracks which tool logged the brew (CLI, mobile app, POS). Useful for data quality in aggregation but premature at this stage. Remains in the roadmap as a longer-term item.
- **Mobile display bug on brewspec.coffee** — site defect, not a schema change. Track separately.
- **Pour schedule / step-by-step timing** — deferred from prior versions.
- **Water chemistry beyond `ppm`** — deferred from prior versions.
- **BrewLog CLI v0.5** — separate task depending on this spec.

---

## Design Notes

### Origin Structure: Why These Fields

The eight fields on each origin object map directly to the hierarchy used on specialty coffee packaging and green coffee catalogues:

| Field | What it captures | Example |
|-------|-----------------|---------|
| `name` | Human-readable label for this origin entry | `"Ethiopia Yirgacheffe Natural"` |
| `country` | Country of production | `"Ethiopia"` |
| `region` | State, province, or named growing region | `"Yirgacheffe"` |
| `subregion` | District, zone, kebele, or sub-area | `"Kochere"` |
| `producer` | Farm, estate, cooperative, or washing station | `"Daye Bensa Washing Station"` |
| `process` | Green coffee processing method | `"Natural"`, `"Washed"`, `"Honey"` |
| `lot` | Lot or batch identifier from the producer | `"Lot 42 Export Grade 1"` |
| `harvest_year` | Year the crop was harvested | `2025` |

All fields are optional on each entry. A minimal entry with only `country: "Ethiopia"` is valid and represents the most basic useful provenance record.

### Origin Migration from v0.4

v0.4 files using `coffee.origin` require a mechanical migration:

```yaml
# v0.4 format
coffee:
  origin: ["Ethiopia", "Colombia"]

# v0.5 equivalent
coffee:
  origins:
    - country: "Ethiopia"
    - country: "Colombia"
```

The migration preserves all information; no data is lost. The `country` field is the natural home for a plain country string. Tools performing automatic migration should place each string from the old `origin` array into the `country` field of a new `origins` entry.

### `brew_ratio` Semantics

`brew_ratio` is stored as a single float representing grams of water per gram of coffee. This is the most common convention in specialty coffee (e.g., a 1:15.5 recipe is stored as `15.5`).

```yaml
dose_g: 18.0
water_weight_g: 280.0
brew_ratio: 15.56     # computed: 280 / 18 ≈ 15.56
```

The field is optional even when `dose_g` and `water_weight_g` are present. Users may choose to omit it (ratio is derivable), include a pre-computed value for convenience, or supply a target ratio that differs slightly from the actual measured weights. The schema does not enforce consistency between the three fields — this is an application-layer concern.

The spec document should note: tools that display `brew_ratio` should prefer the stored value when present and fall back to computing it from `water_weight_g / dose_g` when absent. When displaying, the ratio can be formatted as the raw float (`15.56`), as `1:15.56`, or as a volumetric measure (`≈ 63.9 g/L`) — the schema stores the float; display formatting is a tool decision.

### `grinder_setting` as Freeform String

The grinder setting is intentionally freeform (`type: string`). Different grinder designs use incompatible systems: Comandante uses click counts (e.g., `"21"`), Timemore uses a numbered dial (e.g., `"3.0"`), Weber EG-1 uses a micro-stepped dial position (e.g., `"3.2.1"`), espresso grinders use a number-letter code or a dial indicator. No single numeric type or structured format covers all grinders.

The `minLength: 1`, `maxLength: 100` constraints are consistent with other equipment string fields in the schema.

### Equipment Object: Full Field List for v0.5

After this version, `equipment` has four fields, all optional:

```yaml
equipment:
  grinder: "Comandante C40"         # existing — model name
  brewer: "Hario V60 02"            # existing — brewer model name
  grinder_setting: "21 clicks"      # new — setting used for this brew
  notes: "Burrs replaced 2026-01"   # new — equipment state notes
```

All four remain optional. The object continues to enforce `additionalProperties: false`.

### Full v0.5 Data Structure (for Architect)

```yaml
brewspec_version: "0.5"          # required, const "0.5"
brews:
  - date: "2026-02-26"           # required — YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ (unchanged)
    type: "pour_over"             # required — enum: immersion | pour_over | espresso | hybrid (unchanged)
    dose_g: 18.0                  # required — number, > 0 (unchanged)
    water_weight_g: 280.0         # required — number, > 0 (unchanged)
    brew_ratio: 15.56             # optional — number, > 0 (NEW)
    method: "Hario V60"          # optional — freeform string (unchanged)
    water_volume_ml: 280.0       # optional — number, > 0 (unchanged)
    water_temp_c: 96.0           # optional — number, 0–100 (unchanged)
    grind: "medium_fine"         # optional — enum, 7 values (unchanged)
    duration_s: 180              # optional — number, > 0 (unchanged)
    notes: "Washed filter paper" # optional — operational notes (unchanged)
    coffee:                      # optional object
      roast_date: "2026-01-20"   # optional — unchanged
      type: "single_origin"      # optional — enum (unchanged)
      origins:                   # optional — array of origin objects (NEW, replaces origin)
        - name: "Ethiopia Yirgacheffe"
          country: "Ethiopia"
          region: "Yirgacheffe"
          subregion: "Kochere"
          producer: "Daye Bensa"
          process: "Washed"
          lot: "Lot 42"
          harvest_year: 2025
      varietal: "Heirloom"       # optional — unchanged
      process: "Washed"          # optional — unchanged (brew-level processing note)
    water:                       # optional object — unchanged
      ppm: 150
    equipment:                   # optional object
      grinder: "Comandante C40"  # optional — unchanged
      brewer: "Hario V60 02"     # optional — unchanged
      grinder_setting: "21"      # optional — NEW
      notes: "Burrs 3 months old"# optional — NEW
    result:                      # optional object — unchanged from v0.4
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

Fields removed from v0.4: `coffee.origin` (string array).
Fields added in v0.5: `brew_ratio`, `equipment.grinder_setting`, `equipment.notes`, `coffee.origins` (structured array).

---

## Security Requirements

**Data sensitivity:**
- `coffee.origins` fields contain coffee provenance information. No PII risk.
- `equipment.notes` and `equipment.grinder_setting` are user-generated strings. May contain personal observations (e.g., "bought grinder second-hand from John"). Low sensitivity — consistent with the existing `notes` field treatment. Local-only; no cloud transmission in v0.5.
- `brew_ratio` is a numeric field. No sensitivity.

**Input validation:**
- `brew_ratio`: must be validated as a number with `exclusiveMinimum: 0`. Zero and negative values are rejected by the schema. Applications should additionally validate that the type is numeric (not a string representing a number).
- `coffee.origins` array: each entry must pass object-level validation with `additionalProperties: false`. Unrecognised fields must be rejected. `harvest_year` must be validated as an integer in range 1900–2100.
- `equipment.grinder_setting` and `equipment.notes`: freeform strings. Must not be executed, evaluated, or interpolated. Stored and displayed as plain text only. The `maxLength` constraints limit storage impact from malformed or adversarial inputs.
- All new string fields inherit the same safe-handling requirements as existing freeform fields: no SQL interpolation, no shell execution, stored and retrieved as plain strings.
- The validation pipeline is unchanged: safe parse → schema validation → application logic. All validation occurs before any write to persistent storage.

**File I/O:**
- No new file I/O concerns beyond the existing three new invalid example files. All follow the same pattern as existing invalid examples: plain YAML, no executable content.
- `yaml.safe_load()` requirement is unchanged.

**No secrets in spec:**
- No credentials, API keys, or PII in any example file.
- Producer names and lot identifiers in examples are fictitious or publicly known specialty coffee names.

---

## Dependencies

**Upstream:**
- `brewspec-v0.4` (done) — v0.5 builds on the v0.4 schema. All v0.4 non-origin fields are unchanged.

**Downstream:**
- `brewlog-cli-v0.5` (ready_for_design) — depends on `brew_ratio` field for display and storage. Depends on `coffee.origins` structure for import/export. Depends on `equipment.grinder_setting` and `equipment.notes` for add/update/show. The CLI spec cannot be fully implemented until the v0.5 schema is stable.
- All future tools building against BrewSpec. The `coffee.origin` removal is a breaking change for any tool targeting v0.4.

**External:**
- JSON Schema Draft 2020-12 — unchanged
- ISO 8601 standard — unchanged

---

## Success Metrics

- **Correctness**: JSON Schema v0.5 passes meta-validation (is itself a valid JSON Schema)
- **Completeness**: All acceptance criteria AC-1 through AC-38 met
- **Origin migration**: The Backward Compatibility section gives a developer a complete v0.4 to v0.5 migration path. A v0.4 file with `coffee.origin: ["Ethiopia"]` can be migrated to v0.5 by following the documented steps in under 2 minutes.
- **Test suite**: All tests pass (100%); new tests cover `brew_ratio` constraints, `grinder_setting` constraints, `equipment.notes` constraints, `coffee.origins` structure, blend origins, old `coffee.origin` rejection, and version const rejection.
- **Example coverage**: At least one valid example demonstrates all new fields in a realistic brew record.
- **Carry-forward resolved**: `rating_out_of_range.yaml` comment accurate; README invalid examples inventory complete.

---

## Open Questions

- [x] **Origin backward compatibility approach** — resolved: Option A (Replace). `coffee.origin` string array is removed; `coffee.origins` structured array is the sole origin field in v0.5. Migration path documented.
- [x] **`brew_ratio` type** — resolved: single float (water:coffee ratio). Stored as a number, e.g. `15.5`. Display formatting (1:15.5, 63g/L) is a tool concern.
- [x] **`grinder_setting` type** — resolved: freeform string. No numeric type imposed because grinder setting systems are incompatible across brands.
- [ ] **`coffee.origins[].process` vs. brew-level `coffee.process`** — the `coffee` object currently has a top-level `process` field (e.g., `"Washed"`) inherited from v0.1. With structured `origins`, each origin entry also has a `process` field. These overlap semantically. The architect should confirm which takes precedence and whether the brew-level `coffee.process` field should be deprecated in a future version. For v0.5, both coexist — no change to `coffee.process`.
