# ADR-003: Split brew.notes into Process Notes and Cupping Notes

**Date:** 2026-03-29
**Status:** Accepted
**Decider:** architect
**Affects:** BrewSpec, BrewLog CLI, all downstream tool builders

---

## Context

BrewSpec v0.9 had a single `brew.notes` field intended for "brew-process notes — operational observations about the preparation." In practice, this field was used for two semantically different types of information:

1. **Process observations** — how the brew was prepared. Examples: "rinsed filter paper", "pre-infused 30s at 3 bar", "water from Brita filter", "re-calibrated grinder". These are observations about the preparation procedure and technique.

2. **Coffee sensory notes** — what the coffee tastes like before or outside of a specific brew. Examples: "bag notes: jasmine, peach, citrus", "SCA cupping score: 87", "Ethiopia lot described as: floral, berry". These are evaluations of the coffee ingredient, not of the brew process.

When both types of information exist, users were forced to either mix them in a single field or omit one. Coffee professionals conducting pre-brew cupping sessions had no standard field to record those observations in BrewSpec format — the only sensory field was `result.tasting_notes`, which is explicitly tied to a brew outcome.

The single-field model also created a semantic ambiguity: a tool builder reading `brew.notes` cannot determine whether the content is about how the brew was made or what the coffee tastes like. This makes parsing, display, and analysis unreliable.

There were two distinct decisions embedded in this change:
1. Rename `brew.notes` to `brew.process_notes` (breaking, to disambiguate the semantic clearly)
2. Add `coffee.cupping_notes` and `origin.cupping_notes` as new fields for pre-brew or bag-description sensory evaluations

---

## Decision

In BrewSpec v1.0, `brew.notes` is renamed to `brew.process_notes`. Two new optional fields are added: `coffee.cupping_notes` (sensory notes for the coffee as a whole) and `origin.cupping_notes` (sensory notes for a specific origin component).

> We will split the conflated `brew.notes` field into `brew.process_notes` (process observations) and `coffee.cupping_notes` / `origin.cupping_notes` (sensory evaluations), placing each in the object where it semantically belongs.

---

## Rationale

- **Schema constraints should be enforceable** — The semantic distinction between preparation observations and sensory evaluation is a real difference that belongs in the data model. A schema that cannot express this distinction cannot enforce it. A rename makes the constraint explicit and testable.

- **The spec leads, products follow** — Coffee professionals and tool builders who work with cupping data cannot use BrewSpec as their canonical format if sensory notes are conflated with process notes. The schema should be expressive enough for professional workflows.

- **Validate at every system boundary** — The `additionalProperties: false` pattern ensures that documents using the old `brew.notes` field name are rejected by v1.0 validators. This is the correct behaviour: silent acceptance of a migrated field would allow un-migrated documents to pass validation while losing the semantic distinction the rename was meant to establish.

**Placement of cupping notes fields:**
Cupping notes are placed on `coffee` and `origin` (not on `brew`) because they describe the coffee ingredient, not a specific brew session. A bag description exists before any brew happens. A cupping session produces notes about the coffee that apply across multiple brews. Placing these fields on `brew` would incorrectly imply that cupping notes are specific to a single brew event.

---

## Alternatives Considered

**Option: Keep `brew.notes` and add `coffee.cupping_notes` as a supplementary field**
- What it is: do not rename `brew.notes`; add cupping note fields without removing the existing field
- Why it was considered: avoids a breaking change; backward compatible; users who call their process notes "notes" can continue to do so
- Why it was rejected: the semantic ambiguity remains. `brew.notes` is still available for either use, which means tool builders cannot rely on it containing only process observations. The field name does not communicate its intended content, and the description is the only enforcement mechanism — which is not enforceable by the schema. The rename makes the distinction structural rather than documentary.

**Option: Rename `brew.notes` to `brew.process_notes` but add cupping notes at brew level**
- What it is: `brew.cupping_notes` instead of `coffee.cupping_notes`
- Why it was considered: keeps all non-result sensory notes at the brew level; simpler for users who think of everything in terms of a single brew event
- Why it was rejected: cupping notes describe the coffee ingredient, not the brew event. A pre-brew cupping session produces notes about the coffee that apply to all brews with that coffee, not just one. Placing cupping notes on `brew` would force users to copy the same notes onto every brew of the same coffee. The `coffee` object is the correct owner of coffee-level attributes; the `origin` object is the correct owner of origin-level attributes. This matches the existing pattern where `coffee.roast_level` and `coffee.roaster` are on the `coffee` object, not on the brew.

**Option: Use a separate top-level `cupping` array**
- What it is: a parallel `cupping:` array in the BrewSpec document, separate from `brews:`
- Why it was considered: keeps cupping sessions as first-class records; allows recording a cupping without any associated brew
- Why it was rejected: this is a significantly larger schema change that goes beyond the scope of v1.0. The `cupping_notes` fields on `coffee` and `origin` address the identified use cases (bag descriptions, pre-brew notes tied to a specific coffee) without restructuring the document model. A standalone cupping array could be added in a future version if demand grows.

---

## Consequences

**Positive:**
- `brew.process_notes` is unambiguously about preparation; tool builders can parse and display it with confidence about its content type
- `coffee.cupping_notes` and `origin.cupping_notes` provide a standard location for pre-brew or bag-description sensory evaluations
- Coffee professionals can store cupping session notes in BrewSpec format without them being mixed with process observations
- The existing `result.tasting_notes` field continues to serve its role as brew-outcome sensory description; the three fields (`brew.process_notes`, `coffee.cupping_notes`, `result.tasting_notes`) now form a complete, non-overlapping set of text note fields

**Negative / Trade-offs:**
- `brew.notes` is removed. All v0.9 documents that use this field are invalid under v1.0 until migrated. The migration path is a simple rename.
- Tool builders who stored mixed content in `brew.notes` will need to decide how to separate process observations from sensory notes during migration. The schema cannot do this separation automatically.

**Neutral / What changes:**
- BrewLog CLI must rename its `notes` column and Pydantic field to `process_notes`, add `coffee_cupping_notes` and `origin_cupping_notes` fields to its data model, and update any CLI prompts or display that referenced `notes` (tracked under `brewlog-cli-v1.0`)
- The `roast_level` field description in the schema references "the brew-level notes field" as a fallback for finer roast detail — this reference should be updated to `brew.process_notes` during the v1.0 schema update
