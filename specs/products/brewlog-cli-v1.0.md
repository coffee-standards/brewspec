# Product: BrewLog CLI v1.0

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-30
**Last Updated:** 2026-03-30

---

## Problem Statement

BrewSpec v1.0 introduces breaking field renames, new fields, and a constraint tightening. The BrewLog CLI currently targets v0.9 — it cannot import v1.0 documents, and its exports produce v0.9 documents that fail v1.0 schema validation.

Specifically:
- The CLI stores `water_weight_g` and `notes` in both its Pydantic models and SQLite schema. Both fields are removed from BrewSpec v1.0.
- Six new fields have no corresponding DB columns, Pydantic fields, CLI flags, or serialisation logic.
- `coffee.name` maxLength tightened from 150 to 100; the Pydantic validator still allows 150.
- `BREWSPEC_VERSION` in `serialise.py` is `"0.9"` — exports carry the wrong version string.

Until these changes land, BrewLog cannot serve as a reference implementation of v1.0, and any user who tries to import a v1.0 BrewSpec file will get a validation failure.

Target personas:
- **Home Brewer** — benefits from the new `--target-yield` flag when dialling in espresso, and from `--process-notes` being a distinct flag separated from sensory notes.
- **Coffee Professional** — needs `--cupping-notes` fields at coffee and origin level to log pre-brew evaluations, and `--pressure-bar` / `--flow-rate` for complete espresso records.
- **Tool Builder** — needs BrewLog's import/export to round-trip v1.0 documents correctly so it remains a valid reference implementation.

---

## User Stories

- As a **home brewer** dialling in espresso, I want to record my intended output weight with `--target-yield` on `add` so that I can compare my recipe target against the actual yield I log with `--yield-g`.
- As a **home brewer**, I want to record the actual water used with `--actual-water` when I deviate from my recipe so that my brew record reflects what I actually did.
- As a **home brewer**, I want `--process-notes` to be a distinct flag from `--tasting-notes` and `result_tasting_notes` so that my preparation observations and sensory impressions are never mixed in a single field.
- As a **coffee professional**, I want `--coffee-cupping-notes` on `add` and `update` so that I can log bag description or pre-brew cupping notes alongside the brew record.
- As a **coffee professional**, I want `--origin-cupping-notes` on `add` and `update` so that I can record per-component sensory notes for blends.
- As a **coffee professional** using an espresso machine, I want `--pressure-bar` and `--flow-rate` flags on `add` and `update` so that my BrewSpec record captures the full equipment setup.
- As a **home brewer**, I want my existing brew history to survive the upgrade intact, with renamed columns mapped correctly and new columns defaulting to NULL, so that I do not lose data when updating BrewLog.
- As a **tool builder**, I want `brewlog export` to produce valid v1.0 BrewSpec documents so that BrewLog remains a working reference implementation of the current spec.
- As a **tool builder**, I want `brewlog import` to accept v1.0 BrewSpec documents and reject v0.9 documents so that the CLI enforces the current spec version.

---

## Acceptance Criteria

### Version bump

- **AC-1**: `BREWSPEC_VERSION` in `serialise.py` is updated from `"0.9"` to `"1.0"`. Exported documents carry `brewspec_version: "1.0"`.
- **AC-2**: The bundled schema file used for import and export validation is the v1.0 schema (`brewspec.schema.json` at the repo root). The CLI must not ship or reference the v0.9 schema for validation.

### DB migration — renamed columns

- **AC-3**: On `get_connection()`, the migration logic renames the `water_weight_g` column to `water_g` in the SQLite `brews` table if it has not been renamed already. All existing row data is preserved.
- **AC-4**: On `get_connection()`, the migration logic renames the `notes` column to `process_notes` in the `brews` table if it has not been renamed already. All existing row data is preserved.
- **AC-5**: After migration, a database that previously contained `water_weight_g` and `notes` columns has no `water_weight_g` column and no `notes` column. PRAGMA table_info confirms the columns are `water_g` and `process_notes`.
- **AC-6**: Migration is idempotent — running `get_connection()` a second time on an already-migrated database produces no error and no change.

### DB migration — new columns

