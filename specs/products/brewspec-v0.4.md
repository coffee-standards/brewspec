# Product: BrewSpec v0.4

**Status:** Ready
**Priority:** P2 (Medium)
**Author:** product-manager
**Created:** 2026-02-21
**Last Updated:** 2026-02-22

---

## Problem Statement

BrewSpec v0.3 established a solid foundation with equipment tracking, extraction yield, and string length constraints. v0.4 is a larger iteration that addresses the primary UX blocker for BrewLog CLI v0.3, adds a standard grind vocabulary, and introduces a structured result model that supports the commercial product's analysis capabilities.

**Five problems this version solves:**

1. **Date field UX is painful.** The current schema requires a full ISO 8601 UTC datetime (`2026-02-21T09:00:00Z`). Users logging brews just want to enter the date (`2026-02-21`). BrewLog CLI v0.3 cannot ship a better date UX until the schema permits date-only strings.

2. **Grind field is a freeform string with no vocabulary.** `grind` currently accepts any text, producing inconsistent values across tools and users (e.g., "medium", "med", "Medium Fine", "setting 15"). A standard vocabulary is needed to enable meaningful comparison and analysis.

3. **Result measurements are scattered as flat fields.** `tds` and `ey` sit at the brew level alongside input parameters (`dose_g`, `water_weight_g`). A third result measurement (`brix`) is being added, and sensory evaluation data is being added — these all belong logically together in a dedicated `result` object.

4. **Rating is too coarse and does not align with professional evaluation.** The existing `rating` (integer 1–5) captures a single overall impression. Specialty coffee evaluation uses multi-dimensional scoring aligned to the SCA cupping protocol. v0.4 expands rating to a `ratings` object inside `result` with dimensions professionals and enthusiasts already use.

5. **There is no field for sensory description separate from operational notes.** The existing `notes` field conflates tasting impressions ("bright citrus, caramel finish") with operational logging ("washed filter paper, used Brita water"). v0.4 adds a dedicated `tasting_notes` field inside `result` for sensory description, making `notes` explicitly for operational/brew-process context.

**v0.4 is more breaking than prior versions.** `tds`, `ey`, and `rating` move from flat brew-level fields into the new `result` object. v0.3 files using these fields will not validate against the v0.4 schema. The migration path is documented explicitly. This is intentional — the structural improvement to the data model justifies the break, and the versioned `brewspec_version` const provides a clean per-version validation path.

Target personas:
- **Home brewers** — date-only input removes the biggest `brewlog add` friction; `ratings` dimensions provide a richer but still optional way to capture impressions
- **Coffee professionals** — `ratings` aligned to SCA protocol, `tasting_notes` for sensory description, `brix` for sugar content measurement all support professional evaluation workflows
- **Tool builders** — standard `grind` enum enables filtering and comparison; `result` object groups all outcome data cleanly; validation-at-storage-time guidance clarifies expected pipeline behaviour

---

## User Stories

