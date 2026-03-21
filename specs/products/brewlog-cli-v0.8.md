# Product: BrewLog CLI v0.8

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-03-21
**Last Updated:** 2026-03-21

---

## Problem Statement

BrewLog CLI v0.7 is compliant with BrewSpec v0.8. BrewSpec v0.9 introduces two changes that align the rating system with the SCA Coffee Value Assessment (CVA) standard (SCA-104, adopted 2024). Both changes require BrewLog CLI to update in lockstep:

1. **Rating range 1-5 is inconsistent with the CVA 9-point hedonic scale.** The current CLI enforces `1 <= rating <= 5` on all eight rating dimensions. BrewSpec v0.9 changes the schema to a 1-9 range. Users who record ratings using the CVA methodology are currently forced to truncate or rescale their assessments. The CLI must accept and validate the full 1-9 range.

2. **The `body` field name is incorrect CVA terminology.** BrewSpec v0.4 introduced `ratings.body` as a sensory dimension. The CVA standard uses the term `mouthfeel`, not `body`. BrewSpec v0.9 renames this field. The CLI must rename the corresponding DB column (`rating_body` → `rating_mouthfeel`), the Pydantic model field, the CLI flags, and all display output. This is a breaking change requiring a DB migration.

**Important note on existing data:** The rename from `body` to `mouthfeel` in the CLI is more accurately a correction to `body` having already been renamed in a prior release. Examining the current codebase (v0.7), the DB column is already `result_rating_mouthfeel`, the Pydantic field is already `mouthfeel`, the CLI flag is already `--rating-mouthfeel`, and the display label is already `Mouthfeel`. The rename in BrewSpec v0.9 is aligning the schema JSON to match what BrewLog CLI already uses internally. As a result, the column rename migration is not required for existing BrewLog databases — only the Pydantic validator range (1-5 → 1-9), the CLI flag help text, and the list filter validation need to change. The bundled schema must be updated to v0.9.

Target personas:
- **Home brewer** — ratings are the most personal and frequently used result fields. Expanding to 1-9 gives finer resolution to capture nuanced sensory differences between brews.
- **Coffee professional** — CVA alignment is a hard requirement for professionals using the SCA assessment framework. The 9-point hedonic scale is the industry standard for structured cupping.
- **Tool builder** — the CLI must remain a compliant reference implementation of the current BrewSpec version.

---

## User Stories

- As a **home brewer**, I want to log a rating of 7 out of 9 so that my rating reflects real nuance beyond the old 1-5 scale.
- As a **coffee professional**, I want all rating dimensions to accept 1-9 values so that I can record CVA-compliant assessments directly in BrewLog without rescaling.
- As a **home brewer**, I want the `--rating-min` and `--rating-max` filters on `brewlog list` to accept 1-9 values so that I can filter my brew history using the new scale.
- As a **home brewer**, I want the `brewlog stats` rating distribution to display all nine rating levels (1-9) so that I can see my full history at a glance.
- As a **tool builder**, I want BrewLog CLI to export files with `brewspec_version: "0.9"` so that downstream tooling receives valid BrewSpec v0.9 documents.
- As a **tool builder**, I want BrewLog CLI to import BrewSpec v0.9 files with ratings in the 1-9 range so that data round-trips are lossless.

---

## Acceptance Criteria

### Rating Range: 1-9

- **AC-1**: The `RatingsInput` Pydantic model validates all eight rating dimensions (`overall`, `fragrance`, `aroma`, `flavour`, `aftertaste`, `acidity`, `sweetness`, `mouthfeel`) as integers in the range 1-9 inclusive. Values of 0 or 10 are rejected with an error message stating "rating dimension must be between 1 and 9 inclusive".
- **AC-2**: `brewlog add` accepts `--rating-overall`, `--rating-fragrance`, `--rating-aroma`, `--rating-flavour`, `--rating-aftertaste`, `--rating-acidity`, `--rating-sweetness`, and `--rating-mouthfeel` flags with values 1-9. Supplying a value outside this range exits with code 1 and an error message: `"Error: --rating-{dim} must be an integer between 1 and 9."`.
- **AC-3**: `brewlog update` accepts the same eight `--rating-*` flags with values 1-9. Supplying a value outside this range exits with code 1 and an error message: `"Error: --rating-{dim} must be an integer between 1 and 9."`.
- **AC-4**: The `--rating-min` and `--rating-max` options on `brewlog list` accept values 1-9. Supplying a value outside 1-9 exits with code 1 and an error: `"Error: --rating-min must be an integer between 1 and 9."` / `"Error: --rating-max must be an integer between 1 and 9."`.
- **AC-5**: `brewlog list --rating-min 7` returns only brews with `result_rating_overall >= 7`. `brewlog list --rating-max 3` returns only brews with `result_rating_overall <= 3`. The existing `--rating-min <= --rating-max` ordering check is retained.
- **AC-6**: The `brewlog show` command displays rating values in the range 1-9 correctly. No display change is required beyond accepting that the stored integer may now be up to 9.
- **AC-7**: The `brewlog stats` rating distribution covers all nine values (1 through 9). The `get_brew_stats` DB function returns a `rating_distribution` dict with keys 1-9 (replacing the current 1-5 dict). Each key maps to the count of brews with that `result_rating_overall` value. Values with zero brews are shown with count 0.
- **AC-8**: The `brewlog stats` display renders the distribution for all nine values. Example format:
  ```
  Distribution:
    1:  0
    2:  1
    3:  3
    4:  8
    5: 12
    6:  9
    7:  4
    8:  2
    9:  1
  ```
  The label format changes from `"N star(s):"` to `"N:"` to accommodate the wider scale cleanly.
