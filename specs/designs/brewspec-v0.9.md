# Design: BrewSpec v0.9

**Feature:** brewspec-v0.9
**Author:** architect
**Created:** 2026-03-21
**Input:** specs/products/brewspec-v0.9.md
**Baseline:** specs/designs/brewspec-v0.8.md
**Status:** Ready for Dev

---

## Overview

BrewSpec v0.9 is a single-concern release: align all eight rating fields in `result.ratings` with the SCA Coffee Value Assessment (CVA) standard (SCA-104, 2024) by expanding the scale from 1-5 to 1-9. The field names are already correct after v0.8 (`mouthfeel` replaced `body`). The only change is the numeric range. The schema version bumps to `"0.9"`. All other fields are unchanged.

This is a partially breaking change: v0.8 documents with ratings values 1-5 remain valid under v0.9 with only a version bump. V0.9 documents with ratings values 6-9 are rejected by the v0.8 schema. The existing invalid example `examples/invalid/rating_out_of_range.yaml` must be updated — its current value of `6` becomes valid under v0.9, so it must change to `10`.

Architecture principles trace: schema constraints must be enforceable with valid and invalid examples (arch principle "Schema constraints should be enforceable"); breaking changes require a version bump and migration guidance (arch principle "Additive changes are preferred over breaking changes").

---

## 1. Changes Required

### 1.1 `brewspec.schema.json` — Version Bump

**Before:**
```json
"title": "BrewSpec v0.8",
"brewspec_version": {
  "const": "0.8",
  "description": "The BrewSpec version. Must be \"0.8\"."
}
```

**After:**
```json
"title": "BrewSpec v0.9",
"brewspec_version": {
  "const": "0.9",
  "description": "The BrewSpec version. Must be \"0.9\"."
}
```

No other top-level or `$defs` structures change.

### 1.2 `brewspec.schema.json` — `$defs/ratings` Object Description

Update the description on the `ratings` object to reference the CVA 1-9 hedonic scale and the SCA-104 standard, replacing the v0.8 reference to the legacy SCA cupping protocol.

**Before:**
```json
"ratings": {
  "type": "object",
  "additionalProperties": false,
  "description": "Optional multi-dimensional sensory ratings. Dimensions align with SCA cupping protocol. All fields optional integers 1-5.",
  ...
}
```

**After:**
```json
"ratings": {
  "type": "object",
  "additionalProperties": false,
  "description": "Optional multi-dimensional sensory ratings. Dimensions align with the SCA Coffee Value Assessment (CVA) affective protocol (SCA-104, 2024). All fields optional integers 1-9 (CVA hedonic scale: 1 = dislike extremely, 9 = like extremely).",
  ...
}
```

### 1.3 `brewspec.schema.json` — All Eight Ratings Fields: `minimum` and `maximum`

Every ratings field changes from `maximum: 5` to `maximum: 9`. The `minimum: 1` constraint is unchanged. The description for each field is updated to reflect the 1-9 scale endpoints using the CVA anchor labels.

Field-by-field before/after:

**`overall`**

Before:
```json
"overall": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Holistic impression. 1 = poor, 5 = excellent."
}
```

After:
```json
"overall": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Holistic impression. 1 = dislike extremely, 9 = like extremely."
}
```

**`fragrance`**

Before:
```json
"fragrance": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Dry grounds aroma before water is added."
}
```

After:
```json
"fragrance": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Dry grounds aroma before water is added. 1 = dislike extremely, 9 = like extremely."
}
```

**`aroma`**

Before:
```json
"aroma": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Wet aroma after water is added."
}
```

After:
```json
"aroma": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Wet aroma after water is added. 1 = dislike extremely, 9 = like extremely."
}
```

**`flavour`** (British spelling preserved — no change to field name)

Before:
```json
"flavour": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Taste and aroma experienced during drinking."
}
```

After:
```json
"flavour": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Taste and aroma experienced during drinking. 1 = dislike extremely, 9 = like extremely."
}
```