- **AC-7**: On `get_connection()`, the v1.0 migration adds the following new columns to the `brews` table if they do not already exist:
  - `yield_g REAL` (brew-level recipe target yield)
  - `result_water_g REAL` (actual water used, stored under the result prefix for consistency)
  - `coffee_cupping_notes TEXT`
  - `origin_cupping_notes TEXT` (stored at the brew level; applies to the first or only origin)
  - `equipment_pressure_bar REAL`
  - `equipment_flow_rate_ml_s REAL`
- **AC-8**: Each new column defaults to NULL for all existing rows. No existing data is modified.

### Pydantic model changes

- **AC-9**: `BrewInput.water_weight_g` is renamed to `BrewInput.water_g`. The field validator enforces `> 0`. All references in CLI commands and DB insert logic use `water_g`.
- **AC-10**: `BrewInput.notes` is renamed to `BrewInput.process_notes`. The field validator enforces `minLength: 1` and `maxLength: 2000` (consistent with the BrewSpec v1.0 schema constraint). All references in CLI commands and DB insert logic use `process_notes`.
- **AC-11**: `BrewInput.yield_g` is added: `Optional[float] = None`, validated `> 0`. This is the recipe-level target output weight, distinct from `ResultInput.yield_g` (actual output weight).
- **AC-12**: `ResultInput.water_g` is added: `Optional[float] = None`, validated `> 0`. This is the actual water used.
- **AC-13**: `CoffeeInput.cupping_notes` is added: `Optional[str] = None`, validated non-empty when present (`minLength: 1`) and `maxLength: 2000`.
- **AC-14**: `OriginInput.cupping_notes` is added: `Optional[str] = None`, validated non-empty when present (`minLength: 1`) and `maxLength: 2000`.
- **AC-15**: `EquipmentInput.pressure_bar` is added: `Optional[float] = None`, validated `> 0`.
- **AC-16**: `EquipmentInput.flow_rate_ml_s` is added: `Optional[float] = None`, validated `> 0`.
- **AC-17**: `CoffeeInput.validate_coffee_name` maxLength constraint is tightened from `150` to `100`. Supplying a `coffee_name` of 101 characters raises a `ValidationError`.
- **AC-18**: The docstring on `BrewInput` is updated to reference BrewSpec v1.0.

### `brewlog add` — CLI flags

- **AC-19**: The `--water` / `water_weight` flag on `brewlog add` is renamed. The flag is now `--water` with internal name `water_g` (the prompt text becomes "Water in grams"). The interactive prompt label changes from "Water weight in grams" to "Water in grams". Behaviour and validation are unchanged.
- **AC-20**: The `--notes` flag on `brewlog add` is renamed to `--process-notes` (internal name `process_notes`). The help text reads: "Operational preparation notes (e.g. 'rinsed filter, 30s bloom'). For sensory impressions use --tasting-notes."
- **AC-21**: `brewlog add` gains a `--target-yield` flag (`type=float`, internal name `target_yield`) for `brew.yield_g` (recipe target output weight). Help text: "Recipe target output weight in grams (> 0). For espresso dialling — the intended liquid yield. For actual output weight use --yield-g."
- **AC-22**: `brewlog add` gains an `--actual-water` flag (`type=float`, internal name `actual_water`) for `result.water_g`. Help text: "Actual water used in grams (> 0). Record when actual water deviates from the recipe target (--water)."
- **AC-23**: `brewlog add` gains a `--coffee-cupping-notes` flag (`type=str`, internal name `coffee_cupping_notes`) for `coffee.cupping_notes`. Help text: "Sensory notes on the coffee as a whole — bag description or pre-brew cupping impressions."
- **AC-24**: `brewlog add` gains an `--origin-cupping-notes` flag (`type=str`, internal name `origin_cupping_notes`). When `--origin-cupping-notes` is supplied alongside structured `--origin-*` flags, the cupping note is applied to the first origin entry. Help text: "Sensory notes for the origin component (or the single origin for single-origin coffees)."
- **AC-25**: `brewlog add` gains a `--pressure-bar` flag (`type=float`, internal name `pressure_bar`) for `equipment.pressure_bar`. Help text: "Line or lever pressure in bars (> 0). Primarily for espresso."
- **AC-26**: `brewlog add` gains a `--flow-rate` flag (`type=float`, internal name `flow_rate_ml_s`) for `equipment.flow_rate_ml_s`. Help text: "Volumetric flow rate in ml/s (> 0). Useful for espresso profiling."
- **AC-27**: Supplying `--target-yield 0` or a negative value produces an error message and exits with code 1. Same for `--actual-water`, `--pressure-bar`, and `--flow-rate`.
- **AC-28**: Supplying `--coffee-cupping-notes ""` or `--origin-cupping-notes ""` (empty string) produces an error and exits with code 1.

