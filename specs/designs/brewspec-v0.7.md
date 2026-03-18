# Design: BrewSpec v0.7

**Feature:** brewspec-v0.7
**Author:** architect
**Created:** 2026-03-16
**Input:** specs/products/brewspec-v0.7.md
**Baseline:** specs/designs/brewspec-v0.6.md
**Status:** Ready for Dev

---

## Overview

BrewSpec v0.7 makes two targeted changes to the schema. First, it adds `result.yield_g` — an optional positive number representing the output weight of a brew in grams. This field primarily serves espresso (where yield is a first-class recipe metric distinct from water input) but is valid for any brew type. Second, it removes the `required` array from the brew object, making `date`, `type`, `dose_g`, and `water_weight_g` optional. This unblocks partial BrewSpec exports — such as a Calibrate component card representing only coffee or equipment metadata — without requiring fabricated field values.

The yield addition is a non-breaking additive change. The removal of required constraints is a breaking change for validators (compiled schemas must be updated) but is not a breaking change for existing documents — all v0.6-valid documents remain valid under v0.7 with only a `brewspec_version` bump.

The BrewLog CLI requires a schema version reference update and minor additions to its Pydantic model and database schema to accept and store `result.yield_g`. No CLI commands change; the new field follows the same path as existing result fields.

---

## 1. Changes Required

### 1.1 JSON Schema: `brewspec_version` constant

Change the `const` value from `"0.6"` to `"0.7"` and update the `title` string.

Before:
```json
"title": "BrewSpec v0.6",
"brewspec_version": {
  "const": "0.6",
  "description": "The BrewSpec version. Must be \"0.6\"."
}
```

After:
```json
"title": "BrewSpec v0.7",
"brewspec_version": {
  "const": "0.7",
  "description": "The BrewSpec version. Must be \"0.7\"."
}
```

### 1.2 JSON Schema: Remove `required` array from `$defs/brew`

In v0.6, the `brew` definition has:
```json
"brew": {
  "type": "object",
  "required": ["date", "type", "dose_g", "water_weight_g"],
  "additionalProperties": false,
  "properties": { ... }
}
```

In v0.7, remove the `required` key entirely:
```json
"brew": {
  "type": "object",
  "additionalProperties": false,
  "properties": { ... }
}
```

The top-level schema `required` array — `["brewspec_version", "brews"]` — is unchanged. The `brews` array itself retains `"minItems": 1`. The change is scoped entirely to the `brew` object definition.

### 1.3 JSON Schema: Add `yield_g` to `$defs/result`

Add one property to the `result` object definition. The `result` definition currently has five properties: `tds`, `ey`, `brix`, `tasting_notes`, `ratings`. Add `yield_g` as a sixth.

Insertion (after `brix`, before `tasting_notes` — alphabetical placement by convention is not required; insert after `brix` for logical grouping with measurement fields):

```json
"yield_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Output weight of the brew in grams. For espresso, this is the liquid collected in the cup (distinct from water_weight_g, which is the input water). For other brew types, yield_g may approximate water_weight_g less absorbed water. Must be > 0 if present."
}
```

The full updated `result` definition in context:

```json
"result": {
  "type": "object",
  "additionalProperties": false,
  "description": "Optional brew outcome descriptor. Groups measurements and sensory evaluation. All fields optional.",
  "properties": {
    "tds": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Total dissolved solids percentage of the finished brew. Must be > 0 if present."
    },
    "ey": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Extraction yield as a percentage (e.g., 20.1 for 20.1%). Must be > 0 if present. No maximum enforced."
    },
    "brix": {
      "type": "number",
      "minimum": 0,
      "description": "Dissolved sugar content in degrees Brix. A value of 0 is valid (distilled water). Must be >= 0 if present."
    },
    "yield_g": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Output weight of the brew in grams. For espresso, this is the liquid collected in the cup (distinct from water_weight_g, which is the input water). For other brew types, yield_g may approximate water_weight_g less absorbed water. Must be > 0 if present."
    },
    "tasting_notes": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000,
      "description": "Sensory description of the brew (e.g. 'Bright citrus acidity, caramel sweetness, clean finish'). For brew-process notes, use the top-level notes field."
    },
    "ratings": {
      "$ref": "#/$defs/ratings"
    }
  }
}
```

