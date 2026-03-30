# Design: BrewLog CLI v1.0

**Feature:** brewlog-cli-v1.0
**Author:** architect
**Created:** 2026-03-30
**Input:** specs/products/brewlog-cli-v1.0.md
**Baseline:** specs/designs/brewlog-cli-v0.8.md (if present)
**Status:** Ready for Dev

---

## Overview

BrewLog CLI currently targets BrewSpec v0.9. BrewSpec v1.0 introduced two breaking field renames (`water_weight_g` → `water_g`, `notes` → `process_notes`), six new optional fields, and a `coffee.name` maxLength tightening from 150 to 100. Until this task lands, the CLI cannot import v1.0 documents and exports fail v1.0 schema validation.

This design covers: a DB migration that renames two columns and adds six new columns; Pydantic model changes across five models; six new CLI flags on both `add` and `update`; serialisation changes to `row_to_brew_dict()` and `insert_brew_dict()`; a `search_brews()` column reference fix; and a `BREWSPEC_VERSION` bump.

No new commands are introduced. No changes to `brewlog list` or `brewlog stats`. No v0.9 import compatibility shim.

---

## 1. Design Decision: `origin_cupping_notes` Storage

**Decision: Option A — embed `cupping_notes` within each origin object in the `coffee_origins` JSON column.**

The product spec recommends Option A and flags it for architect confirmation. Option A is correct.

**Rationale.** The `coffee_origins` column already stores each origin as a JSON object. Every other per-origin field (`name`, `country`, `region`, etc.) lives inside that JSON. Adding `cupping_notes` as a key within each origin object is consistent with the existing pattern and requires no new column. The alternative — a flat `origin_cupping_notes TEXT` column — would store only the first origin's note, silently discarding notes for blend components 2+. For the multi-origin case this is data loss, not a trade-off.

**Impact on AC-7, AC-45, AC-55:**

- **AC-7** (revised): The v1.0 migration adds five new columns, not six. `origin_cupping_notes` is not a separate column. The new columns are: `yield_g REAL`, `result_water_g REAL`, `coffee_cupping_notes TEXT`, `equipment_pressure_bar REAL`, `equipment_flow_rate_ml_s REAL`.
- **AC-45** (revised): `row_to_brew_dict()` reads `cupping_notes` from within the parsed JSON of the first origin object in `coffee.origins` — not from a separate DB column.
- **AC-55** (revised): `insert_brew_dict()` writes `cupping_notes` into the first origin entry's dict before `json.dumps()` — not into a separate column.

**`add` and `update` behaviour for `--origin-cupping-notes`:** When `--origin-cupping-notes` is supplied, the cupping note is stored as `cupping_notes` on the first entry in the origins JSON array. For `add`, this means the value is merged into the first `OriginInput` before serialisation. For `update`, the origins JSON is read back, the first entry is updated in-place, and the JSON is re-serialised.

---

## 2. DB Migration Design

### 2.1 Migration block naming

Add a single new constant in `db.py` following the existing `_V3` through `_V8` pattern:

```python
_V10_MIGRATION_COLUMNS: dict[str, str] = {
    "yield_g":                   "REAL",
    "result_water_g":            "REAL",
    "coffee_cupping_notes":      "TEXT",
    "equipment_pressure_bar":    "REAL",
    "equipment_flow_rate_ml_s":  "REAL",
}
```

### 2.2 Column renames

Two columns must be renamed. SQLite `ALTER TABLE ... RENAME COLUMN` is available from SQLite 3.25.0 (2018). Python 3.11 ships with SQLite 3.39.2 on Linux and ≥ 3.39.x on macOS — well above the threshold. The rename-rebuild-copy pattern used for the NOT NULL migration in v0.7 is not needed here.

Idempotency guard: before executing each rename, check whether the old column name still exists using `PRAGMA table_info(brews)`. If the old name is absent (migration already ran), skip.

### 2.3 Migration SQL

```sql
-- Rename water_weight_g to water_g (idempotent guard applied in Python)
ALTER TABLE brews RENAME COLUMN water_weight_g TO water_g;

-- Rename notes to process_notes (idempotent guard applied in Python)
ALTER TABLE brews RENAME COLUMN notes TO process_notes;

-- Add new columns (existing _apply_migrations loop handles idempotency via
-- the `existing` set check — no change needed to that loop pattern)
ALTER TABLE brews ADD COLUMN yield_g REAL;
ALTER TABLE brews ADD COLUMN result_water_g REAL;
ALTER TABLE brews ADD COLUMN coffee_cupping_notes TEXT;
ALTER TABLE brews ADD COLUMN equipment_pressure_bar REAL;
ALTER TABLE brews ADD COLUMN equipment_flow_rate_ml_s REAL;
```

