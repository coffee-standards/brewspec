"""
Unit tests for the database layer in brewlog.db.
Tests map to AC-1, AC-3, AC-4, AC-10, AC-12, AC-14, AC-15, AC-16, AC-20,
AC-21, AC-22, AC-23, AC-28, AC-33, AC-34,
and the Security parameterised-query requirement.
"""

import json

from brewlog import db as db_module
from brewlog.models import BrewInput, CoffeeInput, WaterInput, ResultInput, RatingsInput


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
        grind="medium_fine",
        duration_s=180,
        notes="Bright acidity",
        coffee=CoffeeInput(
            roast_date="2026-01-20",
            type="single_origin",
            origin=["Ethiopia"],
            varietal="Heirloom",
            process="Washed",
        ),
        water=WaterInput(ppm=150.0),
        result=ResultInput(
            tds=1.38,
            ey=20.5,
            brix=1.5,
            tasting_notes="Bright citrus",
            ratings=RatingsInput(overall=4, acidity=5),
        ),
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
    assert row["grind"] == "medium_fine"
    assert row["duration_s"] == 180
    assert row["result_tds"] == 1.38
    assert row["result_ey"] == 20.5
    assert row["result_brix"] == 1.5
    assert row["result_tasting_notes"] == "Bright citrus"
    assert row["notes"] == "Bright acidity"
    assert row["coffee_roast_date"] == "2026-01-20"
    assert row["coffee_type"] == "single_origin"
    assert row["coffee_varietal"] == "Heirloom"
    assert row["coffee_process"] == "Washed"
    assert row["water_ppm"] == 150.0
    # v0.3: ratings now stored in individual columns, not JSON
    assert row["result_rating_overall"] == 4
    assert row["result_rating_acidity"] == 5


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
        "grind": "medium_fine",
        "duration_s": 180,
        "notes": "Bright acidity",
        "coffee": {
            "roast_date": "2026-01-20",
            "type": "single_origin",
            "origin": ["Ethiopia"],
            "varietal": "Heirloom",
            "process": "Washed",
        },
        "water": {"ppm": 150.0},
        "result": {
            "tds": 1.38,
            "ey": 20.5,
        },
    }
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    row = db_module.get_brew(brew_id, tmp_db)
    assert row["method"] == "Hario V60"
    assert row["coffee_type"] == "single_origin"
    assert json.loads(row["coffee_origin"]) == ["Ethiopia"]
    assert row["water_ppm"] == 150.0
    assert row["result_tds"] == 1.38
    assert row["result_ey"] == 20.5


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
    )
    brew_id = db_module.insert_brew(brew, tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row is not None
    assert row["method"] == malicious
    assert row["notes"] == malicious
    # Table still exists
    cursor = tmp_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='brews'"
    )
    assert cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# AC-1, AC-34: UPDATABLE_COLUMNS allowlist and update_brew assertion
# ---------------------------------------------------------------------------

def test_updatable_columns_constant_exists():
    """AC-1: UPDATABLE_COLUMNS is importable from db."""
    from brewlog.db import UPDATABLE_COLUMNS  # noqa: F401


def test_updatable_columns_is_frozenset():
    """AC-1: UPDATABLE_COLUMNS is a frozenset."""
    from brewlog.db import UPDATABLE_COLUMNS
    assert isinstance(UPDATABLE_COLUMNS, frozenset)


def test_updatable_columns_contains_new_columns():
    """AC-34: all 8 result_rating_* columns are in UPDATABLE_COLUMNS."""
    from brewlog.db import UPDATABLE_COLUMNS
    new_cols = {
        "result_rating_overall",
        "result_rating_fragrance",
        "result_rating_aroma",
        "result_rating_flavour",
        "result_rating_aftertaste",
        "result_rating_acidity",
        "result_rating_sweetness",
        "result_rating_mouthfeel",
    }
    assert new_cols.issubset(UPDATABLE_COLUMNS)


def test_updatable_columns_does_not_contain_id():
    """AC-1: 'id' must NOT be in UPDATABLE_COLUMNS."""
    from brewlog.db import UPDATABLE_COLUMNS
    assert "id" not in UPDATABLE_COLUMNS


def test_updatable_columns_does_not_contain_date():
    """AC-1: 'date' must NOT be in UPDATABLE_COLUMNS (required field)."""
    from brewlog.db import UPDATABLE_COLUMNS
    assert "date" not in UPDATABLE_COLUMNS


def test_update_brew_rejects_unknown_column(tmp_db):
    """AC-1: update_brew with an unknown column raises AssertionError."""
    import pytest as _pytest
    brew_id = db_module.insert_brew(_minimal_brew(), tmp_db)
    with _pytest.raises(AssertionError):
        db_module.update_brew(brew_id, {"evil_col": "x"}, tmp_db)


def test_update_brew_accepts_all_valid_columns(tmp_db):
    """AC-1, AC-34: update_brew accepts columns from UPDATABLE_COLUMNS."""
    from brewlog.db import UPDATABLE_COLUMNS
    brew_id = db_module.insert_brew(_minimal_brew(), tmp_db)
    valid_updates = {
        "method": "V60",
        "notes": "test",
        "result_brix": 1.5,
        "result_rating_overall": 4,
    }
    for col in valid_updates:
        assert col in UPDATABLE_COLUMNS
    found = db_module.update_brew(brew_id, valid_updates, tmp_db)
    assert found is True


