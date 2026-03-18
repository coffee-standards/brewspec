# Technical Design: BrewLog CLI v0.3

**Feature:** brewlog-cli-v0.3
**Author:** architect
**Created:** 2026-02-22
**Input:** specs/products/brewlog-cli-v0.3.md
**Baseline:** specs/designs/brewlog-cli-v0.2.md
**Status:** Ready for Dev

---

## Overview

BrewLog CLI v0.3 advances the CLI from BrewSpec v0.3 targeting to full BrewSpec v0.4 compliance and delivers two carry-forward improvements from the v0.2 review. The existing codebase at `brewspec/brewlog/` is already substantially advanced beyond the v0.2 design: the DB schema already uses flat `result_*` columns (not the legacy `tds`, `ey`, `rating` flat columns described in the spec), the Pydantic models already include `RatingsInput` and `ResultInput`, and `serialise.py` already produces v0.4-structured export documents. The v0.3 task is therefore primarily about: (1) replacing the `--overall` flag convention with the `--rating-overall` / `--rating-*` naming the spec requires, (2) retiring `--rating`, (3) adding the seven remaining rating dimension flags, (4) adding `--until` to `brewlog list`, (5) adding `--rating-min` / `--rating-max` filters, (6) hardening `update_brew()` with a column allowlist assertion, (7) updating the date prompt default to `YYYY-MM-DD`, (8) updating the import command to reject non-v0.4 files with a specific error message, and (9) updating `brewlog show` and `brewlog list` display to match the spec.

**Important baseline finding:** The DB schema does NOT contain the legacy `tds`, `ey`, or `rating` flat columns. The current implementation already uses `result_tds`, `result_ey`, `result_brix`, `result_tasting_notes`, and `result_ratings` (JSON-encoded ratings dict). This simplifies the migration significantly: no backward-compatibility logic for a legacy `rating` column is needed. AC-22's "architect's discretion" clause is exercised: the legacy `rating` column is not introduced. See ADR-1.

---

## 1. Changes Required

### 1.1 DB schema migration (`db.py` — `_init_schema`)

**What changes:** The current `_init_schema` uses `CREATE TABLE IF NOT EXISTS` with the v0.4 columns already present (`result_tds`, `result_ey`, `result_brix`, `result_tasting_notes`, `result_ratings`). The v0.3 task replaces the single JSON `result_ratings` column with 8 individual integer columns — one per SCA rating dimension.

**Migration strategy:** Add an `_apply_migrations` function called from `get_connection` after `_init_schema`. The migration function uses `PRAGMA table_info(brews)` to detect which columns are missing, then issues `ALTER TABLE brews ADD COLUMN` for each missing column. Existing data is never modified or dropped.

**Columns being replaced (JSON column → individual columns):**

The existing `result_ratings TEXT` column (JSON-encoded dict) is superseded by 8 individual integer columns. The `result_ratings` column is **retained** in the DB for backward-compatibility with rows written by v0.2 — these rows cannot be altered. On read, show and list commands check `result_rating_overall` first, then fall back to parsing `result_ratings` JSON. On write (insert and update), all new writes go to the individual columns; `result_ratings` is no longer written.

**New columns added by migration:**

```sql
ALTER TABLE brews ADD COLUMN result_rating_overall   INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_fragrance INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_aroma     INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_flavour   INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_aftertaste INTEGER; -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_acidity   INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_sweetness INTEGER;  -- optional, 1-5
ALTER TABLE brews ADD COLUMN result_rating_mouthfeel INTEGER;  -- optional, 1-5
```

**Migration function pattern:**

```python
_V3_MIGRATION_COLUMNS = {
    "result_rating_overall":   "INTEGER",
    "result_rating_fragrance": "INTEGER",
    "result_rating_aroma":     "INTEGER",
    "result_rating_flavour":   "INTEGER",
    "result_rating_aftertaste": "INTEGER",
    "result_rating_acidity":   "INTEGER",
    "result_rating_sweetness": "INTEGER",
    "result_rating_mouthfeel": "INTEGER",
}

def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Add any missing v0.3 columns without modifying existing data."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(brews)").fetchall()
    }
    for col, col_type in _V3_MIGRATION_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE brews ADD COLUMN {col} {col_type}")
    conn.commit()
```

`get_connection` calls `_init_schema(conn)` then `_apply_migrations(conn)`. Both functions are idempotent.

**`_init_schema` change:** The `CREATE TABLE IF NOT EXISTS` statement keeps `result_ratings TEXT` (for databases created fresh by v0.3, the column is still present for compatibility). The 8 new columns are also added to the CREATE TABLE for fresh installations, so `_apply_migrations` finds them already present and is a no-op on fresh DBs.

The full updated `CREATE TABLE` statement (fresh install):

```sql
CREATE TABLE IF NOT EXISTS brews (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    date                    TEXT    NOT NULL,
    type                    TEXT    NOT NULL,
    method                  TEXT,
    dose_g                  REAL    NOT NULL,
    water_weight_g          REAL    NOT NULL,
    water_volume_ml         REAL,
    water_temp_c            REAL,
    grind                   TEXT,
    duration_s              INTEGER,
    notes                   TEXT,
    coffee_roast_date       TEXT,
    coffee_type             TEXT,
    coffee_origin           TEXT,
    coffee_varietal         TEXT,
    coffee_process          TEXT,
    water_ppm               REAL,
    equipment_grinder       TEXT,
    equipment_brewer        TEXT,
    result_tds              REAL,
    result_ey               REAL,
    result_brix             REAL,
    result_tasting_notes    TEXT,
    result_ratings          TEXT,
    result_rating_overall   INTEGER,
    result_rating_fragrance INTEGER,
    result_rating_aroma     INTEGER,
    result_rating_flavour   INTEGER,
    result_rating_aftertaste INTEGER,
    result_rating_acidity   INTEGER,
    result_rating_sweetness INTEGER,
    result_rating_mouthfeel INTEGER
);
CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
```

---

### 1.2 Column allowlist in `update_brew()` (`db.py`)

**What changes:** Add a module-level `UPDATABLE_COLUMNS` frozenset constant and an assertion inside `update_brew()` before the SQL is constructed.

**Module-level constant:**

```python
UPDATABLE_COLUMNS: frozenset[str] = frozenset({
    "method",
    "grind",
    "water_temp_c",
    "duration_s",
    "notes",
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
    "coffee_origin",
    "coffee_varietal",
    "coffee_process",
    "water_ppm",
    "equipment_grinder",
    "equipment_brewer",
})
```

**Assertion inside `update_brew()` — insert before the SET clause is built:**

```python
assert set(updates.keys()).issubset(UPDATABLE_COLUMNS), (
    f"Unexpected column names in update dict: "
    f"{set(updates.keys()) - UPDATABLE_COLUMNS}"
)
```

This assertion fires on programming errors (e.g., a sentinel key leaking into the updates dict) before any SQL is constructed. It does not catch values; only column name safety.

---

### 1.3 `--rating-*` flags — rename from `--overall` to `--rating-overall` + add 7 dimensions (`commands/add.py` and `commands/update.py`)

**Context:** The existing `add` and `update` commands have `--overall` for the overall rating only. The spec requires `--rating-overall` plus seven additional dimension flags (`--rating-fragrance`, `--rating-aroma`, `--rating-flavour`, `--rating-aftertaste`, `--rating-acidity`, `--rating-sweetness`, `--rating-mouthfeel`). The old `--overall` option is removed. A retired `--rating` option is added that produces an error on use (not a valid alias).

**`commands/add.py` option changes:**

Remove:
```python
@click.option("--overall", "overall", type=int, default=None,
              help="Overall rating 1-5.")
```

Add (8 new options, replacing the removed one):
```python
@click.option("--rating", "rating_retired", type=int, default=None, hidden=True)
@click.option("--rating-overall",    "rating_overall",    type=int, default=None,
              help="Overall impression, 1-5.")
@click.option("--rating-fragrance",  "rating_fragrance",  type=int, default=None,
              help="Fragrance rating, 1-5.")
@click.option("--rating-aroma",      "rating_aroma",      type=int, default=None,
              help="Aroma rating, 1-5.")
@click.option("--rating-flavour",    "rating_flavour",    type=int, default=None,
              help="Flavour rating, 1-5.")
@click.option("--rating-aftertaste", "rating_aftertaste", type=int, default=None,
              help="Aftertaste rating, 1-5.")
@click.option("--rating-acidity",    "rating_acidity",    type=int, default=None,
              help="Acidity rating, 1-5.")
@click.option("--rating-sweetness",  "rating_sweetness",  type=int, default=None,
              help="Sweetness rating, 1-5.")
@click.option("--rating-mouthfeel",  "rating_mouthfeel",  type=int, default=None,
              help="Mouthfeel rating, 1-5.")
```

The `--rating` option is declared `hidden=True` so it does not appear in `--help`, but Click still parses it if supplied, allowing the command body to detect it and emit the retirement error before doing anything else.

**`add` function signature change:**

Replace `overall` parameter with:
```
rating_retired, rating_overall, rating_fragrance, rating_aroma, rating_flavour,
rating_aftertaste, rating_acidity, rating_sweetness, rating_mouthfeel
```

**`--rating` retirement check — insert at the top of the function body, before the interactive-mode tip:**

