# Product: BrewLog CLI v0.5

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-02-26
**Last Updated:** 2026-03-07

---

## Problem Statement

BrewLog CLI v0.4 delivered a solid core: add, list, show, update, delete, export (YAML, JSON, CSV), and import with full BrewSpec v0.4 compliance. Users can log brews reliably and get their data back out in multiple formats. v0.5 addresses the next wave of friction that surfaces once a user has been logging for weeks and their database starts to grow.

**Five problems this version solves:**

1. **There is no way to get an overview of your brewing history.** Once a user has 30, 50, or 100 brews logged, `brewlog list` shows rows but tells them nothing about trends or summary statistics. Users have no answer to "how many brews have I logged?" or "what's my average rating?" without exporting to CSV and opening a spreadsheet. A single `brewlog stats` command covering counts, averages, and distribution solves this without adding analytical complexity.

2. **Finding a specific brew in a growing list is slow.** `brewlog list --since DATE` and `--type TYPE` help narrow by metadata, but if a user remembers a brew by its coffee name, a tasting note, or a word in their notes, they have no way to find it without scanning the full list. A `brewlog search` command over coffee name, notes, and tasting notes addresses this directly.

3. **Re-importing an export file creates duplicate brews.** The current import command inserts every brew in the file regardless of whether it already exists in the database. A user who exports their data, makes a backup, and then re-imports it doubles their history. Import deduplication (match on date + coffee name + method) prevents this without requiring complex identity management.

4. **There is no way to export a single brew.** `brewlog export` dumps the entire database. A user who wants to share one brew — as a recipe, as a cupping result, or as a BrewSpec file to send to a roaster — must export everything and manually extract the single record. `brewlog export --id N` fills this gap cleanly.

5. **Users cannot manage multiple brew databases.** The database path is hardcoded to `~/.brewlog/brews.db`. A user with two espresso machines, or separate home and work setups, has no way to maintain distinct brew logs without hacking around the fixed path. A `--db PATH` global flag enables multiple databases with zero infrastructure complexity.

**Additionally (schema adoption):**

BrewSpec v0.6 is the target schema for this version. It introduced four breaking changes from v0.5: `water_volume_ml` removed from the brew object; `coffee.process` removed from the top-level coffee object (now only valid in `coffee.origins[].process`); `coffee.varietal` removed from the top-level coffee object (now only valid in `coffee.origins[].varietal`); and `equipment.grinder_setting` type changed from string to number. It also adds two new optional fields: `coffee.name` (branded product name) and `coffee.origins[].varietal` (varietal per origin component). The CLI must adopt these changes for full v0.6 compliance. The interactive brew type update (deferred from prior versions) is also in scope for v0.5.

**No carry-forward items from v0.4 review.** The v0.4 reviewer report (`reviews/2026-02-26-reviewer-brewlog-cli-v0.4.yaml`) returned PASS with `carry_forward: []`. No blocking or non-blocking items were deferred.

Target personas:
- **Home brewer** — stats and search are the features that make the tool more useful as the brew history grows. Brew ratio display removes a common mental calculation. Import deduplication prevents data corruption on routine backup workflows.
- **Coffee professional** — structured origin on add/update/show/export, grinder setting tracking, and equipment notes support the level of detail they need for professional record-keeping.
- **Tool builder** — single-brew export produces minimal valid BrewSpec v0.6 files, useful for testing. Custom DB path enables isolated test environments. Full v0.6 compliance maintains the CLI as a reference implementation.

---

## User Stories

- As a **home brewer**, I want to run `brewlog stats` and see a summary of my brewing history so that I can understand my patterns without exporting to a spreadsheet.
- As a **home brewer**, I want to search `brewlog search "ethiopia"` and find all brews where Ethiopia appears in the coffee name, notes, or tasting notes so that I can quickly locate a brew I remember by flavour or coffee name.
- As a **home brewer**, I want import to skip brews already in my database so that re-importing a backup file doesn't create duplicates.
- As a **home brewer**, I want to run `brewlog export --id N` to get a single brew as a BrewSpec file so that I can share a recipe without exporting my entire history.
- As a **home brewer**, I want to pass `--db ~/work-brews.db` to use a different database file so that I can maintain separate brew logs for different setups.
- As a **coffee professional**, I want to record the country, region, producer, process, lot, and harvest year for the coffee origin when I log a brew so that my records carry the same detail as a specialty bag label.
- As a **coffee professional**, I want to record my grinder's setting (`--grinder-setting "21 clicks"`) alongside the model so that my brews are reproducible.
- As a **home brewer**, I want `brewlog show` and `brewlog list` to display the brew ratio so that I can see the recipe at a glance without calculating it from dose and water.
- As a **home brewer**, I want `brewlog update --type` to show the same numbered menu I see on `brewlog add` so that interactive type selection is consistent across commands.

---

## Acceptance Criteria

### `brewlog stats` — Brew History Summary

- **AC-1**: `brewlog stats` is a new top-level command. Running it with no arguments prints a summary of all brews in the database. Exit code is 0 on success.
- **AC-2**: The `stats` output includes:
  - Total brews logged (count of all rows in the `brews` table)
  - Most common brew type (the `type` value appearing most frequently; ties broken by alphabetical order of the type name; if no brews exist, display `None`)
  - Average overall rating (mean of all non-null `result_rating_overall` values, rounded to one decimal place; if no brews have an overall rating, display `No ratings logged`)
  - Rating distribution: for each integer value 1–5, the count of brews with `result_rating_overall` equal to that value. Ratings with zero brews are still shown (count: 0).