### 2.4 Idempotency check logic

In `_apply_migrations()`, add the rename block before the existing column-addition loop. The guard reads `PRAGMA table_info(brews)` once and builds a column-name set:

```python
existing = {
    row[1]
    for row in conn.execute("PRAGMA table_info(brews)").fetchall()
}

if "water_weight_g" in existing:
    conn.execute("ALTER TABLE brews RENAME COLUMN water_weight_g TO water_g")

if "notes" in existing:
    conn.execute("ALTER TABLE brews RENAME COLUMN notes TO process_notes")
```

This check runs every time `get_connection()` is called. On an already-migrated database, neither old column name exists, so both branches are skipped. No error is produced.

### 2.5 Transaction boundary

Both renames and all five new-column additions must execute inside a single transaction. SQLite's `ALTER TABLE RENAME COLUMN` and `ALTER TABLE ADD COLUMN` are transactional when executed via `conn.execute()` (not `executescript()`). The migration must **not** use `executescript()` for the rename block — `executescript()` commits any open transaction before executing, which would split the migration. Use `conn.execute()` for each statement. Call `conn.commit()` once at the end of the entire migration block.

The correct structure in `_apply_migrations()`:

1. Optionally run `_rebuild_brews_table()` if `_has_not_null_on_date()` is True (existing logic, unchanged).
2. Rebuild the `existing` column set.
3. Execute both renames inside `conn.execute()` calls (guarded by the column-name checks above).
4. Rebuild `existing` again after renames (the renamed columns now appear under their new names).
5. Run the new-column addition loop for `_V10_MIGRATION_COLUMNS` (same pattern as the existing `all_migration_columns` loop, but as a separate pass for clarity).
6. Continue with the existing Step A (grinder_setting coercion) and Step B (coffee_origin migration).
7. `conn.commit()` at the end as normal.

### 2.6 `_init_schema` update

`_init_schema()` creates the `brews` table for fresh databases. Update the `CREATE TABLE IF NOT EXISTS brews` statement and the `_rebuild_brews_table()` fallback table to use `water_g` and `process_notes` (replacing `water_weight_g` and `notes`). Also add the five new columns. This ensures new installations get the correct schema without running migrations.

The `all_cols` list in `_rebuild_brews_table()` must also be updated: replace `water_weight_g` with `water_g` and `notes` with `process_notes`, and add the five new column names. This list is used for the `INSERT INTO brews SELECT` copy operation — it must not reference old column names that no longer exist after the rename.

---

## 3. Pydantic Model Changes

### 3.1 `BrewInput`

- Rename field `water_weight_g: Optional[float] = None` to `water_g: Optional[float] = None`.
- Rename field `notes: Optional[str] = None` to `process_notes: Optional[str] = None`.
- Add field `yield_g: Optional[float] = None` (brew-level recipe target output weight).
- Update the existing `validate_positive_required` validator signature: replace `"water_weight_g"` with `"water_g"` in the `@field_validator` arguments.
- Rename the `validate_notes` validator to `validate_process_notes`. Update its `@field_validator` argument from `"notes"` to `"process_notes"`. Keep the same body (non-empty when present, maxLength 2000).
- Add a new validator `validate_brew_yield_g` for `yield_g`:

```python
@field_validator("yield_g")
@classmethod
def validate_brew_yield_g(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("yield_g must be > 0")
    return v
```

- Update the docstring: change "BrewSpec v0.9" to "BrewSpec v1.0".

### 3.2 `ResultInput`

- Add field `water_g: Optional[float] = None` (actual water used).
- Add a new validator `validate_result_water_g` for the new field:

```python
@field_validator("water_g")
@classmethod
def validate_result_water_g(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("water_g must be > 0")
    return v
```

Note: `ResultInput` already has a `yield_g` field with a `yield_g_must_be_positive` validator. No change needed there.

### 3.3 `CoffeeInput`

- Add field `cupping_notes: Optional[str] = None`.
- Add a new validator:

```python
@field_validator("cupping_notes")
@classmethod
def validate_coffee_cupping_notes(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("cupping_notes must not be empty when provided")
        if len(v) > 2000:
            raise ValueError("cupping_notes must not exceed 2000 characters")
    return v
```

- Update the existing `validate_coffee_name` validator: change `150` to `100` in both the check and the error message.

### 3.4 `OriginInput`

- Add field `cupping_notes: Optional[str] = None`.
- Add a new validator:

```python
@field_validator("cupping_notes")
@classmethod
def validate_origin_cupping_notes(cls, v: Optional[str]) -> Optional[str]:
    if v is not None:
        if len(v.strip()) == 0:
            raise ValueError("cupping_notes must not be empty when provided")
        if len(v) > 2000:
            raise ValueError("cupping_notes must not exceed 2000 characters")
    return v
```

### 3.5 `EquipmentInput`

- Add field `pressure_bar: Optional[float] = None`.
- Add field `flow_rate_ml_s: Optional[float] = None`.
- Add validators:

```python
@field_validator("pressure_bar", "flow_rate_ml_s")
@classmethod
def validate_equipment_positive_floats(cls, v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("value must be > 0")
    return v
```

---

## 4. CLI Interface Design

### 4.1 `cmd_add.py` — new and changed options

All changes are additions or renames to the `@click.option` decorator list and the function signature. The existing options not listed here are unchanged.

**Changed option — `--water`:**

```python
@click.option("--water", "water_g", type=float, default=None,
              help="Water in grams (> 0).")
```

- Old internal name: `water_weight` (passed to `BrewInput` as `water_weight_g`).
- New internal name: `water_g` (passed to `BrewInput` as `water_g`).
- The interactive prompt label changes from `"Water weight in grams"` to `"Water in grams"`.
- The guard condition `if water_weight is None:` becomes `if water_g is None:`.
- The `BrewInput(...)` call changes `water_weight_g=water_weight` to `water_g=water_g`.

**Changed option — `--notes` → `--process-notes`:**

```python
@click.option("--process-notes", "process_notes", type=str, default=None,
              help="Operational preparation notes (e.g. 'rinsed filter, 30s bloom'). "
                   "For sensory impressions use --tasting-notes.")
```

- The `BrewInput(...)` call changes `notes=notes` to `process_notes=process_notes`.

**New option — `--target-yield`:**

```python
@click.option("--target-yield", "target_yield", type=float, default=None,
              help="Recipe target output weight in grams (> 0). For espresso dialling — "
                   "the intended liquid yield. For actual output weight use --yield-g.")
```

Maps to `BrewInput.yield_g`. Add a pre-validation guard in the command body:

```python
if target_yield is not None and target_yield <= 0:
    click.echo("Error: --target-yield must be greater than 0.", err=True)
    sys.exit(1)
```

Pass to `BrewInput(yield_g=target_yield)`.

**New option — `--actual-water`:**

```python
@click.option("--actual-water", "actual_water", type=float, default=None,
              help="Actual water used in grams (> 0). Record when actual water deviates "
                   "from the recipe target (--water).")
```

Maps to `ResultInput.water_g`. Add a pre-validation guard:

```python
if actual_water is not None and actual_water <= 0:
    click.echo("Error: --actual-water must be greater than 0.", err=True)
    sys.exit(1)
```

Pass to `ResultInput(water_g=actual_water, ...)`. The `has_result` check must include `actual_water is not None`.

**New option — `--coffee-cupping-notes`:**

```python
@click.option("--coffee-cupping-notes", "coffee_cupping_notes", type=str, default=None,
              help="Sensory notes on the coffee as a whole — bag description or "
                   "pre-brew cupping impressions.")
```

Maps to `CoffeeInput.cupping_notes`. Add a pre-validation guard:

```python
if coffee_cupping_notes is not None and not coffee_cupping_notes.strip():
    click.echo("Error: --coffee-cupping-notes must not be empty.", err=True)
    sys.exit(1)
```

Add `coffee_cupping_notes` to the `has_coffee` detection set. Pass to `CoffeeInput(cupping_notes=coffee_cupping_notes, ...)`.

**New option — `--origin-cupping-notes`:**

```python
@click.option("--origin-cupping-notes", "origin_cupping_notes", type=str, default=None,
              help="Sensory notes for the origin component (or the single origin "
                   "for single-origin coffees).")
```

Add a pre-validation guard:

```python
if origin_cupping_notes is not None and not origin_cupping_notes.strip():
    click.echo("Error: --origin-cupping-notes must not be empty.", err=True)
    sys.exit(1)
```

