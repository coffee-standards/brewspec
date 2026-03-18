# Product: BrewLog CLI

**Status:** In Progress
**Current version:** v0.1.1
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-02-19
**Last Updated:** 2026-02-20

---

## Problem Statement

Home brewers who want to track their brews have no purpose-built tool that is free, portable, and works offline. Their current workarounds — notes apps, spreadsheets, memory — produce data that is locked in proprietary formats, hard to query, and impossible to migrate to other tools.

BrewLog CLI solves this for the terminal-comfortable home brewer. It provides a local command-line tool to log, view, update, and export brews using the BrewSpec format. It proves the spec works end-to-end in a real implementation and establishes the data portability foundation for the future commercial product.

Target personas:
- **Primary — The Home Brewer**: logs brews to remember what worked. Currently uses a notes app, spreadsheet, or memory. Comfortable with a terminal, or willing to try.
- **Secondary — The Coffee Professional**: needs portable data. The export command produces BrewSpec-compliant files they can share or migrate.
- **Tertiary — The Tool Builder**: the CLI is a reference implementation of BrewSpec. Its import/export demonstrates the spec in action.

---

## User Stories

- As a **home brewer**, I want to log a brew from the terminal so that I have a record of what I brewed and how it tasted without switching to a notes app.
- As a **home brewer**, I want required fields prompted interactively so that I don't have to memorize the command syntax for a quick log entry.
- As a **home brewer**, I want to list my recent brews in a summary table so that I can quickly see what I've brewed lately.
- As a **home brewer**, I want to show all fields for a specific brew so that I can recall the exact parameters I used.
- As a **home brewer**, I want to export all my brews to a BrewSpec file so that my data is portable and I'm never locked into this tool.
- As a **home brewer**, I want to import brews from a BrewSpec file so that I can bring in data from another tool or a backup.
- As a **home brewer**, I want to update optional details on a logged brew after the fact so that I can add rating, notes, or method information I didn't have at logging time.
- As a **coffee professional**, I want exports to produce valid BrewSpec files so that I can open them in any tool that implements the standard.
- As a **tool builder**, I want the CLI to demonstrate correct BrewSpec import and export so that I have a reference implementation to build against.
- As a **home brewer**, I want to delete a brew I logged by mistake so that my history stays accurate without requiring me to export and re-import everything.

---

## Acceptance Criteria

### Installation and Initialisation

- **AC-1**: The package installs via `pip install .` (or `pip install -e .` for development) from the project root and makes the `brewlog` command available on the system PATH.
- **AC-2**: Running `brewlog` with no arguments displays an ASCII art coffee cup followed by help text listing all available commands. No error is raised.
- **AC-3**: On first run of any command that requires the database, the SQLite database file is created automatically at `~/.brewlog/brews.db` (directory created if it does not exist). The user is not required to run a setup or init command.
- **AC-4**: The database schema is created automatically on first run. It must include a `brews` table with columns covering all BrewSpec brew-level fields, coffee/water metadata fields, and v0.3 equipment and extraction yield fields.

### `brewlog add`

- **AC-5**: Running `brewlog add` with no flags enters an interactive prompt sequence. The user is prompted for each required field in order: date (default: current UTC datetime in ISO 8601 format, accepted on Enter), brew type (accepts: `immersion`, `pour_over`, `espresso`, `hybrid`), dose in grams, water weight in grams.
- **AC-6**: Each required field prompt displays the field name, expected format or accepted values, and the default value where one exists. Example: `Date [2026-02-19T08:30:00Z]:`.
- **AC-7**: If the user provides an invalid value at any prompt (e.g., a non-numeric dose, a brew type not in the enum), the prompt repeats with an error message explaining what went wrong. The command does not exit; it re-prompts until a valid value is entered or the user cancels with Ctrl+C.
- **AC-8**: All optional fields are accepted as flags. The following flags are supported on `brewlog add`:
  - `--date TEXT` — ISO 8601 UTC datetime string (overrides interactive prompt)
  - `--type TEXT` — brew type enum (overrides interactive prompt)
  - `--dose FLOAT` — coffee dose in grams (overrides interactive prompt)
  - `--water FLOAT` — water weight in grams (overrides interactive prompt)
  - `--method TEXT` — freeform brew method (e.g., `"Hario V60"`)
  - `--temp FLOAT` — water temperature in Celsius
  - `--grind TEXT` — freeform grind description
  - `--duration INT` — brew duration in seconds
  - `--rating INT` — rating 1–5
  - `--notes TEXT` — freeform notes
  - `--roast-date TEXT` — coffee roast date (YYYY-MM-DD)
  - `--coffee-type TEXT` — `single_origin` or `blend`
  - `--origin TEXT` — coffee origin; may be supplied multiple times for blends (e.g., `--origin Ethiopia --origin Colombia`)
  - `--varietal TEXT` — freeform coffee varietal
  - `--process TEXT` — freeform processing method
  - `--water-ppm FLOAT` — water mineral content in ppm
  - `--tds FLOAT` — brew TDS percentage
  - `[v0.2] --ey FLOAT` — extraction yield percentage (BrewSpec v0.3 field; not yet implemented on `add`)
  - `[v0.2] --grinder TEXT` — freeform grinder name or description (BrewSpec v0.3 field; not yet implemented on `add`)
  - `[v0.2] --brewer TEXT` — freeform brewer name or description (BrewSpec v0.3 field; not yet implemented on `add`)
