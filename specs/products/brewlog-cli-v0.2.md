# Product: BrewLog CLI v0.2

**Status:** Draft
**Priority:** P1 (High)
**Author:** product-manager
**Created:** 2026-02-20
**Last Updated:** 2026-02-20

---

## Problem Statement

BrewLog CLI v0.1.1 proves the core logging workflow: users can add, list, view, update, export, and import brews. Real usage has surfaced three categories of friction that v0.2 addresses.

**Bugs and spec deviations carried forward from the v0.1 review:**
- The `show` command sends its missing-ID error message to stdout instead of stderr. Scripts that pipe `brewlog show` output will receive diagnostic messages mixed into their data stream.
- The `export` command accepts paths without a file extension (e.g. `myfile` instead of `myfile.yaml`). The resulting file cannot be re-imported because format detection relies on the extension. This is a silent data-loss risk.
- A test assertion for the ASCII welcome screen checks only generic single characters (`(`, `.`, `_`) rather than a unique substring of the cup art, producing near-meaningless test coverage.

**Missing capability (confirmed real usage need):**
- Users cannot delete a brew. A logging mistake requires exporting the full database, editing the file, and re-importing — unreasonable friction for a tool designed for fast, frictionless use. `brewlog delete` is the highest-priority new feature in this version.

**Usability gaps:**
- The interactive brew type prompt is freeform text. Users must type `pour_over` or `immersion` exactly — a typo loops back with no guidance on what the valid values are. A numbered menu removes ambiguity entirely.
- `--ey`, `--grinder`, and `--brewer` are available on `brewlog update` but not on `brewlog add`. Users who know their equipment upfront must log the brew and immediately run `update` to fill in fields they had at logging time. This inconsistency has no justification.
- Once a user accumulates more than 20 brews, the default `list` output becomes noise. There is no way to narrow it without exporting. Filtering by type, rating, and date covers the most natural queries: "show me my best pours" and "what have I brewed this week."

Target personas:
- **Primary — The Home Brewer**: logs brews frequently, makes mistakes, and wants to find specific brews without scrolling through an unfiltered table.
- **Secondary — The Coffee Professional**: relies on clean export/import round-trips; the export extension bug directly breaks their portability workflow.
- **Tertiary — The Tool Builder**: the CLI is a reference implementation; correct stderr/stdout separation matters for scripting against it.

---

## User Stories

- As a **home brewer**, I want to delete a brew I logged by mistake so that my history stays accurate without requiring me to export and re-import everything.
- As a **home brewer**, I want the brew type prompt to show me a numbered menu so that I don't have to remember the exact enum values when logging interactively.
- As a **home brewer**, I want to supply `--ey`, `--grinder`, and `--brewer` when logging a new brew so that I can capture all the details in a single `add` command without needing a follow-up `update`.
- As a **home brewer**, I want to filter `brewlog list` by type, rating, and date so that I can find the brews I care about without scrolling through my entire history.
- As a **coffee professional**, I want `brewlog export` to reject paths without a valid file extension so that the exported file is always importable by any BrewSpec-compatible tool.
- As a **tool builder**, I want `brewlog show` to write error messages to stderr so that diagnostic output does not pollute a piped data stream.

---

## Acceptance Criteria

### Carry-forward fixes (bugs and spec deviations from v0.1 review)

- **AC-1**: When `brewlog show [id]` is called with an ID that does not exist in the database, the error message (e.g. `No brew found with ID 42.`) is written to stderr using `click.echo(..., err=True)`. The exit code remains 1. This corrects a v0.1 defect where this message was sent to stdout.

- **AC-2**: `brewlog export [path]` validates that the output path ends with `.yaml`, `.yml`, or `.json` before writing. If the path has any other extension or no extension at all, the command prints a clear error message to stderr (e.g. `Output path must end with .yaml, .yml, or .json.`) and exits with code 1. No file is written. This corrects a v0.1 defect where extensionless paths were silently accepted, producing files that could not be re-imported.

