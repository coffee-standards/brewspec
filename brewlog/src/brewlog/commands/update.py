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
    COFFEE_TYPE_ENUM,
    GRIND_ENUM,
    ROAST_DATE_PATTERN,
)


@click.command("update")
@click.argument("brew_id", type=int, required=False, default=None)
@click.option("--method",      "method",       type=str,   default=None,
              help="Brew method (e.g. 'V60').")
@click.option("--grind",       "grind",        type=str,   default=None,
              help=(
                  "Grind size: turkish | espresso | fine | medium_fine | "
                  "medium | medium_coarse | coarse."
              ))
@click.option("--temp",        "temp",         type=float, default=None,
              help="Water temperature in Celsius (0-100).")
@click.option("--duration",    "duration",     type=int,   default=None,
              help="Brew duration in seconds (> 0).")
@click.option("--notes",       "notes",        type=str,   default=None,
              help="Brew process notes.")
@click.option("--tds",         "tds",          type=float, default=None,
              help="TDS percentage (> 0).")
@click.option("--ey",          "ey",           type=float, default=None,
              help="Extraction yield (> 0).")
@click.option("--brix",        "brix",         type=float, default=None,
              help="Degrees Brix (>= 0).")
@click.option("--tasting-notes", "tasting_notes", type=str, default=None,
              help=(
                  "Sensory tasting notes — impressions of the cup. "
                  "For operational brew-process notes use --notes."
              ))
@click.option("--rating",         "rating_retired", type=int, default=None, hidden=True)
@click.option("--rating-overall", "rating_overall",    type=int, default=None,
              help="Overall impression, 1-5.")
@click.option("--rating-fragrance", "rating_fragrance", type=int, default=None,
              help="Fragrance rating, 1-5.")
@click.option("--rating-aroma",    "rating_aroma",     type=int, default=None,
              help="Aroma rating, 1-5.")
@click.option("--rating-flavour",  "rating_flavour",   type=int, default=None,
              help="Flavour rating, 1-5.")
@click.option("--rating-aftertaste", "rating_aftertaste", type=int, default=None,
              help="Aftertaste rating, 1-5.")
@click.option("--rating-acidity",  "rating_acidity",   type=int, default=None,
              help="Acidity rating, 1-5.")
@click.option("--rating-sweetness", "rating_sweetness", type=int, default=None,
              help="Sweetness rating, 1-5.")
@click.option("--rating-mouthfeel", "rating_mouthfeel", type=int, default=None,
              help="Mouthfeel rating, 1-5.")
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
    method, grind, temp, duration, notes, tds, ey, brix, tasting_notes,
    rating_retired,
    rating_overall, rating_fragrance, rating_aroma, rating_flavour,
    rating_aftertaste, rating_acidity, rating_sweetness, rating_mouthfeel,
    roast_date, coffee_type, origin, varietal, process,
    water_ppm, grinder, brewer,
) -> None:
    """Update optional fields on an existing brew (defaults to the latest brew)."""

    # -- Check for retired --rating flag first (AC-32) --
    if rating_retired is not None:
        click.echo(
            "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
            "Use --rating-overall N to set your overall impression (1-5).\n"
            "See --help for all available rating dimension flags.",
            err=True,
        )
        sys.exit(1)

    # -- Validate flag values --

    _RATING_DIMS = {
        "rating-overall":    rating_overall,
        "rating-fragrance":  rating_fragrance,
        "rating-aroma":      rating_aroma,
        "rating-flavour":    rating_flavour,
        "rating-aftertaste": rating_aftertaste,
        "rating-acidity":    rating_acidity,
        "rating-sweetness":  rating_sweetness,
        "rating-mouthfeel":  rating_mouthfeel,
    }
    for flag_name, flag_val in _RATING_DIMS.items():
        if flag_val is not None and not (1 <= flag_val <= 5):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 5.",
                err=True,
            )
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

    if brix is not None and brix < 0:
        click.echo("Error: brix must be >= 0", err=True)
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
        click.echo("Error: method must be 1-100 characters", err=True)
        sys.exit(1)

    if grind is not None and grind not in GRIND_ENUM:
        click.echo(
            f"Error: grind must be one of: {sorted(GRIND_ENUM)}",
            err=True,
        )
        sys.exit(1)

    if notes is not None and (len(notes.strip()) == 0 or len(notes) > 2000):
        click.echo("Error: notes must be 1-2000 characters", err=True)
        sys.exit(1)

    if tasting_notes is not None and (len(tasting_notes.strip()) == 0 or len(tasting_notes) > 2000):
        click.echo("Error: tasting-notes must be 1-2000 characters", err=True)
        sys.exit(1)

    if varietal is not None and (len(varietal.strip()) == 0 or len(varietal) > 100):
        click.echo("Error: varietal must be 1-100 characters", err=True)
        sys.exit(1)

    if process is not None and (len(process.strip()) == 0 or len(process) > 100):
        click.echo("Error: process must be 1-100 characters", err=True)
        sys.exit(1)

    if grinder is not None and (len(grinder.strip()) == 0 or len(grinder) > 100):
        click.echo("Error: grinder must be 1-100 characters", err=True)
        sys.exit(1)

    if brewer is not None and (len(brewer.strip()) == 0 or len(brewer) > 100):
        click.echo("Error: brewer must be 1-100 characters", err=True)
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
    if notes is not None:
        updates["notes"] = notes
    if tds is not None:
        updates["result_tds"] = tds
    if ey is not None:
        updates["result_ey"] = ey
    if brix is not None:
        updates["result_brix"] = brix
    if tasting_notes is not None:
        updates["result_tasting_notes"] = tasting_notes
    # AC-31: individual rating columns (no JSON sentinel pattern)
    if rating_overall is not None:
        updates["result_rating_overall"] = rating_overall
    if rating_fragrance is not None:
        updates["result_rating_fragrance"] = rating_fragrance
    if rating_aroma is not None:
        updates["result_rating_aroma"] = rating_aroma
    if rating_flavour is not None:
        updates["result_rating_flavour"] = rating_flavour
    if rating_aftertaste is not None:
        updates["result_rating_aftertaste"] = rating_aftertaste
    if rating_acidity is not None:
        updates["result_rating_acidity"] = rating_acidity
    if rating_sweetness is not None:
        updates["result_rating_sweetness"] = rating_sweetness
    if rating_mouthfeel is not None:
        updates["result_rating_mouthfeel"] = rating_mouthfeel
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