- **AC-9**: All field values are validated against BrewSpec constraints before the brew is written to the database. Invalid flag values produce a clear error message and exit without writing. Specifically:
  - `dose` and `water` must be numbers greater than zero
  - `type` must be one of `immersion`, `pour_over`, `espresso`, `hybrid`
  - `temp` must be a number between 0 and 100 inclusive
  - `duration` must be an integer greater than zero
  - `rating` must be an integer between 1 and 5 inclusive
  - `tds` must be a number greater than zero
  - `water-ppm` must be a number greater than or equal to zero (zero ppm is valid)
  - `roast-date` must match the pattern `YYYY-MM-DD`
  - `coffee-type` must be `single_origin` or `blend`
  - `date` must be a valid ISO 8601 UTC datetime string
- **AC-10**: On successful write, the command prints a single confirmation line showing the assigned brew ID. Example: `Brew #14 logged.`
- **AC-11**: When required fields are supplied as flags and all values are valid, the command skips interactive prompts entirely and writes directly. This enables scripted/automated use.

### `brewlog list`

- **AC-12**: Running `brewlog list` displays a formatted table of the most recent 20 brews, ordered by date descending (most recent first).
- **AC-13**: The table includes the following columns: `ID`, `Date`, `Type`, `Method`, `Dose (g)`, `Water (g)`, `Rating`. Columns for optional fields display a blank or dash when the value is not set for a given row.
- **AC-14**: Running `brewlog list --limit N` displays the most recent N brews. N must be a positive integer; invalid values produce a clear error.
- **AC-15**: Running `brewlog list --all` displays every brew in the database, ordered by date descending.
- **AC-16**: If the database contains no brews, `brewlog list` prints a friendly message (e.g., `No brews logged yet. Run 'brewlog add' to get started.`) and exits with code 0.

### `brewlog show`

- **AC-17**: Running `brewlog show [id]` displays all stored fields for the brew with the given integer ID. Every field that has a value is shown; fields with no value are omitted from the output.
- **AC-18**: The output is formatted for human readability. Fields are grouped logically: brew parameters first (date, type, method, dose, water weight, water temp, grind, duration), then results (TDS, rating, notes), then coffee metadata (roast date, type, origin, varietal, process), then water metadata (ppm).
- **AC-19**: If no brew with the given ID exists, the command prints a clear error message (e.g., `No brew found with ID 42.`) and exits with a non-zero exit code.
- **AC-20**: Running `brewlog show` with no argument prints a usage error and exits with a non-zero exit code.

### `brewlog export`

- **AC-21**: Running `brewlog export [path]` writes all brews in the database to the specified file path as a BrewSpec-compliant YAML document. The exported file must pass validation against the BrewSpec JSON Schema.
- **AC-22**: Running `brewlog export [path] --format json` writes the same output as a JSON file. The exported file must pass validation against the BrewSpec JSON Schema.
- **AC-23**: The exported document uses the array structure required by BrewSpec: a `brewspec_version` string at the top level and a `brews` array containing all brew records.
- **AC-24**: Optional fields that have no value for a given brew are omitted from that brew's entry in the export. The exported file must not contain null values or empty objects for absent optional fields.
- **AC-25**: If the database contains no brews, the command writes a valid BrewSpec document with an empty-safe structure — specifically, it exits with a message (e.g., `No brews to export.`) and does not write a file. A file with `brews: []` is not valid BrewSpec (minItems: 1) and must not be produced.
- **AC-26**: The output path is validated before writing. Paths containing `..` components are rejected with a clear error to prevent directory traversal. If the parent directory does not exist, the command fails with a clear error rather than creating directories silently.
- **AC-27**: If a file already exists at the output path, the command prompts the user to confirm overwrite before proceeding. A `--force` flag skips the confirmation.

