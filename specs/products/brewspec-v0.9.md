# Product: BrewSpec v0.9

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-21
**Last Updated:** 2026-03-21

---

## Problem Statement

BrewSpec's `ratings` object was introduced in v0.4, aligned to the SCA's legacy cupping protocol, using a 1-5 integer scale. The SCA adopted a replacement standard in 2024 — the Coffee Value Assessment (CVA), document SCA-104 — which uses a 9-point hedonic scale for affective (consumer-sensory) assessment. The CVA scale is:

- 1 = dislike extremely
- 2 = dislike very much
- 3 = dislike moderately
- 4 = dislike slightly
- 5 = neither like nor dislike
- 6 = like slightly
- 7 = like moderately
- 8 = like very much
- 9 = like extremely

The CVA attributes covered by BrewSpec's existing ratings fields are: fragrance, aroma, flavor, aftertaste, acidity, sweetness, mouthfeel, and overall. BrewSpec already uses the correct CVA attribute names as of v0.8 (`mouthfeel` replaced `body` in v0.8). The only remaining misalignment is the scale: BrewSpec uses 1-5 where the CVA uses 1-9.

This misalignment creates two practical problems:

1. **Interoperability gap.** Coffee professionals and tool builders working with CVA data cannot use BrewSpec ratings fields directly — they must convert or store data outside the spec.
2. **Constrained expressiveness.** The 1-9 hedonic scale has more resolution than 1-5. Forcing home brewers onto a 1-5 scale means data that was entered as, say, a 7 on a familiar consumer scale must be coerced down to 3 or 4 before it can be stored.

Target personas:
- **Coffee professionals** — need CVA-aligned fields to log cupping and tasting session results in a standard format without manual conversion.
- **Home brewers** — benefit from the broader 9-point scale, which is more intuitive (mirrors common consumer rating patterns) and more expressive.
- **Tool builders** — need the schema to match the current industry standard so they can build CVA-compatible tools on top of BrewSpec without custom shim logic.

### Note on body → mouthfeel rename

The manifest task description for v0.9 includes "rename ratings.body → ratings.mouthfeel". This rename was completed in v0.8: the field is already named `mouthfeel` in both `brewspec.schema.json` and the `brewspec-v0.8.md` spec document. The v0.9 scope is the 1-9 scale change only. This spec confirms the rename is complete and does not re-do it.

---

## User Stories

- As a **coffee professional**, I want to record CVA affective ratings on a 1-9 scale so that my BrewSpec brew logs are directly compatible with my CVA tasting session data without any conversion.
- As a **home brewer**, I want to rate my brews on a 1-9 scale so that I have more resolution to distinguish between brews I like slightly versus brews I like very much.
- As a **tool builder**, I want BrewSpec ratings fields to use the CVA 1-9 hedonic scale so that I can build CVA-compatible tools without mapping BrewSpec ratings to a different scale.
- As a **home brewer** with existing brew logs recorded on the 1-5 scale, I want my existing ratings (1-5) to remain valid under v0.9 so that I do not need to re-enter historical data.

---

## Acceptance Criteria

### Schema Version Bump

- **AC-1**: The JSON Schema is updated so that `brewspec_version` validates against `const: "0.9"`. Documents declaring `brewspec_version: "0.8"` are rejected by the v0.9 schema.

### Ratings Scale: 1-9

- **AC-2**: All eight fields in the `ratings` object (`overall`, `fragrance`, `aroma`, `flavour`, `aftertaste`, `acidity`, `sweetness`, `mouthfeel`) are updated to `minimum: 1`, `maximum: 9`.
- **AC-3**: A brew with any ratings field set to `1` passes validation.
- **AC-4**: A brew with any ratings field set to `5` passes validation (existing 1-5 values remain valid).
- **AC-5**: A brew with any ratings field set to `9` passes validation.
- **AC-6**: A brew with any ratings field set to `0` fails validation (below minimum of 1).
- **AC-7**: A brew with any ratings field set to `10` fails validation (above maximum of 9).
- **AC-8**: A brew with any ratings field set to `6`, `7`, or `8` passes validation (previously out-of-range on the 1-5 scale).
- **AC-9**: A brew document with no `ratings` object passes validation (the ratings object remains entirely optional).
- **AC-10**: A brew with a `ratings` object that omits all eight fields passes validation (all individual rating fields remain optional).