`origin_cupping_notes` must be passed into `_build_origins_from_flags()`. See Section 4.3 for how it is applied to the first origin entry.

**New option — `--pressure-bar`:**

```python
@click.option("--pressure-bar", "pressure_bar", type=float, default=None,
              help="Line or lever pressure in bars (> 0). Primarily for espresso.")
```

Maps to `EquipmentInput.pressure_bar`. Add a pre-validation guard:

```python
if pressure_bar is not None and pressure_bar <= 0:
    click.echo("Error: --pressure-bar must be greater than 0.", err=True)
    sys.exit(1)
```

Add `pressure_bar` to the `has_equipment` detection set. Pass to `EquipmentInput(pressure_bar=pressure_bar, ...)`.

**New option — `--flow-rate`:**

```python
@click.option("--flow-rate", "flow_rate_ml_s", type=float, default=None,
              help="Volumetric flow rate in ml/s (> 0). Useful for espresso profiling.")
```

Maps to `EquipmentInput.flow_rate_ml_s`. Add a pre-validation guard:

```python
if flow_rate_ml_s is not None and flow_rate_ml_s <= 0:
    click.echo("Error: --flow-rate must be greater than 0.", err=True)
    sys.exit(1)
```

Add `flow_rate_ml_s` to the `has_equipment` detection set. Pass to `EquipmentInput(flow_rate_ml_s=flow_rate_ml_s, ...)`.

### 4.2 `_build_origins_from_flags()` — `origin_cupping_notes` parameter

Add an `origin_cupping_notes: str | None = None` parameter. When `origin_cupping_notes` is provided and an origins list is built (structured or plain), apply the value as `cupping_notes` on the first entry:

- **Structured path:** after constructing the `OriginInput` for `i == 0`, include `cupping_notes=origin_cupping_notes`.
- **Plain string path:** after constructing `OriginInput(country=origins[0].country, ...)`, add `cupping_notes=origin_cupping_notes` for the first entry.
- **elevation_masl-only path:** include `cupping_notes=origin_cupping_notes` in the single `OriginInput`.

When `origin_cupping_notes` is not None and no origin flags are supplied (no structured flags, no `--origin`, no `elevation_masl`), create a single origin entry with only `cupping_notes` set: `return [OriginInput(cupping_notes=origin_cupping_notes)]`. Also add `origin_cupping_notes is not None` to the `has_coffee` detection check so this creates a coffee object.

The `has_structured` check must include `origin_cupping_notes is not None` to be included in origin presence detection.

### 4.3 `insert_brew()` in `db.py` — column updates

The `insert_brew()` function constructs `BrewInput`-to-DB mapping directly. It must be updated to:

- Replace `water_weight_g` column reference with `water_g` (both in the SQL column list and in params, reading `brew.water_g`).
- Replace `notes` column reference with `process_notes` (reading `brew.process_notes`).
- Add `yield_g` to the brew-level columns (reading `brew.yield_g`).
- Add `result_water_g` to the result columns (reading `result.water_g if result else None`).
- Add `coffee_cupping_notes` (reading `coffee.cupping_notes if coffee else None`).
- Add `equipment_pressure_bar` (reading `equipment.pressure_bar if equipment else None`).
- Add `equipment_flow_rate_ml_s` (reading `equipment.flow_rate_ml_s if equipment else None`).

For origin cupping notes in `insert_brew()`: the `coffee_origins` JSON is built from `[o.model_dump(exclude_none=True) for o in coffee.origins]`. Since `OriginInput` now has a `cupping_notes` field, `model_dump(exclude_none=True)` will include `cupping_notes` in the origin dict when it is set. No special handling is needed — it falls out naturally.

### 4.4 `cmd_update.py` — new and changed options

All changes mirror the `add` command.

**Changed option — `--notes` → `--process-notes`:**

```python
@click.option("--process-notes", "process_notes", type=str, default=None,
              help="Operational preparation notes (e.g. 'rinsed filter, 30s bloom'). "
                   "For sensory impressions use --tasting-notes.")
```

The validation guard currently reads `if notes is not None and (len(notes.strip()) == 0 or len(notes) > 2000)`. Rename to `process_notes` with error message: `"Error: --process-notes must be 1-2000 characters"`.

In the updates dict: change `updates["notes"] = notes` to `updates["process_notes"] = process_notes`.