**`aftertaste`**

Before:
```json
"aftertaste": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Length and quality of positive flavour attributes after swallowing."
}
```

After:
```json
"aftertaste": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Length and quality of positive flavour attributes after swallowing. 1 = dislike extremely, 9 = like extremely."
}
```

**`acidity`**

Before:
```json
"acidity": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Quality (not quantity) of acidity; brightness."
}
```

After:
```json
"acidity": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Quality (not quantity) of acidity; brightness. 1 = dislike extremely, 9 = like extremely."
}
```

**`sweetness`**

Before:
```json
"sweetness": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Perceived sweetness."
}
```

After:
```json
"sweetness": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Perceived sweetness. 1 = dislike extremely, 9 = like extremely."
}
```

**`mouthfeel`**

Before:
```json
"mouthfeel": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "description": "Tactile sensation; body and texture."
}
```

After:
```json
"mouthfeel": {
  "type": "integer",
  "minimum": 1,
  "maximum": 9,
  "description": "Tactile sensation; body and texture. 1 = dislike extremely, 9 = like extremely."
}
```

### 1.4 `examples/invalid/rating_out_of_range.yaml` — Update to Value 10

The current file tests `overall: 6`, which was out-of-range on the 1-5 scale. Under v0.9, `6` is valid. The file must be updated to test `overall: 10` (above the new maximum of 9). The comment and `brewspec_version` must also be updated.

**Before:**
```yaml
# Invalid: result.ratings.overall value of 6 exceeds the maximum of 5.
# All rating dimension fields (overall, fragrance, aroma, flavour, aftertaste,
# acidity, sweetness, mouthfeel) accept integers 1-5 inclusive only.
brewspec_version: "0.8"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    result:
      ratings:
        overall: 6
```

**After:**
```yaml
# Invalid: result.ratings.overall value of 10 exceeds the maximum of 9.
# All rating dimension fields (overall, fragrance, aroma, flavour, aftertaste,
# acidity, sweetness, mouthfeel) accept integers 1-9 inclusive only.
brewspec_version: "0.9"
brews:
  - date: "2026-02-28"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
    result:
      ratings:
        overall: 10
```

### 1.5 Valid Example Files — Version Bump

All valid example files must have `brewspec_version` updated from `"0.8"` to `"0.9"`. Rating values do not need to change — all existing 1-5 values remain valid on the 1-9 scale.

Files requiring version bump only (no rating value changes):

| File | Has ratings | Rating values present |
|------|-------------|----------------------|
| `examples/valid/pour_over.yaml` | Yes | overall: 4, aroma: 4, acidity: 5 |
| `examples/valid/pour_over.json` | Yes | overall: 4, aroma: 4, acidity: 5 |
| `examples/valid/pour_over_date_only.yaml` | Yes | overall: 4, fragrance: 3, aroma: 4, flavour: 5, aftertaste: 4, acidity: 5, sweetness: 3, mouthfeel: 4 |
| `examples/valid/espresso.yaml` | Yes | overall: 4, mouthfeel: 5 |
| `examples/valid/espresso_with_yield.yaml` | Yes | overall: 4, flavour: 4, mouthfeel: 5 |
| `examples/valid/equipment.yaml` | Yes | overall: 5 |
| `examples/valid/hybrid.yaml` | Yes | overall: 4 |
| `examples/valid/multi_brew.yaml` | Yes | overall: 4; overall: 3 |
| `examples/valid/valid_single_origin_full.yaml` | Yes | overall: 5, flavour: 5, acidity: 4 |
| `examples/valid/valid_single_origin_with_varietal.yaml` | Yes | overall: 5, flavour: 5, acidity: 4 |
| `examples/valid/valid_blend_with_per_origin_varietal.yaml` | Yes | overall: 4, flavour: 4 |
| `examples/valid/valid_blend_origin.yaml` | No | — |
| `examples/valid/immersion_minimal.yaml` | No | — |
| `examples/valid/minimal_no_required_fields.yaml` | No | — |
| `examples/valid/valid_brew_ratio.yaml` | No | — |
| `examples/valid/valid_grinder_setting.yaml` | No | — |
| `examples/valid/valid_equipment_notes.yaml` | No | — |