- **AC-3**: The stats output format is plain text, grouped into labelled sections. Example:
  ```
  Brew Summary
  ============
  Total brews:       47
  Most common type:  pour_over

  Ratings
  -------
  Average overall:   3.8
  Distribution:
    1 star:  2
    2 stars: 5
    3 stars: 12
    4 stars: 20
    5 stars: 8
  ```
  The exact column widths may vary; the above represents the required content and grouping, not pixel-perfect alignment.
- **AC-4**: When the database is empty, `brewlog stats` prints a friendly message (e.g., `No brews logged yet. Run 'brewlog add' to log your first brew.`) and exits with code 0.
- **AC-5**: `brewlog stats` works correctly with the `--db PATH` global flag (see AC-31).

### `brewlog search` — Free-Text Search

- **AC-6**: `brewlog search QUERY` is a new top-level command. It accepts a single positional argument, QUERY, which is a search string. The command searches across four fields: `coffee_name`, `notes`, `result_tasting_notes`, and `coffee_origins` (the JSON-encoded origin array). A brew matches if QUERY appears as a case-insensitive substring in any of these fields.
- **AC-7**: The search is performed as parameterised SQL `LIKE` queries across `coffee_name`, `notes`, `result_tasting_notes`, `coffee_origins`, and the legacy `coffee_origin` column. The search does not require the query to match all fields; a match in any one field is sufficient. All matching brews are returned.
- **AC-8**: `brewlog search QUERY` outputs matching brews in the same tabular format as `brewlog list` — same columns, same column-hiding rules (only columns with at least one non-null value shown).
- **AC-9**: The search is case-insensitive. `brewlog search "Ethiopia"` and `brewlog search "ethiopia"` return the same results.
- **AC-10**: If no brews match the query, a friendly message is printed (e.g., `No brews found matching "ethiopia".`) and the command exits with code 0.
- **AC-11**: An empty query string produces a clear error message and exits with code 1. Running `brewlog search ""` is an error.
- **AC-12**: `brewlog search QUERY` supports `--limit N` to cap the number of results returned. Default behaviour (no `--limit`) returns all matches.
- **AC-13**: The search is implemented using parameterised SQL `LIKE` queries (e.g., `notes LIKE ?` with the parameter `%query%`). The QUERY value is never interpolated directly into a SQL string.
- **AC-14**: `brewlog search` works correctly with the `--db PATH` global flag (see AC-31).

### Import Deduplication

- **AC-15**: When `brewlog import [path]` processes a brew from the import file, it checks whether a brew with the same `date`, `type`, `dose_g`, and `water_weight_g` already exists in the database. If a matching row is found, that brew is skipped (not inserted). The match checks all four fields simultaneously (logical AND).
- **AC-16**: At the end of a successful import, the command prints a summary indicating how many brews were inserted and how many were skipped as duplicates. Example: `Import complete: 8 brews added, 3 skipped (already exist).`
- **AC-17**: If all brews in the import file are duplicates, the command prints the summary (0 added, N skipped) and exits with code 0. No error is raised.
- **AC-18**: If no brews in the import file are duplicates, the behaviour is identical to the previous import behaviour (all brews inserted). The summary line is still printed.
- **AC-19**: Deduplication is applied after schema validation. If the file fails schema validation, the command exits with code 1 before any deduplication check occurs.
- **AC-20**: `brewlog import` works correctly with the `--db PATH` global flag (see AC-31).

### Single-Brew Export: `brewlog export --id N`

- **AC-21**: `brewlog export [path] --id N` exports a single brew with the given integer ID as a BrewSpec v0.6 file. The file contains a `brews` array with exactly one entry. The format defaults to YAML (`.yaml`). The `--format csv` and `--format json` flags continue to work with `--id`.
- **AC-22**: If the brew ID does not exist, the command prints a clear error message (e.g., `No brew found with ID N.`) to stderr and exits with code 1. No file is written.
- **AC-23**: The single-brew export file passes v0.6 schema validation. All existing export serialisation rules apply (field mapping, `result` object, `coffee.origins` structure, etc.).
- **AC-24**: The existing `brewlog export [path]` with no `--id` flag continues to export all brews. No change to existing behaviour.
- **AC-25**: The existing path validation rules (extension validation, `..` rejection, overwrite protection, `--force` flag) apply equally to `--id` exports.
- **AC-26**: `brewlog export` with `--id` works correctly with the `--db PATH` global flag (see AC-31).

### Custom Database Path: `--db PATH`