- As a **home brewer**, I want to enter just a date (`2026-02-21`) when logging a brew so that I don't have to remember or invent an exact time or timezone.
- As a **home brewer**, I want to choose a grind size from a standard list (e.g., `medium`, `medium_fine`) so that my grind descriptions are consistent across brews and comparable to others'.
- As a **coffee professional**, I want to record multi-dimensional sensory ratings (fragrance, aroma, flavour, acidity, etc.) on a 1–5 scale so that my brew evaluations align with SCA cupping protocol dimensions while staying consistent with the existing BrewSpec rating convention.
- As a **coffee professional**, I want a dedicated `tasting_notes` field for sensory description so that my operational brew notes and my sensory impressions are kept separate.
- As a **coffee professional**, I want to record `brix` (dissolved sugar content) alongside TDS and extraction yield so that I have a complete picture of extraction quality.
- As a **tool builder**, I want `tds`, `ey`, `brix`, `ratings`, and `tasting_notes` grouped in a `result` object so that I can clearly distinguish input parameters from outcome data when processing brew records.
- As a **tool builder**, I want the BrewSpec schema to accept both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ` for the `date` field so that I can let users enter either format without building a schema-workaround.
- As a **tool builder**, I want the spec document to state that tools should validate at storage time so that I know where in my pipeline to place the validation gate.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema file is updated so that `brewspec_version` validates against `const: "0.4"`. The schema title and description are updated to reflect v0.4. Files declaring `brewspec_version: "0.3"` are rejected by the v0.4 schema.

### Date Format: Accept Both Date-Only and Datetime

- **AC-2**: The `date` field on the brew object accepts both of the following formats:
  - Full ISO 8601 UTC datetime: `YYYY-MM-DDTHH:MM:SSZ` (existing format, backward-compatible)
  - Date-only: `YYYY-MM-DD` (new format)
- **AC-3**: A brew with `date: "2026-02-21"` (date-only) passes validation.
- **AC-4**: A brew with `date: "2026-02-21T09:00:00Z"` (full datetime) passes validation.
- **AC-5**: A brew with `date: "2026-02-21T09:00:00"` (datetime without Z suffix) fails validation.
- **AC-6**: A brew with `date: "21-02-2026"` (wrong order) fails validation.
- **AC-7**: A brew with `date: "2026-13-01"` (month 13) passes schema validation. Calendar-correct validation is an application-layer concern; the schema enforces format only.
- **AC-8**: The JSON Schema implements the dual-format `date` field using `oneOf` (or equivalent) with two pattern alternatives — the exact JSON Schema expression is deferred to the architect:
  - Pattern 1 (datetime): `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`
  - Pattern 2 (date-only): `^\d{4}-\d{2}-\d{2}$`

### Grind Field: Standard Vocabulary

- **AC-9**: The `grind` field on the brew object is changed from a freeform `type: string` to a strict enumeration. The accepted values are:
  `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`
- **AC-10**: A brew with `grind: "medium"` passes validation. A brew with `grind: "turkish"` passes validation. A brew with `grind: "espresso"` passes validation.
- **AC-11**: A brew with `grind: "medium_fine"` passes validation. A brew with `grind: "coarse"` passes validation.
- **AC-12**: A brew with `grind: "setting 15"` (freeform string not in the enum) fails validation.
- **AC-13**: A brew with `grind: "Medium"` (wrong case) fails validation.
- **AC-14**: A brew that omits the `grind` field entirely passes validation (`grind` remains optional).

### New Object: `result`

- **AC-15**: The brew object accepts an optional `result` field. When present, it is an object with `additionalProperties: false`.
- **AC-16**: The `result` object, when present, accepts the following optional fields and no others:
  - `tds` — moved from flat brew level (see AC-20)
  - `ey` — moved from flat brew level (see AC-20)
  - `brix` — new field (see AC-21)
  - `ratings` — new object (see AC-22 through AC-25)
  - `tasting_notes` — new field (see AC-26)
- **AC-17**: A brew that omits the `result` object entirely passes validation.
- **AC-18**: A brew that includes `result: {}` (empty object) passes validation.
- **AC-19**: A brew that includes an unrecognised field inside `result` (e.g., `result: { score: 95 }`) fails validation due to `additionalProperties: false`.

### `tds` and `ey` Move to `result`

- **AC-20**: `tds` and `ey` are removed from the flat brew object and defined exclusively inside the `result` object.
  - `result.tds`: optional, `type: number`, `exclusiveMinimum: 0`. Same constraints as the v0.3 flat field.
  - `result.ey`: optional, `type: number`, `exclusiveMinimum: 0`. Same constraints as the v0.3 flat field.
  - A brew with `tds` or `ey` at the top level of the brew object (outside `result`) fails v0.4 validation.
  - A brew with `result: { tds: 1.38, ey: 20.1 }` passes validation.

### New Field: `brix`

- **AC-21**: The `result` object accepts an optional `brix` field (`number`, `minimum: 0`). When present, it represents the dissolved sugar content in degrees Brix (e.g., `1.5` for 1.5 °Brix). A value of `0` is permitted (distilled water reads 0 °Brix). Negative values fail validation.
  - `result.brix: 0` passes validation.
  - `result.brix: 1.5` passes validation.
  - `result.brix: -1` fails validation.

### New Object: `ratings` (inside `result`)

- **AC-22**: The `result` object accepts an optional `ratings` field. When present, it is an object with `additionalProperties: false`.
- **AC-23**: The `ratings` object, when present, accepts the following optional fields and no others. All are `type: integer`, `minimum: 1`, `maximum: 5`:
  - `overall`
  - `fragrance`
  - `aroma`
  - `flavour`
  - `aftertaste`
  - `acidity`
  - `sweetness`
  - `mouthfeel`
- **AC-24**: A brew with `result: { ratings: { overall: 4, acidity: 3 } }` passes validation. Not all dimensions are required.
- **AC-25**: A brew with `result: { ratings: { overall: 0 } }` fails validation (minimum: 1). A brew with `result: { ratings: { overall: 6 } }` fails validation (maximum: 5). A brew with `result: { ratings: { overall: 3.5 } }` fails validation (must be integer).

### New Field: `tasting_notes` (inside `result`)

- **AC-26**: The `result` object accepts an optional `tasting_notes` field (`type: string`, `minLength: 1`, `maxLength: 2000`). When present, it represents sensory description of the brew (e.g., `"Bright citrus, caramel finish, clean aftertaste"`). This field is for sensory impressions and is distinct from the brew-level `notes` field.

### Brew-Level `rating` Removed

- **AC-27**: The `rating` field (integer 1–5) is removed from the flat brew object. A brew with a top-level `rating` field fails v0.4 validation due to `additionalProperties: false` on the brew object.

### `notes` Field Clarification (No Schema Change)

- **AC-28**: The existing `notes` field on the brew object is unchanged in schema terms (`type: string`, `minLength: 1`, `maxLength: 2000`). The spec document and field reference are updated with the following description: "Brew-process notes — operational observations about the preparation (e.g. 'washed filter paper', 'water from Brita filter', 'grinder re-calibrated'). For sensory description, use `result.tasting_notes`." No schema change is required; this is a documentation clarification only.

### Examples Updated for v0.4

- **AC-29**: All existing valid example files are updated to `brewspec_version: "0.4"`. Where example files contained `tds`, `ey`, or `rating` at the brew level, these are migrated into a `result` object.
- **AC-30**: At least one valid example uses the date-only format (`YYYY-MM-DD`).
- **AC-31**: At least one valid example continues to use the full datetime format (`YYYY-MM-DDTHH:MM:SSZ`).
- **AC-32**: At least one valid example includes the `result` object with `tds`, `ey`, and `ratings` populated.
- **AC-33**: At least one valid example includes `result.tasting_notes`.
- **AC-34**: At least one valid example includes `result.brix`.
- **AC-35**: At least one valid example uses the `grind` enum field.
- **AC-36**: The invalid examples directory includes a new file `invalid_date_no_z.yaml` demonstrating rejection of a datetime string without the Z suffix (e.g., `date: "2026-02-21T09:00:00"`).
- **AC-37**: The invalid examples directory includes a new file `invalid_grind_freeform.yaml` demonstrating rejection of a freeform grind value not in the enum (e.g., `grind: "setting 15"`).
- **AC-38**: The invalid examples directory includes a new file `invalid_tds_at_brew_level.yaml` demonstrating that `tds` at the flat brew level is now rejected.

### Spec Document (brewspec-v0.4.md)

- **AC-39**: `brewspec-v0.4.md` exists as the canonical spec document for v0.4. It contains a complete, updated field reference covering all brew-level fields (with `date` dual-format, `grind` enum, `result` object, `notes` clarification), the `coffee` object, the `water` object, the `equipment` object, and the new `result` object.
- **AC-40**: `brewspec-v0.4.md` contains a "What Changed in v0.4" section documenting: the version bump, the date dual-format, the `grind` enum, the `result` object (with `tds`, `ey`, `brix`, `ratings`, `tasting_notes`), the removal of flat `tds`/`ey`/`rating` from the brew object, and the `notes` field clarification.
- **AC-41**: `brewspec-v0.4.md` contains a "Validation" section that explicitly states: tools implementing BrewSpec should validate a brew document at storage time — before writing to any database or file — not only at display or read time. The section includes the expected pipeline: safe parse → schema validation → application logic.
- **AC-42**: `brewspec-v0.4.md` contains a "Backward Compatibility" section documenting: which v0.3 fields are removed or moved (flat `tds`, `ey`, `rating`), which changes are additive (date-only format, `brix`, `tasting_notes`, `ratings` object), what `grind` enum migration requires, and a step-by-step migration guide from v0.3 to v0.4.

### Test Suite

- **AC-43**: The test suite is updated to validate all v0.4 example files. New tests cover:
  - `date: "2026-02-21"` (date-only) passes validation
  - `date: "2026-02-21T09:00:00Z"` (full datetime) passes validation
  - `date: "2026-02-21T09:00:00"` (datetime without Z) fails validation
  - `date: "21-02-2026"` (wrong order) fails validation
  - Each of the 7 `grind` enum values (`turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`) passes validation
  - A freeform `grind` value (`"setting 15"`) fails validation
  - `grind` omitted passes validation
  - `result: { tds: 1.38, ey: 20.1 }` passes validation
  - `result: {}` passes validation
  - Brew without `result` passes validation
  - `result` with unknown field fails validation
  - `tds` at flat brew level fails validation
  - `ey` at flat brew level fails validation
  - `result.brix: 1.5` passes validation
  - `result.brix: 0` passes validation
  - `result.brix: -1` fails validation
  - `result.ratings: { overall: 4 }` passes validation
  - `result.ratings: { overall: 5 }` passes validation (maximum)
  - `result.ratings: { overall: 0 }` fails validation (minimum: 1)
  - `result.ratings: { overall: 6 }` fails validation (maximum: 5)
  - `result.ratings: { overall: 3.5 }` fails validation (not integer)
  - `result.tasting_notes: "Bright citrus"` passes validation
  - Top-level `rating` at brew level fails validation
  - `brewspec_version: "0.3"` is rejected by v0.4 schema

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"0.4"`
- Date field dual-format: accept both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`; Z suffix required for full datetime (timezone offsets excluded)
- `grind` field: strict enum (`turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`); field remains optional
- New `result` object: optional, `additionalProperties: false`, containing `tds`, `ey`, `brix`, `ratings`, `tasting_notes`
- `tds` and `ey` moved from flat brew level to `result` — breaking change from v0.3
- New `result.brix`: optional `number`, `minimum: 0`
- New `result.ratings` object: optional, `additionalProperties: false`, 8 dimensions all optional integers 1–5
- New `result.tasting_notes`: optional string, `minLength: 1`, `maxLength: 2000`
- Flat `rating` (integer 1–5) removed from brew object — breaking change from v0.3
- `notes` field documentation clarified as operational/brew-process notes (no schema change)
- Validation-at-storage-time guidance added to spec document
- All existing valid examples updated to `brewspec_version: "0.4"`, with `tds`/`ey`/`rating` migrated to `result`
- New valid examples demonstrating date-only format, `grind` enum, `result` with all fields
- New invalid examples: `invalid_date_no_z.yaml`, `invalid_grind_freeform.yaml`, `invalid_tds_at_brew_level.yaml`
- Updated spec document: `brewspec-v0.4.md` with complete field reference, What Changed, Validation, Backward Compatibility sections
- Test suite updated to cover all new ACs

### Out of Scope

- **`duration_s` type change** — `duration_s` remains `Optional[int]` in the Pydantic model. Fractions of a second are too precise for a brew logging tool. The schema already defines this as `type: number`; the Pydantic model intentionally stays as `int` to round to whole seconds. Not a problem to fix.
- **Timezone offset support in datetime** — datetime format continues to require the Z suffix (`YYYY-MM-DDTHH:MM:SSZ`). Supporting offsets like `+10:00` or `-05:00` would create mixed datetime data across files and complicate analytics in the commercial product where all timestamps need to be comparable. Date-only format (`YYYY-MM-DD`) is the UX solution for users who don't want to enter time components. Full datetime with timezone offsets is deferred indefinitely.
- **`method` field enumerations** — `method` remains a freeform string. The `grind` enum is prioritized because grind size is a physical dimension that maps to a consistent vocabulary. Method descriptions vary more in practice (e.g., "Hario V60 02 Plastic" vs. "V60") and benefit less from enumeration. Revisit if usage data shows a clear vocabulary emerging.
- **Equipment registry** — companion document for grinder/brewer name normalization deferred. No adoption data to drive choices. Different scope from the data format.
- **`result` object grouping as `anyOf` / optional fields** — the `result` object uses `additionalProperties: false` and all fields optional. No `required` array inside `result`. Tools should treat all result fields as best-effort measurements.
- **SCA numerical scoring (total score)** — the `ratings` object captures individual dimensions aligned to SCA cupping protocol. A computed total score (e.g., summing dimensions) is not enforced by the schema; application layers may compute it from the dimensions if desired. No `total` field inside `ratings`.
- **`maxItems` on `coffee.origin` array** — still application-layer concern. Deferred.
- **Pour schedule / step-by-step timing** — deferred from prior versions.
- **Water chemistry beyond `ppm`** — deferred from prior versions.
- **`maxLength` on `grind`** — the `grind` field is now a strict enum; string length constraints are irrelevant.
- **BrewLog CLI v0.3** — a separate task depending on this spec.

---

## Design Notes

### v0.4 Has Breaking Changes Beyond the Version Const

Unlike v0.3 (which was non-breaking except for the version const), v0.4 introduces three breaking changes that will invalidate v0.3 files:

| Breaking Change | v0.3 Behaviour | v0.4 Behaviour |
|----------------|----------------|----------------|
| Flat `tds` | Optional number on brew object | Removed; now only valid inside `result` |
| Flat `ey` | Optional number on brew object | Removed; now only valid inside `result` |
| Flat `rating` | Optional integer 1–5 on brew object | Removed; replaced by `result.ratings` object |
| `grind` values | Any freeform string | Strict 7-value enum; freeform values fail |

The migration path from v0.3 to v0.4 for files using these fields:
1. Update `brewspec_version` to `"0.4"`
2. Move `tds` (if present) from brew level to `result.tds`
3. Move `ey` (if present) from brew level to `result.ey`
4. Remove flat `rating` (if present) and move its value to `result.ratings.overall` (the 1–5 scale is unchanged; a v0.3 `rating: 4` becomes `result.ratings.overall: 4`)
5. Replace freeform `grind` value (if present) with the closest enum value (`turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`), or omit if no match applies

### Date Field: Dual-Format via `oneOf` or Combined Pattern

The current v0.3 `date` field uses a single pattern: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`.