### `brewlog import`

- **AC-28**: Running `brewlog import [path]` reads a YAML or JSON file, validates it against the BrewSpec JSON Schema, and on success inserts all brews into the local database. The file format (YAML or JSON) is detected automatically from the file extension (`.yaml`, `.yml`, `.json`).
- **AC-29**: If the file fails schema validation, the command prints the validation error(s) and exits with a non-zero exit code. No brews are written to the database.
- **AC-30**: If the file passes validation, the command prints a summary on completion. Example: `Imported 5 brews.`
- **AC-31**: All YAML parsing uses `yaml.safe_load()`. Use of `yaml.load()` without a safe loader is not permitted anywhere in the codebase.
- **AC-32**: The import path is validated before reading. Paths containing `..` components are rejected. Files larger than 10MB are rejected with a clear error before parsing to prevent memory issues from pathologically large inputs.
- **AC-33**: Brews from the imported file are appended to the database. Existing brews are not modified or deleted. There is no deduplication in v0.1 — re-importing the same file will create duplicate rows.

### `brewlog` (no arguments — welcome screen)

- **AC-34**: Running `brewlog` with no arguments displays an ASCII art coffee cup, the application name (`BrewLog`), and the version number, followed by the standard help text listing all available commands and a brief description of each.
- **AC-35**: The ASCII art and welcome output are written to stdout. The exit code is 0.
- **AC-36**: The welcome screen does not appear when running any subcommand (`add`, `list`, `show`, `export`, `import`). Subcommand output is not prefixed or decorated with the ASCII art.

### `brewlog add` — interactive tip (v0.1.1)

- **AC-37**: When `brewlog add` is run with no required flags supplied on the command line (fully interactive mode), a tip line is printed to stdout before the first prompt: `Tip: add optional details with flags, e.g. --method "V60" --rating 4  (run --help for all options)`. The tip does not appear when any required flag (`--date`, `--type`, `--dose`, `--water`) is provided on the command line.

### `brewlog update` (v0.1.1)

- **AC-38**: Running `brewlog update [ID]` where `ID` is a positive integer updates the brew with that ID. On success, the command prints `Brew #N updated.` and exits with code 0.
- **AC-39**: Running `brewlog update` with no positional `ID` argument targets the most recent brew (highest ID / latest date). If the database contains no brews, the command prints a clear error message and exits with code 1.
- **AC-40**: At least one update flag must be supplied. If `brewlog update` is invoked with no flags (other than the optional ID), the command prints a clear error message explaining that at least one field flag is required and exits with code 1.
- **AC-41**: If the specified brew ID does not exist in the database, the command prints a clear error message (e.g., `No brew found with ID N.`) and exits with code 1. The database is not modified.
- **AC-42**: The following 16 flags are supported on `brewlog update`. Each flag, when supplied, overwrites the existing value for that field on the target brew:
  - `--method TEXT` — freeform brew method
  - `--grind TEXT` — freeform grind description
  - `--temp FLOAT` — water temperature in Celsius
  - `--duration INT` — brew duration in seconds
  - `--rating INT` — rating 1–5
  - `--notes TEXT` — freeform notes
  - `--tds FLOAT` — brew TDS percentage
  - `--ey FLOAT` — extraction yield percentage
  - `--roast-date TEXT` — coffee roast date (YYYY-MM-DD)
  - `--coffee-type TEXT` — `single_origin` or `blend`
  - `--origin TEXT` — coffee origin; may be supplied multiple times (replaces the full origin array)
  - `--varietal TEXT` — freeform coffee varietal
  - `--process TEXT` — freeform processing method
  - `--water-ppm FLOAT` — water mineral content in ppm
  - `--grinder TEXT` — freeform grinder name or description
  - `--brewer TEXT` — freeform brewer name or description