- **AC-27**: A new `--db PATH` option is added to the top-level `brewlog` group (the CLI root), making it available as a global flag for all subcommands. PATH is a filesystem path to a SQLite database file.
- **AC-28**: When `--db PATH` is supplied, the CLI uses that file as its database instead of the default `~/.brewlog/brews.db`. If the file does not exist, it is created (same behaviour as the default path on first run).
- **AC-29**: When `--db PATH` is not supplied, the CLI behaves exactly as before, using `~/.brewlog/brews.db`. No change to existing default behaviour.
- **AC-30**: `--db PATH` is validated before any command executes. If the parent directory of PATH does not exist, a clear error message is printed to stderr and the command exits with code 1 without touching the database.
- **AC-31**: `--db PATH` works with all commands: `add`, `list`, `show`, `update`, `delete`, `export`, `import`, `stats`, and `search`.
- **AC-32**: PATH containing `..` components is rejected with a clear error message and exit code 1, consistent with existing path traversal protections for export/import paths.
- **AC-33**: The `--db PATH` flag is documented in the top-level `brewlog --help` output.

### BrewSpec v0.6 Schema Adoption

- **AC-34**: The CLI targets BrewSpec v0.6. All exports write `brewspec_version: "0.6"`. The JSON Schema file used for export validation and import validation is the v0.6 schema.
- **AC-35**: `brewlog import [path]` rejects files declaring any version other than `"0.6"` with a clear, actionable error message that states the version found, lists the structural changes required to migrate to v0.6, and exits with code 1. No rows are written.
- **AC-36**: The import rejection message for unsupported versions includes at minimum:
  - The version found in the file (e.g., `This file uses BrewSpec v0.5, which is not supported by this version of BrewLog.`)
  - For v0.5 files: the five migration steps required to upgrade to v0.6:
    1. Change `brewspec_version` from `"0.5"` to `"0.6"`
    2. Remove `water_volume_ml` from all brew entries (field removed in v0.6)
    3. Move `coffee.process` into each `coffee.origins[].process` entry and remove the top-level field
    4. Move `coffee.varietal` into each `coffee.origins[].varietal` entry and remove the top-level field
    5. Change `equipment.grinder_setting` from a string to a number (e.g., `"21"` → `21`)
  - For v0.4 files: additionally rename `coffee.origin` (string array) to `coffee.origins` (array of objects with `country` populated)
  - A reference to the migration guide at `https://github.com/coffee-standards/brewspec`

### `brew_ratio` Display and Storage

- **AC-37**: `brewlog add` supports a new `--brew-ratio FLOAT` flag (optional). When supplied, the value is validated as a number greater than zero. A value of 0 or negative produces a clear error and exits with code 1 without writing to the database.
- **AC-38**: `brewlog update` supports the same `--brew-ratio FLOAT` flag with the same validation.
- **AC-39**: A new `brew_ratio` column (`REAL`, optional) is added to the `brews` table via automatic migration on first run of any command that opens the database. The migration adds the column without modifying existing rows or columns.
- **AC-40**: `brewlog show [id]` displays `Brew Ratio` in the brew parameters section when the value is non-null. Format: `Brew Ratio: 15.6` (one decimal place). If both `brew_ratio` and the values needed to compute it (`dose_g`, `water_weight_g`) are present, the stored value is displayed — no recomputation.
- **AC-41**: `brewlog list` does not add a `Brew Ratio` column. Ratio is a per-brew detail suited to `show`, not a list overview column.
- **AC-42**: `brewlog export` serialises `brew_ratio` into the exported BrewSpec v0.6 file at the brew level when the value is non-null. `brewlog import` reads `brew_ratio` from imported v0.6 files into the `brew_ratio` column.
- **AC-43**: The column allowlist in `update_brew()` is updated to include `brew_ratio`.

### BrewSpec v0.5 Origin Fields: `coffee.origins`

- **AC-44**: The database schema is updated to store structured origin data. The existing `coffee_origin` column (TEXT, JSON-encoded array of strings) is replaced by a new `coffee_origins` column (TEXT, JSON-encoded array of origin objects). Migration: on first run, add `coffee_origins` column and, for each existing row with a non-null `coffee_origin` value, migrate the string array to a JSON array of objects with `country` populated (e.g., `["Ethiopia"]` becomes `[{"country": "Ethiopia"}]`). The old `coffee_origin` column is retained for backward compatibility but is no longer written to on new rows.
- **AC-45**: `brewlog add` supports the following new flags for origin data. All are optional and may be supplied multiple times to represent a blend (see AC-46):
  - `--origin-name TEXT` — label for this origin entry
  - `--origin-country TEXT` — country of origin
  - `--origin-region TEXT` — region within the country
  - `--origin-subregion TEXT` — sub-area within the region
  - `--origin-producer TEXT` — farm, cooperative, or washing station
  - `--origin-process TEXT` — green coffee processing method
  - `--origin-varietal TEXT` — coffee varietal for this origin component (new in v0.6; replaces top-level `coffee.varietal`)
  - `--origin-lot TEXT` — lot or batch identifier
  - `--origin-year INT` — harvest year (integer)
- **AC-46**: When multiple sets of origin flags are supplied (for blends), each flag group corresponds to one entry in `coffee.origins`. The implementation strategy for multiple entries (e.g., repeatable flag groups vs. JSON string input) is left to the architect. The spec requires that at least single-origin logging is fully functional via flags; blend logging via flags is in scope but the UX is architect-determined.
- **AC-47**: `brewlog update` supports the same origin flags as `brewlog add`. Supplying origin flags on `update` replaces the entire `coffee_origins` value for that brew (not a partial update of individual fields within an existing origin entry).
- **AC-48**: `brewlog show [id]` displays origin data in the Coffee section when `coffee_origins` is non-null. For a single origin, display each populated field on its own labelled line. For multiple origins (blend), display each origin as a numbered block.

  Single-origin display example:
  ```
  Coffee
  ------
  Roast Date:     2026-01-20
  Type:           single_origin
  Origin:
    Country:      Ethiopia
    Region:       Yirgacheffe
    Producer:     Daye Bensa
    Varietal:     Heirloom
    Process:      Washed
    Harvest Year: 2025
  ```

  Blend display example:
  ```
  Coffee
  ------
  Type:           blend
  Origin 1:
    Name:         Ethiopia Yirgacheffe
    Country:      Ethiopia
  Origin 2:
    Name:         Colombia Huila
    Country:      Colombia
  ```
  Only populated fields within each origin block are shown.

