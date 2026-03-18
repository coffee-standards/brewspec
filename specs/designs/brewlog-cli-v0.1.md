# Technical Design: BrewLog CLI v0.1

**Status:** Draft
**Author:** architect
**Date:** 2026-02-19
**Input:** `specs/products/brewlog.md`
**Target spec:** BrewSpec v0.2 (`brewspec.schema.json`)

---

## Contents

1. Package Structure
2. Data Models (Pydantic)
3. SQLite Schema
4. CLI Interface Design
5. Database Layer Design
6. Export / Import Serialisation Logic
7. Test Strategy
8. Security Checklist

---

## 1. Package Structure

```
coffee-brew-app/
  pyproject.toml               # package metadata, entry point, dependencies
  requirements.txt             # pinned dev/test dependencies
  src/
    brewlog/
      __init__.py              # package version constant: __version__ = "0.1.0"
      cli.py                   # Click group + welcome screen (AC-2, AC-34)
      models.py                # Pydantic models for input validation
      db.py                    # SQLite init, all DB operations
      serialise.py             # row-to-BrewSpec-dict and BrewSpec-dict-to-row logic
      schema.py                # loads brewspec.schema.json; exposes validate_document()
      commands/
        __init__.py            # empty
        add.py                 # `brewlog add` command
        list_.py               # `brewlog list` command (file named list_.py, not list.py)
        show.py                # `brewlog show` command
        export.py              # `brewlog export` command
        import_.py             # `brewlog import` command (file named import_.py)
  tests/
    __init__.py
    conftest.py                # shared fixtures: tmp db path, sample brew dicts, CliRunner
    test_models.py             # Pydantic model unit tests
    test_db.py                 # database layer unit tests
    test_serialise.py          # serialisation / deserialisation unit tests
    test_cmd_add.py            # CLI integration tests for `add`
    test_cmd_list.py           # CLI integration tests for `list`
    test_cmd_show.py           # CLI integration tests for `show`
    test_cmd_export.py         # CLI integration tests for `export`
    test_cmd_import.py         # CLI integration tests for `import`
    test_roundtrip.py          # end-to-end export/import round-trip test
    fixtures/
      valid_brewspec.yaml      # minimal valid BrewSpec v0.2 YAML file (1 brew)
      valid_brewspec_multi.yaml # valid BrewSpec v0.2 YAML file (3 brews)
      valid_brewspec.json      # same single brew as JSON
      invalid_missing_field.yaml  # missing required field (for import rejection test)
      invalid_wrong_version.yaml  # brewspec_version: "0.1" (for import rejection test)
      large_file.yaml          # placeholder note: generated at test time, not committed
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "brewlog"
version = "0.1.0"
description = "A local CLI brew tracker using the BrewSpec format"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "jsonschema>=4.18",
]

[project.scripts]
brewlog = "brewlog.cli:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Package data: bundling the schema

`brewspec.schema.json` must travel with the package so that import/export validation
works after `pip install` without a network call. Copy the file into the package at
build time and declare it as package data.

```toml
# append to pyproject.toml
[tool.setuptools.package-data]
brewlog = ["brewspec.schema.json"]
```

The schema file is placed at `src/brewlog/brewspec.schema.json` (copied from the
brewspec public repo at build/setup time). The `schema.py` module resolves its path
using `importlib.resources` so it works from both the source tree and an installed
wheel.

---

## 2. Data Models (Pydantic)

All models live in `src/brewlog/models.py`. They serve two purposes:

- **CLI input validation** — the `add` command constructs a `BrewInput` from CLI
  arguments and prompts before writing to the DB.
- **Import validation** — each brew object from a parsed BrewSpec file is validated
  through `BrewInput` (after the JSON Schema pass) before insertion.

The models mirror the BrewSpec v0.2 field structure exactly. Field names use the
BrewSpec snake_case names. Optional fields default to `None`.

### 2.1 `CoffeeInput`

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
import re

BREW_TYPE_ENUM = frozenset({"immersion", "pour_over", "espresso", "hybrid"})
COFFEE_TYPE_ENUM = frozenset({"single_origin", "blend"})
ROAST_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CoffeeInput(BaseModel):
    roast_date: Optional[str] = None
    type: Optional[str] = None        # "single_origin" | "blend"
    origin: Optional[list[str]] = None
    varietal: Optional[str] = None
    process: Optional[str] = None

    @field_validator("roast_date")
    @classmethod
    def validate_roast_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not ROAST_DATE_PATTERN.match(v):
            raise ValueError("roast_date must match YYYY-MM-DD")
        return v

    @field_validator("type")
    @classmethod
    def validate_coffee_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in COFFEE_TYPE_ENUM:
            raise ValueError(f"coffee type must be one of: {sorted(COFFEE_TYPE_ENUM)}")
        return v

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            if len(v) == 0:
                raise ValueError("origin must have at least one entry")
            for item in v:
                if not isinstance(item, str) or len(item.strip()) == 0:
                    raise ValueError("each origin entry must be a non-empty string")
        return v

    @field_validator("varietal", "process")
    @classmethod
    def validate_min_length_1(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("value must not be empty")
        return v
```

### 2.2 `WaterInput`

```python
class WaterInput(BaseModel):
    ppm: Optional[float] = None

    @field_validator("ppm")
    @classmethod
    def validate_ppm(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("water ppm must be >= 0")
        return v
```

### 2.3 `BrewInput`

The primary model. All required fields have no default. All optional fields default
to `None`. Validators enforce every BrewSpec v0.2 constraint plus the spec's
`minLength: 1` requirement for freeform text fields.

```python
import re
from datetime import datetime, timezone

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class BrewInput(BaseModel):
    # Required fields
    date: str
    type: str                          # brew type enum
    dose_g: float
    water_weight_g: float

    # Optional brew parameters
    method: Optional[str] = None
    water_volume_ml: Optional[float] = None
    water_temp_c: Optional[float] = None
    grind: Optional[str] = None
    duration_s: Optional[int] = None
    tds: Optional[float] = None
    rating: Optional[int] = None
    notes: Optional[str] = None

    # Optional nested objects (flattened for CLI; stored flat in DB)
    coffee: Optional[CoffeeInput] = None
    water: Optional[WaterInput] = None

    # -- Validators for required fields --

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not DATE_PATTERN.match(v):
            raise ValueError(
                "date must be ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ"
            )
        # Secondary check: ensure it parses as a real datetime
        try:
            datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("date is not a valid datetime")
        return v

    @field_validator("type")
    @classmethod
    def validate_brew_type(cls, v: str) -> str:
        if v not in BREW_TYPE_ENUM:
            raise ValueError(
                f"type must be one of: {sorted(BREW_TYPE_ENUM)}"
            )
        return v

    @field_validator("dose_g", "water_weight_g")
    @classmethod
    def validate_positive_required(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    # -- Validators for optional numeric fields --

    @field_validator("water_volume_ml", "tds")
    @classmethod
    def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    @field_validator("water_temp_c")
    @classmethod
    def validate_water_temp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("water_temp_c must be between 0 and 100 inclusive")
        return v

    @field_validator("duration_s")
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("duration_s must be greater than 0")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating must be between 1 and 5 inclusive")
        return v

    # -- Validators for optional freeform text fields --

    @field_validator("method", "grind", "notes")
    @classmethod
    def validate_nonempty_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            raise ValueError("value must not be empty when provided")
        return v
```

### 2.4 Field-to-model mapping table

