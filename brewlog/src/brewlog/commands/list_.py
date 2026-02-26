"""
`brewlog list` command.

Displays a formatted table of recent brews, ordered by date descending.

v0.4 changes:
- Column visibility: optional columns (Method, Overall Rating) are only
  rendered when at least one row in the result set has a non-null value
  for that column.
- Legacy fallback: Overall Rating falls back to the `overall` key inside
  the `result_ratings` JSON column for v0.2 rows where
  `result_rating_overall` is NULL.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime

import click

from brewlog import db
from brewlog.models import BREW_TYPE_ENUM


# ---------------------------------------------------------------------------
# Legacy rating helper — Item 1 (MED-1)
# ---------------------------------------------------------------------------


def _get_overall_rating(row) -> int | None:
    """
    Return the overall rating for a row, falling back to the legacy
    result_ratings JSON column for v0.2 rows.

    Priority:
      1. result_rating_overall (v0.3+ column)
      2. result_ratings JSON 'overall' key (v0.2 legacy)
      3. None
    """
    if row["result_rating_overall"] is not None:
        return row["result_rating_overall"]
    if row["result_ratings"] is not None:
        try:
            legacy = json.loads(row["result_ratings"])
            return legacy.get("overall")
        except (json.JSONDecodeError, AttributeError):
            pass
    return None


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

# Always-visible columns: (header_label, right_align, width)
# right_align True means right-pad with spaces on left; False means left-pad.
_ALWAYS_COLS = [
    ("ID",     True,  4),
    ("Date",   False, 20),
    ("Type",   False, 10),
]

# Optional columns — only rendered when any row has a value.
# Each entry: (key_fn, header_label, right_align, width)
# key_fn receives a row and returns a display string or None.
_OPTIONAL_COLS = [
    ("method",   "Method",         False, 15),
]

# Fixed always-visible trailing numeric columns
_NUMERIC_COLS = [
    ("dose_g",         "Dose (g)",   True, 9),
    ("water_weight_g", "Water (g)",  True, 10),
]

# Rating column — optional, uses legacy fallback
_RATING_LABEL = "Overall Rating"
_RATING_WIDTH = 14


# ---------------------------------------------------------------------------
# Column visibility detection — Item 4
# ---------------------------------------------------------------------------


def _has_any_method(rows) -> bool:
    """Return True if any row has a non-null method."""
    return any(row["method"] is not None for row in rows)


def _has_any_rating(rows) -> bool:
    """
    Return True if any row has an overall rating (modern or legacy).
    Implements Item 1 and Item 4 together.
    """
    return any(_get_overall_rating(row) is not None for row in rows)


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------


def _render_table(rows) -> None:
    """Render the brew table, showing only columns that have data."""
    show_method = _has_any_method(rows)
    show_rating = _has_any_rating(rows)

    # Build header
    header_parts = [
        f"{'ID':>{4}}",
        f"{'Date':<{20}}",
        f"{'Type':<{10}}",
    ]
    sep_parts = [
        f"{'':->{ 4}}",
        f"{'':->{ 20}}",
        f"{'':->{ 10}}",
    ]

    if show_method:
        header_parts.append(f"{'Method':<{15}}")
        sep_parts.append(f"{'':->{ 15}}")

    header_parts.append(f"{'Dose (g)':>{9}}")
    sep_parts.append(f"{'':->{ 9}}")

    header_parts.append(f"{'Water (g)':>{10}}")
    sep_parts.append(f"{'':->{ 10}}")

    if show_rating:
        header_parts.append(f"{'Overall Rating':>{_RATING_WIDTH}}")
        sep_parts.append(f"{'':->{ _RATING_WIDTH}}")

    click.echo("  ".join(header_parts))
    click.echo("  ".join(sep_parts))

    for row in rows:
        parts = [
            f"{row['id']:>{4}}",
            f"{row['date']:<{20}}",
            f"{row['type']:<{10}}",
        ]

        if show_method:
            method = row["method"] if row["method"] is not None else "-"
            parts.append(f"{method:<{15}}")

        parts.append(f"{row['dose_g']:>{9}.1f}")
        parts.append(f"{row['water_weight_g']:>{10}.1f}")

        if show_rating:
            rating_val = _get_overall_rating(row)
            rating = str(rating_val) if rating_val is not None else "-"
            parts.append(f"{rating:>{_RATING_WIDTH}}")

        click.echo("  ".join(parts))


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

    _render_table(rows)
