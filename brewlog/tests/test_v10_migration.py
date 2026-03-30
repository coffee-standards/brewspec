"""
Migration tests for BrewLog CLI v1.0.

Tests cover all migration acceptance criteria:
AC-3: water_weight_g renamed to water_g
AC-4: notes renamed to process_notes
AC-5: old columns absent after migration, new names present
AC-6: idempotent migration
AC-7: new columns added (yield_g, result_water_g, coffee_cupping_notes,
       equipment_pressure_bar, equipment_flow_rate_ml_s)
AC-8: new columns default to NULL for existing rows

TDD: tests written before implementation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


from brewlog import db as db_module


# ---------------------------------------------------------------------------
# Helper: create an old-schema DB (simulating a pre-v1.0 database)
# ---------------------------------------------------------------------------

def _create_old_schema_db(db_path: Path) -> None:
    """
    Create a SQLite DB that looks like a pre-v1.0 BrewLog database.
    Uses water_weight_g and notes columns (pre-rename), without the new columns.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE brews (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            date                      TEXT,
            type                      TEXT,
            method                    TEXT,
            dose_g                    REAL,
            water_weight_g            REAL,
            brew_ratio                REAL,
            water_volume_ml           REAL,
            water_temp_c              REAL,
            grind                     TEXT,
            duration_s                INTEGER,
            notes                     TEXT,
            coffee_roast_date         TEXT,
            coffee_type               TEXT,
            coffee_name               TEXT,
            coffee_origins            TEXT,
            coffee_origin             TEXT,
            coffee_varietal           TEXT,
            coffee_process            TEXT,
            water_ppm                 REAL,
            equipment_grinder         TEXT,
            equipment_brewer          TEXT,
            equipment_grinder_setting REAL,
            equipment_notes           TEXT,
            result_tds                REAL,
            result_ey                 REAL,
            result_brix               REAL,
            result_yield_g            REAL,
            result_tasting_notes      TEXT,
            result_ratings            TEXT,
            result_rating_overall     INTEGER,
            result_rating_fragrance   INTEGER,
            result_rating_aroma       INTEGER,
            result_rating_flavour     INTEGER,
            result_rating_aftertaste  INTEGER,
            result_rating_acidity     INTEGER,
            result_rating_sweetness   INTEGER,
            result_rating_mouthfeel   INTEGER,
            coffee_roaster            TEXT,
            coffee_roast_level        TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_brews_date ON brews (date DESC)")
    conn.commit()
    conn.close()


def _insert_old_row(db_path: Path, water_weight_g: float = 280.0, notes: str = "Test notes") -> int:
    """Insert a row into an old-schema DB using old column names."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO brews (date, type, dose_g, water_weight_g, notes) VALUES (?, ?, ?, ?, ?)",
        ("2026-01-15", "pour_over", 18.0, water_weight_g, notes),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def _get_column_names(db_path: Path) -> set[str]:
    """Return the set of column names in the brews table."""
    conn = sqlite3.connect(db_path)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(brews)").fetchall()}
    conn.close()
    return cols


# ---------------------------------------------------------------------------
# AC-3: water_weight_g renamed to water_g
# ---------------------------------------------------------------------------

class TestMigrationRenameWaterWeightG:
    """AC-3: water_weight_g column is renamed to water_g."""

    def test_water_weight_g_renamed_to_water_g(self, tmp_path):
        """After migration, water_g present and water_weight_g absent."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path, water_weight_g=250.0)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols, "water_g column must be present after migration"
        assert "water_weight_g" not in cols, "water_weight_g column must be absent after migration"

    def test_water_g_data_preserved_after_rename(self, tmp_path):
        """AC-3: existing data in water_weight_g is preserved under water_g."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, water_weight_g=250.0)

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["water_g"] == 250.0
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# AC-4: notes renamed to process_notes
# ---------------------------------------------------------------------------

class TestMigrationRenameNotes:
    """AC-4: notes column is renamed to process_notes."""

    def test_notes_renamed_to_process_notes(self, tmp_path):
        """After migration, process_notes present and notes absent."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path, notes="Pre-infused 5s")

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "process_notes" in cols
        assert "notes" not in cols

    def test_process_notes_data_preserved_after_rename(self, tmp_path):
        """AC-4: existing data in notes is preserved under process_notes."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, notes="Pre-infused 5s")

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["process_notes"] == "Pre-infused 5s"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# AC-5: both old columns absent, both new names present
# ---------------------------------------------------------------------------

class TestMigrationBothRenames:
    """AC-5: after migration, water_weight_g and notes absent, water_g and process_notes present."""

    def test_both_old_columns_absent(self, tmp_path):
        """Old names must not appear in PRAGMA table_info after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_weight_g" not in cols
        assert "notes" not in cols

    def test_both_new_columns_present(self, tmp_path):
        """New names must appear in PRAGMA table_info after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols
        assert "process_notes" in cols


# ---------------------------------------------------------------------------
# AC-6: idempotent migration
# ---------------------------------------------------------------------------

class TestMigrationIdempotent:
    """AC-6: calling get_connection() multiple times on the same DB produces no error."""

    def test_migration_idempotent_twice(self, tmp_path):
        """Second call to get_connection() on already-migrated DB must not fail."""
        db_path = tmp_path / "test.db"
        conn1 = db_module.get_connection(db_path=db_path)
        conn1.close()
        # Second call must not raise
        conn2 = db_module.get_connection(db_path=db_path)
        conn2.close()

    def test_migration_idempotent_on_old_db(self, tmp_path):
        """Running migration twice on an old DB produces no error."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn1 = db_module.get_connection(db_path=db_path)
        conn1.close()

        # Second call on now-migrated DB must not fail
        conn2 = db_module.get_connection(db_path=db_path)
        conn2.close()

        cols = _get_column_names(db_path)
        assert "water_g" in cols
        assert "process_notes" in cols
        assert "water_weight_g" not in cols
        assert "notes" not in cols


# ---------------------------------------------------------------------------
# AC-7: new columns added
# ---------------------------------------------------------------------------

class TestMigrationNewColumns:
    """AC-7: the v1.0 migration adds five new columns."""

    def test_new_columns_present_on_fresh_db(self, tmp_path):
        """Fresh DB created by get_connection() has all five new columns."""
        db_path = tmp_path / "fresh.db"
        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "yield_g" in cols
        assert "result_water_g" in cols
        assert "coffee_cupping_notes" in cols
        assert "equipment_pressure_bar" in cols
        assert "equipment_flow_rate_ml_s" in cols

    def test_new_columns_added_to_old_db(self, tmp_path):
        """Old DB gains all five new columns after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        conn.close()

        cols = _get_column_names(db_path)
        assert "yield_g" in cols
        assert "result_water_g" in cols
        assert "coffee_cupping_notes" in cols
        assert "equipment_pressure_bar" in cols
        assert "equipment_flow_rate_ml_s" in cols


# ---------------------------------------------------------------------------
# AC-8: new columns are NULL for pre-migration rows
# ---------------------------------------------------------------------------

class TestMigrationNewColumnsAreNull:
    """AC-8: new columns default to NULL for existing rows."""

    def test_new_columns_null_for_existing_row(self, tmp_path):
        """Pre-migration row has NULL for all five new columns after migration."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path)

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            assert row["yield_g"] is None
            assert row["result_water_g"] is None
            assert row["coffee_cupping_notes"] is None
            assert row["equipment_pressure_bar"] is None
            assert row["equipment_flow_rate_ml_s"] is None
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Transaction integrity
# ---------------------------------------------------------------------------

class TestMigrationTransaction:
    """Both renames and all new column additions must complete together."""

    def test_both_renames_and_new_columns_all_present(self, tmp_path):
        """After migration, both renamed columns and all new columns are present."""
        db_path = tmp_path / "old.db"
        _create_old_schema_db(db_path)
        row_id = _insert_old_row(db_path, water_weight_g=200.0, notes="Bloom 30s")

        conn = db_module.get_connection(db_path=db_path)
        try:
            row = db_module.get_brew(row_id, conn)
            # Renamed columns preserved data
            assert row["water_g"] == 200.0
            assert row["process_notes"] == "Bloom 30s"
            # New columns are NULL
            assert row["yield_g"] is None
            assert row["result_water_g"] is None
            assert row["coffee_cupping_notes"] is None
            assert row["equipment_pressure_bar"] is None
            assert row["equipment_flow_rate_ml_s"] is None
        finally:
            conn.close()
