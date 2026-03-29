# Design: BrewSpec v1.0

**Feature:** brewspec-v1.0
**Author:** architect
**Created:** 2026-03-29
**Input:** specs/products/brewspec-v1.0.md
**Baseline:** specs/designs/brewspec-v0.9.md
**Status:** Ready for Dev

---

## Overview

This design covers the four schema changes that constitute BrewSpec v1.0: water/yield field symmetry (rename `brew.water_weight_g` to `brew.water_g`, add `brew.yield_g` and `result.water_g`), standardised `name` field `maxLength` (`coffee.name` changed from 150 to 100), notes field differentiation (rename `brew.notes` to `brew.process_notes`, add `coffee.cupping_notes` and `origin.cupping_notes`), and new espresso equipment fields (`equipment.pressure_bar` and `equipment.flow_rate_ml_s`). All four changes contain at least one breaking element. They are bundled into a single major version to minimise downstream disruption.

Two ADRs accompany this design: ADR-002 (recipe/result field symmetry) and ADR-003 (notes field differentiation). These record the rationale for the two changes that involved architectural trade-offs between naming approaches and placement of new fields.

---

## 1. Changes Required

### 1.1 Root-level schema metadata

**File:** `brewspec.schema.json`

Change the `title` and `brewspec_version` const:

```json
"title": "BrewSpec v1.0",
"description": "An open standard for describing coffee brews.",
```

Change the `brewspec_version` property:

```json
"brewspec_version": {
  "const": "1.0",
  "description": "The BrewSpec version. Must be \"1.0\"."
}
```

The `$id` URL remains unchanged. The `$schema` URL remains unchanged.

**AC-1 coverage:** Documents declaring any version other than `"1.0"` are rejected by the const constraint.

---

### 1.2 Brew object — water and yield fields

**Location in schema:** `$defs.brew.properties`

**Remove** the following property entirely:

```json
"water_weight_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Water weight in grams. Must be > 0."
}
```

**Add** the following two properties in its place. Insert `water_g` at the same position where `water_weight_g` was (after `dose_g`, before `brew_ratio`). Insert `yield_g` after `duration_s` and before `process_notes` (the renamed notes field):

```json
"water_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Recipe target water in grams. Must be > 0."
},
```

```json
"yield_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Recipe target output weight in grams. Primarily used in espresso dialling to record intended yield before brewing. Must be > 0."
},
```

**Update** the `brew_ratio` description to reference `brew.water_g` instead of `water_weight_g`:

```json
"brew_ratio": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Water-to-coffee ratio expressed as a single float (grams of water per gram of coffee). e.g. 15.5 represents 15.5:1 or approximately 64g/L. Can be computed from water_g / dose_g. When both are present, tools should validate consistency; mismatches should be surfaced as a warning, not a schema error."
}
```

**AC-2, AC-3, AC-5 (unchanged `result.yield_g`) coverage.**

---

### 1.3 Result object — water field

**Location in schema:** `$defs.result.properties`

**Add** the following property. Insert it after `brix` and before `yield_g` (maintaining a logical grouping of measurement fields before sensory fields):

```json
"result.water_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Actual water used in grams. Records the measured input water when it deviates from the recipe target (brew.water_g). Must be > 0."
}
```

The JSON key is `water_g` (not `result.water_g`). The full property block within `$defs.result.properties`:

```json
"water_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Actual water used in grams. Records the measured input water when it deviates from the recipe target (brew.water_g). Must be > 0."
}
```

**Also update** the `yield_g` description in the result object to reference `brew.water_g` instead of `water_weight_g`:

```json
"yield_g": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Output weight of the brew in grams. For espresso, this is the liquid collected in the cup (distinct from brew.water_g, which is the input water). For other brew types, yield_g may approximate water_g less absorbed water. Must be > 0 if present."
}
```

**AC-4 coverage.**

---

### 1.4 Coffee object — name maxLength and cupping_notes

**Location in schema:** `$defs.coffee.properties`

**Modify** `coffee.name` — change `maxLength` from `150` to `100`. All other constraints unchanged:

```json
"name": {
  "type": "string",
  "minLength": 1,
  "maxLength": 100,
  "description": "A branded product name or human-readable descriptive label for the coffee (e.g. 'Ethiopia Yirgacheffe', 'Blue Bottle Hayes Valley Espresso', 'Estate'). Optional. Not required even when origins[] is populated. New in v0.6.",
  "examples": ["Ethiopia Yirgacheffe", "Blue Bottle Hayes Valley Espresso", "Estate"]
}
```

**Add** `coffee.cupping_notes` after the existing `origins` property:

```json
"cupping_notes": {
  "type": "string",
  "minLength": 1,
  "maxLength": 2000,
  "description": "Sensory notes on the coffee as a whole — from a bag description, pre-brew cupping, or any evaluation not tied to a specific brew result. For a single-origin coffee, this serves as the cupping note for the coffee. For blends, this describes the blend as a whole; individual components carry origin.cupping_notes."
}
```

**AC-13, AC-18 coverage.**

---

### 1.5 Origin object — cupping_notes

**Location in schema:** `$defs.origin.properties`

**Add** `origin.cupping_notes` after the existing `elevation_masl` property (end of the origin properties list):

```json
"cupping_notes": {
  "type": "string",
  "minLength": 1,
  "maxLength": 2000,
  "description": "Sensory notes specific to this origin component. For a single-origin coffee, this may duplicate coffee.cupping_notes. For blends, each component carries its own cupping note here."
}
```

**AC-19 coverage.**

---

### 1.6 Brew object — notes field rename

**Location in schema:** `$defs.brew.properties`

**Remove** the `notes` property entirely:

```json
"notes": {
  "type": "string",
  "minLength": 1,
  "maxLength": 2000,
  "description": "Brew-process notes — operational observations about the preparation ..."
}
```

**Add** `process_notes` in its place. Position: after `duration_s`, before `result`. Insert after the new `yield_g` field added in section 1.2:

```json
"process_notes": {
  "type": "string",
  "minLength": 1,
  "maxLength": 2000,
  "description": "Operational observations about the preparation (e.g. 'washed filter paper', 'pre-infused 30s', 'water from Brita filter'). For sensory description of the coffee, use coffee.cupping_notes or result.tasting_notes."
}
```

**Also update** the `coffee.roast_level` description to reference `brew.process_notes` instead of `notes`:

```json
"roast_level": {
  "type": "string",
  "enum": ["light", "medium", "dark"],
  "description": "Roast level category. Deliberately coarse — three values cover the labels on the majority of retail bags. For finer roast detail, use the brew-level process_notes field. New in v0.8."
}
```

**AC-17 coverage.**

---

### 1.7 Equipment object — pressure and flow rate

**Location in schema:** `$defs.equipment.properties`

**Add** two properties after the existing `notes` property (end of the equipment properties list):

```json
"pressure_bar": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Line or lever pressure in bars. Primarily relevant for espresso. Must be > 0 if present."
},
"flow_rate_ml_s": {
  "type": "number",
  "exclusiveMinimum": 0,
  "description": "Volumetric flow rate in millilitres per second. Useful for espresso profiling and controlled pour-over. Must be > 0 if present."
}
```

**AC-26, AC-27 coverage.**

---

## 2. Data Models

This is a schema-only task. No Pydantic models or SQLite schema changes belong in this design. The BrewLog CLI adoption of these changes is tracked separately under `brewlog-cli-v1.0`.

---

## 3. CLI Interface

Not applicable — this is a schema-only task.

---

## 4. Architecture Decision Records

Two new ADRs are written for this version:

- **ADR-002** (`specs/decisions/ADR-002-recipe-result-field-symmetry.md`): Records the decision to rename `water_weight_g` to `water_g` and establish recipe/result symmetry for water and yield fields.
- **ADR-003** (`specs/decisions/ADR-003-notes-field-differentiation.md`): Records the decision to rename `brew.notes` to `brew.process_notes` and add `coffee.cupping_notes` / `origin.cupping_notes`.

The `coffee.name` maxLength reduction and the equipment field additions do not introduce architectural trade-offs warranting separate ADRs. They follow directly from the product spec constraints.

---

## 5. Public Spec Document

### 5.1 Archive step

Before creating `brewspec-v1.0.md`, the dev must copy the current `brewspec-v0.9.md` to `versions/brewspec-v0.9.md`. Then overwrite `brewspec-v1.0.md` at the repo root (a new file — it does not currently exist; `brewspec-v0.9.md` is the current root-level spec doc). Rename `brewspec-v0.9.md` to `brewspec-v1.0.md` effectively.

**Correct sequence:**
1. `cp brewspec-v0.9.md versions/brewspec-v0.9.md`
2. Create new `brewspec-v1.0.md` at repo root with updated content

### 5.2 Structure

`brewspec-v1.0.md` must contain these sections in order:

1. **Overview** — What BrewSpec is; what v1.0 defines (update the scope bullet list)
2. **Field Reference** — Table of all fields with type, required/optional, constraints, description
3. **What Changed in v1.0** — Bulleted list of all four changes; each breaking element explicitly called out
4. **Validation** — Guidance that tools should validate at storage time, not just display time
5. **Backward Compatibility** — Migration instructions: what v0.9 documents must change to be valid v1.0