### `brewlog update` — CLI flags

- **AC-29**: The `--notes` flag on `brewlog update` is renamed to `--process-notes`. The `UPDATABLE_COLUMNS` allowlist in `db.py` is updated: `notes` is removed, `process_notes` is added.
- **AC-30**: `brewlog update` gains `--target-yield FLOAT`, `--actual-water FLOAT`, `--coffee-cupping-notes TEXT`, `--origin-cupping-notes TEXT`, `--pressure-bar FLOAT`, and `--flow-rate FLOAT` flags, matching the corresponding `add` flags. All are included in `UPDATABLE_COLUMNS`.
- **AC-31**: Validation on `update` flags follows the same rules as `add`: `target-yield`, `actual-water`, `pressure-bar`, and `flow-rate` must be `> 0`; `coffee-cupping-notes` and `origin-cupping-notes` must be non-empty strings.
- **AC-32**: The `water_weight_g` column reference in `UPDATABLE_COLUMNS` is removed; `water_g` is added. The required-fields note in AC-45 of the base spec is updated: `water_g` replaces `water_weight_g` as a non-updatable required field.

### `brewlog show` — display

- **AC-33**: `brewlog show [id]` displays `process_notes` (not `notes`) in the output when the field has a value.
- **AC-34**: `brewlog show [id]` displays the brew-level `yield_g` (recipe target yield) in the brew parameters section when present, labelled "Target yield (g)".
- **AC-35**: `brewlog show [id]` displays `result.water_g` (actual water used) in the results section when present, labelled "Actual water (g)".
- **AC-36**: `brewlog show [id]` displays `coffee.cupping_notes` in the coffee section when present.
- **AC-37**: `brewlog show [id]` displays `origin.cupping_notes` per-origin in the coffee section when present.
- **AC-38**: `brewlog show [id]` displays `equipment.pressure_bar` and `equipment.flow_rate_ml_s` in the equipment section when present.

### `brewlog list` — column display

- **AC-39**: `brewlog list` does not display `notes` — the column is renamed to `process_notes`. The column is not shown in the list table (it was never in the list table; this AC confirms no regression).

### Export serialisation

- **AC-40**: `row_to_brew_dict()` in `serialise.py` reads `water_g` (not `water_weight_g`) from the DB row and emits `water_g` in the output dict.
- **AC-41**: `row_to_brew_dict()` reads `process_notes` (not `notes`) from the DB row and emits `process_notes` in the output dict.
- **AC-42**: `row_to_brew_dict()` includes `yield_g` from the brew-level DB column in the output dict when present (distinct from `result.yield_g`).
- **AC-43**: `row_to_brew_dict()` includes `result_water_g` from the DB in the result sub-object as `water_g` when present.
- **AC-44**: `row_to_brew_dict()` includes `coffee_cupping_notes` in the coffee sub-object as `cupping_notes` when present.
- **AC-45**: `row_to_brew_dict()` includes `origin_cupping_notes` on the first origin object in `coffee.origins` as `cupping_notes` when present and when at least one origin is present.
- **AC-46**: `row_to_brew_dict()` includes `equipment_pressure_bar` and `equipment_flow_rate_ml_s` in the equipment sub-object as `pressure_bar` and `flow_rate_ml_s` respectively when present.
- **AC-47**: An export produced from a database containing all v1.0 fields passes validation against the v1.0 JSON Schema without errors.
- **AC-48**: An export produced from a database that only has the fields present in a pre-v1.0 brew (populated `water_g`, `dose_g`, `type`, `date`; all new columns NULL) also passes v1.0 schema validation.

### Import