- **AC-49**: `brewlog export` serialises `coffee_origins` into the `coffee.origins` array in the exported v0.6 file. For rows with a legacy `coffee_origin` value (old string array) and no `coffee_origins` value, the exporter migrates the string array to `[{ "country": "..." }]` for each entry in the exported file. The exported file passes v0.6 schema validation. The exporter does NOT include `coffee.process` or `coffee.varietal` at the top level (removed in v0.6); these values are serialised within `coffee.origins[].process` and `coffee.origins[].varietal` respectively if present in the origin data.
- **AC-50**: `brewlog import` reads `coffee.origins` from v0.6 files into the `coffee_origins` column as a JSON-encoded array of objects. The `coffee_origin` column is not written on import of v0.6 files.

### `coffee.name` Field (new in v0.6)

- **AC-50a**: A new `coffee_name` column (TEXT, optional) is added to the `brews` table via automatic migration on first run.
- **AC-50b**: `brewlog add` supports a `--coffee-name TEXT` flag (optional). Validated as a non-empty string; an empty string produces a clear error and exits with code 1.
- **AC-50c**: `brewlog update` supports the same `--coffee-name TEXT` flag with the same validation.
- **AC-50d**: `brewlog show [id]` displays `Name` as the first field in the Coffee section when `coffee_name` is non-null. Example: `Name: Ethiopia Yirgacheffe`.
- **AC-50e**: `brewlog export` serialises `coffee_name` as `coffee.name` in the exported v0.6 file when non-null. `brewlog import` reads `coffee.name` from v0.6 files into the `coffee_name` column.
- **AC-50f**: The column allowlist in `update_brew()` is updated to include `coffee_name`.
- **AC-50g**: `brewlog search` includes `coffee_name` as one of the searched columns (already reflected in AC-6/AC-7).

### Equipment Fields: `grinder_setting` and `notes`

- **AC-51**: A new `equipment_grinder_setting` column (REAL, optional) is added to the `brews` table via automatic migration. The type is REAL (number), not TEXT — `grinder_setting` was a string in v0.5 schema but is a number in v0.6. A migration note should handle any legacy TEXT rows by coercing to REAL on read (or treating nulls from legacy rows gracefully).
- **AC-52**: A new `equipment_notes` column (TEXT, optional) is added to the `brews` table via automatic migration.
- **AC-53**: `brewlog add` supports `--grinder-setting FLOAT` and `--equipment-notes TEXT` flags (optional). `--grinder-setting` is validated as a number greater than zero; zero or negative values produce a clear error and exit code 1. `--equipment-notes` is validated as a non-empty string; an empty string produces a clear error and exits with code 1.
- **AC-54**: `brewlog update` supports the same `--grinder-setting FLOAT` and `--equipment-notes TEXT` flags with the same validation.
- **AC-55**: `brewlog show [id]` displays `Grinder Setting` and `Equipment Notes` in the Equipment section when those values are non-null.

  Example:
  ```
  Equipment
  ---------
  Grinder:         Comandante C40
  Grinder Setting: 21 clicks
  Brewer:          Hario V60 02
  Notes:           Burrs 3 months old
  ```
- **AC-56**: `brewlog export` serialises `equipment_grinder_setting` as `equipment.grinder_setting` (a number) and `equipment_notes` as `equipment.notes` in exported v0.6 files when non-null. `brewlog import` reads these fields from v0.6 files into the corresponding columns.
- **AC-57**: The column allowlist in `update_brew()` is updated to include `equipment_grinder_setting` and `equipment_notes`.

### Interactive Brew Type on `brewlog update`

- **AC-58**: When `brewlog update` is run with `--type` as a flag but no value (i.e., the flag is present but empty), the CLI presents the same numbered menu as `brewlog add`:
  ```
  Select brew type:
    1. espresso
    2. hybrid
    3. immersion
    4. pour_over
  Choice [1-4]:
  ```
  The menu values and ordering (alphabetical) are identical to the `add` menu. Invalid selection re-prompts. Ctrl+C cancels without modifying the brew.
- **AC-59**: When `brewlog update` is run with `--type VALUE` (a value is supplied), the type is accepted as-is and validated against the enum. No interactive menu is shown. This preserves the existing non-interactive flag behaviour.
- **AC-60**: When `brewlog update` is run with no `--type` flag, no type update is attempted. Existing behaviour unchanged.

### Version Bump

- **AC-61**: `pyproject.toml` version is bumped to `0.5.0`.
- **AC-62**: `src/brewlog/__init__.py` `__version__` is updated to `"0.5.0"`.
- **AC-63**: The welcome screen (bare `brewlog` invocation) displays `BrewLog v0.5.0`.