```python
if rating_retired is not None:
    click.echo(
        "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
        "Use --rating-overall N to set your overall impression (1-5).\n"
        "See --help for all available rating dimension flags.",
        err=True,
    )
    sys.exit(1)
```

**Interactive tip update (AC-30):**

```python
if date is None and brew_type is None and dose is None and water_weight is None:
    click.echo(
        'Tip: add optional details with flags, e.g. --method "V60" --rating-overall 4'
        ' --tasting-notes "Bright acidity"  (run --help for all options)'
    )
```

**Rating validation (replace existing `overall` validation):**

```python
_RATING_DIMS = {
    "rating_overall":    rating_overall,
    "rating_fragrance":  rating_fragrance,
    "rating_aroma":      rating_aroma,
    "rating_flavour":    rating_flavour,
    "rating_aftertaste": rating_aftertaste,
    "rating_acidity":    rating_acidity,
    "rating_sweetness":  rating_sweetness,
    "rating_mouthfeel":  rating_mouthfeel,
}
for flag_name, flag_val in _RATING_DIMS.items():
    if flag_val is not None and not (1 <= flag_val <= 5):
        click.echo(
            f"Error: --{flag_name.replace('_', '-')} must be an integer between 1 and 5.",
            err=True,
        )
        sys.exit(1)
```

**RatingsInput construction (replace existing `ratings_obj` block):**

```python
has_any_rating = any(v is not None for v in _RATING_DIMS.values())
ratings_obj = None
if has_any_rating:
    try:
        ratings_obj = RatingsInput(
            overall=rating_overall,
            fragrance=rating_fragrance,
            aroma=rating_aroma,
            flavour=rating_flavour,
            aftertaste=rating_aftertaste,
            acidity=rating_acidity,
            sweetness=rating_sweetness,
            mouthfeel=rating_mouthfeel,
        )
    except ValidationError as exc:
        click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        sys.exit(1)
```

**`has_result` check update:**

```python
has_result = any(v is not None for v in (tds, ey, brix, tasting_notes)) or has_any_rating
```

**`commands/update.py` option changes:**

Same pattern as `add`: remove `--overall`, add `--rating` (hidden, retired) plus all 8 `--rating-*` options. The retirement error check fires before any other validation. The seven dimension flags are validated the same way as in `add`. The update dict construction changes:

Replace the existing `--overall` / `_overall` sentinel pattern:
```python
# Old pattern (remove):
if overall is not None:
    updates["_overall"] = overall  # sentinel; handled below
# ... and the subsequent merge-into-JSON block
```

New pattern (add individual columns directly):
```python
if rating_overall is not None:
    updates["result_rating_overall"] = rating_overall
if rating_fragrance is not None:
    updates["result_rating_fragrance"] = rating_fragrance
if rating_aroma is not None:
    updates["result_rating_aroma"] = rating_aroma
if rating_flavour is not None:
    updates["result_rating_flavour"] = rating_flavour
if rating_aftertaste is not None:
    updates["result_rating_aftertaste"] = rating_aftertaste
if rating_acidity is not None:
    updates["result_rating_acidity"] = rating_acidity
if rating_sweetness is not None:
    updates["result_rating_sweetness"] = rating_sweetness
if rating_mouthfeel is not None:
    updates["result_rating_mouthfeel"] = rating_mouthfeel
```

The entire `_overall` sentinel block and the read-before-write connection that fetches existing `result_ratings` JSON is removed. The update command no longer needs to read before write for rating updates.

---

### 1.4 `insert_brew` and `insert_brew_dict` — store individual rating columns (`db.py`)

**What changes:** Both insert functions currently store ratings as a JSON string in `result_ratings`. They must be updated to store ratings in the 8 individual `result_rating_*` columns instead.

**`insert_brew` changes:**

Remove the JSON serialisation block:
```python
# Remove:
result_ratings_json = None
if result and result.ratings:
    ratings_dict = {
        k: v for k, v in result.ratings.model_dump().items()
        if v is not None
    }
    if ratings_dict:
        result_ratings_json = json.dumps(ratings_dict)
```

Expand the INSERT column list and params tuple:

```sql
INSERT INTO brews (
    date, type, method, dose_g, water_weight_g,
    water_volume_ml, water_temp_c, grind, duration_s,
    notes,
    coffee_roast_date, coffee_type, coffee_origin,
    coffee_varietal, coffee_process,
    water_ppm,
    equipment_grinder, equipment_brewer,
    result_tds, result_ey, result_brix,
    result_tasting_notes,
    result_rating_overall, result_rating_fragrance, result_rating_aroma,
    result_rating_flavour, result_rating_aftertaste, result_rating_acidity,
    result_rating_sweetness, result_rating_mouthfeel
) VALUES (
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?,
    ?, ?, ?,
    ?, ?,
    ?,
    ?, ?,
    ?, ?, ?,
    ?,
    ?, ?, ?,
    ?, ?, ?,
    ?, ?
)
```

Params tuple (result section):
```python
ratings = result.ratings if result else None
params = (
    brew.date, brew.type, brew.method, brew.dose_g, brew.water_weight_g,
    brew.water_volume_ml, brew.water_temp_c, brew.grind, brew.duration_s,
    brew.notes,
    coffee.roast_date if coffee else None,
    coffee.type if coffee else None,
    json.dumps(coffee.origin) if (coffee and coffee.origin) else None,
    coffee.varietal if coffee else None,
    coffee.process if coffee else None,
    water.ppm if water else None,
    equipment.grinder if equipment else None,
    equipment.brewer if equipment else None,
    result.tds if result else None,
    result.ey if result else None,
    result.brix if result else None,
    result.tasting_notes if result else None,
    ratings.overall if ratings else None,
    ratings.fragrance if ratings else None,
    ratings.aroma if ratings else None,
    ratings.flavour if ratings else None,
    ratings.aftertaste if ratings else None,
    ratings.acidity if ratings else None,
    ratings.sweetness if ratings else None,
    ratings.mouthfeel if ratings else None,
)
```

Note: `result_ratings` TEXT column is no longer written by new inserts. Old rows still have their `result_ratings` JSON populated (from v0.2 writes). The column is retained in the schema.

**`insert_brew_dict` changes:**

Same expansion. The `ratings` dict from the import document maps to individual columns:

```python
ratings = result.get("ratings") or {}
params = (
    ...
    result.get("tds"),
    result.get("ey"),
    result.get("brix"),
    result.get("tasting_notes"),
    ratings.get("overall"),
    ratings.get("fragrance"),
    ratings.get("aroma"),
    ratings.get("flavour"),
    ratings.get("aftertaste"),
    ratings.get("acidity"),
    ratings.get("sweetness"),
    ratings.get("mouthfeel"),
)
```

---

### 1.5 Date prompt default — `YYYY-MM-DD` today (`commands/add.py`)

**What changes:** `_prompt_date()` currently defaults to `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`. Change the default to today's local date in `YYYY-MM-DD` format.

**Updated `_prompt_date()`:**

```python
def _prompt_date() -> str:
    """Prompt for a date with today's date as default. Re-prompts on invalid input."""
    from datetime import date as _date
    default = _date.today().strftime("%Y-%m-%d")
    while True:
        value = click.prompt("Date", default=default)
        if DATE_PATTERN.match(value):
            if "T" in value:
                try:
                    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    return value
                except ValueError:
                    pass
            else:
                return value
        click.echo(
            "  Error: date must be YYYY-MM-DD (e.g. 2026-02-22) "
            "or YYYY-MM-DDTHH:MM:SSZ (e.g. 2026-02-22T09:15:00Z)"
        )
```

The error message is updated to show both accepted formats with concrete examples. The prompt display is `Date [2026-02-22]:` (Click renders the default in brackets automatically).

---

### 1.6 `--since` and `--until` date filter comparison strategy (`db.py` — `list_brews_filtered`)

**Context:** The DB stores dates as either `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`. The existing `--since` filter already compares as `date >= ?` with the raw `YYYY-MM-DD` string. This works correctly for `YYYY-MM-DDTHH:MM:SSZ` dates because lexicographic ordering of ISO 8601 is correct — but only if the `--since` value is also a full datetime string. Passing a `YYYY-MM-DD` string to `date >= ?` when the stored value is `YYYY-MM-DDTHH:MM:SSZ` works correctly only by coincidence of the format: `"2026-02-01T..."` sorts after `"2026-02-01"` because `T` has a higher ASCII value than any digit.

However, the spec now requires both stored formats and day-granularity comparison. The safe approach uses `substr(date, 1, 10)` on both sides to normalise to `YYYY-MM-DD` before comparing.

**Updated filter conditions:**

```python
# --since: brews on or after this calendar day (inclusive)
if since is not None:
    conditions.append("substr(date, 1, 10) >= ?")
    params.append(since)

# --until: brews on or before this calendar day (inclusive)
if until is not None:
    conditions.append("substr(date, 1, 10) <= ?")
    params.append(until)
```

Both `since` and `until` are `YYYY-MM-DD` strings (validated before the DB call). `substr(date, 1, 10)` extracts the date prefix from both stored formats. The comparison is therefore format-agnostic and correctly implements day-granularity filtering.

**`list_brews_filtered` signature change:**

