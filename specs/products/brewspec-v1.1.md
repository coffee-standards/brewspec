# Product: BrewSpec v1.1

**Status:** Ready
**Priority:** P2 (Normal)
**Author:** reviewer
**Created:** 2026-06-06
**Last Updated:** 2026-06-06

---

## Problem Statement

BrewSpec v1.0 has two gaps identified via cross-repo comparison with Slate (the companion iOS app):

**Gap 1: No water source categorisation.**
The `water` object captures `ppm` (total dissolved solids), but has no structured way to record what kind of water was used. Users using tap water, filtered water, bottled water, or engineered mineral water cannot record this without burying it in freeform `process_notes`. Slate tracks water source as a first-class field; BrewSpec has no equivalent.

**Gap 2: No grinder hardware detail beyond model and dial position.**
`equipment.grinder` records the grinder model and `equipment.grinder_setting` records the dial position, but two additional parameters matter for variable-speed grinders: which burr set is installed, and at what RPM the grinder is running. These are primary variables for single-dose and high-end espresso grinders. Slate tracks both; BrewSpec has no equivalent.

Both gaps can be addressed with additive-only changes — no breaking changes are required. This makes them a natural minor version bump: v1.0 → v1.1.

Target personas:
- **Home brewers with variable-speed grinders** — need to record burr set and RPM as part of their recipe so that results are reproducible when they change settings.
- **Coffee professionals** — need structured water type categorisation to filter and analyse brews by water source without parsing freeform notes.
- **Tool builders (Slate and others)** — need schema fields for water.type, water.notes, equipment.burr_set, and equipment.rpm to map their native data model to BrewSpec without data loss.

---

## User Stories

- As a **home brewer** using a variable-speed grinder (e.g. Lagom P100, DF64 Gen 2), I want to record the RPM I use (`equipment.rpm`) so that I can reproduce results when I experiment with different motor speeds.
- As a **home brewer** who experiments with different burr sets, I want to record which burrs are installed (`equipment.burr_set`) so that my brew log captures a full grinder configuration, not just the model and dial position.
- As a **coffee professional** analysing brew records, I want to record the type of water used (`water.type`) so that I can group and compare brews by water source without parsing freeform notes.
- As a **home brewer** using engineered or bottled water, I want a free-text `water.notes` field to record the mineral profile or brand name alongside the `water.type` category.
- As a **tool builder** mapping Slate's data model to BrewSpec, I want schema fields for all four of these attributes so that a full Slate brew record can round-trip to BrewSpec without data loss.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema `brewspec_version` const is updated to `"1.1"`. The schema `$id` ends in `v1.1.json`. The schema `title` is `"BrewSpec v1.1"`. Documents declaring any other version string are rejected by the v1.1 schema.

### New Field: water.type

- **AC-2**: `water.type` is added to the `water` object: `type: string`, enum `["tap", "filtered", "reverse_osmosis", "bottled", "engineered"]`, optional (not in `required`).
- **AC-3**: Each of the five enum values (`tap`, `filtered`, `reverse_osmosis`, `bottled`, `engineered`) passes validation when used as `water.type`.
- **AC-4**: A value not in the enum (e.g. `"mineral"`) fails validation.
- **AC-5**: A capitalised value (e.g. `"Tap"`) fails validation (enum is case-sensitive).
- **AC-6**: Omitting `water.type` passes validation (field is optional).

### New Field: water.notes

- **AC-7**: `water.notes` is added to the `water` object: `type: string`, `minLength: 1`, `maxLength: 2000`, optional.
- **AC-8**: A non-empty string passes validation.
- **AC-9**: An empty string (`""`) fails validation (minLength: 1).
- **AC-10**: A string of exactly 2000 characters passes validation.
- **AC-11**: A string of 2001 characters fails validation (maxLength: 2000).
- **AC-12**: Omitting `water.notes` passes validation (field is optional).

### New Field: equipment.burr_set

- **AC-13**: `equipment.burr_set` is added to the `equipment` object: `type: string`, `minLength: 1`, `maxLength: 100`, optional.
- **AC-14**: A non-empty string (e.g. `"HU-32 98mm SSP"`) passes validation.
- **AC-15**: An empty string (`""`) fails validation (minLength: 1).
- **AC-16**: A string of exactly 100 characters passes validation.
- **AC-17**: A string of 101 characters fails validation (maxLength: 100).
- **AC-18**: Omitting `equipment.burr_set` passes validation (field is optional).

### New Field: equipment.rpm

