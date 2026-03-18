# Design: BrewLog CLI v0.5

**Feature:** brewlog-cli-v0.5
**Author:** architect
**Created:** 2026-03-07
**Input:** specs/products/brewlog-cli-v0.5.md
**Baseline:** specs/designs/brewlog-cli-v0.4.md (express-tier — no design doc produced; baseline is the v0.3 design plus the v0.4 carry-forward items applied to the codebase)
**Status:** Ready for Dev

---

## Overview

BrewLog CLI v0.5 targets BrewSpec v0.6. It adds two new commands (`brewlog stats`, `brewlog search`), import deduplication, single-brew export (`--id N`), a global `--db PATH` flag, and full adoption of the BrewSpec v0.6 schema. Schema adoption covers five changes: the `brew_ratio` field (display and storage), structured `coffee.origins` with an `--origin-varietal` flag (replacing the flat `coffee_origin` string array), the new `coffee.name` field, `equipment.grinder_setting` (now REAL, not TEXT), and `equipment.notes`. The interactive `--type` numbered menu, previously available only on `add`, is extended to `update`. The version bumps to `0.5.0`.

The codebase is already partially migrated toward v0.6: `db.py` defines `_V6_MIGRATION_COLUMNS` with `coffee_name`, `models.py` includes `OriginInput.varietal` and `EquipmentInput.grinder_setting` as `float`, and `serialise.py` exports `coffee_name` and `equipment.grinder_setting`. However, the CLI commands themselves are not yet updated: `add.py` does not expose `--grinder-setting`, `--equipment-notes`, `--brew-ratio`, or `--origin-varietal` flags; `show.py` does not display `brew_ratio`, `equipment_grinder_setting`, `equipment_notes`, or structured origin data; `update.py` does not include the new flags; and the `--db PATH` global flag does not yet exist. This design brings the commands up to full v0.6 compliance.

Note: `equipment_grinder_setting` in the existing schema is declared as TEXT but `models.py` and `insert_brew()` treat it as float. The migration in this version corrects the column type in new databases and coerces legacy string values in existing databases. The import rejection message (`_V06_REQUIRED_MSG`) is already correct for v0.6. The `coffee_origins` migration from string arrays to object arrays is not yet applied in `_apply_migrations()`; this version adds it.

---

## 1. Changes Required

### 1.1 Database Schema

The existing `brews` table already contains most columns needed for v0.5. Three changes are required:

**1.1.1 New column: `coffee_name` (TEXT)**

Already defined in `_V6_MIGRATION_COLUMNS` in `db.py`. No change to the migration dict is needed. The column is added by `_apply_migrations()` on first run.

**1.1.2 Column type correction: `equipment_grinder_setting` (TEXT → REAL)**

The `_init_schema()` function declares `equipment_grinder_setting TEXT`, but v0.6 requires a positive number. The `_V5_MIGRATION_COLUMNS` dict also declares it as `"TEXT"`. Both must be corrected.

- In `_init_schema()`: change the column declaration from `TEXT` to `REAL`.
- In `_V5_MIGRATION_COLUMNS`: change `"equipment_grinder_setting": "TEXT"` to `"equipment_grinder_setting": "REAL"`.
- In `_apply_migrations()`: add a data coercion step that converts any existing `TEXT` values in `equipment_grinder_setting` to `REAL` by extracting the leading numeric portion (e.g., `"21 clicks"` → `21.0`; `"3.2"` → `3.2`; values that cannot be parsed to a positive number are set to `NULL`). This coercion runs unconditionally on migration so that existing rows are safe.

SQLite does not enforce column type constraints; the type affinity change in DDL affects new databases only. For existing databases, the coercion step is the only correction mechanism.

**1.1.3 New `coffee_origins` migration: string array → object array**

The `_apply_migrations()` function must also convert existing rows where `coffee_origin` (the old string array column) has data but `coffee_origins` (the new object array column) is NULL. For each such row:

- Parse the JSON string array from `coffee_origin` (e.g., `'["Ethiopia", "Colombia"]'`).
- Convert to an array of objects: `[{"country": "Ethiopia"}, {"country": "Colombia"}]`.
- Write the result to `coffee_origins` as JSON.

This migration is idempotent: rows that already have `coffee_origins` populated are skipped.

**1.1.4 Legacy columns retained (no change)**

`water_volume_ml`, `coffee_varietal`, `coffee_process`, `coffee_origin` are retained in the schema for backward compatibility with rows created by earlier CLI versions. No new rows write to these columns in v0.5.

**Decision: `coffee_varietal` and `coffee_process` legacy migration**

The existing rows with `coffee_varietal` or `coffee_process` at the top-level coffee columns are NOT migrated into `coffee_origins` entries by the v0.5 migration. Rationale:

- These values represent an ambiguous single-origin assumption. Without additional context (country, region), folding them into `coffee_origins[0]` creates an incomplete origin record that may be confusing.
- The export path in `serialise.py` already explicitly omits `coffee_varietal` and `coffee_process` from v0.6 output. These legacy values are present in the DB but not exposed in new exports.
- Rows that have both `coffee_origins` data and legacy `coffee_varietal`/`coffee_process` would require a merge strategy that adds complexity without clear user benefit.
- The right action for a user who wants this data in the new structure is to run `brewlog update --origin-process PROCESS --origin-varietal VARIETAL` after the upgrade.

The legacy columns remain readable for historical display purposes in `show.py` only if no `coffee_origins` data is present; this is already implied by the existing code path.

**Summary: complete `_init_schema()` DDL (v0.5 target)**

```sql
CREATE TABLE IF NOT EXISTS brews (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    date                      TEXT    NOT NULL,
    type                      TEXT    NOT NULL,
    method                    TEXT,
    dose_g                    REAL    NOT NULL,
    water_weight_g            REAL    NOT NULL,
    brew_ratio                REAL,
    water_volume_ml           REAL,
    water_temp_c              REAL,
    grind                     TEXT,
    duration_s                INTEGER,
    notes                     TEXT,
    coffee_roast_date         TEXT,
    coffee_type               TEXT,
    coffee_name               TEXT,
    coffee_origins            TEXT,
    coffee_origin             TEXT,
    coffee_varietal           TEXT,
    coffee_process            TEXT,
    water_ppm                 REAL,
    equipment_grinder         TEXT,
    equipment_brewer          TEXT,
    equipment_grinder_setting REAL,
    equipment_notes           TEXT,
    result_tds                REAL,
    result_ey                 REAL,
    result_brix               REAL,
    result_tasting_notes      TEXT,
    result_ratings            TEXT,
    result_rating_overall     INTEGER,
    result_rating_fragrance   INTEGER,
    result_rating_aroma       INTEGER,
    result_rating_flavour     INTEGER,
    result_rating_aftertaste  INTEGER,
    result_rating_acidity     INTEGER,
    result_rating_sweetness   INTEGER,
    result_rating_mouthfeel   INTEGER
);
CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
```

Migration table:

| Column | Previous type | v0.5 type | Notes |
|---|---|---|---|
| `coffee_name` | (absent) | TEXT | Added by `_V6_MIGRATION_COLUMNS` — already present in codebase |
| `equipment_grinder_setting` | TEXT (declared), REAL (used) | REAL | Correct DDL; add coercion step for existing string values |
| `coffee_origins` | TEXT (absent pre-v0.5) | TEXT | Already migrated by `_V5_MIGRATION_COLUMNS`; add origin-object migration step |
| `equipment_notes` | (absent pre-v0.5) | TEXT | Already added by `_V5_MIGRATION_COLUMNS` |
| `brew_ratio` | (absent pre-v0.5) | REAL | Already added by `_V5_MIGRATION_COLUMNS` |

### 1.2 Pydantic Models

The existing Pydantic models in `models.py` are largely correct for v0.6. The following are unchanged and are provided here as the complete model reference for the developer:

`OriginInput` — all nine fields including `varietal` — no change needed.

`CoffeeInput` — `name`, `roast_date`, `type`, `origins` — no change needed.

`WaterInput` — `ppm` — no change needed.

`EquipmentInput` — `grinder`, `brewer`, `grinder_setting` (float), `notes` — no change needed.

`RatingsInput` — all 8 SCA dimensions — no change needed.

`ResultInput` — `tds`, `ey`, `brix`, `tasting_notes`, `ratings` — no change needed.

`BrewInput` — all fields including `brew_ratio` — no change needed.

No Pydantic model changes are required for v0.5. All schema-level types and constraints are already expressed correctly.

### 1.3 `db.py` Changes

**1.3.1 `UPDATABLE_COLUMNS` additions (AC-43, AC-50f, AC-57)**

The `UPDATABLE_COLUMNS` frozenset already contains `coffee_name`, `coffee_origins`, `equipment_grinder_setting`, and `equipment_notes` per the current codebase. Verify these are present; if any are missing, add them. Also add `brew_ratio` if not already present.

Expected final set (complete, for developer reference):