```python
def list_brews_filtered(
    conn: sqlite3.Connection,
    limit: int = 20,
    all_rows: bool = False,
    brew_type: str | None = None,
    since: str | None = None,
    until: str | None = None,
    rating_min: int | None = None,
    rating_max: int | None = None,
) -> list[sqlite3.Row]:
```

**New filter conditions added:**

```python
if rating_min is not None:
    conditions.append("result_rating_overall >= ?")
    params.append(rating_min)

if rating_max is not None:
    conditions.append("result_rating_overall <= ?")
    params.append(rating_max)
```

All condition strings are static. Only parameter values come from user input.

---

### 1.7 `brewlog list` — `--until`, `--rating-min`, `--rating-max` flags (`commands/list_.py`)

**New `@click.option` declarations:**

```python
@click.option(
    "--until", "until", type=str, default=None,
    help="Filter brews on or before this date (YYYY-MM-DD).",
)
@click.option(
    "--rating-min", "rating_min", type=int, default=None,
    help="Filter brews with overall rating >= N (1-5).",
)
@click.option(
    "--rating-max", "rating_max", type=int, default=None,
    help="Filter brews with overall rating <= N (1-5).",
)
```

**Command signature change:**

```python
def list_cmd(
    limit: int, show_all: bool,
    brew_type: str | None, since: str | None, until: str | None,
    rating_min: int | None, rating_max: int | None,
) -> None:
```

**Validation additions (insert after existing `--since` validation):**

```python
import re as _re
_DATE_PATTERN = _re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Validate --until
if until is not None:
    try:
        datetime.strptime(until, "%Y-%m-%d")
    except ValueError:
        click.echo(
            f"Error: --until '{until}' is not a valid date. Use YYYY-MM-DD format.",
            err=True,
        )
        sys.exit(1)

# Validate --since / --until ordering
if since is not None and until is not None and since > until:
    click.echo(
        "Error: --since must not be later than --until.",
        err=True,
    )
    sys.exit(1)

# Validate --rating-min
if rating_min is not None and not (1 <= rating_min <= 5):
    click.echo(
        "Error: --rating-min must be an integer between 1 and 5.",
        err=True,
    )
    sys.exit(1)

# Validate --rating-max
if rating_max is not None and not (1 <= rating_max <= 5):
    click.echo(
        "Error: --rating-max must be an integer between 1 and 5.",
        err=True,
    )
    sys.exit(1)

# Validate --rating-min / --rating-max ordering
if rating_min is not None and rating_max is not None and rating_min > rating_max:
    click.echo(
        "Error: --rating-min must not exceed --rating-max.",
        err=True,
    )
    sys.exit(1)
```

**DB call update — always use `list_brews_filtered` (simplification):**

```python
has_filters = any([
    brew_type is not None, since is not None, until is not None,
    rating_min is not None, rating_max is not None,
])

conn = db.get_connection()
try:
    rows = db.list_brews_filtered(
        conn,
        limit=limit,
        all_rows=show_all,
        brew_type=brew_type,
        since=since,
        until=until,
        rating_min=rating_min,
        rating_max=rating_max,
    )
finally:
    conn.close()
```

`list_brews` is no longer called by `list_cmd`. `list_brews_filtered` with no filters produces the same result as `list_brews`.

**No-match message:**

```python
if not rows:
    if has_filters:
        click.echo("No brews match the given filters.")
    else:
        click.echo("No brews logged yet. Run 'brewlog add' to get started.")
    return
```

**`Rating` column renamed to `Overall Rating`:**

In `_format_header()` and `_format_separator()`, replace the current TDS column approach. The current list table has: ID, Date, Type, Method, Dose (g), Water (g), TDS. Per the spec, the `Rating` column is renamed to `Overall Rating`. The current list table does not show a rating column at all (it shows TDS). The v0.3 design adds an `Overall Rating` column displaying `result_rating_overall`.

**Updated column layout:**

```python
_COL_ID      = 4
_COL_DATE    = 20
_COL_TYPE    = 10
_COL_METHOD  = 15
_COL_DOSE    = 9
_COL_WATER   = 10
_COL_RATING  = 14   # "Overall Rating" header, right-aligned
```

```python
def _format_header() -> str:
    return (
        f"{'ID':>{_COL_ID}}  "
        f"{'Date':<{_COL_DATE}}  "
        f"{'Type':<{_COL_TYPE}}  "
        f"{'Method':<{_COL_METHOD}}  "
        f"{'Dose (g)':>{_COL_DOSE}}  "
        f"{'Water (g)':>{_COL_WATER}}  "
        f"{'Overall Rating':>{_COL_RATING}}"
    )

def _format_row(row) -> str:
    method = row["method"] if row["method"] is not None else "-"
    # AC-38: prefer result_rating_overall; dash if absent
    overall = row["result_rating_overall"]
    rating_display = str(overall) if overall is not None else "-"
    return (
        f"{row['id']:>{_COL_ID}}  "
        f"{row['date']:<{_COL_DATE}}  "
        f"{row['type']:<{_COL_TYPE}}  "
        f"{method:<{_COL_METHOD}}  "
        f"{row['dose_g']:>{_COL_DOSE}.1f}  "
        f"{row['water_weight_g']:>{_COL_WATER}.1f}  "
        f"{rating_display:>{_COL_RATING}}"
    )
```

Note: the TDS column is removed from the list view in v0.3 (it is replaced by Overall Rating). This is a display change only; TDS data continues to be stored and displayed in `show`.

---

### 1.8 `brewlog show` — Results section update (`commands/show.py`)

**What changes:** The current `show.py` displays results from `result_tds`, `result_ey`, `result_brix`, `result_tasting_notes`, and `result_ratings` (JSON). The JSON-based ratings display loop is replaced with individual column reads. The section structure matches the spec's format exactly.

**Updated `has_results` check:**

```python
_RESULT_COLS = (
    "result_tds", "result_ey", "result_brix", "result_tasting_notes",
    "result_rating_overall", "result_rating_fragrance", "result_rating_aroma",
    "result_rating_flavour", "result_rating_aftertaste", "result_rating_acidity",
    "result_rating_sweetness", "result_rating_mouthfeel",
)
has_results = any(row[f] is not None for f in _RESULT_COLS)
```

**Updated Results section rendering (replace the existing results block):**

```python
if has_results:
    click.echo("")
    click.echo("Results")
    click.echo("-------")
    if row["result_tds"] is not None:
        _print_field("TDS (%):", row["result_tds"])
    if row["result_ey"] is not None:
        _print_field("EY (%):", row["result_ey"])
    if row["result_brix"] is not None:
        _print_field("Brix:", row["result_brix"])
    if row["result_tasting_notes"] is not None:
        _print_field("Tasting Notes:", row["result_tasting_notes"])

    _RATING_SHOW = [
        ("result_rating_overall",    "Overall"),
        ("result_rating_fragrance",  "Fragrance"),
        ("result_rating_aroma",      "Aroma"),
        ("result_rating_flavour",    "Flavour"),
        ("result_rating_aftertaste", "Aftertaste"),
        ("result_rating_acidity",    "Acidity"),
        ("result_rating_sweetness",  "Sweetness"),
        ("result_rating_mouthfeel",  "Mouthfeel"),
    ]
    has_any_rating = any(row[col] is not None for col, _ in _RATING_SHOW)
    if has_any_rating:
        click.echo(f"  {'Ratings:'}")
        for col, label in _RATING_SHOW:
            if row[col] is not None:
                click.echo(f"    {label:<14}{row[col]}")
```

The `result_ratings` JSON column is intentionally not read by `show` for new rows. However, for backward-compatible display of v0.2 rows (which have `result_ratings` populated but all `result_rating_*` columns NULL), the fallback reads the JSON:

```python
if not has_any_rating and row["result_ratings"] is not None:
    import json as _json
    legacy_ratings = _json.loads(row["result_ratings"])
    if legacy_ratings:
        click.echo(f"  {'Ratings:'}")
        for dim, val in legacy_ratings.items():
            label = dim.capitalize()
            click.echo(f"    {label:<14}{val}")
```

Also, the `has_results` check must include `result_ratings` for backward-compatible display of v0.2 rows:

```python
has_results = any(row[f] is not None for f in _RESULT_COLS) or row["result_ratings"] is not None
```

**Section header format:** The spec shows `Results` / `-------` as the separator. The current code uses `click.echo("Results")` without a separator line. Add `click.echo("-------")` after `click.echo("Results")` to match the spec output. Apply the same change to the Coffee, Water, and Equipment section headers for consistency (these all follow the same pattern in the spec output mock).

---

### 1.9 `brewlog show` — existing brew parameter display

The spec shows a slightly different format for the brew parameters section header (no "Brew parameters" header — just fields directly under the `Brew #N` / `-------` header). The current `show.py` prints "Brew parameters" as a section header. This header is removed: required fields are printed directly after the `Brew #N` header line.

**Change:** Remove the `_start_brew_params()` helper and the `"Brew parameters"` echo. Print `Date:`, `Type:`, etc. directly after the `"---..."` separator.

---

### 1.10 Import command — v0.4 version check and v0.3 rejection (`commands/import_.py`)

**What changes:** Before JSON Schema validation, the import command checks `brewspec_version` in the parsed document. If the version is not `"0.4"`, the command prints the exact error message from the spec and exits with code 1. JSON Schema validation (`schema.validate_document`) runs only if the version check passes.

