# ADR-002: Establish Recipe/Result Field Symmetry for Water and Yield

**Date:** 2026-03-29
**Status:** Accepted
**Decider:** architect
**Affects:** BrewSpec, BrewLog CLI, all downstream tool builders

---

## Context

BrewSpec v0.9 had an asymmetry in how it modelled recipe intent versus measured outcome for two key brew variables: water weight and output yield.

**Water:** The brew object had `water_weight_g` as a recipe-level field (what you plan to use). The result object had no corresponding field for what water was actually used. A brewer who intended to use 280g but actually used 275g had no way to record both values — only the recipe intent could be stored.

**Yield:** The result object had `result.yield_g` (actual output weight — what you measured). The brew object had no corresponding field for intended yield. For espresso dialling, the target output weight (the recipe) is a separate value from what was actually collected. Without `brew.yield_g`, brewers could not store "I targeted 36g out" alongside "I actually got 34g."

Additionally, the field name `water_weight_g` was redundant — grams already denotes weight. All other measurement fields in the schema follow the `field_unit` naming pattern (`dose_g`, `water_temp_c`, `duration_s`, `elevation_masl`), making `water_weight_g` an outlier that does not follow the convention.

Three options were available for addressing this:

1. Add `result.water_g` and `brew.yield_g` as new fields without renaming the existing `water_weight_g`.
2. Rename `water_weight_g` to `water_g` to fix the naming inconsistency, and add `result.water_g` and `brew.yield_g` to complete the symmetry.
3. Defer the rename and add only the missing fields as `result.water_g` and `brew.yield_g`.

Because v1.0 was already a breaking version (combining four breaking changes), bundling the rename with the symmetry additions incurred no additional version bump. Leaving the naming inconsistency would have meant carrying a known debt item into v1.0 and potentially deferring it to v2.0 with no gain.

---

## Decision

In BrewSpec v1.0, `brew.water_weight_g` is renamed to `brew.water_g`. Two new optional fields are added: `brew.yield_g` (recipe target output weight) and `result.water_g` (actual water used). The existing `result.yield_g` is unchanged.

> We will establish recipe/result symmetry by renaming `brew.water_weight_g` to `brew.water_g` and adding `brew.yield_g` and `result.water_g`, creating matching pairs for both water and yield at the recipe (intent) and result (measurement) levels.

The full symmetry table is:

| Intent (recipe) | Actual (result) |
|---|---|
| `brew.water_g` | `result.water_g` |
| `brew.yield_g` | `result.yield_g` |

---

## Rationale

- **Schema constraints should be enforceable** — The symmetry is a concrete, testable model. Each field has a clear, distinct meaning (intent vs. measurement) with `exclusiveMinimum: 0` constraints that are enforceable.

- **Additive changes are preferred over breaking changes** — The two new fields (`brew.yield_g`, `result.water_g`) are additive (optional). The rename of `water_weight_g` to `water_g` is a breaking change, but it is justified because: (a) the naming inconsistency would accumulate as debt; (b) v1.0 already requires a version bump for other breaking changes, so the marginal cost of this rename is low; (c) the `field_unit` naming convention is now applied uniformly across all measurement fields.

- **The spec leads, products follow** — The rename is evaluated on its merit as a spec improvement (consistent naming, reduced cognitive overhead for tool builders) rather than as accommodation for a specific product.

---

## Alternatives Considered

**Option: Keep `water_weight_g` and add new fields without renaming**
- What it is: leave `brew.water_weight_g` as-is, add `result.water_g` and `brew.yield_g`
- Why it was considered: avoids the rename as a breaking change; simpler migration for existing v0.9 tools
- Why it was rejected: the naming inconsistency would persist indefinitely. `water_weight_g` is the only measurement field that does not follow the `field_unit` convention. Fixing it later would require another breaking version for a purely cosmetic change. Since v1.0 is already breaking, the cost of bundling the rename is near zero.

**Option: Rename to `water_g` but do not add `brew.yield_g` or `result.water_g`**
- What it is: fix the naming inconsistency only; defer symmetry additions
- Why it was considered: a smaller change set for v1.0
- Why it was rejected: the asymmetry problem was the root cause identified in the product spec. Fixing the name without completing the symmetry would have addressed the cosmetic issue but left the data model gap open. Both are motivated by the same core problem — it is cleaner to solve them together.

**Option: Use `brew.target_water_g` and `brew.target_yield_g` to distinguish intent from recipe fields**
- What it is: use a `target_` prefix to distinguish recipe-intent fields from result-actual fields
- Why it was considered: more explicit about the recipe-vs-measurement distinction
- Why it was rejected: the existing `result.*` prefix already creates the structural distinction between intent (brew level) and measurement (result level). Adding a `target_` prefix on top of the structural distinction is redundant and inconsistent with the naming convention for other brew-level fields (`dose_g`, `duration_s`). A user setting up a recipe populates brew-level fields; those are the recipe. No prefix needed.

---

## Consequences

**Positive:**
- Consistent `field_unit` naming across all measurement fields — tool builders apply one pattern
- Brewers can now record both recipe intent and actual measurement for water and yield — enabling deviation tracking
- Espresso dialling workflow is fully representable: `brew.yield_g` (target) alongside `result.yield_g` (actual) in the same document
- `brew_ratio` description can be updated to reference `brew.water_g` without a field name change

**Negative / Trade-offs:**
- `brew.water_weight_g` is removed. All v0.9 documents that use this field are invalid under v1.0 until migrated. This is the intended behaviour — `additionalProperties: false` ensures the old field name is rejected, not silently dropped.
- Every v0.9 example file that uses `water_weight_g` must be updated. Every invalid example that uses `water_weight_g` must be reviewed to confirm its intended failure case still holds.

**Neutral / What changes:**
- BrewLog CLI must rename its `water_weight_g` column and Pydantic field to `water_g`, add `yield_g` to the brew model, and add `water_g` to the result model (tracked under `brewlog-cli-v1.0`)
- The `brew_ratio` description in the schema references `water_weight_g`; it must be updated to `water_g` in this version bump (no field change, description-only update)
- The `result.yield_g` description references `water_weight_g`; it must also be updated to `brew.water_g`

---

## Review Notes

The naming inconsistency and symmetry gap were both identified in the product spec as motivated by the same root cause. The decision to bundle rename and additions was confirmed by the architect during design — no user input required.