### 1.4 New valid example: `examples/valid/espresso_with_yield.yaml`

Create this file demonstrating espresso with `result.yield_g`:

```yaml
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "espresso"
    dose_g: 18.0
    water_weight_g: 36.0
    grind: "espresso"
    duration_s: 28
    equipment:
      grinder: "Comandante C40 MK4"
      brewer: "La Marzocco Linea Mini"
      grinder_setting: 12
    result:
      yield_g: 36.5
      tds: 9.2
      tasting_notes: "Caramel sweetness, low acidity, thick mouthfeel"
      ratings:
        overall: 4
        flavour: 4
        mouthfeel: 5
```

### 1.5 New invalid example: `examples/invalid/invalid_yield_zero.yaml`

Create this file demonstrating rejection of `yield_g: 0`:

```yaml
brewspec_version: "0.7"
brews:
  - date: "2026-03-16"
    type: "espresso"
    dose_g: 18.0
    water_weight_g: 36.0
    result:
      yield_g: 0
```

### 1.6 Update existing valid examples

All files in `examples/valid/` must have `brewspec_version` bumped from `"0.6"` to `"0.7"`. The test suite validates every file in `examples/valid/` against the current schema, so any file still carrying `"0.6"` will fail the version `const` check.

The existing invalid examples in `examples/invalid/` that test structural errors (not the version value) do not need their `brewspec_version` updated — they are expected to fail anyway, and many may fail for multiple reasons. However, if any invalid example relies on an exact version match to isolate a single error, update those too. Review each: if the `brewspec_version` is `"0.6"` and the intended failure is not version-related, update it to `"0.7"` so the test remains focused on its intended violation.

### 1.7 Spec document: `brewspec-v0.7.md`

The dev must write a new public spec document in the brewspec repo root. Archive the existing `brewspec-v0.6.md` to `versions/brewspec-v0.6.md` first, then write `brewspec-v0.7.md`. See Section 5 for full content requirements.

---

## 2. Data Models

### 2.1 Pydantic Models (BrewLog CLI)

The BrewLog CLI defines Pydantic models in `brewlog/src/brewlog/models.py`. The `ResultInput` model needs one new optional field. No other models change.

Current `ResultInput` (inferred from v0.6 schema coverage):
```python
class ResultInput(BaseModel):
    tds: float | None = None
    ey: float | None = None
    brix: float | None = None
    tasting_notes: str | None = None
    ratings: RatingsInput | None = None
```

Updated `ResultInput`:
```python
class ResultInput(BaseModel):
    tds: float | None = None
    ey: float | None = None
    brix: float | None = None
    yield_g: float | None = None
    tasting_notes: str | None = None
    ratings: RatingsInput | None = None
```

Field constraints must match the schema: `yield_g` must be `> 0` when present. Add a Pydantic field validator:

```python
from pydantic import field_validator

class ResultInput(BaseModel):
    tds: float | None = None
    ey: float | None = None
    brix: float | None = None
    yield_g: float | None = None
    tasting_notes: str | None = None
    ratings: RatingsInput | None = None

    @field_validator("yield_g")
    @classmethod
    def yield_g_must_be_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("yield_g must be > 0")
        return v
```

The `BrewInput` model (top-level brew object) does not change — `date`, `type`, `dose_g`, and `water_weight_g` are already defined as optional in the CLI model (the CLI has always allowed partial input for the `update` command). Confirm this is the case; if any of these four fields are currently `Field(...)` (required), make them optional with `= None`.

### 2.2 SQLite Schema (BrewLog CLI)

Add one new column to the `brews` table: `result_yield_g REAL`.

This column is added via the existing migration mechanism in `db.py`. Add to the migration dict (the equivalent of `_V6_MIGRATION_COLUMNS`):

```python
_V7_MIGRATION_COLUMNS = {
    "result_yield_g": "REAL",
}
```

The `_apply_migrations()` function iterates over migration dicts and adds columns that do not yet exist. Adding `_V7_MIGRATION_COLUMNS` to the migration sequence ensures the column is present on both new databases and upgraded existing databases.

