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
# Row to BrewSpec dict (for export)
# ---------------------------------------------------------------------------

def row_to_brew_dict(row: sqlite3.Row) -> dict:
    """
    Convert a sqlite3.Row to a BrewSpec v0.3 brew dict.

    Rules:
    - NULL columns are omitted entirely (no null values in output).
    - coffee_origin is deserialised from JSON string to list.
    - coffee sub-object is only included if at least one coffee field is present.
    - water sub-object is only included if water_ppm is present.
    - equipment sub-object is only included if grinder or brewer is present.
    """
    r = dict(row)  # sqlite3.Row to plain dict

    brew: dict = {}

    # Required fields (always present; NOT NULL in schema)
    brew["date"] = r["date"]
    brew["type"] = r["type"]
    brew["dose_g"] = r["dose_g"]
    brew["water_weight_g"] = r["water_weight_g"]

    # Optional brew-level fields — include only if not NULL
    for field in (
        "method", "water_volume_ml", "water_temp_c", "grind",
        "duration_s", "tds", "ey", "rating", "notes"
    ):
        if r.get(field) is not None:
            brew[field] = r[field]

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
    if coffee:  # only include if at least one field is present
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
    if equipment:  # only include if at least one field is present
        brew["equipment"] = equipment

    return brew


def rows_to_brewspec_document(rows: list[sqlite3.Row]) -> dict:
    """
    Convert a list of DB rows to a full BrewSpec v0.3 document dict.
    Returns {"brewspec_version": "0.3", "brews": [...]}
    """
    return {
        "brewspec_version": "0.3",
        "brews": [row_to_brew_dict(row) for row in rows],
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
