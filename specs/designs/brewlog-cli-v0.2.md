# Technical Design: BrewLog CLI v0.2

**Status:** Complete
**Author:** architect
**Created:** 2026-02-21
**Spec source:** `specs/products/brewlog-cli-v0.2.md`
**Baseline implementation:** `github.com/coffee-standards/brewspec` (tag: `brewlog-v0.1.1`)

---

## 1. Overview

v0.2 makes six targeted changes to the v0.1.1 codebase. No schema migration is needed — all DB columns exist. No new Python dependencies are required.

**What changes:**

| Change | Files touched | ACs |
|--------|--------------|-----|
| `show` stderr fix | `commands/show.py` | AC-1 |
| `export` extension validation | `serialise.py` | AC-2 |
| ASCII cup test assertion | `tests/test_cmd_welcome.py` | AC-3 |
| New `delete` command | `commands/delete.py`, `db.py`, `cli.py`, `tests/test_cmd_delete.py` | AC-4 to AC-9 |
| `add` numbered brew type menu | `commands/add.py` | AC-10, AC-11, AC-12, AC-13 |
| `add` flag parity (`--ey`, `--grinder`, `--brewer`) | `commands/add.py` | AC-14, AC-15, AC-16, AC-17 |
| `list` filtering (`--type`, `--rating`, `--since`) | `commands/list_.py`, `db.py`, `tests/test_cmd_list_filter.py` | AC-18 to AC-24 |

**What does not change:** `models.py`, `schema.py`, `commands/update.py`, `commands/import_.py`, `commands/export.py` (other than what is noted for serialise.py), DB schema, `pyproject.toml`.

---

## 2. File-by-file changes

### 2.1 `commands/show.py` — stderr fix (AC-1)

**What changes:** Line 36. The `click.echo` call that prints the not-found error currently omits `err=True`. Add `err=True`.

**Before:**
```python
click.echo(f"No brew found with ID {id}.")
```

**After:**
```python
click.echo(f"No brew found with ID {id}.", err=True)
```

No other changes to this file. Exit code stays `sys.exit(1)`.

---

### 2.2 `serialise.py` — export extension validation (AC-2)

**What changes:** `validate_export_path()` gains an extension check inserted immediately after the `..` check and before the parent-directory check.

The valid extensions are `.yaml`, `.yml`, `.json`. The check uses `pathlib.Path.suffix` (case-sensitive; lowercase only — uppercase extensions such as `.YAML` are rejected with the same error message, which is consistent with the existing import path detection).

**Logic to add** inside `validate_export_path`, after the `..` rejection block:

```python
VALID_EXPORT_EXTENSIONS = {".yaml", ".yml", ".json"}
if p.suffix not in VALID_EXPORT_EXTENSIONS:
    click.echo(
        "Error: output path must end with .yaml, .yml, or .json.",
        err=True,
    )
    sys.exit(1)
```

Placement: after the `".." in p.parts` check, before the `p.parent.exists()` check. This matches the ordering stated in the spec: validate extension, then validate parent directory.

No other changes to `serialise.py`.

---

### 2.3 `tests/test_cmd_welcome.py` — strengthen ASCII cup assertion (AC-3)

**What changes:** `test_no_args_shows_ascii_cup` only. Replace the weak assertion:

```python
assert "(" in result.output or "." in result.output or "_" in result.output
```

with a specific substring unique to the cup art in `cli.py`:

```python
assert ".______." in result.output
```

The string `.______."` appears in the `ASCII_CUP` constant in `cli.py` (line `  .______.`) and would not appear in arbitrary output. No change to production code.

---

### 2.4 `commands/delete.py` — new file (AC-4 to AC-9)

Create `brewlog/commands/delete.py`. Full command definition:

```
Command name:  delete
Positional argument:  id  (type=int, required=True)
Flags:  --force  (is_flag=True, default=False)
```

**Execution sequence (mirrors spec design note):**