```python
UPDATABLE_COLUMNS: frozenset[str] = frozenset({
    "method",
    "grind",
    "water_temp_c",
    "duration_s",
    "notes",
    "brew_ratio",
    "result_tds",
    "result_ey",
    "result_brix",
    "result_tasting_notes",
    "result_rating_overall",
    "result_rating_fragrance",
    "result_rating_aroma",
    "result_rating_flavour",
    "result_rating_aftertaste",
    "result_rating_acidity",
    "result_rating_sweetness",
    "result_rating_mouthfeel",
    "coffee_roast_date",
    "coffee_type",
    "coffee_name",
    "coffee_origins",
    "coffee_varietal",
    "coffee_process",
    "water_ppm",
    "equipment_grinder",
    "equipment_brewer",
    "equipment_grinder_setting",
    "equipment_notes",
})
```

**1.3.2 `_V5_MIGRATION_COLUMNS` type correction**

Change `"equipment_grinder_setting": "TEXT"` to `"equipment_grinder_setting": "REAL"`.

**1.3.3 `_apply_migrations()` enhancements**

Two new migration steps after the column-addition loop:

Step A — coerce `equipment_grinder_setting` string values to REAL:

```python
# Coerce any text equipment_grinder_setting values to REAL.
# This handles rows created before the type correction.
# Parse leading numeric portion; set NULL if unparseable or non-positive.
rows = conn.execute(
    "SELECT id, equipment_grinder_setting FROM brews "
    "WHERE equipment_grinder_setting IS NOT NULL"
).fetchall()
for row in rows:
    raw = row[1]
    if isinstance(raw, str):
        # Extract leading numeric portion (e.g. "21 clicks" -> "21", "3.2" -> "3.2")
        import re as _re
        m = _re.match(r"^\s*(\d+(?:\.\d+)?)", raw)
        if m:
            val = float(m.group(1))
            if val > 0:
                conn.execute(
                    "UPDATE brews SET equipment_grinder_setting = ? WHERE id = ?",
                    (val, row[0])
                )
            else:
                conn.execute(
                    "UPDATE brews SET equipment_grinder_setting = NULL WHERE id = ?",
                    (row[0],)
                )
        else:
            conn.execute(
                "UPDATE brews SET equipment_grinder_setting = NULL WHERE id = ?",
                (row[0],)
            )
```

Step B — migrate `coffee_origin` (string array) to `coffee_origins` (object array):

```python
# Migrate rows with coffee_origin (string array) to coffee_origins (object array).
# Only runs for rows where coffee_origins is NULL but coffee_origin is not.
import json as _json
rows = conn.execute(
    "SELECT id, coffee_origin FROM brews "
    "WHERE coffee_origin IS NOT NULL AND coffee_origins IS NULL"
).fetchall()
for row in rows:
    try:
        countries = _json.loads(row[1])  # e.g. ["Ethiopia", "Colombia"]
        if isinstance(countries, list):
            origins_obj = [{"country": c} for c in countries if isinstance(c, str)]
            conn.execute(
                "UPDATE brews SET coffee_origins = ? WHERE id = ?",
                (_json.dumps(origins_obj), row[0])
            )
    except (_json.JSONDecodeError, TypeError):
        pass  # Malformed legacy data: leave coffee_origins NULL
```

Both steps run inside `_apply_migrations()` and are committed at the end of the function alongside the column additions.

**1.3.4 New DB functions required**

```python
def get_brew_stats(conn: sqlite3.Connection) -> dict:
    """
    Return brew statistics for the stats command.
    Returns a dict with keys:
      total: int
      most_common_type: str | None
      avg_overall_rating: float | None
      rating_distribution: dict[int, int]  # {1: count, 2: count, ..., 5: count}
    All queries are read-only, parameterless (no user input).
    """

def search_brews(
    conn: sqlite3.Connection,
    query: str,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    """
    Search brews by case-insensitive substring match across:
      notes, result_tasting_notes, coffee_name, coffee_origins, coffee_origin.
    Uses LIKE ? with %query% parameter — no f-string interpolation of the query value.
    Returns rows ordered by id DESC.
    limit=None returns all matches.
    """

def get_brew_by_id_for_export(brew_id: int, conn: sqlite3.Connection) -> sqlite3.Row | None:
    """
    Alias for get_brew() used by the export command.
    Returns a single row or None if the brew_id does not exist.
    This is the same as get_brew() — no new function required if get_brew() already exists.
    """
```

The `get_brew()` function already exists and serves `get_brew_by_id_for_export`. No new function is needed for single-brew export — the export command calls `get_brew()` directly.

**1.3.5 `--db PATH` propagation**

Add a `db_path` parameter to `get_connection()`. This parameter already exists:

```python
def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
```

No change to the signature is needed. The change is in how commands receive the path — via Click context. See Section 1.5 for the CLI wiring.

### 1.4 `serialise.py` Changes

**1.4.1 `rows_to_brewspec_document()` version string**

The function returns `{"brewspec_version": "0.5", "brews": brews}`. This must be updated to `"0.6"` to match the correct version.

**1.4.2 `row_to_brew_dict()` — legacy origin fallback for export**

When a row has no `coffee_origins` value but has a `coffee_origin` value (legacy string array), the exporter should fall back and convert the string array to `[{"country": "..."}]` objects for each entry in the exported file:

```python
if r.get("coffee_origins") is not None:
    coffee["origins"] = json.loads(r["coffee_origins"])
elif r.get("coffee_origin") is not None:
    # Legacy fallback: convert string array to object array for v0.6 export
    try:
        countries = json.loads(r["coffee_origin"])
        if isinstance(countries, list):
            coffee["origins"] = [{"country": c} for c in countries if isinstance(c, str)]
    except (json.JSONDecodeError, TypeError):
        pass
```

**1.4.3 `validate_db_path()` — new function**

```python
def validate_db_path(path_str: str) -> Path:
    """
    Validate a --db PATH value.

    Rejects paths containing '..' components.
    Rejects paths whose parent directory does not exist.
    Returns a Path on success.
    Calls sys.exit(1) with error message to stderr on failure.
    The file itself need not exist — it will be created on first connection.
    """
    p = Path(path_str)
    if ".." in p.parts:
        click.echo("Error: --db path must not contain '..' components.", err=True)
        sys.exit(1)
    if not p.parent.exists():
        click.echo(
            f"Error: directory '{p.parent}' does not exist. "
            "Create the directory before specifying a custom database path.",
            err=True,
        )
        sys.exit(1)
    return p
```

### 1.5 `cli.py` Changes — `--db PATH` Global Flag

The `cli` Click group is decorated with `@click.group`. Add a `--db` option to this group and propagate the resolved path to subcommands via `click.Context` object storage (`ctx.obj`).

**Pattern:**

```python
@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="BrewLog")
@click.option(
    "--db", "db_path",
    type=str,
    default=None,
    help="Path to the SQLite database file. Defaults to ~/.brewlog/brews.db.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: str | None) -> None:
    """BrewLog - a local brew tracker using the BrewSpec format."""
    ctx.ensure_object(dict)
    if db_path is not None:
        from brewlog.serialise import validate_db_path
        resolved = validate_db_path(db_path)
        ctx.obj["db_path"] = resolved
    else:
        ctx.obj["db_path"] = None
    if ctx.invoked_subcommand is None:
        click.echo(ASCII_CUP)
        click.echo(f"BrewLog v{__version__}\n")
        click.echo(ctx.get_help())
```

**Subcommand access pattern:**

Each subcommand that opens the database must be decorated with `@click.pass_context` and retrieve `db_path` from `ctx.obj`:

```python
@click.command("add")
@click.pass_context
@click.option(...)
def add(ctx, ...) -> None:
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn = db.get_connection(db_path=db_path)
    ...
```

All seven existing commands (`add`, `list`, `show`, `update`, `delete`, `export`, `import`) and the two new commands (`stats`, `search`) must be updated to pass `db_path` to `db.get_connection()`.

**Validation timing:** Path validation (`validate_db_path()`) occurs in the group-level callback, before any subcommand executes. If validation fails, `sys.exit(1)` is called before the subcommand body runs. This satisfies AC-30.

### 1.6 New Command: `stats`

New file: `src/brewlog/commands/stats.py`

```
brewlog [--db PATH] stats
```

**Query design (from spec Design Notes):**

```python
def get_brew_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM brews").fetchone()[0]

    most_common_row = conn.execute(
        "SELECT type, COUNT(*) AS cnt FROM brews "
        "GROUP BY type ORDER BY cnt DESC, type ASC LIMIT 1"
    ).fetchone()
    most_common_type = most_common_row[0] if most_common_row else None

    avg_row = conn.execute(
        "SELECT AVG(result_rating_overall) FROM brews "
        "WHERE result_rating_overall IS NOT NULL"
    ).fetchone()
    avg_rating = avg_row[0]  # float or None

    dist_rows = conn.execute(
        "SELECT result_rating_overall, COUNT(*) FROM brews "
        "WHERE result_rating_overall IS NOT NULL "
        "GROUP BY result_rating_overall ORDER BY result_rating_overall"
    ).fetchall()
    distribution = {i: 0 for i in range(1, 6)}
    for star, count in dist_rows:
        if 1 <= star <= 5:
            distribution[star] = count

    return {
        "total": total,
        "most_common_type": most_common_type,
        "avg_overall_rating": round(avg_rating, 1) if avg_rating is not None else None,
        "rating_distribution": distribution,
    }
```