---

## Scope

### In Scope

**New commands:**
- `brewlog stats` — summary counts, most common type, average rating, rating distribution (AC-1 through AC-5)
- `brewlog search QUERY` — case-insensitive substring search over notes, tasting notes, and origin fields; tabular output; `--limit N` flag (AC-6 through AC-14)

**Import deduplication:**
- Skip brews already in database on import (match: date + type + dose_g + water_weight_g); import summary line (AC-15 through AC-20)

**Single-brew export:**
- `brewlog export [path] --id N` exports one brew as a BrewSpec v0.6 file; existing export path and all formats unchanged (AC-21 through AC-26)

**Custom database path:**
- `--db PATH` global flag on `brewlog` group; works with all commands; path validation (AC-27 through AC-33)

**BrewSpec v0.6 schema adoption:**
- CLI targets v0.6 schema; exports write `brewspec_version: "0.6"`; import rejects unsupported versions with actionable migration message (AC-34 through AC-36)

**`brew_ratio` field:**
- `--brew-ratio FLOAT` on add and update; `brew_ratio` column; displayed in show; serialised in export/import (AC-37 through AC-43)

**Structured origin (`coffee.origins`):**
- `coffee_origins` column replacing `coffee_origin`; origin flags on add and update (including new `--origin-varietal`); display in show; serialise in export/import; legacy migration (AC-44 through AC-50)

**`coffee.name` field (new in v0.6):**
- `coffee_name` column; `--coffee-name TEXT` on add and update; display as first field in Coffee section of show; serialise in export/import; added to search and column allowlist (AC-50a through AC-50g)

**Equipment fields:**
- `--grinder-setting FLOAT` (number, not string) and `--equipment-notes TEXT` on add and update; display in show; serialise in export/import; column allowlist updates (AC-51 through AC-57)

**Interactive brew type on update:**
- Numbered menu when `--type` flag supplied without value (AC-58 through AC-60)

**Version bump:**
- `pyproject.toml` and `__init__.py` to `0.5.0`; welcome screen updated (AC-61 through AC-63)

### Out of Scope

- **Fuzzy search** — `brewlog search` uses exact case-insensitive substring matching (SQL `LIKE`). Fuzzy/approximate matching (e.g., Levenshtein distance, trigram) is not included. It adds a dependency and implementation complexity that is not warranted until usage patterns show it is needed.
- **`brewlog stats` per-type breakdown** — the stats command shows overall counts and ratings only. Per-type average ratings, per-type brew counts, and time-series data are deferred. Stats v1 is intentionally minimal.
- **`brewlog search` by metadata fields** — search is limited to `notes`, `result_tasting_notes`, and origin fields. Searching by date range, rating, or type is already covered by `brewlog list` filters and is not duplicated in `search`.
- **Import deduplication configurability** — the deduplication key (date + type + dose_g + water_weight_g) is fixed. No flag to change the match key or to force-insert duplicates. If a user genuinely needs to import a true duplicate brew (same date, type, and quantities but a distinct event), they must add it manually via `brewlog add`.
- **Single-brew export to stdout** — `brewlog export --id N [path]` requires a path. No stdout mode.
- **`brewlog export --since / --until` date-range filtering** — partial export by date range remains deferred.
- **Origin blend percentage/weight split** — `coffee.origins` entries do not include proportion fields. The CLI has no `--origin-percent` or `--origin-weight` flag.
- **Interactive origin prompts** — origin fields are flag-only on both `add` and `update`. They are not added to the interactive prompt flow (which covers only the four required fields: date, type, dose, water).
- **`coffee_process` / `coffee_varietal` column removal** — these top-level columns are legacy data from CLI v0.4 (when `coffee.process` and `coffee.varietal` existed at the top level of the coffee object). Both fields were removed from the BrewSpec schema at the top level in v0.6; process and varietal now live exclusively in `coffee.origins[].process` and `coffee.origins[].varietal`. The legacy DB columns (`coffee_process`, `coffee_varietal`) are retained but not written to on new rows and not serialised in v0.6 exports. The architect should define migration behaviour for any legacy rows that have these top-level values.
- **`brewlog stats` date-range filter** — `brewlog stats` always covers the full database. No `--since / --until` filtering on stats in v0.5.
- **`brewlog update` for required fields** — date, type, dose_g, and water_weight_g remain non-updatable. Delete and re-add to correct a required field.
- **Water chemistry beyond `ppm`** — deferred from prior versions.
- **Pour schedule / step-by-step timing** — deferred from prior versions.

---

## Design Notes

### `brewlog stats` — Query Design

The stats command requires three distinct queries:

1. `SELECT COUNT(*) FROM brews` — total brews
2. `SELECT type, COUNT(*) as cnt FROM brews GROUP BY type ORDER BY cnt DESC, type ASC LIMIT 1` — most common type (ties broken alphabetically)
3. `SELECT AVG(result_rating_overall) FROM brews WHERE result_rating_overall IS NOT NULL` — average rating; format result to one decimal place
4. `SELECT result_rating_overall, COUNT(*) FROM brews WHERE result_rating_overall IS NOT NULL GROUP BY result_rating_overall ORDER BY result_rating_overall` — rating distribution (post-process to fill in zero counts for missing values)