**New options — six flags matching `add`:**

Same `@click.option` decorators and pre-validation guards as `add` (Sections 4.1). The validation guards are inline (not delegated to Pydantic for update) following the existing `update` command pattern.

For `--target-yield`: `updates["yield_g"] = target_yield`
For `--actual-water`: `updates["result_water_g"] = actual_water`
For `--coffee-cupping-notes`: `updates["coffee_cupping_notes"] = coffee_cupping_notes`
For `--pressure-bar`: `updates["equipment_pressure_bar"] = pressure_bar`
For `--flow-rate`: `updates["equipment_flow_rate_ml_s"] = flow_rate_ml_s`

**`--origin-cupping-notes` on update:**

This flag must update the `coffee_origins` JSON column. The update command currently builds `origins_json` from the structured origin flags. When `--origin-cupping-notes` is supplied:

- If any structured `--origin-*` flag is also supplied, include `cupping_notes` on the first entry of the new origins list before `json.dumps()`.
- If no structured `--origin-*` flag is supplied, read the existing `coffee_origins` JSON from the DB row, update the first entry's `cupping_notes` key, re-serialise, and set `updates["coffee_origins"] = new_json`. This requires fetching the brew row before building the updates dict:

```python
if origin_cupping_notes is not None and not has_structured_origin and not origin:
    # Read existing origins, patch first entry, write back
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn_read = db.get_connection(db_path=db_path)
    try:
        row = db.get_brew(brew_id_resolved, conn_read)
    finally:
        conn_read.close()
    existing_origins = json.loads(row["coffee_origins"]) if row and row["coffee_origins"] else [{}]
    existing_origins[0]["cupping_notes"] = origin_cupping_notes
    updates["coffee_origins"] = json.dumps(existing_origins)
```

When structured origin flags are present, `cupping_notes` is added to `origins_list[0]` before `json.dumps(origins_list)`.

Note: the brew ID must be resolved before the read-then-patch. The existing command resolves brew ID just before calling `db.update_brew()`. Restructure the update command slightly: resolve brew_id (call `db.get_latest_brew_id()` if needed) before constructing the updates dict, so it is available for the origin cupping notes read-back.

### 4.5 `UPDATABLE_COLUMNS` in `db.py`

Remove `"notes"` from `UPDATABLE_COLUMNS`. Add:

```python
"process_notes",
"yield_g",
"result_water_g",
"coffee_cupping_notes",
"equipment_pressure_bar",
"equipment_flow_rate_ml_s",
```

Note: `water_g` is a required field on `add` (not updatable via `update`), consistent with the existing treatment of `dose_g` and `water_g`. It is not added to `UPDATABLE_COLUMNS`.

---

## 5. `cmd_show.py` Changes

### 5.1 Brew parameters section

- Replace `_print_field("Water weight:", row["water_weight_g"], "g")` with `_print_field("Water:", row["water_g"], "g")`.
- Replace `if row["notes"] is not None: _print_field("Notes:", row["notes"])` with:

```python
if row["process_notes"] is not None:
    _print_field("Process Notes:", row["process_notes"])
```

- Add after the `brew_ratio` block (in the brew parameters section):

```python
if row["yield_g"] is not None:
    _print_field("Target yield (g):", row["yield_g"])
```

### 5.2 Results section

- Update `_RESULT_COLS` tuple: add `"result_water_g"` to the has-results detection tuple.
- Add display for `result_water_g` in the results body:

```python
if row["result_water_g"] is not None:
    _print_field("Actual water (g):", row["result_water_g"])
```

Insert this before the `result_tds` line.

### 5.3 Coffee section

- Update `has_coffee` detection: add `"coffee_cupping_notes"` to the field list.
- Add display of `coffee_cupping_notes` after the `coffee_type` line:

```python
if row["coffee_cupping_notes"] is not None:
    _print_field("Cupping Notes:", row["coffee_cupping_notes"])
```

### 5.4 Origins display

In `_display_origins()`, add `("cupping_notes", "Cupping Notes:")` to the `_ORIGIN_FIELDS` list. Place it last in the list (after `elevation_masl`).

### 5.5 Equipment section

- Update `has_equipment` detection: add `"equipment_pressure_bar"` and `"equipment_flow_rate_ml_s"` to the field tuple.
- Add display lines at the end of the equipment section body:

```python
if row["equipment_pressure_bar"] is not None:
    _print_field("Pressure (bar):", row["equipment_pressure_bar"])
if row["equipment_flow_rate_ml_s"] is not None:
    _print_field("Flow Rate (ml/s):", row["equipment_flow_rate_ml_s"])
```

---

## 6. Serialisation Changes

### 6.1 `BREWSPEC_VERSION` in `serialise.py` and bundled schema

Change `BREWSPEC_VERSION = "0.9"` to `BREWSPEC_VERSION = "1.0"`.

The CLI bundles its own copy of the schema at `brewlog/src/brewlog/brewspec.schema.json`, loaded
via `importlib.resources` in `schema.py`. This file must be replaced with the current v1.0
schema from the repo root:

```bash
cp brewspec.schema.json brewlog/src/brewlog/brewspec.schema.json
```

Run this as part of the DB/serialisation step (implementation order step 1 or 3). The `schema.py`
file itself requires no changes — `SCHEMA_RESOURCE_NAME = "brewspec.schema.json"` and the
`importlib.resources.files("brewlog")` path remain correct.

### 6.2 `row_to_brew_dict()` in `serialise.py`

**Renamed field mappings:**

Replace the existing brew-level field iteration:

```python
for field in ("date", "type", "dose_g", "water_weight_g"):
```

with:

```python
for field in ("date", "type", "dose_g", "water_g"):
```

Replace `for field in ("method", "water_temp_c", "duration_s", "notes"):` with:

```python
for field in ("method", "water_temp_c", "duration_s", "process_notes"):
```

**New field mappings:**

After the `brew_ratio` block, add:

```python
if r.get("yield_g") is not None:
    brew["yield_g"] = r["yield_g"]
```

In the coffee sub-object block, add after `coffee_roast_level`:

```python
if r.get("coffee_cupping_notes") is not None:
    coffee["cupping_notes"] = r["coffee_cupping_notes"]
```

For `origin.cupping_notes`: the coffee_origins JSON column is parsed to a list of dicts. The existing code does `coffee["origins"] = json.loads(r["coffee_origins"])`. Since `cupping_notes` is stored inside the origin objects within the JSON, it is automatically included in the parsed output — no additional code is needed. The `row_to_brew_dict` function does not need to do anything special; the JSON deserialisation surfaces it.

In the result sub-object block, add before the `result_tasting_notes` line:

```python
if r.get("result_water_g") is not None:
    result["water_g"] = r["result_water_g"]
```

In the equipment sub-object block, add after `equipment_notes`:

```python
if r.get("equipment_pressure_bar") is not None:
    equipment["pressure_bar"] = r["equipment_pressure_bar"]
if r.get("equipment_flow_rate_ml_s") is not None:
    equipment["flow_rate_ml_s"] = r["equipment_flow_rate_ml_s"]
```

### 6.3 `insert_brew_dict()` in `db.py`

**Renamed field mappings:**

Replace `brew_dict.get("water_weight_g")` with `brew_dict.get("water_g")` in the params tuple.
Replace `brew_dict.get("notes")` with `brew_dict.get("process_notes")`.
Update the SQL column list accordingly: `water_weight_g` → `water_g`, `notes` → `process_notes`.

**New field mappings:**

Add to the SQL column list and params tuple:

| SQL column | Source expression |
|---|---|
| `yield_g` | `brew_dict.get("yield_g")` |
| `result_water_g` | `result.get("water_g")` |
| `coffee_cupping_notes` | `coffee.get("cupping_notes")` |
| `equipment_pressure_bar` | `equipment.get("pressure_bar")` |
| `equipment_flow_rate_ml_s` | `equipment.get("flow_rate_ml_s")` |

For `origin_cupping_notes` via the `coffee_origins` JSON column: origins are serialised with `json.dumps(origins)` where `origins = coffee.get("origins")`. When the v1.0 document has `cupping_notes` on origin objects, those keys are preserved automatically in the JSON dump. No separate column write is needed. The first origin's `cupping_notes` is readable from the JSON at any later point.

---

## 7. Search Command

In `search_brews()` in `db.py`, change the LIKE clause from:

```sql
notes LIKE ?
```

to:

```sql
process_notes LIKE ?
```

The docstring must also be updated: replace "notes" with "process_notes" in the comment listing the searched columns.

---

## 8. File Manifest