- **AC-9**: The help text for `--rating-overall`, `--rating-fragrance`, `--rating-aroma`, `--rating-flavour`, `--rating-aftertaste`, `--rating-acidity`, `--rating-sweetness`, and `--rating-mouthfeel` in both `add` and `update` reads `"[Dimension] rating, 1-9."`.

### DB Column: mouthfeel (no migration required)

- **AC-10**: The `result_rating_mouthfeel` column already exists in the DB schema from v0.3. No column rename or data migration is required. This AC is a confirmation, not a change: the DB layer requires no modification for the `mouthfeel` rename because the BrewLog CLI already uses `mouthfeel` internally.
- **AC-11**: The `UPDATABLE_COLUMNS` allowlist in `db.py` retains `result_rating_mouthfeel` unchanged. No update is needed.

### Bundled Schema: BrewSpec v0.9

- **AC-12**: The bundled JSON Schema file (used by `brewlog import` for validation) is updated to the BrewSpec v0.9 schema.
- **AC-13**: The `BREWSPEC_VERSION` constant in `serialise.py` is updated from `"0.8"` to `"0.9"`.
- **AC-14**: `brewlog export` produces documents with `brewspec_version: "0.9"` at the top level.
- **AC-15**: `brewlog import` accepts BrewSpec v0.9 documents (with `brewspec_version: "0.9"` and ratings in the 1-9 range) and stores them correctly. Documents declaring `brewspec_version: "0.8"` or earlier that are otherwise valid also continue to import without error (the validator uses the bundled v0.9 schema which accepts all valid structures).

### Serialise / Deserialise

- **AC-16**: `row_to_brew_dict` in `serialise.py` continues to read `result_rating_mouthfeel` from the DB row and map it to the `mouthfeel` key in the exported ratings dict. No change is needed here; this is a confirmation AC.
- **AC-17**: `insert_brew_dict` in `db.py` reads `ratings.get("mouthfeel")` from the imported document and stores it in `result_rating_mouthfeel`. No change is needed here; this is a confirmation AC.

### Pydantic Model Docstring

- **AC-18**: The `RatingsInput` class docstring is updated from `"All fields optional integers 1-5."` to `"All fields optional integers 1-9 (SCA CVA hedonic scale)."`.

### No Regression

- **AC-19**: All existing tests continue to pass after the changes. The only test updates required are: test inputs using ratings of 5 or below remain valid; tests that assert the old 1-5 validation error message are updated to expect 1-9; tests for `stats` distribution are updated to cover 1-9.
- **AC-20**: `ruff check .` passes with zero errors before handoff to reviewer.

---

## Scope

### In Scope

- `RatingsInput` Pydantic model: change validator range from `1 <= v <= 5` to `1 <= v <= 9`; update docstring
- `add` command: update rating flag help text and inline range check from `1 <= v <= 5` to `1 <= v <= 9`
- `update` command: update rating flag help text and inline range check from `1 <= v <= 5` to `1 <= v <= 9`
- `list` command: update `--rating-min` / `--rating-max` validation from range 1-5 to 1-9; update help text
- `stats` command and `get_brew_stats` DB function: extend distribution dict from keys 1-5 to keys 1-9; update display labels from `"N star(s):"` to `"N:"`
- `serialise.py`: update `BREWSPEC_VERSION` from `"0.8"` to `"0.9"`
- Bundled schema: replace the bundled BrewSpec v0.8 JSON Schema with v0.9
- `BrewInput` docstring: bump version reference from v0.8 to v0.9
- Test suite: update all tests that assert 1-5 range errors or stats distribution to use 1-9

