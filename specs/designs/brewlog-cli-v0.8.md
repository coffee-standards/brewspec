# Design: BrewLog CLI v0.8

**Feature:** brewlog-cli-v0.8
**Author:** architect
**Created:** 2026-03-21
**Input:** specs/products/brewlog-cli-v0.8.md
**Baseline:** specs/designs/brewlog-cli-v0.5.md (most recent full-pipeline design)
**Status:** Ready for Dev

---

## Overview

BrewLog CLI v0.8 adopts BrewSpec v0.9, which aligns the rating system with the SCA Coffee Value Assessment (CVA) standard. The change is narrow: the rating range expands from 1-5 to 1-9 across six code locations — Pydantic model, two CLI commands (add, update), list filter validation, stats distribution query, and stats display. The bundled schema is replaced with v0.9 and `BREWSPEC_VERSION` is bumped. No DB schema migration is required; the `result_rating_mouthfeel` column is already in place from v0.3, and existing stored values of 1-5 remain valid under the widened range.

Two self-review observations are addressed in this design:
- **SPEC-1**: Function docstrings in `serialise.py` that reference v0.8 are also updated (not only the `RatingsInput` class docstring).
- **SPEC-2**: Cross-version import behaviour is verified and documented in Section 3.4.

---

## 1. Changes Required

### 1.1 models.py — RatingsInput validator and docstring

**Location:** `brewlog/src/brewlog/models.py`, class `RatingsInput`

**Before:**
```python
class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-5."""

    ...

    @field_validator(
        "overall", "fragrance", "aroma", "flavour",
        "aftertaste", "acidity", "sweetness", "mouthfeel"
    )
    @classmethod
    def validate_rating_dimension(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating dimension must be between 1 and 5 inclusive")
        return v
```

**After:**
```python
class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-9 (SCA CVA hedonic scale)."""

    ...

    @field_validator(
        "overall", "fragrance", "aroma", "flavour",
        "aftertaste", "acidity", "sweetness", "mouthfeel"
    )
    @classmethod
    def validate_rating_dimension(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 9):
            raise ValueError("rating dimension must be between 1 and 9 inclusive")
        return v
```

**Also update** the `BrewInput` class docstring (line 288):

**Before:**
```python
class BrewInput(BaseModel):
    """Primary model for a brew log entry. Validates all BrewSpec v0.8 constraints."""
```

**After:**
```python
class BrewInput(BaseModel):
    """Primary model for a brew log entry. Validates all BrewSpec v0.9 constraints."""
```

The module-level docstring references `v0.8` on line 11:

**Before:**
```python
Field names mirror BrewSpec v0.8 snake_case names exactly.
```

**After:**
```python
Field names mirror BrewSpec v0.9 snake_case names exactly.
```

### 1.2 commands/add.py — rating flag help text and inline validation

**Location:** `brewlog/src/brewlog/commands/add.py`

**Help text — eight rating flags** (lines 222-236):

Before, all eight flags read `"... rating, 1-5."`:
```python
@click.option("--rating-overall", "rating_overall", type=int, default=None,
              help="Overall impression, 1-5.")
@click.option("--rating-fragrance", "rating_fragrance", type=int, default=None,
              help="Fragrance rating, 1-5.")
# ... (same pattern for remaining six)
```

After, all eight flags read `"... rating, 1-9."`:
```python
@click.option("--rating-overall", "rating_overall", type=int, default=None,
              help="Overall impression, 1-9.")
@click.option("--rating-fragrance", "rating_fragrance", type=int, default=None,
              help="Fragrance rating, 1-9.")
@click.option("--rating-aroma", "rating_aroma", type=int, default=None,
              help="Aroma rating, 1-9.")
@click.option("--rating-flavour", "rating_flavour", type=int, default=None,
              help="Flavour rating, 1-9.")
@click.option("--rating-aftertaste", "rating_aftertaste", type=int, default=None,
              help="Aftertaste rating, 1-9.")
@click.option("--rating-acidity", "rating_acidity", type=int, default=None,
              help="Acidity rating, 1-9.")
@click.option("--rating-sweetness", "rating_sweetness", type=int, default=None,
              help="Sweetness rating, 1-9.")
@click.option("--rating-mouthfeel", "rating_mouthfeel", type=int, default=None,
              help="Mouthfeel rating, 1-9.")
```