The updated `_init_schema()` DDL should include `result_yield_g REAL` in the `brews` table alongside the other result columns (`result_tds`, `result_ey`, `result_brix`, `result_tasting_notes`).

No other DDL changes are required.

### 2.3 BrewLog CLI: Serialisation and Deserialisation

Two code paths handle `result` fields and must be updated:

**`serialise.py` (DB row → BrewSpec export):** Add `result_yield_g` to the `result` object construction. The pattern follows the existing result fields. When `result_yield_g` is not NULL, include `yield_g` in the exported `result` dict.

**`import_.py` (BrewSpec document → DB row):** Add extraction of `result.yield_g` from the imported brew dict and storage to `result_yield_g`. Follow the same pattern as `result.tds` → `result_tds`.

**`show.py` (DB row → terminal display):** Add display of `result_yield_g` when present. Place it alongside the other result measurement fields (TDS, EY, Brix). Format: `Yield: {value}g`.

**`add.py` and `update.py`:** These commands do not need a `--yield-g` flag in v0.7. The field is a measured result typically captured at brew time by a scale, not entered during the logging flow. The import path handles it for tools that export yield data. If a flag is needed in the future, it follows the same pattern as `--tds`. Mark this as an intentional deferral — no flag in v0.7.

### 2.4 BrewLog CLI: Schema Version Acceptance

The CLI ships its own copy of the BrewSpec JSON Schema at `brewlog/src/brewlog/brewspec.schema.json`. This file must be updated to v0.7 (same changes as the root `brewspec.schema.json`). The import validator uses this bundled schema to check incoming documents, so leaving it at v0.6 would reject v0.7 documents.

The rejection message referencing the version (e.g., `_V06_REQUIRED_MSG` or equivalent) should be updated to reference v0.7.

---

## 3. CLI Interface

No new commands or flags in v0.7. The `show` command display update (Section 2.3) is the only visible change from the user's perspective.

---

## 4. Architecture Decision Records

No new cross-cutting decisions. The two changes in this version follow directly from established patterns:
- Adding an optional field to `result` follows the same pattern as `tds`, `ey`, `brix` (precedent in v0.2–v0.6).
- Removing required constraints is consistent with the "Schema must allow partial representation" principle established in `specs/arch/principles.md` under "BrewSpec is the canonical data interchange format" — the schema serves as interchange, not enforcement of complete data.

No ADR is required.

---

## 5. Public Spec Document

The dev must produce `brewspec-v0.7.md` in the brewspec repo root. Archive `brewspec-v0.6.md` to `versions/brewspec-v0.6.md` before writing the new file.

### 5.1 Structure

The spec document must include these sections in order:

1. **Overview** — What BrewSpec is; scope of v0.7
2. **Field Reference** — Updated tables for all objects, with `yield_g` added to the Result Object table and required status updated for the four brew object fields
3. **What Changed in v0.7** — New fields and breaking changes clearly separated
4. **Validation** — Guidance unchanged from v0.6; retain the safe-parse pipeline, validate at storage time
5. **Backward Compatibility** — Migration from v0.6 is a version bump only; breaking change note for validator authors
6. **Examples** — Updated examples list including the two new v0.7 examples

### 5.2 Field Reference Updates