### Out of Scope

- Any new CLI commands or flags not related to the rating range or schema version bump
- DB column rename (already correct — `result_rating_mouthfeel` is in place)
- UI changes to `show` beyond accepting stored values up to 9
- Migration of existing stored ratings (1-5 values remain valid under 1-9; no data transform needed)
- `brewlog search` — no changes required for this version
- Any BrewSpec v0.9 schema changes beyond the two described (rating range 1-9; `ratings.body` → `ratings.mouthfeel`). The `mouthfeel` rename is already implemented in BrewLog CLI.

---

## Design Notes

### Why no DB migration for mouthfeel

The `ratings.body` → `ratings.mouthfeel` rename in BrewSpec v0.9 appears as a breaking change at the schema level, but the BrewLog CLI already adopted `mouthfeel` as the internal name when implementing the rating dimensions in v0.3. The DB column is `result_rating_mouthfeel`, the Pydantic model field is `mouthfeel`, the CLI flags are `--rating-mouthfeel`, and the show/list display reads `Mouthfeel`. No data migration or column rename is needed. The v0.9 schema adoption closes the naming gap at the spec level.

### Rating scale change: existing data compatibility

Existing brews with stored ratings of 1-5 remain valid and correct under the 1-9 validator. SQLite stores integers; a stored value of 4 is still 4. No data migration, coercion, or translation is needed. The scale change is additive — it widens the accepted range.

### Stats distribution display labels

The current `stats` command uses `"1 star:"` / `"N stars:"` labels, implying a star-rating metaphor that does not fit a 9-point CVA scale. The new display should use numeric-only labels (`"1:"`, `"2:"`, ..., `"9:"`) to avoid implying a star-count interpretation. This is a cosmetic change consistent with the CVA framing.

### Bundled schema dependency

This task depends on BrewSpec v0.9 being available (the schema JSON file). The task is being developed in parallel with `brewspec-v0.9`. The dev agent must ensure the v0.9 schema file is available before writing the import test. If the v0.9 schema is not yet merged to the worktree branch, the dev agent should note this as a blocker.

### Data Requirements

- DB schema: no changes. All columns exist.
- `UPDATABLE_COLUMNS` in `db.py`: no changes needed.
- `_V3_MIGRATION_COLUMNS` through `_V8_MIGRATION_COLUMNS`: no new migration constants needed for this version. A `_V9_MIGRATION_COLUMNS` dict is not required.
- `get_brew_stats`: return dict key `rating_distribution` changes shape from `{1: int, ..., 5: int}` to `{1: int, ..., 9: int}`.

---

## Security Requirements

- **Data sensitivity**: Rating values are user-entered integers. No PII. Brew logs are local-only personal data stored in `~/.brewlog/brews.db`.
- **Input validation**: All rating dimension inputs must be validated as integers in range 1-9 before DB write. This validation occurs at two layers: the Pydantic `RatingsInput` model (for `add` and import paths) and the inline flag checks in `add.py` and `update.py` (for the CLI path). Both layers must enforce the 1-9 constraint.
- **SQL injection**: No change to SQL layer. All existing queries use parameterised `?` placeholders. No new queries are introduced by this task.
- **File I/O**: No change to import/export path validation. The existing `validate_import_path` and `validate_export_path` functions are unaffected.
- **Schema version on import**: The import command validates imported files against the bundled schema. Updating the bundled schema to v0.9 means files with ratings > 5 will now pass schema validation. This is the intended behaviour.

---

## Dependencies

- **Depends on**: `brewspec-v0.9` — this task requires the v0.9 JSON Schema file to update the bundled schema and to run import tests against v0.9 documents. Being developed in parallel.
- **Depends on**: `brewlog-cli-v0.7` — previous CLI version; this task builds on that codebase (done).
- **Downstream**: BrewSpec Site — may want to note v0.9 adoption in landing page copy; tracked separately if needed.

---

## Success Metrics

- `ruff check .` passes with zero errors
- `pytest tests/` passes with zero failures
- `brewlog add --rating-overall 9` succeeds and stores 9 in the DB
- `brewlog add --rating-overall 10` exits with code 1 and the correct error message
- `brewlog export` produces a document with `brewspec_version: "0.9"`
- `brewlog stats` distribution shows keys 1 through 9

---

## Open Questions

None. Scope has been approved by the user.