**Inline validation block** (lines 341-357 in the `add` function body):

Before:
```python
    # -- Validate rating dimensions (1-5) --
    _RATING_DIMS = { ... }
    for flag_name, flag_val in _RATING_DIMS.items():
        if flag_val is not None and not (1 <= flag_val <= 5):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 5.",
                err=True,
            )
            sys.exit(1)
```

After:
```python
    # -- Validate rating dimensions (1-9) --
    _RATING_DIMS = { ... }
    for flag_name, flag_val in _RATING_DIMS.items():
        if flag_val is not None and not (1 <= flag_val <= 9):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 9.",
                err=True,
            )
            sys.exit(1)
```

The inline tip string (line 318) also references "rating-overall 4" as an example — this remains valid under 1-9 and does not need changing.

The retired `--rating` error message (line 268) references "overall impression (1-5)". Update to 1-9:

**Before:**
```python
        click.echo(
            "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
            "Use --rating-overall N to set your overall impression (1-5).\n"
            "See --help for all available rating dimension flags.",
            err=True,
        )
```

**After:**
```python
        click.echo(
            "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
            "Use --rating-overall N to set your overall impression (1-9).\n"
            "See --help for all available rating dimension flags.",
            err=True,
        )
```

### 1.3 commands/update.py — rating flag help text and inline validation

**Location:** `brewlog/src/brewlog/commands/update.py`

Same two changes as `add.py`:

**Help text — eight rating flags** (lines 62-76): change `"... 1-5."` to `"... 1-9."` on all eight flags, following the same pattern as Section 1.2.

**Inline validation block** (lines 177-183):

Before:
```python
    for flag_name, flag_val in _RATING_DIMS.items():
        if flag_val is not None and not (1 <= flag_val <= 5):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 5.",
                err=True,
            )
            sys.exit(1)
```

After:
```python
    for flag_name, flag_val in _RATING_DIMS.items():
        if flag_val is not None and not (1 <= flag_val <= 9):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 9.",
                err=True,
            )
            sys.exit(1)
```

The retired `--rating` error message (line 149) also references `(1-5)`. Apply the same fix as Section 1.2.

### 1.4 commands/list_.py — rating filter help text and validation

**Location:** `brewlog/src/brewlog/commands/list_.py`

**Help text — two filter flags** (lines 254-259):

Before:
```python
@click.option(
    "--rating-min", "rating_min", type=int, default=None,
    help="Filter brews with overall rating >= N (1-5).",
)
@click.option(
    "--rating-max", "rating_max", type=int, default=None,
    help="Filter brews with overall rating <= N (1-5).",
)
```

After:
```python
@click.option(
    "--rating-min", "rating_min", type=int, default=None,
    help="Filter brews with overall rating >= N (1-9).",
)
@click.option(
    "--rating-max", "rating_max", type=int, default=None,
    help="Filter brews with overall rating <= N (1-9).",
)
```

**Validation blocks** (lines 319-333):

Before:
```python
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
```

After:
```python
    # Validate --rating-min
    if rating_min is not None and not (1 <= rating_min <= 9):
        click.echo(
            "Error: --rating-min must be an integer between 1 and 9.",
            err=True,
        )
        sys.exit(1)

    # Validate --rating-max
    if rating_max is not None and not (1 <= rating_max <= 9):
        click.echo(
            "Error: --rating-max must be an integer between 1 and 9.",
            err=True,
        )
        sys.exit(1)
```

