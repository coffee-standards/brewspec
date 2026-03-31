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
    OriginInput,
    WaterInput,
    EquipmentInput,
    ResultInput,
    RatingsInput,
    ROAST_LEVEL_ENUM,
    DATE_PATTERN,
)
from brewlog.prompts import prompt_brew_type


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


def _build_origins_from_flags(
    origin_name: tuple,
    origin_country: tuple,
    origin_region: tuple,
    origin_subregion: tuple,
    origin_producer: tuple,
    origin_process: tuple,
    origin_lot: tuple,
    origin_year: tuple,
    origin_varietal: tuple,
    origin_plain: tuple,
    elevation_masl: int | None = None,
    origin_cupping_notes: str | None = None,
) -> list[OriginInput] | None:
    """
    Build a list of OriginInput objects from the positional-parallel flag tuples.

    The structured --origin-* flags take precedence over plain --origin flags.
    If no structured origin flags are given but --origin is, fall back to plain string origins.
    elevation_masl applies to the first origin entry when provided.
    origin_cupping_notes is applied to the first origin entry when provided.
    """
    has_structured = any([
        origin_name, origin_country, origin_region, origin_subregion,
        origin_producer, origin_process, origin_lot, origin_year, origin_varietal,
    ])

    if not has_structured and not origin_plain and elevation_masl is None and origin_cupping_notes is None:
        return None

    if not has_structured and not origin_plain and elevation_masl is None and origin_cupping_notes is not None:
        # Only origin_cupping_notes given — create a single origin with just that field
        return [OriginInput(cupping_notes=origin_cupping_notes)]

    if not has_structured and not origin_plain and elevation_masl is not None:
        # Only elevation_masl (and possibly cupping_notes) given
        return [OriginInput(elevation_masl=elevation_masl, cupping_notes=origin_cupping_notes)]

    if not has_structured and origin_plain:
        # Legacy: plain string origins
        origins = [OriginInput(country=o) for o in origin_plain]
        # Apply elevation_masl to first entry if provided
        if elevation_masl is not None and origins:
            origins[0] = OriginInput(
                country=origins[0].country,
                elevation_masl=elevation_masl,
                cupping_notes=origin_cupping_notes if len(origins) > 0 else None,
            )
        elif origin_cupping_notes is not None and origins:
            origins[0] = OriginInput(country=origins[0].country, cupping_notes=origin_cupping_notes)
        return origins

    # Structured: positional-parallel approach
    # Find the max length across all flag tuples
    max_len = max(
        len(origin_name), len(origin_country), len(origin_region),
        len(origin_subregion), len(origin_producer), len(origin_process),
        len(origin_lot), len(origin_year), len(origin_varietal),
    )

    def _get(tpl: tuple, i: int):
        return tpl[i] if i < len(tpl) else None

    origins = []
    for i in range(max_len):
        # elevation_masl and origin_cupping_notes apply to first origin entry
        elev = elevation_masl if i == 0 else None
        cup_notes = origin_cupping_notes if i == 0 else None
        origin = OriginInput(
            name=_get(origin_name, i),
            country=_get(origin_country, i),
            region=_get(origin_region, i),
            subregion=_get(origin_subregion, i),
            producer=_get(origin_producer, i),
            process=_get(origin_process, i),
            lot=_get(origin_lot, i),
            harvest_year=_get(origin_year, i),
            varietal=_get(origin_varietal, i),
            elevation_masl=elev,
            cupping_notes=cup_notes,
        )
        origins.append(origin)
    return origins if origins else None


# ---------------------------------------------------------------------------
# Command definition
# ---------------------------------------------------------------------------

@click.command("add")
@click.pass_context
@click.option("--date",        "date",         type=str,   default=None,
              help="Brew date: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD.")
@click.option("--type",        "brew_type",    type=str,   default=None,
              help="Brew type: immersion, pour_over, espresso, hybrid.")
@click.option("--dose",        "dose",         type=float, default=None,
              help="Coffee dose in grams (> 0).")
@click.option("--water",       "water_g",      type=float, default=None,
              help="Water in grams (> 0).")
@click.option("--brew-ratio",  "brew_ratio",   type=float, default=None,
              help="Water-to-coffee ratio (> 0). e.g. 15.5")
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
@click.option("--process-notes", "process_notes", type=str, default=None,
              help=(
                  "Operational preparation notes (e.g. 'rinsed filter, 30s bloom'). "
                  "For sensory impressions use --tasting-notes."
              ))