All queries are read-only and parameterless. No user input is involved. `--db PATH` is the only variable; the database connection path is the only parameter.

### `brewlog search` — SQL Implementation

```sql
SELECT * FROM brews
WHERE (
    coffee_name LIKE ?
    OR notes LIKE ?
    OR result_tasting_notes LIKE ?
    OR coffee_origins LIKE ?
    OR coffee_origin LIKE ?
)
ORDER BY id DESC
LIMIT ?
```

The QUERY parameter is wrapped as `%query%` for each placeholder. The `LIMIT` clause uses the `--limit N` value when supplied, or is omitted (or set to a very large value) when no limit is specified. Both `coffee_origins` and `coffee_origin` are searched to cover existing rows using the legacy column.

The search does not use FTS5 or any SQLite extension. Plain `LIKE` is sufficient for the expected data volume (hundreds to low thousands of rows) and avoids adding a dependency or requiring a schema rebuild.

### Import Deduplication — Match Key Choice

The deduplication key (date + type + dose_g + water_weight_g) was chosen because:
- These four fields uniquely identify a brew event with high confidence: same date, same brew method, same dose, same water weight is almost certainly the same brew.
- All four are required fields — always present, never null — making the match deterministic.
- More specific keys (adding `notes` or `method`) would risk false negatives when a user slightly edits a brew's notes before re-importing.
- Looser keys (date only, or date + type) would risk false positives for users who brew the same type multiple times per day.

The match uses exact equality on all four fields. Floating-point equality for `dose_g` and `water_weight_g` is exact (SQLite stores the value as-is; re-imported values from a BrewSpec file parsed from the same source should be bit-for-bit identical).

### Origin Data Storage

The `coffee_origins` column stores a JSON-encoded array of origin objects:

```json
[
  {
    "country": "Ethiopia",
    "region": "Yirgacheffe",
    "producer": "Daye Bensa",
    "varietal": "Heirloom",
    "process": "Washed",
    "harvest_year": 2025
  }
]
```

For single-origin brews, the array has one element. For blends, multiple elements. On export, this column is decoded and serialised into the `coffee.origins` YAML structure. On import, the `coffee.origins` array is JSON-encoded and stored in this column.

The legacy `coffee_origin` column (string array, e.g., `["Ethiopia"]`) is retained for backward compatibility with rows created by CLI v0.3/v0.4. The migration on first run of v0.5 converts existing `coffee_origin` rows to `coffee_origins` format. After migration, both columns exist; new rows write only to `coffee_origins`.

### `--db PATH` Implementation

The `--db PATH` option should be added to the Click group object for the top-level `brewlog` command. Click passes context-level options to subcommands via `ctx.obj` or `ctx.params`. The database path should be resolved once (from the global flag or the default) and passed into each command's database initialisation.

The architect should confirm how Click context propagation works in the existing codebase and ensure the path is resolved before any command executes its database open operation.

Path validation rules for `--db PATH`:
- `..` components are rejected (consistent with export/import path rules)
- Parent directory must exist (the file itself need not exist — it is created on first use)
- No extension restriction — `.db`, `.sqlite`, or no extension are all acceptable

### Origin Flags on `add` and `update` — Architect Decision Point

Recording a blend via CLI flags is non-trivial. The simplest approach for single-origin:

```bash
brewlog add --type pour_over --dose 18 --water 280 \
  --origin-country Ethiopia --origin-region Yirgacheffe --origin-producer "Daye Bensa"
```

For blends, the natural flag approach breaks down — `--origin-country` cannot be supplied twice with distinct intent. Options:
- Accept `--origins-json '...'` for blends as a JSON string argument (power user escape hatch)
- Accept multiple `--origin-*` flag sets using Click's `multiple=True` behaviour (pairs flags positionally — fragile)
- For v0.5, document that blend logging requires the JSON escape hatch or manual DB editing; single-origin via flags is the primary UX

The architect should select the approach and document it in the design. The spec requires single-origin flag logging to work cleanly; blend logging via flags is best-effort.

### Database Schema — Full Column List After v0.5/v0.6 Migration

```
id                        INTEGER PRIMARY KEY AUTOINCREMENT
date                      TEXT NOT NULL
type                      TEXT NOT NULL
method                    TEXT
dose_g                    REAL NOT NULL
water_weight_g            REAL NOT NULL
brew_ratio                REAL                   -- NEW in v0.5, optional, > 0
water_volume_ml           REAL                   -- LEGACY: removed from BrewSpec v0.6; retained for existing rows, not written on new rows
water_temp_c              REAL
grind                     TEXT
duration_s                INTEGER
tds                       REAL
ey                        REAL
rating                    INTEGER                -- legacy, maps to result_rating_overall on export
notes                     TEXT
coffee_name               TEXT                   -- NEW in v0.6, optional
coffee_roast_date         TEXT
coffee_type               TEXT
coffee_origin             TEXT                   -- legacy JSON string array; still read for existing rows
coffee_origins            TEXT                   -- NEW in v0.5, JSON array of origin objects (including varietal and process per origin in v0.6)
coffee_varietal           TEXT                   -- LEGACY: top-level varietal removed in BrewSpec v0.6; retained for existing rows, not written on new rows
coffee_process            TEXT                   -- LEGACY: top-level process removed in BrewSpec v0.6; retained for existing rows, not written on new rows
water_ppm                 REAL
equipment_grinder         TEXT
equipment_brewer          TEXT
equipment_grinder_setting REAL                   -- NEW in v0.5 (was TEXT); v0.6 schema requires number; migrate legacy TEXT values on read
equipment_notes           TEXT                   -- NEW in v0.5
result_brix               REAL
result_tasting_notes      TEXT
result_rating_overall     INTEGER
result_rating_fragrance   INTEGER
result_rating_aroma       INTEGER
result_rating_flavour     INTEGER
result_rating_aftertaste  INTEGER
result_rating_acidity     INTEGER
result_rating_sweetness   INTEGER
result_rating_mouthfeel   INTEGER
```

