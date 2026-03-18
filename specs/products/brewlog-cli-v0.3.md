# Product: BrewLog CLI v0.3

**Status:** Ready
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-02-22
**Last Updated:** 2026-02-22

---

## Problem Statement

BrewLog CLI v0.2 shipped a complete core feature set: add, list, show, update, delete, export, import, and list filtering. But v0.2 still targets the BrewSpec v0.3 schema, and real-world use has exposed two categories of remaining friction that v0.3 addresses.

**Schema currency — the CLI is a version behind:**
BrewSpec v0.4 shipped with breaking structural changes: the `date` field now accepts `YYYY-MM-DD` (date-only), `tds` and `ey` moved from flat brew-level fields into a new `result` object, flat `rating` was replaced by a `result.ratings` object with 8 SCA-aligned dimensions, `grind` became a strict 7-value enum, and three new `result` fields were added (`brix`, `tasting_notes`, and the `ratings` dimensions). Until the CLI adopts v0.4, exports will fail v0.4 validation, imports of v0.4 files will be rejected, and the CLI is a broken reference implementation.

**Date field UX — the most common piece of friction:**
The single most-reported friction point is the date prompt in `brewlog add`. Entering `2026-02-22T09:15:00Z` when you just want to log today's brew is onerous. The schema change in v0.4 permits date-only input. The CLI must adopt it.

**Carry-forward items from v0.2 review:**
Two non-blocking recommendations were deferred from v0.2: a column allowlist assertion in `update_brew()` as structural defence-in-depth, and `--rating-min` / `--rating-max` range filters on `list` to complement the exact-match `--rating` filter.

Target personas:
- **Primary — The Home Brewer**: benefits most from date-only input and from a simpler, faster `add` experience. The v0.4 result fields (especially overall rating) remain accessible without forcing SCA-level evaluation on casual use.
- **Secondary — The Coffee Professional**: gains full SCA-aligned `ratings` dimensions on both `add` and `update`, plus dedicated `tasting_notes` and `brix` fields that match their evaluation workflow.
- **Tertiary — The Tool Builder**: the CLI is a reference implementation of BrewSpec. It must target the current schema version. v0.4 adoption restores that status.

---

## User Stories

- As a **home brewer**, I want to enter just the date (`2026-02-22`) when logging a brew so that I don't have to remember or invent an exact time and timezone.
- As a **home brewer**, I want to choose a grind size from the standard vocabulary (`medium`, `medium_fine`, etc.) so that my grind descriptions are consistent across brews.
- As a **home brewer**, I want to give my brew an overall rating in a single flag (`--rating-overall 4`) when logging so that I can capture a quick impression without filling in all 8 SCA dimensions.
- As a **coffee professional**, I want to record all 8 SCA rating dimensions (`fragrance`, `aroma`, `flavour`, `aftertaste`, `acidity`, `sweetness`, `mouthfeel`, `overall`) on a brew so that my evaluations align with the cupping protocol.
- As a **coffee professional**, I want a dedicated `--tasting-notes` field separate from `--notes` so that my sensory impressions and my operational brew notes don't get mixed together.
- As a **coffee professional**, I want to record `brix` alongside TDS and extraction yield so that I have a complete extraction picture in one log entry.
- As a **home brewer**, I want to filter `brewlog list` by a rating range (`--rating-min 3 --rating-max 5`) so that I can find my best brews without running multiple exact-match queries.
- As a **home brewer**, I want `brewlog list --until DATE` so that I can filter by a date range, not just a start date.
- As a **coffee professional**, I want exports to produce valid BrewSpec v0.4 files so that they are interoperable with any v0.4-compliant tool.
- As a **tool builder**, I want importing a BrewSpec v0.3 file to fail with a clear, actionable error so that I know exactly what to change to bring the file up to v0.4.

---

## Acceptance Criteria

### Carry-Forward Fixes

- **AC-1**: The `update_brew()` function in the database layer maintains a static allowlist of updatable column names. Before constructing the UPDATE statement, it asserts that every column name in the supplied update dict is a member of this allowlist. If any column name is not in the allowlist, the function raises an internal error and does not execute any SQL. This assertion makes the structural safety property explicit and catches future regressions at the call site rather than at the database layer.

- **AC-2**: `brewlog list --rating-min N` filters the output to brews where the `rating` value (stored as `result.ratings.overall`) is greater than or equal to `N`. `N` must be an integer between 1 and 5 inclusive. An invalid value produces a clear error message and exits with code 1.

- **AC-3**: `brewlog list --rating-max N` filters the output to brews where the `rating` value (stored as `result.ratings.overall`) is less than or equal to `N`. `N` must be an integer between 1 and 5 inclusive. An invalid value produces a clear error message and exits with code 1.

- **AC-4**: `--rating-min` and `--rating-max` may be supplied together to form a range. When both are present, the filter returns brews where the overall rating is `>= rating-min` AND `<= rating-max`. If `--rating-min` exceeds `--rating-max`, the command prints a clear error message and exits with code 1.