- **AC-49**: `brewlog import [path]` validates the input file against the v1.0 BrewSpec JSON Schema. A v1.0 file containing `brew.water_g` passes. A file containing `brew.water_weight_g` fails validation and no rows are written.
- **AC-50**: `insert_brew_dict()` in `db.py` reads `water_g` (not `water_weight_g`) from the brew dict and writes it to the `water_g` DB column.
- **AC-51**: `insert_brew_dict()` reads `process_notes` (not `notes`) from the brew dict and writes it to the `process_notes` DB column.
- **AC-52**: `insert_brew_dict()` reads `yield_g` from the brew-level dict (recipe target) and writes it to the `yield_g` DB column (not `result_yield_g`).
- **AC-53**: `insert_brew_dict()` reads `result.water_g` from the result sub-object and writes it to `result_water_g` in the DB.
- **AC-54**: `insert_brew_dict()` reads `coffee.cupping_notes` and writes it to `coffee_cupping_notes` in the DB.
- **AC-55**: `insert_brew_dict()` reads `cupping_notes` from the first origin entry in `coffee.origins` and writes it to `origin_cupping_notes` in the DB.
- **AC-56**: `insert_brew_dict()` reads `equipment.pressure_bar` and `equipment.flow_rate_ml_s` and writes them to `equipment_pressure_bar` and `equipment_flow_rate_ml_s` in the DB.

### Import/export round-trip

- **AC-57**: A v1.0 BrewSpec document that uses all new fields can be imported, stored, exported, and the exported file passes v1.0 schema validation. All field values are preserved through the round-trip.

### Search command

- **AC-58**: `search_brews()` in `db.py` searches `process_notes` (not `notes`) when looking for text matches. The `notes` column reference in the LIKE query is replaced with `process_notes`.

### Test suite

- **AC-59**: All existing tests that reference `water_weight_g` are updated to use `water_g`.
- **AC-60**: All existing tests that reference `notes` as a brew-level field are updated to use `process_notes`.
- **AC-61**: New tests cover each new CLI flag on `add`: `--target-yield`, `--actual-water`, `--coffee-cupping-notes`, `--origin-cupping-notes`, `--pressure-bar`, `--flow-rate`. Each test verifies the value is written to the DB.
- **AC-62**: New tests cover each new CLI flag on `update` for the same six fields.
- **AC-63**: A migration test verifies that a pre-v1.0 database (with `water_weight_g` and `notes` columns) is correctly migrated: columns renamed, data preserved, new columns added as NULL.
- **AC-64**: A round-trip test imports a valid v1.0 BrewSpec file, then exports it, and asserts the exported document passes v1.0 schema validation.
- **AC-65**: Validation error tests confirm that `--target-yield 0`, `--actual-water -1`, `--pressure-bar 0`, `--flow-rate 0` each produce an error and exit code 1.
- **AC-66**: A validation error test confirms that `--coffee-name` of 101 characters produces an error and exit code 1 (maxLength tightened from 150 to 100).
- **AC-67**: The full test suite passes `ruff check .` with no errors.

---

## Scope

### In Scope

- `BREWSPEC_VERSION` bump to `"1.0"` in `serialise.py`
- Bundled schema updated to v1.0
- DB migration: rename `water_weight_g` → `water_g`, rename `notes` → `process_notes`
- DB migration: add `yield_g`, `result_water_g`, `coffee_cupping_notes`, `origin_cupping_notes`, `equipment_pressure_bar`, `equipment_flow_rate_ml_s` columns
- Pydantic model changes: rename `water_weight_g` and `notes` fields; add `BrewInput.yield_g`, `ResultInput.water_g`, `CoffeeInput.cupping_notes`, `OriginInput.cupping_notes`, `EquipmentInput.pressure_bar`, `EquipmentInput.flow_rate_ml_s`; tighten `CoffeeInput.name` maxLength to 100
- `brewlog add`: rename `--water` internal name, rename `--notes` to `--process-notes`, add six new flags
- `brewlog update`: rename `--notes` to `--process-notes`, add six new flags, update `UPDATABLE_COLUMNS`
- `brewlog show`: display renamed and new fields
- `serialise.py`: update `row_to_brew_dict()` and `insert_brew_dict()` for all renamed and new fields
- `search_brews()`: search `process_notes` instead of `notes`
- Test suite: update all renamed field references, add tests for new flags, migration, and round-trip

### Out of Scope