**Version check — insert after `if not isinstance(doc, dict)` block, before `schema.validate_document`:**

```python
version = doc.get("brewspec_version")
if version != "0.4":
    _version_str = f'v{version}' if version else 'unknown version'
    click.echo(
        f"Error: This file uses BrewSpec {_version_str}, which is not supported by BrewLog v0.3.\n"
        "BrewLog v0.3 requires BrewSpec v0.4.\n"
        "\n"
        "To migrate your file from v0.3 to v0.4, make the following changes:\n"
        "  1. Change 'brewspec_version' from \"0.3\" to \"0.4\"\n"
        "  2. Move 'tds' (if present) from the brew level to 'result.tds'\n"
        "  3. Move 'ey' (if present) from the brew level to 'result.ey'\n"
        "  4. Move 'rating' (if present) from the brew level to 'result.ratings.overall'\n"
        "  5. Replace any freeform 'grind' values with one of:\n"
        "     turkish, espresso, fine, medium_fine, medium, medium_coarse, coarse\n"
        "     (or remove the 'grind' field if no match applies)\n"
        "\n"
        "Full migration guide: https://github.com/coffee-standards/brewspec",
        err=True,
    )
    sys.exit(1)
```

The error message is written to stderr (`err=True`). Exit code is 1. No rows are written.

**Detection logic:** The check is on the raw `brewspec_version` value from the parsed document. If the document is missing the key entirely (`version is None`), the same rejection path fires with `"unknown version"` in the message. This is correct: only version `"0.4"` is accepted.

**Schema validation unchanged:** After the version check passes, `schema.validate_document(doc)` runs as before. Because the schema has `"const": "0.4"` on `brewspec_version`, the JSON Schema would also reject non-v0.4 files — but the explicit version check fires first and provides the actionable message.

**Docstring update:** Update the command docstring from `BrewSpec v0.2 YAML or JSON file` to `BrewSpec v0.4 YAML or JSON file`.

---

### 1.11 Export command — `grind` enum handling for legacy rows (`commands/export.py` / `serialise.py`)

**What changes:** The `row_to_brew_dict` function in `serialise.py` currently includes `grind` unconditionally if it is not NULL. Rows written under v0.2 may have freeform `grind` values (e.g., `"medium-fine"`, `"setting 15"`) that are not valid v0.4 enum members. Including them in the export causes the schema validation step to fail.

**Decision:** Omit the `grind` field from the exported brew record if the stored value is not a valid v0.4 enum member, and emit a warning to stderr listing the affected brew ID.

**Changes to `serialise.py`:**

Add constant:
```python
GRIND_ENUM = frozenset({
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse",
})
```

Update the optional fields loop in `row_to_brew_dict`:

```python
# Optional brew-level fields — include only if not NULL
for field in ("method", "water_volume_ml", "water_temp_c", "duration_s", "notes"):
    if r.get(field) is not None:
        brew[field] = r[field]

# grind: include only if it is a valid v0.4 enum member
if r.get("grind") is not None:
    if r["grind"] in GRIND_ENUM:
        brew["grind"] = r["grind"]
    else:
        # Return the invalid value separately so the caller can warn
        brew["_invalid_grind"] = r["grind"]
```

`row_to_brew_dict` now returns a sentinel key `_invalid_grind` when the grind value is invalid. The export command reads this key and removes it before building the final document.

**Changes to `commands/export.py` — warning emission:**

```python
# Build document dict
brews_dicts = []
warned_grind = []
for row in rows:
    brew_dict = serialise.row_to_brew_dict(row)
    if "_invalid_grind" in brew_dict:
        warned_grind.append((row["id"], brew_dict.pop("_invalid_grind")))
    brews_dicts.append(brew_dict)

if warned_grind:
    click.echo(
        "Warning: the following brews have non-standard grind values that are "
        "not valid in BrewSpec v0.4 and were omitted from the export:",
        err=True,
    )
    for brew_id, grind_val in warned_grind:
        click.echo(f"  Brew #{brew_id}: grind = '{grind_val}'", err=True)

document = {"brewspec_version": "0.4", "brews": brews_dicts}
```

This replaces the current call to `serialise.rows_to_brewspec_document(rows)` with inline construction.

---

### 1.12 `grind` enum interactive prompt on `add` (`commands/add.py`)

**What changes:** Per the spec (AC-18 carries the help text requirement; the product spec section on grind also states the interactive prompt should present a numbered menu). The existing `add` command prompts for grind only when `--grind` is not supplied — but currently there is no interactive grind prompt (it is purely flag-driven). The spec states:

> The interactive prompt on `add` (if no `--grind` flag) should present a numbered menu like the brew type menu.

However, `grind` is an optional field. The interactive prompt applies only when the user is in fully interactive mode AND explicitly wants to set a grind — but since grind is optional (not required), the prompt cannot be inserted into the required-field prompt sequence.

**Decision:** The grind field remains flag-only on `add`. No interactive grind prompt is added. The spec's key design areas note says "the interactive prompt on `add` (if no `--grind` flag) should present a numbered menu" but this conflicts with the product spec scope section which states: "Individual `brewlog add` prompts for result fields — `--brix`, `--tasting-notes`, and all `--rating-*` flags remain flag-only on `add`. Only the four required fields (`date`, `type`, `dose`, `water`) are prompted interactively." Grind is optional, not required, so it follows the same pattern. The flag help text lists all 7 accepted values (AC-18 is satisfied by the help text). See ADR-2.

---

### 1.13 `schema.py` — version reference update

**What changes:** Update the module docstring to reference v0.4 (currently says v0.2). The bundled `brewspec.schema.json` file in the `brewlog` package must be the v0.4 schema. If the packaged schema file has not yet been updated, the dev must copy the canonical v0.4 schema from the `brewspec` repo into `src/brewlog/brewspec.schema.json`.

**Schema path constant:** Add a module-level constant for the schema resource path (AC-15):

```python
SCHEMA_RESOURCE_NAME = "brewspec.schema.json"
```

And reference it in `_load_schema()`:

```python
def _load_schema() -> dict:
    with importlib.resources.files("brewlog").joinpath(SCHEMA_RESOURCE_NAME).open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)
```

No other call sites need to be updated since `_SCHEMA` is a module-level cached value.

---

### 1.14 Version bump (`__init__.py` and `cli.py`)

**`src/brewlog/__init__.py`:**
```python
__version__ = "0.3.0"
```

**`cli.py`:** The version is pulled from `__version__` dynamically via `@click.version_option(version=__version__)`, so no change is needed to `cli.py` beyond ensuring the import is correct. The welcome screen displays `BrewLog v0.3.0` automatically.

---

## 2. Data Models

### 2.1 Pydantic Models

The Pydantic models in `models.py` are **already correct for v0.3** with one exception: the `RatingsInput` model already has all 8 dimensions. No changes to `RatingsInput`, `ResultInput`, `BrewInput`, `CoffeeInput`, `WaterInput`, or `EquipmentInput` are required.

The complete current `models.py` state (shown for developer reference — do not re-implement):

```python
GRIND_ENUM = frozenset({
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse",
})
DATE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z|\d{4}-\d{2}-\d{2})$"
)

class RatingsInput(BaseModel):
    overall: Optional[int] = None
    fragrance: Optional[int] = None
    aroma: Optional[int] = None
    flavour: Optional[int] = None
    aftertaste: Optional[int] = None
    acidity: Optional[int] = None
    sweetness: Optional[int] = None
    mouthfeel: Optional[int] = None
    # validator: all fields 1-5 inclusive

class ResultInput(BaseModel):
    tds: Optional[float] = None
    ey: Optional[float] = None
    brix: Optional[float] = None
    tasting_notes: Optional[str] = None
    ratings: Optional[RatingsInput] = None
    # validators: tds/ey > 0, brix >= 0, tasting_notes non-empty, maxLength 2000

class BrewInput(BaseModel):
    date: str          # YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
    type: str          # BREW_TYPE_ENUM
    dose_g: float      # > 0
    water_weight_g: float  # > 0
    method: Optional[str] = None
    water_volume_ml: Optional[float] = None
    water_temp_c: Optional[float] = None
    grind: Optional[str] = None    # GRIND_ENUM
    duration_s: Optional[int] = None
    notes: Optional[str] = None
    coffee: Optional[CoffeeInput] = None
    water: Optional[WaterInput] = None
    equipment: Optional[EquipmentInput] = None
    result: Optional[ResultInput] = None
```

### 2.2 SQLite Schema