- **AC-3** _(test-only — no user-facing change)_: The test `test_no_args_shows_ascii_cup` is strengthened to assert on a unique substring of the ASCII coffee cup art (e.g. `.______.` or `( (`) rather than single-character matches (`(`, `.`, `_`). The updated assertion must be specific enough that it would fail if the cup art were replaced with arbitrary text containing those characters. No change to production code is required for this AC.

### `brewlog delete`

- **AC-4**: Running `brewlog delete [id]` where `id` is a positive integer displays a confirmation prompt before deleting: `Delete brew #N? [y/N]:`. The user must type `y` or `Y` to confirm. Any other input (including Enter on an empty response) cancels the operation, prints `Cancelled.` to stdout, and exits with code 0. No database change is made on cancellation.

- **AC-5**: On confirmed deletion, the command deletes the brew with the given ID from the database, prints `Brew #N deleted.` to stdout, and exits with code 0.

- **AC-6**: Running `brewlog delete [id]` with the `--force` flag skips the confirmation prompt and proceeds directly to deletion. On success, the command prints `Brew #N deleted.` and exits with code 0.

- **AC-7**: If the specified brew ID does not exist in the database, the command prints a clear error message to stderr (e.g. `No brew found with ID N.`) and exits with code 1. The database is not modified. This check is performed before the confirmation prompt is shown — the user is not asked to confirm deletion of a non-existent brew.

- **AC-8**: Running `brewlog delete` with no positional `id` argument prints a usage error and exits with a non-zero exit code. There is no default-to-latest behaviour for `delete` (unlike `update`).

- **AC-9**: `brewlog delete` does not exist as a command in v0.1.1. After implementation, running `brewlog` with no arguments (the welcome screen) must list `delete` alongside all other available commands.

### `brewlog add` — interactive brew type menu

- **AC-10**: When `brewlog add` is run without a `--type` flag (interactive mode), the brew type prompt is a numbered menu rather than a freeform text input. The menu is presented in this exact form:
  ```
  Brew type:
    1) espresso
    2) hybrid
    3) immersion
    4) pour_over
  Choice [1-4]:
  ```
  The options are listed in alphabetical order. The user types a number (1–4) and presses Enter to select.

- **AC-11**: If the user enters a value that is not a valid integer in the range 1–4 at the brew type menu (including empty input, non-numeric input, or an out-of-range integer), the menu is displayed again with a brief error message (e.g. `Invalid choice. Please enter a number between 1 and 4.`). The command does not exit; it re-prompts until a valid selection is made or the user cancels with Ctrl+C.

- **AC-12**: When `--type` is supplied as a flag on `brewlog add`, the numbered menu is not shown. The flag value is validated against the enum (`immersion`, `pour_over`, `espresso`, `hybrid`) as before. This AC confirms no regression to the flag-driven path.

- **AC-13**: The brew type stored in the database and produced in exports reflects the enum string value corresponding to the user's menu selection (e.g. selecting `1` stores `espresso`), not the numeric choice.

### `brewlog add` — flag parity

- **AC-14**: `brewlog add` supports the following three additional flags, matching the flags already available on `brewlog update`:
  - `--ey FLOAT` — extraction yield percentage
  - `--grinder TEXT` — freeform grinder name or description
  - `--brewer TEXT` — freeform brewer name or description

- **AC-15**: The `--ey` flag on `brewlog add` is validated against the same constraint as on `brewlog update`: value must be a number greater than zero. An invalid value produces a clear error message and exits with code 1 without writing to the database.

- **AC-16**: The `--grinder` and `--brewer` flags on `brewlog add` accept any non-empty freeform string. They are stored in the `equipment_grinder` and `equipment_brewer` columns respectively. No format constraint beyond non-empty applies.

- **AC-17**: When `--ey`, `--grinder`, and/or `--brewer` are supplied on `brewlog add` alongside valid required fields, the brew is written to the database in a single operation with all supplied values included. No follow-up `update` command is needed.