v0.4 must accept both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`. The architect should choose between:
- `oneOf` with two sub-schemas each specifying `type: string` and a `pattern`
- A single `pattern` using regex alternation (`|`)

Either satisfies the ACs. The date-only pattern (`^\d{4}-\d{2}-\d{2}$`) is end-anchored and will not match a datetime string (which has additional characters after the date segment).

**Why Z is required for full datetime / why timezone offsets are excluded:**

The Z suffix enforces UTC. Timezone offsets (`+10:00`, `-05:00`) would allow two brew files to record the same moment differently, complicating time-based analysis in the commercial product. Aggregate analytics — comparing brew times across users, detecting patterns by time of day — require a single canonical timezone. UTC is the standard. Date-only format (`YYYY-MM-DD`) solves the primary UX problem for users who do not want to record a time; users who do want to record a time continue to use UTC format. Timezone offset support would add schema complexity for a use case (per-timezone time recording) that does not benefit the logging or analysis goals.

### `grind` Enum: Strict, No Freeform Fallback

The `grind` field changes from a freeform string to a strict enum. No freeform fallback is provided.

Rationale: the purpose of adding an enum is to enable meaningful comparison across brews and users. A freeform fallback (`oneOf` enum + arbitrary string) would allow tools to continue sending unrecognized values, defeating the standardization goal. Users who want to record a specific setting (e.g., "setting 15 on Comandante") can use the `notes` field or a future equipment-specific extension. The chosen vocabulary maps to a physical coarseness spectrum that any grinder can approximate.

The 7 values in order from finest to coarsest: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`.