Full schema after v0.3 migration (see Section 1.1 for the complete DDL). Summary of columns:

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | |
| `date` | TEXT | NOT NULL | YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ |
| `type` | TEXT | NOT NULL | brew type enum |
| `method` | TEXT | | optional |
| `dose_g` | REAL | NOT NULL | > 0 |
| `water_weight_g` | REAL | NOT NULL | > 0 |
| `water_volume_ml` | REAL | | optional |
| `water_temp_c` | REAL | | 0-100 |
| `grind` | TEXT | | v0.4 enum (legacy freeform values may exist) |
| `duration_s` | INTEGER | | > 0 |
| `notes` | TEXT | | operational brew notes |
| `coffee_roast_date` | TEXT | | YYYY-MM-DD |
| `coffee_type` | TEXT | | single_origin \| blend |
| `coffee_origin` | TEXT | | JSON-encoded string array |
| `coffee_varietal` | TEXT | | freeform |
| `coffee_process` | TEXT | | freeform |
| `water_ppm` | REAL | | >= 0 |
| `equipment_grinder` | TEXT | | freeform |
| `equipment_brewer` | TEXT | | freeform |
| `result_tds` | REAL | | > 0 |
| `result_ey` | REAL | | > 0 |
| `result_brix` | REAL | | >= 0, NEW in v0.3 |
| `result_tasting_notes` | TEXT | | non-empty string |
| `result_ratings` | TEXT | | JSON dict — LEGACY (v0.2 rows only; new writes do not use this column) |
| `result_rating_overall` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_fragrance` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_aroma` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_flavour` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_aftertaste` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_acidity` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_sweetness` | INTEGER | | 1-5, NEW in v0.3 |
| `result_rating_mouthfeel` | INTEGER | | 1-5, NEW in v0.3 |

---

## 3. CLI Interface

### 3.1 `brewlog add` — flag changes

**Removed:**
```
--overall INT    (was: Overall rating 1-5)
```

**Added:**
```
--rating-overall INT     Overall impression, 1-5.
--rating-fragrance INT   Fragrance rating, 1-5.
--rating-aroma INT       Aroma rating, 1-5.
--rating-flavour INT     Flavour rating, 1-5.
--rating-aftertaste INT  Aftertaste rating, 1-5.
--rating-acidity INT     Acidity rating, 1-5.
--rating-sweetness INT   Sweetness rating, 1-5.
--rating-mouthfeel INT   Mouthfeel rating, 1-5.
```

**Hidden (retired, error on use):**
```
--rating INT     [hidden — produces error]
```

**Help text for `--grind`:**
```
--grind TEXT     Grind size: turkish | espresso | fine | medium_fine | medium | medium_coarse | coarse.
```

**Error on `--rating` use:**
```
Error: --rating has been replaced by --rating-overall in BrewLog v0.3.
Use --rating-overall N to set your overall impression (1-5).
See --help for all available rating dimension flags.
```
Written to stderr. Exit code 1.

**Updated interactive tip (fully interactive mode only):**
```
Tip: add optional details with flags, e.g. --method "V60" --rating-overall 4 --tasting-notes "Bright acidity"  (run --help for all options)
```

**Date prompt default changes:**
```
Date [2026-02-22]:
```
(Default is today's local date in YYYY-MM-DD. User presses Enter to accept.)

### 3.2 `brewlog update` — flag changes

Same rating flag changes as `add`. The `--rating` retirement check fires first. The `_overall` sentinel pattern is removed. All 8 `--rating-*` dimensions write directly to individual DB columns.

### 3.3 `brewlog list` — new flags and display

```
brewlog list [OPTIONS]

Options:
  --limit INTEGER     Number of brews to show (default: 20).
  --all               Show all brews.
  --type TEXT         Filter by brew type: immersion, pour_over, espresso, hybrid.
  --since DATE        Filter brews on or after this date (YYYY-MM-DD).
  --until DATE        Filter brews on or before this date (YYYY-MM-DD).   [NEW]
  --rating-min N      Filter brews with overall rating >= N (1-5).        [NEW]
  --rating-max N      Filter brews with overall rating <= N (1-5).        [NEW]
  --help              Show this message and exit.
```

**Column layout change (Rating column replaces TDS):**
```
  ID  Date                  Type        Method           Dose (g)   Water (g)  Overall Rating
----  --------------------  ----------  ---------------  ---------  ----------  --------------
   1  2026-02-22            pour_over   Hario V60             18.0       280.0               4
   2  2026-02-21T09:15:00Z  espresso    -                     16.0       32.0                -
```

**Error messages (stderr, exit 1):**
- Invalid `--until`: `Error: --until '...' is not a valid date. Use YYYY-MM-DD format.`
- `--since` > `--until`: `Error: --since must not be later than --until.`
- Invalid `--rating-min`: `Error: --rating-min must be an integer between 1 and 5.`
- Invalid `--rating-max`: `Error: --rating-max must be an integer between 1 and 5.`
- `--rating-min` > `--rating-max`: `Error: --rating-min must not exceed --rating-max.`

**No-match message (stdout, exit 0):**
- `No brews match the given filters.`

### 3.4 `brewlog show [id]` — updated Results section

```
Brew #14
---------
  Date:               2026-02-22
  Type:               pour_over
  Method:             Hario V60
  Dose:               18.0 g
  Water weight:       280.0 g
  Water temp:         96.0 C
  Grind:              medium_fine
  Duration:           180 s
  Notes:              Washed filter paper

Results
-------
  TDS (%):            1.38
  EY (%):             20.1
  Brix:               1.5
  Tasting Notes:      Bright citrus, caramel finish
  Ratings:
    Overall           4
    Fragrance         3
    Aroma             4
    Flavour           5
    Aftertaste        4
    Acidity           5
    Sweetness         3
    Mouthfeel         4

Coffee
------
  Roast date:         2026-01-20
  Type:               single_origin
  Origin:             Ethiopia
  Varietal:           Heirloom
  Process:            Washed

Water
-----
  PPM:                150.0

Equipment
---------
  Grinder:            Comandante C40
  Brewer:             Hario V60 02
```

Sections with no populated fields are omitted. The `Ratings:` sub-section is omitted if no `result_rating_*` column (and no legacy `result_ratings` JSON) has a value.

### 3.5 `brewlog import` — v0.3 rejection

```
$ brewlog import old_brews_v03.yaml
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
Written to stderr. Exit code 1. No rows written.

### 3.6 `brewlog` (no arguments) — welcome screen

```
    ( (
     ) )
  .______.
  |      |]
  \      /
   `----'

BrewLog v0.3.0
```

---

## 4. Architecture Decision Records

### ADR-1: Deprecate legacy `rating` flat column in favour of `result_rating_overall`

**Context:** The product spec (AC-22) permits the architect to deprecate the legacy `rating` column if no production data exists in it. Inspection of the current codebase at `brewspec/brewlog/` reveals that the DB schema does NOT contain a flat `rating` column at the brew level. The current implementation already uses `result_tds`, `result_ey`, and `result_ratings` (JSON) columns. The flat `tds`, `ey`, and `rating` columns from the spec's "legacy" scenario have never been introduced in production code.

**Decision:** The legacy `rating` column does not exist and will not be introduced. The v0.3 schema migration only needs to add the 8 individual `result_rating_*` columns. The `result_ratings` JSON column (introduced in the current codebase) is the only "legacy" column that needs backward-compatible handling.

**Rationale:** The codebase is ahead of the spec's assumed baseline. Introducing a `rating` column only to then deprecate it would be pointless churn. The spec's "architect's discretion" clause explicitly permits this decision.

**Consequences:** The `result_ratings` JSON column (current implementation) is the backward-compatibility concern. Rows written by the current v0.2 implementation have ratings stored as JSON in `result_ratings`. The v0.3 design handles this by: (a) retaining `result_ratings` in the schema, (b) not writing to it in new inserts/updates, (c) reading it as a fallback in `show` when all `result_rating_*` columns are NULL, and (d) reading it in `list` when `result_rating_overall` is NULL (for the rating display column — the JSON `overall` key).

**`list` display backward compat:** The `_format_row` function must handle the `result_ratings` fallback for `overall`:

```python
overall = row["result_rating_overall"]
if overall is None and row["result_ratings"] is not None:
    import json as _json
    legacy = _json.loads(row["result_ratings"])
    overall = legacy.get("overall")
rating_display = str(overall) if overall is not None else "-"
```

---

### ADR-2: Grind interactive prompt — flag-only, no numbered menu

**Context:** The key design areas in the task prompt state: "The interactive prompt on `add` (if no `--grind` flag) should present a numbered menu like the brew type menu." However, `grind` is an optional field. The product spec scope section explicitly states: "Individual `brewlog add` prompts for result fields — `--brix`, `--tasting-notes`, and all `--rating-*` flags remain flag-only on `add`. Only the four required fields (`date`, `type`, `dose`, `water`) are prompted interactively."

**Decision:** No interactive grind prompt is added to `brewlog add`. Grind remains flag-only. The help text for `--grind` on both `add` and `update` lists all 7 accepted enum values (satisfying AC-18).

**Rationale:** (1) The product spec scope is authoritative and explicitly defers optional field prompts. (2) An interactive numbered menu for an optional field would add a prompt that users who want no grind set must skip — poor UX. (3) The key design areas note appears to be aspirational/exploratory language that conflicts with the confirmed product scope. When the spec and design-areas note conflict, the spec wins.

**Consequences:** AC-18's interactive menu requirement is not implemented. The help text requirement (listing accepted values) is fully satisfied. If the product manager wants an interactive grind menu, it should be scoped as a separate AC in v0.4.

---

### ADR-3: Replace `result_ratings` JSON column with individual columns

**Context:** The current implementation stores all ratings dimensions as a single JSON-encoded TEXT column (`result_ratings`). The product spec's `brews` table schema (AC-20) shows individual columns for each dimension. The spec asks the architect to evaluate whether to use the individual column approach.

**Decision:** New writes use 8 individual `result_rating_*` integer columns. The `result_ratings` JSON column is retained for backward-compatible reads but is never written to by v0.3+ code.