All files receive `brewspec_version: "0.9"`. No rating integer values change.

### 1.6 `examples/valid/light_roast_ethiopian.yaml` — Add 6-9 Range Rating Value

This file already has a `ratings` object with all 1-5 values. Add `aftertaste: 7` to demonstrate a value in the 6-9 range that was previously invalid under v0.8. This satisfies AC-16. The file also receives the version bump from section 1.5.

**Before (ratings block):**
```yaml
    result:
      tds: 1.38
      ey: 20.1
      yield_g: 260.0
      tasting_notes: "Bright blueberry, jasmine, honey sweetness"
      ratings:
        overall: 5
        fragrance: 4
        aroma: 5
        flavour: 5
        acidity: 5
        sweetness: 4
        mouthfeel: 4
```

**After (ratings block):**
```yaml
    result:
      tds: 1.38
      ey: 20.1
      yield_g: 260.0
      tasting_notes: "Bright blueberry, jasmine, honey sweetness"
      ratings:
        overall: 5
        fragrance: 4
        aroma: 5
        flavour: 5
        aftertaste: 7
        acidity: 5
        sweetness: 4
        mouthfeel: 4
```

`aftertaste: 7` is a natural choice — it was a field already present in the schema but not set in this example, and 7 ("like moderately") is a credible aftertaste rating for a well-regarded Ethiopian pour over.

### 1.7 Spec Document — Archive v0.8 and Write v0.9

Two file operations:

1. Copy `brewspec-v0.8.md` to `versions/brewspec-v0.8.md` (archive the previous version)
2. Write `brewspec-v0.9.md` at the repo root (the new canonical spec document)

The v0.9 spec document structure (per design template section 5.1):

1. **Overview** — Describe v0.9; include what changed
2. **Field Reference** — Complete table for all fields; ratings table updated to show `integers 1-9 (CVA hedonic scale)`
3. **What Changed in v0.9** — Scale change from 1-5 to 1-9, CVA alignment, breaking change characterisation
4. **CVA Hedonic Scale Reference** — Table of all nine anchors (1 = Dislike extremely through 9 = Like extremely) and SCA-104 reference
5. **Validation** — Carry forward from v0.8 verbatim (no change to validation pipeline)
6. **Backward Compatibility** — Migration guidance from v0.8; confirm that 1-5 values need no changes; version bump only

The ratings table in the Field Reference section must read:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `overall` | integer | No | 1-9 inclusive | Holistic impression. 1 = dislike extremely, 9 = like extremely. |
| `fragrance` | integer | No | 1-9 inclusive | Dry grounds aroma before water is added. |
| `aroma` | integer | No | 1-9 inclusive | Wet aroma after water is added. |
| `flavour` | integer | No | 1-9 inclusive | Taste and aroma experienced during drinking. |
| `aftertaste` | integer | No | 1-9 inclusive | Length and quality of positive flavour attributes after swallowing. |
| `acidity` | integer | No | 1-9 inclusive | Quality (not quantity) of acidity; brightness. |
| `sweetness` | integer | No | 1-9 inclusive | Perceived sweetness. |
| `mouthfeel` | integer | No | 1-9 inclusive | Tactile sensation; body and texture. |

The section header must read: "Ratings Object (entire object optional; all fields within optional; integers 1-9, CVA hedonic scale)".

The "What Changed in v0.9" section must cover:
- Ratings scale: all eight fields updated from `maximum: 5` to `maximum: 9`
- CVA alignment: references SCA Coffee Value Assessment (SCA-104, 2024)
- Breaking change characterisation: v0.9 documents with ratings 6-9 are rejected by v0.8 validators; existing v0.8 documents with ratings 1-5 pass v0.9 validation with only a version bump