### 5.3 Field Reference additions

The field reference table must include all new and modified fields. The `brew.water_weight_g` row must be absent. The following rows must be present or updated:

**Brew Object Fields (additions/changes):**

| Field | Type | Required | Constraints | Description | Examples |
|-------|------|----------|-------------|-------------|----------|
| `water_g` | number | No | > 0 (exclusive) | Recipe target water in grams. | `280`, `36` |
| `yield_g` | number | No | > 0 (exclusive) | Recipe target output weight in grams. Primarily for espresso dialling. | `36.0`, `38` |
| `process_notes` | string | No | minLength 1, maxLength 2000 | Operational preparation observations. | `"Rinsed filter, 30s bloom"` |

The `notes` row must be absent.

**Coffee Object Fields (additions/changes):**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | No | minLength 1, maxLength 100 | (changed from 150) |
| `cupping_notes` | string | No | minLength 1, maxLength 2000 | Sensory notes on the coffee as a whole. |

**Origin Object Fields (addition):**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `cupping_notes` | string | No | minLength 1, maxLength 2000 | Sensory notes specific to this origin component. |

**Equipment Object Fields (additions):**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `pressure_bar` | number | No | > 0 (exclusive) | Line or lever pressure in bars. |
| `flow_rate_ml_s` | number | No | > 0 (exclusive) | Volumetric flow rate in ml/s. |

**Result Object Fields (addition):**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `water_g` | number | No | > 0 (exclusive) | Actual water used in grams. |

### 5.4 What Changed in v1.0

The "What Changed in v1.0" section must list all four changes and identify each breaking element:

- **BREAKING: `brew.water_weight_g` removed — renamed to `brew.water_g`**. Documents using `water_weight_g` fail v1.0 validation.
- **NEW: `brew.yield_g`** — recipe target output weight in grams (optional).
- **NEW: `result.water_g`** — actual water used in grams (optional).
- **BREAKING: `brew.notes` removed — renamed to `brew.process_notes`**. Documents using `notes` at the brew level fail v1.0 validation.
- **NEW: `coffee.cupping_notes`** — sensory notes on the coffee as a whole (optional).
- **NEW: `origin.cupping_notes`** — sensory notes for a specific origin component (optional).
- **BREAKING: `coffee.name` maxLength changed from 150 to 100**. Documents with `coffee.name` longer than 100 characters fail v1.0 validation.
- **NEW: `equipment.pressure_bar`** — line or lever pressure in bars (optional).
- **NEW: `equipment.flow_rate_ml_s`** — volumetric flow rate in ml/s (optional).

### 5.5 Backward Compatibility section

The backward compatibility section must state exactly what a v0.9 document must change to be valid under v1.0:

1. **Bump version**: Change `brewspec_version: "0.9"` to `brewspec_version: "1.0"`.
2. **Rename `brew.water_weight_g` to `brew.water_g`**: Every brew that has `water_weight_g` must rename it. Documents with `water_weight_g` fail with an `additionalProperties` error under v1.0.
3. **Rename `brew.notes` to `brew.process_notes`**: Every brew that has a top-level `notes` field must rename it. Documents with `brew.notes` fail with an `additionalProperties` error under v1.0.
4. **Check `coffee.name` length**: If any `coffee.name` value exceeds 100 characters, it must be shortened or the field omitted. Documents with `coffee.name` longer than 100 characters fail with a `maxLength` error.

Documents that do not use `water_weight_g`, `brew.notes`, or a `coffee.name` longer than 100 characters are valid under v1.0 with only the version bump.

**AC-44, AC-45, AC-46 coverage.**

---

## 6. File Manifest