| File | Operation | Notes |
|---|---|---|
| `brewlog/src/brewlog/db.py` | Modify | Migration constants, `_init_schema`, `_rebuild_brews_table`, `_apply_migrations`, `insert_brew`, `insert_brew_dict`, `UPDATABLE_COLUMNS`, `search_brews` |
| `brewlog/src/brewlog/models.py` | Modify | `BrewInput`, `ResultInput`, `CoffeeInput`, `OriginInput`, `EquipmentInput` |
| `brewlog/src/brewlog/serialise.py` | Modify | `BREWSPEC_VERSION`, `row_to_brew_dict` |
| `brewlog/src/brewlog/commands/add.py` | Modify | New/renamed options, `_build_origins_from_flags`, `BrewInput` construction, `has_*` checks |
| `brewlog/src/brewlog/commands/update.py` | Modify | New/renamed options, updates dict, origin cupping notes read-back logic |
| `brewlog/src/brewlog/commands/show.py` | Modify | `_RESULT_COLS`, `_display_origins`, display blocks for all renamed and new fields |
| `brewlog/tests/` | Modify/Add | Per Section 9 |

---

## 9. Test Strategy

All new tests are in the `brewlog/tests/` directory. Existing tests that reference `water_weight_g`, `water_weight`, or `notes` (brew-level) must be updated to use the new names.

### Migration tests (`tests/test_migration.py` or inline in `test_db.py`)

| Test | Approach |
|---|---|
| `test_migration_renames_water_weight_g` | Create a DB with the old schema (using `sqlite3` directly to create `water_weight_g` column with data), call `get_connection()`, assert `PRAGMA table_info(brews)` shows `water_g` not `water_weight_g`, assert the row data is preserved. |
| `test_migration_renames_notes` | Same approach: create DB with `notes` column and data, call `get_connection()`, assert `process_notes` present and `notes` absent, assert data preserved. |
| `test_migration_adds_new_columns` | Call `get_connection()` on a fresh DB, assert all five new columns (`yield_g`, `result_water_g`, `coffee_cupping_notes`, `equipment_pressure_bar`, `equipment_flow_rate_ml_s`) are present in `PRAGMA table_info(brews)`. |
| `test_migration_new_columns_are_null` | Insert a pre-migration row (only old columns), call `get_connection()` on the same DB, assert all five new columns are NULL for that row. |
| `test_migration_idempotent` | Call `get_connection()` twice on the same DB, assert no error is raised and the schema is unchanged on the second call. |
| `test_migration_both_renames_in_transaction` | Simulate a mid-migration failure is impractical in SQLite's Python driver, so instead assert that after `get_connection()` completes the rename counts are consistent (both old names absent, both new names present). |

### Renamed field tests

- All existing tests in `test_cmd_add.py` and `test_db.py` that pass `water_weight_g` or `water_weight` must be updated to `water_g`.
- All existing tests that pass `notes` as a brew-level field must be updated to `process_notes`.
- Confirm `--water` flag internal name change does not break the interactive-mode tests that prompt for "Water in grams".

### New flag tests on `add` (`tests/test_cmd_add.py`)

One test per new flag verifying the value is written to the DB:

| Flag | Test name | Assert |
|---|---|---|
| `--target-yield 36.0` | `test_add_target_yield` | `row["yield_g"] == 36.0` |
| `--actual-water 35.5` | `test_add_actual_water` | `row["result_water_g"] == 35.5` |
| `--coffee-cupping-notes "chocolate"` | `test_add_coffee_cupping_notes` | `row["coffee_cupping_notes"] == "chocolate"` |
| `--origin-cupping-notes "citrus"` + `--origin-country Colombia` | `test_add_origin_cupping_notes` | parsed `coffee_origins` JSON first entry has `cupping_notes == "citrus"` |
| `--pressure-bar 9.0` | `test_add_pressure_bar` | `row["equipment_pressure_bar"] == 9.0` |
| `--flow-rate 1.3` | `test_add_flow_rate_ml_s` | `row["equipment_flow_rate_ml_s"] == 1.3` |

### New flag tests on `update` (`tests/test_cmd_update.py`)

Mirror the `add` tests but via `brewlog update N --flag value`. Assert the DB row reflects the updated value after the command completes.

### Round-trip test (`tests/test_roundtrip.py` or inline in `test_cmd_import.py`)

- Construct a valid v1.0 BrewSpec YAML with all new fields populated.
- Call `brewlog import path`.
- Call `brewlog export out.yaml`.
- Assert `jsonschema.validate(output, schema)` passes without errors.
- Assert each field value in the exported document matches the imported value.