@click.option("--target-yield", "target_yield", type=float, default=None,
              help=(
                  "Recipe target output weight in grams (> 0). For espresso dialling — "
                  "the intended liquid yield. For actual output weight use --yield-g."
              ))
@click.option("--actual-water", "actual_water", type=float, default=None,
              help=(
                  "Actual water used in grams (> 0). Record when actual water deviates "
                  "from the recipe target (--water)."
              ))
@click.option("--actual-dose", "actual_dose", type=float, default=None,
              help=(
                  "Actual coffee dose used in grams (> 0). Record when actual dose deviates "
                  "from the recipe target (--dose)."
              ))
@click.option("--actual-duration", "actual_duration", type=float, default=None,
              help=(
                  "Actual extraction time in seconds (> 0). Record the measured shot or brew time."
              ))
@click.option("--roast-date",  "roast_date",   type=str,   default=None,
              help="Coffee roast date (YYYY-MM-DD).")
@click.option("--coffee-type", "coffee_type",  type=str,   default=None,
              help="Coffee classification: single_origin or blend.")
@click.option("--coffee-name", "coffee_name",  type=str,   default=None,
              help="Coffee product name or descriptive label (e.g. 'Ethiopia Yirgacheffe').")
@click.option("--coffee-cupping-notes", "coffee_cupping_notes", type=str, default=None,
              help=(
                  "Sensory notes on the coffee as a whole — bag description or "
                  "pre-brew cupping impressions."
              ))
@click.option("--roaster",     "roaster",      type=str,   default=None,
              help="Roaster name (company or person who roasted the coffee).")
@click.option("--roast-level", "roast_level",  type=str,   default=None,
              help="Roast level: light, medium, or dark.")
@click.option("--elevation-masl", "elevation_masl", type=int, default=None,
              help="Growing elevation in meters above sea level (> 0). Applies to the first origin entry.")
@click.option("--origin",      "origin",       type=str,   default=None,
              multiple=True,
              help="Coffee origin (may be repeated: --origin Ethiopia --origin Colombia). Legacy flag.")
@click.option("--origin-name",      "origin_name",      type=str, multiple=True, default=(),
              help="Origin component name (repeatable).")
@click.option("--origin-country",   "origin_country",   type=str, multiple=True, default=(),
              help="Country of production (repeatable).")
@click.option("--origin-region",    "origin_region",    type=str, multiple=True, default=(),
              help="Region within the country (repeatable).")
@click.option("--origin-subregion", "origin_subregion", type=str, multiple=True, default=(),
              help="Sub-area within the region (repeatable).")
@click.option("--origin-producer",  "origin_producer",  type=str, multiple=True, default=(),
              help="Farm, cooperative, or washing station (repeatable).")
@click.option("--origin-process",   "origin_process",   type=str, multiple=True, default=(),
              help="Green coffee processing method (repeatable).")
@click.option("--origin-lot",       "origin_lot",       type=str, multiple=True, default=(),
              help="Lot or batch identifier (repeatable).")
@click.option("--origin-year",      "origin_year",      type=int, multiple=True, default=(),
              help="Harvest year, e.g. 2025 (repeatable).")
@click.option("--origin-varietal",  "origin_varietal",  type=str, multiple=True, default=(),
              help="Coffee varietal for this origin entry (repeatable).")
@click.option("--origin-cupping-notes", "origin_cupping_notes", type=str, default=None,
              help=(
                  "Sensory notes for the origin component (or the single origin "
                  "for single-origin coffees)."
              ))
@click.option("--water-ppm",   "water_ppm",    type=float, default=None,
              help="Water mineral content in ppm (>= 0).")
@click.option("--tds",         "tds",          type=float, default=None,
              help="Brew TDS percentage (> 0).")
@click.option("--ey",          "ey",           type=float, default=None,
              help="Extraction yield percentage (> 0).")
@click.option("--brix",        "brix",         type=float, default=None,
              help="Degrees Brix (>= 0).")
@click.option("--yield-g",     "yield_g",      type=float, default=None,
              help="Output weight of the brew in grams (> 0). For espresso: liquid collected in cup.")
@click.option("--tasting-notes", "tasting_notes", type=str, default=None,
              help=(
                  "Sensory tasting notes — impressions of the cup. "
                  "For operational brew-process notes use --process-notes."
              ))
@click.option("--rating",         "rating_retired",    type=int, default=None, hidden=True)
@click.option("--rating-overall", "rating_overall",    type=int, default=None,
              help="Overall impression, 1-9.")