- **AC-5**: `--rating-min` and `--rating-max` are combinable with all existing `brewlog list` filters (`--type`, `--since`, `--until`, `--limit`, `--all`). They interact with `--limit` and `--all` in the same way as existing filters: the limit applies to the filtered result set. When combined with `--rating N` (exact match), all four must hold simultaneously. If no brews match the combined filters, the command prints a friendly message and exits with code 0.

### Date Format UX

- **AC-6**: When `brewlog add` is run in interactive mode (no `--date` flag supplied), the date prompt default is today's date in `YYYY-MM-DD` format (e.g., `Date [2026-02-22]:`). The user may press Enter to accept the default or type a date. The default is computed at prompt time from the local system clock.

- **AC-7**: The date prompt on `brewlog add` accepts both of the following formats as valid input:
  - Date-only: `YYYY-MM-DD` (e.g., `2026-02-22`)
  - Full ISO 8601 UTC datetime: `YYYY-MM-DDTHH:MM:SSZ` (e.g., `2026-02-22T09:15:00Z`)
  If the user enters any other format (e.g., `22-02-2026`, `2026-02-22T09:00:00` without Z), the prompt repeats with a clear error message explaining the accepted formats. The command does not exit; it re-prompts until a valid value is entered or the user cancels with Ctrl+C.

- **AC-8**: The `--date` flag on `brewlog add` and `brewlog update` accepts both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`. An invalid format produces a clear error message and exits with code 1. Note: `brewlog update` does not currently support `--date` (required fields are not updatable); this AC covers the `add` flag path only.

- **AC-9**: The date value is stored in the database exactly as the user supplied it — either as `YYYY-MM-DD` or as `YYYY-MM-DDTHH:MM:SSZ`. No normalisation to datetime is performed. This preserves the user's intent and matches the dual-format BrewSpec v0.4 schema.

- **AC-10**: `brewlog list` and `brewlog show` display the date exactly as stored (no normalisation). The `--since DATE` and `--until DATE` filters on `brewlog list` perform their comparisons correctly against both stored date formats. Specifically, a stored date-only value (`2026-02-22`) is treated as on that calendar day; a stored datetime value (`2026-02-22T09:15:00Z`) is also treated as on that calendar day for filter purposes. The comparison is made at day granularity regardless of the stored format.

### BrewSpec v0.4 Schema Adoption

- **AC-11**: The CLI targets BrewSpec v0.4. All exports write `brewspec_version: "0.4"`. The JSON Schema file used for export validation and import validation is the v0.4 schema (not v0.3).

- **AC-12**: `brewlog export [path]` serialises brew records to the v0.4 structure. Specifically:
  - `tds`, `ey`, `brix`, `tasting_notes`, and `ratings` are serialised under a `result` object, not at the flat brew level.
  - `rating` (integer 1–5 stored pre-v0.3 as a flat column) is serialised as `result.ratings.overall`.
  - The `result` object is omitted entirely from the exported brew record if none of its fields have a value for that brew.
  - The exported file passes validation against the v0.4 JSON Schema.

- **AC-13**: `brewlog import [path]` validates the input file against the v0.4 JSON Schema before inserting any rows. If the file declares `brewspec_version: "0.3"` or any version other than `"0.4"`, the import is rejected with a clear error message that:
  - States the version found in the file (e.g., `This file uses BrewSpec v0.3, which is not supported by this version of BrewLog.`)
  - Lists exactly which structural changes are required to migrate to v0.4 (flat `tds`/`ey` move to `result.tds`/`result.ey`; flat `rating` moves to `result.ratings.overall`; freeform `grind` values must be replaced with an enum value)
  - Points to the BrewSpec v0.4 migration guide at `https://github.com/coffee-standards/brewspec` for full instructions
  - Exits with code 1. No rows are written to the database.

- **AC-14**: `brewlog import [path]` correctly reads v0.4 files and maps `result.tds`, `result.ey`, `result.brix`, `result.tasting_notes`, and `result.ratings.*` fields into the corresponding database columns. On success, all imported brews are visible via `brewlog list` and `brewlog show` with their result fields populated.

- **AC-15**: The v0.4 JSON Schema used by the CLI for import validation and export validation is the canonical schema file from the BrewSpec repository (not a hand-written copy). The schema path used in code is configurable via a constant, not hardcoded into multiple call sites.

### `grind` Field — Enum Validation

- **AC-16**: The `--grind TEXT` flag on `brewlog add` is changed to validate against the v0.4 `grind` enum. Accepted values are: `turkish`, `espresso`, `fine`, `medium_fine`, `medium`, `medium_coarse`, `coarse`. Any other value (including previously valid freeform strings like `"setting 15"` or `"medium-fine"` with a hyphen) produces a clear error message listing the accepted values and exits with code 1. No brew is written.

- **AC-17**: The `--grind TEXT` flag on `brewlog update` is changed to validate against the same v0.4 `grind` enum with the same accepted values and error behaviour. No database write occurs on an invalid value.

- **AC-18**: The help text for `--grind` on both `add` and `update` lists the accepted enum values: `turkish | espresso | fine | medium_fine | medium | medium_coarse | coarse`.