The "Backward Compatibility" section must cover:
- Migration steps from v0.8: change `brewspec_version` from `"0.8"` to `"0.9"`; no rating values need to change
- Note that the scale expansion is one-directional: 6-9 values go from invalid to valid; 10+ values were and remain invalid

### 1.8 Test Suite — `tests/test_brewspec_schema.py`

The test file is updated in place. The following changes are required:

**1. Module docstring and `VALID_DOC` constant**

Update the module docstring from "BrewSpec v0.8" to "BrewSpec v0.9". Update `VALID_DOC` version string:

```python
VALID_DOC = {"brewspec_version": "0.9", "brews": [VALID_BREW]}
```

**2. AC-1 version tests**

- Rename `test_schema_title_is_v0_8` to `test_schema_title_is_v0_9`; update assertion to `"BrewSpec v0.9"`
- Update `test_version_must_be_0_8` to `test_version_must_be_0_9`; update version strings throughout
- Rename `test_version_const_rejects_v0_7` to `test_version_const_rejects_v0_8`; assert that `"0.8"` is rejected

All inline `"brewspec_version": "0.8"` strings in existing tests must be changed to `"0.9"`.

**3. Ratings tests — update existing**

The following existing tests require changes:

| Existing test | Required change |
|---|---|
| `test_ratings_overall_maximum_accepted` | Update doc version to `"0.9"`; rename to make intent clear that `5` remains valid (AC-4) |
| `test_ratings_above_maximum_rejected` | Docstring says "6 fails" — update to say "10 fails"; change test value from `6` to `10` (AC-7) |
| All inline `"brewspec_version": "0.8"` in ratings block | Change to `"0.9"` |

**4. Ratings tests — add new**

Add the following new test functions. Tests must be written before the schema is modified (TDD).

```
test_ratings_new_maximum_accepted          — overall: 9 passes (AC-5)
test_ratings_above_new_maximum_rejected    — overall: 10 fails (AC-7)
test_ratings_value_6_accepted              — overall: 6 passes (AC-8)
test_ratings_value_7_accepted              — overall: 7 passes (AC-8)
test_ratings_value_8_accepted              — overall: 8 passes (AC-8)
test_ratings_version_0_8_rejected          — brewspec_version "0.8" fails (AC-1)
test_ratings_all_fields_accept_minimum     — parametrized: each of 8 fields at 1 passes (AC-3)
test_ratings_all_fields_accept_5           — parametrized: each of 8 fields at 5 passes (AC-4)
test_ratings_all_fields_accept_maximum     — parametrized: each of 8 fields at 9 passes (AC-5)
test_ratings_all_fields_reject_below_min   — parametrized: each of 8 fields at 0 fails (AC-6)
test_ratings_all_fields_reject_above_max   — parametrized: each of 8 fields at 10 fails (AC-7)
```

For the parametrized tests, use `@pytest.mark.parametrize` over the list of all eight field names:

```python
RATING_FIELDS = ["overall", "fragrance", "aroma", "flavour", "aftertaste", "acidity", "sweetness", "mouthfeel"]
```

**5. File-based test — `rating_out_of_range.yaml`**

The existing file-based invalid test that loads `rating_out_of_range.yaml` continues to function correctly after the file is updated to value `10` — no test code change needed for that assertion, but confirm the test does not hardcode the value `6` anywhere.

---

## 2. Data Models

This is a schema-only release. No Pydantic models, no SQLite schema, no CLI interface. This section is not applicable.

SQLite schema: unchanged. No action.

Pydantic models (BrewLog CLI): the CLI's Pydantic `Ratings` model will be updated in the separate `brewlog-cli-v0.8` task, which depends on this spec.

---

## 3. CLI Interface

Not applicable. This is a BrewSpec schema task. The CLI is updated separately in `brewlog-cli-v0.8`.

---

## 4. Architecture Decision Records