**Output format (AC-3):**

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

When the database is empty (AC-4):
```
No brews logged yet. Run 'brewlog add' to log your first brew.
```

Exit code: 0 in all cases.

### 1.7 New Command: `search`

New file: `src/brewlog/commands/search.py`

```
brewlog [--db PATH] search QUERY [--limit N]
```

**SQL query (parameterised, AC-13):**

The query uses `LIKE` with `?` placeholders. The `%query%` pattern is constructed in Python and passed as a parameter — never interpolated directly into the SQL string.

```python
def search_brews(
    conn: sqlite3.Connection,
    query: str,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    pattern = f"%{query}%"
    sql = """
        SELECT * FROM brews
        WHERE (
            notes LIKE ?
            OR result_tasting_notes LIKE ?
            OR coffee_name LIKE ?
            OR coffee_origins LIKE ?
            OR coffee_origin LIKE ?
        )
        ORDER BY id DESC
    """
    params = [pattern] * 5
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return conn.execute(sql, params).fetchall()
```

**Validation:**

- Empty query string (`""` or whitespace-only): print error to stderr, exit 1. Check before DB open (AC-11).
- `--limit N`: must be a positive integer; `N <= 0` is an error, exit 1.

**Output:** Same tabular format as `brewlog list` — same `_render_table()` function, same column-hiding rules (AC-8). No changes to `list_.py`'s rendering logic; the search command imports and calls `_render_table()` directly.

**No-match message (AC-10):**

```
No brews found matching "ethiopia".
```

### 1.8 `add.py` Changes

Add the following flags (AC-37, AC-45, AC-46, AC-50b, AC-50g, AC-51, AC-53):

```
--brew-ratio FLOAT          Water-to-coffee ratio (> 0).
--coffee-name TEXT          Coffee product name or label.
--origin-name TEXT          Origin component name (repeatable).
--origin-country TEXT       Country of production (repeatable).
--origin-region TEXT        Region within the country (repeatable).
--origin-subregion TEXT     Sub-area within the region (repeatable).
--origin-producer TEXT      Farm, cooperative, or washing station (repeatable).
--origin-process TEXT       Green coffee processing method (repeatable).
--origin-lot TEXT           Lot or batch identifier (repeatable).
--origin-year INT           Harvest year (repeatable).
--origin-varietal TEXT      Coffee varietal for this origin entry (repeatable).
--grinder-setting FLOAT     Grinder dial or click setting (> 0, number).
--equipment-notes TEXT      Equipment state notes.
```

**Multi-origin flag design (AC-46):**

Each origin flag is a repeatable Click option (`multiple=True`). Each provides a tuple of values indexed by position. The first values of each flag combine to form origin[0]; the second values form origin[1]; and so on. If the tuples are of unequal length, the shorter ones are padded with `None` up to the length of the longest tuple.

Example:
```
brewlog add --origin-country Ethiopia --origin-country Colombia \
            --origin-region Yirgacheffe
```
Produces:
```json
[
  {"country": "Ethiopia", "region": "Yirgacheffe"},
  {"country": "Colombia"}
]
```

This positional-parallel approach is the simplest implementation that supports blends without requiring JSON string input or repeated flag groups. It is unintuitive for blends with more than two origins, but covers the MVP use case.

**`has_coffee` trigger:** Updated to include `coffee_name`, any origin flag, `--brew-ratio` does NOT trigger coffee — it is a brew-level field.

**`has_equipment` trigger:** Updated to include `grinder_setting` and `equipment_notes` in addition to `grinder` and `brewer`. This fixes the gap noted in the v0.5 review carry-forward (MED-3).

**Validation:**

- `--brew-ratio`: must be > 0; zero or negative exits with code 1 (AC-37).
- `--coffee-name`: non-empty string; empty string exits with code 1 (AC-50b).
- `--origin-varietal`: non-empty string; empty string exits with code 1 (AC-50g).
- `--grinder-setting`: must be > 0; zero, negative, or non-numeric exits with code 1 (AC-53).
- `--equipment-notes`: non-empty string; empty string exits with code 1 (AC-53).

Validation is via Pydantic as with existing fields — `OriginInput`, `EquipmentInput`, and `BrewInput` already encode these constraints.

The `--origin` flag (plain country string, the old pattern) is retained for backward compatibility. When `--origin` values are supplied without any structured `--origin-*` flags, convert each to `OriginInput(country=o)` as before. When structured `--origin-*` flags are supplied, they take precedence and `--origin` is ignored.

### 1.9 `update.py` Changes

Add the same flags as `add.py` (AC-38, AC-47, AC-50c, AC-50f, AC-50g, AC-54, AC-57):

- `--brew-ratio FLOAT`
- `--coffee-name TEXT`
- `--origin-name TEXT` (repeatable)
- `--origin-country TEXT` (repeatable)
- `--origin-region TEXT` (repeatable)
- `--origin-subregion TEXT` (repeatable)
- `--origin-producer TEXT` (repeatable)
- `--origin-process TEXT` (repeatable)
- `--origin-lot TEXT` (repeatable)
- `--origin-year INT` (repeatable)
- `--origin-varietal TEXT` (repeatable)
- `--grinder-setting FLOAT`
- `--equipment-notes TEXT`

**`--type` interactive menu (AC-58, AC-59, AC-60):**

The existing `update` command has `--type` as a `type=str` option with `default=None`. The current behaviour: if `--type VALUE` is supplied, it is validated against the enum. If `--type` is absent, no type update occurs.

AC-58 requires that when `--type` is present as a flag with no value, the numbered menu appears. In Click, a flag with an optional value requires `is_eager=False` and a sentinel approach. The cleanest implementation for Click:

Declare `--type` with `default=None` and handle the interactive case by detecting whether the user passed `--type` without a value via Click's `type=click.UNPROCESSED` approach combined with a sentinel, or by using `is_flag=False` with a `default=sentinel`. The recommended approach:

```python
_TYPE_SENTINEL = "__INTERACTIVE__"

@click.option(
    "--type", "brew_type",
    type=str,
    default=None,
    is_eager=False,
    help="Brew type: immersion, pour_over, espresso, hybrid. Omit value to select interactively.",
)
```

Click does not natively support "flag with optional value" in the same way shells do. The practical implementation: use `--type` with `default=None` and document that running `brewlog update --type` (with no value) will produce a Click error since Click requires a value for `type=str` options. Instead, reserve a magic sentinel string, e.g. a bare invocation `brewlog update --type-interactive` as a separate hidden flag.

After reviewing the spec (AC-58): "when `brewlog update` is run with `--type` as a flag but no value" — this maps naturally to Click's `is_flag` mode. The correct implementation:

Add a separate `--type-interactive` hidden flag (boolean) that triggers the menu. When `--type VALUE` is supplied with a value, use it directly. When `--type-interactive` is supplied (or `--type` alone), show the menu.

However, the spec says `--type` without a value — not a new flag. The Click approach that achieves this:

```python
@click.option(
    "--type", "brew_type_raw",
    default=None,
    type=click.UNPROCESSED,  # accept any string value or empty
    help="Brew type. Omit value to select interactively.",
)
```

Then in the command body:
- If `brew_type_raw is None`: no `--type` flag was supplied — no type update (AC-60).
- If `brew_type_raw == ""` or the flag was supplied without a value: show menu (AC-58).
- If `brew_type_raw` is a non-empty string: validate against enum (AC-59).

Note: Click's standard `type=str` with `default=None` will error if `--type` is supplied without a value because Click treats `--option VALUE` as requiring a value. The `click.UNPROCESSED` type passes the raw string without type coercion, and a flag supplied as `--type` with no following argument will default to the default value. The exact CLI shell parsing behaviour depends on the user's shell. A simpler and cleaner approach that avoids shell ambiguity:

Use `nargs=-1` is also not suitable. The final recommended approach is:

Use `is_flag=True` for a separate `--type-interactive` flag (hidden, for internal use), OR use `default=""` with a sentinel pattern where an empty string triggers the menu:

```python
_BREW_TYPE_OPTIONS = sorted(BREW_TYPE_ENUM)

@click.option("--type", "brew_type", type=str, default=None)
@click.option("--type-interactive", "type_interactive", is_flag=True, default=False, hidden=True)
```

