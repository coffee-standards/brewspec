"""
`brewlog import` command.

Imports brews from a BrewSpec v0.6 YAML or JSON file.
Validates the file against the JSON Schema before any DB writes.
Uses yaml.safe_load() for all YAML parsing — yaml.load() is prohibited.
All inserts are performed in a single transaction (all-or-nothing).
"""

from __future__ import annotations

import json
import sys

import click
import yaml

from brewlog import db, schema, serialise

# Verbatim error message for non-v0.6 BrewSpec files. AC-25/MED-2.
# The {version} placeholder is replaced with the version string found in the file.
_V06_REQUIRED_MSG = """\
Error: This file uses BrewSpec v{version}, which is not supported by BrewLog v0.5.
BrewLog v0.5 requires BrewSpec v0.5.

To migrate your file from v0.4 to v0.5, make the following changes:
  1. Change 'brewspec_version' from "0.4" to "0.5"
  2. Replace 'coffee.origin' (string array) with 'coffee.origins' (object array):
     Before: coffee:
               origin: ["Ethiopia", "Colombia"]
     After:  coffee:
               origins:
                 - country: "Ethiopia"
                 - country: "Colombia"

Full migration guide: https://github.com/coffee-standards/brewspec"""


@click.command("import")
@click.argument("path", type=str)
def import_cmd(path: str) -> None:
    """Import brews from a BrewSpec v0.6 YAML or JSON file."""

    # -- Path validation (before opening the file) --
    in_path = serialise.validate_import_path(path)

    # -- Detect format from extension --
    suffix = in_path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        fmt = "yaml"
    elif suffix == ".json":
        fmt = "json"
    else:
        click.echo(
            f"Error: unrecognised file extension '{suffix}'. "
            "Supported formats: .yaml, .yml, .json",
            err=True,
        )
        sys.exit(1)

    # -- Parse file --
    raw_text = in_path.read_text(encoding="utf-8")
    if fmt == "yaml":
        try:
            doc = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            click.echo(f"Error parsing YAML: {exc}", err=True)
            sys.exit(1)
    else:
        try:
            doc = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            click.echo(f"Error parsing JSON: {exc}", err=True)
            sys.exit(1)

    if not isinstance(doc, dict):
        click.echo("Error: file content is not a valid BrewSpec document.", err=True)
        sys.exit(1)

    # -- Check for non-v0.6 BrewSpec version before schema validation --
    file_version = str(doc.get("brewspec_version", ""))
    if file_version != "0.6":
        version_label = file_version if file_version else "(unknown)"
        click.echo(_V06_REQUIRED_MSG.format(version=version_label), err=True)
        sys.exit(1)

    # -- Schema validation (before any DB writes) --
    errors = schema.validate_document(doc)
    if errors:
        click.echo("Validation failed:", err=True)
        for e in errors:
            click.echo(f"  - {e}", err=True)
        sys.exit(1)

    # -- Insert all brews in a single transaction --
    brews = doc.get("brews", [])
    conn = db.get_connection()
    try:
        conn.execute("BEGIN")
        try:
            for brew_dict in brews:
                db.insert_brew_dict(brew_dict, conn)
            conn.commit()
        except Exception:
            conn.rollback()
            click.echo("Error: failed to insert brews. No changes written.", err=True)
            sys.exit(1)
    finally:
        conn.close()

    click.echo(f"Imported {len(brews)} brews.")