- **No new commands** — all changes are to existing `add`, `update`, `show`, `export`, and `import` commands. No new commands in this version.
- **No `brewlog list` column additions** — the list table does not display `process_notes`, `yield_g`, or other new fields. The table was already compact; new fields are accessible via `show`.
- **No v0.9 import compatibility shim** — v0.9 documents (which use `water_weight_g` and `brew.notes`) are rejected by the v1.0 schema. Users must migrate their files. No automatic field remapping on import.
- **No `origin_cupping_notes` per-origin on multi-origin updates** — when updating via `--origin-cupping-notes`, the note applies to the first origin only. Full per-origin structured update is deferred.
- **No changes to `brewlog stats`** — no new aggregations for v1.0 fields.
- **No changes to `brewlog search`** — search still matches against `process_notes`, `result_tasting_notes`, and coffee name fields. No search against `coffee_cupping_notes` or `origin_cupping_notes` in this version.
- **No `--water` interactive prompt rename** — the interactive prompt currently says "Water weight in grams"; this changes to "Water in grams" (AC-19) but no other prompt behaviour changes.
- **No CSV export** — deferred, as in prior versions.

---

## Design Notes

### DB migration strategy

SQLite does not support `ALTER TABLE ... RENAME COLUMN` in versions prior to 3.25.0 (released 2018). Python 3.11 ships with SQLite 3.39+ on all supported platforms, so `ALTER TABLE brews RENAME COLUMN water_weight_g TO water_g` is safe to use directly. The architect should confirm this is the approach rather than the rename-rebuild-copy pattern used for the NOT NULL migration in v0.7.

The v1.0 migration is a new named migration block (e.g., `_V10_MIGRATION_COLUMNS` for new columns, and a separate rename guard for the two column renames). The existing migration blocks (`_V3` through `_V8`) are unchanged.

Migration guard pattern: before renaming, check `PRAGMA table_info(brews)` to see if the old column name still exists. If it does, rename. If it does not (already migrated), skip. This makes migration idempotent.

### Column naming convention

The existing DB schema uses a flat prefix pattern for nested objects:
- `coffee_*` for fields under `coffee`
- `equipment_*` for fields under `equipment`
- `result_*` for fields under `result`

New columns follow the same pattern:
- `yield_g` — brew-level (no prefix, mirrors the BrewSpec field path `brew.yield_g`)
- `result_water_g` — mirrors `result.water_g`
- `coffee_cupping_notes` — mirrors `coffee.cupping_notes`
- `origin_cupping_notes` — a single column storing the cupping note for the first/primary origin; mirrors the common single-origin use case
- `equipment_pressure_bar` — mirrors `equipment.pressure_bar`
- `equipment_flow_rate_ml_s` — mirrors `equipment.flow_rate_ml_s`

### `origin_cupping_notes` storage

`origin.cupping_notes` is an array-level field in the BrewSpec schema (it lives on each object in `coffee.origins[]`). The CLI stores origins as a JSON-encoded array in `coffee_origins`. Two options for storing cupping notes:

1. Embed `cupping_notes` inside the JSON `coffee_origins` array — no new column, but requires parsing the JSON to extract the field for `show` and search.
2. Single `origin_cupping_notes TEXT` column — stores the cupping note for the first/only origin; simpler for the common single-origin case, but loses per-origin notes for blends.

**Recommendation: option 1** — embed `cupping_notes` within the `coffee_origins` JSON. This handles blends correctly, is consistent with how all other per-origin fields are stored, and does not require a new column. The `add` command already has per-origin structured flags (`--origin-name`, `--origin-country`, etc.) — `--origin-cupping-notes` follows the same positional-parallel pattern. The architect should confirm this approach.

If option 1 is chosen, AC-7 must be updated to remove `origin_cupping_notes TEXT` from the new-column list, and AC-45 and AC-55 must be updated to read/write from within the JSON array rather than a separate column.

### `brew.yield_g` vs `result.yield_g` naming in the DB

The existing DB has `result_yield_g` for the result-level actual output weight. The new brew-level recipe target uses `yield_g` (no prefix). This is intentional: the brew-level field maps directly to `brew.yield_g` in BrewSpec. The result-level field maps to `result.yield_g`. The naming asymmetry in the DB (`yield_g` vs `result_yield_g`) is unavoidable given the flat-prefix schema convention.

The `show` command must label these clearly: `yield_g` as "Target yield (g)" and `result_yield_g` as "Actual yield (g)" to avoid confusion.

### BrewSpec v1.0 data structure reference