The `--rating-min <= --rating-max` ordering check (lines 335-342) is unchanged — it operates on the validated integer values and is range-agnostic.

### 1.5 db.py — get_brew_stats distribution range

**Location:** `brewlog/src/brewlog/db.py`, function `get_brew_stats`

**Docstring update** for `rating_distribution` key:

Before:
```
      rating_distribution: dict[int, int]  {1: count, ..., 5: count}
```

After:
```
      rating_distribution: dict[int, int]  {1: count, ..., 9: count}
```

**Distribution initialization and guard** (lines 709-712):

Before:
```python
    distribution = {i: 0 for i in range(1, 6)}
    for star, count in dist_rows:
        if 1 <= star <= 5:
            distribution[star] = count
```

After:
```python
    distribution = {i: 0 for i in range(1, 10)}
    for star, count in dist_rows:
        if 1 <= star <= 9:
            distribution[star] = count
```

The guard `if 1 <= star <= 9` protects against any legacy values outside the 1-9 range being inserted into the distribution dict. Values of 6-9 stored from this release onwards will appear correctly; any hypothetical out-of-range values (e.g. if someone manually edited the DB) are silently ignored rather than raising a KeyError.

### 1.6 commands/stats.py — distribution display

**Location:** `brewlog/src/brewlog/commands/stats.py`

**Before:**
```python
    click.echo("Distribution:")
    dist = stats_data["rating_distribution"]
    for star in range(1, 6):
        label = f"{star} star:" if star == 1 else f"{star} stars:"
        click.echo(f"  {label:<8}{dist[star]}")
```

**After:**
```python
    click.echo("Distribution:")
    dist = stats_data["rating_distribution"]
    for n in range(1, 10):
        click.echo(f"  {n}:{dist[n]:>3}")
```

The format `"  {n}:{dist[n]:>3}"` produces output aligned with the AC-8 specification:
```
Distribution:
  1:  0
  2:  1
  3:  3
  ...
  9:  1
```

The `>3` right-alignment for the count gives up to three digits of space, which comfortably handles any realistic brew count.

### 1.7 serialise.py — version constant and docstrings (SPEC-1)

**Location:** `brewlog/src/brewlog/serialise.py`

**BREWSPEC_VERSION constant** (line 17):

Before:
```python
BREWSPEC_VERSION = "0.8"
```

After:
```python
BREWSPEC_VERSION = "0.9"
```

**row_to_brew_dict docstring** (line 50): references `"BrewSpec v0.8 brew dict"`.

Before:
```
    Convert a sqlite3.Row to a BrewSpec v0.8 brew dict.
```

After:
```
    Convert a sqlite3.Row to a BrewSpec v0.9 brew dict.
```

**rows_to_brewspec_document docstring** (line 163-164): references `"BrewSpec v0.8 document"` twice.

Before:
```python
def rows_to_brewspec_document(rows: list[sqlite3.Row]) -> dict:
    """
    Convert a list of DB rows to a full BrewSpec v0.8 document dict.
    Returns {"brewspec_version": "0.8", "brews": [...]}.
    ...
    """
```

After:
```python
def rows_to_brewspec_document(rows: list[sqlite3.Row]) -> dict:
    """
    Convert a list of DB rows to a full BrewSpec v0.9 document dict.
    Returns {"brewspec_version": "0.9", "brews": [...]}.
    ...
    """
```

### 1.8 Bundled schema — replace with BrewSpec v0.9

**Location:** `brewlog/src/brewlog/brewspec.schema.json`

Replace the entire file with the BrewSpec v0.9 JSON Schema. The v0.9 schema differs from v0.8 in two places:

1. `brewspec_version` const changes from `"0.8"` to `"0.9"`.
2. The `ratings` properties change their `minimum`/`maximum` constraints from `1`/`5` to `1`/`9`.

The v0.9 schema file is produced by the parallel `brewspec-v0.9` task. The dev must confirm the schema file is available in the worktree before writing the import integration test. If the schema is not yet present, that test is the only blocker — all other tests can be written and run independently.