| File | Operation | Notes |
|------|-----------|-------|
| `brewspec.schema.json` | Modify | All changes from Section 1 |
| `brewspec-v1.0.md` | Create | New root-level spec doc (see Section 5) |
| `versions/brewspec-v0.9.md` | Create (archive) | Copy current `brewspec-v0.9.md` before creating v1.0 |
| `brewspec-v0.9.md` | Leave in place | The root-level `brewspec-v0.9.md` is archived by copying, not by deleting — remove it only after `brewspec-v1.0.md` is created |
| `examples/valid/espresso.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/espresso_with_yield.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/pour_over.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/pour_over_date_only.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/light_roast_ethiopian.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/valid_single_origin_full.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/immersion_minimal.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/hybrid.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/equipment.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/valid_grinder_setting.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/valid_equipment_notes.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/valid_brew_ratio.yaml` | Modify | Version bump, `water_weight_g` → `water_g`, `notes` → `process_notes` |
| `examples/valid/valid_single_origin_with_varietal.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/valid_blend_with_per_origin_varietal.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/valid_blend_origin.yaml` | Modify | Version bump, `water_weight_g` → `water_g` |
| `examples/valid/multi_brew.yaml` | Modify | Version bump, `water_weight_g` → `water_g` for all three brews |
| `examples/valid/minimal_no_required_fields.yaml` | Modify | Version bump, `notes` → `process_notes` |
| `examples/valid/espresso_full_symmetry.yaml` | Create | AC-36, AC-37, AC-39: demonstrates `brew.yield_g`, `result.water_g`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s` |
| `examples/valid/pour_over_cupping_notes.yaml` | Create | AC-38: demonstrates `coffee.cupping_notes` and `origin.cupping_notes` |
| `examples/invalid/invalid_water_weight_g.yaml` | Create | AC-40: uses `brew.water_weight_g`, fails v1.0 |
| `examples/invalid/invalid_brew_notes.yaml` | Create | AC-41: uses `brew.notes`, fails v1.0 |
| `examples/invalid/invalid_water_volume_ml.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_grinder_setting_string.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_origin_string_array.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_coffee_process_top_level.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_tds_at_brew_level.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_grind_freeform.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_date_no_z.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/rating_out_of_range.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_yield_zero.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/negative_weight.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` (failure case: `dose_g: -10` still holds) |
| `examples/invalid/missing_version.yaml` | Modify | AC-43: `water_weight_g` → `water_g` (failure case: missing version still holds) |
| `examples/invalid/zero_duration.yaml` | Modify | AC-42, AC-43: version `"1.0"`, `water_weight_g` → `water_g` (failure case: `duration_s: 0` still holds) |
| `examples/invalid/empty_brews_array.yaml` | Modify | AC-43: version `"1.0"` (no `water_weight_g` present; failure case unchanged) |
| `examples/invalid/invalid_roast_level.yaml` | Modify | AC-43: version `"1.0"` (already version `"0.9"`; failure case unchanged) |
| `examples/invalid/missing_required_field.yaml` | Modify | AC-43: version `"1.0"`, `water_weight_g` → `water_g`. See note in Section 7 regarding the intended failure case. |
| `examples/invalid/v0.2_format.yaml` | No change | AC-43 exception: this file tests that version `"0.2"` is rejected — the version string is the failure case. Leave as-is. |
| `examples/invalid/v0.1_format.yaml` | No change | AC-43 exception: this file tests that version `"0.2"` is rejected — the version string is the failure case. Leave as-is. |
| `examples/invalid/invalid_type_enum.yaml` | Modify | AC-43: version `"1.0"`, `water_weight_g` → `water_g` |
| `examples/invalid/invalid_water_temp_precision.yaml` | No change | AC-43: no `water_weight_g`; already fails via `water_temp_c: 96.15` (multipleOf violation). Update version to `"1.0"` — wait, this file has no `brewspec_version` field currently visible; check: the file content shows `brewspec_version: "0.9"` in the actual file. Update to `"1.0"`. |
| `tests/test_brewspec_schema.py` | Modify | Add all new test cases per Section 7; update VALID_BREW and VALID_DOC fixtures |
| `specs/decisions/ADR-002-recipe-result-field-symmetry.md` | Create | Written by architect |
| `specs/decisions/ADR-003-notes-field-differentiation.md` | Create | Written by architect |

**Note on `invalid_water_temp_precision.yaml`:** the file contains only `brewspec_version: "0.9"` and `brews: [{water_temp_c: 96.15}]`. Update version to `"1.0"`. The failure case (`multipleOf: 0.1` violation) is unaffected.

**Note on `missing_required_field.yaml`:** this file was labelled as "missing required 'date' field" but `date` has been optional since v0.7. Under v1.0, the document (`type: pour_over, dose_g: 20, water_g: 320`) passes validation — the file no longer demonstrates an invalid case when `water_weight_g` is renamed to `water_g` and the version is `"1.0"`. The dev must update this file to demonstrate an actual invalid case. Recommended change: set version to `"1.0"` and keep `water_g`, but add a field that is actually invalid — for example `water_temp_c: 96.15` to demonstrate the `multipleOf` constraint (or any other distinct invalid case not already covered by another file). Alternatively, the dev may choose to rename this file's purpose to match the actual schema violation it demonstrates. The key constraint is that it must fail v1.0 validation for its stated reason.

---

## 7. Test Strategy

The test file is `tests/test_brewspec_schema.py`. The test suite uses `pytest` with `jsonschema.Draft202012Validator`. Tests use a VALID_BREW fixture and inline YAML/dict fixtures for edge cases.

**Required fixture update:** The global `VALID_BREW` constant and `VALID_DOC` constant must be updated from v0.9 to v1.0. Change `water_weight_g` to `water_g` and `brewspec_version` from `"0.9"` to `"1.0"`. Update all inline dicts in existing v0.9 tests that reference `water_weight_g` to use `water_g` and update `brewspec_version` to `"1.0"`. The existing tests that verify old version strings are rejected (e.g., `test_version_const_rejects_v0_8`) must additionally have a `test_version_const_rejects_v0_9` test added.

---

### AC-1: Version bump to 1.0

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_schema_title_is_v1_0` | Valid pass (schema meta) | `schema["title"]` | `"BrewSpec v1.0"` |
| `test_version_must_be_1_0` | Valid pass | `{"brewspec_version": "1.0", "brews": [VALID_BREW]}` | passes |
| `test_version_must_be_1_0` | Invalid reject | `{"brewspec_version": "0.9", "brews": [VALID_BREW]}` | raises ValidationError |
| `test_version_const_rejects_v0_9` | Invalid reject | `{"brewspec_version": "0.9", "brews": [VALID_BREW]}` | raises ValidationError |
| `test_version_const_rejects_v0_8` | Invalid reject | `{"brewspec_version": "0.8", ...}` | raises ValidationError |