- **AC-43**: Multiple flags may be supplied in a single invocation. All supplied fields are updated atomically — either all fields are written or none are (no partial updates on validation failure).
- **AC-44**: All field values supplied to `brewlog update` are validated against the same constraints as `brewlog add` before any database write:
  - `temp` must be a number between 0 and 100 inclusive
  - `duration` must be an integer greater than zero
  - `rating` must be an integer between 1 and 5 inclusive
  - `tds` and `ey` must be numbers greater than zero
  - `water-ppm` must be a number greater than or equal to zero
  - `roast-date` must match the pattern `YYYY-MM-DD`
  - `coffee-type` must be `single_origin` or `blend`
  - Invalid values produce a clear error message and exit with code 1 without modifying the database.
- **AC-45**: The `brewlog update` command does not modify the required fields (`date`, `type`, `dose_g`, `water_weight_g`). These fields are set at log time and are not updatable via `update`. If a user needs to correct a required field, they must delete the brew and re-add it.

### v0.2 planned acceptance criteria

- **[v0.2] AC-46**: Running `brewlog delete [id]` where `id` is a positive integer deletes the brew with that ID from the database. Before deleting, the command prompts the user for confirmation: `Delete brew #N? [y/N]:`. The user must type `y` or `Y` to confirm; any other input cancels with a message (`Cancelled.`) and exits with code 0. On successful delete, the command prints `Brew #N deleted.` and exits with code 0. If the specified brew ID does not exist, the command prints a clear error message and exits with code 1. A `--force` flag skips the confirmation prompt and proceeds directly to deletion.
- **[v0.2] AC-47**: `brewlog add` supports `--ey FLOAT`, `--grinder TEXT`, and `--brewer TEXT` flags, matching the flags already available on `brewlog update`. Validation follows the same rules as for `update` (ey > 0; grinder and brewer are freeform strings).
- **[v0.2] AC-48**: `brewlog export [path]` validates that the output path ends with `.yaml`, `.yml`, or `.json` before writing. If the path has any other extension or no extension, the command prints a clear error message (e.g., `Output path must end with .yaml, .yml, or .json.`) and exits with code 1. No file is written.
- **[v0.2] AC-49**: When `brewlog show [id]` is called with an ID that does not exist in the database, the error message is written to stderr (not stdout) using `click.echo(..., err=True)`. The exit code remains 1.
- **[v0.2] AC-50**: Running `brewlog list --type TYPE` filters the output to brews where the type field matches `TYPE` exactly. `TYPE` must be one of the valid brew type enum values (`immersion`, `pour_over`, `espresso`, `hybrid`); an invalid value produces a clear error and exits with code 1. If no brews match the filter, a friendly message is printed and the command exits with code 0.
- **[v0.2] AC-51**: Running `brewlog list --rating N` filters the output to brews with exactly the given integer rating. `N` must be an integer between 1 and 5 inclusive; an invalid value produces a clear error and exits with code 1. If no brews match the filter, a friendly message is printed and the command exits with code 0.
- **[v0.2] AC-52**: Running `brewlog list --since DATE` filters the output to brews with a date on or after `DATE`. `DATE` must be in `YYYY-MM-DD` format; an invalid value produces a clear error and exits with code 1. The comparison is performed against the brew's `date` field at day granularity (time component ignored). If no brews match the filter, a friendly message is printed and the command exits with code 0.

---

## Scope

### In Scope (shipped — v0.1 and v0.1.1)

- `brewlog add` — interactive prompts for required fields; flags for all optional fields; validation before write; flag tip hint in interactive mode
- `brewlog list` — summary table; default last 20; `--limit N`; `--all`
- `brewlog show [id]` — full detail view for a single brew by integer ID
- `brewlog export [path]` — full database export to BrewSpec YAML (default) or JSON (`--format json`)
- `brewlog import [path]` — import from BrewSpec YAML or JSON; validate before write; append only
- `brewlog update [id]` — update optional fields on an existing brew by ID or on the latest brew when ID is omitted; 16 updatable flags including v0.3 fields (ey, grinder, brewer)
- `brewlog` (no args) — ASCII art coffee cup and help screen
- Local SQLite storage at `~/.brewlog/brews.db`; auto-created on first run
- Input validation against BrewSpec constraints on all user-supplied values
- Path validation for export and import (directory traversal prevention, file size limit on import)
- Safe YAML parsing (`yaml.safe_load()`) throughout
- Works on macOS, Linux, and Windows (Python 3.11+)

