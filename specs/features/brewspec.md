---
feature: brewspec-format
status: implemented        # implemented | partial | planned
last_updated: 2026-06-06
linear: []                 # not on Linear; version history in versions/ and git
---

# BrewSpec Format

> The open data format for describing coffee brews. This is the canonical, as-built record of what a valid BrewSpec document is; the published prose standard is `brewspec-v1.1.md` and the machine contract is `brewspec.schema.json` (the single source of truth — if docs and schema disagree, the schema wins).

## Behaviour

A BrewSpec document is a JSON/YAML object `{ brewspec_version, brews: [...] }` — both **required**. Each entry in `brews` is one brew, composed of optional sub-objects. Every object sets `additionalProperties: false`; every field within the sub-objects is optional, so a minimal brew is nearly empty and a full one is richly detailed.

A brew separates **intent** (the recipe you planned) from **measurement** (what actually happened), with matching field pairs across the two (see the symmetry decision below).

### Brew object — recipe intent
The planned brew: `brew_type`, `dose_g`, `water_g`, `yield_g`, `water_temp_c`, `duration_s`, grind, and `process_notes` (process observations). Top-level brew identity (date, etc.) lives here too.

### Coffee object (+ origins)
The coffee used: identity fields and `cupping_notes` (sensory evaluation of the coffee as a whole). An optional `origins` array carries per-origin detail, each with its own `cupping_notes`.

### Water, Equipment objects
Optional descriptors of the water profile and the gear (grinder, brewer, etc.).

### Result object — measurement
What was measured: `water_g`, `yield_g`, `dose_g`, `duration_s` (the actuals matching the recipe intents), plus the `ratings` object.

### Ratings object
Eight sensory fields scored on the **CVA 1–9 hedonic scale** (integers, min 1, max 9).

## Data model

The JSON Schema (`brewspec.schema.json`) is canonical; `brewspec-v1.1.md` carries the full field-by-field reference. Load-bearing invariants:

- `brewspec_version` and `brews` are required; everything else is optional.
- Objects are closed (`additionalProperties: false`) — unknown fields are invalid.
- Numeric fields using `multipleOf: 0.1` must be parsed as `Decimal`, not float, or validation drifts on floating-point representation (see `brewspec-v1.1.md` § Validation).

## Versioning & compatibility

**The schema is a backward-compatible contract.** New versions *add* fields; they never remove or repurpose an existing one. A change that breaks an existing valid document is a version bump with migration guidance and a snapshot in `versions/`. Documents from older versions remain valid for their unchanged fields. The current published version is **v1.1**.

## Known limitations

Open questions and deferred items are tracked in `brewspec-v1.1.md` § Open Questions and in `roadmap.md`. Per-origin normalisation and a few sensory dimensions are deliberately left to future versions.

## Decisions

### Decision: CVA 1–9 hedonic rating scale (was ADR-001)

*Decided 2026 (effective v0.9).*

**Context.** Ratings originally used a 1–5 scale with no alignment to an industry standard. The SCA published the Coffee Value Assessment (CVA, SCA-104, 2024) with a 9-point hedonic scale that the specialty industry is standardising on.

**Decision.** All eight `result.ratings` fields use the **CVA 9-point hedonic scale** — integers, `minimum: 1`, `maximum: 9`.

**Alternatives.** Keep 1–5 (loses industry alignment and import/export interoperability with CVA tools); a bespoke scale (no interoperability — against the spec's core purpose).

**Consequences.** Aligns BrewSpec with the SCA standard. Raising the `maximum` from 5 to 9 is a breaking change for ratings; downstream tools must accept 1–9.

### Decision: Recipe/result field symmetry (was ADR-002)

*Decided 2026, delivered in two phases (v1.0 + a non-breaking follow-on).*

**Context.** v0.9 modelled intent and measurement asymmetrically: `water_weight_g` existed only at recipe level, `yield_g` only at result level, so a brewer could not record both planned and actual for water or yield. `water_weight_g` was also a naming outlier (grams already implies weight) versus the `field_unit` convention (`dose_g`, `water_temp_c`).

**Decision.** Rename `brew.water_weight_g` → `brew.water_g`, and add `brew.yield_g`, `result.water_g`, `result.dose_g`, `result.duration_s` — matching **intent/actual pairs for all four core measurements** (dose, water, yield, duration).

**Alternatives.** Add the missing fields without the rename (carries the naming inconsistency as debt into v1.0); defer the rename to a later major version (no gain, more churn later).

**Consequences.** Full symmetry; a brewer records target and actual for every core variable. The rename is breaking and was bundled into the already-breaking v1.0 (no extra version bump). `result.dose_g`/`result.duration_s` were backported additively in a follow-on.

### Decision: Notes field differentiation (was ADR-003)

*Decided 2026 (v1.0).*

**Context.** `brew.notes` conflated two different things: observations about the *process* and sensory evaluation of the *coffee*. Sensory notes belong to the coffee (or a specific origin), not the brew event.

**Decision.** Rename `brew.notes` → `brew.process_notes`, and add `coffee.cupping_notes` and `origin.cupping_notes`, placing each note type in the object where it semantically belongs.

**Alternatives.** Keep a single `notes` field (conflation persists, harder for tools to use); freeform tags (loses the semantic structure).

**Consequences.** Cleaner data model; sensory data attaches to the coffee/origin and survives across brews. The rename is breaking (v1.0).

## Cross-references

- `brewspec-v1.1.md` — the published human-readable standard (full field reference)
- `brewspec.schema.json` — the machine contract (canonical)
- `specs/features/brewlog.md` — the reference CLI that round-trips this format
- `specs/arch/principles.md` — architecture principles (schema-canonical, portability)
- `versions/` — released spec snapshots