**Brew Object table** — update the Required column for four fields from `Required` to `Optional`:

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `date` | string | Optional | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` | Brew date or datetime (UTC) | `"2026-02-21"`, `"2026-02-15T08:30:00Z"` |
| `type` | string | Optional | Enum: `immersion`, `pour_over`, `espresso`, `hybrid` | Brew method category | `"pour_over"` |
| `dose_g` | number | Optional | > 0 (exclusive) | Coffee dose in grams | `20`, `18` |
| `water_weight_g` | number | Optional | > 0 (exclusive) | Water weight in grams | `320`, `36` |

All other brew object fields remain as previously specified.

**Result Object table** — add `yield_g`:

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `yield_g` | number | Optional | > 0 (exclusive) | Output weight of the brew in grams. For espresso, this is the liquid collected in the cup. Distinct from `water_weight_g` (input water). Both fields may be recorded for espresso to capture the full dose-yield relationship. New in v0.7. | `36.5`, `40` |

Insert this row after `brix` and before `tasting_notes`.

### 5.3 Espresso Context Note

Under the `yield_g` field in the spec document, include this note:

> For espresso, brewers set a target yield as part of the recipe (e.g., "18 g in, 36 g out" → 2:1 ratio). The measured output weight at brew time is the value stored in `result.yield_g`. The separation between `water_weight_g` (input) and `result.yield_g` (output) accounts for puck absorption, typically 2–4 g for espresso. Tools that implement a process card model (such as Calibrate) may additionally store a target yield on their internal process card — that is an application-level concern beyond the scope of BrewSpec.

### 5.4 What Changed in v0.7

**New Fields**

- **`result.yield_g`** (`number`, optional, `exclusiveMinimum: 0`) — Output weight of the brew in grams. Primarily used for espresso where yield is a first-class recipe metric distinct from input water weight. Also valid for other brew types. New in v0.7.

**Breaking Changes**

- **Brew object `required` constraint removed** — The four previously required brew object fields (`date`, `type`, `dose_g`, `water_weight_g`) are now optional. This is a breaking change for validators: compiled or cached schemas must be updated. It is **not** a breaking change for existing documents — all v0.6-valid documents remain valid under v0.7. Documents that include all four fields continue to pass validation unchanged.

### 5.5 Backward Compatibility Section

**Documents from v0.6**

v0.7 introduces no changes that cause v0.6-valid documents to fail v0.7 validation. Migration from v0.6 to v0.7 requires only a `brewspec_version` bump:

```yaml
# Before
brewspec_version: "0.6"