`turkish` and `espresso` are named-standard grinds: Turkish coffee requires a specific powder-fine grind; espresso requires a specific fine-but-not-powder grind. Using named standards rather than generic descriptors (`powder`, `extra_fine`) is more meaningful to users and tool builders — a barista knows what "espresso" means; "extra_fine" requires interpretation. Values are snake_case for consistency with other enum fields in the schema (e.g., `type: pour_over`).

### `result` Object Design

`result` follows the same pattern as `coffee`, `water`, and `equipment`: optional, `additionalProperties: false`, all contained fields optional.

The `result` object groups all outcome/evaluation data for a brew:
- **Measurements**: `tds`, `ey`, `brix` — what you can measure about the liquid
- **Sensory evaluation**: `ratings` (structured, per SCA dimensions), `tasting_notes` (freeform)

This grouping cleanly separates "what you put in" (dose, water, parameters — still at brew level) from "what you got out" (measurements and evaluation — in `result`).

#### `ratings` Dimensions

The 8 dimensions in `result.ratings` align with SCA cupping protocol attributes:
- `fragrance` — dry grounds aroma before water is added
- `aroma` — wet aroma after water is added
- `flavour` — taste and aroma experienced during drinking
- `aftertaste` — length and quality of positive flavour attributes after swallowing
- `acidity` — quality (not quantity) of acidity; brightness
- `sweetness` — perceived sweetness
- `mouthfeel` — tactile sensation; body and texture
- `overall` — holistic impression not captured by other dimensions

