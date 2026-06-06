# Product: Site — BrewSpec v1.1 Field Documentation

**Status:** Backlog
**Priority:** P2 (Normal)
**Author:** Scott Luengen
**Created:** 2026-06-06

---

## Problem Statement

BrewSpec v1.1 shipped four new fields (`water.type`, `water.notes`, `equipment.burr_set`, `equipment.rpm`) and published the updated schema to `site/public/schema/v1.1.json`. The docs site was not updated as part of that release. Two things are now stale:

1. **Hero version string.** `Hero.astro` hardcodes `brewspec_version: "1.0"` in the YAML example shown on the landing page. Visitors see a version that doesn't match the current standard.
2. **Field reference page.** `schema.astro` documents the `water` section with only `ppm`, and the `equipment` section with no `burr_set` or `rpm`. The four v1.1 fields are absent from the reference visitors use to understand the format.

---

## Acceptance Criteria

### Hero version string

- **AC-1:** `site/src/components/Hero.astro` shows `brewspec_version: "1.1"` in the YAML code block.

### Field reference — Water section

- **AC-2:** The water table in `schema.astro` includes a row for `water.type`: type `string`, constraint `enum: tap | filtered | reverse_osmosis | bottled | engineered`, description "Water source category."
- **AC-3:** The water table includes a row for `water.notes`: type `string`, constraint `minLength: 1, maxLength: 2000`, description "Free-text notes on the water used (brand, mineral profile, etc.)."
- **AC-4:** Both new rows appear after the existing `ppm` row.

### Field reference — Equipment section

- **AC-5:** The equipment table in `schema.astro` includes a row for `equipment.burr_set`: type `string`, constraint `minLength: 1, maxLength: 100`, description "Burr set installed in the grinder."
- **AC-6:** The equipment table includes a row for `equipment.rpm`: type `number`, constraint `> 0`, description "Grinder motor speed in RPM (variable-speed grinders)."
- **AC-7:** Both new rows appear after the existing `grinder_setting` row and before `pressure_bar`.

### Content test

- **AC-8:** `site/src/content.test.ts` passes with no changes required (new content is additive and should not break existing assertions). If the test file asserts on field counts or specific field names, it must be updated to include the four new fields.

---

## Scope

### In Scope

- Update `brewspec_version` string in `Hero.astro`: `"1.0"` → `"1.1"`
- Add `water.type` and `water.notes` rows to the Water table in `schema.astro`
- Add `equipment.burr_set` and `equipment.rpm` rows to the Equipment table in `schema.astro`
- Update `content.test.ts` if it asserts on field presence (verify before and after)

### Out of Scope

- Any schema changes — v1.1 schema is already shipped
- Sidebar navigation changes — existing water/equipment anchor links already work
- New pages or sections
- Any other version references beyond the Hero YAML block

---

## Notes

The schema file (`site/public/schema/v1.1.json`) was correctly published as part of the v1.1 feature commit. Only the human-readable site content needs updating.