The existing pattern of rejecting all prior version strings (v0.1 through v0.8) should be maintained by adding `test_version_const_rejects_v0_9`.

---

### AC-2, AC-6, AC-7: `brew.water_g` (renamed from `water_weight_g`)

| Test function | Type | Input brew fields | Expected |
|---|---|---|---|
| `test_brew_water_g_accepts_positive` | Valid pass | `{"water_g": 280}` | passes |
| `test_brew_water_g_zero_fails` | Invalid reject | `{"water_g": 0}` | raises ValidationError |
| `test_brew_water_weight_g_rejected` | Invalid reject | `{"water_weight_g": 280}` | raises ValidationError — `additionalProperties` violation |

For `test_brew_water_weight_g_rejected`, the minimal invalid doc fixture is:
```yaml
brewspec_version: "1.0"
brews:
  - water_weight_g: 280
```

---

### AC-3, AC-8, AC-9: `brew.yield_g` (new)

| Test function | Type | Input brew fields | Expected |
|---|---|---|---|
| `test_brew_yield_g_accepts_positive` | Valid pass | `{"yield_g": 36}` | passes |
| `test_brew_yield_g_zero_fails` | Invalid reject | `{"yield_g": 0}` | raises ValidationError |
| `test_brew_yield_g_optional` | Valid pass | `{}` (brew with no yield_g) | passes |

---

### AC-4, AC-10, AC-11: `result.water_g` (new)

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_result_water_g_accepts_positive` | Valid pass | `{"result": {"water_g": 285}}` | passes |
| `test_result_water_g_zero_fails` | Invalid reject | `{"result": {"water_g": 0}}` | raises ValidationError |
| `test_result_water_g_optional` | Valid pass | `{"result": {}}` | passes |

---

### AC-5: `result.yield_g` unchanged

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_result_yield_g_unchanged` | Valid pass | `{"result": {"yield_g": 36.5}}` | passes |

This test confirms no regression on the existing `result.yield_g` field.

---

### AC-12: All water/yield fields optional

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_brew_water_yield_all_optional` | Valid pass | `{}` (empty brew) | passes |

---

### AC-13, AC-14, AC-15: `coffee.name` maxLength 100

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_coffee_name_100_chars_passes` | Valid pass | `{"coffee": {"name": "A" * 100}}` | passes |
| `test_coffee_name_101_chars_fails` | Invalid reject | `{"coffee": {"name": "A" * 101}}` | raises ValidationError |

The 100-character string fixture: any string of exactly 100 ASCII characters (e.g., `"A" * 100` in Python).

---