| BrewSpec v0.2 field      | Model field          | Type              | Constraint                        |
|--------------------------|----------------------|-------------------|-----------------------------------|
| `date`                   | `BrewInput.date`     | `str`             | Pattern `YYYY-MM-DDTHH:MM:SSZ`, valid datetime |
| `type`                   | `BrewInput.type`     | `str`             | Enum: `immersion\|pour_over\|espresso\|hybrid` |
| `dose_g`                 | `BrewInput.dose_g`   | `float`           | > 0                               |
| `water_weight_g`         | `BrewInput.water_weight_g` | `float`     | > 0                               |
| `method`                 | `BrewInput.method`   | `Optional[str]`   | minLength 1                       |
| `water_volume_ml`        | `BrewInput.water_volume_ml` | `Optional[float]` | > 0                          |
| `water_temp_c`           | `BrewInput.water_temp_c` | `Optional[float]` | 0–100 inclusive               |
| `grind`                  | `BrewInput.grind`    | `Optional[str]`   | minLength 1                       |
| `duration_s`             | `BrewInput.duration_s` | `Optional[int]` | > 0                               |
| `tds`                    | `BrewInput.tds`      | `Optional[float]` | > 0                               |
| `rating`                 | `BrewInput.rating`   | `Optional[int]`   | 1–5 inclusive                     |
| `notes`                  | `BrewInput.notes`    | `Optional[str]`   | minLength 1                       |
| `coffee.roast_date`      | `CoffeeInput.roast_date` | `Optional[str]` | Pattern `YYYY-MM-DD`            |
| `coffee.type`            | `CoffeeInput.type`   | `Optional[str]`   | Enum: `single_origin\|blend`      |
| `coffee.origin`          | `CoffeeInput.origin` | `Optional[list[str]]` | minItems 1, each minLength 1  |
| `coffee.varietal`        | `CoffeeInput.varietal` | `Optional[str]` | minLength 1                       |
| `coffee.process`         | `CoffeeInput.process` | `Optional[str]`  | minLength 1                       |
| `water.ppm`              | `WaterInput.ppm`     | `Optional[float]` | >= 0                              |

---

## 3. SQLite Schema

### 3.1 Architecture decision: `coffee_origin` storage

**Decision: JSON-encoded array column.**

The `coffee_origin` field maps to BrewSpec's `coffee.origin: array[string]`. Two
options were evaluated:

| Option | Pros | Cons |
|--------|------|------|
| JSON-encoded TEXT column | Zero schema complexity; single table; round-trips perfectly; no join needed for export | Not queryable in SQL without JSON functions (acceptable for v0.1 — no filtering on origin) |
| Separate `brew_origins` join table | Fully normalised; queryable | Adds schema complexity; join required on every read; complicates insert/export logic |

For v0.1 there is no filtering by origin. The primary operation is write-then-read-back
for export. JSON column wins: simpler code, simpler schema, identical fidelity.
A join table is the right answer once `list` filtering by origin is added in v0.2.

The stored value is a JSON array string (e.g., `'["Ethiopia", "Colombia"]'`).
`NULL` is stored when no origin is provided — not an empty array.

### 3.2 DDL

```sql
CREATE TABLE IF NOT EXISTS brews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT    NOT NULL,
    type                TEXT    NOT NULL,
    method              TEXT,
    dose_g              REAL    NOT NULL,
    water_weight_g      REAL    NOT NULL,
    water_volume_ml     REAL,
    water_temp_c        REAL,
    grind               TEXT,
    duration_s          INTEGER,
    tds                 REAL,
    rating              INTEGER,
    notes               TEXT,
    coffee_roast_date   TEXT,
    coffee_type         TEXT,
    coffee_origin       TEXT,          -- JSON-encoded array: '["Ethiopia"]' or NULL
    coffee_varietal     TEXT,
    coffee_process      TEXT,
    water_ppm           REAL
);

-- Index for list command (ordered by date desc, most recent first)
CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
```

**Constraints not encoded in DDL** (enforced by Pydantic models before insert):

- `date` pattern, `type` enum, `dose_g > 0`, `water_weight_g > 0` — all enforced
  at the model layer. SQLite NOT NULL is a backstop, not the primary guard.
- No CHECK constraints in SQL. The Pydantic layer is authoritative; redundant SQL
  CHECKs add maintenance surface without adding safety for a validated-input tool.

### 3.3 Database file location

```python
import os
from pathlib import Path

DB_DIR = Path.home() / ".brewlog"
DB_PATH = DB_DIR / "brews.db"
```

`DB_DIR` is created with `mkdir(parents=True, exist_ok=True)` on first `get_connection()`
call. No explicit `brewlog init` command is required (AC-3).

---

## 4. CLI Interface Design

All CLI code uses Click 8.x. The root group is defined in `src/brewlog/cli.py`;
each command is defined in its own file under `src/brewlog/commands/`.

### 4.1 Root group — `cli.py`

```python
import click
from brewlog import __version__

ASCII_CUP = """\
    ( (
     ) )
  .______.
  |      |]
  \\      /
   `----'