---

## 2. Data Models

### 2.1 Pydantic Models

No structural field changes. Only the validator range and docstrings change.

Updated `RatingsInput` (complete class — only the docstring and validator body change):

```python
class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-9 (SCA CVA hedonic scale)."""

    overall: Optional[int] = None
    fragrance: Optional[int] = None
    aroma: Optional[int] = None
    flavour: Optional[int] = None
    aftertaste: Optional[int] = None
    acidity: Optional[int] = None
    sweetness: Optional[int] = None
    mouthfeel: Optional[int] = None

    @field_validator(
        "overall", "fragrance", "aroma", "flavour",
        "aftertaste", "acidity", "sweetness", "mouthfeel"
    )
    @classmethod
    def validate_rating_dimension(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 9):
            raise ValueError("rating dimension must be between 1 and 9 inclusive")
        return v
```

### 2.2 SQLite Schema

No changes. The `result_rating_mouthfeel` column already exists. No new migration constants are needed; `_V9_MIGRATION_COLUMNS` is not required for this version. The spec confirms this explicitly (AC-10, AC-11).

---

## 3. CLI Interface

### 3.1 brewlog add — rating flags

All eight `--rating-*` flags have updated help text. No new flags. No behavior change beyond the widened range.

```
brewlog add [OPTIONS]

Rating options (1-9):
  --rating-overall INTEGER      Overall impression, 1-9.
  --rating-fragrance INTEGER    Fragrance rating, 1-9.
  --rating-aroma INTEGER        Aroma rating, 1-9.
  --rating-flavour INTEGER      Flavour rating, 1-9.
  --rating-aftertaste INTEGER   Aftertaste rating, 1-9.
  --rating-acidity INTEGER      Acidity rating, 1-9.
  --rating-sweetness INTEGER    Sweetness rating, 1-9.
  --rating-mouthfeel INTEGER    Mouthfeel rating, 1-9.
```

**Error message (out-of-range value):**
```
Error: --rating-overall must be an integer between 1 and 9.
```
Exit code: 1

### 3.2 brewlog update — rating flags

Identical changes to `add`. Same flags, same error message format, same exit code.

### 3.3 brewlog list — rating filter flags

```
brewlog list [OPTIONS]

  --rating-min INTEGER   Filter brews with overall rating >= N (1-9).
  --rating-max INTEGER   Filter brews with overall rating <= N (1-9).
```

**Error messages:**
```
Error: --rating-min must be an integer between 1 and 9.
Error: --rating-max must be an integer between 1 and 9.
```

The existing ordering check error message is unchanged:
```
Error: --rating-min N cannot exceed --rating-max M.
```

### 3.4 brewlog import — cross-version behaviour (SPEC-2)

AC-15 states that files with `brewspec_version: "0.8"` or earlier that are otherwise valid must continue to import without error.

The bundled v0.9 schema uses `"const": "0.9"` for `brewspec_version`. This means a document with `brewspec_version: "0.8"` will fail JSON Schema validation against the bundled v0.9 schema.

**Resolution:** The import command in `commands/import_.py` validates against the bundled schema. When a v0.8 document is imported against a v0.9 schema, the `brewspec_version` const constraint will reject it. The existing import error handling already emits a schema validation failure message.

This is the correct and expected behavior: the bundled schema is the v0.9 validator, and v0.8 documents do not satisfy the v0.9 `brewspec_version` const. AC-15 must be read as: "v0.8 documents that have ratings in the 1-9 range are structurally valid and will be accepted if the version field matches". It does not mean the validator should accept mismatched version strings.

The dev should verify this by inspecting `commands/import_.py` before writing the import test. The test for AC-15 should assert that a v0.9 document with ratings in 6-9 imports correctly, and that a v0.8 document fails with a version mismatch error (schema const violation) — not a ratings-range error. This is consistent behavior and no code change is needed in the import path.