All are optional so users can record only the dimensions they care about. The 1–5 scale (integers only) is consistent with the existing BrewSpec `rating` field convention and provides a simple, familiar range for home brewers while still capturing meaningful differentiation across SCA dimensions.

#### `brix` vs. `tds`

`brix` (degrees Brix) measures dissolved sugar content via refractometer. `tds` (total dissolved solids percentage) measures total dissolved solids via refractometer calibrated differently. They are related but distinct measurements. Both are optional, allowing tools and users to record whichever instruments they have. The schema does not enforce consistency between `brix` and `tds`.

`brix` uses `minimum: 0` (not `exclusiveMinimum`) because 0 °Brix is a physically valid reading (distilled water). This differs from `tds` and `ey` which use `exclusiveMinimum: 0`.

#### `tasting_notes` vs. `notes`

| Field | Location | Purpose | Example |
|-------|----------|---------|---------|
| `notes` | Brew level | Brew-process notes — operational observations about the preparation (e.g. 'washed filter paper', 'water from Brita filter', 'grinder re-calibrated'). For sensory description, use `result.tasting_notes`. | `"Washed filter paper, water from Brita filter"` |
| `result.tasting_notes` | Result object | Sensory description of the brew | `"Bright citrus acidity, caramel sweetness, clean finish"` |