1. Validate `id > 0`. If `id <= 0`: print `Error: brew ID must be a positive integer.` to stderr, `sys.exit(1)`. (Click's `type=int` already handles non-integer input with its own usage error — no manual check needed for that.)
2. Open DB connection.
3. Call `db.get_brew(id, conn)` — SELECT before DELETE. If `None`: print `No brew found with ID {id}.` to stderr, `sys.exit(1)`. Close connection.
4. If not `--force`: call `click.confirm(f"Delete brew #{id}?", default=False)`. On `False` (any input other than `y`/`Y`): print `Cancelled.` to stdout, `sys.exit(0)`.
5. Call `db.delete_brew(id, conn)`.
6. Print `Brew #{id} deleted.` to stdout, `sys.exit(0)`.

**Click `confirm` behaviour note:** `click.confirm(..., default=False)` maps Enter (empty input) to `False`, which produces a `click.exceptions.Abort` or returns `False`. Use the return-value form (not `abort=True`) so we can print `Cancelled.` ourselves:

```python
confirmed = click.confirm(f"Delete brew #{id}?", default=False)
if not confirmed:
    click.echo("Cancelled.")
    return
```

This satisfies AC-4 (any input other than `y`/`Y` cancels, prints `Cancelled.`, exits 0) because `click.confirm` with `default=False` treats Enter as `n`.

---

### 2.5 `db.py` — two new functions (AC-4, AC-5, AC-18 to AC-24)

Add `delete_brew` and `list_brews_filtered` after the existing `update_brew` function.

**`delete_brew(brew_id, conn) -> bool`**

```python
def delete_brew(brew_id: int, conn: sqlite3.Connection) -> bool:
    cursor = conn.execute("DELETE FROM brews WHERE id = ?", (brew_id,))
    conn.commit()
    return cursor.rowcount > 0
```

Notes:
- Uses `?` placeholder — no interpolation.
- Returns `True` if a row was deleted, `False` if not found (existence is checked by the command before calling this, but the return value allows the command to guard against a race condition).
- Does not check existence itself; that is the command's responsibility (per the spec's "explicit SELECT" design note).

**`list_brews_filtered(conn, limit, all_rows, brew_type, since, rating) -> list`**

See Section 4 for the full design of this function.

---

### 2.6 `cli.py` — register delete command (AC-9)

Import and register the new command:

```python
from brewlog.commands.delete import delete
# ...
cli.add_command(delete)
```

`delete` is registered with its natural name (`"delete"`). No alias needed.

After this change, `brewlog` with no arguments will list `delete` alongside the other commands in the help text, satisfying AC-9.

---

### 2.7 `commands/add.py` — numbered brew type menu (AC-10 to AC-13)

**Replace `_prompt_brew_type()`** with a new implementation that presents a numbered menu. The old function is removed; the new one takes its place.

The menu order is alphabetical, which produces this fixed mapping:

| Number | Enum string |
|--------|------------|
| 1 | espresso |
| 2 | hybrid |
| 3 | immersion |
| 4 | pour_over |

This mapping must be derived programmatically from `sorted(BREW_TYPE_ENUM)` at function definition time so that if the enum ever changes, the menu stays correct. However, the order and content of the enum are stable in v0.2 — the numbered range `1-4` is correct.

New `_prompt_brew_type()` implementation pattern:

```python
def _prompt_brew_type() -> str:
    """Prompt for brew type with a numbered menu. Re-prompts on invalid input."""
    options = sorted(BREW_TYPE_ENUM)  # alphabetical: espresso, hybrid, immersion, pour_over
    while True:
        click.echo("Brew type:")
        for i, opt in enumerate(options, start=1):
            click.echo(f"  {i}) {opt}")
        raw = click.prompt("Choice [1-4]", prompt_suffix=": ")
        try:
            choice = int(raw)
        except ValueError:
            click.echo(f"  Invalid choice. Please enter a number between 1 and {len(options)}.")
            continue
        if not (1 <= choice <= len(options)):
            click.echo(f"  Invalid choice. Please enter a number between 1 and {len(options)}.")
            continue
        return options[choice - 1]
```

**The `--type` flag path is unchanged.** When `brew_type` is not `None` (supplied as a flag), `_prompt_brew_type()` is not called. The existing `BrewInput` Pydantic validation rejects invalid enum values via `sys.exit(1)`. No change to that path.

**Stored value:** `options[choice - 1]` is the enum string (e.g. `"espresso"`), not the integer. This is passed directly to `BrewInput(type=brew_type)` and stored verbatim in the `type` column. AC-13 is satisfied structurally.

**Interactive test input change:** Existing interactive tests pass `"pour_over\n"` as the type input. After this change, the menu requires a number. Tests that drive the interactive path must be updated to pass `"4\n"` (for `pour_over`) instead of `"pour_over\n"`. This affects `test_cmd_add.py` tests that use `runner.invoke(cli, ["add"], input="...")`. The developer must update those inputs as part of this task.

---

### 2.8 `commands/add.py` — flag parity for `--ey`, `--grinder`, `--brewer` (AC-14 to AC-17)

**Add three new `@click.option` decorators** to the `add` command, matching the signatures in `update.py`:

```python
@click.option("--ey",      "ey",      type=float, default=None,
              help="Extraction yield percentage (> 0).")
@click.option("--grinder", "grinder", type=str,   default=None,
              help="Grinder name or description.")
@click.option("--brewer",  "brewer",  type=str,   default=None,
              help="Brewer/dripper name or description.")
```

**Add the three parameters to the `add` function signature:**

```python
def add(
    date, brew_type, dose, water_weight,
    method, temp, grind, duration, rating, notes,
    roast_date, coffee_type, origin, varietal, process,
    water_ppm, tds,
    ey, grinder, brewer,   # <-- new
) -> None:
```

**Add validation** after the existing `tds` validation (immediately before the Pydantic model construction block). Mirror the pattern from `update.py`:

```python
if ey is not None and ey <= 0:
    click.echo("Error: ey must be greater than 0", err=True)
    sys.exit(1)

if grinder is not None and (len(grinder.strip()) == 0 or len(grinder) > 100):
    click.echo("Error: grinder must be 1–100 characters", err=True)
    sys.exit(1)

if brewer is not None and (len(brewer.strip()) == 0 or len(brewer) > 100):
    click.echo("Error: brewer must be 1–100 characters", err=True)
    sys.exit(1)
```

**Pass values through to `BrewInput`:**

`BrewInput` already has `ey: Optional[float]` and `equipment: Optional[EquipmentInput]`. Wire the new flags into the existing model construction:

```python
equipment_obj = None
if grinder is not None or brewer is not None:
    try:
        equipment_obj = EquipmentInput(grinder=grinder, brewer=brewer)
    except ValidationError as exc:
        click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        sys.exit(1)

brew = BrewInput(
    ...
    tds=tds,
    ey=ey,          # <-- add
    ...
    equipment=equipment_obj,   # <-- add
)
```

`BrewInput` already has `ey` as a direct field, so it is passed directly. `grinder` and `brewer` route through `EquipmentInput`. No changes to `BrewInput` or `EquipmentInput` in `models.py` are needed.

**Also import `EquipmentInput`** in the import line at the top of `add.py`:

```python
from brewlog.models import BrewInput, CoffeeInput, WaterInput, EquipmentInput, DATE_PATTERN, BREW_TYPE_ENUM
```

---

### 2.9 `commands/list_.py` — filter flags (AC-18 to AC-24)

**Add three new `@click.option` declarations:**

```python
@click.option(
    "--type", "filter_type",
    type=str, default=None,
    help="Filter by brew type (immersion, pour_over, espresso, hybrid).",
)
@click.option(
    "--rating", "filter_rating",
    type=int, default=None,
    help="Filter by rating (1-5).",
)
@click.option(
    "--since", "filter_since",
    type=str, default=None,
    help="Filter to brews on or after DATE (YYYY-MM-DD).",
)
```

**Add parameters to `list_cmd` signature:**

```python
def list_cmd(limit: int, show_all: bool, filter_type, filter_rating, filter_since) -> None:
```

**Add input validation** before the DB call. Validation must occur before any database access (AC per spec security requirements). Errors are written to stderr with `err=True`:

```python
from brewlog.models import BREW_TYPE_ENUM
import re as _re

_SINCE_PATTERN = _re.compile(r"^\d{4}-\d{2}-\d{2}$")

# In list_cmd:
if filter_type is not None and filter_type not in BREW_TYPE_ENUM:
    click.echo(
        f"Error: --type must be one of: {sorted(BREW_TYPE_ENUM)}",
        err=True,
    )
    sys.exit(1)

if filter_rating is not None and not (1 <= filter_rating <= 5):
    click.echo("Error: --rating must be an integer between 1 and 5.", err=True)
    sys.exit(1)

if filter_since is not None:
    if not _SINCE_PATTERN.match(filter_since):
        click.echo("Error: --since must be in YYYY-MM-DD format.", err=True)
        sys.exit(1)
```

**Replace the `db.list_brews` call** with `db.list_brews_filtered`:

```python
rows = db.list_brews_filtered(
    conn,
    limit=limit,
    all_rows=show_all,
    brew_type=filter_type,
    rating=filter_rating,
    since=filter_since,
)
```

**Replace the empty-result message** for the filtered case:

```python
if not rows:
    if filter_type is not None or filter_rating is not None or filter_since is not None:
        click.echo("No brews match the given filters.")
    else:
        click.echo("No brews logged yet. Run 'brewlog add' to get started.")
    return
```

**BREW_TYPE_ENUM import:** Add to the import line:

```python
from brewlog.models import BREW_TYPE_ENUM
```

---

### 2.10 `tests/test_cmd_delete.py` — new file

See Section 5.1 for the full test case list.

---

### 2.11 `tests/test_cmd_list_filter.py` — new file

See Section 5.2 for the full test case list.

---

## 3. Interface design

### 3.1 `brewlog show [id]` — stderr fix

No interface change. The error message text is unchanged. Only the stream changes.

- Error message: `No brew found with ID {id}.` — written to **stderr** (previously stdout)
- Exit code: 1 (unchanged)

### 3.2 `brewlog export [path]`

New validation added before any DB access:

- If path lacks `.yaml`, `.yml`, or `.json` extension: print `Error: output path must end with .yaml, .yml, or .json.` to **stderr**, exit 1, no file written.

All other behaviour is unchanged.

### 3.3 `brewlog delete [id]`

```
Usage: brewlog delete [OPTIONS] ID

  Delete a brew by ID.

Arguments:
  ID  Brew ID to delete (positive integer).  [required]

Options:
  --force  Skip confirmation prompt.
  --help   Show this message and exit.
```