### In Scope (planned — v0.2)

- `brewlog delete [id]` — delete a brew by integer ID with confirmation prompt; `--force` to skip confirmation. P1 — confirmed user need from real usage.
- `brewlog add` flag parity — add `--ey`, `--grinder`, `--brewer` flags to `brewlog add` to match `brewlog update`. P2.
- `brewlog list` filtering — `--type TYPE`, `--rating N`, `--since DATE` flags to narrow list output. P2.
- Export path extension validation — reject extensionless or incorrectly-extensioned export paths before writing. P2 (carry-forward from v0.1 review).
- `brewlog show` stderr fix — route the missing-ID error message to stderr. P2 (carry-forward from v0.1 review).

### Out of Scope

- **`brewlog list --until DATE`** and **date range filtering** — `--since` is in scope for v0.2; an upper-bound filter deferred to v0.3 pending real usage data.
- **`brewlog delete` range deletion** — deleting all brews before a date or by type deferred to v0.3; confirm basic delete is useful first.
- **CSV export** (`brewlog export --format csv`) — useful for Excel/spreadsheet use cases but lossy (cannot round-trip) and not a valid BrewSpec format; deferred.
- **BrewSpec v0.1 import support** — v0.2/v0.3 are the target schemas; v0.1 adoption is near-zero and a migration path is documented in the BrewSpec v0.2 spec.
- **Custom database path or configuration file** — storage location is fixed at `~/.brewlog/brews.db`; deferred.
- **Database migration tooling** — the live schema already supports v0.3 fields; no migration needed for v0.2.
- **Interactive prompts for optional fields** — only required fields are prompted; optional fields require explicit flags. Reduces complexity and is consistent with Unix convention.
- **Deduplication on import** — re-importing the same file creates duplicate rows; deferred. Confirmed: no deduplication in v0.1 or v0.2; this is documented behaviour.
- **Networked or cloud functionality** — all operations are local and offline; no network calls permitted.
- **`brewlog export` for a single brew by ID** — export is always full database; single-brew export deferred.
- **`brewlog update` for required fields** — date, type, dose, and water weight are set at log time and are not updatable via the update command.

---

## Design Notes

### CLI Framework

Use Click (already in the tech stack). Click provides built-in support for interactive prompts (`click.prompt`), flag validation, and subcommand grouping — a natural fit for this interface design.

### Database Schema

The `brews` table maps directly to the BrewSpec brew-level structure. Current columns (inclusive of v0.3 additions already live):

```
id               INTEGER PRIMARY KEY AUTOINCREMENT
date             TEXT NOT NULL          -- ISO 8601 UTC datetime
type             TEXT NOT NULL          -- enum: immersion | pour_over | espresso | hybrid
method           TEXT                   -- optional, freeform
dose_g           REAL NOT NULL          -- > 0
water_weight_g   REAL NOT NULL          -- > 0
water_volume_ml  REAL                   -- optional, > 0
water_temp_c     REAL                   -- optional, 0–100
grind            TEXT                   -- optional, freeform
duration_s       INTEGER                -- optional, > 0
tds              REAL                   -- optional, > 0
ey               REAL                   -- optional, > 0 (BrewSpec v0.3)
rating           INTEGER                -- optional, 1–5
notes            TEXT                   -- optional, freeform
coffee_roast_date TEXT                  -- optional, YYYY-MM-DD
coffee_type      TEXT                   -- optional: single_origin | blend
coffee_origin    TEXT                   -- optional, JSON-encoded array of strings
coffee_varietal  TEXT                   -- optional, freeform
coffee_process   TEXT                   -- optional, freeform
water_ppm        REAL                   -- optional, >= 0
equipment_grinder TEXT                  -- optional, freeform (BrewSpec v0.3)
equipment_brewer  TEXT                  -- optional, freeform (BrewSpec v0.3)
```

`coffee_origin` is stored as a JSON-encoded array of strings (e.g., `'["Ethiopia", "Colombia"]'`) to preserve the BrewSpec array structure without requiring a separate join table. The architect may choose a different approach if justified.