- **AC-19**: `brewlog show [id]` displays the `grind` field as the raw enum string (e.g., `medium_fine`), consistent with how `type` is displayed (e.g., `pour_over`). No formatting or capitalisation is applied.

### Database Schema Update

- **AC-20**: The database schema is updated to include the following new columns on the `brews` table (added via migration on first run after upgrade):
  - `result_brix REAL` — optional, `>= 0`
  - `result_tasting_notes TEXT` — optional, freeform string
  - `result_rating_overall INTEGER` — optional, 1–5
  - `result_rating_fragrance INTEGER` — optional, 1–5
  - `result_rating_aroma INTEGER` — optional, 1–5
  - `result_rating_flavour INTEGER` — optional, 1–5
  - `result_rating_aftertaste INTEGER` — optional, 1–5
  - `result_rating_acidity INTEGER` — optional, 1–5
  - `result_rating_sweetness INTEGER` — optional, 1–5
  - `result_rating_mouthfeel INTEGER` — optional, 1–5

- **AC-21**: The existing `tds` and `ey` columns are retained in the database with their current names and constraints. No column rename or data migration is required. These columns continue to hold their values; the change in v0.3 is how they are serialised during export (under `result`) and how they are read during import (from `result`).

- **AC-22**: The existing `rating` column (integer 1–5) is retained in the database for backward compatibility with existing brew records. On export, the value in `rating` is serialised as `result.ratings.overall`. On import, `result.ratings.overall` is stored in both the `rating` column (for backward compatibility with list display) and `result_rating_overall`. The architect may choose to use only `result_rating_overall` and deprecate the `rating` column if they can confirm no production data exists in the `rating` column from pre-v0.3 CLI usage — but must document this decision in the design.

- **AC-23**: Schema migration is applied automatically on first run of any command that opens the database. The migration check adds any missing columns without dropping or modifying existing columns or data. An existing v0.2 database with brews in it must remain fully readable and functional after the migration runs.

### `brewlog add` — New Result Fields

- **AC-24**: `brewlog add` supports the following new flags for the `result` object:
  - `--brix FLOAT` — dissolved sugar content in degrees Brix
  - `--tasting-notes TEXT` — sensory description of the brew (distinct from `--notes`)
  - `--rating-overall INT` — overall impression, 1–5
  - `--rating-fragrance INT` — fragrance rating, 1–5
  - `--rating-aroma INT` — aroma rating, 1–5
  - `--rating-flavour INT` — flavour rating, 1–5
  - `--rating-aftertaste INT` — aftertaste rating, 1–5
  - `--rating-acidity INT` — acidity rating, 1–5
  - `--rating-sweetness INT` — sweetness rating, 1–5
  - `--rating-mouthfeel INT` — mouthfeel rating, 1–5

- **AC-25**: The existing `--rating INT` flag on `brewlog add` is retired. Running `brewlog add --rating 4` produces a clear error message indicating that `--rating` has been replaced by `--rating-overall` and exits with code 1. The flag is not silently ignored and does not map to `--rating-overall` automatically, to avoid surprising users who supply it by habit.

- **AC-26**: All new `--rating-*` flags on `brewlog add` are validated as integers between 1 and 5 inclusive. A non-integer, zero, or out-of-range value produces a clear error message and exits with code 1 without writing to the database.

- **AC-27**: `--brix FLOAT` on `brewlog add` is validated as a number greater than or equal to zero. A negative value produces a clear error message and exits with code 1. A value of `0` is valid (distilled water reads 0 °Brix).

- **AC-28**: `--tasting-notes TEXT` on `brewlog add` accepts any non-empty string. An empty string produces a clear error message and exits with code 1 (consistent with `minLength: 1` in the schema). The help text for `--tasting-notes` states that this field is for sensory impressions and that operational brew notes belong in `--notes`.

- **AC-29**: When all result flags are absent, the brew is written successfully with no result fields populated. No result fields are required.

- **AC-30**: When `brewlog add` is run in fully interactive mode (no required flags supplied), the tip line is updated to reflect the new flags: `Tip: add optional details with flags, e.g. --method "V60" --rating-overall 4 --tasting-notes "Bright acidity"  (run --help for all options)`. The old `--rating 4` example is removed from the tip.

### `brewlog update` — New Result Fields

- **AC-31**: `brewlog update` supports the same new result flags as `brewlog add`:
  - `--brix FLOAT`
  - `--tasting-notes TEXT`
  - `--rating-overall INT`
  - `--rating-fragrance INT`
  - `--rating-aroma INT`
  - `--rating-flavour INT`
  - `--rating-aftertaste INT`
  - `--rating-acidity INT`
  - `--rating-sweetness INT`
  - `--rating-mouthfeel INT`

- **AC-32**: The existing `--rating INT` flag on `brewlog update` is retired with the same error behaviour as on `brewlog add`: running `brewlog update [id] --rating 4` produces a clear error message indicating that `--rating` has been replaced by `--rating-overall` and exits with code 1.