### `brewlog list` — filtering

- **AC-18**: Running `brewlog list --type TYPE` filters the output to brews where the `type` field exactly matches `TYPE`. `TYPE` must be one of the valid brew type enum values (`immersion`, `pour_over`, `espresso`, `hybrid`). An invalid value produces a clear error message and exits with code 1.

- **AC-19**: Running `brewlog list --rating N` filters the output to brews where the `rating` field exactly equals `N`. `N` must be an integer between 1 and 5 inclusive. An invalid value produces a clear error message and exits with code 1.

- **AC-20**: Running `brewlog list --since DATE` filters the output to brews with a `date` field on or after `DATE`. `DATE` must be in `YYYY-MM-DD` format. An invalid value produces a clear error message and exits with code 1. The comparison is performed at day granularity — the time component of the stored brew date is ignored when evaluating the filter.

- **AC-21**: The `--type`, `--rating`, and `--since` flags are combinable in a single command invocation. All supplied filters are applied together (logical AND): only brews matching every supplied filter are returned. Example: `brewlog list --type pour_over --rating 4 --since 2026-01-01` returns only brews that are `pour_over`, rated exactly 4, and dated on or after 2026-01-01.

- **AC-22**: When one or more filters are active and no brews match, the command prints a friendly message (e.g. `No brews match the given filters.`) and exits with code 0. It does not print an empty table.

- **AC-23**: Filter flags interact correctly with `--limit N` and `--all`. When `--limit N` is supplied alongside filter flags, the limit applies to the filtered result set (i.e. the most recent N brews among those matching the filters). When `--all` is supplied alongside filter flags, all matching brews are returned regardless of count.

- **AC-24**: When no filter flags are supplied, `brewlog list` behaviour is identical to v0.1.1: default last 20 brews, ordered by date descending. No regression.

---

## Scope

### In Scope

- Carry-forward fix: `brewlog show` missing-ID error message routed to stderr (`click.echo(..., err=True)`)
- Carry-forward fix: `brewlog export` path extension validation — reject paths not ending in `.yaml`, `.yml`, or `.json`
- Carry-forward test fix: `test_no_args_shows_ascii_cup` assertion strengthened to a unique substring of the cup art
- `brewlog delete [id]` — delete a brew by integer ID with confirmation prompt; `--force` to skip; no default-to-latest behaviour
- `brewlog add` — interactive brew type numbered menu replacing freeform prompt for the type field only
- `brewlog add` flag parity — `--ey`, `--grinder`, `--brewer` flags added to match `brewlog update`
- `brewlog list` filtering — `--type`, `--rating`, `--since` flags; combinable; interacts correctly with `--limit` and `--all`

### Out of Scope

