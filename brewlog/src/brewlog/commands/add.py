"""
`brewlog add` command.

Logs a new brew. Required fields can be supplied as flags (non-interactive)
or entered interactively via prompts. Validation is performed via Pydantic
models before any DB write.
"""

from __future__ import annotations

import sys
from datetime import date as _date_cls
from datetime import datetime, timezone

import click
from pydantic import ValidationError

from brewlog import db
from brewlog.models import (
    BrewInput,
    CoffeeInput,
    WaterInput,
    EquipmentInput,
    ResultInput,
    RatingsInput,
    DATE_PATTERN,
    BREW_TYPE_ENUM,
)


# ---------------------------------------------------------------------------
# Interactive prompt helpers
# ---------------------------------------------------------------------------

def _prompt_date() -> str:
    """Prompt for a date with today's local date as default. Re-prompts on invalid input."""
    default = _date_cls.today().strftime("%Y-%m-%d")
    while True:
        value = click.prompt("Date", default=default)
        if DATE_PATTERN.match(value):
            if "T" in value:
                try:
                    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    return value
                except ValueError:
                    pass
            else:
                return value
        click.echo(
            "  Error: date must be YYYY-MM-DD (e.g. 2026-02-22) "
            "or YYYY-MM-DDTHH:MM:SSZ (e.g. 2026-02-22T09:15:00Z)"
        )


def _prompt_brew_type() -> str:
    """Prompt for brew type using a numbered menu. Re-prompts on invalid selection."""
    options = sorted(BREW_TYPE_ENUM)
    n = len(options)
    while True:
        click.echo("Brew type:")
        for i, opt in enumerate(options, start=1):
            click.echo(f"  {i}) {opt}")
        raw = click.prompt(f"Choice [1-{n}]")
        try:
            choice = int(raw)
        except ValueError:
            click.echo(f"  Invalid choice. Please enter a number between 1 and {n}.")
            continue
        if 1 <= choice <= n:
            return options[choice - 1]
        click.echo(f"  Invalid choice. Please enter a number between 1 and {n}.")


def _prompt_positive_float(label: str) -> float:
    """Prompt for a positive float value. Re-prompts on non-numeric or non-positive input."""
    while True:
        raw = click.prompt(label)
        try:
            value = float(raw)
        except ValueError:
            click.echo(f"  Error: {label} must be a number")
            continue
        if value <= 0:
            click.echo(f"  Error: {label} must be greater than 0")
            continue
        return value


# ---------------------------------------------------------------------------
# Command definition
# ---------------------------------------------------------------------------

@click.command("add")
@click.option("--date",        "date",         type=str,   default=None,
              help="Brew date: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD.")
@click.option("--type",        "brew_type",    type=str,   default=None,
              help="Brew type: immersion, pour_over, espresso, hybrid.")
@click.option("--dose",        "dose",         type=float, default=None,
              help="Coffee dose in grams (> 0).")
@click.option("--water",       "water_weight", type=float, default=None,
              help="Water weight in grams (> 0).")
@click.option("--method",      "method",       type=str,   default=None,
              help="Freeform brewer description (e.g. 'Hario V60').")
@click.option("--temp",        "temp",         type=float, default=None,
              help="Water temperature in Celsius (0-100).")
@click.option("--grind",       "grind",        type=str,   default=None,
              help=(
                  "Grind size: turkish | espresso | fine | medium_fine | "
                  "medium | medium_coarse | coarse."
              ))
@click.option("--duration",    "duration",     type=int,   default=None,
              help="Brew duration in seconds (> 0).")
@click.option("--notes",       "notes",        type=str,   default=None,
              help="Brew process notes.")
@click.option("--roast-date",  "roast_date",   type=str,   default=None,
              help="Coffee roast date (YYYY-MM-DD).")
@click.option("--coffee-type", "coffee_type",  type=str,   default=None,
              help="Coffee classification: single_origin or blend.")
@click.option("--origin",      "origin",       type=str,   default=None,
              multiple=True,
              help="Coffee origin (may be repeated: --origin Ethiopia --origin Colombia).")
@click.option("--varietal",    "varietal",     type=str,   default=None,
              help="Coffee varietal (freeform).")
@click.option("--process",     "process",      type=str,   default=None,
              help="Coffee processing method (freeform).")
@click.option("--water-ppm",   "water_ppm",    type=float, default=None,
              help="Water mineral content in ppm (>= 0).")
@click.option("--tds",         "tds",          type=float, default=None,
              help="Brew TDS percentage (> 0).")
@click.option("--ey",          "ey",           type=float, default=None,
              help="Extraction yield percentage (> 0).")