**Migration note:** When CLI v0.5 runs against an existing database, the automatic migration adds: `brew_ratio`, `coffee_name`, `coffee_origins`, `equipment_grinder_setting` (REAL), `equipment_notes`. Legacy columns `water_volume_ml`, `coffee_varietal`, `coffee_process`, and `coffee_origin` are retained as-is — no destructive migration. The architect should determine whether legacy `coffee_varietal` and `coffee_process` values should be migrated into `coffee_origins` entries during the first-run migration or left as-is.

### `brewlog show` — Updated Output Structure (v0.6)

```
Brew #14
---------
Date:              2026-02-26
Type:              pour_over
Method:            Hario V60
Dose (g):          18.0
Water (g):         280.0
Brew Ratio:        15.6
Water Temp (C):    96.0
Grind:             medium_fine
Duration (s):      180
Notes:             Washed filter paper

Results
-------
TDS (%):           1.38
EY (%):            20.1
Brix:              1.5
Tasting Notes:     Bright citrus, caramel finish
Ratings:
  Overall:         4
  Fragrance:       3
  Aroma:           4
  Flavour:         5
  Aftertaste:      4
  Acidity:         5
  Sweetness:       3
  Mouthfeel:       4

Coffee
------
Name:              Ethiopia Yirgacheffe Natural
Roast Date:        2026-01-20
Type:              single_origin
Origin:
  Country:         Ethiopia
  Region:          Yirgacheffe
  Producer:        Daye Bensa
  Varietal:        Heirloom
  Process:         Washed
  Harvest Year:    2025

Water
-----
PPM:               150

Equipment
---------
Grinder:           Comandante C40
Grinder Setting:   21
Brewer:            Hario V60 02
Notes:             Burrs 3 months old
```

Notes: `Name` is shown when `coffee_name` is non-null. `Varietal` and `Process` are shown within the origin block, not at the top coffee level. `Grinder Setting` is a number (not a string like "21 clicks").

Sections with no populated fields for a given brew are omitted.

### Column Allowlist Update for `update_brew()`

The `UPDATABLE_COLUMNS` frozenset must be expanded to include the v0.5 additions:

```python
UPDATABLE_COLUMNS = frozenset({
    # ... existing columns ...
    "brew_ratio",
    "coffee_name",
    "coffee_origins",
    "equipment_grinder_setting",
    "equipment_notes",
})
```

---

## Security Requirements

**Data sensitivity:**
- `coffee.origins` fields (country, region, producer, lot, etc.) contain coffee provenance information. No PII risk. The origin object may incidentally contain personal context if a user enters notes like "bought from my friend's farm" — treated as low-sensitivity personal data, local-only.
- `equipment_notes` may contain maintenance records. Low sensitivity. Local-only.
- `equipment_grinder_setting` is a numeric or short text value. No sensitivity.
- `brew_ratio` is a numeric measurement. No sensitivity.
- No network transmission. All operations remain local and offline.

**Input validation:**
- `--brew-ratio FLOAT`: validated as a number greater than zero. Zero and negative values rejected before any database write.
- `--grinder-setting TEXT` and `--equipment-notes TEXT`: validated as non-empty strings (`minLength: 1`). Empty strings rejected.
- `--origin-*` flags: all string fields validated as non-empty when supplied. `--origin-year INT` validated as an integer. No calendar range check required (consistent with schema approach for `harvest_year`).
- `--db PATH`: validated for `..` components and parent directory existence before any database operation. Path is not interpolated into any SQL statement.
- `brewlog search QUERY`: QUERY is validated as non-empty. The QUERY value is passed as a SQL parameter (`?` placeholder with `%query%` wrapping), never interpolated into the query string.
- All existing field validations carry forward unchanged.

**SQL injection:**
- `brewlog search` uses parameterised LIKE queries. The user-supplied QUERY string is never concatenated into the SQL statement.
- `--db PATH` is a file path used to open a SQLite connection. It is not part of any SQL statement.
- The column allowlist in `update_brew()` (including new v0.5 additions) remains the defence-in-depth for the dynamic UPDATE statement.
- All new database reads (stats, search) use parameterised queries or no parameters (stats uses no user-supplied values).

**File I/O:**
- `--db PATH` path validation: `..` rejection and parent directory existence check, consistent with export/import path rules.
- `brewlog export --id N` uses the same path validation as full export. No new file-write surface.
- YAML parsing: `yaml.safe_load()` requirement is unchanged for import.
- Import schema validation (against v0.5 schema) occurs before any deduplication check or database write. Malformed files are rejected before any DB access.

