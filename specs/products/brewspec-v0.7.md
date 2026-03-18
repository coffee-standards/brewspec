# Product: BrewSpec v0.7

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-15
**Last Updated:** 2026-03-15

---

## Problem Statement

Two gaps in BrewSpec v0.6 block the next Calibrate Coffee iteration:

1. **No yield field.** Espresso brewing treats output weight (`yield_g`) as a first-class recipe metric — it defines the recipe alongside dose. Without a standard field for it, espresso brews cannot be fully described in BrewSpec, and Calibrate's component card model cannot represent the espresso process card correctly.

2. **Four required fields make partial exports invalid.** The Calibrate component card model decomposes a brew into reusable cards (Coffee, Process, Equipment, Water) and a Brew Record. A BrewSpec export representing only a subset of those cards — for example, just a Coffee Card or just a Process Card — fails v0.6 validation because `date`, `type`, `dose_g`, and `water_weight_g` are required. The schema must allow partial representations.

These changes unblock the Tool Builder persona (building Calibrate on top of BrewSpec) and improve the schema's fitness as a general-purpose interchange format for the Coffee Professional persona.

---

## User Stories

- As a **Tool Builder**, I want to export partial brew data (e.g. a coffee card with no process parameters) in a valid BrewSpec document so that I can represent component-level data without fabricating field values.
- As a **Coffee Professional** using an espresso-focused tool, I want to record my shot's output weight in a standard field so that my yield data is portable to any BrewSpec-compatible app.
- As a **Home Brewer** tracking espresso, I want `yield_g` stored in the result of my brew log so that I can review my yield history alongside TDS and extraction yield.
- As a **Tool Builder** implementing BrewSpec validation, I want the schema change from required-to-optional to be clearly documented with a migration path so that I can update my validator with confidence.

---

## Acceptance Criteria

**AC-1:** The `result` object schema adds an optional `yield_g` field of type `number` with `exclusiveMinimum: 0`. A brew document with `result.yield_g` present and a positive value passes v0.7 validation.

**AC-2:** A brew document with `result.yield_g` set to `0` or a negative number fails v0.7 validation.

**AC-3:** A brew document with no `result.yield_g` field passes v0.7 validation (the field is optional).

**AC-4:** The four previously required brew object fields — `date`, `type`, `dose_g`, `water_weight_g` — are optional in v0.7. A brew document omitting all four passes validation, provided `brewspec_version` is present and `brews` contains at least one object.

**AC-5:** A brew document that was valid under v0.6 (with all four required fields present and correct) is also valid under v0.7 with only a `brewspec_version` bump. No v0.6 valid document is broken by this change.

**AC-6:** The spec document describes the espresso use case for `yield_g`: that it functions as both a recipe target (what the brewer aims for) and a measured result (what was actually produced), and that BrewSpec represents it solely as a result field in `result.yield_g`. The placement in BrewSpec does not imply where consuming tools (such as Calibrate) store or display it.

**AC-7:** The "What Changed in v0.7" section of the spec document identifies the removal of required constraints on `date`, `type`, `dose_g`, and `water_weight_g` as a breaking change, with a migration note explaining that existing v0.6-valid documents require only a version bump and no structural changes.

**AC-8:** The JSON Schema is updated: `brewspec_version` remains the only field in the `required` array at the top level; `brews` remains required. Within each brew object, the `required` array is removed or left empty (no required brew-level fields).

**AC-9:** A valid example file `examples/valid/espresso_with_yield.yaml` is added demonstrating an espresso brew with `result.yield_g` populated.

**AC-10:** An invalid example file `examples/invalid/invalid_yield_zero.yaml` is added demonstrating a `result.yield_g` value of `0` being rejected.

---

## Scope

### In Scope

- Add `result.yield_g` as an optional `number` field with `exclusiveMinimum: 0`
- Remove `date`, `type`, `dose_g`, and `water_weight_g` from the brew object's `required` array
- Update `brewspec_version` value to `"0.7"` in the schema
- Update the spec document (`brewspec-v0.7.md`) with field reference, changelog, and backward compatibility sections
- Add valid example: `examples/valid/espresso_with_yield.yaml`
- Add invalid example: `examples/invalid/invalid_yield_zero.yaml`
- Update BrewLog CLI schema version reference to accept v0.7 documents
- Update existing valid examples to use `brewspec_version: "0.7"` where the test suite requires it

### Out of Scope

- Any Calibrate-side data model changes (component card model is a separate task)
- Extended water chemistry fields (`ph`, bicarbonate, mineral breakdown) — deferred since v0.5
- Pour schedules or step-by-step timing
- A migration tool or script for upgrading v0.6 documents (manual bump of `brewspec_version` is sufficient)
- Standardized enumeration for `method` (deferred pending usage data)
- Any new required fields

---

## Design Notes

### `result.yield_g` placement

`yield_g` belongs in the `result` object, not at the brew level. The `result` object groups measured brew outcomes; yield is a measured output (the weight of liquid in the cup). For espresso specifically, yield is also used as a recipe target, but that concern is handled by the consuming application (Calibrate's Process Card), not by BrewSpec. The schema stays simple: one field, one location.

### Espresso context note (for the spec doc)

The spec document should include a note under `result.yield_g` explaining: for espresso, brewers set a target yield as part of the recipe (e.g. "18 g in, 36 g out"). The measured output weight at brew time is the value stored here. Tools that implement a process card model (such as Calibrate) may additionally store a target yield on their internal process card — that is an application-level concern beyond the scope of BrewSpec.

### Making fields optional — what "breaking" means here

Removing a `required` constraint is technically a breaking change for **validators** (they must re-build or update their compiled schemas) and for any **consuming tool** that assumes these fields will always be present and reads them without a null check. It is not a breaking change for existing documents — all valid v0.6 documents remain valid under v0.7. The "What Changed" section of the spec must call this out clearly.

### Brew object `required` array

In v0.6, the brew object schema has: `required: [date, type, dose_g, water_weight_g]`. In v0.7, this array is removed entirely (or replaced with an empty array). `brewspec_version` at the top level and the `brews` array itself remain required.

---

## Security Requirements

- **Data sensitivity:** `result.yield_g` is brew measurement data — not personally identifiable. Same sensitivity profile as existing result fields.
- **Input validation:** `yield_g` must be validated as a number with `exclusiveMinimum: 0` at schema validation time, before storage. A value of `0` or negative must be rejected. Non-numeric inputs must be rejected by type check.
- **Safe parsing:** No change to the existing safe-parse requirement (YAML safe_load, JSON parse before schema validation). The removal of required fields does not weaken the validation pipeline — schema validation still runs on all inputs.
- **File I/O:** Exported BrewSpec files containing `result.yield_g` require no special handling beyond existing safe-parse rules.

---

## Dependencies

- **Depends on:** `brewspec-v0.6` (done) — this version builds on the v0.6 schema
- **Blocks:** Calibrate component card model implementation (the next Calibrate iteration requires v0.7 for partial-export validity and espresso yield representation)

---

## Success Metrics

- The JSON Schema passes all existing valid examples under v0.7 (no regressions)
- The JSON Schema rejects all existing invalid examples under v0.7 (no false passes)
- `examples/valid/espresso_with_yield.yaml` passes v0.7 validation
- `examples/invalid/invalid_yield_zero.yaml` fails v0.7 validation
- A brew document containing only `brewspec_version` and one empty brew object passes v0.7 validation (confirms all-optional behaviour)
- Test suite passes with ruff clean

---

## Open Questions

None. Both changes are fully specified. Domain assumptions about espresso yield validated against the component card mapping document (`specs/designs/component-card-mapping.md`).
