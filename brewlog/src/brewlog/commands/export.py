"""
`brewlog export` command.

Exports all brews to a BrewSpec v0.2-compliant YAML or JSON file.
Path is validated before any DB access. File is validated against the
JSON Schema before writing to disk.
"""

from __future__ import annotations

import json
import sys

import click
import yaml

from brewlog import db, schema, serialise


@click.command("export")
@click.argument("path", type=str)
@click.option(
    "--format", "fmt",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    show_default=True,
    help="Output format: yaml (default) or json.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing file without prompting.",
)
def export(path: str, fmt: str, force: bool) -> None:
    """Export all brews to a BrewSpec v0.2 file."""

    # -- Path validation (before any DB access) --
    out_path = serialise.validate_export_path(path)

    # -- Fetch rows --
    conn = db.get_connection()
    try:
        rows = db.get_all_brews(conn)
    finally:
        conn.close()

    if not rows:
        click.echo("No brews to export.")
        return

    # -- Build document dict --
    document = serialise.rows_to_brewspec_document(rows)

    # -- Schema validation (safety net) --
    errors = schema.validate_document(document)
    if errors:
        click.echo("Internal error: serialised document failed schema validation.", err=True)
        for e in errors:
            click.echo(f"  - {e}", err=True)
        sys.exit(1)

    # -- Overwrite protection --
    if out_path.exists() and not force:
        overwrite = click.confirm(
            f"File already exists at '{out_path}'. Overwrite?",
            default=False,
        )
        if not overwrite:
            click.echo("Export cancelled.")
            return

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