- **AC-33**: All new `--rating-*` flags on `brewlog update` are validated against the same constraints as on `brewlog add` (integer, 1–5 inclusive). `--brix` is validated as `>= 0`. `--tasting-notes` must be non-empty. Validation failures produce a clear error and exit with code 1 without modifying the database.

- **AC-34**: The column allowlist in `update_brew()` (from AC-1) is updated to include all new columns: `result_brix`, `result_tasting_notes`, `result_rating_overall`, `result_rating_fragrance`, `result_rating_aroma`, `result_rating_flavour`, `result_rating_aftertaste`, `result_rating_acidity`, `result_rating_sweetness`, `result_rating_mouthfeel`.

### `brewlog show` — Display v0.4 Result Fields

- **AC-35**: `brewlog show [id]` displays result fields in a dedicated "Results" section when any result field is populated. The section is omitted entirely if no result fields have values for that brew.

- **AC-36**: The Results section of `brewlog show [id]` output groups fields as follows (each field shown only if it has a value):
  - Measurements: `TDS`, `Extraction Yield (%)`, `Brix`
  - Evaluation: `Tasting Notes`, then `Ratings` sub-section
  - Ratings sub-section displays each dimension that has a value: `Overall`, `Fragrance`, `Aroma`, `Flavour`, `Aftertaste`, `Acidity`, `Sweetness`, `Mouthfeel` — each as `<Label>: <integer>`

- **AC-37**: `brewlog show [id]` does not display the `Ratings` sub-section header if no `result_rating_*` columns have values for that brew.

### `brewlog list` — Display and Filtering Updates

- **AC-38**: The `Rating` column in `brewlog list` output is renamed to `Overall Rating`. It continues to display the value stored in `result_rating_overall` (or the legacy `rating` column for pre-v0.3 brews — see AC-22). Brews with no overall rating display a dash in this column.

- **AC-39**: `brewlog list --until DATE` filters the output to brews with a `date` field on or before `DATE`. `DATE` must be in `YYYY-MM-DD` format. An invalid value produces a clear error message and exits with code 1. The comparison is performed at day granularity — the time component of a stored datetime value is ignored. If no brews match the filter, a friendly message is printed and the command exits with code 0.

- **AC-40**: `--until DATE` is combinable with `--since DATE` and all other existing `brewlog list` flags. When both `--since` and `--until` are supplied, only brews with a date on or after `--since` AND on or before `--until` are returned (inclusive on both ends). If `--since` is later than `--until`, the command prints a clear error message and exits with code 1.

- **AC-41**: When no brews match the combined set of filters (including `--rating-min`, `--rating-max`, `--until`, and all existing filters), the command prints a friendly message (e.g., `No brews match the given filters.`) and exits with code 0. It does not print an empty table.

### `brewlog` (no arguments — welcome screen)

- **AC-42**: The version number displayed on the welcome screen (bare `brewlog` invocation) is updated to `0.3.0`.

---

## Scope

### In Scope

**Carry-forward fixes (from v0.2 review):**
- Column allowlist assertion in `update_brew()` as structural defence-in-depth (AC-1)
- `brewlog list --rating-min N` and `--rating-max N` range filters; combinable with each other and with existing filters (AC-2 through AC-5)

**Date format UX (unblocked by BrewSpec v0.4):**
- `brewlog add` interactive date prompt defaults to today in `YYYY-MM-DD` format (AC-6)
- Date prompt and `--date` flag accept both `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ` (AC-7, AC-8)
- Date stored exactly as supplied; no normalisation (AC-9)
- `--since` and `--until` filter comparisons work correctly against both stored date formats (AC-10)

**BrewSpec v0.4 schema adoption:**
- CLI targets v0.4 schema for export validation and import validation (AC-11)
- Export serialises `tds`, `ey`, `brix`, `tasting_notes`, `ratings` under `result` object (AC-12)
- Import rejects v0.3 files with a specific, actionable error message including migration steps and docs link (AC-13)
- Import correctly reads v0.4 `result` fields into database columns (AC-14)
- v0.4 schema file referenced via a single constant (AC-15)

**`grind` field enum enforcement:**
- `--grind` on `add` and `update` validates against the 7-value enum (AC-16, AC-17)
- Help text for `--grind` lists accepted values (AC-18)
- `brewlog show` displays grind as raw enum string (AC-19)

**Database schema update:**
- New columns for all `result` sub-fields (AC-20)
- Existing `tds`, `ey`, `rating` columns retained; no data migration required (AC-21, AC-22)
- Automatic migration on first run; existing databases remain fully functional (AC-23)

**`brewlog add` and `brewlog update` — result fields:**
- All 8 `--rating-*` dimension flags on both `add` and `update` (AC-24, AC-31)
- `--rating` flag retired on both commands with a clear replacement error message (AC-25, AC-32)
- `--brix` and `--tasting-notes` flags on both `add` and `update` (AC-24, AC-31)
- All new field validations (AC-26, AC-27, AC-28, AC-33, AC-34)
- Interactive tip updated to use `--rating-overall` example (AC-30)