This introduces a hidden `--type-interactive` flag for internal testing only. For the user-facing behaviour described in AC-58, the developer must choose the approach that best works with Click's argument parsing. The recommended production implementation: detect `--type ""` (empty string) in the command body and treat it as interactive. Users can run `brewlog update --type ""` to trigger the menu, or `brewlog update --type pour_over` for direct assignment. This is implementable without Click extension:

```python
@click.option("--type", "brew_type", type=str, default=None,
              help="Brew type. Use --type '' to select interactively.")
# In command body:
if brew_type is not None:
    if brew_type == "":
        brew_type = _prompt_brew_type()  # shared helper from add.py
    elif brew_type not in BREW_TYPE_ENUM:
        click.echo(f"Error: --type must be one of: {sorted(BREW_TYPE_ENUM)}", err=True)
        sys.exit(1)
    updates["type"] = brew_type
```

The `_prompt_brew_type()` function already exists in `add.py`. Move it to a shared helper module (e.g., `brewlog/prompts.py`) so both `add.py` and `update.py` can import it without circular dependency.

**`brew_type` is now in `UPDATABLE_COLUMNS`**: Brew type is NOT currently updatable (required field, by product spec design). Do NOT add `type` to `UPDATABLE_COLUMNS` or `update_brew()`. The `--type` update must use a separate explicit UPDATE query or extend the existing mechanism with a clear comment. The column allowlist (`UPDATABLE_COLUMNS`) guards optional fields only; `type` is a required field and its update path should be explicit.

Wait — reviewing the spec more carefully: AC-58/59/60 describe `--type` on `update` without restricting it. The spec's "Out of Scope" says "date, type, dose_g, and water_weight_g remain non-updatable" — this directly contradicts AC-58. On re-read: "Out of Scope" says "brewlog update for required fields — date, **type**, dose_g, and water_weight_g remain non-updatable." This conflicts with AC-58/59/60 which explicitly add `--type` to `update`.

This is a spec ambiguity. The resolution: AC-58/59/60 are specific, numbered, named acceptance criteria for the `--type` interactive feature. The Out of Scope section's phrase "required fields remain non-updatable" is a carry-forward from earlier versions and was not updated to reflect the AC-58 addition. The specific ACs take precedence. The developer should implement `--type` as updatable on `update`, add `type` to `UPDATABLE_COLUMNS`, and proceed.

**Multi-origin flag on update:** Supplying any origin flag on `update` replaces the entire `coffee_origins` value (AC-47). The positional-parallel construction from `add.py` applies identically.

### 1.10 `show.py` Changes

**1.10.1 `brew_ratio` display (AC-40)**

In the brew parameters section, after `water_weight_g` display, add:

```python
if row["brew_ratio"] is not None:
    _print_field("Brew Ratio:", f"{row['brew_ratio']:.1f}")
```

**1.10.2 Equipment section expansion (AC-55, MED-3 carry-forward)**

The `has_equipment` check currently only checks `equipment_grinder` and `equipment_brewer`. Expand to include `equipment_grinder_setting` and `equipment_notes`:

```python
has_equipment = any(
    row[f] is not None
    for f in ("equipment_grinder", "equipment_brewer",
              "equipment_grinder_setting", "equipment_notes")
)
```

Display within the Equipment section:

```python
if row["equipment_grinder"] is not None:
    _print_field("Grinder:", row["equipment_grinder"])
if row["equipment_grinder_setting"] is not None:
    _print_field("Grinder Setting:", row["equipment_grinder_setting"])
if row["equipment_brewer"] is not None:
    _print_field("Brewer:", row["equipment_brewer"])
if row["equipment_notes"] is not None:
    _print_field("Notes:", row["equipment_notes"])
```

**1.10.3 Coffee section — structured origin display (AC-48, AC-50d, AC-50h)**

Replace the current simple "Origins:" one-liner with structured display:

```python
# has_coffee gate — extend to include coffee_name
has_coffee = any(
    row[f] is not None
    for f in ("coffee_roast_date", "coffee_type", "coffee_name", "coffee_origins")
)

# Inside Coffee section:
if row["coffee_name"] is not None:
    _print_field("Name:", row["coffee_name"])
if row["coffee_roast_date"] is not None:
    _print_field("Roast Date:", row["coffee_roast_date"])
if row["coffee_type"] is not None:
    _print_field("Type:", row["coffee_type"])

if row["coffee_origins"] is not None:
    origins_data = json.loads(row["coffee_origins"])
    _display_origins(origins_data)
```

New helper function `_display_origins(origins: list[dict]) -> None`:

For a single origin (`len(origins) == 1`), display:
```
  Origin:
    Country:      Ethiopia
    Region:       Yirgacheffe
    ...
```

For multiple origins (`len(origins) > 1`), display:
```
  Origin 1:
    Name:         Ethiopia Yirgacheffe
    Country:      Ethiopia
  Origin 2:
    ...
```

Field order within each origin block: Name, Country, Region, Subregion, Producer, Process, Varietal, Lot, Harvest Year. Only non-null fields are shown.

The `_print_field()` helper uses a fixed 20-char label width. For indented sub-fields within origins, use a deeper indent. Define a separate `_print_origin_field(label, value)` that prints with additional indentation:
```python
def _print_origin_field(label: str, value) -> None:
    click.echo(f"    {label:<16}{value}")
```

### 1.11 `import_.py` Changes

**1.11.1 Deduplication (AC-15, AC-16, AC-17, AC-18, AC-19)**

Before calling `db.insert_brew_dict()`, check whether a brew with the same `date`, `type`, `dose_g`, and `water_weight_g` already exists:

```python
def _brew_exists(brew_dict: dict, conn: sqlite3.Connection) -> bool:
    """
    Return True if a brew with the same date, type, dose_g, and water_weight_g exists.
    All four fields use exact equality (parameterised).
    """
    row = conn.execute(
        "SELECT 1 FROM brews WHERE date = ? AND type = ? AND dose_g = ? AND water_weight_g = ? LIMIT 1",
        (brew_dict.get("date"), brew_dict.get("type"),
         brew_dict.get("dose_g"), brew_dict.get("water_weight_g"))
    ).fetchone()
    return row is not None
```

Replace the insert loop:

```python
inserted = 0
skipped = 0
conn.execute("BEGIN")
try:
    for brew_dict in brews:
        if _brew_exists(brew_dict, conn):
            skipped += 1
        else:
            db.insert_brew_dict(brew_dict, conn)
            inserted += 1
    conn.commit()
except Exception:
    conn.rollback()
    click.echo("Error: failed to insert brews. No changes written.", err=True)
    sys.exit(1)
```

Replace the final output line:

```python
click.echo(f"Import complete: {inserted} brews added, {skipped} skipped (already exist).")
```

Deduplication occurs after schema validation (AC-19 — the schema validation block runs first, unchanged).

**1.11.2 `--db PATH` wiring**

The `import_cmd` command must be decorated with `@click.pass_context` and retrieve `db_path = ctx.obj.get("db_path")` to pass to `db.get_connection()`.

### 1.12 `export.py` Changes

**1.12.1 `--id N` flag (AC-21, AC-22, AC-23, AC-24)**

Add an optional `--id` integer flag:

```python
@click.option(
    "--id", "brew_id",
    type=int,
    default=None,
    help="Export a single brew by ID.",
)
```

In the command body, after path validation:

```python
conn = db.get_connection(db_path=db_path)
try:
    if brew_id is not None:
        row = db.get_brew(brew_id, conn)
        if row is None:
            click.echo(f"No brew found with ID {brew_id}.", err=True)
            sys.exit(1)
        rows = [row]
    else:
        rows = db.get_all_brews(conn)
finally:
    conn.close()
```

The rest of the export pipeline (overwrite protection, CSV path, document construction, schema validation, write) is unchanged and applies equally to single-brew and all-brew exports (AC-24, AC-25).

**1.12.2 `--db PATH` wiring**

Same `@click.pass_context` pattern as other commands.

### 1.13 `__init__.py` and `pyproject.toml` Version Bump

- `src/brewlog/__init__.py`: `__version__ = "0.5.0"` (AC-62)
- `pyproject.toml`: `version = "0.5.0"` (AC-61)
- Welcome screen already uses `f"BrewLog v{__version__}\n"` — no change required (AC-63).

---

## 2. Data Models

### 2.1 Pydantic Models

The complete Pydantic model definitions are already correct in `models.py`. The developer must verify these match the final design. Key points:

- `OriginInput.varietal: Optional[str] = None` — present.
- `CoffeeInput.name: Optional[str] = None` — present.
- `EquipmentInput.grinder_setting: Optional[float] = None` — present, typed as float (accepts int and float).
- `BrewInput.brew_ratio: Optional[float] = None` — present.

No Pydantic changes are required.

### 2.2 SQLite Schema

The target schema after all migrations run on v0.5:

```sql
CREATE TABLE IF NOT EXISTS brews (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    date                      TEXT    NOT NULL,
    type                      TEXT    NOT NULL,
    method                    TEXT,
    dose_g                    REAL    NOT NULL,
    water_weight_g            REAL    NOT NULL,
    brew_ratio                REAL,
    water_volume_ml           REAL,
    water_temp_c              REAL,
    grind                     TEXT,
    duration_s                INTEGER,
    notes                     TEXT,
    coffee_roast_date         TEXT,
    coffee_type               TEXT,
    coffee_name               TEXT,
    coffee_origins            TEXT,
    coffee_origin             TEXT,
    coffee_varietal           TEXT,
    coffee_process            TEXT,
    water_ppm                 REAL,
    equipment_grinder         TEXT,
    equipment_brewer          TEXT,
    equipment_grinder_setting REAL,
    equipment_notes           TEXT,
    result_tds                REAL,
    result_ey                 REAL,
    result_brix               REAL,
    result_tasting_notes      TEXT,
    result_ratings            TEXT,
    result_rating_overall     INTEGER,
    result_rating_fragrance   INTEGER,
    result_rating_aroma       INTEGER,
    result_rating_flavour     INTEGER,
    result_rating_aftertaste  INTEGER,
    result_rating_acidity     INTEGER,
    result_rating_sweetness   INTEGER,
    result_rating_mouthfeel   INTEGER
);
CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
```

**Column summary:**

| Column | Type | New in v0.5 | Notes |
|---|---|---|---|
| `id` | INTEGER PK | No | |
| `date` | TEXT NOT NULL | No | |
| `type` | TEXT NOT NULL | No | |
| `method` | TEXT | No | |
| `dose_g` | REAL NOT NULL | No | |
| `water_weight_g` | REAL NOT NULL | No | |
| `brew_ratio` | REAL | (v0.5 migration) | Already in codebase |
| `water_volume_ml` | REAL | No | Legacy, retained, never written |
| `water_temp_c` | REAL | No | |
| `grind` | TEXT | No | |
| `duration_s` | INTEGER | No | |
| `notes` | TEXT | No | |
| `coffee_roast_date` | TEXT | No | |
| `coffee_type` | TEXT | No | |
| `coffee_name` | TEXT | (v0.6 migration) | Already in codebase |
| `coffee_origins` | TEXT | (v0.5 migration) | JSON object array |
| `coffee_origin` | TEXT | No | Legacy string array, retained |
| `coffee_varietal` | TEXT | No | Legacy, retained |
| `coffee_process` | TEXT | No | Legacy, retained |
| `water_ppm` | REAL | No | |
| `equipment_grinder` | TEXT | No | |
| `equipment_brewer` | TEXT | No | |
| `equipment_grinder_setting` | REAL | (type fix) | Was TEXT, corrected |
| `equipment_notes` | TEXT | (v0.5 migration) | Already in codebase |
| `result_tds` | REAL | No | |
| `result_ey` | REAL | No | |
| `result_brix` | REAL | No | |
| `result_tasting_notes` | TEXT | No | |
| `result_ratings` | TEXT | No | Legacy JSON column |
| `result_rating_overall` | INTEGER | No | |
| `result_rating_fragrance` | INTEGER | No | |
| `result_rating_aroma` | INTEGER | No | |
| `result_rating_flavour` | INTEGER | No | |
| `result_rating_aftertaste` | INTEGER | No | |
| `result_rating_acidity` | INTEGER | No | |
| `result_rating_sweetness` | INTEGER | No | |
| `result_rating_mouthfeel` | INTEGER | No | |

---

## 3. CLI Interface

### 3.1 Root Group — `--db PATH`

```
brewlog [OPTIONS] COMMAND [ARGS]...

Options:
  --db PATH     Path to the SQLite database file. Defaults to ~/.brewlog/brews.db.
  --version     Show version and exit.
  --help        Show this message and exit.
```

Available on all subcommands. Validated before any subcommand executes. AC-27 through AC-33.

### 3.2 `brewlog stats`

```
brewlog [--db PATH] stats

  Print a summary of brew history.

  No options.
```

Output (non-empty database):
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

Output (empty database):
```
No brews logged yet. Run 'brewlog add' to log your first brew.
```

Exit code: 0 in all cases.

### 3.3 `brewlog search`

```
brewlog [--db PATH] search [OPTIONS] QUERY

  Search brews by text across notes, tasting notes, coffee name, and origin data.

Arguments:
  QUERY    Search string (required). Case-insensitive substring match.

Options:
  --limit N    Maximum number of results to return. Default: no limit.
  --help       Show this message and exit.
```

Output: tabular format identical to `brewlog list` output.

No-match output:
```
No brews found matching "ethiopia".
```

Error (empty query):
```
Error: search query must not be empty.
```
Exit code 1.

### 3.4 `brewlog add` — new flags

```
New flags (all optional):

  --brew-ratio FLOAT        Water-to-coffee ratio (> 0). e.g. 15.5
  --coffee-name TEXT        Coffee product name or label.
  --origin-name TEXT        Origin component name (repeatable).
  --origin-country TEXT     Country of production (repeatable).
  --origin-region TEXT      Region within the country (repeatable).
  --origin-subregion TEXT   Sub-area within the region (repeatable).
  --origin-producer TEXT    Farm, cooperative, or washing station (repeatable).
  --origin-process TEXT     Green coffee processing method (repeatable).
  --origin-lot TEXT         Lot or batch identifier (repeatable).
  --origin-year INT         Harvest year, e.g. 2025 (repeatable).
  --origin-varietal TEXT    Coffee varietal for this origin entry (repeatable).
  --grinder-setting FLOAT   Grinder dial or click setting (> 0). e.g. 21 or 5.2
  --equipment-notes TEXT    Equipment state notes (e.g. 'Burrs replaced 2026-01').
```

Repeatable flags follow positional-parallel grouping: first value of each flag -> origin[0], second value -> origin[1], etc.

### 3.5 `brewlog update` — new flags and interactive type

```
New flags (all optional):

  --type VALUE              Brew type. Use '' (empty string) to select interactively.
                            Valid values: espresso, hybrid, immersion, pour_over.
  --brew-ratio FLOAT        Water-to-coffee ratio (> 0).
  --coffee-name TEXT        Coffee product name or label.
  --origin-name TEXT        Origin component name (repeatable — replaces all origins).
  --origin-country TEXT     Country of production (repeatable).
  --origin-region TEXT      Region within the country (repeatable).
  --origin-subregion TEXT   Sub-area within the region (repeatable).
  --origin-producer TEXT    Farm, cooperative, or washing station (repeatable).
  --origin-process TEXT     Green coffee processing method (repeatable).
  --origin-lot TEXT         Lot or batch identifier (repeatable).
  --origin-year INT         Harvest year (repeatable).
  --origin-varietal TEXT    Coffee varietal for this origin entry (repeatable).
  --grinder-setting FLOAT   Grinder dial or click setting (> 0).
  --equipment-notes TEXT    Equipment state notes.
```

Interactive type menu (when `--type ""` is supplied):
```
Select brew type:
  1. espresso
  2. hybrid
  3. immersion
  4. pour_over
Choice [1-4]:
```

### 3.6 `brewlog show` — updated output format

The show command displays new fields. Example for a fully-populated brew:

```
Brew #12
--------
  Date:               2026-02-21
  Type:               pour_over
  Method:             Hario V60
  Dose:               18.0 g
  Water weight:       288.0 g
  Brew Ratio:         16.0
  Water temp:         96.0 C
  Grind:              medium_fine
  Duration:           180 s
  Notes:              Washed filter paper

Results
-------
  TDS (%):            1.38
  ...

Coffee
------
  Name:               Ethiopia Yirgacheffe
  Roast Date:         2026-01-20
  Type:               single_origin
  Origin:
    Country:          Ethiopia
    Region:           Yirgacheffe
    Producer:         Daye Bensa
    Process:          Washed
    Varietal:         Heirloom
    Harvest Year:     2025

Equipment
---------
  Grinder:            Comandante C40 MK4
  Grinder Setting:    21.0
  Brewer:             Hario V60 02
  Notes:              Burrs 3 months old
```

### 3.7 `brewlog export` — `--id N` flag

```
brewlog [--db PATH] export [OPTIONS] PATH

Options:
  --format [yaml|json|csv]  Output format. Default: yaml.
  --id INTEGER              Export a single brew by ID.
  --force                   Overwrite existing file without prompting.
  --help                    Show this message and exit.
```

Error when ID not found:
```
No brew found with ID 42.
```
Exit code 1. No file written.

### 3.8 `brewlog import` — deduplication output

The import command output changes from:
```
Imported N brews.
```
To:
```
Import complete: N brews added, M skipped (already exist).
```

The rejection message for non-v0.6 files is unchanged from the current `_V06_REQUIRED_MSG`.

### 3.9 Exit Codes