"""

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="BrewLog")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """BrewLog - a local brew tracker using the BrewSpec format."""
    if ctx.invoked_subcommand is None:
        click.echo(ASCII_CUP)
        click.echo(f"BrewLog v{__version__}\n")
        click.echo(ctx.get_help())
```

**AC-34, AC-35, AC-36:** The ASCII cup and version are printed only when no
subcommand is given (`ctx.invoked_subcommand is None`). Subcommands are registered
via `cli.add_command()` at the bottom of `cli.py` after all imports.

```python
from brewlog.commands.add import add
from brewlog.commands.list_ import list_cmd
from brewlog.commands.show import show
from brewlog.commands.export import export
from brewlog.commands.import_ import import_cmd

cli.add_command(add)
cli.add_command(list_cmd, name="list")
cli.add_command(show)
cli.add_command(export)
cli.add_command(import_cmd, name="import")
```

### 4.2 `brewlog add` — `commands/add.py`

```python
@click.command("add")
@click.option("--date",        type=str,   default=None, help="ISO 8601 UTC datetime (YYYY-MM-DDTHH:MM:SSZ).")
@click.option("--type",   "brew_type",
                               type=str,   default=None, help="Brew type: immersion, pour_over, espresso, hybrid.")
@click.option("--dose",        type=float, default=None, help="Coffee dose in grams (> 0).")
@click.option("--water",  "water_weight",
                               type=float, default=None, help="Water weight in grams (> 0).")
@click.option("--method",      type=str,   default=None, help="Freeform brewer description (e.g. 'Hario V60').")
@click.option("--temp",        type=float, default=None, help="Water temperature in Celsius (0-100).")
@click.option("--grind",       type=str,   default=None, help="Freeform grind description.")
@click.option("--duration",    type=int,   default=None, help="Brew duration in seconds (> 0).")
@click.option("--rating",      type=int,   default=None, help="Rating 1-5.")
@click.option("--notes",       type=str,   default=None, help="Freeform tasting notes.")
@click.option("--roast-date",  type=str,   default=None, help="Coffee roast date (YYYY-MM-DD).")
@click.option("--coffee-type", type=str,   default=None, help="Coffee classification: single_origin or blend.")
@click.option("--origin",      type=str,   default=None, multiple=True,
              help="Coffee origin (may be repeated for blends: --origin Ethiopia --origin Colombia).")
@click.option("--varietal",    type=str,   default=None, help="Coffee varietal (freeform).")
@click.option("--process",     type=str,   default=None, help="Coffee processing method (freeform).")
@click.option("--water-ppm",   type=float, default=None, help="Water mineral content in ppm (>= 0).")
@click.option("--tds",         type=float, default=None, help="Brew TDS percentage (> 0).")
def add(...) -> None:
    """Log a new brew."""
```

**Parameter names (Python identifiers) used inside the function body:**

| CLI flag        | Python name in function | Notes |
|-----------------|------------------------|-------|
| `--date`        | `date`                 |       |
| `--type`        | `brew_type`            | renamed to avoid shadowing Python builtin |
| `--dose`        | `dose`                 |       |
| `--water`       | `water_weight`         |       |
| `--method`      | `method`               |       |
| `--temp`        | `temp`                 |       |
| `--grind`       | `grind`                |       |
| `--duration`    | `duration`             |       |
| `--rating`      | `rating`               |       |
| `--notes`       | `notes`                |       |
| `--roast-date`  | `roast_date`           |       |
| `--coffee-type` | `coffee_type`          |       |
| `--origin`      | `origin`               | `tuple[str, ...]` due to `multiple=True` |
| `--varietal`    | `varietal`             |       |
| `--process`     | `process`              |       |
| `--water-ppm`   | `water_ppm`            |       |
| `--tds`         | `tds`                  |       |

#### 4.2.1 Interactive prompt sequence

When `date`, `brew_type`, `dose`, or `water_weight` are `None` (not supplied as
flags), the command prompts for them in order. All prompts use `click.prompt()` with
inline validation via a retry loop.

```python
from datetime import datetime, timezone

def _prompt_date() -> str:
    default = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    while True:
        value = click.prompt(f"Date", default=default)
        try:
            BrewInput(date=value, type="immersion", dose_g=1, water_weight_g=1)
            # Only date is validated here via a partial approach; use direct regex
        except Exception:
            pass
        if DATE_PATTERN.match(value):
            return value
        click.echo("  Error: date must be in format YYYY-MM-DDTHH:MM:SSZ (e.g. 2026-02-19T08:30:00Z)")
```

The pattern for all four required-field prompts is:

```python
# Pseudo-code for the prompt loop pattern used for all required fields
while <field> is None or <field is invalid>:
    raw = click.prompt("<Field name> [<hint>]", default=<default_or_empty>)
    try:
        <validate raw>
        <field> = <parsed raw>
        break
    except (ValueError, ValidationError):
        click.echo(f"  Error: <explanation>")
```

Specific prompts:

```
Date [2026-02-19T08:30:00Z]: _
  (accepts enter for default; re-prompts with error on invalid format)

Brew type (immersion, pour_over, espresso, hybrid): _
  (no default; re-prompts until valid enum value entered)

Coffee dose in grams: _
  (no default; re-prompts until positive number entered)

Water weight in grams: _
  (no default; re-prompts until positive number entered)
```

**AC-5, AC-6, AC-7, AC-11:** When all four required fields are provided as flags,
the while-loops are skipped entirely — no prompts are shown.

#### 4.2.2 Post-prompt validation and write

After all four required field values are resolved (from flags or prompts), the full
`BrewInput` is constructed. If construction raises a `ValidationError` (from flag
values that passed Click's type coercion but fail Pydantic's range/enum checks),
the command prints the error and calls `sys.exit(1)`.

```python
from pydantic import ValidationError

try:
    brew = BrewInput(
        date=date,
        type=brew_type,
        dose_g=dose,
        water_weight_g=water_weight,
        method=method or None,
        water_volume_ml=None,       # not exposed as a flag in v0.1 (see note below)
        water_temp_c=temp,
        grind=grind,
        duration_s=duration,
        tds=tds,
        rating=rating,
        notes=notes,
        coffee=CoffeeInput(
            roast_date=roast_date,
            type=coffee_type,
            origin=list(origin) if origin else None,
            varietal=varietal,
            process=process,
        ) if any([roast_date, coffee_type, origin, varietal, process]) else None,
        water=WaterInput(ppm=water_ppm) if water_ppm is not None else None,
    )
except ValidationError as exc:
    click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
    sys.exit(1)

brew_id = db.insert_brew(brew)
click.echo(f"Brew #{brew_id} logged.")
```

**Note on `water_volume_ml`:** The product spec does not list `--water-volume` as
a supported flag on `brewlog add` (AC-8 enumerates all supported flags and it is
absent). `water_volume_ml` is therefore not exposed as a CLI flag in v0.1. It will
be imported from BrewSpec files and stored in the DB when present.

### 4.3 `brewlog list` — `commands/list_.py`

```python
@click.command("list")
@click.option("--limit", type=int, default=20,
              help="Number of brews to show (default: 20).")
@click.option("--all", "show_all", is_flag=True, default=False,
              help="Show all brews.")
def list_cmd(limit: int, show_all: bool) -> None:
    """List recent brews."""
```

- If `show_all` is True, `limit` is ignored and all rows are returned.
- If `limit` is supplied and is not a positive integer, print error and exit 1 (AC-14).
- Output is a fixed-width table printed to stdout using string formatting (no
  third-party table library).
- Columns: `ID`, `Date`, `Type`, `Method`, `Dose (g)`, `Water (g)`, `Rating`
- Optional column values display `-` when NULL.
- If no rows exist, print `No brews logged yet. Run 'brewlog add' to get started.`
  and exit 0 (AC-16).

Table format example:
```
 ID   Date                  Type        Method           Dose (g)   Water (g)   Rating
----  --------------------  ----------  ---------------  ---------  ----------  ------
  14  2026-02-19T08:30:00Z  pour_over   Hario V60           18.0       280.0       4
  13  2026-02-18T07:15:00Z  immersion   -                   20.0       300.0       -
```

Column widths are fixed. Date column width: 20. Type: 10. Method: 15. Dose: 9.
Water: 10. Rating: 6.

### 4.4 `brewlog show` — `commands/show.py`

```python
@click.command("show")
@click.argument("id", type=int)
def show(id: int) -> None:
    """Show all fields for a brew by ID."""
```

- `id` is a required positional argument (Click `ARGUMENT`, not `OPTION`).
- Running with no argument raises Click's built-in `MissingArgument` error and exits
  non-zero (AC-20).
- If no brew found for `id`, print `No brew found with ID {id}.` and `sys.exit(1)` (AC-19).
- Output groups fields under headers (AC-18):

```
Brew #14
---------
Brew parameters
  Date:           2026-02-19T08:30:00Z
  Type:           pour_over
  Method:         Hario V60
  Dose:           18.0 g
  Water weight:   280.0 g
  Water temp:     96.0 C
  Grind:          medium-fine
  Duration:       180 s

Results
  TDS:            1.38
  Rating:         4
  Notes:          Bright acidity

Coffee
  Roast date:     2026-01-20
  Type:           single_origin
  Origin:         Ethiopia
  Varietal:       Heirloom
  Process:        Washed

Water
  PPM:            150.0
```

Fields with no value are omitted entirely from the output (AC-17). Sections with
no fields to show (e.g., the Coffee section if no coffee metadata was supplied) are
also omitted.

### 4.5 `brewlog export` — `commands/export.py`

```python
@click.command("export")
@click.argument("path", type=str)
@click.option("--format", "fmt", type=click.Choice(["yaml", "json"]),
              default="yaml", show_default=True,
              help="Output format: yaml (default) or json.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing file without prompting.")
def export(path: str, fmt: str, force: bool) -> None:
    """Export all brews to a BrewSpec v0.2 file."""
```

- `path` is a required positional argument.
- Path validation occurs before any DB access (see Section 6.2).
- If DB has no brews, print `No brews to export.` and exit 0 (AC-25).
- If file exists and `--force` is not set, prompt: `File already exists. Overwrite? [y/N]:` (AC-27).
- On YAML output, use `yaml.dump(..., default_flow_style=False, allow_unicode=True,
  sort_keys=False)`.
- On JSON output, use `json.dumps(..., indent=2, ensure_ascii=False)`.
- After serialising, validate the document against the schema before writing to disk.
  If validation fails (should never happen given correct serialisation, but acts as a
  safety net), print error and exit 1 without writing.

### 4.6 `brewlog import` — `commands/import_.py`

```python
@click.command("import")
@click.argument("path", type=str)
def import_cmd(path: str) -> None:
    """Import brews from a BrewSpec v0.2 YAML or JSON file."""
```

- `path` is a required positional argument.
- Path validation occurs before opening the file (see Section 6.2).
- File format detected from extension: `.yaml` / `.yml` use `yaml.safe_load()`;
  `.json` uses `json.loads()`. Unrecognised extension exits with error.
- File size check occurs before reading content (see Section 8).
- Schema validation occurs before any DB writes. If validation fails, print
  error(s) and exit 1. No partial writes.
- Brews are inserted in a single transaction (all-or-nothing after schema validation
  passes).
- On success, print `Imported N brews.` (AC-30).

---

## 5. Database Layer Design

All DB code lives in `src/brewlog/db.py`. Uses Python's stdlib `sqlite3` module —
no ORM.

### 5.1 `get_connection()`

```python
import sqlite3
from pathlib import Path

def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Return a sqlite3 Connection to the brew database.
    Creates the database directory and schema on first call.
    db_path defaults to DB_PATH (~/.brewlog/brews.db).
    The db_path parameter exists to support test isolation (tmp paths).
    """
    if db_path is None:
        db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # rows accessible as dicts
    _init_schema(conn)
    return conn
