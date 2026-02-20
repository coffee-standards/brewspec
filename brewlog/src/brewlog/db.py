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
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS brews (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            date                TEXT    NOT NULL,
            type                TEXT    NOT NULL,
            method              TEXT,
            dose_g              REAL    NOT NULL,
            water_weight_g      REAL    NOT NULL,
            water_volume_ml     REAL,
            water_temp_c        REAL,
            grind               TEXT,
            duration_s          INTEGER,
            tds                 REAL,
            ey                  REAL,
            rating              INTEGER,
            notes               TEXT,
            coffee_roast_date   TEXT,
            coffee_type         TEXT,
            coffee_origin       TEXT,
            coffee_varietal     TEXT,
            coffee_process      TEXT,
            water_ppm           REAL,
            equipment_grinder   TEXT,
            equipment_brewer    TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC);
    """)
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

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            tds, ey, rating, notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm,
            equipment_grinder, equipment_brewer
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?,
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
        brew.tds,
        brew.ey,
        brew.rating,
        brew.notes,
        coffee.roast_date if coffee else None,
        coffee.type if coffee else None,
        json.dumps(coffee.origin) if (coffee and coffee.origin) else None,
        coffee.varietal if coffee else None,
        coffee.process if coffee else None,
        water.ppm if water else None,
        equipment.grinder if equipment else None,
        equipment.brewer if equipment else None,
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
    origin = coffee.get("origin")

    sql = """
        INSERT INTO brews (
            date, type, method, dose_g, water_weight_g,
            water_volume_ml, water_temp_c, grind, duration_s,
            tds, ey, rating, notes,
            coffee_roast_date, coffee_type, coffee_origin,
            coffee_varietal, coffee_process,
            water_ppm,
            equipment_grinder, equipment_brewer
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?,
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
        brew_dict.get("tds"),
        brew_dict.get("ey"),
        brew_dict.get("rating"),
        brew_dict.get("notes"),
        coffee.get("roast_date"),
        coffee.get("type"),
        json.dumps(origin) if origin else None,
        coffee.get("varietal"),
        coffee.get("process"),
        water.get("ppm"),
        equipment.get("grinder"),
        equipment.get("brewer"),
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


def get_all_brews(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all brews ordered by date descending. Used by export."""
    sql = "SELECT * FROM brews ORDER BY date DESC"
    return conn.execute(sql).fetchall()


def get_latest_brew_id(conn: sqlite3.Connection) -> int | None:
    """Return the id of the most-recently-dated brew, or None if the table is empty."""
    row = conn.execute("SELECT id FROM brews ORDER BY date DESC LIMIT 1").fetchone()
    return row["id"] if row else None


def update_brew(brew_id: int, updates: dict, conn: sqlite3.Connection) -> bool:
    """
    SET only the columns in `updates` for the row with brew_id.
    Returns True if the row was found and updated, False otherwise.
    All column names in `updates` must be valid brews table columns.
    Uses parameterised ? placeholders — no string interpolation of values.
    """
    set_clauses = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [brew_id]
    cursor = conn.execute(
        f"UPDATE brews SET {set_clauses} WHERE id = ?",  # noqa: S608
        values,
    )
    conn.commit()
    return cursor.rowcount > 0