# After
brewspec_version: "0.7"
```

No structural changes are required. All field values, types, and constraints from v0.6 remain valid in v0.7.

**Validator migration note**

Tools that compiled or cached the v0.6 schema for performance (e.g., using `jsonschema.Draft202012Validator(schema)` with a pre-compiled schema object) must re-compile with the v0.7 schema. The `$defs/brew` definition no longer has a `required` array; any code that assumed these fields were always present must add null checks before accessing `date`, `type`, `dose_g`, or `water_weight_g`.

---

## 6. File Manifest

| File | Repo | Operation | Notes |
|------|------|-----------|-------|
| `brewspec.schema.json` | brewspec | Modify | Version bump, remove `required` from brew def, add `yield_g` to result def |
| `brewspec-v0.7.md` | brewspec | Create | New root spec doc per Section 5 |
| `versions/brewspec-v0.6.md` | brewspec | Archive | Copy `brewspec-v0.6.md` here before writing new root spec |
| `examples/valid/espresso_with_yield.yaml` | brewspec | Create | New valid example per Section 1.4 |
| `examples/invalid/invalid_yield_zero.yaml` | brewspec | Create | New invalid example per Section 1.5 |
| `examples/valid/*.yaml` (all existing) | brewspec | Modify | Bump `brewspec_version` from `"0.6"` to `"0.7"` |
| `examples/invalid/*.yaml` (non-version tests) | brewspec | Modify | Bump `brewspec_version` from `"0.6"` to `"0.7"` where the intended failure is not version-related |
| `tests/test_brewspec_schema.py` | brewspec | Modify | Add test cases per Section 7 |
| `brewlog/src/brewlog/brewspec.schema.json` | brewspec | Modify | Sync with root schema — same changes |
| `brewlog/src/brewlog/models.py` | brewspec | Modify | Add `yield_g` to `ResultInput`; confirm brew fields are optional |
| `brewlog/src/brewlog/db.py` | brewspec | Modify | Add `_V7_MIGRATION_COLUMNS`; add `result_yield_g REAL` to `_init_schema()` DDL |
| `brewlog/src/brewlog/serialise.py` | brewspec | Modify | Add `result_yield_g` to result export |
| `brewlog/src/brewlog/import_.py` | brewspec | Modify | Extract and store `result.yield_g`; update version acceptance to v0.7 |
| `brewlog/src/brewlog/show.py` | brewspec | Modify | Display `result_yield_g` when present |
| `brewlog/tests/test_*.py` | brewspec | Modify | Add test cases per Section 7 |

---

## 7. Test Strategy

### AC-1: `result.yield_g` valid when positive

| Test | Input | Expected |
|------|-------|----------|
| Typical espresso yield | `result: {yield_g: 36.5}` | passes validation |
| Minimum viable yield | `result: {yield_g: 0.1}` | passes validation |
| Large yield | `result: {yield_g: 500}` | passes validation |
| Integer yield | `result: {yield_g: 36}` | passes validation |
| `espresso_with_yield.yaml` example | full file | passes validation |

### AC-2: `result.yield_g` invalid when zero or negative

| Test | Input | Expected |
|------|-------|----------|
| Zero yield | `result: {yield_g: 0}` | fails — `exclusiveMinimum: 0` |
| Negative yield | `result: {yield_g: -5}` | fails — `exclusiveMinimum: 0` |
| `invalid_yield_zero.yaml` example | full file | fails validation |

### AC-3: `result.yield_g` optional

| Test | Input | Expected |
|------|-------|----------|
| Result present, no yield | `result: {tds: 9.2}` | passes validation |
| No result at all | brew with no `result` key | passes validation |

### AC-4: Four brew fields are optional

| Test | Input | Expected |
|------|-------|----------|
| Omit all four | brew object `{}` (empty) | passes validation |
| Omit `date` only | brew without `date` | passes validation |
| Omit `type` only | brew without `type` | passes validation |
| Omit `dose_g` only | brew without `dose_g` | passes validation |
| Omit `water_weight_g` only | brew without `water_weight_g` | passes validation |
| Omit all four with other fields | brew with only `method` | passes validation |
| Minimal document | `{brewspec_version: "0.7", brews: [{}]}` | passes validation |

### AC-5: v0.6-valid documents pass under v0.7

| Test | Input | Expected |
|------|-------|----------|
| All four fields present | v0.6 doc with `brewspec_version` bumped to `"0.7"` | passes validation |
| `pour_over.yaml` bumped | existing valid example with version `"0.7"` | passes validation |
| `espresso.yaml` bumped | existing valid example with version `"0.7"` | passes validation |

### AC-6 / AC-7: Spec document content (documentation test — verify by inspection)

Confirm `brewspec-v0.7.md` contains:
- `yield_g` in the Result Object field reference table
- Espresso context note under `yield_g`
- "What Changed in v0.7" section with both changes
- Breaking change note for validators

### AC-8: JSON Schema structure

| Test | Input | Expected |
|------|-------|----------|
| `$defs/brew` has no `required` key | inspect schema JSON | `required` key absent from brew definition |
| Top-level `required` unchanged | inspect schema JSON | `["brewspec_version", "brews"]` |
| `$defs/result` contains `yield_g` | inspect schema JSON | `yield_g` present with `exclusiveMinimum: 0` |
| Version const is `"0.7"` | inspect schema JSON | `const: "0.7"` |

### AC-9 / AC-10: Example files (file existence tests)

| Test | Condition | Expected |
|------|-----------|----------|
| `espresso_with_yield.yaml` exists | file present | passes validation against v0.7 schema |
| `invalid_yield_zero.yaml` exists | file present | fails validation against v0.7 schema |

### BrewLog CLI: `result_yield_g` column migration

| Test | Condition | Expected |
|------|-----------|----------|
| Column added to new DB | fresh install | `result_yield_g REAL` column present |
| Column added to existing DB | pre-v0.7 database | migration adds column without error |
| Idempotent migration | run migration twice | no error, column not duplicated |

### BrewLog CLI: `yield_g` import/export round-trip

| Test | Input | Expected |
|------|-------|----------|
| Import v0.7 doc with yield | `espresso_with_yield.yaml` | `result_yield_g` stored in DB |
| Export brew with yield | DB row with `result_yield_g = 36.5` | exported YAML contains `result.yield_g: 36.5` |
| Import v0.7 doc without yield | any v0.7 valid doc with no `result.yield_g` | import succeeds; `result_yield_g` is NULL |
| Export brew without yield | DB row with `result_yield_g IS NULL` | exported YAML has no `result.yield_g` key |

### BrewLog CLI: `show` command display

| Test | Condition | Expected |
|------|-----------|----------|
| Show brew with yield | row has `result_yield_g` | output contains `Yield: 36.5g` |
| Show brew without yield | row has NULL `result_yield_g` | no yield line in output |

### BrewLog CLI: Pydantic model validation

| Test | Input | Expected |
|------|-------|----------|
| `yield_g = 0` rejected | `ResultInput(yield_g=0)` | `ValidationError` |
| `yield_g = -1` rejected | `ResultInput(yield_g=-1)` | `ValidationError` |
| `yield_g = 36.5` accepted | `ResultInput(yield_g=36.5)` | model valid |
| `yield_g = None` accepted | `ResultInput()` | model valid |

---

## 8. Security Considerations

**Input validation**

`result.yield_g` is validated at two layers:
1. JSON Schema (`exclusiveMinimum: 0`, type `number`) — rejects non-numeric input and values <= 0 before any storage.
2. Pydantic `field_validator` in `ResultInput` — provides the same constraint at the CLI model layer.

The removal of `required` constraints does not weaken the validation pipeline. Schema validation still runs on all inputs; fewer fields are required does not mean fewer fields are validated. Fields that are present are still type-checked and constraint-checked. Fields that are absent are simply absent.

**File I/O**

No change to the safe-parse requirement. The existing pipeline (`yaml.safe_load` → JSON Schema validation → application logic) is unchanged. The two new example files (one valid, one invalid) are authored by the dev and not user-supplied; they are used in tests, not at runtime.

**SQL**

`result_yield_g` is stored as `REAL` in SQLite. The value is sourced from the Pydantic model (already validated). The INSERT and UPDATE statements that write this column are parameterised (the existing pattern in `db.py` uses `?` placeholders). No f-string interpolation of user data.

**Error messages**

No new user-facing error messages. The existing validation error surface for result fields (e.g., "must be > 0") covers `yield_g` without special handling. The Pydantic validator message ("yield_g must be > 0") does not expose internal paths or stack traces.

**Data integrity**

The `result_yield_g REAL` column has no NOT NULL constraint, consistent with other optional result columns. NULL represents "not recorded". Downstream display code must handle NULL cleanly (the `show.py` pattern of `if value is not None` is already established).

The trust boundary is: user input → safe parse → Pydantic validation → JSON Schema validation → parameterised SQL write. `yield_g` enters at the import path (file content) or CLI add/update path (direct user input). Both paths go through the full validation stack.

---

## 9. TDD Implementation Order

1. Write failing tests: JSON Schema structure checks (AC-8) — verify `required` absent from `$defs/brew`, `yield_g` present in `$defs/result`, version const is `"0.7"`.
2. Update `brewspec.schema.json` (changes in Sections 1.1, 1.2, 1.3). Tests from step 1 pass.
3. Write failing tests: `yield_g` valid cases (AC-1), invalid cases (AC-2), optional (AC-3).
4. Verify tests from step 3 pass with the updated schema (no code change needed — schema is already updated).
5. Write failing tests: four fields optional (AC-4), v0.6 backward compat (AC-5).
6. Verify tests from steps 5 pass.
7. Create example files (Sections 1.4, 1.5). Write file existence and validation tests (AC-9, AC-10).
8. Bump `brewspec_version` in all existing valid examples (Section 1.6). Confirm full valid example suite passes.
9. Write failing tests: BrewLog CLI `ResultInput` Pydantic validation.
10. Update `models.py` (Section 2.1). Tests from step 9 pass.
11. Write failing tests: BrewLog CLI `result_yield_g` column migration (new DB and existing DB).
12. Update `db.py` (Section 2.2). Tests from step 11 pass.
13. Write failing tests: import/export round-trip with `yield_g`.
14. Update `serialise.py`, `import_.py`, and the bundled `brewspec.schema.json` in brewlog (Sections 2.3, 2.4). Tests from step 13 pass.
15. Write failing tests: `show` command display.
16. Update `show.py` (Section 2.3). Tests from step 15 pass.
17. Run full test suite — confirm all pass.
18. Run `ruff check .` — fix any lint errors.