```

### 5.2 `_init_schema(conn)`

```python
def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS brews (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            date                TEXT    NOT NULL,
            type                TEXT    NOT NULL,
            method              TEXT,
            dose_g              REAL    NOT NULL,
            water_weight_g      REAL    NOT NULL,
            water_volume_ml     REAL,
            water_temp_c        REAL,
            grind               TEXT,
            duration_s          INTEGER,
            tds                 REAL,
            rating              INTEGER,
            notes               TEXT,
            coffee_roast_date   TEXT,
            coffee_type         TEXT,
            coffee_origin       TEXT,
            coffee_varietal     TEXT,
            coffee_process      TEXT,
            water_ppm           REAL
        );
        CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
    """)
    conn.commit()
```

### 5.3 `insert_brew(brew, conn)`

```python
import json

def insert_brew(brew: "BrewInput", conn: sqlite3.Connection) -> int:
    """
    Insert a validated BrewInput into the brews table.
    Returns the new row's integer ID.
    All SQL uses ? placeholders. No string interpolation.
    """
    coffee = brew.coffee
    water = brew.water

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            tds, rating, notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?
        )
    """
    params = (
        brew.date,
        brew.type,
        brew.method,
        brew.dose_g,
        brew.water_weight_g,
        brew.water_volume_ml,
        brew.water_temp_c,
        brew.grind,
        brew.duration_s,
        brew.tds,
        brew.rating,
        brew.notes,
        coffee.roast_date if coffee else None,
        coffee.type if coffee else None,
        json.dumps(coffee.origin) if (coffee and coffee.origin) else None,
        coffee.varietal if coffee else None,
        coffee.process if coffee else None,
        water.ppm if water else None,
    )
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor.lastrowid
```

### 5.4 `get_brew(brew_id, conn)`

```python
def get_brew(brew_id: int, conn: sqlite3.Connection) -> sqlite3.Row | None:
    """
    Fetch a single brew row by integer ID.
    Returns sqlite3.Row or None if not found.
    """
    sql = "SELECT * FROM brews WHERE id = ?"
    cursor = conn.execute(sql, (brew_id,))
    return cursor.fetchone()
```

### 5.5 `list_brews(conn, limit, all_rows)`

```python
def list_brews(
    conn: sqlite3.Connection,
    limit: int = 20,
    all_rows: bool = False,
) -> list[sqlite3.Row]:
    """
    Return brews ordered by date descending.
    If all_rows is True, limit is ignored.
    """
    if all_rows:
        sql = "SELECT * FROM brews ORDER BY date DESC"
        cursor = conn.execute(sql)
    else:
        sql = "SELECT * FROM brews ORDER BY date DESC LIMIT ?"
        cursor = conn.execute(sql, (limit,))
    return cursor.fetchall()
