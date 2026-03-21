"""
Pydantic models for BrewLog input validation.

These models serve two purposes:
  1. CLI input validation — the `add` command constructs a BrewInput from CLI
     arguments and prompts before writing to the DB.
  2. Secondary validation layer — after JSON Schema validation on import, each
     brew can optionally be run through BrewInput for additional checks.

Field names mirror BrewSpec v0.9 snake_case names exactly.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BREW_TYPE_ENUM = frozenset({"immersion", "pour_over", "espresso", "hybrid"})
COFFEE_TYPE_ENUM = frozenset({"single_origin", "blend"})
GRIND_ENUM = frozenset({
    "turkish", "espresso", "fine", "medium_fine",
    "medium", "medium_coarse", "coarse"
})
ROAST_LEVEL_ENUM = frozenset({"light", "medium", "dark"})
ROAST_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z|\d{4}-\d{2}-\d{2})$"
)


# ---------------------------------------------------------------------------
# OriginInput
# ---------------------------------------------------------------------------

class OriginInput(BaseModel):
    """A single origin record within a coffee.origins array. All fields optional."""

    name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    producer: Optional[str] = None
    process: Optional[str] = None
    lot: Optional[str] = None
    harvest_year: Optional[int] = None
    varietal: Optional[str] = None  # new in v0.6
    elevation_masl: Optional[int] = None  # new in v0.8

    @field_validator("name", "country", "region", "subregion", "producer", "process", "lot", "varietal")
    @classmethod
    def validate_origin_string(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v

    @field_validator("harvest_year")
    @classmethod
    def validate_harvest_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1900 <= v <= 2100):
            raise ValueError("harvest_year must be between 1900 and 2100 inclusive")
        return v

    @field_validator("elevation_masl")
    @classmethod
    def validate_elevation_masl(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("elevation_masl must be greater than 0")
        return v


# ---------------------------------------------------------------------------
# CoffeeInput
# ---------------------------------------------------------------------------

class CoffeeInput(BaseModel):
    """Optional coffee ingredient descriptor. All fields optional."""

    name: Optional[str] = None          # new in v0.6; branded or descriptive label
    roaster: Optional[str] = None       # new in v0.8; company/person who roasted
    roast_level: Optional[str] = None   # new in v0.8; light | medium | dark
    roast_date: Optional[str] = None
    type: Optional[str] = None          # "single_origin" | "blend"
    origins: Optional[list[OriginInput]] = None
    # process: removed in v0.6
    # varietal: removed in v0.6

    @field_validator("name")
    @classmethod
    def validate_coffee_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty")
            if len(v) > 150:
                raise ValueError("value must not exceed 150 characters")
        return v

    @field_validator("roaster")
    @classmethod
    def validate_roaster(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("roaster must not be empty when provided")
            if len(v) > 100:
                raise ValueError("roaster must not exceed 100 characters")
        return v

    @field_validator("roast_level")
    @classmethod
    def validate_roast_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ROAST_LEVEL_ENUM:
            raise ValueError(
                f"roast_level must be one of: {sorted(ROAST_LEVEL_ENUM)}"
            )
        return v

    @field_validator("roast_date")
    @classmethod
    def validate_roast_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not ROAST_DATE_PATTERN.match(v):
            raise ValueError("roast_date must match YYYY-MM-DD")
        return v

    @field_validator("type")
    @classmethod
    def validate_coffee_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in COFFEE_TYPE_ENUM:
            raise ValueError(
                f"coffee type must be one of: {sorted(COFFEE_TYPE_ENUM)}"
            )
        return v

    @field_validator("origins")
    @classmethod
    def validate_origins(cls, v: Optional[list[OriginInput]]) -> Optional[list[OriginInput]]:
        if v is not None and len(v) == 0:
            raise ValueError(
                "origins must have at least one entry when present; "
                "omit the field to record no origin data"
            )
        return v


# ---------------------------------------------------------------------------
# WaterInput
# ---------------------------------------------------------------------------

class WaterInput(BaseModel):
    """Optional water ingredient descriptor. All fields optional."""

    ppm: Optional[float] = None

    @field_validator("ppm")
    @classmethod
    def validate_ppm(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("water ppm must be >= 0")
        return v


# ---------------------------------------------------------------------------
# EquipmentInput
# ---------------------------------------------------------------------------

class EquipmentInput(BaseModel):
    """Optional equipment descriptor. All fields optional."""

    grinder: Optional[str] = None
    brewer: Optional[str] = None
    grinder_setting: Optional[float] = None   # was Optional[str] in v0.5; float accepts int and float
    notes: Optional[str] = None

    @field_validator("grinder", "brewer")
    @classmethod
    def validate_equipment_short_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v

    @field_validator("grinder_setting")
    @classmethod
    def validate_grinder_setting(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("grinder_setting must be greater than 0")
        return v

    @field_validator("notes")
    @classmethod
    def validate_equipment_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("notes must not be empty when provided")
            if len(v) > 2000:
                raise ValueError("notes must not exceed 2000 characters")
        return v


# ---------------------------------------------------------------------------
# RatingsInput
# ---------------------------------------------------------------------------

class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-9 (SCA CVA hedonic scale)."""

    overall: Optional[int] = None
    fragrance: Optional[int] = None
    aroma: Optional[int] = None
    flavour: Optional[int] = None
    aftertaste: Optional[int] = None
    acidity: Optional[int] = None
    sweetness: Optional[int] = None
    mouthfeel: Optional[int] = None

    @field_validator(
        "overall", "fragrance", "aroma", "flavour",
        "aftertaste", "acidity", "sweetness", "mouthfeel"
    )
    @classmethod
    def validate_rating_dimension(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 9):
            raise ValueError("rating dimension must be between 1 and 9 inclusive")
        return v