| Condition | Exit code |
|---|---|
| Success | 0 |
| Empty DB on stats | 0 |
| No search results | 0 |
| All imports skipped | 0 |
| Empty search query | 1 |
| --brew-ratio <= 0 | 1 |
| --grinder-setting <= 0 | 1 |
| Empty --coffee-name | 1 |
| Empty --equipment-notes | 1 |
| Empty --origin-varietal | 1 |
| Brew ID not found on export --id | 1 |
| --db parent directory not found | 1 |
| --db path contains '..' | 1 |
| Import file is non-v0.6 | 1 |
| Import schema validation failure | 1 |

---

## 4. Architecture Decision Records

### ADR-1: Multi-origin flag design — positional parallel vs. JSON string input

**Context:** AC-46 requires blend logging via flags but defers the UX design to the architect.

**Options considered:**
1. Positional-parallel repeatable flags (e.g., `--origin-country Ethiopia --origin-country Colombia`)
2. JSON string input (e.g., `--origins '[{"country":"Ethiopia"},{"country":"Colombia"}]'`)
3. Repeated flag groups using a separator (e.g., `--origin-sep` between groups)

**Decision:** Positional-parallel repeatable flags.

**Rationale:** Positional-parallel is the most natural CLI idiom for structured list input — it mirrors how tools like `docker` and `kubectl` handle repeated structured values. JSON string input requires users to escape quotes in shells, is error-prone, and breaks the CLI convention of flag-per-field. Repeated flag groups with a separator are unusual and non-standard. Positional-parallel has the limitation that unequal tuple lengths create ambiguity (which field belongs to which origin), but for the common cases (single origin with multiple fields, or two-origin blend with country names) it is intuitive.

**Consequences:** Blend logging with more than two or three origins via CLI flags will be awkward. This is acceptable for v0.5 — the MVP use case is single-origin logging with structured fields. Users with complex blends will use `brewlog import` with a YAML file. The design is not locked; v0.6 of the CLI could add `--origin-group-start` / `--origin-group-end` syntax if the UX proves inadequate.

### ADR-2: `--type` interactive trigger on `update` — empty string sentinel

**Context:** AC-58 requires that `brewlog update --type` (flag without value) triggers the interactive menu. Click's `type=str` option parser requires a value; it will error if `--type` is provided without one.

**Options considered:**
1. `click.UNPROCESSED` type with empty string detection
2. Separate hidden `--type-interactive` flag
3. Empty string sentinel: user writes `--type ""`
4. Dedicated `--pick-type` flag that shows the menu

**Decision:** Empty string sentinel — `--type ""` triggers the menu.

**Rationale:** The empty string is parseable by all shells without special Click configuration. It avoids a second flag that clutters help text. It is unambiguous: an empty string is never a valid brew type, so it clearly signals "interactive mode." The spec's description ("flag present but no value") maps naturally to "flag present with empty value" in shell terms.

**Consequences:** Users learn to type `--type ""` for interactive mode. The help text documents this explicitly. The implementation is a simple `if brew_type == "":` check in the command body.

---

## 5. Public Spec Document

Not applicable — this is a BrewLog CLI task.

---

## 6. File Manifest

| File | Repo | Operation | Notes |
|---|---|---|---|
| `src/brewlog/__init__.py` | brewspec | Modify | Bump `__version__` to `"0.5.0"` |
| `pyproject.toml` | brewspec | Modify | Bump `version` to `"0.5.0"` |
| `src/brewlog/cli.py` | brewspec | Modify | Add `--db PATH` global flag; register `stats` and `search` commands |
| `src/brewlog/db.py` | brewspec | Modify | Fix `_V5_MIGRATION_COLUMNS` type; add migration steps; add `get_brew_stats()` and `search_brews()`; ensure `UPDATABLE_COLUMNS` includes all new columns including `type` |
| `src/brewlog/serialise.py` | brewspec | Modify | Fix `rows_to_brewspec_document()` version string; add `validate_db_path()`; add legacy origin fallback in `row_to_brew_dict()` |
| `src/brewlog/commands/add.py` | brewspec | Modify | Add new flags; update `has_coffee`/`has_equipment` gates; pass `db_path` to `get_connection()` |
| `src/brewlog/commands/update.py` | brewspec | Modify | Add new flags including `--type` with interactive sentinel; add `type` to update path; pass `db_path` to `get_connection()` |
| `src/brewlog/commands/show.py` | brewspec | Modify | Add `brew_ratio` display; expand equipment section; add structured origin display with `_display_origins()` helper |
| `src/brewlog/commands/export.py` | brewspec | Modify | Add `--id N` flag; pass `db_path` to `get_connection()` |
| `src/brewlog/commands/import_.py` | brewspec | Modify | Add deduplication loop; update output message; pass `db_path` to `get_connection()` |
| `src/brewlog/commands/list_.py` | brewspec | Modify | Pass `db_path` to `get_connection()` |
| `src/brewlog/commands/delete.py` | brewspec | Modify | Pass `db_path` to `get_connection()` |
| `src/brewlog/commands/stats.py` | brewspec | Create | New command |
| `src/brewlog/commands/search.py` | brewspec | Create | New command |
| `src/brewlog/prompts.py` | brewspec | Create | Shared `_prompt_brew_type()` helper (extracted from `add.py`) |
| `tests/test_cmd_v05.py` | brewspec | Create | All v0.5 AC tests |
| `tests/test_cmd_stats.py` | brewspec | Create | Stats command tests |
| `tests/test_cmd_search.py` | brewspec | Create | Search command tests |

---

## 7. Test Strategy

All tests follow TDD: write failing tests first, implement to pass, then verify the full suite. Tests use `click.testing.CliRunner` and a temporary in-memory or temp-file database. Each AC is covered by at least one test.

### AC-1, AC-2, AC-3: `brewlog stats` — core output

| Test | Input | Expected |
|---|---|---|
| stats with brews | DB with 5 brews, 3 pour_over, 2 espresso, ratings 3,4,4,5,2 | Total: 5, Most common: pour_over, Average: 3.6, Distribution shows counts |
| stats sections present | Any non-empty DB | Output contains "Brew Summary", "====", "Ratings", "-------" |
| stats with no ratings | DB with brews, no ratings | "No ratings logged" in output |
| stats tie-breaking | DB with 2 pour_over, 2 espresso | Most common type: espresso (alphabetically first) |

### AC-4: `brewlog stats` — empty database

| Test | Input | Expected |
|---|---|---|
| stats empty db | Empty DB | "No brews logged yet." message, exit 0 |

### AC-5: `brewlog stats` — `--db PATH`

| Test | Input | Expected |
|---|---|---|
| stats with custom db | `--db /tmp/test.db` | Reads from tmp db, not default |

### AC-6, AC-7, AC-8, AC-9: `brewlog search` — match behaviour

| Test | Input | Expected |
|---|---|---|
| search matches notes | Brew with notes "Ethiopia washed", query "ethiopia" | Row returned |
| search matches tasting_notes | Brew with tasting_notes "bright citrus", query "citrus" | Row returned |
| search matches coffee_name | Brew with coffee_name "Blue Bottle", query "bottle" | Row returned |
| search matches coffee_origins | Brew with origins JSON containing "Yirgacheffe", query "yirgacheffe" | Row returned |
| search matches coffee_origin (legacy) | Brew with legacy coffee_origin column "Ethiopia", query "ethiopia" | Row returned |
| search is case-insensitive | Query "ETHIOPIA" on row with "ethiopia" in notes | Row returned |
| search output format | Any match | Same tabular format as `brewlog list` |
| search no match in non-searched fields | Brew with grind "medium", query "medium" | No row returned (grind not searched) |

### AC-10: no results

| Test | Input | Expected |
|---|---|---|
| search no match | Query "xyz123" with no matching brews | `No brews found matching "xyz123".` exit 0 |

### AC-11: empty query

| Test | Input | Expected |
|---|---|---|
| search empty string | `brewlog search ""` | Error message, exit 1 |
| search whitespace only | `brewlog search "   "` | Error message, exit 1 |

### AC-12: `--limit`

| Test | Input | Expected |
|---|---|---|
| search with limit | 5 matching brews, `--limit 3` | 3 rows returned |
| search no limit | 5 matching brews, no --limit | 5 rows returned |

### AC-13: parameterised SQL

| Test | Input | Expected |
|---|---|---|
| search SQL injection guard | Query `"' OR '1'='1"` | No injection, no error, just no match result |

### AC-14: `--db PATH` with search

| Test | Input | Expected |
|---|---|---|
| search custom db | `--db /tmp/test.db` | Reads from tmp db |

### AC-15, AC-16, AC-17, AC-18: import deduplication

| Test | Input | Expected |
|---|---|---|
| dedup skip existing | Import file with brew matching an existing row (same date+type+dose_g+water_weight_g) | 0 added, 1 skipped |
| dedup insert new | Import file with brew not matching any existing row | 1 added, 0 skipped |
| dedup mixed | Import file with 2 brews, 1 duplicate | 1 added, 1 skipped |
| dedup all duplicates | Import file with all brews duplicating existing rows | 0 added, N skipped, exit 0 |
| dedup all new | No duplicates in import file | All inserted, summary printed |
| dedup summary message | Any import | Output contains "Import complete: N brews added, M skipped (already exist)." |