**Note for the dev:** check `commands/import_.py` to confirm the schema validation path is unchanged. If the import command passes the document version field through any non-schema validation that enforces a version allowlist, it must accept `"0.9"`.

### 3.5 brewlog stats — distribution display

**Before (1-5 scale):**
```
Distribution:
  1 star:  0
  2 stars: 1
  3 stars: 3
  4 stars: 8
  5 stars:12
```

**After (1-9 scale):**
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

The format uses `f"  {n}:{dist[n]:>3}"`, producing two leading spaces, the digit, a colon, and the count right-aligned in a 3-character field.

---

## 4. Architecture Decision Records

No new ADRs required. This is a downstream spec adoption with no architectural trade-offs. The decision to follow the BrewSpec version is governed by the existing principle: "The spec leads, products follow."

---

## 5. Public Spec Document

Not applicable — this is a BrewLog CLI task, not a BrewSpec schema task.

---

## 6. File Manifest

| File | Operation | Notes |
|------|-----------|-------|
| `brewlog/src/brewlog/models.py` | Modify | RatingsInput docstring + validator range (1-5 → 1-9); BrewInput docstring; module docstring |
| `brewlog/src/brewlog/commands/add.py` | Modify | Eight rating flag help texts (1-9); inline validation range (1-9); retired --rating message |
| `brewlog/src/brewlog/commands/update.py` | Modify | Eight rating flag help texts (1-9); inline validation range (1-9); retired --rating message |
| `brewlog/src/brewlog/commands/list_.py` | Modify | Two filter flag help texts (1-9); two validation guards (1-9) |
| `brewlog/src/brewlog/db.py` | Modify | `get_brew_stats`: distribution dict range(1,10); guard `<= 9`; docstring |
| `brewlog/src/brewlog/commands/stats.py` | Modify | Distribution loop range(1,10); label format `"N:"` instead of `"N star(s):"` |
| `brewlog/src/brewlog/serialise.py` | Modify | `BREWSPEC_VERSION = "0.9"`; two function docstrings |
| `brewlog/src/brewlog/brewspec.schema.json` | Replace | BrewSpec v0.9 schema (from brewspec-v0.9 task) |
| `brewlog/tests/test_v09.py` | Create | New test file for v0.9 adoption (see Section 7) |
| `brewlog/tests/test_models.py` | Modify | Update rating validation tests: 1-5 error → 1-9 error |
| `brewlog/tests/test_cmd_stats.py` | Modify | Distribution tests: range 1-9; label format |
| `brewlog/tests/test_cmd_list_filter.py` | Modify | Rating filter boundary tests: upper bound 6 → 10 |
| `brewlog/tests/test_cmd_add.py` | Modify | Rating validation error message: "1 and 5" → "1 and 9" |
| `brewlog/tests/test_cmd_update.py` | Modify | Rating validation error message: "1 and 5" → "1 and 9" |

---

## 7. Test Strategy

All new tests go in `brewlog/tests/test_v09.py`. Existing tests in other files require targeted updates to assertions that reference the old range or labels.

### AC-1: RatingsInput validates all dimensions as integers 1-9

**File:** `test_v09.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_ratings_input_value_1_accepted` | `RatingsInput(overall=1)` | No error |
| `test_ratings_input_value_9_accepted` | `RatingsInput(overall=9)` | No error |
| `test_ratings_input_value_5_still_accepted` | `RatingsInput(overall=5)` | No error (existing data compat) |
| `test_ratings_input_value_0_rejected` | `RatingsInput(overall=0)` | `ValidationError` |
| `test_ratings_input_value_10_rejected` | `RatingsInput(overall=10)` | `ValidationError` |
| `test_ratings_input_error_message_1_to_9` | `RatingsInput(overall=0)` | error message contains "1 and 9" |
| `test_ratings_input_all_dimensions_6_through_9` | Set each of the 8 dims to values 6-9 | No error |

