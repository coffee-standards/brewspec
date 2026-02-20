"""
`brewlog add` command.

Logs a new brew. Required fields can be supplied as flags (non-interactive)
or entered interactively via prompts. Validation is performed via Pydantic
models before any DB write.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import click
from pydantic import ValidationError

from brewlog import db
from brewlog.models import BrewInput, CoffeeInput, WaterInput, DATE_PATTERN, BREW_TYPE_ENUM


# ---------------------------------------------------------------------------
# Interactive prompt helpers
# ---------------------------------------------------------------------------

def _prompt_date() -> str:
    """Prompt for a date with the current UTC time as default. Re-prompts on invalid input."""
    default = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    while True:
        value = click.prompt("Date", default=default)
        if DATE_PATTERN.match(value):
            try:
                datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                return value
            except ValueError:
                pass
        click.echo(
            "  Error: date must be in format YYYY-MM-DDTHH:MM:SSZ "
            "(e.g. 2026-02-19T08:30:00Z)"
        )


def _prompt_brew_type() -> str:
    """Prompt for brew type. Re-prompts on invalid enum value."""
    valid = ", ".join(sorted(BREW_TYPE_ENUM))
    while True:
        value = click.prompt(f"Brew type ({valid})")
        if value in BREW_TYPE_ENUM:
            return value
        click.echo(
            f"  Error: brew type must be one of: {valid}"
        )


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
              help="ISO 8601 UTC datetime (YYYY-MM-DDTHH:MM:SSZ).")
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
              help="Freeform grind description.")
@click.option("--duration",    "duration",     type=int,   default=None,
              help="Brew duration in seconds (> 0).")
@click.option("--rating",      "rating",       type=int,   default=None,
              help="Rating 1-5.")
@click.option("--notes",       "notes",        type=str,   default=None,
              help="Freeform tasting notes.")
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
def add(
    date, brew_type, dose, water_weight,
    method, temp, grind, duration, rating, notes,
    roast_date, coffee_type, origin, varietal, process,
    water_ppm, tds,
) -> None:
    """Log a new brew."""

    # -- Resolve required fields (prompt if not supplied as flags) --

    if date is None:
        date = _prompt_date()
    elif not DATE_PATTERN.match(date):
        click.echo(
            "Error: date must be ISO 8601 UTC format: YYYY-MM-DDTHH:MM:SSZ",
            err=True,
        )
        sys.exit(1)

    if brew_type is None:
        brew_type = _prompt_brew_type()

    if dose is None:
        dose = _prompt_positive_float("Coffee dose in grams")

    if water_weight is None:
        water_weight = _prompt_positive_float("Water weight in grams")

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

    try:
        brew = BrewInput(
            date=date,
            type=brew_type,
            dose_g=dose,
            water_weight_g=water_weight,
            method=method or None,
            water_volume_ml=None,           # not exposed as flag in v0.1
            water_temp_c=temp,
            grind=grind,
            duration_s=duration,
            tds=tds,
            rating=rating,
            notes=notes,
            coffee=coffee_obj,
            water=water_obj,
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
