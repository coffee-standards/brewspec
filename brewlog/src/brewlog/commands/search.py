"""
`brewlog search` command.

Searches brews by case-insensitive substring match across:
  notes, result_tasting_notes, coffee_name, coffee_origins, coffee_origin.

Uses parameterised SQL LIKE queries — the query value is never interpolated
into the SQL string.
"""

from __future__ import annotations

import sys

import click

from brewlog import db
from brewlog.commands.list_ import _render_table


@click.command("search")
@click.argument("query", type=str)
@click.option(
    "--limit", "limit", type=int, default=None,
    help="Maximum number of results to return. Default: no limit.",
)
@click.pass_context
def search(ctx: click.Context, query: str, limit: int | None) -> None:
    """Search brews by text across notes, tasting notes, coffee name, and origin data."""

    # Validate query (AC-11): must be non-empty and non-whitespace-only
    if not query or not query.strip():
        click.echo("Error: search query must not be empty.", err=True)
        sys.exit(1)

    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn = db.get_connection(db_path=db_path)
    try:
        rows = db.search_brews(conn, query, limit=limit)
    finally:
        conn.close()

    if not rows:
        click.echo(f'No brews found matching "{query}".')
        return

    _render_table(rows)