Both are optional freeform strings with `maxLength: 2000`. The schema does not enforce content type — this is a documentation distinction to guide tool UX.

### Full v0.4 Data Structure (for Architect)

```yaml
brewspec_version: "0.4"          # required, const "0.4"
brews:
  - date: "2026-02-21"           # required — YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
    type: "pour_over"             # required — enum: immersion | pour_over | espresso | hybrid
    dose_g: 18                    # required — number, > 0
    water_weight_g: 280           # required — number, > 0
    method: "Hario V60"          # optional — freeform string, minLength: 1, maxLength: 100
    water_volume_ml: 280         # optional — number, > 0
    water_temp_c: 96             # optional — number, 0–100 inclusive
    grind: "medium_fine"         # optional — enum: turkish|espresso|fine|medium_fine|medium|medium_coarse|coarse; CHANGED from freeform in v0.3
    duration_s: 180              # optional — number, > 0
    notes: "Washed filter paper" # optional — freeform string, minLength: 1, maxLength: 2000
    coffee:                      # optional object — unchanged from v0.3
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    water:                       # optional object — unchanged from v0.3
      ppm: 150
    equipment:                   # optional object — unchanged from v0.3
      grinder: "Comandante C40"
      brewer: "Hario V60 02"
    result:                      # optional object — NEW in v0.4
      tds: 1.38                  # optional — number, > 0 (MOVED from brew level)
      ey: 20.1                   # optional — number, > 0 (MOVED from brew level)
      brix: 1.5                  # optional — number, >= 0 (NEW)
      tasting_notes: "Bright citrus, caramel finish"  # optional — string, maxLength 2000 (NEW)
      ratings:                   # optional object (NEW)
        overall: 4               # optional — integer 1–5
        fragrance: 3             # optional — integer 1–5
        aroma: 4                 # optional — integer 1–5
        flavour: 5               # optional — integer 1–5
        aftertaste: 4            # optional — integer 1–5
        acidity: 5               # optional — integer 1–5
        sweetness: 3             # optional — integer 1–5
        mouthfeel: 4             # optional — integer 1–5
```

Fields removed from v0.3: `tds` (flat), `ey` (flat), `rating` (flat).

---

