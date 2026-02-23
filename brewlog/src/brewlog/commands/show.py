"""
`brewlog show` command.

Displays all stored fields for a specific brew by integer ID.
Fields with no value are omitted. Sections with no fields are also omitted.
"""

from __future__ import annotations

import json
import sys

import click

from brewlog import db


def _print_field(label: str, value, unit: str = "") -> None:
    """Print a single field with label alignment."""
    display = f"{value}{' ' + unit if unit else ''}"
    click.echo(f"  {label:<20}{display}")


# All result columns used for has_results detection (AC-35)
_RESULT_COLS = (
    "result_tds", "result_ey", "result_brix", "result_tasting_notes",
    "result_rating_overall", "result_rating_fragrance", "result_rating_aroma",
    "result_rating_flavour", "result_rating_aftertaste", "result_rating_acidity",
    "result_rating_sweetness", "result_rating_mouthfeel",
)

# Rating dimensions for display (AC-36)
_RATING_SHOW = [
    ("result_rating_overall",    "Overall"),
    ("result_rating_fragrance",  "Fragrance"),
    ("result_rating_aroma",      "Aroma"),
    ("result_rating_flavour",    "Flavour"),
    ("result_rating_aftertaste", "Aftertaste"),
    ("result_rating_acidity",    "Acidity"),
    ("result_rating_sweetness",  "Sweetness"),
    ("result_rating_mouthfeel",  "Mouthfeel"),
]


@click.command("show")
@click.argument("id", type=int)
def show(id: int) -> None:
    """Show all fields for a brew by ID."""

    conn = db.get_connection()
    try:
        row = db.get_brew(id, conn)
    finally:
        conn.close()

    if row is None:
        click.echo(f"No brew found with ID {id}.", err=True)
        sys.exit(1)

    click.echo(f"Brew #{id}")
    click.echo("-" * (len(f"Brew #{id}") + 1))

    # -- Brew parameters section (no header, fields directly after Brew #N) --

    # Required fields always present
    _print_field("Date:", row["date"])
    _print_field("Type:", row["type"])

    if row["method"] is not None:
        _print_field("Method:", row["method"])

    _print_field("Dose:", row["dose_g"], "g")
    _print_field("Water weight:", row["water_weight_g"], "g")

    if row["water_temp_c"] is not None:
        _print_field("Water temp:", row["water_temp_c"], "C")

    if row["grind"] is not None:
        _print_field("Grind:", row["grind"])

    if row["duration_s"] is not None:
        _print_field("Duration:", row["duration_s"], "s")

    if row["water_volume_ml"] is not None:
        _print_field("Water volume:", row["water_volume_ml"], "ml")

    if row["notes"] is not None:
        _print_field("Notes:", row["notes"])

    # -- Results section (AC-35) --
    # Include legacy result_ratings JSON in has_results check for backward compat
    has_results = (
        any(row[f] is not None for f in _RESULT_COLS)
        or row["result_ratings"] is not None
    )
    if has_results:
        click.echo("")
        click.echo("Results")
        click.echo("-------")
        if row["result_tds"] is not None:
            _print_field("TDS (%):", row["result_tds"])
        if row["result_ey"] is not None:
            _print_field("EY (%):", row["result_ey"])
        if row["result_brix"] is not None:
            _print_field("Brix:", row["result_brix"])
        if row["result_tasting_notes"] is not None:
            _print_field("Tasting Notes:", row["result_tasting_notes"])

        # AC-36, AC-37: Ratings sub-section
        has_any_rating = any(row[col] is not None for col, _ in _RATING_SHOW)
        if has_any_rating:
            click.echo(f"  {'Ratings:'}")
            for col, label in _RATING_SHOW:
                if row[col] is not None:
                    click.echo(f"    {label:<14}{row[col]}")
        elif row["result_ratings"] is not None:
            # Backward-compat: v0.2 rows with JSON-encoded ratings
            legacy_ratings = json.loads(row["result_ratings"])
            if legacy_ratings:
                click.echo(f"  {'Ratings:'}")
                for dim, val in legacy_ratings.items():
                    label = dim.capitalize()
                    click.echo(f"    {label:<14}{val}")

    # -- Coffee section --
    has_coffee = any(
        row[f] is not None
        for f in ("coffee_roast_date", "coffee_type", "coffee_origin",
                  "coffee_varietal", "coffee_process")
    )
    if has_coffee:
        click.echo("")
        click.echo("Coffee")
        click.echo("------")
        if row["coffee_roast_date"] is not None:
            _print_field("Roast date:", row["coffee_roast_date"])
        if row["coffee_type"] is not None:
            _print_field("Type:", row["coffee_type"])
        if row["coffee_origin"] is not None:
            origins = json.loads(row["coffee_origin"])
            _print_field("Origin:", ", ".join(origins))
        if row["coffee_varietal"] is not None:
            _print_field("Varietal:", row["coffee_varietal"])
        if row["coffee_process"] is not None:
            _print_field("Process:", row["coffee_process"])

    # -- Water section --
    if row["water_ppm"] is not None:
        click.echo("")
        click.echo("Water")
        click.echo("-----")
        _print_field("PPM:", row["water_ppm"])

    # -- Equipment section --
    has_equipment = any(
        row[f] is not None
        for f in ("equipment_grinder", "equipment_brewer")
    )
    if has_equipment:
        click.echo("")
        click.echo("Equipment")
        click.echo("---------")
        if row["equipment_grinder"] is not None:
            _print_field("Grinder:", row["equipment_grinder"])
        if row["equipment_brewer"] is not None:
            _print_field("Brewer:", row["equipment_brewer"])