- **AC-19**: `equipment.rpm` is added to the `equipment` object: `type: number`, `exclusiveMinimum: 0`, optional.
- **AC-20**: A positive integer (e.g. `300`) passes validation.
- **AC-21**: A positive float (e.g. `450.5`) passes validation.
- **AC-22**: `0` fails validation (exclusiveMinimum: 0).
- **AC-23**: A negative number (e.g. `-100`) fails validation.
- **AC-24**: A string (e.g. `"300"`) fails validation (type: number).
- **AC-25**: Omitting `equipment.rpm` passes validation (field is optional).

### Schema Copies in Sync

- **AC-26**: `brewlog/src/brewlog/brewspec.schema.json` is byte-for-byte identical to the root `brewspec.schema.json`.
- **AC-27**: `site/public/schema/v1.1.json` is byte-for-byte identical to the root `brewspec.schema.json`.

### Valid Examples Updated

- **AC-28**: All existing valid example files (YAML and JSON) are updated to `brewspec_version: "1.1"`.
- **AC-29**: A new example `examples/valid/water_and_grinder_hardware.yaml` exists and demonstrates all four new fields: `water.type`, `water.notes`, `equipment.burr_set`, `equipment.rpm`.

### Spec Document

- **AC-30**: `brewspec-v1.0.md` version header shows `Version: 1.1`.
- **AC-31**: `brewspec-v1.0.md` Water Object table contains rows for `water.type` and `water.notes` with correct constraints.
- **AC-32**: `brewspec-v1.0.md` Equipment Object table contains rows for `equipment.burr_set` and `equipment.rpm` with correct constraints.
- **AC-33**: `brewspec-v1.0.md` contains a "What Changed in v1.1" section describing all four new fields.

### Test Suite

- **AC-34**: The test suite covers all new fields. New tests include at minimum:
  - Each `water.type` enum value accepted (5 parametrised cases)
  - `water.type` invalid enum value rejected
  - `water.type` omitted passes
  - Schema structure assertion: `$defs/water/properties` contains `type`
  - `water.notes` non-empty string accepted
  - `water.notes` empty string rejected
  - `water.notes` at maxLength (2000) accepted
  - `water.notes` exceeding maxLength (2001) rejected
  - `water.notes` omitted passes
  - Schema structure assertion: `$defs/water/properties` contains `notes`
  - `equipment.burr_set` non-empty string accepted
  - `equipment.burr_set` empty string rejected
  - `equipment.burr_set` at maxLength (100) accepted
  - `equipment.burr_set` exceeding maxLength (101) rejected
  - `equipment.burr_set` omitted passes
  - Schema structure assertion: `$defs/equipment/properties` contains `burr_set`
  - `equipment.rpm` positive integer accepted
  - `equipment.rpm` positive float accepted
  - `equipment.rpm: 0` rejected
  - `equipment.rpm` negative value rejected
  - `equipment.rpm` string rejected
  - `equipment.rpm` omitted passes
  - Schema structure assertion: `$defs/equipment/properties` contains `rpm`
  - `brewspec_version: "1.0"` rejected by v1.1 schema
  - `water_and_grinder_hardware.yaml` passes v1.1 validation

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"1.1"`, `$id` to `.../v1.1.json`, `title` to `"BrewSpec v1.1"`
- **New field**: `water.type` (enum: tap, filtered, reverse_osmosis, bottled, engineered)
- **New field**: `water.notes` (string, minLength 1, maxLength 2000)
- **New field**: `equipment.burr_set` (string, minLength 1, maxLength 100)
- **New field**: `equipment.rpm` (number, exclusiveMinimum 0)
- All three schema copies updated in sync (root, brewlog, site/v1.1.json)
- Spec document `brewspec-v1.0.md` updated: version header, field tables, "What Changed in v1.1" section
- All valid example files bumped to `brewspec_version: "1.1"`
- New example `examples/valid/water_and_grinder_hardware.yaml` demonstrating all four fields

### Out of Scope

- Extended water chemistry (pH, bicarbonate, mineral breakdown) — deferred
- Grinder motor type or voltage — deferred
- Enumeration for RPM ranges — deferred; freeform number is sufficient for v1.1
- Any breaking changes to existing fields

---

## Non-Breaking Guarantee

All changes in v1.1 are additive. Existing v1.0 documents remain valid against the v1.0 schema. To validate against v1.1, the only required change is updating `brewspec_version` from `"1.0"` to `"1.1"`. No field has been removed, renamed, or had its constraints tightened.
