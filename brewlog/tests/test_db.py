"""
Unit tests for the database layer in brewlog.db.
Tests map to AC-3, AC-4, AC-10, AC-12, AC-14, AC-15, AC-16, AC-28, AC-33,
and the Security parameterised-query requirement.
"""

import json
import pytest

from brewlog import db as db_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def test_init_db_creates_table(tmp_db):
    """AC-4: brews table exists after get_connection()."""
    cursor = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='brews'"
    )
    assert cursor.fetchone() is not None


def test_init_db_creates_index(tmp_db):
    """AC-4: idx_brews_date index exists."""
    cursor = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_brews_date'"
    )
    assert cursor.fetchone() is not None


def test_init_db_idempotent(tmp_path):
    """AC-3: calling get_connection() twice does not fail."""
    conn1 = db_module.get_connection(db_path=tmp_path / "test.db")
    conn1.close()
    conn2 = db_module.get_connection(db_path=tmp_path / "test.db")
    conn2.close()


def test_init_db_creates_directory(tmp_path):
    """AC-3: DB directory is created if it does not exist."""
    nested = tmp_path / "nested" / "dir"
    # Directory does not yet exist
    assert not nested.exists()
    conn = db_module.get_connection(db_path=nested / "test.db")
    conn.close()
    assert nested.exists()


# ---------------------------------------------------------------------------
# insert_brew
# ---------------------------------------------------------------------------

def _minimal_brew():
    return BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
    )


def _full_brew():
    return BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        method="Hario V60",
        water_temp_c=96.0,
        grind="medium-fine",
        duration_s=180,
        tds=1.38,
        rating=4,
        notes="Bright acidity",
        coffee=CoffeeInput(
            roast_date="2026-01-20",
            type="single_origin",
            origin=["Ethiopia"],
            varietal="Heirloom",
            process="Washed",
        ),
        water=WaterInput(ppm=150.0),
    )


def test_insert_brew_minimal(tmp_db):
    """AC-10: inserts minimal BrewInput, returns id=1."""
    brew_id = db_module.insert_brew(_minimal_brew(), tmp_db)
    assert brew_id == 1


def test_insert_brew_returns_incrementing_ids(tmp_db):
    """AC-10: Sequential inserts return incrementing IDs."""
    id1 = db_module.insert_brew(_minimal_brew(), tmp_db)
    id2 = db_module.insert_brew(_minimal_brew(), tmp_db)
    assert id2 == id1 + 1


