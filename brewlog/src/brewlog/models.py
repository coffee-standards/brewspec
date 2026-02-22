"""
Pydantic models for BrewLog input validation.

These models serve two purposes:
  1. CLI input validation — the `add` command constructs a BrewInput from CLI
     arguments and prompts before writing to the DB.
  2. Secondary validation layer — after JSON Schema validation on import, each
     brew can optionally be run through BrewInput for additional checks.

Field names mirror BrewSpec v0.4 snake_case names exactly.
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
ROAST_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z|\d{4}-\d{2}-\d{2})$"
)


# ---------------------------------------------------------------------------
# CoffeeInput
# ---------------------------------------------------------------------------

class CoffeeInput(BaseModel):
    """Optional coffee ingredient descriptor. All fields optional."""

    roast_date: Optional[str] = None
    type: Optional[str] = None          # "single_origin" | "blend"
    origin: Optional[list[str]] = None
    varietal: Optional[str] = None
    process: Optional[str] = None

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

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            if len(v) == 0:
                raise ValueError("origin must have at least one entry")
            for item in v:
                if not isinstance(item, str) or len(item.strip()) == 0:
                    raise ValueError("each origin entry must be a non-empty string")
                if len(item) > 100:
                    raise ValueError("each origin entry must not exceed 100 characters")
        return v

    @field_validator("varietal", "process")
    @classmethod
    def validate_min_length_1(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
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

    @field_validator("grinder", "brewer")
    @classmethod
    def validate_equipment_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("value must not be empty when provided")
            if len(v) > 100:
                raise ValueError("value must not exceed 100 characters")
        return v


# ---------------------------------------------------------------------------
# RatingsInput
# ---------------------------------------------------------------------------

class RatingsInput(BaseModel):
    """Optional multi-dimensional sensory ratings. All fields optional integers 1-5."""

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
        if v is not None and not (1 <= v <= 5):
            raise ValueError("rating dimension must be between 1 and 5 inclusive")
        return v


# ---------------------------------------------------------------------------
# ResultInput
# ---------------------------------------------------------------------------

class ResultInput(BaseModel):
    """Optional brew outcome descriptor. All fields optional."""

    tds: Optional[float] = None
    ey: Optional[float] = None
    brix: Optional[float] = None
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
    """Primary model for a brew log entry. Validates all BrewSpec v0.4 constraints."""

    # Required fields (no default)
    date: str
    type: str                           # brew type enum
    dose_g: float
    water_weight_g: float

    # Optional brew parameters
    method: Optional[str] = None
    water_volume_ml: Optional[float] = None
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
    # Required field validators
    # ------------------------------------------------------------------

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
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
    def validate_brew_type(cls, v: str) -> str:
        if v not in BREW_TYPE_ENUM:
            raise ValueError(
                f"type must be one of: {sorted(BREW_TYPE_ENUM)}"
            )
        return v

    @field_validator("dose_g", "water_weight_g")
    @classmethod
    def validate_positive_required(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    # ------------------------------------------------------------------
    # Optional numeric field validators
    # ------------------------------------------------------------------

    @field_validator("water_volume_ml")
    @classmethod
    def validate_exclusive_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("value must be greater than 0")
        return v

    @field_validator("water_temp_c")
    @classmethod
    def validate_water_temp(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("water_temp_c must be between 0 and 100 inclusive")
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