**No secrets in code:**
- No API keys, credentials, tokens, or secrets of any kind in source code or test fixtures.
- The `--db PATH` default (`~/.brewlog/brews.db`) and the BrewSpec repo URL are not sensitive and may appear in documentation and code.

---

## Dependencies

**Upstream:**
- `brewspec-v0.6` (done) — CLI v0.5 targets the v0.6 schema. The v0.6 JSON Schema file is required for import and export validation. `brew_ratio`, `equipment.grinder_setting`, `equipment.notes`, and `coffee.origins` were v0.5 additions; `coffee.name` and `coffee.origins[].varietal` are v0.6 additions. BrewSpec v0.6 is done and shipped.
- `brewlog-cli-v0.4` (done) — v0.5 is a direct iteration. Existing database schema, command structure, validation patterns, and test suite are the baseline.

**Downstream:**
- `commercial-brew-tracking-app` (backlog) — relies on BrewSpec-compliant export. v0.5 exports will be the expected format when the commercial app's import path is built. Structured origin data and brew ratio in v0.5 exports enrich the data available to analytics.

**Runtime Dependencies (unchanged):**
- `click` — CLI framework
- `pyyaml` — YAML parsing and serialisation (`safe_load` only)
- `pydantic` — input validation models
- `jsonschema` — BrewSpec schema validation for import and export

---

## Success Metrics

Tied to `specs/strategy.md` Phase 1 success metrics:

- **`brewlog stats` correctness**: Running `brewlog stats` on a database with known brews returns the correct total count, correct most-common type, and correct average rating (within floating-point rounding to one decimal place).
- **`brewlog search` correctness**: `brewlog search "ethiopia"` returns all brews where "ethiopia" (case-insensitive) appears in notes, tasting notes, or origin fields. Returns zero results when no match exists (not an error).
- **Import deduplication**: Re-importing a previously imported file results in 0 new rows added and N skipped. The database row count does not change.
- **Single-brew export**: `brewlog export /tmp/brew14.yaml --id 14` produces a valid BrewSpec v0.6 file containing exactly one brew with the correct field values.
- **Custom DB path**: `brewlog --db /tmp/test.db add --type pour_over --dose 18 --water 280 --date 2026-02-26` creates `/tmp/test.db`, adds one brew, and `brewlog --db /tmp/test.db list` shows that brew.
- **Schema currency**: `brewlog export` produces files that pass validation against the v0.6 JSON Schema. `brewlog import` correctly rejects v0.5 and v0.4 files with actionable migration messages.
- **Origin round-trip**: A brew logged with `--origin-country Ethiopia --origin-region Yirgacheffe`, exported, and re-imported retains all origin field values.
- **Brew ratio display**: A brew with `--brew-ratio 15.5` logged shows `Brew Ratio: 15.5` in `brewlog show`.
- **Interactive type on update**: Running `brewlog update --type` (no value) shows the numbered menu; selecting `4` updates the type to `pour_over`.
- **Test suite**: 100% pass rate required before reviewer sign-off. All new ACs must have corresponding tests written first (TDD). The full test suite (including v0.4 regression tests) must pass without modification.
- **Security baseline**: Column allowlist updated with all v0.5/v0.6 additions (including `coffee_name`). Search uses parameterised queries only. Import validated against v0.6 schema before any DB write or deduplication check.
- **Grinder setting as number**: `brewlog add --grinder-setting 21` stores `21.0` (REAL); `brewlog show` displays `Grinder Setting: 21.0`; exported YAML writes `grinder_setting: 21.0`. A string value like `"21 clicks"` is rejected with a clear error.
- **coffee.name round-trip**: A brew logged with `--coffee-name "Ethiopia Yirgacheffe"`, exported, and re-imported retains the name value. `brewlog search "yirgacheffe"` finds the brew via the `coffee_name` column.

---

## Open Questions

- [x] **`brewlog search` fuzzy matching** — resolved: no fuzzy matching in v0.5. Exact case-insensitive substring match (SQL LIKE) only.
- [x] **Stats scope** — resolved: overall counts and overall rating only. No per-type breakdown in v0.5.
- [x] **Import deduplication key** — resolved: date + type + dose_g + water_weight_g. Four required fields, exact match.
- [x] **`brew_ratio` in list** — resolved: not shown in list. Ratio is a per-brew detail for `show` only.
- [ ] **Origin blend logging UX** — how should `brewlog add` support blend origins via CLI flags? Single-origin flag approach is clear (see Design Notes). Blend requires an architect decision on the input method. Document chosen approach in the design doc.
- [ ] **`coffee_origin` migration timing** — the migration of legacy `coffee_origin` rows to `coffee_origins` format runs on first run after v0.5 upgrade. Should the migration run once at startup (checking for unmigrated rows) or lazily on read? The architect should confirm the migration strategy and ensure it is safe to run on databases with hundreds of rows.
- [ ] **`coffee_varietal` / `coffee_process` legacy migration** — rows created by CLI v0.4 may have top-level `coffee_varietal` and `coffee_process` columns populated. In v0.6 these fields are not valid at the top level. Should the migration fold these values into `coffee_origins[0].varietal` and `coffee_origins[0].process` on the first run (risky for blends), or leave them in place and only exclude them from v0.6 exports? The architect should define and document the chosen approach.