```

### 5.6 `get_all_brews(conn)`

```python
def get_all_brews(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all brews ordered by date descending. Used by export."""
    sql = "SELECT * FROM brews ORDER BY date DESC"
    return conn.execute(sql).fetchall()
```

### 5.7 Connection management in commands

Each command function opens a connection at entry, uses it, and closes it before
returning. No connection is held as a module-level singleton. Pattern used in every
command:

```python
conn = db.get_connection()
try:
    # ... command logic ...
finally:
    conn.close()
```

### 5.8 `insert_brew_dict(brew_dict, conn)`

Used by the import command after schema validation. Accepts a raw dict (one brew
from the parsed BrewSpec file) rather than a `BrewInput`. This avoids running the
Pydantic prompts path for import.

```python
def insert_brew_dict(brew_dict: dict, conn: sqlite3.Connection) -> int:
    """
    Insert a brew from a validated BrewSpec brew dict (already schema-validated).
    Returns the new row ID.
    All SQL uses ? placeholders.
    """
    coffee = brew_dict.get("coffee") or {}
    water = brew_dict.get("water") or {}
    origin = coffee.get("origin")

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            tds, rating, notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?
        )
    """
    params = (
        brew_dict.get("date"),
        brew_dict.get("type"),
        brew_dict.get("method"),
        brew_dict.get("dose_g"),
        brew_dict.get("water_weight_g"),
        brew_dict.get("water_volume_ml"),
        brew_dict.get("water_temp_c"),
        brew_dict.get("grind"),
        brew_dict.get("duration_s"),
        brew_dict.get("tds"),
        brew_dict.get("rating"),
        brew_dict.get("notes"),
        coffee.get("roast_date"),
        coffee.get("type"),
        json.dumps(origin) if origin else None,
        coffee.get("varietal"),
        coffee.get("process"),
        water.get("ppm"),
    )
    cursor = conn.execute(sql, params)
    return cursor.lastrowid
```

The import command wraps all `insert_brew_dict` calls in a single transaction:

```python
conn.execute("BEGIN")
try:
    for brew_dict in brews:
        insert_brew_dict(brew_dict, conn)
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

---

## 6. Export / Import Serialisation Logic

All serialisation logic lives in `src/brewlog/serialise.py`.

### 6.1 DB row to BrewSpec dict (for export)

```python
import json
import sqlite3

def row_to_brew_dict(row: sqlite3.Row) -> dict:
    """
    Convert a sqlite3.Row to a BrewSpec v0.2 brew dict.
    Rules:
    - NULL columns are omitted entirely (no null values in output).
    - coffee_origin is deserialised from JSON string to list.
    - coffee sub-object is only included if at least one coffee field is present.
    - water sub-object is only included if water_ppm is present.
    """
    r = dict(row)  # sqlite3.Row to plain dict

    brew: dict = {}

    # Required fields (always present; NOT NULL in schema)
    brew["date"] = r["date"]
    brew["type"] = r["type"]
    brew["dose_g"] = r["dose_g"]
    brew["water_weight_g"] = r["water_weight_g"]

    # Optional brew-level fields — include only if not NULL
    for field in ("method", "water_volume_ml", "water_temp_c", "grind",
                  "duration_s", "tds", "rating", "notes"):
        if r[field] is not None:
            brew[field] = r[field]

    # Coffee sub-object
    coffee: dict = {}
    if r["coffee_roast_date"] is not None:
        coffee["roast_date"] = r["coffee_roast_date"]
    if r["coffee_type"] is not None:
        coffee["type"] = r["coffee_type"]
    if r["coffee_origin"] is not None:
        coffee["origin"] = json.loads(r["coffee_origin"])
    if r["coffee_varietal"] is not None:
        coffee["varietal"] = r["coffee_varietal"]
    if r["coffee_process"] is not None:
        coffee["process"] = r["coffee_process"]
    if coffee:  # only include if at least one field is present
        brew["coffee"] = coffee

    # Water sub-object
    if r["water_ppm"] is not None:
        brew["water"] = {"ppm": r["water_ppm"]}

    return brew


def rows_to_brewspec_document(rows: list[sqlite3.Row]) -> dict:
    """
    Convert a list of DB rows to a full BrewSpec v0.2 document dict.
    Returns {"brewspec_version": "0.2", "brews": [...]}
    """
    return {
        "brewspec_version": "0.2",
        "brews": [row_to_brew_dict(row) for row in rows],
    }
```

### 6.2 Path validation (shared by export and import)

```python
from pathlib import Path
import sys

def validate_export_path(path_str: str) -> Path:
    """
    Validate an export path string.
    Rejects paths containing '..' components (directory traversal).
    Rejects paths whose parent directory does not exist.
    Returns a resolved Path on success.
    Calls sys.exit(1) with error message on failure.
    """
    p = Path(path_str)
    # Reject '..' at any position in the path
    if ".." in p.parts:
        click.echo("Error: path must not contain '..' components.", err=True)
        sys.exit(1)
    # Reject if parent directory does not exist
    if not p.parent.exists():
        click.echo(f"Error: directory '{p.parent}' does not exist.", err=True)
        sys.exit(1)
    return p


def validate_import_path(path_str: str) -> Path:
    """
    Validate an import path string.
    Rejects paths containing '..' components.
    Rejects files larger than 10MB (10 * 1024 * 1024 bytes).
    Returns a resolved Path on success.
    Calls sys.exit(1) with error message on failure.
    """
    MAX_BYTES = 10 * 1024 * 1024  # 10MB

    p = Path(path_str)
    if ".." in p.parts:
        click.echo("Error: path must not contain '..' components.", err=True)
        sys.exit(1)
    if not p.exists():
        click.echo(f"Error: file '{p}' does not exist.", err=True)
        sys.exit(1)
    if p.stat().st_size > MAX_BYTES:
        click.echo(
            f"Error: file exceeds 10MB limit ({p.stat().st_size} bytes). "
            "Refusing to parse.",
            err=True,
        )
        sys.exit(1)
    return p
```

**Note on `..` detection:** `Path("..")` and `Path("foo/../bar")` both surface `..`
in `Path.parts`. This is the detection mechanism. An alternative is to compare
`p.resolve()` against a safe base directory, but `..` in parts is simpler and
sufficient for a local tool where the user is specifying their own path.

### 6.3 BrewSpec dict to DB (for import)

The import path does not go through `BrewInput` Pydantic models. Instead:

1. Parse file → raw Python dict (using `yaml.safe_load` or `json.loads`).
2. Validate dict against JSON Schema (`schema.validate_document(doc)`). Fail fast
   if invalid; print all errors.
3. For each brew in `doc["brews"]`, call `db.insert_brew_dict(brew_dict, conn)`.

This keeps the import path clean: JSON Schema is the authority for file-level
validation; `BrewInput` is the authority for user-supplied CLI values.

### 6.4 Schema validation module — `schema.py`

```python
import json
from pathlib import Path
import importlib.resources

import jsonschema
from jsonschema import Draft202012Validator


def _load_schema() -> dict:
    """Load the bundled brewspec.schema.json using importlib.resources."""
    with importlib.resources.files("brewlog").joinpath("brewspec.schema.json").open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


_SCHEMA = _load_schema()
_VALIDATOR = Draft202012Validator(_SCHEMA)


def validate_document(doc: dict) -> list[str]:
    """
    Validate a parsed BrewSpec document dict against the v0.2 JSON Schema.
    Returns a list of error message strings. Empty list means valid.
    """
    errors = sorted(_VALIDATOR.iter_errors(doc), key=lambda e: e.path)
    return [e.message for e in errors]
```

Usage in export (safety net):

```python
errors = schema.validate_document(document)
if errors:
    click.echo("Internal error: serialised document failed schema validation.", err=True)
    for e in errors:
        click.echo(f"  - {e}", err=True)
    sys.exit(1)
```

Usage in import (primary validation):

```python
errors = schema.validate_document(doc)
if errors:
    click.echo("Validation failed:", err=True)
    for e in errors:
        click.echo(f"  - {e}", err=True)
    sys.exit(1)
```

---

## 7. Test Strategy

### 7.1 Test framework and conventions

- **Framework:** `pytest` with no plugins beyond what's in `requirements.txt`.
- **CLI testing:** Click's `CliRunner` for all command tests (in-process; no subprocess).
- **DB isolation:** Each DB test uses a `tmp_path` fixture from pytest to create a
  fresh SQLite file; `db.get_connection(db_path=tmp_path / "test.db")` is called
  rather than the default path.
- **No network:** All tests are offline. The schema is loaded from the bundled file.
- **No secrets or sensitive data** in any fixture.
- **Test naming:** `test_<what>_<condition>` pattern throughout.

### 7.2 `conftest.py` shared fixtures

```python
import pytest
from click.testing import CliRunner
from brewlog import db as db_module
from pathlib import Path


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_db(tmp_path):
    """Return a fresh sqlite3.Connection to a tmp db file."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    yield conn
    conn.close()


@pytest.fixture
def minimal_brew_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
    }


@pytest.fixture
def full_brew_dict():
    return {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
        "method": "Hario V60",
        "water_temp_c": 96.0,
        "grind": "medium-fine",
        "duration_s": 180,
        "tds": 1.38,
        "rating": 4,
        "notes": "Bright acidity",
        "coffee": {
            "roast_date": "2026-01-20",
            "type": "single_origin",
            "origin": ["Ethiopia"],
            "varietal": "Heirloom",
            "process": "Washed",
        },
        "water": {"ppm": 150.0},
    }
```

### 7.3 `tests/test_models.py` — Pydantic model unit tests

| Test function | What it tests | AC |
|---|---|---|
| `test_brew_input_valid_minimal` | Required-only fields accepted | AC-9 |
| `test_brew_input_valid_all_fields` | All optional fields accepted | AC-8, AC-9 |
| `test_brew_input_invalid_date_format` | Non-ISO-8601 date rejected | AC-9 |
| `test_brew_input_invalid_date_impossible` | `2026-13-01T00:00:00Z` rejected | AC-9 |
| `test_brew_input_invalid_type_enum` | Unknown type string rejected | AC-9 |
| `test_brew_input_dose_zero` | `dose_g=0` rejected | AC-9 |
| `test_brew_input_dose_negative` | `dose_g=-1` rejected | AC-9 |
| `test_brew_input_water_weight_zero` | `water_weight_g=0` rejected | AC-9 |
| `test_brew_input_temp_boundary_low` | `water_temp_c=0` accepted | AC-9 |
| `test_brew_input_temp_boundary_high` | `water_temp_c=100` accepted | AC-9 |
| `test_brew_input_temp_out_of_range` | `water_temp_c=101` rejected | AC-9 |
| `test_brew_input_duration_zero` | `duration_s=0` rejected | AC-9 |
| `test_brew_input_duration_negative` | `duration_s=-1` rejected | AC-9 |
| `test_brew_input_rating_low_boundary` | `rating=1` accepted | AC-9 |
| `test_brew_input_rating_high_boundary` | `rating=5` accepted | AC-9 |
| `test_brew_input_rating_below_min` | `rating=0` rejected | AC-9 |
| `test_brew_input_rating_above_max` | `rating=6` rejected | AC-9 |
| `test_brew_input_tds_zero` | `tds=0` rejected | AC-9 |
| `test_brew_input_water_ppm_zero` | `ppm=0` accepted (>= 0 is valid) | AC-9 |
| `test_brew_input_water_ppm_negative` | `ppm=-1` rejected | AC-9 |
| `test_brew_input_method_empty_string` | `method=""` rejected | AC-9 |
| `test_brew_input_grind_empty_string` | `grind=""` rejected | AC-9 |
| `test_brew_input_notes_empty_string` | `notes=""` rejected | AC-9 |
| `test_coffee_input_roast_date_valid` | `roast_date="2026-01-20"` accepted | AC-9 |
| `test_coffee_input_roast_date_invalid_format` | `roast_date="01-20-2026"` rejected | AC-9 |
| `test_coffee_input_type_valid_single_origin` | `type="single_origin"` accepted | AC-9 |
| `test_coffee_input_type_valid_blend` | `type="blend"` accepted | AC-9 |
| `test_coffee_input_type_invalid` | `type="unknown"` rejected | AC-9 |
| `test_coffee_input_origin_empty_list` | `origin=[]` rejected (minItems 1) | AC-9 |
| `test_coffee_input_origin_empty_item` | `origin=[""]` rejected | AC-9 |
| `test_coffee_input_origin_multiple` | `origin=["Ethiopia", "Colombia"]` accepted | AC-8 |

### 7.4 `tests/test_db.py` — database layer tests

| Test function | What it tests | AC |
|---|---|---|
| `test_init_db_creates_table` | `brews` table exists after `get_connection()` | AC-4 |
| `test_init_db_creates_index` | `idx_brews_date` index exists | AC-4 |
| `test_init_db_idempotent` | calling `get_connection()` twice does not fail | AC-3 |
| `test_insert_brew_minimal` | inserts minimal BrewInput, returns id=1 | AC-10 |
| `test_insert_brew_all_fields` | inserts full BrewInput, all fields retrievable | AC-10 |
| `test_insert_brew_origin_serialised` | coffee_origin stored as JSON string | Section 3.1 |
| `test_get_brew_existing` | `get_brew(1)` returns correct row | AC-17 |
| `test_get_brew_not_found` | `get_brew(999)` returns None | AC-19 |
| `test_list_brews_default_limit` | returns at most 20 rows, ordered by date desc | AC-12 |
| `test_list_brews_custom_limit` | `list_brews(limit=5)` returns at most 5 rows | AC-14 |
| `test_list_brews_all` | `list_brews(all_rows=True)` returns all rows | AC-15 |
| `test_list_brews_empty` | returns empty list when no rows | AC-16 |
| `test_list_brews_order` | most recent date comes first | AC-12 |
| `test_insert_brew_dict_minimal` | `insert_brew_dict` with minimal dict inserts correctly | AC-28 |
| `test_insert_brew_dict_full` | `insert_brew_dict` with full dict inserts correctly | AC-28 |
| `test_insert_brew_dict_no_dedup` | re-inserting same dict creates a second row | AC-33 |
| `test_parameterised_query_safety` | INSERT with SQL-special characters in text fields does not corrupt DB | Security |

### 7.5 `tests/test_serialise.py` — serialisation unit tests

| Test function | What it tests | AC |
|---|---|---|
| `test_row_to_brew_dict_minimal` | required fields present; no null values in output | AC-24 |
| `test_row_to_brew_dict_no_nulls` | NULL columns absent from output dict entirely | AC-24 |
| `test_row_to_brew_dict_coffee_object_included` | coffee dict included when at least one field set | Section 6.1 |
| `test_row_to_brew_dict_coffee_object_omitted` | coffee dict absent when all coffee fields NULL | AC-24 |
| `test_row_to_brew_dict_water_object_included` | water dict included when ppm set | Section 6.1 |
| `test_row_to_brew_dict_water_object_omitted` | water dict absent when ppm NULL | AC-24 |
| `test_row_to_brew_dict_origin_deserialised` | JSON string `'["Ethiopia"]'` becomes `["Ethiopia"]` | Section 6.1 |
| `test_row_to_brew_dict_origin_multi` | multi-origin round-trips correctly | AC-8 |
| `test_rows_to_brewspec_document_structure` | top-level keys are `brewspec_version` and `brews` | AC-23 |
| `test_validate_export_path_rejects_dotdot` | `../evil` rejected | AC-26 |
| `test_validate_export_path_rejects_embedded_dotdot` | `foo/../bar` rejected | AC-26 |
| `test_validate_export_path_rejects_missing_parent` | parent dir does not exist → error | AC-26 |
| `test_validate_import_path_rejects_dotdot` | `../evil.yaml` rejected | AC-32 |
| `test_validate_import_path_rejects_oversized` | file > 10MB rejected before parse | AC-32 |
| `test_validate_import_path_rejects_missing_file` | non-existent path rejected | AC-28 |

### 7.6 `tests/test_cmd_add.py` — CLI integration tests

Uses `CliRunner(mix_stderr=False)` for clean stderr separation.

| Test function | What it tests | AC |
|---|---|---|
| `test_add_all_flags_no_prompts` | all 4 required flags → no prompts, brew logged | AC-11 |
| `test_add_confirmation_message` | output contains `Brew #1 logged.` | AC-10 |
| `test_add_invalid_type_flag` | `--type invalid` → error, exit 1, no DB write | AC-9 |
| `test_add_invalid_dose_zero` | `--dose 0` → error, exit 1 | AC-9 |
| `test_add_invalid_dose_negative` | `--dose -5` → error, exit 1 | AC-9 |
| `test_add_invalid_temp_out_of_range` | `--temp 101` → error, exit 1 | AC-9 |
| `test_add_invalid_rating_out_of_range` | `--rating 6` → error, exit 1 | AC-9 |
| `test_add_invalid_duration_zero` | `--duration 0` → error, exit 1 | AC-9 |
| `test_add_invalid_roast_date_format` | `--roast-date 01-20-2026` → error, exit 1 | AC-9 |
| `test_add_invalid_coffee_type` | `--coffee-type espresso` → error, exit 1 | AC-9 |
| `test_add_origin_multiple` | `--origin Ethiopia --origin Colombia` stored as list | AC-8 |
| `test_add_interactive_accepts_default_date` | empty Enter for date uses current UTC | AC-5, AC-6 |
| `test_add_interactive_reprompts_invalid_type` | invalid type re-prompts with error | AC-7 |
| `test_add_interactive_reprompts_invalid_dose` | non-numeric dose re-prompts | AC-7 |
| `test_add_optional_fields_stored` | all optional flags round-trip through DB | AC-8 |
| `test_add_db_auto_created` | first add creates DB file | AC-3 |

### 7.7 `tests/test_cmd_list.py` — CLI integration tests

| Test function | What it tests | AC |
|---|---|---|
| `test_list_empty_db_message` | friendly message when no brews | AC-16 |
| `test_list_empty_db_exit_zero` | exit code 0 when empty | AC-16 |
| `test_list_shows_table_headers` | column headers in output | AC-13 |
| `test_list_default_limit_20` | at most 20 rows with default call | AC-12 |
| `test_list_custom_limit` | `--limit 5` returns at most 5 rows | AC-14 |
| `test_list_all` | `--all` returns all brews | AC-15 |
| `test_list_limit_invalid_zero` | `--limit 0` → error, exit 1 | AC-14 |
| `test_list_limit_invalid_negative` | `--limit -1` → error, exit 1 | AC-14 |
| `test_list_optional_field_dash_when_absent` | missing optional field shows `-` | AC-13 |
| `test_list_order_most_recent_first` | row order matches date desc | AC-12 |

### 7.8 `tests/test_cmd_show.py` — CLI integration tests

| Test function | What it tests | AC |
|---|---|---|
| `test_show_existing_brew` | shows all fields for brew #1 | AC-17 |
| `test_show_groups_fields` | brew parameters, results, coffee, water sections present | AC-18 |
| `test_show_omits_null_fields` | field not set is absent from output | AC-17 |
| `test_show_omits_empty_sections` | no coffee section if no coffee metadata | AC-18 |
| `test_show_not_found_message` | `No brew found with ID 999.` printed | AC-19 |
| `test_show_not_found_exit_nonzero` | exit code 1 when not found | AC-19 |
| `test_show_no_argument_error` | missing ID → usage error, exit nonzero | AC-20 |

### 7.9 `tests/test_cmd_export.py` — CLI integration tests

| Test function | What it tests | AC |
|---|---|---|
| `test_export_yaml_creates_file` | file exists at path after export | AC-21 |
| `test_export_yaml_valid_schema` | exported YAML passes `validate_document()` | AC-21 |
| `test_export_json_creates_file` | `--format json` creates JSON file | AC-22 |
| `test_export_json_valid_schema` | exported JSON passes `validate_document()` | AC-22 |
| `test_export_document_structure` | top-level keys: brewspec_version, brews | AC-23 |
| `test_export_no_null_values` | no null values in exported YAML | AC-24 |
| `test_export_no_empty_objects` | empty coffee/water objects absent | AC-24 |
| `test_export_empty_db_exits_clean` | `No brews to export.` message, exit 0, no file written | AC-25 |
| `test_export_path_dotdot_rejected` | `../out.yaml` → error, exit 1 | AC-26 |
| `test_export_missing_parent_dir` | parent dir does not exist → error, exit 1 | AC-26 |
| `test_export_overwrite_prompts` | existing file → confirmation prompt shown | AC-27 |
| `test_export_force_skips_prompt` | `--force` skips overwrite prompt | AC-27 |

### 7.10 `tests/test_cmd_import.py` — CLI integration tests

| Test function | What it tests | AC |
|---|---|---|
| `test_import_yaml_success` | imports valid YAML, prints `Imported N brews.` | AC-28, AC-30 |
| `test_import_json_success` | imports valid JSON | AC-28 |
| `test_import_invalid_schema_rejected` | file with missing field → error, exit 1, no DB write | AC-29 |
| `test_import_wrong_version_rejected` | `brewspec_version: "0.1"` → error, exit 1 | AC-29 |
| `test_import_no_partial_write` | invalid file after valid brews → no rows inserted | AC-29 |
| `test_import_path_dotdot_rejected` | path with `..` → error, exit 1 | AC-32 |
| `test_import_file_too_large` | file > 10MB → error before parse, exit 1 | AC-32 |
| `test_import_appends_not_replaces` | import twice → 2x rows (no dedup) | AC-33 |
| `test_import_uses_safe_load` | YAML load does not execute arbitrary Python objects | AC-31 |
| `test_import_unknown_extension_rejected` | `.csv` extension → error, exit 1 | AC-28 |
| `test_import_count_message` | `Imported 3 brews.` for a 3-brew file | AC-30 |

### 7.11 `tests/test_roundtrip.py` — end-to-end round-trip

| Test function | What it tests | AC |
|---|---|---|
| `test_export_import_roundtrip_yaml` | add 3 brews → export YAML → import to fresh DB → all fields match | AC-21, AC-28 |
| `test_export_import_roundtrip_json` | same as above with JSON | AC-22, AC-28 |
| `test_roundtrip_origin_array_preserved` | multi-origin blend survives export/import unchanged | AC-8 |
| `test_roundtrip_optional_absent_fields_omitted` | null fields absent after round-trip | AC-24 |
| `test_roundtrip_schema_valid_at_midpoint` | exported file passes JSON Schema validation independently | AC-21 |

### 7.12 `tests/test_cmd_welcome.py`

| Test function | What it tests | AC |
|---|---|---|
| `test_no_args_shows_ascii_cup` | ASCII cup in output | AC-34 |
| `test_no_args_shows_version` | version string in output | AC-34 |
| `test_no_args_shows_help` | command list in output | AC-34 |
| `test_no_args_exit_zero` | exit code 0 | AC-35 |
| `test_subcommand_no_ascii_cup` | `brewlog list` output does not contain ASCII cup | AC-36 |

### 7.13 AC-to-test mapping summary

| AC | Primary test file(s) |
|---|---|
| AC-1 | Manual install check; not a pytest test |
| AC-2 | `test_cmd_welcome.py` |
| AC-3 | `test_cmd_add.py::test_add_db_auto_created`, `test_db.py::test_init_db_idempotent` |
| AC-4 | `test_db.py::test_init_db_creates_table`, `test_init_db_creates_index` |
| AC-5 | `test_cmd_add.py::test_add_interactive_accepts_default_date` |
| AC-6 | `test_cmd_add.py::test_add_interactive_accepts_default_date` (prompt text check) |
| AC-7 | `test_cmd_add.py::test_add_interactive_reprompts_*` |
| AC-8 | `test_models.py::test_brew_input_valid_all_fields`, `test_cmd_add.py::test_add_optional_fields_stored` |
| AC-9 | `test_models.py` (all constraint tests), `test_cmd_add.py` (invalid flag tests) |
| AC-10 | `test_cmd_add.py::test_add_confirmation_message` |
| AC-11 | `test_cmd_add.py::test_add_all_flags_no_prompts` |
| AC-12 | `test_cmd_list.py::test_list_default_limit_20`, `test_list_order_most_recent_first` |
| AC-13 | `test_cmd_list.py::test_list_shows_table_headers`, `test_list_optional_field_dash_when_absent` |
| AC-14 | `test_cmd_list.py::test_list_custom_limit`, `test_list_limit_invalid_*` |
| AC-15 | `test_cmd_list.py::test_list_all` |
| AC-16 | `test_cmd_list.py::test_list_empty_db_message`, `test_list_empty_db_exit_zero` |
| AC-17 | `test_cmd_show.py::test_show_existing_brew`, `test_show_omits_null_fields` |
| AC-18 | `test_cmd_show.py::test_show_groups_fields`, `test_show_omits_empty_sections` |
| AC-19 | `test_cmd_show.py::test_show_not_found_message`, `test_show_not_found_exit_nonzero` |
| AC-20 | `test_cmd_show.py::test_show_no_argument_error` |
| AC-21 | `test_cmd_export.py::test_export_yaml_*`, `test_roundtrip.py` |
| AC-22 | `test_cmd_export.py::test_export_json_*` |
| AC-23 | `test_cmd_export.py::test_export_document_structure` |
| AC-24 | `test_cmd_export.py::test_export_no_null_values`, `test_export_no_empty_objects` |
| AC-25 | `test_cmd_export.py::test_export_empty_db_exits_clean` |
| AC-26 | `test_cmd_export.py::test_export_path_dotdot_rejected`, `test_export_missing_parent_dir` |
| AC-27 | `test_cmd_export.py::test_export_overwrite_prompts`, `test_export_force_skips_prompt` |
| AC-28 | `test_cmd_import.py::test_import_yaml_success`, `test_import_json_success` |
| AC-29 | `test_cmd_import.py::test_import_invalid_schema_rejected`, `test_import_no_partial_write` |
| AC-30 | `test_cmd_import.py::test_import_count_message` |
| AC-31 | `test_cmd_import.py::test_import_uses_safe_load` |
| AC-32 | `test_cmd_import.py::test_import_path_dotdot_rejected`, `test_import_file_too_large` |
| AC-33 | `test_db.py::test_insert_brew_dict_no_dedup`, `test_cmd_import.py::test_import_appends_not_replaces` |
| AC-34 | `test_cmd_welcome.py::test_no_args_shows_ascii_cup`, `test_no_args_shows_version` |
| AC-35 | `test_cmd_welcome.py::test_no_args_exit_zero` |
| AC-36 | `test_cmd_welcome.py::test_subcommand_no_ascii_cup` |

---

## 8. Security Checklist

This section maps each security requirement from `specs/products/brewlog.md` to the
design element that satisfies it.

### 8.1 SQL injection prevention

**Requirement (AC-9 / Security section):** All DB reads and writes use parameterised
queries. No string interpolation into SQL.

**How the design satisfies it:**
- `insert_brew()` (Section 5.3): All 18 column values supplied via `?` placeholder
  tuple. SQL string is a hardcoded constant with no f-strings or `.format()`.
- `insert_brew_dict()` (Section 5.8): Same pattern. 18 `?` placeholders.
- `get_brew()` (Section 5.4): `WHERE id = ?` with `(brew_id,)` tuple.
- `list_brews()` (Section 5.5): `LIMIT ?` with `(limit,)` tuple.
- `_init_schema()` (Section 5.2): Uses `executescript()` with a hardcoded string —
  no user input ever reaches this function.
- Test coverage: `test_db.py::test_parameterised_query_safety` verifies that
  text fields containing `'; DROP TABLE brews; --` are stored and retrieved as
  plain strings without corrupting the schema.

### 8.2 Safe YAML parsing

**Requirement (AC-31):** All YAML parsing uses `yaml.safe_load()`. `yaml.load()`
without a safe loader is prohibited.

**How the design satisfies it:**
- `import_.py` command: calls `yaml.safe_load(f.read())` exclusively.
- No other file in the package parses YAML. Export uses `yaml.dump()`, which is
  output-only.
- Test coverage: `test_cmd_import.py::test_import_uses_safe_load` passes a YAML
  file containing a Python-object constructor tag (e.g., `!!python/object/apply:os.system`)
  and verifies that the import either rejects it at the schema validation step or
  that `yaml.safe_load()` raises a `yaml.constructor.ConstructorError` — confirming
  the safe loader is in use.

### 8.3 Path traversal prevention

**Requirement (AC-26, AC-32):** Paths containing `..` are rejected before any file
I/O. Files > 10MB are rejected before parsing on import.

**How the design satisfies it:**
- `validate_export_path()` (Section 6.2): Checks `".." in p.parts`. Checks that
  `p.parent.exists()`. Calls `sys.exit(1)` on failure.
- `validate_import_path()` (Section 6.2): Same `..` check. Additionally checks
  `p.stat().st_size > 10 * 1024 * 1024` before opening the file.
- Both functions are called at the top of their respective command functions,
  before any DB connection or file read.
- Test coverage: `test_serialise.py::test_validate_export_path_rejects_dotdot`,
  `test_validate_import_path_rejects_dotdot`, `test_validate_import_path_rejects_oversized`.

### 8.4 Input validation at application layer

**Requirement:** All user-supplied values validated via Pydantic before DB write.

**How the design satisfies it:**
- `BrewInput`, `CoffeeInput`, `WaterInput` (Section 2) enforce all BrewSpec v0.2
  constraints: enum values, numeric ranges, date patterns, minLength on text fields.
- Validation occurs in the `add` command before `insert_brew()` is called.
- For import, JSON Schema validation (`validate_document()`) acts as the first gate
  before any DB write.
- The DB layer (`insert_brew()`, `insert_brew_dict()`) does not perform independent
  validation — it trusts the layer above. This is acceptable because the command
  functions are the only callers, and they validate first.

### 8.5 No secrets in code

**Requirement:** No API keys, credentials, tokens, or secrets in source or fixtures.

**How the design satisfies it:**
- The only hardcoded path is `~/.brewlog/brews.db`, which is explicitly documented
  as non-sensitive in the product spec.
- No authentication, no tokens, no API endpoints.
- Fixtures in `tests/fixtures/` contain only sample brew data (dates, weights,
  method names). No PII, no credentials.

### 8.6 No network calls

**Requirement:** All operations are local and offline. No network calls permitted.

**How the design satisfies it:**
- No HTTP client library is imported anywhere in the package.
- The JSON Schema is bundled with the package (`src/brewlog/brewspec.schema.json`)
  and loaded via `importlib.resources`. The `$id` URL in the schema is metadata only
  — `jsonschema` does not fetch it for `Draft202012Validator`.
- `requirements.txt` includes no HTTP client libraries.
- No calls to `urllib`, `httpx`, `requests`, or `socket`.

### 8.7 Freeform text safety

**Requirement:** Freeform text fields (`method`, `grind`, `notes`, `varietal`,
`process`) must be stored and displayed as plain text. Never executed or interpolated.

**How the design satisfies it:**
- These fields are passed as `?` parameters in SQL — the DB treats them as string
  literals.
- `show` command outputs field values via `click.echo(f"  Notes: {value}")` — string
  interpolation into a `click.echo()` call is display-only, not execution.
- No `eval()`, `exec()`, `subprocess`, or shell command construction anywhere in
  the package.
- `minLength: 1` validators on text fields prevent empty-string sentinel values
  that could confuse display logic.

### 8.8 Data integrity on corrupt DB

**Consideration:** What happens if `~/.brewlog/brews.db` is corrupted?

**Design decision:** The tool lets `sqlite3` surface its native exception
(`sqlite3.DatabaseError`). The command catches it, prints a user-readable message
(`Error: database is corrupted or unreadable. Check ~/.brewlog/brews.db.`), and
exits with code 1. No automatic repair or data deletion. The user is responsible
for their local data. Export before any manual DB intervention is the recovery path.
This is documented in the help text for the `--help` output of `export`.

### 8.9 Trust boundary summary

```
User input (CLI flags / interactive prompts)
  --> Pydantic BrewInput validation (type, range, enum, pattern checks)
      --> db.insert_brew() with ? parameterised SQL
          --> SQLite file at ~/.brewlog/brews.db

File input (import path)
  --> validate_import_path() (path traversal, size limit)
      --> yaml.safe_load() or json.loads()
          --> schema.validate_document() against JSON Schema
              --> db.insert_brew_dict() with ? parameterised SQL
                  --> SQLite file

DB row (read for export)
  --> serialise.row_to_brew_dict() (NULL omission, JSON deserialization)
      --> schema.validate_document() (safety net)
          --> yaml.dump() / json.dumps() to file
```

No user input reaches the DB without passing through the Pydantic or JSON Schema
validation layer first. No file content reaches the DB without passing through both
the size check and schema validation first.

---

## Appendix A: `requirements.txt` (dev + test)

```
# Runtime (also declared in pyproject.toml)
click>=8.1
pyyaml>=6.0
pydantic>=2.0
jsonschema>=4.18

# Test
pytest>=8.0
```

No other dependencies. `sqlite3` is stdlib. `importlib.resources` is stdlib (3.9+).
`json`, `re`, `sys`, `pathlib`, `datetime` are all stdlib.

---

## Appendix B: Open question resolution

**Import duplicate handling (from product spec open questions):**
No additional handling at the database layer is needed in v0.1. The design uses
plain `INSERT` with no `INSERT OR IGNORE` or `UNIQUE` constraints. Re-importing the
same file creates duplicate rows. This is the specified behaviour (AC-33) and is
documented explicitly. A `UNIQUE` constraint on `(date, type, dose_g, water_weight_g)`
is a candidate for v0.2 but is not included here — the uniqueness semantics for
brews are non-obvious (two brews with identical parameters are plausibly distinct).