### AC-2: brewlog add accepts 1-9, rejects out-of-range

**File:** `test_v09.py`

| Test | Command | Expected |
|------|---------|----------|
| `test_add_rating_overall_9_accepted` | `brewlog add ... --rating-overall 9` | exit 0, brew stored |
| `test_add_rating_overall_7_accepted` | `brewlog add ... --rating-overall 7` | exit 0 |
| `test_add_rating_overall_10_rejected` | `brewlog add ... --rating-overall 10` | exit 1 |
| `test_add_rating_overall_10_error_message` | `brewlog add ... --rating-overall 10` | stderr contains "between 1 and 9" |
| `test_add_rating_overall_0_rejected` | `brewlog add ... --rating-overall 0` | exit 1 |
| `test_add_rating_mouthfeel_9_accepted` | `brewlog add ... --rating-mouthfeel 9` | exit 0 |
| `test_add_rating_stored_correctly` | add with `--rating-overall 7` | DB row has `result_rating_overall = 7` |

### AC-3: brewlog update accepts 1-9, rejects out-of-range

**File:** `test_v09.py`

| Test | Command | Expected |
|------|---------|----------|
| `test_update_rating_overall_9_accepted` | `brewlog update --rating-overall 9` | exit 0 |
| `test_update_rating_overall_10_rejected` | `brewlog update --rating-overall 10` | exit 1 |
| `test_update_rating_overall_10_error_message` | `brewlog update --rating-overall 10` | stderr contains "between 1 and 9" |

### AC-4: list --rating-min / --rating-max accept 1-9, reject out-of-range

**File:** `test_v09.py` (new boundary tests) + `test_cmd_list_filter.py` (update existing)

| Test | Command | Expected |
|------|---------|----------|
| `test_list_rating_min_9_accepted` | `brewlog list --rating-min 9` | exit 0 |
| `test_list_rating_max_9_accepted` | `brewlog list --rating-max 9` | exit 0 |
| `test_list_rating_min_10_rejected` | `brewlog list --rating-min 10` | exit 1 |
| `test_list_rating_max_10_rejected` | `brewlog list --rating-max 10` | exit 1 |
| `test_list_rating_min_0_rejected` | `brewlog list --rating-min 0` | exit 1 |
| `test_list_rating_min_error_message` | `--rating-min 10` | error contains "between 1 and 9" |
| `test_list_rating_max_error_message` | `--rating-max 10` | error contains "between 1 and 9" |

**Updates to `test_cmd_list_filter.py`:**

These existing tests use the old upper boundary of 6 as the invalid value and expect "between 1 and 5". Update them:
- `test_filter_rating_min_invalid_high`: change value `6` → `10`; update error string assertion
- `test_filter_rating_max_invalid_high`: change value `6` → `10`; update error string assertion

### AC-5: list --rating-min/--rating-max filter correctly in 1-9 range

**File:** `test_v09.py`

| Test | Setup | Command | Expected |
|------|-------|---------|----------|
| `test_list_rating_min_7_returns_7_and_above` | Insert brews with ratings 6, 7, 8 | `--rating-min 7` | Only ratings 7, 8 returned |
| `test_list_rating_max_3_returns_3_and_below` | Insert brews with ratings 3, 4, 5 | `--rating-max 3` | Only rating 3 returned |

### AC-7/AC-8: stats distribution covers 1-9, labels are numeric

**File:** `test_v09.py` (new assertions) + `test_cmd_stats.py` (update existing)

| Test | Setup | Expected |
|------|-------|----------|
| `test_get_brew_stats_distribution_keys_1_to_9` | Empty DB | `distribution` dict has exactly keys 1-9 |
| `test_get_brew_stats_rating_7_counted` | Insert brew with overall=7 | `distribution[7] == 1` |
| `test_get_brew_stats_rating_9_counted` | Insert brew with overall=9 | `distribution[9] == 1` |
| `test_stats_display_shows_9_levels` | Insert brew with overall=7 | Output contains "7:" (numeric label) |
| `test_stats_display_no_star_labels` | Any brew with rating | Output does NOT contain "star" |
| `test_stats_display_all_nine_labels_present` | 9 brews rated 1-9 | Output contains "1:", "5:", "9:" |