An ADR is warranted. The rating scale is a cross-cutting decision that affects the schema, all downstream tools (BrewLog CLI, future tool builders), and backward compatibility. The decision to adopt the CVA 1-9 scale rather than keeping a custom scale or adopting a different standard is a significant, durable commitment. See `/Users/scottluengen/Documents/1_Projects/brewspec/specs/decisions/ADR-001-ratings-scale-cva-hedonic.md`.

---

## 5. Public Spec Document

Required. Described in full in section 1.7 above.

### 5.1 Structure

The `brewspec-v0.9.md` document must include these sections:

1. **Overview** — What BrewSpec is; scope of v0.9; defer list carried forward
2. **Field Reference** — Complete table for all fields; ratings section heading and table updated for 1-9 scale
3. **What Changed in v0.9** — Scale change, CVA alignment, breaking change notes
4. **CVA Hedonic Scale** — Table of 1-9 anchors; SCA-104 citation
5. **Validation** — Safe-parse pipeline; multipleOf note; carry forward verbatim from v0.8
6. **Backward Compatibility** — Migration steps; compatibility characterisation; link to archived v0.8

### 5.2 Field Reference — Ratings Table

The ratings section heading must read:

```
### Ratings Object (entire object optional; all fields within optional; integers 1-9, CVA hedonic scale)
```

The table format:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `overall` | integer | No | 1-9 inclusive | Holistic impression. 1 = dislike extremely, 9 = like extremely. |
| `fragrance` | integer | No | 1-9 inclusive | Dry grounds aroma before water is added. |
| `aroma` | integer | No | 1-9 inclusive | Wet aroma after water is added. |
| `flavour` | integer | No | 1-9 inclusive | Taste and aroma experienced during drinking. |
| `aftertaste` | integer | No | 1-9 inclusive | Length and quality of positive flavour attributes after swallowing. |
| `acidity` | integer | No | 1-9 inclusive | Quality (not quantity) of acidity; brightness. |
| `sweetness` | integer | No | 1-9 inclusive | Perceived sweetness. |
| `mouthfeel` | integer | No | 1-9 inclusive | Tactile sensation; body and texture. |

---

## 6. File Manifest

Complete list of every file the dev must create or modify.

| File | Operation | Notes |
|------|-----------|-------|
| `brewspec.schema.json` | Modify | Title, version const, ratings object description, all 8 ratings field maximums and descriptions (sections 1.1-1.3) |
| `brewspec-v0.9.md` | Create | New canonical spec document (section 1.7) |
| `brewspec-v0.8.md` | Archive → `versions/brewspec-v0.8.md` | Copy before overwriting; do not delete from root until new doc is written |
| `examples/invalid/rating_out_of_range.yaml` | Modify | Value 6 → 10, comment updated, version 0.8 → 0.9 (section 1.4) |
| `examples/valid/light_roast_ethiopian.yaml` | Modify | Version bump + add `aftertaste: 7` (sections 1.5, 1.6) |
| `examples/valid/pour_over.yaml` | Modify | Version bump only |
| `examples/valid/pour_over.json` | Modify | Version bump only |
| `examples/valid/pour_over_date_only.yaml` | Modify | Version bump only |
| `examples/valid/espresso.yaml` | Modify | Version bump only |
| `examples/valid/espresso_with_yield.yaml` | Modify | Version bump only |
| `examples/valid/equipment.yaml` | Modify | Version bump only |
| `examples/valid/hybrid.yaml` | Modify | Version bump only |
| `examples/valid/multi_brew.yaml` | Modify | Version bump only |
| `examples/valid/valid_single_origin_full.yaml` | Modify | Version bump only |
| `examples/valid/valid_single_origin_with_varietal.yaml` | Modify | Version bump only |
| `examples/valid/valid_blend_with_per_origin_varietal.yaml` | Modify | Version bump only |
| `examples/valid/valid_blend_origin.yaml` | Modify | Version bump only |
| `examples/valid/immersion_minimal.yaml` | Modify | Version bump only |
| `examples/valid/minimal_no_required_fields.yaml` | Modify | Version bump only |
| `examples/valid/valid_brew_ratio.yaml` | Modify | Version bump only |
| `examples/valid/valid_grinder_setting.yaml` | Modify | Version bump only |
| `examples/valid/valid_equipment_notes.yaml` | Modify | Version bump only |
| `tests/test_brewspec_schema.py` | Modify | Version strings, new and updated ratings tests (section 1.8) |