**`brewlog show` — result display:**
- Results section with measurements and SCA ratings dimensions (AC-35, AC-36, AC-37)

**`brewlog list` — display and filtering:**
- `Rating` column renamed to `Overall Rating` (AC-38)
- `--until DATE` filter (AC-39, AC-40, AC-41)

**Welcome screen:**
- Version updated to `0.3.0` (AC-42)

### Out of Scope

- **v0.3 import auto-migration** — the CLI rejects v0.3 files with actionable guidance (OQ2, confirmed). No automatic migration of field placement. Users must update their files manually per the migration guide.
- **v0.3 schema as a fallback** — the CLI supports only v0.4. Dual-schema import support would double the validation surface and is not warranted by observed demand.
- **`brewlog export --since / --until`** — export filtering (subset of database by date range) is deferred. No observed demand; export-all remains correct for the portability use case. Added design complexity from interaction with the format flag.
- **Individual `brewlog add` prompts for result fields** — `--brix`, `--tasting-notes`, and all `--rating-*` flags remain flag-only on `add`. Only the four required fields (`date`, `type`, `dose`, `water`) are prompted interactively. Adding optional result field prompts would make the interactive flow too long for the home brewer use case.
- **`ratings` total score computation** — the schema does not define a computed total. The CLI does not compute or display a sum of rating dimensions. Application layers may compute totals from the stored dimensions if desired.
- **Import deduplication** — re-importing the same file creates duplicate rows. Documented behaviour. No user demand. Deferred indefinitely.
- **Custom database path** — storage is fixed at `~/.brewlog/brews.db`. Deferred.
- **Single-brew export by ID** — full database export remains the only export mode. Deferred.
- **CSV export** — lossy, not a valid BrewSpec format. Deferred indefinitely.
- **`brewlog delete` range/bulk deletion** — basic per-ID delete (shipped in v0.2) is confirmed useful. Range deletion deferred until someone asks for it.
- **`brewlog update` for required fields** — `date`, `type`, `dose_g`, and `water_weight_g` remain non-updatable. Delete and re-add to correct a required field.
- **Water chemistry beyond `ppm`** — deferred from prior versions.
- **Pour schedule / step-by-step timing** — deferred from prior versions.

---

## Design Notes

### BrewSpec v0.4 Data Structure Reference

The export and import format for v0.3 of the CLI:

```yaml
brewspec_version: "0.4"
brews:
  - date: "2026-02-22"             # required — YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
    type: "pour_over"               # required — enum: immersion | pour_over | espresso | hybrid
    dose_g: 18.0                   # required, > 0
    water_weight_g: 280.0          # required, > 0
    method: "Hario V60"            # optional, freeform, minLength: 1
    water_volume_ml: 280.0         # optional, > 0
    water_temp_c: 96.0             # optional, 0–100
    grind: "medium_fine"           # optional — enum: turkish|espresso|fine|medium_fine|medium|medium_coarse|coarse
    duration_s: 180                # optional, > 0
    notes: "Washed filter paper"   # optional — operational brew notes
    coffee:
      roast_date: "2026-01-20"
      type: "single_origin"
      origin: ["Ethiopia"]
      varietal: "Heirloom"
      process: "Washed"
    water:
      ppm: 150
    equipment:
      grinder: "Comandante C40"
      brewer: "Hario V60 02"
    result:                        # optional object — new in v0.4
      tds: 1.38                    # optional, > 0
      ey: 20.1                     # optional, > 0
      brix: 1.5                    # optional, >= 0
      tasting_notes: "Bright citrus, caramel finish"  # optional, sensory impressions
      ratings:                     # optional object
        overall: 4                 # optional, integer 1–5
        fragrance: 3               # optional, integer 1–5
        aroma: 4                   # optional, integer 1–5
        flavour: 5                 # optional, integer 1–5
        aftertaste: 4              # optional, integer 1–5
        acidity: 5                 # optional, integer 1–5
        sweetness: 3               # optional, integer 1–5
        mouthfeel: 4               # optional, integer 1–5
```

Fields removed from v0.3 schema (and therefore no longer valid at the flat brew level): `tds`, `ey`, `rating`.

### Database Schema (Full — v0.3 of CLI)

The `brews` table after the v0.3 migration:

```
id                      INTEGER PRIMARY KEY AUTOINCREMENT
date                    TEXT NOT NULL          -- YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
type                    TEXT NOT NULL          -- enum: immersion | pour_over | espresso | hybrid
method                  TEXT                   -- optional, freeform
dose_g                  REAL NOT NULL          -- > 0
water_weight_g          REAL NOT NULL          -- > 0
water_volume_ml         REAL                   -- optional, > 0
water_temp_c            REAL                   -- optional, 0–100
grind                   TEXT                   -- optional, enum (v0.4)
duration_s              INTEGER                -- optional, > 0
tds                     REAL                   -- optional, > 0 (maps to result.tds on export)
ey                      REAL                   -- optional, > 0 (maps to result.ey on export)
rating                  INTEGER                -- legacy column: maps to result.ratings.overall on export
notes                   TEXT                   -- optional, freeform — operational/brew-process notes
coffee_roast_date       TEXT                   -- optional, YYYY-MM-DD
coffee_type             TEXT                   -- optional: single_origin | blend
coffee_origin           TEXT                   -- optional, JSON-encoded array of strings
coffee_varietal         TEXT                   -- optional, freeform
coffee_process          TEXT                   -- optional, freeform
water_ppm               REAL                   -- optional, >= 0
equipment_grinder       TEXT                   -- optional, freeform
equipment_brewer        TEXT                   -- optional, freeform
result_brix             REAL                   -- optional, >= 0 (NEW in v0.3)
result_tasting_notes    TEXT                   -- optional, freeform (NEW in v0.3)
result_rating_overall   INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_fragrance INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_aroma     INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_flavour   INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_aftertaste INTEGER               -- optional, 1–5 (NEW in v0.3)
result_rating_acidity   INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_sweetness INTEGER                -- optional, 1–5 (NEW in v0.3)
result_rating_mouthfeel INTEGER                -- optional, 1–5 (NEW in v0.3)
```

The architect should evaluate whether the legacy `rating` column should be deprecated in favour of `result_rating_overall`. If all existing brews in production have `rating = NULL` (because the column was always optional and users may not have set it), a clean migration to `result_rating_overall` is possible. If brews exist with `rating` populated, the export logic must read from `rating` for those rows and from `result_rating_overall` for rows added by v0.3+. The architect must document the chosen approach in the design.

### `--rating` Flag Retirement

The `--rating` flag is retired (not aliased) on both `add` and `update`. The reason: an alias (`--rating` → `--rating-overall`) would silently succeed where a user typed `--rating` by habit, giving no signal that anything changed. This is acceptable in isolation but creates a false expectation that other non-`-overall` dimensions are similarly aliased. A clear error is more honest and less confusing than a silent redirect.

The error message for `--rating` must be actionable:
```
Error: --rating has been replaced by --rating-overall in BrewLog v0.3.
Use --rating-overall N to set your overall impression (1-5).
See --help for all available rating dimension flags.
```

### `grind` Enum — Migration of Existing Data

Brews logged with a freeform `grind` value under v0.2 remain in the database unchanged. The `grind` column for those rows contains whatever string the user entered (e.g., `"medium-fine"`, `"setting 15"`). These values:
- Are displayed as-is in `brewlog show` (no validation on read)
- Are omitted from export if they are not valid enum members (they will fail schema validation; the export command must handle this gracefully — see Security Requirements / Input Validation)
- Are not migrated automatically

The architect must decide how to handle export of invalid `grind` values in existing rows. Options: (a) omit the field from the export with a warning, (b) fail the export with a message listing the offending brew IDs. Option (a) is recommended — it keeps the portability promise intact while surfacing the issue to the user. The architect should document the chosen approach.

### Date Filter Comparison with Dual-Format Dates

The `--since DATE` and `--until DATE` filters must compare correctly against both stored date formats (`YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`). The recommended approach for SQLite:

- For a `--since 2026-02-01` filter: `WHERE substr(date, 1, 10) >= '2026-02-01'`
- For a `--until 2026-02-28` filter: `WHERE substr(date, 1, 10) <= '2026-02-28'`

Using `substr(date, 1, 10)` extracts the `YYYY-MM-DD` prefix from both formats, making the comparison format-agnostic. This is a parameterised query; the date string from the filter flag is passed as a parameter, not interpolated.

### Export Serialisation — v0.4 `result` Object

When serialising a brew record for export:
- If none of `tds`, `ey`, `result_brix`, `result_tasting_notes`, and any `result_rating_*` column have a value, omit the `result` object entirely.
- If at least one result field has a value, include the `result` object with only the populated sub-fields.
- Inside `result`, include `ratings` only if at least one `result_rating_*` column has a value.
- The legacy `rating` column value (if non-null) is exported as `result.ratings.overall` and the `result_rating_overall` value (if non-null) takes precedence. If both are set (which should not occur after v0.3 ships, but could in migrated data), `result_rating_overall` wins.
- The exported data structure is validated against the v0.4 JSON Schema before writing to disk. Validation failure produces a clear error and no file is written.

### Import — v0.4 `result` Field Mapping