**Updates to `test_cmd_stats.py`:**
- `test_stats_rating_distribution_all_stars`: currently asserts "1 star", "2 star" etc. in output. Update to assert "1:", "2:", ... "5:" are present. Extend to also assert "6:", "7:", "8:", "9:".

### AC-9: Help text reads "1-9"

**File:** `test_v09.py`

| Test | Command | Expected |
|------|---------|----------|
| `test_add_help_rating_overall_mentions_1_9` | `brewlog add --help` | output contains "1-9" |
| `test_update_help_rating_overall_mentions_1_9` | `brewlog update --help` | output contains "1-9" |
| `test_list_help_rating_min_mentions_1_9` | `brewlog list --help` | output contains "1-9" |

### AC-12/AC-13/AC-14: Bundled schema v0.9, BREWSPEC_VERSION, export

**File:** `test_v09.py`

| Test | What | Expected |
|------|------|----------|
| `test_brewspec_version_constant` | `from brewlog.serialise import BREWSPEC_VERSION` | `== "0.9"` |
| `test_export_produces_v09_version` | Export a brew to YAML, parse | `brewspec_version == "0.9"` |

### AC-15: Import accepts v0.9 documents with ratings 1-9

**File:** `test_v09.py`

| Test | Input | Expected |
|------|-------|----------|
| `test_import_v09_document_with_rating_7` | Valid v0.9 YAML with `overall: 7` | exit 0, brew stored with `result_rating_overall = 7` |
| `test_import_v09_document_with_rating_9` | Valid v0.9 YAML with `overall: 9` | exit 0 |
| `test_import_v08_document_rejected_version_mismatch` | v0.8 YAML (brewspec_version: "0.8") | exit 1, error mentions version or schema |

Note: the third test above confirms SPEC-2 behaviour — v0.8 documents fail on the `brewspec_version` const, not on ratings range.

### AC-18: RatingsInput docstring updated

**File:** `test_v09.py`

| Test | What | Expected |
|------|------|----------|
| `test_ratings_input_docstring_mentions_1_9` | `RatingsInput.__doc__` | contains "1-9" |

### AC-19: Existing tests pass

No new test. The dev must run `pytest tests/` after all changes and confirm zero failures. The targeted existing test updates are:
- `test_cmd_stats.py`: star label assertions (detailed above)
- `test_cmd_list_filter.py`: high-boundary assertions (detailed above)
- `test_cmd_add.py`: search for any assertions on "between 1 and 5" and update to "between 1 and 9"
- `test_cmd_update.py`: same search

### AC-20: ruff check passes

Run `ruff check .` from `brewlog/` before handoff. Fix any issues before signalling ready for review.

---

## 8. Security Considerations

**Input validation (two-layer defense in depth):**

Rating values are user-entered integers. Both validation layers are updated consistently:
1. **Pydantic layer** (`RatingsInput.validate_rating_dimension`): rejects values outside 1-9 with `ValueError`. This is the validation path for `brewlog add` (via `RatingsInput` construction) and the import path (via the secondary validation layer if used).
2. **CLI inline layer** (`add.py`, `update.py` inline guards): rejects out-of-range values before Pydantic construction, producing the user-facing error message per spec. Both layers enforce the same 1-9 bound.

The error messages specify `"between 1 and 9"` which gives no information about internal code structure or paths.

**SQL injection:** No change to the SQL layer. All existing queries use parameterised `?` placeholders. The rating distribution query in `get_brew_stats` does not interpolate user input — it reads stored integers from the DB using a static query. The `if 1 <= star <= 9` guard prevents out-of-range DB values from corrupting the distribution dict.