**Rationale:** (1) Individual columns are queryable directly in SQL without JSON parsing — this is essential for `--rating-min` / `--rating-max` filters, which compare `result_rating_overall` directly. (2) Individual columns have proper SQLite type affinity (INTEGER). (3) The spec explicitly enumerates the individual columns. (4) The JSON column approach was a reasonable interim approach but cannot be used for SQL filtering without `json_extract()`, which adds complexity.

**Consequences:** The `_overall` sentinel pattern and read-before-write logic in `update.py` is eliminated. The update command becomes simpler. The `show.py` Results section reads individual columns with a JSON fallback for legacy rows. The `list_brews_filtered` SQL comparisons use `result_rating_overall` directly.

---

## 5. File Manifest

| File | Repo | Operation | Notes |
|------|------|-----------|-------|
| `src/brewlog/__init__.py` | brewspec | Modify | Bump `__version__` to `"0.3.0"` |
| `src/brewlog/db.py` | brewspec | Modify | `_V3_MIGRATION_COLUMNS`, `_apply_migrations`, `_init_schema` (update CREATE TABLE), `UPDATABLE_COLUMNS`, `update_brew` (add assertion), `insert_brew` (individual rating columns), `insert_brew_dict` (individual rating columns), `list_brews_filtered` (add `until`, `rating_min`, `rating_max` params) |
| `src/brewlog/commands/add.py` | brewspec | Modify | Replace `--overall` with 8 `--rating-*` options + hidden `--rating` (retired), update `_prompt_date()` default, update tip, update rating validation and `RatingsInput` construction |
| `src/brewlog/commands/update.py` | brewspec | Modify | Replace `--overall` with 8 `--rating-*` options + hidden `--rating` (retired), remove `_overall` sentinel, remove read-before-write for ratings, add direct column writes |
| `src/brewlog/commands/list_.py` | brewspec | Modify | Add `--until`, `--rating-min`, `--rating-max` options, add validation, always call `list_brews_filtered`, update `_format_header`, `_format_row`, add `result_ratings` JSON fallback for overall |
| `src/brewlog/commands/show.py` | brewspec | Modify | Update `has_results` check, update Results section rendering (individual columns + legacy JSON fallback), remove "Brew parameters" section header, add section separator lines |
| `src/brewlog/commands/import_.py` | brewspec | Modify | Add version check before schema validation, emit exact rejection message for non-v0.4 files, update docstring |
| `src/brewlog/commands/export.py` | brewspec | Modify | Replace `rows_to_brewspec_document` call with inline construction + invalid-grind warning logic |
| `src/brewlog/serialise.py` | brewspec | Modify | Add `GRIND_ENUM`, update `row_to_brew_dict` to emit `_invalid_grind` sentinel for non-enum grind values; `rows_to_brewspec_document` can be retained but is no longer called by the export command |
| `src/brewlog/schema.py` | brewspec | Modify | Add `SCHEMA_RESOURCE_NAME` constant, update docstring to reference v0.4 |
| `src/brewlog/brewspec.schema.json` | brewspec | Verify/Update | Must be the canonical v0.4 schema. Confirm it matches `/Users/scottluengen/Documents/1_Projects/brewspec/brewspec.schema.json` |
| `tests/test_cmd_add.py` | brewspec | Modify | Replace `--overall` references with `--rating-overall`, add tests for all 8 `--rating-*` flags, add `--rating` retirement test, add date-prompt default test |
| `tests/test_cmd_update.py` | brewspec | Modify | Same rating flag updates, add `--rating` retirement test, add tests for all 8 dimensions |
| `tests/test_cmd_list.py` | brewspec | Modify | Update column header assertion (TDS → Overall Rating) |
| `tests/test_cmd_list_filter.py` | brewspec | Modify | Add tests for `--until`, `--rating-min`, `--rating-max` |
| `tests/test_cmd_show.py` | brewspec | Modify | Update Results section assertions for individual columns |
| `tests/test_cmd_import.py` | brewspec | Modify | Add v0.3-rejection test, v0.4-acceptance test |
| `tests/test_cmd_export.py` | brewspec | Modify | Add invalid-grind-warning test |
| `tests/test_db.py` | brewspec | Modify | Add migration test, add `UPDATABLE_COLUMNS` assertion test |
| `tests/test_serialise.py` | brewspec | Modify | Add invalid-grind sentinel test |
| `tests/conftest.py` | brewspec | Modify | Update `full_brew_dict` fixture to include `result.ratings` sub-object with all dimensions |

---

## 6. Test Strategy

Tests must be written before implementation (TDD). Test files are listed in the order the dev should address them.

### AC-1, AC-34: Column allowlist in `update_brew()`

File: `tests/test_db.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_updatable_columns_constant_exists` | Import `UPDATABLE_COLUMNS` from `db` | No ImportError |
| `test_updatable_columns_is_frozenset` | `type(UPDATABLE_COLUMNS)` | `frozenset` |
| `test_updatable_columns_contains_new_columns` | Check all 8 `result_rating_*` names in set | All present |
| `test_updatable_columns_does_not_contain_id` | `"id" not in UPDATABLE_COLUMNS` | True |
| `test_updatable_columns_does_not_contain_date` | `"date" not in UPDATABLE_COLUMNS` | True |
| `test_update_brew_rejects_unknown_column` | `update_brew(1, {"evil_col": "x"}, conn)` | Raises `AssertionError` |
| `test_update_brew_accepts_all_valid_columns` | `update_brew(id, {col: valid_val for col in UPDATABLE_COLUMNS}, conn)` | Returns `True` |

### AC-2, AC-3, AC-4, AC-5: `--rating-min` / `--rating-max` on `list`

File: `tests/test_cmd_list_filter.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_rating_min_filters_correctly` | 3 brews with overall=2,3,4; `--rating-min 3` | 2 rows returned (3 and 4) |
| `test_rating_max_filters_correctly` | 3 brews with overall=2,3,4; `--rating-max 3` | 2 rows returned (2 and 3) |
| `test_rating_min_max_combined` | brews with overall=1,3,5; `--rating-min 2 --rating-max 4` | 1 row (overall=3) |
| `test_rating_min_invalid_zero` | `--rating-min 0` | exit 1, error message |
| `test_rating_min_invalid_six` | `--rating-min 6` | exit 1, error message |
| `test_rating_max_invalid_zero` | `--rating-max 0` | exit 1, error message |
| `test_rating_max_invalid_six` | `--rating-max 6` | exit 1, error message |
| `test_rating_min_exceeds_max` | `--rating-min 4 --rating-max 2` | exit 1, error message |
| `test_rating_filters_no_match` | brews with overall=1,2; `--rating-min 4` | "No brews match", exit 0 |
| `test_rating_min_max_combined_with_type` | `--type pour_over --rating-min 3` | only matching brews |
| `test_rating_min_max_combined_with_since` | `--since 2026-02-01 --rating-min 3` | only matching brews |
| `test_rating_min_max_with_limit` | 5 brews with overall>=3; `--rating-min 3 --limit 2` | 2 rows |
| `test_brew_with_no_overall_excluded_by_rating_min` | brew with overall=NULL; `--rating-min 1` | brew not in results |

### AC-6, AC-7, AC-8, AC-9, AC-10: Date format

File: `tests/test_cmd_add.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_date_prompt_default_is_today_yyyy_mm_dd` | Interactive add, press Enter at date prompt | Stored date matches `date.today().strftime("%Y-%m-%d")` |
| `test_date_prompt_accepts_date_only` | Date prompt input: `"2026-02-22\n"` | Brew stored with date `"2026-02-22"` |
| `test_date_prompt_accepts_full_datetime` | Date prompt input: `"2026-02-22T09:15:00Z\n"` | Brew stored with date `"2026-02-22T09:15:00Z"` |
| `test_date_prompt_rejects_invalid_format` | Date prompt input: `"22-02-2026\n2026-02-22\n"` | Re-prompts, then accepts second input |
| `test_date_prompt_rejects_missing_z` | Date prompt input: `"2026-02-22T09:15:00\n2026-02-22\n"` | Re-prompts |
| `test_date_flag_accepts_date_only` | `--date 2026-02-22` | exit 0, stored as `"2026-02-22"` |
| `test_date_flag_accepts_full_datetime` | `--date 2026-02-22T09:15:00Z` | exit 0, stored as `"2026-02-22T09:15:00Z"` |
| `test_date_flag_invalid_format_exits_1` | `--date 22/02/2026` | exit 1 |
| `test_date_stored_exactly_as_supplied_date_only` | `--date 2026-02-22` | DB row `date == "2026-02-22"` |
| `test_date_stored_exactly_as_supplied_datetime` | `--date 2026-02-22T09:00:00Z` | DB row `date == "2026-02-22T09:00:00Z"` |