```yaml
brewspec_version: "1.0"
brews:
  - date: "2026-03-30"
    type: "espresso"
    dose_g: 18.0
    water_g: 36.0            # renamed from water_weight_g
    yield_g: 36.0            # NEW: recipe target output weight
    process_notes: "Pre-infused 5s at 3 bar"  # renamed from notes
    coffee:
      name: "Colombia Huila"  # maxLength now 100 (was 150)
      cupping_notes: "Dark chocolate, citrus"  # NEW
      origins:
        - name: "Huila Washed"
          cupping_notes: "Bright malic acidity"  # NEW
    equipment:
      grinder: "Niche Zero"
      pressure_bar: 9.0      # NEW
      flow_rate_ml_s: 1.3    # NEW
    result:
      water_g: 35.5          # NEW: actual water used
      yield_g: 36.5          # unchanged
      tds: 9.1
```

---

## Security Requirements

- **Data sensitivity**: Brew logs contain personal preference and habit data. All new fields are freeform text or numeric recipe parameters — no PII is added. The existing security posture is unchanged.
- **Input validation**: All new numeric fields (`brew.yield_g`, `result.water_g`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s`) must be validated `> 0` at the Pydantic layer before any DB write. Invalid values produce a clear error and exit code 1 without writing.
- **Input validation**: All new text fields (`process_notes`, `coffee.cupping_notes`, `origin.cupping_notes`) must be validated non-empty when provided (`minLength: 1`) and bounded at `maxLength: 2000`, consistent with the BrewSpec v1.0 schema. Validation happens in Pydantic, not only at the DB layer.
- **SQL injection**: The DB column renames are performed with static DDL strings (`ALTER TABLE brews RENAME COLUMN water_weight_g TO water_g`). No user input flows into migration DDL. All new columns are added with static `ALTER TABLE ... ADD COLUMN` statements. Parameterised `?` placeholders are used for all row-level reads and writes — this is an existing requirement that must be maintained across all new DB columns.
- **File I/O**: Import validation now validates against the v1.0 schema. A v0.9 file (`water_weight_g`, `brew.notes`) is rejected before any parse output reaches the DB. The 10MB file size limit and `..` path rejection remain in force unchanged.
- **YAML parsing**: `yaml.safe_load()` is the only permitted YAML parser. No change required — this is an existing constraint. All new test fixtures must use safe-loadable YAML.
- **Migration safety**: The rename migration must run inside a transaction. If the rename fails partway (e.g., disk full), the DB must not be left in a partially migrated state. The architect must confirm the transaction boundary covers both renames and all new column additions.
- **No secrets in code or tests**: No API keys, tokens, or credentials in source or test fixtures.

---

## Dependencies

- **Upstream — blocks this task**:
  - `brewspec-v1.0` (done) — the v1.0 JSON Schema and the field changes it defines are the source of truth for all changes in this task.
  - `brewlog-cli-v0.8` (done) — this task builds on the v0.8 CLI codebase.

- **Downstream — blocked by this task**:
  - `brewspec-site-v1.0` (backlog) — the site update references BrewLog CLI v1.0 as the working reference implementation.

- **Runtime dependencies** (unchanged):
  - `click` — CLI framework
  - `pyyaml` — YAML parsing (`safe_load` only)
  - `pydantic` — input validation
  - `jsonschema` — BrewSpec v1.0 schema validation for import and export

---

## Success Metrics

- `brewlog export` produces a document that passes `jsonschema.validate()` against `brewspec.schema.json` (v1.0) without errors.
- `brewlog import` accepts a valid v1.0 BrewSpec file and rejects a v0.9 file with a clear validation error.
- A database created under v0.8 is migrated without data loss: existing rows have `water_g` and `process_notes` populated from the renamed columns, and all new columns are NULL.
- All new flags (`--target-yield`, `--actual-water`, `--coffee-cupping-notes`, `--origin-cupping-notes`, `--pressure-bar`, `--flow-rate`) write correct values to the DB and appear in `brewlog show` output.
- Full test suite passes with zero failures and `ruff check .` is clean.

---

## Open Questions

None. All field names, types, constraints, CLI flag names, and DB column names are fully specified in the manifest task description and the BrewSpec v1.0 spec (`specs/products/brewspec-v1.0.md`). The one design question worth architect confirmation is the `origin_cupping_notes` storage approach (embed in `coffee_origins` JSON vs. separate column — see Design Notes above).