When reading a v0.4 import file:
- `result.tds` → `tds` column
- `result.ey` → `ey` column
- `result.brix` → `result_brix` column
- `result.tasting_notes` → `result_tasting_notes` column
- `result.ratings.overall` → `result_rating_overall` column (and `rating` column for backward compat — architect's discretion per AC-22 note)
- `result.ratings.fragrance` → `result_rating_fragrance` column
- `result.ratings.aroma` → `result_rating_aroma` column
- `result.ratings.flavour` → `result_rating_flavour` column
- `result.ratings.aftertaste` → `result_rating_aftertaste` column
- `result.ratings.acidity` → `result_rating_acidity` column
- `result.ratings.sweetness` → `result_rating_sweetness` column
- `result.ratings.mouthfeel` → `result_rating_mouthfeel` column

### v0.3 Import Rejection Message

The error message for a v0.3 (or other unsupported version) import file must be specific and actionable. Exact content:

```
Error: This file uses BrewSpec v0.3, which is not supported by BrewLog v0.3.
BrewLog v0.3 requires BrewSpec v0.4.

To migrate your file from v0.3 to v0.4, make the following changes:
  1. Change 'brewspec_version' from "0.3" to "0.4"
  2. Move 'tds' (if present) from the brew level to 'result.tds'
  3. Move 'ey' (if present) from the brew level to 'result.ey'
  4. Move 'rating' (if present) from the brew level to 'result.ratings.overall'
  5. Replace any freeform 'grind' values with one of:
     turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse
     (or remove the 'grind' field if no match applies)

Full migration guide: https://github.com/coffee-standards/brewspec
```

The message is written to stderr. Exit code is 1.

### `brewlog show` Output Grouping (Updated for v0.3)

```
Brew #14
---------
Date:           2026-02-22
Type:           pour_over
Method:         Hario V60
Dose (g):       18.0
Water (g):      280.0
Water Temp (C): 96.0
Grind:          medium_fine
Duration (s):   180
Notes:          Washed filter paper

Results
-------
TDS (%):        1.38
EY (%):         20.1
Brix:           1.5
Tasting Notes:  Bright citrus, caramel finish
Ratings:
  Overall:      4
  Fragrance:    3
  Aroma:        4
  Flavour:      5
  Aftertaste:   4
  Acidity:      5
  Sweetness:    3
  Mouthfeel:    4

Coffee
------
Roast Date:     2026-01-20
Type:           single_origin
Origin:         Ethiopia
Varietal:       Heirloom
Process:        Washed

Water
-----
PPM:            150

Equipment
---------
Grinder:        Comandante C40
Brewer:         Hario V60 02
```

Sections with no populated fields for a given brew are omitted from the output.

### Column Allowlist for `update_brew()`

The allowlist must be a module-level constant (not computed dynamically). It should cover all columns that `update` can modify. The assertion should be:

```python
UPDATABLE_COLUMNS = frozenset({
    "method", "grind", "water_temp_c", "duration_s", "tds", "ey",
    "notes", "coffee_roast_date", "coffee_type", "coffee_origin",
    "coffee_varietal", "coffee_process", "water_ppm",
    "equipment_grinder", "equipment_brewer",
    "result_brix", "result_tasting_notes",
    "result_rating_overall", "result_rating_fragrance", "result_rating_aroma",
    "result_rating_flavour", "result_rating_aftertaste", "result_rating_acidity",
    "result_rating_sweetness", "result_rating_mouthfeel",
})

assert set(updates.keys()).issubset(UPDATABLE_COLUMNS), (
    f"Unexpected column names in update dict: {set(updates.keys()) - UPDATABLE_COLUMNS}"
)
```

---

## Security Requirements

**Data Sensitivity:**
- Brew logs are personal data. `result.tasting_notes` and the existing `notes` field contain user-generated personal impressions. Low sensitivity individually; in aggregate they reflect user habits, preferences, and patterns over time.
- `result.ratings` dimensions are personal evaluations. Low sensitivity.
- `result_brix` is a numeric measurement. No PII risk.
- Date-only values (`YYYY-MM-DD`) carry slightly less temporal precision than full datetimes — a marginal privacy improvement for users who prefer not to record the time of day.
- The tool must not transmit any data over the network. All operations remain local and offline.

**Input Validation:**
- All new `--rating-*` flags must be validated as integers in the range 1–5 before any database write. Non-integer, zero, and out-of-range values must be rejected at the application layer (Pydantic model or equivalent), not only at the database layer.
- `--brix` must be validated as a non-negative number (`>= 0`). A negative value is rejected.
- `--tasting-notes` must be validated as a non-empty string (`minLength: 1`). An empty string is rejected.
- `--grind` must be validated against the closed 7-value enum. Any value not in the enum is rejected with a message listing the accepted values.
- `--date` (both interactive and flag) must be validated against both accepted formats (`YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`). Any other format is rejected. Note: format validation does not guarantee calendar correctness (e.g., month 13 passes format validation). This is intentional and consistent with prior versions.
- The `--rating-min` / `--rating-max` flags must be validated as integers in 1–5 before constructing any SQL query. A `--rating-min` greater than `--rating-max` must be caught at the application layer before the query is built.
- Freeform text fields (`notes`, `tasting_notes`, `method`, `grind`, `coffee_varietal`, `coffee_process`, `equipment_grinder`, `equipment_brewer`) must never be executed, evaluated, or interpolated into commands. They are stored and retrieved as plain strings only.

**SQL Injection:**
- The column allowlist assertion in `update_brew()` (AC-1) makes the safety property of the dynamic UPDATE statement structurally explicit. Column names in the UPDATE come from application code via the allowlist, not from user input. Parameter values are passed as SQL parameters, not interpolated.
- All new database reads and writes must use parameterised queries. The `--rating-min` / `--rating-max` filters, the `--until DATE` filter, and all new INSERT columns must use `?` placeholders.
- Dynamic WHERE clause construction for `brewlog list` (established in v0.2) is extended with the new filter conditions. The condition strings (`result_rating_overall >= ?`, `result_rating_overall <= ?`, `substr(date, 1, 10) <= ?`) must be static strings in source code; only the parameter values come from user input.

**File I/O:**
- No new file I/O surfaces are introduced in v0.3. All existing controls remain in place:
  - Export path: `..` component rejection, extension validation (`.yaml`, `.yml`, `.json` only), overwrite confirmation
  - Import path: `..` component rejection, 10MB file size limit before parsing
  - YAML parsing: `yaml.safe_load()` only; `yaml.load()` without a safe loader is prohibited
- Imported data continues to be validated against the BrewSpec JSON Schema before any database writes. This is the primary defence against malformed or adversarially crafted import files. The schema must be the v0.4 schema file.
- Export serialisation: the export function must not include `grind` values from existing rows if they are not valid v0.4 enum members (they would cause export validation to fail). See Design Notes for the recommended handling (omit with warning vs. fail with message).

**No Secrets in Code:**
- No API keys, credentials, tokens, or secrets of any kind may appear in the source code or test fixtures.
- The database path (`~/.brewlog/brews.db`) and the BrewSpec repo URL are not sensitive and may appear in documentation and code.

---

## Dependencies

**Upstream:**
- `brewspec-v0.4` (done) — BrewLog CLI v0.3 targets the v0.4 schema. The date dual-format, `grind` enum, `result` object, and `result.ratings` dimensions are all v0.4 additions. The v0.4 JSON Schema file from the BrewSpec repository is used for import and export validation.
- `brewlog-cli-v0.2` (done) — v0.3 is a direct iteration. The existing database schema, command structure, validation patterns, and test suite are the baseline.

**Downstream:**
- `commercial-brew-tracking-app` (backlog) — relies on BrewSpec-compliant export. v0.3 of the CLI produces v0.4 files, which will be the expected format when the commercial app's import path is built.
- `brewspec-v0.5` (backlog) — any future schema changes that affect the CLI will require a corresponding BrewLog CLI update.

**Runtime Dependencies (unchanged):**
- `click` — CLI framework
- `pyyaml` — YAML parsing and serialisation (`safe_load` only)
- `pydantic` — input validation models
- `jsonschema` — BrewSpec schema validation for import and export

---

## Success Metrics

Tied to `specs/strategy.md` Phase 1 success metrics:

- **Schema currency**: `brewlog export` produces files that pass validation against the v0.4 JSON Schema without modification.
- **Date UX**: A user can log a brew with today's date by pressing Enter at the date prompt without typing anything. The stored value is `YYYY-MM-DD` format.
- **Result fields**: All 8 rating dimensions, `brix`, and `tasting_notes` can be set on `add` and `update`, are stored correctly, appear in `show` output, and round-trip correctly through export and import.
- **Filtering completeness**: `--rating-min`, `--rating-max`, and `--until` work individually and in combination with all existing filters. Range filter with `--rating-min 3 --rating-max 5` returns the correct subset of brews.
- **Import rejection**: Importing a v0.3 BrewSpec file produces the exact error message defined in Design Notes (version found, list of required changes, docs URL). Exit code is 1. No rows are written.
- **Backward compatibility**: An existing v0.2 database (with brews logged under prior versions) remains fully readable and functional after the v0.3 migration runs. All existing brews appear in `list`, `show`, and `export`.
- **Test suite**: 100% pass rate required before reviewer sign-off. All new ACs must have corresponding tests written first (TDD). The full test suite (including v0.2 regression tests) must pass without modification.
- **Security baseline**: Column allowlist assertion present in `update_brew()`. All new SQL uses parameterised queries. No `grind` enum bypass possible via CLI flags. Import file validated against v0.4 schema before any database write.

---

## Open Questions

- [x] **OQ1 — Ratings UX** — Resolved: Option B (Full). All 8 rating dimension flags on both `add` and `update`. `--rating` flag is retired (not aliased) with a clear error message.
- [x] **OQ2 — v0.3 import handling** — Resolved: Option A (Reject with guidance). CLI rejects v0.3 files with an actionable error listing required changes and pointing to the migration guide. No auto-migration.
- [x] **OQ3 — Grind display in `show`** — Resolved: raw enum string (e.g., `medium_fine`), consistent with how `type` displays (e.g., `pour_over`).
- [x] **OQ4 — List rating column** — Resolved: column renamed to `Overall Rating`.
- [ ] **Legacy `rating` column** — Should the architect deprecate the `rating` column in favour of `result_rating_overall` in the database schema? If any production brews have `rating` populated, a clean migration is required. The architect must assess and document the chosen approach. See AC-22 and Design Notes.
- [ ] **Export of invalid `grind` values** — Brews logged under v0.2 may have freeform `grind` values that are not valid v0.4 enum members. Should the export omit the `grind` field for those brews (with a warning) or fail with a message listing the offending brew IDs? The architect must choose and document the approach. See Design Notes.