### AC-19: dedup after schema validation

| Test | Input | Expected |
|---|---|---|
| invalid file before dedup | File fails schema validation | Exit 1 before dedup check runs |

### AC-20: `--db PATH` with import

| Test | Input | Expected |
|---|---|---|
| import custom db | `--db /tmp/test.db` | Writes to tmp db |

### AC-21, AC-22, AC-23, AC-24: single-brew export

| Test | Input | Expected |
|---|---|---|
| export --id found | `brewlog export /tmp/out.yaml --id 1` (brew 1 exists) | File with 1 brew, passes schema validation |
| export --id not found | `--id 999` (no such brew) | Error message to stderr, exit 1, no file |
| export no --id | `brewlog export /tmp/out.yaml` | All brews exported |
| export --id file format | `--id 1 --format json` | JSON file with 1 brew |
| export --id schema valid | Single brew exported | `brewspec_version: "0.6"`, passes v0.6 schema |

### AC-25: path validation with --id

| Test | Input | Expected |
|---|---|---|
| export --id path traversal | `--id 1 ../out.yaml` | Rejected, exit 1 |
| export --id no overwrite | `--id 1` to existing file, no --force | Prompts for overwrite |

### AC-26: `--db PATH` with export --id

| Test | Input | Expected |
|---|---|---|
| export --id custom db | `--db /tmp/test.db --id 1` | Reads from tmp db |

### AC-27, AC-28, AC-29: `--db PATH` global flag