File: `tests/test_cmd_list_filter.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_since_works_with_date_only_stored_date` | Brew stored with `date="2026-02-22"`; `--since 2026-02-22` | Brew appears |
| `test_since_works_with_datetime_stored_date` | Brew stored with `date="2026-02-22T09:00:00Z"`; `--since 2026-02-22` | Brew appears |
| `test_since_day_boundary_date_only` | Brew at `"2026-02-21"`; `--since 2026-02-22` | Brew excluded |
| `test_until_works_with_date_only_stored_date` | Brew stored with `date="2026-02-22"`; `--until 2026-02-22` | Brew appears |
| `test_until_works_with_datetime_stored_date` | Brew stored with `date="2026-02-22T09:00:00Z"`; `--until 2026-02-22` | Brew appears |
| `test_until_day_boundary` | Brew at `"2026-02-23"`; `--until 2026-02-22` | Brew excluded |
| `test_since_and_until_combined_inclusive` | Brew at `"2026-02-10"`, `"2026-02-15"`, `"2026-02-20"`; `--since 2026-02-10 --until 2026-02-20` | All 3 appear |
| `test_since_after_until_exits_1` | `--since 2026-02-20 --until 2026-02-10` | exit 1 |

### AC-11, AC-12: Export v0.4 compliance

File: `tests/test_cmd_export.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_export_writes_version_0_4` | Export after adding brews | `brewspec_version: "0.4"` in output |
| `test_export_result_fields_under_result_key` | Brew with tds, ey, brix, tasting_notes, ratings | Exported brew has `result.tds`, `result.ey` etc. |
| `test_export_result_omitted_when_no_result_fields` | Brew with no result fields | No `result` key in exported brew |
| `test_export_ratings_under_result_ratings` | Brew with all 8 rating dimensions | `result.ratings.overall` etc. in export |
| `test_export_passes_schema_validation` | Any non-empty DB | `schema.validate_document(doc)` returns `[]` |
| `test_export_invalid_grind_omitted_with_warning` | Insert brew with raw `grind="setting 15"` via direct DB write | Export succeeds, brew has no `grind` key, stderr contains warning |
| `test_export_valid_grind_included` | Brew with `grind="medium_fine"` | Exported brew has `grind: medium_fine` |

### AC-13: Import rejects non-v0.4 files

File: `tests/test_cmd_import.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_import_rejects_v03_file` | File with `brewspec_version: "0.3"` | exit 1 |
| `test_import_v03_rejection_message_contains_version` | Same | `"v0.3"` in stderr |
| `test_import_v03_rejection_message_contains_migration_steps` | Same | `"result.tds"` in stderr |
| `test_import_v03_rejection_message_contains_docs_url` | Same | `"github.com/coffee-standards/brewspec"` in stderr |
| `test_import_v03_no_rows_written` | Same | DB row count unchanged after attempt |
| `test_import_rejects_v02_file` | File with `brewspec_version: "0.2"` | exit 1 |
| `test_import_rejects_missing_version` | File with no `brewspec_version` key | exit 1 |
| `test_import_accepts_v04_file` | Valid v0.4 file | exit 0, rows inserted |

### AC-14: Import correctly reads v0.4 `result` fields

File: `tests/test_cmd_import.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_import_maps_result_tds` | v0.4 file with `result.tds: 1.38` | DB `result_tds = 1.38` |
| `test_import_maps_result_ey` | v0.4 file with `result.ey: 20.1` | DB `result_ey = 20.1` |
| `test_import_maps_result_brix` | v0.4 file with `result.brix: 1.5` | DB `result_brix = 1.5` |
| `test_import_maps_result_tasting_notes` | v0.4 file with `result.tasting_notes: "Citrus"` | DB `result_tasting_notes = "Citrus"` |
| `test_import_maps_result_ratings_overall` | v0.4 file with `result.ratings.overall: 4` | DB `result_rating_overall = 4` |
| `test_import_maps_all_rating_dimensions` | v0.4 file with all 8 dimensions | All 8 DB columns populated |
| `test_import_result_omitted_brew` | v0.4 file brew with no `result` key | All `result_*` DB columns NULL |

### AC-16, AC-17, AC-18, AC-19: `grind` enum enforcement

File: `tests/test_cmd_add.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_grind_all_valid_values_accepted` | `--grind X` for each of 7 enum values | exit 0 |
| `test_grind_freeform_rejected` | `--grind "setting 15"` | exit 1 |
| `test_grind_hyphenated_rejected` | `--grind "medium-fine"` | exit 1 |
| `test_grind_empty_string_rejected` | `--grind ""` | exit 1 |
| `test_grind_help_lists_enum_values` | `--help` output | `medium_fine` and `coarse` in help text |

File: `tests/test_cmd_update.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_update_grind_valid` | `--grind coarse` | exit 0 |
| `test_update_grind_invalid` | `--grind "light"` | exit 1 |

File: `tests/test_cmd_show.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_show_displays_grind_as_raw_enum` | Brew with `grind="medium_fine"` | `"medium_fine"` in output |

### AC-20, AC-21, AC-22, AC-23: Database migration

File: `tests/test_db.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_migration_adds_new_columns_to_existing_db` | Simulate v0.2 DB (create table without rating cols), then call `get_connection` | `PRAGMA table_info` shows all 8 new cols |
| `test_migration_is_idempotent` | Call `get_connection` twice | No error, columns present exactly once |
| `test_migration_preserves_existing_rows` | Insert brew in v0.2 DB, run migration, read row | Row intact |
| `test_fresh_db_has_all_columns` | Fresh DB | `PRAGMA table_info` shows all expected columns |
| `test_result_ratings_column_retained` | Fresh DB | `result_ratings` column still present |

### AC-24, AC-25, AC-26, AC-27, AC-28, AC-29, AC-30: `brewlog add` result flags

File: `tests/test_cmd_add.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_add_rating_retired_flag_exits_1` | `--rating 4` | exit 1 |
| `test_add_rating_retired_message` | `--rating 4` | stderr contains `--rating-overall` |
| `test_add_rating_overall_stored` | `--rating-overall 4` | DB `result_rating_overall = 4` |
| `test_add_rating_fragrance_stored` | `--rating-fragrance 3` | DB `result_rating_fragrance = 3` |
| `test_add_rating_aroma_stored` | `--rating-aroma 4` | DB `result_rating_aroma = 4` |
| `test_add_rating_flavour_stored` | `--rating-flavour 5` | DB `result_rating_flavour = 5` |
| `test_add_rating_aftertaste_stored` | `--rating-aftertaste 4` | DB `result_rating_aftertaste = 4` |
| `test_add_rating_acidity_stored` | `--rating-acidity 5` | DB `result_rating_acidity = 5` |
| `test_add_rating_sweetness_stored` | `--rating-sweetness 3` | DB `result_rating_sweetness = 3` |
| `test_add_rating_mouthfeel_stored` | `--rating-mouthfeel 4` | DB `result_rating_mouthfeel = 4` |
| `test_add_rating_overall_invalid_zero` | `--rating-overall 0` | exit 1 |
| `test_add_rating_overall_invalid_six` | `--rating-overall 6` | exit 1 |
| `test_add_rating_overall_invalid_string` | `--rating-overall abc` | Click type error, exit != 0 |
| `test_add_brix_valid_zero` | `--brix 0` | exit 0, `result_brix = 0.0` |
| `test_add_brix_valid_positive` | `--brix 1.5` | exit 0, `result_brix = 1.5` |
| `test_add_brix_invalid_negative` | `--brix -0.1` | exit 1 |
| `test_add_tasting_notes_stored` | `--tasting-notes "Bright acidity"` | DB `result_tasting_notes = "Bright acidity"` |
| `test_add_tasting_notes_empty_string_exits_1` | `--tasting-notes ""` | exit 1 |
| `test_add_no_result_flags_succeeds` | no result flags | exit 0, all result cols NULL |
| `test_add_tip_shows_rating_overall` | Interactive mode | `"--rating-overall 4"` in tip output |
| `test_add_tip_does_not_show_rating` | Interactive mode | `"--rating 4"` not in tip output |
| `test_add_all_8_rating_dimensions_stored` | all 8 `--rating-*` flags | all 8 DB columns populated correctly |

### AC-31, AC-32, AC-33, AC-34: `brewlog update` result flags

File: `tests/test_cmd_update.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_update_rating_retired_flag_exits_1` | `--rating 4` | exit 1 |
| `test_update_rating_retired_message` | `--rating 4` | stderr contains `--rating-overall` |
| `test_update_rating_overall_stored` | `--rating-overall 3` | DB `result_rating_overall = 3` |
| `test_update_all_rating_dimensions_stored` | all 8 `--rating-*` flags | all 8 DB cols updated |
| `test_update_rating_invalid_exits_1` | `--rating-overall 6` | exit 1 |
| `test_update_brix_valid` | `--brix 1.5` | exit 0 |
| `test_update_brix_negative_exits_1` | `--brix -1` | exit 1 |
| `test_update_tasting_notes_stored` | `--tasting-notes "Caramel"` | DB updated |
| `test_update_tasting_notes_empty_exits_1` | `--tasting-notes ""` | exit 1 |
| `test_update_does_not_write_result_ratings_column` | Any rating update | `result_ratings` column unchanged |

### AC-35, AC-36, AC-37: `brewlog show` Results section