## Security Requirements

**Data sensitivity:**
- `result.tasting_notes` and the existing `notes` field contain personal brew impressions. Low sensitivity but treated as user-generated personal data consistent with the privacy principle: local-only, user-controlled, no cloud in v0.4.
- `result.ratings` are personal evaluations. Low sensitivity.
- `brix` is a numeric measurement. No PII risk.
- Date-only values (`2026-02-21`) carry slightly less temporal precision than full datetimes. This is a privacy improvement, not a concern.

**Input validation:**
- `grind` enum validation: the schema enforces valid enum membership. Tools must reject values outside the enum. The enum is closed (`additionalProperties` equivalent for enums is the enum list itself).
- `result` object: `additionalProperties: false` prevents injection of unrecognised fields. Consistent with all other objects.
- `result.ratings` fields: all must be validated as integers in range 1–5. A non-integer or out-of-range value must be rejected at schema validation.
- `result.tasting_notes`: freeform string, `maxLength: 2000`. Must not be executed, evaluated, or interpolated. Stored and displayed as plain text only.
- `result.brix`: numeric, `minimum: 0`. Negative values rejected by schema.
- The validation pipeline is unchanged: safe parse → schema validation → application logic. Validation must occur before any write to persistent storage.

**File I/O:**
- No new file I/O concerns introduced. All existing controls (path traversal checks, file size limit, `yaml.safe_load()`) are unchanged.
- Three new invalid example files follow the same pattern as existing invalid examples: plain YAML, no executable content.

**No secrets in spec:**
- No credentials, API keys, authentication tokens, or PII in any example file.
- Date values in examples are fictitious brew dates.

---

## Dependencies

**Upstream:**
- `brewspec-v0.3` (done) — v0.4 builds on the v0.3 schema and spec document

**Downstream:**
- `brewlog-cli-v0.3` (ready_for_spec) — blocked on v0.4 for the date-only input UX improvement. The CLI spec should not be written until v0.4 ships or the date format AC is confirmed in-scope.
- All future products and third-party tools building against BrewSpec. The breaking changes in v0.4 mean tools targeting v0.3 will need to update.

**External:**
- JSON Schema Draft 2020-12 — unchanged
- ISO 8601 standard — unchanged (both accepted date formats are valid ISO 8601)
- GitHub raw content URL for schema `$id` — unchanged

---

## Success Metrics

- **Correctness**: JSON Schema v0.4 passes meta-validation (is itself a valid JSON Schema)
- **Completeness**: All acceptance criteria AC-1 through AC-43 met
- **Breaking changes documented**: The Backward Compatibility section gives a developer a complete migration path from v0.3 in under 5 minutes
- **Unblocking**: BrewLog CLI v0.3 can implement date-only date input after v0.4 ships
- **Test suite**: All tests pass (100%); new tests cover dual date format, grind enum, result object structure, ratings range, brix constraints, removed flat fields, and version const rejection
- **Example coverage**: At least one valid example demonstrates all new fields in a realistic brew record

---

## Open Questions

- [x] **`duration_s` float** — resolved: keep as `Optional[int]`. Fractions of a second are too precise for a logging tool.
- [x] **Timezone offsets** — resolved: Z-only for full datetime. Date-only format solves the UX problem; timezone offsets create data comparability issues in analytics.
- [x] **`grind` freeform fallback** — resolved: strict enum only. Freeform fallback defeats the standardization goal.
- [x] **`result` object breaking change** — resolved: strict move. `tds`, `ey`, and `rating` do not remain at flat brew level. Migration path documented.
- [x] **`rating` scale migration** — resolved: old 1–5 `rating` field is removed. New `result.ratings` dimensions use the same 1–5 scale. Migration is direct: v0.3 `rating: 4` maps to `result.ratings.overall: 4`.
- [x] **`grind` enum completeness** — resolved: 7 values finalized: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`. `turkish` replaces `powder`; `espresso` replaces `extra_fine`; `extra_coarse` removed.
- [ ] **BrewLog CLI v0.3 `ratings` UX** — when logging via `brewlog add`, should the CLI prompt for individual rating dimensions or accept an `--overall` shortcut that only sets `result.ratings.overall`? This is a CLI UX question for the BrewLog v0.3 spec. Noted here as a dependency assumption.