# ---------------------------------------------------------------------------
# AC-20, AC-23: DB schema migration
# ---------------------------------------------------------------------------

def test_fresh_db_has_all_new_rating_columns(tmp_path):
    """AC-20, AC-23: fresh DB has all 8 result_rating_* columns."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
        expected = {
            "result_rating_overall",
            "result_rating_fragrance",
            "result_rating_aroma",
            "result_rating_flavour",
            "result_rating_aftertaste",
            "result_rating_acidity",
            "result_rating_sweetness",
            "result_rating_mouthfeel",
        }
        assert expected.issubset(columns)
    finally:
        conn.close()


def test_result_ratings_column_retained(tmp_path):
    """AC-21: result_ratings (legacy JSON) column still present in schema."""
    conn = db_module.get_connection(db_path=tmp_path / "test.db")
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
        assert "result_ratings" in columns
    finally:
        conn.close()


def test_migration_adds_new_columns_to_existing_db(tmp_path):
    """AC-23: calling get_connection on a v0.2-style DB adds the new columns."""
    import sqlite3 as sqlite3_module
    db_path = tmp_path / "old.db"
    # Create a v0.2-style DB without the new rating columns
    old_conn = sqlite3_module.connect(db_path)
    old_conn.executescript("""
        CREATE TABLE brews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            dose_g REAL NOT NULL,
            water_weight_g REAL NOT NULL,
            result_tds REAL,
            result_ey REAL,
            result_brix REAL,
            result_tasting_notes TEXT,
            result_ratings TEXT
        );
    """)
    old_conn.commit()
    old_conn.close()

    # Now open with get_connection — migration should add new columns
    conn = db_module.get_connection(db_path=db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
        expected = {
            "result_rating_overall",
            "result_rating_fragrance",
            "result_rating_aroma",
            "result_rating_flavour",
        }
        assert expected.issubset(columns), f"Columns present: {columns}"
    finally:
        conn.close()


def test_migration_preserves_existing_rows(tmp_path):
    """AC-23: existing rows survive migration intact."""
    import sqlite3 as sqlite3_module
    db_path = tmp_path / "old.db"
    old_conn = sqlite3_module.connect(db_path)
    old_conn.executescript("""
        CREATE TABLE brews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            dose_g REAL NOT NULL,
            water_weight_g REAL NOT NULL,
            result_ratings TEXT
        );
        INSERT INTO brews (date, type, dose_g, water_weight_g)
        VALUES ('2026-01-01', 'pour_over', 18.0, 280.0);
    """)
    old_conn.commit()
    old_conn.close()

    conn = db_module.get_connection(db_path=db_path)
    try:
        row = conn.execute("SELECT * FROM brews WHERE id=1").fetchone()
        assert row is not None
    finally:
        conn.close()


def test_migration_is_idempotent(tmp_path):
    """AC-23: calling get_connection twice is safe — no duplicate columns."""
    conn1 = db_module.get_connection(db_path=tmp_path / "test.db")
    conn1.close()
    conn2 = db_module.get_connection(db_path=tmp_path / "test.db")
    try:
        columns = [row[1] for row in conn2.execute("PRAGMA table_info(brews)").fetchall()]
        assert columns.count("result_rating_overall") == 1
    finally:
        conn2.close()


# ---------------------------------------------------------------------------
# AC-14: insert_brew_dict stores individual rating columns
# ---------------------------------------------------------------------------

def test_insert_brew_dict_stores_individual_rating_columns(tmp_db):
    """AC-14: insert_brew_dict maps result.ratings to individual columns."""
    brew_dict = {
        "date": "2026-02-22",
        "type": "pour_over",
        "dose_g": 18.0,
        "water_weight_g": 280.0,
        "result": {
            "tds": 1.38,
            "ey": 20.1,
            "brix": 1.5,
            "tasting_notes": "Bright citrus",
            "ratings": {
                "overall": 4,
                "fragrance": 3,
                "aroma": 4,
                "flavour": 5,
                "aftertaste": 4,
                "acidity": 5,
                "sweetness": 3,
                "mouthfeel": 4,
            },
        },
    }
    brew_id = db_module.insert_brew_dict(brew_dict, tmp_db)
    tmp_db.commit()
    row = db_module.get_brew(brew_id, tmp_db)
    assert row["result_rating_overall"] == 4
    assert row["result_rating_fragrance"] == 3
    assert row["result_rating_aroma"] == 4
    assert row["result_rating_flavour"] == 5
    assert row["result_rating_aftertaste"] == 4
    assert row["result_rating_acidity"] == 5
    assert row["result_rating_sweetness"] == 3
    assert row["result_rating_mouthfeel"] == 4


def test_insert_brew_stores_individual_rating_columns(tmp_db):
    """AC-14: insert_brew (from BrewInput) maps ratings to individual columns."""
    brew = BrewInput(
        date="2026-02-22",
        type="pour_over",
        dose_g=18.0,
        water_weight_g=280.0,
        result=ResultInput(
            tds=1.38,
            ratings=RatingsInput(
                overall=4,
                fragrance=3,
                aroma=4,
                flavour=5,
                aftertaste=4,
                acidity=5,
                sweetness=3,
                mouthfeel=4,
            ),
        ),
    )
    brew_id = db_module.insert_brew(brew, tmp_db)
    row = db_module.get_brew(brew_id, tmp_db)
    assert row["result_rating_overall"] == 4
    assert row["result_rating_fragrance"] == 3
    assert row["result_rating_aroma"] == 4
    assert row["result_rating_flavour"] == 5


# ---------------------------------------------------------------------------
# AC-2, AC-3, AC-4, AC-5: list_brews_filtered with rating_min/rating_max/until
# ---------------------------------------------------------------------------

def _insert_brew_with_rating(conn, date: str, overall):
    """Helper: insert a brew and update result_rating_overall column."""
    brew = BrewInput(date=date, type="pour_over", dose_g=18.0, water_weight_g=280.0)
    brew_id = db_module.insert_brew(brew, conn)
    if overall is not None:
        db_module.update_brew(brew_id, {"result_rating_overall": overall}, conn)
    return brew_id


def test_list_brews_filtered_rating_min(tmp_db):
    """AC-2: rating_min filters brews by overall rating >= N."""
    _insert_brew_with_rating(tmp_db, "2026-02-01", 2)
    _insert_brew_with_rating(tmp_db, "2026-02-02", 3)
    _insert_brew_with_rating(tmp_db, "2026-02-03", 4)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, rating_min=3)
    assert len(rows) == 2
    overalls = {row["result_rating_overall"] for row in rows}
    assert overalls == {3, 4}


def test_list_brews_filtered_rating_max(tmp_db):
    """AC-3: rating_max filters brews by overall rating <= N."""
    _insert_brew_with_rating(tmp_db, "2026-02-01", 2)
    _insert_brew_with_rating(tmp_db, "2026-02-02", 3)
    _insert_brew_with_rating(tmp_db, "2026-02-03", 4)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, rating_max=3)
    assert len(rows) == 2
    overalls = {row["result_rating_overall"] for row in rows}
    assert overalls == {2, 3}


def test_list_brews_filtered_rating_range(tmp_db):
    """AC-4: rating_min + rating_max form a range filter."""
    _insert_brew_with_rating(tmp_db, "2026-02-01", 1)
    _insert_brew_with_rating(tmp_db, "2026-02-02", 3)
    _insert_brew_with_rating(tmp_db, "2026-02-03", 5)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, rating_min=2, rating_max=4)
    assert len(rows) == 1
    assert rows[0]["result_rating_overall"] == 3


def test_list_brews_filtered_null_rating_excluded_by_min(tmp_db):
    """AC-2: brews with NULL overall rating are excluded by rating_min."""
    _insert_brew_with_rating(tmp_db, "2026-02-01", None)
    _insert_brew_with_rating(tmp_db, "2026-02-02", 3)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, rating_min=1)
    assert len(rows) == 1
    assert rows[0]["result_rating_overall"] == 3


def test_list_brews_filtered_until(tmp_db):
    """AC-39: until filters brews on or before the given date."""
    _insert_brew_with_rating(tmp_db, "2026-02-10", None)
    _insert_brew_with_rating(tmp_db, "2026-02-15", None)
    _insert_brew_with_rating(tmp_db, "2026-02-20", None)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, until="2026-02-15")
    assert len(rows) == 2
    dates = {row["date"] for row in rows}
    assert dates == {"2026-02-10", "2026-02-15"}


def test_list_brews_filtered_since_and_until(tmp_db):
    """AC-40: since + until form an inclusive range."""
    _insert_brew_with_rating(tmp_db, "2026-02-01", None)
    _insert_brew_with_rating(tmp_db, "2026-02-10", None)
    _insert_brew_with_rating(tmp_db, "2026-02-20", None)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, since="2026-02-01", until="2026-02-10")
    assert len(rows) == 2


def test_list_brews_filtered_since_with_datetime_stored(tmp_db):
    """AC-10: substr comparison works with stored YYYY-MM-DDTHH:MM:SSZ dates."""
    brew = BrewInput(date="2026-02-22T09:15:00Z", type="pour_over", dose_g=18.0, water_weight_g=280.0)
    db_module.insert_brew(brew, tmp_db)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, since="2026-02-22")
    assert len(rows) == 1


def test_list_brews_filtered_until_with_datetime_stored(tmp_db):
    """AC-10: until comparison works with stored YYYY-MM-DDTHH:MM:SSZ dates."""
    brew = BrewInput(date="2026-02-22T09:15:00Z", type="pour_over", dose_g=18.0, water_weight_g=280.0)
    db_module.insert_brew(brew, tmp_db)
    rows = db_module.list_brews_filtered(tmp_db, all_rows=True, until="2026-02-22")
    assert len(rows) == 1