### AC-16: `origin.name` maxLength 100 unchanged

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_origin_name_100_chars_passes` | Valid pass | `{"coffee": {"origins": [{"name": "A" * 100}]}}` | passes |
| `test_origin_name_101_chars_fails` | Invalid reject | `{"coffee": {"origins": [{"name": "A" * 101}]}}` | raises ValidationError |

These tests confirm that `origin.name` maxLength is 100 (and was not accidentally changed).

---

### AC-17, AC-20, AC-21, AC-24: `brew.process_notes` (renamed from `notes`)

| Test function | Type | Input brew fields | Expected |
|---|---|---|---|
| `test_brew_process_notes_accepts_string` | Valid pass | `{"process_notes": "Rinsed filter, let bloom 30s"}` | passes |
| `test_brew_notes_rejected` | Invalid reject | `{"notes": "Rinsed filter"}` | raises ValidationError — `additionalProperties` violation |
| `test_brew_process_notes_empty_string_fails` | Invalid reject | `{"process_notes": ""}` | raises ValidationError — `minLength: 1` |
| `test_brew_process_notes_optional` | Valid pass | `{}` (brew with no process_notes) | passes |

For `test_brew_notes_rejected`, the minimal invalid doc fixture is:
```yaml
brewspec_version: "1.0"
brews:
  - notes: "Rinsed filter"
```

---

### AC-18, AC-22: `coffee.cupping_notes` (new)

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_coffee_cupping_notes_accepts_string` | Valid pass | `{"coffee": {"cupping_notes": "Jasmine, peach, light honey"}}` | passes |
| `test_coffee_cupping_notes_empty_string_fails` | Invalid reject | `{"coffee": {"cupping_notes": ""}}` | raises ValidationError |
| `test_coffee_cupping_notes_optional` | Valid pass | `{"coffee": {}}` | passes |

---

### AC-19, AC-23: `origin.cupping_notes` (new)

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_origin_cupping_notes_accepts_string` | Valid pass | `{"coffee": {"origins": [{"cupping_notes": "Berry jam, floral"}]}}` | passes |
| `test_origin_cupping_notes_empty_string_fails` | Invalid reject | `{"coffee": {"origins": [{"cupping_notes": ""}]}}` | raises ValidationError |
| `test_origin_cupping_notes_optional` | Valid pass | `{"coffee": {"origins": [{}]}}` | passes |

---

### AC-25: All notes fields optional

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_notes_fields_all_optional` | Valid pass | `{}` (empty brew; coffee omitted entirely) | passes |

---

### AC-26, AC-28, AC-29: `equipment.pressure_bar` (new)

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_equipment_pressure_bar_accepts_positive` | Valid pass | `{"equipment": {"pressure_bar": 9}}` | passes |
| `test_equipment_pressure_bar_zero_fails` | Invalid reject | `{"equipment": {"pressure_bar": 0}}` | raises ValidationError |
| `test_equipment_pressure_bar_decimal_passes` | Valid pass | `{"equipment": {"pressure_bar": 9.0}}` | passes |
| `test_equipment_pressure_bar_optional` | Valid pass | `{"equipment": {}}` | passes |

---

### AC-27, AC-30, AC-31: `equipment.flow_rate_ml_s` (new)

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_equipment_flow_rate_ml_s_accepts_positive` | Valid pass | `{"equipment": {"flow_rate_ml_s": 1.5}}` | passes |
| `test_equipment_flow_rate_ml_s_zero_fails` | Invalid reject | `{"equipment": {"flow_rate_ml_s": 0}}` | raises ValidationError |
| `test_equipment_flow_rate_ml_s_optional` | Valid pass | `{"equipment": {}}` | passes |

---

### AC-32: Equipment fields optional

| Test function | Type | Input | Expected |
|---|---|---|---|
| `test_equipment_pressure_flow_both_optional` | Valid pass | `{"equipment": {"grinder": "Niche Zero"}}` (no pressure or flow) | passes |

---

### AC-33, AC-34, AC-35: Valid example files pass v1.0 validation

The existing parametrized test that loads all files from `examples/valid/` must pass after the example files are updated. The parametrized test function name is `test_valid_example_files` (following the existing pattern in the test suite). No new test function needed — the existing fixture-loading test covers this group of ACs.

---

### AC-40, AC-41: New invalid examples reject removed fields

| Test function | Type | File | Expected |
|---|---|---|---|
| `test_invalid_example_files` | Invalid reject | `examples/invalid/invalid_water_weight_g.yaml` | fails validation |
| `test_invalid_example_files` | Invalid reject | `examples/invalid/invalid_brew_notes.yaml` | fails validation |

The existing parametrized test that loads all files from `examples/invalid/` covers these. The new files just need to exist and fail validation.

---

### AC-36, AC-37, AC-38, AC-39: New valid examples pass validation

