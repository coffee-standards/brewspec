"""
Serialisation / deserialisation logic for BrewLog.

Converts between SQLite rows and BrewSpec document dicts.
Also handles path validation for export and import commands.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import click


# ---------------------------------------------------------------------------
# Constants — AC-11, AC-15
# ---------------------------------------------------------------------------

# v0.4 grind enum values. Any stored grind not in this set is a legacy
# freeform value that must be omitted from exports (and triggers a warning).
GRIND_ENUM: frozenset[str] = frozenset({
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse",
})

# Ordered list of (db_column, export_key) pairs for the 8 SCA rating dimensions.
_RATING_DIMS = [
    ("result_rating_overall",    "overall"),
    ("result_rating_fragrance",  "fragrance"),
    ("result_rating_aroma",      "aroma"),
    ("result_rating_flavour",    "flavour"),
    ("result_rating_aftertaste", "aftertaste"),
    ("result_rating_acidity",    "acidity"),
    ("result_rating_sweetness",  "sweetness"),
    ("result_rating_mouthfeel",  "mouthfeel"),
]


# ---------------------------------------------------------------------------
# Row to BrewSpec dict (for export)
# ---------------------------------------------------------------------------

def row_to_brew_dict(row: sqlite3.Row) -> dict:
    """
    Convert a sqlite3.Row to a BrewSpec v0.4 brew dict.

    Rules:
    - NULL columns are omitted entirely (no null values in output).
    - coffee_origin is deserialised from JSON string to list.
    - coffee sub-object is only included if at least one coffee field is present.
    - water sub-object is only included if water_ppm is present.
    - equipment sub-object is only included if grinder or brewer is present.
    - result sub-object is only included if at least one result field is present.
    - Ratings are read from individual result_rating_* columns (not JSON).
    - grind is validated against GRIND_ENUM; invalid values set _invalid_grind
      sentinel and are omitted from the main output so the caller can warn.
    """
    r = dict(row)  # sqlite3.Row to plain dict

    brew: dict = {}

    # Required fields (always present; NOT NULL in schema)
    brew["date"] = r["date"]
    brew["type"] = r["type"]
    brew["dose_g"] = r["dose_g"]
    brew["water_weight_g"] = r["water_weight_g"]

    # Optional brew-level fields (not grind — handled separately below)
    for field in ("method", "water_volume_ml", "water_temp_c", "duration_s", "notes"):
        if r.get(field) is not None:
            brew[field] = r[field]

    # grind: validate against v0.4 enum; omit and set sentinel if invalid (AC-11)
    if r.get("grind") is not None:
        if r["grind"] in GRIND_ENUM:
            brew["grind"] = r["grind"]
        else:
            brew["_invalid_grind"] = r["grind"]

    # Coffee sub-object
    coffee: dict = {}
    if r.get("coffee_roast_date") is not None:
        coffee["roast_date"] = r["coffee_roast_date"]
    if r.get("coffee_type") is not None:
        coffee["type"] = r["coffee_type"]
    if r.get("coffee_origin") is not None:
        coffee["origin"] = json.loads(r["coffee_origin"])
    if r.get("coffee_varietal") is not None:
        coffee["varietal"] = r["coffee_varietal"]
    if r.get("coffee_process") is not None:
        coffee["process"] = r["coffee_process"]
    if coffee:
        brew["coffee"] = coffee

    # Water sub-object
    if r.get("water_ppm") is not None:
        brew["water"] = {"ppm": r["water_ppm"]}

    # Equipment sub-object
    equipment: dict = {}
    if r.get("equipment_grinder") is not None:
        equipment["grinder"] = r["equipment_grinder"]
    if r.get("equipment_brewer") is not None:
        equipment["brewer"] = r["equipment_brewer"]
    if equipment:
        brew["equipment"] = equipment

    # Result sub-object — read from individual columns (AC-12)
    result: dict = {}
    if r.get("result_tds") is not None:
        result["tds"] = r["result_tds"]
    if r.get("result_ey") is not None:
        result["ey"] = r["result_ey"]
    if r.get("result_brix") is not None:
        result["brix"] = r["result_brix"]
    if r.get("result_tasting_notes") is not None:
        result["tasting_notes"] = r["result_tasting_notes"]

    # Ratings: read from individual result_rating_* columns (not JSON)
    ratings: dict = {}
    for col, key in _RATING_DIMS:
        if r.get(col) is not None:
            ratings[key] = r[col]
    if ratings:
        result["ratings"] = ratings

    if result:
        brew["result"] = result

    return brew


def rows_to_brewspec_document(rows: list[sqlite3.Row]) -> dict:
    """
    Convert a list of DB rows to a full BrewSpec v0.4 document dict.
    Returns {"brewspec_version": "0.4", "brews": [...]}.

    Note: any _invalid_grind sentinels are stripped here. Use the export
    command's inline construction if you need to emit per-brew warnings.
    """
    brews = []
    for row in rows:
        brew_dict = row_to_brew_dict(row)
        brew_dict.pop("_invalid_grind", None)
        brews.append(brew_dict)
    return {
        "brewspec_version": "0.4",
        "brews": brews,
    }


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def validate_export_path(path_str: str) -> Path:
    """
    Validate an export path string.

    Rejects paths containing '..' components (directory traversal).
    Rejects paths whose parent directory does not exist.
    Returns a Path on success.
    Calls sys.exit(1) with error message on failure.
    """
    p = Path(path_str)
    # Reject '..' at any position in the path
    if ".." in p.parts:
        click.echo("Error: path must not contain '..' components.", err=True)
        sys.exit(1)
    # Reject paths without a recognised extension
    if p.suffix.lower() not in (".yaml", ".yml", ".json"):
        click.echo(
            "Error: output path must end with .yaml, .yml, or .json.",
            err=True,
        )
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
    Rejects paths that do not exist.
    Returns a Path on success.
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