| Test | Input | Expected |
|---|---|---|
| --db uses custom db | `--db /tmp/custom.db brewlog add ...` | Brew stored in /tmp/custom.db |
| --db creates file | `--db /tmp/new.db` (doesn't exist) | File created on first command |
| no --db uses default | No --db flag | Uses ~/.brewlog/brews.db |

### AC-30: `--db` parent directory validation

| Test | Input | Expected |
|---|---|---|
| --db nonexistent parent | `--db /nonexistent/dir/x.db` | Error message to stderr, exit 1 |

### AC-31: `--db PATH` works with all commands

| Test | Input | Expected |
|---|---|---|
| --db with add | `--db /tmp/t.db add ...` | Writes to tmp db |
| --db with list | `--db /tmp/t.db list` | Reads from tmp db |
| --db with show | `--db /tmp/t.db show 1` | Reads from tmp db |
| --db with update | `--db /tmp/t.db update 1 --notes x` | Updates in tmp db |
| --db with delete | `--db /tmp/t.db delete 1 --force` | Deletes from tmp db |
| --db with stats | Already covered in AC-5 | |
| --db with search | Already covered in AC-14 | |
| --db with export | Already covered in AC-26 | |
| --db with import | Already covered in AC-20 | |

### AC-32: `--db PATH` traversal rejection

| Test | Input | Expected |
|---|---|---|
| --db contains .. | `--db ../other.db` | Error message to stderr, exit 1 |

### AC-33: `--db` in help text

| Test | Input | Expected |
|---|---|---|
| --db in help | `brewlog --help` | `--db PATH` option appears in output |

### AC-34: v0.6 export version

| Test | Input | Expected |
|---|---|---|
| export writes v0.6 | `brewlog export /tmp/out.yaml` | File contains `brewspec_version: '0.6'` |

### AC-35: import rejects non-v0.6

| Test | Input | Expected |
|---|---|---|
| import v0.5 file | File with `brewspec_version: "0.5"` | Rejected with error message, exit 1 |
| import v0.4 file | File with `brewspec_version: "0.4"` | Rejected with error message, exit 1 |
| import unknown version | File with `brewspec_version: "99"` | Rejected with error message, exit 1 |

### AC-36: rejection message content

| Test | Input | Expected |
|---|---|---|
| rejection message v0.5 | Import v0.5 file | Message contains "BrewSpec v0.5", lists 5 migration steps, references github URL |

### AC-37, AC-38: `--brew-ratio`

| Test | Input | Expected |
|---|---|---|
| brew-ratio valid | `--brew-ratio 15.5` | Stored in DB, no error |
| brew-ratio zero | `--brew-ratio 0` | Error message, exit 1 |
| brew-ratio negative | `--brew-ratio -1.0` | Error message, exit 1 |
| brew-ratio update | `update --brew-ratio 16.0` | Updates row, no error |

### AC-39: `brew_ratio` column migration

| Test | Input | Expected |
|---|---|---|
| column exists post-migration | Open DB (new or existing) | `brew_ratio REAL` column present |

### AC-40: `brew_ratio` display in show

| Test | Input | Expected |
|---|---|---|
| show with ratio | Brew with brew_ratio=15.5 | "Brew Ratio: 15.5" in output |
| show without ratio | Brew without brew_ratio | "Brew Ratio" label absent from output |

### AC-41: `brew_ratio` not in list

| Test | Input | Expected |
|---|---|---|
| list no ratio column | Brews with brew_ratio set | "Brew Ratio" column absent from list output |

### AC-42: `brew_ratio` in export/import

| Test | Input | Expected |
|---|---|---|
| export serialises ratio | Brew with brew_ratio stored | Exported YAML contains `brew_ratio: 15.5` |
| import reads ratio | YAML with brew_ratio | Value stored in brew_ratio column |

### AC-43: `brew_ratio` in column allowlist

| Test | Input | Expected |
|---|---|---|
| update_brew with brew_ratio | `updates={"brew_ratio": 15.5}` | No assertion error; update succeeds |

### AC-44: `coffee_origins` migration from string array

| Test | Input | Expected |
|---|---|---|
| migration string to object | Row with `coffee_origin='["Ethiopia"]'` and NULL `coffee_origins` | After migration, `coffee_origins='[{"country":"Ethiopia"}]'` |
| migration skips existing | Row already has `coffee_origins` | Row unchanged |

### AC-45, AC-46: structured origin flags on add

| Test | Input | Expected |
|---|---|---|
| origin-country flag | `--origin-country Ethiopia` | Stored as `[{"country":"Ethiopia"}]` in coffee_origins |
| origin multiple flags | `--origin-country Ethiopia --origin-region Yirgacheffe` | Single origin object with both fields |
| origin-varietal | `--origin-varietal Heirloom` | Stored in origin object |
| multi-origin blend | `--origin-country Ethiopia --origin-country Colombia` | Two origin objects in array |
| mixed length flags | `--origin-country Ethiopia --origin-country Colombia --origin-region Yirgacheffe` | First origin has region, second does not |

### AC-47: origin flags on update replace all origins

| Test | Input | Expected |
|---|---|---|
| update origin replaces | Brew with 2 origins, `update --origin-country Brazil` | coffee_origins has only 1 entry: Brazil |

### AC-48: structured origin display in show

| Test | Input | Expected |
|---|---|---|
| single origin show | Brew with 1 origin, country+region+varietal | "Origin:", "Country:", "Region:", "Varietal:" displayed |
| blend show | Brew with 2 origins | "Origin 1:", "Origin 2:" displayed |
| empty fields omitted | Origin with only country | Only "Country:" shown, no empty labels |

### AC-49: export legacy coffee_origin to v0.6

| Test | Input | Expected |
|---|---|---|
| export legacy origin | Row with coffee_origin '["Ethiopia"]' and NULL coffee_origins | Exported `coffee.origins: [{country: Ethiopia}]` |

### AC-50: import reads coffee.origins

| Test | Input | Expected |
|---|---|---|
| import v0.6 origins | YAML with coffee.origins array | Stored as JSON in coffee_origins column |
| import does not write coffee_origin | v0.6 file | coffee_origin column NULL for imported row |

### AC-50a, AC-50b, AC-50c, AC-50d, AC-50e, AC-50f: `coffee.name`

| Test | Input | Expected |
|---|---|---|
| add with coffee-name | `--coffee-name "Ethiopia Yirgacheffe"` | Stored in coffee_name column |
| add empty coffee-name | `--coffee-name ""` | Error, exit 1 |
| show coffee-name first | Brew with coffee_name | "Name:" appears before "Roast Date:" in Coffee section |
| export coffee-name | Brew with coffee_name | Exported as `coffee.name` |
| import coffee.name | YAML with coffee.name | Stored in coffee_name column |
| update coffee-name | `update --coffee-name "New Name"` | Updates coffee_name |

### AC-50g, AC-50h, AC-50i: `--origin-varietal`

| Test | Input | Expected |
|---|---|---|
| add origin-varietal | `--origin-country Ethiopia --origin-varietal Heirloom` | Origin object contains `"varietal": "Heirloom"` |
| add empty origin-varietal | `--origin-varietal ""` | Error, exit 1 |
| show varietal in origin block | Brew with varietal in origin | "Varietal:" shown in origin block |
| export varietal | Origin object with varietal | Exported as `varietal` in origin object |
| import varietal | YAML with origins[].varietal | Stored in coffee_origins JSON |

### AC-51, AC-52: new equipment columns

| Test | Input | Expected |
|---|---|---|
| equipment_grinder_setting column | Open fresh DB | `equipment_grinder_setting REAL` column exists |
| equipment_notes column | Open fresh DB | `equipment_notes TEXT` column exists |

### AC-53, AC-54: equipment flags on add/update

| Test | Input | Expected |
|---|---|---|
| grinder-setting valid | `--grinder-setting 21` | Stored as REAL 21.0 |
| grinder-setting float | `--grinder-setting 5.2` | Stored as REAL 5.2 |
| grinder-setting zero | `--grinder-setting 0` | Error, exit 1 |
| grinder-setting negative | `--grinder-setting -1` | Error, exit 1 |
| equipment-notes valid | `--equipment-notes "Burrs replaced"` | Stored in equipment_notes |
| equipment-notes empty | `--equipment-notes ""` | Error, exit 1 |
| update grinder-setting | `update --grinder-setting 22` | Updates column |

### AC-55: equipment display in show

| Test | Input | Expected |
|---|---|---|
| show grinder setting | Brew with grinder_setting=21 | "Grinder Setting: 21.0" in Equipment section |
| show equipment notes | Brew with equipment_notes="Burrs old" | "Notes: Burrs old" in Equipment section |
| has_equipment triggers on setting | Brew with only grinder_setting, no grinder/brewer | Equipment section shown |

### AC-56: equipment serialisation

| Test | Input | Expected |
|---|---|---|
| export grinder_setting | Brew with grinder_setting=21.0 | Exported as `equipment.grinder_setting: 21.0` (number) |
| import grinder_setting | YAML with `grinder_setting: 21` | Stored as REAL 21.0 |
| export equipment_notes | Brew with equipment_notes | Exported as `equipment.notes` |

### AC-57: equipment in column allowlist

| Test | Input | Expected |
|---|---|---|
| update_brew equipment_grinder_setting | `updates={"equipment_grinder_setting": 21.0}` | No assertion error |
| update_brew equipment_notes | `updates={"equipment_notes": "text"}` | No assertion error |

### AC-58, AC-59, AC-60: interactive type on update

| Test | Input | Expected |
|---|---|---|
| update --type "" interactive | `--type "" ` with mock input "3" | Type set to "immersion" (3rd in alpha order) |
| update --type value direct | `--type pour_over` | Type updated, no prompt |
| update no --type flag | No --type flag | No type change |
| update --type invalid | `--type badtype` | Error, exit 1 |
| update --type "" invalid choice | Input "9" | Re-prompts |
| update --type "" ctrl-c | KeyboardInterrupt during prompt | No DB update, exit non-zero |

### AC-61, AC-62, AC-63: version bump

| Test | Input | Expected |
|---|---|---|
| version output | `brewlog --version` | "BrewLog, version 0.5.0" |
| welcome screen | `brewlog` (bare) | "BrewLog v0.5.0" in output |
| __version__ | `from brewlog import __version__` | `__version__ == "0.5.0"` |

### Migration tests

| Test | Input | Expected |
|---|---|---|
| grinder_setting string coercion | DB row with equipment_grinder_setting="21 clicks" | After migration, stored as 21.0 |
| grinder_setting unparseable | Row with equipment_grinder_setting="five clicks" | After migration, stored as NULL |
| grinder_setting already REAL | Row with equipment_grinder_setting=21.0 | Unchanged |

---

## 8. Security Considerations

**Input validation:**

- `brewlog search QUERY`: The QUERY value is wrapped as `%query%` in Python and passed as a single parameter to the SQL `LIKE ?` clause. The query string is never interpolated into the SQL string. This prevents SQL injection regardless of query content (AC-13).
- `--brew-ratio`, `--grinder-setting`: validated as positive floats before DB write. Pydantic validators enforce the constraint at model construction.
- `--coffee-name`, `--equipment-notes`, `--origin-varietal`: validated as non-empty strings before DB write. Pydantic validators enforce `len(v.strip()) > 0` and `maxLength` per spec.
- `--db PATH`: validated for `..` traversal and parent directory existence before any DB open. The validation runs in the root group callback, before any subcommand executes (AC-30, AC-32). The path is resolved to a `Path` object before passing to `get_connection()`.

**File I/O:**

- Import path: existing `validate_import_path()` rejects `..` and enforces the 10MB size limit. No change to this function.
- Export path: existing `validate_export_path()` rejects `..` and enforces allowed extensions. No change.
- `--db PATH`: validated via new `validate_db_path()` which rejects `..` and requires the parent directory to exist.
- `yaml.safe_load()` is used for all YAML parsing — `yaml.load()` is never used. No change.

**SQL:**

- `search_brews()`: uses `LIKE ?` with parameterised placeholders. The `%query%` pattern is constructed in Python and passed as a parameter — never as part of the SQL string.
- `_brew_exists()` in import deduplication: uses `?` placeholders for all four comparison values.
- `get_brew_stats()`: all queries are read-only and have no user-supplied parameters.
- `update_brew()`: the column allowlist (`UPDATABLE_COLUMNS`) guards against unexpected column names. Column names come from application code (CLI flag name -> column name mapping), never from user input directly. The assertion `set(updates.keys()).issubset(UPDATABLE_COLUMNS)` is defence-in-depth.
- `_apply_migrations()` new steps: migration queries use `?` placeholders for ID and value parameters. The column name string (`equipment_grinder_setting`) is hardcoded, not user-supplied.

**Data integrity:**

- Import deduplication uses a transaction: if any insert fails, the entire import rolls back. Partial imports are not possible.
- The `coffee_origin` -> `coffee_origins` migration is idempotent (skips rows where `coffee_origins` is already set) and transactional (committed alongside column additions). A failed migration attempt leaves the DB in its pre-migration state.
- `grinder_setting` string-to-REAL coercion: values that cannot be parsed to a positive number are set to NULL rather than causing an error, preserving the row.

**Error messages:**

- Error messages do not expose internal file system paths beyond what the user supplied. The DB path in `--db` errors echoes only what the user provided.
- Stack traces are never surfaced to the user. All exception handling uses `click.echo(..., err=True)` and `sys.exit(1)`.
- Import schema validation errors echo the schema error messages from `jsonschema` (which contain field paths from the document, not internal paths). This is acceptable — the user provided the document.

**Trust boundary:**

```
User input (CLI flags, QUERY argument, file paths, YAML/JSON file content)
  -> CLI validation layer (type checks, empty-string checks, range checks)
  -> Pydantic model construction (BrewInput, CoffeeInput, EquipmentInput, etc.)
  -> DB write (parameterised SQL only)
  -> DB read (parameterised SQL only)
  -> Serialise to BrewSpec dict (no user values interpolated into SQL or file paths)
  -> Schema validation gate (before file write)
  -> File write (validated path, resolved Path object)
```

No user input crosses a trust boundary without validation at the CLI or Pydantic layer.

---

## 9. TDD Implementation Order

1. Write failing tests for `--db PATH` global flag (AC-27 through AC-33). Implement `validate_db_path()`, update `cli.py`, update all commands to accept `db_path` from context.

2. Write failing tests for DB migration correctness: `equipment_grinder_setting` coercion, `coffee_origin` -> `coffee_origins` object migration. Implement migration steps in `_apply_migrations()`.

3. Write failing tests for `brewlog stats` (AC-1 through AC-5). Implement `get_brew_stats()` in `db.py` and `stats.py` command.

4. Write failing tests for `brewlog search` (AC-6 through AC-14). Implement `search_brews()` in `db.py` and `search.py` command.

5. Write failing tests for import deduplication (AC-15 through AC-20). Implement `_brew_exists()` and dedup loop in `import_.py`.

6. Write failing tests for single-brew export (AC-21 through AC-26). Implement `--id N` flag in `export.py`.

7. Write failing tests for `brew_ratio` (AC-37 through AC-43). Implement `--brew-ratio` flag in `add.py` and `update.py`; update `show.py`.

8. Write failing tests for `coffee.name` (AC-50a through AC-50f). Implement `--coffee-name` flag in `add.py` and `update.py`; update `show.py` Coffee section.

9. Write failing tests for structured origin flags and `--origin-varietal` (AC-44 through AC-50, AC-50g through AC-50i). Implement origin flag set in `add.py` and `update.py`; update `show.py` origin display; update `serialise.py` legacy fallback.

10. Write failing tests for equipment flags (AC-51 through AC-57). Implement `--grinder-setting` and `--equipment-notes` in `add.py` and `update.py`; update `show.py` equipment section.

11. Write failing tests for interactive `--type` on update (AC-58 through AC-60). Extract `_prompt_brew_type()` to `prompts.py`; implement interactive sentinel in `update.py`.

12. Write failing tests for version bump (AC-61 through AC-63). Update `__init__.py` and `pyproject.toml`.

13. Run the full test suite — confirm all tests pass.

14. Run `ruff check .` — fix any lint errors.
