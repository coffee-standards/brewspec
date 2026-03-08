"""
`brewlog export` command.

Exports all brews (or a single brew via --id N) to a BrewSpec v0.6-compliant
YAML or JSON file, or a flat CSV file (--format csv).

Path is validated before any DB access. YAML/JSON files are validated
against the JSON Schema before writing to disk.
"""

from __future__ import annotations

import csv
import io
import json
import sys

import click
import yaml

from brewlog import db, schema, serialise


def _rows_to_csv(rows) -> str:
    """
    Serialise a list of sqlite3.Row objects to a CSV string.

    One row per brew. All DB columns are included as headers; null values
    are written as empty strings (never 'None' or 'null').
    """
    if not rows:
        return ""

    # Build flat dicts from rows — all columns, nulls as empty strings.
    dicts = []
    for row in rows:
        d = {}
        for key in row.keys():
            val = row[key]
            d[key] = "" if val is None else val
        dicts.append(d)

    fieldnames = list(dicts[0].keys())

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(dicts)
    return buf.getvalue()


@click.command("export")
@click.argument("path", type=str)
@click.option(
    "--format", "fmt",
    type=click.Choice(["yaml", "json", "csv"]),
    default="yaml",
    show_default=True,
    help="Output format: yaml (default), json, or csv.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing file without prompting.",
)
@click.option(
    "--id", "brew_id",
    type=int,
    default=None,
    help="Export a single brew by ID.",
)
@click.pass_context
def export(ctx: click.Context, path: str, fmt: str, force: bool, brew_id: int | None) -> None:
    """Export all brews to a BrewSpec v0.6 file."""

    # -- Path validation (before any DB access) --
    out_path = serialise.validate_export_path(path, fmt=fmt)

    # -- Fetch rows --
    db_path = ctx.obj.get("db_path") if ctx.obj else None
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

    if not rows:
        click.echo("No brews to export.")
        return

    # -- Overwrite protection --
    if out_path.exists() and not force:
        overwrite = click.confirm(
            f"File already exists at '{out_path}'. Overwrite?",
            default=False,
        )
        if not overwrite:
            click.echo("Export cancelled.")
            return

    # -- CSV path --
    if fmt == "csv":
        content = _rows_to_csv(rows)
        out_path.write_text(content, encoding="utf-8")
        click.echo(f"Exported {len(rows)} brews to '{out_path}'.")
        return

    # -- Build document dict; handle invalid grind values (AC-11) --
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
            "not valid in BrewSpec v0.6 and were omitted from the export:",
            err=True,
        )
        for bid, grind_val in warned_grind:
            click.echo(f"  Brew #{bid}: grind = '{grind_val}'", err=True)

    document = {"brewspec_version": "0.6", "brews": brews_dicts}

    # -- Schema validation (safety net) --
    errors = schema.validate_document(document)
    if errors:
        click.echo("Internal error: serialised document failed schema validation.", err=True)
        for e in errors:
            click.echo(f"  - {e}", err=True)
        sys.exit(1)

    # -- Serialise and write --
    if fmt == "yaml":
        content = yaml.dump(
            document,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    else:
        content = json.dumps(document, indent=2, ensure_ascii=False)

    out_path.write_text(content, encoding="utf-8")
    click.echo(f"Exported {len(rows)} brews to '{out_path}'.")