def test_insert_brew_all_fields(tmp_db):
    """AC-10: inserts full BrewInput, all fields retrievable."""
    brew_id = db_module.insert_brew(_full_brew(), tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row is not None
    assert row["date"] == "2026-02-19T08:30:00Z"
    assert row["type"] == "pour_over"
    assert row["method"] == "Hario V60"
    assert row["dose_g"] == 18.0
    assert row["water_weight_g"] == 280.0
    assert row["water_temp_c"] == 96.0
    assert row["grind"] == "medium-fine"
    assert row["duration_s"] == 180
    assert row["tds"] == 1.38
    assert row["rating"] == 4
    assert row["notes"] == "Bright acidity"
    assert row["coffee_roast_date"] == "2026-01-20"
    assert row["coffee_type"] == "single_origin"
    assert row["coffee_varietal"] == "Heirloom"
    assert row["coffee_process"] == "Washed"
    assert row["water_ppm"] == 150.0


def test_insert_brew_origin_serialised(tmp_db):
    """Section 3.1: coffee_origin stored as JSON string."""
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        coffee=CoffeeInput(origin=["Ethiopia", "Colombia"]),
    )
    brew_id = db_module.insert_brew(brew, tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    stored_origin = row["coffee_origin"]
    assert isinstance(stored_origin, str)
    assert json.loads(stored_origin) == ["Ethiopia", "Colombia"]


def test_insert_brew_no_coffee_origin_is_null(tmp_db):
    """Section 3.1: NULL stored when no origin provided."""
    brew_id = db_module.insert_brew(_minimal_brew(), tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row["coffee_origin"] is None


# ---------------------------------------------------------------------------
# get_brew
# ---------------------------------------------------------------------------

def test_get_brew_existing(tmp_db):
    """AC-17: get_brew(1) returns correct row."""
    brew_id = db_module.insert_brew(_minimal_brew(), tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row is not None
    assert row["id"] == brew_id
    assert row["type"] == "pour_over"


def test_get_brew_not_found(tmp_db):
    """AC-19: get_brew(999) returns None."""
    result = db_module.get_brew(999, tmp_db)
    assert result is None


# ---------------------------------------------------------------------------
# list_brews
# ---------------------------------------------------------------------------

def _insert_n_brews(conn, n: int):
    """Insert n brews with incrementing dates."""
    for i in range(n):
        brew = BrewInput(
            date=f"2026-02-{i + 1:02d}T08:30:00Z",
            type="pour_over",
            dose_g=18.0,
            water_weight_g=280.0,
        )
        db_module.insert_brew(brew, conn)


def test_list_brews_default_limit(tmp_db):
    """AC-12: returns at most 20 rows with default limit."""
    _insert_n_brews(tmp_db, 25)
    rows = db_module.list_brews(tmp_db)
    assert len(rows) == 20


def test_list_brews_custom_limit(tmp_db):
    """AC-14: list_brews(limit=5) returns at most 5 rows."""
    _insert_n_brews(tmp_db, 10)
    rows = db_module.list_brews(tmp_db, limit=5)
    assert len(rows) == 5


def test_list_brews_all(tmp_db):
    """AC-15: list_brews(all_rows=True) returns all rows."""
    _insert_n_brews(tmp_db, 25)
    rows = db_module.list_brews(tmp_db, all_rows=True)
    assert len(rows) == 25


def test_list_brews_empty(tmp_db):
    """AC-16: returns empty list when no rows."""
    rows = db_module.list_brews(tmp_db)
    assert rows == []


def test_list_brews_order(tmp_db):
    """AC-12: most recent date comes first."""
    _insert_n_brews(tmp_db, 5)
    rows = db_module.list_brews(tmp_db, all_rows=True)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True)


# ---------------------------------------------------------------------------
# insert_brew_dict
# ---------------------------------------------------------------------------

def test_insert_brew_dict_minimal(tmp_db):
    """AC-28: insert_brew_dict with minimal dict inserts correctly."""
    brew_dict = {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
    }
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    row = db_module.get_brew(brew_id, tmp_db)
    assert row is not None
    assert row["date"] == "2026-02-19T08:30:00Z"
    assert row["type"] == "pour_over"


def test_insert_brew_dict_full(tmp_db):
    """AC-28: insert_brew_dict with full dict inserts correctly."""
    brew_dict = {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
        "method": "Hario V60",
        "water_temp_c": 96.0,
        "grind": "medium-fine",
        "duration_s": 180,
        "tds": 1.38,
        "rating": 4,
        "notes": "Bright acidity",
        "coffee": {
            "roast_date": "2026-01-20",
            "type": "single_origin",
            "origin": ["Ethiopia"],
            "varietal": "Heirloom",
            "process": "Washed",
        },
        "water": {"ppm": 150.0},
    }
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    row = db_module.get_brew(brew_id, tmp_db)
    assert row["method"] == "Hario V60"
    assert row["coffee_type"] == "single_origin"
    assert json.loads(row["coffee_origin"]) == ["Ethiopia"]
    assert row["water_ppm"] == 150.0


def test_insert_brew_dict_no_dedup(tmp_db):
    """AC-33: re-inserting same dict creates a second row."""
    brew_dict = {
        "date": "2026-02-19T08:30:00Z",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
    }
    id1 = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    id2 = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    assert id2 != id1
    rows = db_module.list_brews(tmp_db, all_rows=True)
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# Security: parameterised queries
# ---------------------------------------------------------------------------

def test_parameterised_query_safety(tmp_db):
    """Security: SQL-special characters in text fields don't corrupt DB."""
    malicious = "'; DROP TABLE brews; --"
    brew = BrewInput(
        date="2026-02-19T08:30:00Z",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        method=malicious,
        notes=malicious,
        grind=malicious,
    )
    brew_id = db_module.insert_brew(brew, tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row is not None
    assert row["method"] == malicious
    assert row["notes"] == malicious
    assert row["grind"] == malicious
    # Table still exists
    cursor = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='brews'"
    )
    assert cursor.fetchone() is not None