### Ratings Descriptions

- **AC-11**: The JSON Schema description for the `ratings` object is updated to reference the CVA 1-9 hedonic scale and the SCA Coffee Value Assessment (SCA-104, 2024).
- **AC-12**: The JSON Schema description for each ratings field is updated to reflect the 1-9 scale endpoints. At minimum: `overall` description reflects `1 = dislike extremely, 9 = like extremely`. The description pattern is consistent across all eight fields.

### Invalid Example Update

- **AC-13**: The existing invalid example `examples/invalid/rating_out_of_range.yaml` is updated so that the out-of-range value is `10` (exceeds the new maximum of 9). The file comment is updated to reflect the new valid range of 1-9.

### Valid Examples Update

- **AC-14**: All valid example files that contain a `ratings` object are updated to `brewspec_version: "0.9"`. Rating values in these files do not need to change — existing 1-5 values are valid on the 1-9 scale.
- **AC-15**: All other valid example files (those without a `ratings` object) are updated to `brewspec_version: "0.9"`.
- **AC-16**: At least one valid example file contains a ratings field with a value in the 6-9 range, demonstrating the expanded scale. The existing `examples/valid/light_roast_ethiopian.yaml` is the recommended file to update with a 6-9 value.

### Spec Document

- **AC-17**: `brewspec-v0.9.md` exists as the canonical spec document for v0.9. It contains a complete, updated field reference covering all fields, with the `ratings` table updated to show `integers 1-9 (CVA hedonic scale)`.
- **AC-18**: `brewspec-v0.9.md` contains a "What Changed in v0.9" section documenting: the ratings scale change from 1-5 to 1-9, the CVA standard alignment, and the breaking nature of the scale change (values 6-9 are now valid; existing 1-5 values remain valid).
- **AC-19**: `brewspec-v0.9.md` contains a "Backward Compatibility" section explaining: v0.8 documents containing ratings values 1-5 are valid under v0.9 with only a version bump. No rating values need to be changed during migration.
- **AC-20**: `brewspec-v0.9.md` includes a section explaining the CVA hedonic scale anchors (1 = dislike extremely through 9 = like extremely) and the SCA-104 reference.

### Test Suite

- **AC-21**: The test suite is updated to cover all new and changed ACs. New and updated tests include at minimum:
  - Each of the eight ratings fields accepts value `1`
  - Each of the eight ratings fields accepts value `5` (backward compatibility)
  - Each of the eight ratings fields accepts value `9`
  - Each of the eight ratings fields rejects value `0`
  - Each of the eight ratings fields rejects value `10`
  - At least one ratings field accepts value `6`
  - At least one ratings field accepts value `7`
  - At least one ratings field accepts value `8`
  - `rating_out_of_range.yaml` (value `10`) fails validation
  - `brewspec_version: "0.8"` is rejected by the v0.9 schema

---

## Scope

### In Scope

- Schema version bump: `brewspec_version` const to `"0.9"`
- All eight ratings fields updated: `minimum: 1`, `maximum: 9` — **breaking change** (values 6-9 now valid; values 0 and 10 now consistently invalid)
- JSON Schema descriptions for `ratings` object and all eight fields updated to reference CVA and the 1-9 scale
- Spec document `brewspec-v0.9.md` written with updated field reference, changelog, and backward compatibility sections
- All valid example files updated to `brewspec_version: "0.9"`
- `examples/invalid/rating_out_of_range.yaml` updated: out-of-range value changed from `6` to `10`, comment updated
- At least one valid example updated to demonstrate a rating value in the 6-9 range
- Test suite updated to cover all ACs above

### Out of Scope

- **New ratings dimensions** — the eight CVA attributes already in the schema (fragrance, aroma, flavour, aftertaste, acidity, sweetness, mouthfeel, overall) cover the CVA affective assessment. No new attributes are added in v0.9.
- **CVA descriptive assessment** (SCA-105) — the descriptive protocol uses a different data structure (QForm). Mapping that to BrewSpec is deferred until there is demonstrated demand from tool builders.
- **Floating-point or decimal ratings** — the CVA hedonic scale uses whole integers 1-9. The `ratings` fields remain `type: integer`. No decimal values.
- **BrewLog CLI v0.8** — separate downstream task depending on this spec.
- **BrewSpec Site v0.9** — separate downstream task in express tier.
- **body → mouthfeel rename** — already completed in v0.8. No action required.