@click.option("--rating-fragrance", "rating_fragrance", type=int, default=None,
              help="Fragrance rating, 1-9.")
@click.option("--rating-aroma",    "rating_aroma",     type=int, default=None,
              help="Aroma rating, 1-9.")
@click.option("--rating-flavour",  "rating_flavour",   type=int, default=None,
              help="Flavour rating, 1-9.")
@click.option("--rating-aftertaste", "rating_aftertaste", type=int, default=None,
              help="Aftertaste rating, 1-9.")
@click.option("--rating-acidity",  "rating_acidity",   type=int, default=None,
              help="Acidity rating, 1-9.")
@click.option("--rating-sweetness", "rating_sweetness", type=int, default=None,
              help="Sweetness rating, 1-9.")
@click.option("--rating-mouthfeel", "rating_mouthfeel", type=int, default=None,
              help="Mouthfeel rating, 1-9.")
@click.option("--grinder",     "grinder",      type=str,   default=None,
              help="Grinder name or description.")
@click.option("--grinder-setting", "grinder_setting", type=float, default=None,
              help="Grinder dial or click setting (> 0). e.g. 21 or 5.2")
@click.option("--brewer",      "brewer",       type=str,   default=None,
              help="Brewer/dripper name or description.")
@click.option("--equipment-notes", "equipment_notes", type=str, default=None,
              help="Equipment state notes (e.g. 'Burrs replaced 2026-01').")
@click.option("--pressure-bar", "pressure_bar", type=float, default=None,
              help="Line or lever pressure in bars (> 0). Primarily for espresso.")
@click.option("--flow-rate",   "flow_rate_ml_s", type=float, default=None,
              help="Volumetric flow rate in ml/s (> 0). Useful for espresso profiling.")
