"""
Database layer for BrewLog.

Uses Python's stdlib sqlite3 module — no ORM.
All SQL queries use parameterised ? placeholders — no string interpolation.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brewlog.models import BrewInput

# ---------------------------------------------------------------------------
# Database file location
# ---------------------------------------------------------------------------

DB_DIR = Path.home() / ".brewlog"
DB_PATH = DB_DIR / "brews.db"


# ---------------------------------------------------------------------------
# Column allowlist for update_brew() — AC-1, AC-34
# ---------------------------------------------------------------------------

UPDATABLE_COLUMNS: frozenset[str] = frozenset({
    "method",
    "grind",
    "water_temp_c",
    "duration_s",
    "notes",
    "result_tds",
    "result_ey",
    "result_brix",
    "result_tasting_notes",
    "result_rating_overall",
    "result_rating_fragrance",
    "result_rating_aroma",
    "result_rating_flavour",
    "result_rating_aftertaste",
    "result_rating_acidity",
    "result_rating_sweetness",
    "result_rating_mouthfeel",
    "coffee_roast_date",
    "coffee_type",
    "coffee_origin",
    "coffee_varietal",
    "coffee_process",
    "water_ppm",
    "equipment_grinder",
    "equipment_brewer",
})


# ---------------------------------------------------------------------------
# Migration constants — AC-20, AC-23
# ---------------------------------------------------------------------------

_V3_MIGRATION_COLUMNS: dict[str, str] = {
    "result_rating_overall":    "INTEGER",
    "result_rating_fragrance":  "INTEGER",
    "result_rating_aroma":      "INTEGER",
    "result_rating_flavour":    "INTEGER",
    "result_rating_aftertaste": "INTEGER",
    "result_rating_acidity":    "INTEGER",
    "result_rating_sweetness":  "INTEGER",
    "result_rating_mouthfeel":  "INTEGER",
}


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Return a sqlite3.Connection to the brew database.

    Creates the database directory and schema on first call.
    db_path defaults to DB_PATH (~/.brewlog/brews.db).
    The db_path parameter exists to support test isolation (tmp paths).
    """
    if db_path is None:
        db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # rows accessible as dicts
    _init_schema(conn)
    _apply_migrations(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS brews (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            date                    TEXT    NOT NULL,
            type                    TEXT    NOT NULL,
            method                  TEXT,
            dose_g                  REAL    NOT NULL,
            water_weight_g          REAL    NOT NULL,
            water_volume_ml         REAL,
            water_temp_c            REAL,
            grind                   TEXT,
            duration_s              INTEGER,
            notes                   TEXT,
            coffee_roast_date       TEXT,
            coffee_type             TEXT,
            coffee_origin           TEXT,
            coffee_varietal         TEXT,
            coffee_process          TEXT,
            water_ppm               REAL,
            equipment_grinder       TEXT,
            equipment_brewer        TEXT,
            result_tds              REAL,
            result_ey               REAL,
            result_brix             REAL,
            result_tasting_notes    TEXT,
            result_ratings          TEXT,
            result_rating_overall   INTEGER,
            result_rating_fragrance INTEGER,
            result_rating_aroma     INTEGER,
            result_rating_flavour   INTEGER,
            result_rating_aftertaste INTEGER,
            result_rating_acidity   INTEGER,
            result_rating_sweetness INTEGER,
            result_rating_mouthfeel INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
    """)
    conn.commit()


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Add any missing v0.3 columns without modifying existing data. AC-23."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(brews)").fetchall()
    }
    for col, col_type in _V3_MIGRATION_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE brews ADD COLUMN {col} {col_type}")  # noqa: S608
    conn.commit()


# ---------------------------------------------------------------------------
# Insert operations
# ---------------------------------------------------------------------------

def insert_brew(brew: "BrewInput", conn: sqlite3.Connection) -> int:
    """
    Insert a validated BrewInput into the brews table.
    Returns the new row's integer ID.
    All SQL uses ? placeholders. No string interpolation.
    """
    coffee = brew.coffee
    water = brew.water
    equipment = brew.equipment
    result = brew.result
    ratings = result.ratings if result else None

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm,
            equipment_grinder, equipment_brewer,
            result_tds, result_ey, result_brix,
            result_tasting_notes,
            result_rating_overall, result_rating_fragrance, result_rating_aroma,
            result_rating_flavour, result_rating_aftertaste, result_rating_acidity,
            result_rating_sweetness, result_rating_mouthfeel
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?,
            ?, ?, ?,
            ?, ?,
            ?,
            ?, ?,
            ?, ?, ?,
            ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?
        )
    """
    params = (
        brew.date,
        brew.type,
        brew.method,
        brew.dose_g,
        brew.water_weight_g,
        brew.water_volume_ml,
        brew.water_temp_c,
        brew.grind,
        brew.duration_s,
        brew.notes,
        coffee.roast_date if coffee else None,
        coffee.type if coffee else None,
        json.dumps(coffee.origin) if (coffee and coffee.origin) else None,
        coffee.varietal if coffee else None,
        coffee.process if coffee else None,
        water.ppm if water else None,
        equipment.grinder if equipment else None,
        equipment.brewer if equipment else None,
        result.tds if result else None,
        result.ey if result else None,
        result.brix if result else None,
        result.tasting_notes if result else None,
        ratings.overall if ratings else None,
        ratings.fragrance if ratings else None,
        ratings.aroma if ratings else None,
        ratings.flavour if ratings else None,
        ratings.aftertaste if ratings else None,
        ratings.acidity if ratings else None,
        ratings.sweetness if ratings else None,
        ratings.mouthfeel if ratings else None,
    )
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor.lastrowid


def insert_brew_dict(brew_dict: dict, conn: sqlite3.Connection) -> int:
    """
    Insert a brew from a validated BrewSpec brew dict (already schema-validated).
    Returns the new row ID.
    All SQL uses ? placeholders.

    Note: Does NOT call conn.commit() — the caller is responsible for committing
    (to support transactional batch inserts in the import command).
    """
    coffee = brew_dict.get("coffee") or {}
    water = brew_dict.get("water") or {}
    equipment = brew_dict.get("equipment") or {}
    result = brew_dict.get("result") or {}
    origin = coffee.get("origin")
    ratings = result.get("ratings") or {}

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm,
            equipment_grinder, equipment_brewer,
            result_tds, result_ey, result_brix,
            result_tasting_notes,
            result_rating_overall, result_rating_fragrance, result_rating_aroma,
            result_rating_flavour, result_rating_aftertaste, result_rating_acidity,
            result_rating_sweetness, result_rating_mouthfeel
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?,
            ?, ?, ?,
            ?, ?,
            ?,
            ?, ?,
            ?, ?, ?,
            ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?
        )
    """
    params = (
        brew_dict.get("date"),
        brew_dict.get("type"),
        brew_dict.get("method"),
        brew_dict.get("dose_g"),
        brew_dict.get("water_weight_g"),
        brew_dict.get("water_volume_ml"),
        brew_dict.get("water_temp_c"),
        brew_dict.get("grind"),
        brew_dict.get("duration_s"),
        brew_dict.get("notes"),
        coffee.get("roast_date"),
        coffee.get("type"),
        json.dumps(origin) if origin else None,
        coffee.get("varietal"),
        coffee.get("process"),
        water.get("ppm"),
        equipment.get("grinder"),
        equipment.get("brewer"),
        result.get("tds"),
        result.get("ey"),
        result.get("brix"),
        result.get("tasting_notes"),
        ratings.get("overall"),
        ratings.get("fragrance"),
        ratings.get("aroma"),
        ratings.get("flavour"),
        ratings.get("aftertaste"),
        ratings.get("acidity"),
        ratings.get("sweetness"),
        ratings.get("mouthfeel"),
    )
    cursor = conn.execute(sql, params)
    return cursor.lastrowid


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_brew(brew_id: int, conn: sqlite3.Connection) -> sqlite3.Row | None:
    """
    Fetch a single brew row by integer ID.
    Returns sqlite3.Row or None if not found.
    """
    sql = "SELECT * FROM brews WHERE id = ?"
    cursor = conn.execute(sql, (brew_id,))
    return cursor.fetchone()


def list_brews(
    conn: sqlite3.Connection,
    limit: int = 20,
    all_rows: bool = False,
) -> list[sqlite3.Row]:
    """
    Return brews ordered by date descending.
    If all_rows is True, limit is ignored.
    """
    if all_rows:
        sql = "SELECT * FROM brews ORDER BY date DESC"
        cursor = conn.execute(sql)
    else:
        sql = "SELECT * FROM brews ORDER BY date DESC LIMIT ?"
        cursor = conn.execute(sql, (limit,))
    return cursor.fetchall()


def list_brews_filtered(
    conn: sqlite3.Connection,
    limit: int = 20,
    all_rows: bool = False,
    brew_type: str | None = None,
    since: str | None = None,
    until: str | None = None,
    rating_min: int | None = None,
    rating_max: int | None = None,
) -> list[sqlite3.Row]:
    """
    Return brews ordered by date descending with optional filters.

    All filters are applied as AND conditions. Condition strings are static;
    values are always passed as parameters — no string interpolation of values.

    Args:
        brew_type: exact match on the type column.
        since: lower bound (inclusive) on date, compared at day granularity.
        until: upper bound (inclusive) on date, compared at day granularity.
        rating_min: minimum result_rating_overall (inclusive).
        rating_max: maximum result_rating_overall (inclusive).
        limit: maximum rows to return (ignored when all_rows is True).
        all_rows: if True, return all matching rows.
    """
    conditions: list[str] = []
    params: list = []

    if brew_type is not None:
        conditions.append("type = ?")
        params.append(brew_type)

    if since is not None:
        # Use substr to compare at day granularity for both stored formats.
        conditions.append("substr(date, 1, 10) >= ?")
        params.append(since)

    if until is not None:
        # Use substr to compare at day granularity for both stored formats.
        conditions.append("substr(date, 1, 10) <= ?")
        params.append(until)

    if rating_min is not None:
        conditions.append("result_rating_overall >= ?")
        params.append(rating_min)

    if rating_max is not None:
        conditions.append("result_rating_overall <= ?")
        params.append(rating_max)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    if all_rows:
        sql = f"SELECT * FROM brews {where} ORDER BY date DESC"  # noqa: S608
        cursor = conn.execute(sql, params)
    else:
        sql = f"SELECT * FROM brews {where} ORDER BY date DESC LIMIT ?"  # noqa: S608
        cursor = conn.execute(sql, params + [limit])

    return cursor.fetchall()


def get_all_brews(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all brews ordered by date descending. Used by export."""
    sql = "SELECT * FROM brews ORDER BY date DESC"
    return conn.execute(sql).fetchall()


def delete_brew(brew_id: int, conn: sqlite3.Connection) -> bool:
    """
    Delete the brew with the given ID. Returns True if a row was deleted.
    Uses a parameterised ? placeholder — no string interpolation.
    """
    cursor = conn.execute("DELETE FROM brews WHERE id = ?", (brew_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_latest_brew_id(conn: sqlite3.Connection) -> int | None:
    """Return the id of the most-recently-dated brew, or None if the table is empty."""
    row = conn.execute("SELECT id FROM brews ORDER BY date DESC LIMIT 1").fetchone()
    return row["id"] if row else None


def update_brew(brew_id: int, updates: dict, conn: sqlite3.Connection) -> bool:
    """
    SET only the columns in `updates` for the row with brew_id.
    Returns True if the row was found and updated, False otherwise.
    Column names must be in UPDATABLE_COLUMNS — assertion enforces this. AC-1.
    Uses parameterised ? placeholders — no string interpolation of values.
    """
    assert set(updates.keys()).issubset(UPDATABLE_COLUMNS), (
        f"Unexpected column names in update dict: "
        f"{set(updates.keys()) - UPDATABLE_COLUMNS}"
    )
    set_clauses = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [brew_id]
    cursor = conn.execute(
        f"UPDATE brews SET {set_clauses} WHERE id = ?",  # noqa: S608
        values,
    )
    conn.commit()
    return cursor.rowcount > 0