- **`brewlog list --until DATE`** and date range filtering — `--since` provides recency filtering; an upper-bound filter is deferred to v0.3 pending evidence of real user need.
- **`brewlog delete` range/bulk deletion** — deleting all brews before a date or matching a filter is deferred to v0.3. Confirm single-delete is the right model before adding power-user variants.
- **`brewlog delete` default-to-latest** — unlike `update`, `delete` requires an explicit ID. Defaulting delete to the latest brew is too dangerous without additional confirmation complexity.
- **Interactive prompts for `--ey`, `--grinder`, `--brewer`** — these remain flag-only. Only the four required fields (`date`, `type`, `dose`, `water`) are prompted interactively. Adding optional field prompts would make the interactive flow too long for casual use.
- **Numbered menus for other prompted fields** — the brew type menu is specific to an enum field. Date, dose, and water have no fixed enumeration; freeform prompts remain correct for those fields.
- **CSV export** — lossy, not a valid BrewSpec format, no observed user demand. Deferred indefinitely.
- **Import deduplication** — documented as intentional absent behaviour in v0.1. No user demand. Deferred indefinitely.
- **Custom database path** — storage is fixed at `~/.brewlog/brews.db`. Deferred.
- **Single-brew export** — full database export remains the only export mode. Deferred.
- **Date format change (date-only `YYYY-MM-DD`)** — user feedback is that the full ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`) is onerous for a logging tool. This requires a BrewSpec schema change first and cannot be a CLI-only change. Tracked as a carry-forward item on the `brewspec-v0.4` task.
- **`brewlog update` changes** — the `update` command is unchanged in v0.2. All 16 flags are already present.

---

## Design Notes

### `brewlog delete` implementation

The `delete` command must check for existence before prompting for confirmation (AC-7). The lookup should be a parameterised SELECT before any DELETE is issued. The sequence is: validate `id` is a positive integer → SELECT to confirm existence → show confirmation prompt (unless `--force`) → DELETE with parameterised query. No row count trick as an existence proxy — an explicit SELECT makes the error message accurate.

The `--force` flag mirrors the pattern already established on `brewlog export` (overwrite confirmation). Consistent flag naming across commands matters for learnability.

### Interactive brew type menu

The menu replaces the `click.prompt()` call for the `type` field only. The implementation should use a custom loop with `click.prompt()` or `click.echo()` + `input()` — whichever produces the cleanest numbered menu output. The stored value is always the enum string, never the integer. The architect should decide the exact implementation approach.

Menu order is alphabetical: `espresso`, `hybrid`, `immersion`, `pour_over`. This is stable — the BrewSpec type enum does not change in v0.2.

### `brewlog list` filter implementation

Filters are applied via dynamic WHERE clause construction in the database query. The architect should use parameterised query building (e.g. building a list of conditions and a list of parameters, then joining with `AND`) rather than string interpolation. The `--since` filter must use a string comparison on the stored ISO 8601 date value at day granularity — strip the time component from the stored date before comparing, or compare against `DATE` + `T00:00:00Z` as a lower bound. The architect should choose the approach that is most correct given SQLite's text-based date storage.

All three filters apply before `--limit` is evaluated. The limit is applied to the already-filtered result set.

### Flag parity for `brewlog add`

The `--ey`, `--grinder`, and `--brewer` flags already have corresponding database columns (`ey`, `equipment_grinder`, `equipment_brewer`) and are fully handled in the `update` command. Adding them to `add` is a matter of wiring the flags through the `add` command's option declarations and the database INSERT call. No schema change required.

### Export path extension validation placement

The extension check belongs at the start of the `export` command, before any database reads or file I/O. The sequence should be: validate extension → check for existing file (overwrite prompt) → read database → validate schema → write file.

---

## Security Requirements

**Data sensitivity:**
- Brew logs are personal data (user habits, implicit time and location patterns). This does not change in v0.2.
- The `delete` command permanently removes a brew record. There is no undo. This is intentional and must be clearly communicated in the confirmation prompt. No audit log or soft-delete is required for v0.2.
- No new data types are introduced in v0.2. The three new `add` flags (`--ey`, `--grinder`, `--brewer`) map to fields already in the schema and handled by `update`.

**Input validation:**
- `brewlog delete [id]`: the `id` argument must be validated as a positive integer before any database operation. Non-integer, zero, and negative values must produce a clear error and exit with code 1 before any database access.
- `brewlog list` filter flags: all three filter values must be validated before constructing the database query. `--type` must be validated against the enum. `--rating` must be validated as an integer between 1 and 5. `--since` must be validated as a parseable `YYYY-MM-DD` date. An invalid filter value must never reach the database query.
- `--ey` on `brewlog add`: validated as a number greater than zero, consistent with `brewlog update`.
- `--grinder` and `--brewer` on `brewlog add`: freeform strings; must not be empty (consistent with BrewSpec `minLength: 1`). Stored and retrieved as plain strings only — never executed or interpolated.

**SQL injection:**
- `brewlog delete`: the DELETE statement must use a parameterised query (`DELETE FROM brews WHERE id = ?`). String interpolation is not permitted.
- `brewlog list` filtering: dynamic WHERE clause construction is the highest-risk surface in this version. The condition strings must be static (e.g. `type = ?`, `rating = ?`, `date >= ?`) and all values must be passed as parameters. Under no circumstances should a filter value be interpolated into the SQL string. The architect must design the query-building pattern to make injection structurally impossible.

**File I/O:**
- No new file I/O surfaces are introduced in v0.2. The export extension validation (AC-2) reduces file I/O risk by preventing creation of files that lack a format indicator. Existing path traversal protection (`..` rejection) and import file size limit remain in place from v0.1.

**No secrets in code:**
- No API keys, credentials, tokens, or secrets may appear in source code or test fixtures.

---

## Dependencies

**Upstream:**
- `brewlog-cli-v0.1.1` (done) — v0.2 is a direct iteration. The existing database schema already includes `ey`, `equipment_grinder`, and `equipment_brewer` columns. No schema migration is needed. All v0.1.1 commands and behaviours are the baseline.
- `brewspec-v0.3` (done) — the JSON Schema used for export validation. No change to the schema dependency in v0.2.

**Downstream:**
- `commercial-brew-tracking-app` (backlog) — relies on BrewSpec-compliant export. The export extension validation fix in v0.2 improves the reliability of the round-trip that the commercial app's import path will depend on.
- `brewspec-v0.4` (backlog) — the date format carry-forward item (date-only `YYYY-MM-DD`) is tracked on the `brewspec-v0.4` task and will require a corresponding BrewLog CLI update when the schema change ships.

---

## Success Metrics

Tied to `specs/strategy.md` Phase 1 success metrics:

- **Correctness**: All three carry-forward bugs are resolved. `brewlog show` error goes to stderr. `brewlog export` rejects extensionless paths. `test_no_args_shows_ascii_cup` asserts on a unique substring.
- **Delete reliability**: `brewlog delete` with confirmation and `--force` passes all AC tests. A brew deleted by ID is confirmed absent from the database and from subsequent `brewlog list` output.
- **Interactive usability**: The brew type numbered menu correctly maps numeric selection to the enum string. Invalid selections re-prompt. Flag-driven `--type` is unaffected.
- **Flag parity**: `brewlog add --ey`, `--grinder`, `--brewer` store values correctly and appear in export output. Behaviour is consistent with `brewlog update` for the same flags.
- **Filtering**: All three filter flags work individually and in combination. Filters interact correctly with `--limit` and `--all`. Empty-result case produces a friendly message.
- **Test suite**: 100% pass rate required before reviewer sign-off. All new ACs must have corresponding tests written first (TDD).
- **Security baseline**: No SQL injection vectors in dynamic filter construction. Parameterised DELETE. No regression on existing path traversal protection.

---

## Open Questions

- [x] **Combinable filters** — Confirmed: `--type`, `--rating`, and `--since` must be combinable in a single invocation. Applied as logical AND. Limit applies to the filtered result set.
- [x] **Test assertion AC** — Confirmed: add as an explicit AC (AC-3) so it is tracked and not dropped.
- [x] **`brewlog delete` confirmed** — Confirmed in scope with confirmation prompt and `--force` flag.
- [x] **Interactive brew type menu** — Confirmed: numbered menu replacing freeform prompt for brew type only. Other required fields keep current prompt style.
- [x] **`brewlog add` flag parity** — Confirmed: `--ey`, `--grinder`, `--brewer` added to `add`.
- [x] **Date format (YYYY-MM-DD)** — Deferred. User feedback confirms the current ISO 8601 UTC datetime format is too onerous for a logging tool. A date-only format would be more natural but requires a BrewSpec schema change first. This cannot be a CLI-only change. Tracked as a carry-forward item on `brewspec-v0.4`. The corresponding CLI change will follow in the BrewLog CLI version that targets the updated schema.