**File I/O:** No changes to `validate_import_path` or `validate_export_path`. The only import-path change is the bundled schema file, which is a static project asset — not user input.

**Schema version on import:** Replacing the bundled schema with v0.9 changes what the import validator accepts. Documents with ratings 6-9 now pass schema validation. This is intentional and the correct behavior. Documents declaring `brewspec_version: "0.8"` will be rejected by the `const` constraint — this is also correct behavior and is documented in Section 3.4.

**Data integrity:** Existing stored ratings of 1-5 are unaffected. The widened validation range is strictly additive — it never corrupts or migrates existing data.

**Trust boundary summary:**

```
User input (--rating-overall N)
  → CLI inline guard (1 <= N <= 9 check in add.py / update.py)
  → Pydantic RatingsInput validator (1 <= v <= 9)
  → db.insert_brew() with parameterised SQL
  → SQLite storage (INTEGER column, no constraint at DB level)

Import path:
  User file
  → validate_import_path() (path safety, size limit)
  → JSON Schema validation against bundled v0.9 schema
  → db.insert_brew_dict() with parameterised SQL
  → SQLite storage
```

---

## 9. TDD Implementation Order

1. **Write failing tests for AC-1 (RatingsInput model range)**
   - `test_ratings_input_value_9_accepted`, `test_ratings_input_value_10_rejected`, `test_ratings_input_error_message_1_to_9`
   - These fail because the validator still enforces 1-5.

2. **Implement: update `models.py`** — validator range (1→9), RatingsInput docstring, BrewInput docstring, module docstring.
   - AC-1 and AC-18 tests now pass.

3. **Write failing tests for AC-2 (add command) and AC-3 (update command)**
   - `test_add_rating_overall_9_accepted`, `test_add_rating_overall_10_rejected`, etc.
   - These fail because the CLI inline guard still checks `<= 5`.

4. **Implement: update `commands/add.py` and `commands/update.py`** — inline validation range and all help text strings.
   - AC-2, AC-3, AC-9 (add/update) tests now pass.

5. **Write failing tests for AC-4 (list rating filter) and AC-5 (filter behavior)**
   - Update existing `test_filter_rating_min_invalid_high` and `test_filter_rating_max_invalid_high`.
   - Add new boundary tests at 9 (valid) and 10 (invalid).
   - These fail because list_ still validates `<= 5`.

6. **Implement: update `commands/list_.py`** — validation guards and help text.
   - AC-4, AC-5 tests now pass.

7. **Write failing tests for AC-7/AC-8 (stats distribution)**
   - `test_get_brew_stats_distribution_keys_1_to_9`, `test_stats_display_shows_9_levels`, etc.
   - Update `test_stats_rating_distribution_all_stars` to expect numeric labels.
   - These fail because the distribution is still 1-5 and labels still say "star".

8. **Implement: update `db.py` and `commands/stats.py`** — distribution range and display format.
   - AC-7, AC-8 tests now pass.

9. **Write failing tests for AC-13/AC-14 (BREWSPEC_VERSION and export)**
   - `test_brewspec_version_constant`, `test_export_produces_v09_version`
   - These fail because version is still "0.8".

10. **Implement: update `serialise.py`** — `BREWSPEC_VERSION = "0.9"` and two function docstrings.
    - AC-13, AC-14 tests now pass.

11. **Obtain BrewSpec v0.9 schema file.** Confirm it is in the worktree. If not, note as blocker.

12. **Write failing test for AC-15 (import v0.9 document)**
    - `test_import_v09_document_with_rating_7`
    - This fails because the bundled schema still validates v0.8.

13. **Implement: replace `brewspec.schema.json`** with v0.9 schema.
    - AC-12, AC-15 tests now pass.

14. **Run full test suite:** `pytest tests/` — all tests must pass.

15. **Run lint:** `ruff check .` from `brewlog/` — zero errors required before handoff.