File: `tests/test_cmd_show.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_show_results_section_present_when_any_result_set` | Brew with `result_rating_overall=4` | `"Results"` in output |
| `test_show_results_section_absent_when_no_results` | Brew with all result cols NULL | `"Results"` not in output |
| `test_show_tds_displayed` | Brew with `result_tds=1.38` | `"1.38"` in Results section |
| `test_show_ey_displayed` | Brew with `result_ey=20.1` | `"20.1"` in Results section |
| `test_show_brix_displayed` | Brew with `result_brix=1.5` | `"1.5"` in Results section |
| `test_show_tasting_notes_displayed` | Brew with `result_tasting_notes="Citrus"` | `"Citrus"` in Results section |
| `test_show_ratings_subsection_present_when_any_rating_set` | Brew with `result_rating_overall=4` | `"Ratings"` in output |
| `test_show_ratings_subsection_absent_when_no_ratings` | Brew with tds only, no rating cols | `"Ratings"` not in output |
| `test_show_displays_each_rating_dimension` | All 8 rating dimensions set | All 8 labels in output |
| `test_show_omits_unset_rating_dimensions` | Only `result_rating_overall` set | Other dimension labels absent |
| `test_show_legacy_ratings_json_displayed` | v0.2 row with `result_ratings='{"overall": 3}'`, all new cols NULL | Overall rating shown in output |

### AC-38, AC-39, AC-40, AC-41: `brewlog list` display and filtering

File: `tests/test_cmd_list.py` and `tests/test_cmd_list_filter.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_list_header_shows_overall_rating` | `brewlog list` with brews | `"Overall Rating"` in header |
| `test_list_header_does_not_show_tds` | `brewlog list` | `"TDS"` not in header |
| `test_list_shows_overall_rating_value` | Brew with `result_rating_overall=4` | `"4"` in row |
| `test_list_shows_dash_for_no_overall_rating` | Brew with no rating | `"-"` in row |
| `test_list_until_valid` | `--until 2026-02-22` | exit 0 |
| `test_list_until_invalid_format` | `--until 20260222` | exit 1 |
| `test_list_until_filters_correctly` | 2 brews, one after `--until` | Only earlier brew appears |
| `test_list_until_inclusive` | Brew exactly on `--until` date | Brew appears |
| `test_list_since_and_until_combined` | `--since 2026-02-01 --until 2026-02-15` | Only brews in range |
| `test_list_since_after_until_exits_1` | `--since 2026-02-20 --until 2026-02-10` | exit 1 |
| `test_list_no_match_message` | No brews match any filter combo | `"No brews match the given filters."`, exit 0 |

### AC-42: Welcome screen version

File: `tests/test_cmd_welcome.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_welcome_shows_version_0_3_0` | `brewlog` (no args) | `"0.3.0"` in output |

### Round-trip tests

File: `tests/test_roundtrip.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_roundtrip_all_8_rating_dimensions` | Add brew with all 8 ratings; export; import to new DB; show | All 8 ratings identical |
| `test_roundtrip_date_only_preserved` | Add brew with `date="2026-02-22"`; export; verify `date` field in YAML | `date: "2026-02-22"` (not normalised) |

---

## 7. Security Considerations

### 7.1 Input validation

All new `--rating-*` flags are `type=int` in Click, which rejects non-integer input before the command body runs. The range check (1–5) is performed explicitly in the command body before any DB call. This is defence in depth: Click handles type coercion, the command body handles range validation, and the Pydantic `RatingsInput` validator handles the same constraint as a third layer.

`--brix` is `type=float`; the `>= 0` check is in the command body and in `ResultInput.validate_brix`. `--tasting-notes` is `type=str`; the non-empty check is in the command body and in `ResultInput.validate_tasting_notes`.

The `--rating-min` and `--rating-max` flags on `list` are validated as integers in 1–5 before any SQL is constructed. The `--since` / `--until` ordering check prevents an impossible date range from generating a query that returns confusing results (it would return zero rows, but the error is more informative).

### 7.2 SQL injection

The `UPDATABLE_COLUMNS` allowlist assertion in `update_brew()` makes explicit the invariant that column names in the UPDATE statement come from application code only. Even without the assertion, column names were already safe (they come from static string literals in `update.py`). The assertion adds a structural guarantee that any future programming error (e.g., a user-controlled string accidentally becoming a dict key) is caught before SQL execution.

The new filter conditions in `list_brews_filtered` use static condition strings:
- `"substr(date, 1, 10) >= ?"` — static string
- `"substr(date, 1, 10) <= ?"` — static string
- `"result_rating_overall >= ?"` — static string
- `"result_rating_overall <= ?"` — static string

Values are passed as `params` list entries. No user input is concatenated into the SQL string.

### 7.3 File I/O

The import command adds a version check before JSON Schema validation. This does not change the trust boundary: the file is still parsed with `yaml.safe_load()` or `json.loads()` before the version check, and the parsed document is still validated against the JSON Schema before any DB writes. The version check is an early-exit optimisation with a better error message, not a security gate.

The export command's invalid-grind handling omits `grind` fields that are not valid enum members. The omitted value is emitted as a warning to stderr (not stdout), preventing it from appearing in the exported document where it would fail schema validation.

### 7.4 Error messages

The v0.3 import rejection message contains the version found in the file (from `doc.get("brewspec_version")`). This value is user-supplied data. It must be formatted with an f-string that includes it in a readable context, not executed or passed to any shell. The pattern `f'v{version}'` is safe: `version` is a string from YAML/JSON parsing and is only used for display.

### 7.5 Trust boundary

```
User input (CLI flags/prompts/import file)
    |
    v
Command validation
  - Click type coercion (int, float, str)
  - Explicit range/format checks in command body
  - --rating retirement check (first check, before anything else)
    |
    v
Pydantic model construction (BrewInput, RatingsInput, ResultInput)
  - Second validation layer on all numeric constraints
    |
    v
db.py functions
  - UPDATABLE_COLUMNS assertion (update_brew only)
  - Parameterised SQL placeholders (no interpolation of values)
  - Migration is schema-only (no user data involved)
    |
    v
SQLite file (~/.brewlog/brews.db)
  - Local, user-owned, no network access
```

For import:
```
Import file path
    |
    v
validate_import_path() — '..' rejection, 10MB limit, exists check
    |
    v
yaml.safe_load() / json.loads()
    |
    v
brewspec_version check — version must be "0.4"
    |
    v
schema.validate_document() — JSON Schema validation
    |
    v
insert_brew_dict() — parameterised SQL, no interpolation
    |
    v
SQLite file
```

### 7.6 Data integrity

The `_apply_migrations` function uses `PRAGMA table_info` to check existing columns before issuing `ALTER TABLE`. SQLite's `ALTER TABLE ADD COLUMN` with a default of `NULL` on an existing table is safe: it adds the column to all existing rows with NULL, leaving existing data untouched. The migration cannot corrupt existing data.

---

## 8. TDD Implementation Order

The developer must write failing tests first for each group, then implement to make them pass. `ruff check .` must pass after each step.

1. Write failing tests for AC-1, AC-34 (`UPDATABLE_COLUMNS` constant + `update_brew` assertion)
2. Implement `UPDATABLE_COLUMNS` and assertion in `db.py` — tests pass
3. Write failing tests for AC-20, AC-21, AC-22, AC-23 (migration)
4. Implement `_V3_MIGRATION_COLUMNS`, `_apply_migrations`, update `_init_schema` and `get_connection` — tests pass
5. Write failing tests for AC-14, AC-22 (import `insert_brew_dict` individual columns)
6. Update `insert_brew_dict` and `insert_brew` in `db.py` to use individual rating columns — tests pass
7. Write failing tests for AC-24 to AC-30 (`add` rating flags)
8. Update `commands/add.py`: rename `--overall` to `--rating-overall`, add 7 dimensions, add hidden `--rating`, update tip, update date prompt default — tests pass
9. Write failing tests for AC-31 to AC-34 (`update` rating flags)
10. Update `commands/update.py`: same flag changes, remove sentinel pattern, write individual columns — tests pass
11. Write failing tests for AC-35, AC-36, AC-37 (`show` Results section)
12. Update `commands/show.py`: individual columns, legacy JSON fallback, remove "Brew parameters" header, add section separator lines — tests pass
13. Write failing tests for AC-38, AC-39, AC-40, AC-41 (`list` display and filtering)
14. Update `commands/list_.py`: rename column header, add `--until`, `--rating-min`, `--rating-max`, update validation, update `_format_row` with rating display and fallback — tests pass
15. Update `db.py` `list_brews_filtered`: add `until`, `rating_min`, `rating_max` params with `substr` comparison — tests pass
16. Write failing tests for AC-2, AC-3, AC-4, AC-5 (`--rating-min` / `--rating-max` filtering)
17. Confirm `list_brews_filtered` already handles these — tests pass
18. Write failing tests for AC-6, AC-7, AC-8, AC-9, AC-10 (date format)
19. Confirm existing date handling already correct for most cases; update `_prompt_date` default — tests pass
20. Write failing tests for AC-11, AC-12 (export v0.4 compliance + invalid grind)
21. Update `serialise.py` with `GRIND_ENUM` and `_invalid_grind` sentinel; update `commands/export.py` with warning logic — tests pass
22. Write failing tests for AC-13 (import v0.3 rejection)
23. Update `commands/import_.py` with version check — tests pass
24. Write failing tests for AC-15 (`SCHEMA_RESOURCE_NAME` constant)
25. Update `schema.py` — tests pass
26. Write failing test for AC-42 (version 0.3.0 on welcome screen)
27. Update `__init__.py` to `"0.3.0"` — tests pass
28. Run full test suite — confirm all pass including v0.2 regression tests
29. Run `ruff check .` — fix any lint errors