The `ey`, `equipment_grinder`, and `equipment_brewer` columns are already present in the live schema as of v0.1.1. They map to BrewSpec v0.3 fields (`ey` flat on the brew object; `equipment.grinder` and `equipment.brewer` under the equipment object). No schema migration is needed for v0.2.

### Export Serialisation

When serialising a brew record for export:
- Fields with NULL values in the database are omitted from the output dict entirely — not included as `null`.
- `coffee_origin` is deserialised from its JSON string back to a Python list before export.
- The `coffee` object is only included in the output if at least one coffee metadata field is present.
- The `water` object is only included in the output if `water_ppm` is present.
- The resulting data structure is validated against the BrewSpec JSON Schema before writing to disk.

### BrewSpec Data Structure Reference (v0.3)

```yaml
brewspec_version: "0.3"
brews:
  - date: "2026-02-19T08:30:00Z"    # required
    type: "pour_over"                 # required, enum
    method: "Hario V60"              # optional
    dose_g: 18.0                     # required, > 0
    water_weight_g: 280.0            # required, > 0
    water_volume_ml: 280.0           # optional, > 0
    water_temp_c: 96.0               # optional, 0–100
    grind: "medium-fine"             # optional
    duration_s: 180                  # optional, > 0
    tds: 1.38                        # optional, > 0
    ey: 20.1                         # optional, > 0 (v0.3)
    rating: 4                        # optional, 1–5
    notes: "Bright acidity"          # optional
    coffee:                          # optional object
      roast_date: "2026-01-20"       # optional, YYYY-MM-DD
      type: "single_origin"          # optional, enum
      origin: ["Ethiopia"]           # optional, array, minItems: 1
      varietal: "Heirloom"           # optional, freeform
      process: "Washed"              # optional, freeform
    water:                           # optional object
      ppm: 150                       # optional, >= 0
    equipment:                       # optional object (v0.3)
      grinder: "Comandante C40"      # optional, freeform
      brewer: "Hario V60-02"         # optional, freeform
```

### Interactive Prompt Behaviour

The `add` command uses `click.prompt()` for required fields:
- `date` defaults to the current UTC datetime formatted as ISO 8601. User presses Enter to accept.
- `type` validates against the enum inline; re-prompts on invalid input.
- `dose_g` and `water_weight_g` are numeric; re-prompt on non-numeric or non-positive input.

When all required fields are supplied as flags, no prompts are shown. This makes the command scriptable without disabling interactive mode explicitly.

When entering interactive mode (no required flags supplied), the tip line is printed once before the first prompt: `Tip: add optional details with flags, e.g. --method "V60" --rating 4  (run --help for all options)`. This is informational only and does not interrupt the prompt flow.

### ASCII Art

The coffee cup is displayed only on bare `brewlog` invocation (no subcommand). It should not appear in `--help` output for subcommands. A simple 6–10 line ASCII cup is sufficient. Keep it in a constant in the source — do not fetch it at runtime.

### Exit Codes

- 0 — success, or informational output (no brews found, nothing to export)
- 1 — user error (invalid input, file not found, schema validation failure, path traversal attempt)

---

## Security Requirements

**Data Sensitivity:**
- Brew logs are personal data. They reflect user habits, preferences, and implicitly time-of-day and location patterns.
- No PII is required by the data model (no name, email, or account), but users may write identifying information in freeform fields (`notes`, `method`, `grind`, `coffee_varietal`, `coffee_process`).
- The database is stored locally at `~/.brewlog/brews.db`. It is the user's data, on the user's machine. The tool must not transmit any data over the network.
- Freeform text fields must be stored and displayed as plain text. They must never be executed, evaluated, or interpolated into shell commands.

**Input Validation:**
- All user-supplied values must be validated against BrewSpec v0.3 constraints before writing to the database. Validation must occur in the application layer (Pydantic models or equivalent), not only at the database layer.
- Numeric fields (`dose_g`, `water_weight_g`, `water_volume_ml`, `water_temp_c`, `duration_s`, `tds`, `ey`, `water_ppm`) must be validated for type (numeric) and range before storage.
- Enum fields (`type`, `coffee_type`) must be validated against the allowed values before storage.
- The `date` field must be validated as a parseable ISO 8601 UTC datetime string.
- The `coffee_roast_date` field must be validated against the pattern `YYYY-MM-DD`. Note: the pattern does not validate calendar correctness (e.g., month 13 would pass). This is acceptable — calendar validation is an application-layer concern deferred if needed.
- Freeform text fields (`method`, `grind`, `notes`, `coffee_varietal`, `coffee_process`, `equipment_grinder`, `equipment_brewer`) must not have user input executed or interpolated. They are stored and retrieved as plain strings only. The architect should enforce `minLength: 1` to prevent empty string entries for fields the user explicitly supplies.

