"""
`brewlog list` command.

Displays a formatted table of recent brews, ordered by date descending.
"""

from __future__ import annotations

import sys
from datetime import datetime

import click

from brewlog import db
from brewlog.models import BREW_TYPE_ENUM


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
_COL_RATING = 14  # "Overall Rating"


def _format_header() -> str:
    """Return the table header line."""
    return (
        f"{'ID':>{_COL_ID}}  "
        f"{'Date':<{_COL_DATE}}  "
        f"{'Type':<{_COL_TYPE}}  "
        f"{'Method':<{_COL_METHOD}}  "
        f"{'Dose (g)':>{_COL_DOSE}}  "
        f"{'Water (g)':>{_COL_WATER}}  "
        f"{'Overall Rating':>{_COL_RATING}}"
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
    rating = str(row["result_rating_overall"]) if row["result_rating_overall"] is not None else "-"

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
@click.option(
    "--type", "brew_type", type=str, default=None,
    help="Filter by brew type: immersion, pour_over, espresso, hybrid.",
)
@click.option(
    "--since", type=str, default=None,
    help="Filter brews on or after this date (YYYY-MM-DD).",
)
@click.option(
    "--until", type=str, default=None,
    help="Filter brews on or before this date (YYYY-MM-DD).",
)
@click.option(
    "--rating-min", "rating_min", type=int, default=None,
    help="Filter brews with overall rating >= N (1-5).",
)
@click.option(
    "--rating-max", "rating_max", type=int, default=None,
    help="Filter brews with overall rating <= N (1-5).",
)
def list_cmd(
    limit: int,
    show_all: bool,
    brew_type: str | None,
    since: str | None,
    until: str | None,
    rating_min: int | None,
    rating_max: int | None,
) -> None:
    """List recent brews."""

    # Validate limit
    if not show_all and limit <= 0:
        click.echo("Error: --limit must be a positive integer.", err=True)
        sys.exit(1)

    # Validate --type
    if brew_type is not None and brew_type not in BREW_TYPE_ENUM:
        click.echo(
            f"Error: invalid brew type '{brew_type}'. "
            f"Must be one of: {', '.join(sorted(BREW_TYPE_ENUM))}.",
            err=True,
        )
        sys.exit(1)

    # Validate --since
    if since is not None:
        try:
            datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            click.echo(
                f"Error: --since '{since}' is not a valid date. Use YYYY-MM-DD format.",
                err=True,
            )
            sys.exit(1)

    # Validate --until
    if until is not None:
        try:
            datetime.strptime(until, "%Y-%m-%d")
        except ValueError:
            click.echo(
                f"Error: --until '{until}' is not a valid date. Use YYYY-MM-DD format.",
                err=True,
            )
            sys.exit(1)

    # Validate --since and --until ordering
    if since is not None and until is not None:
        if since > until:
            click.echo(
                f"Error: --since '{since}' cannot be later than --until '{until}'.",
                err=True,
            )
            sys.exit(1)

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

    # Validate --rating-min <= --rating-max
    if rating_min is not None and rating_max is not None:
        if rating_min > rating_max:
            click.echo(
                f"Error: --rating-min {rating_min} cannot exceed --rating-max {rating_max}.",
                err=True,
            )
            sys.exit(1)

    has_filters = (
        brew_type is not None
        or since is not None
        or until is not None
        or rating_min is not None
        or rating_max is not None
    )

    conn = db.get_connection()
    try:
        rows = db.list_brews_filtered(
            conn,
            limit=limit,
            all_rows=show_all,
            brew_type=brew_type,
            since=since,
            until=until,
            rating_min=rating_min,
            rating_max=rating_max,
        )
    finally:
        conn.close()

    if not rows:
        if has_filters:
            click.echo("No brews match the given filters.")
        else:
            click.echo("No brews logged yet. Run 'brewlog add' to get started.")
        return

    click.echo(_format_header())
    click.echo(_format_separator())
    for row in rows:
        click.echo(_format_row(row))