@click.option("--brix",        "brix",         type=float, default=None,
              help="Degrees Brix (>= 0).")
@click.option("--tasting-notes", "tasting_notes", type=str, default=None,
              help=(
                  "Sensory tasting notes — impressions of the cup. "
                  "For operational brew-process notes use --notes."
              ))
@click.option("--rating",         "rating_retired",    type=int, default=None, hidden=True)
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
@click.option("--grinder",     "grinder",      type=str,   default=None,
              help="Grinder name or description.")
@click.option("--brewer",      "brewer",       type=str,   default=None,
              help="Brewer/dripper name or description.")
def add(
    date, brew_type, dose, water_weight,
    method, temp, grind, duration, notes,
    roast_date, coffee_type, origin, varietal, process,
    water_ppm, tds, ey, brix, tasting_notes,
    rating_retired,
    rating_overall, rating_fragrance, rating_aroma, rating_flavour,
    rating_aftertaste, rating_acidity, rating_sweetness, rating_mouthfeel,
    grinder, brewer,
) -> None:
    """Log a new brew."""

    # -- Check for retired --rating flag first --
    if rating_retired is not None:
        click.echo(
            "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
            "Use --rating-overall N to set your overall impression (1-5).\n"
            "See --help for all available rating dimension flags.",
            err=True,
        )
        sys.exit(1)

    # -- Tip: shown only in fully interactive mode (no required flags given) --

    if date is None and brew_type is None and dose is None and water_weight is None:
        click.echo(
            'Tip: add optional details with flags, e.g. --method "V60" --rating-overall 4'
            ' --tasting-notes "Bright acidity"  (run --help for all options)'
        )

    # -- Resolve required fields (prompt if not supplied as flags) --

    if date is None:
        date = _prompt_date()
    elif not DATE_PATTERN.match(date):
        click.echo(
            "Error: date must be YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ",
            err=True,
        )
        sys.exit(1)

    if brew_type is None:
        brew_type = _prompt_brew_type()

    if dose is None:
        dose = _prompt_positive_float("Coffee dose in grams")

    if water_weight is None:
        water_weight = _prompt_positive_float("Water weight in grams")

    # -- Validate rating dimensions (1-5) --
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

    # -- Build Pydantic model (validates all fields) --

    has_coffee = any([roast_date, coffee_type, origin, varietal, process])
    coffee_obj = None
    if has_coffee:
        try:
            coffee_obj = CoffeeInput(
                roast_date=roast_date,
                type=coffee_type,
                origin=list(origin) if origin else None,
                varietal=varietal,
                process=process,
            )
        except ValidationError as exc:
            click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
            sys.exit(1)

    water_obj = None
    if water_ppm is not None:
        try:
            water_obj = WaterInput(ppm=water_ppm)
        except ValidationError as exc:
            click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
            sys.exit(1)

    equipment_obj = None
    if grinder is not None or brewer is not None:
        try:
            equipment_obj = EquipmentInput(grinder=grinder, brewer=brewer)
        except ValidationError as exc:
            click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
            sys.exit(1)

    result_obj = None
    has_any_rating = any(v is not None for v in _RATING_DIMS.values())
    has_result = any(v is not None for v in (tds, ey, brix, tasting_notes)) or has_any_rating
    if has_result:
        ratings_obj = None
        if has_any_rating:
            try:
                ratings_obj = RatingsInput(
                    overall=rating_overall,
                    fragrance=rating_fragrance,
                    aroma=rating_aroma,
                    flavour=rating_flavour,
                    aftertaste=rating_aftertaste,
                    acidity=rating_acidity,
                    sweetness=rating_sweetness,
                    mouthfeel=rating_mouthfeel,
                )
            except ValidationError as exc:
                click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
                sys.exit(1)
        try:
            result_obj = ResultInput(
                tds=tds,
                ey=ey,
                brix=brix,
                tasting_notes=tasting_notes,
                ratings=ratings_obj,
            )
        except ValidationError as exc:
            click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
            sys.exit(1)

    try:
        brew = BrewInput(
            date=date,
            type=brew_type,
            dose_g=dose,
            water_weight_g=water_weight,
            method=method or None,
            water_volume_ml=None,
            water_temp_c=temp,
            grind=grind,
            duration_s=duration,
            notes=notes,
            coffee=coffee_obj,
            water=water_obj,
            equipment=equipment_obj,
            result=result_obj,
        )
    except ValidationError as exc:
        click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        sys.exit(1)

    # -- Write to DB --
    conn = db.get_connection()
    try:
        brew_id = db.insert_brew(brew, conn)
    finally:
        conn.close()

    click.echo(f"Brew #{brew_id} logged.")