| Test function | Type | File | Validates |
|---|---|---|---|
| `test_valid_example_files` | Valid pass | `examples/valid/espresso_full_symmetry.yaml` | `brew.yield_g`, `result.water_g`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s` |
| `test_valid_example_files` | Valid pass | `examples/valid/pour_over_cupping_notes.yaml` | `coffee.cupping_notes`, `origin.cupping_notes` |

These are covered by the parametrized valid-examples test. The files need to exist and pass validation.

---

### AC-47: Explicit named tests required by the product spec

The product spec (AC-47) explicitly names the following tests that must exist in the suite. Map each to the test functions defined above:

| Spec requirement | Test function |
|---|---|
| `brew.water_g` accepts a positive number | `test_brew_water_g_accepts_positive` |
| `brew.water_g: 0` fails | `test_brew_water_g_zero_fails` |
| `brew.water_weight_g` fails (removed field) | `test_brew_water_weight_g_rejected` |
| `brew.yield_g` accepts a positive number | `test_brew_yield_g_accepts_positive` |
| `brew.yield_g: 0` fails | `test_brew_yield_g_zero_fails` |
| `result.water_g` accepts a positive number | `test_result_water_g_accepts_positive` |
| `result.water_g: 0` fails | `test_result_water_g_zero_fails` |
| `coffee.name` of 100 chars passes | `test_coffee_name_100_chars_passes` |
| `coffee.name` of 101 chars fails | `test_coffee_name_101_chars_fails` |
| `brew.process_notes` accepts a non-empty string | `test_brew_process_notes_accepts_string` |
| `brew.process_notes: ""` fails (minLength: 1) | `test_brew_process_notes_empty_string_fails` |
| `brew.notes` fails (removed field) | `test_brew_notes_rejected` |
| `coffee.cupping_notes` accepts a non-empty string | `test_coffee_cupping_notes_accepts_string` |
| `origin.cupping_notes` accepts a non-empty string | `test_origin_cupping_notes_accepts_string` |
| `equipment.pressure_bar` accepts a positive number | `test_equipment_pressure_bar_accepts_positive` |
| `equipment.pressure_bar: 0` fails | `test_equipment_pressure_bar_zero_fails` |
| `equipment.flow_rate_ml_s` accepts a positive number | `test_equipment_flow_rate_ml_s_accepts_positive` |
| `equipment.flow_rate_ml_s: 0` fails | `test_equipment_flow_rate_ml_s_zero_fails` |
| `brewspec_version: "0.9"` rejected by v1.0 schema | `test_version_const_rejects_v0_9` |

All 19 explicitly named tests in AC-47 are covered by the test functions specified above.

---

## 8. Security Considerations

All security analysis follows directly from the product spec's security requirements section. No new trust boundaries are introduced by this change set.

**Input validation:** All new fields are constrained at the JSON Schema level:
- String fields (`brew.process_notes`, `coffee.cupping_notes`, `origin.cupping_notes`) have `minLength: 1` and `maxLength: 2000`. The `minLength: 1` constraint prevents empty strings from passing as valid values, consistent with all other string fields in the schema. `maxLength: 2000` prevents unbounded string storage.
- Number fields (`brew.water_g`, `brew.yield_g`, `result.water_g`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s`) have `exclusiveMinimum: 0`. Type enforcement is handled by the JSON Schema `type: number` constraint — no string injection is possible through these fields.
- `coffee.name` maxLength reduction from 150 to 100 is a tightening of an existing constraint, not a new trust boundary.

**Removed fields and additionalProperties:** The `additionalProperties: false` constraint on the brew and coffee objects means documents containing `brew.water_weight_g` or `brew.notes` fail schema validation with a clear error. This is the correct behaviour — it forces migration rather than silently accepting data under the wrong field name. The constraint is already present in v0.9 and carries forward unchanged.

**File I/O:** No change to the file I/O pattern. YAML is parsed with `yaml.safe_load()` before schema validation. The example files added in this version contain only brew recipe data — no executable content, credentials, or PII.

**Data integrity:** The recipe/result field pairs (`brew.water_g`/`result.water_g`, `brew.yield_g`/`result.yield_g`) are both optional. A document with `result.water_g` but no `brew.water_g` is valid — the schema does not require the recipe field to be present for the result field. This is by design (a minimal log needs neither), consistent with how all other brew-level and result-level fields relate. The schema does not enforce cross-field consistency (e.g., that `result.water_g` ≤ `brew.water_g` + some tolerance). Cross-field validation is advisory logic for tools, not a schema constraint.

**No sensitive data:** All new fields are brew recipe parameters or freeform notes. Sensitivity profile is identical to the rest of BrewSpec — personal preferences and process records, not PII.

---

## 9. TDD Implementation Order

1. Update `VALID_BREW` and `VALID_DOC` fixtures: change `water_weight_g` → `water_g`, version `"0.9"` → `"1.0"`. Update all existing inline fixture dicts in existing tests that reference `water_weight_g`. All existing tests that pass before this step should still pass (they will fail only because the schema has not changed yet — which is the correct red state).