---

## 7. Test Strategy

### AC-1: Version bump — `brewspec_version` const is `"0.9"`

| Test | Input | Expected |
|------|-------|----------|
| Schema title check | Read `schema["title"]` | `"BrewSpec v0.9"` |
| Correct version accepted | `brewspec_version: "0.9"` | passes validation |
| Version `"0.8"` rejected | `brewspec_version: "0.8"` | fails with `ValidationError` |
| Version `"1.0"` rejected | `brewspec_version: "1.0"` | fails with `ValidationError` |
| Missing version rejected | no `brewspec_version` key | fails with `ValidationError` |

### AC-2: All eight ratings fields have `minimum: 1`, `maximum: 9`

Covered by the parametrized boundary tests below. No separate test needed.

### AC-3: Value `1` accepted for each field

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_all_fields_accept_minimum` (parametrized × 8) | each field: 1 | passes |

### AC-4: Value `5` accepted for each field (backward compatibility)

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_all_fields_accept_5` (parametrized × 8) | each field: 5 | passes |

### AC-5: Value `9` accepted for each field

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_all_fields_accept_maximum` (parametrized × 8) | each field: 9 | passes |
| `test_ratings_new_maximum_accepted` | `overall: 9` | passes |

### AC-6: Value `0` rejected for each field

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_all_fields_reject_below_min` (parametrized × 8) | each field: 0 | fails |
| `test_ratings_below_minimum_rejected` (existing — keep, update version string) | `overall: 0` | fails |

### AC-7: Value `10` rejected for each field

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_all_fields_reject_above_max` (parametrized × 8) | each field: 10 | fails |
| `test_ratings_above_new_maximum_rejected` | `overall: 10` | fails |
| `test_ratings_above_maximum_rejected` (existing — update value from 6 to 10, update docstring) | `overall: 10` | fails |

### AC-8: Values `6`, `7`, `8` accepted

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_value_6_accepted` | `overall: 6` | passes |
| `test_ratings_value_7_accepted` | `overall: 7` | passes |
| `test_ratings_value_8_accepted` | `overall: 8` | passes |

### AC-9: Document with no `ratings` object passes

| Test | Input | Expected |
|------|-------|----------|
| Covered by `VALID_DOC` used in nearly all existing tests | no `result.ratings` | passes |

