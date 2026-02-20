"""
`brewlog update` command.

Updates optional fields on an existing brew. Supply the brew ID as an optional
positional argument; omit it to update the most-recently-dated brew.
At least one flag must be provided.
"""

from __future__ import annotations

import sys

import click

from brewlog import db
from brewlog.models import (
    BREW_TYPE_ENUM,
    COFFEE_TYPE_ENUM,
    ROAST_DATE_PATTERN,
)


@click.command("update")
@click.argument("brew_id", type=int, required=False, default=None)
@click.option("--method",      "method",       type=str,   default=None,
              help="Brew method (e.g. 'V60').")
@click.option("--grind",       "grind",        type=str,   default=None,
              help="Grind description.")
@click.option("--temp",        "temp",         type=float, default=None,
              help="Water temperature in Celsius (0–100).")
@click.option("--duration",    "duration",     type=int,   default=None,
              help="Brew duration in seconds (> 0).")
@click.option("--rating",      "rating",       type=int,   default=None,
              help="Rating 1–5.")
@click.option("--notes",       "notes",        type=str,   default=None,
              help="Tasting notes.")
@click.option("--tds",         "tds",          type=float, default=None,
              help="TDS percentage (> 0).")
@click.option("--ey",          "ey",           type=float, default=None,
              help="Extraction yield (> 0).")
@click.option("--roast-date",  "roast_date",   type=str,   default=None,
              help="Coffee roast date (YYYY-MM-DD).")
@click.option("--coffee-type", "coffee_type",  type=str,   default=None,
              help="Coffee classification: single_origin or blend.")
@click.option("--origin",      "origin",       type=str,   default=None,
              multiple=True,
              help="Coffee origin (may be repeated).")
@click.option("--varietal",    "varietal",     type=str,   default=None,
              help="Coffee varietal.")
@click.option("--process",     "process",      type=str,   default=None,
              help="Coffee processing method.")
@click.option("--water-ppm",   "water_ppm",    type=float, default=None,
              help="Water mineral content in ppm (>= 0).")
@click.option("--grinder",     "grinder",      type=str,   default=None,
              help="Grinder name/model.")
@click.option("--brewer",      "brewer",       type=str,   default=None,
              help="Brewer/dripper name.")
def update(
    brew_id,
    method, grind, temp, duration, rating, notes, tds, ey,
    roast_date, coffee_type, origin, varietal, process,
    water_ppm, grinder, brewer,
) -> None:
    """Update optional fields on an existing brew (defaults to the latest brew)."""

    # -- Validate flag values --

    if rating is not None and not (1 <= rating <= 5):
        click.echo("Error: rating must be between 1 and 5", err=True)
        sys.exit(1)

    if temp is not None and not (0 <= temp <= 100):
        click.echo("Error: temp must be between 0 and 100", err=True)
        sys.exit(1)

    if duration is not None and duration <= 0:
        click.echo("Error: duration must be greater than 0", err=True)
        sys.exit(1)

    if tds is not None and tds <= 0:
        click.echo("Error: tds must be greater than 0", err=True)
        sys.exit(1)

    if ey is not None and ey <= 0:
        click.echo("Error: ey must be greater than 0", err=True)
        sys.exit(1)

    if roast_date is not None and not ROAST_DATE_PATTERN.match(roast_date):
        click.echo("Error: roast-date must be in YYYY-MM-DD format", err=True)
        sys.exit(1)

    if coffee_type is not None and coffee_type not in COFFEE_TYPE_ENUM:
        click.echo(
            f"Error: coffee-type must be one of: {sorted(COFFEE_TYPE_ENUM)}",
            err=True,
        )
        sys.exit(1)

    if water_ppm is not None and water_ppm < 0:
        click.echo("Error: water-ppm must be >= 0", err=True)
        sys.exit(1)

    if method is not None and (len(method.strip()) == 0 or len(method) > 100):
        click.echo("Error: method must be 1–100 characters", err=True)
        sys.exit(1)

    if grind is not None and (len(grind.strip()) == 0 or len(grind) > 100):
        click.echo("Error: grind must be 1–100 characters", err=True)
        sys.exit(1)

    if notes is not None and (len(notes.strip()) == 0 or len(notes) > 2000):
        click.echo("Error: notes must be 1–2000 characters", err=True)
        sys.exit(1)

    if varietal is not None and (len(varietal.strip()) == 0 or len(varietal) > 100):
        click.echo("Error: varietal must be 1–100 characters", err=True)
        sys.exit(1)

    if process is not None and (len(process.strip()) == 0 or len(process) > 100):
        click.echo("Error: process must be 1–100 characters", err=True)
        sys.exit(1)

    if grinder is not None and (len(grinder.strip()) == 0 or len(grinder) > 100):
        click.echo("Error: grinder must be 1–100 characters", err=True)
        sys.exit(1)

    if brewer is not None and (len(brewer.strip()) == 0 or len(brewer) > 100):
        click.echo("Error: brewer must be 1–100 characters", err=True)
        sys.exit(1)

    # -- Build updates dict (DB column -> value) --

    import json as _json

    updates: dict = {}
    if method is not None:
        updates["method"] = method
    if grind is not None:
        updates["grind"] = grind
    if temp is not None:
        updates["water_temp_c"] = temp
    if duration is not None:
        updates["duration_s"] = duration
    if rating is not None:
        updates["rating"] = rating
    if notes is not None:
        updates["notes"] = notes
    if tds is not None:
        updates["tds"] = tds
    if ey is not None:
        updates["ey"] = ey
    if roast_date is not None:
        updates["coffee_roast_date"] = roast_date
    if coffee_type is not None:
        updates["coffee_type"] = coffee_type
    if origin:
        updates["coffee_origin"] = _json.dumps(list(origin))
    if varietal is not None:
        updates["coffee_varietal"] = varietal
    if process is not None:
        updates["coffee_process"] = process
    if water_ppm is not None:
        updates["water_ppm"] = water_ppm
    if grinder is not None:
        updates["equipment_grinder"] = grinder
    if brewer is not None:
        updates["equipment_brewer"] = brewer

    if not updates:
        click.echo(
            "Error: no fields to update — provide at least one flag (run --help for options)",
            err=True,
        )
        sys.exit(1)

    # -- Resolve brew ID --

    conn = db.get_connection()
    try:
        if brew_id is None:
            brew_id = db.get_latest_brew_id(conn)
            if brew_id is None:
                click.echo("Error: no brews logged yet", err=True)
                sys.exit(1)

        found = db.update_brew(brew_id, updates, conn)
    finally:
        conn.close()

    if not found:
        click.echo(f"Error: brew #{brew_id} not found", err=True)
        sys.exit(1)

    click.echo(f"Brew #{brew_id} updated.")