---

## Design Notes

### Breaking change characterisation

This is a schema-tightening change in one direction (the maximum increases from 5 to 9) and a relaxation in another (values 6-9 go from invalid to valid). Whether this constitutes a "breaking change" depends on perspective:

- **For validators:** a v0.8 schema validating a v0.9 document with a rating of `7` would reject it (7 > 5). From the v0.8 schema's point of view, that's a breaking change.
- **For existing documents:** all v0.8 documents with ratings values 1-5 pass v0.9 validation with only a version bump. No data migration is needed.

The practical effect is one-directional breakage: v0.9 documents may contain ratings values that v0.8 schemas reject. This is the standard pattern for BrewSpec version evolution.

### CVA hedonic scale anchors

For reference in spec document and schema descriptions:

| Value | Anchor label |
|-------|--------------|
| 1 | Dislike extremely |
| 2 | Dislike very much |
| 3 | Dislike moderately |
| 4 | Dislike slightly |
| 5 | Neither like nor dislike |
| 6 | Like slightly |
| 7 | Like moderately |
| 8 | Like very much |
| 9 | Like extremely |

### Full v0.9 ratings structure (for Architect)

Changes from v0.8 are marked.

```yaml
result:
  ratings:                         # optional object
    overall: 7                     # integer 1-9 (CHANGED — was 1-5 in v0.8)
    fragrance: 6                   # integer 1-9 (CHANGED — was 1-5 in v0.8)
    aroma: 8                       # integer 1-9 (CHANGED — was 1-5 in v0.8)
    flavour: 7                     # integer 1-9 (CHANGED — was 1-5 in v0.8)
    aftertaste: 7                  # integer 1-9 (CHANGED — was 1-5 in v0.8)
    acidity: 8                     # integer 1-9 (CHANGED — was 1-5 in v0.8)
    sweetness: 6                   # integer 1-9 (CHANGED — was 1-5 in v0.8)
    mouthfeel: 7                   # integer 1-9 (CHANGED — was 1-5 in v0.8)
```

All other fields in the schema are unchanged from v0.8.

### Invalid example update

The current `examples/invalid/rating_out_of_range.yaml` tests `overall: 6`, which was out-of-range on the 1-5 scale. Under v0.9, `6` is a valid rating. The invalid example must be updated to use `overall: 10` (or any value > 9) to remain a meaningful negative test case.

---

## Security Requirements

- **Data sensitivity:** Ratings are personal sensory preferences. Not PII. Sensitivity profile unchanged from v0.8.
- **Input validation:** All ratings fields remain `type: integer` with explicit `minimum` and `maximum` constraints. The only change is that `maximum` increases from `5` to `9`. No new injection surface. Integer type prevents string injection. Schema validation continues to be the enforcement mechanism.
- **Safe parsing:** No change to the existing safe-parse requirement (`yaml.safe_load()`, then schema validation). The scale change does not affect the parsing pipeline.
- **File I/O:** Example files are plain YAML. No change to file I/O patterns.
- **No secrets in examples:** Rating values in examples are plain integers. No credentials, API keys, or PII.

---

## Dependencies

- **Depends on:** `brewspec-v0.8` (done) — this version builds on the v0.8 schema and spec
- **Blocks:** `brewlog-cli-v0.8` (BrewLog CLI must adopt the 1-9 scale and update its Pydantic model, DB, prompts, and display); `brewspec-site-v0.9` (landing page update)
- **Downstream impact:** Any tool that stores or validates BrewSpec ratings will need to accept values 6-9 after adopting v0.9. Tools that stored ratings as 1-5 integers need no data migration — existing values remain valid.

---

## Success Metrics

- The JSON Schema v0.9 passes meta-validation (is itself a valid JSON Schema)
- All existing valid examples pass v0.9 validation after version bump (no rating data changes needed)
- All existing invalid examples continue to fail v0.9 validation
- `examples/invalid/rating_out_of_range.yaml` (value `10`) fails v0.9 validation
- At least one valid example contains a rating value in the 6-9 range and passes validation
- Test suite passes with ruff clean
- The ratings scale change is the only schema change in v0.9 — no other fields are affected

---

## Open Questions

None. Scope is fully specified and approved. The CVA scale anchors and attribute names are drawn directly from SCA-104 (2024).
