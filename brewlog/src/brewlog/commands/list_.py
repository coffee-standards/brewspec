"""
`brewlog list` command.

Displays a formatted table of recent brews, ordered by date descending.
"""

from __future__ import annotations

import sys

import click

from brewlog import db


# ---------------------------------------------------------------------------
# Table formatting helpers
# ---------------------------------------------------------------------------

# Column widths (characters)
_COL_ID = 4
_COL_DATE = 20
_COL_TYPE = 10
_COL_METHOD = 15
_COL_DOSE = 9
_COL_WATER = 10
_COL_RATING = 6


def _format_header() -> str:
    """Return the table header line."""
    return (
        f"{'ID':>{_COL_ID}}  "
        f"{'Date':<{_COL_DATE}}  "
        f"{'Type':<{_COL_TYPE}}  "
        f"{'Method':<{_COL_METHOD}}  "
        f"{'Dose (g)':>{_COL_DOSE}}  "
        f"{'Water (g)':>{_COL_WATER}}  "
        f"{'Rating':>{_COL_RATING}}"
    )


def _format_separator() -> str:
    """Return the separator line under the header."""
    return (
        f"{'':->{ _COL_ID}}  "
        f"{'':->{ _COL_DATE}}  "
        f"{'':->{ _COL_TYPE}}  "
        f"{'':->{ _COL_METHOD}}  "
        f"{'':->{ _COL_DOSE}}  "
        f"{'':->{ _COL_WATER}}  "
        f"{'':->{ _COL_RATING}}"
    )


def _format_row(row) -> str:
    """Format a single brew row for the table."""
    method = row["method"] if row["method"] is not None else "-"
    rating = str(row["rating"]) if row["rating"] is not None else "-"

    return (
        f"{row['id']:>{_COL_ID}}  "
        f"{row['date']:<{_COL_DATE}}  "
        f"{row['type']:<{_COL_TYPE}}  "
        f"{method:<{_COL_METHOD}}  "
        f"{row['dose_g']:>{_COL_DOSE}.1f}  "
        f"{row['water_weight_g']:>{_COL_WATER}.1f}  "
        f"{rating:>{_COL_RATING}}"
    )


# ---------------------------------------------------------------------------
# Command definition
# ---------------------------------------------------------------------------

@click.command("list")
@click.option(
    "--limit", type=int, default=20,
    help="Number of brews to show (default: 20).",
)
@click.option(
    "--all", "show_all", is_flag=True, default=False,
    help="Show all brews.",
)
def list_cmd(limit: int, show_all: bool) -> None:
    """List recent brews."""

    # Validate limit
    if not show_all and limit <= 0:
        click.echo("Error: --limit must be a positive integer.", err=True)
        sys.exit(1)

    conn = db.get_connection()
    try:
        rows = db.list_brews(conn, limit=limit, all_rows=show_all)
    finally:
        conn.close()

    if not rows:
        click.echo("No brews logged yet. Run 'brewlog add' to get started.")
        return

    click.echo(_format_header())
    click.echo(_format_separator())
    for row in rows:
        click.echo(_format_row(row))