def add(
    ctx,
    date, brew_type, dose, water_g,
    brew_ratio,
    method, temp, grind, duration, process_notes,
    target_yield, actual_water, actual_dose, actual_duration,
    roast_date, coffee_type, coffee_name, coffee_cupping_notes,
    roaster, roast_level, elevation_masl,
    origin,
    origin_name, origin_country, origin_region, origin_subregion,
    origin_producer, origin_process, origin_lot, origin_year, origin_varietal,
    origin_cupping_notes,
    water_ppm, tds, ey, brix, yield_g, tasting_notes,
    rating_retired,
    rating_overall, rating_fragrance, rating_aroma, rating_flavour,
    rating_aftertaste, rating_acidity, rating_sweetness, rating_mouthfeel,
    grinder, grinder_setting, brewer, equipment_notes,
    pressure_bar, flow_rate_ml_s,
) -> None:
    """Log a new brew."""

    # -- Check for retired --rating flag first --
    if rating_retired is not None:
        click.echo(
            "Error: --rating has been replaced by --rating-overall in BrewLog v0.3.\n"
            "Use --rating-overall N to set your overall impression (1-9).\n"
            "See --help for all available rating dimension flags.",
            err=True,
        )
        sys.exit(1)

    # -- Validate new v0.5 flags before prompting for required fields --

    if brew_ratio is not None and brew_ratio <= 0:
        click.echo("Error: --brew-ratio must be greater than 0.", err=True)
        sys.exit(1)

    if coffee_name is not None and not coffee_name.strip():
        click.echo("Error: --coffee-name must not be empty.", err=True)
        sys.exit(1)

    if grinder_setting is not None and grinder_setting <= 0:
        click.echo("Error: --grinder-setting must be greater than 0.", err=True)
        sys.exit(1)

    if equipment_notes is not None and not equipment_notes.strip():
        click.echo("Error: --equipment-notes must not be empty.", err=True)
        sys.exit(1)

    if yield_g is not None and yield_g <= 0:
        click.echo("Error: --yield-g must be greater than 0.", err=True)
        sys.exit(1)

    if roast_level is not None and roast_level not in ROAST_LEVEL_ENUM:
        click.echo(
            f"Error: --roast-level must be one of: {sorted(ROAST_LEVEL_ENUM)}",
            err=True,
        )
        sys.exit(1)

    if elevation_masl is not None and elevation_masl <= 0:
        click.echo("Error: --elevation-masl must be greater than 0.", err=True)
        sys.exit(1)

    # Validate --origin-varietal entries (non-empty when supplied)
    for v in origin_varietal:
        if not v or not v.strip():
            click.echo("Error: --origin-varietal must not be empty.", err=True)
            sys.exit(1)

    # -- Validate new v1.0 flags --

    if target_yield is not None and target_yield <= 0:
        click.echo("Error: --target-yield must be greater than 0.", err=True)
        sys.exit(1)

    if actual_water is not None and actual_water <= 0:
        click.echo("Error: --actual-water must be greater than 0.", err=True)
        sys.exit(1)

    if coffee_cupping_notes is not None and not coffee_cupping_notes.strip():
        click.echo("Error: --coffee-cupping-notes must not be empty.", err=True)
        sys.exit(1)

    if origin_cupping_notes is not None and not origin_cupping_notes.strip():
        click.echo("Error: --origin-cupping-notes must not be empty.", err=True)
        sys.exit(1)

    if pressure_bar is not None and pressure_bar <= 0:
        click.echo("Error: --pressure-bar must be greater than 0.", err=True)
        sys.exit(1)

    if flow_rate_ml_s is not None and flow_rate_ml_s <= 0:
        click.echo("Error: --flow-rate must be greater than 0.", err=True)
        sys.exit(1)

    if actual_dose is not None and actual_dose <= 0:
        click.echo("Error: --actual-dose must be greater than 0.", err=True)
        sys.exit(1)

    if actual_duration is not None and actual_duration <= 0:
        click.echo("Error: --actual-duration must be greater than 0.", err=True)
        sys.exit(1)

    # -- Tip: shown only in fully interactive mode (no required flags given) --

    if date is None and brew_type is None and dose is None and water_g is None:
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
        brew_type = prompt_brew_type()

    if dose is None:
        dose = _prompt_positive_float("Coffee dose in grams")

    if water_g is None:
        water_g = _prompt_positive_float("Water in grams")

    # -- Validate rating dimensions (1-9) --
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
        if flag_val is not None and not (1 <= flag_val <= 9):
            click.echo(
                f"Error: --{flag_name} must be an integer between 1 and 9.",
                err=True,
            )
            sys.exit(1)

    # -- Build coffee object --

    has_structured_origin = any([
        origin_name, origin_country, origin_region, origin_subregion,
        origin_producer, origin_process, origin_lot, origin_year, origin_varietal,
    ])
    has_coffee = any([
        roast_date, coffee_type, coffee_name, coffee_cupping_notes,
        roaster, roast_level,
        origin, has_structured_origin, elevation_masl is not None,
        origin_cupping_notes is not None,
    ])
    coffee_obj = None
    if has_coffee:
        try:
            origins_list = _build_origins_from_flags(
                origin_name, origin_country, origin_region, origin_subregion,
                origin_producer, origin_process, origin_lot, origin_year, origin_varietal,
                origin,
                elevation_masl=elevation_masl,
                origin_cupping_notes=origin_cupping_notes,
            )
            coffee_obj = CoffeeInput(
                roast_date=roast_date,
                type=coffee_type,
                name=coffee_name,
                cupping_notes=coffee_cupping_notes,
                roaster=roaster,
                roast_level=roast_level,
                origins=origins_list,
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

    has_equipment = any(v is not None for v in (grinder, brewer, grinder_setting, equipment_notes, pressure_bar, flow_rate_ml_s))
    equipment_obj = None
    if has_equipment:
        try:
            equipment_obj = EquipmentInput(
                grinder=grinder,
                brewer=brewer,
                grinder_setting=grinder_setting,
                notes=equipment_notes,
                pressure_bar=pressure_bar,
                flow_rate_ml_s=flow_rate_ml_s,
            )
        except ValidationError as exc:
            click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
            sys.exit(1)

    result_obj = None
    has_any_rating = any(v is not None for v in _RATING_DIMS.values())
    has_result = any(v is not None for v in (tds, ey, brix, yield_g, actual_water, actual_dose, actual_duration, tasting_notes)) or has_any_rating
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
                yield_g=yield_g,
                water_g=actual_water,
                dose_g=actual_dose,
                duration_s=actual_duration,
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
            water_g=water_g,
            brew_ratio=brew_ratio,
            method=method or None,
            water_temp_c=temp,
            grind=grind,
            duration_s=duration,
            process_notes=process_notes,
            yield_g=target_yield,
            coffee=coffee_obj,
            water=water_obj,
            equipment=equipment_obj,
            result=result_obj,
        )
    except ValidationError as exc:
        click.echo(f"Error: {exc.errors()[0]['msg']}", err=True)
        sys.exit(1)

    # -- Write to DB --
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    conn = db.get_connection(db_path=db_path)
    try:
        brew_id = db.insert_brew(brew, conn)
    finally:
        conn.close()

    click.echo(f"Brew #{brew_id} logged.")