### AC-10: `ratings` object with no fields passes

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_partial_accepted` (existing — keep) | `ratings: {}` or partial | passes |

### AC-11 / AC-12: Schema descriptions updated

| Test | Input | Expected |
|------|-------|----------|
| `test_schema_is_valid_draft_2020_12` (existing) | meta-validation | passes (schema is valid) |
| (No direct string-content assertions needed — meta-validation confirms schema is structurally sound) | | |

### AC-13: `rating_out_of_range.yaml` fails with value `10`

| Test | Input | Expected |
|------|-------|----------|
| File-based invalid test (existing pattern) | `examples/invalid/rating_out_of_range.yaml` | fails with `ValidationError` |

### AC-14 / AC-15: All valid examples pass after version bump

| Test | Input | Expected |
|------|-------|----------|
| `test_all_valid_examples_pass` (existing pattern — loads all files in `examples/valid/`) | all valid YAML/JSON files | all pass |

### AC-16: At least one valid example has a rating value in 6-9 range

| Test | Input | Expected |
|------|-------|----------|
| `test_all_valid_examples_pass` (file-based) includes `light_roast_ethiopian.yaml` which now contains `aftertaste: 7` | `light_roast_ethiopian.yaml` | passes |

No separate test is needed — the existing all-valid-examples test provides coverage. A comment in the test or in the file itself can note that this file serves as the 6-9 range demonstration (AC-16).

### Additional: non-regression on existing test coverage

These existing tests require version string updates only (not logic changes):

- `test_version_const_rejects_v0_7` → rename to `test_version_const_rejects_v0_8`, change rejected value to `"0.8"`
- All inline `"brewspec_version": "0.8"` strings throughout the test file → change to `"0.9"`
- `VALID_DOC` constant → update to `"0.9"`

---

## 8. Security Considerations

**Input validation**: All eight ratings fields remain `type: integer` with explicit `minimum: 1` and `maximum: 9`. The integer type prevents string injection. The minimum and maximum constraints prevent value stuffing above or below the scale. No new injection surface is introduced — only the numeric ceiling changes. The schema remains the authoritative validation boundary.

**Trust boundaries**: Unchanged from v0.8. The validation pipeline is: safe parse (`yaml.safe_load`) → schema validation (`Draft202012Validator`) → application logic. The scale change does not affect any step of this pipeline.

**File I/O**: Example files are plain YAML/JSON, read-only during test execution. No new file I/O patterns are introduced. The `rating_out_of_range.yaml` update is a simple integer value change with no parsing implications.

**Data integrity**: Existing stored ratings values of 1-5 remain valid under v0.9. No data migration is required. Tools that validated against v0.8 and accepted ratings 1-5 will continue to accept those values against v0.9. The risk direction is one-way: a v0.9 document with rating 7 loaded into a v0.8 validator will be rejected — this is expected and correct version-mismatch behaviour.

**No sensitive data in examples**: All rating values in examples are plain integers. No credentials, API keys, or PII in any example file.

**Error messages**: No changes to error message surfaces. `jsonschema.ValidationError` messages for out-of-range integers will now reference the new maximum of 9; this is accurate and does not expose internal state.

---

## 9. TDD Implementation Order

1. **Write failing tests for AC-1** (version bump): `test_schema_title_is_v0_9`, `test_version_must_be_0_9`, `test_version_const_rejects_v0_8`. Tests fail because schema still says `"0.8"`.

2. **Write failing tests for AC-5, AC-7, AC-8** (new scale boundaries): `test_ratings_new_maximum_accepted` (9 passes), `test_ratings_above_new_maximum_rejected` (10 fails), `test_ratings_value_6_accepted`, `test_ratings_value_7_accepted`, `test_ratings_value_8_accepted`. Tests fail on the boundary cases because maximum is still 5.

3. **Write failing parametrized tests for AC-3, AC-4, AC-5, AC-6, AC-7**: `test_ratings_all_fields_accept_minimum`, `test_ratings_all_fields_accept_5`, `test_ratings_all_fields_accept_maximum`, `test_ratings_all_fields_reject_below_min`, `test_ratings_all_fields_reject_above_max`. Tests for value 9 and rejection of 10 fail.

4. **Update `brewspec.schema.json`**: version const `"0.9"`, title `"BrewSpec v0.9"`, all 8 ratings fields `maximum: 9`, updated descriptions. All step-1, 2, and 3 tests now pass.

5. **Update version strings in existing tests**: change all `"0.8"` to `"0.9"` in `VALID_DOC` and all inline dicts. Update `test_ratings_above_maximum_rejected` from value `6` to `10`. Run full suite — all pass.

6. **Update `examples/invalid/rating_out_of_range.yaml`**: value `6` → `10`, comment updated, version `"0.9"`. Confirm file-based invalid test still passes.

7. **Update all valid example files**: change `brewspec_version` from `"0.8"` to `"0.9"` in all 21 files. Add `aftertaste: 7` to `light_roast_ethiopian.yaml`. Run file-based valid example tests — all pass.

8. **Write `brewspec-v0.9.md`**: full spec document per section 1.7. Archive `brewspec-v0.8.md` to `versions/brewspec-v0.8.md` first.

9. **Run full test suite** — all tests pass.

10. **Run `ruff check .`** — fix any lint errors. Zero violations required before handoff.