**Happy path (interactive):**
```
$ brewlog delete 3
Delete brew #3? [y/N]: y
Brew #3 deleted.
```

**Happy path (`--force`):**
```
$ brewlog delete 3 --force
Brew #3 deleted.
```

**Cancelled:**
```
$ brewlog delete 3
Delete brew #3? [y/N]:
Cancelled.
```
(Enter key maps to `N`; exit code 0)

**ID not found:**
```
$ brewlog delete 99
No brew found with ID 99.
```
Written to stderr. Exit code 1. Confirmation prompt is NOT shown.

**No ID supplied:**
```
$ brewlog delete
Error: Missing argument 'ID'.
```
Click's built-in usage error. Exit non-zero.

**Non-positive ID (`--type=int` handles non-integers via Click's own error):**
The command adds a guard: if `id <= 0`, print `Error: brew ID must be a positive integer.` to stderr, exit 1.

### 3.4 `brewlog add` — numbered brew type menu

Interactive mode only (when `--type` not supplied):

```
Brew type:
  1) espresso
  2) hybrid
  3) immersion
  4) pour_over
Choice [1-4]:
```

On invalid input (empty, non-numeric, out of range):
```
  Invalid choice. Please enter a number between 1 and 4.
```
Menu is re-displayed. Command does not exit.

On valid input (`1`–`4`): the corresponding enum string is used and the prompt sequence continues.

When `--type pour_over` is supplied as a flag: menu is not shown. Flag value validated by Pydantic as before.

### 3.5 `brewlog add` — new flags

```
--ey FLOAT      Extraction yield percentage (> 0).
--grinder TEXT  Grinder name or description.
--brewer TEXT   Brewer/dripper name or description.
```

Error messages (stderr, exit 1):
- `--ey` invalid: `Error: ey must be greater than 0`
- `--grinder` empty or too long: `Error: grinder must be 1–100 characters`
- `--brewer` empty or too long: `Error: brewer must be 1–100 characters`

### 3.6 `brewlog list` — filter flags

```
--type TYPE     Filter by brew type (immersion, pour_over, espresso, hybrid).
--rating N      Filter by rating exactly equal to N (1-5).
--since DATE    Filter to brews on or after DATE (YYYY-MM-DD).
```

These combine with the existing `--limit N` and `--all` flags.

Error messages (stderr, exit 1):
- Invalid `--type`: `Error: --type must be one of: ['espresso', 'hybrid', 'immersion', 'pour_over']`
- Invalid `--rating`: `Error: --rating must be an integer between 1 and 5.`
- Invalid `--since`: `Error: --since must be in YYYY-MM-DD format.`

No-match message (stdout, exit 0):
- `No brews match the given filters.`

The existing `No brews logged yet. Run 'brewlog add' to get started.` message is shown only when no filters are active and the DB is empty.

---

## 4. DB layer changes

### 4.1 `delete_brew(brew_id, conn) -> bool`

```python
def delete_brew(brew_id: int, conn: sqlite3.Connection) -> bool:
    """
    Delete the brew with the given ID.
    Returns True if a row was deleted, False if no matching row.
    Uses parameterised ? placeholder — no string interpolation.
    """
    cursor = conn.execute("DELETE FROM brews WHERE id = ?", (brew_id,))
    conn.commit()
    return cursor.rowcount > 0
```

The command performs an existence check (via `get_brew`) before calling this. The `bool` return is a safety net for race conditions but is not the primary existence check mechanism.

### 4.2 `list_brews_filtered(conn, limit, all_rows, brew_type, rating, since) -> list`

**Dynamic WHERE clause strategy:**

Build two parallel lists: `conditions` (list of SQL clause strings with `?` placeholders) and `params` (list of values). Join conditions with `AND`. All filter values travel as parameters — never interpolated into the SQL string.

```python
def list_brews_filtered(
    conn: sqlite3.Connection,
    limit: int = 20,
    all_rows: bool = False,
    brew_type: str | None = None,
    rating: int | None = None,
    since: str | None = None,
) -> list[sqlite3.Row]:
    """
    Return brews ordered by date descending, with optional filters.
    All filter values are passed as SQL parameters — no string interpolation.
    If no filters are supplied, behaviour is identical to list_brews().
    """
    conditions: list[str] = []
    params: list = []

    if brew_type is not None:
        conditions.append("type = ?")
        params.append(brew_type)

    if rating is not None:
        conditions.append("rating = ?")
        params.append(rating)

    if since is not None:
        # since is YYYY-MM-DD; stored dates are YYYY-MM-DDTHH:MM:SSZ.
        # Comparison: date >= since + "T00:00:00Z" ensures day-granularity
        # correctness using SQLite's lexicographic text comparison on ISO 8601.
        conditions.append("date >= ?")
        params.append(since + "T00:00:00Z")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    if all_rows:
        sql = f"SELECT * FROM brews {where_clause} ORDER BY date DESC"
        cursor = conn.execute(sql, params)
    else:
        sql = f"SELECT * FROM brews {where_clause} ORDER BY date DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(sql, params)

    return cursor.fetchall()
```

**Why `since + "T00:00:00Z"` rather than a date function:**

SQLite stores dates as `TEXT` in `YYYY-MM-DDTHH:MM:SSZ` format. ISO 8601 strings sort lexicographically correctly. Appending `T00:00:00Z` to the user-supplied `YYYY-MM-DD` value produces a valid lower-bound string for the comparison `date >= ?`. This is more portable than `DATE(date) >= ?` (which would require SQLite's date function to correctly parse the `Z` suffix) and avoids a full table scan that might result from a function applied to the indexed `date` column.

**Interaction with `--limit` and `--all`:**

The `LIMIT ?` clause is applied after the `WHERE` clause in the SQL. This means the limit applies to the already-filtered result set (AC-23). When `--all` is supplied, no `LIMIT` is added.

**Backward compatibility:** When all three filter arguments are `None`, `conditions` is empty, `where_clause` is `""`, and the query is equivalent to the existing `list_brews()` query. The `list_cmd` command calls `list_brews_filtered` in all cases; `list_brews` is retained for backward compatibility but is no longer called by `list_cmd`.

**SQL safety note:** The `WHERE` and `ORDER BY` and `LIMIT` keywords are static strings. Only filter values are parameterised. The `where_clause` string contains only static condition strings (`"type = ?"`, `"rating = ?"`, `"date >= ?"`). No user input is ever interpolated into the SQL string.

---

## 5. Test strategy

All new tests use the existing fixture pattern from `conftest.py`: `runner_with_db` fixture with `monkeypatch.setattr(db_module, "DB_PATH", ...)`. Helper functions insert brews directly via `db_module.insert_brew()` or `db_module.get_connection()`.

### 5.1 `tests/test_cmd_delete.py`

AC mapping is listed with each test. Tests are written in the order of the TDD red phase.

```
test_delete_no_id_exits_nonzero
  AC-8: invoke ["delete"] with no ID → exit_code != 0

test_delete_nonexistent_id_stderr
  AC-7: invoke ["delete", "999"] (empty DB) → "No brew found with ID 999" in result.output (via mix_stderr=False: check result.stderr or use runner with mix_stderr=False)

test_delete_nonexistent_id_exit_1
  AC-7: same invocation → exit_code == 1

test_delete_nonexistent_id_no_prompt
  AC-7: "Delete" must NOT appear in stdout (prompt not shown for nonexistent brew)
  Use runner with mix_stderr=False; confirm prompt text absent from stdout

test_delete_cancels_on_n
  AC-4: insert 1 brew, invoke ["delete", "1"], input="n\n"
  → "Cancelled." in result.output, exit_code == 0

test_delete_cancels_on_empty_enter
  AC-4: insert 1 brew, invoke ["delete", "1"], input="\n"
  → "Cancelled." in result.output, exit_code == 0

test_delete_cancels_on_arbitrary_input
  AC-4: insert 1 brew, invoke ["delete", "1"], input="no\n"
  → "Cancelled." in result.output, exit_code == 0

test_delete_cancels_no_db_change
  AC-4: insert 1 brew, invoke ["delete", "1"], input="n\n"
  → db still has 1 brew (verify via db.get_brew(1, conn) is not None)

test_delete_confirms_on_y
  AC-5: insert 1 brew, invoke ["delete", "1"], input="y\n"
  → "Brew #1 deleted." in result.output, exit_code == 0

test_delete_confirms_on_capital_Y
  AC-5: insert 1 brew, invoke ["delete", "1"], input="Y\n"
  → "Brew #1 deleted." in result.output, exit_code == 0

test_delete_removes_from_db
  AC-5: insert 1 brew, invoke ["delete", "1"], input="y\n"
  → db.get_brew(1, conn) is None after deletion

test_delete_force_skips_prompt
  AC-6: insert 1 brew, invoke ["delete", "1", "--force"]
  → "Brew #1 deleted." in result.output, exit_code == 0
  → no "Delete brew" prompt text in output

test_delete_force_removes_from_db
  AC-6: insert 1 brew, invoke ["delete", "1", "--force"]
  → db.get_brew(1, conn) is None after deletion

test_delete_force_nonexistent_id
  AC-7 + AC-6 interaction: invoke ["delete", "999", "--force"] (empty DB)
  → error message to stderr, exit_code == 1
  → no deletion message in stdout

test_delete_non_positive_id_zero
  AC-8 + security: invoke ["delete", "0"]
  → exit_code == 1 (either Click type error or our guard)

test_delete_non_positive_id_negative
  AC-8 + security: invoke ["delete", "-1"]
  → exit_code != 0

test_delete_shown_in_welcome_screen
  AC-9: invoke [] (no args, no DB needed since welcome doesn't touch DB)
  → "delete" in result.output

test_delete_confirmation_prompt_format
  AC-4: insert 1 brew, invoke ["delete", "1"], input="n\n"
  → "Delete brew #1?" in result.output (exact prompt substring)
```

**Note on stderr testing:** Use `runner = CliRunner(mix_stderr=False)` for tests that assert on stderr content vs. stdout content. The default `CliRunner()` mixes streams. Tests that only check `result.output` and `result.exit_code` can use the default runner. The `runner_with_db` fixture can use `mix_stderr=False` for the delete tests that need stream separation.

### 5.2 `tests/test_cmd_list_filter.py`

AC mapping is listed with each test.

```
_populate_typed_brews(db_path)
  Helper: insert one brew of each type (pour_over, immersion, espresso, hybrid)
  with different dates: 2026-01-10, 2026-01-20, 2026-02-01, 2026-02-15
  All with rating=3 except pour_over which gets rating=5.

test_filter_by_type_returns_matching_only
  AC-18: invoke ["list", "--type", "pour_over"] with 4 brews of different types
  → exactly 1 data row in output, containing "pour_over"

test_filter_by_type_excludes_others
  AC-18: invoke ["list", "--type", "espresso"]
  → "pour_over" not in output data rows

test_filter_by_type_invalid_exits_1
  AC-18: invoke ["list", "--type", "drip"]
  → exit_code == 1

test_filter_by_type_invalid_message
  AC-18: invoke ["list", "--type", "drip"]
  → error message in output (mix_stderr=False: check stderr)

test_filter_by_rating_returns_matching_only
  AC-19: insert 3 brews: rating=3, rating=4, rating=5
  invoke ["list", "--rating", "4"]
  → exactly 1 data row, and output contains "4"

test_filter_by_rating_invalid_zero
  AC-19: invoke ["list", "--rating", "0"] → exit_code == 1

test_filter_by_rating_invalid_six
  AC-19: invoke ["list", "--rating", "6"] → exit_code == 1

test_filter_by_rating_invalid_message
  AC-19: invoke ["list", "--rating", "0"] → error message present

test_filter_by_since_returns_on_or_after
  AC-20: insert brews at 2026-01-10, 2026-02-01, 2026-02-15
  invoke ["list", "--since", "2026-02-01"]
  → 2 data rows (2026-02-01 and 2026-02-15 both qualify)
  → "2026-01-10" not in output

test_filter_by_since_exact_date_included
  AC-20: insert brew at exactly 2026-02-01T08:30:00Z
  invoke ["list", "--since", "2026-02-01"]
  → brew appears (date matches exactly at day boundary)

test_filter_by_since_invalid_format
  AC-20: invoke ["list", "--since", "01-01-2026"] → exit_code == 1

test_filter_by_since_invalid_message
  AC-20: invoke ["list", "--since", "not-a-date"] → error message present

test_filter_combined_type_and_rating
  AC-21: insert pour_over/rating=5, pour_over/rating=3, immersion/rating=5
  invoke ["list", "--type", "pour_over", "--rating", "5"]
  → exactly 1 data row

test_filter_combined_type_and_since
  AC-21: insert pour_over/2026-01-10, pour_over/2026-02-15, immersion/2026-02-15
  invoke ["list", "--type", "pour_over", "--since", "2026-02-01"]
  → exactly 1 data row (pour_over from 2026-02-15 only)

test_filter_combined_all_three
  AC-21: insert multiple brews across types/ratings/dates
  invoke ["list", "--type", "pour_over", "--rating", "5", "--since", "2026-02-01"]
  → only matching brews appear

test_filter_no_match_friendly_message
  AC-22: invoke ["list", "--type", "espresso"] with only pour_over brews
  → "No brews match the given filters." in result.output, exit_code == 0

test_filter_no_match_no_table
  AC-22: same as above → header separator ("---") not in output

test_filter_with_limit
  AC-23: insert 5 pour_over brews and 5 immersion brews (total 10)
  invoke ["list", "--type", "pour_over", "--limit", "3"]
  → exactly 3 data rows, all "pour_over"

test_filter_with_all
  AC-23: insert 5 pour_over brews and 5 immersion brews (total 10)
  invoke ["list", "--type", "pour_over", "--all"]
  → exactly 5 data rows, all "pour_over"

test_filter_no_flags_unchanged_behaviour
  AC-24: insert 25 brews
  invoke ["list"] (no filter flags)
  → 20 data rows (default limit), "No brews logged yet" not in output
  This confirms no regression to the unfiltered path.
```

### 5.3 Modifications to existing test files

**`tests/test_cmd_welcome.py`**
- `test_no_args_shows_ascii_cup`: replace weak assertion with `assert ".______." in result.output` (AC-3).
- `test_no_args_shows_help`: add `assert "delete" in result.output` (AC-9).
- No other changes.

**`tests/test_cmd_add.py`** — interactive path input changes
The `_prompt_brew_type` replacement means any test that drives the interactive path and passes `"pour_over\n"` as type input must now pass `"4\n"` (pour_over is option 4). The developer must audit and update all affected `input=` strings in interactive test cases. This affects: `test_add_interactive_accepts_default_date`, `test_add_interactive_shows_date_prompt`, `test_add_interactive_reprompts_invalid_type`, `test_add_interactive_reprompts_invalid_dose`, `test_add_interactive_shows_tip`, and `test_add_with_flags_no_tip` (the last one is flag-driven and unaffected).

The developer must also add tests to `test_cmd_add.py` for the three new flags (AC-14 to AC-17):
- `test_add_ey_flag_stored` — `--ey 22.5` round-trips through DB
- `test_add_ey_invalid_zero` — `--ey 0` → exit 1
- `test_add_ey_invalid_negative` — `--ey -1` → exit 1
- `test_add_grinder_flag_stored` — `--grinder "Comandante C40"` round-trips
- `test_add_grinder_empty_string` — `--grinder ""` → exit 1
- `test_add_brewer_flag_stored` — `--brewer "Hario V60-02"` round-trips
- `test_add_brewer_empty_string` — `--brewer ""` → exit 1
- `test_add_ey_grinder_brewer_together` — all three supplied → stored in single INSERT (AC-17)

**`tests/test_cmd_show.py`**
- `test_show_not_found_message`: existing assertion `assert "No brew found with ID 999" in result.output` is currently checking `result.output`. After the fix, the message goes to stderr. If the runner is default (`mix_stderr=False` is NOT the default — the default `CliRunner()` mixes stderr into stdout), this test still passes. However, to properly test the stderr routing (AC-1), add a new test:
  - `test_show_not_found_goes_to_stderr` — use `CliRunner(mix_stderr=False)`, assert message in `result.stderr` and absent from `result.output` (stdout).

**`tests/test_cmd_export.py`**
- Add test for the extension validation fix (AC-2):
  - `test_export_no_extension_rejected` — invoke with `"myfile"` → exit 1, error message present
  - `test_export_wrong_extension_rejected` — invoke with `"myfile.csv"` → exit 1
  - `test_export_valid_extension_yaml` — invoke with `"myfile.yaml"` on a populated DB → exit 0 (regression check)
  - `test_export_valid_extension_yml` — invoke with `"myfile.yml"` → exit 0
  - `test_export_valid_extension_json` — invoke with `"myfile.json"` → exit 0

---

## 6. Security analysis

### 6.1 Dynamic WHERE clause (highest-risk surface)

The `list_brews_filtered` function builds a dynamic query using a list of static condition strings and a parallel list of parameter values. The construction is:

```python
conditions: list[str] = []   # e.g. ["type = ?", "rating = ?"]
params: list = []             # e.g. ["pour_over", 4]
```

The SQL string is assembled from static condition strings only. User-supplied values appear exclusively in `params`, which are passed to `conn.execute(sql, params)` as the second argument. SQLite's `?` placeholder mechanism handles escaping; the values are never concatenated into the SQL string.

This pattern makes injection structurally impossible: there is no path by which a user-controlled value can alter the SQL syntax. The `WHERE`, `AND`, `ORDER BY`, and `LIMIT` keywords are all hard-coded strings. The column names in conditions (`type`, `rating`, `date`) are hard-coded string literals.

The one area of care: the `f"SELECT * FROM brews {where_clause} ORDER BY date DESC"` f-string. `where_clause` is assembled only from the static strings `"WHERE "`, `"type = ?"`, `"rating = ?"`, `"date >= ?"`, and `" AND "`. None of these contain user data. This is safe and follows the same pattern as the existing `update_brew` function in `db.py`, which also uses an f-string for the SET clause with static column names.

### 6.2 DELETE SQL

```python
conn.execute("DELETE FROM brews WHERE id = ?", (brew_id,))
```

Single `?` placeholder. `brew_id` is typed `int` (enforced by Click's `type=int`). No string interpolation. Safe.

### 6.3 ID validation before DB access

The `delete` command validates `id > 0` before any DB call. Click's `type=int` rejects non-integer input with its own usage error before the command body runs. These two checks together mean no non-integer and no non-positive value ever reaches the SQL layer.

### 6.4 Filter value validation before DB access

All three filter values (`--type`, `--rating`, `--since`) are validated in the command body before `db.list_brews_filtered` is called. Invalid values exit with code 1 before any DB access. This ensures that only structurally valid, in-range values reach the query builder. The query builder applies them as parameters regardless — defence in depth.

### 6.5 No new file I/O surfaces

The extension validation in `serialise.py` reduces the file I/O attack surface by preventing creation of files without a recognisable format indicator. No new file I/O operations are introduced in v0.2.

### 6.6 No new freeform text execution paths

`--grinder` and `--brewer` on `add` are freeform strings stored verbatim in `TEXT` columns and displayed with `click.echo`. They are never executed, interpolated into shell commands, or used in SQL queries directly (they travel through Pydantic validation then as `?` parameters in `insert_brew`). The `minLength: 1` check prevents empty-string entries.

### 6.7 Trust boundary summary

```
User input (CLI flags/prompts)
    |
    v
Command validation (explicit checks: range, enum, format, positive integer)
    |
    v
Pydantic model construction (BrewInput, EquipmentInput) — second validation layer
    |
    v
db.py functions — parameterised SQL only, no interpolation
    |
    v
SQLite file (~/.brewlog/brews.db) — local, user-owned
```

The `delete` command's trust boundary is slightly different: it performs an explicit SELECT (existence check) before the DELETE, ensuring the user receives an accurate error message if the ID does not exist, and ensuring the DELETE only runs on a confirmed-existing row.

---

## 7. Numbered menu design for brew type

### 7.1 Exact prompt format

The prompt is rendered exactly as:

```
Brew type:
  1) espresso
  2) hybrid
  3) immersion
  4) pour_over
Choice [1-4]:
```

Each option line is indented with two spaces. The `click.echo` calls produce the header and option lines. `click.prompt("Choice [1-4]", prompt_suffix=": ")` produces the final prompt line. (If `click.prompt` appends its own `: ` suffix by default, `prompt_suffix=""` should be used instead and `: ` included in the prompt text itself — the developer should verify the exact Click rendering in the test environment.)

Alternative: use `click.prompt("Choice [1-4]")` which Click renders as `Choice [1-4]: ` by default. Either is acceptable; the developer chooses the form that produces the cleanest rendered output.

### 7.2 Mapping from number to enum string

```python
options = sorted(BREW_TYPE_ENUM)
# options == ["espresso", "hybrid", "immersion", "pour_over"]  (alphabetical)
```

The mapping is:
- `1` → `options[0]` → `"espresso"`
- `2` → `options[1]` → `"hybrid"`
- `3` → `options[2]` → `"immersion"`
- `4` → `options[3]` → `"pour_over"`

Derived as `options[choice - 1]` where `choice` is the validated integer.

### 7.3 Invalid input handling

The function loops until a valid selection is made or the user cancels with Ctrl+C.

An input is invalid if any of the following are true:
- It cannot be converted to an integer (`int(raw)` raises `ValueError`)
- The resulting integer is less than 1
- The resulting integer is greater than `len(options)` (currently 4)

On invalid input, print `  Invalid choice. Please enter a number between 1 and 4.` and re-display the full menu from the top. The error message is indented with two spaces for visual consistency with the option list.

Empty input (the user presses Enter without typing) is treated as a non-numeric input by `int("")`, which raises `ValueError`. It is caught and re-prompts. This is intentional: there is no sensible default for brew type, so Enter-to-accept is not provided for this field.

### 7.4 Stored value

The function returns `options[choice - 1]`, which is the enum string (`"espresso"`, `"hybrid"`, `"immersion"`, or `"pour_over"`). This string is passed directly to `BrewInput(type=brew_type)`. Pydantic's `validate_brew_type` validator confirms it is in `BREW_TYPE_ENUM`. It is stored in the `type` TEXT column verbatim. No integer is stored anywhere.

### 7.5 Ctrl+C behaviour

If the user presses Ctrl+C during the menu loop, Click raises `click.exceptions.Abort`. This propagates up and Click's default Ctrl+C handling prints `Aborted!` and exits non-zero. This is existing behaviour consistent with the other prompts in `add` — no special handling is needed.

---

## Self-Review

Scores against `.claude/review-scorecard.yaml` dimensions (agent: architect):

| Dimension | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Input Adherence | 3x | 3 | All 24 ACs addressed. Each AC maps to a specific section, file, and implementation note. |
| Format Compliance | 2x | 3 | Document uses the exact 7-section structure requested. All subsections present. |
| Scope Discipline | 2x | 3 | No out-of-scope changes added. `models.py`, schema, import, update are explicitly noted as unchanged. |
| Spec Traceability | 2x | 3 | Every design element traces to an AC or a spec design note. AC references are explicit throughout. |
| Convention Compliance | 1x | 3 | Parameterised SQL, Pydantic validation, Click CLI patterns, stdlib only, no new dependencies. |
| Downstream Handoff | 2x | 3 | Each file section gives exact before/after code, full function signatures, import lines, and ordering notes. No ambiguity for the developer. |
| Testability | 2x | 3 | Section 5 lists named test functions with inputs, assertions, and AC references for every new test. |
| Security | 2x | 3 | Dynamic WHERE clause injection analysis, DELETE parameterisation, trust boundary diagram, filter pre-validation all addressed. |

**Weighted score calculation:**

Total weight: (3+2+2+2+1+2+2+2) = 16

Weighted sum: (3×3)+(2×3)+(2×3)+(2×3)+(1×3)+(2×3)+(2×3)+(2×3) = 9+6+6+6+3+6+6+6 = 48

Max possible: 16 × 3 = 48

Normalised score: 48/48 = **1.0**

Threshold: 0.8. Result: **PASS**.