### Validation error tests

| Input | Expected |
|---|---|
| `--target-yield 0` | exit code 1, error message contains "target-yield" |
| `--target-yield -1` | exit code 1 |
| `--actual-water 0` | exit code 1 |
| `--actual-water -5` | exit code 1 |
| `--pressure-bar 0` | exit code 1 |
| `--flow-rate 0` | exit code 1 |
| `--coffee-cupping-notes ""` | exit code 1 |
| `--origin-cupping-notes ""` | exit code 1 |

### maxLength test

| Input | Expected |
|---|---|
| `--coffee-name` of 101 characters | exit code 1, error message mentions coffee-name |
| `--coffee-name` of 100 characters | accepted, written to DB |

---

## 10. Security Considerations

All security requirements from the product spec are addressed as follows.

**Migration DDL uses only static strings.** The two `ALTER TABLE RENAME COLUMN` statements and all five `ALTER TABLE ADD COLUMN` statements are written as literal string arguments to `conn.execute()`. No user input flows into migration DDL at any point. The column names are compile-time constants defined in `_V10_MIGRATION_COLUMNS`.

**Transaction coverage.** All migration steps (both renames and all five column additions) execute within a single transaction via `conn.execute()` calls before a single `conn.commit()`. Partial migration is not possible — if any statement fails (e.g. disk full), the transaction is rolled back and the DB is left in its pre-migration state.

**Parameterised queries for new columns.** `insert_brew()`, `insert_brew_dict()`, and `update_brew()` use only `?` placeholder parameters for all values including the five new columns. No f-string interpolation of user-supplied values anywhere in the DB layer.

**Input validation before DB write.** All new numeric fields (`brew.yield_g`, `result.water_g`, `equipment.pressure_bar`, `equipment.flow_rate_ml_s`) are validated `> 0` in the Pydantic models and additionally guarded with inline checks in the CLI commands before any DB write. All new text fields (`process_notes`, `coffee.cupping_notes`, `origin.cupping_notes`) are validated non-empty and bounded at 2000 characters in Pydantic. Validation failures produce a `click.echo(..., err=True)` message and `sys.exit(1)` — no stack traces.

**Import validation flow.** `cmd_import.py` runs `jsonschema.validate()` against `brewspec.schema.json` (v1.0) before any call to `insert_brew_dict()`. A v0.9 document containing `water_weight_g` or `brew.notes` will fail schema validation at this point because v1.0 uses `additionalProperties: false`. No rows are written on validation failure. The 10MB file size limit and `..` path rejection in `validate_import_path()` are unchanged.

**YAML parsing.** `yaml.safe_load()` is the only permitted YAML parser. All new test fixtures use safe-loadable YAML (no Python-object tags).

**No sensitive data.** The new fields contain recipe parameters and sensory notes. No PII is introduced.

---

## 11. Implementation Order

Work through changes in this sequence so that each step's tests can run against a consistent foundation.

1. **DB migration** (`db.py`): write failing migration tests first. Update `_init_schema`, `_apply_migrations`, `_rebuild_brews_table`, `_V10_MIGRATION_COLUMNS`, `UPDATABLE_COLUMNS`, `search_brews`. Run migration tests until passing.

2. **Pydantic models** (`models.py`): write failing model validation tests. Apply all changes from Section 3. Run model tests until passing.

3. **`serialise.py`**: write failing round-trip and serialisation unit tests. Apply changes from Section 6.2 (`BREWSPEC_VERSION`, `row_to_brew_dict`).

4. **`db.py` — `insert_brew` and `insert_brew_dict`**: write failing insert tests. Apply changes from Sections 4.3 and 6.3.

5. **`cmd_add.py`**: write failing CLI tests for each new/renamed flag. Apply changes from Sections 4.1 and 4.2.

6. **`cmd_update.py`**: write failing CLI tests for each new/renamed flag on update. Apply changes from Section 4.4.

7. **`cmd_show.py`**: write failing show output tests for each new and renamed field. Apply changes from Section 5.

8. **Round-trip test**: write the import → export → validate test from Section 9. Run to confirm the full stack works end-to-end.

9. **Update all existing tests** referencing `water_weight_g`, `water_weight`, or brew-level `notes` to use the new names (AC-59, AC-60).

10. **Final checks**: run the full test suite. Run `ruff check .` and fix any lint errors. Both must be clean before signalling ready for review.
