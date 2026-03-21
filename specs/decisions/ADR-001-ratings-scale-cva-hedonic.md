# ADR-001: Adopt the SCA CVA 9-Point Hedonic Scale for BrewSpec Ratings

**Date:** 2026-03-21
**Status:** Accepted
**Decider:** architect
**Affects:** BrewSpec, BrewLog CLI, all downstream tool builders

---

## Context

BrewSpec introduced a `result.ratings` object in v0.4 with eight sensory dimensions aligned to the SCA's legacy cupping protocol. The original scale was 1-5 (integers). This was a reasonable first choice at the time — the legacy protocol was the dominant reference, and a 1-5 scale is simple to implement and explain.

In 2024, the SCA adopted a replacement standard: the Coffee Value Assessment (CVA), document SCA-104. The CVA uses a 9-point hedonic scale for affective (consumer-sensory) assessment:

| Value | Label |
|-------|-------|
| 1 | Dislike extremely |
| 2 | Dislike very much |
| 3 | Dislike moderately |
| 4 | Dislike slightly |
| 5 | Neither like nor dislike |
| 6 | Like slightly |
| 7 | Like moderately |
| 8 | Like very much |
| 9 | Like extremely |

The CVA affective attribute names (fragrance, aroma, flavor, aftertaste, acidity, sweetness, mouthfeel, overall) match the eight BrewSpec rating fields after the v0.8 rename of `body` to `mouthfeel`.

Two practical problems arose from the 1-5 / CVA misalignment:

1. Coffee professionals working with CVA data could not use BrewSpec ratings fields directly. A CVA rating of 7 ("like moderately") had to be coerced to 3 or 4 before it could be stored in a BrewSpec document — damaging data fidelity and making BrewSpec unsuitable for professional use.

2. Tool builders targeting CVA-compatible workflows needed custom shim logic to bridge the scale difference. This raised the adoption cost and introduced a divergence point that BrewSpec's interoperability goal could not tolerate.

A decision was required: which rating scale should BrewSpec use going forward, and how should the transition be managed?

---

## Decision

BrewSpec adopts the SCA Coffee Value Assessment (CVA) 9-point hedonic scale (SCA-104, 2024) as the rating scale for all eight fields in `result.ratings`. The `minimum` on each field remains `1`. The `maximum` changes from `5` to `9`. This takes effect in BrewSpec v0.9.

> We will use the CVA 1-9 hedonic scale for all BrewSpec ratings fields, aligned to SCA-104 (2024).

---

## Rationale

- **The spec leads, products follow** — The CVA is now the primary SCA standard for affective sensory assessment. BrewSpec, as an open standard for the coffee industry, should track the current standard, not the superseded one. Staying on 1-5 would make BrewSpec a legacy format relative to the industry's current practice.

- **Interoperability over features** — A 1-9 scale that matches CVA means professionals can log CVA session results into BrewSpec without conversion. Tool builders can build CVA-compatible products on top of BrewSpec without shim logic. Any other scale would create a permanent interoperability gap.

- **Backward compatibility is preserved where possible** — The transition from 1-5 to 1-9 is backward-compatible for existing data: all values 1-5 remain valid on the 1-9 scale. V0.8 documents migrate to v0.9 with only a version bump; no rating values need to change. This is the most benign form of breaking change.

- **Schema constraints should be enforceable** — The 1-9 range is a concrete, enforceable constraint expressed as `minimum: 1, maximum: 9` in JSON Schema. It can be tested with valid and invalid examples, making the constraint visible and verifiable rather than documentary.

---

## Alternatives Considered

**Option: Keep 1-5 indefinitely**
- What it is: no scale change; BrewSpec ratings remain 1-5
- Why it was considered: avoids any breaking change; simpler for casual home brewers who may find 9 points unwieldy
- Why it was rejected: creates a permanent interoperability gap with CVA. Coffee professionals and tool builders targeting CVA workflows cannot use BrewSpec ratings without manual conversion. This conflicts with the interoperability goal and makes BrewSpec less useful precisely for the users — coffee professionals and tool builders — who are most likely to build the ecosystem around it.

**Option: 1-10 scale**
- What it is: expand to a 1-10 integer scale (common in consumer contexts)
- Why it was considered: familiar to general audiences; wide adoption in consumer product rating contexts
- Why it was rejected: 1-10 is not the CVA standard. Using it would still require conversion for CVA data (CVA maxes at 9, not 10). The goal is CVA alignment, not generic consumer familiarity. A 1-10 scale would retain the interoperability problem.

**Option: Float scale (e.g., 1.0-9.0 with decimal precision)**
- What it is: allow decimal ratings like 7.5
- Why it was considered: more granular; some manual scoring sheets use half-point increments
- Why it was rejected: the CVA hedonic scale uses whole integers 1-9. Allowing floats would diverge from the standard's intent and add implementation complexity in validators, UI, and storage. The `type: integer` constraint is simple, clear, and matches the standard exactly.

**Option: Map CVA values to BrewSpec's 1-5 scale with a lookup table**
- What it is: define a documented mapping (e.g., CVA 7-8 → BrewSpec 4, CVA 9 → BrewSpec 5) and document this in the spec
- Why it was considered: avoids a breaking change; preserves backward compatibility for validators
- Why it was rejected: a lossy mapping is worse than an honest scale change. CVA 6, 7, and 8 would all collapse onto BrewSpec 3 or 4. This destroys the expressiveness benefit of the CVA scale and produces data that misrepresents the original assessment. Data fidelity is more important than avoiding a version bump.

---

## Consequences

**Positive:**
- BrewSpec ratings are directly usable in CVA-aligned workflows without conversion
- Coffee professionals can store CVA affective session results in BrewSpec with full fidelity
- Tool builders targeting CVA workflows can build on BrewSpec without shim logic
- The spec is aligned to the current industry standard, not a superseded one
- Existing 1-5 data is valid on the 1-9 scale with no value changes

**Negative / Trade-offs:**
- V0.8 validators will reject v0.9 documents that contain ratings values 6-9. This is the standard version-mismatch pattern and is expected behaviour, but it means any validator hardcoded to v0.8 must be updated to validate v0.9 documents.
- The `examples/invalid/rating_out_of_range.yaml` file must be updated: the value `6` (which demonstrated the old out-of-range case) becomes valid in v0.9 and must change to `10`.
- Home brewers who built mental models around a 1-5 scale will need to adjust. The new scale is more expressive but also requires recalibration of what, say, a "4" means (on the 1-5 scale, 4 is above average; on the 1-9 scale, 4 is "dislike slightly").

**Neutral / What changes:**
- BrewLog CLI must update its Pydantic model, validation, CLI prompts, and display to accept 1-9 ratings (tracked in `brewlog-cli-v0.8`)
- The BrewSpec site must be updated to reflect the new scale in the landing page examples (tracked in `brewspec-site-v0.9`)
- Any downstream tool that currently validates against the v0.8 schema and enforces a maximum of 5 will need to adopt the v0.9 schema to accept values 6-9

---

## Review Notes

The scale change from 1-5 to 1-9 was confirmed as fully specified in the product spec (specs/products/brewspec-v0.9.md) with no open questions. The CVA anchor labels and attribute names are drawn directly from SCA-104 (2024). No user input was required to resolve this decision.