2. Write all new failing tests from Section 7 (all 19 AC-47 tests plus the additional edge cases).

3. Implement schema change 1.1 (version bump and title). Confirm `test_schema_title_is_v1_0` and `test_version_must_be_1_0` pass; confirm `test_version_const_rejects_v0_9` passes.

4. Implement schema change 1.2 (`brew.water_g`, `brew.yield_g`, `brew_ratio` description). Confirm water_g and yield_g tests pass. Confirm `test_brew_water_weight_g_rejected` passes.

5. Implement schema change 1.3 (`result.water_g`, update `result.yield_g` description). Confirm result water_g tests pass.

6. Implement schema change 1.4 (`coffee.name` maxLength, `coffee.cupping_notes`). Confirm name maxLength tests and cupping_notes tests pass.

7. Implement schema change 1.5 (`origin.cupping_notes`). Confirm origin cupping_notes tests pass.

8. Implement schema change 1.6 (`brew.process_notes` rename). Confirm process_notes tests pass. Confirm `test_brew_notes_rejected` passes.

9. Implement schema change 1.7 (`equipment.pressure_bar`, `equipment.flow_rate_ml_s`). Confirm equipment field tests pass.

10. Update valid example files (version bumps, renames). Confirm the parametrized valid examples test passes for all updated files.

11. Create new valid example files (`espresso_full_symmetry.yaml`, `pour_over_cupping_notes.yaml`). Confirm they pass the parametrized valid examples test.

12. Create new invalid example files (`invalid_water_weight_g.yaml`, `invalid_brew_notes.yaml`). Confirm they fail the parametrized invalid examples test.

13. Update existing invalid example files (version bumps, field renames per File Manifest). Confirm all invalid examples still fail as intended.

14. Archive `brewspec-v0.9.md` to `versions/brewspec-v0.9.md`. Create `brewspec-v1.0.md` with content per Section 5.

15. Run full test suite — confirm all tests pass.

16. Run `ruff check .` — fix any lint errors.

---

## Appendix A: New Valid Example File Content

### `examples/valid/espresso_full_symmetry.yaml`

This file satisfies AC-36 (`brew.yield_g` alongside `result.yield_g`), AC-37 (`result.water_g`), and AC-39 (`equipment.pressure_bar` and `equipment.flow_rate_ml_s`). The product spec's design notes section provides the canonical example; the dev must use the structure below.

```yaml
# Valid example: espresso with full recipe/result symmetry.
# Demonstrates brew.yield_g (recipe target), result.water_g (actual water used),
# equipment.pressure_bar, and equipment.flow_rate_ml_s.
brewspec_version: "1.0"
brews:
  - date: "2026-03-29"
    type: "espresso"
    method: "La Marzocco Linea Mini"
    dose_g: 18.0
    water_g: 36.0
    yield_g: 36.0
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
      water_g: 35.5
      yield_g: 36.5
      tds: 9.1
      ey: 19.6
      tasting_notes: "Caramel sweetness, low bright acidity, clean finish"
      ratings:
        overall: 8
        flavour: 8
        acidity: 7
        mouthfeel: 7
```

This single file demonstrates AC-36, AC-37, AC-38 (via `coffee.cupping_notes` and `origin.cupping_notes`), and AC-39 simultaneously. However, a second dedicated file for cupping notes is still required (see below), because the spec requires at least one example that clearly demonstrates the cupping notes use case for pour-over.

### `examples/valid/pour_over_cupping_notes.yaml`

This file satisfies AC-38 (`coffee.cupping_notes` and `origin.cupping_notes`).

```yaml
# Valid example: pour-over with coffee and origin cupping notes.
# Demonstrates coffee.cupping_notes (coffee-level sensory evaluation)
# and origin.cupping_notes (component-level sensory evaluation).
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

### `examples/invalid/invalid_water_weight_g.yaml`

```yaml
# Invalid: brew.water_weight_g was removed in v1.0.
# Renamed to brew.water_g. This field fails additionalProperties: false.
brewspec_version: "1.0"
brews:
  - date: "2026-03-29"
    type: "pour_over"
    dose_g: 18.0
    water_weight_g: 280.0
```

### `examples/invalid/invalid_brew_notes.yaml`

```yaml
# Invalid: brew.notes was removed in v1.0.
# Renamed to brew.process_notes. This field fails additionalProperties: false.
brewspec_version: "1.0"
brews:
  - date: "2026-03-29"
    type: "pour_over"
    dose_g: 18.0
    water_g: 280.0
    notes: "Rinsed filter"
```