**SQL Injection:**
- All database reads and writes must use parameterised queries (e.g., SQLite `?` placeholders via the `sqlite3` module or an ORM). String interpolation into SQL queries is not permitted anywhere in the codebase.

**File I/O:**
- `brewlog export [path]`: The output path must be validated before use. Paths containing `..` components must be rejected to prevent directory traversal. The command must not write outside the user's intended directory.
- `brewlog import [path]`: The input path must be validated before reading. Paths containing `..` must be rejected. Files larger than 10MB must be rejected before parsing to prevent denial-of-service via large file inputs.
- All YAML parsing must use `yaml.safe_load()`. The use of `yaml.load()` without a safe loader is prohibited. This is the single most critical security requirement for file import.
- Imported data must be validated against the BrewSpec JSON Schema before any database writes. Schema validation is the application's first line of defense against malformed or malicious input files.

**No Secrets in Code:**
- No API keys, credentials, tokens, or secrets of any kind may appear in the source code or test fixtures.
- The database path (`~/.brewlog/brews.db`) is not sensitive and may appear in documentation and code.

---

## Dependencies

**Upstream:**
- `brewspec-v0.3` (done) — BrewLog CLI targets the v0.3 schema for storage and import/export. The live DB schema includes v0.3 fields (ey, equipment.grinder, equipment.brewer). The JSON Schema file from the BrewSpec repository is used for import and export validation.

**Downstream:**
- `brewlog-cli-v0.2` (ready_for_spec) — delete, list filtering, add flag parity, and carry-forward fixes depend on this v0.1.1 foundation.
- `commercial-brew-tracking-app` (backlog) — the migration path from CLI to the commercial product depends on BrewSpec-compliant export being implemented here.

**Runtime dependencies:**
- `click` — CLI framework
- `pyyaml` — YAML parsing and serialisation (safe_load only)
- `pydantic` — input validation models
- `jsonschema` — BrewSpec schema validation for import and export

---

## Success Metrics

Tied to `specs/strategy.md` Phase 1 success metrics:

- **Installation**: The CLI installs and the `brewlog` command is available after `pip install .`
- **Time to first brew**: A user can install BrewLog, log a brew, and view history in under 2 minutes (measured manually against the happy path)
- **Portability**: Export produces a file that passes BrewSpec schema validation without modification
- **Cross-platform**: All commands work correctly on macOS, Linux, and Windows with Python 3.11+
- **Reliability**: Test suite covers all acceptance criteria; 100% pass rate required before review sign-off
- **Security baseline**: No SQL injection vectors; safe YAML parsing throughout; path traversal rejected on export and import

**Learning metrics (not pass/fail, but to observe):**
- Which optional fields do users actually supply in `add`? (indicates what matters to them)
- Do users interact with export/import, or only add/list? (indicates whether portability is valued)

---

## Open Questions

- [x] **`brewlog add` interaction model** — Confirmed: interactive prompts for required fields; flags for optionals.
- [x] **Brew identifier** — Confirmed: SQLite auto-increment integer rowid.
- [x] **Export scope** — Confirmed: always exports all brews.
- [x] **Export format** — Confirmed: YAML default; `--format json` for JSON; CSV deferred.
- [x] **`brewlog list` truncation** — Confirmed: default last 20; `--limit N`; `--all`.
- [x] **ASCII art** — Confirmed: shown on bare `brewlog` invocation only; not on subcommands.
- [x] **Import duplicate handling** — Confirmed: no deduplication in v0.1 or v0.2. Re-importing the same file creates duplicate rows. This is documented behaviour in AC-33. Deduplication deferred indefinitely — no user demand observed.
- [ ] **`brewlog delete` range deletion** — Should `brewlog delete` support deleting all brews before a given date or matching a filter? Deferred to v0.3 if basic delete (AC-46) proves useful in practice.