# ---------------------------------------------------------------------------
# ResultInput
# ---------------------------------------------------------------------------

class ResultInput(BaseModel):
    """Optional brew outcome descriptor. All fields optional."""

    tds: Optional[float] = None
    ey: Optional[float] = None
    brix: Optional[float] = None
    yield_g: Optional[float] = None
    tasting_notes: Optional[str] = None
    ratings: Optional[RatingsInput] = None

    @field_validator("tds", "ey")
    @classmethod
    def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    @field_validator("brix")
    @classmethod
    def validate_brix(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("brix must be >= 0")
        return v

    @field_validator("yield_g")
    @classmethod
    def yield_g_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("yield_g must be > 0")
        return v

    @field_validator("tasting_notes")
    @classmethod
    def validate_tasting_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("tasting_notes must not be empty when provided")
            if len(v) > 2000:
                raise ValueError("tasting_notes must not exceed 2000 characters")
        return v


# ---------------------------------------------------------------------------
# BrewInput
# ---------------------------------------------------------------------------

class BrewInput(BaseModel):
    """Primary model for a brew log entry. Validates all BrewSpec v0.9 constraints."""

    # In v0.7 these four fields are optional at the schema level.
    # The CLI add/update commands still collect them interactively.
    date: Optional[str] = None
    type: Optional[str] = None          # brew type enum
    dose_g: Optional[float] = None
    water_weight_g: Optional[float] = None

    # Optional brew parameters
    brew_ratio: Optional[float] = None
    method: Optional[str] = None
    # water_volume_ml: removed in v0.6
    water_temp_c: Optional[float] = None
    grind: Optional[str] = None
    duration_s: Optional[int] = None
    notes: Optional[str] = None

    # Optional nested objects (stored flat in DB)
    coffee: Optional[CoffeeInput] = None
    water: Optional[WaterInput] = None
    equipment: Optional[EquipmentInput] = None
    result: Optional[ResultInput] = None

    # ------------------------------------------------------------------
    # Field validators (fields are optional in v0.7)
    # ------------------------------------------------------------------

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not DATE_PATTERN.match(v):
            raise ValueError(
                "date must be YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ"
            )
        # Format-specific secondary validation
        if "T" in v:
            # Full datetime — verify it parses as a real datetime
            try:
                datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError("date is not a valid datetime")
        # Date-only format: the pattern enforces format.
        # Calendar correctness (e.g., month 13) is NOT checked here per AC-7.
        return v

    @field_validator("type")
    @classmethod
    def validate_brew_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in BREW_TYPE_ENUM:
            raise ValueError(
                f"type must be one of: {sorted(BREW_TYPE_ENUM)}"
            )
        return v

    @field_validator("dose_g", "water_weight_g")
    @classmethod
    def validate_positive_required(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    # ------------------------------------------------------------------
    # Optional numeric field validators
    # ------------------------------------------------------------------

    @field_validator("brew_ratio")
    @classmethod
    def validate_brew_ratio(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("brew_ratio must be greater than 0")
        return v

    @field_validator("water_temp_c")
    @classmethod
    def validate_water_temp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if not (0 <= v <= 100):
                raise ValueError("water_temp_c must be between 0 and 100 inclusive")
            # v0.8: values must have at most 1 decimal place (multipleOf 0.1)
            if round(v, 1) != v:
                raise ValueError(
                    "water_temp_c must not have more than 1 decimal place (e.g. 96.1, not 96.15)"
                )
        return v

    @field_validator("duration_s")
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("duration_s must be greater than 0")
        return v

    # ------------------------------------------------------------------
    # Optional freeform text field validators
    # ------------------------------------------------------------------

    @field_validator("method")
    @classmethod
    def validate_short_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v

    @field_validator("grind")
    @classmethod
    def validate_grind(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in GRIND_ENUM:
            raise ValueError(
                f"grind must be one of: {sorted(GRIND_ENUM)}"
            )
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 2000:
                raise ValueError("notes must not exceed 2000 characters")
        return v
